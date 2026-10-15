/*
===========================================================================
W3-007 & W3-008 - MIGRATION (SQL Server / T-SQL)
Người thực hiện: Nguyễn Thái Nghĩa
Áp dụng lên schema nhánh giao dịch (T2,3) đang có:
    Users, Products, Variants, Carts, Cart_Items, Orders, Order_Details

Giữ nguyên tên bảng/khóa của nhánh giao dịch (theo quy ước mục 10 của báo cáo ERD):
    Variants, Variant_ID, Cart_Items, Order_Details ... KHÔNG đổi.

Việc script làm:
  W3-008: tách 4 cột chữ (Products.Brand, Products.Category, Variants.Color,
          Variants.Size) thành 4 bảng danh mục: Brands, Product_Types, Colors, Sizes.
  W3-007: Variants dùng Color_ID/Size_ID, thêm UNIQUE(Product_ID, Color_ID, Size_ID),
          thêm Is_Active cho Products và Variants, view tính tồn kho.
          (CHECK Stock_Quantity >= 0 đã có sẵn trong Variants, không thêm trùng.)

*/

-- ===========================================================================
-- BƯỚC 0 - KIỂM TRA DỮ LIỆU CŨ (mỗi truy vấn phải trả 0 dòng)
-- ===========================================================================
-- 0.1 Variants thiếu Color hoặc Size
SELECT Variant_ID, Product_ID, Color, Size
FROM Variants
WHERE NULLIF(LTRIM(RTRIM(Color)), '') IS NULL
   OR NULLIF(LTRIM(RTRIM(Size)),  '') IS NULL;

-- 0.2 Products thiếu Brand hoặc Category
SELECT Product_ID, Product_Name, Brand, Category
FROM Products
WHERE NULLIF(LTRIM(RTRIM(Brand)),    '') IS NULL
   OR NULLIF(LTRIM(RTRIM(Category)), '') IS NULL;

-- 0.3 Trùng (Product_ID, Color, Size): sẽ làm UNIQUE ở bước 6 thất bại
SELECT Product_ID, LTRIM(RTRIM(Color)) AS Color, LTRIM(RTRIM(Size)) AS Size, COUNT(*) AS So_dong
FROM Variants
GROUP BY Product_ID, LTRIM(RTRIM(Color)), LTRIM(RTRIM(Size))
HAVING COUNT(*) > 1;
GO

-- ===========================================================================
-- BƯỚC 1 - CHUẨN HÓA KHOẢNG TRẮNG TRONG DỮ LIỆU CŨ
-- Cắt đầu/cuối và gộp nhiều khoảng trắng liên tiếp thành 1.
-- ===========================================================================
UPDATE Products
SET Brand    = LTRIM(RTRIM(REPLACE(REPLACE(REPLACE(Brand,    ' ', '<>'), '><', ''), '<>', ' '))),
    Category = LTRIM(RTRIM(REPLACE(REPLACE(REPLACE(Category, ' ', '<>'), '><', ''), '<>', ' ')));

UPDATE Variants
SET Color = LTRIM(RTRIM(REPLACE(REPLACE(REPLACE(Color, ' ', '<>'), '><', ''), '<>', ' '))),
    Size  = LTRIM(RTRIM(REPLACE(REPLACE(REPLACE(Size,  ' ', '<>'), '><', ''), '<>', ' ')));
GO

