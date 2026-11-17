# Hướng dẫn Chạy và Kiểm Thử Hệ Thống - Nhóm 6 (Bản Hoàn Thiện W12)

Dự án Website Quản lý Cửa hàng Giày dép (Shoes Store) kết nối backend Flask, cơ sở dữ liệu (SQLite cho demo/test nhanh, SQL Server cho môi trường triển khai thực tế) và frontend HTML5/CSS3/JS thuần tiếng Việt.

---

## 1. Hướng Dẫn Khởi Chạy Ứng Dụng

Khởi chạy bằng lệnh chính thống:
```powershell
python run.py
```
Mặc định ứng dụng sẽ lắng nghe tại: `http://127.0.0.1:5000/`.

### 1.1. Chạy với SQLite (Mặc định cho Test / Demo)
```powershell
$env:DB_BACKEND = "sqlite"
python run.py
```
- Cơ sở dữ liệu SQLite tự động tạo tại `instance/demo.sqlite3` với đầy đủ 15 bảng và dữ liệu mẫu nếu chưa có.
- Tự động thực hiện nâng cấp cấu trúc bảng an toàn (additive migration), không làm mất dữ liệu người dùng.

### 1.2. Chạy với SQL Server
Khi triển khai trên SQL Server, thiết lập biến môi trường kết nối:
```powershell
$env:DB_BACKEND = "sqlserver"
# Ví dụ kết nối với Windows Authentication (ODBC Driver 18 hoặc 17):
$env:SQLSERVER_CONN = "Driver={ODBC Driver 18 for SQL Server};Server=localhost\SQLEXPRESS;Database=QuanLyBanHang;Trusted_Connection=yes;TrustServerCertificate=yes;"
python run.py
```

---

## 2. Các Script SQL Server và Thứ Tự Chạy

Các script nằm trong thư mục `database/`:

1. **Khởi tạo Database mới hoàn toàn (Fresh Installation)**:
   - File: `database/init_database_sqlserver.sql`
   - Mục đích: Tạo mới database `QuanLyBanHang`, 14 bảng chuẩn, các khóa chính/ngoại, chỉ mục, trigger tự động tính tổng tiền và dữ liệu mẫu (Admin, Seller, Customer, Danh mục, Thương hiệu, Màu, Size, Sản phẩm, Biến thể).
   - Thứ tự: Chạy script này trên SQL Server Management Studio (SSMS) hoặc qua `sqlcmd` khi bắt đầu triển khai trên server mới.

2. **Nâng cấp Database cũ giữ nguyên dữ liệu (Safe Idempotent Migration)**:
   - File: `database/upgrade_existing_sqlserver.sql`
   - Mục đích: Chạy lại an toàn nhiều lần trên database đã có dữ liệu từ các tuần trước.
   - Nguyên tắc: **Không chạy `DROP TABLE`**, không xóa hay ghi đè dữ liệu. Tự động kiểm tra `COL_LENGTH` và `OBJECT_ID` trước khi thêm cột mới (`HienThi`, `MaThuongHieu`, `Ho`, `Ten`, `GioiTinh`, `NgaySinh`, `NguoiKhoa`, `ThoiGianKhoa`, `MaNguoiXuLy`...) và tạo mới các bảng bổ trợ (`ThuongHieu`, `MauSac`, `KichThuoc`, `ThongTinGiaoDich`, `SanPhamHinhAnh`, `YeuThich`).
   - Tự động trích xuất và đồng bộ dữ liệu vào bảng danh mục phụ nếu bảng đang trống.

---

## 3. Ma Trận Phân Quyền (Role-Based Access Control)

Hệ thống phân quyền nghiêm ngặt tại Backend (decorator `@admin`, `@admin_only`, `@staff_or_admin`, `@login_required` và session security guard):

