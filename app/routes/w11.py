"""W11 – chức năng đọc dữ liệu và hiển thị; không chỉnh checkout/giỏ hàng/schema."""
from flask import Blueprint, abort, current_app, jsonify, render_template, request, url_for
from ..db import query_all
from ..data import get_all_products, get_categories, get_product_by_id, get_variants
from ..services.w11_insights import out_of_stock_products_report, product_quality_report, slow_stock_report
from .admin import admin_only

w11 = Blueprint('w11', __name__)


def _sqlite_or_503():
    # Hỗ trợ cả SQLite và SQL Server; không chặn 503
    pass


@w11.get('/admin/out-of-stock')
@admin_only
def out_of_stock_products():
    _sqlite_or_503()
    keyword = request.args.get('q', '').strip()[:80]
    products = out_of_stock_products_report(keyword=keyword)
    return render_template('w11/out_of_stock_products.html', products=products, keyword=keyword)


@w11.get('/admin/product-health')
@admin_only
def product_health():
    # Thay thế trang kiểm tra sản phẩm cũ: hiển thị trực tiếp danh sách sản phẩm hết hàng
    return out_of_stock_products()


@w11.get('/admin/slow-products')
@admin_only
def slow_products():
    _sqlite_or_503()
    try:
        days = int(request.args.get('days', '30'))
    except ValueError:
        abort(400)
    if days not in (7, 30, 90):
        abort(400)
    sort = request.args.get('sort', 'sold_asc')
    if sort not in ('sold_asc', 'stock_desc'):
        abort(400)
    keyword = request.args.get('q', '').strip()[:80]
    report = slow_stock_report(days=days, keyword=keyword,
                              zero_only=request.args.get('only_zero') == '1', order=sort)
    return render_template('w11/slow_products.html', report=report, keyword=keyword,
                           only_zero=request.args.get('only_zero') == '1', sort=sort)


@w11.get('/find-your-shoes')
def shoe_finder():
    _sqlite_or_503()
    products = get_all_products()
    categories = get_categories()
    brands = sorted({str(p['ThuongHieu']).strip() for p in products if p['ThuongHieu']}, key=str.casefold)
    # Chỉ lấy size/màu còn tồn của sản phẩm hiển thị.
    variants = query_all('''SELECT DISTINCT bt.MaSanPham,bt.KichThuoc,bt.MauSac
        FROM BienTheSanPham bt JOIN SanPham sp ON sp.MaSanPham=bt.MaSanPham
        WHERE sp.HienThi=1 AND bt.SoLuongTon>0''')
    sizes = sorted({v['KichThuoc'] for v in variants if v['KichThuoc']}, key=str.casefold)
    colors = sorted({v['MauSac'] for v in variants if v['MauSac']}, key=str.casefold)
    selected = {key: request.args.get(key, '').strip()[:100]
                for key in ('category', 'brand', 'color', 'size')}
    allowed = {'category': {str(c['MaDanhMuc']) for c in categories},
               'brand': set(brands), 'color': set(colors), 'size': set(sizes)}
    if any(selected[key] and selected[key] not in allowed[key] for key in allowed):
        abort(400, description='Bộ lọc không hợp lệ.')
    result = None
    if request.args.get('show') == '1':
        possible = set()
        for variant in variants:
            if selected['color'] and variant['MauSac'] != selected['color']:
                continue
            if selected['size'] and variant['KichThuoc'] != selected['size']:
                continue
            possible.add(int(variant['MaSanPham']))
        result = [p for p in products if int(p['MaSanPham']) in possible
                  and (not selected['category'] or str(p['MaDanhMuc']) == selected['category'])
                  and (not selected['brand'] or p['ThuongHieu'] == selected['brand'])]
    return render_template('w11/shoe_finder.html', categories=categories, brands=brands,
                           colors=colors, sizes=sizes, selected=selected, products=result)


@w11.get('/api/w11/quick-view/<int:product_id>')
def quick_view(product_id):
    _sqlite_or_503()
    product = get_product_by_id(product_id)  # HienThi=1, nên sản phẩm ẩn trả 404.
    if not product:
        abort(404)
    variants = get_variants(product_id)
    from ..services.product_images import get_product_image_url
    image_url = get_product_image_url(product)
    return jsonify({
        'id': product_id,
        'name': product['TenSanPham'],
        'brand': product['ThuongHieu'] or '',
        'category': product['TenDanhMuc'] or '',
        'price': float(product['GiaBan']),
        'price_text': '{:,.0f} ₫'.format(float(product['GiaBan'])).replace(',', '.'),
        'stock': int(product['TongTon']),
        'description': product['MoTa'] or '',
        'image_url': image_url,
        'colors': sorted({v['MauSac'] for v in variants if int(v['SoLuongTon']) > 0}),
        'sizes': sorted({v['KichThuoc'] for v in variants if int(v['SoLuongTon']) > 0}),
        'variants': [{'color': v['MauSac'], 'size': v['KichThuoc'], 'stock': int(v['SoLuongTon'])}
                     for v in variants if int(v['SoLuongTon']) > 0],
        'detail_url': url_for('product_detail', product_id=product_id),
    })
