/* =====================================================================
   seed_products_w4.sql   (W4 - hoan thien seed giay dep + kiem chung DB tai lap)
   Them 16 san pham giay/dep CO TINH HUONG BIEN vao DB hien co.

   NGUYEN TAC
   - KHONG lam mat du lieu co san: chi INSERT ... WHERE NOT EXISTS (theo ten san pham,
     theo bo ba san pham-mau-size). Khong UPDATE/DELETE/DROP. Chay lai nhieu lan an toan:
     lan 2 se them 0 dong va KHONG dat lai ton kho da thay doi.
   - Chay SAU: schema.sql, seed.sql, migrate_w3_visibility_sqlserver.sql (can cot SanPham.HienThi).
   - Chon dung database TEST trong SSMS truoc khi chay. File luu UTF-8 co BOM.
   - Anh san pham KHONG seed (bang SanPhamHinhAnh chi luu file upload that qua trang admin).

   TINH HUONG BIEN (16 san pham, 36 bien the):
    1. Giày Running Nike Air Zoom                       | màu-size chéo: có Đen và 42 nhưng không có Đen-42
    2. Giày Sneaker Adidas Originals                    | bình thường (1 màu, 2 size)
    3. Dép Xỏ Ngón Bitis Hunter                         | màu-size chéo: Đen chỉ có 40, Xanh chỉ có 41
    4. Giày Sneaker Puma Suede                          | bình thường
    5. Dép Crocs Classic Clog                           | bình thường
    6. Giày Running Asics Gel-Kayano                    | tồn thấp: Xanh-43 chỉ còn 1 (test mua 2 > tồn)
    7. Giày Thể Thao Nữ Adidas Ultraboost               | cùng size 39 khác màu
    8. Sneaker Converse Chuck 70 (Hi)                   | màu-size chéo: KHÔNG có Đen-40 / Trắng-41; tên có ngoặc
    9. Sneaker Vans Old Skool 100% Cotton               | tên có ký tự % (test tìm kiếm LIKE)
   10. Dép Quai Hậu Nữ Teva Hurricane                   | bình thường
   11. Sandal O'Neill Beach_Pro                         | tên có ' và _ (test tìm kiếm, escape)
   12. Giày Sneaker New Balance 574                     | ẨN (HienThi=0): không được hiện ở danh sách/chi tiết/mua
   13. Giày Chạy Bộ Mizuno Wave Rider                   | HẾT HÀNG: mọi biến thể tồn 0
   14. Dép Adidas Adilette Shower                       | bình thường
   15. Giày Thể Thao Chạy Bộ Đường Dài Siêu Nhẹ Đệm Khí | tên dài + giá cao + size không phải số
   16. Sandal Nhập Mới (Chưa Có Biến Thể)               | KHÔNG có biến thể: TongTon=0, trang chi tiết không có lựa chọn

   TONG KY VONG cho 16 san pham nay: 15 hien thi, 1 an, 1 het hang,
   1 khong co bien the, 36 bien the, tong ton 532 (hien thi: 512).
   TRANG THAI: viet va doc ky; CHUA chay tren SQL Server that. Dan ket qua khoi kiem tra
   cuoi file vao bao cao khi chay tren may nhom.
   ===================================================================== */
SET NOCOUNT ON;
SET QUOTED_IDENTIFIER ON;
SET ANSI_NULLS ON;
GO

/* ---- B0. Kiem tra dieu kien; sai thi dung toan bo script ---- */
IF DB_NAME() IN (N'master', N'model', N'msdb', N'tempdb')
   OR OBJECT_ID(N'dbo.SanPham', N'U') IS NULL
   OR OBJECT_ID(N'dbo.BienTheSanPham', N'U') IS NULL
   OR OBJECT_ID(N'dbo.DanhMuc', N'U') IS NULL
   OR COL_LENGTH(N'dbo.SanPham', N'HienThi') IS NULL
BEGIN
    RAISERROR(N'DUNG: chon database test co bang SanPham/BienTheSanPham/DanhMuc va chay migrate_w3_visibility_sqlserver.sql truoc (can cot SanPham.HienThi).', 16, 1);
    SET NOEXEC ON;
END
GO

/* ---- B1. Nap du lieu (1 transaction; loi la ROLLBACK toan bo) ---- */
DECLARE @nguoiTao INT = (SELECT TOP (1) MaNguoiDung FROM dbo.NguoiDung WHERE Email = N'minh@shop.vn');  -- NULL cung duoc
DECLARE @spTruoc INT = (SELECT COUNT(*) FROM dbo.SanPham);
DECLARE @btTruoc INT = (SELECT COUNT(*) FROM dbo.BienTheSanPham);

