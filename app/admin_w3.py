"""Adapter Flask cho luồng quản lý sản phẩm W3 – tham chiếu prototype Khải, không phải code gốc Khải.
Dùng schema 9 bảng hiện có (SQLite test / SQL Server sau migration). Không mở quyền admin cho người dùng thường.
"""
from functools import wraps
from decimal import Decimal, InvalidOperation
from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for, current_app
from .db import query_all, query_one, get_db_connection

admin_w3=Blueprint('admin_w3',__name__,url_prefix='/admin/products')

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
      dm.TenDanhMuc, COALESCE(SUM(bt.SoLuongTon),0) AS TongTon FROM SanPham sp
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
                conn.commit()
                flash('Đã lưu sản phẩm vào cơ sở dữ liệu.','success')
                return redirect(url_for('admin_w3.variants',product_id=new_id))
            except Exception:
                conn.rollback();current_app.logger.exception('Không lưu được sản phẩm')
                flash('Lỗi lưu sản phẩm, dữ liệu đã rollback.','warning')
            finally:conn.close()
    return render_template('admin/w3_product_form.html',categories=query_all('SELECT * FROM DanhMuc'),product=None)

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
                conn.commit();flash('Đã cập nhật sản phẩm.','success')
                return redirect(url_for('admin_w3.products'))
            except Exception:
                conn.rollback();current_app.logger.exception('Lỗi sửa sản phẩm');flash('Lỗi cập nhật.','warning')
            finally:conn.close()
    return render_template('admin/w3_product_form.html',categories=query_all('SELECT * FROM DanhMuc'),product=product)

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
