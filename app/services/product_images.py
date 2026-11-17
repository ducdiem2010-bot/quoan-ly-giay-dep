"""Dịch vụ quản lý và phân giải ảnh sản phẩm đồng bộ toàn hệ thống.

Ưu tiên:
1. Ảnh đại diện trong SanPhamHinhAnh (hoặc cột AnhDaiDien).
2. Nếu chưa có ảnh đại diện, lấy ảnh đầu tiên trong SanPhamHinhAnh.
3. Nếu chưa có ảnh upload, đối chiếu với ảnh thật trong images/storefront/ (12 sản phẩm ban đầu).
4. Nếu thực sự chưa có ảnh, trả về None (không dùng ảnh giả lập).
"""

from pathlib import Path
from flask import current_app, url_for
from ..db import query_all


# Bảng đối chiếu 12 sản phẩm gốc với 12 tệp ảnh thật trong static/images/storefront/
STOREFRONT_LOCAL_IMAGES = {
    1: "images/storefront/product-01.jpg",   # Nike Air Zoom Pegasus
    2: "images/storefront/product-02.jpg",   # Adidas Originals Superstar
    3: "images/storefront/product-03.jpg",   # Biti’s Hunter Sandal
    4: "images/storefront/product-04.jpg",   # Puma Suede Classic
    5: "images/storefront/product-05.jpg",   # Crocs Classic Clog
    6: "images/storefront/product-06.jpg",   # New Balance 574
    7: "images/storefront/product-07.jpg",   # Converse Chuck Taylor
    8: "images/storefront/product-08.jpg",   # Asics Gel Contend
    9: "images/storefront/product-09.jpg",   # Dép Adidas Adilette
    10: "images/storefront/product-10.jpg",  # Sandal Teva Hurricane
    11: "images/storefront/product-11.jpg",  # Sandal Học Sinh Chống Trượt
    12: "images/storefront/product-12.jpg",  # Giày Thể Thao Mẫu Ẩn
}

# Đối chiếu theo cặp (Tên sản phẩm, Thương hiệu) chuẩn hóa
STOREFRONT_NAME_BRAND_MAP = {
    ("nike air zoom pegasus", "nike"): "images/storefront/product-01.jpg",
    ("adidas originals superstar", "adidas"): "images/storefront/product-02.jpg",
    ("biti’s hunter sandal", "biti’s"): "images/storefront/product-03.jpg",
    ("puma suede classic", "puma"): "images/storefront/product-04.jpg",
    ("crocs classic clog", "crocs"): "images/storefront/product-05.jpg",
    ("new balance 574", "new balance"): "images/storefront/product-06.jpg",
    ("converse chuck taylor", "converse"): "images/storefront/product-07.jpg",
    ("asics gel contend", "asics"): "images/storefront/product-08.jpg",
    ("dép adidas adilette", "adidas"): "images/storefront/product-09.jpg",
    ("sandal teva hurricane", "teva"): "images/storefront/product-10.jpg",
    ("sandal học sinh chống trượt", "localshoes"): "images/storefront/product-11.jpg",
    ("giày thể thao mẫu ẩn", "localshoes"): "images/storefront/product-12.jpg",
}


def resolve_product_image_path(product):
    """Trả về đường dẫn tệp tương đối trong thư mục static của ứng dụng Flask.

    Ví dụ: 'uploads/products/shoe.jpg' hoặc 'images/storefront/product-01.jpg'.
    Quy tắc an toàn:
    1. Chỉ trả về đường dẫn nếu tệp thật sự tồn tại trên ổ đĩa.
    2. Lấy ảnh theo liên kết đúng trong database (SanPhamHinhAnh), ưu tiên ảnh đại diện.
    3. Nếu ảnh đại diện bị mất/không tồn tại trên đĩa, tự động thử ảnh phụ hợp lệ tiếp theo.
    4. Không bao giờ gán ảnh mẫu theo ID hoặc số thứ tự sản phẩm.
    5. Nếu sản phẩm thực sự chưa có ảnh hoặc file ảnh không tồn tại, trả về None.
    """
    if not product:
        return None

    pid = product.get("MaSanPham")
    try:
        pid = int(pid) if pid is not None else None
    except (ValueError, TypeError):
        pid = None

    static_root = Path(current_app.static_folder) if current_app else Path("app/static")

    def _get_valid_relative_path(filename):
        if not filename or not isinstance(filename, str):
            return None
        fn = filename.strip()
        if not fn or ".." in fn or "/" in fn or "\\" in fn:
            return None
        # Kiểm tra uploads/products/
        upload_path = static_root / "uploads" / "products" / fn
        if upload_path.is_file():
            return f"uploads/products/{fn}"
        # Kiểm tra images/storefront/
        storefront_path = static_root / "images" / "storefront" / fn
        if storefront_path.is_file():
            return f"images/storefront/{fn}"
        return None

    # 1. Truy vấn liên kết ảnh đúng trong SanPhamHinhAnh (ảnh đại diện trước, rồi đến các ảnh phụ)
    if pid is not None:
        try:
            images = query_all(
                """SELECT TenTep, LaAnhDaiDien FROM SanPhamHinhAnh
                   WHERE MaSanPham=?
                   ORDER BY LaAnhDaiDien DESC, ThuTu ASC, MaHinhAnh ASC""",
                (pid,)
            )
            for img in images:
                valid_path = _get_valid_relative_path(img.get("TenTep"))
                if valid_path:
                    return valid_path
        except Exception:
            pass

    # 2. Kiểm tra trường AnhDaiDien truyền sẵn (từ query/join catalog)
    upload_name = product.get("AnhDaiDien")
    if upload_name:
        valid_path = _get_valid_relative_path(upload_name)
        if valid_path:
            return valid_path

    # Sản phẩm thực sự chưa có ảnh hợp lệ trên đĩa
    return None


def get_product_image_url(product):
    """Trả về URL static hoàn chỉnh của ảnh sản phẩm để render trong thẻ <img>.

    Nếu sản phẩm chưa có ảnh, trả về None.
    """
    rel = resolve_product_image_path(product)
    if rel:
        return url_for("static", filename=rel)
    return None
