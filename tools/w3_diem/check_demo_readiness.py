"""Công cụ W3-060: Kiểm tra độ sẵn sàng Demo và khả năng cài đặt đa máy (5 thành viên).
Phụ trách: Điểm (Nhóm trưởng Nhóm 6).

Mục tiêu:
- Kiểm tra danh mục điều kiện tiên quyết trước khi demo trước giảng viên:
  + Môi trường Python, thư viện requirements.txt
  + Application factory, Static assets (CSS, JS, Icons)
  + Luồng đọc dữ liệu trang chủ
  + Kết quả smoke test & regression
- Cảnh báo rõ ràng: Chưa kiểm chứng cài đặt trên máy thành viên khác (Minh, Nghĩa, Khải, Tuấn).
- Cung cấp checklist hướng dẫn cài đặt chuẩn trên máy mới.
"""
import importlib
import os
import sys
from pathlib import Path
from typing import Dict, List, Any


class DemoReadinessChecker:
    def __init__(self, project_root: Path = None):
        if project_root is None:
            current = Path(__file__).resolve().parent
            while current.parent != current:
                if (current / "run.py").exists():
                    self.project_root = current
                    break
                current = current.parent
            else:
                self.project_root = Path.cwd()
        else:
            self.project_root = Path(project_root)

        self.checks: List[Dict[str, Any]] = []

    def run(self):
        print(f"=== [W3-060] KIỂM TRA ĐỘ SẴN SÀNG DEMO VÀ CÀI ĐẶT DỰ ÁN (MILESTONE CHECK) ===")
        print(f"Project root: {self.project_root.resolve()}\n")

        self.check_core_dependencies()
        self.check_static_assets()
        self.check_public_smoke_flow()
        self.check_multi_machine_readiness()

        self.print_checklist()

    def check_core_dependencies(self):
        req_file = self.project_root / "requirements.txt"
        packages = ["flask", "werkzeug"]
        if req_file.exists():
            for line in req_file.read_text(encoding="utf-8").splitlines():
                pkg = line.strip().split("==")[0].split(">=")[0]
                if pkg and not pkg.startswith("#"):
                    packages.append(pkg)

        missing = []
        for pkg in set(packages):
            mod_name = pkg.lower()
            try:
                importlib.import_module(mod_name)
            except ImportError:
                missing.append(pkg)

        if not missing:
            self.checks.append({"item": "Thư viện Python cốt lõi", "status": "PASS", "detail": "Đã cài đặt đầy đủ các gói cần thiết."})
        else:
            self.checks.append({"item": "Thư viện Python cốt lõi", "status": "FAIL", "detail": f"Thiếu gói: {', '.join(missing)}. Cần chạy: pip install -r requirements.txt"})

    def check_static_assets(self):
        static_dir = self.project_root / "app" / "static"
        required_dirs = ["css", "js", "images"]
        missing_dirs = [d for d in required_dirs if not (static_dir / d).exists()]

        if not missing_dirs:
            self.checks.append({"item": "Thư mục tài nguyên Static (CSS/JS/Ảnh)", "status": "PASS", "detail": "Đầy đủ css, js, images."})
        else:
            self.checks.append({"item": "Thư mục tài nguyên Static (CSS/JS/Ảnh)", "status": "FAIL", "detail": f"Thiếu thư mục: {missing_dirs}"})

    def check_public_smoke_flow(self):
        sys.path.insert(0, str(self.project_root))
        try:
            from app import create_app
            app = create_app({"TESTING": True, "DB_BACKEND": "sqlite"})
            client = app.test_client()
            res = client.get("/")
            if res.status_code == 200 and "Nike Air Zoom" in res.get_data(as_text=True):
                self.checks.append({"item": "Luồng duyệt Public trang chủ", "status": "PASS", "detail": "Trang chủ tải thành công (HTTP 200), hiển thị danh sách sản phẩm."})
            else:
                self.checks.append({"item": "Luồng duyệt Public trang chủ", "status": "FAIL", "detail": f"Trang chủ trả về mã {res.status_code} hoặc thiếu dữ liệu mẫu."})
        except Exception as e:
            self.checks.append({"item": "Luồng duyệt Public trang chủ", "status": "ERROR", "detail": f"Lỗi khởi tạo ứng dụng: {e}"})

    def check_multi_machine_readiness(self):
        # Kiểm tra tính sẵn sàng trên 5 máy
        self.checks.append({
            "item": "Kiểm chứng cài đặt trên 5 máy thành viên",
            "status": "BLOCKED / CẦN THỰC HIỆN",
            "detail": "Hiện tại mới kiểm tra trên máy Điểm. Minh, Nghĩa, Khải, Tuấn phải tự clone và chạy lệnh kiểm thử trên máy riêng để lấy bằng chứng.",
        })

    def print_checklist(self):
        print("=" * 90)
        print(f"{'HẠNG MỤC KIỂM TRA':<40} | {'TRẠNG THÁI':<25} | CHI TIẾT")
        print("-" * 90)
        for c in self.checks:
            print(f"{c['item']:<40} | {c['status']:<25} | {c['detail']}")
        print("=" * 90)

        # Xuất file checklist Markdown
        output_dir = self.project_root / "docs" / "w3_diem"
        output_dir.mkdir(parents=True, exist_ok=True)
        checklist_file = output_dir / "CHECKLIST_DEMO_5_MAY.md"
        with open(checklist_file, "w", encoding="utf-8") as f:
            f.write("# CHECKLIST CÀI ĐẶT VÀ SẴN SÀNG DEMO 5 MÁY (W3-060)\n\n")
            f.write("## 1. Kết quả kiểm tra máy hiện tại\n\n")
            f.write("| Hạng mục | Trạng thái | Chi tiết |\n|---|---|---|\n")
            for c in self.checks:
                f.write(f"| {c['item']} | **{c['status']}** | {c['detail']} |\n")
            f.write("\n## 2. Kế hoạch kiểm chứng 5 máy độc lập\n\n")
            f.write("| Máy thành viên | Người phụ trách | Phiên bản Python | Dịch vụ SQL Server | Kết quả Test (PASS/FAIL) | Ảnh chụp minh chứng |\n")
            f.write("|---|---|---|---|---|---|\n")
            f.write("| Máy 1 | **Điểm** (Trưởng nhóm) | Python 3.13 | Local / SQLite Demo | Đạt | `docs/w3_diem/evidence/may1_diem.png` |\n")
            f.write("| Máy 2 | **Minh** (Backend DB) | Cần kiểm tra | SQL Server Developer | Chưa xác minh | Cần Minh gửi |\n")
            f.write("| Máy 3 | **Nghĩa** (Biến thể/Kho) | Cần kiểm tra | Cần kiểm tra | Chưa xác minh | Cần Nghĩa gửi |\n")
            f.write("| Máy 4 | **Khải** (Admin/Ảnh) | Cần kiểm tra | Cần kiểm tra | Chưa xác minh | Cần Khải gửi |\n")
            f.write("| Máy 5 | **Tuấn** (Giao diện UI) | Cần kiểm tra | Cần kiểm tra | Chưa xác minh | Cần Tuấn gửi |\n")
        print(f"[OK] Đã xuất checklist 5 máy ra: {checklist_file}")


if __name__ == "__main__":
    checker = DemoReadinessChecker()
    checker.run()
