import hmac
import os
import uuid
from decimal import Decimal, InvalidOperation
from functools import wraps

import pyodbc
from dotenv import load_dotenv
from flask import (Flask, abort, flash, jsonify, redirect, render_template,
                   request, session, url_for)

# Import trực tiếp tất cả các hàm từ file db.py trong cùng thư mục
from db import (
    add_variant,
    create_brand,
    create_product,
    delete_brand,
    delete_product,
    delete_variant,
    get_all_products,
    get_all_products_admin,
    get_brands,
    get_brands_admin,
    get_categories,
    get_product_by_id,
    get_variant_by_attributes,
    get_variants,
    toggle_visibility,
    update_brand,
    update_stock,
get_categories_admin,
    create_category,
    update_category,
    delete_category,
    get_colors_admin,
    create_color,
    update_color,
    delete_color,
    get_sizes_admin,
    create_size,
    update_size,
    delete_size,
check_and_deduct_inventory,
    create_order,
    cancel_order,
check_duplicate_transaction,
    update_payment_status,
)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "chi-dung-khi-dev")
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # Ảnh tối đa 5 MB

ADMIN_PASSWORD = "minhdeptrai"
UPLOAD_DIR = os.path.join(app.static_folder, "uploads")
ALLOWED_EXT = {"jpg", "jpeg", "png", "webp"}
GENDERS = ("Nam", "Nữ", "Unisex")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ------------------------------------------------------------- Tiện ích
def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def save_image(file_storage):
    """Lưu ảnh vào static/uploads với tên ngẫu nhiên; trả về tên file hoặc None."""
    if not file_storage or not file_storage.filename:
        return None
    ext = file_storage.filename.rsplit(".", 1)[-1].lower() if "." in file_storage.filename else ""
    if ext not in ALLOWED_EXT:
        raise ValueError("Ảnh chỉ nhận định dạng jpg, jpeg, png hoặc webp.")
    name = f"{uuid.uuid4().hex}.{ext}"
    file_storage.save(os.path.join(UPLOAD_DIR, name))
    return name


def remove_image(name):
    if name:
        try:
            os.remove(os.path.join(UPLOAD_DIR, name))
        except OSError:
            pass


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapper


# ------------------------------------------------------------ Trang công khai
@app.route("/")
def index():
    return render_template("index.html", products=get_all_products())


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = get_product_by_id(product_id)
    if not product:
        abort(404)
    return render_template("product.html", product=product,
                           variants=get_variants(product_id))


# ---------------------------------------------------------------- Quản trị
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if ADMIN_PASSWORD and hmac.compare_digest(password.encode(), ADMIN_PASSWORD.encode()):
            session["is_admin"] = True
            return redirect(url_for("admin_products"))
        flash("Sai mật khẩu, hoặc chưa đặt ADMIN_PASSWORD trong file .env.", "error")
    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/admin")
@admin_required
def admin_products():
    return render_template("admin_products.html", products=get_all_products_admin())


def render_product_form(form):
    return render_template("admin_product_form.html", form=form,
                           categories=get_categories(), brands=get_brands(),
                           genders=GENDERS)


@app.route("/admin/product/new", methods=["GET", "POST"])
@admin_required
def admin_product_new():
    if request.method == "GET":
        return render_product_form({})

    f = request.form
    ten = f.get("ten", "").strip()
    mo_ta = f.get("mo_ta", "").strip() or None
    danh_muc_moi = f.get("danh_muc_moi", "").strip() or None
    thuong_hieu_moi = f.get("thuong_hieu_moi", "").strip() or None
    ma_danh_muc = to_int(f.get("ma_danh_muc"))
    ma_thuong_hieu = to_int(f.get("ma_thuong_hieu"))
    gioi_tinh = f.get("gioi_tinh", "Unisex")
    hien_thi = 1 if f.get("hien_thi") else 0

    try:
        gia = Decimal(f.get("gia", "").replace(",", "").strip())
    except InvalidOperation:
        gia = None

    errors = []
    if not ten or len(ten) > 200:
        errors.append("Nhập tên sản phẩm (tối đa 200 ký tự).")
    if gia is None or gia < 0:
        errors.append("Giá phải là số từ 0 trở lên.")
    if ma_danh_muc is None and not danh_muc_moi:
        errors.append("Chọn danh mục hoặc nhập danh mục mới.")
    if gioi_tinh not in GENDERS:
        errors.append("Giới tính không hợp lệ.")
    if (danh_muc_moi and len(danh_muc_moi) > 100) or (thuong_hieu_moi and len(thuong_hieu_moi) > 100):
        errors.append("Tên danh mục và thương hiệu tối đa 100 ký tự.")

    hinh_anh = None
    if not errors:
        try:
            hinh_anh = save_image(request.files.get("hinh_anh"))
        except ValueError as e:
            errors.append(str(e))

    if errors:
        for e in errors:
            flash(e, "error")
        return render_product_form(f)

    try:
        new_id = create_product(ten, gia, ma_danh_muc, danh_muc_moi, ma_thuong_hieu,
                                thuong_hieu_moi, gioi_tinh, mo_ta, hinh_anh, hien_thi)
    except pyodbc.Error:
        remove_image(hinh_anh)
        flash("Không lưu được sản phẩm. Kiểm tra lại danh mục và thương hiệu đã chọn.", "error")
        return render_product_form(f)

    flash("Đã thêm sản phẩm. Thêm size và màu cho sản phẩm ở bước này.", "ok")
    return redirect(url_for("admin_variants", product_id=new_id))


