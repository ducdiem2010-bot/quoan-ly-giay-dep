import tempfile
from pathlib import Path
import unittest
from app import create_app
from app.db import query_one


class TestProductEditImageDisplay(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "test_prod_img.sqlite3")
        self.app = create_app({
            'TESTING': True,
            'DATABASE': self.db_path,
            'SECRET_KEY': 'test-prod-img-secret',
            'DB_BACKEND': 'sqlite'
        })
        self.client = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def _login_admin(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['role'] = 'Admin'

    def test_product_11_edit_displays_existing_image(self):
        """Kiểm tra trang /admin/products/11/edit hiển thị ảnh hiện có của sản phẩm."""
        self._login_admin()
        res = self.client.get('/admin/products/11/edit')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')

        # Phải có khối ảnh hiện có
        self.assertIn('Ảnh hiện có của sản phẩm', html)
        # Phải chứa đường dẫn ảnh product-11.jpg
        self.assertIn('product-11.jpg', html)
        self.assertIn('images/storefront/product-11.jpg', html)
        # Phải có nhãn ảnh đại diện
        self.assertIn('Ảnh đại diện', html)

    def test_all_12_products_have_edit_image_display(self):
        """Kiểm tra 12 sản phẩm mẫu đều có ảnh hiển thị trong form sửa sản phẩm."""
        self._login_admin()
        for pid in range(1, 13):
            res = self.client.get(f'/admin/products/{pid}/edit')
            self.assertEqual(res.status_code, 200, f'Lỗi truy cập sửa sản phẩm {pid}')
            html = res.data.decode('utf-8')
            expected_img = f'product-{pid:02d}.jpg'
            self.assertIn(expected_img, html, f'Sản phẩm {pid} chưa hiển thị ảnh {expected_img}')

    def test_admin_products_list_images(self):
        """Kiểm tra danh sách /admin/products hiển thị ảnh cho sản phẩm 11."""
        self._login_admin()
        res = self.client.get('/admin/products')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')
        self.assertIn('product-11.jpg', html)

    def test_quick_view_api_returns_image_url(self):
        """Kiểm tra API quick-view trả về image_url hợp lệ cho sản phẩm 11."""
        res = self.client.get('/api/w11/quick-view/11')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIsNotNone(data.get('image_url'))
        self.assertIn('product-11.jpg', data['image_url'])

    def test_product_without_image_displays_no_image_notice(self):
        """Kiểm tra sản phẩm chưa có ảnh (như SP 13) hiển thị thông báo rõ ràng, không bị trống/lỗi."""
        self._login_admin()
        res = self.client.get('/admin/products/13/edit')
        if res.status_code == 200:
            html = res.data.decode('utf-8')
            self.assertIn('Sản phẩm hiện chưa có ảnh', html)


if __name__ == '__main__':
    unittest.main()
