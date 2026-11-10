/* =====================================================================
   migration_w4_giao_dich_sqlserver.sql   (W4-007 - Minh)
   Mo rong schema giao nhan / giao dich thanh toan tren SQL Server.

   NGUYEN TAC
   - CHI BO SUNG / CHUYEN DOI: khong DROP bang, khong DELETE du lieu, khong
     TRUNCATE. Chay lai nhieu lan an toan (idempotent): buoc nao da xong thi bo qua.
   - Don hang cu (schema 9 bang) khong mat: cot cu TrangThai, TongTien,
     bang ThongTinGiaoDich giu nguyen; du lieu cu duoc CHUYEN sang cot moi.
   - Thiet ke cot/constraint theo ERD v2 (DonHang, ChiTietDonHang, HoaDon);
     ten cot cu TongTien = "TienHang" trong ERD v2 (giu ten cu de code cu khong vo).
   - Nhat ky: moi buoc ghi vao dbo.NhatKyMigration (bang chung chay that).

   TRUOC KHI CHAY (bat buoc, tren DATABASE TEST truoc)
   1) Sao luu:
        BACKUP DATABASE [TEN_DB_TEST]
          TO DISK = N'C:\Backup\TEN_DB_TEST_truoc_W4_007.bak'
          WITH COPY_ONLY, INIT, CHECKSUM;
   2) Chon dung database trong SSMS (o "Available Databases"), KHONG de master.
   3) File nay luu UTF-8 co BOM; SSMS: File > Open > Open with encoding neu loi font.
   4) Thu tu chay: schema.sql -> seed.sql -> migrate_w3_visibility -> migrate_product_images
      -> migrate_w3_favorites -> migrate_account_profile -> migration_checkout
      -> FILE NAY -> seed_products_w4.sql -> (tuy chon) seed_orders_w4.sql

   ROLLBACK
   - Chinh: RESTORE tu file .bak o buoc 1.
   - Phu (chi cau truc): rollback_migration_w4_giao_dich_sqlserver.sql.

   TRANG THAI: da viet va doc ky, CHUA chay tren SQL Server that
   (moi truong tao file khong co SQL Server). Phai chay tren may nhom, dan log
   (NhatKyMigration + ket qua khoi kiem tra cuoi file) vao bao cao truoc khi nghiem thu.
   ===================================================================== */
SET NOCOUNT ON;
SET QUOTED_IDENTIFIER ON;
SET ANSI_NULLS ON;
GO

/* ---- B0. Kiem tra database dich; sai thi dung toan bo script ---- */
IF DB_NAME() IN (N'master', N'model', N'msdb', N'tempdb')
   OR OBJECT_ID(N'dbo.DonHang', N'U') IS NULL
   OR OBJECT_ID(N'dbo.BienTheSanPham', N'U') IS NULL
   OR OBJECT_ID(N'dbo.ChiTietDonHang', N'U') IS NULL
   OR OBJECT_ID(N'dbo.NguoiDung', N'U') IS NULL
BEGIN
    RAISERROR(N'DUNG: chua chon dung database (can co DonHang, ChiTietDonHang, BienTheSanPham, NguoiDung). Chon database test roi chay lai.', 16, 1);
    SET NOEXEC ON;
END
GO

