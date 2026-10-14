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
