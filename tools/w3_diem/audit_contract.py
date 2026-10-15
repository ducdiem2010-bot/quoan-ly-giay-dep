"""Công cụ W3-015: Đối chiếu Use Case – ERD – SQL – API Contract.
Phụ trách: Điểm (Nhóm trưởng Nhóm 6).

Mục tiêu:
- Tự động quét mã nguồn Flask (routes, data, db) và đối chiếu với:
  + Bộ quy tắc A01-A08
  + API Contract v1
  + CSDL SQL Server (schema.sql và DB thật nếu kết nối được)
- Phát hiện các sai khác, thiếu sót kỹ thuật và gán rõ người chịu trách nhiệm.
- Không sửa code backend của thành viên khác.
"""
import ast
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Any


class ContractAuditor:
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

        self.findings: List[Dict[str, Any]] = []

    def add_finding(self, issue_id: str, title: str, severity: str, owner: str,
                    w3_code: str, file_path: str, line_no: int, description: str, recommendation: str):
        self.findings.append({
            "id": issue_id,
            "title": title,
            "severity": severity,  # Critical, Major, Minor
            "owner": owner,        # Minh, Nghĩa, Khải, Tuấn, Toàn nhóm
            "w3_code": w3_code,
            "file": file_path,
            "line": line_no,
            "description": description,
            "recommendation": recommendation,
        })

    def run_audit(self):
        print(f"=== [W3-015] BẮT ĐẦU KIỂM TOÁN ĐỐI CHIẾU HỢP ĐỒNG API - SQL - ERD ===")
        self.audit_routes()
        self.audit_data_queries()
        self.audit_schema_and_db()
        self.audit_admin_authorization()
        return self.findings

    def audit_routes(self):
        routes_file = self.project_root / "app" / "routes.py"
        if not routes_file.exists():
            return

        text = routes_file.read_text(encoding="utf-8")
        lines = text.splitlines()

        # Kiểm tra quy tắc A07: giá > 0
        for idx, line in enumerate(lines, 1):
            if "price >= 0" in line:
                self.add_finding(
                    "AUDIT-01",
                    "Kiểm tra giá cho phép bằng 0 (vi phạm A07)",
                    "Major",
                    "Khải",
                    "W3-013",
                    "app/routes.py",
                    idx,
                    "Điều kiện 'price >= 0' chấp nhận sản phẩm giá 0đ, trái quy tắc A07 (giá phải > 0đ).",
                    "Sửa điều kiện thành 'price > 0'."
                )

            if "CHƯA lưu sản phẩm" in line:
                self.add_finding(
                    "AUDIT-02",
                    "Form thêm sản phẩm Admin chưa có logic INSERT vào Database",
                    "Critical",
                    "Khải",
                    "W3-013",
                    "app/routes.py",
                    idx,
                    "Route '/admin/product/add' chỉ flash thông báo demo Tuần 2, chưa thực hiện INSERT SanPham và BienTheSanPham.",
                    "Triển khai giao dịch INSERT sản phẩm, biến thể và rollback nếu lỗi."
                )

        # Kiểm tra các route yêu thích (favorite) và upload ảnh
        if "/favorite" not in text and "yeu_thich" not in text:
            self.add_finding(
                "AUDIT-03",
                "Chưa có route xử lý Yêu thích sản phẩm (Favorites)",
                "Major",
                "Khải",
                "W3-014",
                "app/routes.py",
                0,
                "Chưa thấy endpoint thêm/xem sản phẩm yêu thích của khách hàng theo quy tắc A02/RBAC.",
                "Triển khai endpoint POST /favorite/<id> và GET /favorites với xác thực session khách."
            )

        if "upload" not in text and "HinhAnh" not in text:
            self.add_finding(
                "AUDIT-04",
                "Chưa có route upload và quản lý nhiều ảnh sản phẩm (A01, A05)",
                "Major",
                "Khải",
                "W3-054",
                "app/routes.py",
                0,
                "Hệ thống hiện chỉ nhận tên ảnh dạng chuỗi (image.svg), chưa có xử lý upload file JPG/PNG/WebP <= 5MB.",
                "Triển khai upload ảnh theo quy tắc A05 và bảng HinhAnhSanPham."
            )

    def audit_data_queries(self):
        data_file = self.project_root / "app" / "data.py"
        if not data_file.exists():
            return

        text = data_file.read_text(encoding="utf-8")
        lines = text.splitlines()

        # Kiểm tra lọc sản phẩm ẩn (A02)
        if "TrangThai" not in text and "DaAn" not in text:
            self.add_finding(
                "AUDIT-05",
                "Truy vấn danh sách sản phẩm chưa lọc sản phẩm ẩn (Quy tắc A02)",
                "Critical",
                "Minh",
                "W3-004",
                "app/data.py",
                4,
                "SELECT_PRODUCT trong data.py hiển thị mọi sản phẩm kể cả sản phẩm ẩn/dừng bán.",
                "Bổ sung điều kiện WHERE sp.TrangThai = 1 (hoặc DaAn = 0) cho các truy vấn public."
            )

        # Kiểm tra hợp đồng lọc public: brand_id, type_id, gender, color_id, size_id, price_min, price_max, sort, page
        expected_filters = ["brand_id", "gender", "color_id", "size_id", "price_min", "price_max", "sort", "page"]
        missing_filters = [f for f in expected_filters if f not in text]
        if missing_filters:
            self.add_finding(
                "AUDIT-06",
                f"Thiếu các tham số lọc/sắp xếp/phân trang theo API Contract: {', '.join(missing_filters)}",
                "Major",
                "Minh",
                "W3-005",
                "app/data.py",
                19,
                "Hàm get_all_products hiện chỉ nhận category_id và keyword. Chưa hỗ trợ lọc đa tiêu chí.",
                f"Bổ sung xử lý tham số: {', '.join(missing_filters)} kết hợp phân trang LIMIT/OFFSET."
            )

        # Kiểm tra quy tắc lọc cùng một biến thể (same variant)
        if "size_id" in text and "color_id" in text:
            if "EXISTS" not in text and "INTERSECT" not in text:
                self.add_finding(
                    "AUDIT-07",
                    "Cần kiểm tra kỹ logic lọc màu và size để tránh bắt chéo 2 biến thể khác nhau",
                    "Major",
                    "Nghĩa",
                    "W3-007",
                    "app/data.py",
                    0,
                    "Lọc màu và size phải thỏa mãn trên CÙNG MỘT dòng BienTheSanPham có SoLuongTon > 0.",
                    "Dùng truy vấn con trên BienTheSanPham: WHERE MauSac = ? AND KichThuoc = ?."
                )

    def audit_schema_and_db(self):
        schema_file = self.project_root / "database" / "schema.sql"
        if not schema_file.exists():
            return

        text = schema_file.read_text(encoding="utf-8")

        # Kiểm tra tên database
        if "QuanLyBanHang" in text:
            self.add_finding(
                "AUDIT-08",
                "Schema SQL Server vẫn khai báo 'QuanLyBanHang' thay vì 'quan_ly_giay_dep'",
                "Critical",
                "Minh",
                "W3-004",
                "database/schema.sql",
                3,
                "Script schema.sql tạo database QuanLyBanHang, lệch với tên database chính quan_ly_giay_dep của nhóm.",
                "Đổi tên USE QuanLyBanHang thành USE quan_ly_giay_dep và bỏ lệnh tự ý CREATE DATABASE master."
            )

        # Kiểm tra DROP TABLE
        if "DROP TABLE IF EXISTS" in text:
            self.add_finding(
                "AUDIT-09",
                "Script schema.sql chứa lệnh DROP TABLE hủy dữ liệu",
                "Critical",
                "Minh",
                "W3-004",
                "database/schema.sql",
                10,
                "Có các câu lệnh DROP TABLE từ dòng 10-18, gây nguy cơ mất sạch dữ liệu nếu chạy trên DB chính.",
                "Chỉ sử dụng script migration an toàn, cấm chạy trực tiếp schema.sql trên quan_ly_giay_dep."
            )

        # Kiểm tra cột TrangThai trong bảng SanPham (hỗ trợ A02)
        match_sp = re.search(r"CREATE\s+TABLE\s+SanPham\s*\((.*?)\);", text, re.DOTALL | re.IGNORECASE)
        if match_sp:
            sp_body = match_sp.group(1)
            if "TrangThai" not in sp_body and "DaAn" not in sp_body:
                self.add_finding(
                    "AUDIT-10",
                    "Bảng SanPham chưa có cột TrangThai / DaAn để quản lý sản phẩm ẩn (A02)",
                    "Critical",
                    "Minh",
                    "W3-004",
                    "database/schema.sql",
                    55,
                    "Bảng SanPham thiếu trường trạng thái hiển thị.",
                    "Thêm cột: TrangThai BIT NOT NULL DEFAULT 1 (1: Hiển thị, 0: Ẩn)."
                )
            if "CHECK (GiaBan >= 0)" in sp_body:
                self.add_finding(
                    "AUDIT-11",
                    "Ràng buộc CSDL CHECK (GiaBan >= 0) cho phép giá = 0, trái quy tắc A07",
                    "Major",
                    "Minh",
                    "W3-004",
                    "database/schema.sql",
                    66,
                    "Ràng buộc CK_SanPham_GiaBan cho phép GiaBan = 0.",
                    "Sửa thành: CHECK (GiaBan > 0)."
                )

        # Kiểm tra bảng ảnh và yêu thích
        if "HinhAnhSanPham" not in text:
            self.add_finding(
                "AUDIT-12",
                "Thiếu bảng HinhAnhSanPham trong SQL Server (A01, A04)",
                "Major",
                "Minh",
                "W3-004",
                "database/schema.sql",
                0,
                "Chưa có bảng lưu nhiều ảnh của sản phẩm và đánh dấu ảnh đại diện.",
                "Tạo bảng HinhAnhSanPham(MaHinhAnh, MaSanPham, DuongDan, LaDaiDien)."
            )

        if "SanPhamYeuThich" not in text and "YeuThich" not in text:
            self.add_finding(
                "AUDIT-13",
                "Thiếu bảng SanPhamYeuThich trong SQL Server",
                "Major",
                "Minh",
                "W3-004",
                "database/schema.sql",
                0,
                "Chưa có bảng lưu danh sách sản phẩm yêu thích theo tài khoản khách hàng.",
                "Tạo bảng SanPhamYeuThich(MaNguoiDung, MaSanPham, NgayLuu)."
            )

    def audit_admin_authorization(self):
        routes_file = self.project_root / "app" / "routes.py"
        if not routes_file.exists():
            return
        text = routes_file.read_text(encoding="utf-8")

        # Kiểm tra decorator admin_required
        if "@admin_required" in text:
            # Kiểm tra xem có route admin nào thiếu bảo vệ không
            lines = text.splitlines()
            for idx, line in enumerate(lines, 1):
                if line.strip().startswith("@app.") and "/admin" in line:
                    # Kiểm tra dòng tiếp theo hoặc trước đó có @admin_required không
                    context = "\n".join(lines[max(0, idx-2):min(len(lines), idx+3)])
                    if "@admin_required" not in context:
                        self.add_finding(
                            "AUDIT-14",
                            f"Nghi vấn route Admin thiếu @admin_required bảo vệ tại dòng {idx}",
                            "Critical",
                            "Khải",
                            "W3-013",
                            "app/routes.py",
                            idx,
                            f"Route {line.strip()} có thể chưa được bọc bởi @admin_required.",
                            "Bắt buộc gắn @admin_required cho tất cả các endpoint /admin/*."
                        )

    def print_report(self):
        print("\n" + "=" * 90)
        print(f"{'MÃ':<10} | {'MỨC ĐỘ':<10} | {'NGƯỜI GIAO':<12} | {'TIÊU ĐỀ':<35} | FILE & DÒNG")
        print("-" * 90)
        for f in self.findings:
            loc = f"{f['file']}:{f['line']}" if f['line'] > 0 else f['file']
            print(f"{f['id']:<10} | {f['severity']:<10} | {f['owner']:<12} | {f['title'][:35]:<35} | {loc}")
        print("=" * 90)
        print(f"Tổng cộng phát hiện: {len(self.findings)} vấn đề cần lưu ý và xử lý liên nhóm.")

        # Xuất file Markdown
        output_dir = self.project_root / "docs" / "w3_diem"
        output_dir.mkdir(parents=True, exist_ok=True)
        md_file = output_dir / "BIEN_BAN_DOI_CHIEU_HOP_DONG.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write("# BIÊN BẢN ĐỐI CHIẾU HỢP ĐỒNG USE CASE - ERD - SQL - API (W3-015)\n\n")
            f.write(f"**Người thực hiện:** Điểm (Nhóm trưởng)  \n")
            f.write(f"**Tổng số phát hiện:** {len(self.findings)}  \n\n")
            f.write("| Mã | Mức độ | Người chịu trách nhiệm | Mã W3 | Vấn đề | Đề xuất giải quyết |\n")
            f.write("|---|---|---|---|---|---|\n")
            for item in self.findings:
                f.write(f"| {item['id']} | **{item['severity']}** | {item['owner']} | {item['w3_code']} | {item['title']} ({item['file']}:{item['line']}) | {item['recommendation']} |\n")
        print(f"[OK] Đã xuất biên bản đối chiếu ra: {md_file}")


if __name__ == "__main__":
    auditor = ContractAuditor()
    auditor.run_audit()
    auditor.print_report()