@app.route("/admin/product/<int:product_id>/toggle", methods=["POST"])
@admin_required
def admin_product_toggle(product_id):
    toggle_visibility(product_id)
    return redirect(url_for("admin_products"))


@app.route("/admin/product/<int:product_id>/delete", methods=["POST"])
@admin_required
def admin_product_delete(product_id):
    product = get_product_by_id(product_id, only_visible=False)
    if not product:
        abort(404)
    try:
        delete_product(product_id)
    except pyodbc.IntegrityError:
        flash("Sản phẩm đã nằm trong giỏ hàng hoặc đơn hàng nên không xóa được. Hãy ẩn sản phẩm.", "error")
    else:
        remove_image(product["HinhAnh"])
        flash("Đã xóa sản phẩm.", "ok")
    return redirect(url_for("admin_products"))


@app.route("/admin/product/<int:product_id>/variants", methods=["GET", "POST"])
@admin_required
def admin_variants(product_id):
    product = get_product_by_id(product_id, only_visible=False)
    if not product:
        abort(404)

    if request.method == "POST":
        size = request.form.get("kich_thuoc", "").strip()
        color = request.form.get("mau_sac", "").strip()
        stock = to_int(request.form.get("so_luong_ton"))

        if not size or not color or stock is None or len(size) > 30 or len(color) > 50:
            flash("Vui lòng nhập đầy đủ và hợp lệ Size, Màu và Số lượng.", "error")
        else:
            try:
                add_variant(product_id, size, color, stock)
                flash("Đã thêm biến thể.", "ok")
            except ValueError as ve:
                # Bắt chính xác lỗi Trùng lặp hoặc Tồn âm từ db.py trả ra
                flash(str(ve), "error")
            except pyodbc.IntegrityError:
                flash("Lỗi toàn vẹn dữ liệu từ CSDL.", "error")
        return redirect(url_for("admin_variants", product_id=product_id))
    return render_template("admin_variants.html", product=product,
                           variants=get_variants(product_id))


@app.route("/admin/product/<int:product_id>/variant/<int:variant_id>/stock", methods=["POST"])
@admin_required
def admin_variant_stock(product_id, variant_id):
    stock = to_int(request.form.get("so_luong_ton"))
    try:
        if stock is None:
            raise ValueError("Vui lòng nhập số lượng hợp lệ.")
        update_stock(product_id, variant_id, stock)
        flash("Đã lưu số lượng tồn.", "ok")
    except ValueError as ve:
        flash(str(ve), "error")
    return redirect(url_for("admin_variants", product_id=product_id))


@app.route("/admin/product/<int:product_id>/variant/<int:variant_id>/delete", methods=["POST"])
@admin_required
def admin_variant_delete(product_id, variant_id):
    try:
        delete_variant(product_id, variant_id)
        flash("Đã xóa biến thể.", "ok")
    except pyodbc.IntegrityError:
        flash("Biến thể đã nằm trong giỏ hàng hoặc đơn hàng nên không xóa được. Hãy đặt tồn kho về 0.", "error")
    return redirect(url_for("admin_variants", product_id=product_id))


