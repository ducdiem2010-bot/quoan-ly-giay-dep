"""Đánh giá sản phẩm (Product Reviews).

Mọi truy vấn tham số hóa bằng dấu ?, chỉ dùng cú pháp chạy được trên cả SQLite
và SQL Server (phân trang và tính trung bình thực hiện bằng Python).
"""
from decimal import Decimal, ROUND_HALF_UP
from math import ceil
import re

from ..db import get_db_connection, query_all, query_one

PER_PAGE = 10
SORT_OPTIONS = {
    "newest": "dg.NgayDanhGia DESC, dg.MaDanhGia DESC",
    "highest": "dg.SoSao DESC, dg.MaDanhGia DESC",
    "lowest": "dg.SoSao ASC, dg.MaDanhGia DESC",
}
SORT_LABELS = {"newest": "Mới nhất", "highest": "Sao cao nhất", "lowest": "Sao thấp nhất"}

MIN_CONTENT = 10
MAX_CONTENT = 1000
MAX_TITLE = 150
MAX_REPLY = 500

_TAG_RE = re.compile(r"<[^>]*>")
_CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


class ReviewError(Exception):
    """Lỗi nghiệp vụ kèm mã HTTP thống nhất (400/401/403/404/409)."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def clean_text(value):
    """Bỏ thẻ HTML, ký tự điều khiển và khoảng trắng thừa (chống XSS lưu trữ)."""
    text = _TAG_RE.sub("", str(value or ""))
    text = text.replace("<", "").replace(">", "")
    return _CTRL_RE.sub("", text).strip()


def parse_review_input(data):
    """Kiểm tra dữ liệu gửi lên; trả về dict đã chuẩn hóa hoặc ném ReviewError(400)."""
    raw_stars = str(data.get("so_sao", "")).strip()
    if not re.fullmatch(r"[1-5]", raw_stars):
        raise ReviewError(400, "Số sao đánh giá phải là số nguyên từ 1 đến 5.")
    content = clean_text(data.get("noi_dung"))
    if len(content) < MIN_CONTENT:
        raise ReviewError(400, "Nội dung nhận xét cần tối thiểu 10 ký tự.")
    if len(content) > MAX_CONTENT:
        raise ReviewError(400, "Nội dung nhận xét tối đa 1000 ký tự.")
    title = clean_text(data.get("tieu_de"))
    if len(title) > MAX_TITLE:
        raise ReviewError(400, "Tiêu đề tối đa 150 ký tự.")
    order_id = None
    raw_order = str(data.get("ma_don_hang") or "").strip()
    if raw_order:
        if not raw_order.isdigit():
            raise ReviewError(400, "Mã đơn hàng không hợp lệ.")
        order_id = int(raw_order)
    return {"so_sao": int(raw_stars), "tieu_de": title or None,
            "noi_dung": content, "ma_don_hang": order_id}


# --------------------------------------------------------------------------
# Xác thực "đã mua" – chỉ tính đơn Hoàn thành của chính người dùng
# --------------------------------------------------------------------------
_ORDER_HAS_PRODUCT = """EXISTS (SELECT 1 FROM ChiTietDonHang ct
        JOIN BienTheSanPham bt ON ct.MaBienThe = bt.MaBienThe
        WHERE ct.MaDonHang = dh.MaDonHang AND bt.MaSanPham = ?)"""


def completed_orders_with_product(user_id, product_id):
    """Các đơn 'Hoàn thành' của user có chứa sản phẩm (mới nhất trước), kèm cờ đã đánh giá."""
    return query_all(
        """SELECT dh.MaDonHang, dh.NgayDat,
                  (SELECT COUNT(*) FROM DanhGiaSanPham dg
                    WHERE dg.MaNguoiDung = dh.MaNguoiDung AND dg.MaSanPham = ?
                      AND dg.MaDonHang = dh.MaDonHang) AS DaDanhGia
           FROM DonHang dh
           WHERE dh.MaNguoiDung = ? AND dh.TrangThai = 'Hoàn thành' AND """ + _ORDER_HAS_PRODUCT +
        " ORDER BY dh.NgayDat DESC, dh.MaDonHang DESC",
        (product_id, user_id, product_id))


def resolve_order(user_id, product_id, order_id=None):
    """Trả về MaDonHang dùng để đánh giá, hoặc ném 403/409."""
    orders = completed_orders_with_product(user_id, product_id)
    if order_id is not None:
        match = next((o for o in orders if int(o["MaDonHang"]) == order_id), None)
        if match is None:
            raise ReviewError(403, "Bạn chỉ có thể đánh giá sản phẩm thuộc đơn hàng đã hoàn thành của mình.")
        if int(match["DaDanhGia"]):
            raise ReviewError(409, "Bạn đã đánh giá sản phẩm này cho đơn hàng tương ứng.")
        return order_id
    if not orders:
        raise ReviewError(403, "Bạn cần có đơn hàng đã hoàn thành chứa sản phẩm này mới được đánh giá.")
    pending = next((o for o in orders if not int(o["DaDanhGia"])), None)
    if pending is None:
        raise ReviewError(409, "Bạn đã đánh giá sản phẩm này cho đơn hàng tương ứng.")
    return int(pending["MaDonHang"])


def create_review(user_id, product_id, data):
    """Lưu đánh giá mới; trả về MaDanhGia. data là dict đã qua parse_review_input()."""
    order_id = resolve_order(user_id, product_id, data["ma_don_hang"])
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO DanhGiaSanPham
               (MaSanPham, MaNguoiDung, MaDonHang, SoSao, TieuDe, NoiDung, TrangThaiHienThi)
               VALUES (?, ?, ?, ?, ?, ?, 1)""",
            (product_id, user_id, order_id, data["so_sao"], data["tieu_de"], data["noi_dung"]))
        conn.commit()
    except Exception as exc:
        conn.rollback()
        # Hai request đồng thời cùng qua bước kiểm tra: ràng buộc UNIQUE chặn bản ghi thứ hai.
        if "unique" in str(exc).lower() or "duplicate" in str(exc).lower() or "integrity" in type(exc).__name__.lower():
            raise ReviewError(409, "Bạn đã đánh giá sản phẩm này cho đơn hàng tương ứng.") from exc
        raise
    finally:
        conn.close()
    row = query_one("""SELECT MaDanhGia FROM DanhGiaSanPham
                       WHERE MaNguoiDung=? AND MaSanPham=? AND MaDonHang=?""",
                    (user_id, product_id, order_id))
    return int(row["MaDanhGia"]) if row else None


