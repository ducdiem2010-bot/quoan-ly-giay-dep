"""Kiểm thử chi tiết footer mới theo yêu cầu thiết kế và backend."""

import unittest
from pathlib import Path
import tempfile
from app import create_app
from app.store_config import STORE_INFO


class CustomFooterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "test.sqlite3")
        self.app = create_app({
            "TESTING": True,
            "DATABASE": self.db_path,
            "SECRET_KEY": "footer-test-secret",
            "DB_BACKEND": "sqlite"
        })
        self.client = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def login(self, email="khach@shop.vn", password="Demo@12345"):
        self.client.get("/login")
        with self.client.session_transaction() as sess:
            token = sess["_csrf"]
        return self.client.post("/login", data={
            "csrf_token": token,
            "email": email,
            "password": password
        }, follow_redirects=True)

    def test_footer_structure_and_content_on_homepage(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)

        # 1. Khối phía trên: Trợ lý tìm giày
        self.assertIn("TƯ VẤN • CHỌN SIZE • KIỂM TRA HÀNG", html)
        self.assertIn("Tìm đôi giày", html)
        self.assertIn("phù hợp với bạn", html)
        self.assertIn("Khám phá sản phẩm phù hợp với nhu cầu, phong cách và kích cỡ của bạn.", html)
        self.assertIn("Trợ lý tìm giày", html)
        self.assertIn('href="/find-your-shoes"', html)

        # 2. Cột 1 — SHOES STORE
        self.assertIn("SHOES STORE", html)
        self.assertIn("Giày thể thao, sneaker và dép cho việc đi học, đi làm và sử dụng hằng ngày.", html)

        # 3. Cột 2 — Thông tin cửa hàng
        self.assertIn("Thông tin cửa hàng", html)
        self.assertIn("12 Đường Giày Xinh, Khu phố Mẫu", html)
        self.assertIn("Hotline: 0900 000 000", html)
        self.assertIn("Giờ hoạt động: 06:00–21:00", html)
        self.assertIn("Địa chỉ và số điện thoại minh họa", html)

        # 4. Cột 3 — Kết nối & tư vấn
        self.assertIn("Kết nối &amp; tư vấn", html)
        self.assertIn("Nhóm Zalo tư vấn chung", html)
        self.assertIn("Nhiều nhân viên hỗ trợ", html)
        self.assertIn("https://zalo.me/g/mvubxrw7ajipawhvlw9v", html)
        self.assertIn('rel="noopener noreferrer"', html)

        # 5. Dòng bản quyền & nút Về đầu trang
        self.assertIn("SHOES STORE · Nhóm 6", html)
        self.assertIn('id="w11-back-to-top"', html)
        self.assertIn("Về đầu trang", html)

        # 6. Các thành phần cũ đã bỏ khỏi footer
        self.assertNotIn("Tìm giày nhanh", html)
        self.assertNotIn("Giải đáp nhanh", html)
        self.assertNotIn("Khám phá chân trang", html)

    def test_shoe_finder_button_destination_and_function(self):
        # Nút Trợ lý tìm giày phải dẫn đúng route /find-your-shoes và hoạt động tốt
        res = self.client.get("/find-your-shoes")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("Trợ lý tìm giày", html)

        # Chạy thử chức năng tìm giày thật
        search_res = self.client.get("/find-your-shoes?category=1&brand=Nike&size=39&show=1")
        self.assertEqual(search_res.status_code, 200)
        self.assertIn("Nike Air Zoom Pegasus", search_res.get_data(as_text=True))

    def test_footer_displays_across_different_pages(self):
        # 1. Trang danh mục / sản phẩm
        res = self.client.get("/products")
        self.assertEqual(res.status_code, 200)
        self.assertIn("12 Đường Giày Xinh, Khu phố Mẫu", res.get_data(as_text=True))
        self.assertIn('id="w11-back-to-top"', res.get_data(as_text=True))

        # 2. Trang đăng nhập
        res = self.client.get("/login")
        self.assertEqual(res.status_code, 200)
        self.assertIn("12 Đường Giày Xinh, Khu phố Mẫu", res.get_data(as_text=True))

        # 3. Trang tài khoản khách hàng
        self.login("khach@shop.vn")
        res = self.client.get("/account")
        self.assertEqual(res.status_code, 200)
        self.assertIn("12 Đường Giày Xinh, Khu phố Mẫu", res.get_data(as_text=True))

        # 4. Trang quản trị admin (dùng chân trang quản trị gọn theo yêu cầu mới)
        self.client.get("/logout")
        self.login("admin@shop.vn")
        res = self.client.get("/admin/product-health")
        self.assertEqual(res.status_code, 200)
        self.assertIn("Tất cả quyền được bảo lưu. (Khu vực quản trị)", res.get_data(as_text=True))
        self.assertNotIn("custom-store-footer", res.get_data(as_text=True))

    def test_hotline_mode_switch(self):
        # Mặc định hotline_is_active là False -> nút Gọi tư vấn là button thông báo
        res = self.client.get("/")
        html = res.get_data(as_text=True)
        self.assertIn("Gọi tư vấn", html)
        self.assertNotIn('href="tel:', html)

        # Khi cấu hình hotline_is_active = True và hotline_tel thật
        active_config = dict(STORE_INFO)
        active_config["hotline_is_active"] = True
        active_config["hotline_tel"] = "0900000000"
        self.app.config["STORE_INFO"] = active_config

        res2 = self.client.get("/")
        html2 = res2.get_data(as_text=True)
        self.assertIn('href="tel:0900000000"', html2)


if __name__ == "__main__":
    unittest.main()
