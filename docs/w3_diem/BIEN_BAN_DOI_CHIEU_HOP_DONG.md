# BIÊN BẢN ĐỐI CHIẾU HỢP ĐỒNG USE CASE - ERD - SQL - API (W3-015)

**Người thực hiện:** Điểm (Nhóm trưởng)
**Tổng số phát hiện:** 12

| Mã | Mức độ | Người chịu trách nhiệm | Mã W3 | Vấn đề | Đề xuất giải quyết |
|---|---|---|---|---|---|
| AUDIT-01 | **Major** | Khải | W3-013 | Kiểm tra giá cho phép bằng 0 (vi phạm A07) (app/routes.py:193) | Sửa điều kiện thành 'price > 0'. |
| AUDIT-02 | **Critical** | Khải | W3-013 | Form thêm sản phẩm Admin chưa có logic INSERT vào Database (app/routes.py:194) | Triển khai giao dịch INSERT sản phẩm, biến thể và rollback nếu lỗi. |
| AUDIT-03 | **Major** | Khải | W3-014 | Chưa có route xử lý Yêu thích sản phẩm (Favorites) (app/routes.py:0) | Triển khai endpoint POST /favorite/<id> và GET /favorites với xác thực session khách. |
| AUDIT-04 | **Major** | Khải | W3-054 | Chưa có route upload và quản lý nhiều ảnh sản phẩm (A01, A05) (app/routes.py:0) | Triển khai upload ảnh theo quy tắc A05 và bảng HinhAnhSanPham. |
| AUDIT-05 | **Critical** | Minh | W3-004 | Truy vấn danh sách sản phẩm chưa lọc sản phẩm ẩn (Quy tắc A02) (app/data.py:4) | Bổ sung điều kiện WHERE sp.TrangThai = 1 (hoặc DaAn = 0) cho các truy vấn public. |
| AUDIT-06 | **Major** | Minh | W3-005 | Thiếu các tham số lọc/sắp xếp/phân trang theo API Contract: brand_id, gender, color_id, size_id, price_min, price_max, sort, page (app/data.py:19) | Bổ sung xử lý tham số: brand_id, gender, color_id, size_id, price_min, price_max, sort, page kết hợp phân trang LIMIT/OFFSET. |
| AUDIT-08 | **Critical** | Minh | W3-004 | Schema SQL Server vẫn khai báo 'QuanLyBanHang' thay vì 'quan_ly_giay_dep' (database/schema.sql:3) | Đổi tên USE QuanLyBanHang thành USE quan_ly_giay_dep và bỏ lệnh tự ý CREATE DATABASE master. |
| AUDIT-09 | **Critical** | Minh | W3-004 | Script schema.sql chứa lệnh DROP TABLE hủy dữ liệu (database/schema.sql:10) | Chỉ sử dụng script migration an toàn, cấm chạy trực tiếp schema.sql trên quan_ly_giay_dep. |
| AUDIT-10 | **Critical** | Minh | W3-004 | Bảng SanPham chưa có cột TrangThai / DaAn để quản lý sản phẩm ẩn (A02) (database/schema.sql:55) | Thêm cột: TrangThai BIT NOT NULL DEFAULT 1 (1: Hiển thị, 0: Ẩn). |
| AUDIT-11 | **Major** | Minh | W3-004 | Ràng buộc CSDL CHECK (GiaBan >= 0) cho phép giá = 0, trái quy tắc A07 (database/schema.sql:66) | Sửa thành: CHECK (GiaBan > 0). |
| AUDIT-12 | **Major** | Minh | W3-004 | Thiếu bảng HinhAnhSanPham trong SQL Server (A01, A04) (database/schema.sql:0) | Tạo bảng HinhAnhSanPham(MaHinhAnh, MaSanPham, DuongDan, LaDaiDien). |
| AUDIT-13 | **Major** | Minh | W3-004 | Thiếu bảng SanPhamYeuThich trong SQL Server (database/schema.sql:0) | Tạo bảng SanPhamYeuThich(MaNguoiDung, MaSanPham, NgayLuu). |
