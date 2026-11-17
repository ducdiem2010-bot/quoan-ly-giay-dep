"""W12: Nghiệp vụ quản trị (Admin) và nhân viên bán hàng (Seller).
Hỗ trợ cả SQLite và SQL Server, chuẩn hóa tham số hóa và quyền hạn.
"""
from functools import wraps
from math import ceil
import re
from urllib.parse import urlencode
from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for, current_app
from werkzeug.security import generate_password_hash
from ..db import get_db_connection, query_all, query_one
from ..services.order_ops import (
    confirm_order_stock, complete_order_status,
    cancel_order_stock, record_order_payment, OrderOperationError
)

w12 = Blueprint('w12', __name__)


def roles_required(*roles):
    def decorate(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            if not session.get('user_id'):
                return redirect(url_for('login', next=request.path))
            user_role = session.get('role')
            if user_role not in roles:
                abort(403)
            return func(*args, **kwargs)
        return wrapped
    return decorate


admin = roles_required('Admin')
seller = roles_required('Seller')
staff_or_admin = roles_required('Admin', 'Seller')


def _q():
    return request.args.get('q', '', type=str).strip()[:80]


def _filter_and_paginate_orders(is_admin_view=True):
    filters = []
    args = []
    q = _q()
    status = request.args.get('status', '', type=str).strip()[:40]
    pay_status = request.args.get('pay_status', '', type=str).strip()[:40]
    sort = request.args.get('sort', 'newest', type=str).strip()

    if q:
        if q.isdigit():
            filters.append("""(dh.MaDonHang=? OR nd.HoVaTen LIKE ? OR nd.Email LIKE ?
                              OR nd.SoDienThoai LIKE ? OR tg.HoTen LIKE ? OR tg.SoDienThoai LIKE ?)""")
            kw = f"%{q}%"
            args.extend([int(q), kw, kw, kw, kw, kw])
        else:
            filters.append("(nd.HoVaTen LIKE ? OR nd.Email LIKE ? OR tg.HoTen LIKE ? OR tg.SoDienThoai LIKE ?)")
            kw = f"%{q}%"
            args.extend([kw, kw, kw, kw])

    allowed_statuses = ('Chờ xác nhận', 'Đã xác nhận', 'Hoàn thành', 'Đã hủy')
    if status:
        if status not in allowed_statuses:
            abort(400, description='Trạng thái lọc không hợp lệ.')
        filters.append('dh.TrangThai=?')
        args.append(status)

    if pay_status:
        if pay_status not in ('Chưa thanh toán', 'Đã thanh toán'):
            abort(400, description='Trạng thái thanh toán không hợp lệ.')
        filters.append('tg.TrangThaiThanhToan=?')
        args.append(pay_status)

    where_clause = ' WHERE ' + ' AND '.join(filters) if filters else ''
    order_direction = 'ASC' if sort == 'oldest' else 'DESC'

    count_sql = f"""SELECT COUNT(*) AS total
                    FROM DonHang dh
                    LEFT JOIN NguoiDung nd ON nd.MaNguoiDung = dh.MaNguoiDung
                    LEFT JOIN ThongTinGiaoDich tg ON tg.MaDonHang = dh.MaDonHang
                    {where_clause}"""
    count_row = query_one(count_sql, tuple(args))
    total_items = count_row['total'] if count_row else 0

    per_page = 15
    page_count = max(1, ceil(total_items / per_page))
    try:
        page = max(1, min(page_count, int(request.args.get('page', 1))))
    except (ValueError, TypeError):
        page = 1
    offset = (page - 1) * per_page

    select_sql = f"""SELECT dh.MaDonHang, dh.MaNguoiDung, dh.NgayDat, dh.TrangThai, dh.TongTien,
                            dh.MaNguoiXuLy, dh.ThoiGianXuLy,
                            nd.HoVaTen AS KhachHang, nd.Email AS EmailKhach, nd.SoDienThoai AS SdtKhach,
                            tg.HoTen AS TenNguoiNhan, tg.SoDienThoai AS SdtNguoiNhan,
                            tg.DiaChiGiaoHang, tg.PhuongThucThanhToan, tg.TrangThaiThanhToan
                     FROM DonHang dh
                     LEFT JOIN NguoiDung nd ON nd.MaNguoiDung = dh.MaNguoiDung
                     LEFT JOIN ThongTinGiaoDich tg ON tg.MaDonHang = dh.MaDonHang
                     {where_clause}
                     ORDER BY dh.MaDonHang {order_direction}"""

    all_rows = query_all(select_sql, tuple(args))
    orders_page = all_rows[offset:offset + per_page]

    # Query string helper for pagination
    query_params = request.args.to_dict()
    def page_url(p):
        p_dict = dict(query_params)
        p_dict['page'] = p
        endpoint = 'w12.admin_orders' if is_admin_view else 'w12.staff_orders'
        return url_for(endpoint) + '?' + urlencode(p_dict)

    pagination = {
        'total': total_items,
        'page': page,
        'page_count': page_count,
        'prev_url': page_url(page - 1) if page > 1 else None,
        'next_url': page_url(page + 1) if page < page_count else None,
    }

    return orders_page, q, status, pay_status, sort, pagination


# ==============================================================================
# ADMIN ĐƠN HÀNG & PHIẾU XUẤT
# ==============================================================================

@w12.get('/admin/orders')
@admin
def admin_orders():
    orders, q, status, pay_status, sort, pagination = _filter_and_paginate_orders(is_admin_view=True)
    return render_template('w12/admin_orders.html', orders=orders, q=q, status=status,
                           pay_status=pay_status, sort=sort, pagination=pagination)


@w12.get('/admin/orders/<int:order_id>')
@admin
def admin_order_detail(order_id):
    order = query_one('''SELECT dh.MaDonHang, dh.MaNguoiDung, dh.NgayDat, dh.TrangThai, dh.TongTien,
                                dh.MaNguoiXuLy, dh.ThoiGianXuLy,
                                nd.HoVaTen AS KhachHang, nd.Email AS EmailKhach, nd.SoDienThoai AS SdtKhach,
                                tg.HoTen AS TenNguoiNhan, tg.SoDienThoai AS SdtNguoiNhan, tg.Email AS EmailNguoiNhan,
                                tg.HinhThucNhanHang, tg.DiaChiGiaoHang, tg.PhuongThucThanhToan,
                                tg.TrangThaiThanhToan, tg.PhiVanChuyen, tg.GhiChu, tg.NgayTao AS NgayTaoGiaoDich,
                                tg.NguoiThuTien, tg.ThoiGianThanhToan,
                                nx.HoVaTen AS TenNguoiXuLy, nt.HoVaTen AS TenNguoiThuTien
                         FROM DonHang dh
                         LEFT JOIN NguoiDung nd ON nd.MaNguoiDung = dh.MaNguoiDung
                         LEFT JOIN ThongTinGiaoDich tg ON tg.MaDonHang = dh.MaDonHang
                         LEFT JOIN NguoiDung nx ON nx.MaNguoiDung = dh.MaNguoiXuLy
                         LEFT JOIN NguoiDung nt ON nt.MaNguoiDung = tg.NguoiThuTien
                         WHERE dh.MaDonHang=?''', (order_id,))
    if not order:
        abort(404)
    items = query_all('''SELECT sp.MaSanPham, sp.TenSanPham, bt.MauSac, bt.KichThuoc,
                                ct.SoLuong, ct.DonGia, (ct.SoLuong * ct.DonGia) AS ThanhTien
                         FROM ChiTietDonHang ct
                         JOIN BienTheSanPham bt ON bt.MaBienThe = ct.MaBienThe
                         JOIN SanPham sp ON sp.MaSanPham = bt.MaSanPham
                         WHERE ct.MaDonHang=?
                         ORDER BY ct.MaChiTietDon''', (order_id,))
    return render_template('w12/admin_order_detail.html', order=order, items=items)


@w12.get('/admin/invoices')
@admin
def invoices():
    orders, q, status, pay_status, sort, pagination = _filter_and_paginate_orders(is_admin_view=True)
    return render_template('w12/admin_invoices.html', orders=orders, q=q, status=status, pagination=pagination)


# ==============================================================================
# KHU VỰC NHÂN VIÊN (SELLER)
# ==============================================================================

@w12.get('/staff')
@seller
def staff_home():
    products = query_all('''SELECT sp.MaSanPham, sp.TenSanPham, sp.HienThi, sp.GiaBan,
                                   dm.TenDanhMuc,
                                   COALESCE(SUM(bt.SoLuongTon), 0) AS TongTon
                            FROM SanPham sp
                            JOIN DanhMuc dm ON dm.MaDanhMuc = sp.MaDanhMuc
                            LEFT JOIN BienTheSanPham bt ON bt.MaSanPham = sp.MaSanPham
                            GROUP BY sp.MaSanPham, sp.TenSanPham, sp.HienThi, sp.GiaBan, dm.TenDanhMuc
                            ORDER BY sp.MaSanPham DESC''')
    stats = query_one('''SELECT COUNT(*) AS total_orders,
                                COALESCE(SUM(CASE WHEN TrangThai='Chờ xác nhận' THEN 1 ELSE 0 END), 0) AS pending_count,
                                COALESCE(SUM(CASE WHEN TrangThai='Đã xác nhận' THEN 1 ELSE 0 END), 0) AS confirmed_count
                         FROM DonHang''') or {}
    return render_template('w12/staff.html', products=products, stats=stats)


@w12.get('/staff/orders')
@seller
def staff_orders():
    orders, q, status, pay_status, sort, pagination = _filter_and_paginate_orders(is_admin_view=False)
    return render_template('w12/staff_orders.html', orders=orders, q=q, status=status,
                           pay_status=pay_status, sort=sort, pagination=pagination)


@w12.get('/staff/orders/<int:order_id>')
@seller
def staff_order_detail(order_id):
    order = query_one('''SELECT dh.MaDonHang, dh.MaNguoiDung, dh.NgayDat, dh.TrangThai, dh.TongTien,
                                dh.MaNguoiXuLy, dh.ThoiGianXuLy,
                                nd.HoVaTen AS KhachHang, nd.Email AS EmailKhach, nd.SoDienThoai AS SdtKhach,
                                tg.HoTen AS TenNguoiNhan, tg.SoDienThoai AS SdtNguoiNhan, tg.Email AS EmailNguoiNhan,
                                tg.HinhThucNhanHang, tg.DiaChiGiaoHang, tg.PhuongThucThanhToan,
                                tg.TrangThaiThanhToan, tg.PhiVanChuyen, tg.GhiChu, tg.NgayTao AS NgayTaoGiaoDich,
                                tg.NguoiThuTien, tg.ThoiGianThanhToan,
                                nx.HoVaTen AS TenNguoiXuLy, nt.HoVaTen AS TenNguoiThuTien
                         FROM DonHang dh
                         LEFT JOIN NguoiDung nd ON nd.MaNguoiDung = dh.MaNguoiDung
                         LEFT JOIN ThongTinGiaoDich tg ON tg.MaDonHang = dh.MaDonHang
                         LEFT JOIN NguoiDung nx ON nx.MaNguoiDung = dh.MaNguoiXuLy
                         LEFT JOIN NguoiDung nt ON nt.MaNguoiDung = tg.NguoiThuTien
                         WHERE dh.MaDonHang=?''', (order_id,))
    if not order:
        abort(404)
    items = query_all('''SELECT sp.MaSanPham, sp.TenSanPham, bt.MauSac, bt.KichThuoc,
                                ct.SoLuong, ct.DonGia, (ct.SoLuong * ct.DonGia) AS ThanhTien
                         FROM ChiTietDonHang ct
                         JOIN BienTheSanPham bt ON bt.MaBienThe = ct.MaBienThe
                         JOIN SanPham sp ON sp.MaSanPham = bt.MaSanPham
                         WHERE ct.MaDonHang=?
                         ORDER BY ct.MaChiTietDon''', (order_id,))
    return render_template('w12/admin_order_detail.html', order=order, items=items, is_staff=True)


# ==============================================================================
# CÁC THAO TÁC XỬ LÝ ĐƠN HÀNG (DÙNG CHUNG CHO NHÂN VIÊN VÀ ADMIN)
# ==============================================================================

@w12.post('/orders/<int:order_id>/confirm')
@staff_or_admin
def order_action_confirm(order_id):
    redirect_target = request.referrer or (url_for('w12.admin_order_detail', order_id=order_id)
                                           if session.get('role') == 'Admin'
                                           else url_for('w12.staff_order_detail', order_id=order_id))
    try:
        confirm_order_stock(order_id, session['user_id'])
        flash(f"Đã xác nhận đơn hàng #{order_id} và trừ tồn kho thành công.", "success")
    except OrderOperationError as e:
        flash(str(e), "warning")
    except Exception:
        current_app.logger.exception("Lỗi xác nhận đơn")
        flash("Không thể xác nhận đơn hàng. Đã rollback dữ liệu an toàn.", "warning")
    return redirect(redirect_target)


@w12.post('/orders/<int:order_id>/complete')
@staff_or_admin
def order_action_complete(order_id):
    redirect_target = request.referrer or (url_for('w12.admin_order_detail', order_id=order_id)
                                           if session.get('role') == 'Admin'
                                           else url_for('w12.staff_order_detail', order_id=order_id))
    try:
        complete_order_status(order_id, session['user_id'])
        flash(f"Đơn hàng #{order_id} đã được chuyển sang trạng thái Hoàn thành.", "success")
    except OrderOperationError as e:
        flash(str(e), "warning")
    except Exception:
        current_app.logger.exception("Lỗi hoàn thành đơn")
        flash("Không thể cập nhật trạng thái đơn hàng.", "warning")
    return redirect(redirect_target)


@w12.post('/orders/<int:order_id>/cancel')
@staff_or_admin
def order_action_cancel(order_id):
    redirect_target = request.referrer or (url_for('w12.admin_order_detail', order_id=order_id)
                                           if session.get('role') == 'Admin'
                                           else url_for('w12.staff_order_detail', order_id=order_id))
    reason = request.form.get('reason', '').strip()[:200]
    try:
        cancel_order_stock(order_id, session['user_id'], reason=reason)
        flash(f"Đã hủy đơn hàng #{order_id} thành công (đã hoàn kho nếu đơn đã từng xác nhận).", "success")
    except OrderOperationError as e:
        flash(str(e), "warning")
    except Exception:
        current_app.logger.exception("Lỗi hủy đơn")
        flash("Không thể hủy đơn hàng.", "warning")
    return redirect(redirect_target)


@w12.post('/orders/<int:order_id>/pay')
@staff_or_admin
def order_action_pay(order_id):
    redirect_target = request.referrer or (url_for('w12.admin_order_detail', order_id=order_id)
                                           if session.get('role') == 'Admin'
                                           else url_for('w12.staff_order_detail', order_id=order_id))
    try:
        record_order_payment(order_id, session['user_id'])
        flash(f"Đã ghi nhận thanh toán cho đơn hàng #{order_id}.", "success")
    except OrderOperationError as e:
        flash(str(e), "warning")
    except Exception:
        current_app.logger.exception("Lỗi ghi nhận thanh toán")
        flash("Không thể ghi nhận thanh toán.", "warning")
    return redirect(redirect_target)


# ==============================================================================
# QUẢN LÝ TÀI KHOẢN: NHÂN VIÊN & KHÁCH HÀNG (ADMIN)
# ==============================================================================

def _users_list(role_id, kind='staff'):
    q = _q()
    status_filter = request.args.get('status', '').strip()
    filters = ['MaVaiTro=?']
    args = [role_id]

    if q:
        if q.isdigit():
            filters.append('(MaNguoiDung=? OR HoVaTen LIKE ? OR Email LIKE ? OR SoDienThoai LIKE ?)')
            kw = f"%{q}%"
            args.extend([int(q), kw, kw, kw])
        else:
            filters.append('(HoVaTen LIKE ? OR Email LIKE ? OR SoDienThoai LIKE ?)')
            kw = f"%{q}%"
            args.extend([kw, kw, kw])

    if status_filter == 'active':
        filters.append('TrangThai=1')
    elif status_filter == 'locked':
        filters.append('TrangThai=0')

    where_sql = ' WHERE ' + ' AND '.join(filters)

    count_row = query_one(f"SELECT COUNT(*) AS total FROM NguoiDung {where_sql}", tuple(args))
    total_items = count_row['total'] if count_row else 0

    per_page = 10
    page_count = max(1, ceil(total_items / per_page))
    try:
        page = max(1, min(page_count, int(request.args.get('page', 1))))
    except (ValueError, TypeError):
        page = 1
    offset = (page - 1) * per_page

    select_sql = f"""SELECT MaNguoiDung, HoVaTen, Email, SoDienThoai, TrangThai, NgayTao,
                            NguoiKhoa, ThoiGianKhoa, GhiChuKhoa
                     FROM NguoiDung {where_sql}
                     ORDER BY MaNguoiDung DESC"""
    rows = query_all(select_sql, tuple(args))
    current_rows = rows[offset:offset + per_page]

    q_dict = request.args.to_dict()
    def to_page(p):
        d = dict(q_dict)
        d['page'] = p
        endpoint = 'w12.staff_list' if kind == 'staff' else 'w12.customers'
        return url_for(endpoint) + '?' + urlencode(d)

    pagination = {
        'total': total_items,
        'page': page,
        'page_count': page_count,
        'prev_url': to_page(page - 1) if page > 1 else None,
        'next_url': to_page(page + 1) if page < page_count else None,
    }

    return current_rows, q, status_filter, pagination


@w12.get('/admin/staff')
@admin
def staff_list():
    users, q, status_filter, pagination = _users_list(2, kind='staff')
    return render_template('w12/admin_users.html', users=users, q=q, status=status_filter,
                           pagination=pagination, kind='staff')


@w12.route('/admin/staff/new', methods=['GET', 'POST'])
@admin
def staff_create():
    values = {'name': '', 'email': '', 'phone': ''}
    if request.method == 'POST':
        name = request.form.get('name', '').strip()[:100]
        email = request.form.get('email', '').strip().lower()[:150]
        phone = request.form.get('phone', '').strip()[:20]
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password')
        values = {'name': name, 'email': email, 'phone': phone}

        digits = re.sub(r'\D', '', phone) if phone else ''

        if len(name) < 2:
            flash('Họ và tên phải có tối thiểu 2 ký tự.', 'warning')
        elif not email or '@' not in email or '.' not in email.rsplit('@', 1)[-1]:
            flash('Địa chỉ email không hợp lệ.', 'warning')
        elif phone and (len(digits) < 9 or len(digits) > 12):
            flash('Số điện thoại phải từ 9 đến 12 chữ số.', 'warning')
        elif len(password) < 8:
            flash('Mật khẩu ban đầu phải có tối thiểu 8 ký tự.', 'warning')
        elif confirm_password is not None and password != confirm_password:
            flash('Mật khẩu ban đầu và xác nhận mật khẩu không khớp nhau.', 'warning')
        elif query_one('SELECT MaNguoiDung FROM NguoiDung WHERE Email=?', (email,)):
            flash('Email này đã được sử dụng bởi tài khoản khác.', 'warning')
        else:
            conn = get_db_connection()
            try:
                cur = conn.cursor()
                cur.execute('''INSERT INTO NguoiDung (MaVaiTro, HoVaTen, Email, SoDienThoai, MatKhauHash, TrangThai)
                               VALUES (2, ?, ?, ?, ?, 1)''',
                            (name, email, phone, generate_password_hash(password)))
                conn.commit()
                flash('Tạo tài khoản nhân viên thành công. Vai trò tự gán: Nhân viên (Seller).', 'success')
                return redirect(url_for('w12.staff_list'))
            except Exception:
                conn.rollback()
                current_app.logger.exception('Không tạo được tài khoản nhân viên')
                flash('Lỗi khi lưu tài khoản nhân viên vào cơ sở dữ liệu.', 'warning')
            finally:
                conn.close()

    return render_template('w12/admin_staff_form.html', user=None, values=values)


@w12.route('/admin/staff/<int:user_id>/edit', methods=['GET', 'POST'])
@admin
def staff_edit(user_id):
    user = query_one('SELECT MaNguoiDung, HoVaTen, Email, SoDienThoai, TrangThai FROM NguoiDung WHERE MaNguoiDung=? AND MaVaiTro=2', (user_id,))
    if not user:
        abort(404)
    if request.method == 'POST':
        name = request.form.get('name', '').strip()[:100]
        email = request.form.get('email', '').strip().lower()[:150]
        phone = request.form.get('phone', '').strip()[:20]
        digits = re.sub(r'\D', '', phone) if phone else ''

        if len(name) < 2:
            flash('Họ và tên phải có tối thiểu 2 ký tự.', 'warning')
        elif not email or '@' not in email or '.' not in email.rsplit('@', 1)[-1]:
            flash('Địa chỉ email không hợp lệ.', 'warning')
        elif not digits or len(digits) < 9 or len(digits) > 12:
            flash('Số điện thoại phải từ 9 đến 12 chữ số.', 'warning')
        elif query_one('SELECT MaNguoiDung FROM NguoiDung WHERE Email=? AND MaNguoiDung<>?', (email, user_id)):
            flash('Email này đã được sử dụng bởi tài khoản khác.', 'warning')
        else:
            conn = get_db_connection()
            try:
                cur = conn.cursor()
                cur.execute('''UPDATE NguoiDung SET HoVaTen=?, Email=?, SoDienThoai=?
                               WHERE MaNguoiDung=? AND MaVaiTro=2''',
                            (name, email, phone, user_id))
                conn.commit()
                flash('Đã cập nhật thông tin nhân viên thành công.', 'success')
                return redirect(url_for('w12.staff_list'))
            except Exception:
                conn.rollback()
                flash('Không thể cập nhật thông tin nhân viên.', 'warning')
            finally:
                conn.close()
    return render_template('w12/admin_staff_form.html', user=user, values=user)


@w12.get('/admin/customers')
@admin
def customers():
    users, q, status_filter, pagination = _users_list(3, kind='customer')
    return render_template('w12/admin_users.html', users=users, q=q, status=status_filter,
                           pagination=pagination, kind='customer')


@w12.get('/admin/customers/<int:user_id>/orders')
@admin
def customer_orders(user_id):
    user = query_one('SELECT MaNguoiDung, HoVaTen, Email, SoDienThoai, TrangThai FROM NguoiDung WHERE MaNguoiDung=? AND MaVaiTro=3', (user_id,))
    if not user:
        abort(404)
    orders = query_all('''SELECT dh.MaDonHang, dh.NgayDat, dh.TrangThai, dh.TongTien,
                                 tg.TrangThaiThanhToan, tg.PhuongThucThanhToan, tg.DiaChiGiaoHang
                          FROM DonHang dh
                          LEFT JOIN ThongTinGiaoDich tg ON tg.MaDonHang = dh.MaDonHang
                          WHERE dh.MaNguoiDung=?
                          ORDER BY dh.MaDonHang DESC''', (user_id,))
    return render_template('w12/admin_customer_orders.html', user=user, orders=orders)


@w12.post('/admin/users/<int:user_id>/toggle')
@admin
def user_toggle(user_id):
    """Khóa / Mở khóa tài khoản nhân viên hoặc khách hàng.
    Lưu người thao tác và thời gian khóa. Phiên làm việc cũ bị thu hồi ngay ở request sau.
    """
    user = query_one('SELECT MaVaiTro, TrangThai, HoVaTen FROM NguoiDung WHERE MaNguoiDung=?', (user_id,))
    if not user or int(user['MaVaiTro']) not in (2, 3):
        abort(404)

    new_status = 0 if user['TrangThai'] else 1
    reason = request.form.get('reason', '').strip()[:255] if new_status == 0 else None
    admin_id = session.get('user_id')

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('''UPDATE NguoiDung
                       SET TrangThai = ?, NguoiKhoa = ?, ThoiGianKhoa = CURRENT_TIMESTAMP, GhiChuKhoa = ?
                       WHERE MaNguoiDung = ? AND MaVaiTro IN (2, 3)''',
                    (new_status, admin_id if new_status == 0 else None, reason, user_id))
        conn.commit()
        status_text = "được mở khóa" if new_status == 1 else "đã bị khóa"
        flash(f"Tài khoản {user['HoVaTen']} #{user_id} {status_text}.", "success")
    except Exception:
        conn.rollback()
        current_app.logger.exception('Lỗi toggle trạng thái tài khoản')
        flash('Không thể thay đổi trạng thái tài khoản.', 'warning')
    finally:
        conn.close()

    return redirect(url_for('w12.staff_list' if user['MaVaiTro'] == 2 else 'w12.customers'))


@w12.post('/admin/staff/<int:user_id>/delete')
@admin
def staff_delete(user_id):
    """Xóa nhân viên an toàn:
    - Nếu đã có giao dịch hoặc dữ liệu liên quan (tạo SP, xử lý đơn, thu tiền) -> XÓA MỀM (ngừng hoạt động / khóa).
    - Nếu chưa có dữ liệu phụ thuộc -> Xóa cứng.
    """
    user = query_one('SELECT MaNguoiDung, HoVaTen FROM NguoiDung WHERE MaNguoiDung=? AND MaVaiTro=2', (user_id,))
    if not user:
        abort(404)
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        # Kiểm tra dữ liệu liên quan
        cur.execute('SELECT COUNT(*) FROM SanPham WHERE MaNguoiTao=?', (user_id,))
        sp_count = int(cur.fetchone()[0])

        cur.execute('SELECT COUNT(*) FROM DonHang WHERE MaNguoiDung=? OR MaNguoiXuLy=?', (user_id, user_id))
        dh_count = int(cur.fetchone()[0])

        cur.execute('SELECT COUNT(*) FROM ThongTinGiaoDich WHERE NguoiThuTien=?', (user_id,))
        pay_count = int(cur.fetchone()[0])

        has_history = (sp_count > 0 or dh_count > 0 or pay_count > 0)

        if has_history:
            cur.execute("""UPDATE NguoiDung
                           SET TrangThai = 0,
                               GhiChuKhoa = 'Ngừng hoạt động / xóa mềm do đã có dữ liệu lịch sử trong hệ thống'
                           WHERE MaNguoiDung = ? AND MaVaiTro = 2""", (user_id,))
            msg = f"Nhân viên '{user['HoVaTen']}' đã có lịch sử sản phẩm/đơn hàng: hệ thống đã chuyển sang Ngừng hoạt động (khóa tài khoản) để bảo toàn dữ liệu lịch sử."
        else:
            cur.execute('DELETE FROM NguoiDung WHERE MaNguoiDung=? AND MaVaiTro=2', (user_id,))
            msg = f"Đã xóa hoàn toàn nhân viên '{user['HoVaTen']}' (chưa có dữ liệu phụ thuộc)."

        conn.commit()
        flash(msg, 'success')
    except Exception:
        conn.rollback()
        current_app.logger.exception('Lỗi xóa nhân viên')
        flash('Không thể xóa nhân viên; dữ liệu được giữ nguyên.', 'warning')
    finally:
        conn.close()
    return redirect(url_for('w12.staff_list'))
