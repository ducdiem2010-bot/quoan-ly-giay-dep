> CẢNH BÁO PHẠM VI: Đây là tài liệu lịch sử W2; mọi khẳng định không giao hàng/không thanh toán online đã bị thay thế bằng phạm vi mới CÓ giao hàng và thanh toán online. Các chức năng chưa triển khai vẫn phải ghi chưa hoàn thành.

# TỪ ĐIỂN DỮ LIỆU — NHÓM 6 (TUẦN 2)

Bản dùng chung cho SQL Server và bản SQLite demo. **Không trộn tên cột tiếng Anh/Việt hoặc tên viết tắt**: dùng chính xác `MaSanPham`, `MaDanhMuc`, `MaBienThe`, ... khi viết query.

## Cấu trúc 9 bảng

| Bảng | Khóa chính | Khóa ngoại | Thuộc tính chính & kiểu SQL Server | Ý nghĩa/ràng buộc |
| --- | --- | --- | --- | --- |
| `VaiTro` | `MaVaiTro` INT IDENTITY | — | `TenVaiTro` NVARCHAR(50), `MoTa` NVARCHAR(255) | Tên vai trò UNIQUE |
| `NguoiDung` | `MaNguoiDung` INT IDENTITY | `MaVaiTro` → VaiTro | `HoVaTen` NVARCHAR(100), `Email` NVARCHAR(150), `MatKhauHash` NVARCHAR(255), `SoDienThoai` VARCHAR(15), `DiaChi` NVARCHAR(255), `TrangThai` BIT, `NgayTao` DATETIME2 | Email UNIQUE, mật khẩu chỉ lưu hash, 1 người thuộc 1 vai trò |
| `DanhMuc` | `MaDanhMuc` INT IDENTITY | — | `TenDanhMuc` NVARCHAR(100), `MoTa` NVARCHAR(500) | Tên danh mục UNIQUE |
| `SanPham` | `MaSanPham` INT IDENTITY | `MaDanhMuc` → DanhMuc, `MaNguoiTao` → NguoiDung (NULL) | `TenSanPham` NVARCHAR(200), `GiaBan` DECIMAL(18,2), `ThuongHieu` NVARCHAR(100), `MoTa` NVARCHAR(MAX), `NgayTao` DATETIME2 | Giá >=0; người tạo 0..1, mỗi danh mục nhiều SP |
| `BienTheSanPham` | `MaBienThe` INT IDENTITY | `MaSanPham` → SanPham | `KichThuoc` NVARCHAR(30), `MauSac` NVARCHAR(50), `SoLuongTon` INT | Tồn >=0; UNIQUE(SP, size, màu) |
| `GioHang` | `MaGioHang` INT IDENTITY | `MaNguoiDung` → NguoiDung | `NgayTao` DATETIME2 | Mỗi người dùng tối đa 1 giỏ DB; demo web đang dùng session |
| `ChiTietGioHang` | `MaChiTietGioHang` INT IDENTITY | `MaGioHang` → GioHang, `MaBienThe` → BienTheSanPham | `SoLuong` INT | Số lượng >0, UNIQUE(giỏ, biến thể) |
| `DonHang` | `MaDonHang` INT IDENTITY | `MaNguoiDung` → NguoiDung (NULL) | `NgayDat` DATETIME2, `TrangThai` NVARCHAR(30), `TongTien` DECIMAL(18,2) | Chỉ nhận hàng tại cửa hàng; 0..1 tài khoản, không có địa chỉ ship |
| `ChiTietDonHang` | `MaChiTietDon` INT IDENTITY | `MaDonHang` → DonHang, `MaBienThe` → BienTheSanPham | `SoLuong` INT, `DonGia` DECIMAL(18,2), `ThanhTien` AS computed | 1 đơn có nhiều dòng; giá chốt tại thời điểm đặt |

## Các mối quan hệ phải thống nhất khi vẽ ERD
- VaiTro 1 — N NguoiDung.
- DanhMuc 1 — N SanPham.
- NguoiDung 1 — 0..N SanPham (người tạo là tùy chọn).
- SanPham 1 — N BienTheSanPham.
- NguoiDung 1 — 0..1 GioHang; GioHang 1 — N ChiTietGioHang.
- BienTheSanPham 1 — N ChiTietGioHang (quan hệ N–N giỏ và biến thể qua bảng nối).
- NguoiDung 1 — 0..N DonHang; DonHang 1 — N ChiTietDonHang.
- BienTheSanPham 1 — N ChiTietDonHang (quan hệ N–N đơn và biến thể qua bảng nối).

## Quy tắc backend còn phải kiểm soát
Tổng tồn kho và trừ tồn phải xử lý trong transaction khi đơn hàng thật được triển khai; hiện tại chỉ có kiểm tra tồn để thêm session giỏ. `TongTien` tự tính bằng trigger trong cả SQL Server và SQLite. `NgayTao` có mặc định. **Bảng công việc yêu cầu chính xác 8 bảng, trong khi thiết kế thực có 9 bảng**; cần lấy ý kiến giảng viên, không tự tuyên bố đạt.