# 1. NHIỆM VỤ W3-021: API CHỌN BIẾN THỂ (COLOR + SIZE)
@app.route("/api/product/select-variant", methods=["POST"])
def api_select_variant():
    data = request.get_json() or {}
    product_id = to_int(data.get("product_id"))
    size = str(data.get("size", "")).strip()
    color = str(data.get("color", "")).strip()

    if not product_id or not size or not color:
        return jsonify({"success": False, "message": "Thiếu thông tin tra cứu"}), 400

    variant = get_variant_by_attributes(product_id, size, color)

    if not variant:
        return jsonify({
            "success": False,
            "message": "Kích thước và màu sắc này hiện không có sẵn!"
        }), 404

    trang_thai = "Còn hàng" if variant["SoLuongTon"] > 0 else "Hết hàng"

    return jsonify({
        "success": True,
        "variant_id": variant["MaBienThe"],
        "stock_qty": variant["SoLuongTon"],
        "status": trang_thai,
        "price": variant["GiaBan"]
    }), 200


# 2. NHIỆM VỤ W3-022: CRUD THƯƠNG HIỆU (ADMIN)
@app.route("/admin/brands", methods=["GET", "POST"])
@admin_required
def admin_brands():
    search = request.args.get("q", "").strip()
    if request.method == "POST":
        ten_moi = request.form.get("ten_thuong_hieu", "").strip()
        if not ten_moi:
            flash("Tên thương hiệu không được để trống.", "error")
        else:
            try:
                create_brand(ten_moi)
                flash("Đã thêm thương hiệu thành công.", "ok")
                return redirect(url_for("admin_brands"))
            except ValueError as e:
                flash(str(e), "error")
            except pyodbc.Error:
                flash("Lỗi kết nối cơ sở dữ liệu.", "error")

    brands = get_brands_admin(search_query=search)
    return render_template("admin_brands.html", brands=brands, search=search)


@app.route("/admin/brand/<int:brand_id>/edit", methods=["POST"])
@admin_required
def admin_brand_edit(brand_id):
    ten_moi = request.form.get("ten_thuong_hieu", "").strip()
    if not ten_moi:
        flash("Tên thương hiệu không được để trống.", "error")
    else:
        try:
            update_brand(brand_id, ten_moi)
            flash("Cập nhật thương hiệu thành công.", "ok")
        except ValueError as id_err:
            flash(str(id_err), "error")
    return redirect(url_for("admin_brands"))


@app.route("/admin/brand/<int:brand_id>/delete", methods=["POST"])
@admin_required
def admin_brand_delete(brand_id):
    try:
        delete_brand(brand_id)
        flash("Đã xóa thương hiệu.", "ok")
    except pyodbc.IntegrityError:
        flash("Thương hiệu đang gắn với sản phẩm nên không thể xóa để tránh mồ côi dữ liệu!", "error")
    return redirect(url_for("admin_brands"))
# ----------------------------------------------------------------- 3. NHIỆM VỤ W3-034: CRUD DANH MỤC (ADMIN)
@app.route("/admin/categories", methods=["GET", "POST"])
@admin_required
def admin_categories():
    search = request.args.get("q", "").strip()
    if request.method == "POST":
        ten_moi = request.form.get("ten_danh_muc", "").strip()
        if not ten_moi:
            flash("Tên danh mục không được để trống.", "error")
        else:
            try:
                create_category(ten_moi)
                flash("Đã thêm danh mục thành công.", "ok")
                return redirect(url_for("admin_categories"))
            except ValueError as e:
                flash(str(e), "error")
            except pyodbc.Error:
                flash("Lỗi cơ sở dữ liệu.", "error")

    categories = get_categories_admin(search_query=search)
    return render_template("admin_categories.html", categories=categories, search=search)


@app.route("/admin/category/<int:category_id>/edit", methods=["POST"])
@admin_required
def admin_category_edit(category_id):
    ten_moi = request.form.get("ten_danh_muc", "").strip()
    if not ten_moi:
        flash("Tên danh mục không được để trống.", "error")
    else:
        try:
            update_category(category_id, ten_moi)
            flash("Cập nhật danh mục thành công.", "ok")
        except ValueError as err:
            flash(str(err), "error")
    return redirect(url_for("admin_categories"))


@app.route("/admin/category/<int:category_id>/delete", methods=["POST"])
@admin_required
def admin_category_delete(category_id):
    try:
        delete_category(category_id)
        flash("Đã xóa danh mục.", "ok")
    except pyodbc.IntegrityError:
        flash("Danh mục đang chứa sản phẩm nên không thể xóa!", "error")
    return redirect(url_for("admin_categories"))


