"""Regression: hủy đơn đang vận chuyển -> nhập kho sau, chống cộng trùng;
thống kê chỉ tính đơn hoàn thành đã giao và đã có giao dịch đã thanh toán.
Chỉ sử dụng database SQLite tạm, tuyệt đối không truy cập database demo thật.
"""
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from app import create_app
from app.db import get_db_connection, query_all, query_one
from app.services import dashboard
from app.services.best_sellers import get_best_selling_products
from app.services.order_ops import (
    OrderOperationError, confirm_order_stock, start_order_shipping,
    record_order_payment, cancel_order_stock, get_order_return_lines,
    confirm_return_stock,
)
from app.services.checkout import create_pending_order


class ReturnInventoryRevenueRegressions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = create_app({
            'TESTING': True, 'DB_BACKEND': 'sqlite',
            'DATABASE': str(Path(self.tmp.name) / 'test.sqlite3'),
            'SECRET_KEY': 'test-only-return-and-revenue',
        })
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()
        self.tmp.cleanup()

    def order(self, qty=2, basket=None):
        return create_pending_order({
            'full_name': 'Người mua demo', 'phone': '0000000000',
            'email': 'demo@example.com', 'fulfillment': 'delivery',
            'address': 'Hà Nội', 'payment_method': 'cod', 'note': 'test'
        }, basket or {1: qty}, user_id=3)

    def stock(self, variant=1):
        return int(query_one('SELECT SoLuongTon FROM BienTheSanPham WHERE MaBienThe=?', (variant,))['SoLuongTon'])

    def shipping_cancel(self, qty=2):
        order_id = self.order(qty)
        confirm_order_stock(order_id, 1)
        start_order_shipping(order_id, 1)
        # Fixture lịch sử đã hủy trước thay đổi nghiệp vụ; không tạo qua API mới.
        conn=get_db_connection()
        conn.execute("UPDATE DonHang SET TrangThai='Đã hủy' WHERE MaDonHang=?", (order_id,))
        conn.execute("INSERT INTO HoanKhoChiTiet (MaDonHang,MaBienThe,SoLuongCanHoan) VALUES (?,1,?)", (order_id,qty))
        conn.commit(); conn.close()
        return order_id

    def test_legacy_cancelled_shipping_retains_pending_return(self):
        before = self.stock()
        order_id = self.shipping_cancel(2)
        self.assertEqual(self.stock(), before-2)
        order = query_one('SELECT TrangThai,TrangThaiGiaoHang FROM DonHang WHERE MaDonHang=?', (order_id,))
        self.assertEqual(order['TrangThai'], 'Đã hủy')
        self.assertEqual(order['TrangThaiGiaoHang'], 'Đang giao')  # lịch sử vận chuyển, không phải đang vận chuyển tiếp
        lines = get_order_return_lines(order_id)
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]['ConCho'], 2)
        self.assertEqual(lines[0]['SoLuongDaHoan'], 0)

    def test_returns_only_on_staff_confirmation(self):
        before = self.stock()
        oid = self.shipping_cancel(2)
        confirm_return_stock(oid, 2, {1: 2})
        self.assertEqual(self.stock(), before)
        self.assertEqual(get_order_return_lines(oid)[0]['ConCho'], 0)
        with self.assertRaises(OrderOperationError):
            confirm_return_stock(oid, 2, {1: 2})
        self.assertEqual(self.stock(), before)

    def test_partial_and_damaged_stock_processing(self):
        before = self.stock()
        oid = self.shipping_cancel(3)
        confirm_return_stock(oid, 1, {1: 1}, {1: 1})
        self.assertEqual(self.stock(), before-2)
        self.assertEqual(get_order_return_lines(oid)[0]['ConCho'], 1)
        confirm_return_stock(oid, 1, {1: 1})
        line = get_order_return_lines(oid)[0]
        self.assertEqual((line['SoLuongDaHoan'],line['SoLuongHong'],line['ConCho']),(2,1,0))
        self.assertEqual(self.stock(), before-1)  # 1 sản phẩm hỏng không nhập lại
        logs = query_all('SELECT * FROM LichSuHoanKho WHERE MaDonHang=?', (oid,))
        self.assertEqual(len(logs),2)
        self.assertEqual(logs[0]['NguoiThucHien'],1)

    def test_over_return_and_negative_quantity_rollback(self):
        before = self.stock()
        oid = self.shipping_cancel(2)
        for good,bad in ((3,0),(-1,0),(2,1)):
            with self.assertRaises(OrderOperationError):
                confirm_return_stock(oid, 1, {1:good},{1:bad})
            self.assertEqual(self.stock(), before-2)
            self.assertEqual(get_order_return_lines(oid)[0]['ConCho'],2)
        self.assertEqual(query_one('SELECT COUNT(*) AS c FROM LichSuHoanKho WHERE MaDonHang=?',(oid,))['c'],0)

    def test_immediate_return_before_shipping_once(self):
        before = self.stock()
        oid = self.order(2)
        confirm_order_stock(oid, 1)
        cancel_order_stock(oid, 1)
        self.assertEqual(self.stock(), before)
        self.assertEqual(get_order_return_lines(oid),[])
        with self.assertRaises(OrderOperationError):
            cancel_order_stock(oid, 1)
        self.assertEqual(self.stock(), before)

    def test_shipping_cancel_is_rejected_with_or_without_payment(self):
        for paid in (False, True):
            oid = self.order(1)
            confirm_order_stock(oid,1)
            if paid: record_order_payment(oid,1)
            start_order_shipping(oid,1)
            before=self.stock()
            with self.assertRaises(OrderOperationError): cancel_order_stock(oid,2)
            self.assertEqual(self.stock(), before)
            self.assertEqual(query_one('SELECT TrangThai FROM DonHang WHERE MaDonHang=?',(oid,))['TrangThai'],'Đã xác nhận')
            self.assertEqual(get_order_return_lines(oid), [])

    def test_paid_not_shipped_cancels_and_waits_for_refund(self):
        oid = self.order(1)
        before = self.stock()
        confirm_order_stock(oid,1)
        record_order_payment(oid,1)
        cancel_order_stock(oid,2)
        self.assertEqual(query_one('SELECT TrangThai FROM DonHang WHERE MaDonHang=?',(oid,))['TrangThai'],'Đã hủy')
        self.assertEqual(self.stock(),before)  # chưa gửi hàng: cộng kho ngay
        self.assertEqual(query_one('SELECT TrangThaiHoanTien FROM DonHang WHERE MaDonHang=?',(oid,))['TrangThaiHoanTien'],'Chờ xử lý hoàn tiền')

    def test_competing_return_confirmations_are_idempotent(self):
        oid = self.shipping_cancel(2)
        after_cancel = self.stock()
        success, errors = [], []
        def worker():
            with self.app.app_context():
                try:
                    confirm_return_stock(oid,1,{1:2})
                    success.append(1)
                except Exception as exc:
                    errors.append(str(exc))
        t1=threading.Thread(target=worker); t2=threading.Thread(target=worker)
        t1.start();t2.start();t1.join();t2.join()
        self.assertEqual(len(success),1)
        self.assertEqual(len(errors),1)
        self.assertEqual(self.stock(),after_cancel+2)

    def test_route_renders_and_accepts_return_only_with_staff_role(self):
        oid = self.shipping_cancel(1)
        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess['user_id']=2
            sess['role']='Seller'
        page=client.get(f'/staff/orders/{oid}')
        self.assertEqual(page.status_code,200)
        self.assertIn('Xác nhận hoàn kho',page.get_data(as_text=True))
        with client.session_transaction() as sess:
            token=sess['_csrf']
        res=client.post(f'/orders/{oid}/return-stock',data={
            'csrf_token':token,'good_1':'1','bad_1':'0'
        },follow_redirects=True)
        self.assertEqual(res.status_code,200)
        self.assertIn('Đã xử lý hoàn kho',res.get_data(as_text=True))
        self.assertEqual(get_order_return_lines(oid)[0]['ConCho'],0)
        with client.session_transaction() as sess:
            sess['role']='Customer'
        self.assertEqual(client.post(f'/orders/{oid}/return-stock',data={'csrf_token':token}).status_code,403)

    def test_completed_order_without_payment_never_counts_as_sale(self):
        oid = self.order(2)
        conn=get_db_connection()
        conn.execute("UPDATE DonHang SET TrangThai='Hoàn thành',TrangThaiGiaoHang='Đã giao' WHERE MaDonHang=?",(oid,))
        conn.execute('DELETE FROM ThongTinGiaoDich WHERE MaDonHang=?',(oid,))
        conn.commit();conn.close()
        self.assertEqual(dashboard.get_dashboard_stats()['completed_order_value'],0)
        self.assertFalse(any(int(r['MaSanPham'])==1 for r in get_best_selling_products()))
        client=self.app.test_client()
        res=client.get('/xu-huong')
        self.assertEqual(res.status_code,200)
        # Đơn thiếu giao dịch phải không đóng góp chỉ số 2 đôi
        from app.services.w11_insights import slow_stock_report
        report=slow_stock_report()
        self.assertEqual(int(next(r for r in report['items'] if r['MaSanPham']==1)['sold_period']),0)

    def test_paid_but_not_completed_remains_separate_metric(self):
        oid=self.order(2)
        confirm_order_stock(oid,1)
        record_order_payment(oid,1)
        stats=dashboard.get_dashboard_stats()
        self.assertGreater(stats['paid_order_value'],0)
        self.assertEqual(stats['completed_order_value'],0)

    def test_sqlserver_dashboard_uses_completed_not_paid_value(self):
        with patch.object(dashboard,'query_all',return_value=[]), patch.object(
            dashboard,'query_one',return_value={
                'total_orders':2,'pending_orders':0,'paid_orders':2,
                'paid_order_value':1300000, 'completed_order_value':500000,
            }):
            original=self.app.config['DB_BACKEND']
            self.app.config['DB_BACKEND']='sqlserver'
            try:
                stats=dashboard.get_dashboard_stats()
                self.assertEqual(stats['completed_order_value'],500000)
                self.assertEqual(stats['paid_order_value'],1300000)
            finally:
                self.app.config['DB_BACKEND']=original

if __name__=='__main__':
    unittest.main()