-- ===========================================================================
-- BƯỚC 2 - TẠO 4 BẢNG DANH MỤC (W3-008)
-- Code: VARCHAR, collation nhị phân => phân biệt hoa/thường, CHECK chỉ cho A-Z 0-9 _ -
-- Name: UNIQUE (theo collation của DB, mặc định không phân biệt hoa/thường)
-- LƯU Ý: so sánh '=' trong T-SQL bỏ qua khoảng trắng cuối nên CHECK dùng LIKE.
-- ===========================================================================
CREATE TABLE Brands (
    Brand_ID  INT IDENTITY(1,1) CONSTRAINT PK_Brands PRIMARY KEY,
    Code      VARCHAR(30) COLLATE Latin1_General_BIN2 NOT NULL,
    Name      NVARCHAR(100) NOT NULL,
    Is_Active BIT NOT NULL CONSTRAINT DF_Brands_Is_Active DEFAULT 1,
    CONSTRAINT UQ_Brands_Code UNIQUE (Code),
    CONSTRAINT UQ_Brands_Name UNIQUE (Name),
    CONSTRAINT CK_Brands_Code CHECK (LEN(Code) > 0 AND Code NOT LIKE '%[^A-Z0-9_-]%'),
    CONSTRAINT CK_Brands_Name CHECK (LEN(Name) > 0 AND Name NOT LIKE ' %' AND Name NOT LIKE '% ' AND Name NOT LIKE '%  %')
);

CREATE TABLE Product_Types (
    Type_ID   INT IDENTITY(1,1) CONSTRAINT PK_Product_Types PRIMARY KEY,
    Code      VARCHAR(30) COLLATE Latin1_General_BIN2 NOT NULL,
    Name      NVARCHAR(100) NOT NULL,
    Is_Active BIT NOT NULL CONSTRAINT DF_Product_Types_Is_Active DEFAULT 1,
    CONSTRAINT UQ_Product_Types_Code UNIQUE (Code),
    CONSTRAINT UQ_Product_Types_Name UNIQUE (Name),
    CONSTRAINT CK_Product_Types_Code CHECK (LEN(Code) > 0 AND Code NOT LIKE '%[^A-Z0-9_-]%'),
    CONSTRAINT CK_Product_Types_Name CHECK (LEN(Name) > 0 AND Name NOT LIKE ' %' AND Name NOT LIKE '% ' AND Name NOT LIKE '%  %')
);

CREATE TABLE Colors (
    Color_ID  INT IDENTITY(1,1) CONSTRAINT PK_Colors PRIMARY KEY,
    Code      VARCHAR(30) COLLATE Latin1_General_BIN2 NOT NULL,
    Name      NVARCHAR(50) NOT NULL,
    Hex_Code  CHAR(7) NULL,
    Is_Active BIT NOT NULL CONSTRAINT DF_Colors_Is_Active DEFAULT 1,
    CONSTRAINT UQ_Colors_Code UNIQUE (Code),
    CONSTRAINT UQ_Colors_Name UNIQUE (Name),
    CONSTRAINT CK_Colors_Code CHECK (LEN(Code) > 0 AND Code NOT LIKE '%[^A-Z0-9_-]%'),
    CONSTRAINT CK_Colors_Name CHECK (LEN(Name) > 0 AND Name NOT LIKE ' %' AND Name NOT LIKE '% ' AND Name NOT LIKE '%  %'),
    CONSTRAINT CK_Colors_Hex  CHECK (Hex_Code IS NULL OR Hex_Code LIKE '#[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]')
);

CREATE TABLE Sizes (
    Size_ID    INT IDENTITY(1,1) CONSTRAINT PK_Sizes PRIMARY KEY,
    Code       VARCHAR(30) COLLATE Latin1_General_BIN2 NOT NULL,
    Name       NVARCHAR(20) NOT NULL,
    Sort_Order INT NOT NULL CONSTRAINT DF_Sizes_Sort_Order DEFAULT 0,
    Is_Active  BIT NOT NULL CONSTRAINT DF_Sizes_Is_Active DEFAULT 1,
    CONSTRAINT UQ_Sizes_Code UNIQUE (Code),
    CONSTRAINT UQ_Sizes_Name UNIQUE (Name),
    CONSTRAINT CK_Sizes_Code CHECK (LEN(Code) > 0 AND Code NOT LIKE '%[^A-Z0-9_-]%'),
    CONSTRAINT CK_Sizes_Name CHECK (LEN(Name) > 0 AND Name NOT LIKE ' %' AND Name NOT LIKE '% ' AND Name NOT LIKE '%  %')
);
GO

