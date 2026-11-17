"""Nghiệp vụ xử lý trạng thái đơn hàng, giao nhận, hoàn/trừ tồn kho và thanh toán.
Áp dụng transaction chặt chẽ, hỗ trợ cả SQLite và SQL Server.
Tách biệt 3 trạng thái độc lập:
1. DonHang.TrangThai: 'Chờ xác nhận', 'Đã xác nhận', 'Hoàn thành', 'Đã hủy'
2. ThongTinGiaoDich.TrangThaiThanhToan: 'Chưa thanh toán', 'Đã thanh toán'
3. DonHang.TrangThaiGiaoHang: 'Chưa giao', 'Đang giao', 'Đã giao'
"""
from datetime import datetime, timezone
from decimal import Decimal
from flask import current_app
from ..db import get_db_connection, query_one, query_all


class OrderOperationError(ValueError):
    pass


def _now_str():
    # Có offset rõ ràng cho log mới; dữ liệu log cũ không được tự chuyển giờ.
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _append_log(current_log, action_text):
    now = _now_str()
    entry = f"[{now}] {action_text}"
    if current_log:
        return f"{current_log}\n{entry}"
    return entry


def confirm_order_stock(order_id, user_id):
    """Xác nhận đơn hàng: kiểm tra tồn kho trong transaction và trừ kho thực tế.
    Chỉ thực hiện khi đơn ở trạng thái 'Chờ xác nhận'.
    """
    backend = current_app.config.get('DB_BACKEND', 'sqlite')
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if backend == 'sqlite':
            cur.execute('BEGIN IMMEDIATE')
            lock_clause = ''
        else:
            lock_clause = ' WITH (UPDLOCK, HOLDLOCK)'

        cur.execute(f"SELECT TrangThai, LichSuXuLy FROM DonHang{lock_clause} WHERE MaDonHang=?", (order_id,))
        row = cur.fetchone()
        if not row:
            raise OrderOperationError(f"Đơn hàng #{order_id} không tồn tại.")
        current_status = row[0]
        log = row[1] or ""
        if current_status != 'Chờ xác nhận':
            raise OrderOperationError(f"Đơn hàng #{order_id} đang ở trạng thái '{current_status}', chỉ có thể xác nhận khi 'Chờ xác nhận'.")

        # Lấy danh sách biến thể và số lượng cần mua
        cur.execute("""SELECT ct.MaBienThe, ct.SoLuong, sp.TenSanPham, bt.KichThuoc, bt.MauSac, bt.SoLuongTon
                       FROM ChiTietDonHang ct
                       JOIN BienTheSanPham bt ON bt.MaBienThe = ct.MaBienThe
                       JOIN SanPham sp ON sp.MaSanPham = bt.MaSanPham
                       WHERE ct.MaDonHang=?""", (order_id,))
        items = cur.fetchall()
        if not items:
            raise OrderOperationError(f"Đơn hàng #{order_id} không có chi tiết sản phẩm.")

        # 1. Kiểm tra tồn kho của từng biến thể
        for item in items:
            vid, qty, name, size, color, stock = item[0], item[1], item[2], item[3], item[4], item[5]
            if stock < qty:
                raise OrderOperationError(f"Sản phẩm '{name}' (Size {size}, {color}) không đủ hàng tồn kho (còn {stock}, cần {qty}).")

        # 2. Trừ tồn kho
        for item in items:
            vid, qty = item[0], item[1]
            cur.execute("UPDATE BienTheSanPham SET SoLuongTon = SoLuongTon - ? WHERE MaBienThe=?", (qty, vid))

        # 3. Chuyển trạng thái đơn sang 'Đã xác nhận', lưu người xác nhận và thời gian, không ghi đè lịch sử
        new_log = _append_log(log, f"Xác nhận đơn & trừ kho bởi user #{user_id}")
        cur.execute("""UPDATE DonHang
                       SET TrangThai = 'Đã xác nhận',
                           NguoiXacNhan = ?,
                           ThoiGianXacNhan = CURRENT_TIMESTAMP,
                           MaNguoiXuLy = ?,
                           ThoiGianXuLy = CURRENT_TIMESTAMP,
                           LichSuXuLy = ?
                       WHERE MaDonHang = ?""", (user_id, user_id, new_log, order_id))

        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def start_order_shipping(order_id, user_id):
    """Bắt đầu giao hàng: chuyển trạng thái giao hàng từ 'Chưa giao' sang 'Đang giao'.
    Chỉ thực hiện khi đơn hàng đã ở trạng thái 'Đã xác nhận'.
    Không tự động thay đổi trạng thái thanh toán.
    """
    backend = current_app.config.get('DB_BACKEND', 'sqlite')
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if backend == 'sqlite':
            cur.execute('BEGIN IMMEDIATE')
            lock_clause = ''
        else:
            lock_clause = ' WITH (UPDLOCK, HOLDLOCK)'

        cur.execute(f"SELECT TrangThai, COALESCE(TrangThaiGiaoHang, 'Chưa giao'), LichSuXuLy FROM DonHang{lock_clause} WHERE MaDonHang=?", (order_id,))
        row = cur.fetchone()
        if not row:
            raise OrderOperationError(f"Đơn hàng #{order_id} không tồn tại.")
        order_status, ship_status, log = row[0], row[1], row[2] or ""

        if order_status == 'Chờ xác nhận':
            raise OrderOperationError(f"Đơn hàng #{order_id} đang chờ xác nhận, phải xác nhận đơn trước khi giao hàng.")
        if order_status == 'Đã hủy':
            raise OrderOperationError(f"Đơn hàng #{order_id} đã bị hủy, không thể giao hàng.")
        if order_status == 'Hoàn thành':
            raise OrderOperationError(f"Đơn hàng #{order_id} đã hoàn thành, không thể thao tác giao hàng.")
        if order_status != 'Đã xác nhận':
            raise OrderOperationError(f"Đơn hàng #{order_id} ở trạng thái '{order_status}', không thể bắt đầu giao.")

        if ship_status == 'Đang giao':
            raise OrderOperationError(f"Đơn hàng #{order_id} đang trong quá trình giao hàng.")
        if ship_status == 'Đã giao':
            raise OrderOperationError(f"Đơn hàng #{order_id} đã giao thành công trước đó.")
        if ship_status != 'Chưa giao':
            raise OrderOperationError(f"Trạng thái giao hàng '{ship_status}' không hợp lệ để bắt đầu giao.")

        new_log = _append_log(log, f"Bắt đầu giao hàng (Đang giao) bởi user #{user_id}")
        cur.execute("""UPDATE DonHang
                       SET TrangThaiGiaoHang = 'Đang giao',
                           NguoiGiaoHang = ?,
                           ThoiGianBatDauGiao = CURRENT_TIMESTAMP,
                           MaNguoiXuLy = ?,
                           ThoiGianXuLy = CURRENT_TIMESTAMP,
                           LichSuXuLy = ?
                       WHERE MaDonHang = ?""", (user_id, user_id, new_log, order_id))

        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def mark_order_delivered(order_id, user_id):
    """Xác nhận giao hàng thành công: chuyển trạng thái từ 'Đang giao' sang 'Đã giao'.
    Chỉ thực hiện khi đơn đang ở 'Đã xác nhận' và 'Đang giao'.
    Bắt buộc không được nhảy cóc từ 'Chưa giao' sang 'Đã giao' (TC08).
    Không tự động ghi nhận thanh toán hoặc hoàn thành đơn.
    """
    backend = current_app.config.get('DB_BACKEND', 'sqlite')
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if backend == 'sqlite':
            cur.execute('BEGIN IMMEDIATE')
            lock_clause = ''
        else:
            lock_clause = ' WITH (UPDLOCK, HOLDLOCK)'

        cur.execute(f"SELECT TrangThai, COALESCE(TrangThaiGiaoHang, 'Chưa giao'), LichSuXuLy FROM DonHang{lock_clause} WHERE MaDonHang=?", (order_id,))
        row = cur.fetchone()
        if not row:
            raise OrderOperationError(f"Đơn hàng #{order_id} không tồn tại.")
        order_status, ship_status, log = row[0], row[1], row[2] or ""

        if order_status == 'Chờ xác nhận':
            raise OrderOperationError(f"Đơn hàng #{order_id} chưa được xác nhận, không thể ghi nhận đã giao.")
        if order_status == 'Đã hủy':
            raise OrderOperationError(f"Đơn hàng #{order_id} đã bị hủy, không thể giao hàng.")
        if order_status == 'Hoàn thành':
            raise OrderOperationError(f"Đơn hàng #{order_id} đã hoàn thành.")

        if ship_status == 'Chưa giao':
            raise OrderOperationError(f"Đơn hàng #{order_id} chưa xuất kho giao hàng, không thể chuyển trực tiếp sang 'Đã giao'.")
        if ship_status == 'Đã giao':
            raise OrderOperationError(f"Đơn hàng #{order_id} đã được xác nhận giao hàng trước đó.")
        if ship_status != 'Đang giao':
            raise OrderOperationError(f"Trạng thái giao hàng '{ship_status}' không hợp lệ để xác nhận đã giao.")

        new_log = _append_log(log, f"Xác nhận giao hàng thành công (Đã giao) bởi user #{user_id}")
        cur.execute("""UPDATE DonHang
                       SET TrangThaiGiaoHang = 'Đã giao',
                           NguoiXacNhanGiao = ?,
                           ThoiGianGiaoThanhCong = CURRENT_TIMESTAMP,
                           MaNguoiXuLy = ?,
                           ThoiGianXuLy = CURRENT_TIMESTAMP,
                           LichSuXuLy = ?
                       WHERE MaDonHang = ?""", (user_id, user_id, new_log, order_id))

        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def record_order_payment(order_id, user_id):
    """Ghi nhận đã thu tiền cho đơn hàng.
    Lưu người thực hiện (NguoiThuTien) và thời gian (ThoiGianThanhToan).
    Chỉ thực hiện khi đơn ở trạng thái 'Đã xác nhận'.
    Chặn thanh toán nếu đơn hàng ở trạng thái 'Chờ xác nhận' (Lỗi 1, TC01).
    Chặn thanh toán nếu đơn hàng đã bị hủy (TC06).
    Chặn thanh toán nếu đơn hàng đã hoàn thành (Lỗi 3, TC07).
    Chống ghi nhận thanh toán trùng (TC05).
    """
    backend = current_app.config.get('DB_BACKEND', 'sqlite')
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if backend == 'sqlite':
            cur.execute('BEGIN IMMEDIATE')
            lock_clause = ''
        else:
            lock_clause = ' WITH (UPDLOCK, HOLDLOCK)'

        cur.execute(f"""SELECT dh.TrangThai, tg.TrangThaiThanhToan, dh.LichSuXuLy,
                               tg.MaDonHang, tg.HoTen, tg.SoDienThoai, tg.PhuongThucThanhToan
                        FROM DonHang dh{lock_clause}
                        LEFT JOIN ThongTinGiaoDich tg{lock_clause} ON tg.MaDonHang = dh.MaDonHang
                        WHERE dh.MaDonHang = ?""", (order_id,))
        row = cur.fetchone()
        if not row:
            raise OrderOperationError(f"Không tìm thấy thông tin đơn hàng #{order_id}.")
        order_status, pay_status, log = row[0], row[1], row[2] or ""

        if order_status == 'Chờ xác nhận':
            raise OrderOperationError(f"Đơn hàng #{order_id} đang ở trạng thái 'Chờ xác nhận', cần xác nhận đơn trước khi ghi nhận thanh toán.")
        if order_status == 'Đã hủy':
            raise OrderOperationError(f"Đơn hàng #{order_id} đã bị hủy, không thể ghi nhận thanh toán.")
        if order_status == 'Hoàn thành':
            raise OrderOperationError(f"Đơn hàng #{order_id} đã hoàn thành, không thể ghi nhận thanh toán lại.")
        if order_status != 'Đã xác nhận':
            raise OrderOperationError(f"Đơn hàng #{order_id} ở trạng thái '{order_status}', không thể ghi nhận thanh toán.")

        if pay_status == 'Đã thanh toán':
            raise OrderOperationError(f"Đơn hàng #{order_id} đã được ghi nhận thanh toán trước đó, không thể ghi trùng.")

        # Không được biến một đơn thiếu dữ liệu thành giao dịch COD giả.
        if row[3] is None:
            raise OrderOperationError(
                f"Đơn hàng #{order_id} chưa có thông tin giao dịch. Cần đối soát dữ liệu đơn gốc trước khi xác nhận thu tiền."
            )
        recipient_name = str(row[4] or '').strip()
        recipient_phone = str(row[5] or '').strip()
        payment_method = str(row[6] or '').strip()
        if not recipient_name or not recipient_phone or (recipient_name == 'Khách hàng' and recipient_phone == '0000000000'):
            raise OrderOperationError("Thông tin người nhận chưa hợp lệ; không xác nhận thanh toán bằng dữ liệu giả.")
        if payment_method not in ('cod', 'bank_transfer'):
            raise OrderOperationError("Phương thức thanh toán chưa hợp lệ; cần đối soát thông tin giao dịch.")
        # Thao tác này là XÁC NHẬN ĐÃ THU TIỀN THỰC TẾ bởi người có quyền.
        # Chuyển khoản đã đối soát có thể xác nhận trước khi giao; COD chỉ xác nhận sau khi thực sự thu tiền.
        cur.execute("""UPDATE ThongTinGiaoDich
                       SET TrangThaiThanhToan = 'Đã thanh toán',
                           NguoiThuTien = ?, ThoiGianThanhToan = CURRENT_TIMESTAMP
                       WHERE MaDonHang = ? AND TrangThaiThanhToan <> 'Đã thanh toán'""",
                    (user_id, order_id))
        # Với một số driver SQL Server (SET NOCOUNT ON), rowcount có thể là -1.
        if cur.rowcount == 0:
            raise OrderOperationError("Không thể xác nhận thanh toán do trạng thái giao dịch đã thay đổi.")

        new_log = _append_log(log, f"Ghi nhận thu tiền (Đã thanh toán) bởi user #{user_id}")
        cur.execute("""UPDATE DonHang
                       SET MaNguoiXuLy = ?,
                           ThoiGianXuLy = CURRENT_TIMESTAMP,
                           LichSuXuLy = ?
                       WHERE MaDonHang = ?""", (user_id, new_log, order_id))

        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def complete_order_status(order_id, user_id):
    """Hoàn thành đơn hàng: chuyển trạng thái từ 'Đã xác nhận' sang 'Hoàn thành'.
    ĐIỀU KIỆN TIÊN QUYẾT BẮT BUỘC ĐỒNG THỜI:
    1. TrangThai == 'Đã xác nhận' (TC02, TC22).
    2. TrangThaiGiaoHang == 'Đã giao' (Lỗi 5, TC10).
    3. ThongTinGiaoDich tồn tại và có thông tin nhận hàng hợp lệ (HoTen và SoDienThoai không rỗng) (Lỗi 4, TC16).
       Không tạo thông tin giao dịch giả khi xác nhận thanh toán.
    4. TrangThaiThanhToan == 'Đã thanh toán' (Lỗi 2, TC03, TC09).
    Lưu NguoiHoanThanh, ThoiGianHoanThanh và không ghi đè lịch sử xử lý trước đó (Lỗi 7, TC18).
    """
    backend = current_app.config.get('DB_BACKEND', 'sqlite')
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if backend == 'sqlite':
            cur.execute('BEGIN IMMEDIATE')
            lock_clause = ''
        else:
            lock_clause = ' WITH (UPDLOCK, HOLDLOCK)'

        cur.execute(f"""SELECT dh.TrangThai, COALESCE(dh.TrangThaiGiaoHang, 'Chưa giao'),
                               tg.TrangThaiThanhToan, tg.HoTen, tg.SoDienThoai, dh.LichSuXuLy
                        FROM DonHang dh{lock_clause}
                        LEFT JOIN ThongTinGiaoDich tg{lock_clause} ON tg.MaDonHang = dh.MaDonHang
                        WHERE dh.MaDonHang = ?""", (order_id,))
        row = cur.fetchone()
        if not row:
            raise OrderOperationError(f"Đơn hàng #{order_id} không tồn tại.")
        current_status = row[0]
        ship_status = row[1]
        pay_status = row[2]
        recipient_name = (row[3] or "").strip()
        recipient_phone = (row[4] or "").strip()
        log = row[5] or ""

        # 1. Kiểm tra trạng thái đơn hàng
        if current_status == 'Chờ xác nhận':
            raise OrderOperationError(f"Đơn hàng #{order_id} đang ở trạng thái 'Chờ xác nhận', không thể hoàn thành trực tiếp.")
        if current_status == 'Đã hủy':
            raise OrderOperationError(f"Đơn hàng #{order_id} đã bị hủy, không thể hoàn thành.")
        if current_status == 'Hoàn thành':
            raise OrderOperationError(f"Đơn hàng #{order_id} đã ở trạng thái 'Hoàn thành' trước đó.")
        if current_status != 'Đã xác nhận':
            raise OrderOperationError(f"Đơn hàng #{order_id} đang ở trạng thái '{current_status}', chỉ có thể hoàn thành khi 'Đã xác nhận'.")

        # 2. Kiểm tra thông tin giao dịch & người nhận (Lỗi 4, TC16)
        if not recipient_name or not recipient_phone:
            raise OrderOperationError(f"Đơn hàng #{order_id} chưa có thông tin giao dịch/người nhận đầy đủ. Vui lòng bổ sung trước khi hoàn thành.")

        # 3. Kiểm tra trạng thái giao hàng (Lỗi 5, TC10)
        if ship_status != 'Đã giao':
            raise OrderOperationError(f"Đơn hàng #{order_id} chưa được giao thành công (trạng thái hiện tại: '{ship_status}'). Phải giao hàng thành công trước khi hoàn thành đơn.")

        # 4. Kiểm tra trạng thái thanh toán (Lỗi 2, TC03, TC09)
        if pay_status != 'Đã thanh toán':
            raise OrderOperationError(f"Đơn hàng #{order_id} chưa được thanh toán (trạng thái thanh toán: '{pay_status or 'Chưa thanh toán'}'). Phải thanh toán trước khi hoàn thành đơn.")

        # Đạt mọi điều kiện: Cập nhật Hoàn thành
        new_log = _append_log(log, f"Đánh dấu Hoàn thành bởi user #{user_id}")
        cur.execute("""UPDATE DonHang
                       SET TrangThai = 'Hoàn thành',
                           NguoiHoanThanh = ?,
                           ThoiGianHoanThanh = CURRENT_TIMESTAMP,
                           MaNguoiXuLy = ?,
                           ThoiGianXuLy = CURRENT_TIMESTAMP,
                           LichSuXuLy = ?
                       WHERE MaDonHang = ?""", (user_id, user_id, new_log, order_id))

        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def cancel_order_stock(order_id, user_id, reason=None):
    """Chỉ hủy trước khi giao; nếu đã xác nhận thì hoàn kho đúng một lần.
    Đơn đang giao bị chặn. Phiếu hoàn kho lịch sử vẫn xử lý qua confirm_return_stock.
    """
    backend = current_app.config.get('DB_BACKEND', 'sqlite')
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if backend == 'sqlite':
            cur.execute('BEGIN IMMEDIATE')
            lock_clause = ''
        else:
            lock_clause = ' WITH (UPDLOCK, HOLDLOCK)'
        cur.execute(f'''SELECT dh.TrangThai, tg.TrangThaiThanhToan, tg.GhiChu,
                               COALESCE(dh.TrangThaiGiaoHang, 'Chưa giao'), dh.LichSuXuLy
                        FROM DonHang dh{lock_clause}
                        LEFT JOIN ThongTinGiaoDich tg{lock_clause} ON tg.MaDonHang=dh.MaDonHang
                        WHERE dh.MaDonHang=?''', (order_id,))
        row = cur.fetchone()
        if not row:
            raise OrderOperationError(f"Đơn hàng #{order_id} không tồn tại.")
        status, payment, note, shipping, log = row[0], row[1], row[2] or '', row[3], row[4] or ''
        if status in ('Hoàn thành', 'Đã hủy'):
            raise OrderOperationError(f"Đơn hàng #{order_id} đã bị hủy, không thể hủy.") if status == 'Đã hủy' else OrderOperationError(f"Đơn hàng #{order_id} đã hoàn thành, không thể hủy.")
        if shipping == 'Đang giao':
            raise OrderOperationError('Không thể hủy đơn đang giao. Chỉ trả hàng sau khi đơn Hoàn thành.')
        if shipping == 'Đã giao':
            raise OrderOperationError('Đơn đã giao thành công, không thể hủy theo quy trình thông thường.')
        # Đã có nghiệp vụ hoàn tiền tách biệt: cho phép hủy cả đơn đã thu tiền
        # nhưng chưa giao. Thao tác hủy KHÔNG đánh dấu tiền đã hoàn.
        if shipping == 'Đang giao' and status != 'Đã xác nhận':
            raise OrderOperationError('Trạng thái đơn/giao hàng không nhất quán.')

        if status == 'Đã xác nhận':
            cur.execute('SELECT MaBienThe, SoLuong FROM ChiTietDonHang WHERE MaDonHang=?', (order_id,))
            items = cur.fetchall()
            if not items:
                raise OrderOperationError('Đơn thiếu chi tiết sản phẩm, không thể xử lý hoàn kho.')
            for vid, qty in items:
                if shipping == 'Đang giao':
                    # Lập phiếu chờ hoàn cho từng biến thể, tuyệt đối không cộng kho ở bước này.
                    cur.execute('''INSERT INTO HoanKhoChiTiet
                                   (MaDonHang, MaBienThe, SoLuongCanHoan)
                                   VALUES (?,?,?)''', (order_id, vid, qty))
                else:
                    cur.execute('UPDATE BienTheSanPham SET SoLuongTon=SoLuongTon+? WHERE MaBienThe=?', (qty, vid))
        pending = (shipping == 'Đang giao')
        action = 'Hủy đơn (CHỜ HOÀN KHO, chưa cộng tồn kho)' if pending else 'Hủy đơn (đã xử lý kho nếu có trừ kho)'
        if reason:
            action += f' | Lý do: {reason.strip()[:200]}'
        refund_state = 'Chờ xử lý hoàn tiền' if payment == 'Đã thanh toán' else 'Không cần hoàn tiền'
        new_log = _append_log(log, f'{action} bởi user #{user_id}')
        cur.execute('''UPDATE DonHang
                       SET TrangThai='Đã hủy', TrangThaiHoanTien=?, NguoiHuy=?,
                           ThoiGianHuy=CURRENT_TIMESTAMP, MaNguoiXuLy=?,
                           ThoiGianXuLy=CURRENT_TIMESTAMP, LichSuXuLy=?
                       WHERE MaDonHang=?''', (refund_state, user_id, user_id, new_log, order_id))
        if reason:
            appended = (note + ' [Lý do hủy: ' + reason.strip()[:200] + ']').strip()
            cur.execute('SELECT 1 FROM ThongTinGiaoDich WHERE MaDonHang=?', (order_id,))
            if cur.fetchone():
                cur.execute('UPDATE ThongTinGiaoDich SET GhiChu=? WHERE MaDonHang=?', (appended, order_id))
            else:
                cur.execute('''INSERT INTO ThongTinGiaoDich
                               (MaDonHang, HoTen, SoDienThoai, HinhThucNhanHang,
                                PhuongThucThanhToan, TrangThaiThanhToan, GhiChu)
                               VALUES (?, 'Khách hàng','0000000000','delivery','cod','Chưa thanh toán',?)''',
                            (order_id, appended))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_order_return_lines(order_id):
    '''Mỗi biến thể một dòng số lượng cần xử lý, đã hoàn bán được, hàng hỏng.'''
    return query_all('''SELECT hk.MaBienThe, hk.SoLuongCanHoan, hk.SoLuongDaHoan,
                        hk.SoLuongHong, (hk.SoLuongCanHoan-hk.SoLuongDaHoan-hk.SoLuongHong) AS ConCho,
                        COALESCE(ct.TenSanPham, sp.TenSanPham) AS TenSanPham,
                        COALESCE(ct.KichThuoc, bt.KichThuoc) AS KichThuoc,
                        COALESCE(ct.MauSac, bt.MauSac) AS MauSac
                 FROM HoanKhoChiTiet hk
                 JOIN BienTheSanPham bt ON bt.MaBienThe=hk.MaBienThe
                 JOIN SanPham sp ON sp.MaSanPham=bt.MaSanPham
                 LEFT JOIN ChiTietDonHang ct ON ct.MaDonHang=hk.MaDonHang AND ct.MaBienThe=hk.MaBienThe
                 WHERE hk.MaDonHang=? ORDER BY hk.MaBienThe''', (order_id,))


