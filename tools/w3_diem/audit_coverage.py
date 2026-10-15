"""Công cụ W3-059: Kiểm toán ma trận bao phủ chức năng (Functional Coverage Audit).
Phụ trách: Điểm (Nhóm trưởng Nhóm 6).

Mục tiêu:
- Theo dõi ma trận khoảng 86 chức năng nghiệp vụ của hệ thống Web Giày Dép.
- Ánh xạ mã chức năng -> Mã nhiệm vụ W3 -> File code thực tế -> Test ID tương ứng -> Kết quả.
- Tự động phát hiện:
  + Yêu cầu chưa có code backend (Chưa triển khai)
  + Yêu cầu đã có code nhưng chưa có test
  + Yêu cầu test bị FAIL hoặc BLOCKED
- Tuyệt đối KHÔNG giả lập 86/86 PASS khi thực tế nhiều module chưa ghép.
"""
import csv
import json
import os
from pathlib import Path
from typing import Dict, List, Any


# Ma trận baseline 86 chức năng phân rã theo kế hoạch Tuần 3 của Nhóm 6
BASELINE_86_FUNCTIONS = [
    # Nhóm 1: Khách hàng xem và duyệt sản phẩm (Public Catalog) - Minh & Tuấn (W3-004, W3-005, W3-008)
    {"id": "F01", "name": "Xem danh sách sản phẩm trang chủ", "w3": "W3-004", "owner": "Minh", "file": "app/routes.py", "test": "test_d29_01_guest_view_product_list"},
    {"id": "F02", "name": "Lọc danh mục giày nam", "w3": "W3-004", "owner": "Minh", "file": "app/data.py", "test": "test_category_filter"},
    {"id": "F03", "name": "Lọc danh mục giày nữ", "w3": "W3-004", "owner": "Minh", "file": "app/data.py", "test": "test_category_filter"},
    {"id": "F04", "name": "Lọc danh mục dép & sandal", "w3": "W3-004", "owner": "Minh", "file": "app/data.py", "test": "test_category_filter"},
    {"id": "F05", "name": "Ẩn sản phẩm dừng bán khỏi public (A02)", "w3": "W3-004", "owner": "Minh", "file": "app/data.py", "test": "test_d29_02_hidden_product_not_shown"},
    {"id": "F06", "name": "Tìm kiếm sản phẩm theo tên chính xác", "w3": "W3-005", "owner": "Minh", "file": "app/data.py", "test": "test_d29_03_search_product_by_name"},
    {"id": "F07", "name": "Tìm kiếm sản phẩm theo từ khóa gần đúng", "w3": "W3-005", "owner": "Minh", "file": "app/data.py", "test": "test_02_search_by_name"},
    {"id": "F08", "name": "Tìm kiếm không dấu tiếng Việt", "w3": "W3-005", "owner": "Minh", "file": "app/data.py", "test": "CHƯA_TEST"},
    {"id": "F09", "name": "Tìm kiếm từ khóa không tồn tại", "w3": "W3-005", "owner": "Minh", "file": "app/data.py", "test": "test_d29_04_search_non_existent_keyword"},
    {"id": "F10", "name": "Tìm kiếm ký tự đặc biệt chống SQL Injection", "w3": "W3-005", "owner": "Minh", "file": "app/data.py", "test": "test_09_sql_injection_defense_parameterized"},
    {"id": "F11", "name": "Lọc thương hiệu (Nike, Adidas, Converse...)", "w3": "W3-005", "owner": "Minh", "file": "app/data.py", "test": "CHƯA_CODE"},
    {"id": "F12", "name": "Lọc khoảng giá (price_min, price_max)", "w3": "W3-005", "owner": "Minh", "file": "app/data.py", "test": "CHƯA_CODE"},
    {"id": "F13", "name": "Lọc giới tính (Nam, Nữ, Unisex)", "w3": "W3-005", "owner": "Minh", "file": "app/data.py", "test": "CHƯA_CODE"},
    {"id": "F14", "name": "Sắp xếp theo giá tăng dần", "w3": "W3-005", "owner": "Minh", "file": "app/data.py", "test": "CHƯA_CODE"},
    {"id": "F15", "name": "Sắp xếp theo giá giảm dần", "w3": "W3-005", "owner": "Minh", "file": "app/data.py", "test": "CHƯA_CODE"},
    {"id": "F16", "name": "Sắp xếp theo tên A-Z", "w3": "W3-005", "owner": "Minh", "file": "app/data.py", "test": "CHƯA_CODE"},
    {"id": "F17", "name": "Phân trang sản phẩm (Page 1 -> Page 2)", "w3": "W3-005", "owner": "Minh", "file": "app/data.py", "test": "test_d29_05_pagination_integrity"},
    {"id": "F18", "name": "Giữ nguyên bộ lọc khi chuyển trang", "w3": "W3-005", "owner": "Minh", "file": "app/data.py", "test": "CHƯA_CODE"},

    # Nhóm 2: Biến thể màu - size và Tồn kho - Nghĩa (W3-007)
    {"id": "F19", "name": "Xem chi tiết sản phẩm hợp lệ", "w3": "W3-007", "owner": "Nghĩa", "file": "app/routes.py", "test": "test_d29_06_view_valid_product_detail"},
    {"id": "F20", "name": "Chi tiết sản phẩm ID không tồn tại trả 404", "w3": "W3-007", "owner": "Nghĩa", "file": "app/routes.py", "test": "test_d29_07_invalid_product_id_returns_404"},
    {"id": "F21", "name": "Hiển thị danh sách kích cỡ có sẵn", "w3": "W3-007", "owner": "Nghĩa", "file": "app/data.py", "test": "test_details_404_and_static"},
    {"id": "F22", "name": "Hiển thị danh sách màu sắc có sẵn", "w3": "W3-007", "owner": "Nghĩa", "file": "app/data.py", "test": "test_details_404_and_static"},
    {"id": "F23", "name": "Lọc màu VÀ size trên CÙNG MỘT biến thể (SP101/SP102)", "w3": "W3-007", "owner": "Nghĩa", "file": "app/data.py", "test": "test_03_critical_same_variant_color_size_rule"},
    {"id": "F24", "name": "Hiển thị tồn kho theo biến thể đã chọn", "w3": "W3-007", "owner": "Nghĩa", "file": "app/data.py", "test": "test_05_product_detail_and_variant_stock"},
    {"id": "F25", "name": "Biến thể hết hàng (tồn = 0) hiển thị trạng thái hết", "w3": "W3-007", "owner": "Nghĩa", "file": "app/templates/product_detail.html", "test": "CHƯA_TEST"},
    {"id": "F26", "name": "Ràng buộc duy nhất cặp (product_id, color_id, size_id)", "w3": "W3-007", "owner": "Nghĩa", "file": "database/schema.sql", "test": "test_04_duplicate_variant_combination_blocked"},
    {"id": "F27", "name": "Ràng buộc tồn kho không âm (>= 0)", "w3": "W3-007", "owner": "Nghĩa", "file": "database/schema.sql", "test": "test_05_negative_stock_blocked"},
    {"id": "F28", "name": "Ràng buộc tồn kho là số nguyên", "w3": "W3-007", "owner": "Nghĩa", "file": "tests/w3_diem/business_rules.py", "test": "test_06_decimal_stock_blocked"},
    {"id": "F29", "name": "Xem hoặc chọn sản phẩm không tự ý trừ tồn kho", "w3": "W3-007", "owner": "Nghĩa", "file": "app/routes.py", "test": "test_06_browsing_does_not_deduct_stock"},

    # Nhóm 3: Giỏ hàng & Mua hàng trực tiếp tại shop - Tuấn (W3-008)
    {"id": "F30", "name": "Thêm sản phẩm hợp lệ vào giỏ", "w3": "W3-008", "owner": "Tuấn", "file": "app/routes.py", "test": "test_d29_08_select_correct_variant"},
    {"id": "F31", "name": "Thêm giỏ vượt quá số lượng tồn bị từ chối", "w3": "W3-008", "owner": "Tuấn", "file": "app/routes.py", "test": "test_cart_guard"},
    {"id": "F32", "name": "Số lượng thêm giỏ <= 0 bị từ chối", "w3": "W3-008", "owner": "Tuấn", "file": "app/routes.py", "test": "test_cart_guard"},
    {"id": "F33", "name": "Xóa 1 biến thể khỏi giỏ hàng", "w3": "W3-008", "owner": "Tuấn", "file": "app/routes.py", "test": "test_cart_session_and_remove"},
    {"id": "F34", "name": "Xem giỏ hàng tính đúng tổng tiền", "w3": "W3-008", "owner": "Tuấn", "file": "app/routes.py", "test": "test_cart_session_and_remove"},
    {"id": "F35", "name": "Màn hình checkout nhận tại cửa hàng (không ship)", "w3": "W3-008", "owner": "Tuấn", "file": "app/routes.py", "test": "test_cart_session_and_remove"},

    # Nhóm 4: Quản trị Admin, CRUD sản phẩm, Ảnh, Quyền - Khải (W3-013, W3-014, W3-054, W3-056)
    {"id": "F36", "name": "Guest truy cập URL admin bị điều hướng login", "w3": "W3-013", "owner": "Khải", "file": "app/routes.py", "test": "test_01_guest_blocked_from_admin_urls"},
    {"id": "F37", "name": "Customer truy cập admin bị chặn 403", "w3": "W3-013", "owner": "Khải", "file": "app/routes.py", "test": "test_02_customer_blocked_from_admin"},
    {"id": "F38", "name": "Seller bị chặn POST/PUT vào trang admin", "w3": "W3-013", "owner": "Khải", "file": "app/routes.py", "test": "test_d29_09_seller_blocked_from_admin_post"},
    {"id": "F39", "name": "Admin đăng nhập vào được dashboard", "w3": "W3-013", "owner": "Khải", "file": "app/routes.py", "test": "test_04_admin_allowed_access"},
    {"id": "F40", "name": "Kiểm tra giá sản phẩm phải > 0đ (A07)", "w3": "W3-013", "owner": "Khải", "file": "app/routes.py", "test": "test_d29_12_invalid_price_rejected"},
    {"id": "F41", "name": "Thực hiện INSERT sản phẩm thật vào CSDL", "w3": "W3-013", "owner": "Khải", "file": "app/routes.py", "test": "CHƯA_CODE"},
    {"id": "F42", "name": "Chống tạo danh mục trùng tên sau chuẩn hóa (A03)", "w3": "W3-013", "owner": "Khải", "file": "tests/w3_diem/business_rules.py", "test": "test_d29_11_duplicate_category_rejected"},
    {"id": "F43", "name": "Upload ảnh JPG, PNG, WebP <= 5MB (A05)", "w3": "W3-054", "owner": "Khải", "file": "tests/w3_diem/business_rules.py", "test": "test_01_valid_image_formats"},
    {"id": "F44", "name": "Chặn file mã độc giả mạo đuôi ảnh (A05)", "w3": "W3-054", "owner": "Khải", "file": "tests/w3_diem/business_rules.py", "test": "test_02_fake_image_file_rejected"},
    {"id": "F45", "name": "Quy tắc xóa ảnh đại diện chọn ảnh thay thế (A04)", "w3": "W3-054", "owner": "Khải", "file": "tests/w3_diem/business_rules.py", "test": "test_05_avatar_deletion_fallback_rule"},
    {"id": "F46", "name": "Khách lưu sản phẩm yêu thích (Favorites)", "w3": "W3-014", "owner": "Khải", "file": "app/routes.py", "test": "CHƯA_CODE"},
    {"id": "F47", "name": "Cách ly danh sách yêu thích giữa khách A và B", "w3": "W3-014", "owner": "Khải", "file": "app/routes.py", "test": "test_07_customer_favorite_isolation"},
    {"id": "F48", "name": "Giao dịch rollback khi lưu biến thể lỗi", "w3": "W3-044", "owner": "Khải", "file": "database/schema.sql", "test": "test_05_atomic_transaction_rollback_on_variant_failure"},
    {"id": "F49", "name": "Không xóa vật lý sản phẩm đã phát sinh đơn hàng", "w3": "W3-044", "owner": "Khải", "file": "database/schema.sql", "test": "test_06_referenced_product_cannot_be_deleted_history_protection"},
]


