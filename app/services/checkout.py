"""Ghi yêu cầu đặt hàng (demo). Không thu tiền, không trừ kho khi chờ xác nhận.

SQLite tự tạo bảng metadata khi đặt hàng để giữ nguyên 9 bảng của bộ kiểm thử W2 ban đầu.
SQL Server: quản trị viên PHẢI chạy migration_checkout_sqlserver.sql trước.
"""
import re
from decimal import Decimal
from flask import current_app, has_request_context, session
from ..db import get_db_connection

CHECKOUT_META_SQLITE = """
CREATE TABLE IF NOT EXISTS ThongTinGiaoDich (
    MaDonHang INTEGER PRIMARY KEY REFERENCES DonHang(MaDonHang) ON DELETE CASCADE,
    HoTen TEXT NOT NULL, SoDienThoai TEXT NOT NULL, Email TEXT,
    HinhThucNhanHang TEXT NOT NULL CHECK(HinhThucNhanHang IN ('delivery','pickup')),
    DiaChiGiaoHang TEXT, PhuongThucThanhToan TEXT NOT NULL
      CHECK(PhuongThucThanhToan IN ('cod','bank_transfer')),
    TrangThaiThanhToan TEXT NOT NULL DEFAULT 'Chưa thanh toán',
    PhiVanChuyen REAL,
    GhiChu TEXT, NgayTao TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

class CheckoutValidationError(ValueError):
    pass


def validate_checkout(form):
    data = {key: str(form.get(key, '')).strip() for key in
            ('full_name', 'phone', 'email', 'fulfillment', 'address', 'payment_method', 'note')}
    if not 2 <= len(data['full_name']) <= 100:
        raise CheckoutValidationError('Họ tên phải từ 2 đến 100 ký tự.')
    digits = re.sub(r'\D', '', data['phone'])
    if not 9 <= len(digits) <= 12 or len(data['phone']) > 20:
        raise CheckoutValidationError('Số điện thoại không hợp lệ.')
    if data['email'] and (len(data['email']) > 150 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', data['email'])):
        raise CheckoutValidationError('Email không hợp lệ.')
    if data['fulfillment'] not in {'pickup', 'delivery'}:
        raise CheckoutValidationError('Hãy chọn hình thức nhận hàng.')
    if data['fulfillment'] == 'delivery' and not 8 <= len(data['address']) <= 255:
        raise CheckoutValidationError('Hãy nhập địa chỉ giao hàng đầy đủ (8–255 ký tự).')
    if data['payment_method'] not in {'cod', 'bank_transfer'}:
        raise CheckoutValidationError('Chỉ hỗ trợ COD và yêu cầu chuyển khoản chờ xác nhận. Cổng online chưa hoạt động.')
    if len(data['note']) > 500:
        raise CheckoutValidationError('Ghi chú tối đa 500 ký tự.')
    if data['fulfillment'] == 'pickup':
        data['address'] = ''
    return data


def create_pending_order(form_data, basket, user_id=None, checkout_token=None):
    """Kiểm tra tồn kho trong transaction, lưu chi tiết và phương thức nhận/trả.

    Trả về mã đơn mới. Không có webhook/PSP; trạng thái thanh toán luôn CHƯA THANH TOÁN.
    Giá đặt chỉ gồm tiền sản phẩm; phí vận chuyển = NULL cho delivery (chờ xác nhận).
    Hỗ trợ checkout_token để chống tạo đơn trùng an toàn tại database (idempotency).
    """
    items = {}
    for variant_id, amount in basket.items():
        try:
            vid, qty = int(variant_id), int(amount)
        except (TypeError, ValueError):
            raise CheckoutValidationError('Giỏ hàng có dữ liệu không hợp lệ.')
        if vid < 1 or qty < 1 or qty > 99 or vid in items:
            raise CheckoutValidationError('Số lượng hoặc biến thể không hợp lệ.')
        items[vid] = qty
    if not items:
        raise CheckoutValidationError('Giỏ hàng đang trống.')
    backend = current_app.config['DB_BACKEND']
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if backend == 'sqlite':
            cur.execute('BEGIN IMMEDIATE')
            cur.execute(CHECKOUT_META_SQLITE)

        # Chống tạo đơn trùng (idempotency check cấp database)
        if checkout_token:
            cur.execute('SELECT MaDonHang, MaNguoiDung FROM DonHang WHERE CheckoutToken = ?', (checkout_token,))
            existing = cur.fetchone()
            if existing:
                owner_id = existing[1]
                if owner_id is not None and (user_id is None or int(owner_id) != int(user_id)):
                    raise CheckoutValidationError('Mã phiên đặt hàng không thuộc về tài khoản hiện tại.')
                if owner_id is None and user_id is not None:
                    raise CheckoutValidationError('Mã phiên đặt hàng không thuộc về tài khoản hiện tại.')
                if owner_id is None and user_id is None:
                    if has_request_context():
                        active_tok = session.get('_active_checkout_token')
                        proc_tok = session.get('_last_processed_checkout_token')
                        if checkout_token != active_tok and checkout_token != proc_tok:
                            raise CheckoutValidationError('Mã phiên đặt hàng không thuộc về phiên làm việc hiện tại.')
                conn.commit()
                return int(existing[0])

        total = Decimal('0')
        rows = []
        for vid, qty in items.items():
            lock = ' WITH (UPDLOCK, HOLDLOCK)' if backend == 'sqlserver' else ''
            cur.execute('SELECT bt.MaBienThe, bt.SoLuongTon, sp.GiaBan, sp.HienThi, sp.TenSanPham, bt.MauSac, bt.KichThuoc FROM BienTheSanPham bt '
                        f'JOIN SanPham sp{lock} ON sp.MaSanPham=bt.MaSanPham '
                        'WHERE bt.MaBienThe=?', (vid,))
            r = cur.fetchone()
            if not r:
                raise CheckoutValidationError(f'Sản phẩm có mã biến thể #{vid} không tồn tại.')
            if not bool(r[3]):
                raise CheckoutValidationError(f'Sản phẩm "{r[4]}" đã ngừng kinh doanh hoặc tạm ẩn, không thể đặt hàng.')
            if int(r[1]) < qty:
                raise CheckoutValidationError(f'Sản phẩm "{r[4]}" có biến thể #{vid} không đủ hàng (còn {r[1]}, cần {qty}).')
            price = Decimal(str(r[2])).quantize(Decimal('0.01'))
            p_name = str(r[4] or '')
            p_color = str(r[5] or '')
            p_size = str(r[6] or '')
            rows.append((vid, qty, price, p_name, p_color, p_size))
            total += price * qty
        if backend == 'sqlite':
            cur.execute("INSERT INTO DonHang (MaNguoiDung, TrangThai, TongTien, CheckoutToken) VALUES (?, 'Chờ xác nhận', ?, ?)",
                        (user_id, float(total), checkout_token))
            order_id = cur.lastrowid
        else:
            cur.execute("INSERT INTO DonHang (MaNguoiDung, TrangThai, TongTien, CheckoutToken) OUTPUT INSERTED.MaDonHang VALUES (?, N'Chờ xác nhận', ?, ?)",
                        (user_id, total, checkout_token))
            order_id = cur.fetchone()[0]
        for vid, qty, price, p_name, p_color, p_size in rows:
            cur.execute('INSERT INTO ChiTietDonHang (MaDonHang,MaBienThe,SoLuong,DonGia,TenSanPham,MauSac,KichThuoc) VALUES (?,?,?,?,?,?,?)',
                        (order_id, vid, qty, float(price) if backend == 'sqlite' else price, p_name, p_color, p_size))
        # Cập nhật tổng rõ ràng cho SQL Server (SQLite có trigger tính tự động).
        cur.execute('UPDATE DonHang SET TongTien=? WHERE MaDonHang=?',
                    (float(total) if backend == 'sqlite' else total, order_id))
        shipping_fee = 0 if form_data['fulfillment'] == 'pickup' else None
        cur.execute("""INSERT INTO ThongTinGiaoDich
            (MaDonHang,HoTen,SoDienThoai,Email,HinhThucNhanHang,DiaChiGiaoHang,
             PhuongThucThanhToan,TrangThaiThanhToan,PhiVanChuyen,GhiChu)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (order_id, form_data['full_name'], form_data['phone'], form_data['email'] or None,
             form_data['fulfillment'], form_data['address'] or None,
             form_data['payment_method'], 'Chưa thanh toán', shipping_fee, form_data['note'] or None))
        conn.commit()
        return order_id
    except Exception as exc:
        conn.rollback()
        if checkout_token and ('UNIQUE constraint failed' in str(exc) or 'IX_DonHang_CheckoutToken' in str(exc)):
            with get_db_connection() as rconn:
                row = rconn.execute('SELECT MaDonHang, MaNguoiDung FROM DonHang WHERE CheckoutToken = ?', (checkout_token,)).fetchone()
                if row:
                    owner_id = row[1]
                    if owner_id is not None and (user_id is None or int(owner_id) != int(user_id)):
                        raise CheckoutValidationError('Mã phiên đặt hàng không thuộc về tài khoản hiện tại.')
                    if owner_id is None and user_id is not None:
                        raise CheckoutValidationError('Mã phiên đặt hàng không thuộc về tài khoản hiện tại.')
                    if owner_id is None and user_id is None:
                        if has_request_context():
                            active_tok = session.get('_active_checkout_token')
                            proc_tok = session.get('_last_processed_checkout_token')
                            if checkout_token != active_tok and checkout_token != proc_tok:
                                raise CheckoutValidationError('Mã phiên đặt hàng không thuộc về phiên làm việc hiện tại.')
                    return int(row[0])
        raise
    finally:
        conn.close()
