"""W4-008: Transaction giữ đúng tồn kho + vòng đời đơn hàng (SQL Server là đích, SQLite chỉ demo/test).

QUY TẮC TỒN KHO (đã áp dụng trong code và kiểm thử):
  1. Tạo đơn hợp lệ  -> TRỪ tồn theo từng biến thể (BienTheSanPham.SoLuongTon), DonHang.DaTruKho = 1.
  2. Đơn bị hủy / bị từ chối (không xác nhận) / thanh toán online thất bại -> HOÀN đúng số lượng
     đã trừ, DonHang.DaTruKho = 0. Hoàn chỉ xảy ra khi DaTruKho = 1 nên KHÔNG BAO GIỜ hoàn 2 lần.
  3. Không đủ tồn ở BẤT KỲ dòng nào -> ROLLBACK toàn bộ: không có đơn, không dòng nào bị trừ.
  4. Tồn không âm: lệnh trừ là UPDATE có điều kiện (SoLuongTon >= số mua) và kiểm tra rowcount,
     cộng thêm CHECK SoLuongTon >= 0 của bảng. Hai khách mua cùng lúc 1 sản phẩm cuối cùng:
     đúng 1 người thành công.

KHÓA / ĐỒNG THỜI:
  - SQL Server: đọc hàng bằng WITH (UPDLOCK, ROWLOCK) và luôn khóa biến thể theo thứ tự MaBienThe tăng dần
    để hai giao dịch không khóa chéo nhau (deadlock). Isolation mặc định READ COMMITTED là đủ vì lệnh
    trừ tồn là một câu UPDATE nguyên tử có điều kiện.
  - SQLite: BEGIN IMMEDIATE (khóa ghi toàn DB) cho mỗi giao dịch.

Tất cả thay đổi trạng thái đơn đi qua module này để cột cũ DonHang.TrangThai luôn khớp cột mới
(SQL Server có CHECK CK_DonHang_DongBoTrangThaiCu bắt lỗi nếu lệch).
Mọi truy vấn tham số hóa bằng dấu ?.
"""
import re
from contextlib import contextmanager
from decimal import Decimal

from flask import current_app

from ..db import get_db_connection

# --- Bộ giá trị trạng thái (khớp CHECK trong migration_w4_giao_dich_sqlserver.sql) ---
XN_CHO, XN_DA, XN_TUCHOI = "Chờ xác nhận", "Đã xác nhận", "Từ chối"
GH_CHUA, GH_CHUAN_BI, GH_DANG, GH_DA, GH_THAT_BAI = "Chưa giao", "Đang chuẩn bị", "Đang giao", "Đã giao", "Giao thất bại"
TT_CHUA, TT_DA, TT_HOAN = "Chưa thanh toán", "Đã thanh toán", "Hoàn tiền"
GD_CHO, GD_OK, GD_FAIL, GD_HOAN = "Chờ xử lý", "Thành công", "Thất bại", "Hoàn tiền"
PAYMENT_LABEL = {"cod": "COD", "bank_transfer": "Chuyển khoản"}
STAFF_ROLES = {"Admin", "Seller"}
MAX_QTY = 99


class InventoryError(ValueError):
    """Lỗi nghiệp vụ có thể hiện cho người dùng (không phải lỗi hệ thống)."""


class InsufficientStockError(InventoryError):
    pass


class InvalidOrderStateError(InventoryError):
    pass


def _backend():
    return current_app.config["DB_BACKEND"]


def _now_sql(backend):
    """Giờ lấy từ CHÍNH database (không dùng giờ máy chạy Flask) để luôn thỏa CHECK ThoiDiem >= NgayDat."""
    return "SYSDATETIME()" if backend == "sqlserver" else "CURRENT_TIMESTAMP"


def _money(value, backend):
    return float(value) if backend == "sqlite" else Decimal(str(value)).quantize(Decimal("0.01"))


def normalize_phone(raw):
    """'0912 345-678' -> '0912345678' (khớp CHECK chỉ gồm chữ số và dấu +)."""
    cleaned = re.sub(r"[\s.\-()]", "", str(raw or ""))
    return cleaned if re.fullmatch(r"\+?\d{9,15}", cleaned) else None


