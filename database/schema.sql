

IF DB_ID(N'quan_ly_giay_dep') IS NULL
BEGIN
    EXEC('CREATE DATABASE quan_ly_giay_dep');
END
GO

USE quan_ly_giay_dep;
GO


------------------------------------------------------------
-- 0.1 XÓA BẢNG CŨ ĐỂ CÓ THỂ CHẠY LẠI FILE
-- Xóa từ bảng con -> bảng cha
------------------------------------------------------------

IF OBJECT_ID(N'chi_tiet_don_hang', N'U') IS NOT NULL
    DROP TABLE chi_tiet_don_hang;
GO

IF OBJECT_ID(N'chi_tiet_gio_hang', N'U') IS NOT NULL
    DROP TABLE chi_tiet_gio_hang;
GO

IF OBJECT_ID(N'don_hang', N'U') IS NOT NULL
    DROP TABLE don_hang;
GO

IF OBJECT_ID(N'gio_hang', N'U') IS NOT NULL
    DROP TABLE gio_hang;
GO

IF OBJECT_ID(N'bien_the_san_pham', N'U') IS NOT NULL
    DROP TABLE bien_the_san_pham;
GO

IF OBJECT_ID(N'san_pham', N'U') IS NOT NULL
    DROP TABLE san_pham;
GO

IF OBJECT_ID(N'danh_muc', N'U') IS NOT NULL
    DROP TABLE danh_muc;
GO

IF OBJECT_ID(N'nguoi_dung', N'U') IS NOT NULL
    DROP TABLE nguoi_dung;
GO

IF OBJECT_ID(N'vai_tro', N'U') IS NOT NULL
    DROP TABLE vai_tro;
GO


/* =========================================================
   1. BẢNG VAI TRÒ
   ========================================================= */

CREATE TABLE vai_tro
(
    ma_vai_tro INT IDENTITY(1,1) PRIMARY KEY,

    ten_vai_tro NVARCHAR(50) NOT NULL,

    mo_ta NVARCHAR(255) NULL,

    CONSTRAINT UQ_vai_tro_ten
        UNIQUE (ten_vai_tro)
);
GO


/* =========================================================
   2. BẢNG NGƯỜI DÙNG
   ========================================================= */

CREATE TABLE nguoi_dung
(
    ma_nguoi_dung INT IDENTITY(1,1) PRIMARY KEY,

    ma_vai_tro INT NOT NULL,

    ho_ten NVARCHAR(100) NOT NULL,

    email VARCHAR(150) NOT NULL,

    mat_khau VARCHAR(255) NOT NULL,

    so_dien_thoai VARCHAR(15) NULL,

    dia_chi NVARCHAR(255) NULL,

    trang_thai BIT NOT NULL
        CONSTRAINT DF_nguoi_dung_trang_thai
        DEFAULT 1,

    ngay_tao DATETIME2 NOT NULL
        CONSTRAINT DF_nguoi_dung_ngay_tao
        DEFAULT SYSDATETIME(),

    CONSTRAINT UQ_nguoi_dung_email
        UNIQUE (email),

    CONSTRAINT FK_nguoi_dung_vai_tro
        FOREIGN KEY (ma_vai_tro)
        REFERENCES vai_tro(ma_vai_tro)
);
GO


/* =========================================================
   3. BẢNG DANH MỤC
   Ví dụ:
   - Giày
   - Dép
   ========================================================= */

CREATE TABLE danh_muc
(
    ma_danh_muc INT IDENTITY(1,1) PRIMARY KEY,

    ten_danh_muc NVARCHAR(100) NOT NULL,

    mo_ta NVARCHAR(255) NULL,

    CONSTRAINT UQ_danh_muc_ten
        UNIQUE (ten_danh_muc)
);
GO


/* =========================================================
   4. BẢNG SẢN PHẨM
   Không lưu Size/Màu/Tồn kho ở đây.
   Các thông tin đó nằm trong bien_the_san_pham.
   ========================================================= */