BEGIN TRY
    BEGIN TRAN;

    /* Danh muc: chi them neu thieu (theo ten) */
    INSERT INTO dbo.DanhMuc (TenDanhMuc, MoTa)
    SELECT v.Ten, v.MoTa
    FROM (VALUES
        (N'Giày Thể Thao', N'Giày vận động, chạy bộ'),
        (N'Giày Sneaker', N'Sneaker đi học, đi chơi'),
        (N'Dép & Sandal', N'Dép, sandal nhiều kích cỡ')
    ) v(Ten, MoTa)
    WHERE NOT EXISTS (SELECT 1 FROM dbo.DanhMuc d WHERE d.TenDanhMuc = v.Ten);

    CREATE TABLE #sp_w4 (Ten NVARCHAR(200) NOT NULL, TenDanhMuc NVARCHAR(100) NOT NULL, Gia DECIMAL(18,2) NOT NULL,
                         ThuongHieu NVARCHAR(100) NULL, MoTa NVARCHAR(MAX) NULL, HienThi BIT NOT NULL);
    INSERT INTO #sp_w4 (Ten, TenDanhMuc, Gia, ThuongHieu, MoTa, HienThi) VALUES
    (N'Giày Running Nike Air Zoom', N'Giày Thể Thao', 1250000, N'Nike', N'Giày chạy bộ êm ái, hỗ trợ vận động tốt', 1),
    (N'Giày Sneaker Adidas Originals', N'Giày Sneaker', 990000, N'Adidas', N'Phong cách thời trang cổ điển, dễ phối đồ', 1),
    (N'Dép Xỏ Ngón Bitis Hunter', N'Dép & Sandal', 250000, N'Bitis', N'Chất liệu cao su siêu bền, chống trượt', 1),
    (N'Giày Sneaker Puma Suede', N'Giày Sneaker', 850000, N'Puma', N'Da lộn cao cấp, năng động trẻ trung', 1),
    (N'Dép Crocs Classic Clog', N'Dép & Sandal', 490000, N'Crocs', N'Nhựa Croslite siêu nhẹ, chống nước, thoáng khí', 1),
    (N'Giày Running Asics Gel-Kayano', N'Giày Thể Thao', 2890000, N'Asics', N'Giày chạy bộ đệm ổn định', 1),
    (N'Giày Thể Thao Nữ Adidas Ultraboost', N'Giày Thể Thao', 3200000, N'Adidas', N'Đệm Boost êm ái', 1),
    (N'Sneaker Converse Chuck 70 (Hi)', N'Giày Sneaker', 1650000, N'Converse', N'Cổ cao, phong cách cổ điển', 1),
    (N'Sneaker Vans Old Skool 100% Cotton', N'Giày Sneaker', 1450000, N'Vans', N'Vải canvas bền', 1),
    (N'Dép Quai Hậu Nữ Teva Hurricane', N'Dép & Sandal', 1100000, N'Teva', N'Quai hậu đi biển', 1),
    (N'Sandal O''Neill Beach_Pro', N'Dép & Sandal', 420000, N'O''Neill', N'Sandal đi biển', 1),
    (N'Giày Sneaker New Balance 574', N'Giày Sneaker', 2100000, N'New Balance', N'SP đang ẩn', 0),
    (N'Giày Chạy Bộ Mizuno Wave Rider', N'Giày Thể Thao', 2450000, N'Mizuno', N'SP hết hàng', 1),
    (N'Dép Adidas Adilette Shower', N'Dép & Sandal', 650000, N'Adidas', N'Dép tắm nhẹ, chống trượt', 1),
    (N'Giày Thể Thao Chạy Bộ Đường Dài Siêu Nhẹ Đệm Khí Chống Sốc Chống Trượt Phiên Bản Giới Hạn Mùa Thu 2026 Cổ Thấp Unisex', N'Giày Thể Thao', 9990000, N'LocalShoes', N'Tên dài ~120 ký tự, giá cao, size chữ', 1),
    (N'Sandal Nhập Mới (Chưa Có Biến Thể)', N'Dép & Sandal', 199000, N'LocalShoes', N'Chưa nhập kho: chưa có biến thể nào', 1);

    CREATE TABLE #bt_w4 (Ten NVARCHAR(200) NOT NULL, Mau NVARCHAR(50) NOT NULL, Size NVARCHAR(30) NOT NULL, Ton INT NOT NULL);
    INSERT INTO #bt_w4 (Ten, Mau, Size, Ton) VALUES
    (N'Giày Running Nike Air Zoom', N'Đen', N'40', 50),
    (N'Giày Running Nike Air Zoom', N'Đen', N'41', 40),
    (N'Giày Running Nike Air Zoom', N'Trắng', N'42', 30),
    (N'Giày Sneaker Adidas Originals', N'Trắng', N'39', 20),
    (N'Giày Sneaker Adidas Originals', N'Trắng', N'40', 25),
    (N'Dép Xỏ Ngón Bitis Hunter', N'Đen', N'40', 15),
    (N'Dép Xỏ Ngón Bitis Hunter', N'Xanh', N'41', 10),
    (N'Giày Sneaker Puma Suede', N'Đen', N'38', 20),
    (N'Giày Sneaker Puma Suede', N'Đen', N'39', 15),
    (N'Dép Crocs Classic Clog', N'Xám', N'39', 30),
    (N'Dép Crocs Classic Clog', N'Xám', N'40', 25),
    (N'Giày Running Asics Gel-Kayano', N'Đen', N'40', 12),
    (N'Giày Running Asics Gel-Kayano', N'Đen', N'41', 8),
    (N'Giày Running Asics Gel-Kayano', N'Xanh', N'42', 10),
    (N'Giày Running Asics Gel-Kayano', N'Xanh', N'43', 1),
    (N'Giày Thể Thao Nữ Adidas Ultraboost', N'Trắng', N'38', 10),
    (N'Giày Thể Thao Nữ Adidas Ultraboost', N'Trắng', N'39', 14),
    (N'Giày Thể Thao Nữ Adidas Ultraboost', N'Hồng', N'39', 6),
    (N'Sneaker Converse Chuck 70 (Hi)', N'Đen', N'41', 10),
    (N'Sneaker Converse Chuck 70 (Hi)', N'Trắng', N'40', 12),
    (N'Sneaker Vans Old Skool 100% Cotton', N'Đen', N'39', 20),
    (N'Sneaker Vans Old Skool 100% Cotton', N'Đen', N'40', 18),
    (N'Sneaker Vans Old Skool 100% Cotton', N'Xám', N'41', 9),
    (N'Dép Quai Hậu Nữ Teva Hurricane', N'Hồng', N'38', 10),
    (N'Dép Quai Hậu Nữ Teva Hurricane', N'Hồng', N'39', 10),
    (N'Sandal O''Neill Beach_Pro', N'Xanh', N'40', 15),
    (N'Sandal O''Neill Beach_Pro', N'Đen', N'41', 5),
    (N'Giày Sneaker New Balance 574', N'Xám', N'40', 10),
    (N'Giày Sneaker New Balance 574', N'Xám', N'41', 10),
    (N'Giày Chạy Bộ Mizuno Wave Rider', N'Đen', N'40', 0),
    (N'Giày Chạy Bộ Mizuno Wave Rider', N'Đen', N'41', 0),
    (N'Giày Chạy Bộ Mizuno Wave Rider', N'Trắng', N'42', 0),
    (N'Dép Adidas Adilette Shower', N'Đen', N'39', 20),
    (N'Dép Adidas Adilette Shower', N'Đen', N'40', 20),
    (N'Dép Adidas Adilette Shower', N'Trắng', N'41', 15),
    (N'Giày Thể Thao Chạy Bộ Đường Dài Siêu Nhẹ Đệm Khí Chống Sốc Chống Trượt Phiên Bản Giới Hạn Mùa Thu 2026 Cổ Thấp Unisex', N'Đen', N'Free size', 7);

    /* San pham (dong dong: cot HienThi chi hop le sau migrate_w3_visibility) */
    EXEC sys.sp_executesql N'
        INSERT INTO dbo.SanPham (MaDanhMuc, MaNguoiTao, TenSanPham, GiaBan, ThuongHieu, MoTa, HienThi)
        SELECT dm.MaDanhMuc, @nguoiTao, s.Ten, s.Gia, s.ThuongHieu, s.MoTa, s.HienThi
        FROM #sp_w4 s
        JOIN dbo.DanhMuc dm ON dm.TenDanhMuc = s.TenDanhMuc
        WHERE NOT EXISTS (SELECT 1 FROM dbo.SanPham x WHERE x.TenSanPham = s.Ten)',
        N'@nguoiTao INT', @nguoiTao = @nguoiTao;

    /* Bien the: chi them bo ba (san pham, size, mau) chua co; khong dung vao ton kho da co */
    INSERT INTO dbo.BienTheSanPham (MaSanPham, KichThuoc, MauSac, SoLuongTon)
    SELECT sp.MaSanPham, b.Size, b.Mau, b.Ton
    FROM #bt_w4 b
    JOIN dbo.SanPham sp ON sp.TenSanPham = b.Ten
    WHERE NOT EXISTS (SELECT 1 FROM dbo.BienTheSanPham x
                      WHERE x.MaSanPham = sp.MaSanPham AND x.KichThuoc = b.Size AND x.MauSac = b.Mau);

    DROP TABLE #bt_w4;
    DROP TABLE #sp_w4;

    IF OBJECT_ID(N'dbo.NhatKyMigration', N'U') IS NOT NULL
        INSERT INTO dbo.NhatKyMigration (TenMigration, Buoc, KetQua, GhiChu)
        VALUES (N'W4-seed-products', N'nap-du-lieu', N'OK',
                N'SanPham them=' + CAST((SELECT COUNT(*) FROM dbo.SanPham) - @spTruoc AS NVARCHAR(20))
              + N'; BienThe them=' + CAST((SELECT COUNT(*) FROM dbo.BienTheSanPham) - @btTruoc AS NVARCHAR(20)));

    COMMIT;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK;
    IF OBJECT_ID(N'tempdb..#bt_w4') IS NOT NULL DROP TABLE #bt_w4;
    IF OBJECT_ID(N'tempdb..#sp_w4') IS NOT NULL DROP TABLE #sp_w4;
    PRINT N'Seed LOI va da ROLLBACK: ' + ERROR_MESSAGE();
    THROW;