@contextmanager
def _transaction():
    """Một giao dịch: commit khi thoát bình thường, rollback + ném lại lỗi khi có ngoại lệ."""
    conn = get_db_connection()
    backend = _backend()
    try:
        cur = conn.cursor()
        if backend == "sqlite":
            cur.execute("BEGIN IMMEDIATE")
        yield cur, backend
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def normalize_items(basket):
    """{'12': 2, ...} -> {12: 2}. Từ chối số lượng/biến thể sai và dòng trùng."""
    items = {}
    for variant_id, amount in (basket or {}).items():
        try:
            vid, qty = int(variant_id), int(amount)
        except (TypeError, ValueError):
            raise InventoryError("Giỏ hàng có dữ liệu không hợp lệ.")
        if vid < 1 or qty < 1 or qty > MAX_QTY or vid in items:
            raise InventoryError("Số lượng hoặc biến thể không hợp lệ.")
        items[vid] = qty
    if not items:
        raise InventoryError("Giỏ hàng đang trống.")
    return items


def _lock_hint(backend):
    return " WITH (UPDLOCK, ROWLOCK)" if backend == "sqlserver" else ""


def _describe(row):
    return f"{row[3]} ({row[4]}/{row[5]})"


def reserve_stock(cur, backend, items):
    """Khóa + kiểm tra + trừ tồn cho mọi dòng trong CÙNG giao dịch của người gọi.

    items: {MaBienThe: SoLuong}. Trả về danh sách dòng đã chốt giá:
    [(vid, qty, giá, tên SP, màu, size)]. Ném InsufficientStockError nếu thiếu hàng; người gọi PHẢI
    rollback (context _transaction làm việc đó) để các dòng đã trừ trước đó được trả lại.
    """
    lines = []
    for vid in sorted(items):                       # thứ tự cố định chống deadlock
        qty = items[vid]
        cur.execute(
            "SELECT bt.MaBienThe, bt.SoLuongTon, sp.GiaBan, sp.TenSanPham, bt.MauSac, bt.KichThuoc, sp.HienThi "
            f"FROM BienTheSanPham bt{_lock_hint(backend)} JOIN SanPham sp ON sp.MaSanPham = bt.MaSanPham "
            "WHERE bt.MaBienThe = ?", (vid,))
        row = cur.fetchone()
        if not row or not row[6]:                   # không có hoặc sản phẩm đang ẩn
            raise InsufficientStockError(f"Sản phẩm (mã biến thể {vid}) không còn bán.")
        if int(row[1]) < qty:
            raise InsufficientStockError(
                f"{_describe(row)} đã hết hoặc không đủ hàng (còn {int(row[1])}, cần {qty}).")
        hint = " WITH (ROWLOCK)" if backend == "sqlserver" else ""
        cur.execute(f"UPDATE BienTheSanPham{hint} SET SoLuongTon = SoLuongTon - ? "
                    "WHERE MaBienThe = ? AND SoLuongTon >= ?", (qty, vid, qty))
        if cur.rowcount != 1:                       # có người khác vừa mua mất
            raise InsufficientStockError(f"{_describe(row)} vừa hết hàng, vui lòng thử lại.")
        lines.append((vid, qty, row[2], row[3], row[4], row[5]))
    return lines


def release_stock(cur, order_id):
    """Cộng lại tồn theo các dòng của đơn. CHỈ gọi sau khi đã chuyển DaTruKho 1 -> 0 thành công."""
    cur.execute("SELECT MaBienThe, SoLuong FROM ChiTietDonHang WHERE MaDonHang = ? ORDER BY MaBienThe", (order_id,))
    for vid, qty in cur.fetchall():
        cur.execute("UPDATE BienTheSanPham SET SoLuongTon = SoLuongTon + ? WHERE MaBienThe = ?", (int(qty), int(vid)))


