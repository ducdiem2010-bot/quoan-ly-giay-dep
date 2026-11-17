"""Trả hàng sau Hoàn thành và đối soát tiền hoàn.

- TraHangChiTiet: chỉ ghi khi hàng thực nhận; giao dịch mới chỉ có số lượng trả, cộng kho khi thực nhận.
- HoanTienGiaoDich: chỉ ghi khi nhân viên xác nhận đã trả tiền thật.
- Doanh thu thuần theo khoản giảm doanh thu ĐÃ CHẤP NHẬN, không theo thời điểm chuyển tiền.
Tất cả thay đổi có khóa theo đơn, giao dịch nguyên tử và mã yêu cầu chống gửi lại.
"""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re
from hashlib import sha256
from flask import current_app
from ..db import get_db_connection, query_all, query_one
from .order_ops import OrderOperationError, _append_log

CENTS = Decimal('0.01')


def money(value):
    try:
        result = Decimal(str(value)).quantize(CENTS, rounding=ROUND_HALF_UP)
    except (ValueError, InvalidOperation, TypeError):
        raise OrderOperationError('Số tiền không hợp lệ.')
    if not result.is_finite() or result < 0 or result > Decimal('999999999999.99'):
        raise OrderOperationError('Số tiền không hợp lệ.')
    return result


def _start(cur):
    if current_app.config.get('DB_BACKEND', 'sqlite') == 'sqlite':
        cur.execute('BEGIN IMMEDIATE')
        return ''
    return ' WITH (UPDLOCK, HOLDLOCK)'


def _require_token(token):
    token = (token or '').strip()
    if not (16 <= len(token) <= 64) or not token.isascii() or not all(c.isalnum() or c in '-_' for c in token):
        raise OrderOperationError('Mã xác nhận không hợp lệ. Hãy tải lại trang và thử lại.')
    return token


def list_completed_returns(order_id):
    return query_all('''SELECT t.MaTraHang, t.MaDonHang, t.MaBienThe, t.SoLuong,
                        t.SoLuongTot, t.SoLuongHong, t.LyDo, t.TienGiamDoanhThu,
                        t.HoVaTenNguoiThucHien, t.ThoiGian, t.MaYeuCau, t.MaNhomTra, ct.DonGia,
                        COALESCE(ct.KichThuoc, bt.KichThuoc) AS KichThuoc,
                        COALESCE(ct.MauSac, bt.MauSac) AS MauSac,
                        COALESCE(ct.TenSanPham, sp.TenSanPham) AS TenSanPham
                     FROM TraHangChiTiet t
                     LEFT JOIN ChiTietDonHang ct ON ct.MaDonHang=t.MaDonHang AND ct.MaBienThe=t.MaBienThe
                     LEFT JOIN BienTheSanPham bt ON bt.MaBienThe=t.MaBienThe
                     LEFT JOIN SanPham sp ON sp.MaSanPham=bt.MaSanPham
                     WHERE t.MaDonHang=? ORDER BY t.MaTraHang DESC''', (order_id,))


def order_refund_summary(order_id):
    order = query_one('''SELECT dh.MaDonHang, dh.TrangThai, dh.TongTien,
                      COALESCE(tg.TrangThaiThanhToan,'Chưa thanh toán') AS ThanhToan
                      FROM DonHang dh LEFT JOIN ThongTinGiaoDich tg ON tg.MaDonHang=dh.MaDonHang
                      WHERE dh.MaDonHang=?''', (order_id,))
    if not order:
        raise OrderOperationError('Không tìm thấy đơn hàng.')
    approved = money(query_one('''SELECT COALESCE(SUM(TienGiamDoanhThu),0) AS total
                            FROM TraHangChiTiet WHERE MaDonHang=?''', (order_id,))['total'])
    paid = money(query_one('''SELECT COALESCE(SUM(SoTien),0) AS total
                        FROM HoanTienGiaoDich WHERE PhuongThuc IN ('cash','bank_transfer') AND MaDonHang=?''', (order_id,))['total'])
    if order['TrangThai'] == 'Đã hủy' and order['ThanhToan'] == 'Đã thanh toán':
        due = money(order['TongTien'])
    elif order['TrangThai'] == 'Hoàn thành':
        due = approved
    else:
        due = Decimal('0.00')
    due = min(due, money(order['TongTien']))
    remaining = max(Decimal('0.00'), due - paid)
    return {'approved': float(due), 'refunded': float(paid), 'remaining': float(remaining),
            'status': ('Không cần hoàn tiền' if due == 0 else
                       'Đã hoàn tiền' if remaining == 0 else
                       'Hoàn tiền một phần' if paid > 0 else 'Chờ hoàn tiền'),
            'gross': float(money(order['TongTien'])),
            'net_revenue': float(max(Decimal('0.00'), money(order['TongTien'])-approved)) if order['TrangThai']=='Hoàn thành' else 0}


