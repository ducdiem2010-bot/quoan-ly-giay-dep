# NHÓM 6 — WEBSITE QUẢN LÝ CỬA HÀNG GIÀY DÉP

**Bản ghép mã nguồn cho nhiệm vụ Tuần 2 (T2–T6)** | Ngày ghép: 12/10/2026

## 1. Cách chạy nhanh bằng VS Code (Windows)
1. Giải nén toàn bộ ZIP, mở **thư mục `Nhom6_Tuan2_DaGhep`**, không mở riêng từng thư mục con.
2. Mở VS Code > Terminal > New Terminal; trong terminal phải đang đứng ở thư mục chứa `run.py`.
3. Chạy các lệnh:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run.py
```

Nếu Windows không cho activate: `& .\.venv\Scripts\python.exe -m pip install -r requirements.txt` rồi `& .\.venv\Scripts\python.exe run.py`.

4. Mở **http://127.0.0.1:5000/** trên trình duyệt của máy đang chạy.
5. **Không chạy `app.py` trong `tai_lieu_nguon/`**. Tệp chạy chính là `run.py`.

Mặc định bản này chạy **SQLite demo**, tự khởi tạo `instance/demo.sqlite3` với 9 bảng, **10 sản phẩm**, 3 danh mục, 3 tài khoản mẫu. SQLite giúp các thành viên demo khi máy chưa có SQL Server.

## 2. Chạy với Microsoft SQL Server (hướng nhóm đã chọn)

- Cài SQL Server và SSMS, ODBC Driver 17/18, gói Python `pyodbc` (`python -m pip install pyodbc`).
- Mở `database/schema.sql` bằng SSMS, chạy toàn bộ; sau đó chạy `database/seed.sql`. **Đây là T-SQL, không chạy bằng SQLite/MySQL.** Script schema sẽ xóa/khởi tạo lại bảng — chỉ dùng khi thiết lập dữ liệu demo, không chạy trên hệ thống có dữ liệu quan trọng.
- Trong PowerShell terminal ở thư mục dự án:

```powershell
$env:DB_BACKEND="sqlserver"
$env:SQLSERVER_CONN="DRIVER={ODBC Driver 17 for SQL Server};SERVER=.\SQLEXPRESS;DATABASE=QuanLyBanHang;Trusted_Connection=yes;"
$env:SECRET_KEY="thay_bang_chuoi_ngau_nhien_du_dai_truoc_khi_chay"
python run.py
```

- Chỉnh tên SERVER theo tên máy SQL Server. **Chế độ SQL Server chưa được kết nối/kiểm thử thực tế trong môi trường bàn giao**, nên phải kiểm tra SSMS trên máy nhóm trước khi nghiệm thu cuối.

## 3. Tài khoản demo (thay trước khi triển khai)

| Loại | Email | Mật khẩu |
| --- | --- | --- |
| Quản lý (Admin) | `admin@shop.vn` | `Demo@12345` |
| Nhân viên (Seller) | `minh@shop.vn` | `Demo@12345` |
| Khách hàng (Customer) | `khach@shop.vn` | `Demo@12345` |

Mật khẩu được lưu theo dạng hash PBKDF2, nhưng vì tài khoản demo công khai trong README nên **không dùng cho hệ thống thật**. Đổi SECRET_KEY và mật khẩu trước khi đưa lên Internet.

## 4. Cấu trúc mã nguồn

```text
Nhom6_Tuan2_DaGhep/
├─ run.py                    # LỆNH CHẠY DUY NHẤT
├─ requirements.txt
├─ app/
│  ├─ __init__.py            # Flask application factory
│  ├─ routes.py              # Trang chủ, SP, danh mục, giỏ, login, admin, lỗi
│  ├─ db.py                  # Kết nối DB, quản lý lỗi, query
│  ├─ data.py                # JOIN danh mục và biến thể sản phẩm
│  ├─ templates/             # base.html và các template Jinja2
│  │  ├─ admin_base.html
│  │  └─ admin/
│  └─ static/css|js|images/ # CSS responsive, JS, ảnh SVG nội bộ
├─ database/
│  ├─ schema.sql             # SQL Server (đích của nhóm)
│  ├─ seed.sql
│  ├─ schema_sqlite.sql      # Demo kiểm thử không cần SQL Server
│  └─ seed_sqlite.sql
├─ tests/test_smoke.py       # Test hệ thống
├─ docs/                     # Ma trận nghiệm thu, ERD, Wireframe, Word
└─ tai_lieu_nguon/          # Mã nguồn thành viên để đối chiếu, KHÔNG chạy
```

## 5. Danh sách URL cần bấm khi demo

| URL | Công dụng |
| --- | --- |
| `/` | Trang chủ đọc sản phẩm từ DB và tìm kiếm `?q=Nike` |
| `/category/1`, `/category/2`, `/category/3` | Lọc theo danh mục |
| `/product/1` | Chi tiết, chọn size/màu/số lượng, thêm giỏ |
| `/product/99999` | Trang lỗi 404 thân thiện |
| `/cart` | Xem giỏ lưu ở session, xóa hàng |
| `/checkout` | **Chỉ giao diện mẫu Tuần 2; chưa đặt đơn thật** |
| `/login`, `/register` | Đăng nhập/đăng ký |
| `/admin` | Bắt buộc đăng nhập Admin |
| `/admin/product/add` | **Form thêm sản phẩm; chỉ kiểm tra input, chưa ghi DB** |

## 6. Chạy kiểm thử tự động

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

Trong môi trường ghép đã chạy thành công **10/10 kiểm thử backend trên SQLite demo** (xem `docs/BAO_CAO_SMOKE_TEST.md`). Phạm vi chưa xác minh: SQL Server thật, chạy trên 5 máy thành viên và kiểm tra scroll ngang trực tiếp bằng browser ở 375px/768px.

## 7. Điểm khác với bảng Tuần 2

- Bảng ghi “8 bảng”, nhưng ERD/schema thực có **9 bảng** vì bổ sung bảng `BienTheSanPham` quản lý size/màu/tồn kho chuẩn hơn. Chưa thể gọi là đạt **đúng 8 bảng**; giảng viên cần đồng ý thay đổi.
- Source `admin html.htm` chỉ là bản HTML trang GitHub đã tải về, không phải `admin_base` của Khải. Bộ Admin mới được dựng lại để ghép đúng.
- Không giao hàng, không thanh toán online, không có chi nhánh. Các ví dụ trong source SQL gốc liên quan `DiaChiGiaoHang` hoặc `Đang giao` đã bị loại khỏi **bản schema ghép**.
- ERD/Wireframe `.drawio` là bản **tái dựng**, phải được Minh, Nghĩa, Tuấn, Khải xác nhận trước khi báo là bản chính thức.

**Bắt buộc xem:** `docs/BANG_DOI_CHIEU_NGHIEM_THU.xlsx` và `docs/CON_VIEC_CAN_XAC_NHAN.md` trước khi nộp.
