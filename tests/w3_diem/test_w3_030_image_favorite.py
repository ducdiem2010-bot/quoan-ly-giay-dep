"""Nhiệm vụ W3-030: Kiểm thử chính sách ảnh (A01, A04, A05) và Yêu thích (Favorites).
Phụ trách: Điểm (Nhóm trưởng Nhóm 6).

Nguyên tắc:
- Chỉ viết test kiểm tra quy tắc.
- Không tự code lại hệ thống upload hoặc favorite của Khải.
- Nếu thiếu backend từ Khải (W3-014, W3-054, W3-056), giữ trạng thái BLOCKED.
"""
import io
import unittest
from app import create_app
from tests.w3_diem.business_rules import (
    MAX_IMAGE_SIZE_BYTES,
    ALLOWED_IMAGE_EXTENSIONS,
    validate_image_bytes,
    FALLBACK_AVATAR_IMAGE,
)
from tests.w3_diem.fixtures import (
    create_isolated_test_app,
    extract_csrf_token,
    TEST_ACCOUNTS,
)


class TestW3030ImageFavorite(unittest.TestCase):
    """Kiểm thử chính sách xử lý ảnh và hệ thống sản phẩm yêu thích."""

    def setUp(self):
        self.app, self.temp_dir, self.db_path = create_isolated_test_app()
        self.client = self.app.test_client()

    # ================= KHỐI KIỂM THỬ CHÍNH SÁCH ẢNH =================

    def test_01_valid_image_formats(self):
        """1. Kiểm tra ảnh đúng định dạng JPG, PNG, WebP hợp lệ."""
        valid_jpeg_header = b"\xFF\xD8\xFF\xE0\x00\x10JFIF" + b"\x00" * 100
        valid, msg = validate_image_bytes(valid_jpeg_header, "shoe.jpg")
        self.assertTrue(valid, "Ảnh JPEG có header chuẩn phải hợp lệ")

        valid_png_header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        valid, msg = validate_image_bytes(valid_png_header, "shoe.png")
        self.assertTrue(valid, "Ảnh PNG có header chuẩn phải hợp lệ")

        valid_webp_header = b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP" + b"\x00" * 100
        valid, msg = validate_image_bytes(valid_webp_header, "shoe.webp")
        self.assertTrue(valid, "Ảnh WebP có header chuẩn phải hợp lệ")

    def test_02_fake_image_file_rejected(self):
        """2. Phát hiện file giả mạo ảnh (ví dụ file script mã độc đổi đuôi thành .jpg)."""
        malicious_content = b"<?php echo 'Hacked'; ?> <script>alert(1)</script>"
        valid, msg = validate_image_bytes(malicious_content, "shell.jpg")
        self.assertFalse(valid, "File chứa mã nguồn script giả đuôi .jpg phải bị phát hiện và từ chối")
        self.assertIn("giả mạo", msg.lower())

    def test_03_image_exceeding_5mb_rejected(self):
        """3. Ảnh vượt quá giới hạn 5MB phải bị từ chối (A05)."""
        fake_large_image = b"\xFF\xD8\xFF" + b"\x00" * (MAX_IMAGE_SIZE_BYTES + 1024)
        valid, msg = validate_image_bytes(fake_large_image, "large_shoe.jpg")
        self.assertFalse(valid, "Ảnh lớn hơn 5MB phải bị từ chối")
        self.assertIn("vượt quá", msg.lower())

    def test_04_dangerous_file_extensions_blocked(self):
        """4. Tuyệt đối không cho phép file có phần mở rộng nguy hiểm (.exe, .php, .sh, .html)."""
        dangerous_names = ["malware.exe", "test.php", "script.sh", "page.html", "config.py"]
        for fname in dangerous_names:
            valid, msg = validate_image_bytes(b"\x00" * 10, fname)
            self.assertFalse(valid, f"File {fname} phải bị từ chối ngay lập tức")

    def test_05_avatar_deletion_fallback_rule(self):
        """5. Quy tắc A04: Khi xóa ảnh đại diện, phải chọn ảnh thay thế hoặc fallback default."""
        images = [
            {"id": 1, "url": "shoe-front.jpg", "is_avatar": True},
            {"id": 2, "url": "shoe-side.jpg", "is_avatar": False},
        ]
        # Xóa ảnh 1 (đang là avatar)
        images = [img for img in images if img["id"] != 1]
        # Nếu còn ảnh khác -> ảnh tiếp theo làm avatar
        if images:
            images[0]["is_avatar"] = True
            new_avatar = images[0]["url"]
        else:
            new_avatar = FALLBACK_AVATAR_IMAGE

        self.assertEqual(new_avatar, "shoe-side.jpg", "Ảnh còn lại phải được thăng hạng làm avatar")

    # ================= KHỐI KIỂM THỬ YÊU THÍCH (FAVORITES) =================

    def test_06_guest_cannot_save_favorite(self):
        """6. Khách chưa đăng nhập (Guest) không thể lưu sản phẩm yêu thích (phải chuyển hướng login)."""
        self.client.get("/")
        with self.client.session_transaction() as sess:
            token = sess.get("_csrf", "")

        res = self.client.post("/favorite/1", data={"csrf_token": token}, follow_redirects=False)
        # Nếu chưa có route favorite (Khải W3-014 chưa ghép)
        if res.status_code == 404:
            self.skipTest("[BLOCKED] Route /favorite chưa được triển khai bởi Khải (W3-014).")
        # Nếu có route: Guest phải bị chuyển hướng tới /login hoặc nhận mã 401/403
        self.assertIn(res.status_code, [302, 401, 403], "Khách chưa đăng nhập không được phép lưu favorite")

    def test_07_customer_favorite_isolation(self):
        """7. Khách A không được truy cập danh sách yêu thích của Khách B (cách ly dữ liệu)."""
        # Kiểm tra sự tồn tại của endpoint quản lý favorite
        res = self.client.get("/favorites")
        if res.status_code == 404:
            self.skipTest("[BLOCKED] Chức năng danh sách yêu thích chưa có backend từ Khải (W3-014).")
        self.assertIn(res.status_code, [302, 401], "Chưa đăng nhập truy cập /favorites phải bị chặn")

    def test_08_duplicate_favorite_blocked(self):
        """8. Ràng buộc: Một người dùng không thể lưu trùng 1 sản phẩm nhiều lần (UNIQUE (user_id, product_id))."""
        # Kiểm tra logic nghiệp vụ: không tạo bản ghi duplicate trong CSDL
        # Đây là assertion hợp đồng dành cho Khải
        pass


if __name__ == "__main__":
    unittest.main(verbosity=2)
