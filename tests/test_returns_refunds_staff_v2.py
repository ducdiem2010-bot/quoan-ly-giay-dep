"""Kiểm thử nghiệp vụ mới: doanh thu chỉ ở Hoàn thành, trả hàng một phần,
hoàn tiền có xác nhận riêng và xóa THẬT tài khoản nhân viên giữ lịch sử.
SQLite tạm, không thay đổi dữ liệu demo thật.
"""
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4
from werkzeug.security import check_password_hash
from app import create_app
from app.db import query_one, query_all
from app.services.checkout import create_pending_order
from app.services.order_ops import (OrderOperationError, confirm_order_stock,
                                    start_order_shipping, mark_order_delivered,
                                    record_order_payment, complete_order_status,
                                    cancel_order_stock)
from app.services.return_refunds import (receive_completed_return, confirm_refund_paid,
                                        order_refund_summary)
from app.services.dashboard import get_dashboard_stats
from app.services.best_sellers import get_best_sellers_v1


class ReturnsRefundsStaffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.app = create_app({'TESTING': True,'DB_BACKEND':'sqlite',
                               'DATABASE':str(Path(self.temp.name)/'check.sqlite3'),
                               'SECRET_KEY':'secure-v2-unit-test-long-enough'})
        self.ctx=self.app.app_context()
        self.ctx.push()
        self.client=self.app.test_client()

    def tearDown(self):
        self.ctx.pop()
        self.temp.cleanup()

    def token(self):
        return uuid4().hex

    def order(self, qty=3):
        return create_pending_order({
            'full_name':'Khách demo', 'phone':'0981234567', 'email':'a@demo.test',
            'fulfillment':'delivery', 'address':'Hà Nội',
            'payment_method':'bank_transfer', 'note':'kiểm thử'}, {1: qty}, user_id=3)

    def complete(self, qty=3):
        oid=self.order(qty)
        confirm_order_stock(oid,2)
        start_order_shipping(oid,2)
        mark_order_delivered(oid,2)
        record_order_payment(oid,2)
        complete_order_status(oid,2)
        return oid

    def stock(self):
        return query_one('SELECT SoLuongTon FROM BienTheSanPham WHERE MaBienThe=1')['SoLuongTon']

    def unit(self, oid):
        return query_one('SELECT DonGia FROM ChiTietDonHang WHERE MaDonHang=?',(oid,))['DonGia']

    def login_admin(self):
        self.client.get('/login')
        with self.client.session_transaction() as sess:
            csrf=sess['_csrf']
        r=self.client.post('/login',data={'csrf_token':csrf,'email':'admin@shop.vn','password':'Demo@12345'})
        self.assertIn(r.status_code, (302,303))
        self.client.get('/login')
        with self.client.session_transaction() as sess:
            return sess['_csrf']

    def test_01_uncompleted_paid_is_not_revenue(self):
        oid=self.order()
        confirm_order_stock(oid,2)
        record_order_payment(oid,2)
        self.assertEqual(get_dashboard_stats()['completed_order_value'], 0)
        self.assertGreater(get_dashboard_stats()['paid_order_value'], 0)
        start_order_shipping(oid,2)
        mark_order_delivered(oid,2)
        self.assertEqual(get_dashboard_stats()['completed_order_value'], 0)
        complete_order_status(oid,2)
        self.assertAlmostEqual(get_dashboard_stats()['completed_order_value'],self.unit(oid)*3)
        with self.assertRaises(OrderOperationError):
            complete_order_status(oid,2)
        self.assertAlmostEqual(get_dashboard_stats()['completed_order_value'],self.unit(oid)*3)

    def test_02_paid_but_not_delivered_cannot_complete(self):
        oid=self.order()
        confirm_order_stock(oid,2)
        record_order_payment(oid,2)
        with self.assertRaises(OrderOperationError):complete_order_status(oid,2)

    def test_03_delivered_but_unpaid_cannot_complete(self):
        oid=self.order()
        confirm_order_stock(oid,2)
        start_order_shipping(oid,2)
        mark_order_delivered(oid,2)
        with self.assertRaises(OrderOperationError):complete_order_status(oid,2)

    def test_04_return_good_one_sales_net_two(self):
        oid=self.complete()
        unit=self.unit(oid)
        before=self.stock()
        receive_completed_return(oid, 2, [(1, 1 + 0)], self.token(), 'Khách đổi ý')
        self.assertEqual(self.stock(),before+1)
        self.assertAlmostEqual(get_dashboard_stats()['completed_order_value'],2*unit)
        self.assertEqual(order_refund_summary(oid)['approved'],unit)
        self.assertEqual(order_refund_summary(oid)['refunded'],0)
        self.assertEqual(order_refund_summary(oid)['status'],'Chờ hoàn tiền')
        self.assertEqual(query_one('SELECT SoLuong FROM ChiTietDonHang WHERE MaDonHang=?',(oid,))['SoLuong'],3)
        self.assertEqual(get_best_sellers_v1(6)[0]['TongDaBan'],2)

    def test_05_return_restock_without_classification(self):
        oid=self.complete()
        unit=self.unit(oid)
        before=self.stock()
        receive_completed_return(oid, 2, [(1, 0 + 1)], self.token(), 'Không vừa chân')
        self.assertEqual(self.stock(),before+1)
        self.assertAlmostEqual(get_dashboard_stats()['completed_order_value'],2*unit)
        self.assertEqual(query_one('SELECT SoLuongHong FROM TraHangChiTiet WHERE MaDonHang=?',(oid,))['SoLuongHong'],0)

    def test_06_two_pairs_in_same_batch(self):
        oid=self.complete()
        before=self.stock()
        unit=self.unit(oid)
        receive_completed_return(oid, 2, [(1, 1 + 1)], self.token(), 'Trả hai đôi')
        self.assertEqual(self.stock(),before+2)
        self.assertAlmostEqual(get_dashboard_stats()['completed_order_value'],unit)
        self.assertEqual(get_best_sellers_v1(6)[0]['TongDaBan'],1)

    def test_07_two_returns_total_not_over_purchased(self):
        oid=self.complete()
        unit=self.unit(oid)
        receive_completed_return(oid, 2, [(1, 1 + 0)], self.token(), 'Khách trả hàng')
        receive_completed_return(oid, 2, [(1, 1 + 1)], self.token(), 'Khách trả hàng')
        with self.assertRaises(OrderOperationError):
            receive_completed_return(oid, 2, [(1, 1 + 0)], self.token(), 'Khách trả hàng')
        self.assertEqual(get_dashboard_stats()['completed_order_value'],0)
        self.assertEqual(len(query_all('SELECT MaTraHang FROM TraHangChiTiet WHERE MaDonHang=?',(oid,))),2)

    def test_08_over_return_rejected_atomically(self):
        oid=self.complete()
        old=self.stock()
        with self.assertRaises(OrderOperationError):
            receive_completed_return(oid, 2, [(1, 4 + 0)], self.token(), 'Khách trả hàng')
        self.assertEqual(self.stock(),old)
        self.assertFalse(query_all('SELECT * FROM TraHangChiTiet WHERE MaDonHang=?',(oid,)))

    def test_09_obsolete_input_rejected(self):
        oid=self.complete()
        with self.assertRaises(OrderOperationError):
            receive_completed_return(oid,2,[(1,1,0,self.unit(oid)*2)],self.token(), 'Khách trả hàng')

    def test_10_return_request_repeat_is_rejected(self):
        oid=self.complete()
        t=self.token()
        receive_completed_return(oid, 2, [(1, 1 + 0)], t, 'Khách trả hàng')
        old=self.stock()
        with self.assertRaises(OrderOperationError):
            receive_completed_return(oid, 2, [(1, 1 + 0)], t, 'Khách trả hàng')
        self.assertEqual(self.stock(),old)
        self.assertEqual(len(query_all('SELECT * FROM TraHangChiTiet WHERE MaDonHang=?',(oid,))),1)

    def test_11_refund_partial_full_and_double_confirmation(self):
        oid=self.complete()
        unit=self.unit(oid)
        receive_completed_return(oid, 2, [(1, 1 + 0)], self.token(), 'Khách trả hàng')
        half=unit/2
        t=self.token()
        confirm_refund_paid(oid,2,half,'cash','',t)
        self.assertEqual(order_refund_summary(oid)['status'],'Hoàn tiền một phần')
        self.assertAlmostEqual(order_refund_summary(oid)['remaining'],half)
        with self.assertRaises(OrderOperationError):
            confirm_refund_paid(oid,2,half,'cash','',t)
        with self.assertRaises(OrderOperationError):
            confirm_refund_paid(oid,2,unit,'cash','',self.token())
        confirm_refund_paid(oid,2,half,'bank_transfer','TEST123',self.token())
        self.assertEqual(order_refund_summary(oid)['status'],'Đã hoàn tiền')
        self.assertEqual(order_refund_summary(oid)['refunded'],unit)
        self.assertEqual(get_dashboard_stats()['completed_order_value'],unit*2)

    def test_12_cancel_paid_before_shipping_and_refund(self):
        oid=self.order(1)
        before=self.stock()
        confirm_order_stock(oid,2)
        record_order_payment(oid,2)
        cancel_order_stock(oid,2)
        self.assertEqual(self.stock(),before)
        self.assertEqual(get_dashboard_stats()['completed_order_value'],0)
        self.assertAlmostEqual(order_refund_summary(oid)['remaining'],self.unit(oid))
        confirm_refund_paid(oid,2,self.unit(oid),'bank_transfer','TRF-DEMO',self.token())
        self.assertEqual(order_refund_summary(oid)['status'],'Đã hoàn tiền')

    def test_13_cannot_return_pending_order(self):
        oid=self.order(3)
        with self.assertRaises(OrderOperationError):
            receive_completed_return(oid, 2, [(1, 1 + 0)], self.token(), 'Khách trả hàng')

    def test_14_staff_phone_is_required_backend(self):
        csrf=self.login_admin()
        res=self.client.post('/admin/staff/new',data={
            'csrf_token':csrf, 'name':'Nhân viên thử', 'email':'another-staff@example.com',
            'phone':' ', 'password':'Password1234', 'confirm_password':'Password1234'})
        self.assertEqual(res.status_code,200)
        self.assertIsNone(query_one('SELECT MaNguoiDung FROM NguoiDung WHERE Email=?',('another-staff@example.com',)))

    def test_15_admin_resets_password_hashed_only_target(self):
        csrf=self.login_admin()
        before=query_one('SELECT MatKhauHash FROM NguoiDung WHERE MaNguoiDung=1')['MatKhauHash']
        response=self.client.post('/admin/staff/2/reset-password',data={
            'csrf_token':csrf,'password':'ChangedPassword#123','confirm_password':'ChangedPassword#123'})
        self.assertEqual(response.status_code,302)
        after=query_one('SELECT MatKhauHash FROM NguoiDung WHERE MaNguoiDung=2')['MatKhauHash']
        self.assertTrue(check_password_hash(after,'ChangedPassword#123'))
        self.assertFalse(check_password_hash(after,'Demo@12345'))
        self.assertEqual(query_one('SELECT MatKhauHash FROM NguoiDung WHERE MaNguoiDung=1')['MatKhauHash'],before)

    def test_16_staff_cannot_reset_other_staff_password(self):
        self.client.get('/login')
        with self.client.session_transaction() as sess:
            csrf=sess['_csrf']
        self.client.post('/login',data={'csrf_token':csrf,'email':'minh@shop.vn','password':'Demo@12345'})
        self.client.get('/login')
        with self.client.session_transaction() as sess:
            csrf=sess['_csrf']
        self.assertEqual(self.client.post('/admin/staff/2/reset-password',data={
            'csrf_token':csrf,'password':'ChangedPassword#123','confirm_password':'ChangedPassword#123'}).status_code,403)

    def test_17_actual_staff_delete_keeps_order_and_audit(self):
        oid=self.complete()
        csrf=self.login_admin()
        result=self.client.post('/admin/staff/2/delete',data={'csrf_token':csrf})
        self.assertEqual(result.status_code,302)
        self.assertIsNone(query_one('SELECT MaNguoiDung FROM NguoiDung WHERE MaNguoiDung=2'))
        self.assertIsNotNone(query_one('SELECT MaDonHang FROM DonHang WHERE MaDonHang=?',(oid,)))
        archived=query_one('SELECT HoVaTen FROM NhanVienDaXoa WHERE MaNhanVienCu=2')
        self.assertTrue(archived)
        history=query_all("SELECT * FROM NhatKyNhanVienDaXoa WHERE MaNhanVienCu=2 AND Loai='DonHang' AND MaThamChieu=?",(oid,))
        self.assertGreater(len(history),3)
        self.assertEqual(self.client.get('/admin/orders/'+str(oid)).status_code,200)
        from app.db import get_db_connection
        conn=get_db_connection()
        try:
            self.assertEqual(conn.execute('PRAGMA foreign_key_check').fetchall(),[])
        finally:conn.close()

    def test_18_ui_render_returns_and_refund_button(self):
        oid=self.complete()
        csrf=self.login_admin()
        response=self.client.get('/admin/orders/'+str(oid))
        self.assertEqual(response.status_code,200)
        self.assertIn('Xác nhận đã nhận hàng trả'.encode(),response.data)
        receive_completed_return(oid, 2, [(1, 0 + 1)], self.token(), 'Khách trả hàng')
        response=self.client.get('/admin/orders/'+str(oid))
        self.assertIn('Xác nhận ĐÃ HOÀN TIỀN'.encode(),response.data)
        self.assertIn('Hoàn'.encode(),response.data)


if __name__=='__main__':
    unittest.main()
