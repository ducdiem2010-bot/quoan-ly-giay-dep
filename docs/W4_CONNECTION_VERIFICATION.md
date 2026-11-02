# Kiểm tra bộ nối backend UI tuần 4

Ngày kiểm tra: 02/11/2026. Bản này bổ sung factory và adapter cho frontend đã bàn giao.

| Phạm vi | Kết quả | Giới hạn |
| --- | --- | --- |
| Unittest toàn dự án | 66/66 PASS | 35 test cũ + 17 test UI + 14 test bộ nối; SQLite và service giả lập |
| Bộ nối qua biến môi trường/config | PASS | Factory, app context, provider trực tiếp, không cache giữa app, chặn factory sai |
| List/detail/cancel qua adapter | PASS trong test | Session owner, CSRF, chỉ đọc khi thiếu cancel, đọc lại trạng thái; không phải backend Nghĩa thật |
| Lệnh kiểm tra GET | 3/3 kịch bản đúng mong đợi | Chưa cấu hình exit 2; fixture đọc đúng chủ exit 0; khác chủ/detail 404 exit 1 |
| Chromium 153 | 39 lượt layout + 6 thao tác PASS | 375/768/1280px, gồm preview và màn hình 503, CDN Bootstrap chặn để kiểm CSS nội bộ |
| JS runtime pageerror | Không ghi nhận | Theo tập trang/thao tác đã chạy |
| SQL Server và backend Nghĩa | BLOCKED / NOT RUN | Chưa có adapter thật/service và môi trường đã nghiệm thu |
| Kho, payment sandbox, quản trị đơn | Chưa nghiệm thu | Không triển khai thay Minh/Nghĩa/Khải trong bản này |

## Lệnh đã chạy

~~~text
python -m unittest discover -s tests -p "test*.py" -v
python tests/run_browser_smoke_w4.py
python scripts/check_order_ui_connection.py --user-id 3
python scripts/check_order_ui_connection.py --user-id 3 --order-id 4101
python scripts/check_order_ui_connection.py --user-id 9 --order-id 4101
~~~

Các lệnh CLI có cấu hình fixture chỉ chạy trong thư mục tạm, DB SQLite tạm; fixture không đóng gói vào app chạy thật. Script CLI chỉ GET và dùng session giả lập, không kiểm chứng auth hoặc tạo/hủy đơn thật.

## Minh chứng

- docs/evidence/w4_connection/unittest_results.txt
- docs/evidence/w4_connection/browser_results.json
- docs/evidence/w4_connection/cli_results.json
- docs/TUAN_W4_CHANGES.json: hash và file giữ nguyên so với WED nhóm 6(7).zip, cùng khác biệt so với ZIP frontend đầu vào.
- docs/TUAN_W4_BACKEND_HANDOFF.md: cách Nghĩa gắn backend thật.

Không thêm screenshot mới vào gói; ảnh frontend v1 được giữ nguyên để tham khảo layout.
Mặc định provider None và preview tắt; người dùng vẫn thấy chưa kết nối cho tới khi gắn adapter thật.
Chưa đánh DONE W4-009/W4-024 hoặc toàn tuần 4 chỉ từ các test này.
Các lỗi backend đã biết của bản gốc (chưa trừ/hoàn tồn, sản phẩm ẩn trong giỏ vẫn đặt được, chưa có portal Nhân viên) chưa được xử lý trong phạm vi bộ nối này.
