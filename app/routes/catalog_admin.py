"""Quản lý các danh mục thuộc tính sản phẩm: Loại (DanhMuc), Thương hiệu (ThuongHieu), Màu sắc (MauSac), Kích thước (KichThuoc).
Kết nối CSDL SQLite/SQL Server, kiểm tra ràng buộc trước khi xóa để bảo toàn dữ liệu.
"""
from functools import wraps
from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for, current_app
from ..db import query_all, query_one, get_db_connection

admin_catalog = Blueprint('admin_catalog', __name__, url_prefix='/admin')


def admin_only(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('login', next=request.path))
        if session.get('role') != 'Admin':
            abort(403)
        return fn(*args, **kwargs)
    return wrapper


# ==========================================
# 1. QUẢN LÝ LOẠI / DANH MỤC (DanhMuc)
# ==========================================
@admin_catalog.route('/categories', methods=['GET', 'POST'])
@admin_only
def categories():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        if not 2 <= len(name) <= 100:
            flash('Tên loại / danh mục phải có từ 2 đến 100 ký tự.', 'warning')
        elif query_one('SELECT 1 FROM DanhMuc WHERE LOWER(TenDanhMuc)=LOWER(?)', (name,)):
            flash('Tên danh mục này đã tồn tại.', 'warning')
        else:
            conn = get_db_connection()
            try:
                cur = conn.cursor()
                cur.execute('INSERT INTO DanhMuc(TenDanhMuc, MoTa) VALUES(?, ?)', (name, description))
                conn.commit()
                flash('Thêm danh mục mới thành công.', 'success')
            except Exception:
                conn.rollback()
                flash('Lỗi khi thêm danh mục.', 'warning')
            finally:
                conn.close()
        return redirect(url_for('admin_catalog.categories'))

    items = query_all('''SELECT dm.MaDanhMuc, dm.TenDanhMuc, dm.MoTa, COUNT(sp.MaSanPham) AS SoSanPham
        FROM DanhMuc dm
        LEFT JOIN SanPham sp ON dm.MaDanhMuc = sp.MaDanhMuc
        GROUP BY dm.MaDanhMuc, dm.TenDanhMuc, dm.MoTa
        ORDER BY dm.MaDanhMuc''')
    return render_template('admin/categories.html', items=items)


@admin_catalog.post('/categories/<int:category_id>/edit')
@admin_only
def category_edit(category_id):
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    if not 2 <= len(name) <= 100:
        flash('Tên loại / danh mục phải có từ 2 đến 100 ký tự.', 'warning')
        return redirect(url_for('admin_catalog.categories'))
    duplicate = query_one('SELECT 1 FROM DanhMuc WHERE LOWER(TenDanhMuc)=LOWER(?) AND MaDanhMuc!=?', (name, category_id))
    if duplicate:
        flash('Tên danh mục này đã được sử dụng.', 'warning')
        return redirect(url_for('admin_catalog.categories'))
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('UPDATE DanhMuc SET TenDanhMuc=?, MoTa=? WHERE MaDanhMuc=?', (name, description, category_id))
        conn.commit()
        flash('Cập nhật danh mục thành công.', 'success')
    except Exception:
        conn.rollback()
        flash('Lỗi cập nhật danh mục.', 'warning')
    finally:
        conn.close()
    return redirect(url_for('admin_catalog.categories'))


@admin_catalog.post('/categories/<int:category_id>/delete')
@admin_only
def category_delete(category_id):
    has_sp = query_one('SELECT 1 FROM SanPham WHERE MaDanhMuc=?', (category_id,))
    if has_sp:
        flash('Danh mục này đang chứa sản phẩm, không thể xóa để tránh lỗi dữ liệu.', 'warning')
        return redirect(url_for('admin_catalog.categories'))
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM DanhMuc WHERE MaDanhMuc=?', (category_id,))
        conn.commit()
        flash('Đã xóa danh mục.', 'success')
    except Exception:
        conn.rollback()
        flash('Lỗi khi xóa danh mục.', 'warning')
    finally:
        conn.close()
    return redirect(url_for('admin_catalog.categories'))


