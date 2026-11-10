# Tài liệu Đối soát Vết (Traceability Matrix): Đơn hàng - Thanh toán - Tồn kho
**Thành viên thực hiện:** Nghĩa & Minh  
**Môn học:** Công nghệ Phần mềm  

## 1. Bảng ánh xạ Use Case & Endpoint (API)
| Mã Use Case | Nghiệp vụ chi tiết | Endpoint API tương ứng | Trạng thái xử lý |
| :--- | :--- | :--- | :--- |
| UC-CHECKOUT | Khách hàng gửi thông tin giỏ hàng để tạo đơn | `POST /api/order/checkout` | Hoàn thành (Mock/DB) |
| UC-CANCEL | Khách hàng hủy đơn trước khi xác nhận | `POST /api/order/cancel/<id>` | Hoàn thành |
| UC-PAY-ONLINE | Tạo URL thanh toán Sandbox | `POST /api/payment/create_url` | Hoàn thành |
| UC-IPN-CALLBACK| Nhận phản hồi thanh toán & chống lặp | `POST /api/payment/callback` | Hoàn thành |

## 2. Quy tắc chuyển đổi Trạng thái Đơn hàng & Thanh toán
- **Trạng thái `0` (Chờ xác nhận):** Đơn hàng mới khởi tạo thành công, giữ chỗ nhưng chưa giao. Khách được quyền hủy đơn.
- **Trạng thái `1` (Đã thanh toán / Đã xác nhận):** Thanh toán Sandbox thành công hoặc Admin xác nhận. **Khóa quyền hủy đơn của khách.**
- **Trạng thái `-1` (Đã hủy):** Đơn bị hủy thành công trước khi xác nhận.

## 3. Cam kết toàn vẹn dữ liệu (DoD Compliance)
- Mọi đơn hàng đều thực hiện **Snapshot** thông tin người nhận tại thời điểm đặt để tránh thay đổi lịch sử.
- Giao dịch thanh toán online được xác minh qua chữ ký (Signature Hash) và chống ghi trùng lặp mã giao dịch (`Transaction ID`).
- Không phát sinh tình trạng tồn kho âm nhờ ràng buộc kiểm tra số lượng trước khi xác nhận.