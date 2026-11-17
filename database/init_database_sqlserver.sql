-- ==============================================================================
-- SCRIPT KHỞI TẠO CƠ SỞ DỮ LIỆU MỚI HOÀN CHỈNH CHO SQL SERVER
-- Dự án: Website Quản lý Cửa hàng Giày dép - Nhóm 6
-- Bao gồm: Cấu trúc 14 bảng, ràng buộc khóa ngoại, chỉ mục, trigger tự động tính tiền,
--          và dữ liệu mẫu chuẩn (Admin, Seller, Customer, Danh mục, Thương hiệu, Sản phẩm).
-- ==============================================================================

USE master;
GO

IF DB_ID(N'QuanLyBanHang') IS NULL
BEGIN
    CREATE DATABASE QuanLyBanHang COLLATE Vietnamese_100_CI_AS;
    PRINT N'✓ Đã tạo mới cơ sở dữ liệu QuanLyBanHang.';
END
GO

USE QuanLyBanHang;
GO

SET NOCOUNT ON;

-- ------------------------------------------------------------------------------
-- 1. BẢNG VAI TRÒ
-- ------------------------------------------------------------------------------
IF OBJECT_ID('VaiTro', 'U') IS NULL
BEGIN
    CREATE TABLE VaiTro (
        MaVaiTro   INT IDENTITY(1,1) CONSTRAINT PK_VaiTro PRIMARY KEY,
        TenVaiTro  NVARCHAR(50)  NOT NULL CONSTRAINT UQ_VaiTro_Ten UNIQUE,
        MoTa       NVARCHAR(255) NULL
    );
END
GO

-- ------------------------------------------------------------------------------
-- 2. BẢNG NGƯỜI DÙNG (ADMIN, NHÂN VIÊN, KHÁCH HÀNG)
-- ------------------------------------------------------------------------------
IF OBJECT_ID('NguoiDung', 'U') IS NULL
BEGIN
    CREATE TABLE NguoiDung (
        MaNguoiDung  INT IDENTITY(1,1) CONSTRAINT PK_NguoiDung PRIMARY KEY,
        MaVaiTro     INT           NOT NULL CONSTRAINT FK_NguoiDung_VaiTro REFERENCES VaiTro(MaVaiTro),
        HoVaTen      NVARCHAR(100) NOT NULL,
        Email        NVARCHAR(150) NOT NULL CONSTRAINT UQ_NguoiDung_Email UNIQUE,
        MatKhauHash  NVARCHAR(255) NOT NULL,
        SoDienThoai  VARCHAR(20)   NULL,
        DiaChi       NVARCHAR(255) NULL,
        TrangThai    BIT           NOT NULL CONSTRAINT DF_NguoiDung_TrangThai DEFAULT 1,
        NgayTao      DATETIME2(0)  NOT NULL CONSTRAINT DF_NguoiDung_NgayTao DEFAULT SYSDATETIME(),
        Ho           NVARCHAR(50)  NULL,
        Ten          NVARCHAR(50)  NULL,
        GioiTinh     NVARCHAR(10)  NULL,
        NgaySinh     DATE          NULL,
        TinhThanh    NVARCHAR(100) NULL,
        PhuongXa     NVARCHAR(100) NULL,
        NguoiKhoa    INT           NULL CONSTRAINT FK_NguoiDung_NguoiKhoa REFERENCES NguoiDung(MaNguoiDung),
        ThoiGianKhoa DATETIME2(0)  NULL,
        GhiChuKhoa   NVARCHAR(255) NULL,
        CONSTRAINT CK_NguoiDung_Email CHECK (Email LIKE '%_@_%._%')
    );
    CREATE INDEX IX_NguoiDung_MaVaiTro ON NguoiDung(MaVaiTro);
END
GO

