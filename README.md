# WEBSITE QUẢN LÝ CỬA HÀNG GIÀY DÉP – NHÓM 6
## Bản tích hợp thử nghiệm tuần 2–3 – cập nhật upload ảnh (06/11/2026)

**Trạng thái:** Flask/SQLite DEMO đã thực thi 24 test tự động; SQL Server trên máy nhóm **chưa được kiểm thử thực tế**.
Đây không phải bản đã nghiệm thu 69 nhiệm vụ W3. Không dùng tài khoản demo hoặc SECRET_KEY mặc định khi triển khai Internet.

## 1. Chạy nhanh trên Windows (demo cô lập)

Mở VS Code ở thư mục chứa `run.py` và chạy:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements_sqlite.txt
python run.py
```

Mở `http://127.0.0.1:5000` – sản phẩm W3 ở `/products`; Admin sau đăng nhập ở `/admin/products`.

**Dữ liệu demo:** seed ban đầu có 10 sản phẩm; SQLite tự bổ sung 2 mẫu kiểm thử nên thường hiển thị 12 sản phẩm. Chỉ phục vụ demo, không đại diện dữ liệu SQL Server.

Lần chạy đầu tạo `instance/demo.sqlite3` tự động. Nếu bạn đã có database cũ trong `instance/`, mã nguồn nâng cấp bổ sung `HienThi` và bảng ảnh `SanPhamHinhAnh` cho SQLite mà không xóa dữ liệu sản phẩm cũ.

Tài khoản có sẵn trong seed phục vụ test: xem `tests/test_smoke.py` (không tái sử dụng password này khi phát hành). Để tự bảo mật, không commit database instance hoặc `.env`.

## 2. SQL Server – chưa xác minh trực tiếp

Nền chuẩn được chọn là `database/schema.sql` và `database/seed.sql` (9 bảng của nhóm). **KHÔNG chạy lại `schema.sql` trên CSDL đã có dữ liệu:** script gốc chứa `DROP TABLE`.

Chỉ trên database test đã sao lưu, DBA cần kiểm tra migration `database/migrate_w3_visibility_sqlserver.sql` và `database/migrate_product_images_sqlserver.sql` (đều không DROP) rồi cập nhật schema test trước khi chạy phiên bản mới.

Thiết lập biến môi trường PowerShell (thay bằng cấu hình thật trên máy; không công khai mật khẩu):

```powershell
$env:DB_BACKEND='sqlserver'
$env:SQLSERVER_CONN='DRIVER={ODBC Driver 18 for SQL Server};SERVER=YOUR_SERVER;DATABASE=QuanLyBanHang;Trusted_Connection=yes;TrustServerCertificate=yes;'
$env:SECRET_KEY='REPLACE_WITH_RANDOM_SECRET'
python run.py
```

Cần cài **pyodbc và ODBC Driver** trên Windows, cấu hình SQL Server phải thống nhất tên DB. Mã adapter tuần 3 dùng schema 9 bảng, KHÔNG tương thích tự động với `vs demo` (có thêm cột BrandId, Gender, HinhAnh).

## 3. Tính năng và giới hạn

**Đã kết nối Flask/test được trên SQLite:** trang chủ W2, `/products` với tìm kiếm, lọc loại/thương hiệu/màu/size, khoảng giá, sắp xếp, phân trang, chi tiết; quản trị thêm/sửa/ẩn sản phẩm và thêm biến thể; kiểm quyền Admin; giữ giỏ hàng/đăng nhập nền W2.

**Chưa được nghiệm thu:** SQL Server chạy thật, backend favorite lưu database, giới tính/4 danh mục Brand-Type-Color-Size riêng, transaction đa bước và báo cáo của Nghĩa. Upload ảnh đã được bổ sung và kiểm thử trên SQLite demo; SQL Server cần chạy migration ảnh trước.

**Phạm vi nghiệp vụ:** giao hàng và thanh toán online là yêu cầu mới đã chốt, **chưa triển khai đầy đủ trong W2–W3**. Không dùng giao diện demo để chứng minh đã tích hợp cổng thanh toán.

## 4. Kiểm thử tự động

