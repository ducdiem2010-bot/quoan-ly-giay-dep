# Bàn giao bộ nối frontend tuần 4 cho Nghĩa

Phạm vi: Tuấn chuẩn bị UI và điểm kết nối cho W4-009/W4-024. Bản này nâng cấp ZIP frontend đã kiểm tra, không phải bản bổ sung module Nhân viên.

**Đã làm sẵn:** tự nạp provider từ cấu hình, adapter bọc hàm backend, form GET/POST tới route đơn hàng, kiểm session/owner/CSRF, hộp thoại hủy, test bộ nối và lệnh kiểm tra GET.
**Còn chờ Nghĩa:** service đơn hàng thật, ánh xạ dữ liệu DB và quy tắc hủy/trạng thái đã được nhóm xác nhận.
**Mặc định:** chưa cấu hình backend -> /my-orders trả 503; preview vẫn tắt. Không dùng mẫu làm backend chạy thật.

## Nghĩa cần ghép ở đâu

1. Ghép các file UI của Tuấn vào nhánh tích hợp theo PR. Giữ app/__init__.py có đăng ký blueprint tuan_w4_ui như ZIP.
2. Sao chép integration_examples/nghia_order_ui.py.example thành app/nghia_order_ui.py.
3. Sửa các import trong file đó trỏ tới hàm backend thật của Nghĩa. Tên nghia_order_service và các tên hàm trong mẫu là ví dụ, chưa có trong ZIP.
4. Nếu service trả tên cột SQL khác hợp đồng hiển thị, viết map_order_to_view rồi truyền to_order_view=map_order_to_view. Không sửa schema theo tên trường UI.
5. Khi backend đã chạy trên DB test, cấu hình factory và khởi động lại server.

PowerShell, sau khi đã hoàn thành bước 2–4:

~~~powershell
$env:TUAN_W4_PREVIEW="0"
$env:TUAN_ORDER_UI_PROVIDER_FACTORY="app.nghia_order_ui:create_provider"
.\.venv\Scripts\python.exe run.py
~~~

Dùng DB test của nhóm. Chỉ đặt DB_BACKEND=sqlserver khi cấu hình SQLSERVER_CONN và migration test đã được Minh kiểm chứng.
File .env.example chỉ là mẫu; lệnh PowerShell trên đặt biến môi trường thực tế. Không mặc định cho rằng ứng dụng tự đọc file .env.

Factory nhận app (đã có app context) và trả provider. Mỗi ứng dụng khởi tạo provider riêng.
Provider truyền trực tiếp qua TUAN_ORDER_UI_PROVIDER có ưu tiên cao hơn factory.
Config TUAN_ORDER_UI_PROVIDER_FACTORY="" sẽ tắt factory từ môi trường.
Cấu hình factory sai sẽ dừng khởi động với thông báo lỗi cấu hình, không âm thầm dùng dữ liệu mẫu.

## Ba hàm phía Nghĩa

| Hàm | Đầu vào | Đầu ra |
| --- | --- | --- |
| list_orders(*, user_id) | Mã Customer từ session server | list/tuple OrderView của đúng khách; [] nếu thực sự không có đơn |
| get_order(*, user_id, order_id) | Khách từ session và mã đơn trong URL | OrderView hoặc None khi không tồn tại/không thuộc khách |
| cancel_order(*, user_id, order_id) | Khách từ session và mã đơn | {"ok": True} sau commit; {"ok": False} khi backend từ chối |

Hàm hủy tùy chọn. Khi chưa có service hủy, bỏ import/callback cancel khỏi mẫu và dùng cancel_order=None. UI sẽ chỉ đọc, không hiện nút hủy.

OrderView tối thiểu cần các trường theo docs/TUAN_W4_ORDER_UI_CONTRACT.md:
id, user_id, created_at, status_label, delivery_stage, fulfillment, payment_status,
payment_status_label, payment_method_label, can_cancel, items_total, total,
shipping_fee, receiver, items.

