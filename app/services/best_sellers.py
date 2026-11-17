"""Sản phẩm bán chạy theo số lượng bán thực tế, không tạo doanh số giả.

SQLite/SQL Server: chỉ đếm bán ròng của đơn Hoàn thành, đã giao và đã thanh toán.
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
       SUM((ct.SoLuong - COALESCE(ret.ReturnedQty,0))) AS TongDaBan
FROM ChiTietDonHang ct
LEFT JOIN (SELECT MaDonHang,MaBienThe,SUM(SoLuong) AS ReturnedQty
           FROM TraHangChiTiet GROUP BY MaDonHang,MaBienThe) ret
 ON ret.MaDonHang=ct.MaDonHang AND ret.MaBienThe=ct.MaBienThe
JOIN DonHang dh ON dh.MaDonHang=ct.MaDonHang
JOIN BienTheSanPham bt ON bt.MaBienThe=ct.MaBienThe
JOIN SanPham sp ON sp.MaSanPham=bt.MaSanPham
JOIN DanhMuc dm ON dm.MaDanhMuc=sp.MaDanhMuc
WHERE dh.TrangThai='Hoàn thành' AND sp.HienThi=1
  AND EXISTS (SELECT 1 FROM ThongTinGiaoDich tg WHERE tg.MaDonHang=dh.MaDonHang AND tg.TrangThaiThanhToan = 'Đã thanh toán')
  AND dh.TrangThaiGiaoHang = 'Đã giao'
GROUP BY sp.MaSanPham, sp.TenSanPham, sp.GiaBan, sp.ThuongHieu,
         sp.MoTa, sp.MaDanhMuc, dm.TenDanhMuc, sp.HienThi
HAVING SUM((ct.SoLuong - COALESCE(ret.ReturnedQty,0)))>0
ORDER BY TongDaBan DESC, sp.MaSanPham ASC
LIMIT ?
"""

# Truy vấn SQL Server đồng bộ với schema chính thức QuanLyBanHang (init_database_sqlserver.sql)
# Chỉ tính đơn Hoàn thành, bảo đảm nhất quán với SQLite
SQLSERVER_BEST_SELLERS = """
SELECT TOP (?) sp.MaSanPham, sp.TenSanPham, sp.GiaBan, sp.ThuongHieu,
       sp.MoTa, sp.MaDanhMuc, dm.TenDanhMuc, sp.HienThi,
       (SELECT TOP 1 ia.TenTep FROM SanPhamHinhAnh ia
        WHERE ia.MaSanPham=sp.MaSanPham AND ia.LaAnhDaiDien=1
        ORDER BY ia.MaHinhAnh ASC) AS AnhDaiDien,
       COALESCE((SELECT SUM(stock.SoLuongTon) FROM BienTheSanPham stock
                 WHERE stock.MaSanPham=sp.MaSanPham),0) AS TongTon,
       SUM((ct.SoLuong - COALESCE(ret.ReturnedQty,0))) AS TongDaBan
FROM ChiTietDonHang ct
LEFT JOIN (SELECT MaDonHang,MaBienThe,SUM(SoLuong) AS ReturnedQty
           FROM TraHangChiTiet GROUP BY MaDonHang,MaBienThe) ret
 ON ret.MaDonHang=ct.MaDonHang AND ret.MaBienThe=ct.MaBienThe
JOIN DonHang dh ON dh.MaDonHang=ct.MaDonHang
JOIN BienTheSanPham bt ON bt.MaBienThe=ct.MaBienThe
JOIN SanPham sp ON sp.MaSanPham=bt.MaSanPham
JOIN DanhMuc dm ON dm.MaDanhMuc=sp.MaDanhMuc
WHERE dh.TrangThai=N'Hoàn thành' AND sp.HienThi=1
  AND EXISTS (SELECT 1 FROM ThongTinGiaoDich tg WHERE tg.MaDonHang=dh.MaDonHang AND tg.TrangThaiThanhToan = N'Đã thanh toán')
  AND dh.TrangThaiGiaoHang = N'Đã giao'
GROUP BY sp.MaSanPham, sp.TenSanPham, sp.GiaBan, sp.ThuongHieu,
         sp.MoTa, sp.MaDanhMuc, dm.TenDanhMuc, sp.HienThi
HAVING SUM((ct.SoLuong - COALESCE(ret.ReturnedQty,0)))>0
ORDER BY TongDaBan DESC, sp.MaSanPham ASC
"""


def get_best_sellers_v1(limit=6):
    """Truy vấn SQLite/V1; giữ tên này để tương thích bản Nghĩa đã bàn giao."""
    return query_all(SQLITE_BEST_SELLERS, (max(1, min(6, int(limit))),))


def get_best_sellers_v2(limit=6):
    """SQL Server đồng bộ schema QuanLyBanHang."""
    return query_all(SQLSERVER_BEST_SELLERS, (max(1, min(6, int(limit))),))


def get_best_selling_products(limit=6):
    backend = current_app.config.get('DB_BACKEND', 'sqlite')
    if backend == 'sqlite':
        return get_best_sellers_v1(limit)
    if backend == 'sqlserver':
        return get_best_sellers_v2(limit)
    raise ValueError('DB_BACKEND không hợp lệ')
