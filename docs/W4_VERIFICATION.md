> Nhật ký frontend v1 được giữ lại. Kết quả mới của bộ nối xem [W4_CONNECTION_VERIFICATION.md](W4_CONNECTION_VERIFICATION.md). Ảnh v1 minh họa layout trước khi bổ sung factory; không phải bằng chứng backend thật.

# Kết quả kiểm chứng W4 — phần frontend Tuấn

Ngày thực hiện: 01/11/2026 (Asia/Bangkok).

| Hạng mục | Kết quả thực tế |
| --- | --- |
| Python | 3.12.14; Flask 3.1.3 |
| Bài test Python | 52/52 PASS: 35 bài gốc + 17 bài UI/contract mới |
| Trình duyệt | Chromium 153.0.8010.0, headless, DB SQLite test tạm |
| Kiểm tra trang/kích thước | 39 lượt: 375px / 768px / 1280px |
| Tràn ngang cấp trang | 0 lượt; scrollWidth bằng viewport trong tất cả lượt |
| Ảnh hỏng | 0 trong các trang kiểm tra |
| JavaScript pageerror | 0 |
| Kiểm tra hành vi trình duyệt | 6 nhóm PASS |
| Liên kết từng đơn ở preview | 5/5 đi tới trạng thái đúng |
| Ảnh minh chứng | 25 PNG: 23 ảnh bản sửa và 2 ảnh checkout bản gốc |
| Backend/order service thật | BLOCKED — chưa được bàn giao provider |
| SQL Server | NOT RUN |
| Gateway/payment online | BLOCKED — chưa tích hợp |
| Điện thoại vật lý / CDN Bootstrap online | NOT RUN |

## Hành vi đã chạy

- Invalid client form: blocked POST, inline errors visible
- Pickup: no required address, no shipping fee
- Bank transfer: pending explanation, no paid claim
- Valid pickup checkout: one POST, real SQLite order, snapshot-labelled response
- Sample cancellation dialog: opens/closes without sending cancellation
- Admin dashboard add link reaches real W3 product form

## Phạm vi minh chứng

Ảnh checkout/result chụp từ trang chạy trên SQLite test thực. Ảnh order/payment có chữ sample chụp UI dữ liệu mẫu, luôn có nhãn; không dùng chúng để nghiệm thu nghiệp vụ backend.

CSS nội bộ được kiểm tra khi chặn CDN. Không suy ra thời gian tải chuẩn hoặc SQL Server đạt từ kết quả này.

Đã phát hiện và sửa trong kiểm tra trình duyệt: địa chỉ cũ quá ngắn vẫn kích hoạt minlength khi chọn pickup. Bản cuối disabled trường địa chỉ khi pickup, giữ giá trị để dùng lại khi chuyển delivery.

Không sửa các bài test gốc để thay đổi kết quả. Các file service/SQL gốc được kiểm tra hash giữ nguyên.

Lỗi nghiệp vụ sản phẩm ẩn trong giỏ, trừ/hoàn tồn và thanh toán online vẫn do backend xử lý. Chưa chốt đủ điều kiện nghiệm thu toàn bộ tuần 4.
