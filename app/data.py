"""Truy vấn dữ liệu; JOIN lấy tên danh mục và tổng tồn trong cùng 1 query."""
from .db import query_all, query_one

SELECT_PRODUCT = """
 SELECT sp.MaSanPham, sp.TenSanPham, sp.GiaBan, sp.ThuongHieu, sp.MoTa,
        sp.MaDanhMuc, dm.TenDanhMuc,
        COALESCE(SUM(bt.SoLuongTon), 0) AS TongTon
 FROM SanPham sp
 JOIN DanhMuc dm ON dm.MaDanhMuc = sp.MaDanhMuc
 LEFT JOIN BienTheSanPham bt ON bt.MaSanPham = sp.MaSanPham
"""
GROUP_PRODUCT = " GROUP BY sp.MaSanPham, sp.TenSanPham, sp.GiaBan, sp.ThuongHieu, sp.MoTa, sp.MaDanhMuc, dm.TenDanhMuc "


def get_categories():
    return query_all("SELECT MaDanhMuc, TenDanhMuc FROM DanhMuc ORDER BY MaDanhMuc")


def get_all_products(category_id=None, keyword=None):
    where, args = [], []
    if category_id is not None:
        where.append("sp.MaDanhMuc = ?")
        args.append(category_id)
    if keyword:
        where.append("(sp.TenSanPham LIKE ? OR sp.ThuongHieu LIKE ?)")
        args.extend([f"%{keyword}%", f"%{keyword}%"])
    sql = SELECT_PRODUCT + (" WHERE " + " AND ".join(where) if where else "") + GROUP_PRODUCT + " ORDER BY sp.MaSanPham"
    return query_all(sql, tuple(args))


def get_product_by_id(product_id):
    return query_one(SELECT_PRODUCT + " WHERE sp.MaSanPham = ? " + GROUP_PRODUCT, (product_id,))


def get_products_by_category(category_id):
    return get_all_products(category_id=category_id)


def get_variants(product_id):
    return query_all("SELECT MaBienThe, MaSanPham, KichThuoc, MauSac, SoLuongTon FROM BienTheSanPham WHERE MaSanPham = ? ORDER BY KichThuoc, MauSac", (product_id,))


def get_variant(variant_id):
    return query_one("""SELECT bt.MaBienThe, bt.MaSanPham, bt.KichThuoc, bt.MauSac, bt.SoLuongTon,
      sp.TenSanPham, sp.GiaBan, sp.ThuongHieu FROM BienTheSanPham bt
      JOIN SanPham sp ON bt.MaSanPham=sp.MaSanPham WHERE bt.MaBienThe=?""", (variant_id,))
