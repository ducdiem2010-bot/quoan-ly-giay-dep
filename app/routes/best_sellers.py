"""Blueprint trang Bán chạy của Nghĩa, đăng ký ở bước M3.1 của Minh."""
from flask import Blueprint, render_template
from ..services.best_sellers import get_best_selling_products

best_sellers = Blueprint('best_sellers', __name__)


@best_sellers.get('/best-sellers')
def show():
    return render_template('best_sellers.html', products=get_best_selling_products())