/* ---- B1. Bang nhat ky migration ---- */
IF OBJECT_ID(N'dbo.NhatKyMigration', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.NhatKyMigration (
        MaNhatKy     INT IDENTITY(1,1) CONSTRAINT PK_NhatKyMigration PRIMARY KEY,
        TenMigration NVARCHAR(100) NOT NULL,
        Buoc         NVARCHAR(100) NOT NULL,
        KetQua       NVARCHAR(20)  NOT NULL,
        GhiChu       NVARCHAR(500) NULL,
        ThoiDiem     DATETIME2(0)  NOT NULL CONSTRAINT DF_NhatKyMigration_ThoiDiem DEFAULT SYSDATETIME(),
        CONSTRAINT CK_NhatKyMigration_KetQua CHECK (KetQua IN (N'OK', N'LOI', N'BO_QUA'))
    );
END
GO

/* ---- B2. Dem so dong TRUOC khi sua (doi chieu "don cu khong mat") ---- */
IF NOT EXISTS (SELECT 1 FROM dbo.NhatKyMigration WHERE TenMigration = N'W4-007' AND Buoc = N'2-dem-truoc')
    INSERT INTO dbo.NhatKyMigration (TenMigration, Buoc, KetQua, GhiChu)
    SELECT N'W4-007', N'2-dem-truoc', N'OK',
           N'DB=' + DB_NAME()
         + N'; DonHang=' + CAST((SELECT COUNT(*) FROM dbo.DonHang) AS NVARCHAR(20))
         + N'; ChiTietDonHang=' + CAST((SELECT COUNT(*) FROM dbo.ChiTietDonHang) AS NVARCHAR(20))
         + N'; BienTheSanPham=' + CAST((SELECT COUNT(*) FROM dbo.BienTheSanPham) AS NVARCHAR(20));
GO

/* ---- B3. Bao dam bang ThongTinGiaoDich (tu migration_checkout) ton tai ---- */
IF OBJECT_ID(N'dbo.ThongTinGiaoDich', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.ThongTinGiaoDich (
      MaDonHang INT NOT NULL CONSTRAINT PK_ThongTinGiaoDich PRIMARY KEY,
      HoTen NVARCHAR(100) NOT NULL,
      SoDienThoai VARCHAR(20) NOT NULL,
      Email NVARCHAR(150) NULL,
      HinhThucNhanHang VARCHAR(20) NOT NULL,
      DiaChiGiaoHang NVARCHAR(255) NULL,
      PhuongThucThanhToan VARCHAR(30) NOT NULL,
      TrangThaiThanhToan NVARCHAR(30) NOT NULL CONSTRAINT DF_TTGD_ThanhToan DEFAULT N'Chưa thanh toán',
      PhiVanChuyen DECIMAL(18,2) NULL,
      GhiChu NVARCHAR(500) NULL,
      NgayTao DATETIME2 NOT NULL CONSTRAINT DF_TTGD_NgayTao DEFAULT SYSDATETIME(),
      CONSTRAINT FK_TTGD_DonHang FOREIGN KEY(MaDonHang) REFERENCES dbo.DonHang(MaDonHang) ON DELETE CASCADE,
      CONSTRAINT CK_TTGD_NhanHang CHECK (HinhThucNhanHang IN ('delivery','pickup')),
      CONSTRAINT CK_TTGD_Payment CHECK (PhuongThucThanhToan IN ('cod','bank_transfer'))
    );
END
GO

/* ---- B4. DonHang: them cot giao nhan / thanh toan / xac nhan / giao hang / huy / ton kho ---- */
IF COL_LENGTH(N'dbo.DonHang', N'LaDonCu') IS NULL
    ALTER TABLE dbo.DonHang ADD LaDonCu BIT NOT NULL CONSTRAINT DF_DonHang_LaDonCu DEFAULT 0;           -- 1 = don tao truoc migration (chua co NV/thoi diem that)
IF COL_LENGTH(N'dbo.DonHang', N'HinhThucNhanHang') IS NULL
    ALTER TABLE dbo.DonHang ADD HinhThucNhanHang VARCHAR(20) NOT NULL CONSTRAINT DF_DonHang_HinhThuc DEFAULT 'delivery';
IF COL_LENGTH(N'dbo.DonHang', N'TenNguoiNhan') IS NULL
    ALTER TABLE dbo.DonHang ADD TenNguoiNhan NVARCHAR(100) NULL;
IF COL_LENGTH(N'dbo.DonHang', N'SdtNguoiNhan') IS NULL
    ALTER TABLE dbo.DonHang ADD SdtNguoiNhan VARCHAR(20) NULL;
IF COL_LENGTH(N'dbo.DonHang', N'DiaChiGiaoHang') IS NULL
    ALTER TABLE dbo.DonHang ADD DiaChiGiaoHang NVARCHAR(255) NULL;                                        -- ban chup luc dat; NULL neu nhan tai cua hang
IF COL_LENGTH(N'dbo.DonHang', N'PhiVanChuyen') IS NULL
    ALTER TABLE dbo.DonHang ADD PhiVanChuyen DECIMAL(18,2) NOT NULL CONSTRAINT DF_DonHang_Phi DEFAULT 0;  -- 0 = mien phi hoac cua hang chua tinh
IF COL_LENGTH(N'dbo.DonHang', N'PhuongThucThanhToan') IS NULL
    ALTER TABLE dbo.DonHang ADD PhuongThucThanhToan NVARCHAR(30) NOT NULL CONSTRAINT DF_DonHang_PTTT DEFAULT N'COD';
IF COL_LENGTH(N'dbo.DonHang', N'TrangThaiThanhToan') IS NULL
    ALTER TABLE dbo.DonHang ADD TrangThaiThanhToan NVARCHAR(30) NOT NULL CONSTRAINT DF_DonHang_TTTT DEFAULT N'Chưa thanh toán';
IF COL_LENGTH(N'dbo.DonHang', N'TrangThaiXacNhan') IS NULL
    ALTER TABLE dbo.DonHang ADD TrangThaiXacNhan NVARCHAR(30) NOT NULL CONSTRAINT DF_DonHang_TTXN DEFAULT N'Chờ xác nhận';
IF COL_LENGTH(N'dbo.DonHang', N'MaNVXacNhan') IS NULL
    ALTER TABLE dbo.DonHang ADD MaNVXacNhan INT NULL;
IF COL_LENGTH(N'dbo.DonHang', N'ThoiDiemXacNhan') IS NULL
    ALTER TABLE dbo.DonHang ADD ThoiDiemXacNhan DATETIME2(0) NULL;
IF COL_LENGTH(N'dbo.DonHang', N'TrangThaiGiaoHang') IS NULL
    ALTER TABLE dbo.DonHang ADD TrangThaiGiaoHang NVARCHAR(30) NOT NULL CONSTRAINT DF_DonHang_TTGH DEFAULT N'Chưa giao';
IF COL_LENGTH(N'dbo.DonHang', N'MaNVCapNhatGiaoHang') IS NULL
    ALTER TABLE dbo.DonHang ADD MaNVCapNhatGiaoHang INT NULL;
IF COL_LENGTH(N'dbo.DonHang', N'ThoiDiemCapNhatGiaoHang') IS NULL
    ALTER TABLE dbo.DonHang ADD ThoiDiemCapNhatGiaoHang DATETIME2(0) NULL;
IF COL_LENGTH(N'dbo.DonHang', N'DaHuy') IS NULL
    ALTER TABLE dbo.DonHang ADD DaHuy BIT NOT NULL CONSTRAINT DF_DonHang_DaHuy DEFAULT 0;
IF COL_LENGTH(N'dbo.DonHang', N'ThoiDiemHuy') IS NULL
    ALTER TABLE dbo.DonHang ADD ThoiDiemHuy DATETIME2(0) NULL;
IF COL_LENGTH(N'dbo.DonHang', N'DaTruKho') IS NULL
    ALTER TABLE dbo.DonHang ADD DaTruKho BIT NOT NULL CONSTRAINT DF_DonHang_DaTruKho DEFAULT 0;           -- 1 = ton kho cua don nay dang bi tru (W4-008)
GO

/* ---- B5. ChiTietDonHang: ban chup ten SP / mau / size (ERD v2), de NULL cho den khi chuyen doi xong ---- */
IF COL_LENGTH(N'dbo.ChiTietDonHang', N'TenSanPham') IS NULL
    ALTER TABLE dbo.ChiTietDonHang ADD TenSanPham NVARCHAR(200) NULL;
IF COL_LENGTH(N'dbo.ChiTietDonHang', N'MauSac') IS NULL
    ALTER TABLE dbo.ChiTietDonHang ADD MauSac NVARCHAR(50) NULL;
IF COL_LENGTH(N'dbo.ChiTietDonHang', N'KichThuoc') IS NULL
    ALTER TABLE dbo.ChiTietDonHang ADD KichThuoc NVARCHAR(30) NULL;
GO

/* ---- B6. CHUYEN DOI du lieu don cu sang cot moi (chay dung 1 lan, co transaction) ----
   Mapping TrangThai (cu) -> cot moi:
     'Cho xac nhan' -> TrangThaiXacNhan='Chờ xác nhận', GiaoHang='Chưa giao', DaHuy=0
     'Da xac nhan'  -> TrangThaiXacNhan='Đã xác nhận',  GiaoHang='Chưa giao', DaHuy=0
     'Hoan thanh'   -> TrangThaiXacNhan='Đã xác nhận',  GiaoHang='Đã giao',   DaHuy=0
     'Da huy'       -> TrangThaiXacNhan='Chờ xác nhận', GiaoHang='Chưa giao', DaHuy=1   (GIA DINH: khong biet da xac nhan truoc khi huy)
   Don cu khong co NV/thoi diem that: ThoiDiem* lay NgayDat (xap xi), MaNV* de NULL, LaDonCu=1.
   Don cu khong co ThongTinGiaoDich: HinhThucNhanHang='pickup' (schema W2 chi co nhan tai cua hang),
   ten nguoi nhan lay tu NguoiDung.HoVaTen. Don cu chua tung tru kho -> DaTruKho=0. */
IF NOT EXISTS (SELECT 1 FROM dbo.NhatKyMigration WHERE TenMigration = N'W4-007' AND Buoc = N'6-chuyen-doi-don-cu' AND KetQua = N'OK')
BEGIN
    BEGIN TRY
        BEGIN TRAN;

        UPDATE d
        SET LaDonCu             = 1,
            DaTruKho            = 0,
            TenNguoiNhan        = COALESCE(t.HoTen, nd.HoVaTen),
            SdtNguoiNhan        = CASE WHEN c.Sdt <> '' AND c.Sdt NOT LIKE '%[^0-9+]%' THEN c.Sdt ELSE NULL END,
            HinhThucNhanHang    = COALESCE(t.HinhThucNhanHang, 'pickup'),
            DiaChiGiaoHang      = t.DiaChiGiaoHang,
            PhiVanChuyen        = ISNULL(t.PhiVanChuyen, 0),
            PhuongThucThanhToan = CASE WHEN t.PhuongThucThanhToan = 'bank_transfer' THEN N'Chuyển khoản' ELSE N'COD' END,
            TrangThaiThanhToan  = CASE WHEN t.TrangThaiThanhToan IN (N'Đã thanh toán', N'Hoàn tiền')
                                       THEN t.TrangThaiThanhToan ELSE N'Chưa thanh toán' END,
            TrangThaiXacNhan    = CASE WHEN d.TrangThai IN (N'Đã xác nhận', N'Hoàn thành')
                                       THEN N'Đã xác nhận' ELSE N'Chờ xác nhận' END,
            ThoiDiemXacNhan     = CASE WHEN d.TrangThai IN (N'Đã xác nhận', N'Hoàn thành') THEN d.NgayDat ELSE NULL END,
            TrangThaiGiaoHang   = CASE WHEN d.TrangThai = N'Hoàn thành' THEN N'Đã giao' ELSE N'Chưa giao' END,
            ThoiDiemCapNhatGiaoHang = CASE WHEN d.TrangThai = N'Hoàn thành' THEN d.NgayDat ELSE NULL END,
            DaHuy               = CASE WHEN d.TrangThai = N'Đã hủy' THEN 1 ELSE 0 END,
            ThoiDiemHuy         = CASE WHEN d.TrangThai = N'Đã hủy' THEN d.NgayDat ELSE NULL END
        FROM dbo.DonHang d
        LEFT JOIN dbo.ThongTinGiaoDich t ON t.MaDonHang = d.MaDonHang
        LEFT JOIN dbo.NguoiDung nd       ON nd.MaNguoiDung = d.MaNguoiDung
        CROSS APPLY (SELECT REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(ISNULL(t.SoDienThoai, ''), ' ', ''), '.', ''), '-', ''), '(', ''), ')', '') AS Sdt) c;

        UPDATE ct
        SET TenSanPham = sp.TenSanPham,
            MauSac     = bt.MauSac,
            KichThuoc  = bt.KichThuoc
        FROM dbo.ChiTietDonHang ct
        JOIN dbo.BienTheSanPham bt ON bt.MaBienThe = ct.MaBienThe
        JOIN dbo.SanPham sp        ON sp.MaSanPham = bt.MaSanPham
        WHERE ct.TenSanPham IS NULL OR ct.MauSac IS NULL OR ct.KichThuoc IS NULL;

        INSERT INTO dbo.NhatKyMigration (TenMigration, Buoc, KetQua, GhiChu)
        VALUES (N'W4-007', N'6-chuyen-doi-don-cu', N'OK',
                N'Da chuyen ' + CAST((SELECT COUNT(*) FROM dbo.DonHang WHERE LaDonCu = 1) AS NVARCHAR(20)) + N' don cu');
        COMMIT;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK;
        INSERT INTO dbo.NhatKyMigration (TenMigration, Buoc, KetQua, GhiChu)
        VALUES (N'W4-007', N'6-chuyen-doi-don-cu', N'LOI', LEFT(ERROR_MESSAGE(), 500));
        RAISERROR(N'Buoc 6 (chuyen doi don cu) LOI va da ROLLBACK - xem dbo.NhatKyMigration.', 16, 1);
    END CATCH
