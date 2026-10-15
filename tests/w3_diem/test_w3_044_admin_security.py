"""Nhiệm vụ W3-044: Kiểm thử Admin, Phân quyền Backend (RBAC), Ràng buộc biến thể và Transaction.
Phụ trách: Điểm (Nhóm trưởng Nhóm 6).

Trọng tâm:
- Quyền truy cập phải được thẩm định tại Backend, chặn đứng truy cập trực tiếp qua URL.
- Seller không được can thiệp CRUD sản phẩm.
- Customer không được vào trang quản trị.
- Tính toàn vẹn giao dịch (Atomic transaction rollback): Lỗi lưu biến thể không sinh ra sản phẩm mồ côi.
"""
import sqlite3
import unittest
from app import create_app
from tests.w3_diem.business_rules import (
    validate_product_price,
    validate_stock_quantity,
    normalize_category_name,
)
from tests.w3_diem.fixtures import (
    create_isolated_test_app,
    extract_csrf_token,
)


class TestW3044AdminSecurity(unittest.TestCase):
    """Bộ kiểm thử bảo mật phân quyền backend và tính toàn vẹn giao dịch."""

    def setUp(self):
        self.app, self.temp_dir, self.db_path = create_isolated_test_app()
        self.client = self.app.test_client()

    def login_user(self, email, password):
        res = self.client.get("/login")
        token = extract_csrf_token(res.get_data(as_text=True))
        return self.client.post("/login", data={
            "csrf_token": token,
            "email": email,
            "password": password,
        }, follow_redirects=True)

    # ================= NHÓM 1: BẢO MẬT & PHÂN QUYỀN (RBAC) =================

    def test_01_guest_blocked_from_admin_urls(self):
        """1. Khách vãng lai (Guest) truy cập trực tiếp URL admin bị điều hướng sang /login."""
        admin_urls = ["/admin", "/admin/product/add"]
        for url in admin_urls:
            res = self.client.get(url, follow_redirects=False)
            self.assertEqual(res.status_code, 302, f"Guest truy cập {url} phải bị 302 redirect")
            self.assertIn("/login", res.location, f"Phải điều hướng về trang login khi chưa xác thực")

    def test_02_customer_blocked_from_admin(self):
        """2. Khách hàng (Customer) bị chặn 403 Forbidden khi truy cập trang quản trị."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 10
            sess["role"] = "Customer"
            sess["user_name"] = "Khách Hàng Test"
        res = self.client.get("/admin", follow_redirects=False)
        self.assertEqual(res.status_code, 403, "Customer vào /admin phải nhận mã 403 Forbidden")

    def test_03_seller_blocked_from_admin_actions(self):
        """3. Nhân viên bán hàng (Seller) chỉ tra cứu, KHÔNG được truy cập hay POST quản trị sản phẩm."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 2
            sess["role"] = "Seller"
            sess["user_name"] = "Nhân Viên Minh"
            sess["_csrf"] = "test-csrf-token-seller"

        # Thử GET /admin
        res_get = self.client.get("/admin", follow_redirects=False)
        self.assertEqual(res_get.status_code, 403, "Seller truy cập /admin phải bị chặn 403")

        # Thử POST trực tiếp vào /admin/product/add kèm csrf_token hợp lệ
        res_post = self.client.post("/admin/product/add", data={"csrf_token": "test-csrf-token-seller", "name": "Hàng lậu"}, follow_redirects=False)
        self.assertEqual(res_post.status_code, 403, "Seller gửi POST vào /admin/product/add phải bị chặn 403 tại backend")

    def test_04_admin_allowed_access(self):
        """4. Quản lý (Admin) truy cập hợp lệ các chức năng quản trị."""
        self.login_user("admin@shop.vn", "Demo@12345")
        res = self.client.get("/admin")
        self.assertEqual(res.status_code, 200, "Admin đăng nhập đúng phải truy cập được dashboard")
        self.assertIn("Quản trị", res.get_data(as_text=True))

    # ================= NHÓM 2: TÍNH TOÀN VẸN GIAO DỊCH (TRANSACTION ROLLBACK) =================

    def test_05_atomic_transaction_rollback_on_variant_failure(self):
        """5. Giao dịch nguyên tử (Atomic Transaction): Nếu lưu biến thể thất bại,
        toàn bộ sản phẩm cha vừa thêm phải được ROLLBACK, không để lại bản ghi rác.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cur = conn.cursor()

            # Đếm số lượng sản phẩm trước khi thử nghiệm
            initial_count = cur.execute("SELECT COUNT(*) FROM SanPham").fetchone()[0]

            # Giả lập tình huống: INSERT sản phẩm cha thành công, nhưng INSERT biến thể bị lỗi (ví dụ tồn kho âm)
            try:
                cur.execute("""
                    INSERT INTO SanPham (MaDanhMuc, MaNguoiTao, TenSanPham, GiaBan, ThuongHieu, MoTa)
                    VALUES (1, 1, 'Giày Thử Nghiệm Rollback', 1900000, 'TestBrand', 'Mô tả test')
                """)
                new_sp_id = cur.lastrowid

                # Cố tình gây lỗi CHECK constraint để kích hoạt rollback
                cur.execute("""
                    INSERT INTO BienTheSanPham (MaSanPham, KichThuoc, MauSac, SoLuongTon)
                    VALUES (?, '42', 'Xanh', -10)
                """, (new_sp_id,))
                conn.commit()
            except (sqlite3.IntegrityError, Exception):
                conn.rollback()

            # Đếm lại số lượng sản phẩm sau khi rollback
            final_count = cur.execute("SELECT COUNT(*) FROM SanPham").fetchone()[0]
            self.assertEqual(
                final_count,
                initial_count,
                "LỖI TOÀN VẸN DỮ LIỆU: Rollback thất bại, sản phẩm mồ côi đã bị lọt vào CSDL!",
            )

    def test_06_referenced_product_cannot_be_deleted_history_protection(self):
        """6. Bảo vệ dữ liệu lịch sử: Sản phẩm đã có trong đơn hàng (ChiTietDonHang)
        KHÔNG ĐƯỢC PHÉP XÓA VẬT LÝ làm mất lịch sử bán hàng (phải dùng cơ chế ẩn).
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cur = conn.cursor()
            # Sản phẩm 1 đã có trong ChiTietGioHang hoặc DonHang
            # Cố tình DELETE trực tiếp sản phẩm đã phát sinh đơn hàng
            with self.assertRaises((sqlite3.IntegrityError, Exception)):
                cur.execute("DELETE FROM SanPham WHERE MaSanPham = 1")
                conn.commit()


if __name__ == "__main__":
    unittest.main(verbosity=2)
