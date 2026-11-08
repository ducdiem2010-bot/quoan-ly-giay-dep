# Demo nhanh – Admin sản phẩm và biến thể (2–3 phút)

## Chuẩn bị

1. Cài thư viện: `python -m pip install -r requirements.txt`.
2. Chạy `python run.py`.
3. Đăng nhập tài khoản Admin demo đã được nhóm cấu hình.
4. Mở `/admin/products`.

## Kịch bản trình diễn

1. **Tồn kho bằng 0:** tìm sản phẩm/biến thể có tồn 0, chỉ vào nhãn đỏ `Hết hàng · tồn 0`.
2. **Ẩn sản phẩm:** nhấn `Ẩn` → hộp xác nhận xuất hiện → chọn `Hủy` để chứng minh chưa thay đổi; thử lại và chọn `Ẩn sản phẩm`, danh sách hiển thị nhãn `Đã ẩn`.
3. **Hiện sản phẩm:** ở dòng vừa ẩn, nhấn `Hiện` → xác nhận; nhãn trở lại `Đang hiển thị`.
4. **Thêm biến thể hợp lệ:** vào `Biến thể`, nhập size/màu và tồn `0`, nhấn `Thêm biến thể`; kiểm tra nhãn hết hàng.
5. **Thử input sai:** nhập tồn `-1` hoặc `1.5`, nhấn lưu; hệ thống báo lỗi và giữ nguyên dữ liệu đã nhập. Thử thêm tổ hợp màu + size bị trùng để xem thông báo từ server/DB.
6. **CSRF:** xác nhận form ẩn/hiện và form biến thể vẫn có hidden `csrf_token`; không xóa trường này khi chỉnh giao diện.

## Bằng chứng cần chụp khi demo trên máy nhóm

- `E01_admin_products_stock_zero.png`: bảng sản phẩm có tồn tổng bằng 0.
- `E02_admin_products_hidden.png`: nhãn `Đã ẩn` và nút `Hiện`.
- `E03_admin_visibility_confirm.png`: hộp xác nhận ẩn/hiện.
- `E04_admin_variant_stock_zero.png`: bảng biến thể có tồn 0.
- `E05_admin_variant_invalid_input.png`: thông báo lỗi với giá trị `-1` hoặc `1.5` còn nguyên.
- `E06_admin_variant_valid_zero.png`: thêm/lưu tồn 0 thành công.

Ảnh chụp thực tế chưa được tạo trong môi trường đóng gói vì không có Flask/browser runtime; không sử dụng ảnh minh họa giả làm bằng chứng QA.
