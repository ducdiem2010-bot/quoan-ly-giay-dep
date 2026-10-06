/*
===========================================================
ĐỀ TÀI: WEBSITE QUẢN LÝ BÁN GIÀY DÉP
PHẦN: ERD MỨC LOGIC - NHÁNH GIAO DỊCH (PHIÊN BẢN ĐÃ CẬP NHẬT)
NGƯỜI THỰC HIỆN: Nguyễn Thái Nghĩa

Cấu trúc cập nhật theo yêu cầu nhóm:
- Carts: hỗ trợ khách đã đăng nhập và khách vãng lai.
- Cart_Items: tham chiếu Variant_ID thay vì Product_ID.
- Orders: User_ID có thể NULL; lưu snapshot thông tin khách hàng.
- Order_Details: tham chiếu Variant_ID và lưu Price tại thời điểm đặt.
*/

-- 1. NGƯỜI DÙNG - BẢNG THAM CHIẾU
CREATE TABLE Users (
    User_ID INT IDENTITY(1,1) PRIMARY KEY,
    Full_Name NVARCHAR(100) NOT NULL,
    Email VARCHAR(100) NOT NULL UNIQUE,
    Password_Hash VARCHAR(255) NOT NULL,
    Phone VARCHAR(20),
    Address NVARCHAR(255),
    Created_At DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
GO
-- 2. SẢN PHẨM - BẢNG THAM CHIẾU

CREATE TABLE Products (
    Product_ID INT IDENTITY(1,1) PRIMARY KEY,
    Product_Name NVARCHAR(150) NOT NULL,
    Price DECIMAL(12,2) NOT NULL CHECK (Price >= 0),
    Brand NVARCHAR(100),
    Category NVARCHAR(100),
    Description NVARCHAR(500),
    Created_At DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
GO


-- 3. BIẾN THỂ - BẢNG THAM CHIẾU

CREATE TABLE Variants (
    Variant_ID INT IDENTITY(1,1) PRIMARY KEY,
    Product_ID INT NOT NULL,
    Size VARCHAR(10),
    Color NVARCHAR(50),
    Stock_Quantity INT NOT NULL DEFAULT 0 CHECK (Stock_Quantity >= 0),
    Created_At DATETIME2 NOT NULL DEFAULT SYSDATETIME(),

    CONSTRAINT FK_Variants_Products
        FOREIGN KEY (Product_ID) REFERENCES Products(Product_ID)
);
GO

-- 4. CARTS - GIỎ HÀNG TỔNG
-- User_ID có thể NULL để hỗ trợ khách vãng lai.
-- Session_ID lưu định danh phiên của khách chưa đăng nhập.
-- Ít nhất một trong User_ID hoặc Session_ID phải có giá trị.
CREATE TABLE Carts (
    Cart_ID INT IDENTITY(1,1) PRIMARY KEY,
    User_ID INT NULL,
    Session_ID VARCHAR(100) NULL,
    Created_At DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    Updated_At DATETIME2 NOT NULL DEFAULT SYSDATETIME(),

    CONSTRAINT FK_Carts_Users
        FOREIGN KEY (User_ID) REFERENCES Users(User_ID),

    CONSTRAINT CK_Carts_Owner
        CHECK (User_ID IS NOT NULL OR Session_ID IS NOT NULL)
);
GO


-- 5. CART_ITEMS - CHI TIẾT GIỎ HÀNG
-- Variant_ID trỏ về bảng Variants, không trỏ trực tiếp Products.

CREATE TABLE Cart_Items (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    Cart_ID INT NOT NULL,
    Variant_ID INT NOT NULL,
    Quantity INT NOT NULL CHECK (Quantity > 0),

    CONSTRAINT FK_CartItems_Carts
        FOREIGN KEY (Cart_ID) REFERENCES Carts(Cart_ID),

    CONSTRAINT FK_CartItems_Variants
        FOREIGN KEY (Variant_ID) REFERENCES Variants(Variant_ID),

    CONSTRAINT UQ_CartItems_Cart_Variant
        UNIQUE (Cart_ID, Variant_ID)
);
GO

-- 6. ORDERS - ĐƠN HÀNG
-- User_ID có thể NULL nếu cho phép khách mua không cần tài khoản.
-- customer_* là snapshot tại thời điểm đặt hàng, không phụ thuộc vào
-- việc User thay đổi profile sau này.

CREATE TABLE Orders (
    Order_ID INT IDENTITY(1,1) PRIMARY KEY,
    User_ID INT NULL,
    Customer_Name NVARCHAR(100) NOT NULL,
    Customer_Phone VARCHAR(20) NOT NULL,
    Shipping_Address NVARCHAR(255) NOT NULL,
    Total_Amount DECIMAL(12,2) NOT NULL DEFAULT 0 CHECK (Total_Amount >= 0),
    Payment_Method VARCHAR(50) NOT NULL,
    Payment_Status VARCHAR(30) NOT NULL DEFAULT 'Pending',
    Order_Status VARCHAR(30) NOT NULL DEFAULT 'Pending',
    Created_At DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    Updated_At DATETIME2 NOT NULL DEFAULT SYSDATETIME(),

    CONSTRAINT FK_Orders_Users
        FOREIGN KEY (User_ID) REFERENCES Users(User_ID)
);
GO

-- 7. ORDER_DETAILS - CHI TIẾT ĐƠN HÀNG
-- Variant_ID trỏ về bảng Variants.
-- Price là giá tại thời điểm đặt hàng, không lấy lại giá hiện tại.

CREATE TABLE Order_Details (
    Detail_ID INT IDENTITY(1,1) PRIMARY KEY,
    Order_ID INT NOT NULL,
    Variant_ID INT NOT NULL,
    Quantity INT NOT NULL CHECK (Quantity > 0),
    Price DECIMAL(12,2) NOT NULL CHECK (Price >= 0),

    CONSTRAINT FK_OrderDetails_Orders
        FOREIGN KEY (Order_ID) REFERENCES Orders(Order_ID),

    CONSTRAINT FK_OrderDetails_Variants
        FOREIGN KEY (Variant_ID) REFERENCES Variants(Variant_ID),

    CONSTRAINT UQ_OrderDetails_Order_Variant
        UNIQUE (Order_ID, Variant_ID)
);
GO


-- GHI CHÚ THIẾT KẾ
-- 1. Users 1-N Carts: User_ID trong Carts là NULLABLE.
-- 2. Carts 1-N Cart_Items.
-- 3. Variants 1-N Cart_Items.
-- 4. Users 1-N Orders: User_ID trong Orders là NULLABLE.
-- 5. Orders 1-N Order_Details.
-- 6. Variants 1-N Order_Details.
-- 7. Carts dùng Session_ID cho khách vãng lai.
-- 8. Orders lưu Customer_Name, Customer_Phone, Shipping_Address
--    để giữ snapshot thông tin giao hàng tại thời điểm đặt.
-- 9. Order_Details.Price giữ giá lịch sử tại thời điểm đặt hàng.