# --------------------------------------------------------------------------
# Hiển thị
# --------------------------------------------------------------------------
def _date_text(value):
    text = str(value or "")
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", text)
    return f"{m.group(3)}/{m.group(2)}/{m.group(1)}" if m else text[:10]


def get_review_summary(product_id):
    """Điểm TB (1 số thập phân), tổng lượt và phân bổ 1–5 sao (chỉ đánh giá đang hiển thị)."""
    rows = query_all(
        """SELECT SoSao, COUNT(*) AS SoLuong FROM DanhGiaSanPham
           WHERE MaSanPham = ? AND TrangThaiHienThi = 1 GROUP BY SoSao""", (product_id,))
    distribution = {star: 0 for star in range(1, 6)}
    for r in rows:
        distribution[int(r["SoSao"])] = int(r["SoLuong"])
    total = sum(distribution.values())
    if total:
        avg = (Decimal(sum(k * v for k, v in distribution.items())) / Decimal(total)
               ).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    else:
        avg = Decimal("0.0")
    percent = {k: (round(v * 100 / total) if total else 0) for k, v in distribution.items()}
    return {"average": float(avg), "total": total, "distribution": distribution, "percent": percent}


def list_reviews(product_id, rating=None, sort="newest", page=1, per_page=PER_PAGE):
    """Danh sách đánh giá hiển thị, kèm phân loại Size/Màu đã mua và phân trang."""
    if sort not in SORT_OPTIONS:
        sort = "newest"
    where, args = "dg.MaSanPham = ? AND dg.TrangThaiHienThi = 1", [product_id]
    if rating:
        where += " AND dg.SoSao = ?"
        args.append(rating)
    total = int(query_one("SELECT COUNT(*) AS n FROM DanhGiaSanPham dg WHERE " + where, tuple(args))["n"])
    pages = max(1, ceil(total / per_page))
    page = max(1, min(pages, page))
    rows = query_all(
        """SELECT dg.MaDanhGia, dg.MaDonHang, dg.SoSao, dg.TieuDe, dg.NoiDung, dg.NgayDanhGia,
                  dg.PhanHoiShop, dg.NgayPhanHoi, nd.HoVaTen
           FROM DanhGiaSanPham dg JOIN NguoiDung nd ON nd.MaNguoiDung = dg.MaNguoiDung
           WHERE """ + where + " ORDER BY " + SORT_OPTIONS[sort], tuple(args))
    offset = (page - 1) * per_page
    items = rows[offset:offset + per_page]
    for r in items:
        variants = query_all(
            """SELECT bt.KichThuoc, bt.MauSac FROM ChiTietDonHang ct
               JOIN BienTheSanPham bt ON bt.MaBienThe = ct.MaBienThe
               WHERE ct.MaDonHang = ? AND bt.MaSanPham = ? ORDER BY bt.MaBienThe""",
            (r["MaDonHang"], product_id))
        r["PhanLoai"] = ", ".join(f"Size {v['KichThuoc']} • {v['MauSac']}" for v in variants)
        r["NgayHienThi"] = _date_text(r["NgayDanhGia"])
        r["NgayPhanHoiHienThi"] = _date_text(r["NgayPhanHoi"]) if r["NgayPhanHoi"] else ""
        r["DaMuaHang"] = True  # chỉ lưu được khi đã mua (đơn Hoàn thành)
    return {"rows": items, "total": total, "page": page, "pages": pages,
            "per_page": per_page, "sort": sort, "rating": rating}


