# Khải K1.1 — Audit giao diện Admin

Các điểm đã xác định từ ZIP **trước bản chỉnh sửa**:

1. `app/templates/admin/w3_products.html`: tồn `0` hiển thị số trần, chưa gắn nhãn **Hết hàng**.
2. Cùng file: sản phẩm `HienThi=0` có chữ `Đã ẩn` nhưng chưa có lớp trạng thái dễ phân biệt.
3. Cùng file: form `Ẩn/Hiện` POST trực tiếp, thiếu xác nhận thao tác; phải giữ `csrf_token`.
4. `app/templates/admin/w3_variants.html`: số lượng nhập dạng number nhưng chưa có thông báo client tiếng Việt khi `-1`, `1.5`, rỗng.
5. Cùng file: lỗi màu/size trùng mới phụ thuộc DB; có thể cảnh báo sớm ở client, server/DB vẫn bắt buộc kiểm tra.
6. Cùng hai template: bảng rộng ở màn 375px cần vùng cuộn ngang **trong bảng**, không làm tràn toàn trang.

Đã bổ sung HTML/CSS/JS riêng phạm vi Admin, không thay `app/routes/admin.py`. Ảnh trình duyệt và kết quả thao tác thực tế: CHƯA KIỂM CHỨNG.
