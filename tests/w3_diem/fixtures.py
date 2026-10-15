"""Dữ liệu kiểm thử mẫu và fixture dùng chung cho bộ test Tuần 3 của Điểm.
Tách biệt hoàn toàn với database chính 'quan_ly_giay_dep' để đảm bảo an toàn 100%.
"""
import os
import sqlite3
import tempfile
from contextlib import closing
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional
from werkzeug.security import generate_password_hash

from app import create_app
from .business_rules import UserRole


# Bộ dữ liệu mẫu chuẩn theo yêu cầu của Điểm
SAMPLE_PRODUCTS = [
    {
        "MaSanPham": 101,
        "TenSanPham": "Giày Chạy Bộ Pegasus SP101",
        "GiaBan": 2200000.0,
        "ThuongHieu": "Nike",
        "MaDanhMuc": 1,
        "TenDanhMuc": "Giày Thể Thao",
        "TrangThai": 1,  # Đang bán
        "GioiTinh": "Nam",
        "MoTa": "Giày chạy bộ cao cấp SP101",
        "variants": [
            {"KichThuoc": "41", "MauSac": "Đen", "SoLuongTon": 5},
            {"KichThuoc": "40", "MauSac": "Trắng", "SoLuongTon": 3},
            # CỰC KỲ QUAN TRỌNG: SP101 KHÔNG có Đen-40
        ],
        "images": [
            {"DuongDan": "sp101_avatar.jpg", "LaDaiDien": 1},
            {"DuongDan": "sp101_side.jpg", "LaDaiDien": 0},
        ],
    },
    {
        "MaSanPham": 102,
        "TenSanPham": "Giày Đi Phố Ultraboost SP102",
        "GiaBan": 3100000.0,
        "ThuongHieu": "Adidas",
        "MaDanhMuc": 1,
        "TenDanhMuc": "Giày Thể Thao",
        "TrangThai": 1,  # Đang bán
        "GioiTinh": "Nam",
        "MoTa": "Giày dạo phố êm ái SP102",
        "variants": [
            {"KichThuoc": "40", "MauSac": "Đen", "SoLuongTon": 3},
            {"KichThuoc": "41", "MauSac": "Đen", "SoLuongTon": 0},  # Hết hàng
        ],
        "images": [
            {"DuongDan": "sp102_avatar.jpg", "LaDaiDien": 1},
        ],
    },
    {
        "MaSanPham": 103,
        "TenSanPham": "Giày Bí Mật SP103 Đã Ẩn",
        "GiaBan": 1500000.0,
        "ThuongHieu": "Converse",
        "MaDanhMuc": 2,
        "TenDanhMuc": "Giày Thời Trang",
        "TrangThai": 0,  # ĐÃ ẨN (Quy tắc A02)
        "GioiTinh": "Unisex",
        "MoTa": "Sản phẩm dừng bán hoặc chưa ra mắt",
        "variants": [
            {"KichThuoc": "39", "MauSac": "Đỏ", "SoLuongTon": 10},
        ],
        "images": [
            {"DuongDan": "sp103_hidden.jpg", "LaDaiDien": 1},
        ],
    },
    {
        "MaSanPham": 104,
        "TenSanPham": "Dép Quai Ngang Đơn Giản SP104",
        "GiaBan": 350000.0,
        "ThuongHieu": "Biti's",
        "MaDanhMuc": 3,
        "TenDanhMuc": "Dép & Sandal",
        "TrangThai": 1,
        "GioiTinh": "Unisex",
        "MoTa": "Dép đi mưa nhẹ nhàng không có biến thể",
        "variants": [],  # Sản phẩm chưa/không có biến thể
        "images": [
            {"DuongDan": "sp104_slide.jpg", "LaDaiDien": 1},
        ],
    },
]

# Tài khoản kiểm thử tiêu chuẩn theo các vai trò
TEST_ACCOUNTS = {
    "admin": {
        "email": "admin_test@shop.vn",
        "password": "AdminPassword@123",
        "role": UserRole.ADMIN,
        "name": "Quản Lý Cửa Hàng (Admin)",
    },
    "seller": {
        "email": "seller_test@shop.vn",
        "password": "SellerPassword@123",
        "role": UserRole.SELLER,
        "name": "Nhân Viên Bán Hàng (Seller)",
    },
    "customer_a": {
        "email": "customer_a@shop.vn",
        "password": "CustomerA@123",
        "role": UserRole.CUSTOMER,
        "name": "Khách Hàng Nguyễn Văn A",
    },
    "customer_b": {
        "email": "customer_b@shop.vn",
        "password": "CustomerB@123",
        "role": UserRole.CUSTOMER,
        "name": "Khách Hàng Trần Thị B",
    },
}


class CSRFExtractor(HTMLParser):
    """Trích xuất mã csrf_token từ form HTML."""
    def __init__(self):
        super().__init__()
        self.csrf_token: Optional[str] = None

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        if tag == "input" and attr_dict.get("name") == "csrf_token":
            self.csrf_token = attr_dict.get("value")


def extract_csrf_token(html_text: str) -> Optional[str]:
    """Hàm tiện ích bóc tách csrf_token từ chuỗi HTML."""
    parser = CSRFExtractor()
    parser.feed(html_text)
    return parser.csrf_token


def create_isolated_test_app(extra_config: dict = None):
    """Tạo Flask app chạy trên database SQLite riêng biệt trong thư mục tạm,
    được khởi tạo cấu trúc và nạp dữ liệu tuần 2 để test không ảnh hưởng gì tới DB thật.
    """
    temp_dir = tempfile.mkdtemp(prefix="w3_test_env_")
    db_file = os.path.join(temp_dir, "isolated_test.sqlite3")

    config = {
        "TESTING": True,
        "DB_BACKEND": "sqlite",
        "DATABASE": db_file,
        "SECRET_KEY": "w3-diem-test-secret-key-isolated",
        "WTF_CSRF_ENABLED": False,
    }
    if extra_config:
        config.update(extra_config)

    app = create_app(config)
    return app, temp_dir, db_file
