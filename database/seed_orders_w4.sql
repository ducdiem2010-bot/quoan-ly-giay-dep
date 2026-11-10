/* =====================================================================
   seed_orders_w4.sql  (TUY CHON - don mau cho moi trang thai, chay SAU migration_w4 + seed_products_w4)
   4 don: cho xac nhan | dang giao (COD) | da giao + da thanh toan chuyen khoan | khach tu huy.
   Ton kho duoc tru dung nhu code (don huy: da hoan nen khong doi). Chay 1 lan (co danh dau
   trong NhatKyMigration); chay lai se bo qua. Khong DROP/DELETE. Chon DB TEST truoc. UTF-8 co BOM.
   TRANG THAI: CHUA chay tren SQL Server that.
   ===================================================================== */
SET NOCOUNT ON; SET QUOTED_IDENTIFIER ON; SET ANSI_NULLS ON;
GO
IF DB_NAME() IN (N'master', N'model', N'msdb', N'tempdb')
   OR COL_LENGTH(N'dbo.DonHang', N'DaTruKho') IS NULL
   OR OBJECT_ID(N'dbo.GiaoDichThanhToan', N'U') IS NULL
   OR OBJECT_ID(N'dbo.NhatKyMigration', N'U') IS NULL
BEGIN
    RAISERROR(N'DUNG: chay migration_w4_giao_dich_sqlserver.sql truoc, tren database test.', 16, 1);
    SET NOEXEC ON;
END
GO
IF EXISTS (SELECT 1 FROM dbo.NhatKyMigration WHERE TenMigration = N'W4-seed-orders' AND KetQua = N'OK')
BEGIN
    PRINT N'Don mau da duoc nap truoc do - bo qua.';
    SET NOEXEC ON;
END
GO
DECLARE @khach INT = (SELECT TOP (1) MaNguoiDung FROM dbo.NguoiDung WHERE Email = N'khach@shop.vn');
DECLARE @nv    INT = (SELECT TOP (1) MaNguoiDung FROM dbo.NguoiDung WHERE Email = N'minh@shop.vn');
DECLARE @v_nike INT = (SELECT bt.MaBienThe FROM dbo.BienTheSanPham bt JOIN dbo.SanPham sp ON sp.MaSanPham = bt.MaSanPham
                       WHERE sp.TenSanPham = N'Giày Running Nike Air Zoom' AND bt.MauSac = N'Đen' AND bt.KichThuoc = N'40');
DECLARE @v_adi  INT = (SELECT bt.MaBienThe FROM dbo.BienTheSanPham bt JOIN dbo.SanPham sp ON sp.MaSanPham = bt.MaSanPham
                       WHERE sp.TenSanPham = N'Giày Sneaker Adidas Originals' AND bt.MauSac = N'Trắng' AND bt.KichThuoc = N'39');
DECLARE @v_shw  INT = (SELECT bt.MaBienThe FROM dbo.BienTheSanPham bt JOIN dbo.SanPham sp ON sp.MaSanPham = bt.MaSanPham
                       WHERE sp.TenSanPham = N'Dép Adidas Adilette Shower' AND bt.MauSac = N'Đen' AND bt.KichThuoc = N'39');
DECLARE @v_ub   INT = (SELECT bt.MaBienThe FROM dbo.BienTheSanPham bt JOIN dbo.SanPham sp ON sp.MaSanPham = bt.MaSanPham
                       WHERE sp.TenSanPham = N'Giày Thể Thao Nữ Adidas Ultraboost' AND bt.MauSac = N'Trắng' AND bt.KichThuoc = N'39');
IF @khach IS NULL OR @nv IS NULL OR @v_nike IS NULL OR @v_adi IS NULL OR @v_shw IS NULL OR @v_ub IS NULL
BEGIN
    RAISERROR(N'DUNG: thieu tai khoan khach@shop.vn / minh@shop.vn hoac san pham tu seed_products_w4.sql.', 16, 1);
    RETURN;
