import os
from pathlib import Path
from flask import Flask, session
from .db import init_demo_database


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "CHỈ_DÙNG_Ở_LOCAL_DÈMO_ĐỔI_KHI_TRIỂN_KHAI"),
        DB_BACKEND=os.getenv("DB_BACKEND", "sqlite").lower(),
        DATABASE=os.getenv("DB_PATH", str(Path(app.instance_path) / "demo.sqlite3")),
        SQLSERVER_CONN=os.getenv("SQLSERVER_CONN", ""),
        MAX_CONTENT_LENGTH=45 * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        # W4 UI uses a real backend only when explicitly supplied.
        TUAN_ORDER_UI_PROVIDER=None,
        TUAN_W4_PREVIEW=False,
        LEGACY_ORDER_REDIRECT=True,
        ENABLE_ACCOUNT_STATUS_GUARD=True,
    )
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
    from .routes.collections import collections
    app.register_blueprint(collections)
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
    # Register W4 customer order UI and run its provider validation on startup.
    # Do not substitute an in-memory/demo order backend in production.
    from .tuan_w4_ui import tuan_w4_ui
    app.register_blueprint(tuan_w4_ui)

    @app.context_processor
    def inject_shared():
        from datetime import datetime, timezone
        return {"cart_count": sum(int(x) for x in session.get("cart", {}).values()),
                "current_year": datetime.now(timezone.utc).year}

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
        return {"is_hot_product": is_hot_product, "stock_status": stock_status}

    @app.template_filter("vnd")
    def vnd(value):
        return "{:,.0f} ₫".format(float(value or 0)).replace(",", ".")

    return app
