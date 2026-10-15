"""Công cụ W3-058: Bộ chạy kiểm thử hồi quy tự động (Regression Test Runner).
Phụ trách: Điểm (Nhóm trưởng Nhóm 6).

Chức năng:
- Tự động phát hiện và thực thi toàn bộ test suite (smoke test tuần 2 và các bộ test tuần 3).
- Thu thập kết quả theo từng bài test: PASS, FAIL, BLOCKED (SKIP), ERROR.
- Ghi nhận thông tin Git commit hash hiện tại để đối chiếu lịch sử phiên bản.
- Xuất báo cáo đa định dạng: Console, file Log, JSON và CSV.
- Cấm tự ý biến FAIL thành PASS khi chưa chạy lại thật.
"""
import csv
import json
import os
import subprocess
import sys
import time
import unittest
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


def get_git_commit_hash(project_root: Path) -> str:
    """Lấy commit hash hiện tại của git nếu có."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(project_root),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return out
    except Exception:
        return "NO_GIT_HASH"


class CustomTestResult(unittest.TestResult):
    def __init__(self):
        super().__init__()
        self.records: List[Dict[str, Any]] = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.records.append({
            "test_id": test.id(),
            "status": "PASS",
            "message": "Passed",
        })

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.records.append({
            "test_id": test.id(),
            "status": "FAIL",
            "message": self._exc_info_to_string(err, test),
        })

    def addError(self, test, err):
        super().addError(test, err)
        self.records.append({
            "test_id": test.id(),
            "status": "ERROR",
            "message": self._exc_info_to_string(err, test),
        })

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        status = "BLOCKED" if "BLOCKED" in reason else "SKIPPED"
        self.records.append({
            "test_id": test.id(),
            "status": status,
            "message": reason,
        })


class RegressionRunner:
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

    def run_tests(self, task_filter: str = None):
        print(f"=== [W3-058] BẮT ĐẦU CHẠY KIỂM THỬ HỒI QUY (REGRESSION TEST) ===")
        start_time = time.time()
        git_hash = get_git_commit_hash(self.project_root)
        print(f"Project root: {self.project_root.resolve()}")
        print(f"Git commit: {git_hash}")
        if task_filter:
            print(f"Bộ lọc nhiệm vụ: {task_filter}")

        # Thêm project root vào sys.path để import
        sys.path.insert(0, str(self.project_root))

        loader = unittest.TestLoader()
        suite = unittest.TestSuite()

        # Nạp test smoke tuần 2
        smoke_dir = self.project_root / "tests"
        suite.addTests(loader.discover(start_dir=str(smoke_dir), pattern="test_smoke.py"))

        # Nạp các bài test tuần 3 của Điểm
        w3_dir = self.project_root / "tests" / "w3_diem"
        if w3_dir.exists():
            suite.addTests(loader.discover(start_dir=str(w3_dir), pattern="test_*.py"))

        result = CustomTestResult()
        suite.run(result)

        elapsed = time.time() - start_time
        self.save_and_display_results(result.records, git_hash, elapsed)
        return result.records

    def save_and_display_results(self, records: List[Dict[str, Any]], git_hash: str, elapsed: float):
        total = len(records)
        pass_count = sum(1 for r in records if r["status"] == "PASS")
        fail_count = sum(1 for r in records if r["status"] == "FAIL")
        blocked_count = sum(1 for r in records if r["status"] in {"BLOCKED", "SKIPPED"})
        error_count = sum(1 for r in records if r["status"] == "ERROR")

        print("\n" + "=" * 95)
        print(f"{'STT':<4} | {'TRẠNG THÁI':<10} | {'MÃ TEST / TÊN BÀI TEST':<50} | KẾT QUẢ")
        print("-" * 95)
        for idx, r in enumerate(records, 1):
            short_id = r["test_id"].split(".")[-1]
            parent_module = r["test_id"].split(".")[-2]
            display_name = f"{parent_module}.{short_id}"
            first_line_msg = r["message"].split("\n")[0][:40]
            print(f"{idx:<4} | {r['status']:<10} | {display_name[:50]:<50} | {first_line_msg}")
        print("=" * 95)
        print(f"TỔNG KẾT: Tổng: {total} | PASS: {pass_count} | FAIL: {fail_count} | BLOCKED: {blocked_count} | ERROR: {error_count}")
        print(f"Thời gian thực thi: {elapsed:.2f}s | Git Commit: {git_hash}\n")

        # Lưu các file báo cáo
        output_dir = self.project_root / "docs" / "w3_diem"
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 1. JSON Report
        json_file = output_dir / f"KET_QUA_REGRESSION_{timestamp}.json"
        summary_data = {
            "timestamp": datetime.now().isoformat(),
            "git_commit": git_hash,
            "elapsed_seconds": round(elapsed, 2),
            "total": total,
            "pass": pass_count,
            "fail": fail_count,
            "blocked": blocked_count,
            "error": error_count,
            "records": records,
        }
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)

        # 2. CSV Report
        csv_file = output_dir / "KET_QUA_REGRESSION_LATEST.csv"
        with open(csv_file, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["STT", "Test ID", "Trạng thái", "Chi tiết", "Commit"])
            for idx, r in enumerate(records, 1):
                writer.writerow([idx, r["test_id"], r["status"], r["message"].replace("\n", " "), git_hash])

        print(f"[OK] Đã lưu báo cáo JSON: {json_file}")
        print(f"[OK] Đã cập nhật bảng CSV: {csv_file}")


if __name__ == "__main__":
    runner = RegressionRunner()
    runner.run_tests()
