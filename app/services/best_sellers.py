"""Sản phẩm bán chạy theo số lượng bán thực tế, không tạo doanh số giả.

V1/SQLite: chỉ đếm đơn Hoàn thành. SQL Server V2 dùng bộ điều kiện
Đã xác nhận + Đã giao + Đã thanh toán + chưa hủy (V2 chưa runtime-test).
"""
from flask import current_app
from ..db import query_all

SQLITE_BEST_SELLERS = """
SELECT sp.MaSanPham, sp.TenSanPham, sp.GiaBan, sp.ThuongHieu, sp.MoTa,
       sp.MaDanhMuc, dm.TenDanhMuc, sp.HienThi,
       (SELECT ia.TenTep FROM SanPhamHinhAnh ia
        WHERE ia.MaSanPham=sp.MaSanPham AND ia.LaAnhDaiDien=1
        ORDER BY ia.MaHinhAnh LIMIT 1) AS AnhDaiDien,
       COALESCE((SELECT SUM(stock.SoLuongTon) FROM BienTheSanPham stock
                 WHERE stock.MaSanPham=sp.MaSanPham),0) AS TongTon,
       SUM(ct.SoLuong) AS TongDaBan
FROM ChiTietDonHang ct
JOIN DonHang dh ON dh.MaDonHang=ct.MaDonHang
JOIN BienTheSanPham bt ON bt.MaBienThe=ct.MaBienThe
JOIN SanPham sp ON sp.MaSanPham=bt.MaSanPham
JOIN DanhMuc dm ON dm.MaDanhMuc=sp.MaDanhMuc
WHERE dh.TrangThai='Hoàn thành' AND sp.HienThi=1
GROUP BY sp.MaSanPham, sp.TenSanPham, sp.GiaBan, sp.ThuongHieu,
         sp.MoTa, sp.MaDanhMuc, dm.TenDanhMuc, sp.HienThi
HAVING SUM(ct.SoLuong)>0
ORDER BY TongDaBan DESC, sp.MaSanPham ASC
LIMIT ?
"""

# Bản SQL Server V2 có schema_v2.sql nhưng chưa được test runtime.
# Siết điều kiện 'Đã thanh toán' để không gắn HOT cho đơn chưa thu tiền;
SQLSERVER_V2_BEST_SELLERS = """
SELECT TOP (?) sp.MaSanPham, sp.TenSanPham, sp.GiaBan,
       COALESCE(th.TenThuongHieu, N'') AS ThuongHieu,
       sp.MoTa, sp.MaDanhMuc, dm.TenDanhMuc, sp.TrangThai AS HienThi,
       CAST(NULL AS NVARCHAR(500)) AS AnhDaiDien,
       COALESCE((SELECT SUM(stock.SoLuongTon) FROM BienTheSanPham stock
                 WHERE stock.MaSanPham=sp.MaSanPham),0) AS TongTon,
       SUM(ct.SoLuong) AS TongDaBan
FROM ChiTietDonHang ct
JOIN DonHang dh ON dh.MaDonHang=ct.MaDonHang
JOIN BienTheSanPham bt ON bt.MaBienThe=ct.MaBienThe
JOIN SanPham sp ON sp.MaSanPham=bt.MaSanPham
JOIN DanhMuc dm ON dm.MaDanhMuc=sp.MaDanhMuc
LEFT JOIN ThuongHieu th ON th.MaThuongHieu=sp.MaThuongHieu
WHERE dh.DaHuy=0 AND dh.TrangThaiXacNhan=N'Đã xác nhận'
  AND dh.TrangThaiGiaoHang=N'Đã giao'
  AND dh.TrangThaiThanhToan=N'Đã thanh toán' AND sp.TrangThai=1
GROUP BY sp.MaSanPham, sp.TenSanPham, sp.GiaBan, th.TenThuongHieu,
         sp.MoTa, sp.MaDanhMuc, dm.TenDanhMuc, sp.TrangThai
HAVING SUM(ct.SoLuong)>0
ORDER BY TongDaBan DESC, sp.MaSanPham ASC
"""


def get_best_sellers_v1(limit=6):
    """Truy vấn SQLite/V1; giữ tên này để tương thích bản Nghĩa đã bàn giao."""
    return query_all(SQLITE_BEST_SELLERS, (max(1, min(6, int(limit))),))


def get_best_sellers_v2(limit=6):
    """SQL Server V2, chưa nghiệm thu thật; chưa chốt ràng buộc thanh toán."""
    return query_all(SQLSERVER_V2_BEST_SELLERS, (max(1, min(6, int(limit))),))


def get_best_selling_products(limit=6):
    backend = current_app.config.get('DB_BACKEND', 'sqlite')
    if backend == 'sqlite':
        return get_best_sellers_v1(limit)
    if backend == 'sqlserver':
        return get_best_sellers_v2(limit)
    raise ValueError('DB_BACKEND không hợp lệ')
