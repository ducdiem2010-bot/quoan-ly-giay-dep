"""Truy cập SQL Server bằng pyodbc.
Mọi truy vấn đều truyền giá trị qua tham số (?) để tránh SQL injection."""
import os

import pyodbc
from dotenv import load_dotenv

load_dotenv()

DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
SERVER = os.getenv("DB_SERVER", r".\SQLEXPRESS")
DATABASE = os.getenv("DB_NAME", "QuanLyBanHang")
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")


def get_db_connection():
    conn_str = f"DRIVER={{{DRIVER}}};SERVER={SERVER};DATABASE={DATABASE};TrustServerCertificate=yes;"
    if DB_USER:
        conn_str += f"UID={DB_USER};PWD={DB_PASSWORD};"
    else:
        conn_str += "Trusted_Connection=yes;"
    return pyodbc.connect(conn_str)


# ---------------------------------------------------------------- tiện ích
def query_all(sql, params=()):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        conn.close()


def query_one(sql, params=()):
    rows = query_all(sql, params)
    return rows[0] if rows else None


def execute(sql, params=()):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def _get_or_create(conn, table, id_col, name_col, name):
    """Lấy id theo tên, chưa có thì thêm mới.
    table/id_col/name_col là hằng số trong code, không lấy từ người dùng."""
    cur = conn.cursor()
    cur.execute(f"SELECT {id_col} FROM {table} WHERE {name_col} = ?", (name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(f"INSERT INTO {table} ({name_col}) OUTPUT INSERTED.{id_col} VALUES (?)", (name,))
    return cur.fetchone()[0]


# ------------------------------------------------------------ trang công khai
def get_all_products():
    return query_all("""
        SELECT sp.MaSanPham, sp.TenSanPham, sp.GiaBan, sp.HinhAnh, sp.GioiTinh,
               th.TenThuongHieu AS ThuongHieu, dm.TenDanhMuc
        FROM SanPham sp
        JOIN DanhMuc dm ON sp.MaDanhMuc = dm.MaDanhMuc
        LEFT JOIN ThuongHieu th ON sp.MaThuongHieu = th.MaThuongHieu
        WHERE sp.HienThi = 1
        ORDER BY sp.NgayTao DESC, sp.MaSanPham DESC
    """)


def get_product_by_id(product_id, only_visible=True):
    sql = """
        SELECT sp.MaSanPham, sp.TenSanPham, sp.GiaBan, sp.MoTa, sp.HinhAnh,
               sp.GioiTinh, sp.HienThi,
               th.TenThuongHieu AS ThuongHieu, dm.TenDanhMuc
        FROM SanPham sp
        JOIN DanhMuc dm ON sp.MaDanhMuc = dm.MaDanhMuc
        LEFT JOIN ThuongHieu th ON sp.MaThuongHieu = th.MaThuongHieu
        WHERE sp.MaSanPham = ?
    """
    if only_visible:
        sql += " AND sp.HienThi = 1"
    return query_one(sql, (product_id,))


def get_variants(product_id):
    return query_all("""
        SELECT MaBienThe, KichThuoc, MauSac, SoLuongTon
        FROM BienTheSanPham
        WHERE MaSanPham = ?
        ORDER BY MauSac, TRY_CAST(KichThuoc AS INT), KichThuoc
    """, (product_id,))


# ----------------------------------------------------------------- quản trị
def get_all_products_admin():
    return query_all("""
        SELECT sp.MaSanPham, sp.TenSanPham, sp.GiaBan, sp.HienThi, sp.GioiTinh,
               th.TenThuongHieu AS ThuongHieu, dm.TenDanhMuc,
               (SELECT COUNT(*) FROM BienTheSanPham bt WHERE bt.MaSanPham = sp.MaSanPham) AS SoBienThe,
               ISNULL((SELECT SUM(SoLuongTon) FROM BienTheSanPham bt WHERE bt.MaSanPham = sp.MaSanPham), 0) AS TongTon
        FROM SanPham sp
        JOIN DanhMuc dm ON sp.MaDanhMuc = dm.MaDanhMuc
        LEFT JOIN ThuongHieu th ON sp.MaThuongHieu = th.MaThuongHieu
        ORDER BY sp.MaSanPham DESC
    """)


def get_categories():
    return query_all("SELECT MaDanhMuc, TenDanhMuc FROM DanhMuc ORDER BY TenDanhMuc")


def get_brands():
    return query_all("SELECT MaThuongHieu, TenThuongHieu FROM ThuongHieu ORDER BY TenThuongHieu")


def create_product(ten, gia, ma_danh_muc, danh_muc_moi, ma_thuong_hieu,
                   thuong_hieu_moi, gioi_tinh, mo_ta, hinh_anh, hien_thi):
    """Thêm sản phẩm. Có thể tạo luôn danh mục / thương hiệu mới trong cùng giao dịch."""
    conn = get_db_connection()
    try:
        if danh_muc_moi:
            ma_danh_muc = _get_or_create(conn, "DanhMuc", "MaDanhMuc", "TenDanhMuc", danh_muc_moi)
        if thuong_hieu_moi:
            ma_thuong_hieu = _get_or_create(conn, "ThuongHieu", "MaThuongHieu", "TenThuongHieu", thuong_hieu_moi)

        cur = conn.cursor()
        # Chưa có đăng nhập thật: gán người tạo là tài khoản Admin/Seller đầu tiên
        cur.execute("SELECT TOP 1 MaNguoiDung FROM NguoiDung WHERE MaVaiTro IN (1, 2) ORDER BY MaNguoiDung")
        creator = cur.fetchone()
        if not creator:
            raise RuntimeError("Chưa có tài khoản Admin/Seller trong bảng NguoiDung")

        cur.execute("""
            INSERT INTO SanPham (MaDanhMuc, MaNguoiTao, MaThuongHieu, TenSanPham, GiaBan,
                                 GioiTinh, MoTa, HinhAnh, HienThi)
            OUTPUT INSERTED.MaSanPham
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (ma_danh_muc, creator[0], ma_thuong_hieu, ten, gia, gioi_tinh, mo_ta, hinh_anh, hien_thi))
        new_id = cur.fetchone()[0]
        conn.commit()
        return new_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def toggle_visibility(product_id):
    return execute(
        "UPDATE SanPham SET HienThi = CASE WHEN HienThi = 1 THEN 0 ELSE 1 END WHERE MaSanPham = ?",
        (product_id,))


def delete_product(product_id):
    return execute("DELETE FROM SanPham WHERE MaSanPham = ?", (product_id,))


def add_variant(product_id, kich_thuoc, mau_sac, so_luong_ton):
    return execute(
        "INSERT INTO BienTheSanPham (MaSanPham, KichThuoc, MauSac, SoLuongTon) VALUES (?, ?, ?, ?)",
        (product_id, kich_thuoc, mau_sac, so_luong_ton))


def update_stock(product_id, variant_id, so_luong_ton):
    return execute(
        "UPDATE BienTheSanPham SET SoLuongTon = ? WHERE MaBienThe = ? AND MaSanPham = ?",
        (so_luong_ton, variant_id, product_id))


def delete_variant(product_id, variant_id):
    return execute(
        "DELETE FROM BienTheSanPham WHERE MaBienThe = ? AND MaSanPham = ?",
        (variant_id, product_id))
# ----------------------------------------------------------------- W3-021: API chọn biến thể
def get_variant_by_attributes(product_id, size, color):
    """Lấy thông tin biến thể theo kích thước và màu sắc."""
    return query_one("""
        SELECT bt.MaBienThe, bt.SoLuongTon, sp.GiaBan
        FROM BienTheSanPham bt
        JOIN SanPham sp ON bt.MaSanPham = sp.MaSanPham
        WHERE bt.MaSanPham = ? AND bt.KichThuoc = ? AND bt.MauSac = ?
    """, (product_id, size, color))


# ----------------------------------------------------------------- W3-022: Quản lý Thương hiệu
def get_brands_admin(search_query=None):
    """Lấy danh sách thương hiệu (kèm hỗ trợ tìm kiếm theo tên)."""
    if search_query:
        return query_all(
            "SELECT MaThuongHieu, TenThuongHieu FROM ThuongHieu WHERE TenThuongHieu LIKE ? ORDER BY TenThuongHieu",
            (f"%{search_query}%",)
        )
    return query_all("SELECT MaThuongHieu, TenThuongHieu FROM ThuongHieu ORDER BY TenThuongHieu")


def create_brand(ten_thuong_hieu):
    """Thêm thương hiệu mới (Chống trùng tên)."""
    existing = query_one("SELECT MaThuongHieu FROM ThuongHieu WHERE TenThuongHieu = ?", (ten_thuong_hieu,))
    if existing:
        raise ValueError("Tên thương hiệu đã tồn tại!")
    return execute("INSERT INTO ThuongHieu (TenThuongHieu) VALUES (?)", (ten_thuong_hieu,))


def update_brand(ma_thuong_hieu, ten_thuong_hieu):
    """Cập nhật tên thương hiệu (Chống trùng tên với bản ghi khác)."""
    existing = query_one(
        "SELECT MaThuongHieu FROM ThuongHieu WHERE TenThuongHieu = ? AND MaThuongHieu <> ?",
        (ten_thuong_hieu, ma_thuong_hieu)
    )
    if existing:
        raise ValueError("Tên thương hiệu đã bị trùng với thương hiệu khác!")
    return execute(
        "UPDATE ThuongHieu SET TenThuongHieu = ? WHERE MaThuongHieu = ?",
        (ten_thuong_hieu, ma_thuong_hieu)
    )


def delete_brand(ma_thuong_hieu):
    """Xóa thương hiệu an toàn (Chống xóa nếu đang gắn với sản phẩm)."""
    check_sp = query_one("SELECT COUNT(*) AS Total FROM SanPham WHERE MaThuongHieu = ?", (ma_thuong_hieu,))
    if check_sp and check_sp["Total"] > 0:
        raise pyodbc.IntegrityError("HY000", "Thương hiệu đang gắn với sản phẩm, không thể xóa!")
    return execute("DELETE FROM ThuongHieu WHERE MaThuongHieu = ?", (ma_thuong_hieu,))
