"""Một bộ route duy nhất; thay các app.py trùng nhau trong ZIP nguồn."""
import secrets
from functools import wraps
from urllib.parse import urlsplit
from flask import (abort, flash, redirect, render_template, request,
                   session, url_for, jsonify, current_app)
from werkzeug.security import check_password_hash, generate_password_hash
from ..data import (get_all_products, get_categories, get_product_by_id,
                   get_products_by_category, get_variants)
from ..db import get_db_connection, query_one, query_all
from ..services.checkout import create_pending_order, validate_checkout, CheckoutValidationError
from ..services.account import checkout_defaults, get_profile, has_default_contact, save_checkout_defaults
from ..services.new_arrivals import get_latest_products
from ..services.best_sellers import get_best_selling_products


def register_routes(app):
    @app.before_request
    def prepare_csrf():
        if "_csrf" not in session:
            session["_csrf"] = secrets.token_hex(20)
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            if not secrets.compare_digest(session["_csrf"], request.form.get("csrf_token", "")):
                abort(400, description="Biểu mẫu đã hết hạn hoặc thiếu mã xác thực.")

    @app.before_request
    def enforce_active_session():
        # Các test contract W4 cũ cố ý tạo session giả không gắn tài khoản DB.
        # Ở môi trường chạy thực, tài khoản bị khóa phải mất quyền ngay cả với cookie cũ.
        if session.get('user_id') and (not app.config.get('TESTING') or
                                       app.config.get('FORCE_ACCOUNT_STATUS_GUARD')):
            try:
                user = query_one('SELECT TrangThai FROM NguoiDung WHERE MaNguoiDung=?',
                                 (session['user_id'],))
            except Exception:
                app.logger.exception('Không thể xác thực trạng thái phiên đăng nhập')
                abort(503)
            if not user or not user['TrangThai']:
                session.clear()
                flash('Tài khoản đã bị khóa hoặc không còn tồn tại.', 'warning')
                return redirect(url_for('login'))

    @app.context_processor
    def inject_common():
        favorites_ui = {}
        if session.get("role") == "Customer" and session.get("user_id"):
            try:
                saved = {int(r["MaSanPham"]) for r in query_all(
                    "SELECT MaSanPham FROM YeuThich WHERE MaNguoiDung=?", (session["user_id"],))}
                for row in query_all("SELECT MaSanPham FROM SanPham WHERE HienThi=1"):
                    pid = int(row["MaSanPham"])
                    endpoint = url_for("toggle_favorite", product_id=pid)
                    favorites_ui[pid] = {"saved": pid in saved, "save_url": endpoint, "remove_url": endpoint}
            except Exception:
                # The UI stays disabled until SQL Server migration is verified.
                app.logger.warning("YeuThich chưa sẵn sàng; kiểm tra migration W3", exc_info=True)
        return {"categories": get_categories(), "csrf_token": session.get("_csrf", ""),
                "favorites_ui": favorites_ui}

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
        catalog = get_all_products()
        products = get_all_products(keyword=keyword) if keyword else catalog
        # Slide "giới thiệu sản phẩm" trên banner: sản phẩm hiển thị mới nhất.
        in_stock = [p for p in catalog if int(p["TongTon"]) > 0] or catalog
        featured = max(in_stock, key=lambda p: p["MaSanPham"]) if in_stock else None
        # Trang chủ chỉ nhận dữ liệu thật; rỗng được xử lý trong partial.
        latest_products = get_latest_products()
        best_selling_products = get_best_selling_products()
        return render_template("index.html", products=products, keyword=keyword,
                               featured=featured, latest_products=latest_products,
                               best_selling_products=best_selling_products)

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
        images = query_all("SELECT TenTep, LaAnhDaiDien, ThuTu FROM SanPhamHinhAnh WHERE MaSanPham=? ORDER BY LaAnhDaiDien DESC, ThuTu, MaHinhAnh", (product_id,))
        product_images = [{'filename': 'uploads/products/' + x['TenTep'], 'is_cover': bool(x['LaAnhDaiDien']), 'alt': product['TenSanPham']} for x in images]
        return render_template("product_detail.html", product=product, variants=get_variants(product_id), product_images=product_images)

    @app.get("/api/products/<int:product_id>/variants")
    def api_product_variants(product_id):
        """W3-021: public read-only endpoint; color/size validated on same variant row."""
        if not get_product_by_id(product_id):
            abort(404)
        color = request.args.get("color", "", type=str).strip()
        size = request.args.get("size", "", type=str).strip()
        if len(color) > 50 or len(size) > 30:
            abort(400)
        cond = ["MaSanPham=?"]
        args = [product_id]
        if color:
            cond.append("MauSac=?"); args.append(color)
        if size:
            cond.append("KichThuoc=?"); args.append(size)
        rows = query_all("SELECT MaBienThe, MaSanPham, MauSac, KichThuoc, SoLuongTon "
                         "FROM BienTheSanPham WHERE " + " AND ".join(cond) +
                         " ORDER BY MauSac,KichThuoc", tuple(args))
        return jsonify({"product_id": product_id, "variants": rows})

    @app.post("/favorites/<int:product_id>/toggle")
    def toggle_favorite(product_id):
        """W3-057: ownership is derived only from authenticated session."""
        user_id = session.get("user_id")
        if not user_id:
            return redirect(url_for("login", next=url_for("product_detail", product_id=product_id)))
        if session.get("role") != "Customer":
            abort(403)
        if not get_product_by_id(product_id):
            abort(404)
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT MaSanPham FROM YeuThich WHERE MaNguoiDung=? AND MaSanPham=?", (user_id, product_id))
            if cur.fetchone():
                cur.execute("DELETE FROM YeuThich WHERE MaNguoiDung=? AND MaSanPham=?", (user_id, product_id))
                msg = "Đã bỏ yêu thích."
            else:
                cur.execute("INSERT INTO YeuThich(MaNguoiDung,MaSanPham) VALUES(?,?)", (user_id, product_id))
                msg = "Đã lưu yêu thích."
            conn.commit()
        except Exception:
            conn.rollback()
            current_app.logger.exception("Lỗi lưu yêu thích; kiểm tra migration YeuThich")
            flash("Chưa thể lưu yêu thích; cần kiểm tra migration cơ sở dữ liệu.", "warning")
        else:
            flash(msg, "success")
        finally:
            conn.close()
        return redirect(url_for("product_detail", product_id=product_id))

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

    @app.post("/buy-now/<int:product_id>")
    def buy_now(product_id):
        """Mua ngay: đi thẳng tới thanh toán, KHÔNG thêm vào giỏ hàng và không đụng giỏ đang có."""
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
        if qty > int(variant["SoLuongTon"]):
            flash("Không đủ tồn kho cho size/màu đã chọn.", "warning")
            return redirect(url_for("product_detail", product_id=product_id))
        session["buy_now"] = {str(variant_id): qty}
        return redirect(url_for("checkout", buy_now=1))

    def build_cart(basket=None):
        if basket is None:
            basket = session.get("cart", {})
        ids = [int(x) for x in basket if str(x).isdigit()]
        if not ids:
            return [], 0
        placeholders = ",".join("?" for _ in ids)
        from ..db import query_all
        rows = query_all("""SELECT bt.MaBienThe, bt.KichThuoc, bt.MauSac, bt.SoLuongTon,
           sp.MaSanPham, sp.TenSanPham, sp.GiaBan, sp.HienThi, (SELECT TenTep FROM SanPhamHinhAnh ia WHERE ia.MaSanPham=sp.MaSanPham AND ia.LaAnhDaiDien=1) AS AnhDaiDien FROM BienTheSanPham bt
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

    @app.post("/cart/update/<int:variant_id>")
    def update_cart_item(variant_id):
        try:
            qty = int(request.form.get("quantity", "1"))
        except (ValueError, TypeError):
            abort(400, description="Số lượng không hợp lệ")
        cart = session.get("cart", {}).copy()
        if qty <= 0:
            cart.pop(str(variant_id), None)
            flash("Đã xóa sản phẩm khỏi giỏ hàng.", "success")
        else:
            variant = query_one("""SELECT bt.SoLuongTon, sp.TenSanPham, sp.HienThi
                                   FROM BienTheSanPham bt
                                   JOIN SanPham sp ON sp.MaSanPham=bt.MaSanPham
                                   WHERE bt.MaBienThe=?""", (variant_id,))
            if not variant:
                abort(404)
            if not bool(variant["HienThi"]):
                cart.pop(str(variant_id), None)
                flash(f"Sản phẩm '{variant['TenSanPham']}' hiện đã ngừng kinh doanh và được xóa khỏi giỏ.", "warning")
            elif qty > int(variant["SoLuongTon"]):
                cart[str(variant_id)] = int(variant["SoLuongTon"])
                flash(f"Kho chỉ còn {variant['SoLuongTon']} sản phẩm cho mẫu '{variant['TenSanPham']}'. Đã cập nhật theo số lượng tối đa.", "warning")
            else:
                cart[str(variant_id)] = min(qty, 99)
                flash("Đã cập nhật số lượng trong giỏ hàng.", "success")
        session["cart"] = cart
        return redirect(url_for("view_cart"))

    @app.post("/cart/remove/<int:variant_id>")
    def remove_from_cart(variant_id):
        cart = session.get("cart", {}).copy()
        cart.pop(str(variant_id), None)
        session["cart"] = cart
        flash("Đã xóa sản phẩm khỏi giỏ hàng.", "success")
        return redirect(url_for("view_cart"))

    @app.route("/checkout", methods=["GET", "POST"])
    def checkout():
        buy_now_mode = request.values.get("buy_now") == "1" and bool(session.get("buy_now"))
        basket = session.get("buy_now") if buy_now_mode else session.get("cart", {})
        items, total = build_cart(basket)
        if not items:
            return redirect(url_for("view_cart"))

        # Bắt buộc đăng nhập nếu cấu hình REQUIRE_LOGIN_TO_CHECKOUT được bật
        user_id = session.get("user_id")
        if app.config.get("REQUIRE_LOGIN_TO_CHECKOUT", False) and not user_id:
            flash("Vui lòng đăng nhập tài khoản trước khi tiến hành đặt hàng.", "warning")
            next_url = url_for("checkout", buy_now=1 if buy_now_mode else None)
            return redirect(url_for("login", next=next_url))

        # Kiểm tra trạng thái tài khoản đang hoạt động (chặn phiên cũ của tài khoản bị khóa)
        if user_id:
            user_acc = query_one("SELECT TrangThai FROM NguoiDung WHERE MaNguoiDung=?", (user_id,))
            if not user_acc or not user_acc["TrangThai"]:
                session.clear()
                flash("Tài khoản của bạn đã bị khóa. Không thể thực hiện đặt hàng.", "warning")
                return redirect(url_for("login"))

        # Kiểm tra sản phẩm ngừng bán / tạm ẩn
        hidden_items = [it for it in items if not bool(it.get("HienThi", 1))]
        if hidden_items:
            names = ", ".join(f"'{x['TenSanPham']}'" for x in hidden_items)
            flash(f"Sản phẩm {names} hiện đang tạm ẩn hoặc ngừng kinh doanh. Vui lòng xóa khỏi giỏ hàng trước khi đặt hàng.", "warning")
            if request.method == "POST":
                return redirect(url_for("view_cart"))

        profile = get_profile(user_id) if user_id else None
        has_default = bool(profile and has_default_contact(profile))
        prefilled = False

        if request.method == "POST":
            form_data = request.form
            save_default = bool(request.form.get("save_default"))

            # Chống tạo đơn trùng (idempotency check)
            token = request.form.get("checkout_token", "").strip()
            if token and token == session.get("_last_processed_checkout_token"):
                flash("Đơn hàng này đã được tiếp nhận xử lý từ trước.", "info")
                return redirect(url_for("checkout_success"))

            try:
                validated = validate_checkout(request.form)
                order_id = create_pending_order(validated, basket, user_id)
            except CheckoutValidationError as exc:
                flash(str(exc), "warning")
            except Exception:
                app.logger.exception("Không lưu được yêu cầu đặt hàng")
                flash("Chưa lưu được yêu cầu đặt hàng. Kiểm tra database và migration checkout trước khi thử lại.", "warning")
            else:
                if token:
                    session["_last_processed_checkout_token"] = token
                if user_id and save_default:
                    try:
                        save_checkout_defaults(user_id, validated)
                    except Exception:
                        app.logger.warning("Không lưu được thông tin mặc định; kiểm tra migration hồ sơ", exc_info=True)
                if buy_now_mode:
                    session.pop("buy_now", None)  # giỏ hàng cũ của khách giữ nguyên
                else:
                    session["cart"] = {}
                session["last_checkout_order"] = {
                    "order_id": int(order_id), "fulfillment": validated["fulfillment"],
                    "payment_method": validated["payment_method"]}
                return redirect(url_for("checkout_success"))
        else:
            # Khách đã đăng nhập: điền sẵn từ hồ sơ, vẫn sửa được. Lần mua đầu tự đề nghị lưu mặc định.
            form_data = checkout_defaults(profile) if profile else {}
            prefilled = has_default
            save_default = not has_default
            session["_active_checkout_token"] = secrets.token_hex(16)

        return render_template("checkout.html", cart_items=items, total=total, form_data=form_data,
                               prefilled=prefilled, save_default=save_default, buy_now=buy_now_mode,
                               checkout_token=session.get("_active_checkout_token", secrets.token_hex(16)))

    @app.get("/checkout/success")
    def checkout_success():
        latest = session.get("last_checkout_order")
        if not latest:
            return redirect(url_for("view_cart"))
        return render_template("checkout_success.html", **latest)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()[:150]
            password = request.form.get("password", "")
            account = query_one("""SELECT nd.MaNguoiDung, nd.HoVaTen, nd.MatKhauHash, nd.TrangThai, vt.TenVaiTro
              FROM NguoiDung nd JOIN VaiTro vt ON vt.MaVaiTro=nd.MaVaiTro WHERE nd.Email=?""", (email,))
            if not account or not check_password_hash(account["MatKhauHash"], password):
                flash("Email hoặc mật khẩu chưa đúng.", "warning")
            elif not account["TrangThai"]:
                flash("Tài khoản của bạn đã bị khóa. Vui lòng liên hệ quản trị viên.", "warning")
            else:
                keep_cart = session.get("cart", {})
                keep_buy_now = session.get("buy_now")  # đang "Mua ngay" dở thì không được mất
                session.clear()
                session["_csrf"] = secrets.token_hex(20)
                session["user_id"] = int(account["MaNguoiDung"])
                session["user_name"] = account["HoVaTen"]
                session["role"] = account["TenVaiTro"]
                session["cart"] = keep_cart
                if keep_buy_now:
                    session["buy_now"] = keep_buy_now
                target = request.form.get("next", "")
                # Chỉ điều hướng nội bộ, ngăn open redirect.
                if target.startswith("/") and not target.startswith("//") and not urlsplit(target).netloc:
                    return redirect(target)
                return redirect(url_for('admin_dashboard') if session['role'] == 'Admin'
                                else url_for('w12.staff_home') if session['role'] == 'Seller'
                                else url_for('home'))
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
        from ..services.dashboard import get_dashboard_stats
        return render_template("admin/index.html", metrics=get_dashboard_stats())

    @app.route("/admin/product/add", methods=["GET", "POST"])
    @admin_required
    def admin_product_add():
        # Route W2 chỉ là form mẫu, không lưu dữ liệu; dẫn tới luồng W3 duy nhất.
        if request.method == 'POST':
            flash('Form cũ đã ngừng sử dụng. Vui lòng nhập lại trên form thêm sản phẩm chính.', 'warning')
        return redirect(url_for('admin_w3.product_new'))

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
