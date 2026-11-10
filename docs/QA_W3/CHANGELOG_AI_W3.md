# NHẬT KÝ MÃ NGUỒN BẢN SỬA AI – 02/11/2026

**Nguồn:** `WED nhóm 6(10).zip`; mã nguồn này do AI chỉnh trên bản sao và **không đại diện cho code thành viên tự viết**. Chưa được Điểm/người phụ trách review và nghiệm thu.

| Task ID | File thay đổi | Đã thực hiện | Kiểm thử đã thực hiện | Người cần review |
|---|---|---|---|---|
| W3-006 | `database/seed.sql`, `database/seed_sqlite.sql`, `database/migrate_w3_visibility_sqlserver.sql` | Thêm 2 sản phẩm giày dép, mẫu ẩn và hết tồn; nâng cấp demo SQLite cũ không xóa 10 sản phẩm cũ | SQLite offline đạt; SQL Server chưa chạy | Minh |
| W3-021 | `app/routes.py` | API GET /api/products/<id>/variants nhận color/size cùng hàng, chặn SP ẩn | Chỉ kiểm cú pháp, test Flask NOT RUN | Nghĩa |
| W3-040 | `app/admin_w3.py`, `app/templates/admin/w3_variants.html` | Admin sửa biến thể qua form + server validate | Chỉ kiểm cú pháp, test Flask NOT RUN | Khải |
| W3-042 | `app/admin_w3.py`, `app/templates/admin/w3_product_form.html` | Có thể tạo biến thể đầu tiên trong cùng transaction khi tạo SP | Chỉ SQLite rollback ví dụ; test Flask NOT RUN | Khải |
| W3-051/057 | `app/routes.py`, `app/db.py`, `database/schema_sqlite.sql`, `database/migrate_w3_favorites_sqlserver.sql` | Favorite lưu riêng theo user, có toggle; nâng cấp SQLite hiện có, migration SQL Server | SQLite constraint đạt; Flask/SQL Server chưa chạy | Khải + Tuấn + Minh |
| W3-006 (test fixture) | `tests/test_smoke.py`; bản gốc `docs/references/test_smoke_w2_original.py` | Cập nhật các assertion số liệu từ 10SP/9bảng sang 12SP/10bảng cho dữ liệu W3, **không bỏ test** | Flask BLOCKED | Điểm |
| W3 liên quan | `verify_w3_offline.py`, `tests/test_w3_extensions.py` | 8 test offline + 6 test Flask mới | 8/8 offline PASS; Flask BLOCKED | Điểm |

## Các thiếu sót chưa được giải quyết
- W3-034/035/036: chưa chốt schema độc lập Brand/Type/Color/Size.
- W3-054/055: chưa có upload/gallery nhiều ảnh an toàn.
- W3-062: chưa có môi trường SQL Server thật.
- W3-069: chưa có hồ sơ/biên bản nghiệm thu có xác nhận và ảnh thực tế.

**Giới hạn kiểm thử:** Không có thư viện Flask trong môi trường tạo bản sửa, pip offline không cài được; không có SQL Server và trình duyệt máy nhóm. 8 offline test không phải 69/69 hoàn thành.

**CẢNH BÁO:** Không dùng trên dữ liệu thực cho đến khi thành viên review, test regression, SQL Server và xử lý P0/P1.