END CATCH
GO

/* =====================================================================
   KHOI KIEM TRA (so ky vong chi dung o lan chay dau tren DB co dung 16 SP nay;
   neu DB co san du lieu khac, doi chieu cot "Ky vong" voi nhom SP W4 - loc theo ten)
   ===================================================================== */
;WITH ten_w4 AS (SELECT Ten FROM (VALUES
    (N'Giày Running Nike Air Zoom'),
    (N'Giày Sneaker Adidas Originals'),
    (N'Dép Xỏ Ngón Bitis Hunter'),
    (N'Giày Sneaker Puma Suede'),
    (N'Dép Crocs Classic Clog'),
    (N'Giày Running Asics Gel-Kayano'),
    (N'Giày Thể Thao Nữ Adidas Ultraboost'),
    (N'Sneaker Converse Chuck 70 (Hi)'),
    (N'Sneaker Vans Old Skool 100% Cotton'),
    (N'Dép Quai Hậu Nữ Teva Hurricane'),
    (N'Sandal O''Neill Beach_Pro'),
    (N'Giày Sneaker New Balance 574'),
    (N'Giày Chạy Bộ Mizuno Wave Rider'),
    (N'Dép Adidas Adilette Shower'),
    (N'Giày Thể Thao Chạy Bộ Đường Dài Siêu Nhẹ Đệm Khí Chống Sốc Chống Trượt Phiên Bản Giới Hạn Mùa Thu 2026 Cổ Thấp Unisex'),
    (N'Sandal Nhập Mới (Chưa Có Biến Thể)')
) t(Ten)),
sp AS (SELECT s.MaSanPham, s.HienThi, ISNULL(SUM(b.SoLuongTon), 0) AS TongTon, COUNT(b.MaBienThe) AS SoBienThe
       FROM dbo.SanPham s JOIN ten_w4 t ON t.Ten = s.TenSanPham
       LEFT JOIN dbo.BienTheSanPham b ON b.MaSanPham = s.MaSanPham
       GROUP BY s.MaSanPham, s.HienThi)
