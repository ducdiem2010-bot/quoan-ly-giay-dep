import csv
import io
import sqlite3
from datetime import datetime, timedelta
from decimal import Decimal
from flask import current_app

from app.db import get_db_connection, query_all, query_one

COMPLETED_ORDER_STATUSES = (
    "COMPLETED", "DELIVERED", "DONE",
    "Hoàn thành", "Đã giao", "Đã giao hàng", "Giao thành công"
)

CANCELLED_ORDER_STATUSES = (
    "CANCELLED", "CANCELED", "RETURNED",
    "Đã hủy", "Hủy", "Đã hoàn trả"
)


def _f(val, default=0.0) -> float:
    if val is None:
        return default
    if isinstance(val, Decimal):
        return float(val)
    return float(val)


def _is_sqlite() -> bool:
    return current_app.config.get("DB_BACKEND", "sqlite") == "sqlite"


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _parse_dt(val):
    if isinstance(val, datetime):
        return val
    if not val:
        return None
    s = str(val).strip().replace("T", " ")[:19]
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _table_columns(table_name: str) -> set:
    if _is_sqlite():
        rows = query_all(f"PRAGMA table_info({table_name})")
        return {r["name"] for r in rows}
    rows = query_all(
        "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = ?",
        (table_name,),
    )
    return {r["COLUMN_NAME"] for r in rows}


def _pick_col(cols: set, candidates: tuple, fallback: str) -> str:
    for c in candidates:
        if c in cols:
            return c
    return fallback


