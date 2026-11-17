/* =====================================================================
   du_lieu_v2.sql - Du lieu mau cho schema v2 (chay SAU schema_v2_proposal.sql)
   Trang thai: DE XUAT - chua chay thu tren SQL Server.
   Du lieu san pham/bien the duoc chuyen tu bo du lieu cu sang cau truc moi.
   ===================================================================== */
USE QuanLyBanHang_V2;
GO
SET QUOTED_IDENTIFIER ON;
SET ANSI_NULLS ON;
GO

/* ---------- Vai tro ---------- */
INSERT INTO VaiTro (TenVaiTro, MoTa) VALUES
(N'Admin',    N'Quản trị hệ thống'),
(N'Seller',   N'Người quản lý sản phẩm, xác nhận và giao đơn'),
(N'Customer', N'Khách hàng');

/* ---------- Nguoi dung (MatKhauHash la gia tri mau, thay bang hash that) ---------- */
INSERT INTO NguoiDung (MaVaiTro, HoVaTen, TenDangNhap, MatKhauHash, SoDienThoai) VALUES
(1, N'Quản Trị Viên',    'admin', 'HASH_PLACEHOLDER', '0900000001'),  -- 1
(2, N'Nguyễn Văn Minh',  'minh',  'HASH_PLACEHOLDER', '0900000002'),  -- 2 (Seller)
(2, N'Lê Hữu Nghĩa',     'nghia', 'HASH_PLACEHOLDER', '0900000003'),  -- 3 (Seller)
(3, N'Trần Thị Tuấn',    'tuan',  'HASH_PLACEHOLDER', '0900000004'),  -- 4 (Customer)
(3, N'Phạm Thu Lan',     'lan',   'HASH_PLACEHOLDER', '0900000005');  -- 5 (Customer)

/* ---------- Danh muc ---------- */
INSERT INTO DanhMuc (TenDanhMuc, MoTa) VALUES
(N'Giày Thể Thao', N'Giày thể thao, chạy bộ các loại'),
(N'Giày Sneaker',  N'Giày sneaker thời trang'),
(N'Dép & Sandal',  N'Dép quai hậu, dép xỏ ngón, dép nhựa');

/* ---------- Thuong hieu: ma 1..12 theo dung thu tu ---------- */
INSERT INTO ThuongHieu (TenThuongHieu) VALUES
(N'Nike'), (N'Adidas'), (N'Bitis'), (N'Puma'), (N'Crocs'), (N'Asics'),
(N'Converse'), (N'Vans'), (N'Teva'), (N'O''Neill'), (N'New Balance'), (N'Mizuno');

/* ---------- Mau sac & Kich thuoc ---------- */
INSERT INTO MauSac (TenMau) VALUES (N'Đen'), (N'Trắng'), (N'Xanh'), (N'Xám'), (N'Hồng');  -- 1..5
INSERT INTO KichThuoc (GiaTriKichThuoc) VALUES (N'38'), (N'39'), (N'40'), (N'41'), (N'42'), (N'43'); -- 1..6

/* ---------- San pham: 14 SP. SP12 bi an (TrangThai=0), SP13 het ton,
              SP9 va SP11 co ky tu dac biet de test tim kiem ---------- */
INSERT INTO SanPham (MaDanhMuc, MaThuongHieu, MaNguoiTao, TenSanPham, GiaBan, TrangThai, MoTa) VALUES
(1,  1, 2, N'Giày Running Nike Air Zoom',          1250000, 1, N'Giày chạy bộ êm ái, hỗ trợ vận động tốt'),
(2,  2, 2, N'Giày Sneaker Adidas Originals',        990000, 1, N'Phong cách thời trang cổ điển, dễ phối đồ'),
(3,  3, 2, N'Dép Xỏ Ngón Bitis Hunter',             250000, 1, N'Chất liệu cao su siêu bền, chống trượt'),
(2,  4, 2, N'Giày Sneaker Puma Suede',              850000, 1, N'Da lộn cao cấp, năng động trẻ trung'),
(3,  5, 2, N'Dép Crocs Classic Clog',               490000, 1, N'Nhựa Croslite siêu nhẹ, chống nước, thoáng khí'),
(1,  6, 2, N'Giày Running Asics Gel-Kayano',       2890000, 1, N'Giày chạy bộ đệm ổn định'),
(1,  2, 3, N'Giày Thể Thao Nữ Adidas Ultraboost',  3200000, 1, N'Đệm Boost êm ái'),
(2,  7, 3, N'Sneaker Converse Chuck 70 (Hi)',      1650000, 1, N'Cổ cao, phong cách cổ điển'),
(2,  8, 3, N'Sneaker Vans Old Skool 100% Cotton',  1450000, 1, N'Vải canvas bền'),
(3,  9, 3, N'Dép Quai Hậu Nữ Teva Hurricane',      1100000, 1, N'Quai hậu đi biển'),
(3, 10, 3, N'Sandal O''Neill Beach_Pro',            420000, 1, N'Sandal đi biển'),
(2, 11, 2, N'Giày Sneaker New Balance 574',        2100000, 0, N'SP đang ẩn'),
(1, 12, 2, N'Giày Chạy Bộ Mizuno Wave Rider',      2450000, 1, N'SP hết hàng'),
(3,  2, 3, N'Dép Adidas Adilette Shower',           650000, 1, N'Dép tắm nhẹ, chống trượt');

