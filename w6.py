from functools import wraps
from flask import (
    Blueprint, abort, flash, jsonify, redirect, render_template,
    request, Response, session, url_for
)
from app.services import w6_features as w6

w6_bp = Blueprint("w6", __name__)


def _current_user_id():
    return session.get("user_id")


def _is_admin():
    return session.get("role") in ("Admin", "Seller")


def login_required_w6(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not _current_user_id():
            flash("Vui lòng đăng nhập để thực hiện chức năng này.", "warning")
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)
    return wrapper


def admin_required_w6(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not _current_user_id():
            return redirect(url_for("login", next=request.path))
        if not _is_admin():
            abort(403)
        return fn(*args, **kwargs)
    return wrapper


def current_app_endpoints():
    from flask import current_app
    return set(current_app.view_functions.keys())


# -------------------- 1. ROUTES ĐÁNH GIÁ SẢN PHẨM --------------------

@w6_bp.route("/products/<int:product_id>/reviews", methods=["POST"])
@login_required_w6
def post_product_review(product_id):
    user_id = _current_user_id()
    rating = int(request.form.get("rating") or 0)
    comment = request.form.get("comment") or ""
    ok, msg = w6.submit_product_review(user_id, product_id, rating, comment)
    flash(msg, "success" if ok else "danger")
    return redirect(request.referrer or f"/products/{product_id}")


@w6_bp.route("/admin/w6/reviews")
@admin_required_w6
def admin_reviews():
    reviews = w6.admin_list_reviews()
    return render_template("w6/admin_reviews.html", reviews=reviews)


@w6_bp.route("/admin/w6/reviews/<int:review_id>/toggle", methods=["POST"])
@admin_required_w6
def admin_toggle_review(review_id):
    ok, msg = w6.admin_toggle_review(review_id)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("w6.admin_reviews"))


@w6_bp.route("/admin/w6/reviews/<int:review_id>/delete", methods=["POST"])
@admin_required_w6
def admin_delete_review(review_id):
    ok, msg = w6.admin_delete_review(review_id)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("w6.admin_reviews"))


# -------------------- 2. ROUTES & API MÃ GIẢM GIÁ (VOUCHER) --------------------

@w6_bp.route("/api/w6/voucher/apply", methods=["POST"])
def api_apply_voucher():
    data = request.form
    code = (data.get("code") or "").strip().upper()
    subtotal = float(data.get("subtotal") or 0)
    user_id = _current_user_id()

    if not code:
        session.pop("applied_voucher", None)
        return jsonify({"ok": True, "message": "Đã gỡ mã giảm giá.", "discount": 0, "final_total": subtotal})

    ok, msg, discount, voucher = w6.validate_and_calculate_voucher(code, subtotal, user_id)
    if not ok:
        session.pop("applied_voucher", None)
        return jsonify({"ok": False, "message": msg, "discount": 0, "final_total": subtotal}), 400

    session["applied_voucher"] = {
        "code": voucher["code"],
        "title": voucher["title"],
        "discount": discount,
    }
    return jsonify({
        "ok": True,
        "message": msg,
        "code": voucher["code"],
        "discount": discount,
        "final_total": max(0.0, subtotal - discount),
    })


@w6_bp.route("/admin/w6/vouchers", methods=["GET", "POST"])
@admin_required_w6
def admin_vouchers():
    if request.method == "POST":
        voucher_id = request.form.get("voucher_id")
        vid = int(voucher_id) if voucher_id else None
        ok, msg = w6.admin_save_voucher(request.form, vid)
        flash(msg, "success" if ok else "danger")
        return redirect(url_for("w6.admin_vouchers"))

    vouchers = w6.admin_list_vouchers()
    return render_template("w6/admin_vouchers.html", vouchers=vouchers)


@w6_bp.route("/admin/w6/vouchers/<int:voucher_id>/toggle", methods=["POST"])
@admin_required_w6
def admin_toggle_voucher(voucher_id):
    ok, msg = w6.admin_toggle_voucher(voucher_id)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("w6.admin_vouchers"))


# -------------------- 3. ROUTES ĐỔI TRẢ / HOÀN TIỀN --------------------

@w6_bp.route("/orders/<int:order_id>/return", methods=["POST"])
@login_required_w6
def submit_order_return(order_id):
    user_id = _current_user_id()
    req_type = request.form.get("request_type") or "RETURN"
    reason = request.form.get("reason") or ""
    evidence_url = request.form.get("evidence_url") or ""
    ok, msg = w6.create_order_return_request(order_id, user_id, req_type, reason, evidence_url)
    flash(msg, "success" if ok else "danger")
    return redirect(request.referrer or f"/orders/{order_id}")


@w6_bp.route("/admin/w6/returns")
@admin_required_w6
def admin_returns():
    returns = w6.admin_list_returns()
    return render_template("w6/admin_returns.html", returns=returns)


@w6_bp.route("/admin/w6/returns/<int:return_id>/process", methods=["POST"])
@admin_required_w6
def admin_process_return(return_id):
    action = request.form.get("action")
    admin_note = request.form.get("admin_note") or ""
    ok, msg = w6.admin_process_return(return_id, action, admin_note)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("w6.admin_returns"))


# -------------------- 4. ROUTES BÁO CÁO THỐNG KÊ & XUẤT CSV --------------------

@w6_bp.route("/admin/w6/reports")
@admin_required_w6
def admin_reports():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    report = w6.get_revenue_report(start_date, end_date)
    return render_template("w6/admin_reports.html", report=report)


@w6_bp.route("/admin/w6/reports/export.csv")
@admin_required_w6
def export_reports_csv():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    csv_bytes = w6.export_revenue_csv(start_date, end_date)
    filename = f"bao_cao_doanh_thu_{start_date or '30ngay'}_{end_date or 'homnay'}.csv"
    return Response(
        csv_bytes,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )