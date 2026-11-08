"""Kiểm thử trang tài khoản khách hàng và thông tin mặc định khi đặt hàng (SQLite demo)."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from app import create_app


class AccountTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.tmp.name) / 'shop.sqlite3')
        self.app = create_app({'TESTING': True, 'DATABASE': self.db, 'SECRET_KEY': 'test-account'})
        self.c = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def token(self):
        self.c.get('/')
        with self.c.session_transaction() as s:
            return s['_csrf']

    def register_login(self, email='an@example.com'):
        t = self.token()
        self.c.post('/register', data=dict(csrf_token=t, full_name='Nguyễn An', email=email, password='matkhau123'))
        r = self.c.post('/login', data=dict(csrf_token=t, email=email, password='matkhau123'))
        self.assertEqual(r.status_code, 302)
        return self.token()

    def profile_form(self, t, **kw):
        d = dict(csrf_token=t, ho='Nguyễn Văn', ten='An', gender='Nam', day='22', month='2', year='2007',
                 province='Hưng Yên', ward='Phường Trà Lý', address='Số 5 đường Test',
                 phone='0943561327', email='an@example.com')
        d.update(kw)
        return d

    def row(self, email='an@example.com'):
        with sqlite3.connect(self.db) as c:
            c.row_factory = sqlite3.Row
            return dict(c.execute('SELECT * FROM NguoiDung WHERE Email=?', (email,)).fetchone())

    def test_account_requires_login(self):
        r = self.c.get('/account')
        self.assertEqual(r.status_code, 302)
        self.assertIn('/login', r.headers['Location'])
        self.assertEqual(self.c.get('/account/orders').status_code, 302)

    def test_save_profile(self):
        t = self.register_login()
        page = self.c.get('/account').get_data(as_text=True)
        self.assertIn('Thông tin cá nhân', page)
        self.assertIn('data-start-editing="1"', page)  # chưa có hồ sơ -> mở sẵn form nhập
        r = self.c.post('/account', data=self.profile_form(t), follow_redirects=True)
        self.assertIn('Đã lưu thông tin tài khoản', r.get_data(as_text=True))
        row = self.row()
        self.assertEqual((row['Ho'], row['Ten'], row['HoVaTen']), ('Nguyễn Văn', 'An', 'Nguyễn Văn An'))
        self.assertEqual((row['GioiTinh'], row['NgaySinh'], row['TinhThanh']), ('Nam', '2007-02-22', 'Hưng Yên'))
        self.assertEqual(row['SoDienThoai'], '0943561327')
        page = self.c.get('/account').get_data(as_text=True)
        self.assertIn('data-start-editing="0"', page)  # đã lưu -> khóa ô, bấm Chỉnh sửa mới sửa
        self.assertIn('value="Phường Trà Lý"', page)

    def test_profile_validation(self):
        t = self.register_login()
        for bad in (dict(ho=''), dict(day='31', month='2'), dict(province='Không có'),
                    dict(phone='12'), dict(email='abc'), dict(gender='X'), dict(year='2999')):
            r = self.c.post('/account', data=self.profile_form(t, **bad))
            self.assertEqual(r.status_code, 200, bad)
            self.assertIn('notice-warning', r.get_data(as_text=True), bad)
        self.assertIsNone(self.row()['TinhThanh'])

    def test_profile_csrf_and_duplicate_email(self):
        t = self.register_login()
        self.assertEqual(self.c.post('/account', data=self.profile_form('sai')).status_code, 400)
        r = self.c.post('/account', data=self.profile_form(t, email='khach@shop.vn'))
        self.assertIn('đã được tài khoản khác', r.get_data(as_text=True))

    def test_checkout_prefill_and_different_info(self):
        t = self.register_login()
        self.c.post('/account', data=self.profile_form(t))
        with self.c.session_transaction() as s:
            s['cart'] = {'1': 1}
        page = self.c.get('/checkout').get_data(as_text=True)
        self.assertIn('value="Nguyễn Văn An"', page)
        self.assertIn('value="0943561327"', page)
        self.assertIn('Số 5 đường Test, Phường Trà Lý, Hưng Yên', page)
        self.assertNotIn('name="save_default" value="1" checked', page)  # đã có mặc định -> không tự ghi đè
        # Khách nhập thông tin khác và KHÔNG tick lưu mặc định -> hồ sơ giữ nguyên.
        r = self.c.post('/checkout', data=dict(csrf_token=t, full_name='Người Nhận Khác', phone='0911111111',
                        email='an@example.com', fulfillment='delivery', address='Địa chỉ khác 99 Hà Nội',
                        payment_method='cod', note=''))
        self.assertEqual(r.status_code, 302)
        row = self.row()
        self.assertEqual((row['HoVaTen'], row['SoDienThoai'], row['DiaChi']), ('Nguyễn Văn An', '0943561327', 'Số 5 đường Test'))

    def test_first_purchase_sets_default(self):
        t = self.register_login()
        with self.c.session_transaction() as s:
            s['cart'] = {'1': 1}
        page = self.c.get('/checkout').get_data(as_text=True)
        self.assertIn('name="save_default" value="1" checked', page)  # lần mua đầu: đề nghị lưu
        r = self.c.post('/checkout', data=dict(csrf_token=t, full_name='Trần Thị Bình', phone='0988777666',
                        email='an@example.com', fulfillment='delivery', address='12 Lê Lợi, Quận 1, TP. Hồ Chí Minh',
                        payment_method='cod', note='', save_default='1'))
        self.assertEqual(r.status_code, 302)
        row = self.row()
        self.assertEqual((row['HoVaTen'], row['Ho'], row['Ten']), ('Trần Thị Bình', 'Trần Thị', 'Bình'))
        self.assertEqual((row['SoDienThoai'], row['DiaChi'], row['Email']), ('0988777666', '12 Lê Lợi, Quận 1, TP. Hồ Chí Minh', 'an@example.com'))
        # lần mua sau đã điền sẵn
        with self.c.session_transaction() as s:
            s['cart'] = {'1': 1}
        page = self.c.get('/checkout').get_data(as_text=True)
        self.assertIn('value="0988777666"', page)

    def test_orders_tab_lists_user_orders(self):
        t = self.register_login()
        self.assertIn('chưa có đơn hàng', self.c.get('/account/orders').get_data(as_text=True))
        with self.c.session_transaction() as s:
            s['cart'] = {'1': 2}
        self.c.post('/checkout', data=dict(csrf_token=t, full_name='Nguyễn An', phone='0912345678', email='',
                    fulfillment='pickup', address='', payment_method='cod', note=''))
        page = self.c.get('/account/orders').get_data(as_text=True)
        self.assertIn('Chờ xác nhận', page)
        self.assertIn('× 2', page)

    def test_guest_checkout_has_login_hint(self):
        with self.c.session_transaction() as s:
            s['cart'] = {'1': 1}
        page = self.c.get('/checkout').get_data(as_text=True)
        self.assertIn('Đăng nhập</a> để tự động điền', page)
        self.assertNotIn('save_default', page)


if __name__ == '__main__':
    unittest.main()