END
ELSE
    INSERT INTO dbo.NhatKyMigration (TenMigration, Buoc, KetQua, GhiChu)
    VALUES (N'W4-007', N'6-chuyen-doi-don-cu', N'BO_QUA', N'Da chuyen doi truoc do');
GO

/* ---- B7. Ban chup chi tiet don: bat NOT NULL sau khi da dien du ---- */
IF NOT EXISTS (SELECT 1 FROM dbo.ChiTietDonHang WHERE TenSanPham IS NULL OR MauSac IS NULL OR KichThuoc IS NULL)
BEGIN
    IF COLUMNPROPERTY(OBJECT_ID(N'dbo.ChiTietDonHang'), N'TenSanPham', 'AllowsNull') = 1
        ALTER TABLE dbo.ChiTietDonHang ALTER COLUMN TenSanPham NVARCHAR(200) NOT NULL;
    IF COLUMNPROPERTY(OBJECT_ID(N'dbo.ChiTietDonHang'), N'MauSac', 'AllowsNull') = 1
        ALTER TABLE dbo.ChiTietDonHang ALTER COLUMN MauSac NVARCHAR(50) NOT NULL;
    IF COLUMNPROPERTY(OBJECT_ID(N'dbo.ChiTietDonHang'), N'KichThuoc', 'AllowsNull') = 1
        ALTER TABLE dbo.ChiTietDonHang ALTER COLUMN KichThuoc NVARCHAR(30) NOT NULL;