def ensure_w6_tables():
    """Tạo 4 bảng Tuần 6 nếu chưa tồn tại (hỗ trợ cả SQLite và SQL Server)."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if _is_sqlite():
            cur.executescript("""
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
                INSERT OR IGNORE INTO vouchers (
                    code, title, discount_type, discount_value, max_discount_amount,
                    min_order_amount, usage_limit, start_date, end_date, is_active
                ) VALUES
                    ('WELCOME10', 'Giảm 10% cho đơn từ 300.000đ (tối đa 100k)', 'PERCENT', 10, 100000, 300000, 200, datetime('now', '-1 day'), datetime('now', '+60 days'), 1),
                    ('GIAM50K', 'Giảm trực tiếp 50.000đ cho đơn từ 500.000đ', 'FIXED', 50000, NULL, 500000, 100, datetime('now', '-1 day'), datetime('now', '+60 days'), 1);
            """)
        else:
            cur.execute("""
                IF OBJECT_ID('dbo.product_reviews', 'U') IS NULL
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
                IF OBJECT_ID('dbo.vouchers', 'U') IS NULL
                CREATE TABLE dbo.vouchers (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    code NVARCHAR(50) NOT NULL UNIQUE,
                    title NVARCHAR(200) NOT NULL,
                    discount_type NVARCHAR(20) NOT NULL,
                    discount_value DECIMAL(18, 2) NOT NULL,
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
                IF OBJECT_ID('dbo.voucher_usages', 'U') IS NULL
                CREATE TABLE dbo.voucher_usages (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    voucher_id INT NOT NULL,
                    user_id INT NOT NULL,
                    order_id INT NOT NULL,
                    discount_amount DECIMAL(18, 2) NOT NULL,
                    used_at DATETIME NOT NULL DEFAULT GETDATE()
                );
                IF OBJECT_ID('dbo.order_returns', 'U') IS NULL
                CREATE TABLE dbo.order_returns (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    order_id INT NOT NULL,
                    user_id INT NOT NULL,
                    request_type NVARCHAR(20) NOT NULL DEFAULT 'RETURN',
                    reason NVARCHAR(1000) NOT NULL,
                    evidence_url NVARCHAR(500) NULL,
                    refund_amount DECIMAL(18, 2) NOT NULL DEFAULT 0,
                    status NVARCHAR(20) NOT NULL DEFAULT 'PENDING',
                    admin_note NVARCHAR(500) NULL,
                    created_at DATETIME NOT NULL DEFAULT GETDATE(),
                    resolved_at DATETIME NULL
                );
            """)
        conn.commit()
    finally:
        conn.close()


def _user_name_expr(alias: str = "u") -> str:
    cols = _table_columns("NguoiDung")
    if "HoTen" in cols:
        return f"COALESCE(NULLIF(TRIM({alias}.HoTen), ''), {alias}.Email, 'Khách hàng')"
    if "Ho" in cols and "Ten" in cols:
        if _is_sqlite():
            return f"COALESCE(NULLIF(TRIM(COALESCE({alias}.Ho,'') || ' ' || COALESCE({alias}.Ten,'')), ''), {alias}.Email, 'Khách hàng')"
        return f"COALESCE(NULLIF(LTRIM(RTRIM(COALESCE({alias}.Ho,'') + ' ' + COALESCE({alias}.Ten,''))), ''), {alias}.Email, 'Khách hàng')"
    name_col = _pick_col(cols, ("TenHienThi", "TenDangNhap", "Email"), "MaNguoiDung")
    return f"COALESCE({alias}.{name_col}, 'Khách hàng')"


# ==============================================================================
# 1. ĐÁNH GIÁ & BÌNH LUẬN SẢN PHẨM (PRODUCT REVIEWS)
# ==============================================================================

def can_user_review_product(user_id: int, product_id: int):
    """Kiểm tra khách hàng đã mua và nhận hàng thành công sản phẩm này chưa."""
    if not user_id or not product_id:
        return False, None

    dh_cols = _table_columns("DonHang")
    user_col = _pick_col(dh_cols, ("MaNguoiDung", "MaKhachHang"), "MaNguoiDung")
    status_col = _pick_col(dh_cols, ("TrangThai", "TrangThaiDonHang"), "TrangThai")

    placeholders = ",".join(["?"] * len(COMPLETED_ORDER_STATUSES))
    sql = f"""
        SELECT dh.MaDonHang AS order_id
        FROM DonHang dh
        INNER JOIN ChiTietDonHang ct ON ct.MaDonHang = dh.MaDonHang
        INNER JOIN BienTheSanPham bt ON bt.MaBienThe = ct.MaBienThe
        WHERE dh.{user_col} = ?
          AND bt.MaSanPham = ?
          AND dh.{status_col} IN ({placeholders})
        ORDER BY dh.MaDonHang DESC
    """
    row = query_one(sql, (user_id, product_id, *COMPLETED_ORDER_STATUSES))
    if row:
        return True, row["order_id"]
    return False, None


def get_product_reviews_summary(product_id: int, star_filter: int = None):
    """Lấy danh sách đánh giá hiển thị và điểm sao trung bình của sản phẩm."""
    all_visible = query_all(
        "SELECT rating FROM product_reviews WHERE product_id = ? AND is_visible = 1",
        (product_id,),
    )
    total_count = len(all_visible)
    avg_rating = round(sum(int(r["rating"]) for r in all_visible) / total_count, 1) if total_count else 0.0
    star_counts = {s: sum(1 for r in all_visible if int(r["rating"]) == s) for s in range(5, 0, -1)}

    name_expr = _user_name_expr("u")
    sql = f"""
        SELECT r.id, r.product_id, r.user_id, r.order_id, r.rating, r.comment,
               r.is_visible, r.created_at, r.updated_at,
               {name_expr} AS reviewer_name
        FROM product_reviews r
        LEFT JOIN NguoiDung u ON u.MaNguoiDung = r.user_id
        WHERE r.product_id = ? AND r.is_visible = 1
    """
    params = [product_id]
    if star_filter in (1, 2, 3, 4, 5):
        sql += " AND r.rating = ?"
        params.append(star_filter)
    sql += " ORDER BY r.created_at DESC, r.id DESC"

    reviews = query_all(sql, tuple(params))
    return {
        "reviews": reviews,
        "total_count": total_count,
        "avg_rating": avg_rating,
        "star_counts": star_counts,
    }


def submit_product_review(user_id: int, product_id: int, rating: int, comment: str):
    comment = (comment or "").strip()
    if rating not in (1, 2, 3, 4, 5):
        return False, "Số sao đánh giá phải từ 1 đến 5."
    if len(comment) < 3:
        return False, "Nội dung bình luận phải có ít nhất 3 ký tự."

    eligible, order_id = can_user_review_product(user_id, product_id)
    if not eligible:
        return False, "Bạn chỉ có thể đánh giá sản phẩm sau khi đã mua và nhận hàng thành công."

    existing = query_one(
        "SELECT id FROM product_reviews WHERE user_id = ? AND product_id = ?",
        (user_id, product_id),
    )
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        now = _now_str()
        if existing:
            cur.execute(
                """
                UPDATE product_reviews
                SET rating = ?, comment = ?, order_id = ?, updated_at = ?, is_visible = 1
                WHERE id = ?
                """,
                (rating, comment, order_id, now, existing["id"]),
            )
            msg = "Đã cập nhật đánh giá của bạn cho sản phẩm."
        else:
            cur.execute(
                """
                INSERT INTO product_reviews (product_id, user_id, order_id, rating, comment, is_visible, created_at)
                VALUES (?, ?, ?, ?, ?, 1, ?)
                """,
                (product_id, user_id, order_id, rating, comment, now),
            )
            msg = "Cảm ơn bạn đã gửi đánh giá sản phẩm!"
        conn.commit()
        return True, msg
    finally:
        conn.close()


def admin_list_reviews():
    name_expr = _user_name_expr("u")
    sql = f"""
        SELECT r.*, COALESCE(sp.TenSanPham, 'SP #' || r.product_id) AS product_name,
               {name_expr} AS user_name
        FROM product_reviews r
        LEFT JOIN SanPham sp ON sp.MaSanPham = r.product_id
        LEFT JOIN NguoiDung u ON u.MaNguoiDung = r.user_id
        ORDER BY r.id DESC
    """
    if not _is_sqlite():
        sql = f"""
            SELECT r.*, COALESCE(sp.TenSanPham, N'SP #' + CAST(r.product_id AS NVARCHAR)) AS product_name,
                   {name_expr} AS user_name
            FROM product_reviews r
            LEFT JOIN SanPham sp ON sp.MaSanPham = r.product_id
            LEFT JOIN NguoiDung u ON u.MaNguoiDung = r.user_id
            ORDER BY r.id DESC
        """
    return query_all(sql)


def admin_toggle_review(review_id: int):
    row = query_one("SELECT id, is_visible FROM product_reviews WHERE id = ?", (review_id,))
    if not row:
        return False, "Không tìm thấy bình luận."
    new_val = 0 if int(row["is_visible"]) == 1 else 1
    conn = get_db_connection()
    try:
        conn.cursor().execute("UPDATE product_reviews SET is_visible = ? WHERE id = ?", (new_val, review_id))
        conn.commit()
        return True, "Đã cập nhật trạng thái hiển thị bình luận."
    finally:
        conn.close()


def admin_delete_review(review_id: int):
    conn = get_db_connection()
    try:
        conn.cursor().execute("DELETE FROM product_reviews WHERE id = ?", (review_id,))
        conn.commit()
        return True, "Đã xóa bình luận."
    finally:
        conn.close()


# ==============================================================================
# 2. QUẢN LÝ MÃ GIẢM GIÁ (VOUCHER / COUPON)
# ==============================================================================

def validate_and_calculate_voucher(code: str, subtotal: float, user_id: int = None):
    code = (code or "").strip().upper()
    if not code:
        return False, "Vui lòng nhập mã giảm giá.", 0.0, None

    voucher = query_one("SELECT * FROM vouchers WHERE UPPER(code) = ?", (code,))
    if not voucher:
        return False, "Mã giảm giá không tồn tại.", 0.0, None
    if int(voucher["is_active"]) != 1:
        return False, "Mã giảm giá hiện đang tạm khóa.", 0.0, None

    now = datetime.now()
    start_dt = _parse_dt(voucher["start_date"])
    end_dt = _parse_dt(voucher["end_date"])
    if start_dt and now < start_dt:
        return False, "Mã giảm giá chưa đến thời gian áp dụng.", 0.0, None
    if end_dt and now > end_dt:
        return False, "Mã giảm giá đã hết hạn sử dụng.", 0.0, None

    if int(voucher["usage_limit"]) > 0 and int(voucher["used_count"]) >= int(voucher["usage_limit"]):
        return False, "Mã giảm giá đã hết lượt sử dụng.", 0.0, None

    min_order = _f(voucher["min_order_amount"])
    if subtotal < min_order:
        return False, f"Đơn hàng tối thiểu {min_order:,.0f}đ mới được áp dụng mã {code}.", 0.0, None

    if user_id:
        used_by_user = query_one(
            "SELECT COUNT(*) AS cnt FROM voucher_usages WHERE voucher_id = ? AND user_id = ?",
            (voucher["id"], user_id),
        )
        per_limit = int(voucher.get("per_user_limit") or 1)
        if used_by_user and int(used_by_user["cnt"]) >= per_limit:
            return False, "Bạn đã sử dụng hết lượt cho mã giảm giá này.", 0.0, None

    d_type = voucher["discount_type"]
    d_val = _f(voucher["discount_value"])
    if d_type == "PERCENT":
        discount = subtotal * (d_val / 100.0)
        max_cap = _f(voucher.get("max_discount_amount"))
        if max_cap > 0:
            discount = min(discount, max_cap)
    else:
        discount = d_val

    discount = round(min(discount, subtotal), 0)
    return True, f"Áp dụng thành công mã {code} (-{discount:,.0f}đ).", discount, voucher


def record_voucher_usage(code: str, user_id: int, order_id: int, discount_amount: float):
    code = (code or "").strip().upper()
    if not code or discount_amount <= 0:
        return
    voucher = query_one("SELECT id FROM vouchers WHERE UPPER(code) = ?", (code,))
    if not voucher:
        return
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO voucher_usages (voucher_id, user_id, order_id, discount_amount, used_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (voucher["id"], user_id or 0, order_id, discount_amount, _now_str()),
        )
        cur.execute("UPDATE vouchers SET used_count = used_count + 1 WHERE id = ?", (voucher["id"],))
        conn.commit()
    finally:
        conn.close()


def admin_list_vouchers():
    return query_all("SELECT * FROM vouchers ORDER BY id DESC")


def admin_save_voucher(data: dict, voucher_id: int = None):
    code = (data.get("code") or "").strip().upper()
    title = (data.get("title") or "").strip()
    discount_type = data.get("discount_type", "FIXED")
    discount_value = _f(data.get("discount_value"))
    max_discount = data.get("max_discount_amount")
    max_discount_val = _f(max_discount) if max_discount not in (None, "", "0") else None
    min_order = _f(data.get("min_order_amount"))
    usage_limit = int(data.get("usage_limit") or 100)
    per_user_limit = int(data.get("per_user_limit") or 1)
    start_date = (data.get("start_date") or "").replace("T", " ")
    end_date = (data.get("end_date") or "").replace("T", " ")
    is_active = 1 if str(data.get("is_active", "1")) in ("1", "true", "on") else 0

    if not code or not title or discount_value <= 0:
        return False, "Vui lòng nhập đầy đủ mã code, tên chương trình và giá trị giảm > 0."
    if discount_type == "PERCENT" and discount_value > 100:
        return False, "Giảm theo phần trăm không được vượt quá 100%."

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if voucher_id:
            cur.execute(
                """
                UPDATE vouchers
                SET code = ?, title = ?, discount_type = ?, discount_value = ?,
                    max_discount_amount = ?, min_order_amount = ?, usage_limit = ?,
                    per_user_limit = ?, start_date = ?, end_date = ?, is_active = ?
                WHERE id = ?
                """,
                (
                    code, title, discount_type, discount_value, max_discount_val,
                    min_order, usage_limit, per_user_limit, start_date, end_date,
                    is_active, voucher_id
                ),
            )
            msg = f"Đã cập nhật mã giảm giá {code}."
        else:
            dup = query_one("SELECT id FROM vouchers WHERE UPPER(code) = ?", (code,))
            if dup:
                return False, f"Mã giảm giá {code} đã tồn tại."
            cur.execute(
                """
                INSERT INTO vouchers (
                    code, title, discount_type, discount_value, max_discount_amount,
                    min_order_amount, usage_limit, used_count, per_user_limit,
                    start_date, end_date, is_active, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?)
                """,
                (
                    code, title, discount_type, discount_value, max_discount_val,
                    min_order, usage_limit, per_user_limit, start_date, end_date,
                    is_active, _now_str()
                ),
            )
            msg = f"Đã tạo mã giảm giá {code}."
        conn.commit()
        return True, msg
    finally:
        conn.close()


def admin_toggle_voucher(voucher_id: int):
    row = query_one("SELECT id, is_active FROM vouchers WHERE id = ?", (voucher_id,))
    if not row:
        return False, "Không tìm thấy mã giảm giá."
    new_state = 0 if int(row["is_active"]) == 1 else 1
    conn = get_db_connection()
    try:
        conn.cursor().execute("UPDATE vouchers SET is_active = ? WHERE id = ?", (new_state, voucher_id))
        conn.commit()
        return True, "Đã cập nhật trạng thái mã giảm giá."
    finally:
        conn.close()


# ==============================================================================
# 3. ĐỔI TRẢ & HOÀN TIỀN ĐƠN HÀNG (ORDER RETURNS)
# ==============================================================================

def create_order_return_request(order_id: int, user_id: int, request_type: str, reason: str, evidence_url: str = ""):
    reason = (reason or "").strip()
    if len(reason) < 5:
        return False, "Vui lòng mô tả lý do đổi/trả chi tiết (tối thiểu 5 ký tự)."
    if request_type not in ("RETURN", "EXCHANGE"):
        request_type = "RETURN"

    dh_cols = _table_columns("DonHang")
    user_col = _pick_col(dh_cols, ("MaNguoiDung", "MaKhachHang"), "MaNguoiDung")
    status_col = _pick_col(dh_cols, ("TrangThai", "TrangThaiDonHang"), "TrangThai")
    total_col = _pick_col(dh_cols, ("TongTien", "ThanhTien", "TongThanhToan"), "TongTien")

    order = query_one(
        f"SELECT MaDonHang, {user_col} AS uid, {status_col} AS st, {total_col} AS amt FROM DonHang WHERE MaDonHang = ?",
        (order_id,),
    )
    if not order or int(order["uid"]) != int(user_id):
        return False, "Không tìm thấy đơn hàng hợp lệ của bạn."
    if order["st"] not in COMPLETED_ORDER_STATUSES:
        return False, "Chỉ đơn hàng đã giao thành công mới có thể gửi yêu cầu đổi/trả."

    existing = query_one(
        "SELECT id FROM order_returns WHERE order_id = ? AND status IN ('PENDING', 'APPROVED')",
        (order_id,),
    )
    if existing:
        return False, "Đơn hàng này đã có yêu cầu đổi/trả đang xử lý hoặc đã được duyệt."

    refund_amt = _f(order["amt"]) if request_type == "RETURN" else 0.0
    conn = get_db_connection()
    try:
        conn.cursor().execute(
            """
            INSERT INTO order_returns (
                order_id, user_id, request_type, reason, evidence_url,
                refund_amount, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'PENDING', ?)
            """,
            (order_id, user_id, request_type, reason, evidence_url.strip(), refund_amt, _now_str()),
        )
        conn.commit()
        return True, "Đã gửi yêu cầu đổi/trả hàng thành công. Quản trị viên sẽ phản hồi sớm nhất."
    finally:
        conn.close()


def get_order_return_info(order_id: int):
    return query_one(
        "SELECT * FROM order_returns WHERE order_id = ? ORDER BY id DESC",
        (order_id,),
    )


def admin_list_returns():
    name_expr = _user_name_expr("u")
    sql = f"""
        SELECT r.*, {name_expr} AS customer_name
        FROM order_returns r
        LEFT JOIN NguoiDung u ON u.MaNguoiDung = r.user_id
        ORDER BY CASE WHEN r.status = 'PENDING' THEN 0 ELSE 1 END, r.id DESC
    """
    return query_all(sql)


def admin_process_return(return_id: int, action: str, admin_note: str = ""):
    if action not in ("APPROVED", "REJECTED"):
        return False, "Hành động xử lý không hợp lệ."

    req = query_one("SELECT * FROM order_returns WHERE id = ?", (return_id,))
    if not req:
        return False, "Không tìm thấy yêu cầu đổi/trả."
    if req["status"] != "PENDING":
        return False, "Yêu cầu này đã được xử lý trước đó."

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE order_returns
            SET status = ?, admin_note = ?, resolved_at = ?
            WHERE id = ?
            """,
            (action, (admin_note or "").strip(), _now_str(), return_id),
        )

        # Duyệt TRẢ HÀNG HOÀN TIỀN -> cập nhật trạng thái đơn & hoàn tồn kho BienTheSanPham
        if action == "APPROVED" and req["request_type"] == "RETURN":
            order_id = req["order_id"]
            dh_cols = _table_columns("DonHang")
            status_col = _pick_col(dh_cols, ("TrangThai", "TrangThaiDonHang"), "TrangThai")
            cur.execute(
                f"UPDATE DonHang SET {status_col} = ? WHERE MaDonHang = ?",
                ("Đã hoàn trả", order_id),
            )

            items = query_all(
                "SELECT MaBienThe, SoLuong FROM ChiTietDonHang WHERE MaDonHang = ?",
                (order_id,),
            )
            for it in items:
                cur.execute(
                    "UPDATE BienTheSanPham SET SoLuongTon = COALESCE(SoLuongTon, 0) + ? WHERE MaBienThe = ?",
                    (int(it["SoLuong"] or 0), it["MaBienThe"]),
                )

        conn.commit()
        msg = "Đã duyệt yêu cầu đổi/trả và hoàn tồn kho biến thể." if action == "APPROVED" else "Đã từ chối yêu cầu đổi/trả."
        return True, msg
    finally:
        conn.close()


