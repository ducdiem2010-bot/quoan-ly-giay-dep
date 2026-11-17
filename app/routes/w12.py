"""W12: Nghiệp vụ quản trị (Admin) và nhân viên bán hàng (Seller).
Hỗ trợ cả SQLite và SQL Server, chuẩn hóa tham số hóa và quyền hạn.
"""
from functools import wraps
from uuid import uuid4
from math import ceil
import re
from urllib.parse import urlencode
from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for, current_app
from werkzeug.security import generate_password_hash
from ..db import get_db_connection, query_all, query_one
from ..services.order_ops import (
    confirm_order_stock, complete_order_status,
    cancel_order_stock, record_order_payment,
    start_order_shipping, mark_order_delivered,
    ensure_order_transaction_info, confirm_return_stock, get_order_return_lines, OrderOperationError
)

from ..services.return_refunds import (
    receive_completed_return, confirm_refund_paid, order_refund_summary, list_completed_returns, group_return_receipts
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



def _attach_return_status(orders):
    """Add return and refund summaries WITHOUT changing order completion status."""
    if not orders:
        return orders
    ids = [int(o['MaDonHang']) for o in orders]
    marks = ','.join('?' for _ in ids)
    rows = query_all(f"""SELECT dh.MaDonHang,
            COALESCE((SELECT SUM(ct.SoLuong) FROM ChiTietDonHang ct WHERE ct.MaDonHang=dh.MaDonHang),0) AS MuaGoc,
            COALESCE((SELECT SUM(t.SoLuong) FROM TraHangChiTiet t WHERE t.MaDonHang=dh.MaDonHang),0) AS DaTra,
            COALESCE((SELECT SUM(t.TienGiamDoanhThu) FROM TraHangChiTiet t WHERE t.MaDonHang=dh.MaDonHang),0) AS TienDuyet,
            COALESCE((SELECT SUM(h.SoTien) FROM HoanTienGiaoDich h WHERE h.MaDonHang=dh.MaDonHang
                AND h.PhuongThuc IN ('cash','bank_transfer')),0) AS DaHoan,
            dh.TrangThai, dh.TongTien,
            COALESCE(tg.TrangThaiThanhToan,'Chưa thanh toán') AS ThanhToan
            FROM DonHang dh LEFT JOIN ThongTinGiaoDich tg ON tg.MaDonHang=dh.MaDonHang
            WHERE dh.MaDonHang IN ({marks})""", tuple(ids))
    by_id = {int(r['MaDonHang']):r for r in rows}
    for order in orders:
        r = by_id.get(int(order['MaDonHang']))
        if not r:
            continue
        bought, returned = int(r['MuaGoc']), int(r['DaTra'])
        if r['TrangThai'] == 'Hoàn thành':
            due = min(float(r['TienDuyet']), float(r['TongTien']))
        elif r['TrangThai'] == 'Đã hủy' and r['ThanhToan'] == 'Đã thanh toán':
            due = float(r['TongTien'])
        else:
            due = 0.0
        paid = float(r['DaHoan'])
        order.update(return_label=('Trả toàn bộ' if bought and returned >= bought else
                                   'Trả một phần' if returned else 'Chưa trả hàng'),
                     refund_label=('Không cần hoàn tiền' if due <= 0 else
                                   'Đã hoàn tiền' if paid >= due else
                                   'Hoàn tiền một phần' if paid > 0 else 'Chờ hoàn tiền'),
                     money_due=due, money_paid=paid, money_remaining=max(0.0,due-paid))
    return orders

def _filter_and_paginate_orders(is_admin_view=True):
    filters = []
    args = []
    q = _q()
    status = request.args.get('status', '', type=str).strip()[:40]
    pay_status = request.args.get('pay_status', '', type=str).strip()[:40]
    ship_status = request.args.get('ship_status', '', type=str).strip()[:40]
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

    if ship_status:
        if ship_status not in ('Chưa giao', 'Đang giao', 'Đã giao'):
            abort(400, description='Trạng thái giao hàng không hợp lệ.')
        filters.append("COALESCE(dh.TrangThaiGiaoHang, 'Chưa giao')=?")
        args.append(ship_status)

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
                            COALESCE(dh.TrangThaiGiaoHang, 'Chưa giao') AS TrangThaiGiaoHang,
                            dh.MaNguoiXuLy, dh.ThoiGianXuLy,
                            dh.NguoiXacNhan, dh.ThoiGianXacNhan,
                            dh.NguoiGiaoHang, dh.ThoiGianBatDauGiao,
                            dh.NguoiXacNhanGiao, dh.ThoiGianGiaoThanhCong,
                            dh.NguoiHoanThanh, dh.ThoiGianHoanThanh,
                            dh.NguoiHuy, dh.ThoiGianHuy, dh.TrangThaiHoanTien,
                            dh.LichSuXuLy,
                            nd.HoVaTen AS KhachHang, nd.Email AS EmailKhach, nd.SoDienThoai AS SdtKhach,
                            tg.HoTen AS TenNguoiNhan, tg.SoDienThoai AS SdtNguoiNhan,
                            tg.DiaChiGiaoHang, tg.PhuongThucThanhToan, tg.TrangThaiThanhToan
                     FROM DonHang dh
                     LEFT JOIN NguoiDung nd ON nd.MaNguoiDung = dh.MaNguoiDung
                     LEFT JOIN ThongTinGiaoDich tg ON tg.MaDonHang = dh.MaDonHang
                     {where_clause}
                     ORDER BY dh.MaDonHang {order_direction}"""

    all_rows = query_all(select_sql, tuple(args))
    orders_page = _attach_return_status(all_rows[offset:offset + per_page])

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

    return orders_page, q, status, pay_status, ship_status, sort, pagination


# ==============================================================================
# ADMIN ĐƠN HÀNG & PHIẾU XUẤT
# ==============================================================================

@w12.get('/admin/orders')
@admin
def admin_orders():
    orders, q, status, pay_status, ship_status, sort, pagination = _filter_and_paginate_orders(is_admin_view=True)
    return render_template('w12/admin_orders.html', orders=orders, q=q, status=status,
                           pay_status=pay_status, ship_status=ship_status, sort=sort, pagination=pagination)


@w12.get('/admin/orders/<int:order_id>')
@admin
def admin_order_detail(order_id):
    order = query_one('''SELECT dh.MaDonHang, dh.MaNguoiDung, dh.NgayDat, dh.TrangThai, dh.TongTien,
                                COALESCE(dh.TrangThaiGiaoHang, 'Chưa giao') AS TrangThaiGiaoHang,
                                dh.MaNguoiXuLy, dh.ThoiGianXuLy,
                                dh.NguoiXacNhan, dh.ThoiGianXacNhan,
                                dh.NguoiGiaoHang, dh.ThoiGianBatDauGiao,
                                dh.NguoiXacNhanGiao, dh.ThoiGianGiaoThanhCong,
                                dh.NguoiHoanThanh, dh.ThoiGianHoanThanh,
                                dh.NguoiHuy, dh.ThoiGianHuy, dh.TrangThaiHoanTien,
                                dh.LichSuXuLy,
                                nd.HoVaTen AS KhachHang, nd.Email AS EmailKhach, nd.SoDienThoai AS SdtKhach,
                                tg.HoTen AS TenNguoiNhan, tg.SoDienThoai AS SdtNguoiNhan, tg.Email AS EmailNguoiNhan,
                                tg.HinhThucNhanHang, tg.DiaChiGiaoHang, tg.PhuongThucThanhToan,
                                tg.TrangThaiThanhToan, tg.PhiVanChuyen, tg.GhiChu, tg.NgayTao AS NgayTaoGiaoDich,
                                tg.NguoiThuTien, tg.ThoiGianThanhToan,
                                nx.HoVaTen AS TenNguoiXuLy, nt.HoVaTen AS TenNguoiThuTien,
                                nxn.HoVaTen AS TenNguoiXacNhan, ngh.HoVaTen AS TenNguoiGiaoHang,
                                nxg.HoVaTen AS TenNguoiXacNhanGiao, nht.HoVaTen AS TenNguoiHoanThanh,
                                nhy.HoVaTen AS TenNguoiHuy
                         FROM DonHang dh
                         LEFT JOIN NguoiDung nd ON nd.MaNguoiDung = dh.MaNguoiDung
                         LEFT JOIN ThongTinGiaoDich tg ON tg.MaDonHang = dh.MaDonHang
                         LEFT JOIN NguoiDung nx ON nx.MaNguoiDung = dh.MaNguoiXuLy
                         LEFT JOIN NguoiDung nt ON nt.MaNguoiDung = tg.NguoiThuTien
                         LEFT JOIN NguoiDung nxn ON nxn.MaNguoiDung = dh.NguoiXacNhan
                         LEFT JOIN NguoiDung ngh ON ngh.MaNguoiDung = dh.NguoiGiaoHang
                         LEFT JOIN NguoiDung nxg ON nxg.MaNguoiDung = dh.NguoiXacNhanGiao
                         LEFT JOIN NguoiDung nht ON nht.MaNguoiDung = dh.NguoiHoanThanh
                         LEFT JOIN NguoiDung nhy ON nhy.MaNguoiDung = dh.NguoiHuy
                         WHERE dh.MaDonHang=?''', (order_id,))
    if not order:
        abort(404)
    try:
        items = query_all('''SELECT COALESCE(sp.MaSanPham, bt.MaSanPham) AS MaSanPham,
                                    COALESCE(ct.TenSanPham, sp.TenSanPham) AS TenSanPham,
                                    COALESCE(ct.MauSac, bt.MauSac) AS MauSac,
                                    COALESCE(ct.KichThuoc, bt.KichThuoc) AS KichThuoc,
                                    ct.MaBienThe, ct.SoLuong, ct.DonGia, (ct.SoLuong * ct.DonGia) AS ThanhTien,
                                    COALESCE((SELECT SUM(r.SoLuong) FROM TraHangChiTiet r
                                     WHERE r.MaDonHang=ct.MaDonHang AND r.MaBienThe=ct.MaBienThe),0) AS DaTra
                             FROM ChiTietDonHang ct
                             LEFT JOIN BienTheSanPham bt ON bt.MaBienThe = ct.MaBienThe
                             LEFT JOIN SanPham sp ON sp.MaSanPham = bt.MaSanPham
                             WHERE ct.MaDonHang=?
                             ORDER BY ct.MaChiTietDon''', (order_id,))
    except Exception:
        items = query_all('''SELECT sp.MaSanPham, sp.TenSanPham, bt.MauSac, bt.KichThuoc,
                                    ct.MaBienThe, ct.SoLuong, ct.DonGia, (ct.SoLuong * ct.DonGia) AS ThanhTien,
                                    COALESCE((SELECT SUM(r.SoLuong) FROM TraHangChiTiet r
                                     WHERE r.MaDonHang=ct.MaDonHang AND r.MaBienThe=ct.MaBienThe),0) AS DaTra
                             FROM ChiTietDonHang ct
                             JOIN BienTheSanPham bt ON bt.MaBienThe = ct.MaBienThe
                             JOIN SanPham sp ON sp.MaSanPham = bt.MaSanPham
                             WHERE ct.MaDonHang=?
                             ORDER BY ct.MaChiTietDon''', (order_id,))
    return render_template('w12/admin_order_detail.html', order=order, items=items,
                           returns=get_order_return_lines(order_id),
                           completed_returns=list_completed_returns(order_id),
                           refund_summary=order_refund_summary(order_id),
                           refund_history=query_all('''SELECT MaHoanTien,SoTien,PhuongThuc,MaThamChieu,HoVaTenNguoiXacNhan,ThoiGian FROM HoanTienGiaoDich WHERE MaDonHang=? ORDER BY MaHoanTien DESC''',(order_id,)),
                           return_form=session.pop('return_form', {}) if session.get('return_form',{}).get('order_id') == order_id else {},
                           return_token=uuid4().hex,refund_token=uuid4().hex,
                           deleted_staff_history=query_all('''SELECT a.HoVaTen,a.Email,k.VaiTroXuLy
                             FROM NhatKyNhanVienDaXoa k JOIN NhanVienDaXoa a ON a.MaNhanVienCu=k.MaNhanVienCu
                             WHERE k.Loai='DonHang' AND k.MaThamChieu=?''',(order_id,)))


@w12.get('/admin/invoices')
@admin
def invoices():
    """Chuyển hướng trang phiếu đơn hàng trùng lặp sang trang quản lý đơn hàng chính, giữ nguyên bộ lọc."""
    return redirect(url_for('w12.admin_orders', **request.args), code=302)


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
    orders, q, status, pay_status, ship_status, sort, pagination = _filter_and_paginate_orders(is_admin_view=False)
    return render_template('w12/staff_orders.html', orders=orders, q=q, status=status,
                           pay_status=pay_status, ship_status=ship_status, sort=sort, pagination=pagination)


@w12.get('/staff/orders/<int:order_id>')
@seller
def staff_order_detail(order_id):
    order = query_one('''SELECT dh.MaDonHang, dh.MaNguoiDung, dh.NgayDat, dh.TrangThai, dh.TongTien,
                                COALESCE(dh.TrangThaiGiaoHang, 'Chưa giao') AS TrangThaiGiaoHang,
                                dh.MaNguoiXuLy, dh.ThoiGianXuLy,
                                dh.NguoiXacNhan, dh.ThoiGianXacNhan,
                                dh.NguoiGiaoHang, dh.ThoiGianBatDauGiao,
                                dh.NguoiXacNhanGiao, dh.ThoiGianGiaoThanhCong,
                                dh.NguoiHoanThanh, dh.ThoiGianHoanThanh,
                                dh.NguoiHuy, dh.ThoiGianHuy, dh.TrangThaiHoanTien,
                                dh.LichSuXuLy,
                                nd.HoVaTen AS KhachHang, nd.Email AS EmailKhach, nd.SoDienThoai AS SdtKhach,
                                tg.HoTen AS TenNguoiNhan, tg.SoDienThoai AS SdtNguoiNhan, tg.Email AS EmailNguoiNhan,
                                tg.HinhThucNhanHang, tg.DiaChiGiaoHang, tg.PhuongThucThanhToan,
                                tg.TrangThaiThanhToan, tg.PhiVanChuyen, tg.GhiChu, tg.NgayTao AS NgayTaoGiaoDich,
                                tg.NguoiThuTien, tg.ThoiGianThanhToan,
                                nx.HoVaTen AS TenNguoiXuLy, nt.HoVaTen AS TenNguoiThuTien,
                                nxn.HoVaTen AS TenNguoiXacNhan, ngh.HoVaTen AS TenNguoiGiaoHang,
                                nxg.HoVaTen AS TenNguoiXacNhanGiao, nht.HoVaTen AS TenNguoiHoanThanh,
                                nhy.HoVaTen AS TenNguoiHuy
                         FROM DonHang dh
                         LEFT JOIN NguoiDung nd ON nd.MaNguoiDung = dh.MaNguoiDung
                         LEFT JOIN ThongTinGiaoDich tg ON tg.MaDonHang = dh.MaDonHang
                         LEFT JOIN NguoiDung nx ON nx.MaNguoiDung = dh.MaNguoiXuLy
                         LEFT JOIN NguoiDung nt ON nt.MaNguoiDung = tg.NguoiThuTien
                         LEFT JOIN NguoiDung nxn ON nxn.MaNguoiDung = dh.NguoiXacNhan
                         LEFT JOIN NguoiDung ngh ON ngh.MaNguoiDung = dh.NguoiGiaoHang
                         LEFT JOIN NguoiDung nxg ON nxg.MaNguoiDung = dh.NguoiXacNhanGiao
                         LEFT JOIN NguoiDung nht ON nht.MaNguoiDung = dh.NguoiHoanThanh
                         LEFT JOIN NguoiDung nhy ON nhy.MaNguoiDung = dh.NguoiHuy
                         WHERE dh.MaDonHang=?''', (order_id,))
    if not order:
        abort(404)
    try:
        items = query_all('''SELECT COALESCE(sp.MaSanPham, bt.MaSanPham) AS MaSanPham,
                                    COALESCE(ct.TenSanPham, sp.TenSanPham) AS TenSanPham,
                                    COALESCE(ct.MauSac, bt.MauSac) AS MauSac,
                                    COALESCE(ct.KichThuoc, bt.KichThuoc) AS KichThuoc,
                                    ct.MaBienThe, ct.SoLuong, ct.DonGia, (ct.SoLuong * ct.DonGia) AS ThanhTien,
                                    COALESCE((SELECT SUM(r.SoLuong) FROM TraHangChiTiet r
                                     WHERE r.MaDonHang=ct.MaDonHang AND r.MaBienThe=ct.MaBienThe),0) AS DaTra
                             FROM ChiTietDonHang ct
                             LEFT JOIN BienTheSanPham bt ON bt.MaBienThe = ct.MaBienThe
                             LEFT JOIN SanPham sp ON sp.MaSanPham = bt.MaSanPham
                             WHERE ct.MaDonHang=?
                             ORDER BY ct.MaChiTietDon''', (order_id,))
    except Exception:
        items = query_all('''SELECT sp.MaSanPham, sp.TenSanPham, bt.MauSac, bt.KichThuoc,
                                    ct.MaBienThe, ct.SoLuong, ct.DonGia, (ct.SoLuong * ct.DonGia) AS ThanhTien,
                                    COALESCE((SELECT SUM(r.SoLuong) FROM TraHangChiTiet r
                                     WHERE r.MaDonHang=ct.MaDonHang AND r.MaBienThe=ct.MaBienThe),0) AS DaTra
                             FROM ChiTietDonHang ct
                             JOIN BienTheSanPham bt ON bt.MaBienThe = ct.MaBienThe
                             JOIN SanPham sp ON sp.MaSanPham = bt.MaSanPham
                             WHERE ct.MaDonHang=?
                             ORDER BY ct.MaChiTietDon''', (order_id,))
    return render_template('w12/admin_order_detail.html', order=order, items=items,
                           is_staff=True, returns=get_order_return_lines(order_id),
                           completed_returns=list_completed_returns(order_id),
                           refund_summary=order_refund_summary(order_id),
                           refund_history=query_all('''SELECT MaHoanTien,SoTien,PhuongThuc,MaThamChieu,HoVaTenNguoiXacNhan,ThoiGian FROM HoanTienGiaoDich WHERE MaDonHang=? ORDER BY MaHoanTien DESC''',(order_id,)),
                           return_form=session.pop('return_form', {}) if session.get('return_form',{}).get('order_id') == order_id else {},
                           return_token=uuid4().hex,refund_token=uuid4().hex,
                           deleted_staff_history=query_all('''SELECT a.HoVaTen,a.Email,k.VaiTroXuLy
                             FROM NhatKyNhanVienDaXoa k JOIN NhanVienDaXoa a ON a.MaNhanVienCu=k.MaNhanVienCu
                             WHERE k.Loai='DonHang' AND k.MaThamChieu=?''',(order_id,)))


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


@w12.post('/orders/<int:order_id>/ship')
@staff_or_admin
def order_action_ship(order_id):
    redirect_target = request.referrer or (url_for('w12.admin_order_detail', order_id=order_id)
                                           if session.get('role') == 'Admin'
                                           else url_for('w12.staff_order_detail', order_id=order_id))
    try:
        start_order_shipping(order_id, session['user_id'])
        flash(f"Đã chuyển đơn hàng #{order_id} sang trạng thái Đang giao hàng.", "success")
    except OrderOperationError as e:
        flash(str(e), "warning")
    except Exception:
        current_app.logger.exception("Lỗi chuyển giao hàng")
        flash("Không thể cập nhật trạng thái giao hàng.", "warning")
    return redirect(redirect_target)


@w12.post('/orders/<int:order_id>/deliver')
@staff_or_admin
def order_action_deliver(order_id):
    redirect_target = request.referrer or (url_for('w12.admin_order_detail', order_id=order_id)
                                           if session.get('role') == 'Admin'
                                           else url_for('w12.staff_order_detail', order_id=order_id))
    try:
        mark_order_delivered(order_id, session['user_id'])
        flash(f"Đã xác nhận đơn hàng #{order_id} giao hàng thành công (Đã giao).", "success")
    except OrderOperationError as e:
        flash(str(e), "warning")
    except Exception:
        current_app.logger.exception("Lỗi xác nhận đã giao hàng")
        flash("Không thể cập nhật trạng thái đã giao hàng.", "warning")
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
        pending_lines = get_order_return_lines(order_id)
        if pending_lines:
            flash(f"Đã hủy đơn #{order_id}. Hàng đang vận chuyển: CHỜ HOÀN KHO; tồn kho chưa được cộng lại.", "success")
        else:
            flash(f"Đã hủy đơn #{order_id} và đã xử lý tồn kho (nếu hàng chưa giao).", "success")
    except OrderOperationError as e:
        flash(str(e), "warning")
    except Exception:
        current_app.logger.exception("Lỗi hủy đơn")
        flash("Không thể hủy đơn hàng.", "warning")
    return redirect(redirect_target)


@w12.post('/orders/<int:order_id>/return-stock')
@staff_or_admin
def order_action_return_stock(order_id):
    """Nhân viên xác nhận hàng đã về kho theo từng biến thể (không tự động khi hủy)."""
    target = (url_for('w12.admin_order_detail', order_id=order_id)
              if session.get('role') == 'Admin'
              else url_for('w12.staff_order_detail', order_id=order_id))
    try:
        lines = get_order_return_lines(order_id)
        good = {int(r['MaBienThe']): request.form.get(f"good_{r['MaBienThe']}", '0') for r in lines}
        bad = {int(r['MaBienThe']): request.form.get(f"bad_{r['MaBienThe']}", '0') for r in lines}
        confirm_return_stock(order_id, session['user_id'], good, bad)
        flash(f"Đã xác nhận nhập lại hàng thực nhận cho đơn #{order_id}.", "success")
    except (OrderOperationError, ValueError) as e:
        flash(str(e), "warning")
    except Exception:
        current_app.logger.exception('Lỗi nhập hàng hoàn về')
        flash('Không thể hoàn kho. Mọi thay đổi đã được hoàn tác.', 'warning')
    return redirect(target)


def _order_detail_target(order_id):
    return url_for('w12.admin_order_detail' if session.get('role') == 'Admin'
                   else 'w12.staff_order_detail', order_id=order_id)


@w12.post('/orders/<int:order_id>/receive-return')
@staff_or_admin
def order_action_receive_return(order_id):
    """Hàng trả thực nhận sau khi hoàn thành; số tiền được duyệt KHÔNG có nghĩa đã trả tiền."""
    try:
        changes = []
        for key, values in request.form.lists():
            if key.startswith('qty_'):
                if len(values) != 1 or not re.fullmatch(r'[0-9]+', values[0]) or not key[4:].isdigit():
                    raise OrderOperationError('Số lượng trả phải là số nguyên không âm.')
                if int(values[0]):
                    changes.append((int(key[4:]), int(values[0])))
        receive_completed_return(order_id,session['user_id'], changes,
                                 request.form.get('request_token'),request.form.get('reason'))
        session.pop('return_form', None)
        flash('Đã ghi nhận hàng trả và điều chỉnh doanh thu thuần; chưa tự xác nhận hoàn tiền.', 'success')
    except (OrderOperationError,ValueError) as exc:
        session['return_form'] = {'order_id':order_id, 'values':{k:v[:255] for k,v in request.form.items() if k == 'reason' or k.startswith('qty_')}}
        flash(str(exc),'warning')
    except Exception:
        session['return_form'] = {'order_id':order_id, 'values':{k:v[:255] for k,v in request.form.items() if k == 'reason' or k.startswith('qty_')}}
        current_app.logger.exception('Lỗi ghi nhận trả hàng một phần')
        flash('Không thể lưu hàng trả. Giao dịch đã được hoàn tác.','warning')
    return redirect(_order_detail_target(order_id))


@w12.post('/orders/<int:order_id>/refund-paid')
@staff_or_admin
def order_action_refund_paid(order_id):
    """Xác nhận ĐÃ TRẢ tiền thực tế; không phát lệnh chuyển khoản."""
    try:
        confirm_refund_paid(order_id,session['user_id'],request.form.get('amount'),
                            request.form.get('method'),request.form.get('reference'),
                            request.form.get('request_token'))
        flash('Đã xác nhận số tiền thực hoàn cho khách và lưu lịch sử giao dịch.','success')
    except (OrderOperationError,ValueError) as exc:
        flash(str(exc),'warning')
    except Exception:
        current_app.logger.exception('Lỗi xác nhận hoàn tiền')
        flash('Không thể ghi nhận hoàn tiền. Giao dịch đã được hoàn tác.','warning')
    return redirect(_order_detail_target(order_id))


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


@w12.post('/orders/<int:order_id>/init-transaction')
@staff_or_admin
def order_action_init_transaction(order_id):
    redirect_target = request.referrer or (url_for('w12.admin_order_detail', order_id=order_id)
                                           if session.get('role') == 'Admin'
                                           else url_for('w12.staff_order_detail', order_id=order_id))
    fn = request.form.get('full_name', '').strip()
    ph = request.form.get('phone', '').strip()
    addr = request.form.get('address', '').strip()
    try:
        ensure_order_transaction_info(order_id, session['user_id'], full_name=fn, phone=ph, address=addr)
        flash(f"Đã cập nhật thông tin giao dịch người nhận cho đơn hàng #{order_id}.", "success")
    except OrderOperationError as e:
        flash(str(e), "warning")
    except Exception:
        current_app.logger.exception("Lỗi cập nhật thông tin giao dịch")
        flash("Không thể cập nhật thông tin giao dịch.", "warning")
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
        elif not digits or len(digits) < 9 or len(digits) > 12 or not re.fullmatch(r'\+?[0-9]+', phone):
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
        elif not digits or len(digits) < 9 or len(digits) > 12 or not re.fullmatch(r'\+?[0-9]+', phone):
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


@w12.route('/admin/staff/<int:user_id>/reset-password', methods=['GET','POST'])
@admin
def staff_reset_password(user_id):
    staff = query_one('SELECT MaNguoiDung,HoVaTen,Email FROM NguoiDung WHERE MaNguoiDung=? AND MaVaiTro=2',(user_id,))
    if not staff:
        abort(404)
    if request.method == 'POST':
        new_pass = request.form.get('password','')
        confirm_pass = request.form.get('confirm_password','')
        if len(new_pass) < 8 or len(new_pass) > 128:
            flash('Mật khẩu mới phải dài từ 8 đến 128 ký tự.','warning')
        elif new_pass != confirm_pass:
            flash('Xác nhận mật khẩu không khớp.','warning')
        else:
            conn = get_db_connection()
            try:
                cur = conn.cursor()
                cur.execute('UPDATE NguoiDung SET MatKhauHash=? WHERE MaNguoiDung=? AND MaVaiTro=2',
                            (generate_password_hash(new_pass),user_id))
                if cur.rowcount != 1:
                    raise ValueError('Nhân viên không tồn tại.')
                conn.commit()
                flash(f'Đã đặt lại mật khẩu cho nhân viên {staff["HoVaTen"]}.','success')
                return redirect(url_for('w12.staff_list'))
            except Exception:
                conn.rollback()
                current_app.logger.exception('Không đặt lại được mật khẩu nhân viên')
                flash('Không thể đặt lại mật khẩu nhân viên.','warning')
            finally:
                conn.close()
    return render_template('w12/admin_staff_password.html', user=staff)


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
                                 COALESCE(dh.TrangThaiGiaoHang, 'Chưa giao') AS TrangThaiGiaoHang,
                                 tg.TrangThaiThanhToan, tg.PhuongThucThanhToan, tg.DiaChiGiaoHang
                          FROM DonHang dh
                          LEFT JOIN ThongTinGiaoDich tg ON tg.MaDonHang = dh.MaDonHang
                          WHERE dh.MaNguoiDung=?
                          ORDER BY dh.MaDonHang DESC''', (user_id,))
    return render_template('w12/admin_customer_orders.html', user=user, orders=_attach_return_status(orders))


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
    """XÓA THẬT tài khoản Seller, nhưng lưu snapshot lịch sử nghiệp vụ trước khi bỏ FK.

    Mọi thay đổi chạy trong một transaction. Không đổi người xử lý thành nhân viên khác,
    không xóa đơn hàng/tiền/hàng trả. Bảng audit độc lập với tài khoản đã xóa.
    """
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if current_app.config.get('DB_BACKEND') == 'sqlite':
            cur.execute('BEGIN IMMEDIATE')
            lock = ''
        else:
            lock = ' WITH (UPDLOCK, HOLDLOCK)'
        cur.execute(f'SELECT MaNguoiDung,HoVaTen,Email FROM NguoiDung{lock} WHERE MaNguoiDung=? AND MaVaiTro=2',(user_id,))
        staff = cur.fetchone()
        if not staff:
            abort(404)
        cur.execute("""INSERT INTO NhanVienDaXoa (MaNhanVienCu,HoVaTen,Email,MaAdminXoa)
                       VALUES (?,?,?,?)""",(user_id,staff[1],staff[2],session.get('user_id')))
        references = (
            ('DonHang','MaDonHang',('MaNguoiDung','MaNguoiXuLy','NguoiXacNhan','NguoiGiaoHang','NguoiXacNhanGiao','NguoiHoanThanh','NguoiHuy')),
            ('ThongTinGiaoDich','MaDonHang',('NguoiThuTien',)),
            ('SanPham','MaSanPham',('MaNguoiTao',)),
            ('LichSuHoanKho','MaHoanKho',('NguoiThucHien',)),
            ('TraHangChiTiet','MaTraHang',('NguoiThucHien',)),
            ('HoanTienGiaoDich','MaHoanTien',('NguoiXacNhan',)),
        )
        for table, pk, columns in references:
            for col in columns:
                cur.execute(f'SELECT {pk} FROM {table} WHERE {col}=?',(user_id,))
                related = [int(row[0]) for row in cur.fetchall()]
                for ref_id in related:
                    cur.execute("""INSERT INTO NhatKyNhanVienDaXoa
                                   (MaNhanVienCu,Loai,MaThamChieu,VaiTroXuLy) VALUES (?,?,?,?)""",
                                (user_id,table,ref_id,col))
                cur.execute(f'UPDATE {table} SET {col}=NULL WHERE {col}=?',(user_id,))
        cur.execute('UPDATE NguoiDung SET NguoiKhoa=NULL WHERE NguoiKhoa=?',(user_id,))
        # GioHang/YeuThich có FK ON DELETE CASCADE; không xóa đơn hàng.
        cur.execute('DELETE FROM NguoiDung WHERE MaNguoiDung=? AND MaVaiTro=2',(user_id,))
        if cur.rowcount != 1:
            raise ValueError('Không xóa được tài khoản nhân viên.')
        conn.commit()
        flash(f'Đã XÓA tài khoản nhân viên {staff[1]}, đã lưu lịch sử người xử lý.', 'success')
    except Exception as exc:
        conn.rollback()
        if not hasattr(exc, 'code') or getattr(exc,'code',None) != 404:
            current_app.logger.exception('Lỗi xóa tài khoản nhân viên')
            flash('Không thể xóa nhân viên; dữ liệu được giữ nguyên.','warning')
        else:
            raise
    finally:
        conn.close()
    return redirect(url_for('w12.staff_list'))


# ==============================================================================
# VIEW / PRINT - read-only endpoints, always re-check order and receipt ownership
# ==============================================================================
def _print_order_data(order_id):
    order = query_one("""SELECT dh.MaDonHang,dh.MaNguoiDung,dh.NgayDat,dh.TrangThai,dh.TongTien,
        nd.HoVaTen AS KhachHang,nd.Email AS EmailKhach,
        tg.HoTen AS TenNguoiNhan,tg.SoDienThoai AS SdtNguoiNhan,tg.DiaChiGiaoHang,
        tg.PhuongThucThanhToan,tg.TrangThaiThanhToan,tg.PhiVanChuyen,
        nh.HoVaTen AS TenNguoiHoanThanh
        FROM DonHang dh LEFT JOIN NguoiDung nd ON nd.MaNguoiDung=dh.MaNguoiDung
        LEFT JOIN ThongTinGiaoDich tg ON tg.MaDonHang=dh.MaDonHang
        LEFT JOIN NguoiDung nh ON nh.MaNguoiDung=dh.NguoiHoanThanh
        WHERE dh.MaDonHang=?""",(order_id,))
    if not order:
        abort(404)
    try:
        items = query_all("""SELECT COALESCE(ct.TenSanPham,sp.TenSanPham) AS TenSanPham,
        COALESCE(ct.KichThuoc,bt.KichThuoc) AS KichThuoc,
        COALESCE(ct.MauSac,bt.MauSac) AS MauSac,
        ct.SoLuong,ct.DonGia,ct.SoLuong*ct.DonGia AS ThanhTien
        FROM ChiTietDonHang ct
        LEFT JOIN BienTheSanPham bt ON bt.MaBienThe=ct.MaBienThe
        LEFT JOIN SanPham sp ON sp.MaSanPham=bt.MaSanPham
        WHERE ct.MaDonHang=? ORDER BY ct.MaChiTietDon""",(order_id,))
    except Exception:
        # Some older SQL Server installs do not yet have purchase snapshot columns.
        items = query_all("""SELECT sp.TenSanPham,bt.KichThuoc,bt.MauSac,
            ct.SoLuong,ct.DonGia,ct.SoLuong*ct.DonGia AS ThanhTien
            FROM ChiTietDonHang ct
            JOIN BienTheSanPham bt ON bt.MaBienThe=ct.MaBienThe
            JOIN SanPham sp ON sp.MaSanPham=bt.MaSanPham
            WHERE ct.MaDonHang=? ORDER BY ct.MaChiTietDon""",(order_id,))
    return order, items

@w12.get('/orders/<int:order_id>/print/sale')
@staff_or_admin
def print_sale(order_id):
    order, items = _print_order_data(order_id)
    returns = list_completed_returns(order_id)
    return render_template('w12/print_document.html', doc_kind='sale', order=order,
                           items=items, has_returns=bool(returns),
                           back_url=_order_detail_target(order_id))

@w12.get('/orders/<int:order_id>/returns/<int:return_id>/print')
@staff_or_admin
def print_return(order_id,return_id):
    order, _ = _print_order_data(order_id)
    receipts = group_return_receipts(list_completed_returns(order_id))
    receipt = next((g for g in receipts if return_id == g['receipt_id']), None)
    if not receipt:
        abort(404)
    return render_template('w12/print_document.html',doc_kind='return',order=order,
                           receipt=receipt, summary=order_refund_summary(order_id),
                           back_url=_order_detail_target(order_id))

@w12.get('/orders/<int:order_id>/refunds/<int:refund_id>/print')
@staff_or_admin
def print_refund(order_id,refund_id):
    order, _ = _print_order_data(order_id)
    transaction = query_one("""SELECT MaHoanTien,MaDonHang,SoTien,PhuongThuc,MaThamChieu,
        HoVaTenNguoiXacNhan,ThoiGian FROM HoanTienGiaoDich
        WHERE MaHoanTien=? AND MaDonHang=? AND PhuongThuc IN ('cash','bank_transfer')""",(refund_id,order_id))
    # 'demo' records are not proof of a real refund.
    if not transaction:
        abort(404)
    return render_template('w12/print_document.html',doc_kind='refund',order=order,
                           transaction=transaction,summary=order_refund_summary(order_id),
                           back_url=_order_detail_target(order_id))
