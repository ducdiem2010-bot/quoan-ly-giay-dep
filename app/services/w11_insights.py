"""W11: báo cáo chỉ đọc trên schema SQLite W10.

Không tạo bảng, cập nhật đơn, tự sửa sản phẩm hoặc quy đổi đơn chưa hoàn thành
thành số lượng đã bán. Schema SQL Server V2 chưa có adapter tương thích W11.
"""
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from flask import current_app
from ..db import query_all
from ..routes.admin import all_products


def _require_sqlite():
    if current_app.config.get('DB_BACKEND') != 'sqlite':
        raise NotImplementedError('W11 chưa kiểm chứng ánh xạ schema SQL Server V2.')


def product_quality_report():
    """Phát hiện dữ liệu bất thường; không xem ảnh fallback hợp lệ là lỗi."""
    _require_sqlite()
    products = all_products()
    variants = query_all('SELECT MaBienThe,MaSanPham,KichThuoc,MauSac,SoLuongTon FROM BienTheSanPham')
    images = query_all('SELECT MaSanPham,TenTep,LaAnhDaiDien FROM SanPhamHinhAnh')
    by_variant, by_image = defaultdict(list), defaultdict(list)
    for variant in variants:
        by_variant[int(variant['MaSanPham'])].append(variant)
    for image in images:
        by_image[int(image['MaSanPham'])].append(image)

    image_root = (Path(current_app.static_folder) / 'uploads' / 'products').resolve()
    records = []
    without_uploaded_image = sum(not by_image[int(p['MaSanPham'])] for p in products)
    for product in products:
        pid = int(product['MaSanPham'])
        issues = []
        def warn(level, description):
            issues.append({'level': level, 'description': description})

        if not (product['TenSanPham'] or '').strip():
            warn('high', 'Thiếu tên sản phẩm bắt buộc')
        if not (product['TenDanhMuc'] or '').strip():
            warn('high', 'Thiếu danh mục bắt buộc')
        try:
            price = float(product['GiaBan'])
            if not 0 <= price <= 10**12 or price != price or price in (float('inf'), float('-inf')):
                warn('high', 'Giá nằm ngoài giới hạn hợp lệ')
        except (ValueError, TypeError):
            warn('high', 'Giá không phải dữ liệu số')

        product_variants = by_variant[pid]
        seen = set()
        for variant in product_variants:
            key = (str(variant['KichThuoc']).strip().casefold(), str(variant['MauSac']).strip().casefold())
            if key in seen:
                warn('high', 'Có biến thể trùng cặp màu/size')
            seen.add(key)
            if not all(key):
                warn('high', 'Biến thể thiếu màu hoặc size')
            stock = variant['SoLuongTon']
            if not isinstance(stock, int) or stock < 0:
                warn('high', 'Biến thể có tồn kho không hợp lệ')
        if bool(product['HienThi']) and not product_variants:
            warn('high', 'Đang hiển thị nhưng chưa có biến thể để bán')
        elif bool(product['HienThi']) and not any(int(v['SoLuongTon'] or 0) > 0 for v in product_variants):
            warn('review', 'Đang hiển thị nhưng toàn bộ biến thể đã hết hàng')

        for image in by_image[pid]:
            name = image['TenTep'] or ''
            path = (image_root / name).resolve()
            if not name or not path.is_relative_to(image_root) or not path.is_file():
                warn('high', 'Tệp ảnh tải lên không tồn tại hoặc đường dẫn không an toàn')
        # Ảnh fallback SVG/JPG trong app/static là cơ chế chính thức của W10.
        # Không gắn nhãn lỗi cho sản phẩm không tải ảnh riêng.
        if issues:
            records.append({**product, 'issues': issues, 'severity':
                'high' if any(i['level'] == 'high' for i in issues) else 'review'})
    records.sort(key=lambda item: (item['severity'] != 'high', item['MaSanPham']))
    return {'total': len(products), 'flagged': len(records),
            'high': sum(p['severity'] == 'high' for p in records),
            'without_uploaded_image': without_uploaded_image, 'records': records}


def slow_stock_report(days=30, keyword='', zero_only=False, order='sold_asc'):
    """Thống kê đơn HOÀN THÀNH, đồng nhất best_sellers.py của W10 (SQLite)."""
    _require_sqlite()
    days = int(days)
    if days not in (7, 30, 90):
        raise ValueError('Khoảng thời gian không hợp lệ')
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    rows = query_all('''
        SELECT bt.MaSanPham,
          COALESCE(SUM(ct.SoLuong),0) AS DaBanTatCa,
          COALESCE(SUM(CASE WHEN dh.NgayDat >= ? THEN ct.SoLuong ELSE 0 END),0) AS DaBanTrongKy,
          MAX(dh.NgayDat) AS LanBanGanNhat
        FROM ChiTietDonHang ct
        JOIN DonHang dh ON dh.MaDonHang=ct.MaDonHang AND dh.TrangThai='Hoàn thành'
        JOIN BienTheSanPham bt ON bt.MaBienThe=ct.MaBienThe
        GROUP BY bt.MaSanPham
    ''', (since,))
    sales = {int(r['MaSanPham']): r for r in rows}
    results = []
    for product in all_products():
        # Sản phẩm bị ẩn không có cơ hội bán: không gọi là bán chậm.
        if not bool(product['HienThi']) or int(product['TongTon']) <= 0:
            continue
        if keyword and keyword.casefold() not in (product['TenSanPham'] or '').casefold():
            continue
        data = sales.get(int(product['MaSanPham']), {})
        recent = int(data.get('DaBanTrongKy') or 0)
        lifetime = int(data.get('DaBanTatCa') or 0)
        if recent > 2 or (zero_only and recent != 0):
            continue
        results.append({**product, 'sold_period': recent, 'sold_all': lifetime,
                        'last_sale': data.get('LanBanGanNhat'),
                        'label': ('Chưa từng có đơn hoàn thành' if lifetime == 0 else
                                  f'Không bán trong {days} ngày' if recent == 0 else 'Bán chậm (1–2 đôi)')})
    if order == 'stock_desc':
        results.sort(key=lambda p: (-int(p['TongTon']), p['MaSanPham']))
    else:
        results.sort(key=lambda p: (p['sold_period'], -int(p['TongTon']), p['MaSanPham']))
    return {'days': days, 'total': len(results), 'items': results, 'since': since,
            'definition': 'Còn tồn và bán tối đa 2 đôi từ các đơn Hoàn thành trong kỳ.'}
