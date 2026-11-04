    /* =====================================================================
   schema_v2_proposal.sql  -  DE XUAT schema v2 cho QuanLyBanHang
   Nguon thiet ke : erd_da_chinh_sua_v2.svg (17 thuc the)
   Nguyen tac     : GIU NGUYEN schema cu (database QuanLyBanHang).
                    Schema moi nam trong database RIENG: QuanLyBanHang_V2.
   TRANG THAI     : DE XUAT - CHUA CHAY THU tren SQL Server. Can chay thu
                    va ghi lai ket qua that truoc khi nghiem thu.
   Luu y          : Script dung filtered index + computed column nen can
                    SET QUOTED_IDENTIFIER ON (neu dung sqlcmd thi them -I).
   ===================================================================== */
USE master;
GO
IF DB_ID(N'QuanLyBanHang_V2') IS NULL
    CREATE DATABASE QuanLyBanHang_V2 COLLATE Vietnamese_100_CI_AS;
GO
USE QuanLyBanHang_V2;
GO
SET QUOTED_IDENTIFIER ON;
SET ANSI_NULLS ON;
GO

/* Xoa bang (thu tu nguoc khoa ngoai) de chay lai nhieu lan - chi anh huong DB _V2 */
DROP TABLE IF EXISTS ThongTinTuVan;
DROP TABLE IF EXISTS ThongTinCuaHang;
DROP TABLE IF EXISTS HoaDon;
DROP TABLE IF EXISTS ChiTietDonHang;
DROP TABLE IF EXISTS DonHang;
DROP TABLE IF EXISTS DiaChiGiaoHang;
DROP TABLE IF EXISTS ChiTietGioHang;
DROP TABLE IF EXISTS GioHang;
DROP TABLE IF EXISTS BienTheSanPham;
DROP TABLE IF EXISTS KichThuoc;
DROP TABLE IF EXISTS MauSac;
DROP TABLE IF EXISTS HinhAnhSanPham;
DROP TABLE IF EXISTS SanPham;
DROP TABLE IF EXISTS ThuongHieu;
DROP TABLE IF EXISTS DanhMuc;
DROP TABLE IF EXISTS NguoiDung;
DROP TABLE IF EXISTS VaiTro;
GO

/* ============================ 1. VAI TRO ============================ */
CREATE TABLE VaiTro (
    MaVaiTro  INT IDENTITY(1,1) CONSTRAINT PK_VaiTro PRIMARY KEY,
    TenVaiTro NVARCHAR(50)  NOT NULL CONSTRAINT UQ_VaiTro_Ten UNIQUE,
    MoTa      NVARCHAR(255) NULL
);
GO

/* ========================== 2. NGUOI DUNG ========================== */
/* ERD v2: dang nhap bang TenDangNhap (UQ); khong con Email, DiaChi
   (dia chi chuyen sang bang DiaChiGiaoHang). */
CREATE TABLE NguoiDung (
    MaNguoiDung  INT IDENTITY(1,1) CONSTRAINT PK_NguoiDung PRIMARY KEY,
    MaVaiTro     INT           NOT NULL,
    HoVaTen      NVARCHAR(100) NOT NULL,
    TenDangNhap  VARCHAR(50)   NOT NULL CONSTRAINT UQ_NguoiDung_TenDangNhap UNIQUE,
    MatKhauHash  NVARCHAR(255) NOT NULL,   -- luu HASH (bcrypt/argon2), khong luu mat khau thuong
    SoDienThoai  VARCHAR(15)   NULL,
    TrangThai    BIT           NOT NULL CONSTRAINT DF_NguoiDung_TrangThai DEFAULT 1, -- 1: hoat dong, 0: khoa
    NgayTao      DATETIME2(0)  NOT NULL CONSTRAINT DF_NguoiDung_NgayTao DEFAULT SYSDATETIME(),
    CONSTRAINT FK_NguoiDung_VaiTro FOREIGN KEY (MaVaiTro) REFERENCES VaiTro(MaVaiTro),
    CONSTRAINT CK_NguoiDung_TenDangNhap CHECK (LEN(TenDangNhap) >= 3 AND TenDangNhap NOT LIKE '% %'),
    CONSTRAINT CK_NguoiDung_SDT CHECK (SoDienThoai IS NULL OR SoDienThoai NOT LIKE '%[^0-9+]%')
);
CREATE INDEX IX_NguoiDung_MaVaiTro ON NguoiDung(MaVaiTro);
GO

