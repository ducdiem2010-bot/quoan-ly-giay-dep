# BÁO CÁO KIỂM TOÁN ĐỘ BAO PHỦ CHỨC NĂNG (W3-059)

**Người thực hiện:** Điểm (Nhóm trưởng)
**Tổng số chức năng theo dõi:** 49
- **Đã xác minh kiểm thử (Verified):** 38
- **Bị chặn do thiếu backend tuần 3 (Blocked):** 9
- **Chưa kiểm thử (Not run):** 2

| Mã FN | Mã W3 | Người phụ trách | Chức năng | File code | Bài test tương ứng | Trạng thái |
|---|---|---|---|---|---|---|
| F01 | W3-004 | Minh | Xem danh sách sản phẩm trang chủ | `app/routes.py` | `test_d29_01_guest_view_product_list` | **VERIFIED (Đã có test & code)** |
| F02 | W3-004 | Minh | Lọc danh mục giày nam | `app/data.py` | `test_category_filter` | **VERIFIED (Đã có test & code)** |
| F03 | W3-004 | Minh | Lọc danh mục giày nữ | `app/data.py` | `test_category_filter` | **VERIFIED (Đã có test & code)** |
| F04 | W3-004 | Minh | Lọc danh mục dép & sandal | `app/data.py` | `test_category_filter` | **VERIFIED (Đã có test & code)** |
| F05 | W3-004 | Minh | Ẩn sản phẩm dừng bán khỏi public (A02) | `app/data.py` | `test_d29_02_hidden_product_not_shown` | **VERIFIED (Đã có test & code)** |
| F06 | W3-005 | Minh | Tìm kiếm sản phẩm theo tên chính xác | `app/data.py` | `test_d29_03_search_product_by_name` | **VERIFIED (Đã có test & code)** |
| F07 | W3-005 | Minh | Tìm kiếm sản phẩm theo từ khóa gần đúng | `app/data.py` | `test_02_search_by_name` | **VERIFIED (Đã có test & code)** |
| F08 | W3-005 | Minh | Tìm kiếm không dấu tiếng Việt | `app/data.py` | `CHƯA_TEST` | **NOT RUN (Chưa viết test)** |
| F09 | W3-005 | Minh | Tìm kiếm từ khóa không tồn tại | `app/data.py` | `test_d29_04_search_non_existent_keyword` | **VERIFIED (Đã có test & code)** |
| F10 | W3-005 | Minh | Tìm kiếm ký tự đặc biệt chống SQL Injection | `app/data.py` | `test_09_sql_injection_defense_parameterized` | **VERIFIED (Đã có test & code)** |
| F11 | W3-005 | Minh | Lọc thương hiệu (Nike, Adidas, Converse...) | `app/data.py` | `CHƯA_CODE` | **BLOCKED (Thiếu backend)** |
| F12 | W3-005 | Minh | Lọc khoảng giá (price_min, price_max) | `app/data.py` | `CHƯA_CODE` | **BLOCKED (Thiếu backend)** |
| F13 | W3-005 | Minh | Lọc giới tính (Nam, Nữ, Unisex) | `app/data.py` | `CHƯA_CODE` | **BLOCKED (Thiếu backend)** |
| F14 | W3-005 | Minh | Sắp xếp theo giá tăng dần | `app/data.py` | `CHƯA_CODE` | **BLOCKED (Thiếu backend)** |
| F15 | W3-005 | Minh | Sắp xếp theo giá giảm dần | `app/data.py` | `CHƯA_CODE` | **BLOCKED (Thiếu backend)** |
| F16 | W3-005 | Minh | Sắp xếp theo tên A-Z | `app/data.py` | `CHƯA_CODE` | **BLOCKED (Thiếu backend)** |
| F17 | W3-005 | Minh | Phân trang sản phẩm (Page 1 -> Page 2) | `app/data.py` | `test_d29_05_pagination_integrity` | **VERIFIED (Đã có test & code)** |
| F18 | W3-005 | Minh | Giữ nguyên bộ lọc khi chuyển trang | `app/data.py` | `CHƯA_CODE` | **BLOCKED (Thiếu backend)** |
| F19 | W3-007 | Nghĩa | Xem chi tiết sản phẩm hợp lệ | `app/routes.py` | `test_d29_06_view_valid_product_detail` | **VERIFIED (Đã có test & code)** |
| F20 | W3-007 | Nghĩa | Chi tiết sản phẩm ID không tồn tại trả 404 | `app/routes.py` | `test_d29_07_invalid_product_id_returns_404` | **VERIFIED (Đã có test & code)** |
| F21 | W3-007 | Nghĩa | Hiển thị danh sách kích cỡ có sẵn | `app/data.py` | `test_details_404_and_static` | **VERIFIED (Đã có test & code)** |
| F22 | W3-007 | Nghĩa | Hiển thị danh sách màu sắc có sẵn | `app/data.py` | `test_details_404_and_static` | **VERIFIED (Đã có test & code)** |
| F23 | W3-007 | Nghĩa | Lọc màu VÀ size trên CÙNG MỘT biến thể (SP101/SP102) | `app/data.py` | `test_03_critical_same_variant_color_size_rule` | **VERIFIED (Đã có test & code)** |
| F24 | W3-007 | Nghĩa | Hiển thị tồn kho theo biến thể đã chọn | `app/data.py` | `test_05_product_detail_and_variant_stock` | **VERIFIED (Đã có test & code)** |
| F25 | W3-007 | Nghĩa | Biến thể hết hàng (tồn = 0) hiển thị trạng thái hết | `app/templates/product_detail.html` | `CHƯA_TEST` | **NOT RUN (Chưa viết test)** |
| F26 | W3-007 | Nghĩa | Ràng buộc duy nhất cặp (product_id, color_id, size_id) | `database/schema.sql` | `test_04_duplicate_variant_combination_blocked` | **VERIFIED (Đã có test & code)** |
| F27 | W3-007 | Nghĩa | Ràng buộc tồn kho không âm (>= 0) | `database/schema.sql` | `test_05_negative_stock_blocked` | **VERIFIED (Đã có test & code)** |
| F28 | W3-007 | Nghĩa | Ràng buộc tồn kho là số nguyên | `tests/w3_diem/business_rules.py` | `test_06_decimal_stock_blocked` | **VERIFIED (Đã có test & code)** |
| F29 | W3-007 | Nghĩa | Xem hoặc chọn sản phẩm không tự ý trừ tồn kho | `app/routes.py` | `test_06_browsing_does_not_deduct_stock` | **VERIFIED (Đã có test & code)** |
| F30 | W3-008 | Tuấn | Thêm sản phẩm hợp lệ vào giỏ | `app/routes.py` | `test_d29_08_select_correct_variant` | **VERIFIED (Đã có test & code)** |
| F31 | W3-008 | Tuấn | Thêm giỏ vượt quá số lượng tồn bị từ chối | `app/routes.py` | `test_cart_guard` | **VERIFIED (Đã có test & code)** |
| F32 | W3-008 | Tuấn | Số lượng thêm giỏ <= 0 bị từ chối | `app/routes.py` | `test_cart_guard` | **VERIFIED (Đã có test & code)** |
| F33 | W3-008 | Tuấn | Xóa 1 biến thể khỏi giỏ hàng | `app/routes.py` | `test_cart_session_and_remove` | **VERIFIED (Đã có test & code)** |
| F34 | W3-008 | Tuấn | Xem giỏ hàng tính đúng tổng tiền | `app/routes.py` | `test_cart_session_and_remove` | **VERIFIED (Đã có test & code)** |
| F35 | W3-008 | Tuấn | Màn hình checkout nhận tại cửa hàng (không ship) | `app/routes.py` | `test_cart_session_and_remove` | **VERIFIED (Đã có test & code)** |
| F36 | W3-013 | Khải | Guest truy cập URL admin bị điều hướng login | `app/routes.py` | `test_01_guest_blocked_from_admin_urls` | **VERIFIED (Đã có test & code)** |
| F37 | W3-013 | Khải | Customer truy cập admin bị chặn 403 | `app/routes.py` | `test_02_customer_blocked_from_admin` | **VERIFIED (Đã có test & code)** |
| F38 | W3-013 | Khải | Seller bị chặn POST/PUT vào trang admin | `app/routes.py` | `test_d29_09_seller_blocked_from_admin_post` | **VERIFIED (Đã có test & code)** |
| F39 | W3-013 | Khải | Admin đăng nhập vào được dashboard | `app/routes.py` | `test_04_admin_allowed_access` | **VERIFIED (Đã có test & code)** |
| F40 | W3-013 | Khải | Kiểm tra giá sản phẩm phải > 0đ (A07) | `app/routes.py` | `test_d29_12_invalid_price_rejected` | **VERIFIED (Đã có test & code)** |
| F41 | W3-013 | Khải | Thực hiện INSERT sản phẩm thật vào CSDL | `app/routes.py` | `CHƯA_CODE` | **BLOCKED (Thiếu backend)** |
| F42 | W3-013 | Khải | Chống tạo danh mục trùng tên sau chuẩn hóa (A03) | `tests/w3_diem/business_rules.py` | `test_d29_11_duplicate_category_rejected` | **VERIFIED (Đã có test & code)** |
| F43 | W3-054 | Khải | Upload ảnh JPG, PNG, WebP <= 5MB (A05) | `tests/w3_diem/business_rules.py` | `test_01_valid_image_formats` | **VERIFIED (Đã có test & code)** |
| F44 | W3-054 | Khải | Chặn file mã độc giả mạo đuôi ảnh (A05) | `tests/w3_diem/business_rules.py` | `test_02_fake_image_file_rejected` | **VERIFIED (Đã có test & code)** |
| F45 | W3-054 | Khải | Quy tắc xóa ảnh đại diện chọn ảnh thay thế (A04) | `tests/w3_diem/business_rules.py` | `test_05_avatar_deletion_fallback_rule` | **VERIFIED (Đã có test & code)** |
| F46 | W3-014 | Khải | Khách lưu sản phẩm yêu thích (Favorites) | `app/routes.py` | `CHƯA_CODE` | **BLOCKED (Thiếu backend)** |
| F47 | W3-014 | Khải | Cách ly danh sách yêu thích giữa khách A và B | `app/routes.py` | `test_07_customer_favorite_isolation` | **VERIFIED (Đã có test & code)** |
| F48 | W3-044 | Khải | Giao dịch rollback khi lưu biến thể lỗi | `database/schema.sql` | `test_05_atomic_transaction_rollback_on_variant_failure` | **VERIFIED (Đã có test & code)** |
| F49 | W3-044 | Khải | Không xóa vật lý sản phẩm đã phát sinh đơn hàng | `database/schema.sql` | `test_06_referenced_product_cannot_be_deleted_history_protection` | **VERIFIED (Đã có test & code)** |
