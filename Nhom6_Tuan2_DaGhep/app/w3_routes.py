"""Route bổ sung W3, không sửa app/routes.py của Tuần 2."""
from flask import Blueprint, current_app, render_template, request, url_for

from .catalog_filter_options import DEMO_FILTER_OPTIONS
from .catalog_filters import prepare_filter_ui
from .catalog_ui import prepare_catalog_page
from .data import get_all_products

w3_catalog = Blueprint("w3_catalog", __name__)


@w3_catalog.get("/products")
def product_list():
    filter_ui = prepare_filter_ui(
        request.args,
        current_app.config.get("CATALOG_FILTER_OPTIONS", DEMO_FILTER_OPTIONS),
    )
    keyword = filter_ui["values"]["q"]
    all_products = get_all_products(keyword=keyword)
    products, pagination = prepare_catalog_page(
        all_products, request.args, url_for("w3_catalog.product_list")
    )
    return render_template(
        "product_list.html", products=products, pagination=pagination,
        keyword=keyword, filter_ui=filter_ui,
    )


def register_w3_routes(app):
    """Nạp Blueprint vào app gốc trước request đầu tiên, không ghi file cũ."""
    if w3_catalog.name in app.blueprints:
        return
    if any(rule.rule == "/products" for rule in app.url_map.iter_rules()):
        raise RuntimeError(
            "Dự án này đã có route /products. Gói chỉ thêm file được thiết kế "
            "cho bản gốc Tuần 2; cần đối chiếu route hiện có trước khi ghép."
        )
    app.register_blueprint(w3_catalog)