---
# BỔ SUNG W4-007 / W4-008 — Giao nhận, thanh toán, tồn kho (cập nhật Data Dictionary)

Migration: `database/migration_w4_giao_dich_sqlserver.sql` (rollback: `rollback_migration_w4_giao_dich_sqlserver.sql`). Thiết kế theo ERD v2 nhưng **giữ tên cột cũ** để code hiện tại không vỡ. **Chưa chạy thử trên SQL Server thật.** SQLite demo tự nâng cấp tương đương (`app/db.py::_upgrade_sqlite_w4`).

## Cột mới của `DonHang`
| Cột | Kiểu SQL Server | Ý nghĩa / ràng buộc |
| --- | --- | --- |
| `LaDonCu` | BIT, DEFAULT 0 | 1 = đơn tạo trước migration (không có mã nhân viên/thời điểm thật) |
| `HinhThucNhanHang` | VARCHAR(20) | `delivery`/`pickup`; delivery bắt buộc có `DiaChiGiaoHang` (trừ đơn cũ) |
| `TenNguoiNhan`, `SdtNguoiNhan` (VARCHAR 20, chỉ số và +), `DiaChiGiaoHang` | NVARCHAR | Bản chụp lúc đặt |
| `PhiVanChuyen` | DECIMAL(18,2) ≥ 0, DEFAULT 0 | 0 = miễn phí hoặc chưa tính |
| `TongThanhToan` | cột tính PERSISTED | `TongTien + PhiVanChuyen`. `TongTien` = tiền hàng (ERD v2 gọi là `TienHang`) |
| `PhuongThucThanhToan` | NVARCHAR(30) | COD · Chuyển khoản · Ví điện tử · Thẻ |
| `TrangThaiThanhToan` | NVARCHAR(30) | Chưa thanh toán · Đã thanh toán · Hoàn tiền |
| `TrangThaiXacNhan`, `MaNVXacNhan` (FK→NguoiDung), `ThoiDiemXacNhan` | | Chờ xác nhận · Đã xác nhận · Từ chối. Chờ ⇒ NV và thời điểm NULL; còn lại ⇒ có thời điểm (và NV, trừ đơn cũ) |
| `TrangThaiGiaoHang`, `MaNVCapNhatGiaoHang` (FK), `ThoiDiemCapNhatGiaoHang` | | Chưa giao · Đang chuẩn bị · Đang giao · Đã giao · Giao thất bại; ≠ Chưa giao ⇒ đã xác nhận |
| `DaHuy`, `ThoiDiemHuy` | BIT, DATETIME2(0) | DaHuy=1 ⇔ có thời điểm hủy |
| `DaTruKho` | BIT | 1 = tồn của đơn đang bị trừ. CHECK: đơn đã hủy/từ chối bắt buộc = 0 |
`TrangThai` (cột cũ) vẫn còn và **luôn khớp** (CHECK `CK_DonHang_DongBoTrangThaiCu`): hủy/từ chối→Đã hủy; đã giao→Hoàn thành; đã xác nhận→Đã xác nhận; còn lại→Chờ xác nhận.

## Bảng/cột mới khác
- `ChiTietDonHang.TenSanPham/MauSac/KichThuoc`: bản chụp (NOT NULL sau khi điền từ dữ liệu cũ).
- `GiaoDichThanhToan` (PK `MaGiaoDich`; FK `MaDonHang`→DonHang): `PhuongThuc`, `SoTien`, `TrangThai` (Chờ xử lý · Thành công · Thất bại · Hoàn tiền), `MaThamChieu`. **UNIQUE**: `MaThamChieu` (lọc NOT NULL); mỗi đơn tối đa 1 giao dịch `Thành công`.
- `HoaDon` (ERD v2): `MaDonHang` UNIQUE, `SoHoaDon` UNIQUE.
- `NhatKyMigration`: nhật ký từng bước migration/seed.
- `ThongTinGiaoDich` (cũ) giữ lại cho email/ghi chú và tương thích; code ghi song song.

## Mapping dữ liệu đơn cũ
`Chờ xác nhận`→(Chờ xác nhận, Chưa giao) · `Đã xác nhận`→(Đã xác nhận, Chưa giao) · `Hoàn thành`→(Đã xác nhận, Đã giao) · `Đã hủy`→(Chờ xác nhận, Chưa giao, DaHuy=1; **giả định** vì không biết đã xác nhận trước khi hủy). Thời điểm xác nhận/giao/hủy lấy `NgayDat` (xấp xỉ). Đơn cũ không có `ThongTinGiaoDich` → `pickup`, tên người nhận lấy từ `NguoiDung`.

## Quy tắc tồn kho (W4-008) — `app/services/order_inventory.py`
Tạo đơn hợp lệ → trừ theo biến thể (UPDATE có điều kiện `SoLuongTon >= SL`, kiểm tra rowcount); hủy / từ chối / thanh toán online thất bại → hoàn đúng 1 lần (chỉ khi `DaTruKho=1`); thiếu ở bất kỳ dòng nào → rollback cả đơn. Giao thất bại **chưa** hoàn kho (ngoài phạm vi, cần chốt quy tắc).
