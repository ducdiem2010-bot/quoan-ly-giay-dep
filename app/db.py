"""Kết nối chung: SQLite chỉ cho demo; SQL Server là đích triển khai nhóm.

Tên cột thống nhất theo schema SQL Server (MaSanPham, TenSanPham, ...).
Tất cả truy vấn đều tham số hóa bằng dấu ?.
"""
from pathlib import Path
import sqlite3
from flask import current_app


class DatabaseConnectionError(RuntimeError):
    pass


def get_db_connection():
    backend = current_app.config["DB_BACKEND"]
    try:
        if backend == "sqlite":
            conn = sqlite3.connect(current_app.config["DATABASE"], timeout=5)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            return conn
        if backend == "sqlserver":
            import pyodbc
            conn_str = current_app.config.get("SQLSERVER_CONN")
            if not conn_str:
                raise DatabaseConnectionError("Chưa cấu hình SQLSERVER_CONN")
            return pyodbc.connect(conn_str, timeout=5)
        raise DatabaseConnectionError("DB_BACKEND chỉ nhận sqlite hoặc sqlserver")
    except DatabaseConnectionError:
        raise
    except Exception as exc:
        current_app.logger.exception("Lỗi kết nối cơ sở dữ liệu")
        raise DatabaseConnectionError("Không thể kết nối cơ sở dữ liệu. Kiểm tra cấu hình.") from exc


def query_all(sql, params=()):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        columns = [d[0] for d in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]
    finally:
        conn.close()


def query_one(sql, params=()):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        row = cur.fetchone()
        return dict(zip([d[0] for d in cur.description], row)) if row is not None else None
    finally:
        conn.close()


