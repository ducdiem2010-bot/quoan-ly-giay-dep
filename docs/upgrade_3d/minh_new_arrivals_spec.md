# Minh M1.1 — Hợp đồng Sản phẩm mới nhất

- Nguồn: `database/schema_sqlite.sql` và `database/schema_v2.sql` trong ZIP; đường dẫn `database/v2/schema_v2_fresh_safe.sql` nêu trong Excel **không tồn tại trong ZIP này**.
- SQLite/V1: `SanPham.HienThi=1`; SQL Server V2: `SanPham.TrangThai=1`.
- Thứ tự: `NgayTao DESC`, tiếp theo `MaSanPham DESC`; tối đa 6 sản phẩm.
- Trả `list[dict]` chứa: `MaSanPham`, `TenSanPham`, `GiaBan`, `ThuongHieu`, `TenDanhMuc`, `TongTon`, `AnhDaiDien` (và metadata tương thích card).
- Bảng giá, tồn và ảnh không được tạo giả. Không có sản phẩm ⇒ danh sách rỗng.
- SQLite dùng `SanPhamHinhAnh.TenTep`; V2 dùng `HinhAnhSanPham.DuongDanAnh`. V2 hiện dùng fallback thay vì tự giả định đường dẫn tệp.
- V2 chỉ có SQL theo schema; **chưa chạy trên SQL Server thật**, chưa nghiệm thu end-to-end. Ứng dụng hiện còn nhiều route cũ dựa trên SQLite/V1.
