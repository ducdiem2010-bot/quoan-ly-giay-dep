# Vị trí lưu: app/routes/best_sellers.py
from flask import Blueprint, render_template
from app.services.best_sellers import get_best_sellers_v1

# Tạo Blueprint cho trang Bán chạy
best_sellers_bp = Blueprint('best_sellers', __name__)


@best_sellers_bp.route('/best-sellers')
def best_sellers_page():
    # Lấy top 6 sản phẩm bán chạy
    products = get_best_sellers_v1(limit=6)

    # Render ra giao diện
    return render_template('best_sellers.html', products=products)

