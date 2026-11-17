> Cập nhật v3: xem [README_TRA_HANG_V3.md](README_TRA_HANG_V3.md) cho quy tắc hiện hành. Mô tả phân loại hàng trả/hủy khi đang giao bên dưới thuộc phiên bản cũ.

# NHÓM 6 — HƯỚNG DẪN CHẠY BẢN NÂNG CẤP TRẢ HÀNG, HOÀN TIỀN

## Phạm vi

- **Doanh thu bán hàng** chỉ tính khi đơn có trạng thái **Hoàn thành**, đã giao và đã ghi nhận thanh toán. Tiền thu trước khi giao được theo dõi riêng.
- Đơn **Hoàn thành** có thể trả một phần theo biến thể (size/màu), số lượng tốt/hỏng. **Hàng tốt** cộng kho bán được khi nhân viên xác nhận nhận hàng; **hàng hỏng** không cộng kho.
- Số lượng bán ròng = số sản phẩm đã bán trong đơn Hoàn thành trừ số đã nhận trả. **Doanh thu thuần** = doanh số gốc của đơn Hoàn thành trừ khoản giảm doanh thu/hoàn tiền được phê duyệt khi nhận hàng trả; khoản **tiền thực hoàn** được ghi riêng, chỉ phát sinh sau nút **Xác nhận ĐÃ HOÀN TIỀN**.
- Đơn đã thu tiền nhưng hủy vẫn có công nợ hoàn tiền. Nhân viên được xác nhận tiền đã hoàn một phần hoặc toàn bộ. Nút xác nhận **không tự chuyển khoản**.
- Admin đặt lại mật khẩu nhân viên; số điện thoại bắt buộc khi tạo nhân viên; Admin **xóa thật** tài khoản Seller, lưu snapshot tên và nhật ký vai trò xử lý để không xóa đơn hàng.

## Cài đặt trên Windows — SQLite (demo)

Mở PowerShell **trong thư mục chứa `run.py` và `requirements_sqlite.txt`**:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements_sqlite.txt
$env:DB_BACKEND = 'sqlite'
$env:SECRET_KEY = 'nhom6-local-testing-key-change-before-deployment'
.\.venv\Scripts\python.exe run.py
```

Mở http://127.0.0.1:5000. Demo SQLite được tạo trong `instance/demo.sqlite3` nếu chưa có. Không đưa database demo đã thay đổi lên GitHub hoặc bàn giao chứa thông tin riêng.

Chạy kiểm thử (từ thư mục chứa `tests/`):

```powershell
$env:DB_BACKEND = 'sqlite'
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test*.py' -v
```

## Nghiệp vụ thử bằng giao diện

1. Đăng nhập tài khoản Admin/Nhân viên trong dữ liệu demo. Tạo đơn có **3 đôi** giày và thực hiện **Xác nhận → Giao hàng → Xác nhận đã giao → Ghi nhận thanh toán → Hoàn thành** (thanh toán có thể thực hiện trước khi giao). Kiểm tra Dashboard chỉ cộng doanh thu khi **Hoàn thành**.
2. Mở **Chi tiết đơn hàng** trên trang quản trị, mục **Trả hàng một phần sau Hoàn thành**. Nhập 1 đôi **không lỗi**, tiền giảm đúng giá một đôi; bấm **Xác nhận hoàn hàng**. Tồn kho tăng 1; doanh số gốc vẫn ghi 3 đôi, doanh số ròng còn 2; hiện **Chờ hoàn tiền**.
3. Nhập khoản thực sự đã trả cho khách tại **Xác nhận ĐÃ HOÀN TIỀN**. Kiểm tra ghi nhận số tiền, người thực hiện, thời gian và không còn công nợ nếu đã hoàn đủ.
4. Với đơn khác, trả 1 đôi **hỏng/lỗi**: tồn kho bán được **không tăng**; nếu cửa hàng duyệt hoàn tiền thì khách vẫn có thể nhận tiền hoàn. Có thể chọn cả hàng tốt và hàng lỗi trong một lượt.
5. Trên **Quản lý nhân viên**, sử dụng **Đặt lại mật khẩu** để thay mật khẩu Seller. Sau đó thử **Xóa** Seller đã tham gia đơn; xác nhận không đăng nhập được bằng tài khoản đã xóa và lịch sử đơn vẫn còn.

## SQL Server

SQL Server là môi trường **cần kiểm thử trực tiếp riêng**. File đã bổ sung:

- `database/migrate_returns_refunds_staff_sqlserver.sql` (migration bổ sung trên database đã triển khai).
- `database/upgrade_existing_sqlserver.sql` và `database/init_database_sqlserver.sql` có đoạn định nghĩa các bảng liên quan.

**Sao lưu database trước khi chạy migration**, kiểm tra kết quả trên bản test SQL Server trước khi chạy dữ liệu thật. Không được coi việc test SQLite PASS là bằng chứng SQL Server PASS.

## Nguyên tắc và giới hạn

Không thay đổi phí giao hàng, Quên mật khẩu, quy trình nhận tại cửa hàng. Giữ quy tắc chỉ hoàn kho đơn hủy đang giao khi hàng thực về. Hệ thống ghi nhận việc hoàn tiền thủ công/mô phỏng, **không kết nối chuyển khoản ngân hàng**.
