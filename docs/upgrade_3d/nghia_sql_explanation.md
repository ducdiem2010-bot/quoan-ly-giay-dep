# Nghĩa N3.1 — Đối chiếu truy vấn bán chạy

Đã thực thi trực tiếp câu SQLite tại `app/services/best_sellers.py` trên DB SQLite **in-memory** tạo từ `database/schema_sqlite.sql` + `database/seed_sqlite.sql`; tạo thêm bảng `SanPhamHinhAnh` giống init demo.

Fixture tự tạo: một sản phẩm, hai biến thể, đơn `Hoàn thành` có hai dòng 2 và 3; đơn `Đã hủy` có 9 sản phẩm cùng biến thể. Truy vấn trả **một dòng sản phẩm, TongDaBan=5**, tồn tổng 10; đơn hủy không tăng số đã bán.

Đây là kiểm thử SQL độc lập, **không phải PASS của Flask/unit test**. File sản phẩm/đơn trong `instance` không bị truy cập hay thay đổi. Cần chạy `tests/test_best_sellers.py` trên Windows với Flask và nghiệm thu SQL V2 riêng.