-- ===========================================================================
-- BƯỚC 3 - ĐỔ DỮ LIỆU CŨ VÀO DANH MỤC MỚI
-- Mỗi bảng: (a) chèn tên duy nhất với Code tạm, (b) đặt Code thật.
-- Code thật = tên viết HOA, thay ' ' và '.' bằng '_'. Nếu tên có dấu / ký tự lạ
-- hoặc bị trùng code thì dùng mã dự phòng (BRAND_001, TYPE_001, ...).
-- Admin có thể đổi Code sau khi migrate xong.
-- ===========================================================================

-- 3.1 Brands
INSERT INTO Brands (Code, Name)
SELECT 'TMP_' + CAST(ROW_NUMBER() OVER (ORDER BY n.Name) AS VARCHAR(10)), n.Name
FROM (SELECT DISTINCT Brand AS Name FROM Products WHERE Brand IS NOT NULL AND Brand <> '') AS n;

;WITH c AS (
    SELECT Brand_ID, Code,
           UPPER(REPLACE(REPLACE(Name, ' ', '_'), '.', '_')) AS Cand,
           ROW_NUMBER() OVER (PARTITION BY UPPER(REPLACE(REPLACE(Name, ' ', '_'), '.', '_')) ORDER BY Brand_ID) AS rn
    FROM Brands
)
UPDATE c
SET Code = CASE WHEN rn = 1 AND LEN(Cand) <= 30
                 AND Cand COLLATE Latin1_General_BIN2 NOT LIKE '%[^A-Z0-9_-]%'
                THEN Cand
                ELSE 'BRAND_' + RIGHT('000' + CAST(Brand_ID AS VARCHAR(10)), 3) END;

-- 3.2 Product_Types (từ Products.Category)
INSERT INTO Product_Types (Code, Name)
SELECT 'TMP_' + CAST(ROW_NUMBER() OVER (ORDER BY n.Name) AS VARCHAR(10)), n.Name
FROM (SELECT DISTINCT Category AS Name FROM Products WHERE Category IS NOT NULL AND Category <> '') AS n;

;WITH c AS (
    SELECT Type_ID, Code,
           UPPER(REPLACE(REPLACE(Name, ' ', '_'), '.', '_')) AS Cand,
           ROW_NUMBER() OVER (PARTITION BY UPPER(REPLACE(REPLACE(Name, ' ', '_'), '.', '_')) ORDER BY Type_ID) AS rn
    FROM Product_Types
)
UPDATE c
SET Code = CASE WHEN rn = 1 AND LEN(Cand) <= 30
                 AND Cand COLLATE Latin1_General_BIN2 NOT LIKE '%[^A-Z0-9_-]%'
                THEN Cand
                ELSE 'TYPE_' + RIGHT('000' + CAST(Type_ID AS VARCHAR(10)), 3) END;

-- 3.3 Colors
INSERT INTO Colors (Code, Name)
SELECT 'TMP_' + CAST(ROW_NUMBER() OVER (ORDER BY n.Name) AS VARCHAR(10)), n.Name
FROM (SELECT DISTINCT Color AS Name FROM Variants WHERE Color IS NOT NULL AND Color <> '') AS n;

;WITH c AS (
    SELECT Color_ID, Code,
           UPPER(REPLACE(REPLACE(Name, ' ', '_'), '.', '_')) AS Cand,
           ROW_NUMBER() OVER (PARTITION BY UPPER(REPLACE(REPLACE(Name, ' ', '_'), '.', '_')) ORDER BY Color_ID) AS rn
    FROM Colors
)
UPDATE c
SET Code = CASE WHEN rn = 1 AND LEN(Cand) <= 30
                 AND Cand COLLATE Latin1_General_BIN2 NOT LIKE '%[^A-Z0-9_-]%'
                THEN Cand
                ELSE 'COLOR_' + RIGHT('000' + CAST(Color_ID AS VARCHAR(10)), 3) END;

