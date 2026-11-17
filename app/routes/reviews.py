"""Đánh giá sản phẩm: gửi đánh giá (Customer) và kiểm duyệt/phản hồi (Admin, Seller).

Luồng HTML form: flash + redirect. Luồng API (Accept/Content-Type JSON): JSON {error, code}
với đúng mã HTTP 400/401/403/404/409. CSRF được kiểm tra chung ở before_request.
"""
from functools import wraps

from flask import (Blueprint, abort, flash, jsonify, redirect, render_template,
                   request, session, url_for)

from ..data import get_product_by_id
from ..services import reviews as svc

reviews = Blueprint("reviews", __name__)


def _wants_json():
    return request.is_json or request.accept_mimetypes.best == "application/json"


def _fail(code, message, target):
    if _wants_json():
        return jsonify({"error": message, "code": code}), code
    flash(message, "warning")
    return redirect(target)


def _payload():
    if request.is_json:
        data = request.get_json(silent=True)
        return data if isinstance(data, dict) else {}
    return request.form


def _product_url(product_id, anchor=True):
    url = url_for("product_detail", product_id=product_id)
    return url + "#reviews" if anchor else url


def staff_required(view):
    """Guest -> 401 (JSON) hoặc về trang đăng nhập; vai trò khác Admin/Seller -> 403."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            if _wants_json():
                return jsonify({"error": "Vui lòng đăng nhập.", "code": 401}), 401
            return redirect(url_for("login", next=request.path))
        if session.get("role") not in ("Admin", "Seller"):
            abort(403)
        return view(*args, **kwargs)
    return wrapper


@reviews.post("/product/<int:product_id>/reviews")
def submit_review(product_id):
    target = _product_url(product_id)
    if not session.get("user_id"):
        if _wants_json():
            return jsonify({"error": "Vui lòng đăng nhập để đánh giá sản phẩm.", "code": 401}), 401
        flash("Vui lòng đăng nhập để đánh giá sản phẩm.", "warning")
        return redirect(url_for("login", next=target))
    if session.get("role") != "Customer":
        return _fail(403, "Chỉ khách hàng mới có thể đánh giá sản phẩm.", target)
    if not get_product_by_id(product_id):
        abort(404)
    try:
        data = svc.parse_review_input(_payload())
        review_id = svc.create_review(int(session["user_id"]), product_id, data)
    except svc.ReviewError as err:
        return _fail(err.code, err.message, target)
    if _wants_json():
        return jsonify({"message": "Cảm ơn bạn đã đánh giá sản phẩm.", "review_id": review_id}), 201
    flash("Cảm ơn bạn! Đánh giá của bạn đã được đăng.", "success")
    return redirect(target)


@reviews.get("/admin/reviews")
@staff_required
def admin_reviews():
    status = request.args.get("status", "", type=str).strip()
    if status not in ("", "0", "1"):
        abort(400, description="Trạng thái lọc không hợp lệ.")
    try:
        rating = int(request.args.get("rating", ""))
    except (TypeError, ValueError):
        rating = None
    if rating is not None and not 1 <= rating <= 5:
        abort(400, description="Số sao lọc không hợp lệ.")
    keyword = request.args.get("q", "", type=str).strip()[:80]
    return render_template("admin/reviews.html", items=svc.list_reviews_admin(status, rating, keyword),
                           status=status, rating=rating, keyword=keyword)


@reviews.post("/admin/reviews/<int:review_id>/toggle")
@staff_required
def toggle_review(review_id):
    target = url_for("reviews.admin_reviews")
    try:
        state = svc.toggle_review(review_id, _payload().get("phan_hoi_shop"))
    except svc.ReviewError as err:
        if err.code == 404:
            abort(404)
        return _fail(err.code, err.message, target)
    msg = "Đã hiển thị lại đánh giá." if state else "Đã ẩn đánh giá khỏi trang công khai."
    if _wants_json():
        return jsonify({"message": msg, "hien_thi": state}), 200
    flash(msg, "success")
    return redirect(target)


@reviews.post("/admin/reviews/<int:review_id>/reply")
@staff_required
def reply_review(review_id):
    target = url_for("reviews.admin_reviews")
    try:
        svc.reply_review(review_id, _payload().get("phan_hoi_shop"))
    except svc.ReviewError as err:
        if err.code == 404:
            abort(404)
        return _fail(err.code, err.message, target)
    if _wants_json():
        return jsonify({"message": "Đã lưu phản hồi của shop."}), 200
    flash("Đã lưu phản hồi của shop.", "success")
    return redirect(target)
