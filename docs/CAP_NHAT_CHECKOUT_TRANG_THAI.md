# Cập nhật sau ghép W2–W3: checkout + trạng thái sản phẩm

**Nguồn:** yêu cầu chỉnh sửa mới của trưởng nhóm sau khi kiểm tra giao diện đang chạy.
**Không phải** mã nguồn nguyên bản của thành viên hoặc một hạng mục W3 được nghiệm thu từ kế hoạch.

## Những file sửa
- `app/templates/product_detail.html`: nhãn `Giới tính` → `Trạng thái`; hiển thị `Còn hàng/Hết hàng` bằng `TongTon` (tồn kho), giữ riêng `Tổng tồn kho`.
- `app/templates/cart.html`: bỏ thông báo không giao hàng; đổi tổng thành tạm tính.
- `app/templates/checkout.html`: hình thức nhận hàng, địa chỉ giao hàng, COD/chuyển khoản, tạm tính, cảnh báo cổng online chưa có.
- `app/routes.py`: xử lý POST `/checkout` và GET `/checkout/success`.

## File thêm
- `app/checkout_service.py`: xác thực dữ liệu và lưu đơn chờ xác nhận, chi tiết đơn, thông tin giao nhận/thanh toán. Không trừ tồn kho khi đơn chưa được xác nhận, không tự tính phí vận chuyển, không thu tiền.
- `app/templates/checkout_success.html`: phản hồi kết quả đặt yêu cầu.
- `app/static/js/checkout.js`, `app/static/css/checkout.css`, `app/static/css/availability.css`: ẩn/hiện địa chỉ, hướng dẫn thanh toán, CSS responsive.
- `database/migration_checkout_sqlserver.sql`: cần chạy thủ công trên SQL Server sau khi sao lưu và xác minh chọn đúng database.
- `tests/test_checkout_update.py`: kiểm thử trạng thái sản phẩm, chọn phương thức giao/nhận, CSRF, validation và ghi DB SQLite.

## Phân biệt trạng thái
- `Trạng thái sản phẩm` = Còn hàng khi tổng tồn kho >0; ngược lại Hết hàng. Không dùng `SanPham.HienThi` (đang bán/ẩn) làm thông tin tồn kho.
- Đơn mới: `Chờ xác nhận`; Thanh toán: `Chưa thanh toán`.
- Phí vận chuyển: chưa xác định cho giao tận nơi; 0 đồng cho nhận tại cửa hàng. `DonHang.TongTien` chỉ bao gồm hàng hóa.
- Cổng thanh toán online: **chưa tích hợp**. Lựa chọn bị vô hiệu hóa, không có giao dịch thực hoặc phát hành QR.
- Không được đưa hệ thống lên sản xuất nếu chưa có phân quyền truy xuất đơn, HTTPS, kế hoạch tồn kho, bảo mật dữ liệu cá nhân và đối soát thanh toán.

## Giới hạn kiểm thử
Các test tự động chạy ở SQLite demo. SQL Server phải chạy migration và kiểm thử lại trên SSMS + Flask. Không được đánh PASS cho SQL Server khi chưa test thực tế.
