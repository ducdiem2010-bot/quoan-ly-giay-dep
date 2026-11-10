/* =====================================================================
   rollback_migration_w4_giao_dich_sqlserver.sql   (W4-007 - ROLLBACK PHU)
   Hoan tac CAU TRUC ma migration_w4_giao_dich_sqlserver.sql da them.

   QUAN TRONG
   - Cach hoan tac DAY DU (ca du lieu) la RESTORE tu file .bak da sao luu truoc migration:
        RESTORE DATABASE [TEN_DB_TEST] FROM DISK = N'C:\Backup\TEN_DB_TEST_truoc_W4_007.bak'
          WITH REPLACE;      -- chi voi DB TEST; dong ket noi khac truoc khi chay
   - Script nay chi go cot/constraint/bang MOI. Thong tin chi ton tai o cot moi se MAT:
     ten/sdt/dia chi nguoi nhan, trang thai xac nhan/giao hang, ban chup chi tiet don,
     giao dich thanh toan, hoa don. Du lieu goc (TrangThai, TongTien, ThongTinGiaoDich) van con.
   - Mac dinh script DUNG neu GiaoDichThanhToan / HoaDon da co du lieu. Muon go van,
     doi @CHO_PHEP_MAT_DU_LIEU = 1 (chi tren DB test).
   - KHONG dong vao BienTheSanPham.SoLuongTon: ton kho da tru/hoan van giu nguyen.
   ===================================================================== */
SET NOCOUNT ON;
SET QUOTED_IDENTIFIER ON;
GO
IF DB_NAME() IN (N'master', N'model', N'msdb', N'tempdb') OR OBJECT_ID(N'dbo.DonHang', N'U') IS NULL
BEGIN
    RAISERROR(N'DUNG: chua chon dung database test.', 16, 1);
    SET NOEXEC ON;
END
GO

DECLARE @CHO_PHEP_MAT_DU_LIEU BIT = 0;   -- doi thanh 1 neu chap nhan mat du lieu bang moi

IF @CHO_PHEP_MAT_DU_LIEU = 0
   AND ( (OBJECT_ID(N'dbo.GiaoDichThanhToan', N'U') IS NOT NULL AND EXISTS (SELECT 1 FROM dbo.GiaoDichThanhToan))
      OR (OBJECT_ID(N'dbo.HoaDon', N'U') IS NOT NULL AND EXISTS (SELECT 1 FROM dbo.HoaDon)) )
BEGIN
    RAISERROR(N'DUNG: GiaoDichThanhToan/HoaDon da co du lieu. Backup roi dat @CHO_PHEP_MAT_DU_LIEU = 1 neu van muon go.', 16, 1);
    RETURN;
END

