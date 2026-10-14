# Bộ HTML/CSS đã liên kết

Các trang dùng đường dẫn tương đối, không cần Flask. Giữ tất cả file trong cùng một thư mục.

## Cách mở dễ nhất

1. Giải nén Shoes_Store_Da_Lien_Ket.zip.
2. Mở thư mục shoes_store_lien_ket bằng VS Code.
3. Bấm chuột phải vào user.html → Open with Live Server, nếu máy đã có tiện ích Live Server.

Bạn cũng có thể nhấp đúp user.html hoặc index.html để mở trực tiếp bằng trình duyệt.
Khi mở bằng file://, JavaScript truyền dữ liệu giỏ trong đường dẫn giữa các trang.
Trên Live Server, các trang dùng chung giỏ trong localStorage. Đây là cách nên dùng khi nhóm kiểm tra hoặc ghép frontend.

Nếu muốn dùng Python có sẵn, mở Terminal ngay trong thư mục này và chạy:

```powershell
py -m http.server 8000
```

Sau đó mở http://127.0.0.1:8000/user.html. Lệnh này không cần cài pip hoặc Flask.

## Các file và đường dẫn

| File | Vai trò |
| --- | --- |
| user.html | Trang chủ và danh sách sản phẩm mẫu; tìm theo tên/brand |
| index.html | Bản cùng nội dung với user.html, để mở thư mục website mặc định |
| product_detail.html?id=SP001 | Chi tiết Nike Air Force 1 |
| product_detail.html?id=SP002 | Chi tiết Adidas Superstar |
| product_detail.html?id=SP003 | Chi tiết Puma Suede |
| product_detail.html?id=SP004 | Chi tiết Asics Gel |
| cart.html | Giỏ hàng, tăng/giảm/xóa, đơn giá, thành tiền và tổng tiền |
| checkout.html | Kiểm tra giỏ, nhập thông tin và nhận hàng tại cửa hàng |
| user.css, cart.css, product_detail.css | CSS gốc đã bỏ dấu Markdown; user.css thêm thẻ danh sách sản phẩm |
| common.css | Trạng thái nút, thông báo, điều hướng và phần CSS bổ sung dùng chung |
| shop.js | Danh mục mẫu, dữ liệu giỏ và xử lý dùng chung giữa các trang |

Khi chỉnh trang chủ, sửa user.html rồi chép cùng nội dung sang index.html.
Các đường dẫn sản phẩm đều chỉ đến product_detail.html với mã sản phẩm trong tham số id.
shop.js đọc mã đó để hiển thị đúng tên, giá và mô tả.

## Luồng bấm để kiểm tra

1. Mở Trang chủ, bấm một thẻ sản phẩm.
2. Chọn size; thay đổi số lượng; bấm Thêm vào giỏ hàng.
3. Bấm Giỏ hàng ở header, kiểm tra đúng tên, size, đơn giá và thành tiền.
4. Tăng/giảm số lượng hoặc xóa sản phẩm.
5. Bấm Tiến hành thanh toán; sản phẩm, size, số lượng và tổng tiền phải khớp giỏ.
6. Bấm Quay lại giỏ hàng hoặc Trang chủ để chuyển trang.
7. Xóa hết giỏ rồi mở Thanh toán: hiện giỏ trống, không hiện form xác nhận.
8. Nhập tên và số điện thoại để thử kiểm tra thông tin.

Giỏ mẫu ban đầu có Nike Air Force 1 size 42 và Adidas Superstar size 41, mỗi loại một đôi; tổng 4.500.000 VNĐ.
Hai sản phẩm cùng mã và cùng size sẽ gộp số lượng. Khác size là hai dòng riêng.
Số lượng nhập từ 1 đến 99; đây là giới hạn nhập liệu, không phải tồn kho thật.
Các menu cũ trỏ tới login.html/products.html/search.html đã đổi sang trang hiện có; chưa có đăng nhập thật.

## Phạm vi bản mẫu

- Đã bỏ phí vận chuyển, địa chỉ giao hàng và chuyển khoản; nhận hàng và trả tiền tại cửa hàng.
- Hình giày là khung minh họa, thông tin liên hệ và sản phẩm là dữ liệu mẫu.
- Nút Xác nhận thông tin chỉ kiểm tra form, chưa tạo đơn hàng và chưa trừ tồn kho.
- Họ tên, điện thoại, email và ghi chú không lưu vào localStorage hoặc URL.
- Giá lấy từ danh mục mẫu trong shop.js. Khi ghép backend, server phải xác định giá/tồn và xử lý đặt hàng thật.

Muốn khôi phục giỏ mẫu trên Live Server: mở Console tại website, chạy:

```javascript
localStorage.removeItem('shoes_store_lien_ket_v1');
location.reload();
```

Nếu mở file trực tiếp, xóa tham số gio trong đường dẫn rồi xóa khóa localStorage như trên để khôi phục.

## Kiểm tra đã thực hiện

- Cú pháp JavaScript; cấu trúc 5 file HTML và 73 đường dẫn/tài nguyên nội bộ.
- 31 trường hợp logic: tính tiền, tăng/giảm/xóa, gộp cùng size, tách khác size, giỏ trống và truyền dữ liệu sang trang khác.
- Kiểm tra truyền giỏ qua file:// khi localStorage không truy cập được.
- Các trang, CSS và JavaScript tải được qua server tĩnh.

Chưa kiểm tra hiển thị và thao tác bằng trình duyệt thực trong môi trường tạo file.
Nhóm nên chạy luồng bấm phía trên trên máy mình trước khi nghiệm thu giao diện.
