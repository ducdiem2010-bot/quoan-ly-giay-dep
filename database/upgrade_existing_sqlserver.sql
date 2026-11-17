-- ==============================================================================
-- SCRIPT NÂNG CẤP CƠ SỞ DỮ LIỆU SQL SERVER (IDEMPOTENT / GIỮ NGUYÊN DỮ LIỆU CŨ)
-- Dự án: Website Quản lý Cửa hàng Giày dép - Nhóm 6
-- Đặc điểm: Chạy lại an toàn nhiều lần, không DROP TABLE, không mất dữ liệu hiện có.
-- ==============================================================================

USE QuanLyBanHang;
GO

SET NOCOUNT ON;
PRINT N'=== BẮT ĐẦU NÂNG CẤP HỆ THỐNG CƠ SỞ DỮ LIỆU SQL SERVER ===';
GO

-- ------------------------------------------------------------------------------
-- 1. BẢNG NGUOIDUNG: Bổ sung các cột hồ sơ, thông tin địa chỉ và theo dõi khóa
-- ------------------------------------------------------------------------------
IF COL_LENGTH('NguoiDung', 'Ho') IS NULL
    ALTER TABLE NguoiDung ADD Ho NVARCHAR(50) NULL;

IF COL_LENGTH('NguoiDung', 'Ten') IS NULL
    ALTER TABLE NguoiDung ADD Ten NVARCHAR(50) NULL;

IF COL_LENGTH('NguoiDung', 'GioiTinh') IS NULL
    ALTER TABLE NguoiDung ADD GioiTinh NVARCHAR(10) NULL;

IF COL_LENGTH('NguoiDung', 'NgaySinh') IS NULL
    ALTER TABLE NguoiDung ADD NgaySinh DATE NULL;

IF COL_LENGTH('NguoiDung', 'TinhThanh') IS NULL
    ALTER TABLE NguoiDung ADD TinhThanh NVARCHAR(100) NULL;

IF COL_LENGTH('NguoiDung', 'PhuongXa') IS NULL
    ALTER TABLE NguoiDung ADD PhuongXa NVARCHAR(100) NULL;

IF COL_LENGTH('NguoiDung', 'NguoiKhoa') IS NULL
    ALTER TABLE NguoiDung ADD NguoiKhoa INT NULL CONSTRAINT FK_NguoiDung_NguoiKhoa REFERENCES NguoiDung(MaNguoiDung);

IF COL_LENGTH('NguoiDung', 'ThoiGianKhoa') IS NULL
    ALTER TABLE NguoiDung ADD ThoiGianKhoa DATETIME2(0) NULL;

IF COL_LENGTH('NguoiDung', 'GhiChuKhoa') IS NULL
    ALTER TABLE NguoiDung ADD GhiChuKhoa NVARCHAR(255) NULL;

PRINT N'✓ Đã kiểm tra và cập nhật các cột mở rộng cho bảng NguoiDung.';
GO

-- ------------------------------------------------------------------------------
-- 2. TẠO CÁC BẢNG QUẢN LÝ THUỘC TÍNH SẢN PHẨM: ThuongHieu, MauSac, KichThuoc
-- ------------------------------------------------------------------------------
IF OBJECT_ID('ThuongHieu', 'U') IS NULL
BEGIN
    CREATE TABLE ThuongHieu (
        MaThuongHieu  INT IDENTITY(1,1) CONSTRAINT PK_ThuongHieu PRIMARY KEY,
        TenThuongHieu NVARCHAR(100) NOT NULL CONSTRAINT UQ_ThuongHieu_Ten UNIQUE,
        MoTa          NVARCHAR(255) NULL
    );
    PRINT N'✓ Đã tạo mới bảng ThuongHieu.';
END
GO

IF OBJECT_ID('MauSac', 'U') IS NULL
BEGIN
    CREATE TABLE MauSac (
        MaMau   INT IDENTITY(1,1) CONSTRAINT PK_MauSac PRIMARY KEY,
        TenMau  NVARCHAR(50) NOT NULL CONSTRAINT UQ_MauSac_Ten UNIQUE,
        MaHex   VARCHAR(10)  NULL,
        MoTa    NVARCHAR(255) NULL
    );
    PRINT N'✓ Đã tạo mới bảng MauSac.';
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
    PRINT N'✓ Đã tạo mới bảng KichThuoc.';
END
GO

