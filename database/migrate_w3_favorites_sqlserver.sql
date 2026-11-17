-- AI-assisted W3-057. Chỉ chạy sau BACKUP, migration visibility, trên DB test trước.
-- Tạo bảng bổ sung, KHÔNG DROP bảng hoặc ghi đè dữ liệu cũ.
IF OBJECT_ID(N'dbo.YeuThich',N'U') IS NULL
BEGIN
    CREATE TABLE dbo.YeuThich (
        MaNguoiDung INT NOT NULL,
        MaSanPham INT NOT NULL,
        CONSTRAINT PK_YeuThich PRIMARY KEY (MaNguoiDung,MaSanPham),
        CONSTRAINT FK_YeuThich_NguoiDung FOREIGN KEY (MaNguoiDung) REFERENCES dbo.NguoiDung(MaNguoiDung) ON DELETE CASCADE,
        CONSTRAINT FK_YeuThich_SanPham FOREIGN KEY (MaSanPham) REFERENCES dbo.SanPham(MaSanPham) ON DELETE CASCADE
    );
END;
GO
SELECT COUNT(*) AS SoYeuThich FROM dbo.YeuThich;
