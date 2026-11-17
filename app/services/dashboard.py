"""Thống kê chỉ đọc cho /admin. Không can thiệp giỏ hàng, đơn hoặc tồn kho."""
from flask import current_app
from ..db import query_all, query_one
from .inventory import LOW_STOCK_THRESHOLD


ORDERS_STATS_SQL = """
SELECT COUNT(*) AS total_orders,
       COALESCE(SUM(CASE WHEN dh.TrangThai='Chờ xác nhận' THEN 1 ELSE 0 END), 0) AS pending_orders,
       COALESCE(SUM(CASE WHEN dh.TrangThai='Hoàn thành'
                      AND dh.TrangThaiGiaoHang='Đã giao'
                      AND tg.TrangThaiThanhToan='Đã thanh toán'
                      THEN dh.TongTien - COALESCE(ret.Reduction,0)
                      ELSE 0 END),0) AS completed_order_value,
       -- Tiền đã ghi nhận vẫn cần theo dõi dù đơn bị hủy và đang chờ hoàn tiền.
       COALESCE(SUM(CASE WHEN tg.TrangThaiThanhToan='Đã thanh toán' THEN dh.TongTien ELSE 0 END), 0) AS paid_order_value,
       COALESCE(SUM(CASE WHEN tg.TrangThaiThanhToan='Đã thanh toán' THEN 1 ELSE 0 END), 0) AS paid_orders
FROM DonHang dh
LEFT JOIN (SELECT MaDonHang,SUM(TienGiamDoanhThu) AS Reduction FROM TraHangChiTiet GROUP BY MaDonHang) ret ON ret.MaDonHang=dh.MaDonHang
LEFT JOIN ThongTinGiaoDich tg ON tg.MaDonHang = dh.MaDonHang
"""

PRODUCT_STOCK_SQL = """
SELECT sp.MaSanPham, sp.TenSanPham, sp.ThuongHieu,
       (SELECT TenTep FROM SanPhamHinhAnh ia WHERE ia.MaSanPham=sp.MaSanPham AND ia.LaAnhDaiDien=1) AS AnhDaiDien,
       COALESCE(SUM(bt.SoLuongTon),0) AS TongTon
FROM SanPham sp
LEFT JOIN BienTheSanPham bt ON bt.MaSanPham=sp.MaSanPham
GROUP BY sp.MaSanPham, sp.TenSanPham, sp.ThuongHieu
ORDER BY sp.MaSanPham DESC
"""

# Bảng đối chiếu ảnh storefront mặc định theo tên và hãng
STOREFRONT_DEFAULT_IMAGES = {
    "nike air zoom pegasus|nike": "images/storefront/product-01.jpg",
    "adidas originals superstar|adidas": "images/storefront/product-02.jpg",
    "biti’s hunter sandal|biti’s": "images/storefront/product-03.jpg",
    "puma suede classic|puma": "images/storefront/product-04.jpg",
    "crocs classic clog|crocs": "images/storefront/product-05.jpg",
    "new balance 574|new balance": "images/storefront/product-06.jpg",
    "converse chuck taylor|converse": "images/storefront/product-07.jpg",
    "asics gel contend|asics": "images/storefront/product-08.jpg",
    "dép adidas adilette|adidas": "images/storefront/product-09.jpg",
    "sandal teva hurricane|teva": "images/storefront/product-10.jpg",
    "sandal học sinh chống trượt|localshoes": "images/storefront/product-11.jpg",
    "giày thể thao mẫu ẩn|localshoes": "images/storefront/product-12.jpg",
}


from .product_images import resolve_product_image_path


def resolve_product_image_relpath(p):
    """Tìm đường dẫn tệp ảnh đại diện thực tế cho sản phẩm (ưu tiên upload > storefront ảnh mẫu > placeholder chưa có ảnh)."""
    rel = resolve_product_image_path(p)
    if rel:
        return rel
    return "images/no-product-image.svg"


def get_dashboard_stats():
    """Trả về chỉ số thực tế; kết nối dữ liệu đơn và giao dịch."""
    products = query_all(PRODUCT_STOCK_SQL)
    for p in products:
        p['AnhHienThi'] = resolve_product_image_relpath(p)

    orders = query_one(ORDERS_STATS_SQL) or {}
    out_of_stock_products = [p for p in products if int(p['TongTon'] or 0) <= 0]
    out_of_stock = len(out_of_stock_products)
    low_stock = [p for p in products if 1 <= int(p['TongTon'] or 0) <= LOW_STOCK_THRESHOLD]

    is_sqlserver = current_app.config.get('DB_BACKEND') == 'sqlserver'
    completed_value = float(orders.get('completed_order_value') or 0)

    return {
        'total_products': len(products),
        'total_orders': int(orders.get('total_orders') or 0),
        'pending_orders': int(orders.get('pending_orders') or 0),
        'paid_orders': int(orders.get('paid_orders') or 0),
        'out_of_stock': out_of_stock,
        'out_of_stock_products': out_of_stock_products[:5],
        'low_stock_count': len(low_stock),
        'low_stock_products': low_stock[:5],
        'completed_order_value': completed_value,
        'paid_order_value': float(orders.get('paid_order_value') or 0),
        'verified_revenue': is_sqlserver,
        'stock_threshold': LOW_STOCK_THRESHOLD,
    }