/* ============================ 3. DANH MUC =========================== */
CREATE TABLE DanhMuc (
    MaDanhMuc  INT IDENTITY(1,1) CONSTRAINT PK_DanhMuc PRIMARY KEY,
    TenDanhMuc NVARCHAR(100) NOT NULL CONSTRAINT UQ_DanhMuc_Ten UNIQUE,
    MoTa       NVARCHAR(500) NULL
);
GO

/* =========================== 4. THUONG HIEU ========================= */
CREATE TABLE ThuongHieu (
    MaThuongHieu  INT IDENTITY(1,1) CONSTRAINT PK_ThuongHieu PRIMARY KEY,
    TenThuongHieu NVARCHAR(100) NOT NULL CONSTRAINT UQ_ThuongHieu_Ten UNIQUE,
    MoTa          NVARCHAR(500) NULL
);
GO

/* ============================ 5. SAN PHAM =========================== */
/* ERD v2: bo GioiTinh va HinhAnh (anh chuyen sang HinhAnhSanPham);
   cot trang thai hien thi dat ten TrangThai (1: hien thi, 0: an). */
CREATE TABLE SanPham (
    MaSanPham    INT IDENTITY(1,1) CONSTRAINT PK_SanPham PRIMARY KEY,
    MaDanhMuc    INT           NOT NULL,
    MaThuongHieu INT           NULL,
    MaNguoiTao   INT           NOT NULL,
    TenSanPham   NVARCHAR(200) NOT NULL,
    GiaBan       DECIMAL(18,2) NOT NULL,
    MoTa         NVARCHAR(MAX) NULL,
    TrangThai    BIT           NOT NULL CONSTRAINT DF_SanPham_TrangThai DEFAULT 1,
    NgayTao      DATETIME2(0)  NOT NULL CONSTRAINT DF_SanPham_NgayTao DEFAULT SYSDATETIME(),
    CONSTRAINT FK_SanPham_DanhMuc    FOREIGN KEY (MaDanhMuc)    REFERENCES DanhMuc(MaDanhMuc),
    CONSTRAINT FK_SanPham_ThuongHieu FOREIGN KEY (MaThuongHieu) REFERENCES ThuongHieu(MaThuongHieu),
    CONSTRAINT FK_SanPham_NguoiTao   FOREIGN KEY (MaNguoiTao)   REFERENCES NguoiDung(MaNguoiDung),
    CONSTRAINT CK_SanPham_GiaBan CHECK (GiaBan >= 0)
);
CREATE INDEX IX_SanPham_MaDanhMuc    ON SanPham(MaDanhMuc);
CREATE INDEX IX_SanPham_MaThuongHieu ON SanPham(MaThuongHieu);
CREATE INDEX IX_SanPham_MaNguoiTao   ON SanPham(MaNguoiTao);
CREATE INDEX IX_SanPham_TenSanPham   ON SanPham(TenSanPham);
CREATE INDEX IX_SanPham_TrangThai_GiaBan ON SanPham(TrangThai, GiaBan);
GO

/* ======================= 6. HINH ANH SAN PHAM ======================= */
CREATE TABLE HinhAnhSanPham (
    MaHinhAnh   INT IDENTITY(1,1) CONSTRAINT PK_HinhAnhSanPham PRIMARY KEY,
    MaSanPham   INT           NOT NULL,
    DuongDanAnh NVARCHAR(500) NOT NULL,
    AnhDaiDien  BIT           NOT NULL CONSTRAINT DF_HinhAnh_DaiDien DEFAULT 0,
    CONSTRAINT FK_HinhAnh_SanPham FOREIGN KEY (MaSanPham) REFERENCES SanPham(MaSanPham) ON DELETE CASCADE
);
CREATE INDEX IX_HinhAnh_MaSanPham ON HinhAnhSanPham(MaSanPham);
/* Moi san pham toi da 1 anh dai dien */
CREATE UNIQUE INDEX UX_HinhAnh_DaiDien ON HinhAnhSanPham(MaSanPham) WHERE AnhDaiDien = 1;
GO