-- ------------------------------------------------------------------------------
-- 3. BẢNG DANH MỤC / LOẠI SẢN PHẨM
-- ------------------------------------------------------------------------------
IF OBJECT_ID('DanhMuc', 'U') IS NULL
BEGIN
    CREATE TABLE DanhMuc (
        MaDanhMuc  INT IDENTITY(1,1) CONSTRAINT PK_DanhMuc PRIMARY KEY,
        TenDanhMuc NVARCHAR(100) NOT NULL CONSTRAINT UQ_DanhMuc_Ten UNIQUE,
        MoTa       NVARCHAR(500) NULL
    );
END
GO

-- ------------------------------------------------------------------------------
-- 4. BẢNG THƯƠNG HIỆU
-- ------------------------------------------------------------------------------
IF OBJECT_ID('ThuongHieu', 'U') IS NULL
BEGIN
    CREATE TABLE ThuongHieu (
        MaThuongHieu  INT IDENTITY(1,1) CONSTRAINT PK_ThuongHieu PRIMARY KEY,
        TenThuongHieu NVARCHAR(100) NOT NULL CONSTRAINT UQ_ThuongHieu_Ten UNIQUE,
        MoTa          NVARCHAR(255) NULL
    );
END
GO

-- ------------------------------------------------------------------------------
-- 5. BẢNG MÀU SẮC & KÍCH THƯỚC
-- ------------------------------------------------------------------------------
IF OBJECT_ID('MauSac', 'U') IS NULL
BEGIN
    CREATE TABLE MauSac (
        MaMau   INT IDENTITY(1,1) CONSTRAINT PK_MauSac PRIMARY KEY,
        TenMau  NVARCHAR(50) NOT NULL CONSTRAINT UQ_MauSac_Ten UNIQUE,
        MaHex   VARCHAR(10)  NULL,
        MoTa    NVARCHAR(255) NULL
    );
END
GO

IF OBJECT_ID('KichThuoc', 'U') IS NULL
BEGIN
    CREATE TABLE KichThuoc (
        MaKichThuoc  INT IDENTITY(1,1) CONSTRAINT PK_KichThuoc PRIMARY KEY,
        TenKichThuoc NVARCHAR(30) NOT NULL CONSTRAINT UQ_KichThuoc_Ten UNIQUE,
        TenSize      NVARCHAR(30) NULL,
        MoTa         NVARCHAR(255) NULL
    );
END
GO

-- ------------------------------------------------------------------------------
-- 6. BẢNG SẢN PHẨM
-- ------------------------------------------------------------------------------
IF OBJECT_ID('SanPham', 'U') IS NULL
BEGIN
    CREATE TABLE SanPham (
        MaSanPham    INT IDENTITY(1,1) CONSTRAINT PK_SanPham PRIMARY KEY,
        MaDanhMuc    INT           NOT NULL CONSTRAINT FK_SanPham_DanhMuc REFERENCES DanhMuc(MaDanhMuc),
        MaThuongHieu INT           NULL CONSTRAINT FK_SanPham_ThuongHieu REFERENCES ThuongHieu(MaThuongHieu),
        MaNguoiTao   INT           NULL CONSTRAINT FK_SanPham_NguoiTao REFERENCES NguoiDung(MaNguoiDung),
        TenSanPham   NVARCHAR(200) NOT NULL,
        HienThi      BIT           NOT NULL CONSTRAINT DF_SanPham_HienThi DEFAULT 1,
        GiaBan       DECIMAL(18,2) NOT NULL CONSTRAINT CK_SanPham_GiaBan CHECK (GiaBan >= 0),
        ThuongHieu   NVARCHAR(100) NULL,
        MoTa         NVARCHAR(MAX) NULL,
        NgayTao      DATETIME2(0)  NOT NULL CONSTRAINT DF_SanPham_NgayTao DEFAULT SYSDATETIME()
    );
    CREATE INDEX IX_SanPham_MaDanhMuc ON SanPham(MaDanhMuc);
    CREATE INDEX IX_SanPham_TenSanPham ON SanPham(TenSanPham);
END
GO

