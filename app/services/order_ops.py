"""Nghiệp vụ xử lý trạng thái đơn hàng, hoàn/trừ tồn kho và thanh toán.
Áp dụng transaction chặt chẽ, hỗ trợ cả SQLite và SQL Server.
"""
from decimal import Decimal
from flask import current_app
from ..db import get_db_connection, query_one, query_all


class OrderOperationError(ValueError):
    pass


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

        cur.execute(f"SELECT TrangThai FROM DonHang{lock_clause} WHERE MaDonHang=?", (order_id,))
        row = cur.fetchone()
        if not row:
            raise OrderOperationError(f"Đơn hàng #{order_id} không tồn tại.")
        current_status = row[0]
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

        # 3. Chuyển trạng thái đơn sang 'Đã xác nhận', lưu người xử lý và thời gian
        cur.execute("""UPDATE DonHang
                       SET TrangThai = 'Đã xác nhận', MaNguoiXuLy = ?, ThoiGianXuLy = CURRENT_TIMESTAMP
                       WHERE MaDonHang = ?""", (user_id, order_id))

        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def complete_order_status(order_id, user_id):
    """Hoàn thành đơn hàng: chuyển trạng thái từ 'Đã xác nhận' sang 'Hoàn thành'."""
    backend = current_app.config.get('DB_BACKEND', 'sqlite')
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if backend == 'sqlite':
            cur.execute('BEGIN IMMEDIATE')
            lock_clause = ''
        else:
            lock_clause = ' WITH (UPDLOCK, HOLDLOCK)'

        cur.execute(f"SELECT TrangThai FROM DonHang{lock_clause} WHERE MaDonHang=?", (order_id,))
        row = cur.fetchone()
        if not row:
            raise OrderOperationError(f"Đơn hàng #{order_id} không tồn tại.")
        current_status = row[0]
        if current_status != 'Đã xác nhận':
            raise OrderOperationError(f"Đơn hàng #{order_id} đang ở trạng thái '{current_status}', chỉ có thể hoàn thành khi 'Đã xác nhận'.")

        cur.execute("""UPDATE DonHang
                       SET TrangThai = 'Hoàn thành', MaNguoiXuLy = ?, ThoiGianXuLy = CURRENT_TIMESTAMP
                       WHERE MaDonHang = ?""", (user_id, order_id))

        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def cancel_order_stock(order_id, user_id, reason=None):
    """Hủy đơn hàng:
    - Nếu đơn 'Chờ xác nhận': chưa trừ kho nên không cần hoàn kho.
    - Nếu đơn 'Đã xác nhận': đã trừ kho nên BẮT BUỘC HOÀN TỒN KHO trong transaction.
    - Nếu đơn 'Hoàn thành' hoặc 'Đã hủy': không thể hủy.
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

        cur.execute(f"SELECT TrangThai FROM DonHang{lock_clause} WHERE MaDonHang=?", (order_id,))
        row = cur.fetchone()
        if not row:
            raise OrderOperationError(f"Đơn hàng #{order_id} không tồn tại.")
        current_status = row[0]
        if current_status == 'Hoàn thành':
            raise OrderOperationError(f"Đơn hàng #{order_id} đã hoàn thành, không thể hủy.")
        if current_status == 'Đã hủy':
            raise OrderOperationError(f"Đơn hàng #{order_id} đã bị hủy trước đó.")

        # Nếu đã xác nhận -> hoàn tồn kho
        if current_status == 'Đã xác nhận':
            cur.execute("SELECT MaBienThe, SoLuong FROM ChiTietDonHang WHERE MaDonHang=?", (order_id,))
            items = cur.fetchall()
            for vid, qty in items:
                cur.execute("UPDATE BienTheSanPham SET SoLuongTon = SoLuongTon + ? WHERE MaBienThe=?", (qty, vid))

        # Cập nhật trạng thái đơn sang 'Đã hủy'
        cur.execute("""UPDATE DonHang
                       SET TrangThai = 'Đã hủy', MaNguoiXuLy = ?, ThoiGianXuLy = CURRENT_TIMESTAMP
                       WHERE MaDonHang = ?""", (user_id, order_id))

        # Nếu có ghi chú lý do hủy -> lưu vào ThongTinGiaoDich
        if reason:
            note_text = f" [Lý do hủy: {reason.strip()}]"
            cur.execute("""UPDATE ThongTinGiaoDich
                           SET GhiChu = COALESCE(GhiChu, '') || ?
                           WHERE MaDonHang = ?""", (note_text, order_id))

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
    Chống ghi nhận thanh toán trùng.
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

        cur.execute(f"SELECT TrangThaiThanhToan FROM ThongTinGiaoDich{lock_clause} WHERE MaDonHang=?", (order_id,))
        row = cur.fetchone()
        if not row:
            raise OrderOperationError(f"Không tìm thấy thông tin giao dịch của đơn hàng #{order_id}.")
        pay_status = row[0]
        if pay_status == 'Đã thanh toán':
            raise OrderOperationError(f"Đơn hàng #{order_id} đã được ghi nhận thanh toán trước đó, không thể ghi trùng.")

        cur.execute("""UPDATE ThongTinGiaoDich
                       SET TrangThaiThanhToan = 'Đã thanh toán',
                           NguoiThuTien = ?,
                           ThoiGianThanhToan = CURRENT_TIMESTAMP
                       WHERE MaDonHang = ?""", (user_id, order_id))

        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