BEGIN TRY
    BEGIN TRAN;

    -- 1) Bang moi
    IF OBJECT_ID(N'dbo.HoaDon', N'U') IS NOT NULL            DROP TABLE dbo.HoaDon;
    IF OBJECT_ID(N'dbo.GiaoDichThanhToan', N'U') IS NOT NULL DROP TABLE dbo.GiaoDichThanhToan;

    -- 2) CHECK + FK tren DonHang (ten co dinh)
    DECLARE @ten SYSNAME, @sql NVARCHAR(400);
    DECLARE c CURSOR LOCAL FAST_FORWARD FOR
        SELECT name FROM sys.check_constraints
        WHERE parent_object_id = OBJECT_ID(N'dbo.DonHang')
          AND name IN (N'CK_DonHang_HinhThuc', N'CK_DonHang_SDT', N'CK_DonHang_Phi', N'CK_DonHang_PTTT',
                       N'CK_DonHang_TTTT', N'CK_DonHang_TTXN', N'CK_DonHang_TTGH', N'CK_DonHang_DiaChi',
                       N'CK_DonHang_XacNhan', N'CK_DonHang_GiaoHang', N'CK_DonHang_Huy', N'CK_DonHang_ThoiGian',
                       N'CK_DonHang_TruKho', N'CK_DonHang_DongBoTrangThaiCu')
        UNION ALL
        SELECT name FROM sys.foreign_keys
        WHERE parent_object_id = OBJECT_ID(N'dbo.DonHang') AND name IN (N'FK_DonHang_NVXacNhan', N'FK_DonHang_NVGiao');
    OPEN c; FETCH NEXT FROM c INTO @ten;
    WHILE @@FETCH_STATUS = 0
    BEGIN
        SET @sql = N'ALTER TABLE dbo.DonHang DROP CONSTRAINT ' + QUOTENAME(@ten);
        EXEC sys.sp_executesql @sql;
        FETCH NEXT FROM c INTO @ten;
    END
    CLOSE c; DEALLOCATE c;

    -- 3) Chi muc
    IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_DonHang_TrangThaiGD' AND object_id = OBJECT_ID(N'dbo.DonHang')) DROP INDEX IX_DonHang_TrangThaiGD ON dbo.DonHang;
    IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_DonHang_NVXacNhan'   AND object_id = OBJECT_ID(N'dbo.DonHang')) DROP INDEX IX_DonHang_NVXacNhan ON dbo.DonHang;
    IF EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_DonHang_NVGiao'      AND object_id = OBJECT_ID(N'dbo.DonHang')) DROP INDEX IX_DonHang_NVGiao ON dbo.DonHang;

    -- 4) Cot tinh phai go truoc cot goc
    IF COL_LENGTH(N'dbo.DonHang', N'TongThanhToan') IS NOT NULL ALTER TABLE dbo.DonHang DROP COLUMN TongThanhToan;

    -- 5) Default constraint roi cot (DonHang)
    DECLARE @df TABLE (Cot SYSNAME, Df SYSNAME);
    INSERT INTO @df VALUES
      (N'LaDonCu', N'DF_DonHang_LaDonCu'), (N'HinhThucNhanHang', N'DF_DonHang_HinhThuc'), (N'PhiVanChuyen', N'DF_DonHang_Phi'),
      (N'PhuongThucThanhToan', N'DF_DonHang_PTTT'), (N'TrangThaiThanhToan', N'DF_DonHang_TTTT'),
      (N'TrangThaiXacNhan', N'DF_DonHang_TTXN'), (N'TrangThaiGiaoHang', N'DF_DonHang_TTGH'),
      (N'DaHuy', N'DF_DonHang_DaHuy'), (N'DaTruKho', N'DF_DonHang_DaTruKho');
    DECLARE @d SYSNAME;
    DECLARE c2 CURSOR LOCAL FAST_FORWARD FOR
        SELECT Df FROM @df WHERE EXISTS (SELECT 1 FROM sys.default_constraints WHERE name = Df AND parent_object_id = OBJECT_ID(N'dbo.DonHang'));
    OPEN c2; FETCH NEXT FROM c2 INTO @d;
    WHILE @@FETCH_STATUS = 0
    BEGIN
        SET @sql = N'ALTER TABLE dbo.DonHang DROP CONSTRAINT ' + QUOTENAME(@d);
        EXEC sys.sp_executesql @sql;
        FETCH NEXT FROM c2 INTO @d;
    END
    CLOSE c2; DEALLOCATE c2;

    DECLARE @cot SYSNAME;
    DECLARE c3 CURSOR LOCAL FAST_FORWARD FOR
        SELECT name FROM sys.columns
        WHERE object_id = OBJECT_ID(N'dbo.DonHang')
          AND name IN (N'LaDonCu', N'HinhThucNhanHang', N'TenNguoiNhan', N'SdtNguoiNhan', N'DiaChiGiaoHang', N'PhiVanChuyen',
                       N'PhuongThucThanhToan', N'TrangThaiThanhToan', N'TrangThaiXacNhan', N'MaNVXacNhan', N'ThoiDiemXacNhan',
                       N'TrangThaiGiaoHang', N'MaNVCapNhatGiaoHang', N'ThoiDiemCapNhatGiaoHang', N'DaHuy', N'ThoiDiemHuy', N'DaTruKho');
    OPEN c3; FETCH NEXT FROM c3 INTO @cot;
    WHILE @@FETCH_STATUS = 0
    BEGIN
        SET @sql = N'ALTER TABLE dbo.DonHang DROP COLUMN ' + QUOTENAME(@cot);
        EXEC sys.sp_executesql @sql;
        FETCH NEXT FROM c3 INTO @cot;
    END
    CLOSE c3; DEALLOCATE c3;

    -- 6) Ban chup tren ChiTietDonHang
    IF COL_LENGTH(N'dbo.ChiTietDonHang', N'TenSanPham') IS NOT NULL ALTER TABLE dbo.ChiTietDonHang DROP COLUMN TenSanPham;
    IF COL_LENGTH(N'dbo.ChiTietDonHang', N'MauSac')     IS NOT NULL ALTER TABLE dbo.ChiTietDonHang DROP COLUMN MauSac;
    IF COL_LENGTH(N'dbo.ChiTietDonHang', N'KichThuoc')  IS NOT NULL ALTER TABLE dbo.ChiTietDonHang DROP COLUMN KichThuoc;

    -- 7) Cho phep chay lai migration: danh dau buoc chuyen doi da bi hoan tac
    IF OBJECT_ID(N'dbo.NhatKyMigration', N'U') IS NOT NULL
    BEGIN
        DELETE FROM dbo.NhatKyMigration WHERE TenMigration = N'W4-007' AND Buoc IN (N'2-dem-truoc', N'6-chuyen-doi-don-cu');
        INSERT INTO dbo.NhatKyMigration (TenMigration, Buoc, KetQua, GhiChu)
        VALUES (N'W4-007', N'rollback-cau-truc', N'OK', N'Da go cot/constraint/bang moi cua W4-007');
    END

    COMMIT;
    PRINT N'Rollback cau truc W4-007 hoan tat.';
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK;
    PRINT N'Rollback LOI va da hoan tac: ' + ERROR_MESSAGE();
    THROW;
END CATCH
GO
SET NOEXEC OFF;
GO

-- Kiem tra sau rollback: khong con cot moi
SELECT name FROM sys.columns
WHERE object_id = OBJECT_ID(N'dbo.DonHang')
  AND name IN (N'DaTruKho', N'TrangThaiXacNhan', N'TongThanhToan', N'LaDonCu');   -- ky vong 0 dong
GO