CREATE TABLE san_pham
(
    ma_san_pham INT IDENTITY(1,1) PRIMARY KEY,

    ma_danh_muc INT NOT NULL,

    -- Người tạo sản phẩm.
    -- Cho phép NULL để tránh lỗi nếu tài khoản người tạo
    -- không còn được sử dụng.
    ma_nguoi_tao INT NULL,

    ten_san_pham NVARCHAR(150) NOT NULL,

    gia_ban DECIMAL(18,2) NOT NULL,

    thuong_hieu NVARCHAR(100) NULL,

    mo_ta NVARCHAR(500) NULL,

    ngay_tao DATETIME2 NOT NULL
        CONSTRAINT DF_san_pham_ngay_tao
        DEFAULT SYSDATETIME(),

    CONSTRAINT CK_san_pham_gia
        CHECK (gia_ban > 0),

    CONSTRAINT FK_san_pham_danh_muc
        FOREIGN KEY (ma_danh_muc)
        REFERENCES danh_muc(ma_danh_muc),

    CONSTRAINT FK_san_pham_nguoi_tao
        FOREIGN KEY (ma_nguoi_tao)
        REFERENCES nguoi_dung(ma_nguoi_dung)
);
GO


/* =========================================================
   5. BẢNG BIẾN THỂ SẢN PHẨM

   Ví dụ:

   Nike Air Force 1
       Size 39 - Trắng
       Size 40 - Trắng
       Size 40 - Đen
   ========================================================= */

CREATE TABLE bien_the_san_pham
(
    ma_bien_the INT IDENTITY(1,1) PRIMARY KEY,

    ma_san_pham INT NOT NULL,

    kich_thuoc NVARCHAR(20) NOT NULL,

    mau_sac NVARCHAR(50) NOT NULL,

    so_luong_ton INT NOT NULL
        CONSTRAINT DF_bien_the_so_luong
        DEFAULT 0,

    ngay_tao DATETIME2 NOT NULL
        CONSTRAINT DF_bien_the_ngay_tao
        DEFAULT SYSDATETIME(),

    CONSTRAINT CK_bien_the_so_luong
        CHECK (so_luong_ton >= 0),

    CONSTRAINT FK_bien_the_san_pham
        FOREIGN KEY (ma_san_pham)
        REFERENCES san_pham(ma_san_pham),

    -- Không cho một sản phẩm có hai biến thể
    -- cùng Size + Màu
    CONSTRAINT UQ_bien_the_san_pham_size_mau
        UNIQUE
        (
            ma_san_pham,
            kich_thuoc,
            mau_sac
        )
);
GO


/* =========================================================
   6. BẢNG GIỎ HÀNG

   Hỗ trợ:
   1. Người dùng đã đăng nhập
   HOẶC
   2. Khách vãng lai sử dụng session_id

   Không cho cả hai cùng NULL.
   Không cho cả hai cùng có giá trị.
   ========================================================= */

CREATE TABLE gio_hang
(
    ma_gio_hang INT IDENTITY(1,1) PRIMARY KEY,

    ma_nguoi_dung INT NULL,

    session_id VARCHAR(100) NULL,

    ngay_tao DATETIME2 NOT NULL
        CONSTRAINT DF_gio_hang_ngay_tao
        DEFAULT SYSDATETIME(),

    ngay_cap_nhat DATETIME2 NOT NULL
        CONSTRAINT DF_gio_hang_cap_nhat
        DEFAULT SYSDATETIME(),

    CONSTRAINT FK_gio_hang_nguoi_dung
        FOREIGN KEY (ma_nguoi_dung)
        REFERENCES nguoi_dung(ma_nguoi_dung),

    -- Chính xác một trong hai phải có giá trị
    CONSTRAINT CK_gio_hang_chu_so_huu
        CHECK
        (
            (
                ma_nguoi_dung IS NOT NULL
                AND session_id IS NULL
            )
            OR
            (
                ma_nguoi_dung IS NULL
                AND session_id IS NOT NULL
            )
        )
);
GO


/* =========================================================
   Mỗi tài khoản chỉ có một giỏ hàng hiện tại
   ========================================================= */

