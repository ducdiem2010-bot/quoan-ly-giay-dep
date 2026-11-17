"""Blueprint riêng của Minh; chỉ được đăng ký tại bước tích hợp M3.1."""
from flask import Blueprint, render_template
from ..services.new_arrivals import get_latest_products

new_arrivals = Blueprint('new_arrivals', __name__)


@new_arrivals.get('/new-arrivals')
def show():
    return render_template('new_arrivals.html', products=get_latest_products())
