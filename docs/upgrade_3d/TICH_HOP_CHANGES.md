# Biên bản tích hợp ứng viên — Nhóm 6

- Lấy nguồn từ ZIP do người dùng cung cấp; không sửa file Excel phân công.
- M1.1–M3.2: tạo service/trang/test Mới nhất; bước M3.1 chỉnh tối thiểu `app/__init__.py`, `app/routes/public.py` và thêm stylesheet trang chủ.
- N1.1–N3.2: tái sử dụng ý tưởng các file `best_sellers.*` ở gốc, tạo module chuẩn cùng SQLite JOIN/GROUP/ORDER, 8 test mới và tài liệu SQL. Không di chuyển/xóa bản nháp gốc vì chưa xác minh có quy trình khác đang dùng.
- K1.1–K3.2: chỉ bổ sung CSS/JS Admin và HTML trong hai template W3; không sửa route Admin, CSRF hoặc schema.
- T1.1–T3.2: giữ Footer mới, Header, slider, card và ảnh; tải `storefront_upgrade.css` chỉ cho trang chủ và trang featured.
- D1.1–D3.2: tạo khung hồ sơ QA đúng đường dẫn và trạng thái thực tế; ảnh/PR/retest chưa làm không được đánh PASS.
- Kiểm chứng: Python compileall và node --check PASS, SQL SQLite fixture PASS. **Flask unittest/HTTP chưa chạy** do thiếu Flask trong môi trường hiện tại. **SQL Server V2 chưa nghiệm thu**.
- Những file đầu vào Excel chỉ định `database/v2/schema_v2_fresh_safe.sql` và `app/v2.py` không tồn tại trong ZIP; thay vào đó đã đọc `database/schema_v2.sql` và ghi rõ blocker.
- Đối chiếu PR GitHub: chưa thể tải mã các nhánh tại môi trường đóng gói; cần trưởng nhóm so sánh commit và nguồn chính chủ trước khi merge.
