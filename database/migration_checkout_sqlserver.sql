-- MIGRATION KHÔNG PHÁ HUỶ: CHỈ THÊM BẢNG THÔNG TIN GIAO DỊCH.
-- Chạy trên CSDL của dự án sau khi backup, KHÔNG chạy lại schema.sql vì file đó DROP bảng.
-- Chọn đúng database trước khi chạy trong SSMS.
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
END;
GO
