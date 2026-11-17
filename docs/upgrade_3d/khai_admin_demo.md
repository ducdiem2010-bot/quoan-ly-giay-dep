# Khải K3.2 — Kịch bản demo và minh chứng cần chụp

Khởi động bằng SQLite test; đăng nhập Admin, mở `/admin/products`.

| Ca | Thao tác | Kỳ vọng | Minh chứng |
|---|---|---|---|
| TC12 | Xem sản phẩm tồn bằng 0 | Nhãn Hết hàng (0) | `docs/QA_3DAY/evidence/khai_admin_soldout.png` — CHƯA CHỤP |
| TC16 | Guest truy cập `/admin/products` | Bị chặn/đăng nhập | CHƯA CHỤP |
| K2.1 | Chọn Ẩn/Hiện | Có confirm; hủy confirm không gửi POST; CSRF còn nguyên | `khai_admin_confirm.png` — CHƯA CHỤP |
| K2.2a | Nhập tồn -1, 1.5, rỗng | Báo lỗi và không gửi sai dữ liệu | `khai_admin_bad_stock.png` — CHƯA CHỤP |
| K2.2b | Nhập màu/size đã tồn tại | Không tạo hai dòng trùng, thông báo rõ | `khai_admin_duplicate.png` — CHƯA CHỤP |

Không tự đánh PASS trước khi thử trên trình duyệt thật. SQL Server V2 còn BLOCKED.