# ==========================================
# 2. QUẢN LÝ THƯƠNG HIỆU (ThuongHieu)
# ==========================================
@admin_catalog.route('/brands', methods=['GET', 'POST'])
@admin_only
def brands():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        if not 2 <= len(name) <= 100:
            flash('Tên thương hiệu phải có từ 2 đến 100 ký tự.', 'warning')
        elif query_one('SELECT 1 FROM ThuongHieu WHERE LOWER(TenThuongHieu)=LOWER(?)', (name,)):
            flash('Thương hiệu này đã tồn tại.', 'warning')
        else:
            conn = get_db_connection()
            try:
                cur = conn.cursor()
                cur.execute('INSERT INTO ThuongHieu(TenThuongHieu, MoTa) VALUES(?, ?)', (name, description))
                conn.commit()
                flash('Thêm thương hiệu mới thành công.', 'success')
            except Exception:
                conn.rollback()
                flash('Lỗi khi thêm thương hiệu.', 'warning')
            finally:
                conn.close()
        return redirect(url_for('admin_catalog.brands'))

    items = query_all('''SELECT th.MaThuongHieu, th.TenThuongHieu, th.MoTa, COUNT(sp.MaSanPham) AS SoSanPham
        FROM ThuongHieu th
        LEFT JOIN SanPham sp ON LOWER(sp.ThuongHieu) = LOWER(th.TenThuongHieu)
        GROUP BY th.MaThuongHieu, th.TenThuongHieu, th.MoTa
        ORDER BY th.MaThuongHieu''')
    return render_template('admin/brands.html', items=items)


@admin_catalog.post('/brands/<int:brand_id>/edit')
@admin_only
def brand_edit(brand_id):
    brand = query_one('SELECT * FROM ThuongHieu WHERE MaThuongHieu=?', (brand_id,))
    if not brand:
        abort(404)
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    if not 2 <= len(name) <= 100:
        flash('Tên thương hiệu phải có từ 2 đến 100 ký tự.', 'warning')
        return redirect(url_for('admin_catalog.brands'))
    duplicate = query_one('SELECT 1 FROM ThuongHieu WHERE LOWER(TenThuongHieu)=LOWER(?) AND MaThuongHieu!=?', (name, brand_id))
    if duplicate:
        flash('Tên thương hiệu này đã tồn tại.', 'warning')
        return redirect(url_for('admin_catalog.brands'))
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        old_name = brand['TenThuongHieu']
        cur.execute('UPDATE ThuongHieu SET TenThuongHieu=?, MoTa=? WHERE MaThuongHieu=?', (name, description, brand_id))
        # Đồng bộ tên thương hiệu trong bảng SanPham nếu có
        cur.execute('UPDATE SanPham SET ThuongHieu=? WHERE ThuongHieu=?', (name, old_name))
        conn.commit()
        flash('Đã cập nhật thương hiệu.', 'success')
    except Exception:
        conn.rollback()
        flash('Lỗi khi cập nhật thương hiệu.', 'warning')
    finally:
        conn.close()
    return redirect(url_for('admin_catalog.brands'))


@admin_catalog.post('/brands/<int:brand_id>/delete')
@admin_only
def brand_delete(brand_id):
    brand = query_one('SELECT * FROM ThuongHieu WHERE MaThuongHieu=?', (brand_id,))
    if not brand:
        abort(404)
    has_sp = query_one('SELECT 1 FROM SanPham WHERE ThuongHieu=? OR MaThuongHieu=?', (brand['TenThuongHieu'], brand_id))
    if has_sp:
        flash('Thương hiệu đang có sản phẩm liên kết, không thể xóa để giữ toàn vẹn dữ liệu.', 'warning')
        return redirect(url_for('admin_catalog.brands'))
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM ThuongHieu WHERE MaThuongHieu=?', (brand_id,))
        conn.commit()
        flash('Đã xóa thương hiệu.', 'success')
    except Exception:
        conn.rollback()
        flash('Lỗi khi xóa thương hiệu.', 'warning')
    finally:
        conn.close()
    return redirect(url_for('admin_catalog.brands'))


