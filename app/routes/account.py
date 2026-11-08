"""Trang tài khoản khách hàng: /account (hồ sơ) và /account/orders (đơn hàng)."""
from datetime import date
from functools import wraps
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ..services.account import (PROVINCES, ProfileValidationError, form_values,
                                form_values_from_request, get_profile, initials,
                                list_orders, update_profile, validate_profile)

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
    return render_template("account_orders.html", tab="orders", orders=list_orders(session["user_id"]))