| Chức năng / Đường dẫn | Khách vãng lai (Guest) | Khách hàng (Customer) | Nhân viên (Seller) | Quản trị viên (Admin) |
|---|:---:|:---:|:---:|:---:|
| Trang chủ, Danh mục, Chi tiết SP, Tìm kiếm | ✓ | ✓ | ✓ | ✓ |
| Giỏ hàng, Sửa số lượng, Xóa món trong giỏ | ✓ | ✓ | ✓ | ✓ |
| Đặt hàng (Checkout) | Chuyển hướng Login (hoặc guest nếu tắt bắt buộc) | ✓ | ✓ | ✓ |
| Xem đơn của chính mình (`/account/orders`) | ✗ (Redirect Login) | ✓ | ✓ | ✓ |
| Hủy đơn đang chờ xác nhận của mình | ✗ | ✓ | ✗ (Xử lý theo quyền nv) | ✓ |
| Xem hồ sơ & Sửa thông tin cá nhân (`/account`) | ✗ (Redirect Login) | ✓ | ✓ | ✓ |
| Khu vực Nhân viên (`/staff`, `/staff/orders`) | ✗ (403) | ✗ (403) | ✓ | ✓ |
| Xem chi tiết & Xử lý đơn (Xác nhận, Hoàn thành, Hủy) | ✗ (403) | ✗ (403) | ✓ | ✓ |
| Ghi nhận thu tiền đơn hàng (`/orders/<id>/pay`) | ✗ (403) | ✗ (403) | ✓ | ✓ |
| Quản lý nhân viên (`/admin/staff/*`) | ✗ (403) | ✗ (403) | ✗ (403) | ✓ |
| Quản lý khách hàng (`/admin/customers/*`) | ✗ (403) | ✗ (403) | ✗ (403) | ✓ |
| Khóa / Mở khóa tài khoản | ✗ (403) | ✗ (403) | ✗ (403) | ✓ |
| Quản lý sản phẩm, thêm/sửa/ẩn/xóa an toàn | ✗ (403) | ✗ (403) | ✗ (403) | ✓ |
| Quản lý Loại, Thương hiệu, Màu sắc, Kích thước | ✗ (403) | ✗ (403) | ✗ (403) | ✓ |
| Xem tổng quan Dashboard KPI | ✗ (403) | ✗ (403) | ✗ (403) | ✓ |

---

## 4. Quy Tắc Quản Lý Tồn Kho, Trạng Thái Đơn & Thanh Toán

1. **Lúc tạo đơn hàng (Checkout)**:
   - Đơn hàng được tạo ở trạng thái `Chờ xác nhận`.
   - **Chưa trừ tồn kho ngay** để tránh giữ hàng ảo khi khách chưa chắc chắn mua hoặc hủy sớm.
   - Giá bán được truy vấn trực tiếp từ bảng `SanPham` trong cơ sở dữ liệu, không tin tưởng giá gửi từ trình duyệt.
   - Chống tạo đơn trùng (Idempotency): Sử dụng `checkout_token` được sinh ngẫu nhiên mỗi phiên checkout, ngăn chặn submit nhiều lần khi người dùng bấm liên tục.

2. **Lúc xác nhận đơn hàng (`POST /orders/<id>/confirm`)**:
   - Thao tác thực hiện bởi Nhân viên (Seller) hoặc Quản trị viên (Admin).
   - Kiểm tra tồn kho thực tế của từng biến thể trong **Transaction có khóa dòng** (`BEGIN IMMEDIATE` trên SQLite, `WITH (UPDLOCK, HOLDLOCK)` trên SQL Server).
   - Nếu đủ hàng: Trừ số lượng tương ứng trong `BienTheSanPham.SoLuongTon`, cập nhật `DonHang.TrangThai = 'Đã xác nhận'`, ghi nhận `MaNguoiXuLy` và `ThoiGianXuLy`.
   - Nếu bất kỳ mặt hàng nào không đủ tồn kho: Toàn bộ thao tác bị hủy bỏ và rollback, thông báo rõ ràng mặt hàng thiếu hàng cho nhân viên.

3. **Lúc hủy đơn hàng (`POST /orders/<id>/cancel` hoặc khách hủy ở `/account/orders/<id>/cancel`)**:
   - Khách hàng chỉ được hủy đơn khi đơn còn ở trạng thái `Chờ xác nhận` và thuộc quyền sở hữu của chính mình.
   - **Quy tắc hoàn kho**:
     * Nếu đơn đang `Chờ xác nhận`: Chỉ đổi trạng thái sang `Đã hủy`, **không hoàn kho** (vì chưa từng trừ kho).
     * Nếu đơn đang `Đã xác nhận`: Hệ thống thực hiện transaction **cộng hoàn trả chính xác số lượng từng sản phẩm vào `SoLuongTon`**, sau đó mới đổi trạng thái sang `Đã hủy`.
     * Đơn đã `Hoàn thành` không được phép hủy để tránh sai lệch kế toán và kho.