-- ------------------------------------------------------------------------------
-- 7. BẢNG HÌNH ẢNH SẢN PHẨM (GALLERY)
-- ------------------------------------------------------------------------------
IF OBJECT_ID('SanPhamHinhAnh', 'U') IS NULL
BEGIN
    CREATE TABLE SanPhamHinhAnh (
        MaHinhAnh     INT IDENTITY(1,1) CONSTRAINT PK_SanPhamHinhAnh PRIMARY KEY,
        MaSanPham     INT           NOT NULL CONSTRAINT FK_SPHA_SanPham REFERENCES SanPham(MaSanPham) ON DELETE CASCADE,
        TenTep        NVARCHAR(255) NOT NULL,
        LaAnhDaiDien  BIT           NOT NULL CONSTRAINT DF_SPHA_LaDaiDien DEFAULT 0,
        ThuTu         INT           NOT NULL CONSTRAINT DF_SPHA_ThuTu DEFAULT 0
    );
    CREATE INDEX IX_SPHA_MaSanPham ON SanPhamHinhAnh(MaSanPham);
END
GO

-- ------------------------------------------------------------------------------
-- 8. BẢNG BIẾN THỂ SẢN PHẨM (SIZE, MÀU, TỒN KHO)
-- ------------------------------------------------------------------------------
IF OBJECT_ID('BienTheSanPham', 'U') IS NULL
BEGIN
    CREATE TABLE BienTheSanPham (
        MaBienThe  INT IDENTITY(1,1) CONSTRAINT PK_BienTheSanPham PRIMARY KEY,
        MaSanPham  INT           NOT NULL CONSTRAINT FK_BienThe_SanPham REFERENCES SanPham(MaSanPham) ON DELETE CASCADE,
        KichThuoc  NVARCHAR(30)  NOT NULL,
        MauSac     NVARCHAR(50)  NOT NULL,
        SoLuongTon INT           NOT NULL CONSTRAINT DF_BienThe_Ton DEFAULT 0 CONSTRAINT CK_BienThe_Ton CHECK (SoLuongTon >= 0),
        CONSTRAINT UQ_BienThe UNIQUE (MaSanPham, KichThuoc, MauSac)
    );
    CREATE INDEX IX_BienThe_MaSanPham ON BienTheSanPham(MaSanPham);
END
GO

-- ------------------------------------------------------------------------------
-- 9. BẢNG GIỎ HÀNG & CHI TIẾT GIỎ HÀNG
-- ------------------------------------------------------------------------------
IF OBJECT_ID('GioHang', 'U') IS NULL
BEGIN
    CREATE TABLE GioHang (
        MaGioHang   INT IDENTITY(1,1) CONSTRAINT PK_GioHang PRIMARY KEY,
        MaNguoiDung INT          NOT NULL CONSTRAINT UQ_GioHang_NguoiDung UNIQUE CONSTRAINT FK_GioHang_NguoiDung REFERENCES NguoiDung(MaNguoiDung) ON DELETE CASCADE,
        NgayTao     DATETIME2(0) NOT NULL CONSTRAINT DF_GioHang_NgayTao DEFAULT SYSDATETIME()
    );
END
GO

IF OBJECT_ID('ChiTietGioHang', 'U') IS NULL
BEGIN
    CREATE TABLE ChiTietGioHang (
        MaChiTietGioHang INT IDENTITY(1,1) CONSTRAINT PK_ChiTietGioHang PRIMARY KEY,
        MaGioHang        INT NOT NULL CONSTRAINT FK_CTGH_GioHang REFERENCES GioHang(MaGioHang) ON DELETE CASCADE,
        MaBienThe        INT NOT NULL CONSTRAINT FK_CTGH_BienThe REFERENCES BienTheSanPham(MaBienThe),
        SoLuong          INT NOT NULL CONSTRAINT DF_CTGH_SoLuong DEFAULT 1 CONSTRAINT CK_CTGH_SoLuong CHECK (SoLuong > 0),
        CONSTRAINT UQ_CTGH UNIQUE (MaGioHang, MaBienThe)
    );
END
GO

