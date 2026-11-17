-- ==============================================================================
-- SCRIPT MIGRATION BỔ SUNG SNAPSHOT LỊCH SỬ ĐƠN HÀNG (SQL SERVER)
-- Dự án: Website Quản lý Cửa hàng Giày dép - Nhóm 6
-- Thứ tự chạy: Chạy sau init_database_sqlserver.sql (hoặc upgrade_existing_sqlserver.sql)
-- Mục đích: Lưu giữ nguyên vẹn tên sản phẩm, màu sắc, kích thước tại thời điểm đặt hàng.
--           Sửa tên/giá/màu/size trong catalog không làm biến đổi nội dung đơn đã đặt.
--           Bảo toàn dữ liệu cũ: cập nhật snapshot từ dữ liệu hiện có cho các đơn cũ.
-- ==============================================================================

USE QuanLyBanHang;
GO

SET NOCOUNT ON;

-- 1. Bổ sung các cột snapshot vào bảng ChiTietDonHang nếu chưa có
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('ChiTietDonHang') AND name = 'TenSanPham')
BEGIN
    ALTER TABLE ChiTietDonHang ADD TenSanPham NVARCHAR(200) NULL;
    PRINT N'Đã thêm cột TenSanPham vào ChiTietDonHang.';
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('ChiTietDonHang') AND name = 'MauSac')
BEGIN
    ALTER TABLE ChiTietDonHang ADD MauSac NVARCHAR(50) NULL;
    PRINT N'Đã thêm cột MauSac vào ChiTietDonHang.';
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('ChiTietDonHang') AND name = 'KichThuoc')
BEGIN
    ALTER TABLE ChiTietDonHang ADD KichThuoc NVARCHAR(30) NULL;
    PRINT N'Đã thêm cột KichThuoc vào ChiTietDonHang.';
END
GO

-- 2. Bổ sung dữ liệu snapshot cho các đơn hàng cũ chưa có từ catalog hiện tại
UPDATE ct
SET ct.TenSanPham = sp.TenSanPham,
    ct.MauSac = bt.MauSac,
    ct.KichThuoc = bt.KichThuoc
FROM ChiTietDonHang ct
JOIN BienTheSanPham bt ON bt.MaBienThe = ct.MaBienThe
JOIN SanPham sp ON sp.MaSanPham = bt.MaSanPham
WHERE ct.TenSanPham IS NULL;
GO

PRINT N'Hoàn tất migration snapshot lịch sử đơn hàng cho SQL Server.';
GO
