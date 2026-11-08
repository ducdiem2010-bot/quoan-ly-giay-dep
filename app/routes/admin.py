"""Adapter Flask cho luồng quản lý sản phẩm W3 – tham chiếu prototype Khải, không phải code gốc Khải.
Dùng schema 9 bảng hiện có (SQLite test / SQL Server sau migration). Không mở quyền admin cho người dùng thường.
"""
from functools import wraps
from decimal import Decimal, InvalidOperation
from pathlib import Path
from uuid import uuid4
from werkzeug.utils import secure_filename
from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for, current_app
from ..db import query_all, query_one, get_db_connection

admin_w3=Blueprint('admin_w3',__name__,url_prefix='/admin/products')

ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
MAX_IMAGE_BYTES = 5 * 1024 * 1024

def _image_signature(data):
    return (data.startswith(b"\xff\xd8\xff") or
            data.startswith(b"\x89PNG\r\n\x1a\n") or
            (data.startswith(b"RIFF") and data[8:12] == b"WEBP"))

def _save_product_images(product_id):
    files = [f for f in request.files.getlist('images') if f and f.filename]
    if not files:
        return 0
    if len(files) > 8:
        raise ValueError('Mỗi lần chỉ được tải lên tối đa 8 ảnh.')
    upload_dir = Path(current_app.static_folder) / 'uploads' / 'products'
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    try:
        existing = query_all('SELECT MaHinhAnh FROM SanPhamHinhAnh WHERE MaSanPham=?', (product_id,))
        for item in files:
            original = secure_filename(item.filename)
            ext = Path(original).suffix.lower()
            if ext not in ALLOWED_IMAGE_EXTENSIONS:
                raise ValueError('Chỉ chấp nhận ảnh JPG, JPEG, PNG hoặc WEBP.')
            data = item.read(MAX_IMAGE_BYTES + 1)
            if not data or len(data) > MAX_IMAGE_BYTES:
                raise ValueError('Mỗi ảnh phải có dung lượng tối đa 5 MB.')
            if not _image_signature(data):
                raise ValueError('Nội dung tệp không phải ảnh hợp lệ.')
            filename = f'{uuid4().hex}{ext}'
            (upload_dir / filename).write_bytes(data)
            saved.append(filename)
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            for index, filename in enumerate(saved):
                is_cover = 1 if not existing and index == 0 else 0
                cur.execute('INSERT INTO SanPhamHinhAnh(MaSanPham,TenTep,LaAnhDaiDien,ThuTu) VALUES(?,?,?,?)',
                            (product_id, filename, is_cover, len(existing) + index))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
        return len(saved)
    except Exception:
        for filename in saved:
            try: (upload_dir / filename).unlink(missing_ok=True)
            except OSError: pass
        raise

def _product_images(product_id):
    rows = query_all('SELECT MaHinhAnh,TenTep,LaAnhDaiDien,ThuTu FROM SanPhamHinhAnh WHERE MaSanPham=? ORDER BY LaAnhDaiDien DESC,ThuTu,MaHinhAnh', (product_id,))
    for row in rows:
        row['filename'] = 'uploads/products/' + row['TenTep']
        row['is_cover'] = bool(row['LaAnhDaiDien'])
        row['alt'] = 'Ảnh sản phẩm'
    return rows

def admin_only(fn):
    @wraps(fn)
    def wrapper(*args,**kwargs):
        if not session.get('user_id'):
            return redirect(url_for('login',next=request.path))
        if session.get('role')!='Admin':abort(403)
        return fn(*args,**kwargs)
    return wrapper

