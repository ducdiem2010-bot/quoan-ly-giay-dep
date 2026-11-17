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
-- 5. BẢNG DONHANG: Bổ sung theo dõi người xử lý, giao nhận và lịch sử thao tác
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

IF COL_LENGTH('DonHang', 'TrangThaiGiaoHang') IS NULL
BEGIN
    ALTER TABLE DonHang ADD TrangThaiGiaoHang NVARCHAR(50) NOT NULL CONSTRAINT DF_DonHang_GiaoHang DEFAULT N'Chưa giao';
    EXEC(N'UPDATE DonHang SET TrangThaiGiaoHang = N''Đã giao'' WHERE TrangThai = N''Hoàn thành''');
    PRINT N'✓ Đã thêm cột TrangThaiGiaoHang vào bảng DonHang.';
END

IF COL_LENGTH('DonHang', 'NguoiXacNhan') IS NULL
    ALTER TABLE DonHang ADD NguoiXacNhan INT NULL CONSTRAINT FK_DonHang_NguoiXacNhan REFERENCES NguoiDung(MaNguoiDung);

IF COL_LENGTH('DonHang', 'ThoiGianXacNhan') IS NULL
    ALTER TABLE DonHang ADD ThoiGianXacNhan DATETIME2(0) NULL;

IF COL_LENGTH('DonHang', 'NguoiGiaoHang') IS NULL
    ALTER TABLE DonHang ADD NguoiGiaoHang INT NULL CONSTRAINT FK_DonHang_NguoiGiao REFERENCES NguoiDung(MaNguoiDung);

IF COL_LENGTH('DonHang', 'ThoiGianBatDauGiao') IS NULL
    ALTER TABLE DonHang ADD ThoiGianBatDauGiao DATETIME2(0) NULL;

IF COL_LENGTH('DonHang', 'NguoiXacNhanGiao') IS NULL
    ALTER TABLE DonHang ADD NguoiXacNhanGiao INT NULL CONSTRAINT FK_DonHang_NguoiXNGiao REFERENCES NguoiDung(MaNguoiDung);

IF COL_LENGTH('DonHang', 'ThoiGianGiaoThanhCong') IS NULL
    ALTER TABLE DonHang ADD ThoiGianGiaoThanhCong DATETIME2(0) NULL;

IF COL_LENGTH('DonHang', 'NguoiHoanThanh') IS NULL
    ALTER TABLE DonHang ADD NguoiHoanThanh INT NULL CONSTRAINT FK_DonHang_NguoiHT REFERENCES NguoiDung(MaNguoiDung);

IF COL_LENGTH('DonHang', 'ThoiGianHoanThanh') IS NULL
    ALTER TABLE DonHang ADD ThoiGianHoanThanh DATETIME2(0) NULL;

IF COL_LENGTH('DonHang', 'NguoiHuy') IS NULL
    ALTER TABLE DonHang ADD NguoiHuy INT NULL CONSTRAINT FK_DonHang_NguoiHuy REFERENCES NguoiDung(MaNguoiDung);

IF COL_LENGTH('DonHang', 'ThoiGianHuy') IS NULL
    ALTER TABLE DonHang ADD ThoiGianHuy DATETIME2(0) NULL;

IF COL_LENGTH('DonHang', 'LichSuXuLy') IS NULL
    ALTER TABLE DonHang ADD LichSuXuLy NVARCHAR(MAX) NULL;
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
-- 8. BẢNG CHITIETDONHANG: Thêm cột snapshot lịch sử đặt hàng
-- ------------------------------------------------------------------------------
IF COL_LENGTH('ChiTietDonHang', 'TenSanPham') IS NULL
    ALTER TABLE ChiTietDonHang ADD TenSanPham NVARCHAR(200) NULL;

IF COL_LENGTH('ChiTietDonHang', 'MauSac') IS NULL
    ALTER TABLE ChiTietDonHang ADD MauSac NVARCHAR(50) NULL;

IF COL_LENGTH('ChiTietDonHang', 'KichThuoc') IS NULL
    ALTER TABLE ChiTietDonHang ADD KichThuoc NVARCHAR(30) NULL;
GO

-- ------------------------------------------------------------------------------
-- 9. CỘT CHECKOUTTOKEN TRÊN BẢNG DONHANG: Chống tạo đơn hàng trùng nguyên tử
-- ------------------------------------------------------------------------------
IF COL_LENGTH('DonHang', 'CheckoutToken') IS NULL
BEGIN
    ALTER TABLE DonHang ADD CheckoutToken NVARCHAR(100) NULL;
    PRINT N'✓ Đã thêm cột CheckoutToken trên bảng DonHang.';
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_DonHang_CheckoutToken' AND object_id = OBJECT_ID('DonHang'))
BEGIN
    IF NOT EXISTS (
        SELECT CheckoutToken
        FROM DonHang
        WHERE CheckoutToken IS NOT NULL
        GROUP BY CheckoutToken
        HAVING COUNT(*) > 1
    )
    BEGIN
        CREATE UNIQUE NONCLUSTERED INDEX IX_DonHang_CheckoutToken ON DonHang(CheckoutToken) WHERE CheckoutToken IS NOT NULL;
        PRINT N'✓ Đã tạo Unique Index IX_DonHang_CheckoutToken trên bảng DonHang.';
    END
    ELSE
    BEGIN
        PRINT N'⚠ Cảnh báo: Có dữ liệu CheckoutToken trùng lặp trong DonHang cũ; chưa thể tạo Unique Index tự động.';
    END
END
GO

-- Điền dữ liệu snapshot cho các đơn cũ chưa có
UPDATE ct
SET ct.TenSanPham = sp.TenSanPham,
    ct.MauSac = bt.MauSac,
    ct.KichThuoc = bt.KichThuoc
FROM ChiTietDonHang ct
JOIN BienTheSanPham bt ON bt.MaBienThe = ct.MaBienThe
JOIN SanPham sp ON sp.MaSanPham = bt.MaSanPham
WHERE ct.TenSanPham IS NULL;
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
