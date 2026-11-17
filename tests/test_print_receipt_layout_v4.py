"""Regression checks for invoices, receipts and display. Requires Flask app test client.
All writes are to a TEMP SQLite database via the inherited setup.
"""
import unittest
from uuid import uuid4
import test_returns_refunds_staff_v2 as base
from app.db import get_db_connection, query_all, query_one
from app.services.return_refunds import (
    receive_completed_return, confirm_refund_paid, list_completed_returns,
    group_return_receipts, order_refund_summary,
)
from app.services.time_display import format_vn, format_audit_log
from app.services.checkout import create_pending_order
from app.services.order_ops import (
    confirm_order_stock, start_order_shipping, mark_order_delivered,
    record_order_payment, complete_order_status,
)


class PrintReceiptLayoutV4(unittest.TestCase):
    setUp = base.ReturnsRefundsStaffTests.setUp
    tearDown = base.ReturnsRefundsStaffTests.tearDown
    order = base.ReturnsRefundsStaffTests.order
    complete = base.ReturnsRefundsStaffTests.complete
    unit = base.ReturnsRefundsStaffTests.unit
    stock = base.ReturnsRefundsStaffTests.stock
    login_admin = base.ReturnsRefundsStaffTests.login_admin
    token = base.ReturnsRefundsStaffTests.token

    def get_admin(self, oid):
        self.login_admin()
        response = self.client.get(f'/admin/orders/{oid}')
        self.assertEqual(response.status_code, 200)
        return response.get_data(as_text=True)

    def test_detail_css_inherits_parent_and_does_not_repeat(self):
        oid = self.complete()
        html = self.get_admin(oid)
        for css in ('w12_admin.css', 'admin_theme.css', 'order_detail_polish.css'):
            self.assertEqual(html.count('css/' + css), 1, css)
        self.assertIn('admin-sidebar', html)
        other = self.client.get('/admin/orders').get_data(as_text=True)
        self.assertIn('css/admin_theme.css', other)
        self.assertNotIn('css/order_detail_polish.css', other)

    def test_staff_css_and_staff_order_page(self):
        oid = self.complete()
        with self.client.session_transaction() as sess:
            sess['user_id'] = 2
            sess['role'] = 'Seller'
        response = self.client.get(f'/staff/orders/{oid}')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('css/w12_admin.css', html)
        self.assertIn('css/order_detail_polish.css', html)
        self.assertEqual(self.client.get('/staff/orders').status_code, 200)

    def test_return_refund_labels_all_three_lists(self):
        oid = self.complete()
        self.login_admin()
        listing = self.client.get('/admin/orders').get_data(as_text=True)
        self.assertIn('Chưa trả hàng', listing)
        receive_completed_return(oid, 2, [(1, 1)], self.token(), 'Một đôi')
        for path in ('/admin/orders', '/staff/orders', '/admin/customers/3/orders'):
            if path.startswith('/staff'):
                with self.client.session_transaction() as sess:
                    sess['user_id'] = 2
                    sess['role'] = 'Seller'
            else:
                self.login_admin()
            html = self.client.get(path).get_data(as_text=True)
            self.assertIn('Trả một phần', html)
            self.assertIn('Chờ hoàn tiền', html)
            self.assertIn('Phải hoàn:', html)
        receive_completed_return(oid, 2, [(1, 2)], self.token(), 'Hai đôi')
        self.login_admin()
        html = self.client.get('/admin/orders').get_data(as_text=True)
        self.assertIn('Trả toàn bộ', html)
        confirm_refund_paid(oid, 2, self.unit(oid), 'cash', '', self.token())
        html = self.client.get('/admin/orders').get_data(as_text=True)
        self.assertIn('Hoàn tiền một phần', html)

    def test_slow_label_full_return_not_never_completed(self):
        oid = self.complete()
        receive_completed_return(oid, 2, [(1, 3)], self.token(), 'Trả hết')
        self.login_admin()
        html = self.client.get('/admin/slow-products?days=30').get_data(as_text=True)
        self.assertIn('Đã bán nhưng đã trả toàn bộ', html)

    def test_datetime_all_sources_once_and_legacy_audit(self):
        self.assertEqual(format_vn('2026-11-16 16:00:00'), '16/11/2026 23:00')
        self.assertEqual(format_vn('2026-11-16T16:00:00+00:00'), '16/11/2026 23:00')
        self.assertEqual(format_audit_log('[2026-11-16T16:00:00+00:00] x'),
                         '[16/11/2026 23:00] x')
        self.assertIn('chưa xác định múi giờ', format_audit_log('[2026-11-16 16:00:00] cũ'))

    def test_sale_stays_original_after_return(self):
        oid = self.complete()
        unit = self.unit(oid)
        receive_completed_return(oid, 2, [(1, 1)], self.token(), 'Mua nhầm size')
        self.login_admin()
        html = self.client.get(f'/orders/{oid}/print/sale').get_data(as_text=True)
        self.assertIn('HÓA ĐƠN BÁN HÀNG', html)
        self.assertIn('Chi tiết sản phẩm mua ban đầu', html)
        self.assertIn('Số lượng và tổng tiền ở đây là dữ liệu mua ban đầu', html)
        self.assertIn(f'{3*unit:,.0f}'.replace(',', '.'), html)

    def test_multi_line_return_one_receipt_and_no_other_receipt(self):
        oid = create_pending_order({'full_name':'Test','phone':'0981234567','email':'a@test.vn',
            'fulfillment':'delivery','address':'HN','payment_method':'bank_transfer','note':''},
            {1:2,3:1},user_id=3)
        confirm_order_stock(oid,2)
        start_order_shipping(oid,2)
        mark_order_delivered(oid,2)
        record_order_payment(oid,2)
        complete_order_status(oid,2)
        receive_completed_return(oid,2,[(1,1),(3,1)],self.token(),'Hai biến thể')
        groups=group_return_receipts(list_completed_returns(oid))
        self.assertEqual(len(groups),1)
        self.assertEqual(len(groups[0]['lines']),2)
        self.login_admin()
        url=f"/orders/{oid}/returns/{groups[0]['receipt_id']}/print"
        html=self.client.get(url).get_data(as_text=True)
        self.assertIn('PHIẾU TRẢ HÀNG', html)
        self.assertIn('Hai biến thể', html)
        self.assertIn('Chờ hoàn tiền', html)
        self.assertIn('theo TỔNG ĐƠN', html)
        receive_completed_return(oid,2,[(1,1)],self.token(),'Lần khác')
        groups=group_return_receipts(list_completed_returns(oid))
        self.assertEqual(len(groups),2)
        newer=self.client.get(f"/orders/{oid}/returns/{groups[0]['receipt_id']}/print").get_data(as_text=True)
        self.assertIn('Lần khác', newer)
        self.assertNotIn('Hai biến thể', newer)

    def test_legacy_without_group_not_auto_combined(self):
        oid=self.complete()
        receive_completed_return(oid,2,[(1,1)],self.token(),'Lần mới')
        conn=get_db_connection()
        try:
            conn.execute("UPDATE TraHangChiTiet SET MaNhomTra=NULL WHERE MaDonHang=?",(oid,))
            conn.commit()
        finally:
            conn.close()
        groups=group_return_receipts(list_completed_returns(oid))
        self.assertEqual(len(groups),1)
        self.assertTrue(groups[0]['legacy_unverified'])

    def test_refund_print_single_transaction_and_demo_disallowed(self):
        oid=self.complete()
        unit=self.unit(oid)
        receive_completed_return(oid,2,[(1,2)],self.token(),'Hai đôi')
        confirm_refund_paid(oid,2,unit,'cash','cash-01',self.token())
        confirm_refund_paid(oid,2,unit,'bank_transfer','bank-02',self.token())
        conn=get_db_connection()
        try:
            conn.execute("INSERT INTO HoanTienGiaoDich(MaDonHang,SoTien,PhuongThuc,HoVaTenNguoiXacNhan,MaYeuCau) VALUES (?,?,'demo','Old',?)",
                         (oid,100,self.token()))
            conn.commit()
        finally:
            conn.close()
        self.login_admin()
        records=query_all('SELECT MaHoanTien,PhuongThuc FROM HoanTienGiaoDich WHERE MaDonHang=? ORDER BY MaHoanTien',(oid,))
        for rec in records:
            response=self.client.get(f"/orders/{oid}/refunds/{rec['MaHoanTien']}/print")
            if rec['PhuongThuc']=='demo':
                self.assertEqual(response.status_code,404)
            else:
                self.assertEqual(response.status_code,200)
                html=response.get_data(as_text=True)
                self.assertIn(f"#{rec['MaHoanTien']}",html)
                self.assertIn('Số tiền của GIAO DỊCH NÀY',html)

    def test_print_is_read_only_even_after_many_views(self):
        oid=self.complete()
        receive_completed_return(oid,2,[(1,1)],self.token(),'Trả lần một')
        receipt=group_return_receipts(list_completed_returns(oid))[0]
        before=(self.stock(), query_one('SELECT COUNT(*) AS n FROM TraHangChiTiet WHERE MaDonHang=?',(oid,))['n'],
                order_refund_summary(oid))
        self.login_admin()
        for _ in range(3):
            self.assertEqual(self.client.get(f'/orders/{oid}/print/sale').status_code,200)
            self.assertEqual(self.client.get(f"/orders/{oid}/returns/{receipt['receipt_id']}/print").status_code,200)
        after=(self.stock(), query_one('SELECT COUNT(*) AS n FROM TraHangChiTiet WHERE MaDonHang=?',(oid,))['n'],
               order_refund_summary(oid))
        self.assertEqual(before,after)

    def test_print_not_accessible_to_customers_or_guests(self):
        oid=self.complete()
        for role,uid in [('Customer',3),('Seller',2)]:
            with self.client.session_transaction() as sess:
                sess['user_id']=uid
                sess['role']=role
            response=self.client.get(f'/orders/{oid}/print/sale')
            self.assertEqual(response.status_code,403 if role=='Customer' else 200)
        with self.client.session_transaction() as sess:
            sess.clear()
        response=self.client.get(f'/orders/{oid}/print/sale')
        self.assertIn(response.status_code,(302,401))

    def test_print_css_pagination(self):
        from pathlib import Path
        css=(Path(__file__).resolve().parents[1]/'app/static/css/order_print.css').read_text(encoding='utf-8')
        for needle in ('@page', 'A4 portrait', 'display:table-header-group', 'break-inside:avoid', '.print-toolbar{display:none'):
            self.assertIn(needle,css)

if __name__=='__main__':
    unittest.main()
