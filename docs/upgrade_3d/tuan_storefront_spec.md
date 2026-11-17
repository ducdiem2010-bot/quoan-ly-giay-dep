# Tuấn T1.1 — Đặc tả giao diện công khai

- Giữ nguyên Header, Hero Slider, Footer đã nâng cấp trong ZIP đầu vào.
- Trang chủ `/` gồm slider, partial `_featured_sections.html`, danh sách tất cả sản phẩm.
- Hai mảng dữ liệu do service truyền: `latest_products`, `best_selling_products` (không query SQL trong Jinja2).
- Thẻ card dùng `_product_card.html`, ảnh `_storefront_image.html`, fallback SVG có nhãn `Ảnh minh họa`, tồn 0 là `Hết hàng`, link `/product/<id>`.
- CSS phần featured chỉ tải trên trang chủ; footer CSS cũ ở `style.css` giữ nguyên.
- Viewport nghiệm thu yêu cầu 375 / 768 / 1280 px. Chưa có ảnh chụp thực từ Flask, cần Tuấn xác minh.