/* ============================ 7. MAU SAC ============================ */
CREATE TABLE MauSac (
    MaMau  INT IDENTITY(1,1) CONSTRAINT PK_MauSac PRIMARY KEY,
    TenMau NVARCHAR(50) NOT NULL CONSTRAINT UQ_MauSac_Ten UNIQUE
);
GO

/* =========================== 8. KICH THUOC ========================== */
CREATE TABLE KichThuoc (
    MaKichThuoc      INT IDENTITY(1,1) CONSTRAINT PK_KichThuoc PRIMARY KEY,
    GiaTriKichThuoc  NVARCHAR(30) NOT NULL CONSTRAINT UQ_KichThuoc_GiaTri UNIQUE
);
GO

/* ======================= 9. BIEN THE SAN PHAM ======================= */
/* ERD v2: mau/size tach thanh danh muc rieng, bien the tro FK vao do. */
CREATE TABLE BienTheSanPham (
    MaBienThe   INT IDENTITY(1,1) CONSTRAINT PK_BienTheSanPham PRIMARY KEY,
    MaSanPham   INT NOT NULL,
    MaMau       INT NOT NULL,
    MaKichThuoc INT NOT NULL,
    SoLuongTon  INT NOT NULL CONSTRAINT DF_BienThe_Ton DEFAULT 0,
    CONSTRAINT FK_BienThe_SanPham   FOREIGN KEY (MaSanPham)   REFERENCES SanPham(MaSanPham) ON DELETE CASCADE,
    CONSTRAINT FK_BienThe_MauSac    FOREIGN KEY (MaMau)       REFERENCES MauSac(MaMau),
    CONSTRAINT FK_BienThe_KichThuoc FOREIGN KEY (MaKichThuoc) REFERENCES KichThuoc(MaKichThuoc),
    CONSTRAINT UQ_BienThe UNIQUE (MaSanPham, MaMau, MaKichThuoc),
    CONSTRAINT CK_BienThe_Ton CHECK (SoLuongTon >= 0)
);
CREATE INDEX IX_BienThe_MauSac_KichThuoc ON BienTheSanPham(MaMau, MaKichThuoc) INCLUDE (MaSanPham);
CREATE INDEX IX_BienThe_MaKichThuoc ON BienTheSanPham(MaKichThuoc);
GO

/* ============================ 10. GIO HANG ========================== */
CREATE TABLE GioHang (
    MaGioHang   INT IDENTITY(1,1) CONSTRAINT PK_GioHang PRIMARY KEY,
    MaNguoiDung INT          NOT NULL CONSTRAINT UQ_GioHang_NguoiDung UNIQUE, -- 1 nguoi dung - 1 gio
    NgayTao     DATETIME2(0) NOT NULL CONSTRAINT DF_GioHang_NgayTao DEFAULT SYSDATETIME(),
    CONSTRAINT FK_GioHang_NguoiDung FOREIGN KEY (MaNguoiDung) REFERENCES NguoiDung(MaNguoiDung) ON DELETE CASCADE
);
GO

/* ======================== 11. CHI TIET GIO HANG ===================== */
CREATE TABLE ChiTietGioHang (
    MaChiTietGioHang INT IDENTITY(1,1) CONSTRAINT PK_ChiTietGioHang PRIMARY KEY,
    MaGioHang        INT NOT NULL,
    MaBienThe        INT NOT NULL,
    SoLuong          INT NOT NULL CONSTRAINT DF_CTGH_SoLuong DEFAULT 1,
    CONSTRAINT FK_CTGH_GioHang FOREIGN KEY (MaGioHang) REFERENCES GioHang(MaGioHang) ON DELETE CASCADE,
    CONSTRAINT FK_CTGH_BienThe FOREIGN KEY (MaBienThe) REFERENCES BienTheSanPham(MaBienThe),
    CONSTRAINT UQ_CTGH UNIQUE (MaGioHang, MaBienThe),
    CONSTRAINT CK_CTGH_SoLuong CHECK (SoLuong > 0)
);
CREATE INDEX IX_CTGH_MaBienThe ON ChiTietGioHang(MaBienThe);
GO

