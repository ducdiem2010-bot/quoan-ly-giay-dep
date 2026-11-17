"""Nghiệp vụ trả hàng v3: kiểm thử trên SQLite tạm, không sửa dữ liệu người dùng."""
import unittest
import threading
from uuid import uuid4
import test_returns_refunds_staff_v2 as base
from app.db import get_db_connection, query_one, query_all
from app.services.return_refunds import receive_completed_return, confirm_refund_paid, order_refund_summary
from app.services.order_ops import OrderOperationError, confirm_order_stock, start_order_shipping, mark_order_delivered, record_order_payment, complete_order_status
from app.services.checkout import create_pending_order

class SimpleReturnsTests(unittest.TestCase):
    setUp=base.ReturnsRefundsStaffTests.setUp
    tearDown=base.ReturnsRefundsStaffTests.tearDown
    order=base.ReturnsRefundsStaffTests.order
    complete=base.ReturnsRefundsStaffTests.complete
    unit=base.ReturnsRefundsStaffTests.unit
    stock=base.ReturnsRefundsStaffTests.stock
    login_admin=base.ReturnsRefundsStaffTests.login_admin
    token=base.ReturnsRefundsStaffTests.token

    def post_return(self, oid, qty='1', **extra):
        csrf=self.login_admin()
        data={'csrf_token':csrf,'request_token':uuid4().hex,'qty_1':qty,'reason':'Không vừa chân'}
        data.update(extra)
        return self.client.post(f'/orders/{oid}/receive-return',data=data,follow_redirects=True)

    def test_server_price_ignores_forged_amount(self):
        oid=self.complete(); unit=self.unit(oid); stock=self.stock()
        conn=get_db_connection(); conn.execute('UPDATE SanPham SET GiaBan=99 WHERE MaSanPham=1');conn.commit();conn.close()
        res=self.post_return(oid,refund_1='0',price='1',bad_1='999')
        self.assertEqual(res.status_code,200)
        self.assertEqual(order_refund_summary(oid)['approved'],unit)
        self.assertEqual(self.stock(),stock+1)
        self.assertIn('Xác nhận ĐÃ HOÀN TIỀN',res.get_data(as_text=True))
        self.assertIn('data-reopen="0"',res.get_data(as_text=True))

    def test_invalid_quantities_and_reason_keep_form_without_mutation(self):
        oid=self.complete(); stock=self.stock()
        for qty,reason in [('-1','abc'),('1.5','abc'),('4','abc'),('0','abc'),('1','   ')]:
            res=self.post_return(oid,qty,reason=reason)
            self.assertEqual(res.status_code,200)
            self.assertIn('data-reopen="1"',res.get_data(as_text=True))
            self.assertEqual(self.stock(),stock)
            self.assertEqual(order_refund_summary(oid)['approved'],0)

    def test_non_completed_and_foreign_variants_rejected(self):
        oid=self.order(); before=self.stock()
        self.post_return(oid)
        self.assertEqual(self.stock(),before)
        confirm_order_stock(oid,2);start_order_shipping(oid,2)
        self.post_return(oid)
        self.assertFalse(query_all('SELECT * FROM TraHangChiTiet WHERE MaDonHang=?',(oid,)))
        oid2=self.complete()
        self.post_return(oid2,'0',qty_99999='1')
        self.assertEqual(order_refund_summary(oid2)['approved'],0)

    def test_partial_full_history_and_refund_no_second_stock(self):
        oid=self.complete(); unit=self.unit(oid); before=self.stock()
        receive_completed_return(oid,2,[(1,1)],self.token(),'Đổi ý')
        receive_completed_return(oid,2,[(1,2)],self.token(),'Không vừa')
        self.assertEqual(self.stock(),before+3)
        confirm_refund_paid(oid,2,unit*3,'cash','',self.token())
        self.assertEqual(self.stock(),before+3)
        self.assertEqual(order_refund_summary(oid)['net_revenue'],0)
        with self.client.session_transaction() as sess:sess['user_id']=3;sess['role']='Customer'
        page=self.client.get('/account/orders').get_data(as_text=True)
        for text in ['Trả toàn bộ','Đổi ý','Không vừa','Đã hoàn tiền','Lịch sử trả hàng']:
            self.assertIn(text,page)
        self.assertNotIn('Nhật ký xử lý',page)

    def test_permissions_and_password_routes(self):
        oid=self.complete()
        for role,uid in [('Customer',3),('Seller',2)]:
            with self.client.session_transaction() as sess:sess['user_id']=uid;sess['role']=role
            self.client.get('/account')
            with self.client.session_transaction() as sess:csrf=sess['_csrf']
            self.assertEqual(self.client.get('/account/change-password').status_code,403)
            self.assertEqual(self.client.post('/account/change-password',data={'csrf_token':csrf}).status_code,403)
            self.assertEqual(self.client.get('/admin/staff/2/reset-password').status_code,403)
            if role=='Customer':
                for action in ['receive-return','refund-paid']:
                    self.assertEqual(self.client.post(f'/orders/{oid}/{action}',data={'csrf_token':csrf}).status_code,403)
                self.assertEqual(self.client.get(f'/staff/orders/{oid}').status_code,403)
        self.login_admin()
        self.assertEqual(self.client.get('/admin/staff/2/reset-password').status_code,200)

    def test_other_customer_cannot_see_order_history(self):
        oid=self.complete(); receive_completed_return(oid,2,[(1,1)],self.token(),'PRIVATE-RETURN-REASON')
        conn=get_db_connection()
        conn.execute("INSERT INTO NguoiDung (HoVaTen,Email,MatKhauHash,MaVaiTro) VALUES ('Other','other@test.local','x',3)")
        uid=conn.execute("SELECT MaNguoiDung FROM NguoiDung WHERE Email='other@test.local'").fetchone()[0];conn.commit();conn.close()
        with self.client.session_transaction() as sess:sess['user_id']=uid;sess['role']='Customer'
        self.assertNotIn('PRIVATE-RETURN-REASON',self.client.get('/account/orders').get_data(as_text=True))

    def test_demo_rejected_and_legacy_demo_not_counted(self):
        oid=self.complete(); unit=self.unit(oid)
        receive_completed_return(oid,2,[(1,1)],self.token(),'Trả hàng')
        with self.assertRaises(OrderOperationError):confirm_refund_paid(oid,2,unit,'demo','',self.token())
        conn=get_db_connection();conn.execute("INSERT INTO HoanTienGiaoDich (MaDonHang,SoTien,PhuongThuc,NguoiXacNhan,HoVaTenNguoiXacNhan,MaYeuCau) VALUES (?,?,'demo',2,'Old demo',?)",(oid,unit,self.token()));conn.commit();conn.close()
        self.assertEqual(order_refund_summary(oid)['remaining'],unit)
        self.assertEqual(order_refund_summary(oid)['refunded'],0)

    def test_atomic_rollback_on_stock_update_failure(self):
        oid=self.complete(); before=self.stock()
        conn=get_db_connection();conn.execute("CREATE TRIGGER fail_stock BEFORE UPDATE OF SoLuongTon ON BienTheSanPham BEGIN SELECT RAISE(ABORT,'injected failure'); END");conn.commit();conn.close()
        with self.assertRaises(Exception):receive_completed_return(oid,2,[(1,1)],self.token(),'Trả hàng')
        self.assertEqual(self.stock(),before)
        self.assertFalse(query_all('SELECT * FROM TraHangChiTiet WHERE MaDonHang=?',(oid,)))

    def test_concurrent_full_returns_only_one_commits(self):
        oid=self.complete(); before=self.stock(); result=[]
        def worker():
            with self.app.app_context():
                try:receive_completed_return(oid,2,[(1,3)],uuid4().hex,'Trả toàn bộ');result.append('ok')
                except OrderOperationError:result.append('rejected')
        threads=[threading.Thread(target=worker) for _ in range(2)]
        for t in threads:t.start()
        for t in threads:t.join()
        self.assertCountEqual(result,['ok','rejected'])
        self.assertEqual(self.stock(),before+3)

    def test_multiple_products_prices_and_duplicate_request(self):
        oid=create_pending_order({'full_name':'Test','phone':'0981234567','email':'a@test.vn','fulfillment':'delivery','address':'HN','payment_method':'bank_transfer','note':''},{1:2,3:1},user_id=3)
        confirm_order_stock(oid,2);start_order_shipping(oid,2);mark_order_delivered(oid,2);record_order_payment(oid,2);complete_order_status(oid,2)
        expected=sum(float(r['DonGia']) for r in query_all('SELECT DonGia FROM ChiTietDonHang WHERE MaDonHang=?',(oid,)))
        token=self.token();receive_completed_return(oid,2,[(1,1),(3,1)],token,'Trả hai sản phẩm')
        self.assertEqual(order_refund_summary(oid)['approved'],expected)
        with self.assertRaises(OrderOperationError):receive_completed_return(oid,2,[(1,1),(3,1)],token,'Lặp')
        self.assertEqual(len(query_all('SELECT * FROM TraHangChiTiet WHERE MaDonHang=?',(oid,))),2)

    def test_legacy_damaged_record_unchanged(self):
        oid=self.complete();before=self.stock()
        conn=get_db_connection();conn.execute("INSERT INTO TraHangChiTiet (MaDonHang,MaBienThe,SoLuong,SoLuongTot,SoLuongHong,LyDo,TienGiamDoanhThu,NguoiThucHien,HoVaTenNguoiThucHien,MaYeuCau) VALUES (?,1,1,0,1,'Old damaged',0,2,'Old staff',?)",(oid,self.token()));conn.commit();conn.close()
        self.login_admin();self.client.get(f'/admin/orders/{oid}')
        self.assertEqual(self.stock(),before)
        receive_completed_return(oid,2,[(1,1)],self.token(),'Lần mới')
        self.assertEqual(self.stock(),before+1)
        row=query_one("SELECT SoLuongHong,SoLuongTot,TienGiamDoanhThu FROM TraHangChiTiet WHERE LyDo='Old damaged'")
        self.assertEqual(tuple(row.values()),(1,0,0))
