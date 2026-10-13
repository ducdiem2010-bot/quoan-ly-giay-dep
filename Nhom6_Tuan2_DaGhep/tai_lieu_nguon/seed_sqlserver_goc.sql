USE QuanLyBanHang;
GO

INSERT INTO VaiTro (TenVaiTro, MoTa) VALUES
(N'Admin', N'Quản trị hệ thống'),
(N'Seller', N'Người quản lý sản phẩm'),
(N'Customer', N'Khách hàng');

-- MatKhauHash la gia tri mau, thay bang hash that tu ung dung
INSERT INTO NguoiDung (MaVaiTro, HoVaTen, Email, MatKhauHash, SoDienThoai, DiaChi) VALUES
(1, N'Quản Trị Viên', 'admin@shop.vn', 'HASH_PLACEHOLDER', '0900000001', N'Hà Nội'),
(2, N'Nguyễn Văn Minh', 'minh@shop.vn', 'HASH_PLACEHOLDER', '0900000002', N'Hà Nội'),
(3, N'Trần Thị Tuấn', 'tuan@gmail.com', 'HASH_PLACEHOLDER', '0900000003', N'Hải Phòng');

-- Cập nhật danh mục chỉ dành cho Giày & Dép
INSERT INTO DanhMuc (TenDanhMuc, MoTa) VALUES
(N'Giày Thể Thao', N'Giày thể thao, chạy bộ các loại'),
(N'Giày Sneaker', N'Giày sneaker thời trang'),
(N'Dép & Sandal', N'Dép quai hậu, dép xỏ ngón, dép nhựa');

-- Cập nhật 5 sản phẩm Giày & Dép
INSERT INTO SanPham (MaDanhMuc, MaNguoiTao, TenSanPham, GiaBan, ThuongHieu, MoTa) VALUES
(1, 2, N'Giày Running Nike Air Zoom', 1250000, N'Nike', N'Giày chạy bộ êm ái, hỗ trợ vận động tốt'),
(2, 2, N'Giày Sneaker Adidas Originals', 990000, N'Adidas', N'Phong cách thời trang cổ điển, dễ phối đồ'),
(3, 2, N'Dép Xỏ Ngón Bitis Hunter', 250000, N'Bitis', N'Chất liệu cao su siêu bền, chống trượt'),
(2, 2, N'Giày Sneaker Puma Suede', 850000, N'Puma', N'Da lộn cao cấp, năng động trẻ trung'),
(3, 2, N'Dép Crocs Classic Clog', 490000, N'Crocs', N'Nhựa Croslite siêu nhẹ, chống nước, thoáng khí');

-- Biến thể sản phẩm (Size giày dép: 38, 39, 40, 41, 42)
INSERT INTO BienTheSanPham (MaSanPham, KichThuoc, MauSac, SoLuongTon) VALUES
(1, N'40', N'Đen', 50), (1, N'41', N'Đen', 40), (1, N'42', N'Trắng', 30),
(2, N'39', N'Trắng', 20), (2, N'40', N'Trắng', 25),
(3, N'40', N'Đen', 15), (3, N'41', N'Xanh', 10),
(4, N'38', N'Đen', 20), (4, N'39', N'Đen', 15),
(5, N'39', N'Xám', 30), (5, N'40', N'Xám', 25);

INSERT INTO GioHang (MaNguoiDung) VALUES (3);
INSERT INTO ChiTietGioHang (MaGioHang, MaBienThe, SoLuong) VALUES (1, 1, 2), (1, 6, 1);

INSERT INTO DonHang (MaNguoiDung, DiaChiGiaoHang) VALUES (3, N'Hải Phòng');
INSERT INTO ChiTietDonHang (MaDonHang, MaBienThe, SoLuong, DonGia) VALUES
(1, 1, 2, 1250000), (1, 4, 1, 990000); -- trigger tu tinh TongTien
GO