-- ------------------------------------------------------------------------------
-- 3. BẢNG SANPHAM: Thêm cột hiển thị (ẩn/hiện) và khóa ngoại ThuongHieu
-- ------------------------------------------------------------------------------
IF COL_LENGTH('SanPham', 'HienThi') IS NULL
BEGIN
    ALTER TABLE SanPham ADD HienThi BIT NOT NULL CONSTRAINT DF_SanPham_HienThi DEFAULT 1;
    PRINT N'✓ Đã thêm cột HienThi vào bảng SanPham.';
END

IF COL_LENGTH('SanPham', 'MaThuongHieu') IS NULL
BEGIN
    ALTER TABLE SanPham ADD MaThuongHieu INT NULL CONSTRAINT FK_SanPham_ThuongHieu REFERENCES ThuongHieu(MaThuongHieu);
    PRINT N'✓ Đã thêm cột MaThuongHieu vào bảng SanPham.';
END
GO

-- ------------------------------------------------------------------------------
-- 4. BẢNG SANPHAMHINHANH: Gallery ảnh sản phẩm (hỗ trợ nhiều ảnh & ảnh đại diện)
-- ------------------------------------------------------------------------------
IF OBJECT_ID('SanPhamHinhAnh', 'U') IS NULL
BEGIN
    CREATE TABLE SanPhamHinhAnh (
        MaHinhAnh     INT IDENTITY(1,1) CONSTRAINT PK_SanPhamHinhAnh PRIMARY KEY,
        MaSanPham     INT NOT NULL CONSTRAINT FK_SPHA_SanPham REFERENCES SanPham(MaSanPham) ON DELETE CASCADE,
        TenTep        NVARCHAR(255) NOT NULL,
        LaAnhDaiDien  BIT NOT NULL CONSTRAINT DF_SPHA_LaDaiDien DEFAULT 0,
        ThuTu         INT NOT NULL CONSTRAINT DF_SPHA_ThuTu DEFAULT 0
    );
    CREATE INDEX IX_SPHA_MaSanPham ON SanPhamHinhAnh(MaSanPham);
    PRINT N'✓ Đã tạo mới bảng SanPhamHinhAnh.';
END
GO

-- ------------------------------------------------------------------------------
-- 5. BẢNG DONHANG: Bổ sung theo dõi người xử lý và thời gian xử lý
-- ------------------------------------------------------------------------------
IF COL_LENGTH('DonHang', 'MaNguoiXuLy') IS NULL
BEGIN
    ALTER TABLE DonHang ADD MaNguoiXuLy INT NULL CONSTRAINT FK_DonHang_NguoiXuLy REFERENCES NguoiDung(MaNguoiDung);
    PRINT N'✓ Đã thêm cột MaNguoiXuLy vào bảng DonHang.';
END

IF COL_LENGTH('DonHang', 'ThoiGianXuLy') IS NULL
BEGIN
    ALTER TABLE DonHang ADD ThoiGianXuLy DATETIME2(0) NULL;
    PRINT N'✓ Đã thêm cột ThoiGianXuLy vào bảng DonHang.';
END
GO

-- ------------------------------------------------------------------------------
-- 6. BẢNG THONGTINGIAODICH: Lưu snapshot giao dịch, thông tin nhận hàng & thanh toán
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
    PRINT N'✓ Đã tạo mới bảng ThongTinGiaoDich.';
END
GO

-- Kiểm tra các cột bổ sung nếu bảng ThongTinGiaoDich đã được tạo từ trước
IF COL_LENGTH('ThongTinGiaoDich', 'NguoiThuTien') IS NULL
    ALTER TABLE ThongTinGiaoDich ADD NguoiThuTien INT NULL CONSTRAINT FK_TTGD_NguoiThu REFERENCES NguoiDung(MaNguoiDung);

IF COL_LENGTH('ThongTinGiaoDich', 'ThoiGianThanhToan') IS NULL
    ALTER TABLE ThongTinGiaoDich ADD ThoiGianThanhToan DATETIME2(0) NULL;
GO