-- ------------------------------------------------------------------------------
-- 10. BẢNG ĐƠN HÀNG
-- ------------------------------------------------------------------------------
IF OBJECT_ID('DonHang', 'U') IS NULL
BEGIN
    CREATE TABLE DonHang (
        MaDonHang            INT IDENTITY(1,1) CONSTRAINT PK_DonHang PRIMARY KEY,
        MaNguoiDung          INT           NULL CONSTRAINT FK_DonHang_NguoiDung REFERENCES NguoiDung(MaNguoiDung),
        NgayDat              DATETIME2(0)  NOT NULL CONSTRAINT DF_DonHang_NgayDat DEFAULT SYSDATETIME(),
        TrangThai            NVARCHAR(30)  NOT NULL CONSTRAINT DF_DonHang_TrangThai DEFAULT N'Chờ xác nhận',
        TrangThaiGiaoHang    NVARCHAR(50)  NOT NULL CONSTRAINT DF_DonHang_GiaoHang DEFAULT N'Chưa giao',
        TongTien             DECIMAL(18,2) NOT NULL CONSTRAINT DF_DonHang_TongTien DEFAULT 0 CONSTRAINT CK_DonHang_TongTien CHECK (TongTien >= 0),
        MaNguoiXuLy          INT           NULL CONSTRAINT FK_DonHang_NguoiXuLy REFERENCES NguoiDung(MaNguoiDung),
        ThoiGianXuLy         DATETIME2(0)  NULL,
        NguoiXacNhan         INT           NULL CONSTRAINT FK_DonHang_NguoiXacNhan REFERENCES NguoiDung(MaNguoiDung),
        ThoiGianXacNhan      DATETIME2(0)  NULL,
        NguoiGiaoHang        INT           NULL CONSTRAINT FK_DonHang_NguoiGiao REFERENCES NguoiDung(MaNguoiDung),
        ThoiGianBatDauGiao   DATETIME2(0)  NULL,
        NguoiXacNhanGiao     INT           NULL CONSTRAINT FK_DonHang_NguoiXNGiao REFERENCES NguoiDung(MaNguoiDung),
        ThoiGianGiaoThanhCong DATETIME2(0) NULL,
        NguoiHoanThanh       INT           NULL CONSTRAINT FK_DonHang_NguoiHT REFERENCES NguoiDung(MaNguoiDung),
        ThoiGianHoanThanh    DATETIME2(0)  NULL,
        NguoiHuy             INT           NULL CONSTRAINT FK_DonHang_NguoiHuy REFERENCES NguoiDung(MaNguoiDung),
        ThoiGianHuy          DATETIME2(0)  NULL,
        LichSuXuLy           NVARCHAR(MAX) NULL,
        CheckoutToken NVARCHAR(100) NULL,
        CONSTRAINT CK_DonHang_TrangThai CHECK (TrangThai IN (N'Chờ xác nhận', N'Đã xác nhận', N'Hoàn thành', N'Đã hủy')),
        CONSTRAINT CK_DonHang_TrangThaiGiaoHang CHECK (TrangThaiGiaoHang IN (N'Chưa giao', N'Đang giao', N'Đã giao'))
    );
    CREATE INDEX IX_DonHang_MaNguoiDung ON DonHang(MaNguoiDung, NgayDat DESC);
    CREATE UNIQUE NONCLUSTERED INDEX IX_DonHang_CheckoutToken ON DonHang(CheckoutToken) WHERE CheckoutToken IS NOT NULL;
END
GO

