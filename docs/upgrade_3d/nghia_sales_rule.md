# Nghĩa N1.1 — Quy tắc xác định bán chạy

## SQLite/V1

`ChiTietDonHang.MaDonHang → DonHang.MaDonHang`, `ChiTietDonHang.MaBienThe → BienTheSanPham.MaBienThe`, `BienTheSanPham.MaSanPham → SanPham.MaSanPham`.

- Chỉ tính `DonHang.TrangThai='Hoàn thành'`.
- Chỉ hiển thị sản phẩm `SanPham.HienThi=1`.
- `SUM(ChiTietDonHang.SoLuong)` được GROUP BY mã sản phẩm, không GROUP BY biến thể.
- Đơn chờ, đã xác nhận nhưng chưa hoàn thành, đã hủy: **không tính**.
- Thứ tự `TongDaBan DESC, MaSanPham ASC`, tối đa 6 sản phẩm.
- Không có đơn hoàn thành → trả `[]`, giao diện báo chưa có dữ liệu.

## SQL Server V2 — cần nhóm xác nhận

Đối chiếu với `database/schema_v2.sql`: điều kiện hiện lập trình là `DaHuy=0`, `TrangThaiXacNhan='Đã xác nhận'`, `TrangThaiGiaoHang='Đã giao'`, `TrangThai=1` cho sản phẩm. **Điều kiện `TrangThaiThanhToan` chưa được chốt** với nhóm/thầy. Không tuyên bố V2 PASS trước khi thống nhất, chạy trên DB V2 thử và đối chiếu SQL.

Không sửa schema/seed hoặc tạo doanh số giả.
