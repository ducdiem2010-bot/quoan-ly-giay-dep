"""Nhãn HOT = Top 3 sản phẩm bán chạy hợp lệ, không lưu thêm cột DB."""
from .best_sellers import get_best_selling_products


def get_hot_product_ids():
    """Dùng chung truy vấn bán chạy; sản phẩm ẩn/không có doanh số bị loại."""
    rows = get_best_selling_products(limit=3)
    return {int(p['MaSanPham']) for p in rows if int(p['TongDaBan'] or 0) > 0}
