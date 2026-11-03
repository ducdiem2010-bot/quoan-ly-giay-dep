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
    """Thêm biến thể mới, chống trùng lặp cặp (Size + Màu) và ngăn tồn âm"""
    # 1. Ngăn tồn âm theo chuẩn DoD W4-018
    if so_luong_ton < 0:
        raise ValueError("Số lượng tồn kho không được phép nhỏ hơn 0 (Tồn âm)!")

    # 2. Kiểm tra cặp biến thể trùng lặp
    existing = query_one("""
        SELECT MaBienThe FROM BienTheSanPham 
        WHERE MaSanPham = ? AND KichThuoc = ? AND MauSac = ?
    """, (product_id, kich_thuoc, mau_sac))

    if existing:
        raise ValueError(
            f"Biến thể Màu '{mau_sac}' và Size '{kich_thuoc}' đã tồn tại! Vui lòng chỉnh sửa số lượng tồn ở dòng có sẵn.")

    return execute(
        "INSERT INTO BienTheSanPham (MaSanPham, KichThuoc, MauSac, SoLuongTon) VALUES (?, ?, ?, ?)",
        (product_id, kich_thuoc, mau_sac, so_luong_ton))


def update_stock(product_id, variant_id, so_luong_ton):
    """Cập nhật tồn kho, ngăn tồn âm"""
    # Ngăn tồn âm theo chuẩn DoD W4-018
    if so_luong_ton < 0:
        raise ValueError("Số lượng cập nhật không được phép là số âm!")

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
# ----------------------------------------------------------------- W3-034: Quản lý Danh mục (Categories)
def get_categories_admin(search_query=None):
    """Lấy danh sách danh mục quản trị (kèm hỗ trợ tìm kiếm theo tên)."""
    if search_query:
        return query_all(
            "SELECT MaDanhMuc, TenDanhMuc FROM DanhMuc WHERE TenDanhMuc LIKE ? ORDER BY TenDanhMuc",
            (f"%{search_query}%",)
        )
    return query_all("SELECT MaDanhMuc, TenDanhMuc FROM DanhMuc ORDER BY TenDanhMuc")

def create_category(ten_danh_muc):
    """Thêm danh mục mới (Chống trùng tên)."""
    existing = query_one("SELECT MaDanhMuc FROM DanhMuc WHERE TenDanhMuc = ?", (ten_danh_muc,))
    if existing:
        raise ValueError("Tên danh mục đã tồn tại!")
    return execute("INSERT INTO DanhMuc (TenDanhMuc) VALUES (?)", (ten_danh_muc,))

def update_category(ma_danh_muc, ten_danh_muc):
    """Cập nhật tên danh mục (Chống trùng tên với bản ghi khác)."""
    existing = query_one(
        "SELECT MaDanhMuc FROM DanhMuc WHERE TenDanhMuc = ? AND MaDanhMuc <> ?",
        (ten_danh_muc, ma_danh_muc)
    )
    if existing:
        raise ValueError("Tên danh mục đã bị trùng với danh mục khác!")
    return execute(
        "UPDATE DanhMuc SET TenDanhMuc = ? WHERE MaDanhMuc = ?",
        (ten_danh_muc, ma_danh_muc)
    )

def delete_category(ma_danh_muc):
    """Xóa danh mục an toàn (Chống xóa nếu đang có sản phẩm thuộc danh mục này)."""
    check_sp = query_one("SELECT COUNT(*) AS Total FROM SanPham WHERE MaDanhMuc = ?", (ma_danh_muc,))
    if check_sp and check_sp["Total"] > 0:
        raise pyodbc.IntegrityError("HY000", "Danh mục đang chứa sản phẩm, không thể xóa!")
    return execute("DELETE FROM DanhMuc WHERE MaDanhMuc = ?", (ma_danh_muc,))


# ----------------------------------------------------------------- W3-035: Quản lý Màu sắc (Colors)
def get_colors_admin(search_query=None):
    """Lấy danh sách màu sắc quản trị (hỗ trợ tìm kiếm)."""
    if search_query:
        return query_all(
            "SELECT MaMau, TenMau FROM MauSac WHERE TenMau LIKE ? ORDER BY TenMau",
            (f"%{search_query}%",)
        )
    return query_all("SELECT MaMau, TenMau FROM MauSac ORDER BY TenMau")

