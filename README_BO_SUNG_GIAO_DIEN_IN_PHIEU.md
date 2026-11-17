# Nâng cấp giao diện, in chứng từ và nhóm trả hàng (16/11/2026)

## Chạy Windows/PowerShell

Mở VS Code tại thư mục `Nhom6_Website_GiayDep` (chứa `run.py`). Sao lưu DB đang dùng.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements_sqlite.txt
$env:DB_BACKEND = "sqlite"
.\.venv\Scripts\python.exe run.py
```

Nếu không có `requirements_sqlite.txt`, kiểm tra lại bạn đang đứng ở **đúng thư mục con** chứa `run.py`; không dùng requirements ở bên ngoài thư mục này. Xem cổng mà Flask in trong terminal.

Kiểm thử:
```powershell
$env:DB_BACKEND = "sqlite"
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test*.py" -v
```

## Cơ sở dữ liệu

- SQLite: lúc `create_app()` chạy, migration **chỉ thêm** `TraHangChiTiet.MaNhomTra` (nullable) nếu còn thiếu, sau đó tạo index. Không xóa và không gộp các dòng trả cũ. Nên sao lưu `.sqlite3` trước khi chạy bản nâng cấp.
- SQL Server: **sau** migration cũ `database/migrate_returns_refunds_staff_sqlserver.sql`, chạy `database/migrate_return_receipt_group_sqlserver.sql` đúng một lần (có kiểm tra tồn tại, an toàn khi chạy lại). Sao lưu DB trước khi thực hiện. Nếu khởi tạo mới bằng script init/upgrade đã cập nhật thì cột đã có.
- Lần trả mới nhiều dòng có chung `MaNhomTra`. Dữ liệu cũ thiếu mã nhóm được hiển thị riêng và đánh dấu 'chưa xác minh nhóm phiếu'; không suy đoán lịch sử.

## Quy tắc giờ

- Các mốc SQLite sinh từ `CURRENT_TIMESTAMP` là UTC, chỉ **chuyển lúc hiển thị** sang Việt Nam `dd/MM/yyyy HH:mm`.
- SQL Server dùng `SYSDATETIME()`/`CURRENT_TIMESTAMP` theo giờ hệ điều hành của máy SQL. Cấu hình `SQLSERVER_TIMEZONE=Asia/Ho_Chi_Minh` khi xác nhận SQL Server đặt giờ Việt Nam; nếu máy SQL chạy UTC thì đặt `SQLSERVER_TIMEZONE=UTC`. Không cộng giờ trực tiếp trong database. Sai cấu hình sẽ khiến giờ hiển thị sai.
- Nhật ký Python mới sử dụng timestamp UTC có offset; nhật ký cũ từ `datetime.now()` không offset giữ nguyên và hiển thị nhãn **'giờ cũ chưa xác định múi giờ'** để đối soát, không đoán +7 giờ.
- Mốc dữ liệu cũ được import thủ công hoặc SQL Server chưa xác nhận timezone phải đối soát riêng.

## In và quyền

- Admin/nhân viên đăng nhập mở `In hóa đơn` ở chi tiết đơn; hóa đơn đơn hoàn thành, phiếu đơn hàng cho đơn chưa hoàn thành.
- Từng nhóm trả có `In phiếu trả hàng`; từng giao dịch hoàn **thực tế** `cash`/`bank_transfer` có `In xác nhận hoàn tiền`.
- Trang in GET chỉ đọc, in/đóng/quay lại không sửa DB. Khách hàng/ẩn danh không truy cập được các trang in này.
- Khoản hoàn đã trả và chưa trả trên phiếu trả hàng là số tổng **theo đơn**, không được gán cho phiếu.
- Các mẫu in HTML/CSS khổ A4; in bảng dài sẽ lặp thead, tránh cắt dòng. PDF in thực tế cần kiểm tra trình duyệt.

## Không thay đổi nghiệp vụ

Trả hàng sau hoàn thành, nhận bao nhiêu cộng kho bấy nhiêu, tiền hoàn tính tại máy chủ, xác nhận hoàn tiền riêng, ngăn gửi trùng, không tự xóa dữ liệu. Giao dịch demo cũ không tính là tiền đã hoàn thật.