-- ------------------------------------------------------------------------------
-- 11. BẢNG CHI TIẾT ĐƠN HÀNG
-- ------------------------------------------------------------------------------
IF OBJECT_ID('ChiTietDonHang', 'U') IS NULL
BEGIN
    CREATE TABLE ChiTietDonHang (
        MaChiTietDon INT IDENTITY(1,1) CONSTRAINT PK_ChiTietDonHang PRIMARY KEY,
        MaDonHang    INT           NOT NULL CONSTRAINT FK_CTDH_DonHang REFERENCES DonHang(MaDonHang) ON DELETE CASCADE,
        MaBienThe    INT           NOT NULL CONSTRAINT FK_CTDH_BienThe REFERENCES BienTheSanPham(MaBienThe),
        SoLuong      INT           NOT NULL CONSTRAINT CK_CTDH_SoLuong CHECK (SoLuong > 0),
        DonGia       DECIMAL(18,2) NOT NULL CONSTRAINT CK_CTDH_DonGia CHECK (DonGia >= 0),
        TenSanPham   NVARCHAR(200) NULL,
        MauSac       NVARCHAR(50)  NULL,
        KichThuoc    NVARCHAR(30)  NULL,
        ThanhTien AS (SoLuong * DonGia) PERSISTED,
        CONSTRAINT UQ_CTDH UNIQUE (MaDonHang, MaBienThe)
    );
    CREATE INDEX IX_CTDH_MaBienThe ON ChiTietDonHang(MaBienThe);
END
GO

-- ------------------------------------------------------------------------------
-- 12. BẢNG THÔNG TIN GIAO DỊCH CHECKOUT
-- ------------------------------------------------------------------------------
IF OBJECT_ID('ThongTinGiaoDich', 'U') IS NULL
BEGIN
    CREATE TABLE ThongTinGiaoDich (
        MaDonHang           INT NOT NULL CONSTRAINT PK_ThongTinGiaoDich PRIMARY KEY CONSTRAINT FK_TTGD_DonHang REFERENCES DonHang(MaDonHang) ON DELETE CASCADE,
        HoTen               NVARCHAR(100) NOT NULL,
        SoDienThoai         VARCHAR(20)   NOT NULL,
        Email               NVARCHAR(150) NULL,
        HinhThucNhanHang    VARCHAR(20)   NOT NULL CONSTRAINT CK_TTGD_HinhThuc CHECK (HinhThucNhanHang IN ('delivery', 'pickup')),
        DiaChiGiaoHang      NVARCHAR(255) NULL,
        PhuongThucThanhToan VARCHAR(30)   NOT NULL CONSTRAINT CK_TTGD_PhuongThuc CHECK (PhuongThucThanhToan IN ('cod', 'bank_transfer')),
        TrangThaiThanhToan  NVARCHAR(50)  NOT NULL CONSTRAINT DF_TTGD_TrangThai DEFAULT N'Chưa thanh toán',
        PhiVanChuyen        DECIMAL(18,2) NULL,
        GhiChu              NVARCHAR(500) NULL,
        NgayTao             DATETIME2(0)  NOT NULL CONSTRAINT DF_TTGD_NgayTao DEFAULT SYSDATETIME(),
        NguoiThuTien        INT           NULL CONSTRAINT FK_TTGD_NguoiThu REFERENCES NguoiDung(MaNguoiDung),
        ThoiGianThanhToan   DATETIME2(0)  NULL
    );
END
GO

-- ------------------------------------------------------------------------------
-- 13. BẢNG YÊU THÍCH
-- ------------------------------------------------------------------------------
IF OBJECT_ID('YeuThich', 'U') IS NULL
BEGIN
    CREATE TABLE YeuThich (
        MaNguoiDung INT NOT NULL CONSTRAINT FK_YT_NguoiDung REFERENCES NguoiDung(MaNguoiDung) ON DELETE CASCADE,
        MaSanPham   INT NOT NULL CONSTRAINT FK_YT_SanPham REFERENCES SanPham(MaSanPham) ON DELETE CASCADE,
        NgayThem    DATETIME2(0) NOT NULL CONSTRAINT DF_YT_NgayThem DEFAULT SYSDATETIME(),
        CONSTRAINT PK_YeuThich PRIMARY KEY (MaNguoiDung, MaSanPham)
    );
END
GO

-- ------------------------------------------------------------------------------
-- 14. TRIGGER TỰ ĐỘNG CẬP NHẬT TỔNG TIỀN ĐƠN HÀNG
-- ------------------------------------------------------------------------------
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

