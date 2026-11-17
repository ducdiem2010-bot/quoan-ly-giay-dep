-- ============================================================
-- MIGRATION TUẦN 6 - SQL SERVER (T-SQL)
-- Chức năng: Đánh giá SP, Mã giảm giá (Voucher), Đổi trả đơn hàng
-- ============================================================

-- 1. Bảng Đánh giá & Bình luận sản phẩm
IF OBJECT_ID('dbo.product_reviews', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.product_reviews (
        id INT IDENTITY(1,1) PRIMARY KEY,
        product_id INT NOT NULL,
        user_id INT NOT NULL,
        order_id INT NULL,
        rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
        comment NVARCHAR(1000) NOT NULL,
        is_visible BIT NOT NULL DEFAULT 1,
        created_at DATETIME NOT NULL DEFAULT GETDATE(),
        updated_at DATETIME NULL
    );
    CREATE INDEX IX_product_reviews_product ON dbo.product_reviews(product_id, is_visible);
    CREATE UNIQUE INDEX UX_product_reviews_user_product ON dbo.product_reviews(user_id, product_id);
END
GO

-- 2. Bảng Mã giảm giá (Voucher)
IF OBJECT_ID('dbo.vouchers', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.vouchers (
        id INT IDENTITY(1,1) PRIMARY KEY,
        code NVARCHAR(50) NOT NULL UNIQUE,
        title NVARCHAR(200) NOT NULL,
        discount_type NVARCHAR(20) NOT NULL CHECK (discount_type IN ('PERCENT', 'FIXED')),
        discount_value DECIMAL(18, 2) NOT NULL CHECK (discount_value > 0),
        max_discount_amount DECIMAL(18, 2) NULL,
        min_order_amount DECIMAL(18, 2) NOT NULL DEFAULT 0,
        usage_limit INT NOT NULL DEFAULT 100,
        used_count INT NOT NULL DEFAULT 0,
        per_user_limit INT NOT NULL DEFAULT 1,
        start_date DATETIME NOT NULL,
        end_date DATETIME NOT NULL,
        is_active BIT NOT NULL DEFAULT 1,
        created_at DATETIME NOT NULL DEFAULT GETDATE()
    );
END
GO

-- 3. Bảng Lịch sử sử dụng mã giảm giá
IF OBJECT_ID('dbo.voucher_usages', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.voucher_usages (
        id INT IDENTITY(1,1) PRIMARY KEY,
        voucher_id INT NOT NULL,
        user_id INT NOT NULL,
        order_id INT NOT NULL,
        discount_amount DECIMAL(18, 2) NOT NULL,
        used_at DATETIME NOT NULL DEFAULT GETDATE()
    );
    CREATE INDEX IX_voucher_usages_user ON dbo.voucher_usages(voucher_id, user_id);
END
GO

-- 4. Bảng Yêu cầu đổi trả / Hoàn tiền đơn hàng
IF OBJECT_ID('dbo.order_returns', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.order_returns (
        id INT IDENTITY(1,1) PRIMARY KEY,
        order_id INT NOT NULL,
        user_id INT NOT NULL,
        request_type NVARCHAR(20) NOT NULL DEFAULT 'RETURN' CHECK (request_type IN ('RETURN', 'EXCHANGE')),
        reason NVARCHAR(1000) NOT NULL,
        evidence_url NVARCHAR(500) NULL,
        refund_amount DECIMAL(18, 2) NOT NULL DEFAULT 0,
        status NVARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
        admin_note NVARCHAR(500) NULL,
        created_at DATETIME NOT NULL DEFAULT GETDATE(),
        resolved_at DATETIME NULL
    );
    CREATE INDEX IX_order_returns_order ON dbo.order_returns(order_id, status);
END
GO

-- Dữ liệu mẫu mã giảm giá để kiểm thử ngay
IF NOT EXISTS (SELECT 1 FROM dbo.vouchers WHERE code = 'WELCOME10')
BEGIN
    INSERT INTO dbo.vouchers (code, title, discount_type, discount_value, max_discount_amount, min_order_amount, usage_limit, start_date, end_date, is_active)
    VALUES
        ('WELCOME10', N'Giảm 10% cho đơn từ 300.000đ (tối đa 100k)', 'PERCENT', 10, 100000, 300000, 200, DATEADD(DAY, -1, GETDATE()), DATEADD(DAY, 60, GETDATE()), 1),
        ('GIAM50K', N'Giảm trực tiếp 50.000đ cho đơn từ 500.000đ', 'FIXED', 50000, NULL, 500000, 100, DATEADD(DAY, -1, GETDATE()), DATEADD(DAY, 60, GETDATE()), 1);
END
GO