/* ---------- Hinh anh: moi SP 1 anh dai dien + them anh phu cho SP1 ---------- */
INSERT INTO HinhAnhSanPham (MaSanPham, DuongDanAnh, AnhDaiDien)
SELECT MaSanPham, CONCAT(N'/images/products/sp', MaSanPham, N'_main.jpg'), 1 FROM SanPham;
INSERT INTO HinhAnhSanPham (MaSanPham, DuongDanAnh, AnhDaiDien) VALUES
(1, N'/images/products/sp1_side.jpg', 0),
(1, N'/images/products/sp1_sole.jpg', 0);

/* ---------- Bien the: (SP, Mau, Size, Ton). Mau: 1 Den 2 Trang 3 Xanh 4 Xam 5 Hong
              Size: 1=38 2=39 3=40 4=41 5=42 6=43 ---------- */
INSERT INTO BienTheSanPham (MaSanPham, MaMau, MaKichThuoc, SoLuongTon) VALUES
(1, 1, 3, 50), (1, 1, 4, 40), (1, 2, 5, 30),                     -- bien the 1..3
(2, 2, 2, 20), (2, 2, 3, 25),                                     -- 4..5
(3, 1, 3, 15), (3, 3, 4, 10),                                     -- 6..7
(4, 1, 1, 20), (4, 1, 2, 15),                                     -- 8..9
(5, 4, 2, 30), (5, 4, 3, 25),                                     -- 10..11
(6, 1, 3, 12), (6, 1, 4,  8), (6, 3, 5, 10), (6, 3, 6, 5),        -- 12..15
(7, 2, 1, 10), (7, 2, 2, 14), (7, 5, 2,  6),                      -- 16..18
(8, 1, 4, 10), (8, 2, 3, 12),                                     -- 19..20 (den41 + trang40: KHONG khop den+40)
(9, 1, 2, 20), (9, 1, 3, 18), (9, 4, 4,  9),                      -- 21..23
(10, 5, 1, 10), (10, 5, 2, 10),                                   -- 24..25
(11, 3, 3, 15), (11, 1, 4,  5),                                   -- 26..27 (co Den va size 40 nhung khac bien the)
(12, 4, 3, 10), (12, 4, 4, 10),                                   -- 28..29
(13, 1, 3,  0), (13, 1, 4,  0), (13, 2, 5, 0),                    -- 30..32 het ton
(14, 1, 2, 20), (14, 1, 3, 20), (14, 2, 4, 15);                   -- 33..35

/* ---------- Gio hang ---------- */
INSERT INTO GioHang (MaNguoiDung) VALUES (4), (5);               -- gio 1: tuan, gio 2: lan
INSERT INTO ChiTietGioHang (MaGioHang, MaBienThe, SoLuong) VALUES
(1, 1, 2), (1, 6, 1),
(2, 17, 1);

/* ---------- Dia chi giao hang ---------- */
INSERT INTO DiaChiGiaoHang (MaNguoiDung, DiaChiChiTiet, MacDinh) VALUES
(4, N'12 Lạch Tray, Ngô Quyền, Hải Phòng', 1),
(4, N'45 Phố Huế, Hai Bà Trưng, Hà Nội',   0),
(5, N'88 Nguyễn Trãi, Thanh Xuân, Hà Nội', 1);

/* ---------- Don hang (TienHang do trigger tu tinh tu chi tiet) ---------- */
/* DH1: da xac nhan, dang giao, COD chua thanh toan */
INSERT INTO DonHang (MaNguoiDung, MaNVXacNhan, MaNVCapNhatGiaoHang, NgayDat,
    TenNguoiNhan, SdtNguoiNhan, DiaChiGiaoHang, PhiVanChuyen,
    PhuongThucThanhToan, TrangThaiThanhToan,
    TrangThaiXacNhan, ThoiDiemXacNhan, TrangThaiGiaoHang, ThoiDiemCapNhatGiaoHang)
VALUES (4, 2, 3, '2026-10-15T09:30:00',
    N'Trần Thị Tuấn', '0900000004', N'12 Lạch Tray, Ngô Quyền, Hải Phòng', 30000,
    N'COD', N'Chưa thanh toán',
    N'Đã xác nhận', '2026-10-15T10:00:00', N'Đang giao', '2026-10-16T08:00:00');