def all_products():
    return query_all('''SELECT sp.MaSanPham, sp.TenSanPham, sp.GiaBan, sp.ThuongHieu,sp.HienThi,
      dm.TenDanhMuc, (SELECT TenTep FROM SanPhamHinhAnh ia WHERE ia.MaSanPham=sp.MaSanPham AND ia.LaAnhDaiDien=1) AS AnhDaiDien, COALESCE(SUM(bt.SoLuongTon),0) AS TongTon FROM SanPham sp
      JOIN DanhMuc dm ON dm.MaDanhMuc=sp.MaDanhMuc LEFT JOIN BienTheSanPham bt ON bt.MaSanPham=sp.MaSanPham
      GROUP BY sp.MaSanPham,sp.TenSanPham,sp.GiaBan,sp.ThuongHieu,sp.HienThi,dm.TenDanhMuc ORDER BY sp.MaSanPham DESC''')

def _fetch(id):
    return query_one('SELECT MaSanPham,MaDanhMuc,TenSanPham,GiaBan,ThuongHieu,MoTa,HienThi FROM SanPham WHERE MaSanPham=?',(id,))

def _parse():
    errors=[]
    name=request.form.get('name','').strip()
    brand=request.form.get('brand','').strip()
    description=request.form.get('description','').strip()
    try:cat=int(request.form.get('category_id',''))
    except(ValueError,TypeError):cat=None
    try:price=Decimal(request.form.get('price',''))
    except(InvalidOperation,ValueError):price=None
    if not 2<=len(name)<=200:errors.append('Tên sản phẩm phải có từ 2 đến 200 ký tự.')
    if price is None or not price.is_finite() or price < 0 or price > 10**12:errors.append('Giá không hợp lệ.')
    if cat is None or not query_one('SELECT MaDanhMuc FROM DanhMuc WHERE MaDanhMuc=?',(cat,)):
        errors.append('Danh mục không hợp lệ.')
    if len(brand)>100:errors.append('Tên thương hiệu quá dài.')
    if len(description)>5000:errors.append('Mô tả quá dài.')
    return {'name':name,'brand':brand,'description':description,'category_id':cat,'price':price},errors

@admin_w3.get('')
@admin_only
def products():
    return render_template('admin/w3_products.html',products=all_products())

@admin_w3.route('/new',methods=['GET','POST'])
@admin_only
def product_new():
    if request.method=='POST':
        data,errors=_parse()
        if errors:
            for e in errors:flash(e,'warning')
        else:
            conn=get_db_connection()
            try:
                cur=conn.cursor()
                args=(data['category_id'],session['user_id'],data['name'],
                      float(data['price']) if current_app.config['DB_BACKEND']=='sqlite' else data['price'],
                      data['brand'],data['description'])
                if current_app.config['DB_BACKEND']=='sqlserver':
                    cur.execute('''INSERT INTO SanPham(MaDanhMuc,MaNguoiTao,TenSanPham,GiaBan,ThuongHieu,MoTa)
                        OUTPUT INSERTED.MaSanPham VALUES(?,?,?,?,?,?)''',args)
                    new_id=int(cur.fetchone()[0])
                else:
                    cur.execute('INSERT INTO SanPham(MaDanhMuc,MaNguoiTao,TenSanPham,GiaBan,ThuongHieu,MoTa) VALUES(?,?,?,?,?,?)',args)
                    new_id=cur.lastrowid
                # Optional first variant is inserted before commit, so a failed
                # variant insert rolls back the product too (W3-042).
                if request.form.get('initial_size','').strip() or request.form.get('initial_color','').strip():
                    vsize=request.form.get('initial_size','').strip()
                    vcolor=request.form.get('initial_color','').strip()
                    try: vstock=int(request.form.get('initial_stock',''))
                    except (TypeError, ValueError): vstock=-1
                    if not vcolor or len(vsize)>30 or len(vcolor)>50 or vstock<0:
                        raise ValueError('Biến thể đầu tiên không hợp lệ')
                    cur.execute('INSERT INTO BienTheSanPham(MaSanPham,KichThuoc,MauSac,SoLuongTon) VALUES(?,?,?,?)',
                                (new_id,vsize,vcolor,vstock))
                conn.commit()
                try:
                    _save_product_images(new_id)
                except ValueError as image_error:
                    flash('Sản phẩm đã được lưu nhưng ảnh chưa được tải lên: ' + str(image_error), 'warning')
                else:
                    flash('Đã lưu sản phẩm và hình ảnh vào cơ sở dữ liệu.','success')
                return redirect(url_for('admin_w3.variants',product_id=new_id))
            except Exception:
                conn.rollback();current_app.logger.exception('Không lưu được sản phẩm')
                flash('Lỗi lưu sản phẩm, dữ liệu đã rollback.','warning')
            finally:conn.close()
    return render_template('admin/w3_product_form.html',categories=query_all('SELECT * FROM DanhMuc'),product=None,images=[])

