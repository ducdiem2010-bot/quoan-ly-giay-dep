> Cập nhật bộ nối: đọc [bàn giao backend](TUAN_W4_BACKEND_HANDOFF.md). Đã có factory/adapter tự gắn provider; backend thật và nghiệm thu E2E vẫn chờ bàn giao.

# Bàn giao phần Tuấn — frontend tuần 4

Nguồn: WED nhóm 6(7).zip và sheet Bảng kế hoạch tuần 4 trong Copy of KeHoach_Nhom6_Tuan4_Tuan5.xlsx.
Không có push/merge GitHub hoặc cập nhật Trello trong lần thực hiện này.

## Tình trạng theo nhiệm vụ

| Task | Đã triển khai trong phạm vi Tuấn | Giới hạn nghiệm thu |
| --- | --- | --- |
| W4-004 | Checkout chia phần, thông tin nhận hàng, giao/nhận, COD/chuyển khoản chờ; tóm tắt đơn, responsive, giữ input khi server báo lỗi | Đã chạy với SQLite. SQL Server chưa chạy; chưa có gateway online thật. |
| W4-009 | Trang danh sách/chi tiết đơn, rỗng/lỗi/quyền, timeline, payment failed/cancelled, dialog hủy; controller UI và contract provider | UI/contract đã kiểm tra; tích hợp đơn thật và hủy thật BLOCKED vì chưa có provider. Preview có nhãn và mặc định tắt. |
| W4-014 | Lỗi gần trường, email/phone/name/address/note; pickup không bị minlength địa chỉ ẩn chặn; trạng thái đang gửi, chặn gửi lặp phía client; giữ validation/CSRF server | Các trạng thái payment thất bại/hủy kiểm tra bằng preview. Chưa kiểm sandbox/callback thật. |
| W4-019 | Rà public, desktop/375/768, sửa link thêm SP từ admin tới form lưu thật, CSS mới có phạm vi, kiểm JS/tài nguyên | Lỗi nghiệp vụ ẩn sản phẩm trong giỏ và tồn kho còn tồn, chuyển backend xử lý; không che bằng JS. Không có kết luận SLA tốc độ. |
| W4-024 | Smoke sản phẩm–giỏ–checkout ghi đơn thật trên SQLite; trang kết quả ghi rõ snapshot; tài liệu và minh chứng | Luồng theo dõi/hủy thật và payment online E2E BLOCKED; chưa có SQL Server. Không chốt toàn bộ W4 Done. |

Kết quả thực thi và ảnh nằm trong docs/UI_smoke_w4.md và docs/evidence/w4/.

## File thay đổi có sẵn

- README.md: thêm liên kết tới hướng dẫn W4, giữ nguyên phần lịch sử W2–W3 bên dưới.

- app/__init__.py: thêm cấu hình preview mặc định tắt/provider None, đăng ký blueprint UI. Không đổi cấu hình DB.
- app/templates/base.html: liên kết Đơn của tôi cho Customer, nạp CSS bổ sung.
- app/templates/checkout.html: bố cục, trường nhập, các lỗi client và hướng dẫn theo khả năng backend hiện tại.
- app/static/js/checkout.js: validation, giao/nhận, trạng thái gửi và chống gửi lặp ở client.
- app/static/css/checkout.css: bố cục checkout/result, 375/768/desktop.
- app/templates/checkout_success.html: phản hồi tại thời điểm gửi, không giả làm trạng thái DB hiện tại.
- app/templates/admin/index.html: chỉ sửa link thêm sản phẩm và mô tả cũ. Đây là thay đổi UI dùng chung cần Khải review.

## File code thêm

- app/tuan_w4_ui.py: controller trình bày; chỉ gọi provider đã được backend cấp, không SQL/transaction.
- app/tuan_w4_preview.py: dữ liệu hư cấu cho preview, không được dùng làm provider thật.
- app/templates/orders/list.html, detail.html, unavailable.html, _preview.html.
- app/static/css/orders_w4.css, tuan_w4.css; app/static/js/orders_w4.js.
- tests/test_tuan_w4_ui.py: quyền/CSRF/contract, có ghi rõ provider giả.
- tests/browser_smoke_w4.cjs; tests/run_browser_smoke_w4.py: kiểm tra trình duyệt trên DB test tạm.

Danh sách đầy đủ, hash và phân loại file: TUAN_W4_CHANGES.json.

## Chuyển xử lý backend

| Vấn đề | Người phụ trách | Lý do chưa sửa tại phần Tuấn |
| --- | --- | --- |
| Chưa có list/detail/cancel service đơn | Nghĩa | UI không tự truy vấn toàn bộ đơn hoặc tự viết nghiệp vụ thay backend. |
| Chưa trừ/hoàn tồn, có thể nhận tổng đặt vượt tồn | Minh + Nghĩa | Cần transaction/khóa và quy tắc nghiệp vụ, không thể giải quyết bằng nút disabled. |
| SP thêm giỏ rồi bị ẩn vẫn đặt được | Nghĩa + Minh; Khải phối hợp trạng thái SP | build_cart/create_pending_order chưa kiểm lại HienThi. UI không có nguồn dữ liệu tin cậy để tự che. |
| Chưa có cổng thanh toán/đối soát | Nghĩa + Minh | Cần gateway, credentials và quyết định nhóm. |
| Chưa có admin xác nhận/giao hàng/in hóa đơn | Khải | Ngoài phần frontend khách hàng của Tuấn. |
| Chưa kiểm SQL Server | Minh; Điểm kiểm thử | SQLite không thay thế kết quả SQL Server. |

Các file app/routes.py, app/checkout_service.py, app/db.py, app/admin_w3.py, app/catalog_w3.py và toàn bộ database/*.sql giữ nguyên so với ZIP gốc. Kiểm tra hash trong manifest bàn giao.

## Quyết định về đóng băng code

Không đủ điều kiện kết luận Code Freeze tuần 4 từ bản frontend này. Những blocker trên phải được ghép, chạy lại test và Điểm xác nhận.
