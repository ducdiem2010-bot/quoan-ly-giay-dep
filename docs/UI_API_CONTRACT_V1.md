# UI/API Contract v1 — Tuần 2

| Chức năng | HTTP | URL | Input | Kết quả |
|---|---|---|---|---|
| Danh sách | GET | `/` | `q`: chuỗi tìm kiếm | HTML `index.html`, danh sách DB |
| Theo danh mục | GET | `/category/<int:category_id>` | ID danh mục | HTML `category.html`, lọc tại SQL |
| Chi tiết | GET | `/product/<int:product_id>` | ID sản phẩm | HTML `product_detail.html`; 404 nếu sai ID |
| Thêm giỏ | POST | `/add-to-cart/<int:product_id>` | `csrf_token`, `variant_id`, `quantity` | Lưu session; redirect `/cart` |
| Giỏ hàng | GET | `/cart` | Session cookie | HTML `cart.html` |
| Xóa 1 biến thể | POST | `/cart/remove/<int:variant_id>` | `csrf_token` | Xóa khỏi session |
| Checkout mẫu | GET | `/checkout` | Session | HTML, **không tạo đơn hàng** |
| Đăng nhập | POST | `/login` | `csrf_token`, `email`, `password`, `next` | Session user + role |
| Đăng ký | POST | `/register` | `csrf_token`, `full_name`, `email`, `password` | User vai trò Customer |
| Logout | POST | `/logout` | `csrf_token` | Xóa session |
| Admin | GET | `/admin` | Cookie login Admin | HTML Dashboard, 302 nếu chưa login; 403 nếu sai role |
| Form thêm SP | GET/POST | `/admin/product/add` | `csrf_token`, `name`, `price`, `stock`, `category_id`, `image`, `brand`, `description` | Kiểm tra form, **chưa INSERT** |

## Quy ước template/assets
- Jinja2 dùng `{% extends "base.html" %}`, khối `{% block content %}`. Admin dùng `admin_base.html`.
- Tất cả CSS, JS, ảnh được tải qua `url_for('static', filename=...)`.
- Giao diện session giỏ hàng dùng khóa **MaBienThe dạng chuỗi**; số lượng là số nguyên >0.
- SQL dùng tên cột theo `data_dictionary.md`, không tự đặt `product_id`/`id_sp` khi giao tiếp DB.
- Không sử dụng AJAX/JSON cho các luồng Tuần 2; HTTP form truyền dữ liệu trực tiếp. API JSON là phần công việc sau.
