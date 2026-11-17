# Điểm D3.1 — Báo cáo kiểm thử bản tích hợp ứng viên

## Đã xác minh thực tế

- Cú pháp Python: `compileall` PASS cho thư mục `app` và `tests`.
- Cú pháp JavaScript: `node --check app/static/js/admin_product_upgrade.js` PASS.
- SQL SQLite chạy trong bộ nhớ tạm (**5/5 ca tại `sqlite_query_smoke.txt`**): `latest` có 6 sản phẩm công khai; `best sellers` rỗng trên seed gốc; fixture bán 2 + 3, hủy + 9 trả `TongDaBan=5`.

## Chưa thực thi

- Bộ unittest Flask mới, regression cũ, HTTP `/`, `/products`, `/new-arrivals`, `/best-sellers`: CHƯA KIỂM CHỨNG — thiếu package Flask trong môi trường đóng gói.
- Manual Test trên Windows: CHƯA KIỂM CHỨNG.
- SQL Server V2: BLOCKED — không có DB test và quy tắc thanh toán chưa được xác nhận.
- Nghiệm thu đủ 24 TC theo Excel, minh chứng PR/ảnh: CHƯA KIỂM CHỨNG.

Không tuyên bố 100% PASS, release readiness hay đạt 9/10 điểm nếu chưa có minh chứng. Các lỗi P0 trong log cũ cần retest sau khi ghép bản mới.
