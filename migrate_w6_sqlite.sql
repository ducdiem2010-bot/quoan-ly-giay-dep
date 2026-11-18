-- ============================================================
-- MIGRATION TUẦN 6 - SQLITE
-- ============================================================

CREATE TABLE IF NOT EXISTS product_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    order_id INTEGER NULL,
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment TEXT NOT NULL,
    is_visible INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT NULL,
    UNIQUE(user_id, product_id)
);

CREATE TABLE IF NOT EXISTS vouchers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    discount_type TEXT NOT NULL CHECK (discount_type IN ('PERCENT', 'FIXED')),
    discount_value REAL NOT NULL CHECK (discount_value > 0),
    max_discount_amount REAL NULL,
    min_order_amount REAL NOT NULL DEFAULT 0,
    usage_limit INTEGER NOT NULL DEFAULT 100,
    used_count INTEGER NOT NULL DEFAULT 0,
    per_user_limit INTEGER NOT NULL DEFAULT 1,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS voucher_usages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    voucher_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    order_id INTEGER NOT NULL,
    discount_amount REAL NOT NULL,
    used_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS order_returns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    request_type TEXT NOT NULL DEFAULT 'RETURN' CHECK (request_type IN ('RETURN', 'EXCHANGE')),
    reason TEXT NOT NULL,
    evidence_url TEXT NULL,
    refund_amount REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
    admin_note TEXT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    resolved_at TEXT NULL
);

INSERT OR IGNORE INTO vouchers (code, title, discount_type, discount_value, max_discount_amount, min_order_amount, usage_limit, start_date, end_date, is_active)
VALUES
    ('WELCOME10', 'Giảm 10% cho đơn từ 300.000đ (tối đa 100k)', 'PERCENT', 10, 100000, 300000, 200, datetime('now', '-1 day'), datetime('now', '+60 days'), 1),
    ('GIAM50K', 'Giảm trực tiếp 50.000đ cho đơn từ 500.000đ', 'FIXED', 50000, NULL, 500000, 100, datetime('now', '-1 day'), datetime('now', '+60 days'), 1);