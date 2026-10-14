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
    finally:
        conn.close()