CREATE UNIQUE INDEX UQ_gio_hang_nguoi_dung
ON gio_hang(ma_nguoi_dung)
WHERE ma_nguoi_dung IS NOT NULL;
GO


/* =========================================================
   Mỗi phiên khách vãng lai chỉ có một giỏ hàng
   ========================================================= */

CREATE UNIQUE INDEX UQ_gio_hang_session
ON gio_hang(session_id)
WHERE session_id IS NOT NULL;
GO


/* =========================================================
   7. CHI TIẾT GIỎ HÀNG
   Quan trọng:
   Trỏ vào biến thể, KHÔNG trỏ thẳng sản phẩm.
   ========================================================= */

CREATE TABLE chi_tiet_gio_hang
(
    ma_ct_gio_hang INT IDENTITY(1,1) PRIMARY KEY,

    ma_gio_hang INT NOT NULL,

    ma_bien_the INT NOT NULL,

    so_luong INT NOT NULL,

    CONSTRAINT CK_chi_tiet_gio_so_luong
        CHECK (so_luong > 0),

    CONSTRAINT FK_chi_tiet_gio_gio_hang
        FOREIGN KEY (ma_gio_hang)
        REFERENCES gio_hang(ma_gio_hang),

    CONSTRAINT FK_chi_tiet_gio_bien_the
        FOREIGN KEY (ma_bien_the)
        REFERENCES bien_the_san_pham(ma_bien_the),

    -- Một biến thể chỉ xuất hiện một lần trong cùng giỏ.
    CONSTRAINT UQ_chi_tiet_gio
        UNIQUE
        (
            ma_gio_hang,
            ma_bien_the
        )
);
GO


/* =========================================================
   8. BẢNG ĐƠN HÀNG

   ma_nguoi_dung được NULL:
   -> hỗ trợ khách không có tài khoản.

   ten_khach_hang / SDT / địa chỉ:
   -> lưu snapshot tại thời điểm đặt hàng.
   ========================================================= */

CREATE TABLE don_hang
(
    ma_don_hang INT IDENTITY(1,1) PRIMARY KEY,

    ma_nguoi_dung INT NULL,

    ten_khach_hang NVARCHAR(100) NOT NULL,

    so_dien_thoai VARCHAR(15) NOT NULL,

    dia_chi_giao_hang NVARCHAR(255) NOT NULL,

    tong_tien DECIMAL(18,2) NOT NULL
        CONSTRAINT DF_don_hang_tong_tien
        DEFAULT 0,

    phuong_thuc_thanh_toan VARCHAR(20) NOT NULL
        CONSTRAINT DF_don_hang_pttt
        DEFAULT 'COD',

    trang_thai_thanh_toan VARCHAR(20) NOT NULL
        CONSTRAINT DF_don_hang_tt_thanh_toan
        DEFAULT 'UNPAID',

    trang_thai_don_hang VARCHAR(20) NOT NULL
        CONSTRAINT DF_don_hang_trang_thai
        DEFAULT 'PENDING',

    ngay_dat DATETIME2 NOT NULL
        CONSTRAINT DF_don_hang_ngay_dat
        DEFAULT SYSDATETIME(),

    ngay_cap_nhat DATETIME2 NOT NULL
        CONSTRAINT DF_don_hang_cap_nhat
        DEFAULT SYSDATETIME(),

    CONSTRAINT CK_don_hang_tong_tien
        CHECK (tong_tien >= 0),

    -- Nhóm không cần thanh toán online phức tạp.
    -- COD: thanh toán khi nhận hàng.
    -- CASH: thanh toán trực tiếp.
    CONSTRAINT CK_don_hang_phuong_thuc
        CHECK
        (
            phuong_thuc_thanh_toan
            IN ('COD', 'CASH')
        ),

    CONSTRAINT CK_don_hang_tt_thanh_toan
        CHECK
        (
            trang_thai_thanh_toan
            IN
            (
                'UNPAID',
                'PAID'
            )
        ),

    CONSTRAINT CK_don_hang_trang_thai
        CHECK
        (
            trang_thai_don_hang
            IN
            (
                'PENDING',
                'CONFIRMED',
                'SHIPPING',
                'COMPLETED',
                'CANCELLED'
            )
        ),

    CONSTRAINT FK_don_hang_nguoi_dung
        FOREIGN KEY (ma_nguoi_dung)
        REFERENCES nguoi_dung(ma_nguoi_dung)
);
GO


