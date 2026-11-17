"""Kiểm thử tích hợp W11 (SQLite demo). Chạy: python -m unittest tests/test_w11_upgrade.py -v.

Các assert về URL/HTML và dữ liệu thực dùng Flask test client, không thay thế
bằng việc chỉ kiểm tra có file/chuỗi trong code.
"""
import sqlite3
from contextlib import closing
import tempfile
import unittest
from pathlib import Path
from app import create_app


class W11UpgradeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / 'test.sqlite3')
        self.app = create_app({'TESTING': True, 'DATABASE': self.db_path,
                               'SECRET_KEY': 'w11-unit-test-secret', 'DB_BACKEND': 'sqlite'})
        self.client = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def login(self, email, password='Demo@12345'):
        self.client.get('/login')
        with self.client.session_transaction() as sess:
            token = sess['_csrf']
        return self.client.post('/login', data={'csrf_token': token, 'email': email,
                                                'password': password}, follow_redirects=True)

    def test_admin_features_require_admin(self):
        for path in ('/admin/product-health', '/admin/slow-products'):
            self.assertEqual(self.client.get(path).status_code, 302)
        self.login('khach@shop.vn')
        for path in ('/admin/product-health', '/admin/slow-products'):
            self.assertEqual(self.client.get(path).status_code, 403)

    def test_quality_report_shows_legitimate_review_and_is_read_only(self):
        self.login('admin@shop.vn')
        with closing(sqlite3.connect(self.db_path)) as db, db:
            before = db.execute('SELECT SUM(SoLuongTon) FROM BienTheSanPham').fetchone()[0]
        page = self.client.get('/admin/product-health')
        self.assertEqual(page.status_code, 200)
        self.assertIn('Trung tâm kiểm tra sản phẩm', page.get_data(as_text=True))
        self.assertIn('Sandal Học Sinh Chống Trượt', page.get_data(as_text=True))
        with closing(sqlite3.connect(self.db_path)) as db, db:
            after = db.execute('SELECT SUM(SoLuongTon) FROM BienTheSanPham').fetchone()[0]
        self.assertEqual(before, after)

    def test_quality_report_detects_missing_uploaded_image(self):
        with closing(sqlite3.connect(self.db_path)) as db, db:
            db.execute("INSERT INTO SanPhamHinhAnh(MaSanPham,TenTep,LaAnhDaiDien,ThuTu) VALUES (1,'missing-w11.jpg',1,0)")
        self.login('admin@shop.vn')
        page = self.client.get('/admin/product-health')
        self.assertEqual(page.status_code, 200)
        self.assertIn('Tệp ảnh tải lên không tồn tại', page.get_data(as_text=True))

    def test_slow_sellers_filter_and_valid_days(self):
        self.login('admin@shop.vn')
        for days in (7, 30, 90):
            page = self.client.get(f'/admin/slow-products?days={days}')
            self.assertEqual(page.status_code, 200)
            self.assertIn('Sản phẩm bán chậm', page.get_data(as_text=True))
        self.assertEqual(self.client.get('/admin/slow-products?days=999').status_code, 400)
        self.assertEqual(self.client.get('/admin/slow-products?sort=DROP').status_code, 400)
        page = self.client.get('/admin/slow-products?q=Converse&only_zero=1')
        self.assertIn('Converse Chuck Taylor', page.get_data(as_text=True))
        self.assertNotIn('Nike Air Zoom Pegasus', page.get_data(as_text=True))

    def test_slow_sellers_exclude_product_with_3_completed_sales(self):
        with closing(sqlite3.connect(self.db_path)) as db, db:
            db.execute("UPDATE DonHang SET TrangThai='Hoàn thành',NgayDat=CURRENT_TIMESTAMP WHERE MaDonHang=1")
            db.execute('UPDATE ChiTietDonHang SET SoLuong=3 WHERE MaDonHang=1 AND MaBienThe=1')
        self.login('admin@shop.vn')
        page = self.client.get('/admin/slow-products?days=30')
        self.assertNotIn('Nike Air Zoom Pegasus', page.get_data(as_text=True))
        self.assertIn('Converse Chuck Taylor', page.get_data(as_text=True))

    def test_shoe_finder_finds_live_stock_by_same_variant(self):
        self.assertEqual(self.client.get('/find-your-shoes').status_code, 200)
        page = self.client.get('/find-your-shoes?category=1&brand=Nike&size=39&show=1')
        self.assertEqual(page.status_code, 200)
        self.assertIn('Nike Air Zoom Pegasus', page.get_data(as_text=True))
        # Nike màu trắng chỉ có ở size 40, không phải size 39.
        miss = self.client.get('/find-your-shoes?brand=Nike&color=Trắng&size=39&show=1')
        self.assertIn('Chưa tìm được sản phẩm phù hợp', miss.get_data(as_text=True))
        self.assertEqual(self.client.get('/find-your-shoes?size=000&show=1').status_code, 400)

    def test_shoe_finder_does_not_reveal_hidden_product(self):
        page = self.client.get('/find-your-shoes?show=1')
        self.assertEqual(page.status_code, 200)
        self.assertNotIn('Giày Thể Thao Mẫu Ẩn', page.get_data(as_text=True))

    def test_quick_view_returns_live_variants_and_blocks_hidden(self):
        page = self.client.get('/api/w11/quick-view/1')
        self.assertEqual(page.status_code, 200)
        data = page.get_json()
        self.assertEqual(data['name'], 'Nike Air Zoom Pegasus')
        self.assertEqual(data['stock'], 33)
        self.assertEqual(len(data['variants']), 3)
        self.assertEqual(self.client.get('/api/w11/quick-view/12').status_code, 404)
        self.assertEqual(self.client.get('/api/w11/quick-view/99999').status_code, 404)

    def test_cards_and_footer_show_real_actions(self):
        page = self.client.get('/')
        html = page.get_data(as_text=True)
        self.assertIn('data-w11-quick', html)
        self.assertIn('/find-your-shoes', html)
        self.assertIn('id="w11-footer-q"', html)
        self.assertIn('id="w11-back-to-top"', html)
        self.assertIn('js/w11_upgrade.js', html)
        self.assertEqual(self.client.get('/products?q=Nike').status_code, 200)

    def test_bug_01_actual_menu_opens_connected_orders(self):
        self.login('khach@shop.vn')
        html = self.client.get('/').get_data(as_text=True)
        self.assertIn('href="/account/orders">Đơn của tôi', html)
        self.assertNotIn('href="/my-orders">Đơn của tôi', html)
        page = self.client.get('/account/orders')
        self.assertEqual(page.status_code, 200)
        self.assertIn('Đơn #1', page.get_data(as_text=True))
        # /my-orders là UI provider thử nghiệm của Tuấn, giữ nguyên contract 503.
        self.assertEqual(self.client.get('/my-orders').status_code, 503)


if __name__ == '__main__':
    unittest.main()
