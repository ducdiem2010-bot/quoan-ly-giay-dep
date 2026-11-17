"""W12: regression for new admin/Seller/customer workflows (SQLite only).

No production database is touched. Run with: python -m unittest discover -s tests -p 'test*.py' -v
"""
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest
from app import create_app


class W12FixLogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dbpath = str(Path(self.tmp.name) / 'w12.sqlite3')
        self.app = create_app({'TESTING': True, 'DB_BACKEND': 'sqlite',
                               'DATABASE': self.dbpath, 'SECRET_KEY': 'w12-test-key',
                               'FORCE_ACCOUNT_STATUS_GUARD': True,
                               'FORCE_LEGACY_ORDER_REDIRECT': True})
        self.c = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def token(self):
        self.c.get('/login')
        with self.c.session_transaction() as s:
            return s['_csrf']

    def login(self, email):
        return self.c.post('/login', data={'csrf_token': self.token(),
                    'email': email, 'password': 'Demo@12345'}, follow_redirects=True)

    def sql(self, statement, params=(), one=False):
        with closing(sqlite3.connect(self.dbpath)) as db:
            result = db.execute(statement, params)
            if statement.lstrip().upper().startswith('SELECT'):
                return result.fetchone() if one else result.fetchall()
            db.commit()

    def test_bug02_legacy_link_redirects_to_connected_orders(self):
        self.login('khach@shop.vn')
        res = self.c.get('/my-orders')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/account/orders', res.location)

    def test_bug03_legacy_form_routes_to_real_w3_form(self):
        self.login('admin@shop.vn')
        self.assertEqual(self.c.get('/admin/product/add').status_code, 302)
        self.assertIn('/admin/products/new', self.c.get('/admin/product/add').location)

    def test_admin_pages_reject_customer(self):
        self.login('khach@shop.vn')
        for path in ('/admin/orders', '/admin/staff', '/admin/customers', '/admin/invoices'):
            with self.subTest(path=path):
                self.assertEqual(self.c.get(path).status_code, 403)

    def test_admin_orders_and_invoices_load(self):
        self.login('admin@shop.vn')
        for path in ('/admin/orders', '/admin/invoices'):
            self.assertEqual(self.c.get(path).status_code, 200)

    def test_admin_search_filters_invalid_status(self):
        self.login('admin@shop.vn')
        self.assertEqual(self.c.get('/admin/orders?status=invalid').status_code, 400)

    def test_staff_created_as_seller_and_hash_is_not_plaintext(self):
        self.login('admin@shop.vn')
        r = self.c.post('/admin/staff/new', data={'csrf_token':self.token(),
            'name':'Nhân viên thử nghiệm', 'email':'seller-w12@example.com',
            'password':'Test12345'}, follow_redirects=False)
        self.assertEqual(r.status_code, 302)
        result = self.sql('SELECT MaVaiTro,MatKhauHash FROM NguoiDung WHERE Email=?',
                          ('seller-w12@example.com',), one=True)
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 2)
        self.assertNotEqual(result[1], 'Test12345')

    def test_customer_cannot_create_staff(self):
        self.login('khach@shop.vn')
        self.assertEqual(self.c.post('/admin/staff/new',
                         data={'csrf_token':self.token(),'name':'A B','email':'a@example.com',
                               'password':'Test12345'}).status_code, 403)

    def test_seller_has_safe_area_but_no_admin_access(self):
        self.login('minh@shop.vn')
        self.assertEqual(self.c.get('/staff').status_code, 200)
        self.assertEqual(self.c.get('/staff/orders').status_code, 200)
        self.assertEqual(self.c.get('/admin/orders').status_code, 403)

    def test_customer_locked_session_is_revoked(self):
        self.login('khach@shop.vn')
        self.sql('UPDATE NguoiDung SET TrangThai=0 WHERE MaNguoiDung=3')
        response=self.c.get('/account')
        self.assertEqual(response.status_code,302)
        self.assertIn('/login',response.location)

    def test_admin_cannot_delete_customer_through_staff_action(self):
        self.login('admin@shop.vn')
        self.assertEqual(self.c.post('/admin/staff/3/delete',
                                    data={'csrf_token':self.token()}).status_code,404)

    def test_product_admin_filter_and_sort(self):
        self.login('admin@shop.vn')
        self.assertEqual(self.c.get('/admin/products?q=Nike&sort=price_asc').status_code,200)
        self.assertEqual(self.c.get('/admin/products?sort=foo').status_code,400)

    def test_cancel_pending_order_owned_by_customer(self):
        self.sql("INSERT INTO DonHang(MaDonHang,MaNguoiDung,TrangThai,TongTien) VALUES(444,3,'Chờ xác nhận',0)")
        original_stock=self.sql('SELECT SUM(SoLuongTon) FROM BienTheSanPham',one=True)[0]
        self.login('khach@shop.vn')
        res=self.c.post('/account/orders/444/cancel',
                        data={'csrf_token':self.token()})
        self.assertEqual(res.status_code,302)
        self.assertEqual(self.sql('SELECT TrangThai FROM DonHang WHERE MaDonHang=444',one=True)[0],'Đã hủy')
        self.assertEqual(original_stock,self.sql('SELECT SUM(SoLuongTon) FROM BienTheSanPham',one=True)[0])

    def test_cannot_cancel_someone_else_order(self):
        self.sql("INSERT INTO DonHang(MaDonHang,MaNguoiDung,TrangThai,TongTien) VALUES(445,1,'Chờ xác nhận',0)")
        self.login('khach@shop.vn')
        self.assertEqual(self.c.post('/account/orders/445/cancel',
                                    data={'csrf_token':self.token()}).status_code,404)
        self.assertEqual(self.sql('SELECT TrangThai FROM DonHang WHERE MaDonHang=445',one=True)[0],'Chờ xác nhận')

    def test_completed_order_cannot_be_cancelled(self):
        self.sql("INSERT INTO DonHang(MaDonHang,MaNguoiDung,TrangThai,TongTien) VALUES(446,3,'Hoàn thành',0)")
        self.login('khach@shop.vn')
        self.c.post('/account/orders/446/cancel',data={'csrf_token':self.token()})
        self.assertEqual(self.sql('SELECT TrangThai FROM DonHang WHERE MaDonHang=446',one=True)[0],'Hoàn thành')


if __name__ == '__main__':
    unittest.main()