# ==============================================================================
# 4. THỐNG KÊ DOANH THU & XUẤT BÁO CÁO CSV
# ==============================================================================

def get_revenue_report(start_date: str = None, end_date: str = None):
    today = datetime.now().date()
    if not end_date:
        end_date = today.strftime("%Y-%m-%d")
    if not start_date:
        start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")

    start_dt = f"{start_date} 00:00:00"
    end_dt = f"{end_date} 23:59:59"

    dh_cols = _table_columns("DonHang")
    ct_cols = _table_columns("ChiTietDonHang")

    status_col = _pick_col(dh_cols, ("TrangThai", "TrangThaiDonHang"), "TrangThai")
    total_col = _pick_col(dh_cols, ("TongTien", "ThanhTien", "TongThanhToan"), "TongTien")
    date_col = _pick_col(dh_cols, ("NgayDat", "NgayTao", "ThoiGianTao"), "NgayDat")
    price_col = _pick_col(ct_cols, ("DonGia", "GiaBan", "Gia"), "DonGia")

    orders = query_all(
        f"""
        SELECT MaDonHang, {status_col} AS status, COALESCE({total_col}, 0) AS total_amount,
               {date_col} AS created_at
        FROM DonHang
        WHERE {date_col} >= ? AND {date_col} <= ?
        ORDER BY {date_col} ASC
        """,
        (start_dt, end_dt),
    )

    gross_revenue = sum(_f(o["total_amount"]) for o in orders if o["status"] in COMPLETED_ORDER_STATUSES)
    completed_count = sum(1 for o in orders if o["status"] in COMPLETED_ORDER_STATUSES)
    cancelled_count = sum(1 for o in orders if o["status"] in CANCELLED_ORDER_STATUSES)
    pending_count = len(orders) - completed_count - cancelled_count

    voucher_row = query_one(
        "SELECT COALESCE(SUM(discount_amount), 0) AS total_disc FROM voucher_usages WHERE used_at >= ? AND used_at <= ?",
        (start_dt, end_dt),
    )
    total_discount = _f(voucher_row["total_disc"]) if voucher_row else 0.0

    refund_row = query_one(
        """
        SELECT COALESCE(SUM(refund_amount), 0) AS total_ref
        FROM order_returns
        WHERE status = 'APPROVED' AND request_type = 'RETURN'
          AND resolved_at >= ? AND resolved_at <= ?
        """,
        (start_dt, end_dt),
    )
    total_refund = _f(refund_row["total_ref"]) if refund_row else 0.0
    net_revenue = max(0.0, gross_revenue - total_refund)

    daily_map = {}
    for o in orders:
        if o["status"] in COMPLETED_ORDER_STATUSES:
            day_key = str(o["created_at"])[:10]
            daily_map[day_key] = daily_map.get(day_key, 0.0) + _f(o["total_amount"])
    daily_series = [{"date": k, "revenue": v} for k, v in sorted(daily_map.items())]

    placeholders = ",".join(["?"] * len(COMPLETED_ORDER_STATUSES))
    top_products_raw = query_all(
        f"""
        SELECT sp.MaSanPham AS id, sp.TenSanPham AS product_name,
               SUM(ct.SoLuong) AS sold_qty,
               SUM(ct.SoLuong * COALESCE(ct.{price_col}, sp.GiaBan)) AS revenue
        FROM ChiTietDonHang ct
        INNER JOIN BienTheSanPham bt ON bt.MaBienThe = ct.MaBienThe
        INNER JOIN SanPham sp ON sp.MaSanPham = bt.MaSanPham
        INNER JOIN DonHang dh ON dh.MaDonHang = ct.MaDonHang
        WHERE dh.{status_col} IN ({placeholders})
          AND dh.{date_col} >= ? AND dh.{date_col} <= ?
        GROUP BY sp.MaSanPham, sp.TenSanPham
        """,
        (*COMPLETED_ORDER_STATUSES, start_dt, end_dt),
    )
    top_products = sorted(top_products_raw, key=lambda x: -int(x["sold_qty"] or 0))[:5]

    low_stock = query_all(
        """
        SELECT sp.MaSanPham AS id, sp.TenSanPham AS product_name,
               COALESCE(SUM(bt.SoLuongTon), 0) AS stock
        FROM SanPham sp
        LEFT JOIN BienTheSanPham bt ON bt.MaSanPham = sp.MaSanPham
        GROUP BY sp.MaSanPham, sp.TenSanPham
        HAVING COALESCE(SUM(bt.SoLuongTon), 0) <= 5
        ORDER BY stock ASC
        """
    )

    return {
        "start_date": start_date,
        "end_date": end_date,
        "total_orders": len(orders),
        "completed_count": completed_count,
        "pending_count": pending_count,
        "cancelled_count": cancelled_count,
        "gross_revenue": gross_revenue,
        "total_discount": total_discount,
        "total_refund": total_refund,
        "net_revenue": net_revenue,
        "daily_series": daily_series,
        "top_products": top_products,
        "low_stock": low_stock,
    }


