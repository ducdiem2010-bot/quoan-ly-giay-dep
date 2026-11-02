-- CHỈ chạy trên DATABASE TEST ĐÃ SAO LƯU; không drop, không seed lại dữ liệu thật.
-- W3 Admin: cờ hiển thị được thêm trên đúng schema 9 bảng nhóm; không tương đương schema của vs demo.
IF COL_LENGTH('dbo.SanPham', 'HienThi') IS NULL
BEGIN
 ALTER TABLE dbo.SanPham ADD HienThi BIT NOT NULL CONSTRAINT DF_SanPham_HienThi DEFAULT (1);
END;
GO
