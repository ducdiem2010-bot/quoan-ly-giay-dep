"""W13 Tuấn: các kiểm thử HTTP/chỉ chạy khi Flask được cài trên máy dev.
Fixture SQLite tạm, không sử dụng hay xóa database thực của người dùng.
"""
from pathlib import Path
import sqlite3
import tempfile
import unittest
from app import create_app


class W13HttpIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dbpath = str(Path(self.tmp.name) / 'w13_http.sqlite3')
        self.app = create_app({'TESTING': True, 'DB_BACKEND':'sqlite', 'DATABASE':self.dbpath,
                               'SECRET_KEY':'W13-integration-test-dev-only',
                               'FORCE_ACCOUNT_STATUS_GUARD':True})
        self.client = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def login_as(self, uid=3, role='Customer'):
        self.client.get('/login')
        with self.client.session_transaction() as s:
            s['user_id'] = uid
            s['role'] = role
            s['user_name'] = 'Test W13'
            s.setdefault('cart', {})

    def csrf(self):
        self.client.get('/cart')
        with self.client.session_transaction() as s:
            return s['_csrf']

    def count_orders(self):
        with sqlite3.connect(self.dbpath) as conn:
            return conn.execute('SELECT COUNT(*) FROM DonHang').fetchone()[0]

    def test_routes_registered(self):
        names = set(self.app.view_functions)
        self.assertTrue({'w13_tuan.timeline',
                         'w13_tuan.recent_products','w13_tuan.recently_viewed_page'} <= names)

    def test_product_detail_renders_w13_widget(self):
        res = self.client.get('/product/1')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn('data-w13-view-product="1"', html)
        self.assertIn('w13_recently_viewed.js', html)
        self.assertIn('w13_customer_ux.css', html)
        self.assertIn('Sản phẩm vừa xem', html)

    def test_recent_page_and_api_only_visible_products(self):
        self.assertEqual(self.client.get('/w13/recently-viewed').status_code, 302)
        self.login_as()
        page = self.client.get('/w13/recently-viewed')
        self.assertEqual(page.status_code, 200)
        self.assertIn('w13_recently_viewed.js', page.get_data(as_text=True))
        res = self.client.get('/w13/recent-products?ids=1,12,999,abc')
        self.assertEqual(res.status_code, 200)
        ids = [p['id'] for p in res.get_json()['products']]
        self.assertEqual(ids, [1])

    def test_customer_history_links_and_account_css(self):
        self.login_as()
        res = self.client.get('/account/orders')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn('css/account.css', html)
        self.assertIn('css/w13_customer_ux.css', html)
        self.assertNotIn('Chọn sản phẩm mua lại', html)
        self.assertIn('href="/product/1"', html)
        self.assertNotIn('add-to-cart', html)
        self.assertNotIn('Bấm để thêm 1 đôi vào giỏ', html)
        self.assertIn('w13-bought-photo', html)
        self.assertIn('/w13/orders/1/timeline', html)
        self.assertIn('Lịch sử đơn hàng', html)
        self.assertIn('Sản phẩm vừa xem', html)  # tab tài khoản, không phải liên kết trong phần danh sách đơn
        self.assertNotIn('w13-history-link">Sản phẩm vừa xem', html)
        profile = self.client.get('/account')
        self.assertEqual(profile.status_code, 200)
        self.assertIn('Xem lịch sử sản phẩm vừa xem', profile.get_data(as_text=True))

    def test_timeline_customer_order(self):
        self.login_as()
        timeline = self.client.get('/w13/orders/1/timeline')
        self.assertEqual(timeline.status_code, 200)
        self.assertIn('Tiến trình đơn #1', timeline.get_data(as_text=True))

    def test_guest_and_admin_cannot_access_customer_timeline(self):
        self.assertEqual(self.client.get('/w13/orders/1/timeline').status_code, 401)
        self.login_as(1, 'Admin')
        self.assertEqual(self.client.get('/w13/orders/1/timeline').status_code, 403)
        self.assertNotIn('add-to-cart', self.client.get('/account/orders').get_data(as_text=True))

    def test_missing_and_other_owner_order(self):
        self.login_as()
        self.assertEqual(self.client.get('/w13/orders/999/timeline').status_code, 404)
        with sqlite3.connect(self.dbpath) as c:
            c.execute("INSERT INTO DonHang (MaDonHang, MaNguoiDung, TrangThai) VALUES (901, 1, 'Chờ xác nhận')")
            c.commit()
        self.assertEqual(self.client.get('/w13/orders/901/timeline').status_code, 403)

    def test_direct_reorder_endpoints_removed(self):
        self.login_as()
        self.assertNotIn('w13_tuan.reorder', self.app.view_functions)
        self.assertNotIn('w13_tuan.add_order_item_to_cart', self.app.view_functions)
        self.assertEqual(self.client.get('/w13/orders/1/reorder').status_code, 404)
        self.assertEqual(self.client.post('/w13/orders/1/reorder').status_code, 404)

    def test_history_product_click_is_get_only_and_never_changes_cart(self):
        self.login_as()
        before = self.count_orders()
        self.assertEqual(self.client.get('/account/orders').status_code, 200)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get('cart'), {})
            self.assertNotIn('_w13_order_add_token', sess)
        detail = self.client.get('/product/1')
        self.assertEqual(detail.status_code, 200)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get('cart'), {})
        self.assertEqual(self.count_orders(), before)
        self.assertNotIn('w13_tuan.add_order_item_to_cart', self.app.view_functions)

    def test_history_product_link_hidden_and_out_of_stock(self):
        self.login_as()
        with sqlite3.connect(self.dbpath) as conn:
            conn.execute('UPDATE BienTheSanPham SET SoLuongTon=0 WHERE MaBienThe=1')
            conn.commit()
        out = self.client.get('/account/orders').get_data(as_text=True)
        self.assertIn('href="/product/1"', out)  # Hết hàng vẫn được xem chi tiết
        with sqlite3.connect(self.dbpath) as conn:
            conn.execute('UPDATE SanPham SET HienThi=0 WHERE MaSanPham=1')
            conn.commit()
        hidden = self.client.get('/account/orders').get_data(as_text=True)
        self.assertNotIn('href="/product/1"', hidden)
        self.assertIn('Sản phẩm không còn hiển thị', hidden)

    def test_other_order_flow_not_broken(self):
        self.login_as()
        self.assertEqual(self.client.get('/cart').status_code,200)
        self.assertEqual(self.client.get('/product/1').status_code,200)


if __name__=='__main__':
    unittest.main()
