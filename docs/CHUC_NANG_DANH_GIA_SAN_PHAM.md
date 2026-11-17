# Chức năng Đánh giá sản phẩm (theo Đặc tả v2.0, mục 1)

## File mới / sửa
| File | Nội dung |
|---|---|
| `app/services/reviews.py` (mới) | Validate, xác thực đã mua, thống kê, phân trang, ẩn/phản hồi |
| `app/routes/reviews.py` (mới) | `POST /product/<id>/reviews`, `GET /admin/reviews`, `POST /admin/reviews/<id>/toggle`, `POST /admin/reviews/<id>/reply` |
| `app/templates/_reviews.html`, `admin/reviews.html` (mới) | Giao diện khách + trang quản trị |
| `app/static/css/product_reviews.css` (mới) | Style |
| `database/migrate_product_reviews_sqlserver.sql` (mới) | Tạo bảng + index cho SQL Server |
| `tests/test_product_reviews.py` (mới) | 21 test theo kịch bản QA mục 6.2 |
| `app/db.py` | SQLite tự tạo bảng `DanhGiaSanPham` + index (không xóa dữ liệu cũ) |
| `app/routes/public.py` | `product_detail` nạp dữ liệu đánh giá; CSRF nhận thêm header `X-CSRF-Token`/JSON |
| `app/__init__.py`, `product_detail.html`, `admin_base.html`, `w12/staff.html` | Đăng ký blueprint, gắn giao diện, thêm menu |
| `tests/test_smoke.py` | Số bảng hợp lệ thêm 16 |

## Mã lỗi
- Luồng form HTML: flash + redirect (guest được đưa tới trang đăng nhập).
- Luồng API (gửi JSON hoặc `Accept: application/json`): trả `{error, code}` đúng 400/401/403/404/409; thành công 201.
- API cần header `X-CSRF-Token` (hoặc `csrf_token` trong body).

## Triển khai SQL Server
Chạy `database/migrate_product_reviews_sqlserver.sql` sau khi backup. Chưa chạy migration thì trang sản phẩm vẫn hiển thị bình thường, phần đánh giá báo "tạm thời chưa khả dụng".
