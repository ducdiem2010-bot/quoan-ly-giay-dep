import tempfile
from pathlib import Path
import unittest
from app import create_app
from app.db import query_all, query_one


class TestStoreNavigationOrders(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "test_store_nav.sqlite3")
        self.app = create_app({
            'TESTING': True,
            'DATABASE': self.db_path,
            'SECRET_KEY': 'test-nav-secret',
            'DB_BACKEND': 'sqlite'
        })
        self.client = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def _login(self, email, password='Demo@12345'):
        self.client.get('/login')
        with self.client.session_transaction() as sess:
            token = sess['_csrf']
        return self.client.post('/login', data={'csrf_token': token, 'email': email, 'password': password}, follow_redirects=True)

    def test_customer_navigation(self):
        """Khách hàng đăng nhập: thanh menu có 'Theo dõi đơn hàng', dropdown có 'Đơn của tôi', không có 'Quản lý đơn hàng'."""
        self._login('khach@shop.vn')
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')

        # Menu chính phải có Theo dõi đơn hàng
        self.assertIn('Theo dõi đơn hàng', html)
        self.assertIn('href="/account/orders"', html)

        # Menu dropdown
        self.assertIn('Thông tin tài khoản', html)
        self.assertIn('Đơn của tôi', html)
        self.assertIn('Đăng xuất', html)
        self.assertNotIn('Khu vực Quản trị', html)
        self.assertNotIn('Khu vực Nhân viên', html)
        self.assertNotIn('Quản lý đơn hàng', html)

        # Xem đơn cá nhân: khách có đơn #1
        res_orders = self.client.get('/account/orders')
        self.assertEqual(res_orders.status_code, 200)
        orders_html = res_orders.data.decode('utf-8')
        self.assertIn('Đơn #1', orders_html)

        # Khách hàng không được vào khu vực quản trị hoặc nhân viên
        self.assertIn(self.client.get('/admin/orders').status_code, [302, 403])
        self.assertIn(self.client.get('/staff/orders').status_code, [302, 403])

    def test_seller_navigation(self):
        """Nhân viên đăng nhập: thanh menu có 'Theo dõi đơn hàng' đến đơn cá nhân; dropdown chỉ có Tài khoản, Khu vực Nhân viên, Đăng xuất."""
        self._login('minh@shop.vn')
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')

        # Thanh menu cửa hàng: có 'Theo dõi đơn hàng', KHÔNG có 'Quản lý đơn hàng'
        self.assertIn('Theo dõi đơn hàng', html)
        self.assertIn('href="/account/orders"', html)
        # Menu nav-links không có Quản lý đơn hàng
        nav_part = html[html.find('<nav aria-label="Điều hướng chính"'):html.find('</nav>')]
        self.assertIn('Theo dõi đơn hàng', nav_part)
        self.assertNotIn('Quản lý đơn hàng', nav_part)

        # Dropdown tên tài khoản: chỉ giữ Thông tin tài khoản, Khu vực Nhân viên, Đăng xuất
        dropdown_part = html[html.find('class="account-dropdown"'):html.find('</details>')]
        self.assertIn('Thông tin tài khoản', dropdown_part)
        self.assertIn('Khu vực Nhân viên', dropdown_part)
        self.assertIn('Đăng xuất', dropdown_part)
        self.assertNotIn('Quản lý đơn hàng', dropdown_part)

        # Xem đơn cá nhân của nhân viên: nhân viên Minh (id=2) chưa mua hàng -> hiển thị chưa có đơn, KHÔNG hiện đơn #1 của khách (id=3)
        res_orders = self.client.get('/account/orders')
        self.assertEqual(res_orders.status_code, 200)
        orders_html = res_orders.data.decode('utf-8')
        self.assertIn('Bạn chưa có đơn hàng nào', orders_html)
        self.assertNotIn('Đơn #1', orders_html)

        # Nhưng trong khu vực nhân viên /staff/orders: nhân viên vẫn quản lý được toàn bộ đơn cửa hàng
        res_staff = self.client.get('/staff/orders')
        self.assertEqual(res_staff.status_code, 200)
        staff_html = res_staff.data.decode('utf-8')
        self.assertIn('Danh sách đơn hàng của khách hàng', staff_html)
        self.assertIn('#1', staff_html)

    def test_admin_navigation(self):
        """Admin đăng nhập: thanh menu có 'Theo dõi đơn hàng'; dropdown chỉ có Tài khoản, Khu vực Quản trị, Đăng xuất."""
        self._login('admin@shop.vn')
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        html = res.data.decode('utf-8')

        # Thanh menu cửa hàng: có 'Theo dõi đơn hàng'
        self.assertIn('Theo dõi đơn hàng', html)
        self.assertIn('href="/account/orders"', html)
        nav_part = html[html.find('<nav aria-label="Điều hướng chính"'):html.find('</nav>')]
        self.assertIn('Theo dõi đơn hàng', nav_part)
        self.assertNotIn('Quản lý đơn hàng', nav_part)

        # Dropdown tên tài khoản: chỉ giữ Thông tin tài khoản, Khu vực Quản trị, Đăng xuất
        dropdown_part = html[html.find('class="account-dropdown"'):html.find('</details>')]
        self.assertIn('Thông tin tài khoản', dropdown_part)
        self.assertIn('Khu vực Quản trị', dropdown_part)
        self.assertIn('Đăng xuất', dropdown_part)
        self.assertNotIn('Quản lý đơn hàng', dropdown_part)

        # Đơn cá nhân của admin (id=1): admin có đơn cá nhân #4, #5, #6 -> hiển thị đơn của mình, KHÔNG hiện đơn #1 của khách (id=3)
        with self.app.app_context():
            from app.db import get_db_connection
            conn = get_db_connection()
            try:
                cur = conn.cursor()
                if not cur.execute('SELECT 1 FROM DonHang WHERE MaNguoiDung = 1').fetchone():
                    cur.execute("INSERT INTO DonHang (MaDonHang, MaNguoiDung, TrangThai) VALUES (6, 1, 'Hoàn thành')")
                    conn.commit()
            finally:
                conn.close()

        res_orders = self.client.get('/account/orders')
        self.assertEqual(res_orders.status_code, 200)
        orders_html = res_orders.data.decode('utf-8')
        self.assertIn('Đơn #6', orders_html)
        self.assertNotIn('Đơn #1', orders_html)

        # Trong khu vực admin /admin/orders: admin quản lý được toàn bộ đơn cửa hàng (bao gồm đơn #1 của khách)
        res_admin_orders = self.client.get('/admin/orders')
        self.assertEqual(res_admin_orders.status_code, 200)
        self.assertIn('#1', res_admin_orders.data.decode('utf-8'))

    def test_security_cannot_cancel_other_user_order(self):
        """Bảo mật: Không thể hủy đơn của người khác bằng cách thay ID trên URL."""
        # Minh (id=2) cố tình gửi POST hủy đơn #1 (của khách id=3)
        self._login('minh@shop.vn')
        with self.client.session_transaction() as sess:
            token = sess['_csrf']
        res = self.client.post('/account/orders/1/cancel', data={'csrf_token': token})
        self.assertEqual(res.status_code, 404)


if __name__ == '__main__':
    unittest.main()
