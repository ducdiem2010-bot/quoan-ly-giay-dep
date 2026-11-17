"""Trang tài khoản khách hàng: /account (hồ sơ) và /account/orders (đơn hàng)."""
from datetime import date
from functools import wraps
from flask import Blueprint, flash, redirect, render_template, request, session, url_for, current_app, abort

from ..db import get_db_connection
from ..services.account import (PROVINCES, ProfileValidationError, PasswordChangeError, form_values,
                                form_values_from_request, get_profile, initials,
                                list_orders, count_orders, update_profile, validate_profile, change_user_password)

acct = Blueprint("acct", __name__)


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Vui lòng đăng nhập để xem tài khoản.", "warning")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapper


def _load_profile():
    profile = get_profile(session["user_id"])
    if profile is None:  # tài khoản đã bị xóa nhưng session còn
        session.clear()
    return profile


@acct.route("/account", methods=["GET", "POST"])
@login_required
def profile():
    user = _load_profile()
    if user is None:
        return redirect(url_for("login"))
    values = form_values(user)
    # Lần đầu chưa có thông tin mở rộng thì mở sẵn chế độ nhập.
    editing = not (user["NgaySinh"] or user["TinhThanh"] or user["GioiTinh"] or user["SoDienThoai"])
    if request.method == "POST":
        try:
            data = validate_profile(request.form)
            session["user_name"] = update_profile(session["user_id"], data)
        except ProfileValidationError as exc:
            flash(str(exc), "warning")
            values, editing = form_values_from_request(request.form), True
        else:
            flash("Đã lưu thông tin tài khoản. Thông tin này sẽ được điền sẵn khi bạn đặt hàng.", "success")
            return redirect(url_for("acct.profile"))
    years = list(range(date.today().year, 1899, -1))
    return render_template("account.html", tab="profile", user=user, v=values, editing=editing,
                           provinces=PROVINCES, years=years, initials=initials(user))


@acct.get("/account/orders")
@login_required
def orders():
    user = _load_profile()
    if user is None:
        return redirect(url_for("login"))
    try:
        page = max(1, int(request.args.get('page', '1')))
    except (TypeError, ValueError):
        page = 1
    per_page = 50
    total = count_orders(session['user_id'])
    pages = max(1, (total + per_page - 1) // per_page)
    page = min(page, pages)
    return render_template('account_orders.html', tab='orders',
                           orders=list_orders(session['user_id'], limit=per_page, page=page),
                           orders_page=page, orders_pages=pages, orders_total=total)


@acct.post('/account/orders/<int:order_id>/cancel')
@login_required
def cancel_pending_order(order_id):
    """Chỉ hủy đơn CHỜ XÁC NHẬN của chủ đơn (bất kể vai trò Customer/Seller/Admin), không tác động kho.

    Checkout hiện tại không trừ kho khi tạo đơn chờ xác nhận.
    Hỗ trợ cả SQLite và SQL Server, không chặn 503.
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
        cur.execute(f"SELECT TrangThai FROM DonHang{lock_clause} WHERE MaDonHang=? AND MaNguoiDung=?",
                    (order_id, session['user_id']))
        row = cur.fetchone()
        if row is None:
            abort(404)
        status = row[0]
        # Kiểm tra trạng thái thanh toán
        paid = False
        try:
            cur.execute('SELECT TrangThaiThanhToan FROM ThongTinGiaoDich WHERE MaDonHang=?', (order_id,))
            pay_row = cur.fetchone()
            if pay_row and pay_row[0] != 'Chưa thanh toán':
                paid = True
        except Exception:
            pass
        if status != 'Chờ xác nhận' or paid:
            flash('Đơn đã được xử lý, hủy hoặc đã thanh toán; không thể hủy thêm.', 'warning')
        else:
            cur.execute("""UPDATE DonHang
                           SET TrangThai='Đã hủy',
                               NguoiHuy=?,
                               ThoiGianHuy=CURRENT_TIMESTAMP,
                               MaNguoiXuLy=?,
                               ThoiGianXuLy=CURRENT_TIMESTAMP
                           WHERE MaDonHang=? AND MaNguoiDung=? AND TrangThai='Chờ xác nhận'""",
                        (session['user_id'], session['user_id'], order_id, session['user_id']))
            flash('Đã hủy đơn chờ xác nhận thành công. Đơn chưa trừ kho nên không cần hoàn kho.', 'success')
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return redirect(url_for('acct.orders'))


@acct.route("/account/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if session.get("role") != "Admin":
        abort(403)
    user = _load_profile()
    if user is None:
        return redirect(url_for("login"))
    if request.method == "POST":
        current_pwd = request.form.get("current_password", "")
        new_pwd = request.form.get("new_password", "")
        confirm_pwd = request.form.get("confirm_password", "")
        try:
            change_user_password(session["user_id"], current_pwd, new_pwd, confirm_pwd)
            flash("Đổi mật khẩu thành công. Mật khẩu mới đã được cập nhật.", "success")
            return redirect(url_for("acct.change_password"))
        except PasswordChangeError as exc:
            flash(str(exc), "warning")
    return render_template("account_change_password.html", tab="change_password", user=user)
