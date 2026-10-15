"""Công cụ W3-069: Tổng hợp toàn bộ kiểm thử và kiểm toán nghiệm thu Tuần 3.
Phụ trách: Điểm (Nhóm trưởng Nhóm 6).

Chạy một lệnh duy nhất:
1. W3-001: Kiểm kê môi trường kỹ thuật (check_environment.py)
2. W3-015: Đối chiếu hợp đồng API - SQL - Use Case (audit_contract.py)
3. W3-058: Chạy kiểm thử hồi quy (run_regression.py)
4. W3-059: Kiểm toán độ bao phủ chức năng (audit_coverage.py)
5. W3-060: Kiểm tra độ sẵn sàng Demo & 5 máy (check_demo_readiness.py)
Xuất Dashboard tổng quan cho Điểm nghiệm thu và làm báo cáo bảo vệ.
"""
import sys
import time
from pathlib import Path

# Đảm bảo đường dẫn import
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from tools.w3_diem.check_environment import EnvironmentChecker
from tools.w3_diem.audit_contract import ContractAuditor
from tools.w3_diem.run_regression import RegressionRunner
from tools.w3_diem.audit_coverage import CoverageAuditor
from tools.w3_diem.check_demo_readiness import DemoReadinessChecker


def run_full_milestone_check():
    start_time = time.time()
    print("=" * 100)
    print("        HỆ THỐNG KIỂM THỬ KỸ THUẬT & NGHIỆM THU TUẦN 3 - NHÓM 6 (WEBSITE BÁN GIÀY DÉP)        ")
    print(f"        Nhóm trưởng phụ trách: Điểm | Thời gian: {time.strftime('%Y-%m-%d %H:%M:%S')}         ")
    print("=" * 100 + "\n")

    # 1. W3-001
    print(">>> BƯỚC 1/5: KIỂM KÊ MÔI TRƯỜNG KỸ THUẬT (W3-001)")
    env_checker = EnvironmentChecker(project_root)
    env_results = env_checker.run_all()
    env_checker.print_summary()
    print("\n" + "-" * 100 + "\n")

    # 2. W3-015
    print(">>> BƯỚC 2/5: ĐỐI CHIẾU HỢP ĐỒNG API - SQL - USE CASE (W3-015)")
    auditor = ContractAuditor(project_root)
    audit_findings = auditor.run_audit()
    auditor.print_report()
    print("\n" + "-" * 100 + "\n")

    # 3. W3-058
    print(">>> BƯỚC 3/5: THỰC THI KIỂM THỬ HỒI QUY TOÀN BỘ SUITE (W3-058)")
    regression_runner = RegressionRunner(project_root)
    test_records = regression_runner.run_tests()
    print("\n" + "-" * 100 + "\n")

    # 4. W3-059
    print(">>> BƯỚC 4/5: KIỂM TOÁN ĐỘ BAO PHỦ CHỨC NĂNG (W3-059)")
    cov_auditor = CoverageAuditor(project_root)
    cov_results = cov_auditor.audit()
    print("\n" + "-" * 100 + "\n")

    # 5. W3-060
    print(">>> BƯỚC 5/5: KIỂM TRA ĐỘ SẴN SÀNG DEMO VÀ CÀI ĐẶT 5 MÁY (W3-060)")
    demo_checker = DemoReadinessChecker(project_root)
    demo_checker.run()
    print("\n" + "=" * 100 + "\n")

    # DASHBOARD TỔNG KẾT
    total_tests = len(test_records)
    pass_tests = sum(1 for r in test_records if r["status"] == "PASS")
    blocked_tests = sum(1 for r in test_records if r["status"] in {"BLOCKED", "SKIPPED"})
    fail_tests = sum(1 for r in test_records if r["status"] == "FAIL")

    total_cov = len(cov_results)
    verified_cov = sum(1 for c in cov_results if "VERIFIED" in c["status"])
    blocked_cov = sum(1 for c in cov_results if "BLOCKED" in c["status"])

    print("               ==================== DASHBOARD NGHIỆM THU TUẦN 3 ====================               ")
    print(f"  * Kết quả chạy Test tự động: {pass_tests}/{total_tests} PASS ({blocked_tests} BLOCKED, {fail_tests} FAIL)")
    print(f"  * Số phát hiện đối chiếu hợp đồng cần xử lý (W3-015): {len(audit_findings)} vấn đề")
    print(f"  * Độ bao phủ chức năng (W3-059): {verified_cov}/{total_cov} chức năng đã có code/test ({blocked_cov} BLOCKED)")
    print(f"  * Tổng thời gian thực thi: {time.time() - start_time:.2f} giây")
    print("  * Đánh giá chung: Nền tảng kiểm thử đã sẵn sàng 100%; Đang chờ Minh, Nghĩa, Khải hoàn thiện code tuần 3.")
    print("=" * 100)


if __name__ == "__main__":
    run_full_milestone_check()
