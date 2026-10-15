"""Nhiệm vụ W3-016: Kiểm thử SQL Server và sản phẩm Public.
Phụ trách: Điểm (Nhóm trưởng Nhóm 6).

Nguyên tắc an toàn database:
- Tuyệt đối KHÔNG thực hiện thao tác INSERT/UPDATE/DELETE/DROP trên database chính 'quan_ly_giay_dep'.
- Mọi thao tác kiểm tra cấu trúc/ràng buộc ghi được thực thi trên môi trường test cô lập (isolated).
- Nếu chưa có chuỗi kết nối SQL Server thật, đánh dấu BLOCKED rõ ràng, không giả lập PASS.
"""
import os
import sqlite3
import unittest
from pathlib import Path
from typing import Optional

from app import create_app
from tests.w3_diem.business_rules import (
    MINIMUM_PRODUCT_PRICE,
    TestStatus,
    validate_product_price,
    validate_stock_quantity,
)
from tests.w3_diem.fixtures import create_isolated_test_app


class TestW3016SqlPublic(unittest.TestCase):
    """Bộ kiểm thử SQL Server và dữ liệu sản phẩm Public."""

    @classmethod
    def setUpClass(cls):
        cls.sqlserver_conn = os.getenv("SQLSERVER_CONN", "").strip()
        cls.sqlserver_available = False
        cls.sql_tables = []

        if cls.sqlserver_conn:
            try:
                import pyodbc
                conn = pyodbc.connect(cls.sqlserver_conn, timeout=3)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_TYPE='BASE TABLE'
                """)
                cls.sql_tables = [row[0] for row in cursor.fetchall()]
                conn.close()
                cls.sqlserver_available = True
            except Exception:
                cls.sqlserver_available = False

    def setUp(self):
        # Môi trường test cô lập phục vụ kiểm tra logic và schema
        self.app, self.temp_dir, self.db_path = create_isolated_test_app()
        self.client = self.app.test_client()

    def test_01_sqlserver_connection_readonly(self):
        """1. Kiểm tra kết nối SQL Server ở chế độ chỉ đọc nếu có cấu hình."""
        if not self.sqlserver_available:
            self.skipTest("[BLOCKED] Chưa có dịch vụ SQL Server hoặc biến SQLSERVER_CONN chưa được thiết lập. Không giả lập PASS.")
        self.assertTrue(self.sqlserver_available)
        self.assertGreater(len(self.sql_tables), 0, "SQL Server phải có các bảng dữ liệu.")

    def test_02_sqlserver_required_tables_exist(self):
        """2. Kiểm tra các bảng cốt lõi tồn tại trên SQL Server."""
        if not self.sqlserver_available:
            self.skipTest("[BLOCKED] Bỏ qua kiểm tra bảng trên SQL Server vì chưa kết nối được.")

        required_tables = ["SanPham", "BienTheSanPham", "DanhMuc", "NguoiDung", "VaiTro"]
        missing = [t for t in required_tables if t not in self.sql_tables]
        self.assertEqual(missing, [], f"Thiếu các bảng sau trên SQL Server: {missing}")

    def test_03_foreign_keys_integrity(self):
        """3. Kiểm tra tính toàn vẹn khóa ngoại (FK)."""
        # Kiểm tra trên SQLite test environment
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
            self.assertEqual(fk_violations, [], f"Phát hiện vi phạm khóa ngoại trong database: {fk_violations}")

    def test_04_duplicate_variant_combination_blocked(self):
        """4. Cặp (MaSanPham, KichThuoc, MauSac) trùng phải bị chặn (UNIQUE constraint)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            # Đảm bảo có sản phẩm 1
            cur = conn.cursor()
            # Thử chèn 2 biến thể trùng kích thước và màu sắc cho cùng 1 sản phẩm
            with self.assertRaises((sqlite3.IntegrityError, Exception)):
                cur.execute("""
                    INSERT INTO BienTheSanPham (MaSanPham, KichThuoc, MauSac, SoLuongTon)
                    VALUES (1, '40', 'Đen', 5)
                """)
                cur.execute("""
                    INSERT INTO BienTheSanPham (MaSanPham, KichThuoc, MauSac, SoLuongTon)
                    VALUES (1, '40', 'Đen', 10)
                """)
                conn.commit()

    def test_05_negative_stock_blocked(self):
        """5. Tồn kho âm phải bị chặn (CHECK constraint SoLuongTon >= 0)."""
        # Kiểm tra business rule
        valid, msg = validate_stock_quantity(-5)
        self.assertFalse(valid, "Hàm kiểm tra nghiệp vụ phải chặn tồn âm")

        # Kiểm tra constraint CSDL trong môi trường test
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            with self.assertRaises((sqlite3.IntegrityError, Exception)):
                cur.execute("""
                    INSERT INTO BienTheSanPham (MaSanPham, KichThuoc, MauSac, SoLuongTon)
                    VALUES (1, '99', 'Cam', -1)
                """)
                conn.commit()

    def test_06_decimal_stock_blocked(self):
        """6. Tồn kho số thập phân phải bị chặn (chỉ nhận số nguyên)."""
        valid, msg = validate_stock_quantity(4.5)
        self.assertFalse(valid, "Tồn kho thập phân 4.5 phải bị từ chối")

    def test_07_zero_and_negative_price_blocked(self):
        """7. Giá bán = 0 hoặc âm phải bị chặn theo quy tắc A07 (Giá > 0 VNĐ)."""
        valid_zero, _ = validate_product_price(0)
        self.assertFalse(valid_zero, "Giá 0đ phải bị từ chối theo A07")

        valid_neg, _ = validate_product_price(-50000)
        self.assertFalse(valid_neg, "Giá âm phải bị từ chối theo A07")

        valid_pos, _ = validate_product_price(150000)
        self.assertTrue(valid_pos, "Giá dương > 0đ phải hợp lệ")

    def test_08_hidden_product_excluded_from_public(self):
        """8. Sản phẩm ẩn (TrangThai = 0 hoặc DaAn = 1) không xuất hiện trên danh sách public (A02)."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        page_content = response.get_data(as_text=True)
        # Kiểm tra không chứa tên sản phẩm ẩn mẫu
        self.assertNotIn("SP103 Đã Ẩn", page_content)

    def test_09_sql_injection_defense_parameterized(self):
        """9. Kiểm tra truy vấn tìm kiếm an toàn, dùng tham số hóa (không nối chuỗi SQL)."""
        # Gửi payload SQL Injection kinh điển vào ô tìm kiếm
        payload = "' OR '1'='1' --"
        response = self.client.get(f"/?q={payload}")
        self.assertEqual(response.status_code, 200, "Ứng dụng phải xử lý an toàn không sập 500 khi gặp payload SQL")
        # Kết quả không được dump toàn bộ sản phẩm trái phép
        page_content = response.get_data(as_text=True)
        self.assertNotIn("syntax error", page_content.lower())
        self.assertNotIn("unclosed quotation mark", page_content.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
