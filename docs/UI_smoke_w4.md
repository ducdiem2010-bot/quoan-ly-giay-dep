> Nhật ký frontend v1 được giữ lại. Kết quả mới của bộ nối xem [W4_CONNECTION_VERIFICATION.md](W4_CONNECTION_VERIFICATION.md). Ảnh v1 minh họa layout trước khi bổ sung factory; không phải bằng chứng backend thật.

# UI smoke tuần 4 — Tuấn

## Môi trường và giới hạn

SQLite test được tạo mới trong thư mục tạm; không ghi vào DB người dùng. Trình duyệt headless Chromium.
Kiểm tra desktop 1280px, tablet 768px và mobile 375px, cao viewport 900px. Có ảnh chụp toàn trang.
Bootstrap CDN được chủ động chặn để kiểm chứng CSS nội bộ khi offline. Chưa xác minh chế độ CDN online hoặc máy chiếu/điện thoại vật lý.
Không có SQL Server/ODBC trong môi trường kiểm tra. Không có provider đơn hàng hoặc cổng thanh toán online thật.

## Tự kiểm tra bằng thao tác

| TC | Bước thao tác | Kết quả mong đợi |
| --- | --- | --- |
| TC-W4-004-01 | /products → chi tiết SP1 → Đen/39/SL1 → giỏ → checkout | Đúng sản phẩm, size/màu, tạm tính; form đầy đủ; gateway chưa kết nối không chọn được |
| TC-W4-014-01 | Nhập tên A, phone abc, địa chỉ abc rồi gửi | Có lỗi cạnh các trường; không phát POST |
| TC-W4-014-02 | Sau bước lỗi địa chỉ, chuyển sang pickup; nhập tên/phone hợp lệ | Địa chỉ ẩn, disabled, không required; không bị minlength cũ chặn; phí 0 |
| TC-W4-014-03 | Chọn bank_transfer | Hướng dẫn chờ xác nhận, không ghi nhận đã thanh toán |
| TC-W4-014-04 | Gửi form hợp lệ hai lần liên tiếp | JS chỉ cho một POST trong lần gửi hiện tại; backend vẫn phải có chống trùng riêng |
| TC-W4-024-01 | Gửi form trên SQLite test | Lưu đơn chờ; đến /checkout/success, ghi rõ snapshot, chưa thanh toán |
| TC-W4-009-01 | Đăng nhập Customer rồi mở /my-orders khi chưa nối provider | HTTP 503 và thông báo chưa kết nối; không bịa danh sách rỗng |
| TC-W4-009-02 | Mở /my-orders khi chưa đăng nhập | Chuyển đến login, giữ next nội bộ |
| TC-W4-009-03 | Bật preview rồi xem orders/detail/failed/cancelled/empty | Từng trạng thái hiện rõ; tất cả có nhãn dữ liệu mẫu |
| TC-W4-009-04 | Mở dialog hủy trên preview, đóng dialog | Không gửi POST/hủy đơn thật |
| TC-W4-019-01 | Dùng 375/768/1280 cho home/products/search/page2/detail/cart/checkout/orders | Trang không tràn ngang, không có ảnh hỏng, không lỗi JS |
| TC-W4-019-02 | Login Admin → /admin → nút Thêm sản phẩm | Tới /admin/products/new, không tới form W2 chỉ kiểm dữ liệu |

## Minh chứng

- checkout_375.png, checkout_768.png, checkout_1280.png: form thật, giỏ SQLite test, chưa nhập PII.
- checkout_invalid_375.png: lỗi validation thực tế.
- checkout_result_375.png: phản hồi gửi đơn thật trên SQLite test, không phải cổng thanh toán.
- orders_sample_*.png, order_detail_sample_*.png: giao diện dữ liệu mẫu, không dùng làm minh chứng backend đã có.
- payment_failed_sample_*.png, cancelled_sample_*.png, empty_sample_*.png: trạng thái mẫu.
- orders_backend_unavailable_*.png: tình trạng chưa nối provider thực tế.
- before_checkout_375.png, before_checkout_1280.png nếu có: bản ZIP gốc, chụp lại thực tế để đối chiếu.
- browser_results.json: kết quả đo scrollWidth, ảnh, hành vi và lỗi JS.
- unittest_results.txt: log chạy các bài test Python.

Chỉ ảnh/thông tin tồn tại trong thư mục evidence mới được tính là đã thực hiện.
Kết quả định lượng cuối được ghi trong W4_VERIFICATION.md sau khi chạy xong.

## Chạy lại kiểm tra

~~~powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test*.py" -v
~~~

Kiểm tra trình duyệt là tùy chọn, cần Node.js và Playwright đã cài riêng:

~~~text
npm install --no-save --package-lock=false playwright
npx playwright install chromium
python tests/run_browser_smoke_w4.py
~~~

Script tạo server/SQLite test riêng, bật preview chỉ trong test và đóng server khi xong.
Có thể đặt W4_EVIDENCE_DIR để lưu kết quả khác; W4_CHROMIUM_EXECUTABLE khi dùng Chromium đã cài.
FakeProvider trong test chỉ kiểm contract/UI; không thay kết quả hủy đơn/SQL Server/payment thực.

## Chưa được đánh PASS

Theo dõi/hủy đơn thật; xác nhận/giao hàng từ admin; kho và hoàn tồn; callback thanh toán; SQL Server; quyền tra cứu đơn khách vãng lai.
