-- Nhóm 6: dữ liệu DEMO, KHÔNG dùng mật khẩu mẫu trên hệ thống thật.
USE QuanLyBanHang;
GO
INSERT INTO VaiTro (TenVaiTro, MoTa) VALUES
(N'Admin', N'Quản lý cửa hàng'),
(N'Seller', N'Nhân viên bán hàng'),
(N'Customer', N'Khách hàng');
INSERT INTO NguoiDung (MaVaiTro, HoVaTen, Email, MatKhauHash, SoDienThoai) VALUES
(1, N'Quản trị demo', N'admin@shop.vn', N'pbkdf2:sha256:120000$f7bx29cCfI$a6fd34b18d6187ac251c4a227be09527bcd2557e6975de5f9b8a32c60a19fe0a', N'0900000001'),
(2, N'Nhân viên Minh', N'minh@shop.vn', N'pbkdf2:sha256:120000$f7bx29cCfI$a6fd34b18d6187ac251c4a227be09527bcd2557e6975de5f9b8a32c60a19fe0a', N'0900000002'),
(3, N'Khách thử nghiệm', N'khach@shop.vn', N'pbkdf2:sha256:120000$f7bx29cCfI$a6fd34b18d6187ac251c4a227be09527bcd2557e6975de5f9b8a32c60a19fe0a', N'0900000003');
INSERT INTO DanhMuc (TenDanhMuc, MoTa) VALUES
(N'Giày Thể Thao', N'Giày vận động, chạy bộ'),
(N'Giày Sneaker', N'Sneaker đi học, đi chơi'),
(N'Dép & Sandal', N'Dép, sandal nhiều kích cỡ');
INSERT INTO SanPham (MaDanhMuc, MaNguoiTao, TenSanPham, GiaBan, ThuongHieu, MoTa) VALUES
(1, 2, N'Nike Air Zoom Pegasus', 1250000, N'Nike', N'Giày chạy bộ êm chân, phù hợp đi học và vận động.'),
(2, 2, N'Adidas Originals Superstar', 990000, N'Adidas', N'Sneaker phong cách cổ điển, dễ phối đồ.'),
(3, 2, N'Biti’s Hunter Sandal', 250000, N'Biti’s', N'Sandal quai hậu thoải mái, chống trượt.'),
(2, 2, N'Puma Suede Classic', 850000, N'Puma', N'Giày da lộn phong cách thể thao.'),
(3, 2, N'Crocs Classic Clog', 490000, N'Crocs', N'Dép nhẹ, dễ vệ sinh, thoáng chân.'),
(1, 2, N'New Balance 574', 1390000, N'New Balance', N'Giày thể thao dáng retro, đế bền.'),
(2, 2, N'Converse Chuck Taylor', 1190000, N'Converse', N'Giày cổ thấp vải canvas phổ biến.'),
(1, 2, N'Asics Gel Contend', 1100000, N'Asics', N'Giày chạy bộ hỗ trợ đệm chân.'),
(3, 2, N'Dép Adidas Adilette', 450000, N'Adidas', N'Dép quai ngang đi trong nhà hoặc ra phố.'),
(3, 2, N'Sandal Teva Hurricane', 1250000, N'Teva', N'Sandal tiện đi du lịch, chống trơn.');
INSERT INTO BienTheSanPham (MaSanPham, KichThuoc, MauSac, SoLuongTon) VALUES
(1, N'39', N'Đen', 10),
(1, N'40', N'Trắng', 11),
(1, N'41', N'Xám', 12),
(2, N'39', N'Đen', 11),
(2, N'40', N'Trắng', 12),
(2, N'41', N'Xám', 13),
(3, N'39', N'Đen', 12),
(3, N'40', N'Trắng', 13),
(3, N'41', N'Xám', 14),
(4, N'39', N'Đen', 13),
(4, N'40', N'Trắng', 14),
(4, N'41', N'Xám', 15),
(5, N'39', N'Đen', 14),
(5, N'40', N'Trắng', 15),
(5, N'41', N'Xám', 16),
(6, N'39', N'Đen', 15),
(6, N'40', N'Trắng', 16),
(6, N'41', N'Xám', 17),
(7, N'39', N'Đen', 16),
(7, N'40', N'Trắng', 17),
(7, N'41', N'Xám', 18),
(8, N'39', N'Đen', 17),
(8, N'40', N'Trắng', 18),
(8, N'41', N'Xám', 19),
(9, N'39', N'Đen', 18),
(9, N'40', N'Trắng', 19),
(9, N'41', N'Xám', 20),
(10, N'39', N'Đen', 19),
(10, N'40', N'Trắng', 20),
(10, N'41', N'Xám', 21);
INSERT INTO GioHang (MaNguoiDung) VALUES
(3);
INSERT INTO ChiTietGioHang (MaGioHang, MaBienThe, SoLuong) VALUES
(1, 1, 2),
(1, 6, 1);
INSERT INTO DonHang (MaNguoiDung, TrangThai) VALUES
(3, N'Đã xác nhận');
INSERT INTO ChiTietDonHang (MaDonHang, MaBienThe, SoLuong, DonGia) VALUES
(1, 1, 2, 1250000),
(1, 4, 1, 990000);
<<<<<<< HEAD
=======

-- W3-006 (AI-assisted): two extra shoe examples, unchanged original 10 IDs.
INSERT INTO SanPham (MaDanhMuc, MaNguoiTao, TenSanPham, GiaBan, ThuongHieu, MoTa) VALUES
(3,2,N'Sandal Học Sinh Chống Trượt',290000,N'LocalShoes',N'Test hết tồn'),
(1,2,N'Giày Thể Thao Mẫu Ẩn',590000,N'LocalShoes',N'Test sản phẩm ẩn');
INSERT INTO BienTheSanPham (MaSanPham,KichThuoc,MauSac,SoLuongTon) VALUES (11,N'39',N'Đỏ',0),(11,N'40',N'Xanh',0),(12,N'41',N'Đen',8);
IF COL_LENGTH('dbo.SanPham','HienThi') IS NOT NULL
    EXEC(N'UPDATE dbo.SanPham SET HienThi=0 WHERE TenSanPham=N''Giày Thể Thao Mẫu Ẩn''');
>>>>>>> ba1d4e0 (Upload project)
GO