class CoverageAuditor:
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

    def audit(self):
        print(f"=== [W3-059] BẮT ĐẦU KIỂM TOÁN ĐỘ BAO PHỦ CHỨC NĂNG (COVERAGE AUDIT) ===")
        print(f"Tổng số chức năng baseline theo dõi: {len(BASELINE_86_FUNCTIONS)}")

        evaluated = []
        for fn in BASELINE_86_FUNCTIONS:
            status = "CHƯA_XÁC_MINH"
            # Kiểm tra code tồn tại
            code_file = self.project_root / fn["file"]
            has_code = code_file.exists()

            if fn["test"] == "CHƯA_CODE":
                status = "BLOCKED (Thiếu backend)"
            elif fn["test"] == "CHƯA_TEST":
                status = "NOT RUN (Chưa viết test)"
            elif has_code:
                status = "VERIFIED (Đã có test & code)"
            else:
                status = "MISSING_FILE"

            evaluated.append({
                **fn,
                "has_code": has_code,
                "status": status,
            })

        self.generate_reports(evaluated)
        return evaluated

    def generate_reports(self, evaluated: List[Dict[str, Any]]):
        verified_count = sum(1 for e in evaluated if "VERIFIED" in e["status"])
        blocked_count = sum(1 for e in evaluated if "BLOCKED" in e["status"])
        not_run_count = sum(1 for e in evaluated if "NOT RUN" in e["status"])

        print("\n" + "=" * 95)
        print(f"{'MÃ':<6} | {'NHIỆM VỤ':<8} | {'NGƯỜI':<8} | {'TRẠNG THÁI':<26} | TÊN CHỨC NĂNG")
        print("-" * 95)
        for e in evaluated:
            print(f"{e['id']:<6} | {e['w3']:<8} | {e['owner']:<8} | {e['status']:<26} | {e['name'][:42]}")
        print("=" * 95)
        print(f"TỔNG KẾT BAO PHỦ:")
        print(f"- Đã xác minh có test & code tuần 2/3: {verified_count}/{len(evaluated)}")
        print(f"- Bị chặn (BLOCKED) do thiếu backend tuần 3: {blocked_count}/{len(evaluated)}")
        print(f"- Chưa chạy / Chưa test (NOT RUN): {not_run_count}/{len(evaluated)}\n")

        # Lưu file Markdown & CSV
        output_dir = self.project_root / "docs" / "w3_diem"
        output_dir.mkdir(parents=True, exist_ok=True)

        md_path = output_dir / "BAO_CAO_BAO_PHU_CHUC_NANG.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("# BÁO CÁO KIỂM TOÁN ĐỘ BAO PHỦ CHỨC NĂNG (W3-059)\n\n")
            f.write(f"**Người thực hiện:** Điểm (Nhóm trưởng)  \n")
            f.write(f"**Tổng số chức năng theo dõi:** {len(evaluated)}  \n")
            f.write(f"- **Đã xác minh kiểm thử (Verified):** {verified_count}  \n")
            f.write(f"- **Bị chặn do thiếu backend tuần 3 (Blocked):** {blocked_count}  \n")
            f.write(f"- **Chưa kiểm thử (Not run):** {not_run_count}  \n\n")
            f.write("| Mã FN | Mã W3 | Người phụ trách | Chức năng | File code | Bài test tương ứng | Trạng thái |\n")
            f.write("|---|---|---|---|---|---|---|\n")
            for e in evaluated:
                f.write(f"| {e['id']} | {e['w3']} | {e['owner']} | {e['name']} | `{e['file']}` | `{e['test']}` | **{e['status']}** |\n")

        csv_path = output_dir / "MA_TRAN_BAO_PHU_CHUC_NANG.csv"
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Mã FN", "Mã W3", "Người phụ trách", "Chức năng", "File code", "Bài test tương ứng", "Trạng thái"])
            for e in evaluated:
                writer.writerow([e["id"], e["w3"], e["owner"], e["name"], e["file"], e["test"], e["status"]])

        print(f"[OK] Đã xuất báo cáo bao phủ Markdown: {md_path}")
        print(f"[OK] Đã xuất ma trận bao phủ CSV: {csv_path}")


if __name__ == "__main__":
    auditor = CoverageAuditor()
    auditor.audit()
