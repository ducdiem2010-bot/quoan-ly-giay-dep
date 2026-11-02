"""Kiểm tra bộ nối trên DB TEST, chỉ GET; không tạo/hủy đơn hoặc xác minh kho."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app


def positive_integer(value):
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise argparse.ArgumentTypeError("Mã phải là số nguyên dương.") from None
    if number < 1:
        raise argparse.ArgumentTypeError("Mã phải là số nguyên dương.")
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user-id", type=positive_integer, required=True,
                        help="Mã Customer TEST dùng làm session giả lập.")
    parser.add_argument("--order-id", type=positive_integer,
                        help="Mã đơn TEST của chính Customer đó, nếu có.")
    args = parser.parse_args(argv)
    app = create_app()
    report = {
        "scope": "UI adapter GET test; không phải nghiệm thu auth/SQL/kho/payment",
        "database_backend": app.config["DB_BACKEND"],
        "provider_configured": app.config.get("TUAN_ORDER_UI_PROVIDER") is not None,
        "requests": [],
    }
    if not report["provider_configured"]:
        report["result"] = "BLOCKED: chưa cấu hình provider backend thật."
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2
    with app.test_client() as client:
        with client.session_transaction() as session:
            session.update(user_id=args.user_id, role="Customer")
        paths = ["/my-orders"]
        if args.order_id:
            paths.append("/my-orders/" + str(args.order_id))
        for path in paths:
            response = client.get(path)
            report["requests"].append({"method": "GET", "path": path,
                                       "status": response.status_code})
    success = all(row["status"] == 200 for row in report["requests"])
    report["result"] = "PASS: các GET được yêu cầu trả 200." if success else (
        "FAIL: xem HTTP status; 404 có thể là sai mã đơn/owner, 503 là lỗi backend/contract.")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())

