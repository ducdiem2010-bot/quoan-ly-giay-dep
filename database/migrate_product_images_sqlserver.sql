/* Chạy một lần trên SQL Server để bật thư viện ảnh sản phẩm. Không xóa dữ liệu cũ. */
IF OBJECT_ID(N'dbo.SanPhamHinhAnh', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.SanPhamHinhAnh (
        MaHinhAnh INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        MaSanPham INT NOT NULL,
        TenTep NVARCHAR(255) NOT NULL,
        LaAnhDaiDien BIT NOT NULL CONSTRAINT DF_SanPhamHinhAnh_Cover DEFAULT (0),
        ThuTu INT NOT NULL CONSTRAINT DF_SanPhamHinhAnh_Order DEFAULT (0),
        NgayTao DATETIME2 NOT NULL CONSTRAINT DF_SanPhamHinhAnh_Date DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_SanPhamHinhAnh_SanPham FOREIGN KEY (MaSanPham) REFERENCES dbo.SanPham(MaSanPham) ON DELETE CASCADE
    );
    CREATE INDEX IX_SanPhamHinhAnh_Product ON dbo.SanPhamHinhAnh(MaSanPham, LaAnhDaiDien, ThuTu);
END;
GO
