# DANH SÁCH CÁC RÀO CẢN KỸ THUẬT (BLOCKER) & PHỤ THUỘC THÀNH VIÊN
**Người lập:** Điểm (Nhóm trưởng Nhóm 6)
**Phạm vi:** Nghiệm thu kỹ thuật Tuần 3
**Cập nhật:** 15/10/2026

---

## 1. TÌNH TRẠNG VỀ WORKBOOK 106 TEST CASE
- **Xác minh thực tế trong workspace:** Trong thư mục `docs/` chỉ có tệp `BANG_DOI_CHIEU_NGHIEM_THU.xlsx` (bảng đối chiếu nghiệm thu Tuần 2) và tài liệu kiến trúc. **CHƯA TÌM THẤY tệp bảng tính 106 test case chi tiết trong workspace hiện tại**.
- **Quyết định của Nhóm trưởng Điểm:**
  + Ghi nhận trung thực: **Chưa thể xác minh danh sách mã 106 test case chi tiết từ tài liệu nguồn ngoài**.
  + **Tuyệt đối không tự bịa đặt mã test ID** trái với thực tế.
  + Đã chuyển dịch các kịch bản kiểm thử chủ chốt vào ma trận 86 chức năng chuẩn và 12 kịch bản chéo bắt buộc (D29-01 đến D29-12). Khi nào nhận được workbook gốc, Điểm chỉ cần gắn mã tương ứng vào công cụ kiểm toán `audit_coverage.py`.

---

## 2. DANH SÁCH CHI TIẾT CÁC BLOCKER KỸ THUẬT

### Blocker 1: Cấu hình và Schema SQL Server (Phụ trách: Minh – W3-004)
- **Vấn đề:**
  1. `database/schema.sql` đang ghi `CREATE DATABASE QuanLyBanHang` và `USE QuanLyBanHang`, lệch hoàn toàn với tên database chính thức của nhóm là `quan_ly_giay_dep`.
  2. Đầu tệp `schema.sql` có các lệnh `DROP TABLE IF EXISTS ...` từ dòng 10–18, có thể xóa sạch dữ liệu nếu chạy trực tiếp trên SQL Server của nhóm.
  3. Bảng `SanPham` chưa có trường `TrangThai BIT DEFAULT 1` hoặc `DaAn` để hỗ trợ sản phẩm ẩn (Quy tắc A02).
  4. Ràng buộc `CK_SanPham_GiaBan CHECK (GiaBan >= 0)` cho phép giá bán = 0, vi phạm quy tắc A07 (giá phải > 0 VNĐ).
  5. Chưa có bảng `HinhAnhSanPham` (hỗ trợ nhiều ảnh A01, A04, A05) và bảng `SanPhamYeuThich`.
- **Yêu cầu đối với Minh:**
  - Viết script migration an toàn (ALTER TABLE / CREATE TABLE mới), không dùng DROP TABLE trên `quan_ly_giay_dep`.

---

### Blocker 2: Backend Public Lọc, Tìm kiếm và Phân trang (Phụ trách: Minh – W3-005)
- **Vấn đề:**
  1. Trong `app/data.py`, câu truy vấn `SELECT_PRODUCT` chưa có điều kiện lọc sản phẩm ẩn (`WHERE sp.TrangThai = 1`).
  2. Chưa nhận các tham số theo đúng API Contract: `brand_id`, `gender`, `color_id`, `size_id`, `price_min`, `price_max`, `sort`, `page`.
  3. Chưa có phân trang `LIMIT / OFFSET` (hoặc `OFFSET ... FETCH NEXT`), dẫn tới test D29-05 bị BLOCKED.
- **Yêu cầu đối với Minh:**
  - Hoàn thiện hàm `get_all_products(...)` mở rộng theo API Contract.

---

### Blocker 3: Logic lọc màu và size trên cùng một biến thể (Phụ trách: Nghĩa – W3-007)
- **Vấn đề:**
  - Cần bảo đảm khi khách lọc đồng thời `color` và `size`, câu lệnh SQL phải kiểm tra trên CÙNG MỘT dòng `BienTheSanPham`.
  - Ví dụ: SP101 có Đen-41 và Trắng-40. Khi lọc Đen-40 thì SP101 BẮT BUỘC KHÔNG ĐƯỢC XUẤT HIỆN.
- **Yêu cầu đối với Nghĩa:**
  - Kiểm tra lại câu query SQL biến thể, tránh dùng 2 subquery độc lập ghép chéo.

---

### Blocker 4: Form Admin CRUD, Upload Ảnh & Yêu thích (Phụ trách: Khải – W3-013, W3-014, W3-054)
- **Vấn đề:**
  1. `app/routes.py` tại route `/admin/product/add` mới chỉ là form demo tuần 2: hiển thị thông báo flash `"Biểu mẫu đạt kiểm tra đầu vào. Tuần 2 mới chuẩn bị form, CHƯA lưu sản phẩm."`, chưa có câu lệnh `INSERT` vào database.
  2. Logic kiểm tra giá vẫn viết `price >= 0`, cần đổi thành `price > 0` theo quy tắc A07.
  3. Chưa có endpoint `/favorite` và `/favorites` cho khách hàng lưu và xem sản phẩm yêu thích (dẫn tới test W3-030 phần favorite bị BLOCKED).
  4. Chưa có logic upload file ảnh thật (kiểm tra dung lượng <= 5MB và magic bytes theo A05).
- **Yêu cầu đối với Khải:**
  - Triển khai logic INSERT sản phẩm kèm biến thể trong giao dịch (Transaction có Rollback nếu lỗi).
  - Triển khai endpoint Favorites và Upload ảnh.

---

### Blocker 5: Kiểm chứng cài đặt trên 5 máy thành viên (Toàn nhóm – W3-060)
- **Vấn đề:**
  - Hiện tại toàn bộ mã nguồn và test suite mới chỉ được kiểm chứng trên máy của Điểm.
  - Chưa thể khẳng định 100% dự án chạy trơn tru trên 4 máy còn lại.
- **Yêu cầu đối với toàn nhóm:**
  - Từng thành viên (Minh, Nghĩa, Khải, Tuấn) pull nhánh mới nhất về, chạy lệnh `python tools/w3_diem/run_all_checks.py`, chụp ảnh Terminal và gửi lại cho Điểm tổng hợp báo cáo.