/* DH2: chuyen khoan da thanh toan, da giao xong */
INSERT INTO DonHang (MaNguoiDung, MaNVXacNhan, MaNVCapNhatGiaoHang, NgayDat,
    TenNguoiNhan, SdtNguoiNhan, DiaChiGiaoHang, PhiVanChuyen,
    PhuongThucThanhToan, TrangThaiThanhToan,
    TrangThaiXacNhan, ThoiDiemXacNhan, TrangThaiGiaoHang, ThoiDiemCapNhatGiaoHang)
VALUES (5, 2, 3, '2026-10-10T14:00:00',
    N'Phạm Thu Lan', '0900000005', N'88 Nguyễn Trãi, Thanh Xuân, Hà Nội', 25000,
    N'Chuyển khoản', N'Đã thanh toán',
    N'Đã xác nhận', '2026-10-10T14:30:00', N'Đã giao', '2026-10-12T16:45:00');

/* DH3: khach tu huy khi con cho xac nhan */
INSERT INTO DonHang (MaNguoiDung, NgayDat, TenNguoiNhan, SdtNguoiNhan, DiaChiGiaoHang, PhiVanChuyen,
    PhuongThucThanhToan, DaHuy, ThoiDiemHuy)
VALUES (4, '2026-10-17T20:15:00',
    N'Trần Thị Tuấn', '0900000004', N'45 Phố Huế, Hai Bà Trưng, Hà Nội', 30000,
    N'COD', 1, '2026-10-17T21:00:00');

/* DH4: dat moi, dang cho xac nhan (vi dien tu, chua thanh toan) */
INSERT INTO DonHang (MaNguoiDung, NgayDat, TenNguoiNhan, SdtNguoiNhan, DiaChiGiaoHang, PhiVanChuyen,
    PhuongThucThanhToan)
VALUES (5, '2026-10-19T08:20:00',
    N'Phạm Thu Lan', '0900000005', N'88 Nguyễn Trãi, Thanh Xuân, Hà Nội', 25000,
    N'Ví điện tử');

/* ---------- Chi tiet don hang (ban chup ten SP/mau/size/gia) ---------- */
INSERT INTO ChiTietDonHang (MaDonHang, MaBienThe, SoLuong, DonGia, TenSanPham, MauSac, KichThuoc) VALUES
(1,  1, 2, 1250000, N'Giày Running Nike Air Zoom',         N'Đen',   N'40'),
(1,  4, 1,  990000, N'Giày Sneaker Adidas Originals',      N'Trắng', N'39'),
(2, 33, 1,  650000, N'Dép Adidas Adilette Shower',         N'Đen',   N'39'),
(3, 12, 1, 2890000, N'Giày Running Asics Gel-Kayano',      N'Đen',   N'40'),
(4, 17, 1, 3200000, N'Giày Thể Thao Nữ Adidas Ultraboost', N'Trắng', N'39');

/* ---------- Hoa don (chi lap cho don da xac nhan) ---------- */
INSERT INTO HoaDon (MaDonHang, SoHoaDon, NgayLap) VALUES
(1, 'HD2026-0001', '2026-10-15T10:05:00'),
(2, 'HD2026-0002', '2026-10-10T14:35:00');

/* ---------- Thong tin cua hang & tu van ---------- */
INSERT INTO ThongTinCuaHang (TenCuaHang, DiaChi, SoDienThoai, Zalo, Facebook) VALUES
(N'Shop Giày Dép Hà Nội', N'Hà Nội', '0900000001', N'0900000001', N'https://facebook.com/shop-demo');

INSERT INTO ThongTinTuVan (TieuDe, NoiDungTuVan, ThongTinLienHe) VALUES
(N'Cách chọn size giày',  N'Đo chiều dài bàn chân vào cuối ngày, cộng thêm 0,5–1 cm rồi đối chiếu bảng size.', N'Zalo: 0900000001'),
(N'Chính sách đổi trả',   N'Đổi size trong 7 ngày nếu sản phẩm chưa qua sử dụng và còn nguyên tem.',            N'Hotline: 0900000001');
GO

/* ---------- Truy van kiem tra nhanh (doi chieu ket qua khi chay that) ---------- */
SELECT COUNT(*) AS TongSP, SUM(CASE WHEN TrangThai = 1 THEN 1 ELSE 0 END) AS SPHienThi FROM SanPham;  -- ky vong 14 / 13
SELECT COUNT(*) AS TongBienThe FROM BienTheSanPham;                                                    -- ky vong 35
SELECT MaDonHang, TienHang, PhiVanChuyen, TongThanhToan FROM DonHang ORDER BY MaDonHang;
-- ky vong TienHang: DH1 3.490.000 | DH2 650.000 | DH3 2.890.000 | DH4 3.200.000
GO

		   USE QuanLyBanHang_V2;
			   SELECT * FROM NguoiDung ORDER BY MaNguoiDung DESC;