@admin_w3.route('/<int:product_id>/edit',methods=['GET','POST'])
@admin_only
def product_edit(product_id):
    product=_fetch(product_id)
    if not product:abort(404)
    if request.method=='POST':
        data,errors=_parse()
        if errors:
            for e in errors:flash(e,'warning')
        else:
            conn=get_db_connection()
            try:
                conn.cursor().execute('''UPDATE SanPham SET MaDanhMuc=?,TenSanPham=?,GiaBan=?,ThuongHieu=?,MoTa=?
                    WHERE MaSanPham=?''',(data['category_id'],data['name'],
                     float(data['price']) if current_app.config['DB_BACKEND']=='sqlite' else data['price'],
                     data['brand'],data['description'],product_id))
                conn.commit()
                try:
                    _save_product_images(product_id)
                except ValueError as image_error:
                    flash('Thông tin sản phẩm đã cập nhật nhưng ảnh chưa được tải lên: ' + str(image_error), 'warning')
                else:
                    flash('Đã cập nhật sản phẩm và hình ảnh.','success')
                return redirect(url_for('admin_w3.products'))
            except Exception:
                conn.rollback();current_app.logger.exception('Lỗi sửa sản phẩm');flash('Lỗi cập nhật.','warning')
            finally:conn.close()
    return render_template('admin/w3_product_form.html',categories=query_all('SELECT * FROM DanhMuc'),product=product,images=_product_images(product_id))

@admin_w3.post('/<int:product_id>/images/<int:image_id>/cover')
@admin_only
def image_cover(product_id, image_id):
    if not _fetch(product_id): abort(404)
    if not query_one('SELECT MaHinhAnh FROM SanPhamHinhAnh WHERE MaHinhAnh=? AND MaSanPham=?', (image_id, product_id)): abort(404)
    conn=get_db_connection()
    try:
        cur=conn.cursor()
        cur.execute('UPDATE SanPhamHinhAnh SET LaAnhDaiDien=0 WHERE MaSanPham=?',(product_id,))
        cur.execute('UPDATE SanPhamHinhAnh SET LaAnhDaiDien=1 WHERE MaHinhAnh=? AND MaSanPham=?',(image_id,product_id))
        conn.commit(); flash('Đã đặt ảnh đại diện sản phẩm.','success')
    except Exception:
        conn.rollback(); flash('Không thể đổi ảnh đại diện.','warning')
    finally: conn.close()
    return redirect(url_for('admin_w3.product_edit', product_id=product_id))

@admin_w3.post('/<int:product_id>/images/<int:image_id>/delete')
@admin_only
def image_delete(product_id, image_id):
    if not _fetch(product_id): abort(404)
    row=query_one('SELECT TenTep,LaAnhDaiDien FROM SanPhamHinhAnh WHERE MaHinhAnh=? AND MaSanPham=?',(image_id,product_id))
    if not row: abort(404)
    conn=get_db_connection()
    try:
        conn.cursor().execute('DELETE FROM SanPhamHinhAnh WHERE MaHinhAnh=? AND MaSanPham=?',(image_id,product_id))
        if row['LaAnhDaiDien']:
            conn.cursor().execute('UPDATE SanPhamHinhAnh SET LaAnhDaiDien=1 WHERE MaHinhAnh=(SELECT MIN(MaHinhAnh) FROM SanPhamHinhAnh WHERE MaSanPham=?)',(product_id,))
        conn.commit()
        (Path(current_app.static_folder)/'uploads'/'products'/row['TenTep']).unlink(missing_ok=True)
        flash('Đã xóa ảnh sản phẩm.','success')
    except Exception:
        conn.rollback(); current_app.logger.exception('Lỗi xóa ảnh'); flash('Không xóa được ảnh.','warning')
    finally: conn.close()
    return redirect(url_for('admin_w3.product_edit', product_id=product_id))

