"""Thống kê chỉ đọc cho /admin. Không can thiệp giỏ hàng, đơn hoặc tồn kho."""
from flask import current_app
from ..db import query_all, query_one
from .inventory import LOW_STOCK_THRESHOLD


ORDERS_STATS_SQL = """
SELECT COUNT(*) AS total_orders,
       COALESCE(SUM(CASE WHEN dh.TrangThai='Chờ xác nhận' THEN 1 ELSE 0 END), 0) AS pending_orders,
       COALESCE(SUM(CASE WHEN dh.TrangThai='Hoàn thành' THEN dh.TongTien ELSE 0 END), 0) AS completed_order_value,
       COALESCE(SUM(CASE WHEN tg.TrangThaiThanhToan='Đã thanh toán' AND dh.TrangThai<>'Đã hủy' THEN dh.TongTien ELSE 0 END), 0) AS paid_order_value,
       COALESCE(SUM(CASE WHEN tg.TrangThaiThanhToan='Đã thanh toán' THEN 1 ELSE 0 END), 0) AS paid_orders
FROM DonHang dh
LEFT JOIN ThongTinGiaoDich tg ON tg.MaDonHang = dh.MaDonHang
"""

PRODUCT_STOCK_SQL = """
SELECT sp.MaSanPham, sp.TenSanPham,
       COALESCE(SUM(bt.SoLuongTon),0) AS TongTon
FROM SanPham sp
LEFT JOIN BienTheSanPham bt ON bt.MaSanPham=sp.MaSanPham
GROUP BY sp.MaSanPham, sp.TenSanPham
ORDER BY sp.MaSanPham DESC
"""


def get_dashboard_stats():
    """Trả về chỉ số thực tế; kết nối dữ liệu đơn và giao dịch."""
    products = query_all(PRODUCT_STOCK_SQL)
    orders = query_one(ORDERS_STATS_SQL) or {}
    out_of_stock = sum(int(p['TongTon'] or 0) <= 0 for p in products)
    low_stock = [p for p in products if 1 <= int(p['TongTon'] or 0) <= LOW_STOCK_THRESHOLD]

    is_sqlserver = current_app.config.get('DB_BACKEND') == 'sqlserver'
    completed_value = float((orders.get('paid_order_value') if is_sqlserver else orders.get('completed_order_value')) or 0)

    return {
        'total_products': len(products),
        'total_orders': int(orders.get('total_orders') or 0),
        'pending_orders': int(orders.get('pending_orders') or 0),
        'paid_orders': int(orders.get('paid_orders') or 0),
        'out_of_stock': out_of_stock,
        'low_stock_count': len(low_stock),
        'low_stock_products': low_stock[:5],
        'completed_order_value': completed_value,
        'verified_revenue': is_sqlserver,
        'stock_threshold': LOW_STOCK_THRESHOLD,
    }
