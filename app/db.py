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
        for col in ("Ho", "Ten", "GioiTinh", "NgaySinh", "TinhThanh", "PhuongXa"):
            if col not in user_cols:
                conn.execute(f"ALTER TABLE NguoiDung ADD COLUMN {col} TEXT")
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
        _upgrade_sqlite_w4(conn)
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


W4_DONHANG_COLUMNS = (
    ("LaDonCu", "INTEGER NOT NULL DEFAULT 0"),
    ("HinhThucNhanHang", "TEXT NOT NULL DEFAULT 'delivery'"),
    ("TenNguoiNhan", "TEXT"), ("SdtNguoiNhan", "TEXT"), ("DiaChiGiaoHang", "TEXT"),
    ("PhiVanChuyen", "REAL NOT NULL DEFAULT 0"),
    ("PhuongThucThanhToan", "TEXT NOT NULL DEFAULT 'COD'"),
    ("TrangThaiThanhToan", "TEXT NOT NULL DEFAULT 'Chưa thanh toán'"),
    ("TrangThaiXacNhan", "TEXT NOT NULL DEFAULT 'Chờ xác nhận'"),
    ("MaNVXacNhan", "INTEGER REFERENCES NguoiDung(MaNguoiDung)"), ("ThoiDiemXacNhan", "TEXT"),
    ("TrangThaiGiaoHang", "TEXT NOT NULL DEFAULT 'Chưa giao'"),
    ("MaNVCapNhatGiaoHang", "INTEGER REFERENCES NguoiDung(MaNguoiDung)"), ("ThoiDiemCapNhatGiaoHang", "TEXT"),
    ("DaHuy", "INTEGER NOT NULL DEFAULT 0"), ("ThoiDiemHuy", "TEXT"),
    ("DaTruKho", "INTEGER NOT NULL DEFAULT 0"),
)


def _upgrade_sqlite_w4(conn):
    """W4-007 cho SQLite demo: bổ sung cột/bảng giao nhận-thanh toán, chuyển đổi đơn cũ, KHÔNG xóa dữ liệu.

    Tương đương migration_w4_giao_dich_sqlserver.sql (cùng mapping trạng thái cũ -> mới).
    """
    cols = {r[1] for r in conn.execute("PRAGMA table_info(DonHang)").fetchall()}
    fresh = "LaDonCu" not in cols
    for name, ddl in W4_DONHANG_COLUMNS:
        if name not in cols:
            conn.execute(f"ALTER TABLE DonHang ADD COLUMN {name} {ddl}")
    ct = {r[1] for r in conn.execute("PRAGMA table_info(ChiTietDonHang)").fetchall()}
    for name in ("TenSanPham", "MauSac", "KichThuoc"):
        if name not in ct:
            conn.execute(f"ALTER TABLE ChiTietDonHang ADD COLUMN {name} TEXT")
    if fresh:  # chỉ chuyển đổi đúng một lần, lúc vừa thêm cột
        conn.execute("""UPDATE DonHang SET LaDonCu=1, DaTruKho=0, HinhThucNhanHang='pickup',
            TrangThaiXacNhan=CASE WHEN TrangThai IN ('Đã xác nhận','Hoàn thành') THEN 'Đã xác nhận' ELSE 'Chờ xác nhận' END,
            ThoiDiemXacNhan=CASE WHEN TrangThai IN ('Đã xác nhận','Hoàn thành') THEN NgayDat END,
            TrangThaiGiaoHang=CASE WHEN TrangThai='Hoàn thành' THEN 'Đã giao' ELSE 'Chưa giao' END,
            ThoiDiemCapNhatGiaoHang=CASE WHEN TrangThai='Hoàn thành' THEN NgayDat END,
            DaHuy=CASE WHEN TrangThai='Đã hủy' THEN 1 ELSE 0 END,
            ThoiDiemHuy=CASE WHEN TrangThai='Đã hủy' THEN NgayDat END,
            TenNguoiNhan=(SELECT HoVaTen FROM NguoiDung nd WHERE nd.MaNguoiDung=DonHang.MaNguoiDung)""")
        has_meta = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='ThongTinGiaoDich'").fetchone()
        if has_meta:
            conn.execute("""UPDATE DonHang SET
                TenNguoiNhan=COALESCE((SELECT HoTen FROM ThongTinGiaoDich t WHERE t.MaDonHang=DonHang.MaDonHang), TenNguoiNhan),
                SdtNguoiNhan=(SELECT SoDienThoai FROM ThongTinGiaoDich t WHERE t.MaDonHang=DonHang.MaDonHang),
                HinhThucNhanHang=COALESCE((SELECT HinhThucNhanHang FROM ThongTinGiaoDich t WHERE t.MaDonHang=DonHang.MaDonHang),'pickup'),
                DiaChiGiaoHang=(SELECT DiaChiGiaoHang FROM ThongTinGiaoDich t WHERE t.MaDonHang=DonHang.MaDonHang),
                PhuongThucThanhToan=CASE WHEN (SELECT PhuongThucThanhToan FROM ThongTinGiaoDich t WHERE t.MaDonHang=DonHang.MaDonHang)='bank_transfer'
                                         THEN 'Chuyển khoản' ELSE 'COD' END""")
    conn.execute("""UPDATE ChiTietDonHang SET
        TenSanPham=(SELECT sp.TenSanPham FROM BienTheSanPham bt JOIN SanPham sp ON sp.MaSanPham=bt.MaSanPham WHERE bt.MaBienThe=ChiTietDonHang.MaBienThe),
        MauSac=(SELECT MauSac FROM BienTheSanPham bt WHERE bt.MaBienThe=ChiTietDonHang.MaBienThe),
        KichThuoc=(SELECT KichThuoc FROM BienTheSanPham bt WHERE bt.MaBienThe=ChiTietDonHang.MaBienThe)
        WHERE TenSanPham IS NULL""")
    conn.execute("""CREATE TABLE IF NOT EXISTS GiaoDichThanhToan (
        MaGiaoDich INTEGER PRIMARY KEY AUTOINCREMENT,
        MaDonHang INTEGER NOT NULL REFERENCES DonHang(MaDonHang),
        PhuongThuc TEXT NOT NULL CHECK(PhuongThuc IN ('COD','Chuyển khoản','Ví điện tử','Thẻ')),
        SoTien REAL NOT NULL CHECK(SoTien>=0),
        TrangThai TEXT NOT NULL DEFAULT 'Chờ xử lý' CHECK(TrangThai IN ('Chờ xử lý','Thành công','Thất bại','Hoàn tiền')),
        MaThamChieu TEXT, GhiChu TEXT,
        NgayTao TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, NgayCapNhat TEXT)""")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS UX_GDTT_MaThamChieu ON GiaoDichThanhToan(MaThamChieu) WHERE MaThamChieu IS NOT NULL")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS UX_GDTT_MotThanhCong ON GiaoDichThanhToan(MaDonHang) WHERE TrangThai='Thành công'")
