import pyodbc

def get_db_connection():
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=.\\SQLEXPRESS;'
        'DATABASE=QuanLyBanHang;'
        'Trusted_Connection=yes;'
    )
    return conn

# 1. Tối ưu truy vấn danh sách trang chủ
def get_all_products():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
            SELECT 
                sp.MaSanPham,
                sp.TenSanPham,
                sp.GiaBan,
                sp.ThuongHieu,
                dm.TenDanhMuc
            FROM SanPham sp WITH (NOLOCK)
            INNER JOIN DanhMuc dm WITH (NOLOCK) ON sp.MaDanhMuc = dm.MaDanhMuc
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    finally:
        cursor.close()
        conn.close()

# 2. Tối ưu truy vấn chi tiết 1 sản phẩm
def get_product_by_id(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
            SELECT 
                sp.MaSanPham,
                sp.TenSanPham,
                sp.GiaBan,
                sp.ThuongHieu,
                sp.MoTa,
                dm.TenDanhMuc
            FROM SanPham sp WITH (NOLOCK)
            INNER JOIN DanhMuc dm WITH (NOLOCK) ON sp.MaDanhMuc = dm.MaDanhMuc
            WHERE sp.MaSanPham = ?
        """
        cursor.execute(query, (product_id,))
        row = cursor.fetchone()
        
        if row:
            columns = [column[0] for column in cursor.description]
            return dict(zip(columns, row))
        return None
    finally:
        cursor.close()
        conn.close()
# 3. Hàm của Nghĩa (T4): Lấy danh sách sản phẩm theo ID Danh Mục
def get_products_by_category(category_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Truy vấn lấy các sản phẩm có MaDanhMuc khớp với category_id truyền vào
        query = """
            SELECT 
                sp.MaSanPham,
                sp.TenSanPham,
                sp.GiaBan,
                sp.ThuongHieu,
                dm.TenDanhMuc
            FROM SanPham sp WITH (NOLOCK)
            INNER JOIN DanhMuc dm WITH (NOLOCK) ON sp.MaDanhMuc = dm.MaDanhMuc
            WHERE sp.MaDanhMuc = ?
        """
        cursor.execute(query, (category_id,))
        rows = cursor.fetchall()

        # Nếu có dữ liệu trả về, đóng gói thành dạng danh sách từ điển (list of dicts)
        if rows:
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        # Nếu không có sản phẩm nào thuộc danh mục này, trả về list rỗng
        return []
    finally:
        cursor.close()
        conn.close()