def export_revenue_csv(start_date: str = None, end_date: str = None) -> bytes:
    report = get_revenue_report(start_date, end_date)
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["BAO CAO DOANH THU TUAN 6", f"Tu {report['start_date']} den {report['end_date']}"])
    writer.writerow([])
    writer.writerow(["Chi so", "Gia tri"])
    writer.writerow(["Tong so don hang", report["total_orders"]])
    writer.writerow(["Don hoan thanh", report["completed_count"]])
    writer.writerow(["Don dang xu ly", report["pending_count"]])
    writer.writerow(["Don huy / hoan tra", report["cancelled_count"]])
    writer.writerow(["Doanh thu gop (VND)", int(report["gross_revenue"])])
    writer.writerow(["Tong giam gia Voucher (VND)", int(report["total_discount"])])
    writer.writerow(["Tong hoan tra (VND)", int(report["total_refund"])])
    writer.writerow(["Doanh thu thuan (VND)", int(report["net_revenue"])])
    writer.writerow([])
    writer.writerow(["Ngay", "Doanh thu (VND)"])
    for row in report["daily_series"]:
        writer.writerow([row["date"], int(row["revenue"])])
    writer.writerow([])
    writer.writerow(["Top san pham ban chay", "So luong ban", "Doanh thu (VND)"])
    for p in report["top_products"]:
        writer.writerow([p["product_name"], p["sold_qty"], int(_f(p["revenue"]))])

    return output.getvalue().encode("utf-8-sig")