END
GO

/* ---- B8. Cot tinh TongThanhToan = TongTien (tien hang) + PhiVanChuyen ---- */
IF COL_LENGTH(N'dbo.DonHang', N'TongThanhToan') IS NULL
    ALTER TABLE dbo.DonHang ADD TongThanhToan AS (TongTien + PhiVanChuyen) PERSISTED;
GO

/* ---- B9. KHOA NGOAI ---- */
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_DonHang_NVXacNhan' AND parent_object_id = OBJECT_ID(N'dbo.DonHang'))
    ALTER TABLE dbo.DonHang WITH CHECK ADD CONSTRAINT FK_DonHang_NVXacNhan
        FOREIGN KEY (MaNVXacNhan) REFERENCES dbo.NguoiDung(MaNguoiDung);
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = N'FK_DonHang_NVGiao' AND parent_object_id = OBJECT_ID(N'dbo.DonHang'))
    ALTER TABLE dbo.DonHang WITH CHECK ADD CONSTRAINT FK_DonHang_NVGiao
        FOREIGN KEY (MaNVCapNhatGiaoHang) REFERENCES dbo.NguoiDung(MaNguoiDung);
GO

/* ---- B10. CHECK (hop dong trang thai) ----
   Bo gia tri hop le (khop ERD v2):
     PhuongThucThanhToan : COD | Chuyển khoản | Ví điện tử | Thẻ
     TrangThaiThanhToan  : Chưa thanh toán | Đã thanh toán | Hoàn tiền
     TrangThaiXacNhan    : Chờ xác nhận | Đã xác nhận | Từ chối
     TrangThaiGiaoHang   : Chưa giao | Đang chuẩn bị | Đang giao | Đã giao | Giao thất bại
   Don cu (LaDonCu=1) duoc mien yeu cau "co ma nhan vien" vi khong the biet. */
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = N'CK_DonHang_HinhThuc' AND parent_object_id = OBJECT_ID(N'dbo.DonHang'))
    ALTER TABLE dbo.DonHang WITH CHECK ADD CONSTRAINT CK_DonHang_HinhThuc
        CHECK (HinhThucNhanHang IN ('delivery', 'pickup'));
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = N'CK_DonHang_SDT' AND parent_object_id = OBJECT_ID(N'dbo.DonHang'))
    ALTER TABLE dbo.DonHang WITH CHECK ADD CONSTRAINT CK_DonHang_SDT
        CHECK (SdtNguoiNhan IS NULL OR SdtNguoiNhan NOT LIKE '%[^0-9+]%');
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = N'CK_DonHang_Phi' AND parent_object_id = OBJECT_ID(N'dbo.DonHang'))
    ALTER TABLE dbo.DonHang WITH CHECK ADD CONSTRAINT CK_DonHang_Phi
        CHECK (PhiVanChuyen >= 0);
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = N'CK_DonHang_PTTT' AND parent_object_id = OBJECT_ID(N'dbo.DonHang'))
    ALTER TABLE dbo.DonHang WITH CHECK ADD CONSTRAINT CK_DonHang_PTTT
        CHECK (PhuongThucThanhToan IN (N'COD', N'Chuyển khoản', N'Ví điện tử', N'Thẻ'));
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = N'CK_DonHang_TTTT' AND parent_object_id = OBJECT_ID(N'dbo.DonHang'))
    ALTER TABLE dbo.DonHang WITH CHECK ADD CONSTRAINT CK_DonHang_TTTT
        CHECK (TrangThaiThanhToan IN (N'Chưa thanh toán', N'Đã thanh toán', N'Hoàn tiền'));
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = N'CK_DonHang_TTXN' AND parent_object_id = OBJECT_ID(N'dbo.DonHang'))
    ALTER TABLE dbo.DonHang WITH CHECK ADD CONSTRAINT CK_DonHang_TTXN
        CHECK (TrangThaiXacNhan IN (N'Chờ xác nhận', N'Đã xác nhận', N'Từ chối'));
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = N'CK_DonHang_TTGH' AND parent_object_id = OBJECT_ID(N'dbo.DonHang'))
    ALTER TABLE dbo.DonHang WITH CHECK ADD CONSTRAINT CK_DonHang_TTGH
        CHECK (TrangThaiGiaoHang IN (N'Chưa giao', N'Đang chuẩn bị', N'Đang giao', N'Đã giao', N'Giao thất bại'));
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = N'CK_DonHang_DiaChi' AND parent_object_id = OBJECT_ID(N'dbo.DonHang'))
    ALTER TABLE dbo.DonHang WITH CHECK ADD CONSTRAINT CK_DonHang_DiaChi
        CHECK (HinhThucNhanHang = 'pickup' OR DiaChiGiaoHang IS NOT NULL OR LaDonCu = 1);
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = N'CK_DonHang_XacNhan' AND parent_object_id = OBJECT_ID(N'dbo.DonHang'))
    ALTER TABLE dbo.DonHang WITH CHECK ADD CONSTRAINT CK_DonHang_XacNhan CHECK (
        (TrangThaiXacNhan = N'Chờ xác nhận' AND ThoiDiemXacNhan IS NULL AND MaNVXacNhan IS NULL)
     OR (TrangThaiXacNhan <> N'Chờ xác nhận' AND ThoiDiemXacNhan IS NOT NULL
         AND (MaNVXacNhan IS NOT NULL OR LaDonCu = 1)));
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = N'CK_DonHang_GiaoHang' AND parent_object_id = OBJECT_ID(N'dbo.DonHang'))
    ALTER TABLE dbo.DonHang WITH CHECK ADD CONSTRAINT CK_DonHang_GiaoHang CHECK (
        TrangThaiGiaoHang = N'Chưa giao'
     OR (TrangThaiXacNhan = N'Đã xác nhận' AND ThoiDiemCapNhatGiaoHang IS NOT NULL
         AND (MaNVCapNhatGiaoHang IS NOT NULL OR LaDonCu = 1)));
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = N'CK_DonHang_Huy' AND parent_object_id = OBJECT_ID(N'dbo.DonHang'))
    ALTER TABLE dbo.DonHang WITH CHECK ADD CONSTRAINT CK_DonHang_Huy CHECK (
        (DaHuy = 0 AND ThoiDiemHuy IS NULL) OR (DaHuy = 1 AND ThoiDiemHuy IS NOT NULL));
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = N'CK_DonHang_ThoiGian' AND parent_object_id = OBJECT_ID(N'dbo.DonHang'))
    ALTER TABLE dbo.DonHang WITH CHECK ADD CONSTRAINT CK_DonHang_ThoiGian CHECK (
        (ThoiDiemXacNhan IS NULL OR ThoiDiemXacNhan >= NgayDat)
    AND (ThoiDiemHuy IS NULL OR ThoiDiemHuy >= NgayDat));
