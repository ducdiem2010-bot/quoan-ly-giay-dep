import os
from pathlib import Path
from flask import Flask, session
from .db import init_demo_database


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    # Cấu hình bảo mật SECRET_KEY: bắt buộc mạnh ở production, cho phép fallback có cảnh báo ở dev/test
    env = os.getenv("FLASK_ENV", "").strip().lower()
    if not env:
        env = "production" if os.getenv("ENV", "").strip().lower() == "production" else "development"

    secret_key = os.getenv("SECRET_KEY", "").strip()
    insecure_keys = {
        "", "dev-secret-key-change-me", "CHỈ_DÙNG_Ở_LOCAL_DÈMO_ĐỔI_KHI_TRIỂN_KHAI",
        "secret", "123456", "change-me", "default-secret-key", "CHANGE_ME_TO_RANDOM_LONG_VALUE",
        "replace-with-random-secret-key-min-32-chars",
    }

    # Cho phép test_config truyền SECRET_KEY trước khi kiểm tra
    if test_config and "SECRET_KEY" in test_config:
        secret_key = test_config["SECRET_KEY"]

    if env == "production":
        if not secret_key or secret_key in insecure_keys or len(secret_key) < 16:
            raise RuntimeError(
                "Lỗi cấu hình bảo mật nghiêm trọng: Không thể khởi chạy ở môi trường production khi SECRET_KEY "
                "chưa được thiết lập an toàn qua biến môi trường. Vui lòng tạo key mạnh trong tệp .env "
                "(Ví dụ lệnh sinh key: python -c \"import secrets; print(secrets.token_hex(32))\")."
            )
    else:
        if not secret_key or secret_key in insecure_keys:
            import logging
            logging.getLogger("shoes_store").warning(
                "[CẢNH BÁO BẢO MẬT] SECRET_KEY đang sử dụng giá trị mặc định cho môi trường dev/test. "
                "Bắt buộc thiết lập biến môi trường SECRET_KEY mạnh trước khi triển khai production."
            )
            secret_key = "dev-secret-key-change-me-for-testing"

    app.config.update(
        SECRET_KEY=secret_key,
        DB_BACKEND=os.getenv("DB_BACKEND", "sqlite").lower(),
        DATABASE=os.getenv("DB_PATH", str(Path(app.instance_path) / "demo.sqlite3")),
        SQLSERVER_CONN=os.getenv("SQLSERVER_CONN", ""),
        SQLSERVER_TIMEZONE=os.getenv("SQLSERVER_TIMEZONE", "Asia/Ho_Chi_Minh"),
        MAX_CONTENT_LENGTH=45 * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        # W4 UI uses a real backend only when explicitly supplied.
        TUAN_ORDER_UI_PROVIDER=None,
        TUAN_W4_PREVIEW=False,
        LEGACY_ORDER_REDIRECT=True,
        ENABLE_ACCOUNT_STATUS_GUARD=True,
    )
    from .store_config import STORE_INFO
    app.config.setdefault("STORE_INFO", STORE_INFO)
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    if app.config["DB_BACKEND"] == "sqlite":
        with app.app_context():
            init_demo_database()
    from .routes import register_routes
    register_routes(app)
    from .routes.catalog import w3_catalog
    from .routes.admin import admin_w3
    from .routes.catalog_admin import admin_catalog
    from .routes.account import acct
    app.register_blueprint(acct)
    app.register_blueprint(w3_catalog)
    app.register_blueprint(admin_w3)
    app.register_blueprint(admin_catalog)
    # M3.1 - Đăng ký 2 Blueprint của Minh/Nghĩa đúng một lần.
    from .routes.new_arrivals import new_arrivals
    from .routes.best_sellers import best_sellers
    app.register_blueprint(new_arrivals)
    app.register_blueprint(best_sellers)
    # W11: các trang mới độc lập, không đụng blueprint hiện có.
    from .routes.w11 import w11
    app.register_blueprint(w11)
    from .routes.w12 import w12
    app.register_blueprint(w12)
    # W13 Tuấn: ghép 3 tiện ích khách hàng vào app Flask thật.
    # Chỉ đăng ký blueprint độc lập; không sửa nghiệp vụ checkout/đơn hàng.
    from .routes.w13_reorder import w13_tuan
    app.register_blueprint(w13_tuan)
    # Register W4 customer order UI and run its provider validation on startup.
    # Do not substitute an in-memory/demo order backend in production.
    from .tuan_w4_ui import tuan_w4_ui
    app.register_blueprint(tuan_w4_ui)

    @app.context_processor
    def inject_shared():
        from datetime import datetime, timezone
        return {"cart_count": sum(int(x) for x in session.get("cart", {}).values()),
                "current_year": datetime.now(timezone.utc).year,
                "store_info": app.config.get("STORE_INFO", STORE_INFO)}

    @app.context_processor
    def inject_product_badges():
        hot_ids = None

        def is_hot_product(product_id):
            nonlocal hot_ids
            if hot_ids is None:
                from .services.hot_products import get_hot_product_ids
                hot_ids = get_hot_product_ids()  # chỉ truy vấn một lần mỗi request
            return int(product_id) in hot_ids

        from .services.inventory import stock_status
        from .services.product_images import get_product_image_url, resolve_product_image_path
        return {
            "is_hot_product": is_hot_product,
            "stock_status": stock_status,
            "product_image_url": get_product_image_url,
            "resolve_product_image_path": resolve_product_image_path,
        }

    from .services.return_refunds import group_return_receipts
    app.add_template_global(group_return_receipts, "group_return_receipts")
    from .services.time_display import format_vn, format_audit_log
    app.add_template_filter(format_vn, 'vn_datetime')
    app.add_template_filter(format_audit_log, 'vn_audit_log')

    @app.template_filter("vnd")
    def vnd(value):
        return "{:,.0f} ₫".format(float(value or 0)).replace(",", ".")

    return app
