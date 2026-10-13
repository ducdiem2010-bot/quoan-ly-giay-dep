# Nhật ký ghép và nguồn đối chiếu

## Nguồn được đọc
- `Dự án qly giày dép(4).zip`: Flask skeleton gốc `run.py`, `app/__init__.py`, `app/routes.py` chỉ hiện trang trắng; bản SQL Server của Minh; trang HTML/CSS/JS Tuấn; tệp `admin html.htm`.
- `dự án.zip`: `anhtuan.zip` (HTML/CSS/JS giao diện), `ban giay dep (1).tar` (schema/seed/route sản phẩm SQL Server), `gio hang (1).zip` (route giỏ hàng, lỗi 404/500, base Jinja).
- `Công việc tuần 2 (2)(1).xlsx`: 25 đầu việc T2-T6, 1 mốc T7.

## Cách ghép (không chép đè)
1. Giữ 1 Flask application factory (`app/__init__.py`), 1 nơi khai báo route (`app/routes.py`). Loại bỏ khai báo `app=Flask(...)` và `@app.route('/')` bị lặp trong `gio hang/app.py` gốc.
2. Chuyển HTML tĩnh của Tuấn sang template Jinja kế thừa `base.html`; bố cục Header, Navbar, Product card, Footer, Chi tiết, Giỏ hàng, Checkout được giữ về chức năng và tổ chức lại chuẩn Flask.
3. Kết hợp `data.py` từ Minh/Nghĩa và `db.py` thống nhất với 9 bảng từ schema Minh. Truy vấn JOIN + GROUP BY và tham số SQL.
4. Giỏ hàng sử dụng **Flask session**. Không dùng JavaScript localStorage cũ song song vì sẽ tạo 2 giỏ hàng không nhất quán.
5. File `.htm` gắn nhãn Admin trong ZIP thực chất là **trang HTML GitHub đã lưu** (nhận dạng qua tiêu đề HTML GitHub và css data-href github). Không thể sử dụng làm giao diện Admin. Viết `admin_base.html`, dashboard và form Admin mới.
6. Lưu một bản các tệp gốc ở `tai_lieu_nguon/` để nhóm kiểm tra lịch sử, không nhập nhầm vào runtime.
7. Bổ sung SQLite **chỉ để demo chạy ở máy chưa cài SQL Server**. Hướng triển khai nhóm vẫn là SQL Server, dùng `database/schema.sql`, `database/seed.sql` khi chuyển sang SQL Server.

## Giới hạn
- `admin_product_add.html` chỉ kiểm tra form; không lưu SP, đúng mức “chuẩn bị form” Tuần 2.
- `checkout.html` có trường thông tin và tổng tiền nhưng **chưa tạo đơn hàng**; thanh toán trực tiếp tại cửa hàng.
- ERD và Wireframe `.drawio` trong `docs/so_do/` **được tái dựng từ schema/giao diện**, không phải các bản vẽ Figma/Draw.io nguyên gốc do thành viên gửi, vì 2 ZIP không chứa các file nguyên gốc đó.
- `schema.sql` là T-SQL (Microsoft SQL Server), không thể chạy trực tiếp trên SQLite/MySQL. Bản `schema_sqlite.sql` được kiểm thử riêng.