-- ------------------------------------------------------------------------------
-- 15. SEED DỮ LIỆU MẪU BAN ĐẦU
-- ------------------------------------------------------------------------------
-- 15.1. Vai trò
IF NOT EXISTS (SELECT 1 FROM VaiTro WHERE MaVaiTro = 1)
BEGIN
    SET IDENTITY_INSERT VaiTro ON;
    INSERT INTO VaiTro (MaVaiTro, TenVaiTro, MoTa) VALUES
        (1, N'Admin', N'Quản trị viên toàn quyền hệ thống'),
        (2, N'Seller', N'Nhân viên bán hàng và xử lý đơn'),
        (3, N'Customer', N'Khách hàng mua sắm');
    SET IDENTITY_INSERT VaiTro OFF;
END
GO

-- 15.2. Tài khoản mẫu (CHỈ DÙNG CHO MÔI TRƯỜNG DEV/TEST; Mật khẩu mặc định: Demo@12345 đã băm scrypt chuẩn Werkzeug)
-- CẢNH BÁO: TUYỆT ĐỐI KHÔNG SỬ DỤNG TÀI KHOẢN VÀ MẬT KHẨU MẪU NÀY CHO MÔI TRƯỜNG PRODUCTION.
IF NOT EXISTS (SELECT 1 FROM NguoiDung WHERE Email = 'admin@shop.vn')
BEGIN
    SET IDENTITY_INSERT NguoiDung ON;
    INSERT INTO NguoiDung (MaNguoiDung, MaVaiTro, HoVaTen, Email, MatKhauHash, SoDienThoai, DiaChi, TrangThai)
    VALUES
        (1, 1, N'Quản trị viên', 'admin@shop.vn', 'scrypt:32768:8:1$7dYy3QJ3WL9UYedE$91bd4ec1ef5f7e068d871985f800d0b09520dd23ba0e836ccbe039821b278998ae13188096164b1368fb59b802eeecc1fb4c4eff69c25877d81ee502ecfaddbc', '0901234567', N'123 Lê Duẩn, Hà Nội', 1),
        (2, 2, N'Trần Thị Minh', 'minh@shop.vn', 'scrypt:32768:8:1$7dYy3QJ3WL9UYedE$91bd4ec1ef5f7e068d871985f800d0b09520dd23ba0e836ccbe039821b278998ae13188096164b1368fb59b802eeecc1fb4c4eff69c25877d81ee502ecfaddbc', '0912345678', N'45 Hai Bà Trưng, Hà Nội', 1),
        (3, 3, N'Khách Hàng Mẫu', 'khach@shop.vn', 'scrypt:32768:8:1$7dYy3QJ3WL9UYedE$91bd4ec1ef5f7e068d871985f800d0b09520dd23ba0e836ccbe039821b278998ae13188096164b1368fb59b802eeecc1fb4c4eff69c25877d81ee502ecfaddbc', '0987654321', N'78 Nguyễn Huệ, Quận 1, TP.HCM', 1);
    SET IDENTITY_INSERT NguoiDung OFF;
END
GO

-- 15.3. Danh mục sản phẩm
IF NOT EXISTS (SELECT 1 FROM DanhMuc WHERE MaDanhMuc = 1)
BEGIN
    SET IDENTITY_INSERT DanhMuc ON;
    INSERT INTO DanhMuc (MaDanhMuc, TenDanhMuc, MoTa) VALUES
        (1, N'Giày Thể Thao', N'Chạy bộ, gym, tennis'),
        (2, N'Giày Sneaker', N'Phong cách thời trang, dạo phố'),
        (3, N'Dép & Sandal', N'Quai ngang, quai hậu, sandal thể thao');
    SET IDENTITY_INSERT DanhMuc OFF;
END
GO

