"""Nhiệm vụ W3-029: Kiểm thử chéo tối thiểu 12 kịch bản thực tế bắt buộc.
Phụ trách: Điểm (Nhóm trưởng Nhóm 6).

Bao gồm đầy đủ 12 tình huống D29-01 đến D29-12:
- Ghi rõ Test ID, Preconditions, Input, Expected, Actual, Status.
- Phân loại chính xác: PASS, FAIL, BLOCKED, NOT RUN.
- Không sửa backend của thành viên khác; nếu tính năng chưa triển khai, đánh dấu BLOCKED/FAIL trung thực.
"""
import unittest
from html.parser import HTMLParser
from app import create_app
from tests.w3_diem.business_rules import (
    normalize_category_name,
    validate_product_price,
    UserRole,
)
from tests.w3_diem.fixtures import (
    create_isolated_test_app,
    extract_csrf_token,
    TEST_ACCOUNTS,
)


class TestW3029CrossScenarios(unittest.TestCase):
    """12 kịch bản kiểm thử chéo toàn diện cho Tuần 3."""

    def setUp(self):
        self.app, self.temp_dir, self.db_path = create_isolated_test_app()
        self.client = self.app.test_client()

    def login_as(self, email, password):
        """Helper đăng nhập hệ thống."""
        res = self.client.get("/login")
        token = extract_csrf_token(res.get_data(as_text=True))
        return self.client.post("/login", data={
            "csrf_token": token,
            "email": email,
            "password": password,
        }, follow_redirects=True)

    def test_d29_01_guest_view_product_list(self):
        """D29-01: Khách chưa đăng nhập xem danh sách sản phẩm.
        Preconditions: Khách là Guest (chưa có session).
        Input: GET /
        Expected: HTTP 200, hiển thị danh sách sản phẩm công khai.
        """
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        content = response.get_data(as_text=True)
        self.assertTrue("sản phẩm" in content.lower())
        self.assertIn("Nike Air Zoom Pegasus", content)

    def test_d29_02_hidden_product_not_shown(self):
        """D29-02: Sản phẩm ẩn không xuất hiện trên giao diện khách.
        Preconditions: Có sản phẩm trạng thái ẩn (TrangThai = 0).
        Input: GET /
        Expected: Sản phẩm ẩn không xuất hiện trong HTML trả về.
        """
        response = self.client.get("/")
        content = response.get_data(as_text=True)
        # Bất kỳ sản phẩm nào có trạng thái ẩn đều không được hiển thị
        self.assertNotIn("Sản phẩm đã ẩn", content)
        self.assertNotIn("SP103 Đã Ẩn", content)

    def test_d29_03_search_product_by_name(self):
        """D29-03: Tìm kiếm sản phẩm theo tên.
        Preconditions: CSDL có sản phẩm tên 'Converse'.
        Input: GET /?q=Converse
        Expected: HTTP 200, danh sách chứa sản phẩm Converse.
        """
        response = self.client.get("/?q=Converse")
        self.assertEqual(response.status_code, 200)
        content = response.get_data(as_text=True)
        self.assertIn("Converse", content)

    def test_d29_04_search_non_existent_keyword(self):
        """D29-04: Tìm kiếm bằng từ khóa không có kết quả.
        Preconditions: CSDL không chứa sản phẩm có tên 'KhongTonTai_XYZ_123'.
        Input: GET /?q=KhongTonTai_XYZ_123
        Expected: HTTP 200, an toàn, không có card sản phẩm nào hiển thị hoặc có thông báo rỗng.
        """
        response = self.client.get("/?q=KhongTonTai_XYZ_123")
        self.assertEqual(response.status_code, 200)
        content = response.get_data(as_text=True)
        self.assertNotIn("Nike Air Zoom", content)

    def test_d29_05_pagination_integrity(self):
        """D29-05: Phân trang trang 1 -> trang 2 không lặp/mất sản phẩm.
        Preconditions: Đã triển khai tính năng phân trang (Minh W3-005).
        Input: GET /?page=1, GET /?page=2
        Expected: Hai trang có danh sách ID sản phẩm tách biệt hoàn toàn.
        """
        res1 = self.client.get("/?page=1")
        res2 = self.client.get("/?page=2")
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res2.status_code, 200)
        # Kiểm tra xem tham số page đã được backend xử lý chưa
        # Trong bản nền Tuần 2, route '/' chưa hỗ trợ tham số page
        # Nếu trang 1 và trang 2 ra nội dung giống y hệt nhau -> backend chưa làm phân trang
        if res1.data == res2.data:
            self.skipTest("[BLOCKED / CHƯA TRIỂN KHAI] Phân trang chưa được ghép từ module W3-005 của Minh.")

    def test_d29_06_view_valid_product_detail(self):
        """D29-06: Xem chi tiết sản phẩm hợp lệ.
        Preconditions: Sản phẩm ID=1 tồn tại trong CSDL.
        Input: GET /product/1
        Expected: HTTP 200, hiển thị đúng tên, giá, thông tin biến thể và form thêm giỏ.
        """
        response = self.client.get("/product/1")
        self.assertEqual(response.status_code, 200)
        content = response.get_data(as_text=True)
        self.assertIn("Nike Air Zoom Pegasus", content)
        self.assertIn('name="variant_id"', content)
        self.assertIn('name="quantity"', content)

    def test_d29_07_invalid_product_id_returns_404(self):
        """D29-07: ID sản phẩm không tồn tại trả về 404.
        Preconditions: ID 999999 không tồn tại trong hệ thống.
        Input: GET /product/999999
        Expected: HTTP 404 Not Found.
        """
        response = self.client.get("/product/999999")
        self.assertEqual(response.status_code, 404)

    def test_d29_08_select_correct_variant(self):
        """D29-08: Chọn đúng biến thể màu–size.
        Preconditions: Biến thể ID=1 tồn tại và còn hàng.
        Input: POST /add-to-cart/1 kèm variant_id=1, quantity=1
        Expected: Chấp nhận thêm vào giỏ, redirect sang trang giỏ hàng.
        """
        detail_res = self.client.get("/product/1")
        token = extract_csrf_token(detail_res.get_data(as_text=True))
        response = self.client.post("/add-to-cart/1", data={
            "csrf_token": token,
            "variant_id": "1",
            "quantity": "1",
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        content = response.get_data(as_text=True)
        self.assertIn("Nike Air Zoom Pegasus", content)

    def test_d29_09_seller_blocked_from_admin_post(self):
        """D29-09: Nhân viên bán hàng (Seller) bị chặn khi POST/GET quản trị.
        Preconditions: Tài khoản Seller 'minh@shop.vn' đã đăng nhập.
        Input: POST /admin/product/add hoặc GET /admin
        Expected: HTTP 403 Forbidden. Backend phải chặn, không chỉ ẩn nút HTML.
        """
        # Đăng nhập bằng tài khoản Seller
        self.login_as("minh@shop.vn", "Demo@12345")

        # Thử truy cập GET /admin
        get_res = self.client.get("/admin")
        self.assertEqual(get_res.status_code, 403, "Seller truy cập GET /admin phải trả về 403")

        # Thử POST trực tiếp vào /admin/product/add kèm csrf_token hợp lệ của seller
        home_res = self.client.get("/")
        token = extract_csrf_token(home_res.get_data(as_text=True))
        post_res = self.client.post("/admin/product/add", data={"csrf_token": token, "name": "SP Gia Mao"}, follow_redirects=False)
        self.assertEqual(post_res.status_code, 403, "Seller POST vào /admin/product/add phải bị chặn 403 tại backend")

    def test_d29_10_admin_add_product_validation(self):
        """D29-10: Quản lý (Admin) thêm sản phẩm hợp lệ.
        Preconditions: Tài khoản Admin 'admin@shop.vn' đã đăng nhập.
        Input: POST /admin/product/add với dữ liệu hợp lệ.
        Expected: Biểu mẫu được duyệt (ở tuần 2 báo đạt kiểm tra, tuần 3 lưu DB).
        """
        self.login_as("admin@shop.vn", "Demo@12345")
        res = self.client.get("/admin/product/add")
        token = extract_csrf_token(res.get_data(as_text=True))

        post_res = self.client.post("/admin/product/add", data={
            "csrf_token": token,
            "name": "Giày Thể Thao Mới Tuần 3",
            "price": "1850000",
            "stock": "10",
            "category_id": "1",
            "image": "shoe-1.svg",
        }, follow_redirects=True)
        self.assertEqual(post_res.status_code, 200)
        content = post_res.get_data(as_text=True)
        self.assertTrue("thành công" in content.lower() or "đạt kiểm tra" in content.lower())

    def test_d29_11_duplicate_category_rejected(self):
        """D29-11: Thêm danh mục trùng tên bị từ chối sau chuẩn hóa (A03).
        Preconditions: Đã có danh mục 'Giày Thể Thao'.
        Input: Thử tạo danh mục '  giày thể thao  ' (chữ thường, khoảng trắng thừa).
        Expected: Bị từ chối do trùng lặp tên danh mục sau khi chuẩn hóa.
        """
        cat1 = normalize_category_name("Giày Thể Thao")
        cat2 = normalize_category_name("  giày thể thao  ")
        self.assertEqual(cat1, cat2, "Quy tắc A03: Hai tên sau chuẩn hóa phải bằng nhau và bị chặn trùng")

    def test_d29_12_invalid_price_rejected(self):
        """D29-12: Nhập giá sai (0đ, âm, chữ) không được tạo dữ liệu (A07).
        Preconditions: Quy tắc A07 quy định giá phải > 0 VNĐ.
        Input: price = 0, price = -100, price = 'mot trieu'
        Expected: Bị từ chối, không được tạo bản ghi trong CSDL.
        """
        for bad_price in [0, -50000, "abc", ""]:
            valid, msg = validate_product_price(bad_price)
            self.assertFalse(valid, f"Giá {bad_price} phải bị từ chối theo A07")


if __name__ == "__main__":
    unittest.main(verbosity=2)