# ==========================================
# 3. QUẢN LÝ MÀU SẮC (MauSac)
# ==========================================
@admin_catalog.route('/colors', methods=['GET', 'POST'])
@admin_only
def colors():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        hex_code = request.form.get('hex', '').strip() or None
        if not 1 <= len(name) <= 50:
            flash('Tên màu phải từ 1 đến 50 ký tự.', 'warning')
        elif query_one('SELECT 1 FROM MauSac WHERE LOWER(TenMau)=LOWER(?)', (name,)):
            flash('Màu sắc này đã tồn tại.', 'warning')
        else:
            conn = get_db_connection()
            try:
                cur = conn.cursor()
                cur.execute('INSERT INTO MauSac(TenMau, MaHex) VALUES(?, ?)', (name, hex_code))
                conn.commit()
                flash('Thêm màu sắc thành công.', 'success')
            except Exception:
                conn.rollback()
                flash('Lỗi khi thêm màu sắc.', 'warning')
            finally:
                conn.close()
        return redirect(url_for('admin_catalog.colors'))

    items = query_all('''SELECT m.MaMau, m.TenMau, m.MaHex, COUNT(bt.MaBienThe) AS SoBienThe
        FROM MauSac m
        LEFT JOIN BienTheSanPham bt ON LOWER(bt.MauSac) = LOWER(m.TenMau)
        GROUP BY m.MaMau, m.TenMau, m.MaHex
        ORDER BY m.MaMau''')
    return render_template('admin/colors.html', items=items)


@admin_catalog.post('/colors/<int:color_id>/edit')
@admin_only
def color_edit(color_id):
    color = query_one('SELECT * FROM MauSac WHERE MaMau=?', (color_id,))
    if not color:
        abort(404)
    name = request.form.get('name', '').strip()
    hex_code = request.form.get('hex', '').strip() or None
    if not 1 <= len(name) <= 50:
        flash('Tên màu không hợp lệ.', 'warning')
        return redirect(url_for('admin_catalog.colors'))
    duplicate = query_one('SELECT 1 FROM MauSac WHERE LOWER(TenMau)=LOWER(?) AND MaMau!=?', (name, color_id))
    if duplicate:
        flash('Tên màu này đã tồn tại.', 'warning')
        return redirect(url_for('admin_catalog.colors'))
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        old_name = color['TenMau']
        cur.execute('UPDATE MauSac SET TenMau=?, MaHex=? WHERE MaMau=?', (name, hex_code, color_id))
        cur.execute('UPDATE BienTheSanPham SET MauSac=? WHERE MauSac=?', (name, old_name))
        conn.commit()
        flash('Đã cập nhật màu sắc.', 'success')
    except Exception:
        conn.rollback()
        flash('Lỗi khi cập nhật màu.', 'warning')
    finally:
        conn.close()
    return redirect(url_for('admin_catalog.colors'))


@admin_catalog.post('/colors/<int:color_id>/delete')
@admin_only
def color_delete(color_id):
    color = query_one('SELECT * FROM MauSac WHERE MaMau=?', (color_id,))
    if not color:
        abort(404)
    has_bt = query_one('SELECT 1 FROM BienTheSanPham WHERE LOWER(MauSac)=LOWER(?)', (color['TenMau'],))
    if has_bt:
        flash('Màu sắc đang được dùng trong các biến thể sản phẩm, không thể xóa.', 'warning')
        return redirect(url_for('admin_catalog.colors'))
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM MauSac WHERE MaMau=?', (color_id,))
        conn.commit()
        flash('Đã xóa màu sắc.', 'success')
    except Exception:
        conn.rollback()
        flash('Lỗi khi xóa màu sắc.', 'warning')
    finally:
        conn.close()
    return redirect(url_for('admin_catalog.colors'))