def build_review_context(product_id, args, session):
    """Dữ liệu cho phần #reviews của trang chi tiết sản phẩm."""
    try:
        rating = int(args.get("rating", ""))
        rating = rating if 1 <= rating <= 5 else None
    except (TypeError, ValueError):
        rating = None
    sort = args.get("sort", "newest")
    try:
        page = int(args.get("page", 1))
    except (TypeError, ValueError):
        page = 1
    ctx = {"review_summary": get_review_summary(product_id),
           "reviews": list_reviews(product_id, rating, sort, page),
           "review_sort_labels": SORT_LABELS,
           "review_eligible_orders": [], "review_can_submit": False,
           "review_already_done": False, "review_unavailable": False}
    if session.get("user_id") and session.get("role") == "Customer":
        orders = completed_orders_with_product(session["user_id"], product_id)
        open_orders = [o for o in orders if not int(o["DaDanhGia"])]
        ctx["review_eligible_orders"] = open_orders
        ctx["review_can_submit"] = bool(open_orders)
        ctx["review_already_done"] = bool(orders) and not open_orders
    return ctx


# --------------------------------------------------------------------------
# Quản trị
# --------------------------------------------------------------------------
def list_reviews_admin(status="", rating=None, keyword=""):
    where, args = [], []
    if status in ("0", "1"):
        where.append("dg.TrangThaiHienThi = ?")
        args.append(int(status))
    if rating:
        where.append("dg.SoSao = ?")
        args.append(rating)
    if keyword:
        where.append("(sp.TenSanPham LIKE ? OR nd.HoVaTen LIKE ? OR dg.NoiDung LIKE ?)")
        args.extend([f"%{keyword}%"] * 3)
    sql = """SELECT dg.MaDanhGia, dg.MaSanPham, dg.MaDonHang, dg.SoSao, dg.TieuDe, dg.NoiDung,
                    dg.PhanHoiShop, dg.TrangThaiHienThi, dg.NgayDanhGia,
                    sp.TenSanPham, nd.HoVaTen
             FROM DanhGiaSanPham dg
             JOIN SanPham sp ON sp.MaSanPham = dg.MaSanPham
             JOIN NguoiDung nd ON nd.MaNguoiDung = dg.MaNguoiDung"""
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY dg.NgayDanhGia DESC, dg.MaDanhGia DESC"
    rows = query_all(sql, tuple(args))
    for r in rows:
        r["NgayHienThi"] = _date_text(r["NgayDanhGia"])
    return rows


def _check_reply(reply):
    reply = clean_text(reply)
    if len(reply) > MAX_REPLY:
        raise ReviewError(400, "Phản hồi của shop tối đa 500 ký tự.")
    return reply


def toggle_review(review_id, reply=None):
    """Đảo TrangThaiHienThi; nếu có phản hồi thì lưu kèm NgayPhanHoi. Trả về trạng thái mới."""
    reply = _check_reply(reply)
    review = query_one("SELECT MaDanhGia, TrangThaiHienThi FROM DanhGiaSanPham WHERE MaDanhGia=?", (review_id,))
    if not review:
        raise ReviewError(404, "Không tìm thấy đánh giá.")
    new_state = 0 if int(review["TrangThaiHienThi"]) else 1
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if reply:
            cur.execute("""UPDATE DanhGiaSanPham SET TrangThaiHienThi=?, PhanHoiShop=?,
                           NgayPhanHoi=CURRENT_TIMESTAMP WHERE MaDanhGia=?""", (new_state, reply, review_id))
        else:
            cur.execute("UPDATE DanhGiaSanPham SET TrangThaiHienThi=? WHERE MaDanhGia=?", (new_state, review_id))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return new_state


def reply_review(review_id, reply):
    """Chỉ lưu phản hồi, không đổi trạng thái hiển thị."""
    reply = _check_reply(reply)
    if not reply:
        raise ReviewError(400, "Vui lòng nhập nội dung phản hồi.")
    if not query_one("SELECT MaDanhGia FROM DanhGiaSanPham WHERE MaDanhGia=?", (review_id,)):
        raise ReviewError(404, "Không tìm thấy đánh giá.")
    conn = get_db_connection()
    try:
        conn.cursor().execute("""UPDATE DanhGiaSanPham SET PhanHoiShop=?, NgayPhanHoi=CURRENT_TIMESTAMP
                                 WHERE MaDanhGia=?""", (reply, review_id))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