def execute(sql, params=()):
    conn = get_db_connection()
    try:
        conn.cursor().execute(sql, params)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_demo_database():
    """Chỉ chạy SQLite. Khởi tạo khi chưa có bảng, không xóa dữ liệu người dùng."""
    if current_app.config["DB_BACKEND"] != "sqlite":
        return
    path = Path(current_app.config["DATABASE"])
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        exists = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='SanPham'").fetchone()
        if not exists:
            root = Path(__file__).resolve().parent.parent / "database"
            conn.executescript((root / "schema_sqlite.sql").read_text(encoding="utf-8"))
            conn.executescript((root / "seed_sqlite.sql").read_text(encoding="utf-8"))
            conn.commit()
        # Nâng cấp nhẹ bản demo cũ: giữ nguyên toàn bộ dữ liệu hiện có.
        columns = {r[1] for r in conn.execute("PRAGMA table_info(SanPham)").fetchall()}
        if "HienThi" not in columns:
            conn.execute("ALTER TABLE SanPham ADD COLUMN HienThi INTEGER NOT NULL DEFAULT 1")
        # Hồ sơ khách hàng: thêm cột mới cho NguoiDung, giữ nguyên dữ liệu cũ.
        user_cols = {r[1] for r in conn.execute("PRAGMA table_info(NguoiDung)").fetchall()}
        for col in ("Ho", "Ten", "GioiTinh", "NgaySinh", "TinhThanh", "PhuongXa", "NguoiKhoa", "ThoiGianKhoa", "GhiChuKhoa"):
            if col not in user_cols:
                conn.execute(f"ALTER TABLE NguoiDung ADD COLUMN {col} TEXT")

        # Cột theo dõi xử lý đơn hàng
        order_cols = {r[1] for r in conn.execute("PRAGMA table_info(DonHang)").fetchall()}
        if "MaNguoiXuLy" not in order_cols:
            conn.execute("ALTER TABLE DonHang ADD COLUMN MaNguoiXuLy INTEGER REFERENCES NguoiDung(MaNguoiDung)")
        if "ThoiGianXuLy" not in order_cols:
            conn.execute("ALTER TABLE DonHang ADD COLUMN ThoiGianXuLy TEXT")

        # Bảng thông tin giao dịch checkout
        conn.execute("""CREATE TABLE IF NOT EXISTS ThongTinGiaoDich (
            MaDonHang INTEGER PRIMARY KEY REFERENCES DonHang(MaDonHang) ON DELETE CASCADE,
            HoTen TEXT NOT NULL, SoDienThoai TEXT NOT NULL, Email TEXT,
            HinhThucNhanHang TEXT NOT NULL CHECK(HinhThucNhanHang IN ('delivery','pickup')),
            DiaChiGiaoHang TEXT, PhuongThucThanhToan TEXT NOT NULL
              CHECK(PhuongThucThanhToan IN ('cod','bank_transfer')),
            TrangThaiThanhToan TEXT NOT NULL DEFAULT 'Chưa thanh toán',
            PhiVanChuyen REAL,
            GhiChu TEXT, NgayTao TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            NguoiThuTien INTEGER REFERENCES NguoiDung(MaNguoiDung),
            ThoiGianThanhToan TEXT
        )""")
        tx_cols = {r[1] for r in conn.execute("PRAGMA table_info(ThongTinGiaoDich)").fetchall()}
        if "NguoiThuTien" not in tx_cols:
            conn.execute("ALTER TABLE ThongTinGiaoDich ADD COLUMN NguoiThuTien INTEGER REFERENCES NguoiDung(MaNguoiDung)")
        if "ThoiGianThanhToan" not in tx_cols:
            conn.execute("ALTER TABLE ThongTinGiaoDich ADD COLUMN ThoiGianThanhToan TEXT")

        # Quản lý danh mục, thương hiệu, màu sắc, kích thước
        conn.execute("""CREATE TABLE IF NOT EXISTS ThuongHieu (
            MaThuongHieu INTEGER PRIMARY KEY AUTOINCREMENT,
            TenThuongHieu TEXT NOT NULL UNIQUE,
            MoTa TEXT
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS MauSac (
            MaMau INTEGER PRIMARY KEY AUTOINCREMENT,
            TenMau TEXT NOT NULL UNIQUE,
            MaHex TEXT,
            MoTa TEXT
        )""")
        ms_cols = {r[1] for r in conn.execute("PRAGMA table_info(MauSac)").fetchall()}
        if "MaHex" not in ms_cols:
            conn.execute("ALTER TABLE MauSac ADD COLUMN MaHex TEXT")

        conn.execute("""CREATE TABLE IF NOT EXISTS KichThuoc (
            MaKichThuoc INTEGER PRIMARY KEY AUTOINCREMENT,
            TenKichThuoc TEXT NOT NULL UNIQUE,
            TenSize TEXT,
            MoTa TEXT
        )""")
        kt_cols = {r[1] for r in conn.execute("PRAGMA table_info(KichThuoc)").fetchall()}
        if "TenKichThuoc" not in kt_cols and "TenSize" in kt_cols:
            conn.execute("ALTER TABLE KichThuoc ADD COLUMN TenKichThuoc TEXT")
            conn.execute("UPDATE KichThuoc SET TenKichThuoc = TenSize WHERE TenKichThuoc IS NULL")
        if "TenSize" not in kt_cols and "TenKichThuoc" in kt_cols:
            conn.execute("ALTER TABLE KichThuoc ADD COLUMN TenSize TEXT")
            conn.execute("UPDATE KichThuoc SET TenSize = TenKichThuoc WHERE TenSize IS NULL")
        if "MaKichThuoc" not in kt_cols and "MaSize" in kt_cols:
            conn.execute("ALTER TABLE KichThuoc ADD COLUMN MaKichThuoc INTEGER")
            conn.execute("UPDATE KichThuoc SET MaKichThuoc = MaSize WHERE MaKichThuoc IS NULL")

        if "MaThuongHieu" not in columns:
            conn.execute("ALTER TABLE SanPham ADD COLUMN MaThuongHieu INTEGER REFERENCES ThuongHieu(MaThuongHieu)")

        # Đồng bộ Thương hiệu, Màu sắc, Kích thước ban đầu nếu bảng đang trống
        brand_count = conn.execute("SELECT COUNT(*) FROM ThuongHieu").fetchone()[0]
        if brand_count == 0:
            brands = conn.execute("SELECT DISTINCT ThuongHieu FROM SanPham WHERE ThuongHieu IS NOT NULL AND TRIM(ThuongHieu) <> ''").fetchall()
            for (bname,) in brands:
                conn.execute("INSERT OR IGNORE INTO ThuongHieu (TenThuongHieu) VALUES (?)", (bname.strip(),))
        color_count = conn.execute("SELECT COUNT(*) FROM MauSac").fetchone()[0]
        if color_count == 0:
            colors = conn.execute("SELECT DISTINCT MauSac FROM BienTheSanPham WHERE MauSac IS NOT NULL AND TRIM(MauSac) <> ''").fetchall()
            for (cname,) in colors:
                conn.execute("INSERT OR IGNORE INTO MauSac (TenMau) VALUES (?)", (cname.strip(),))
        size_count = conn.execute("SELECT COUNT(*) FROM KichThuoc").fetchone()[0]
        if size_count == 0:
            sizes = conn.execute("SELECT DISTINCT KichThuoc FROM BienTheSanPham WHERE KichThuoc IS NOT NULL AND TRIM(KichThuoc) <> ''").fetchall()
            for (sname,) in sizes:
                conn.execute("INSERT OR IGNORE INTO KichThuoc (TenKichThuoc, TenSize) VALUES (?, ?)", (sname.strip(), sname.strip()))
        # Product image gallery: additive migration, keeps existing products intact.
        conn.execute("""CREATE TABLE IF NOT EXISTS SanPhamHinhAnh (
            MaHinhAnh INTEGER PRIMARY KEY AUTOINCREMENT,
            MaSanPham INTEGER NOT NULL REFERENCES SanPham(MaSanPham) ON DELETE CASCADE,
            TenTep TEXT NOT NULL,
            LaAnhDaiDien INTEGER NOT NULL DEFAULT 0 CHECK(LaAnhDaiDien IN (0,1)),
            ThuTu INTEGER NOT NULL DEFAULT 0,
            NgayTao TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")
        # Idempotent additive migration for the SQLite demo, no DROP or data loss.
        conn.execute("""CREATE TABLE IF NOT EXISTS YeuThich (
            MaNguoiDung INTEGER NOT NULL REFERENCES NguoiDung(MaNguoiDung) ON DELETE CASCADE,
            MaSanPham INTEGER NOT NULL REFERENCES SanPham(MaSanPham) ON DELETE CASCADE,
            PRIMARY KEY (MaNguoiDung, MaSanPham))""")
        # Đánh giá sản phẩm: migration cộng thêm, không xóa dữ liệu cũ.
        conn.execute("""CREATE TABLE IF NOT EXISTS DanhGiaSanPham (
            MaDanhGia INTEGER PRIMARY KEY AUTOINCREMENT,
            MaSanPham INTEGER NOT NULL REFERENCES SanPham(MaSanPham) ON DELETE CASCADE,
            MaNguoiDung INTEGER NOT NULL REFERENCES NguoiDung(MaNguoiDung),
            MaDonHang INTEGER NOT NULL REFERENCES DonHang(MaDonHang),
            SoSao INTEGER NOT NULL CHECK(SoSao BETWEEN 1 AND 5),
            TieuDe TEXT,
            NoiDung TEXT NOT NULL,
            PhanHoiShop TEXT,
            NgayPhanHoi TEXT,
            TrangThaiHienThi INTEGER NOT NULL DEFAULT 1 CHECK(TrangThaiHienThi IN (0,1)),
            NgayDanhGia TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(MaNguoiDung, MaSanPham, MaDonHang)
        )""")
        conn.execute("CREATE INDEX IF NOT EXISTS IX_DanhGiaSanPham_MaSanPham_TrangThai "
                     "ON DanhGiaSanPham(MaSanPham, TrangThaiHienThi, NgayDanhGia DESC)")
        # Nâng cấp seed demo cũ (10 SP) không xóa dữ liệu hay thay đổi ID cũ.
        # Không dùng cho SQL Server; trên SQL Server cần quy trình seed/migration test riêng.
        examples = [
            ("Sandal Học Sinh Chống Trượt", 3, 290000, "LocalShoes", "Test hết tồn", [ ("39", "Đỏ", 0), ("40", "Xanh", 0) ], 1),
            ("Giày Thể Thao Mẫu Ẩn", 1, 590000, "LocalShoes", "Test sản phẩm ẩn", [ ("41", "Đen", 8) ], 0),
        ]
        for name, category, price, brand, detail, variants, visible in examples:
            existing = conn.execute("SELECT MaSanPham FROM SanPham WHERE TenSanPham=?", (name,)).fetchone()
            if not existing:
                cur = conn.execute("INSERT INTO SanPham (MaDanhMuc,MaNguoiTao,TenSanPham,GiaBan,ThuongHieu,MoTa,HienThi) VALUES (?,?,?,?,?,?,?)",
                    (category, None, name, price, brand, detail, visible))
                pid = cur.lastrowid
            else:
                pid = int(existing[0])
            if not visible:
                conn.execute("UPDATE SanPham SET HienThi=0 WHERE MaSanPham=?", (pid,))
            for size, color, stock in variants:
                if not conn.execute("SELECT 1 FROM BienTheSanPham WHERE MaSanPham=? AND KichThuoc=? AND MauSac=?", (pid, size, color)).fetchone():
                    conn.execute("INSERT INTO BienTheSanPham(MaSanPham,KichThuoc,MauSac,SoLuongTon) VALUES(?,?,?,?)", (pid, size, color, stock))
        conn.commit()
    finally:
        conn.close()
