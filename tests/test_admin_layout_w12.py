"""
Kiểm tra cấu trúc và tính năng giao diện quản trị Admin/Staff theo yêu cầu W12:
- 5 nhóm menu: Tổng quan, Đơn hàng, Sản phẩm, Tài khoản, Báo cáo
- Tái sử dụng route/backend hiện có, loại bỏ menu trùng
- Chuyển hướng /admin/invoices -> /admin/orders giữ nguyên query parameters
- Tab 4 thuộc tính sản phẩm: Loại/Danh mục, Thương hiệu, Màu sắc, Kích thước
- Header và footer dành riêng cho Admin (không giỏ hàng, footer gọn)
- Phân biệt điều hướng theo vai trò (Admin, Nhân viên, Khách hàng)
"""

from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest

from app import create_app


class TestAdminLayoutW12(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dbpath = str(Path(self.tmp.name) / "admin_test.sqlite3")
        self.app = create_app({
            "TESTING": True,
            "DB_BACKEND": "sqlite",
            "DATABASE": self.dbpath,
            "SECRET_KEY": "w12-test-admin-key",
            "FORCE_ACCOUNT_STATUS_GUARD": True,
            "FORCE_LEGACY_ORDER_REDIRECT": True,
        })
        self.client = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def token(self):
        self.client.get("/login")
        with self.client.session_transaction() as s:
            return s.get("_csrf", "")

    def login(self, email, password="Demo@12345"):
        return self.client.post(
            "/login",
            data={"csrf_token": self.token(), "email": email, "password": password},
            follow_redirects=True,
        )

    def test_admin_sidebar_5_groups_and_items(self):
        """Kiểm tra sidebar Admin có đủ 5 nhóm và không có mục trùng lặp"""
        self.login("admin@shop.vn")
        res = self.client.get("/admin")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)

        # 1. Nhóm Tổng quan
        self.assertIn("Tổng quan", html)
        self.assertIn('href="/admin"', html)

        # 2. Nhóm Đơn hàng
        self.assertIn("Đơn hàng", html)
        self.assertIn('href="/admin/orders"', html)

        # 3. Nhóm Sản phẩm & các mục con
        self.assertIn("Sản phẩm", html)
        self.assertIn("Danh sách sản phẩm", html)
        self.assertIn('href="/admin/products"', html)
        self.assertIn("Thuộc tính sản phẩm", html)
        self.assertIn('href="/admin/categories"', html)

        # 4. Nhóm Tài khoản & các mục con
        self.assertIn("Tài khoản", html)
        self.assertIn("Nhân viên", html)
        self.assertIn('href="/admin/staff"', html)
        self.assertIn("Khách hàng", html)
        self.assertIn('href="/admin/customers"', html)

        # 5. Nhóm Theo dõi sản phẩm & các mục con
        self.assertIn("Theo dõi sản phẩm", html)
        self.assertIn("Sản phẩm hết hàng", html)
        self.assertIn('href="/admin/out-of-stock"', html)
        self.assertIn("Sản phẩm bán chậm", html)
        self.assertIn('href="/admin/slow-products"', html)

        # Kiểm tra mục cũ / trùng không còn xuất hiện độc lập trong sidebar
        self.assertNotIn('href="/admin/invoices"', html)
        self.assertNotIn('class="admin-nav-item">Thêm sản phẩm', html)
        self.assertNotIn('Kiểm tra sản phẩm', html)

    def test_admin_header_and_compact_footer(self):
        """Admin header gọn: Logo, Khu vực quản trị, Xem cửa hàng; Footer gọn; không có giỏ hàng"""
        self.login("admin@shop.vn")
        res = self.client.get("/admin")
        html = res.get_data(as_text=True)

        # Header Admin
        self.assertIn("Khu vực quản trị", html)
        self.assertIn("Xem cửa hàng", html)
        self.assertIn("↗", html)
        self.assertIn('href="/"', html)

        # Không có giỏ hàng trong khu vực quản trị
        self.assertNotIn('cart-count', html)

        # Chân trang Admin gọn
        self.assertIn("Tất cả quyền được bảo lưu. (Khu vực quản trị)", html)
        self.assertNotIn("custom-store-footer", html)

    def test_dashboard_kpis_and_stock_alerts(self):
        """Dashboard hiển thị 6 KPI cards, cảnh báo tồn kho và truy cập nhanh"""
        self.login("admin@shop.vn")
        res = self.client.get("/admin")
        html = res.get_data(as_text=True)

        # 6 KPI cards
        self.assertIn("Tổng sản phẩm", html)
        self.assertIn("Tổng đơn hàng", html)
        self.assertIn("Giá trị đơn hoàn thành", html)
        self.assertIn("Đơn chờ xác nhận", html)
        self.assertIn("Sản phẩm hết hàng", html)
        self.assertIn("Sản phẩm sắp hết", html)

        # Cảnh báo tồn kho
        self.assertIn("Cảnh báo tồn kho", html)
        self.assertIn("Hết hàng", html)
        self.assertIn("Sắp hết", html)
        # Kiểm tra ảnh sản phẩm có liên kết thực tế (không dùng placeholder emoji hoặc svg fallback)
        self.assertIn("stock-product-img-wrap", html)
        self.assertIn("stock-product-img", html)
        self.assertIn("images/storefront/product-11.jpg", html)

        # Truy cập nhanh
        self.assertIn("Truy cập nhanh", html)
        self.assertIn("Quản lý đơn hàng", html)
        self.assertIn("+ Thêm sản phẩm", html)
        self.assertIn("+ Tạo nhân viên", html)

    def test_invoices_redirects_to_orders_with_params(self):
        """Truy cập /admin/invoices được 302 chuyển hướng về /admin/orders giữ nguyên params"""
        self.login("admin@shop.vn")
        res = self.client.get("/admin/invoices?q=DH001")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/admin/orders?q=DH001", res.headers.get("Location"))

        # Follow redirect trả về 200 trang orders
        followed = self.client.get("/admin/invoices?q=DH001", follow_redirects=True)
        self.assertEqual(followed.status_code, 200)

    def test_product_attribute_tabs(self):
        """Các trang thuộc tính sản phẩm hiển thị thanh tab 4 thuộc tính (Loại, Thương hiệu, Màu sắc, Kích thước)"""
        self.login("admin@shop.vn")

        for url, active_text in [
            ("/admin/categories", "Loại / Danh mục"),
            ("/admin/brands", "Thương hiệu"),
            ("/admin/colors", "Màu sắc"),
            ("/admin/sizes", "Kích thước"),
        ]:
            res = self.client.get(url)
            self.assertEqual(res.status_code, 200)
            html = res.get_data(as_text=True)
            self.assertIn("admin-attr-tabs", html)
            self.assertIn(active_text, html)

    def test_product_list_has_add_button(self):
        """Trang danh sách sản phẩm có nút '+ Thêm sản phẩm' bên trong"""
        self.login("admin@shop.vn")
        res = self.client.get("/admin/products")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("+ Thêm sản phẩm", html)
        self.assertIn('href="/admin/products/new"', html)

    def test_role_navigation_separation(self):
        """Phân biệt điều hướng: Nhân viên có Quản lý đơn hàng, Khách hàng có Đơn của tôi"""
        # Khách hàng
        self.login("khach@shop.vn")
        res_khach = self.client.get("/account/orders")
        self.assertEqual(res_khach.status_code, 200)

        # Không cho phép khách hàng vào admin
        res_khach_admin = self.client.get("/admin")
        self.assertIn(res_khach_admin.status_code, [302, 403])

        # Nhân viên (Seller: minh@shop.vn)
        self.client.get("/logout")
        self.login("minh@shop.vn")
        res_staff = self.client.get("/staff/orders")
        self.assertEqual(res_staff.status_code, 200)

    def test_slow_products_table_clean_structure(self):
        """Trang Sản phẩm bán chậm hiển thị bảng sạch (Mã, Tên, Số lượng đã bán, Tồn kho), không có phân tích/đánh giá"""
        self.login("admin@shop.vn")
        res = self.client.get("/admin/slow-products")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)

        # Tiêu đề và tiêu chí
        self.assertIn("Sản phẩm bán chậm", html)
        self.assertIn("Tiêu chí thống kê", html)

        # Cột bảng
        self.assertIn("Mã sản phẩm", html)
        self.assertIn("Tên sản phẩm", html)
        self.assertIn("Số lượng đã bán", html)
        self.assertIn("Tổng tồn kho", html)

        # Không có các cột nhận xét/phân tích cũ
        self.assertNotIn("<th>Nhận xét</th>", html)
        self.assertNotIn("Chưa từng có đơn hoàn thành khác với", html)

    def test_out_of_stock_products_clean_table(self):
        """Trang Sản phẩm hết hàng liệt kê sản phẩm có tồn = 0, không kiểm tra chất lượng thông tin"""
        self.login("admin@shop.vn")

        # Cả URL mới và URL cũ đều trả về 200 trang Sản phẩm hết hàng
        for url in ["/admin/out-of-stock", "/admin/product-health"]:
            res = self.client.get(url)
            self.assertEqual(res.status_code, 200)
            html = res.get_data(as_text=True)

            self.assertIn("Sản phẩm hết hàng", html)
            self.assertIn("Mã sản phẩm", html)
            self.assertIn("Tên sản phẩm", html)
            self.assertIn("Danh mục", html)
            self.assertIn("Tổng tồn kho", html)
            self.assertIn("Trạng thái", html)

            # Không có các khối kiểm tra chất lượng sản phẩm cũ
            self.assertNotIn("Trung tâm kiểm tra sản phẩm", html)
            self.assertNotIn("Cảnh báo nghiêm trọng", html)
            self.assertNotIn("Chưa tải ảnh riêng", html)


if __name__ == "__main__":
    unittest.main()
