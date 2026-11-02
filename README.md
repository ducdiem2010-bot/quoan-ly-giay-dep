Bộ nối frontend–backend W4: [hướng dẫn Nghĩa ghép](docs/TUAN_W4_BACKEND_HANDOFF.md).

> Bổ sung frontend tuần 4 của Tuấn: đọc [README_W4_TUAN.md](README_W4_TUAN.md) trước. Code giao diện, test và minh chứng mới đã được thêm; backend theo dõi/hủy đơn, payment và tồn kho còn phụ thuộc. Phần bên dưới giữ lại thông tin bàn giao lịch sử W2–W3.

# WEBSITE QUẢN LÝ CỬA HÀNG GIÀY DÉP – NHÓM 6
## Bản tích hợp thử nghiệm tuần 2–3 (22/10/2026)

**Trạng thái:** Flask/SQLite DEMO đã thực thi 24 test tự động; SQL Server trên máy nhóm **chưa được kiểm thử thực tế**.
Đây không phải bản đã nghiệm thu 69 nhiệm vụ W3. Không dùng tài khoản demo hoặc SECRET_KEY mặc định khi triển khai Internet.

## 1. Chạy nhanh trên Windows (demo cô lập)

Mở VS Code ở thư mục chứa `run.py` và chạy:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run.py
```

Mở `http://127.0.0.1:5000` – sản phẩm W3 ở `/products`; Admin sau đăng nhập ở `/admin/products`.

**Dữ liệu demo:** schema và seed có 10 sản phẩm. Chỉ phục vụ kiểm thử ban đầu, **chưa đạt W3-006** (đòi >=12 SP trên SQL Server, còn mẫu ẩn/hết tồn và màu/size chéo).

Lần chạy đầu tạo `instance/demo.sqlite3` tự động. Nếu bạn đã có database cũ trong `instance/`, mã nguồn thực hiện nâng cấp nhẹ `HienThi` cho SQLite mà không xóa bảng.

Tài khoản có sẵn trong seed phục vụ test: xem `tests/test_smoke.py` (không tái sử dụng password này khi phát hành). Để tự bảo mật, không commit database instance hoặc `.env`.

## 2. SQL Server – chưa xác minh trực tiếp

Nền chuẩn được chọn là `database/schema.sql` và `database/seed.sql` (9 bảng của nhóm). **KHÔNG chạy lại `schema.sql` trên CSDL đã có dữ liệu:** script gốc chứa `DROP TABLE`.

Chỉ trên database test đã sao lưu, DBA/Minh cần kiểm tra migration `database/migrate_w3_visibility_sqlserver.sql` (không DROP) rồi tự tạo/cập nhật schema test và dữ liệu W3 theo kế hoạch.

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

**Chưa được nghiệm thu:** SQL Server chạy thật, seed W3 >=12, backend favorite lưu database, giới tính/4 danh mục Brand-Type-Color-Size riêng, quản lý ảnh upload, transaction đa bước và báo cáo của Nghĩa.

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
được lưu trong SQLite demo, chưa trừ kho, chưa thu tiền, chưa tính phí vận chuyển cho giao hàng.
Cổng thanh toán online thật chưa tích hợp.

**SQL Server:** chạy **`database/migration_checkout_sqlserver.sql`** trên database đã được backup
trước khi sử dụng POST `/checkout`. Không chạy `database/schema.sql` lên DB đang có dữ liệu,
vì script lịch sử có các lệnh `DROP TABLE`. Kiểm thử lại với SQL Server thực tế.

Xem `docs/CAP_NHAT_CHECKOUT_TRANG_THAI.md` để biết mọi file sửa và giới hạn.
