"""Kiểm thử nút Mua ngay: đi thẳng tới thanh toán, không thêm vào giỏ hàng."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from app import create_app


class BuyNowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.tmp.name) / 'shop.sqlite3')
        self.app = create_app({'TESTING': True, 'DATABASE': self.db, 'SECRET_KEY': 'test-buy-now'})
        self.c = self.app.test_client()
        self.c.get('/')
        with self.c.session_transaction() as s:
            self.t = s['_csrf']

    def tearDown(self):
        self.tmp.cleanup()

    def buy(self, **kw):
        d = dict(csrf_token=self.t, variant_id='1', quantity='2')
        d.update(kw)
        return self.c.post('/buy-now/1', data=d)

    def order_form(self, **kw):
        d = dict(csrf_token=self.t, buy_now='1', full_name='Nguyễn Mua Ngay', phone='0912345678', email='',
                 fulfillment='delivery', address='Số 1 đường Test, Hà Nội', payment_method='cod', note='')
        d.update(kw)
        return d

    def test_product_page_has_both_buttons(self):
        page = self.c.get('/product/1').get_data(as_text=True)
        self.assertIn('Thêm vào giỏ hàng', page)
        self.assertIn('Mua ngay', page)
        self.assertIn('formaction="/buy-now/1"', page)

    def test_buy_now_goes_to_checkout_without_touching_cart(self):
        with self.c.session_transaction() as s:
            s['cart'] = {'2': 1}
        r = self.buy()
        self.assertEqual(r.status_code, 302)
        self.assertIn('/checkout?buy_now=1', r.headers['Location'])
        with self.c.session_transaction() as s:
            self.assertEqual(s['cart'], {'2': 1})
        page = self.c.get('/checkout?buy_now=1').get_data(as_text=True)
        self.assertIn('Sản phẩm mua ngay', page)
        self.assertIn('× 2', page)
        self.assertIn('name="buy_now" value="1"', page)

    def test_buy_now_works_with_empty_cart_and_no_login(self):
        self.buy()
        r = self.c.post('/checkout', data=self.order_form())
        self.assertEqual(r.status_code, 302)
        self.assertIn('/checkout/success', r.headers['Location'])
        with sqlite3.connect(self.db) as c:
            n = c.execute('SELECT COUNT(*) FROM ChiTietDonHang WHERE MaBienThe=1 AND SoLuong=2 AND MaDonHang=(SELECT MAX(MaDonHang) FROM DonHang)').fetchone()[0]
        self.assertEqual(n, 1)

    def test_cart_kept_after_buy_now_order(self):
        with self.c.session_transaction() as s:
            s['cart'] = {'2': 1}
        self.buy()
        self.c.post('/checkout', data=self.order_form())
        with self.c.session_transaction() as s:
            self.assertEqual(s['cart'], {'2': 1})
            self.assertNotIn('buy_now', s)
        page = self.c.get('/checkout').get_data(as_text=True)  # checkout thường vẫn là giỏ hàng
        self.assertIn('Thông tin giỏ hàng', page)

    def test_normal_checkout_ignores_buy_now_session(self):
        with self.c.session_transaction() as s:
            s['cart'] = {'2': 1}
        self.buy()
        page = self.c.get('/checkout').get_data(as_text=True)
        self.assertIn('Thông tin giỏ hàng', page)
        self.assertNotIn('Sản phẩm mua ngay', page)

    def test_buy_now_validation(self):
        self.assertEqual(self.buy(quantity='0').status_code, 400)
        self.assertEqual(self.buy(quantity='abc').status_code, 400)
        self.assertEqual(self.buy(variant_id='99999').status_code, 400)
        self.assertEqual(self.c.post('/buy-now/1', data=dict(variant_id='1', quantity='1')).status_code, 400)  # thiếu CSRF
        self.assertEqual(self.c.post('/buy-now/9999', data=dict(csrf_token=self.t, variant_id='1')).status_code, 404)
        r = self.buy(quantity='99')  # vượt tồn kho
        self.assertEqual(r.status_code, 302)
        self.assertIn('/product/1', r.headers['Location'])

    def test_checkout_without_any_basket_redirects_to_cart(self):
        r = self.c.get('/checkout?buy_now=1')
        self.assertEqual(r.status_code, 302)
        self.assertIn('/cart', r.headers['Location'])


if __name__ == '__main__':
    unittest.main()


class BuyNowLoginTests(BuyNowTests):
    """Khách chưa đăng nhập bấm Mua ngay rồi đăng nhập: không được mất sản phẩm."""
    def test_login_keeps_buy_now_and_query(self):
        self.c.post('/register', data=dict(csrf_token=self.t, full_name='Khách Mới', email='moi@example.com', password='matkhau123'))
        self.buy()
        r = self.c.post('/login', data=dict(csrf_token=self.t, email='moi@example.com', password='matkhau123',
                                            next='/checkout?buy_now=1'))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.headers['Location'], '/checkout?buy_now=1')
        with self.c.session_transaction() as s:
            self.assertEqual(s['buy_now'], {'1': 2})
        page = self.c.get('/checkout?buy_now=1').get_data(as_text=True)
        self.assertIn('Sản phẩm mua ngay', page)
        self.assertIn('Khách Mới', page)  # đã đăng nhập nên điền sẵn tên

    def test_header_login_form_keeps_query_in_next(self):
        self.buy()
        page = self.c.get('/checkout?buy_now=1').get_data(as_text=True)
        self.assertIn('name="next" value="/checkout?buy_now=1"', page)