4. **Ghi nhận thanh toán (`POST /orders/<id>/pay`)**:
   - Chỉ được ghi nhận khi trạng thái thanh toán là `Chưa thanh toán` (chống ghi nhận trùng 2 lần).
   - Cập nhật `ThongTinGiaoDich.TrangThaiThanhToan = 'Đã thanh toán'`, lưu `NguoiThuTien` và `ThoiGianThanhToan`.
   - Đơn chưa thanh toán không bao giờ được tính vào doanh thu thực nhận trên Dashboard KPI.

5. **Xóa an toàn Sản phẩm và Biến thể**:
   - Sản phẩm hoặc biến thể **đã có lịch sử đơn hàng** (`ChiTietDonHang`): Hệ thống từ chối xóa cứng để bảo vệ tính toàn vẹn của dữ liệu và báo cáo tài chính; tự động chuyển sang trạng thái Ẩn (`HienThi = 0`) hoặc đặt tồn kho về 0.
   - Sản phẩm hoặc biến thể **chưa từng phát sinh giao dịch**: Cho phép xóa hoàn toàn khỏi cơ sở dữ liệu và dọn dẹp file ảnh trên đĩa.

---

## 5. Bằng Chứng Kiểm Thử Tự Động

Chạy toàn bộ 154 test cases kiểm thử hồi quy và tích hợp:
```powershell
python -m unittest discover tests -v
```
**Kết quả kiểm thử thực tế**:
```
Ran 154 tests in 61.192s
OK (154/154 tests PASS - 100%)
```

Các bộ test bao phủ toàn diện:
- `tests/test_final_integration.py`: 9 ca kiểm thử tích hợp chuyên sâu cho Sections B, C, D, E, F, G (tạo nhân viên rồi đăng nhập thật, phân quyền 3 vai trò, khóa phiên cũ, CRUD danh mục/thương hiệu/màu/size, xóa an toàn, trừ/hoàn kho, concurrency 2 người mua món cuối, concurrency 2 người xử lý cùng 1 đơn).
- `tests/test_smoke.py`: 10 ca kiểm thử smoke tuần 2 & tuần 3.
- `tests/test_integration_w3.py`: 14 ca kiểm thử catalog, variants, paging, sorting.
- `tests/test_w12_fix_log.py`: 14 ca kiểm thử giao diện và phân quyền nhân viên/khách hàng W12.
- `tests/test_new_arrivals.py` & `tests/test_best_sellers.py`: 48 ca kiểm thử thuật toán sản phẩm mới và bán chạy.
- `tests/test_account.py`, `tests/test_buy_now.py`, `tests/test_w10_dashboard_hot_stock.py`, `tests/test_w11_upgrade.py`: 59 ca kiểm thử giao diện giỏ hàng, đặt hàng nhanh, KPI và trang khách hàng.

---

## 6. Thông Tin Môi Trường SQL Server & Hướng Dẫn Khi Cần Nối Database Thật

Hệ thống đã chuẩn hóa 100% cú pháp truy vấn tham số hóa `?` và migration cho SQL Server. Khi triển khai trên máy chủ SQL Server thực tế:
1. **ODBC Driver**: Máy chủ Windows đã có sẵn `ODBC Driver 18 for SQL Server` và `ODBC Driver 17 for SQL Server`.
2. **Thư viện Python**: Cần cài đặt `pyodbc` vào môi trường Python:
   ```powershell
   pip install pyodbc
   ```
3. **Chuỗi kết nối**: Cung cấp tên Server / Instance vào biến môi trường:
   - Nếu dùng SQL Server Express cục bộ: `Server=localhost\SQLEXPRESS;Database=QuanLyBanHang;Trusted_Connection=yes;TrustServerCertificate=yes;`
   - Nếu dùng SQL Authentication: `Server=IP_OR_HOST,1433;Database=QuanLyBanHang;UID=sa;PWD=YourStrongPassword;Encrypt=yes;TrustServerCertificate=yes;`