@admin_w3.post('/<int:product_id>/visibility')
@admin_only
def visibility(product_id):
    if not _fetch(product_id):abort(404)
    conn=get_db_connection()
    try:
        conn.cursor().execute('UPDATE SanPham SET HienThi=CASE WHEN HienThi=1 THEN 0 ELSE 1 END WHERE MaSanPham=?',(product_id,))
        conn.commit();flash('Đã đổi trạng thái hiển thị sản phẩm.','success')
    except Exception:
        conn.rollback();current_app.logger.exception('Lỗi ẩn sản phẩm');flash('Không thay đổi được trạng thái.','warning')
    finally:conn.close()
    return redirect(url_for('admin_w3.products'))

@admin_w3.route('/<int:product_id>/variants',methods=['GET','POST'])
@admin_only
def variants(product_id):
    product=_fetch(product_id)
    if not product:abort(404)
    if request.method=='POST':
        size=request.form.get('size','').strip()
        color=request.form.get('color','').strip()
        try:stock=int(request.form.get('stock',''))
        except(ValueError,TypeError):stock=-1
        if not size or len(size)>30 or not color or len(color)>50 or stock<0:
            flash('Nhập màu/size và tồn kho không âm hợp lệ.','warning')
        else:
            conn=get_db_connection()
            try:
                conn.cursor().execute('''INSERT INTO BienTheSanPham(MaSanPham,KichThuoc,MauSac,SoLuongTon)
                    VALUES (?,?,?,?)''',(product_id,size,color,stock))
                conn.commit();flash('Đã thêm biến thể.','success')
            except Exception:
                conn.rollback();flash('Không thêm được: có thể trùng màu và size.','warning')
            finally:conn.close()
        return redirect(url_for('admin_w3.variants',product_id=product_id))
    return render_template('admin/w3_variants.html',product=product,variants=query_all('SELECT * FROM BienTheSanPham WHERE MaSanPham=? ORDER BY MaBienThe',(product_id,)))


@admin_w3.post('/<int:product_id>/variants/<int:variant_id>/edit')
@admin_only
def variant_edit(product_id, variant_id):
    """W3-040: edit one existing variant safely. No hard delete."""
    if not _fetch(product_id):
        abort(404)
    size = request.form.get('size','').strip()
    color = request.form.get('color','').strip()
    raw = request.form.get('stock','')
    try:
        stock = int(raw)
    except (ValueError,TypeError):
        stock = -1
    if not size or len(size)>30 or not color or len(color)>50 or stock<0:
        flash('Size/màu/tồn kho không hợp lệ.', 'warning')
        return redirect(url_for('admin_w3.variants', product_id=product_id))
    if not query_one('SELECT MaBienThe FROM BienTheSanPham WHERE MaBienThe=? AND MaSanPham=?', (variant_id, product_id)):
        abort(404)
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('''UPDATE BienTheSanPham SET KichThuoc=?,MauSac=?,SoLuongTon=?
            WHERE MaBienThe=? AND MaSanPham=?''', (size,color,stock,variant_id,product_id))
        if cur.rowcount == 0:
            conn.rollback();abort(404)
        conn.commit()
        flash('Đã cập nhật biến thể.', 'success')
    except Exception:
        conn.rollback()
        current_app.logger.exception('Không cập nhật được biến thể')
        flash('Không cập nhật được biến thể (có thể trùng màu/size).','warning')
    finally:
        conn.close()
    return redirect(url_for('admin_w3.variants', product_id=product_id))
