-- MIGRATION KHÔNG PHÁ HUỶ: thêm cột hồ sơ khách hàng cho bảng NguoiDung.
-- Chạy trên CSDL đã backup. KHÔNG chạy schema.sql (có DROP TABLE). Chọn đúng database trước khi chạy.
IF COL_LENGTH(N'dbo.NguoiDung', N'Ho') IS NULL        ALTER TABLE dbo.NguoiDung ADD Ho NVARCHAR(60) NULL;
IF COL_LENGTH(N'dbo.NguoiDung', N'Ten') IS NULL       ALTER TABLE dbo.NguoiDung ADD Ten NVARCHAR(60) NULL;
IF COL_LENGTH(N'dbo.NguoiDung', N'GioiTinh') IS NULL  ALTER TABLE dbo.NguoiDung ADD GioiTinh NVARCHAR(10) NULL;
IF COL_LENGTH(N'dbo.NguoiDung', N'NgaySinh') IS NULL  ALTER TABLE dbo.NguoiDung ADD NgaySinh DATE NULL;
IF COL_LENGTH(N'dbo.NguoiDung', N'TinhThanh') IS NULL ALTER TABLE dbo.NguoiDung ADD TinhThanh NVARCHAR(60) NULL;
IF COL_LENGTH(N'dbo.NguoiDung', N'PhuongXa') IS NULL  ALTER TABLE dbo.NguoiDung ADD PhuongXa NVARCHAR(100) NULL;
GO
