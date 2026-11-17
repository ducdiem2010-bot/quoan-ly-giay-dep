"""Danh sách sáu sản phẩm công khai mới nhất. Chỉ đọc cơ sở dữ liệu.

SQLite dùng HienThi, SQL Server ERD V2 dùng TrangThai.
Các trường trả về đồng nhất với _product_card.html của nhóm.
"""
from flask import current_app
from ..db import query_all

SQLITE_LATEST = """
SELECT sp.MaSanPham, sp.TenSanPham, sp.GiaBan, sp.ThuongHieu, sp.MoTa,
       sp.MaDanhMuc, dm.TenDanhMuc, sp.HienThi,
       (SELECT ia.TenTep FROM SanPhamHinhAnh ia
        WHERE ia.MaSanPham=sp.MaSanPham AND ia.LaAnhDaiDien=1
        ORDER BY ia.MaHinhAnh LIMIT 1) AS AnhDaiDien,
       COALESCE((SELECT SUM(bt.SoLuongTon) FROM BienTheSanPham bt
                 WHERE bt.MaSanPham=sp.MaSanPham),0) AS TongTon
FROM SanPham sp
JOIN DanhMuc dm ON dm.MaDanhMuc=sp.MaDanhMuc
WHERE sp.HienThi=1
ORDER BY sp.NgayTao DESC, sp.MaSanPham DESC
LIMIT ?
"""

# Truy vấn SQL Server đồng bộ với schema chính thức QuanLyBanHang (init_database_sqlserver.sql)
SQLSERVER_LATEST = """
SELECT TOP (?) sp.MaSanPham, sp.TenSanPham, sp.GiaBan, sp.ThuongHieu,
       sp.MoTa, sp.MaDanhMuc, dm.TenDanhMuc, sp.HienThi,
       (SELECT TOP 1 ia.TenTep FROM SanPhamHinhAnh ia
        WHERE ia.MaSanPham=sp.MaSanPham AND ia.LaAnhDaiDien=1
        ORDER BY ia.MaHinhAnh ASC) AS AnhDaiDien,
       COALESCE((SELECT SUM(bt.SoLuongTon) FROM BienTheSanPham bt
                 WHERE bt.MaSanPham=sp.MaSanPham),0) AS TongTon
FROM SanPham sp
JOIN DanhMuc dm ON dm.MaDanhMuc=sp.MaDanhMuc
WHERE sp.HienThi=1
ORDER BY sp.NgayTao DESC, sp.MaSanPham DESC
"""


def get_latest_products(limit=6):
    """Trả list[dict], không chỉnh sửa tồn kho hay dữ liệu sản phẩm."""
    limit = max(1, min(6, int(limit)))
    backend = current_app.config.get('DB_BACKEND', 'sqlite')
    if backend == 'sqlite':
        return query_all(SQLITE_LATEST, (limit,))
    if backend == 'sqlserver':
        return query_all(SQLSERVER_LATEST, (limit,))
    raise ValueError('DB_BACKEND không hợp lệ')