# ==========================================
# 4. QUẢN LÝ KÍCH THƯỚC (KichThuoc)
# ==========================================
@admin_catalog.route('/sizes', methods=['GET', 'POST'])
@admin_only
def sizes():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not 1 <= len(name) <= 30:
            flash('Kích thước phải từ 1 đến 30 ký tự.', 'warning')
        elif query_one('SELECT 1 FROM KichThuoc WHERE LOWER(TenKichThuoc)=LOWER(?)', (name,)):
            flash('Kích thước này đã tồn tại.', 'warning')
        else:
            conn = get_db_connection()
            try:
                cur = conn.cursor()
                cur.execute('INSERT INTO KichThuoc(TenKichThuoc) VALUES(?)', (name,))
                conn.commit()
                flash('Thêm kích thước thành công.', 'success')
            except Exception:
                conn.rollback()
                flash('Lỗi khi thêm kích thước.', 'warning')
            finally:
                conn.close()
        return redirect(url_for('admin_catalog.sizes'))

    items = query_all('''SELECT k.MaKichThuoc, k.TenKichThuoc, COUNT(bt.MaBienThe) AS SoBienThe
        FROM KichThuoc k
        LEFT JOIN BienTheSanPham bt ON LOWER(bt.KichThuoc) = LOWER(k.TenKichThuoc)
        GROUP BY k.MaKichThuoc, k.TenKichThuoc
        ORDER BY k.MaKichThuoc''')
    return render_template('admin/sizes.html', items=items)


@admin_catalog.post('/sizes/<int:size_id>/edit')
@admin_only
def size_edit(size_id):
    size = query_one('SELECT * FROM KichThuoc WHERE MaKichThuoc=?', (size_id,))
    if not size:
        abort(404)
    name = request.form.get('name', '').strip()
    if not 1 <= len(name) <= 30:
        flash('Kích thước không hợp lệ.', 'warning')
        return redirect(url_for('admin_catalog.sizes'))
    duplicate = query_one('SELECT 1 FROM KichThuoc WHERE LOWER(TenKichThuoc)=LOWER(?) AND MaKichThuoc!=?', (name, size_id))
    if duplicate:
        flash('Kích thước này đã tồn tại.', 'warning')
        return redirect(url_for('admin_catalog.sizes'))
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        old_name = size['TenKichThuoc']
        cur.execute('UPDATE KichThuoc SET TenKichThuoc=? WHERE MaKichThuoc=?', (name, size_id))
        cur.execute('UPDATE BienTheSanPham SET KichThuoc=? WHERE KichThuoc=?', (name, old_name))
        conn.commit()
        flash('Đã cập nhật kích thước.', 'success')
    except Exception:
        conn.rollback()
        flash('Lỗi khi cập nhật kích thước.', 'warning')
    finally:
        conn.close()
    return redirect(url_for('admin_catalog.sizes'))


@admin_catalog.post('/sizes/<int:size_id>/delete')
@admin_only
def size_delete(size_id):
    size = query_one('SELECT * FROM KichThuoc WHERE MaKichThuoc=?', (size_id,))
    if not size:
        abort(404)
    has_bt = query_one('SELECT 1 FROM BienTheSanPham WHERE LOWER(KichThuoc)=LOWER(?)', (size['TenKichThuoc'],))
    if has_bt:
        flash('Kích thước đang được dùng trong các biến thể sản phẩm, không thể xóa.', 'warning')
        return redirect(url_for('admin_catalog.sizes'))
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM KichThuoc WHERE MaKichThuoc=?', (size_id,))
        conn.commit()
        flash('Đã xóa kích thước.', 'success')
    except Exception:
        conn.rollback()
        flash('Lỗi khi xóa kích thước.', 'warning')
    finally:
        conn.close()
    return redirect(url_for('admin_catalog.sizes'))