- id/user_id: int dương, user_id phải đúng chủ đơn.
- receiver: name, phone, address lấy từ snapshot đơn.
- items: product_name, color, size, quantity, unit_price, subtotal.
- Tiền do backend tính/lưu; không âm, hữu hạn. shipping_fee=None là chưa xác định, 0 là miễn phí thật.
- can_cancel phải là bool do backend quyết định.
- status/payment status phải phản ánh dữ liệu thật; không suy paid từ bank_transfer.
- Bảng chuyển trạng thái và nghiệp vụ tồn cần Nghĩa/Minh/Điểm xác nhận trước nghiệm thu.

## Cách nối trực tiếp bằng Python

Nếu Nghĩa đã có app factory riêng, có thể gắn sau khi create_app và trước khi phục vụ request:

~~~python
from app import create_app
from app.tuan_w4_connection import OrderUIAdapter, bind_order_ui_provider

app = create_app()
bind_order_ui_provider(app, OrderUIAdapter(
    list_orders=list_orders_for_customer,
    get_order=get_order_for_customer,
    cancel_order=cancel_order_for_customer,
))
~~~

Các biến hàm ở ví dụ phải được import từ backend thật. Không cần thay HTML/CSS/JS.
OrderUIAdapter chỉ chuyển lời gọi và ánh xạ dữ liệu; không tự thêm SQL, tạo đơn, hủy đơn hoặc hoàn tồn.

## Kiểm tra sau khi ghép

Dùng DB test và mã Customer/đơn test đúng chủ sở hữu:

~~~powershell
.\.venv\Scripts\python.exe scripts/check_order_ui_connection.py --user-id 3
.\.venv\Scripts\python.exe scripts/check_order_ui_connection.py --user-id 3 --order-id 123
~~~

Thay 3 và 123 bằng mã trong DB test của nhóm. Đây là session Customer giả lập qua Flask test client để kiểm bộ nối, không phải kiểm đăng nhập thật.

- Exit 0: các GET được yêu cầu trả 200.
- Exit 1: GET không đạt; xem status. 404 có thể do sai mã đơn/owner; 503 có thể do lỗi backend/hợp đồng.
- Exit 2: chưa cấu hình provider.
- Script chỉ GET, không gửi hủy/tạo đơn. Quá trình tạo app giữ hành vi khởi tạo SQLite demo sẵn có.
- Một GET 200 chỉ chứng minh đường đọc được yêu cầu; không chứng minh backend là DB thật, nghiệp vụ kho hoặc payment đã đạt.

Trên web, đăng nhập Customer thật và thử:
1. Đơn vừa đặt xuất hiện ở /my-orders; chi tiết đúng snapshot.
2. Customer khác không đọc/hủy được bằng URL trực tiếp.
3. Hủy đơn đủ điều kiện; tải lại trạng thái; gửi lặp và chuyển trạng thái giữa hai request.
4. Nhân viên xác nhận trước khi khách hủy -> backend từ chối hủy.
5. Kiểm SQL Server trước/sau với Minh/Điểm; hoàn tồn đúng một lần khi nghiệp vụ yêu cầu.
6. Chưa có backend/DB lỗi -> 503 có thông báo, không giả danh sách rỗng.
7. Provider chỉ đọc -> không có nút hủy và POST trực tiếp không gọi hàm ghi.

Đừng đánh DONE chỉ từ preview hoặc test service giả. Điểm nghiệm thu luồng thật sau khi ghép.

## Phân chia bàn giao

| Người | Phần phụ trách |
| --- | --- |
| Tuấn | UI và bộ nối trong ZIP này, cập nhật giao diện nếu contract được duyệt thay đổi |
| Nghĩa | Contract nghiệp vụ, service list/detail/cancel, ánh xạ trạng thái/snapshot và kiểm quyền trong backend |
| Minh | SQL Server/migration, helper transaction/giữ/trừ/hoàn tồn; phối hợp Nghĩa |
| Khải | Xác nhận/từ chối và trạng thái giao hàng từ Nhân viên/Quản lý |
| Điểm | Test quyền/state/E2E/SQL Server, ghi PASS/FAIL/BLOCKED và nghiệm thu |

SQL/service nghiệp vụ cũ được giữ nguyên. Xem docs/W4_CONNECTION_VERIFICATION.md và manifest để đối chiếu.

