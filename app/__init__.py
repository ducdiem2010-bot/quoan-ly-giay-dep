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
<<<<<<< HEAD
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        TUAN_W4_PREVIEW=os.getenv("TUAN_W4_PREVIEW", "0") == "1",
        TUAN_ORDER_UI_PROVIDER=None,
=======
        MAX_CONTENT_LENGTH=45 * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
>>>>>>> ba1d4e0 (Upload project)
    )
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    if app.config["DB_BACKEND"] == "sqlite":
        with app.app_context():
            init_demo_database()
    from .routes import register_routes
    register_routes(app)
<<<<<<< HEAD
    from .catalog_w3 import w3_catalog
    from .admin_w3 import admin_w3
    app.register_blueprint(w3_catalog)
    app.register_blueprint(admin_w3)
    # W4 Tuấn: bộ điều khiển trình bày; không truy vấn DB hay xử lý nghiệp vụ đơn.
    from .tuan_w4_ui import tuan_w4_ui
    app.register_blueprint(tuan_w4_ui)
=======
    from .routes.catalog import w3_catalog
    from .routes.admin import admin_w3
    app.register_blueprint(w3_catalog)
    app.register_blueprint(admin_w3)
>>>>>>> ba1d4e0 (Upload project)

    @app.context_processor
    def inject_shared():
        return {"cart_count": sum(int(x) for x in session.get("cart", {}).values())}

    @app.template_filter("vnd")
    def vnd(value):
        return "{:,.0f} ₫".format(float(value or 0)).replace(",", ".")

    return app
