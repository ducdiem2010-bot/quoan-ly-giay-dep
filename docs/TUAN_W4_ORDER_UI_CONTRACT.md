> Cập nhật bộ nối: đọc [bàn giao backend](TUAN_W4_BACKEND_HANDOFF.md). Đã có factory/adapter tự gắn provider; backend thật và nghiệm thu E2E vẫn chờ bàn giao.

# Hợp đồng UI đơn hàng W4 — đề xuất chờ chủ backend xác nhận

Owner UI: Tuấn. Backend đơn: Nghĩa; kho/SQL Server: Minh; quản trị đơn: Khải; review/test: Điểm.
Đây là hợp đồng trình bày mới, chưa phải bảng chuyển trạng thái nghiệp vụ đã được nhóm nghiệm thu.

## Cách nối

Blueprint app/tuan_w4_ui.py đã đăng ký trong create_app. Không chứa SQL hoặc transaction.
Backend bàn giao adapter vào cấu hình ứng dụng:

~~~python
# Chỉ thêm khi adapter thật đã có và đã được review.
app.config["TUAN_ORDER_UI_PROVIDER"] = BackendOrdersAdapter()
~~~

Không bật provider giả trong cấu hình chạy thật. Provider hiện mặc định None.

## Chữ ký hàm

| Hàm đồng bộ | Đầu vào do server lấy | Kết quả |
| --- | --- | --- |
| list_orders(*, user_id) | user_id lấy từ session | list[OrderView], chỉ đơn thuộc tài khoản |
| get_order(*, user_id, order_id) | owner từ session, mã đơn trong URL | OrderView hoặc None |
| cancel_order(*, user_id, order_id) | owner từ session, mã đơn trong URL | {"ok": True} chỉ sau khi commit thành công; nếu bị từ chối trả {"ok": False} |

cancel_order là tùy chọn. Chưa có hàm thì UI không cung cấp thao tác hủy.
get_order/list_orders không được lấy user_id từ query/form. UI còn kiểm owner và id trước khi render; đó là lớp bảo vệ bổ sung, không thay truy vấn có kiểm quyền.
Provider lỗi hoặc dữ liệu thiếu/tiền không hợp lệ: trả trang chưa kết nối, không hiển thị traceback.

## OrderView

| Key | Kiểu / ý nghĩa |
| --- | --- |
| id | int > 0, mã đơn thực |
| user_id | int > 0, bằng user_id của session |
| created_at | chuỗi ngày giờ đã định dạng |
| status_label | nhãn trạng thái do backend quyết định |
| delivery_stage | pending / store / shipping / completed / cancelled, chỉ để trình bày |
| fulfillment | delivery / pickup |
| payment_status | pending / paid / failed / cancelled; không suy từ phương thức trả tiền |
| payment_status_label | nhãn thanh toán backend đã xác minh |
| payment_method_label | nhãn phương thức thanh toán thực tế |
| can_cancel | bool do backend xác định; không phải dữ liệu người dùng tự gửi |
| items_total, total | số hoặc chuỗi số VND hữu hạn, không âm; backend tính và chốt |
| shipping_fee | số không âm hoặc None nếu chưa xác định; 0 là miễn phí thật |
| receiver | {name, phone, address}: snapshot trong đơn, không lấy từ hồ sơ hiện tại |
| items | list dòng hàng snapshot |

Mỗi dòng items: product_name, size, color (chuỗi), quantity (int > 0), unit_price và subtotal (số VND không âm).
UI không tính lại tổng từ giá sản phẩm hiện tại. Không dùng tên bảng/cột này để tự sửa schema; adapter ánh xạ schema hiện có.

- Với delivery: timeline dùng store → shipping → completed. pending chưa có tiến trình xác nhận; cancelled không hiển thị tiến trình giao tiếp.
- Với pickup: hiển thị nhãn backend, không tự suy thành luồng vận chuyển.
- Không tự đổi payment_status=paid chỉ vì khách chọn bank_transfer.
- None và lỗi backend không được biến thành một danh sách trống.
- Danh sách rỗng thật phải là [] từ provider đã kết nối.

## Quy tắc hủy thuộc backend

Backend phải kiểm lại quyền và trạng thái hiện tại trong transaction ngay lúc hủy, kể cả UI vừa đọc can_cancel=True.
Chống hủy lặp, hoàn tồn chính xác một lần, xử lý thanh toán và ghi nhật ký thuộc Nghĩa/Minh.
Chỉ trả ok=True sau khi toàn bộ thao tác thành công. Timeout/kết quả không rõ phải tra cứu lại trạng thái trước khi thử tiếp.
Route UI không trực tiếp sửa DonHang hoặc SoLuongTon. Các POST vẫn được prepare_csrf của dự án bảo vệ.

## Endpoint UI đã có

- GET /my-orders
- GET /my-orders/<int:order_id>
- POST /my-orders/<int:order_id>/cancel

Khách chưa đăng nhập được chuyển tới /login với next nội bộ. Role Seller/Admin không được mở trang đơn Customer.
Đơn không tồn tại hoặc khác owner trả 404, không tiết lộ có tồn tại đơn của người khác.
Chưa có provider: HTTP 503. Bản này chưa hỗ trợ tra cứu an toàn đơn vãng lai có user_id=NULL.

## Cần xác nhận trước khi nghiệm thu

Nghĩa chốt bảng chuyển trạng thái và adapter thật; Minh thống nhất snapshot/transaction; Khải xác nhận thay đổi trạng thái từ admin.
Điểm kiểm quyền GET/POST, đổi trạng thái giữa hai request, hủy lặp, timeout, SQL Server và dữ liệu trước/sau.
Các kiểm thử FakeProvider chỉ chứng minh UI nối đúng contract, không chứng minh service đơn/payment/kho đã triển khai.