/* Bat bien ton kho: don da huy / bi tu choi KHONG duoc con giu ton kho (phai hoan truoc/cung luc) */
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = N'CK_DonHang_TruKho' AND parent_object_id = OBJECT_ID(N'dbo.DonHang'))
    ALTER TABLE dbo.DonHang WITH CHECK ADD CONSTRAINT CK_DonHang_TruKho CHECK (
        DaTruKho = 0 OR (DaHuy = 0 AND TrangThaiXacNhan <> N'Từ chối'));
/* Cot TrangThai cu phai luon khop cot moi (code chi ghi qua order_inventory.py) */
IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = N'CK_DonHang_DongBoTrangThaiCu' AND parent_object_id = OBJECT_ID(N'dbo.DonHang'))
    ALTER TABLE dbo.DonHang WITH CHECK ADD CONSTRAINT CK_DonHang_DongBoTrangThaiCu CHECK (
        TrangThai = CASE
            WHEN DaHuy = 1 OR TrangThaiXacNhan = N'Từ chối' THEN N'Đã hủy'
            WHEN TrangThaiGiaoHang = N'Đã giao'             THEN N'Hoàn thành'
            WHEN TrangThaiXacNhan = N'Đã xác nhận'          THEN N'Đã xác nhận'
            ELSE N'Chờ xác nhận' END);