```powershell
python -m unittest discover -s tests -p "test*.py" -v
```

Log thử nghiệm của bản tích hợp được lưu tại `docs/KET_QUA_TEST_W2_W3.txt`. Mọi bài kiểm thử chạy trên SQLite test tạo trong thư mục tạm, không sửa SQL Server.

## 5. GitHub và provenance

Repository: https://github.com/ducdiem2010-bot/quoan-ly-giay-dep

Chỉ đề xuất push lên branch mới `integration-w2-w3`, tạo Pull Request → review → chạy SQL Server trên máy nhóm → mới cân nhắc merge main. **Không force-push, không xóa các nhánh cũ.**

Danh sách nguồn, tệp ghép và trạng thái xem `docs/TICH_HOP_W3_LUU_Y.md`, `docs/SOURCE_GITHUB.md` và báo cáo Word bàn giao bên ngoài ZIP.


## Bổ sung checkout và trạng thái sản phẩm (sau khi tích hợp W2–W3)

Trạng thái trong trang chi tiết được tính từ tổng tồn kho (`Còn hàng/Hết hàng`).
Tại `/checkout`, người dùng có thể nhập địa chỉ giao hàng hoặc chọn nhận tại cửa hàng,
chọn COD hoặc yêu cầu chuyển khoản chờ xác nhận. Sau khi gửi, đơn **chờ xác nhận**
được lưu trong SQLite demo, chưa thu tiền, chưa tính phí vận chuyển cho giao hàng. (Từ W4-008 đơn **có trừ tồn kho** khi đặt, hoàn lại khi hủy/từ chối/thanh toán thất bại — xem mục W4 cuối file.)
Cổng thanh toán online thật chưa tích hợp.

**SQL Server:** chạy **`database/migration_checkout_sqlserver.sql`** trên database đã được backup
trước khi sử dụng POST `/checkout`. Không chạy `database/schema.sql` lên DB đang có dữ liệu,
vì script lịch sử có các lệnh `DROP TABLE`. Kiểm thử lại với SQL Server thực tế.

Xem `docs/CAP_NHAT_CHECKOUT_TRANG_THAI.md` để biết mọi file sửa và giới hạn.

## Bản cập nhật AI hỗ trợ – 02/11/2026 (chưa nghiệm thu)

Bản ZIP mới bổ sung seed đủ 12 sản phẩm, API biến thể, favorite SQLite/SQLServer migration, sửa biến thể admin và tùy chọn lưu biến thể cùng giao dịch. Chi tiết thay đổi và giới hạn ở `docs/QA_W3/CHANGELOG_AI_W3.md` và `docs/QA_W3/HUONG_DAN_CHAY_TEST.md`.

**Kết quả kiểm tra thực tế trong môi trường tạo ZIP**: `python verify_w3_offline.py` → 8/8 PASS với SQLite memory và Python AST. **Chưa chạy được Flask** do không có thư viện, **chưa chạy SQL Server** do thiếu máy chủ/ODBC/SSMS. Không lấy log 35 PASS SQLite lịch sử để coi là kết quả test mới. Mọi tính năng chưa được review và retest trên máy nhóm không được ghi hoàn thành.


## Cấu trúc mã nguồn đã được sắp xếp (02/11/2026)

Đây là **bản refactor thư mục**, không phải một bản bổ sung chức năng hay nghiệm thu mới.

- `app/routes/public.py`: trang chủ, sản phẩm chi tiết, tài khoản, giỏ, checkout và các route public cũ (`app/routes.py`).
- `app/routes/catalog.py`: danh sách sản phẩm / bộ lọc / phân trang (cũ: `app/catalog_w3.py`).
- `app/routes/admin.py`: quản trị sản phẩm / biến thể (cũ: `app/admin_w3.py`).
- `app/services/checkout.py`: validate và tạo đơn demo (cũ: `app/checkout_service.py`).
- `app/db.py`, `app/data.py`, `app/__init__.py`: giữ vị trí để không thay đổi DB và cách khởi chạy.
- `scripts/verify_w3_offline.py`: script QA độc lập (cũ: `verify_w3_offline.py`).
- `tests/`, `database/`, `app/templates/`, `app/static/`, `docs/`, `instance/`: giữ nguyên vị trí.