END
BEGIN TRY
    BEGIN TRAN;
    DECLARE @o1 INT, @o2 INT, @o3 INT, @o4 INT;

    /* Don 1: cho xac nhan, COD, giao tan noi; giu 2 doi Nike Den-40 */
    INSERT INTO dbo.DonHang (MaNguoiDung, NgayDat, TrangThai, HinhThucNhanHang, TenNguoiNhan, SdtNguoiNhan, DiaChiGiaoHang,
        PhiVanChuyen, PhuongThucThanhToan, TrangThaiThanhToan, TrangThaiXacNhan, TrangThaiGiaoHang, DaHuy, DaTruKho)
    VALUES (@khach, '2026-11-05T09:30:00', N'Chờ xác nhận', 'delivery', N'Khách thử nghiệm', '0900000003',
        N'12 Lạch Tray, Ngô Quyền, Hải Phòng', 30000, N'COD', N'Chưa thanh toán', N'Chờ xác nhận', N'Chưa giao', 0, 1);
    SET @o1 = SCOPE_IDENTITY();
    INSERT INTO dbo.ChiTietDonHang (MaDonHang, MaBienThe, SoLuong, DonGia, TenSanPham, MauSac, KichThuoc)
    VALUES (@o1, @v_nike, 2, 1250000, N'Giày Running Nike Air Zoom', N'Đen', N'40');
    INSERT INTO dbo.GiaoDichThanhToan (MaDonHang, PhuongThuc, SoTien, TrangThai) VALUES (@o1, N'COD', 2500000 + 30000, N'Chờ xử lý');

    /* Don 2: da xac nhan, dang giao, COD */
    INSERT INTO dbo.DonHang (MaNguoiDung, NgayDat, TrangThai, HinhThucNhanHang, TenNguoiNhan, SdtNguoiNhan, DiaChiGiaoHang,
        PhiVanChuyen, PhuongThucThanhToan, TrangThaiThanhToan, TrangThaiXacNhan, MaNVXacNhan, ThoiDiemXacNhan,
        TrangThaiGiaoHang, MaNVCapNhatGiaoHang, ThoiDiemCapNhatGiaoHang, DaHuy, DaTruKho)
    VALUES (@khach, '2026-11-04T10:00:00', N'Đã xác nhận', 'delivery', N'Khách thử nghiệm', '0900000003',
        N'45 Phố Huế, Hai Bà Trưng, Hà Nội', 30000, N'COD', N'Chưa thanh toán', N'Đã xác nhận', @nv, '2026-11-04T10:30:00',
        N'Đang giao', @nv, '2026-11-05T08:00:00', 0, 1);
    SET @o2 = SCOPE_IDENTITY();
    INSERT INTO dbo.ChiTietDonHang (MaDonHang, MaBienThe, SoLuong, DonGia, TenSanPham, MauSac, KichThuoc)
    VALUES (@o2, @v_adi, 1, 990000, N'Giày Sneaker Adidas Originals', N'Trắng', N'39');
    INSERT INTO dbo.GiaoDichThanhToan (MaDonHang, PhuongThuc, SoTien, TrangThai) VALUES (@o2, N'COD', 990000 + 30000, N'Chờ xử lý');

    /* Don 3: chuyen khoan da thanh toan, da giao xong */
    INSERT INTO dbo.DonHang (MaNguoiDung, NgayDat, TrangThai, HinhThucNhanHang, TenNguoiNhan, SdtNguoiNhan, DiaChiGiaoHang,
        PhiVanChuyen, PhuongThucThanhToan, TrangThaiThanhToan, TrangThaiXacNhan, MaNVXacNhan, ThoiDiemXacNhan,
        TrangThaiGiaoHang, MaNVCapNhatGiaoHang, ThoiDiemCapNhatGiaoHang, DaHuy, DaTruKho)
    VALUES (@khach, '2026-11-01T14:00:00', N'Hoàn thành', 'delivery', N'Khách thử nghiệm', '0900000003',
        N'88 Nguyễn Trãi, Thanh Xuân, Hà Nội', 25000, N'Chuyển khoản', N'Đã thanh toán', N'Đã xác nhận', @nv, '2026-11-01T14:30:00',
        N'Đã giao', @nv, '2026-11-03T16:45:00', 0, 1);
    SET @o3 = SCOPE_IDENTITY();
    INSERT INTO dbo.ChiTietDonHang (MaDonHang, MaBienThe, SoLuong, DonGia, TenSanPham, MauSac, KichThuoc)
    VALUES (@o3, @v_shw, 1, 650000, N'Dép Adidas Adilette Shower', N'Đen', N'39');
    INSERT INTO dbo.GiaoDichThanhToan (MaDonHang, PhuongThuc, SoTien, TrangThai, MaThamChieu)
    VALUES (@o3, N'Chuyển khoản', 650000 + 25000, N'Thành công', 'FT26110100001');
    INSERT INTO dbo.HoaDon (MaDonHang, SoHoaDon, NgayLap) VALUES (@o3, 'HD2026-W4-0001', '2026-11-01T14:35:00');

    /* Don 4: khach tu huy khi cho xac nhan (ton da duoc hoan => DaTruKho = 0, ton khong doi) */
    INSERT INTO dbo.DonHang (MaNguoiDung, NgayDat, TrangThai, HinhThucNhanHang, TenNguoiNhan, SdtNguoiNhan, DiaChiGiaoHang,
        PhiVanChuyen, PhuongThucThanhToan, TrangThaiThanhToan, TrangThaiXacNhan, TrangThaiGiaoHang, DaHuy, ThoiDiemHuy, DaTruKho)
    VALUES (@khach, '2026-11-06T20:15:00', N'Đã hủy', 'delivery', N'Khách thử nghiệm', '0900000003',
        N'45 Phố Huế, Hai Bà Trưng, Hà Nội', 30000, N'Ví điện tử', N'Chưa thanh toán', N'Chờ xác nhận', N'Chưa giao', 1, '2026-11-06T21:00:00', 0);
    SET @o4 = SCOPE_IDENTITY();
    INSERT INTO dbo.ChiTietDonHang (MaDonHang, MaBienThe, SoLuong, DonGia, TenSanPham, MauSac, KichThuoc)
    VALUES (@o4, @v_ub, 1, 3200000, N'Giày Thể Thao Nữ Adidas Ultraboost', N'Trắng', N'39');
    INSERT INTO dbo.GiaoDichThanhToan (MaDonHang, PhuongThuc, SoTien, TrangThai) VALUES (@o4, N'Ví điện tử', 3200000 + 30000, N'Thất bại');

    /* Tru ton cho don 1-3 (don 4 da hoan). Dieu kien SoLuongTon >= so mua; thieu thi bao loi va ROLLBACK. */
    UPDATE dbo.BienTheSanPham SET SoLuongTon = SoLuongTon - 2 WHERE MaBienThe = @v_nike AND SoLuongTon >= 2;
    IF @@ROWCOUNT <> 1 RAISERROR(N'Khong du ton Nike Den-40 de nap don mau.', 16, 1);
    UPDATE dbo.BienTheSanPham SET SoLuongTon = SoLuongTon - 1 WHERE MaBienThe = @v_adi AND SoLuongTon >= 1;
    IF @@ROWCOUNT <> 1 RAISERROR(N'Khong du ton Adidas Originals de nap don mau.', 16, 1);
    UPDATE dbo.BienTheSanPham SET SoLuongTon = SoLuongTon - 1 WHERE MaBienThe = @v_shw AND SoLuongTon >= 1;
    IF @@ROWCOUNT <> 1 RAISERROR(N'Khong du ton Adilette Shower de nap don mau.', 16, 1);

    INSERT INTO dbo.NhatKyMigration (TenMigration, Buoc, KetQua, GhiChu)
    VALUES (N'W4-seed-orders', N'nap-don-mau', N'OK', N'Don ' + CAST(@o1 AS NVARCHAR(20)) + N'..' + CAST(@o4 AS NVARCHAR(20)));
    COMMIT;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK;
    PRINT N'Nap don mau LOI va da ROLLBACK: ' + ERROR_MESSAGE();
    THROW;
END CATCH
GO
-- Kiem tra (ky vong 4 don mau; TongTien tu trigger: 2.500.000 | 990.000 | 650.000 | 3.200.000; tong tru ton = 4 doi)
SELECT d.MaDonHang, d.TrangThai, d.TrangThaiXacNhan, d.TrangThaiGiaoHang, d.TrangThaiThanhToan, d.DaHuy, d.DaTruKho,
       d.TongTien, d.PhiVanChuyen, d.TongThanhToan
FROM dbo.DonHang d WHERE d.TenNguoiNhan = N'Khách thử nghiệm' AND d.NgayDat >= '2026-11-01' ORDER BY d.MaDonHang;
DBCC CHECKCONSTRAINTS (N'dbo.DonHang') WITH ALL_CONSTRAINTS, NO_INFOMSGS;   -- ky vong 0 dong
GO
SET NOEXEC OFF;
GO