-- 3.4 Sizes (Sort_Order: size số xếp tăng dần trước, size chữ xếp sau theo tên; chỉnh tay nếu cần)
INSERT INTO Sizes (Code, Name, Sort_Order)
SELECT 'TMP_' + CAST(ROW_NUMBER() OVER (ORDER BY CASE WHEN TRY_CAST(n.Name AS DECIMAL(5,1)) IS NULL THEN 1 ELSE 0 END,
                                                 TRY_CAST(n.Name AS DECIMAL(5,1)), n.Name) AS VARCHAR(10)),
       n.Name,
       ROW_NUMBER() OVER (ORDER BY CASE WHEN TRY_CAST(n.Name AS DECIMAL(5,1)) IS NULL THEN 1 ELSE 0 END,
                                   TRY_CAST(n.Name AS DECIMAL(5,1)), n.Name) * 10
FROM (SELECT DISTINCT Size AS Name FROM Variants WHERE Size IS NOT NULL AND Size <> '') AS n;

;WITH c AS (
    SELECT Size_ID, Code,
           UPPER(REPLACE(REPLACE(Name, ' ', '_'), '.', '_')) AS Cand,
           ROW_NUMBER() OVER (PARTITION BY UPPER(REPLACE(REPLACE(Name, ' ', '_'), '.', '_')) ORDER BY Size_ID) AS rn
    FROM Sizes
)
UPDATE c
SET Code = CASE WHEN rn = 1 AND LEN(Cand) <= 30
                 AND Cand COLLATE Latin1_General_BIN2 NOT LIKE '%[^A-Z0-9_-]%'
                THEN Cand
                ELSE 'SIZE_' + RIGHT('000' + CAST(Size_ID AS VARCHAR(10)), 3) END;
GO

-- ===========================================================================
-- BƯỚC 4 - THÊM CỘT MỚI VÀO Products VÀ Variants
-- ===========================================================================
ALTER TABLE Products ADD
    Brand_ID  INT NULL,
    Type_ID   INT NULL,
    Is_Active BIT NOT NULL CONSTRAINT DF_Products_Is_Active DEFAULT 1;

ALTER TABLE Variants ADD
    Color_ID  INT NULL,
    Size_ID   INT NULL,
    Is_Active BIT NOT NULL CONSTRAINT DF_Variants_Is_Active DEFAULT 1;
GO

-- ===========================================================================
-- BƯỚC 5 - GẮN KHÓA NGOẠI CHO DỮ LIỆU CŨ
-- ===========================================================================
UPDATE p SET p.Brand_ID = b.Brand_ID FROM Products p JOIN Brands        b ON b.Name = p.Brand;
UPDATE p SET p.Type_ID  = t.Type_ID  FROM Products p JOIN Product_Types t ON t.Name = p.Category;
UPDATE v SET v.Color_ID = c.Color_ID FROM Variants v JOIN Colors        c ON c.Name = v.Color;
UPDATE v SET v.Size_ID  = s.Size_ID  FROM Variants v JOIN Sizes         s ON s.Name = v.Size;

-- Kiểm tra: phải trả 0 dòng trước khi chạy BƯỚC 6
SELECT 'Products chưa có Brand_ID/Type_ID' AS Loi, Product_ID AS Id FROM Products WHERE Brand_ID IS NULL OR Type_ID IS NULL
UNION ALL
SELECT 'Variants chưa có Color_ID/Size_ID', Variant_ID FROM Variants WHERE Color_ID IS NULL OR Size_ID IS NULL;
GO

-- ===========================================================================
-- BƯỚC 6 - SIẾT RÀNG BUỘC (W3-007 + W3-008) rồi bỏ 4 cột chữ cũ
-- Chạy trong 1 transaction: lỗi ở đâu thì rollback toàn bộ khối này.
-- ===========================================================================
SET XACT_ABORT ON;
BEGIN TRAN;

ALTER TABLE Products ALTER COLUMN Brand_ID INT NOT NULL;
ALTER TABLE Products ALTER COLUMN Type_ID  INT NOT NULL;
ALTER TABLE Variants ALTER COLUMN Color_ID INT NOT NULL;
ALTER TABLE Variants ALTER COLUMN Size_ID  INT NOT NULL;