SELECT COUNT(*)                                                       AS TongSP_W4,        -- ky vong 16
       SUM(CASE WHEN HienThi = 1 THEN 1 ELSE 0 END)                   AS SPHienThi,        -- ky vong 15
       SUM(CASE WHEN HienThi = 0 THEN 1 ELSE 0 END)                   AS SPAn,             -- ky vong 1
       SUM(CASE WHEN SoBienThe > 0 AND TongTon = 0 THEN 1 ELSE 0 END) AS SPHetHang,        -- ky vong 1
       SUM(CASE WHEN SoBienThe = 0 THEN 1 ELSE 0 END)                 AS SPKhongBienThe,   -- ky vong 1
       SUM(SoBienThe)                                                 AS TongBienThe,      -- ky vong 36
       SUM(TongTon)                                                   AS TongTon           -- ky vong 532 (lan dau)
FROM sp;

-- Toan ven: khong ton am, khong trung (SP, size, mau), khong bien the mo coi (ca 3 truy van phai 0 dong)
SELECT * FROM dbo.BienTheSanPham WHERE SoLuongTon < 0;
SELECT MaSanPham, KichThuoc, MauSac, COUNT(*) AS SoLan FROM dbo.BienTheSanPham GROUP BY MaSanPham, KichThuoc, MauSac HAVING COUNT(*) > 1;
SELECT b.* FROM dbo.BienTheSanPham b LEFT JOIN dbo.SanPham s ON s.MaSanPham = b.MaSanPham WHERE s.MaSanPham IS NULL;

-- Tim kiem ky tu dac biet: tim 'O''Neill' phai ra 1 dong (LIKE khong coi ' la ky tu dac biet)
SELECT MaSanPham, TenSanPham FROM dbo.SanPham WHERE TenSanPham LIKE N'%O''Neill%';
GO

SET NOEXEC OFF;
GO
