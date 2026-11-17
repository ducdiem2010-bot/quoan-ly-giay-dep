# W13 Tuấn – BẢN WEBSITE ĐÃ TÍCH HỢP (bản thử nghiệm)

Bản này khác gói `Tuan_W13_Code.zip` độc lập: đã **tích hợp trực tiếp** module K3/K4/K7 vào tệp dùng chung để có thể xem chức năng trên web. **Không thay thế phần branch/handoff của Tuấn trong kế hoạch nhóm nếu Điểm chưa xét duyệt.**

## Chạy trên Windows (PowerShell)

Mở VS Code đúng thư mục có `run.py` và `requirements_sqlite.txt`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements_sqlite.txt
$env:DB_BACKEND = "sqlite"
.\.venv\Scripts\python.exe run.py
```

Mở http://127.0.0.1:5000, xem sản phẩm tại `/product/<id>` để lưu lịch sử đã xem. Chọn **Sản phẩm vừa xem** hoặc **Xem lịch sử** để xem lại; lịch sử lưu riêng trên trình duyệt.

Đăng nhập tài khoản **Customer** → **Tài khoản** → **Theo dõi đơn hàng** (`/account/orders`): mỗi dòng sản phẩm trong lịch sử có **ảnh và tên dẫn đến trang chi tiết sản phẩm** (GET, không thêm vào giỏ); trên trang chi tiết khách tự chọn size/màu, số lượng rồi mua. Mỗi đơn còn có **Xem tiến trình đơn** (chỉ hiển thị mốc thời gian có trong DB). Đã gỡ cả nút Mua lại và route tự thêm giỏ; các URL mua lại W13 cũ trả 404. Phần chi tiết sản phẩm và Thêm vào giỏ của website gốc vẫn giữ nguyên.

### Các tệp dùng chung đã chạm
- `app/__init__.py`: đăng ký blueprint `w13_tuan`.
- `app/templates/account_orders.html`: chèn liên kết K3, K7 và dẫn đến lịch sử vừa xem; vẫn giữ CSS `account.css`.
- `app/templates/product_detail.html`: chèn marker và danh sách K4; tải CSS/JS.
- `app/templates/w13/_recently_viewed.html` và `app/static/css/w13_customer_ux.css`: bổ sung nút xem lịch sử/bố cục.

### Chú ý
- Không thêm migration DB cho 3 tính năng; không đổi thông tin đơn/hóa đơn/trả hàng.
- `/w13/recent-products` chỉ trả sản phẩm hiển thị; `localStorage` chỉ lưu mã sản phẩm.
- Trước khi chuyển vào `main`, Điểm cần rà soát diff và chạy full test, SQL Server, responsive browser trên máy triển khai.