/* ====================== 12. DIA CHI GIAO HANG (MOI) ================= */
/* 1 nguoi dung - N dia chi; toi da 1 dia chi mac dinh moi nguoi. */
CREATE TABLE DiaChiGiaoHang (
    MaDiaChi      INT IDENTITY(1,1) CONSTRAINT PK_DiaChiGiaoHang PRIMARY KEY,
    MaNguoiDung   INT           NOT NULL,
    DiaChiChiTiet NVARCHAR(255) NOT NULL,
    MacDinh       BIT           NOT NULL CONSTRAINT DF_DiaChi_MacDinh DEFAULT 0,
    CONSTRAINT FK_DiaChi_NguoiDung FOREIGN KEY (MaNguoiDung) REFERENCES NguoiDung(MaNguoiDung) ON DELETE CASCADE
);
CREATE INDEX IX_DiaChi_MaNguoiDung ON DiaChiGiaoHang(MaNguoiDung);
CREATE UNIQUE INDEX UX_DiaChi_MacDinh ON DiaChiGiaoHang(MaNguoiDung) WHERE MacDinh = 1;
GO

/* ============================ 13. DON HANG ========================== */
/* ERD v2: them thong tin nguoi nhan, tien/phi ship, thanh toan,
   xac nhan, giao hang, huy. Toan bo dung DECIMAL(18,2) va DATETIME2(0). */
