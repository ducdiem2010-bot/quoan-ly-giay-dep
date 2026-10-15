"""Quy tắc nghiệp vụ chính thức A01-A08 và các ràng buộc kiểm thử Nhóm 6 Tuần 3.
Nhóm trưởng Điểm chốt thống nhất toàn nhóm. Dùng làm nguồn chân lý (Single Source of Truth)
cho toàn bộ test suite và audit scripts. Không tự ý chỉnh sửa quy tắc.
"""
from dataclasses import dataclass
from enum import Enum
from typing import List, Set


class TestStatus(str, Enum):
    """Phân loại trạng thái kiểm thử chuẩn mực theo yêu cầu nghiệm thu."""
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    NOT_RUN = "NOT RUN"
    ERROR = "ERROR"


class UserRole(str, Enum):
    """3 nhóm người dùng chính thức theo thiết kế hệ thống."""
    GUEST = "Guest"
    CUSTOMER = "Customer"
    SELLER = "Seller"
    ADMIN = "Admin"


# A01: Ảnh sản phẩm - Cho phép nhiều ảnh, 1 ảnh đại diện
DEFAULT_PRODUCT_IMAGE = "shoe-default.svg"

# A02: Sản phẩm ẩn - Không xuất hiện trang public, không hiển thị trong yêu thích của khách
HIDDEN_STATUS_VALUE = 0
ACTIVE_STATUS_VALUE = 1

# A03: Chuẩn hóa tên danh mục để chống trùng lặp
def normalize_category_name(name: str) -> str:
    """Chuẩn hóa tên danh mục: xóa khoảng trắng thừa, đưa về chữ thường."""
    if not name:
        return ""
    return " ".join(name.strip().lower().split())


# A04: Xóa ảnh đại diện -> Phải chọn ảnh thay thế hoặc ảnh mặc định
FALLBACK_AVATAR_IMAGE = DEFAULT_PRODUCT_IMAGE

# A05: Quy tắc upload ảnh
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_IMAGE_EXTENSIONS: Set[str] = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_IMAGE_MIME_TYPES: Set[str] = {
    "image/jpeg",
    "image/png",
    "image/webp",
}
# Magic bytes nhận diện nội dung ảnh thật sự, không chỉ dựa vào phần mở rộng
IMAGE_MAGIC_SIGNATURES = {
    "jpeg": [b"\xFF\xD8\xFF"],
    "png": [b"\x89PNG\r\n\x1a\n"],
    "webp": [b"RIFF"],  # WebP bắt đầu bằng 'RIFF....WEBP'
}

def validate_image_bytes(data: bytes, filename: str) -> tuple[bool, str]:
    """Kiểm tra file upload theo quy tắc A05:
    - Dung lượng <= 5MB
    - Phần mở rộng hợp lệ (.jpg, .jpeg, .png, .webp)
    - Magic bytes thực tế khớp định dạng
    """
    if len(data) > MAX_IMAGE_SIZE_BYTES:
        return False, f"Dung lượng vượt quá 5MB ({len(data)} bytes)"

    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return False, f"Đuôi file {ext} không được phép (chỉ nhận JPG/PNG/WebP)"

    # Kiểm tra magic bytes
    if ext in {".jpg", ".jpeg"}:
        if not data.startswith(b"\xFF\xD8\xFF"):
            return False, "File giả mạo định dạng JPEG/JPG"
    elif ext == ".png":
        if not data.startswith(b"\x89PNG\r\n\x1a\n"):
            return False, "File giả mạo định dạng PNG"
    elif ext == ".webp":
        if not (data.startswith(b"RIFF") and b"WEBP" in data[:16]):
            return False, "File giả mạo định dạng WebP"

    return True, "Hợp lệ"


# A06: Size sản phẩm - Chuỗi ký tự, không nhầm giới tính/độ tuổi
VALID_SIZE_EXAMPLES: List[str] = ["38", "39", "40", "41", "42", "43", "44", "S", "M", "L", "XL"]
VALID_GENDERS: Set[str] = {"Nam", "Nữ", "Unisex", "Trẻ em"}

# A07: Giá bán sản phẩm - Bắt buộc > 0 VNĐ
MINIMUM_PRODUCT_PRICE = 1.0  # VNĐ

def validate_product_price(price) -> tuple[bool, str]:
    """Kiểm tra giá bán sản phẩm: > 0, số thực/nguyên dương, từ chối <=0, âm hoặc ký tự."""
    try:
        val = float(price)
        if val <= 0:
            return False, "Giá bán phải lớn hơn 0 VNĐ (Quy tắc A07)"
        return True, "Hợp lệ"
    except (ValueError, TypeError):
        return False, "Giá bán phải là số hợp lệ"


# Tồn kho: Số nguyên >= 0
def validate_stock_quantity(stock) -> tuple[bool, str]:
    """Kiểm tra tồn kho: số nguyên không âm, từ chối số âm hoặc số thập phân."""
    try:
        if isinstance(stock, float) and not stock.is_integer():
            return False, "Số lượng tồn kho phải là số nguyên, không được là số thập phân"
        val = int(stock)
        if val < 0:
            return False, "Số lượng tồn kho không được âm (>= 0)"
        return True, "Hợp lệ"
    except (ValueError, TypeError):
        return False, "Số lượng tồn kho không hợp lệ"


# A08: Hợp đồng API / URL Public
PUBLIC_QUERY_CONTRACT = [
    "q",
    "brand_id",
    "type_id",
    "gender",
    "color_id",
    "size_id",
    "price_min",
    "price_max",
    "sort",
    "page",
]

# Ràng buộc biến thể: Lọc màu VÀ size phải trên CÙNG MỘT biến thể
@dataclass
class ProductVariantRule:
    """Biến thể sản phẩm: (MaSanPham, KichThuoc, MauSac) là duy nhất."""
    product_id: int
    size: str
    color: str
    stock: int


def match_variant_filter(variants: List[dict], color_filter: str = None, size_filter: str = None) -> bool:
    """Quy tắc lọc: nếu truyền cả màu VÀ size, phải tồn tại ít nhất 1 biến thể
    có CẢ HAI giá trị đó và có tồn kho hợp lệ. Không được lấy màu của biến thể A
    ghép với size của biến thể B.
    """
    for v in variants:
        color_match = True
        size_match = True
        if color_filter:
            color_match = str(v.get("MauSac", "")).strip().lower() == color_filter.strip().lower()
        if size_filter:
            size_match = str(v.get("KichThuoc", "")).strip().lower() == size_filter.strip().lower()
        if color_match and size_match:
            return True
    return False
