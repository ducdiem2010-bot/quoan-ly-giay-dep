-- Nâng cấp độc lập, có thể chạy nhiều lần, KHÔNG xóa dữ liệu cũ.
USE QuanLyBanHang;
GO
IF OBJECT_ID(N'dbo.TraHangChiTiet',N'U') IS NULL
BEGIN
    CREATE TABLE dbo.TraHangChiTiet (
        MaTraHang INT IDENTITY(1,1) PRIMARY KEY,
        MaDonHang INT NOT NULL REFERENCES dbo.DonHang(MaDonHang),
        MaBienThe INT NOT NULL REFERENCES dbo.BienTheSanPham(MaBienThe),
        SoLuong INT NOT NULL CHECK(SoLuong>0),
        SoLuongTot INT NOT NULL CHECK(SoLuongTot>=0),
        SoLuongHong INT NOT NULL CHECK(SoLuongHong>=0),
        LyDo NVARCHAR(255) NULL,
        TienGiamDoanhThu DECIMAL(18,2) NOT NULL CHECK(TienGiamDoanhThu>=0),
        NguoiThucHien INT NULL REFERENCES dbo.NguoiDung(MaNguoiDung),
        HoVaTenNguoiThucHien NVARCHAR(100) NOT NULL,
        ThoiGian DATETIME2(0) NOT NULL DEFAULT SYSDATETIME(),
        MaYeuCau VARCHAR(64) NOT NULL UNIQUE,
        MaNhomTra NVARCHAR(64) NULL,
        CONSTRAINT CK_TraHang_Tong CHECK (SoLuongTot+SoLuongHong=SoLuong)
    );
    CREATE INDEX IX_TraHang_Don_BienThe ON dbo.TraHangChiTiet(MaDonHang,MaBienThe);
END
GO
IF OBJECT_ID(N'dbo.HoanTienGiaoDich',N'U') IS NULL
BEGIN
    CREATE TABLE dbo.HoanTienGiaoDich (
        MaHoanTien INT IDENTITY(1,1) PRIMARY KEY,
        MaDonHang INT NOT NULL REFERENCES dbo.DonHang(MaDonHang),
        SoTien DECIMAL(18,2) NOT NULL CHECK (SoTien>0),
        PhuongThuc VARCHAR(30) NOT NULL CHECK (PhuongThuc IN ('cash','bank_transfer','demo')),
        MaThamChieu NVARCHAR(100) NULL,
        NguoiXacNhan INT NULL REFERENCES dbo.NguoiDung(MaNguoiDung),
        HoVaTenNguoiXacNhan NVARCHAR(100) NOT NULL,
        ThoiGian DATETIME2(0) NOT NULL DEFAULT SYSDATETIME(),
        MaYeuCau VARCHAR(64) NOT NULL UNIQUE
    );
    CREATE INDEX IX_HoanTien_Don ON dbo.HoanTienGiaoDich(MaDonHang);
END
GO
IF OBJECT_ID(N'dbo.NhanVienDaXoa',N'U') IS NULL
BEGIN
    CREATE TABLE dbo.NhanVienDaXoa (
        MaNhanVienCu INT NOT NULL PRIMARY KEY,
        HoVaTen NVARCHAR(100) NOT NULL,
        Email NVARCHAR(150) NOT NULL,
        ThoiGianXoa DATETIME2(0) NOT NULL DEFAULT SYSDATETIME(),
        MaAdminXoa INT NULL
    );
END
GO
IF OBJECT_ID(N'dbo.NhatKyNhanVienDaXoa',N'U') IS NULL
BEGIN
    CREATE TABLE dbo.NhatKyNhanVienDaXoa (
        MaNhatKy INT IDENTITY(1,1) PRIMARY KEY,
        MaNhanVienCu INT NOT NULL REFERENCES dbo.NhanVienDaXoa(MaNhanVienCu),
        Loai VARCHAR(50) NOT NULL,
        MaThamChieu INT NOT NULL,
        VaiTroXuLy NVARCHAR(100) NOT NULL
    );
END
GO
