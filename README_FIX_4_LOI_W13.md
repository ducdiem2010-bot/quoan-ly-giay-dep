# W13 — Bốn lỗi đã sửa (17/11/2026)

1. Không tạo bản ghi thanh toán COD giả; xác nhận thanh toán chỉ dựa trên giao dịch có thật và ghi actor/thời gian. Xác nhận chuyển khoản trước giao hàng vẫn được phép.
2. Seed SQLite không ép lại trạng thái ẩn sản phẩm demo đã có.
3. Tài khoản /account/orders phân trang 50 đơn/trang ngay trong SQL; cú pháp SQLite/SQL Server riêng.
4. Giỏ hiển thị lý do không mua được (ẩn/hết hàng/mất biến thể), không tự xóa, không cộng tiền sản phẩm lỗi; checkout chặn backend.

Chạy trên Windows (PowerShell, trong thư mục chứa run.py):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements_sqlite.txt
$env:DB_BACKEND = 'sqlite'
.\.venv\Scripts\python.exe run.py
```

Kiểm thử:

```powershell
$env:DB_BACKEND = 'sqlite'
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test*.py' -v
```

Giải nén vào thư mục riêng. Sao lưu database trước khi cập nhật. Không có migration schema trong lần sửa này.
