"""Các URL W13 độc lập. Điểm đăng ký blueprint tại điểm tích hợp cuối."""
from pathlib import Path
from flask import Blueprint, abort, jsonify, redirect, render_template, request, session, url_for, current_app
from ..db import query_all
from ..services.w13_reorder import OrderAccessError
from ..services.w13_order_timeline import get_timeline

w13_tuan = Blueprint('w13_tuan', __name__, url_prefix='/w13')


def _require_customer():
    if not session.get('user_id'):
        abort(401, description='Bạn cần đăng nhập để xem đơn hàng')
    if session.get('role') != 'Customer':
        abort(403)
    return int(session['user_id'])


@w13_tuan.get('/orders/<int:order_id>/timeline')
def timeline(order_id):
    uid = _require_customer()
    try:
        info = get_timeline(order_id, uid)
    except OrderAccessError as exc:
        abort(exc.status_code)
    return render_template('w13/timeline_page.html', info=info, tab='orders')


@w13_tuan.get('/recent-products')
def recent_products():
    raw = request.args.get('ids', '')
    # IDs validated, bounded: no direct SQL text concatenation from user.
    ids = []
    for token in raw.split(',')[:16]:
        if token.isascii() and token.isdecimal():
            value = int(token)
            if value > 0 and value not in ids:
                ids.append(value)
        if len(ids) == 8:
            break
    if not ids:
        return jsonify({'products': []})
    rows = query_all('''SELECT MaSanPham, TenSanPham, GiaBan FROM SanPham
                        WHERE HienThi=1 AND MaSanPham IN (''' + ','.join('?' for _ in ids) + ')', tuple(ids))
    products = {int(r['MaSanPham']): r for r in rows}
    fallback = url_for('static', filename='images/no-product-image.svg')
    out = []
    for pid in ids:
        row = products.get(pid)
        if row is None: continue
        # Do not trust raw filenames supplied by the DB for an image URL.
        image = fallback
        candidates = query_all('''SELECT TenTep FROM SanPhamHinhAnh WHERE MaSanPham=? AND LaAnhDaiDien=1''', (pid,))
        for candidate in candidates:
            name = (candidate.get('TenTep') or '').strip()
            if not name or '/' in name or chr(92) in name or '..' in name: continue
            for dirname in ('uploads/products', 'images/storefront'):
                if (Path(current_app.static_folder) / dirname / name).is_file():
                    image = url_for('static', filename=dirname+'/'+name)
                    break
            if image != fallback: break
        out.append({'id': pid, 'name': row['TenSanPham'], 'price': float(row['GiaBan']),
                    'image': image, 'url': url_for('product_detail', product_id=pid)})
    return jsonify({'products': out})


@w13_tuan.get('/recently-viewed')
def recently_viewed_page():
    if not session.get('user_id'):
        return redirect(url_for('login', next=request.path))
    if session.get('role') != 'Customer':
        abort(403)
    return render_template('w13/recent_page.html', tab='recent')
