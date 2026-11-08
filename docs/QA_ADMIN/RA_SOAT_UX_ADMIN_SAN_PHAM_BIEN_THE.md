# QA Admin – Sản phẩm và biến thể

Ngày cập nhật: 08/11/2026  
Phạm vi: `/admin/products`, `/admin/products/new`, `/admin/products/<id>/edit`, `/admin/products/<id>/variants`.

## 1. Kết quả rà soát trước khi sửa

| Khu vực | Điểm thiếu/rủi ro tìm thấy | Cập nhật trong bản này |
|---|---|---|
| Bảng sản phẩm | Tổng tồn hiển thị dạng số; chưa có nhãn nổi bật cho tồn 0. Trạng thái ẩn/hiện dùng chung một pill nên khó phân biệt. | Tồn 0 có nhãn `Hết hàng · tồn 0`; trạng thái `Đã ẩn` và `Đang hiển thị` có màu/nhãn riêng; hàng ẩn được làm dịu. |
| Thao tác Ẩn/Hiện | Form đã có hidden CSRF và `data-w3-confirm`, nhưng logic JS cũ gắn listener lên mọi form. | Chỉ xác nhận form/nút được đánh dấu; giữ nguyên POST và hidden `csrf_token`; backend vẫn kiểm tra session/role và CSRF ở `before_request`. |
| Bảng biến thể | Tồn 0 chưa có nhãn cảnh báo; input number chưa khai báo `step=1`; chưa có kiểm tra client rõ ràng cho số nguyên. | Có nhãn hết hàng theo từng biến thể; `min=0`, `step=1`, `data-integer-stock`; JS kiểm tra số nguyên không âm. |
| Lỗi thêm biến thể | Backend redirect sau lỗi nên dữ liệu vừa nhập bị mất. | Lỗi validation/trùng tổ hợp render lại trang với giá trị nhập cũ và thông báo ngay tại form. |
| Lỗi sửa biến thể | Backend redirect khi nhập sai, khiến giá trị sửa bị mất; input gắn ngoài form bằng thuộc tính `form` nên cần lấy controls qua `form.elements`. | Render lại đúng hàng bị lỗi, giữ nguyên size/màu/tồn; JS kiểm cả input liên kết ngoài form. |
| Form sản phẩm | Khi sửa sản phẩm, lỗi validation có thể hiển thị lại dữ liệu cũ thay vì dữ liệu người dùng vừa nhập. | Ưu tiên `request.form` khi POST lỗi để không mất nội dung đã nhập. |
| Phạm vi CSS | Cần tránh tác động trang public, giỏ hàng, checkout. | CSS feedback dùng selector `.w3-admin-page`; không định nghĩa lại style toàn cục `body`, `input`, `button`. |

## 2. Quy tắc bảo vệ vẫn giữ

- Tất cả POST quản trị đi qua kiểm tra CSRF toàn ứng dụng trong `app/routes/public.py` (`prepare_csrf`).
- Form ẩn/hiện, thêm/sửa biến thể vẫn gửi hidden `csrf_token`.
- `admin_only` vẫn yêu cầu đăng nhập và `role == 'Admin'` ở backend.
- Backend xác thực lại tồn kho: chỉ nhận chuỗi chữ số nguyên, không âm, tối đa `2.147.483.647`; không tin riêng kiểm tra JavaScript.
- Ràng buộc DB `CHECK(SoLuongTon >= 0)` và `UNIQUE(MaSanPham,KichThuoc,MauSac)` không bị gỡ bỏ.
- Không thêm thao tác xóa cứng biến thể.

## 3. Ma trận retest

| ID | Thao tác | Kỳ vọng | Trạng thái hiện tại |
|---|---|---|---|
| ADM-UX-01 | Mở danh sách có sản phẩm tổng tồn = 0 | Hiện `Hết hàng · tồn 0` | PASS – template/static check |
| ADM-UX-02 | Mở sản phẩm có biến thể tồn = 0 | Hiện nhãn hết hàng ở đúng dòng biến thể | PASS – template/static check |
| ADM-UX-03 | Sản phẩm HienThi=0 | Hiện nhãn `Đã ẩn`, hàng có phân biệt | PASS – template/static check |
| ADM-UX-04 | Nhấn Ẩn rồi chọn Hủy | Không gửi POST, trạng thái không đổi | NOT RUN – cần browser |
| ADM-UX-05 | Nhấn Ẩn rồi xác nhận | Gửi POST có CSRF, DB chuyển HienThi=0 | NOT RUN – cần Flask/browser/DB |
| ADM-UX-06 | Nhấn Hiện rồi xác nhận | Gửi POST có CSRF, DB chuyển HienThi=1 | NOT RUN – cần Flask/browser/DB |
| ADM-UX-07 | Thêm biến thể tồn `0` | Chấp nhận và lưu đúng số 0 | PASS – parser/DB schema static; route integration NOT RUN |
| ADM-UX-08 | Thêm biến thể tồn `-1`, `1.5`, rỗng, chữ | Chặn; giữ nguyên dữ liệu nhập; thông báo lỗi | PASS – server parser/static; browser NOT RUN |
| ADM-UX-09 | Sửa biến thể tồn `-1` hoặc `1.5` | Chặn; giữ nguyên giá trị trên đúng dòng | PASS – server/template static; browser NOT RUN |
| ADM-UX-10 | Thêm trùng màu + size | DB từ chối; form giữ dữ liệu và báo lỗi | NOT RUN – cần Flask/DB runtime |
| ADM-UX-11 | POST thiếu/sai CSRF | HTTP 400; không thay đổi DB | PASS – kiểm tra cấu trúc middleware; runtime NOT RUN |
| ADM-UX-12 | Nhân viên mở route admin | HTTP 403 | NOT RUN – cần Flask/browser |

## 4. Kết quả kiểm tra được thực hiện trong môi trường đóng gói

- `python scripts/verify_w3_offline.py`: 8/8 PASS.
- `python scripts/verify_admin_ux_offline.py`: 9/9 PASS.
- `python -m py_compile app/routes/admin.py`: PASS.
- `node --check app/static/js/admin_product_feedback.js`: PASS.
- Jinja parse cho các template Admin: PASS.
- ZIP integrity: PASS.

Các kiểm tra trên xác minh cú pháp, hợp đồng giao diện và ràng buộc SQLite. Chúng **không** tương đương kiểm thử tương tác thật trên browser hoặc xác minh SQL Server.

## 5. SQL V2 – BLOCKED

Không tìm thấy file/schema/migration có tên hoặc nội dung được xác định rõ là `SQL V2` trong thư mục `database/`. Dự án hiện có `schema.sql`, `schema_sqlite.sql`, `migrate_w3_visibility_sqlserver.sql` và `migrate_product_images_sqlserver.sql`; đây không được tự suy diễn là SQL V2.

**BLOCKED cho SQL Server** đến khi nhóm cung cấp/chốt SQL V2 và xác minh database test có tối thiểu:

- `SanPham.HienThi` (`BIT NOT NULL`, default 1).
- `BienTheSanPham.SoLuongTon` kiểu số nguyên, `CHECK >= 0`, unique theo sản phẩm + size + màu.
- Bảng `SanPhamHinhAnh` với FK đến `SanPham` nếu sử dụng danh sách ảnh trong trang sửa.

Không chạy `database/schema.sql` trên DB có dữ liệu vì script có `DROP TABLE`. Chỉ áp migration additive trên database test đã backup và được người phụ trách SQL review. Chưa có bằng chứng SQL Server runtime nên không đánh dấu PASS.