GO

/* ---- B11. Bang GiaoDichThanhToan: moi lan thanh toan cua 1 don (UNIQUE giao dich) ---- */
IF OBJECT_ID(N'dbo.GiaoDichThanhToan', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.GiaoDichThanhToan (
        MaGiaoDich   INT IDENTITY(1,1) CONSTRAINT PK_GiaoDichThanhToan PRIMARY KEY,
        MaDonHang    INT           NOT NULL,
        PhuongThuc   NVARCHAR(30)  NOT NULL,
        SoTien       DECIMAL(18,2) NOT NULL,
        TrangThai    NVARCHAR(20)  NOT NULL CONSTRAINT DF_GDTT_TrangThai DEFAULT N'Chờ xử lý',
        MaThamChieu  VARCHAR(64)   NULL,                 -- ma giao dich ngan hang / vi (neu co)
        GhiChu       NVARCHAR(255) NULL,
        NgayTao      DATETIME2(0)  NOT NULL CONSTRAINT DF_GDTT_NgayTao DEFAULT SYSDATETIME(),
        NgayCapNhat  DATETIME2(0)  NULL,
        CONSTRAINT FK_GDTT_DonHang FOREIGN KEY (MaDonHang) REFERENCES dbo.DonHang(MaDonHang),
        CONSTRAINT CK_GDTT_PhuongThuc CHECK (PhuongThuc IN (N'COD', N'Chuyển khoản', N'Ví điện tử', N'Thẻ')),
        CONSTRAINT CK_GDTT_TrangThai  CHECK (TrangThai IN (N'Chờ xử lý', N'Thành công', N'Thất bại', N'Hoàn tiền')),
        CONSTRAINT CK_GDTT_SoTien     CHECK (SoTien >= 0)
    );
END
GO
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_GDTT_MaDonHang' AND object_id = OBJECT_ID(N'dbo.GiaoDichThanhToan'))
    CREATE INDEX IX_GDTT_MaDonHang ON dbo.GiaoDichThanhToan(MaDonHang);
/* UNIQUE: 1 ma tham chieu ngan hang chi dung 1 lan */
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'UX_GDTT_MaThamChieu' AND object_id = OBJECT_ID(N'dbo.GiaoDichThanhToan'))
    CREATE UNIQUE INDEX UX_GDTT_MaThamChieu ON dbo.GiaoDichThanhToan(MaThamChieu) WHERE MaThamChieu IS NOT NULL;