# ----------------------------------------------------------------- 4. NHIỆM VỤ W3-035: CRUD MÀU SẮC (ADMIN)
@app.route("/admin/colors", methods=["GET", "POST"])
@admin_required
def admin_colors():
    search = request.args.get("q", "").strip()
    if request.method == "POST":
        ten_moi = request.form.get("ten_mau", "").strip()
        if not ten_moi:
            flash("Tên màu không được để trống.", "error")
        else:
            try:
                create_color(ten_moi)
                flash("Đã thêm màu thành công.", "ok")
                return redirect(url_for("admin_colors"))
            except ValueError as e:
                flash(str(e), "error")
            except pyodbc.Error:
                flash("Lỗi cơ sở dữ liệu.", "error")

    colors = get_colors_admin(search_query=search)
    return render_template("admin_colors.html", colors=colors, search=search)


@app.route("/admin/color/<int:color_id>/edit", methods=["POST"])
@admin_required
def admin_color_edit(color_id):
    ten_moi = request.form.get("ten_mau", "").strip()
    if not ten_moi:
        flash("Tên màu không được để trống.", "error")
    else:
        try:
            update_color(color_id, ten_moi)
            flash("Cập nhật màu thành công.", "ok")
        except ValueError as err:
            flash(str(err), "error")
    return redirect(url_for("admin_colors"))


@app.route("/admin/color/<int:color_id>/delete", methods=["POST"])
@admin_required
def admin_color_delete(color_id):
    try:
        delete_color(color_id)
        flash("Đã xóa màu sắc.", "ok")
    except pyodbc.IntegrityError:
        flash("Màu sắc đang được sử dụng bởi biến thể sản phẩm, không thể xóa!", "error")
    return redirect(url_for("admin_colors"))


# ----------------------------------------------------------------- 5. NHIỆM VỤ W3-036: CRUD KÍCH THƯỚC (ADMIN)
@app.route("/admin/sizes", methods=["GET", "POST"])
@admin_required
def admin_sizes():
    search = request.args.get("q", "").strip()
    if request.method == "POST":
        ten_moi = request.form.get("ten_size", "").strip()
        if not ten_moi:
            flash("Kích thước không được để trống.", "error")
        else:
            try:
                create_size(ten_moi)
                flash("Đã thêm kích thước thành công.", "ok")
                return redirect(url_for("admin_sizes"))
            except ValueError as e:
                flash(str(e), "error")
            except pyodbc.Error:
                flash("Lỗi cơ sở dữ liệu.", "error")

    sizes = get_sizes_admin(search_query=search)
    return render_template("admin_sizes.html", sizes=sizes, search=search)


@app.route("/admin/size/<int:size_id>/edit", methods=["POST"])
@admin_required
def admin_size_edit(size_id):
    ten_moi = request.form.get("ten_size", "").strip()
    if not ten_moi:
        flash("Kích thước không được để trống.", "error")
    else:
        try:
            update_size(size_id, ten_moi)
            flash("Cập nhật kích thước thành công.", "ok")
        except ValueError as err:
            flash(str(err), "error")
    return redirect(url_for("admin_sizes"))


@app.route("/admin/size/<int:size_id>/delete", methods=["POST"])
@admin_required
def admin_size_delete(size_id):
    try:
        delete_size(size_id)
        flash("Đã xóa kích thước.", "ok")
    except pyodbc.IntegrityError:
        flash("Kích thước đang được sử dụng bởi biến thể sản phẩm, không thể xóa!", "error")
    return redirect(url_for("admin_sizes"))


# =================================================================
# NHIỆM VỤ W4-008: API TẠO VÀ HỦY ĐƠN HÀNG (Dành cho UI của Tuấn)
# =================================================================

@app.route("/api/order/checkout", methods=["POST"])
def api_checkout():
    """Nhận dữ liệu giỏ hàng, validate và tạo đơn hàng."""
    data = request.get_json() or {}

    ho_ten = data.get("ho_ten", "").strip()
    so_dien_thoai = data.get("so_dien_thoai", "").strip()
    dia_chi = data.get("dia_chi", "").strip()
    items = data.get("items", [])  # Mảng chứa: variant_id, quantity, price

    # 1. Validate Input (DoD: Không tạo đơn khi dữ liệu sai)
    if not items or len(items) == 0:
        return jsonify({"success": False, "message": "Giỏ hàng trống!"}), 400
    if not ho_ten or not so_dien_thoai or not dia_chi:
        return jsonify(
            {"success": False, "message": "Vui lòng nhập đầy đủ họ tên, số điện thoại và địa chỉ nhận hàng!"}), 400

    # 2. Gọi Mock Interface kiểm tra tồn kho (chờ Minh ghép)
    is_valid_stock, stock_msg = check_and_deduct_inventory(items)
    if not is_valid_stock:
        return jsonify({"success": False, "message": f"Lỗi tồn kho: {stock_msg}"}), 400

    # Tính tổng tiền (Tuấn sẽ gửi lên hoặc Backend tự tính lại, ở đây ví dụ Backend tự tính)
    tong_tien = sum(Decimal(str(item.get("price", 0))) * int(item.get("quantity", 0)) for item in items)

    # 3. Thực thi tạo đơn và Snapshot
    try:
        new_order_id = create_order(ho_ten, so_dien_thoai, dia_chi, tong_tien, items)
        return jsonify({
            "success": True,
            "message": "Đặt hàng thành công, đang chờ xác nhận.",
            "order_id": new_order_id
        }), 201
    except Exception as e:
        return jsonify({"success": False, "message": "Lỗi hệ thống khi lưu đơn hàng nửa chừng. Vui lòng thử lại!"}), 500