ALTER TABLE Products ADD
    CONSTRAINT FK_Products_Brands        FOREIGN KEY (Brand_ID) REFERENCES Brands(Brand_ID),
    CONSTRAINT FK_Products_Product_Types FOREIGN KEY (Type_ID)  REFERENCES Product_Types(Type_ID);

ALTER TABLE Variants ADD
    CONSTRAINT FK_Variants_Colors FOREIGN KEY (Color_ID) REFERENCES Colors(Color_ID),
    CONSTRAINT FK_Variants_Sizes  FOREIGN KEY (Size_ID)  REFERENCES Sizes(Size_ID),
    CONSTRAINT UQ_Variants_Product_Color_Size UNIQUE (Product_ID, Color_ID, Size_ID);

ALTER TABLE Products DROP COLUMN Brand, Category;
ALTER TABLE Variants DROP COLUMN Color, Size;

COMMIT;
SET XACT_ABORT OFF;
GO

-- ===========================================================================
-- BƯỚC 7 - CHỈ MỤC HỖ TRỢ LỌC (W3-005 của Minh sẽ lọc theo các cột này)
-- UQ_Variants_Product_Color_Size đã có Product_ID đứng đầu nên không cần chỉ mục riêng cho FK Product_ID.
-- ===========================================================================
CREATE INDEX IX_Products_Brand_Type ON Products (Brand_ID, Type_ID) INCLUDE (Price, Is_Active);
CREATE INDEX IX_Variants_Color_Size ON Variants (Color_ID, Size_ID) INCLUDE (Product_ID, Stock_Quantity, Is_Active);
GO

-- ===========================================================================
-- BƯỚC 8 - VIEW TỒN KHO THEO SẢN PHẨM
-- Chỉ tính biến thể đang hoạt động. Sản phẩm không có biến thể active = hết tồn.
-- ===========================================================================
CREATE VIEW vw_Product_Stock AS
SELECT p.Product_ID,
       COALESCE(SUM(CASE WHEN v.Is_Active = 1 THEN v.Stock_Quantity END), 0) AS Total_Stock,
       CASE WHEN COALESCE(SUM(CASE WHEN v.Is_Active = 1 THEN v.Stock_Quantity END), 0) = 0
            THEN 1 ELSE 0 END AS Is_Out_Of_Stock
FROM Products p
LEFT JOIN Variants v ON v.Product_ID = p.Product_ID
GROUP BY p.Product_ID;
GO

-- ===========================================================================
-- KIỂM THỬ - mọi dòng "OK" nghĩa là DB đã từ chối đúng. Cuối cùng ROLLBACK.
-- Dòng "FAIL" nghĩa là câu lệnh sai lại được chấp nhận => ràng buộc thiếu.
-- ===========================================================================
BEGIN TRAN;

DECLARE @b INT, @t INT, @c INT, @s INT, @s2 INT, @p INT;

INSERT INTO Brands        (Code, Name)             VALUES ('TEST_B', N'Test Brand'); SET @b = SCOPE_IDENTITY();
INSERT INTO Product_Types (Code, Name)             VALUES ('TEST_T', N'Test Type');  SET @t = SCOPE_IDENTITY();
INSERT INTO Colors        (Code, Name)             VALUES ('TEST_C', N'Test Color'); SET @c = SCOPE_IDENTITY();
INSERT INTO Sizes         (Code, Name, Sort_Order) VALUES ('TEST_S', N'T99', 9999);  SET @s = SCOPE_IDENTITY();
INSERT INTO Sizes         (Code, Name, Sort_Order) VALUES ('TEST_S2', N'T98', 9998); SET @s2 = SCOPE_IDENTITY();
INSERT INTO Products (Product_Name, Price, Brand_ID, Type_ID) VALUES (N'SP test', 100000, @b, @t); SET @p = SCOPE_IDENTITY();
INSERT INTO Variants (Product_ID, Color_ID, Size_ID, Stock_Quantity) VALUES (@p, @c, @s, 5);   -- hợp lệ
PRINT 'Du lieu mau hop le: da chen.';

