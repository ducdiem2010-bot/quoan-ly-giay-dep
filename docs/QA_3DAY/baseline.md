# Điểm D1.1 — Baseline tích hợp ứng viên

- Nguồn ZIP: `Nhom6_NangCap_Footer_GiuNguyenCauTruc (1).zip`.
- SHA256 ZIP đầu vào: `2f8a0edd7073b269ed25f81dc50f80b55568c8ebe8f795f6e92e951146e7ff66`.
- ZIP không chứa `.git`, nên **không thể xác minh SHA commit** của các file này.
- Môi trường có thể chạy tĩnh với Python/sqlite3; không có gói Flask để chạy server/unittest.
- Không chạy Flask trên `http://127.0.0.1:5000/` trong môi trường này.
- SQL Server V2: BLOCKED (không có kết nối và chưa chốt điều kiện thanh toán).
- Log `autotest.log` được cung cấp trước đó thuộc bản tích hợp khác: 96 bài, 21 FAIL, 46 ERROR, **không tự coi là baseline mới**.
- Đã giữ nguyên database/schema và seed gốc; kiểm thử SQLite dùng bộ nhớ tạm.
- Trạng thái nghiệm thu chính thức: CHƯA KIỂM CHỨNG.