def place_order(contact, basket, user_id=None):
    """Tạo đơn + trừ tồn + ghi giao dịch thanh toán chờ xử lý trong MỘT giao dịch. Trả về MaDonHang.

    contact: dict đã qua validate_checkout (full_name, phone, email, fulfillment, address, payment_method, note).
    """
    items = normalize_items(basket)
    with _transaction() as (cur, backend):
        lines = reserve_stock(cur, backend, items)
        total = sum(Decimal(str(price)).quantize(Decimal("0.01")) * qty for _, qty, price, *_ in lines)
        pay_label = PAYMENT_LABEL[contact["payment_method"]]
        fee = _money(0, backend)               # phí giao hàng do cửa hàng xác nhận sau; 0 = chưa tính
        values = (user_id, XN_CHO, _money(total, backend), contact["fulfillment"], contact["full_name"],
                  normalize_phone(contact["phone"]), contact["address"] or None, fee, pay_label,
                  TT_CHUA, XN_CHO, GH_CHUA, 0, 1)
        columns = ("MaNguoiDung, TrangThai, TongTien, HinhThucNhanHang, TenNguoiNhan, SdtNguoiNhan, DiaChiGiaoHang, "
                   "PhiVanChuyen, PhuongThucThanhToan, TrangThaiThanhToan, TrangThaiXacNhan, TrangThaiGiaoHang, "
                   "DaHuy, DaTruKho")
        marks = ",".join("?" for _ in values)
        if backend == "sqlite":
            cur.execute(f"INSERT INTO DonHang ({columns}) VALUES ({marks})", values)
            order_id = cur.lastrowid
        else:
            cur.execute(f"INSERT INTO DonHang ({columns}) OUTPUT INSERTED.MaDonHang VALUES ({marks})", values)
            order_id = int(cur.fetchone()[0])
        for vid, qty, price, name, color, size in lines:
            cur.execute("INSERT INTO ChiTietDonHang (MaDonHang, MaBienThe, SoLuong, DonGia, TenSanPham, MauSac, KichThuoc) "
                        "VALUES (?,?,?,?,?,?,?)", (order_id, vid, qty, _money(price, backend), name, color, size))
        # Bảng phụ cũ (email, ghi chú, phí NULL = chưa tính) giữ để tương thích; cột chính nằm trên DonHang.
        if backend == "sqlite":
            from .checkout import CHECKOUT_META_SQLITE
            cur.execute(CHECKOUT_META_SQLITE)
        cur.execute("""INSERT INTO ThongTinGiaoDich (MaDonHang, HoTen, SoDienThoai, Email, HinhThucNhanHang,
                       DiaChiGiaoHang, PhuongThucThanhToan, TrangThaiThanhToan, PhiVanChuyen, GhiChu)
                       VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (order_id, contact["full_name"], contact["phone"], contact["email"] or None,
                     contact["fulfillment"], contact["address"] or None, contact["payment_method"], TT_CHUA,
                     0 if contact["fulfillment"] == "pickup" else None, contact["note"] or None))
        cur.execute("INSERT INTO GiaoDichThanhToan (MaDonHang, PhuongThuc, SoTien, TrangThai) VALUES (?,?,?,?)",
                    (order_id, pay_label, _money(total, backend), GD_CHO))
        return order_id


# ----------------------------------------------------------------------------------------------
# Vòng đời đơn: mỗi hàm là một giao dịch; đọc đơn có khóa rồi UPDATE có điều kiện trạng thái.
# ----------------------------------------------------------------------------------------------
_ORDER_SQL = ("SELECT MaDonHang, MaNguoiDung, TrangThaiXacNhan, TrangThaiGiaoHang, TrangThaiThanhToan, DaHuy, "
              "DaTruKho, PhuongThucThanhToan FROM DonHang{hint} WHERE MaDonHang = ?")


def _load_order(cur, backend, order_id):
    cur.execute(_ORDER_SQL.format(hint=_lock_hint(backend)), (order_id,))
    row = cur.fetchone()
    if not row:
        raise InvalidOrderStateError("Không tìm thấy đơn hàng.")
    keys = ("id", "user", "xn", "gh", "tt", "huy", "tru_kho", "pttt")
    order = dict(zip(keys, row))
    order["huy"], order["tru_kho"] = bool(order["huy"]), bool(order["tru_kho"])
    return order


def _require_staff(cur, staff_id):
    cur.execute("SELECT vt.TenVaiTro FROM NguoiDung nd JOIN VaiTro vt ON vt.MaVaiTro = nd.MaVaiTro "
                "WHERE nd.MaNguoiDung = ? AND nd.TrangThai = 1", (staff_id,))
    row = cur.fetchone()
    if not row or row[0] not in STAFF_ROLES:
        raise InvalidOrderStateError("Chỉ Admin hoặc Seller đang hoạt động mới được thực hiện thao tác này.")


def _settle_payment_rows(cur, order_id, paid):
    """Đơn bị hủy: giao dịch đang chờ -> Thất bại; giao dịch đã thu tiền -> Hoàn tiền."""
    now = _now_sql(_backend())
    cur.execute(f"UPDATE GiaoDichThanhToan SET TrangThai = ?, NgayCapNhat = {now} WHERE MaDonHang = ? AND TrangThai = ?",
                (GD_FAIL, order_id, GD_CHO))
    if paid:
        cur.execute(f"UPDATE GiaoDichThanhToan SET TrangThai = ?, NgayCapNhat = {now} WHERE MaDonHang = ? AND TrangThai = ?",
                    (GD_HOAN, order_id, GD_OK))


def _cancel(cur, backend, order, reject_staff=None):
    """Chuyển đơn sang trạng thái kết thúc (hủy hoặc từ chối) và hoàn tồn đúng 1 lần."""
    now = _now_sql(backend)
    paid = order["tt"] == TT_DA
    new_pay = TT_HOAN if paid else order["tt"]
    if reject_staff is not None:
        cur.execute("UPDATE DonHang SET TrangThai = ?, TrangThaiXacNhan = ?, MaNVXacNhan = ?, "
                    f"ThoiDiemXacNhan = {now}, TrangThaiThanhToan = ?, DaTruKho = 0 "
                    "WHERE MaDonHang = ? AND DaHuy = 0 AND TrangThaiXacNhan = ?",
                    ("Đã hủy", XN_TUCHOI, reject_staff, new_pay, order["id"], XN_CHO))
    else:
        cur.execute(f"UPDATE DonHang SET TrangThai = ?, DaHuy = 1, ThoiDiemHuy = {now}, TrangThaiThanhToan = ?, "
                    "DaTruKho = 0 "
                    "WHERE MaDonHang = ? AND DaHuy = 0 AND TrangThaiXacNhan <> ? AND TrangThaiGiaoHang IN (?, ?)",
                    ("Đã hủy", new_pay, order["id"], XN_TUCHOI, GH_CHUA, GH_CHUAN_BI))
    if cur.rowcount != 1:
        raise InvalidOrderStateError("Đơn đã thay đổi trạng thái, không thể thực hiện thao tác này.")
    if order["tru_kho"]:
        release_stock(cur, order["id"])
    _settle_payment_rows(cur, order["id"], paid)


def confirm_order(order_id, staff_id):
    """Seller/Admin xác nhận đơn đang chờ (tồn đã được giữ từ lúc đặt, không trừ thêm)."""
    with _transaction() as (cur, backend):
        _require_staff(cur, staff_id)
        order = _load_order(cur, backend, order_id)
        if order["huy"] or order["xn"] != XN_CHO:
            raise InvalidOrderStateError("Chỉ xác nhận được đơn đang chờ xác nhận và chưa hủy.")
        cur.execute("UPDATE DonHang SET TrangThai = ?, TrangThaiXacNhan = ?, MaNVXacNhan = ?, "
                    f"ThoiDiemXacNhan = {_now_sql(backend)} WHERE MaDonHang = ? AND DaHuy = 0 AND TrangThaiXacNhan = ?",
                    (XN_DA, XN_DA, staff_id, order_id, XN_CHO))
        if cur.rowcount != 1:
            raise InvalidOrderStateError("Đơn vừa được xử lý bởi người khác.")


def reject_order(order_id, staff_id):
    """Không xác nhận (từ chối): hoàn tồn đúng 1 lần."""
    with _transaction() as (cur, backend):
        _require_staff(cur, staff_id)
        order = _load_order(cur, backend, order_id)
        if order["huy"] or order["xn"] != XN_CHO:
            raise InvalidOrderStateError("Chỉ từ chối được đơn đang chờ xác nhận và chưa hủy.")
        _cancel(cur, backend, order, reject_staff=staff_id)


def cancel_order(order_id, customer_id=None, staff_id=None):
    """Hủy đơn và hoàn tồn đúng 1 lần.

    - Khách (customer_id): chỉ đơn của mình và khi còn chờ xác nhận.
    - Nhân viên (staff_id): đến trước khi giao ('Chưa giao' hoặc 'Đang chuẩn bị').
    """
    if (customer_id is None) == (staff_id is None):
        raise InvalidOrderStateError("Cần chỉ rõ đúng một người thực hiện (khách hoặc nhân viên).")
    with _transaction() as (cur, backend):
        if staff_id is not None:
            _require_staff(cur, staff_id)
        order = _load_order(cur, backend, order_id)
        if order["huy"] or order["xn"] == XN_TUCHOI:
            raise InvalidOrderStateError("Đơn đã được hủy hoặc bị từ chối trước đó.")
        if customer_id is not None:
            if order["user"] is None or int(order["user"]) != int(customer_id):
                raise InvalidOrderStateError("Bạn không có quyền hủy đơn này.")
            if order["xn"] != XN_CHO:
                raise InvalidOrderStateError("Đơn đã được xác nhận, hãy liên hệ cửa hàng để hủy.")
        if order["gh"] not in (GH_CHUA, GH_CHUAN_BI):
            raise InvalidOrderStateError("Đơn đã giao hoặc đang giao, không thể hủy.")
        _cancel(cur, backend, order)


def mark_payment_failed(order_id):
    """Thanh toán online thất bại: hủy đơn chưa thu tiền, hoàn tồn đúng 1 lần.

    Không áp dụng cho COD (không có bước thanh toán online) hay đơn đã thu tiền."""
    with _transaction() as (cur, backend):
        order = _load_order(cur, backend, order_id)
        if order["pttt"] == PAYMENT_LABEL["cod"]:
            raise InvalidOrderStateError("Đơn COD không có bước thanh toán online.")
        if order["huy"] or order["xn"] == XN_TUCHOI:
            raise InvalidOrderStateError("Đơn đã được hủy hoặc bị từ chối trước đó.")
        if order["tt"] != TT_CHUA:
            raise InvalidOrderStateError("Đơn đã thanh toán, hãy hủy/hoàn tiền thay vì báo thất bại.")
        _cancel(cur, backend, order)


def mark_paid(order_id, reference=None):
    """Ghi nhận đã thu tiền: giao dịch chờ -> Thành công (mã tham chiếu UNIQUE), đơn -> Đã thanh toán."""
    with _transaction() as (cur, backend):
        order = _load_order(cur, backend, order_id)
        if order["huy"] or order["xn"] == XN_TUCHOI:
            raise InvalidOrderStateError("Đơn đã hủy hoặc bị từ chối, không ghi nhận thanh toán.")
        if order["tt"] != TT_CHUA:
            raise InvalidOrderStateError("Đơn này không ở trạng thái chưa thanh toán.")
        try:
            cur.execute(f"UPDATE GiaoDichThanhToan SET TrangThai = ?, MaThamChieu = ?, NgayCapNhat = {_now_sql(backend)} "
                        "WHERE MaGiaoDich = (SELECT MAX(MaGiaoDich) FROM GiaoDichThanhToan "
                        "WHERE MaDonHang = ? AND TrangThai = ?)", (GD_OK, reference, order_id, GD_CHO))
        except Exception as exc:                     # UNIQUE MaThamChieu / một giao dịch thành công mỗi đơn
            if "unique" in str(exc).lower() or "duplicate" in str(exc).lower() or "IntegrityError" in type(exc).__name__:
                raise InvalidOrderStateError("Mã tham chiếu giao dịch đã được sử dụng.") from exc
            raise
        if cur.rowcount != 1:
            raise InvalidOrderStateError("Không có giao dịch thanh toán đang chờ cho đơn này.")
        cur.execute("UPDATE DonHang SET TrangThaiThanhToan = ? WHERE MaDonHang = ? AND TrangThaiThanhToan = ? AND DaHuy = 0",
                    (TT_DA, order_id, TT_CHUA))
        if cur.rowcount != 1:
            raise InvalidOrderStateError("Đơn vừa thay đổi trạng thái, thử lại.")
