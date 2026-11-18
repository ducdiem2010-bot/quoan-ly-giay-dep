# Quy tắc tính "Sản phẩm bán chạy" (Best Sellers Rule)
**Người viết:** Nguyễn Thái Nghĩa

## 1. Định nghĩa điều kiện "Đã bán"
- **Schema V1 (SQLite):** Chỉ tính những đơn hàng có `DonHang.TrangThaiDon = 1` (Hoàn thành / Đã thanh toán). Các đơn Hủy (-1) hoặc Chờ xác nhận (0) hoàn toàn KHÔNG ĐƯỢC TÍNH vào.
- **Tính cộng dồn Biến thể:** Nếu 1 sản phẩm bán được 2 đôi size 40 và 3 đôi size 41 trong cùng/hoặc khác đơn hàng hoàn thành -> Tổng Đã Bán = 2 + 3 = 5. Sản phẩm nào có tổng số lượng bán lớn nhất sẽ xếp lên đầu (ORDER BY DESC).

## 2. Tuyến JOIN Database
Để đếm chính xác, câu lệnh SQL sẽ JOIN 4 bảng theo tuyến sau:
`SanPham` -> JOIN `BienTheSanPham` (Qua MaSanPham) -> JOIN `ChiTietDonHang` (Qua MaBienThe) -> JOIN `DonHang` (Qua MaDonHang).
- Chỉ lấy các sản phẩm đang hiển thị (`SanPham.HienThi = 1`).