-- T1: trùng (Product, Color, Size)
BEGIN TRY INSERT INTO Variants (Product_ID, Color_ID, Size_ID, Stock_Quantity) VALUES (@p, @c, @s, 1); PRINT 'T1 FAIL';
END TRY BEGIN CATCH PRINT 'T1 OK  - ' + LEFT(ERROR_MESSAGE(), 90); END CATCH;

-- T2: tồn âm (dùng size khác để không bị UNIQUE chặn trước)
BEGIN TRY INSERT INTO Variants (Product_ID, Color_ID, Size_ID, Stock_Quantity) VALUES (@p, @c, @s2, -1); PRINT 'T2 FAIL';
END TRY BEGIN CATCH PRINT 'T2 OK  - ' + LEFT(ERROR_MESSAGE(), 90); END CATCH;

-- T3: Color_ID không tồn tại
BEGIN TRY INSERT INTO Variants (Product_ID, Color_ID, Size_ID, Stock_Quantity) VALUES (@p, -1, @s, 1); PRINT 'T3 FAIL';
END TRY BEGIN CATCH PRINT 'T3 OK  - ' + LEFT(ERROR_MESSAGE(), 90); END CATCH;

-- T4: Size_ID không tồn tại
BEGIN TRY INSERT INTO Variants (Product_ID, Color_ID, Size_ID, Stock_Quantity) VALUES (@p, @c, -1, 1); PRINT 'T4 FAIL';
END TRY BEGIN CATCH PRINT 'T4 OK  - ' + LEFT(ERROR_MESSAGE(), 90); END CATCH;

-- T5: Product_ID không tồn tại
BEGIN TRY INSERT INTO Variants (Product_ID, Color_ID, Size_ID, Stock_Quantity) VALUES (-1, @c, @s, 1); PRINT 'T5 FAIL';
END TRY BEGIN CATCH PRINT 'T5 OK  - ' + LEFT(ERROR_MESSAGE(), 90); END CATCH;

-- T6: giá âm
BEGIN TRY INSERT INTO Products (Product_Name, Price, Brand_ID, Type_ID) VALUES (N'SP gia am', -1, @b, @t); PRINT 'T6 FAIL';
END TRY BEGIN CATCH PRINT 'T6 OK  - ' + LEFT(ERROR_MESSAGE(), 90); END CATCH;

-- T7: xóa Color đang được dùng
BEGIN TRY DELETE FROM Colors WHERE Color_ID = @c; PRINT 'T7 FAIL';
END TRY BEGIN CATCH PRINT 'T7 OK  - ' + LEFT(ERROR_MESSAGE(), 90); END CATCH;

-- T8: trùng tên danh mục (khác hoa/thường)
BEGIN TRY INSERT INTO Brands (Code, Name) VALUES ('TEST_B2', N'test brand'); PRINT 'T8 FAIL (kiem tra collation DB co phan biet hoa/thuong khong)';
END TRY BEGIN CATCH PRINT 'T8 OK  - ' + LEFT(ERROR_MESSAGE(), 90); END CATCH;

-- T9: tên có khoảng trắng thừa ở cuối
BEGIN TRY INSERT INTO Brands (Code, Name) VALUES ('TEST_B3', N'Abc '); PRINT 'T9 FAIL';
END TRY BEGIN CATCH PRINT 'T9 OK  - ' + LEFT(ERROR_MESSAGE(), 90); END CATCH;

-- T10: code viết thường
BEGIN TRY INSERT INTO Brands (Code, Name) VALUES ('abc', N'Abc'); PRINT 'T10 FAIL';
END TRY BEGIN CATCH PRINT 'T10 OK - ' + LEFT(ERROR_MESSAGE(), 90); END CATCH;

-- T11: hex màu sai
BEGIN TRY INSERT INTO Colors (Code, Name, Hex_Code) VALUES ('TEST_C2', N'Mau loi', '#ZZZZZZ'); PRINT 'T11 FAIL';
END TRY BEGIN CATCH PRINT 'T11 OK - ' + LEFT(ERROR_MESSAGE(), 90); END CATCH;

ROLLBACK;
PRINT 'Da ROLLBACK - khong con du lieu test.';
GO