-- 15.4. Thương hiệu
IF NOT EXISTS (SELECT 1 FROM ThuongHieu WHERE TenThuongHieu = 'Nike')
BEGIN
    INSERT INTO ThuongHieu (TenThuongHieu, MoTa) VALUES
        (N'Nike', N'Thương hiệu đồ thể thao hàng đầu thế giới'),
        (N'Adidas', N'Thời trang thể thao năng động phong cách Đức'),
        (N'Puma', N'Bứt phá tốc độ và thiết kế thời thượng'),
        (N'Converse', N'Biểu tượng kinh điển của giới trẻ'),
        (N'Vans', N'Đậm chất đường phố và trượt ván'),
        (N'Biti’s', N'Thương hiệu quốc dân Nâng niu bàn chân Việt'),
        (N'Crocs', N'Thoải mái, tiện lợi và êm ái mỗi ngày');
END
GO

-- 15.5. Màu sắc & Kích thước
IF NOT EXISTS (SELECT 1 FROM MauSac)
BEGIN
    INSERT INTO MauSac (TenMau, MaHex) VALUES
        (N'Đen', '#000000'),
        (N'Trắng', '#ffffff'),
        (N'Xám', '#808080'),
        (N'Xanh Navy', '#000080'),
        (N'Đỏ', '#ff0000');
END
GO

IF NOT EXISTS (SELECT 1 FROM KichThuoc)
BEGIN
    INSERT INTO KichThuoc (TenKichThuoc, TenSize) VALUES
        (N'38', N'38'),
        (N'39', N'39'),
        (N'40', N'40'),
        (N'41', N'41'),
        (N'42', N'42'),
        (N'43', N'43');
END
GO

-- 15.6. Sản phẩm & Biến thể mẫu
IF NOT EXISTS (SELECT 1 FROM SanPham WHERE MaSanPham = 1)
BEGIN
    SET IDENTITY_INSERT SanPham ON;
    INSERT INTO SanPham (MaSanPham, MaDanhMuc, MaThuongHieu, MaNguoiTao, TenSanPham, GiaBan, ThuongHieu, MoTa, HienThi) VALUES
        (1, 1, 1, 1, N'Nike Air Zoom Pegasus', 2500000, N'Nike', N'Giày chạy bộ chuyên nghiệp đệm Zoom êm ái', 1),
        (2, 2, 2, 1, N'Adidas Originals Superstar', 1800000, N'Adidas', N'Sneaker kinh điển mũi vỏ sò phong cách thời trang', 1),
        (3, 2, 4, 1, N'Converse Chuck Taylor All Star', 1200000, N'Converse', N'Giày canvas cổ điển trẻ trung', 1),
        (4, 3, 6, 1, N'Biti’s Hunter Sandal', 450000, N'Biti’s', N'Sandal quai chéo êm nhẹ thích hợp đi học và dạo phố', 1),
        (5, 3, 7, 1, N'Crocs Classic Clog', 850000, N'Crocs', N'Dép sục siêu nhẹ chống trơn trượt', 1);
    SET IDENTITY_INSERT SanPham OFF;

    SET IDENTITY_INSERT BienTheSanPham ON;
    INSERT INTO BienTheSanPham (MaBienThe, MaSanPham, KichThuoc, MauSac, SoLuongTon) VALUES
        (1, 1, N'40', N'Đen', 15),
        (2, 1, N'41', N'Đen', 20),
        (3, 1, N'41', N'Xám', 10),
        (4, 2, N'39', N'Trắng', 12),
        (5, 2, N'40', N'Trắng', 18),
        (6, 3, N'40', N'Đen', 25),
        (7, 4, N'39', N'Xanh Navy', 30),
        (8, 5, N'40', N'Đen', 20);
    SET IDENTITY_INSERT BienTheSanPham OFF;
END
GO

PRINT N'=== KHỞI TẠO CƠ SỞ DỮ LIỆU SQL SERVER HOÀN TẤT THÀNH CÔNG ===';
GO


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

-- Thêm các bảng trả hàng/hoàn tiền và lưu vết nhân viên xóa, chạy nhiều lần an toàn.
-- Nâng cấp độc lập, có thể chạy nhiều lần, KHÔNG xóa dữ liệu cũ.
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