/* =========================================================
   9. CHI TIẾT ĐƠN HÀNG

   Lưu:
   - biến thể
   - số lượng
   - đơn giá tại thời điểm đặt

   Không lấy lại giá hiện tại từ san_pham
   khi xem đơn hàng cũ.
   ========================================================= */

CREATE TABLE chi_tiet_don_hang
(
    ma_ct_don_hang INT IDENTITY(1,1) PRIMARY KEY,

    ma_don_hang INT NOT NULL,

    ma_bien_the INT NOT NULL,

    so_luong INT NOT NULL,

    don_gia DECIMAL(18,2) NOT NULL,

    CONSTRAINT CK_chi_tiet_don_so_luong
        CHECK (so_luong > 0),

    CONSTRAINT CK_chi_tiet_don_gia
        CHECK (don_gia > 0),

    CONSTRAINT FK_chi_tiet_don_don_hang
        FOREIGN KEY (ma_don_hang)
        REFERENCES don_hang(ma_don_hang),

    CONSTRAINT FK_chi_tiet_don_bien_the
        FOREIGN KEY (ma_bien_the)
        REFERENCES bien_the_san_pham(ma_bien_the),

    CONSTRAINT UQ_chi_tiet_don
        UNIQUE
        (
            ma_don_hang,
            ma_bien_the
        )
);
GO


/* =========================================================
   10. INDEX HỖ TRỢ JOIN/TÌM KIẾM
   ========================================================= */

CREATE INDEX IX_nguoi_dung_ma_vai_tro
ON nguoi_dung(ma_vai_tro);
GO

CREATE INDEX IX_san_pham_ma_danh_muc
ON san_pham(ma_danh_muc);
GO

CREATE INDEX IX_san_pham_ma_nguoi_tao
ON san_pham(ma_nguoi_tao);
GO

CREATE INDEX IX_bien_the_ma_san_pham
ON bien_the_san_pham(ma_san_pham);
GO

CREATE INDEX IX_chi_tiet_gio_ma_gio
ON chi_tiet_gio_hang(ma_gio_hang);
GO

CREATE INDEX IX_chi_tiet_gio_ma_bien_the
ON chi_tiet_gio_hang(ma_bien_the);
GO

CREATE INDEX IX_don_hang_ma_nguoi_dung
ON don_hang(ma_nguoi_dung);
GO

CREATE INDEX IX_chi_tiet_don_ma_don
ON chi_tiet_don_hang(ma_don_hang);
GO

CREATE INDEX IX_chi_tiet_don_ma_bien_the
ON chi_tiet_don_hang(ma_bien_the);
GO


/* =========================================================
   11. DỮ LIỆU CƠ BẢN
   Chỉ tạo dữ liệu cần thiết cho hệ thống.
   seed.sql của Nghĩa có thể thêm sản phẩm sau.
   ========================================================= */

INSERT INTO vai_tro
(
    ten_vai_tro,
    mo_ta
)
VALUES
(
    N'Khách hàng',
    N'Người dùng mua hàng trên website'
),
(
    N'Nhân viên',
    N'Nhân viên xử lý sản phẩm và đơn hàng'
),
(
    N'Quản trị viên',
    N'Quản trị hệ thống'
);
GO


INSERT INTO danh_muc
(
    ten_danh_muc,
    mo_ta
)
VALUES
(
    N'Giày',
    N'Các sản phẩm giày'
),
(
    N'Dép',
    N'Các sản phẩm dép'
);
GO


/* =========================================================
   12. KIỂM TRA SCHEMA
   ========================================================= */

SELECT
    TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_NAME;
GO
