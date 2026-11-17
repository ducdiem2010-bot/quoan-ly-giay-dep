-- Chạy SAU migrate_returns_refunds_staff_sqlserver.sql nếu đang nâng cấp DB cũ.
-- Chỉ bổ sung cột nullable, không DROP, UPDATE hay suy đoán nhóm của lịch sử.
IF OBJECT_ID(N'dbo.TraHangChiTiet', N'U') IS NOT NULL
AND COL_LENGTH(N'dbo.TraHangChiTiet', N'MaNhomTra') IS NULL
    ALTER TABLE dbo.TraHangChiTiet ADD MaNhomTra NVARCHAR(64) NULL;
GO
IF OBJECT_ID(N'dbo.TraHangChiTiet', N'U') IS NOT NULL
AND NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'dbo.TraHangChiTiet') AND name=N'IX_TraHang_Nhom')
    CREATE INDEX IX_TraHang_Nhom ON dbo.TraHangChiTiet(MaDonHang, MaNhomTra);
GO