def apply_voucher_to_created_order(code: str, subtotal: float, user_id: int, order_id: int):
    """Kiểm tra lại voucher phía server, trừ tiền trên DonHang và lưu lịch sử dùng mã."""
    ok, _, discount, _ = validate_and_calculate_voucher(code, subtotal, user_id)
    if not ok or discount <= 0:
        return 0.0

    dh_cols = _table_columns("DonHang")
    total_col = _pick_col(dh_cols, ("TongTien", "ThanhTien", "TongThanhToan"), "TongTien")

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            f"""
            UPDATE DonHang
            SET {total_col} = CASE WHEN COALESCE({total_col}, 0) - ? < 0 THEN 0 ELSE COALESCE({total_col}, 0) - ? END
            WHERE MaDonHang = ?
            """,
            (discount, discount, order_id),
        )
        conn.commit()
    finally:
        conn.close()

    record_voucher_usage(code, user_id, order_id, discount)
    return discount


def get_user_returns_map(user_id: int) -> dict:
    """Trả về dict {order_id: return_record} của khách hàng để hiển thị trên /account/orders."""
    if not user_id:
        return {}
    rows = query_all(
        "SELECT * FROM order_returns WHERE user_id = ? ORDER BY id ASC",
        (user_id,),
    )
    return {int(r["order_id"]): r for r in rows}