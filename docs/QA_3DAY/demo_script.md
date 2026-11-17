# Điểm D3.2 — Demo ngắn trên máy nhóm

1. Ghi SHA nhánh test thực tế và `DB_BACKEND=sqlite`, tạo database test riêng.
2. Mở `/`, quan sát hai mục Mới nhất/Bán chạy, đặc biệt trạng thái bán chạy rỗng nếu chỉ có đơn Đã xác nhận.
3. Mở `/new-arrivals` và `/best-sellers`, so thứ tự và liên kết chi tiết.
4. Kiểm tra `/products`, tìm kiếm, giỏ hàng/đăng nhập.
5. Đăng nhập Admin, mở `/admin/products`, kiểm tra tồn 0, ẩn/hiện, nhập tồn sai, chống trùng biến thể.
6. Kiểm tra Footer và responsive 375/768/1280px.
7. Chạy unittest, lưu log; chỉ ghi PASS khi đã quan sát thực tế.
