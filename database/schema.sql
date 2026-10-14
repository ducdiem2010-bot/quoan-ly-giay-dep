USE master;
GO
IF DB_ID(N'QuanLyBanHang') IS NULL
    CREATE DATABASE QuanLyBanHang COLLATE Vietnamese_100_CI_AS;
GO
USE QuanLyBanHang;
GO

/* Xoa bang cu (thu tu nguoc voi khoa ngoai) de chay lai nhieu lan */
DROP TABLE IF EXISTS ChiTietDonHang;
DROP TABLE IF EXISTS ChiTietGioHang;
DROP TABLE IF EXISTS DonHang;
DROP TABLE IF EXISTS GioHang;
DROP TABLE IF EXISTS BienTheSanPham;
DROP TABLE IF EXISTS SanPham;
DROP TABLE IF EXISTS DanhMuc;
DROP TABLE IF EXISTS NguoiDung;
DROP TABLE IF EXISTS VaiTro;
GO

/* ---------------------------- VAI TRO ----------------------------- */
CREATE TABLE VaiTro (
    MaVaiTro   INT IDENTITY(1,1) CONSTRAINT PK_VaiTro PRIMARY KEY,
    TenVaiTro  NVARCHAR(50)  NOT NULL CONSTRAINT UQ_VaiTro_Ten UNIQUE,
    MoTa       NVARCHAR(255) NULL
);
GO

/* --------------------------- NGUOI DUNG --------------------------- */
CREATE TABLE NguoiDung (
    MaNguoiDung  INT IDENTITY(1,1) CONSTRAINT PK_NguoiDung PRIMARY KEY,
    MaVaiTro     INT           NOT NULL,
    HoVaTen      NVARCHAR(100) NOT NULL,
    Email        NVARCHAR(150) NOT NULL CONSTRAINT UQ_NguoiDung_Email UNIQUE,
    MatKhauHash  NVARCHAR(255) NOT NULL,           -- luu HASH (bcrypt/argon2), khong luu mat khau thuong
    SoDienThoai  VARCHAR(15)   NULL,
    DiaChi       NVARCHAR(255) NULL,
    TrangThai    BIT           NOT NULL CONSTRAINT DF_NguoiDung_TrangThai DEFAULT 1, -- 1: hoat dong, 0: khoa
    NgayTao      DATETIME2(0)  NOT NULL CONSTRAINT DF_NguoiDung_NgayTao DEFAULT SYSDATETIME(),
    CONSTRAINT FK_NguoiDung_VaiTro FOREIGN KEY (MaVaiTro) REFERENCES VaiTro(MaVaiTro),
    CONSTRAINT CK_NguoiDung_Email CHECK (Email LIKE '%_@_%._%')
);
CREATE INDEX IX_NguoiDung_MaVaiTro ON NguoiDung(MaVaiTro);
GO

/* ---------------------------- DANH MUC ---------------------------- */
CREATE TABLE DanhMuc (
    MaDanhMuc  INT IDENTITY(1,1) CONSTRAINT PK_DanhMuc PRIMARY KEY,
    TenDanhMuc NVARCHAR(100) NOT NULL CONSTRAINT UQ_DanhMuc_Ten UNIQUE,
    MoTa       NVARCHAR(500) NULL
);
GO

/* ---------------------------- SAN PHAM ---------------------------- */
CREATE TABLE SanPham (
    MaSanPham   INT IDENTITY(1,1) CONSTRAINT PK_SanPham PRIMARY KEY,
    MaDanhMuc   INT            NOT NULL,
    MaNguoiTao  INT            NULL,
    TenSanPham  NVARCHAR(200)  NOT NULL,
    GiaBan      DECIMAL(18,2)  NOT NULL,
    ThuongHieu  NVARCHAR(100)  NULL,
    MoTa        NVARCHAR(MAX)  NULL,
    NgayTao     DATETIME2(0)   NOT NULL CONSTRAINT DF_SanPham_NgayTao DEFAULT SYSDATETIME(),
    CONSTRAINT FK_SanPham_DanhMuc  FOREIGN KEY (MaDanhMuc)  REFERENCES DanhMuc(MaDanhMuc),
    CONSTRAINT FK_SanPham_NguoiTao FOREIGN KEY (MaNguoiTao) REFERENCES NguoiDung(MaNguoiDung),
    CONSTRAINT CK_SanPham_GiaBan CHECK (GiaBan >= 0)
);
CREATE INDEX IX_SanPham_MaDanhMuc  ON SanPham(MaDanhMuc);
CREATE INDEX IX_SanPham_MaNguoiTao ON SanPham(MaNguoiTao);
CREATE INDEX IX_SanPham_TenSanPham ON SanPham(TenSanPham);
GO

/* ------------------------ BIEN THE SAN PHAM ----------------------- */
/* Kich thuoc, mau sac, ton kho nam o bien the (1 san pham - N bien the) */
CREATE TABLE BienTheSanPham (
    MaBienThe  INT IDENTITY(1,1) CONSTRAINT PK_BienTheSanPham PRIMARY KEY,
    MaSanPham  INT           NOT NULL,
    KichThuoc  NVARCHAR(30)  NOT NULL,
    MauSac     NVARCHAR(50)  NOT NULL,
    SoLuongTon INT           NOT NULL CONSTRAINT DF_BienThe_Ton DEFAULT 0,
    CONSTRAINT FK_BienThe_SanPham FOREIGN KEY (MaSanPham) REFERENCES SanPham(MaSanPham) ON DELETE CASCADE,
    CONSTRAINT UQ_BienThe UNIQUE (MaSanPham, KichThuoc, MauSac),
    CONSTRAINT CK_BienThe_Ton CHECK (SoLuongTon >= 0)
);
GO

