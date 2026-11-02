"""Một bộ route duy nhất; thay các app.py trùng nhau trong ZIP nguồn."""
import secrets
from functools import wraps
from urllib.parse import urlsplit
from flask import (abort, flash, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash
from .data import (get_all_products, get_categories, get_product_by_id,
                   get_products_by_category, get_variants)
from .db import get_db_connection, query_one


def register_routes(app):
    @app.before_request
    def prepare_csrf():
        if "_csrf" not in session:
            session["_csrf"] = secrets.token_hex(20)
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            if not secrets.compare_digest(session["_csrf"], request.form.get("csrf_token", "")):
                abort(400, description="Biểu mẫu đã hết hạn hoặc thiếu mã xác thực.")

    @app.context_processor
    def inject_common():
        return {"categories": get_categories(), "csrf_token": session.get("_csrf", "")}

    def admin_required(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login", next=request.path))
            if session.get("role") != "Admin":
                abort(403)
            return view(*args, **kwargs)
        return wrapper

    @app.get("/")
    def home():
        keyword = request.args.get("q", "", type=str).strip()[:80]
        products = get_all_products(keyword=keyword)
        return render_template("index.html", products=products, keyword=keyword)

    @app.get("/category/<int:category_id>")
    def category(category_id):
        selected = next((d for d in get_categories() if d["MaDanhMuc"] == category_id), None)
        if selected is None:
            abort(404)
        return render_template("category.html", products=get_products_by_category(category_id), selected=selected)

    @app.get("/product/<int:product_id>")
    def product_detail(product_id):
        product = get_product_by_id(product_id)
        if not product:
            abort(404)
        return render_template("product_detail.html", product=product, variants=get_variants(product_id))

    @app.post("/add-to-cart/<int:product_id>")
    def add_to_cart(product_id):
        if not get_product_by_id(product_id):
            abort(404)
        try:
            variant_id = int(request.form.get("variant_id", ""))
            qty = int(request.form.get("quantity", "1"))
        except ValueError:
            abort(400, description="Size hoặc số lượng không hợp lệ")
        if qty < 1 or qty > 99:
            abort(400, description="Số lượng phải từ 1 đến 99")
        variant = query_one("SELECT MaBienThe, SoLuongTon FROM BienTheSanPham WHERE MaBienThe=? AND MaSanPham=?", (variant_id, product_id))
        if not variant:
            abort(400, description="Vui lòng chọn size và màu hợp lệ")
        cart = session.get("cart", {}).copy()
        current = int(cart.get(str(variant_id), 0))
        if current + qty > int(variant["SoLuongTon"]):
            flash("Không đủ tồn kho cho size/màu đã chọn.", "warning")
            return redirect(url_for("product_detail", product_id=product_id))
        cart[str(variant_id)] = current + qty
        session["cart"] = cart
        flash("Đã thêm sản phẩm vào giỏ hàng.", "success")
        return redirect(url_for("view_cart"))

    def build_cart():
        basket = session.get("cart", {})
        ids = [int(x) for x in basket if str(x).isdigit()]
        if not ids:
            return [], 0
        placeholders = ",".join("?" for _ in ids)
        from .db import query_all
        rows = query_all("""SELECT bt.MaBienThe, bt.KichThuoc, bt.MauSac, bt.SoLuongTon,
           sp.MaSanPham, sp.TenSanPham, sp.GiaBan FROM BienTheSanPham bt
           JOIN SanPham sp ON bt.MaSanPham=sp.MaSanPham
           WHERE bt.MaBienThe IN (""" + placeholders + ")", tuple(ids))
        total = 0
        for row in rows:
            row["quantity"] = int(basket.get(str(row["MaBienThe"]), 0))
            row["subtotal"] = float(row["GiaBan"]) * row["quantity"]
            total += row["subtotal"]
        return rows, total

    @app.get("/cart")
    def view_cart():
        items, total = build_cart()
        return render_template("cart.html", cart_items=items, total=total)

    @app.post("/cart/remove/<int:variant_id>")
    def remove_from_cart(variant_id):
        cart = session.get("cart", {}).copy()
        cart.pop(str(variant_id), None)
        session["cart"] = cart
        return redirect(url_for("view_cart"))

    @app.get("/checkout")
    def checkout():
        items, total = build_cart()
        if not items:
            return redirect(url_for("view_cart"))
        return render_template("checkout.html", cart_items=items, total=total)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()[:150]
            password = request.form.get("password", "")
            account = query_one("""SELECT nd.MaNguoiDung, nd.HoVaTen, nd.MatKhauHash, nd.TrangThai, vt.TenVaiTro
              FROM NguoiDung nd JOIN VaiTro vt ON vt.MaVaiTro=nd.MaVaiTro WHERE nd.Email=?""", (email,))
            if not account or not account["TrangThai"] or not check_password_hash(account["MatKhauHash"], password):
                flash("Email hoặc mật khẩu chưa đúng.", "warning")
            else:
                keep_cart = session.get("cart", {})
                session.clear()
                session["_csrf"] = secrets.token_hex(20)
                session["user_id"] = int(account["MaNguoiDung"])
                session["user_name"] = account["HoVaTen"]
                session["role"] = account["TenVaiTro"]
                session["cart"] = keep_cart
                target = request.form.get("next", "")
                # Chỉ điều hướng nội bộ, ngăn open redirect.
                if target.startswith("/") and not target.startswith("//") and not urlsplit(target).netloc:
                    return redirect(target)
                return redirect(url_for("admin_dashboard") if session["role"] == "Admin" else url_for("home"))
        return render_template("login.html", next_path=request.values.get("next", ""))

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            name = request.form.get("full_name", "").strip()[:100]
            email = request.form.get("email", "").strip().lower()[:150]
            password = request.form.get("password", "")
            if len(name) < 2 or "@" not in email or "." not in email.split("@")[-1] or len(password) < 8:
                flash("Nhập họ tên, email hợp lệ và mật khẩu từ 8 ký tự.", "warning")
            elif query_one("SELECT MaNguoiDung FROM NguoiDung WHERE Email=?", (email,)):
                flash("Email này đã được đăng ký.", "warning")
            else:
                conn = get_db_connection()
                try:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO NguoiDung(MaVaiTro,HoVaTen,Email,MatKhauHash) VALUES(?,?,?,?)",
                                   (3, name, email, generate_password_hash(password)))
                    conn.commit()
                    flash("Đăng ký thành công. Hãy đăng nhập.", "success")
                    return redirect(url_for("login"))
                except Exception:
                    conn.rollback()
                    app.logger.exception("Lỗi tạo tài khoản")
                    flash("Chưa thể tạo tài khoản; vui lòng kiểm tra thông tin.", "warning")
                finally:
                    conn.close()
        return render_template("register.html")

    @app.post("/logout")
    def logout():
        session.clear()
        flash("Đã đăng xuất.", "success")
        return redirect(url_for("home"))

    @app.get("/admin")
    @admin_required
    def admin_dashboard():
        return render_template("admin/index.html", products=get_all_products())

    @app.route("/admin/product/add", methods=["GET", "POST"])
    @admin_required
    def admin_product_add():
        if request.method == "POST":
            try:
                price = float(request.form.get("price", ""))
                stock = int(request.form.get("stock", ""))
                category_id = int(request.form.get("category_id", ""))
            except ValueError:
                flash("Giá, số lượng tồn hoặc danh mục không đúng.", "warning")
            else:
                name = request.form.get("name", "").strip()
                image = request.form.get("image", "").strip()
                valid_category = category_id in {c["MaDanhMuc"] for c in get_categories()}
                if name and price >= 0 and stock >= 0 and valid_category and image:
                    flash("Biểu mẫu đạt kiểm tra đầu vào. Tuần 2 mới chuẩn bị form, CHƯA lưu sản phẩm.", "success")
                else:
                    flash("Điền đủ tên, giá, tồn kho, danh mục và tên ảnh.", "warning")
        return render_template("admin/product_add.html")

    @app.errorhandler(400)
    def bad_request(error):
        return render_template("error.html", code=400, message="Yêu cầu không hợp lệ", detail=str(error.description)), 400

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("error.html", code=403, message="Bạn không có quyền truy cập", detail="Vui lòng đăng nhập bằng quyền quản lý."), 403

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        app.logger.exception("Lỗi server")
        return render_template("500.html"), 500
