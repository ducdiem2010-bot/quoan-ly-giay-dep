# BÁO CÁO KIỂM THỬ SƠ BỘ (Smoke Test) — NHÓM 6

**Thực hiện:** 12/10/2026. **Môi trường:** Python 3.13 (máy sandbox), Flask từ nguồn gói được đính kèm trong ZIP người dùng để kiểm thử, SQLite demo được khởi tạo mới trong thư mục tạm. **Không dùng SQL Server thật**.

## Kết quả kiểm thử tự động

| Mã | Nội dung | Kết quả |
|---|---|---|
| UT01 | Seed 9 bảng, 10 sản phẩm, 3 danh mục, >=2 user, ràng buộc khóa ngoại, trigger tổng tiền | Đạt |
| UT02 | Trang chủ đọc DB, tìm kiếm SP | Đạt |
| UT03 | Lọc theo danh mục và danh mục không tồn tại | Đạt |
| UT04 | Chi tiết SP hợp lệ, size/số lượng, 404 và ảnh tĩnh | Đạt |
| UT05 | Thêm giỏ bằng session, tính tiền, checkout mẫu, xóa giỏ | Đạt |
| UT06 | Từ chối POST thiếu CSRF, số lượng sai, vượt tồn kho | Đạt |
| UT07 | Yêu cầu Admin login, mật khẩu sai, login đúng, form Admin chỉ kiểm tra dữ liệu | Đạt |
| UT08 | Nhân viên Seller không truy cập trang Admin | Đạt |
| UT09 | Đăng ký và login tài khoản Customer | Đạt |
| UT10 | Xử lý lỗi 500 ẩn traceback trong giao diện | Đạt |

**Kết quả: 10/10 bài tự động đạt** trên SQLite demo (xem `tests/test_smoke.py`). Đã kiểm tra response code, HTML và dữ liệu SQLite; chưa có log kiểm thử 5 máy.

## Kiểm tra chưa hoàn thành
- **Không xác minh SQL Server thực:** sandbox không có dịch vụ SQL Server/ODBC driver, chưa thể khẳng định schema T-SQL chạy thành công.
- **Chưa đo bằng browser thực tại 375/768px:** máy trình duyệt kiểm tra tự động chặn truy cập trang local/file, nên không có bằng chứng thực nghiệm `scrollWidth <= viewport`.
- **Chưa test GitHub clone thực** và năm máy độc lập.
- **Checkout và form thêm sản phẩm vẫn là phạm vi giao diện**; không có tiêu chí chức năng gửi đơn hàng/thêm DB sản phẩm ở tuần 2.

## Lệnh nhóm tự chạy ở VS Code
`python -m unittest discover -s tests -p "test_*.py" -v`

Khi chạy trên từng máy, bổ sung: tên máy, ngày, Python, SQL Server, số test qua, ảnh screenshot trang chủ/sản phẩm/giỏ/admin, lỗi và người sửa.
