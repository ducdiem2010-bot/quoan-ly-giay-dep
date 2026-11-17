"""W10: test mới trên SQLite cô lập, không đụng tới instance/demo.sqlite3."""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from app import create_app
from app.services.dashboard import get_dashboard_stats
from app.services.hot_products import get_hot_product_ids
from app.services.inventory import stock_status


class W10UpgradeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='nhom6_w10_')
        self.app = create_app({
            'TESTING': True, 'DB_BACKEND': 'sqlite',
            'DATABASE': str(Path(self.temp.name) / 'test.sqlite3'),
            'SECRET_KEY': 'w10-test-only',
        })
        self.context = self.app.app_context()
        self.context.push()
        self.client = self.app.test_client()
        self.db = sqlite3.connect(self.app.config['DATABASE'])

    def tearDown(self):
        self.db.close()
        self.context.pop()
        self.temp.cleanup()

    def set_user(self, role):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['role'] = role

    def test_stock_badges(self):
        self.assertEqual(stock_status(0)['label'], 'Hết hàng')
        self.assertEqual(stock_status(3)['label'], 'Sắp hết hàng')
        self.assertEqual(stock_status(10)['label'], 'Còn hàng')

    def test_stock_totals_product_not_variant(self):
        stats = get_dashboard_stats()
        products = self.db.execute('SELECT COUNT(*) FROM SanPham').fetchone()[0]
        self.assertEqual(stats['total_products'], products)
        self.assertGreaterEqual(stats['out_of_stock'], 1)

    def test_dashboard_rejects_guest(self):
        self.assertEqual(self.client.get('/admin').status_code, 302)

    def test_dashboard_rejects_customer(self):
        self.set_user('Customer')
        self.assertEqual(self.client.get('/admin').status_code, 403)

    def test_dashboard_for_admin(self):
        self.set_user('Admin')
        page = self.client.get('/admin')
        self.assertEqual(page.status_code, 200)
        text = page.get_data(as_text=True)
        self.assertIn('Tổng quan cửa hàng', text)
        self.assertIn('Sản phẩm sắp hết hàng', text)
        self.assertIn('Quản trị sản phẩm', text)  # tương thích test cũ

    def _make_seed_order_completed_with_payment(self):
        """Tạo fixture nghiệp vụ hợp lệ: hoàn thành phải giao và thu tiền."""
        self.db.execute("UPDATE DonHang SET TrangThai='Hoàn thành',TrangThaiGiaoHang='Đã giao' WHERE MaDonHang=1")
        self.db.execute("""INSERT OR REPLACE INTO ThongTinGiaoDich
            (MaDonHang,HoTen,SoDienThoai,HinhThucNhanHang,PhuongThucThanhToan,TrangThaiThanhToan)
            VALUES (1,'Khách demo','0000000000','delivery','cod','Đã thanh toán')""")
        self.db.commit()

    def test_sqlite_value_does_not_claim_paid_revenue(self):
        self._make_seed_order_completed_with_payment()
        stats = get_dashboard_stats()
        self.assertEqual(stats['completed_order_value'], 3490000)
        self.assertFalse(stats['verified_revenue'])
        self.set_user('Admin')
        self.assertIn('chưa phải doanh thu thực nhận', self.client.get('/admin').get_data(as_text=True))

    def test_dashboard_zero_and_no_fake_revenue(self):
        self.db.execute('DELETE FROM ChiTietDonHang')
        self.db.execute('DELETE FROM DonHang')
        self.db.execute('DELETE FROM BienTheSanPham')
        self.db.execute('DELETE FROM SanPham')
        self.db.commit()
        stats = get_dashboard_stats()
        self.assertEqual(stats['total_products'], 0)
        self.assertEqual(stats['total_orders'], 0)
        self.assertEqual(stats['completed_order_value'], 0)
        self.assertEqual(stats['out_of_stock'], 0)

    def test_hot_requires_completed_order(self):
        self.assertEqual(get_hot_product_ids(), set())
        self._make_seed_order_completed_with_payment()
        hot = get_hot_product_ids()
        self.assertTrue(hot)
        self.assertLessEqual(len(hot), 3)
        self.assertNotIn(12, hot)  # sản phẩm ẩn của seed

    def test_hot_does_not_count_cancelled_order(self):
        self.db.execute("UPDATE DonHang SET TrangThai='Đã hủy'")
        self.db.commit()
        self.assertFalse(get_hot_product_ids())

    def test_hot_badge_visible_on_home(self):
        self._make_seed_order_completed_with_payment()
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('site-product-hot', response.get_data(as_text=True))


if __name__ == '__main__':
    unittest.main(verbosity=2)