-- ------------------------------------------------------------------------------
-- 7. BẢNG YEUTHICH: Danh sách sản phẩm yêu thích của khách hàng
-- ------------------------------------------------------------------------------
IF OBJECT_ID('YeuThich', 'U') IS NULL
BEGIN
    CREATE TABLE YeuThich (
        MaNguoiDung INT NOT NULL CONSTRAINT FK_YT_NguoiDung REFERENCES NguoiDung(MaNguoiDung) ON DELETE CASCADE,
        MaSanPham   INT NOT NULL CONSTRAINT FK_YT_SanPham REFERENCES SanPham(MaSanPham) ON DELETE CASCADE,
        NgayThem    DATETIME2(0) NOT NULL CONSTRAINT DF_YT_NgayThem DEFAULT SYSDATETIME(),
        CONSTRAINT PK_YeuThich PRIMARY KEY (MaNguoiDung, MaSanPham)
    );
    PRINT N'✓ Đã tạo mới bảng YeuThich.';
END
GO

-- ------------------------------------------------------------------------------
-- 8. ĐỒNG BỘ DỮ LIỆU BAN ĐẦU CHO CÁC BẢNG DANH MỤC PHỤ (NẾU ĐANG TRỐNG)
-- ------------------------------------------------------------------------------
-- 8.1. Đồng bộ Thương hiệu từ SanPham
IF NOT EXISTS (SELECT 1 FROM ThuongHieu)
BEGIN
    INSERT INTO ThuongHieu (TenThuongHieu)
    SELECT DISTINCT LTRIM(RTRIM(ThuongHieu))
    FROM SanPham
    WHERE ThuongHieu IS NOT NULL AND LTRIM(RTRIM(ThuongHieu)) <> '';
    PRINT N'✓ Đã đồng bộ danh mục Thương hiệu từ dữ liệu sản phẩm.';
END

-- 8.2. Cập nhật MaThuongHieu trong bảng SanPham
UPDATE sp
SET sp.MaThuongHieu = th.MaThuongHieu
FROM SanPham sp
JOIN ThuongHieu th ON LOWER(LTRIM(RTRIM(sp.ThuongHieu))) = LOWER(LTRIM(RTRIM(th.TenThuongHieu)))
WHERE sp.MaThuongHieu IS NULL;

-- 8.3. Đồng bộ Màu sắc từ BienTheSanPham
IF NOT EXISTS (SELECT 1 FROM MauSac)
BEGIN
    INSERT INTO MauSac (TenMau)
    SELECT DISTINCT LTRIM(RTRIM(MauSac))
    FROM BienTheSanPham
    WHERE MauSac IS NOT NULL AND LTRIM(RTRIM(MauSac)) <> '';
    PRINT N'✓ Đã đồng bộ danh mục Màu sắc từ các biến thể sản phẩm.';
END

-- 8.4. Đồng bộ Kích thước từ BienTheSanPham
IF NOT EXISTS (SELECT 1 FROM KichThuoc)
BEGIN
    INSERT INTO KichThuoc (TenKichThuoc, TenSize)
    SELECT DISTINCT LTRIM(RTRIM(KichThuoc)), LTRIM(RTRIM(KichThuoc))
    FROM BienTheSanPham
    WHERE KichThuoc IS NOT NULL AND LTRIM(RTRIM(KichThuoc)) <> '';
    PRINT N'✓ Đã đồng bộ danh mục Kích thước từ các biến thể sản phẩm.';
END

-- 8.5. Tạo snapshot ThongTinGiaoDich cho các đơn hàng cũ chưa có giao dịch
INSERT INTO ThongTinGiaoDich (MaDonHang, HoTen, SoDienThoai, Email, HinhThucNhanHang, DiaChiGiaoHang, PhuongThucThanhToan, TrangThaiThanhToan, PhiVanChuyen, NgayTao)
SELECT dh.MaDonHang,
       ISNULL(nd.HoVaTen, N'Khách vãng lai'),
       ISNULL(nd.SoDienThoai, '0900000000'),
       nd.Email,
       'delivery',
       ISNULL(nd.DiaChi, N'Chưa cập nhật địa chỉ'),
       'cod',
       CASE WHEN dh.TrangThai = N'Hoàn thành' THEN N'Đã thanh toán' ELSE N'Chưa thanh toán' END,
       0,
       dh.NgayDat
FROM DonHang dh
LEFT JOIN NguoiDung nd ON nd.MaNguoiDung = dh.MaNguoiDung
WHERE NOT EXISTS (SELECT 1 FROM ThongTinGiaoDich tg WHERE tg.MaDonHang = dh.MaDonHang);
GO

PRINT N'=== NÂNG CẤP CƠ SỞ DỮ LIỆU SQL SERVER HOÀN TẤT THÀNH CÔNG ===';
GO
