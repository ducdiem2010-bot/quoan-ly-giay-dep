-- Migration độc lập, chạy sau khi bảng DonHang và BienTheSanPham đã tồn tại.
-- Quản lý hủy đang giao: trạng thái hoàn tiền và phiếu nhập lại hàng thực nhận.
IF COL_LENGTH('DonHang', 'TrangThaiHoanTien') IS NULL
    ALTER TABLE DonHang ADD TrangThaiHoanTien NVARCHAR(50) NOT NULL
        CONSTRAINT DF_DonHang_TrangThaiHoanTien DEFAULT N'Không cần hoàn tiền';
GO
IF OBJECT_ID('HoanKhoChiTiet','U') IS NULL
BEGIN
    CREATE TABLE HoanKhoChiTiet (
        MaDonHang INT NOT NULL REFERENCES DonHang(MaDonHang),
        MaBienThe INT NOT NULL REFERENCES BienTheSanPham(MaBienThe),
        SoLuongCanHoan INT NOT NULL CHECK (SoLuongCanHoan>0),
        SoLuongDaHoan INT NOT NULL CONSTRAINT DF_HK_DaHoan DEFAULT 0 CHECK (SoLuongDaHoan>=0),
        SoLuongHong INT NOT NULL CONSTRAINT DF_HK_Hong DEFAULT 0 CHECK (SoLuongHong>=0),
        CONSTRAINT PK_HoanKhoChiTiet PRIMARY KEY (MaDonHang, MaBienThe),
        CONSTRAINT CK_HK_Tong CHECK (SoLuongDaHoan+SoLuongHong<=SoLuongCanHoan)
    );
END
GO
IF OBJECT_ID('LichSuHoanKho','U') IS NULL
BEGIN
    CREATE TABLE LichSuHoanKho (
        MaHoanKho INT IDENTITY(1,1) PRIMARY KEY,
        MaDonHang INT NOT NULL REFERENCES DonHang(MaDonHang),
        MaBienThe INT NOT NULL REFERENCES BienTheSanPham(MaBienThe),
        SoLuongNhapKho INT NOT NULL CHECK (SoLuongNhapKho>=0),
        SoLuongKhongBanDuoc INT NOT NULL CHECK (SoLuongKhongBanDuoc>=0),
        NguoiThucHien INT NULL REFERENCES NguoiDung(MaNguoiDung),
        ThoiGian DATETIME2(0) NOT NULL DEFAULT SYSDATETIME(),
        CONSTRAINT CK_LSHK_SoLuong CHECK (SoLuongNhapKho+SoLuongKhongBanDuoc>0)
    );
END
GO