**Chạy trên Windows (thư mục chứa `run.py`):**

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

**Kiểm thử:**

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test*.py" -v
.\.venv\Scripts\python.exe scripts/verify_w3_offline.py
```

Phần `.venv` và `__pycache__` **không nằm trong ZIP**; `.venv` trên máy người dùng không bị xóa. Các route Flask giữ cùng URL, tên endpoint và tên Blueprint bằng cách giữ nguyên decorator / tên Blueprint. SQL Server vẫn phải được kiểm chứng trên máy có ODBC/SSMS. Xem `docs/TAI_CAU_TRUC_CODE.md` và Word bàn giao để biết phạm vi kiểm thử.


## Upload ảnh sản phẩm (bổ sung)

- Đăng nhập bằng tài khoản Admin, mở **Quản lý sản phẩm → Thêm sản phẩm** hoặc sửa sản phẩm hiện có.
- Trong mục **Hình ảnh sản phẩm**, chọn tối đa 8 ảnh mỗi lần (JPG/JPEG/PNG/WebP, tối đa 5 MB/ảnh). Ảnh được xem trước trước khi lưu.
- Ảnh đầu tiên của sản phẩm được chọn làm ảnh đại diện. Ở trang sửa có thể đổi ảnh đại diện hoặc xóa ảnh.
- Tệp ảnh nằm tại `app/static/uploads/products/`; tên tệp được sinh ngẫu nhiên. Cơ sở dữ liệu lưu thông tin liên kết trong bảng `SanPhamHinhAnh`.
- SQLite demo tự tạo bảng khi khởi động, không xóa dữ liệu cũ. Nếu dùng SQL Server, chạy `database/migrate_product_images_sqlserver.sql` một lần trước khi khởi động phiên bản mới.
- Ảnh đại diện hiển thị ở danh sách sản phẩm, trang chi tiết và giỏ hàng.


## Bổ sung trang Tài khoản khách hàng

- `/account`: nhập/sửa Họ, Tên, giới tính, ngày sinh, Tỉnh/Thành phố (34 đơn vị), Phường/Xã, số nhà-đường, số điện thoại, email. `/account/orders`: lịch sử đơn của khách.
- `/checkout` tự điền sẵn từ hồ sơ, khách vẫn sửa được. Có ô "Lưu làm thông tin mặc định" (tự tick ở lần mua đầu); không tick thì hồ sơ giữ nguyên.
- SQLite tự thêm cột mới vào `NguoiDung`. **SQL Server:** chạy `database/migrate_account_profile_sqlserver.sql` trên DB đã backup.
- Phường/Xã hiện là ô nhập tay (chưa có danh sách phường/xã đầy đủ). Test: `tests/test_account.py`.


## Cập nhật W4 (chưa nghiệm thu trên SQL Server)
- **W4-007** `database/migration_w4_giao_dich_sqlserver.sql` (+ `rollback_...`): thêm cột giao nhận/thanh toán/xác nhận/giao hàng/hủy/`DaTruKho` cho `DonHang`, bảng `GiaoDichThanhToan`, `HoaDon`, `NhatKyMigration`; CHECK/FK/UNIQUE; chuyển đổi đơn cũ không mất dữ liệu. Data Dictionary: `docs/data_dictionary.md` (mục W4).
- **W4-008** `app/services/order_inventory.py`: trừ/hoàn tồn trong transaction, rollback khi thiếu tồn, hủy/từ chối/thanh toán thất bại hoàn đúng 1 lần. Test: `tests/test_inventory_w4.py` (SQLite).
- **Seed** `database/seed_products_w4.sql` (16 SP có tình huống biên) và tuỳ chọn `seed_orders_w4.sql`.
- **Tái lập DB**: `docs/DB_repro_steps.md`. Log test SQLite: `docs/KET_QUA_TEST_W4.txt`.
- Chưa có giao diện hủy/xác nhận đơn; các hàm `confirm_order/reject_order/cancel_order/mark_paid/mark_payment_failed` mới chỉ gọi được từ code/test.