def confirm_return_stock(order_id, user_id, received, damaged=None):
    '''Nhập kho thực nhận theo từng biến thể, có hỗ trợ hàng hỏng/nhập nhiều lần.

    received/damaged: dict[MaBienThe] -> số lượng; chỉ các lượng được xác nhận mới ghi.
    BEGIN IMMEDIATE / UPDLOCK để hai nhân viên không thể nhập trùng trong race.
    '''
    damaged = damaged or {}
    backend = current_app.config.get('DB_BACKEND', 'sqlite')
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if backend == 'sqlite':
            cur.execute('BEGIN IMMEDIATE')
            lock_clause = ''
        else:
            lock_clause = ' WITH (UPDLOCK, HOLDLOCK)'
        cur.execute(f'SELECT TrangThai, LichSuXuLy FROM DonHang{lock_clause} WHERE MaDonHang=?', (order_id,))
        row = cur.fetchone()
        if not row or row[0] != 'Đã hủy':
            raise OrderOperationError('Chỉ đơn đã hủy và chờ hoàn kho mới được nhập kho.')
        cur.execute(f'''SELECT MaBienThe, SoLuongCanHoan, SoLuongDaHoan, SoLuongHong
                        FROM HoanKhoChiTiet{lock_clause} WHERE MaDonHang=?''', (order_id,))
        lines = cur.fetchall()
        if not lines:
            raise OrderOperationError('Đơn không có hàng đang chờ hoàn kho.')
        valid = {int(r[0]): r for r in lines}
        for source in (received, damaged):
            if any(int(k) not in valid for k in source):
                raise OrderOperationError('Biến thể không thuộc phiếu hoàn kho.')
        events = []
        for variant, line in valid.items():
            try:
                good = int(received.get(variant, received.get(str(variant), 0)))
                bad = int(damaged.get(variant, damaged.get(str(variant), 0)))
            except (ValueError, TypeError):
                raise OrderOperationError('Số lượng hoàn kho phải là số nguyên.')
            remaining = int(line[1]) - int(line[2]) - int(line[3])
            if min(good, bad) < 0 or good + bad > remaining:
                raise OrderOperationError('Số lượng hoàn kho vượt số lượng chờ xử lý hoặc nhỏ hơn 0.')
            if good or bad:
                events.append((variant, good, bad))
        if not events:
            raise OrderOperationError('Hãy nhập ít nhất một số lượng hàng đã nhận hoặc hàng hỏng.')
        for variant, good, bad in events:
            cur.execute('''UPDATE HoanKhoChiTiet
                           SET SoLuongDaHoan=SoLuongDaHoan+?, SoLuongHong=SoLuongHong+?
                           WHERE MaDonHang=? AND MaBienThe=? AND
                             SoLuongCanHoan-SoLuongDaHoan-SoLuongHong>=?''',
                        (good, bad, order_id, variant, good+bad))
            if cur.rowcount != 1:
                raise OrderOperationError('Phiếu hoàn kho đã được nhân viên khác cập nhật.')
            if good:
                cur.execute('UPDATE BienTheSanPham SET SoLuongTon=SoLuongTon+? WHERE MaBienThe=?', (good, variant))
            cur.execute('''INSERT INTO LichSuHoanKho
                           (MaDonHang, MaBienThe, SoLuongNhapKho, SoLuongKhongBanDuoc, NguoiThucHien)
                           VALUES (?,?,?,?,?)''', (order_id, variant, good, bad, user_id))
        new_log = _append_log(row[1] or '', f'Hoàn kho bởi user #{user_id}: ' +
                              ', '.join(f'biến thể #{v}: nhập {g}, không bán được {b}' for v,g,b in events))
        cur.execute('''UPDATE DonHang SET LichSuXuLy=?, MaNguoiXuLy=?, ThoiGianXuLy=CURRENT_TIMESTAMP
                       WHERE MaDonHang=?''', (new_log, user_id, order_id))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def ensure_order_transaction_info(order_id, user_id=None, full_name=None, phone=None, address=None, fulfillment='delivery', payment_method='cod'):
    """Bổ sung hoặc hoàn thiện thông tin giao dịch demo cho đơn hàng nếu còn thiếu.
    Cho phép dùng thông tin giả lập ('Khách hàng', '0000000000').
    TUYỆT ĐỐI KHÔNG tự động chuyển trạng thái thanh toán sang 'Đã thanh toán'.
    """
    backend = current_app.config.get('DB_BACKEND', 'sqlite')
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if backend == 'sqlite':
            cur.execute('BEGIN IMMEDIATE')
            lock_clause = ''
        else:
            lock_clause = ' WITH (UPDLOCK, HOLDLOCK)'

        cur.execute(f"SELECT MaDonHang, HoTen, SoDienThoai FROM ThongTinGiaoDich{lock_clause} WHERE MaDonHang=?", (order_id,))
        row = cur.fetchone()

        fn = (full_name or "").strip() or "Khách hàng"
        ph = (phone or "").strip() or "0000000000"
        addr = (address or "").strip() or "Địa chỉ nhận hàng (Demo)"
        ful = fulfillment if fulfillment in ('delivery', 'pickup') else 'delivery'
        pm = payment_method if payment_method in ('cod', 'bank_transfer') else 'cod'

        if not row:
            cur.execute("""INSERT INTO ThongTinGiaoDich
                           (MaDonHang, HoTen, SoDienThoai, HinhThucNhanHang, DiaChiGiaoHang, PhuongThucThanhToan, TrangThaiThanhToan)
                           VALUES (?, ?, ?, ?, ?, ?, 'Chưa thanh toán')""",
                        (order_id, fn, ph, ful, addr, pm))
        else:
            cur.execute("""UPDATE ThongTinGiaoDich
                           SET HoTen = CASE WHEN COALESCE(TRIM(HoTen), '') = '' THEN ? ELSE HoTen END,
                               SoDienThoai = CASE WHEN COALESCE(TRIM(SoDienThoai), '') = '' THEN ? ELSE SoDienThoai END
                           WHERE MaDonHang = ?""", (fn, ph, order_id))

        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