@app.route("/api/order/cancel/<int:order_id>", methods=["POST"])
def api_cancel_order(order_id):
    """Xử lý yêu cầu hủy đơn từ khách hàng."""
    try:
        is_cancelled = cancel_order(order_id)
        if is_cancelled:
            # Lưu ý: Khi Minh hoàn thiện DB, ở đây sẽ phải gọi thêm hàm hoàn lại số lượng tồn kho.
            return jsonify({"success": True, "message": "Đã hủy đơn hàng thành công!"}), 200
        else:
            return jsonify({
                "success": False,
                "message": "Không thể hủy! Đơn hàng này đã được xác nhận hoặc đang vận chuyển."
            }), 403
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 404
    # =================================================================
    # NHIỆM VỤ W4-013: API THANH TOÁN ONLINE SANDBOX (Dành cho UI)
    # =================================================================
    import hashlib

    # Cấu hình giả lập (Sandbox Credentials)
    SANDBOX_SECRET = "chi-dung-de-test-thanh-toan"

    @app.route("/api/payment/create_url", methods=["POST"])
    def api_create_payment_url():
        """Sinh URL chuyển hướng người dùng sang cổng thanh toán Sandbox"""
        data = request.get_json() or {}
        order_id = to_int(data.get("order_id"))
        amount = data.get("amount")
        payment_method = data.get("payment_method", "").strip()

        if not order_id or not amount:
            return jsonify({"success": False, "message": "Thiếu thông tin đơn hàng."}), 400

        # DoD: Không coi chuyển khoản thủ công (bank_transfer) là online
        if payment_method == "bank_transfer":
            return jsonify({
                "success": True,
                "message": "Vui lòng chuyển khoản theo cú pháp và chờ Admin xác nhận.",
                "is_online": False
            }), 200

        # Giả lập tạo URL thanh toán (Ví dụ VNPay Sandbox)
        # Thực tế sẽ dùng thư viện mã hóa HMAC SHA512 với secret key
        transaction_id = f"TXN{uuid.uuid4().hex[:8].upper()}"
        secure_hash = hashlib.sha256(f"{order_id}|{amount}|{transaction_id}|{SANDBOX_SECRET}".encode()).hexdigest()

        sandbox_url = f"http://127.0.0.1:5000/sandbox_gateway?order_id={order_id}&amount={amount}&txn={transaction_id}&hash={secure_hash}"

        return jsonify({
            "success": True,
            "is_online": True,
            "payment_url": sandbox_url
        }), 200

    @app.route("/api/payment/callback", methods=["POST"])
    def api_payment_callback():
        """
        IPN/Callback từ cổng thanh toán gọi về Server.
        Xác minh chữ ký và xử lý chống trùng lặp.
        """
        data = request.get_json() or {}
        order_id = data.get("order_id")
        transaction_id = data.get("txn")
        response_code = data.get("response_code")  # "00" = thành công
        secure_hash = data.get("hash")
        amount = data.get("amount")

        # 1. Xác minh chữ ký (Bằng chứng Transaction/Verify theo DoD)
        expected_hash = hashlib.sha256(f"{order_id}|{amount}|{transaction_id}|{SANDBOX_SECRET}".encode()).hexdigest()
        if secure_hash != expected_hash:
            return jsonify({"success": False, "message": "Chữ ký không hợp lệ (Invalid Signature)"}), 400

        # 2. Chống ghi trùng Callback lặp (DoD)
        if check_duplicate_transaction(transaction_id):
            return jsonify({"success": True, "message": "Giao dịch đã được xử lý từ trước"}), 200

        # 3. Cập nhật trạng thái
        is_success = (response_code == "00")
        update_payment_status(order_id, transaction_id, is_success)

        return jsonify({"success": True, "message": "Cập nhật thanh toán thành công"}), 200


if __name__ == "__main__":
    app.run(debug=True)