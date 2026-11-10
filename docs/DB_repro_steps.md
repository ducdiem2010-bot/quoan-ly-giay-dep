# DB_repro_steps — Tái lập SQL Server trên máy thử sạch

> Trạng thái: hướng dẫn viết cho nhóm; **chưa được chạy trên SQL Server thật** (môi trường tạo file không có SQL Server). Người chạy phải điền log/ảnh vào mục 7.

## 0. Nguyên tắc an toàn
- Chỉ chạy trên **database TEST** mới tạo. Không script nào ở đây DROP dữ liệu thật, trừ `database/schema.sql` (lịch sử, có `DROP TABLE`) — **chỉ dùng cho DB test rỗng vừa tạo**.
- Mọi file `.sql` mới lưu UTF-8 có BOM. Nếu tiếng Việt bị lỗi font: SSMS → File → Open → Open With… → UTF-8.
- Không ghi mật khẩu vào file/commit: dùng Windows Authentication (`Trusted_Connection=yes`) hoặc biến môi trường.

## 1. Yêu cầu
SQL Server (Express/Developer) + SSMS; ODBC Driver 18 for SQL Server; Python 3.10+.

## 2. Tạo database test
SSMS → New Query: `CREATE DATABASE QuanLyBanHang_TEST COLLATE Vietnamese_100_CI_AS;` rồi chọn `QuanLyBanHang_TEST` ở ô *Available Databases*. (`schema.sql` có dòng `USE QuanLyBanHang`; với DB test hãy mở file, đổi tên DB trong 3 dòng đầu thành `QuanLyBanHang_TEST`.)

## 3. Chạy theo ĐÚNG thứ tự (mỗi file: chọn DB test → Execute → lưu Messages/Results)
1. `database/schema.sql`  2. `database/seed.sql`  3. `migrate_w3_visibility_sqlserver.sql`  4. `migrate_product_images_sqlserver.sql`  5. `migrate_w3_favorites_sqlserver.sql`  6. `migrate_account_profile_sqlserver.sql`  7. `migration_checkout_sqlserver.sql`
8. **Trước bước 9: sao lưu** `BACKUP DATABASE [QuanLyBanHang_TEST] TO DISK=N'C:\Backup\TEST_truoc_W4.bak' WITH COPY_ONLY, INIT, CHECKSUM;`
9. `migration_w4_giao_dich_sqlserver.sql` (W4-007)  10. `seed_products_w4.sql`  11. (tuỳ chọn) `seed_orders_w4.sql`
Chạy lại bước 9–11 lần 2 phải **không lỗi và không thêm dữ liệu** (idempotent) — ghi lại.

## 4. Smoke query (chụp kết quả)
```sql
SELECT COUNT(*) AS SP, SUM(CASE WHEN HienThi=1 THEN 1 ELSE 0 END) AS Hien FROM dbo.SanPham;   -- 28 / 26 nếu chạy seed_products_w4 trên seed.sql gốc (12 SP cũ, 1 ẩn + 16 SP mới, 1 ẩn)
SELECT TOP 5 MaSanPham, TenSanPham, GiaBan FROM dbo.SanPham ORDER BY MaSanPham DESC;
SELECT MaDonHang, TrangThai, TrangThaiXacNhan, TrangThaiGiaoHang, DaHuy, DaTruKho, TongTien, TongThanhToan FROM dbo.DonHang;
SELECT * FROM dbo.NhatKyMigration ORDER BY MaNhatKy;
```
Khối kiểm tra cuối mỗi file migration/seed phải cho kết quả "kỳ vọng" ghi trong file; `K2` không có dòng `THIEU`; `DBCC CHECKCONSTRAINTS` trả 0 dòng.

## 5. Chạy ứng dụng với DB test (không lộ mật khẩu)
```powershell
py -m venv .venv ; .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:DB_BACKEND='sqlserver'
$env:SQLSERVER_CONN='DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost\SQLEXPRESS;DATABASE=QuanLyBanHang_TEST;Trusted_Connection=yes;TrustServerCertificate=yes;'
$env:SECRET_KEY='<chuoi-ngau-nhien-dai>'
python run.py
```
(Hoặc copy `.env.example` → `.env` cục bộ; `.env` đã nằm trong `.gitignore`.) Kiểm tra: `/products` hiện 26 sản phẩm hiển thị (không có "New Balance 574" ẩn); đặt 1 đơn thử → `SoLuongTon` giảm, `DonHang.DaTruKho=1`.

## 6. Rollback
Đầy đủ: `RESTORE DATABASE [QuanLyBanHang_TEST] FROM DISK=N'C:\Backup\TEST_truoc_W4.bak' WITH REPLACE;` · Chỉ cấu trúc: `rollback_migration_w4_giao_dich_sqlserver.sql`.

## 7. Ghi lỗi môi trường & bằng chứng (điền khi chạy)
| Bước | Kết quả (OK/LỖI) | Thông báo lỗi / cách xử lý | Ảnh/log |
| --- | --- | --- | --- |
| … | | | |
Lỗi thường gặp: `Invalid column name HienThi` (thiếu bước 3) · `Login failed` (sai instance/Windows Auth) · `Data source name not found` (thiếu ODBC Driver 18) · tiếng Việt thành `?` (mở file sai encoding) · `SET QUOTED_IDENTIFIER` (chạy bằng sqlcmd thì thêm `-I`).