def create_color(ten_mau):
    """Thêm màu mới (Chống trùng tên)."""
    existing = query_one("SELECT MaMau FROM MauSac WHERE TenMau = ?", (ten_mau,))
    if existing:
        raise ValueError("Tên màu đã tồn tại!")
    return execute("INSERT INTO MauSac (TenMau) VALUES (?)", (ten_mau,))

def update_color(ma_mau, ten_mau):
    """Cập nhật tên màu."""
    existing = query_one(
        "SELECT MaMau FROM MauSac WHERE TenMau = ? AND MaMau <> ?",
        (ten_mau, ma_mau)
    )
    if existing:
        raise ValueError("Tên màu đã bị trùng với màu khác!")
    return execute(
        "UPDATE MauSac SET TenMau = ? WHERE MaMau = ?",
        (ten_mau, ma_mau)
    )

def delete_color(ma_mau):
    """Xóa màu an toàn (kiểm tra xem có biến thể nào đang dùng màu này không)."""
    # Lấy tên màu trước để check với bảng BienTheSanPham nếu lưu dạng text
    color_obj = query_one("SELECT TenMau FROM MauSac WHERE MaMau = ?", (ma_mau,))
    if color_obj:
        ten_mau = color_obj["TenMau"]
        check_var = query_one("SELECT COUNT(*) AS Total FROM BienTheSanPham WHERE MauSac = ?", (ten_mau,))
        if check_var and check_var["Total"] > 0:
            raise pyodbc.IntegrityError("HY000", "Màu sắc đang được sử dụng bởi biến thể sản phẩm, không thể xóa!")
    return execute("DELETE FROM MauSac WHERE MaMau = ?", (ma_mau,))


# ----------------------------------------------------------------- W3-036: Quản lý Kích thước (Sizes)
def get_sizes_admin(search_query=None):
    """Lấy danh sách kích thước quản trị (hỗ trợ tìm kiếm)."""
    if search_query:
        return query_all(
            "SELECT MaSize, TenSize FROM KichThuoc WHERE TenSize LIKE ? ORDER BY TenSize",
            (f"%{search_query}%",)
        )
    return query_all("SELECT MaSize, TenSize FROM KichThuoc ORDER BY TenSize")

def create_size(ten_size):
    """Thêm size mới (Chống trùng)."""
    existing = query_one("SELECT MaSize FROM KichThuoc WHERE TenSize = ?", (ten_size,))
    if existing:
        raise ValueError("Kích thước này đã tồn tại!")
    return execute("INSERT INTO KichThuoc (TenSize) VALUES (?)", (ten_size,))

def update_size(ma_size, ten_size):
    """Cập nhật size."""
    existing = query_one(
        "SELECT MaSize FROM KichThuoc WHERE TenSize = ? AND MaSize <> ?",
        (ten_size, ma_size)
    )
    if existing:
        raise ValueError("Kích thước đã bị trùng với size khác!")
    return execute(
        "UPDATE KichThuoc SET TenSize = ? WHERE MaSize = ?",
        (ten_size, ma_size)
    )

def delete_size(ma_size):
    """Xóa size an toàn (kiểm tra biến thể đang dùng)."""
    size_obj = query_one("SELECT TenSize FROM KichThuoc WHERE MaSize = ?", (ma_size,))
    if size_obj:
        ten_size = size_obj["TenSize"]
        check_var = query_one("SELECT COUNT(*) AS Total FROM BienTheSanPham WHERE KichThuoc = ?", (ten_size,))
        if check_var and check_var["Total"] > 0:
            raise pyodbc.IntegrityError("HY000", "Kích thước đang được sử dụng bởi biến thể sản phẩm, không thể xóa!")
    return execute("DELETE FROM KichThuoc WHERE MaSize = ?", (ma_size,))


# =================================================================
# NHIỆM VỤ W4-008: TẠO VÀ HỦY ĐƠN HÀNG (PHẦN NGHĨA - THỨ 3 TUẦN 4)
# =================================================================

def check_and_deduct_inventory(items):
    """
    (MOCK INTERFACE) Hàm giả lập kiểm tra và trừ tồn kho.
    - Hiện tại luôn trả về True để Nghĩa test luồng tạo đơn.
    - Minh (W4-012) sẽ viết lại ruột hàm này bằng Transaction SQL thực tế.
    """
    # Logic của Minh sau này sẽ là: lặp qua items, kiểm tra Số Lượng Tồn của từng MaBienThe,
    # nếu đủ thì trừ đi, không đủ thì return False kèm lỗi.
    return True, "Hợp lệ"