CREATE TABLE DonHang (
    MaDonHang                INT IDENTITY(1,1) CONSTRAINT PK_DonHang PRIMARY KEY,
    MaNguoiDung              INT           NOT NULL,           -- khach dat
    MaNVXacNhan              INT           NULL,               -- nhan vien xac nhan
    MaNVCapNhatGiaoHang      INT           NULL,               -- nhan vien cap nhat giao hang
    NgayDat                  DATETIME2(0)  NOT NULL CONSTRAINT DF_DonHang_NgayDat DEFAULT SYSDATETIME(),
    TenNguoiNhan             NVARCHAR(100) NOT NULL,
    SdtNguoiNhan             VARCHAR(15)   NOT NULL,
    DiaChiGiaoHang           NVARCHAR(255) NOT NULL,           -- ban chup tai thoi diem dat
    TienHang                 DECIMAL(18,2) NOT NULL CONSTRAINT DF_DonHang_TienHang DEFAULT 0,  -- trigger tu tinh
    PhiVanChuyen             DECIMAL(18,2) NOT NULL CONSTRAINT DF_DonHang_Phi DEFAULT 0,
    TongThanhToan            AS (TienHang + PhiVanChuyen) PERSISTED,
    PhuongThucThanhToan      NVARCHAR(30)  NOT NULL CONSTRAINT DF_DonHang_PTTT DEFAULT N'COD',
    TrangThaiThanhToan       NVARCHAR(30)  NOT NULL CONSTRAINT DF_DonHang_TTTT DEFAULT N'Chưa thanh toán',
    TrangThaiXacNhan         NVARCHAR(30)  NOT NULL CONSTRAINT DF_DonHang_TTXN DEFAULT N'Chờ xác nhận',
    ThoiDiemXacNhan          DATETIME2(0)  NULL,
    TrangThaiGiaoHang        NVARCHAR(30)  NOT NULL CONSTRAINT DF_DonHang_TTGH DEFAULT N'Chưa giao',
    ThoiDiemCapNhatGiaoHang  DATETIME2(0)  NULL,
    DaHuy                    BIT           NOT NULL CONSTRAINT DF_DonHang_DaHuy DEFAULT 0,
    ThoiDiemHuy              DATETIME2(0)  NULL,

    CONSTRAINT FK_DonHang_KhachHang FOREIGN KEY (MaNguoiDung)         REFERENCES NguoiDung(MaNguoiDung),
    CONSTRAINT FK_DonHang_NVXacNhan FOREIGN KEY (MaNVXacNhan)         REFERENCES NguoiDung(MaNguoiDung),
    CONSTRAINT FK_DonHang_NVGiao    FOREIGN KEY (MaNVCapNhatGiaoHang) REFERENCES NguoiDung(MaNguoiDung),

    CONSTRAINT CK_DonHang_SDT      CHECK (SdtNguoiNhan NOT LIKE '%[^0-9+]%'),
    CONSTRAINT CK_DonHang_TienHang CHECK (TienHang >= 0),
    CONSTRAINT CK_DonHang_Phi      CHECK (PhiVanChuyen >= 0),
    CONSTRAINT CK_DonHang_PTTT CHECK (PhuongThucThanhToan IN
        (N'COD', N'Chuyển khoản', N'Ví điện tử', N'Thẻ')),
    CONSTRAINT CK_DonHang_TTTT CHECK (TrangThaiThanhToan IN
        (N'Chưa thanh toán', N'Đã thanh toán', N'Hoàn tiền')),
    CONSTRAINT CK_DonHang_TTXN CHECK (TrangThaiXacNhan IN
        (N'Chờ xác nhận', N'Đã xác nhận', N'Từ chối')),
    CONSTRAINT CK_DonHang_TTGH CHECK (TrangThaiGiaoHang IN
        (N'Chưa giao', N'Đang chuẩn bị', N'Đang giao', N'Đã giao', N'Giao thất bại')),

    /* Xac nhan: cho xac nhan thi chua co NV/thoi diem; da xu ly thi phai co du ca hai */
    CONSTRAINT CK_DonHang_XacNhan CHECK (
        (TrangThaiXacNhan = N'Chờ xác nhận' AND ThoiDiemXacNhan IS NULL AND MaNVXacNhan IS NULL)
     OR (TrangThaiXacNhan <> N'Chờ xác nhận' AND ThoiDiemXacNhan IS NOT NULL AND MaNVXacNhan IS NOT NULL)),
    /* Giao hang: chi bat dau giao khi da xac nhan; da cap nhat thi phai co NV + thoi diem */
    CONSTRAINT CK_DonHang_GiaoHang CHECK (
        TrangThaiGiaoHang = N'Chưa giao'
     OR (TrangThaiXacNhan = N'Đã xác nhận'
         AND ThoiDiemCapNhatGiaoHang IS NOT NULL AND MaNVCapNhatGiaoHang IS NOT NULL)),
    /* Huy: co co huy <-> co thoi diem huy */
    CONSTRAINT CK_DonHang_Huy CHECK (
        (DaHuy = 0 AND ThoiDiemHuy IS NULL) OR (DaHuy = 1 AND ThoiDiemHuy IS NOT NULL)),
    /* Thoi gian hop ly */
    CONSTRAINT CK_DonHang_ThoiGian CHECK (
        (ThoiDiemXacNhan IS NULL OR ThoiDiemXacNhan >= NgayDat)
    AND (ThoiDiemHuy IS NULL OR ThoiDiemHuy >= NgayDat))
);
CREATE INDEX IX_DonHang_KhachHang ON DonHang(MaNguoiDung, NgayDat DESC);
CREATE INDEX IX_DonHang_NVXacNhan ON DonHang(MaNVXacNhan) WHERE MaNVXacNhan IS NOT NULL;
CREATE INDEX IX_DonHang_NVGiao    ON DonHang(MaNVCapNhatGiaoHang) WHERE MaNVCapNhatGiaoHang IS NOT NULL;
CREATE INDEX IX_DonHang_TrangThai ON DonHang(TrangThaiXacNhan, TrangThaiGiaoHang, TrangThaiThanhToan);
GO

/* ======================== 14. CHI TIET DON HANG ===================== */
/* ERD v2: luu ban chup TenSanPham/MauSac/KichThuoc de lich su don hang
   khong doi khi san pham/mau/size bi sua. */
