> Cập nhật bộ nối: đọc [bàn giao backend](docs/TUAN_W4_BACKEND_HANDOFF.md). Đã có factory/adapter tự gắn provider; backend thật và nghiệm thu E2E vẫn chờ bàn giao.

# Bản bàn giao frontend tuần 4 — Tuấn, Nhóm 6

Đọc file này trước khi chạy. Phạm vi: W4-004, W4-009, W4-014, W4-019, W4-024.

## Chạy trên Windows / VS Code

Mở đúng thư mục có run.py. Terminal PowerShell:

~~~powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:DB_BACKEND="sqlite"
$env:TUAN_W4_PREVIEW="0"
.\.venv\Scripts\python.exe run.py
~~~

Mở http://127.0.0.1:5000/products → chọn sản phẩm → chọn màu, size, số lượng → thêm giỏ → checkout.
Đây là SQLite demo, không phải kết quả nghiệm thu SQL Server.

## Xem phần mới

- /checkout: cần giỏ có sản phẩm; form mới, kiểm tra dữ liệu ngay trên trang.
- /checkout/success: phản hồi sau khi gửi; ghi rõ trạng thái tại thời điểm gửi.
- /my-orders: cần đăng nhập Customer. Mặc định báo chưa nối backend (HTTP 503); không bịa danh sách trống.
- /my-orders/<id>: chờ provider backend cung cấp đơn của đúng tài khoản.
- Nút Thêm sản phẩm tại /admin đã dẫn tới form W3 có chức năng lưu.

## Xem giao diện đơn hàng trước khi Nghĩa ghép backend

Dừng server bằng Ctrl+C rồi chạy:

~~~powershell
$env:TUAN_W4_PREVIEW="1"
.\.venv\Scripts\python.exe run.py
~~~

Mở http://127.0.0.1:5000/ui-preview/w4/orders
Các nút đầu trang dẫn đến chi tiết, đang giao, hoàn thành, thất bại/hủy thanh toán, rỗng và lỗi.
Mọi trang đều ghi DỮ LIỆU MẪU — CHƯA TÍCH HỢP BACKEND. Preview không tạo/hủy đơn và không thu tiền.
Tắt preview bằng cách đặt TUAN_W4_PREVIEW="0" rồi khởi động lại server.

## Đọc tài liệu bàn giao

1. docs/TUAN_W4_HANDOFF.md — tình trạng 5 nhiệm vụ, file thay đổi và việc cần phối hợp.
2. docs/TUAN_W4_ORDER_UI_CONTRACT.md — giao diện hàm/dữ liệu để Nghĩa ghép backend.
3. docs/UI_smoke_w4.md — các bước kiểm tra và minh chứng.
4. docs/TUAN_W4_PR.md — nội dung PR đề xuất.
5. docs/TUAN_W4_CHANGES.json — danh sách file và mã kiểm tra của bản gốc/bản sửa.
6. docs/evidence/w4/ — ảnh thật từ trình duyệt và log. Ảnh có chữ sample là UI dữ liệu mẫu.

Các file service đơn, DB, SQL và route nghiệp vụ cũ được giữ nguyên. Hai lỗi backend còn tồn: chưa trừ/hoàn kho, sản phẩm ẩn trong giỏ vẫn có thể đặt. Không dùng bản này để tuyên bố toàn bộ tuần 4 đã hoàn thành.