/* UNIQUE: moi don toi da 1 giao dich THANH CONG (chong thu tien 2 lan) */
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'UX_GDTT_MotThanhCong' AND object_id = OBJECT_ID(N'dbo.GiaoDichThanhToan'))
    CREATE UNIQUE INDEX UX_GDTT_MotThanhCong ON dbo.GiaoDichThanhToan(MaDonHang) WHERE TrangThai = N'Thành công';
GO

/* ---- B12. Bang HoaDon (ERD v2): 1 don - toi da 1 hoa don ---- */
IF OBJECT_ID(N'dbo.HoaDon', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.HoaDon (
        MaHoaDon  INT IDENTITY(1,1) CONSTRAINT PK_HoaDon PRIMARY KEY,
        MaDonHang INT          NOT NULL CONSTRAINT UQ_HoaDon_DonHang UNIQUE,
        SoHoaDon  VARCHAR(30)  NOT NULL CONSTRAINT UQ_HoaDon_So UNIQUE,
        NgayLap   DATETIME2(0) NOT NULL CONSTRAINT DF_HoaDon_NgayLap DEFAULT SYSDATETIME(),
        CONSTRAINT FK_HoaDon_DonHang FOREIGN KEY (MaDonHang) REFERENCES dbo.DonHang(MaDonHang)
    );
END
GO

/* ---- B13. Chi muc truy van trang thai ---- */
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_DonHang_TrangThaiGD' AND object_id = OBJECT_ID(N'dbo.DonHang'))
    CREATE INDEX IX_DonHang_TrangThaiGD ON dbo.DonHang(TrangThaiXacNhan, TrangThaiGiaoHang, TrangThaiThanhToan);
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_DonHang_NVXacNhan' AND object_id = OBJECT_ID(N'dbo.DonHang'))
    CREATE INDEX IX_DonHang_NVXacNhan ON dbo.DonHang(MaNVXacNhan) WHERE MaNVXacNhan IS NOT NULL;
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_DonHang_NVGiao' AND object_id = OBJECT_ID(N'dbo.DonHang'))
    CREATE INDEX IX_DonHang_NVGiao ON dbo.DonHang(MaNVCapNhatGiaoHang) WHERE MaNVCapNhatGiaoHang IS NOT NULL;
GO

INSERT INTO dbo.NhatKyMigration (TenMigration, Buoc, KetQua, GhiChu)
VALUES (N'W4-007', N'13-hoan-tat-script', N'OK', N'Xem khoi kiem tra ben duoi de xac nhan constraint');
GO

/* =====================================================================
   KHOI KIEM TRA (dan ket qua vao bao cao / DB_repro_steps.md)
   ===================================================================== */
-- K1. Don cu khong mat: so dong phai bang so dong luc B2
SELECT N'K1 so dong sau' AS Muc,
       (SELECT COUNT(*) FROM dbo.DonHang) AS DonHang,
       (SELECT COUNT(*) FROM dbo.ChiTietDonHang) AS ChiTietDonHang,
       (SELECT GhiChu FROM dbo.NhatKyMigration WHERE TenMigration = N'W4-007' AND Buoc = N'2-dem-truoc') AS SoDongTruoc;

-- K2. 14 CHECK + 2 FK + 4 UNIQUE = 20 muc phai du (khong dong nao "THIEU")
SELECT t.Ten, CASE WHEN x.name IS NULL THEN N'THIEU' ELSE N'OK' END AS TrangThai
FROM (VALUES
  (N'CK_DonHang_HinhThuc'), (N'CK_DonHang_SDT'), (N'CK_DonHang_Phi'), (N'CK_DonHang_PTTT'),
  (N'CK_DonHang_TTTT'), (N'CK_DonHang_TTXN'), (N'CK_DonHang_TTGH'), (N'CK_DonHang_DiaChi'),
  (N'CK_DonHang_XacNhan'), (N'CK_DonHang_GiaoHang'), (N'CK_DonHang_Huy'), (N'CK_DonHang_ThoiGian'),
  (N'CK_DonHang_TruKho'), (N'CK_DonHang_DongBoTrangThaiCu'),
  (N'FK_DonHang_NVXacNhan'), (N'FK_DonHang_NVGiao'),
  (N'UX_GDTT_MaThamChieu'), (N'UX_GDTT_MotThanhCong'), (N'UQ_HoaDon_DonHang'), (N'UQ_HoaDon_So')
) t(Ten)
LEFT JOIN (SELECT name FROM sys.check_constraints
           UNION ALL SELECT name FROM sys.foreign_keys
           UNION ALL SELECT name FROM sys.indexes WHERE name LIKE N'UX[_]GDTT%'
           UNION ALL SELECT name FROM sys.key_constraints WHERE name LIKE N'UQ[_]HoaDon%') x
       ON x.name = t.Ten
ORDER BY CASE WHEN x.name IS NULL THEN 0 ELSE 1 END, t.Ten;

-- K3. Rang buoc co thoa voi du lieu hien co khong (phai tra ve 0 dong)
DBCC CHECKCONSTRAINTS (N'dbo.DonHang') WITH ALL_CONSTRAINTS, NO_INFOMSGS;
DBCC CHECKCONSTRAINTS (N'dbo.GiaoDichThanhToan') WITH ALL_CONSTRAINTS, NO_INFOMSGS;
DBCC CHECKCONSTRAINTS (N'dbo.ChiTietDonHang') WITH ALL_CONSTRAINTS, NO_INFOMSGS;

-- K4. Bang doi chieu trang thai cu -> moi (mapping thuc te)
SELECT TrangThai AS TrangThaiCu, TrangThaiXacNhan, TrangThaiGiaoHang, DaHuy, COUNT(*) AS SoDon
FROM dbo.DonHang GROUP BY TrangThai, TrangThaiXacNhan, TrangThaiGiaoHang, DaHuy ORDER BY 1;

-- K5. Nhat ky migration
SELECT * FROM dbo.NhatKyMigration WHERE TenMigration = N'W4-007' ORDER BY MaNhatKy;
GO

SET NOEXEC OFF;
GO
