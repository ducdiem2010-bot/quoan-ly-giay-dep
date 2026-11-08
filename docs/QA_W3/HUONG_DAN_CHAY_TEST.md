# HƯỚNG DẪN CHẠY & KIỂM THỬ TUẦN 3 – NHÓM 6

**Ngày lập:** 02/11/2026. **Trạng thái:** Bản sửa do AI hỗ trợ, chưa nghiệm thu trên Flask/SQL Server thật.

## 1. Sản phẩm bàn giao

- ZIP giữ cấu trúc `Nhom6_WebGiayDep_TichHop_W2_W3`, `run.py` ở thư mục gốc.
- `scripts/verify_w3_offline.py` kiểm tra được SQLite và cú pháp Python **không cần Flask**; log `docs/QA_W3/offline_test_log.txt` ghi 8/8 PASS ở môi trường lần này.
- `tests/test_w3_extensions.py` gồm các test Flask mới, chưa chạy được ở môi trường xử lý do không có Flask. Không mặc định PASS.
- `docs/QA_W3/CHANGELOG_AI_W3.md` ghi rõ sửa file nào, còn thiếu gì, người phụ trách kỹ thuật cần review.

## 2. Cách chạy trên Windows với VS Code

Mở Terminal tại thư mục có `run.py`, chạy:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/verify_w3_offline.py
python -m unittest discover -s tests -p "test*.py" -v
python run.py
```

Truy cập `http://127.0.0.1:5000/`, danh sách sản phẩm `/products`, admin `/admin/products` (cần đăng nhập quyền Admin). Chỉ thử trên dữ liệu mẫu, không đưa tài khoản demo hoặc SECRET_KEY mẫu ra Internet.

Nếu không kích hoạt được virtual environment, có thể chạy `py -m pip install -r requirements.txt`, sau đó `py run.py` bằng cùng phiên bản Python.

## 3. Thử API, favorite và admin variant

1. Truy cập `/api/products/1/variants?color=%C4%90en&size=39`; dự kiến nhận JSON với biến thể ID/size/màu/tồn.
2. Truy cập `/api/products/1/variants?color=%C4%90en&size=40`; dự kiến không có tổ hợp (không được gộp hai biến thể khác hàng).
3. Đăng nhập tài khoản Customer demo → mở `/product/1` → nhấn Favorite → kiểm bảng `YeuThich`; nhấn lần nữa để bỏ. Seller không được thực hiện thao tác này.
4. Đăng nhập Admin → `/admin/products/1/variants`, sửa size/màu/tồn trong một hàng → Lưu. Kiểm database trước/sau, thử số âm và tổ hợp trùng.
5. Thêm sản phẩm mới ở `/admin/products/new` kèm biến thể đầu tiên: kiểm INSERT cả hai thành công hoặc rollback toàn bộ nếu biến thể sai.
6. Tạo dữ liệu test/PR để Điểm thực thi Test Case, chụp browser/Network/SSMS/Terminal.

## 4. SQL Server thật – CHƯA KIỂM CHỨNG

**Không chạy `database/schema.sql` có `DROP TABLE` trên database có dữ liệu.** Minh cần backup database test trước, rà schema và thứ tự migration. Sau khi dùng dữ liệu demo trên DB thử nghiệm: 

- `database/migrate_w3_visibility_sqlserver.sql`: bổ sung `SanPham.HienThi` và áp mẫu ẩn demo.
- `database/migrate_w3_favorites_sqlserver.sql`: bổ sung `YeuThich` + khóa ngoại. Cần review đường đi cascade trước khi áp dụng production.
- `database/seed.sql`: cho database test trống, có 12 sản phẩm; không chạy lại trên DB đã có seed trừ khi có kế hoạch tránh trùng.

Kết nối PowerShell, **điền tên server thực của nhóm**, không chia sẻ mật khẩu:

```powershell
$env:DB_BACKEND='sqlserver'
$env:SQLSERVER_CONN='DRIVER={ODBC Driver 18 for SQL Server};SERVER=YOUR_SERVER;DATABASE=QuanLyBanHang;Trusted_Connection=yes;TrustServerCertificate=yes;'
$env:SECRET_KEY='REPLACE_WITH_RANDOM_SECRET'
python run.py
```

Trong SSMS đối chiếu `SELECT COUNT(*) FROM dbo.SanPham;`, kiểm `HienThi`, `BienTheSanPham`, `YeuThich`, các ràng buộc và dữ liệu trước/sau khi thao tác. Các test từ SQLite **không thay thế** kết quả SQL Server.

## 5. Minh chứng và nghiệm thu

- Mỗi Task ID từ `W3-001` đến `W3-069`: file/PR, SHA, dữ liệu đầu vào, Expected, Actual, ảnh/log, trạng thái PASS/FAIL/BLOCKED/NOT RUN.
- Lưu `TC-W3-xxx-01`, `W3-BUG-xxx`, retest sau sửa; không ghi PASS chỉ vì file có mặt.
- Xem `Nhom6_Test_Plan_Va_Nghiem_Thu_Tuan3.xlsx` (10 sheet), `Nhom6_Bien_Ban_Kiem_Thu_Nghiem_Thu_Tuan3.docx` và `Nhom6_Doi_Chieu_69_Task_Truoc_Sau.xlsx`.
- Điểm chỉ QA/Reviewer; mọi patch do AI sinh phải được thành viên tương ứng review, xác nhận, tạo PR trước khi nhập code nhóm.

## 6. Phần chưa thể tuyên bố hoàn thành

1. SQL Server chạy thật trên máy nhóm (cần Minh).
2. Quản trị đầy đủ Brand/Type/Color/Size theo DoD: schema gốc chưa có 4 bảng độc lập (cần Minh+Nghĩa chốt thiết kế).
3. Upload an toàn và gallery nhiều ảnh (cần Khải); không coi 3 ảnh SVG là upload.
4. Flask/browser regression, API variant, favorite end-to-end, admin transaction và responsive (cần toàn nhóm + Điểm thực thi).
5. Hồ sơ nghiệm thu W3-069 có bằng chứng/5 thành viên xác nhận (cần Điểm chủ trì).

**Kết luận:** 8/8 test offline mới đã đạt, Flask/SQL Server còn BLOCKED/NOT RUN. Chưa đủ điều kiện khẳng định tuần 3 nghiệm thu hoàn tất.
