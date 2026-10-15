"""Công cụ W3-001: Kiểm kê kỹ thuật đầu vào và thẩm định môi trường chạy dự án.
Phụ trách: Điểm (Nhóm trưởng Nhóm 6).

Đảm bảo:
- Chỉ thực hiện truy vấn CHỈ ĐỌC.
- Không in mật khẩu database ra màn hình hay log.
- Phân loại rõ ràng: PASS, FAIL, BLOCKED, NOT RUN.
- Ghi nhận đầy đủ phát hiện kỹ thuật và dấu hiệu code cũ.
"""
import importlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Any


def mask_connection_string(conn_str: str) -> str:
    """Che mật khẩu trong connection string để đảm bảo an toàn thông tin."""
    if not conn_str:
        return "(Trống - Chưa cấu hình)"
    # Thay thế Password=..., PWD=..., hoặc giá trị nhạy cảm
    masked = re.sub(r"(PWD|Password)=([^;]+)", r"\1=********", conn_str, flags=re.IGNORECASE)
    return masked


class EnvironmentChecker:
    def __init__(self, project_root: Path = None):
        if project_root is None:
            # Tự động tìm thư mục chứa run.py
            current = Path(__file__).resolve().parent
            while current.parent != current:
                if (current / "run.py").exists() and (current / "app" / "__init__.py").exists():
                    self.project_root = current
                    break
                current = current.parent
            else:
                self.project_root = Path.cwd()
        else:
            self.project_root = Path(project_root)

        self.results: List[Dict[str, Any]] = []

    def record(self, check_id: str, title: str, status: str, detail: str, evidence: Any = None):
        self.results.append({
            "id": check_id,
            "title": title,
            "status": status,
            "detail": detail,
            "evidence": evidence or {},
        })

    def run_all(self):
        print(f"=== [W3-001] BẮT ĐẦU KIỂM KÊ KỸ THUẬT VÀ MÔI TRƯỜNG DỰ ÁN ===")
        print(f"Project Root xác định: {self.project_root.resolve()}\n")

        self.check_python_version()
        self.check_flask_import()
        self.check_project_files()
        self.check_app_factory_and_routes()
        self.check_database_config_and_readonly()
        self.detect_legacy_demo_code()

        return self.results

    def check_python_version(self):
        v = sys.version_info
        ver_str = f"{v.major}.{v.minor}.{v.micro}"
        if v.major == 3 and v.minor >= 10:
            self.record("ENV-01", "Kiểm tra phiên bản Python", "PASS",
                        f"Python {ver_str} đạt chuẩn yêu cầu (>= 3.10)", {"python_version": ver_str})
        else:
            self.record("ENV-01", "Kiểm tra phiên bản Python", "FAIL",
                        f"Python {ver_str} không khuyến nghị. Dự án cần Python 3.10+", {"python_version": ver_str})

    def check_flask_import(self):
        try:
            import flask
            self.record("ENV-02", "Khả năng import Flask", "PASS",
                        f"Flask {flask.__version__} đã được cài đặt và import thành công.", {"flask_version": flask.__version__})
        except ImportError as e:
            self.record("ENV-02", "Khả năng import Flask", "FAIL",
                        f"Không thể import Flask: {e}", {})

    def check_project_files(self):
        required_files = [
            ("run.py", "File khởi chạy Flask"),
            ("requirements.txt", "Tệp khai báo thư viện"),
            ("app/__init__.py", "Application factory"),
            ("app/routes.py", "Khai báo routes"),
            ("app/db.py", "Kết nối cơ sở dữ liệu"),
            ("app/data.py", "Hàm truy vấn dữ liệu"),
            ("database/schema.sql", "Script SQL Server"),
            ("tests/test_smoke.py", "Bộ smoke test Tuần 2"),
        ]
        missing = []
        for rel_path, desc in required_files:
            full = self.project_root / rel_path
            if not full.exists():
                missing.append(f"{rel_path} ({desc})")

        if not missing:
            self.record("ENV-03", "Kiểm tra các tệp bắt buộc", "PASS",
                        "Tất cả các tệp cốt lõi của dự án đều tồn tại đầy đủ.", {"checked": len(required_files)})
        else:
            self.record("ENV-03", "Kiểm tra các tệp bắt buộc", "FAIL",
                        f"Thiếu các tệp sau: {', '.join(missing)}", {"missing": missing})

    def check_app_factory_and_routes(self):
        sys.path.insert(0, str(self.project_root))
        try:
            from app import create_app
            app = create_app({"TESTING": True, "DB_BACKEND": "sqlite"})
            routes_list = []
            for rule in app.url_map.iter_rules():
                routes_list.append({
                    "endpoint": rule.endpoint,
                    "methods": sorted([m for m in rule.methods if m not in {"HEAD", "OPTIONS"}]),
                    "rule": str(rule),
                })
            self.record("ENV-04", "Kiểm tra Flask Application Factory & Routes", "PASS",
                        f"Khởi tạo app thành công, phát hiện {len(routes_list)} routes.",
                        {"total_routes": len(routes_list), "routes": routes_list})
        except Exception as e:
            self.record("ENV-04", "Kiểm tra Flask Application Factory & Routes", "FAIL",
                        f"Lỗi khi khởi tạo create_app: {e}", {})

    def check_database_config_and_readonly(self):
        db_backend = os.getenv("DB_BACKEND", "sqlite").lower()
        sqlserver_conn = os.getenv("SQLSERVER_CONN", "")
        masked_conn = mask_connection_string(sqlserver_conn)

        self.record("ENV-05", "Kiểm tra cấu hình Database", "PASS",
                    f"Backend hiện tại: {db_backend}. Chuỗi kết nối SQL Server: {masked_conn}",
                    {"backend": db_backend, "sqlserver_configured": bool(sqlserver_conn)})

        # Kiểm tra kết nối SQL Server (nếu cấu hình)
        if db_backend == "sqlserver" or sqlserver_conn:
            try:
                import pyodbc
                conn = pyodbc.connect(sqlserver_conn, timeout=3)
                cursor = conn.cursor()
                # CHỈ ĐỌC: Kiểm tra phiên bản SQL Server và tên database
                cursor.execute("SELECT @@VERSION, DB_NAME()")
                version, db_name = cursor.fetchone()

                # Kiểm tra danh sách bảng
                cursor.execute("""
                    SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_TYPE='BASE TABLE' ORDER BY TABLE_NAME
                """)
                tables = [r[0] for r in cursor.fetchall()]
                conn.close()

                self.record("ENV-06", "Kiểm tra kết nối SQL Server (Chỉ đọc)", "PASS",
                            f"Kết nối SQL Server thành công tới database: '{db_name}'. Số bảng: {len(tables)}",
                            {"database": db_name, "tables": tables, "sql_version": version[:50]})
            except ImportError:
                self.record("ENV-06", "Kiểm tra kết nối SQL Server (Chỉ đọc)", "BLOCKED",
                            "Chưa cài đặt thư viện 'pyodbc' trên môi trường Python này.", {})
            except Exception as e:
                self.record("ENV-06", "Kiểm tra kết nối SQL Server (Chỉ đọc)", "BLOCKED",
                            f"Chưa thể kết nối tới SQL Server: {e}. Vui lòng kiểm tra dịch vụ và mạng.", {})
        else:
            self.record("ENV-06", "Kiểm tra kết nối SQL Server (Chỉ đọc)", "BLOCKED",
                        "Môi trường chưa đặt biến SQLSERVER_CONN hoặc DB_BACKEND đang là sqlite.",
                        {"note": "Không thể kết luận SQL Server PASS khi chưa kết nối thật."})

    def detect_legacy_demo_code(self):
        """Phát hiện các điểm code demo Tuần 2 chưa được nâng cấp lên Tuần 3."""
        findings = []
        routes_file = self.project_root / "app" / "routes.py"
        data_file = self.project_root / "app" / "data.py"
        schema_file = self.project_root / "database" / "schema.sql"

        if routes_file.exists():
            text = routes_file.read_text(encoding="utf-8", errors="ignore")
            if "CHƯA lưu sản phẩm" in text:
                findings.append("app/routes.py: Form thêm sản phẩm admin vẫn đang ở chế độ demo (chưa INSERT DB).")
            if "price >= 0" in text:
                findings.append("app/routes.py: Kiểm tra giá vẫn cho phép price == 0 (vi phạm quy tắc mới A07: giá > 0).")

        if data_file.exists():
            text = data_file.read_text(encoding="utf-8", errors="ignore")
            if "TrangThai" not in text and "DaAn" not in text:
                findings.append("app/data.py: Truy vấn sản phẩm chưa lọc sản phẩm ẩn (chưa đáp ứng quy tắc A02).")
            if "brand_id" not in text and "price_min" not in text:
                findings.append("app/data.py: Chưa triển khai bộ lọc mở rộng theo API Contract (brand, type, color, size, price).")

        if schema_file.exists():
            text = schema_file.read_text(encoding="utf-8", errors="ignore")
            if "QuanLyBanHang" in text:
                findings.append("database/schema.sql: Vẫn dùng tên DB cũ 'QuanLyBanHang', chưa đổi sang 'quan_ly_giay_dep'.")
            if "DROP TABLE IF EXISTS" in text:
                findings.append("database/schema.sql: Có lệnh DROP TABLE nguy hiểm; TUYỆT ĐỐI không chạy trên DB chính.")

        if findings:
            self.record("ENV-07", "Phát hiện mã nguồn demo chưa hoàn thiện của Tuần 3", "FAIL",
                        f"Phát hiện {len(findings)} điểm cần khắc phục/ghép mã nguồn từ các thành viên.",
                        {"findings": findings})
        else:
            self.record("ENV-07", "Phát hiện mã nguồn demo chưa hoàn thiện của Tuần 3", "PASS",
                        "Mã nguồn đã đồng bộ hoàn chỉnh các quy tắc tuần 3.", {})

    def print_summary(self):
        print("\n" + "=" * 80)
        print(f"{'MÃ':<10} | {'TRẠNG THÁI':<12} | {'NỘI DUNG':<35} | CHI TIẾT")
        print("-" * 80)
        for r in self.results:
            status_color = r["status"]
            print(f"{r['id']:<10} | {status_color:<12} | {r['title'][:35]:<35} | {r['detail'][:60]}")
        print("=" * 80)

        # Lưu file báo cáo
        output_dir = self.project_root / "docs" / "w3_diem"
        output_dir.mkdir(parents=True, exist_ok=True)
        report_file = output_dir / "BAO_CAO_KIEM_KE_MOI_TRUONG.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"\n[OK] Đã xuất báo cáo chi tiết ra: {report_file}")


if __name__ == "__main__":
    checker = EnvironmentChecker()
    checker.run_all()
    checker.print_summary()