def create_order(ho_ten, so_dien_thoai, dia_chi, tong_tien, items):
    """
    Tạo đơn hàng mới (Snapshot dữ liệu người nhận) và chi tiết đơn hàng.
    Mặc định trạng thái khởi tạo là 'Chờ xác nhận'.
    """
    conn = get_db_connection()
    try:
        cur = conn.cursor()

        # 1. Bắt đầu Transaction ảo (Sẽ ghép với Transaction DB của Minh sau)
        # Giả định MaNguoiDung = 1 (hoặc lấy từ session nếu đã có chức năng user)
        # TrangThaiDon = 0 (Chờ xác nhận)
        cur.execute("""
            INSERT INTO DonHang (MaNguoiDung, HoTenNguoiNhan, SoDienThoaiNguoiNhan, 
                                 DiaChiNguoiNhan, TongTien, TrangThaiDon, NgayDatHang)
            OUTPUT INSERTED.MaDonHang
            VALUES (?, ?, ?, ?, ?, 0, GETDATE())
        """, (1, ho_ten, so_dien_thoai, dia_chi, tong_tien))

        new_order_id = cur.fetchone()[0]

        # 2. Snapshot (Lưu cứng) chi tiết đơn hàng
        for item in items:
            cur.execute("""
                INSERT INTO ChiTietDonHang (MaDonHang, MaBienThe, SoLuong, GiaMuaSnapshot)
                VALUES (?, ?, ?, ?)
            """, (new_order_id, item['variant_id'], item['quantity'], item['price']))

        conn.commit()
        return new_order_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_order_status(order_id):
    """Lấy trạng thái hiện tại của đơn hàng để kiểm tra trước khi hủy."""
    row = query_one("SELECT TrangThaiDon FROM DonHang WHERE MaDonHang = ?", (order_id,))
    return row['TrangThaiDon'] if row else None


def cancel_order(order_id):
    """
    Hủy đơn hàng nếu trạng thái đang là 'Chờ xác nhận' (TrangThaiDon = 0).
    Trả về True nếu hủy thành công, False nếu vi phạm luật DoD.
    """
    status = get_order_status(order_id)

    if status is None:
        raise ValueError("Đơn hàng không tồn tại.")

    # DoD: Không cho hủy đơn đã xác nhận (Trạng thái > 0)
    if status > 0:
        return False

    # Hủy đơn (Cập nhật trạng thái = -1, ví dụ vậy)
    execute("UPDATE DonHang SET TrangThaiDon = -1 WHERE MaDonHang = ?", (order_id,))
    return True


# =================================================================
# NHIỆM VỤ W4-013: GIAO DỊCH THANH TOÁN ONLINE (PHẦN NGHĨA - THỨ 4)
# =================================================================

def check_duplicate_transaction(transaction_id):
    """
    Kiểm tra xem mã giao dịch (transaction_id) từ cổng thanh toán đã được xử lý chưa.
    Giúp chống tình trạng Callback lặp (ghi trùng) theo yêu cầu DoD.
    """
    # MOCK: Tạm thời gọi vào bảng DonHang (giả sử Minh sẽ thêm cột MaGiaoDich).
    # Trả về True nếu đã tồn tại, False nếu chưa.
    try:
        row = query_one("SELECT MaDonHang FROM DonHang WHERE MaGiaoDich = ?", (transaction_id,))
        return True if row else False
    except pyodbc.Error:
        # Nếu Minh chưa update cột MaGiaoDich, tạm pass qua để Nghĩa test logic code
        return False


def update_payment_status(order_id, transaction_id, is_success):
    """
    Cập nhật trạng thái thanh toán của đơn hàng sau khi có phản hồi từ Sandbox.
    """
    # 0 = Chờ xác nhận, 1 = Đã thanh toán, -1 = Thất bại
    trang_thai_thanh_toan = 1 if is_success else -1

    # Cập nhật DB: Lưu mã giao dịch làm bằng chứng (transaction/verify)
    execute("""
        UPDATE DonHang 
        SET TrangThaiDon = ?, MaGiaoDich = ? 
        WHERE MaDonHang = ?
    """, (trang_thai_thanh_toan, transaction_id, order_id))

    return True