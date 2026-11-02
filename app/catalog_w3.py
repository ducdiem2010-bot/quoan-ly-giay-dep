"""Tích hợp giao diện Tuấn W3-065/W3-066 với Flask, truy vấn tham số hóa.
Lưu ý: schema nhóm chưa có Gender/BrandId/ColorId/SizeId; các bộ lọc sử dụng
cột hiện hữu, thiếu field được ghi ở báo cáo, không tự đoán thêm.
"""
from math import ceil
from urllib.parse import urlencode
from flask import Blueprint, request, render_template, url_for
from .db import query_all

w3_catalog = Blueprint('w3_catalog', __name__)


def _options(sql):
    return [str(x['v']) for x in query_all(sql) if x['v'] is not None and str(x['v']).strip()]


def _number(value, label, errors):
    if not value: return None
    try:
        result = float(value)
        if result < 0 or result > 10**12:raise ValueError()
        return result
    except (ValueError, TypeError):
        errors[label] = 'Giá phải là số không âm hợp lệ.'
        return None


@w3_catalog.get('/products')
def product_list():
    args = request.args
    q = args.get('q', '')[:80].strip()
    chosen = []
    errors = {}
    conditions = ['sp.HienThi = 1']
    params = []
    if q:
        conditions.append('(sp.TenSanPham LIKE ? OR sp.ThuongHieu LIKE ?)')
        params += [f'%{q}%', f'%{q}%']
        chosen.append({'label':'Từ khóa','value':q})
    cats = query_all('SELECT MaDanhMuc, TenDanhMuc FROM DanhMuc ORDER BY TenDanhMuc')
    cat_options=[{'value':str(x['MaDanhMuc']), 'label':x['TenDanhMuc']} for x in cats]
    brands=_options('SELECT DISTINCT ThuongHieu AS v FROM SanPham WHERE ThuongHieu IS NOT NULL ORDER BY ThuongHieu')
    colors=_options('SELECT DISTINCT MauSac AS v FROM BienTheSanPham ORDER BY MauSac')
    sizes=_options('SELECT DISTINCT KichThuoc AS v FROM BienTheSanPham ORDER BY KichThuoc')
    definitions=[('type_id','Loại',cat_options),('brand','Thương hiệu',[{'value':x,'label':x} for x in brands]),('color','Màu',[{'value':x,'label':x} for x in colors]),('size','Size',[{'value':x,'label':x} for x in sizes])]
    selects=[]
    for key,label,options in definitions:
        selected = args.get(key, '')[:100]
        allowed={x['value'] for x in options}
        if selected and selected not in allowed:
            errors[key]='Giá trị bộ lọc không hợp lệ.'
            selected=''
        if selected:
            chosen.append({'label':label,'value':next(x['label'] for x in options if x['value']==selected)})
            if key=='type_id':
                conditions.append('sp.MaDanhMuc=?');params.append(int(selected))
            if key=='brand':
                conditions.append('sp.ThuongHieu=?');params.append(selected)
        selects.append({'name':key,'label':label,'options':options,'selected':selected})
    val={x['name']:x['selected'] for x in selects}
    val.update({'q':q, 'sort':args.get('sort','')[:30], 'price_min':args.get('price_min','')[:30], 'price_max':args.get('price_max','')[:30]})
    minimum=_number(val['price_min'],'price_min',errors)
    maximum=_number(val['price_max'],'price_max',errors)
    if minimum is not None:conditions.append('sp.GiaBan>=?');params.append(minimum);chosen.append({'label':'Giá từ','value':val['price_min']})
    if maximum is not None:conditions.append('sp.GiaBan<=?');params.append(maximum);chosen.append({'label':'Giá đến','value':val['price_max']})
    if minimum is not None and maximum is not None and minimum>maximum:
        errors['price_max']='Giá đến phải lớn hơn hoặc bằng giá từ.'
    # Cùng biến thể: màu/size phải thỏa trên MỘT hàng biến thể.
    selected_color=val.get('color')
    selected_size=val.get('size')
    if selected_color or selected_size:
        vconds=['bt.MaSanPham=sp.MaSanPham']
        if selected_color:vconds.append('bt.MauSac=?');params.append(selected_color)
        if selected_size:vconds.append('bt.KichThuoc=?');params.append(selected_size)
        conditions.append('EXISTS (SELECT 1 FROM BienTheSanPham bt WHERE '+' AND '.join(vconds)+')')
    sql='''SELECT sp.MaSanPham, sp.TenSanPham, sp.GiaBan, sp.ThuongHieu, sp.MoTa,
          sp.MaDanhMuc, dm.TenDanhMuc, COALESCE(SUM(bt.SoLuongTon),0) AS TongTon
          FROM SanPham sp JOIN DanhMuc dm ON sp.MaDanhMuc=dm.MaDanhMuc
          LEFT JOIN BienTheSanPham bt ON sp.MaSanPham=bt.MaSanPham
          WHERE '''+' AND '.join(conditions)+''' GROUP BY sp.MaSanPham, sp.TenSanPham, sp.GiaBan,
          sp.ThuongHieu, sp.MoTa, sp.MaDanhMuc, dm.TenDanhMuc'''
    rows=query_all(sql,tuple(params)) if not errors else []
    sort_key=val['sort']
    sorts={'price_asc':lambda x:(float(x['GiaBan']),x['MaSanPham']),
           'price_desc':lambda x:(-float(x['GiaBan']),x['MaSanPham']),
           'name_asc':lambda x:(x['TenSanPham'].casefold(),x['MaSanPham']),
           'brand_asc':lambda x:((x['ThuongHieu'] or '').casefold(),x['MaSanPham'])}
    if sort_key in sorts:
        rows=sorted(rows,key=sorts[sort_key]);chosen.append({'label':'Sắp xếp','value':sort_key})
    else:
        val['sort']='';rows=sorted(rows,key=lambda x:x['MaSanPham'])
    try:page=max(1,min(10000,int(args.get('page','1'))))
    except ValueError:page=1
    per_page=6;total=len(rows);page_count=max(1,ceil(total/per_page));page=min(page,page_count)
    current=rows[(page-1)*per_page:page*per_page]
    def to_page(p):
        query={k:v for k,v in val.items() if v}
        query['page']=p
        return url_for('w3_catalog.product_list')+'?'+urlencode(query)
    pagination={'total':total,'page':page,'page_count':page_count,'first_item':(page-1)*per_page+1 if total else 0,
                'last_item':min(total,page*per_page),'prev_url':to_page(page-1) if page>1 else None,
                'next_url':to_page(page+1) if page<page_count else None}
    return render_template('product_list.html',products=current,pagination=pagination,keyword=q,
        filter_ui={'values':val,'selects':selects,'chosen':chosen,'errors':errors})
