-- Chức năng Đánh giá sản phẩm (DanhGiaSanPham). Chạy sau BACKUP, trên DB test trước.
-- Chỉ tạo bảng/index bổ sung, KHÔNG DROP và KHÔNG ghi đè dữ liệu cũ.
IF OBJECT_ID(N'dbo.DanhGiaSanPham', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.DanhGiaSanPham (
        MaDanhGia        INT IDENTITY(1,1) NOT NULL,
        MaSanPham        INT NOT NULL,
        MaNguoiDung      INT NOT NULL,
        MaDonHang        INT NOT NULL,
        SoSao            INT NOT NULL,
        TieuDe           NVARCHAR(150) NULL,
        NoiDung          NVARCHAR(1000) NOT NULL,
        PhanHoiShop      NVARCHAR(500) NULL,
        NgayPhanHoi      DATETIME NULL,
        TrangThaiHienThi BIT NOT NULL CONSTRAINT DF_DanhGiaSanPham_HienThi DEFAULT 1,
        NgayDanhGia      DATETIME NOT NULL CONSTRAINT DF_DanhGiaSanPham_Ngay DEFAULT GETDATE(),
        CONSTRAINT PK_DanhGiaSanPham PRIMARY KEY (MaDanhGia),
        CONSTRAINT FK_DanhGiaSanPham_SanPham   FOREIGN KEY (MaSanPham)   REFERENCES dbo.SanPham(MaSanPham),
        CONSTRAINT FK_DanhGiaSanPham_NguoiDung FOREIGN KEY (MaNguoiDung) REFERENCES dbo.NguoiDung(MaNguoiDung),
        CONSTRAINT FK_DanhGiaSanPham_DonHang   FOREIGN KEY (MaDonHang)   REFERENCES dbo.DonHang(MaDonHang),
        CONSTRAINT CK_DanhGiaSanPham_SoSao CHECK (SoSao BETWEEN 1 AND 5),
        CONSTRAINT UQ_DanhGiaSanPham_User_SP_Don UNIQUE (MaNguoiDung, MaSanPham, MaDonHang)
    );
    CREATE INDEX IX_DanhGiaSanPham_MaSanPham_TrangThai
        ON dbo.DanhGiaSanPham (MaSanPham, TrangThaiHienThi, NgayDanhGia DESC);
END;
GO
SELECT COUNT(*) AS SoDanhGia FROM dbo.DanhGiaSanPham;
