-- Nhóm 6: dữ liệu DEMO, KHÔNG dùng mật khẩu mẫu trên hệ thống thật.
INSERT INTO VaiTro (MaVaiTro, TenVaiTro, MoTa) VALUES
(1, 'Admin', 'Quản lý cửa hàng'),
(2, 'Seller', 'Nhân viên bán hàng'),
(3, 'Customer', 'Khách hàng');
INSERT INTO NguoiDung (MaNguoiDung, MaVaiTro, HoVaTen, Email, MatKhauHash, SoDienThoai) VALUES
(1, 1, 'Quản trị demo', 'admin@shop.vn', 'pbkdf2:sha256:120000$f7bx29cCfI$a6fd34b18d6187ac251c4a227be09527bcd2557e6975de5f9b8a32c60a19fe0a', '0900000001'),
(2, 2, 'Nhân viên Minh', 'minh@shop.vn', 'pbkdf2:sha256:120000$f7bx29cCfI$a6fd34b18d6187ac251c4a227be09527bcd2557e6975de5f9b8a32c60a19fe0a', '0900000002'),
(3, 3, 'Khách thử nghiệm', 'khach@shop.vn', 'pbkdf2:sha256:120000$f7bx29cCfI$a6fd34b18d6187ac251c4a227be09527bcd2557e6975de5f9b8a32c60a19fe0a', '0900000003');
INSERT INTO DanhMuc (MaDanhMuc, TenDanhMuc, MoTa) VALUES
(1, 'Giày Thể Thao', 'Giày vận động, chạy bộ'),
(2, 'Giày Sneaker', 'Sneaker đi học, đi chơi'),
(3, 'Dép & Sandal', 'Dép, sandal nhiều kích cỡ');
INSERT INTO SanPham (MaDanhMuc, MaNguoiTao, TenSanPham, GiaBan, ThuongHieu, MoTa) VALUES
(1, 2, 'Nike Air Zoom Pegasus', 1250000, 'Nike', 'Giày chạy bộ êm chân, phù hợp đi học và vận động.'),
(2, 2, 'Adidas Originals Superstar', 990000, 'Adidas', 'Sneaker phong cách cổ điển, dễ phối đồ.'),
(3, 2, 'Biti’s Hunter Sandal', 250000, 'Biti’s', 'Sandal quai hậu thoải mái, chống trượt.'),
(2, 2, 'Puma Suede Classic', 850000, 'Puma', 'Giày da lộn phong cách thể thao.'),
(3, 2, 'Crocs Classic Clog', 490000, 'Crocs', 'Dép nhẹ, dễ vệ sinh, thoáng chân.'),
(1, 2, 'New Balance 574', 1390000, 'New Balance', 'Giày thể thao dáng retro, đế bền.'),
(2, 2, 'Converse Chuck Taylor', 1190000, 'Converse', 'Giày cổ thấp vải canvas phổ biến.'),
(1, 2, 'Asics Gel Contend', 1100000, 'Asics', 'Giày chạy bộ hỗ trợ đệm chân.'),
(3, 2, 'Dép Adidas Adilette', 450000, 'Adidas', 'Dép quai ngang đi trong nhà hoặc ra phố.'),
(3, 2, 'Sandal Teva Hurricane', 1250000, 'Teva', 'Sandal tiện đi du lịch, chống trơn.');
INSERT INTO BienTheSanPham (MaSanPham, KichThuoc, MauSac, SoLuongTon) VALUES
(1, '39', 'Đen', 10),
(1, '40', 'Trắng', 11),
(1, '41', 'Xám', 12),
(2, '39', 'Đen', 11),
(2, '40', 'Trắng', 12),
(2, '41', 'Xám', 13),
(3, '39', 'Đen', 12),
(3, '40', 'Trắng', 13),
(3, '41', 'Xám', 14),
(4, '39', 'Đen', 13),
(4, '40', 'Trắng', 14),
(4, '41', 'Xám', 15),
(5, '39', 'Đen', 14),
(5, '40', 'Trắng', 15),
(5, '41', 'Xám', 16),
(6, '39', 'Đen', 15),
(6, '40', 'Trắng', 16),
(6, '41', 'Xám', 17),
(7, '39', 'Đen', 16),
(7, '40', 'Trắng', 17),
(7, '41', 'Xám', 18),
(8, '39', 'Đen', 17),
(8, '40', 'Trắng', 18),
(8, '41', 'Xám', 19),
(9, '39', 'Đen', 18),
(9, '40', 'Trắng', 19),
(9, '41', 'Xám', 20),
(10, '39', 'Đen', 19),
(10, '40', 'Trắng', 20),
(10, '41', 'Xám', 21);
INSERT INTO GioHang (MaNguoiDung) VALUES
(3);
INSERT INTO ChiTietGioHang (MaGioHang, MaBienThe, SoLuong) VALUES
(1, 1, 2),
(1, 6, 1);
INSERT INTO DonHang (MaNguoiDung, TrangThai) VALUES
(3, 'Đã xác nhận');
INSERT INTO ChiTietDonHang (MaDonHang, MaBienThe, SoLuong, DonGia) VALUES
(1, 1, 2, 1250000),
(1, 4, 1, 990000);
