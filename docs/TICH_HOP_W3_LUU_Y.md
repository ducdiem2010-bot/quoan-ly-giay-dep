# Tình trạng tích hợp W3
- Tuấn: templates và CSS/JS từ W3-065, W3-066; đã nối blueprint /products với dữ liệu dự án; favorite server chưa có bảng trong schema 9 bảng → để trạng thái chưa khả dụng.
- Khải: tham khảo prototype giao diện/luồng admin thu 3, thu 6; CSS nguồn thu 6 được lưu ở docs/references/khai_admin_products_source.css; adapter Flask+SQL được viết bổ sung tại app/admin_w3.py, KHÔNG khẳng định adapter là code gốc Khải.
- Minh: schema.sql và seed.sql trong bản nhóm; SQL Server thật chưa xác minh; migration riêng cần kiểm tra trên DB test.
- Nghĩa: không tự điền kết quả kiểm thử; phần schema liên quan ProductVariant giữ nguyên.
- vs demo: SQL Server schema khác (ThuongHieu, HienThi, HinhAnh, GioiTinh); không chép đè db.py; rút kinh nghiệm từ luồng quản trị và transactions.
- Giao hàng/thanh toán online đã chốt trong scope, chưa phải chức năng W2–W3 đã triển khai. Không ghi phủ định ở UI.
