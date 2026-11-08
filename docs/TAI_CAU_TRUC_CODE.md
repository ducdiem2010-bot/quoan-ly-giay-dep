# Tái cấu trúc thư mục – Nhóm 6 (02/11/2026)

Bản này **chỉ di chuyển module**, cập nhật relative import/Flask app registration và đường dẫn của script QA. Không thêm tính năng, không thay đổi dữ liệu, schema hoặc URL.

## Bản đồ di chuyển

| Đường dẫn trước | Đường dẫn sau | Ý nghĩa |
|---|---|---|
| `app/routes.py` | `app/routes/public.py` | Tách route public/login/cart/checkout thành package routes |
| `app/catalog_w3.py` | `app/routes/catalog.py` | Nhóm route sản phẩm trong package routes |
| `app/admin_w3.py` | `app/routes/admin.py` | Nhóm route quản trị trong package routes |
| `app/checkout_service.py` | `app/services/checkout.py` | Tách service checkout khỏi module route |
| `verify_w3_offline.py` | `scripts/verify_w3_offline.py` | Chuyển tiện ích QA độc lập sang scripts |

## Những file cố ý giữ nguyên

`app/__init__.py` (khởi tạo Flask, đổi đúng import); `app/data.py`, `app/db.py`, `run.py`, `database/`, `app/templates/`, `app/static/`, `tests/`, `docs/`, `instance/` vì di chuyển không đem lại lợi ích rõ rệt và làm tăng rủi ro.

## Lệnh kiểm thử

```powershell
.\.venv\Scripts\python.exe run.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test*.py" -v
.\.venv\Scripts\python.exe scripts/verify_w3_offline.py
```

Trước khi bàn giao chính thức, thành viên phụ trách phải kiểm tra lại các route Flask và SQL Server trên máy nhóm. **Bản ZIP do AI refactor**, chưa được Điểm nghiệm thu thực tế.