/* ----------------------------- GIO HANG --------------------------- */
CREATE TABLE GioHang (
    MaGioHang   INT IDENTITY(1,1) CONSTRAINT PK_GioHang PRIMARY KEY,
    MaNguoiDung INT          NOT NULL CONSTRAINT UQ_GioHang_NguoiDung UNIQUE, -- quan he 1-1
    NgayTao     DATETIME2(0) NOT NULL CONSTRAINT DF_GioHang_NgayTao DEFAULT SYSDATETIME(),
    CONSTRAINT FK_GioHang_NguoiDung FOREIGN KEY (MaNguoiDung) REFERENCES NguoiDung(MaNguoiDung) ON DELETE CASCADE
);
GO

/* ------------------------ CHI TIET GIO HANG ----------------------- */
CREATE TABLE ChiTietGioHang (
    MaChiTietGioHang INT IDENTITY(1,1) CONSTRAINT PK_ChiTietGioHang PRIMARY KEY,
    MaGioHang        INT NOT NULL,
    MaBienThe        INT NOT NULL,
    SoLuong          INT NOT NULL CONSTRAINT DF_CTGH_SoLuong DEFAULT 1,
    CONSTRAINT FK_CTGH_GioHang  FOREIGN KEY (MaGioHang) REFERENCES GioHang(MaGioHang) ON DELETE CASCADE,
    CONSTRAINT FK_CTGH_BienThe  FOREIGN KEY (MaBienThe) REFERENCES BienTheSanPham(MaBienThe),
    CONSTRAINT UQ_CTGH UNIQUE (MaGioHang, MaBienThe),   -- 1 bien the chi 1 dong trong gio
    CONSTRAINT CK_CTGH_SoLuong CHECK (SoLuong > 0)
);
CREATE INDEX IX_CTGH_MaBienThe ON ChiTietGioHang(MaBienThe);
GO

/* ----------------------------- DON HANG --------------------------- */
CREATE TABLE DonHang (
    MaDonHang       INT IDENTITY(1,1) CONSTRAINT PK_DonHang PRIMARY KEY,
    MaNguoiDung     INT           NULL,
    NgayDat         DATETIME2(0)  NOT NULL CONSTRAINT DF_DonHang_NgayDat DEFAULT SYSDATETIME(),
    TrangThai       NVARCHAR(30)  NOT NULL CONSTRAINT DF_DonHang_TrangThai DEFAULT N'Chờ xác nhận',
    TongTien        DECIMAL(18,2) NOT NULL CONSTRAINT DF_DonHang_TongTien DEFAULT 0,
    CONSTRAINT FK_DonHang_NguoiDung FOREIGN KEY (MaNguoiDung) REFERENCES NguoiDung(MaNguoiDung),
    CONSTRAINT CK_DonHang_TrangThai CHECK (TrangThai IN
        (N'Chờ xác nhận', N'Đã xác nhận', N'Hoàn thành', N'Đã hủy')),
    CONSTRAINT CK_DonHang_TongTien CHECK (TongTien >= 0)
);
CREATE INDEX IX_DonHang_MaNguoiDung ON DonHang(MaNguoiDung, NgayDat DESC);
GO

/* ------------------------ CHI TIET DON HANG ----------------------- */
CREATE TABLE ChiTietDonHang (
    MaChiTietDon INT IDENTITY(1,1) CONSTRAINT PK_ChiTietDonHang PRIMARY KEY,
    MaDonHang    INT           NOT NULL,
    MaBienThe    INT           NOT NULL,
    SoLuong      INT           NOT NULL,
    DonGia       DECIMAL(18,2) NOT NULL,   -- gia tai thoi diem dat (khong doi khi SanPham.GiaBan doi)
    ThanhTien AS (SoLuong * DonGia) PERSISTED,
    CONSTRAINT FK_CTDH_DonHang FOREIGN KEY (MaDonHang) REFERENCES DonHang(MaDonHang) ON DELETE CASCADE,
    CONSTRAINT FK_CTDH_BienThe FOREIGN KEY (MaBienThe) REFERENCES BienTheSanPham(MaBienThe),
    CONSTRAINT UQ_CTDH UNIQUE (MaDonHang, MaBienThe),
    CONSTRAINT CK_CTDH_SoLuong CHECK (SoLuong > 0),
    CONSTRAINT CK_CTDH_DonGia  CHECK (DonGia >= 0)
);
CREATE INDEX IX_CTDH_MaBienThe ON ChiTietDonHang(MaBienThe);
GO

/* Chỉ nhận hàng tại cửa hàng: không có địa chỉ giao hàng.
   Quan hệ người tạo sản phẩm và tài khoản đặt hàng có thể 0..1. */

/* Tu dong cap nhat DonHang.TongTien khi them/sua/xoa chi tiet */
CREATE OR ALTER TRIGGER trg_CTDH_CapNhatTongTien
ON ChiTietDonHang
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE d
    SET TongTien = ISNULL((SELECT SUM(ThanhTien) FROM ChiTietDonHang WHERE MaDonHang = d.MaDonHang), 0)
    FROM DonHang d
    WHERE d.MaDonHang IN (SELECT MaDonHang FROM inserted UNION SELECT MaDonHang FROM deleted);
END;
GO

PRINT N'Tao schema thanh cong.';