def receive_completed_return(order_id, user_id, lines, token, reason=''):
    """lines: list[(MaBienThe, so_luong)]. Giá hoàn lấy từ đơn, không từ client.
    Cột Tot/Hong được giữ để đọc lịch sử; giao dịch mới ghi Tot=SoLuong, Hong=0.
    """
    token = _require_token(token)
    if not lines:
        raise OrderOperationError('Chọn ít nhất một sản phẩm trả.')
    reason = (reason or '').strip()
    if not reason or len(reason) > 255:
        raise OrderOperationError('Vui lòng nhập lý do trả hàng từ 1 đến 255 ký tự.')
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        lock = _start(cur)
        cur.execute(f'''SELECT TrangThai, TongTien, LichSuXuLy FROM DonHang{lock} WHERE MaDonHang=?''', (order_id,))
        order = cur.fetchone()
        if not order or order[0] != 'Hoàn thành':
            raise OrderOperationError('Chỉ có thể trả hàng đối với đơn đã Hoàn thành.')
        cur.execute(f'SELECT MaTraHang FROM TraHangChiTiet{lock} WHERE MaYeuCau=?', (token,))
        if cur.fetchone():
            raise OrderOperationError('Yêu cầu trả hàng này đã được xử lý. Không ghi trùng.')
        cur.execute('''SELECT ct.MaBienThe, ct.SoLuong, ct.DonGia,
                       COALESCE((SELECT SUM(t.SoLuong) FROM TraHangChiTiet t
                                 WHERE t.MaDonHang=ct.MaDonHang AND t.MaBienThe=ct.MaBienThe),0),
                       COALESCE((SELECT SUM(t.TienGiamDoanhThu) FROM TraHangChiTiet t
                                 WHERE t.MaDonHang=ct.MaDonHang AND t.MaBienThe=ct.MaBienThe),0)
                       FROM ChiTietDonHang ct WHERE ct.MaDonHang=?''', (order_id,))
        items = {int(r[0]):r for r in cur.fetchall()}
        if not items:
            raise OrderOperationError('Đơn không có sản phẩm để trả.')
        pending = []
        seen = set()
        for line in lines:
            if len(line) != 2 or any(not re.fullmatch(r'[0-9]+', str(v)) for v in line):
                raise OrderOperationError('Số lượng trả phải là số nguyên không âm.')
            variant, good = int(line[0]), int(line[1])
            bad = 0
            if variant in seen or variant not in items or good <= 0:
                raise OrderOperationError('Biến thể hoặc số lượng hàng trả không hợp lệ.')
            seen.add(variant)
            detail = items[variant]
            if good > int(detail[1])-int(detail[3]):
                raise OrderOperationError('Số lượng trả vượt quá số lượng còn lại của đơn.')
            unit = money(detail[2])
            reduction = unit * good
            pending.append((variant,good,bad,reduction))
        # Duyệt tổng hoàn giảm doanh thu trên một đơn, kể cả nhiều lần trả.
        previous = money(query_one_in_cursor(cur, 'SELECT COALESCE(SUM(TienGiamDoanhThu),0) FROM TraHangChiTiet WHERE MaDonHang=?', (order_id,)))
        if previous + sum((p[3] for p in pending), Decimal('0.00')) > money(order[1]):
            raise OrderOperationError('Tổng số tiền hoàn được duyệt vượt tổng tiền đơn hàng.')
        cur.execute('SELECT HoVaTen FROM NguoiDung WHERE MaNguoiDung=? AND MaVaiTro IN (1,2)',(user_id,))
        actor = cur.fetchone()
        if not actor:
            raise OrderOperationError('Tài khoản nhân viên không tồn tại.')
        # Mỗi dòng một token riêng, token chính dùng cho dòng đầu, các dòng tiếp có suffix.
        for index,(variant,good,bad,reduction) in enumerate(pending):
            line_token = token if index == 0 else sha256(f'{token}:{index}'.encode()).hexdigest()
            cur.execute('''INSERT INTO TraHangChiTiet
                (MaDonHang,MaBienThe,SoLuong,SoLuongTot,SoLuongHong,LyDo,TienGiamDoanhThu,
                 NguoiThucHien,HoVaTenNguoiThucHien,MaYeuCau,MaNhomTra)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                (order_id,variant,good+bad,good,bad,reason,float(reduction),user_id,actor[0],line_token,token))
            if good:
                cur.execute('UPDATE BienTheSanPham SET SoLuongTon=SoLuongTon+? WHERE MaBienThe=?', (good,variant))
                if cur.rowcount != 1:
                    raise OrderOperationError('Không thể cập nhật biến thể trong kho.')
        log = _append_log(order[2], f'Trả hàng đơn hoàn thành bởi user #{user_id}: '+', '.join(f'Biến thể #{v}: trả {g} đôi, hoàn {m}' for v,g,b,m in pending))
        cur.execute('UPDATE DonHang SET LichSuXuLy=? WHERE MaDonHang=?',(log,order_id))
        _sync_refund_state(cur,order_id)
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def query_one_in_cursor(cur, sql, params):
    cur.execute(sql, params)
    return cur.fetchone()[0]


def _sync_refund_state(cur, order_id):
    cur.execute('''SELECT dh.TrangThai, dh.TongTien, COALESCE(tg.TrangThaiThanhToan,'Chưa thanh toán')
                   FROM DonHang dh LEFT JOIN ThongTinGiaoDich tg ON tg.MaDonHang=dh.MaDonHang
                   WHERE dh.MaDonHang=?''',(order_id,))
    row=cur.fetchone()
    if not row:
        raise OrderOperationError('Không có đơn hàng.')
    if row[0]=='Đã hủy' and row[2]=='Đã thanh toán':
        due=money(row[1])
    elif row[0]=='Hoàn thành':
        due=money(query_one_in_cursor(cur, 'SELECT COALESCE(SUM(TienGiamDoanhThu),0) FROM TraHangChiTiet WHERE MaDonHang=?', (order_id,)))
    else:
        due=Decimal('0.00')
    paid=money(query_one_in_cursor(cur,"SELECT COALESCE(SUM(SoTien),0) FROM HoanTienGiaoDich WHERE PhuongThuc IN ('cash','bank_transfer') AND MaDonHang=?",(order_id,)))
    status=('Không cần hoàn tiền' if due==0 else 'Đã hoàn tiền' if paid>=due else 'Hoàn tiền một phần' if paid>0 else 'Chờ hoàn tiền')
    cur.execute('UPDATE DonHang SET TrangThaiHoanTien=? WHERE MaDonHang=?',(status,order_id))
    return due, paid


def confirm_refund_paid(order_id, user_id, amount, method, reference, token):
    token=_require_token(token)
    amount=money(amount)
    if amount <= 0:
        raise OrderOperationError('Số tiền hoàn phải lớn hơn 0.')
    if method not in ('cash','bank_transfer'):
        raise OrderOperationError('Phương thức hoàn tiền không hợp lệ.')
    reference=(reference or '').strip()[:100]
    conn=get_db_connection()
    try:
        cur=conn.cursor()
        lock=_start(cur)
        cur.execute(f'SELECT TrangThai,LichSuXuLy FROM DonHang{lock} WHERE MaDonHang=?',(order_id,))
        order=cur.fetchone()
        if not order or order[0] not in ('Hoàn thành','Đã hủy'):
            raise OrderOperationError('Chỉ xác nhận hoàn tiền cho đơn Hoàn thành có hàng trả hoặc đơn Đã hủy đã thu tiền.')
        cur.execute(f'SELECT MaHoanTien FROM HoanTienGiaoDich{lock} WHERE MaYeuCau=?',(token,))
        if cur.fetchone():
            raise OrderOperationError('Yêu cầu này đã được xác nhận hoàn tiền, không ghi trùng.')
        due,already=_sync_refund_state(cur,order_id)
        if amount > due-already:
            raise OrderOperationError('Số tiền hoàn vượt số tiền khách còn được nhận.')
        cur.execute('SELECT HoVaTen FROM NguoiDung WHERE MaNguoiDung=? AND MaVaiTro IN (1,2)',(user_id,))
        actor=cur.fetchone()
        if not actor:
            raise OrderOperationError('Tài khoản xác nhận không tồn tại.')
        cur.execute('''INSERT INTO HoanTienGiaoDich
                       (MaDonHang,SoTien,PhuongThuc,MaThamChieu,NguoiXacNhan,HoVaTenNguoiXacNhan,MaYeuCau)
                       VALUES (?,?,?,?,?,?,?)''',
                    (order_id,float(amount),method,reference,user_id,actor[0],token))
        _sync_refund_state(cur,order_id)
        log=_append_log(order[1],f'XÁC NHẬN ĐÃ HOÀN TIỀN {amount} ({method}) bởi user #{user_id}')
        cur.execute('UPDATE DonHang SET LichSuXuLy=? WHERE MaDonHang=?',(log,order_id))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def group_return_receipts(rows):
    """One explicit receipt group for all lines with the same MaNhomTra.

    Old records with NULL group remain separate; never infer by timestamps or reason.
    """
    groups = {}
    for row in rows or []:
        key = ('group', row['MaNhomTra']) if row.get('MaNhomTra') else ('legacy', int(row['MaTraHang']))
        if key not in groups:
            groups[key] = {'receipt_id': int(row['MaTraHang']), 'time': row['ThoiGian'],
                           'legacy_unverified': not bool(row.get('MaNhomTra')), 'lines': [], 'total': 0}
        receipt = groups[key]
        receipt['lines'].append(row)
        receipt['receipt_id'] = min(receipt['receipt_id'], int(row['MaTraHang']))
        receipt['total'] = float(money(receipt['total']) + money(row['TienGiamDoanhThu']))
    return sorted(groups.values(), key=lambda v: max(int(r['MaTraHang']) for r in v['lines']), reverse=True)