CREATE TABLE ChiTietDonHang (
    MaChiTietDon INT IDENTITY(1,1) CONSTRAINT PK_ChiTietDonHang PRIMARY KEY,
    MaDonHang    INT           NOT NULL,
    MaBienThe    INT           NOT NULL,
    SoLuong      INT           NOT NULL,
    DonGia       DECIMAL(18,2) NOT NULL,   -- gia tai thoi diem dat
    TenSanPham   NVARCHAR(200) NOT NULL,   -- ban chup
    MauSac       NVARCHAR(50)  NOT NULL,   -- ban chup
    KichThuoc    NVARCHAR(30)  NOT NULL,   -- ban chup
    ThanhTien AS (SoLuong * DonGia) PERSISTED,
    CONSTRAINT FK_CTDH_DonHang FOREIGN KEY (MaDonHang) REFERENCES DonHang(MaDonHang) ON DELETE CASCADE,
    CONSTRAINT FK_CTDH_BienThe FOREIGN KEY (MaBienThe) REFERENCES BienTheSanPham(MaBienThe),
    CONSTRAINT UQ_CTDH UNIQUE (MaDonHang, MaBienThe),
    CONSTRAINT CK_CTDH_SoLuong CHECK (SoLuong > 0),
    CONSTRAINT CK_CTDH_DonGia  CHECK (DonGia >= 0)
);
CREATE INDEX IX_CTDH_MaBienThe ON ChiTietDonHang(MaBienThe);
GO

/* Tu dong cap nhat DonHang.TienHang khi them/sua/xoa chi tiet */
CREATE OR ALTER TRIGGER trg_CTDH_CapNhatTienHang
ON ChiTietDonHang
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE d
    SET TienHang = ISNULL((SELECT SUM(c.ThanhTien) FROM ChiTietDonHang c WHERE c.MaDonHang = d.MaDonHang), 0)
    FROM DonHang d
    WHERE d.MaDonHang IN (SELECT MaDonHang FROM inserted UNION SELECT MaDonHang FROM deleted);
END;
GO

/* ============================ 15. HOA DON (MOI) ===================== */
/* 1 don hang - toi da 1 hoa don (UQ MaDonHang) */
CREATE TABLE HoaDon (
    MaHoaDon  INT IDENTITY(1,1) CONSTRAINT PK_HoaDon PRIMARY KEY,
    MaDonHang INT         NOT NULL CONSTRAINT UQ_HoaDon_DonHang UNIQUE,
    SoHoaDon  VARCHAR(30) NOT NULL CONSTRAINT UQ_HoaDon_So UNIQUE,
    NgayLap   DATETIME2(0) NOT NULL CONSTRAINT DF_HoaDon_NgayLap DEFAULT SYSDATETIME(),
    CONSTRAINT FK_HoaDon_DonHang FOREIGN KEY (MaDonHang) REFERENCES DonHang(MaDonHang)
);
GO

/* ===================== 16. THONG TIN CUA HANG (MOI) ================= */
/* Thuc the doc lap, khong co khoa ngoai */
CREATE TABLE ThongTinCuaHang (
    MaCuaHang   INT IDENTITY(1,1) CONSTRAINT PK_ThongTinCuaHang PRIMARY KEY,
    TenCuaHang  NVARCHAR(150) NOT NULL,
    DiaChi      NVARCHAR(255) NOT NULL,
    SoDienThoai VARCHAR(15)   NULL,
    Zalo        NVARCHAR(100) NULL,
    Facebook    NVARCHAR(255) NULL
);
GO

/* ===================== 17. THONG TIN TU VAN (MOI) =================== */
CREATE TABLE ThongTinTuVan (
    MaTuVan        INT IDENTITY(1,1) CONSTRAINT PK_ThongTinTuVan PRIMARY KEY,
    TieuDe         NVARCHAR(200) NOT NULL,
    NoiDungTuVan   NVARCHAR(MAX) NOT NULL,
    ThongTinLienHe NVARCHAR(255) NULL,
    NgayCapNhat    DATETIME2(0)  NOT NULL CONSTRAINT DF_TuVan_NgayCapNhat DEFAULT SYSDATETIME()
);
GO

PRINT N'Tao schema v2 (de xuat) xong - chua duoc kiem chung tren may that.';
