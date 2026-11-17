-- ĐỐI SOÁT CHỈ ĐỌC. Chạy trên database đang sử dụng (SQLite hoặc SQL Server).
-- Không sửa tiền, không tự nhập kho và không xóa lịch sử.
SELECT t.MaTraHang,t.MaDonHang,t.MaBienThe,t.SoLuong,t.SoLuongTot,t.SoLuongHong,
       t.TienGiamDoanhThu,ct.DonGia,t.LyDo,t.ThoiGian
FROM TraHangChiTiet t
LEFT JOIN ChiTietDonHang ct ON ct.MaDonHang=t.MaDonHang AND ct.MaBienThe=t.MaBienThe
WHERE t.SoLuongHong>0 OR t.TienGiamDoanhThu=0
   OR ct.DonGia IS NULL OR t.TienGiamDoanhThu<>t.SoLuong*ct.DonGia;
SELECT MaHoanTien,MaDonHang,SoTien,PhuongThuc,ThoiGian
FROM HoanTienGiaoDich WHERE PhuongThuc NOT IN ('cash','bank_transfer');
SELECT * FROM HoanKhoChiTiet WHERE SoLuongCanHoan>SoLuongDaHoan+SoLuongHong;
