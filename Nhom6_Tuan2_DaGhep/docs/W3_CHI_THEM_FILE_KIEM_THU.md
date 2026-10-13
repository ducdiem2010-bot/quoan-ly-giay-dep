# Kiểm thử W3-010/W3-011 — Chỉ thêm file

Ngày bàn giao: 13/10/2026. Lệnh thực thi: `python -m unittest discover -s tests -p 'test_*.py' -v`.

**Kết quả: 42 tests — OK.** Python 3.12, Flask test client và SQLite tạm. Không coi đây là nghiệm thu SQL Server hoặc ảnh nghiệm thu giao diện browser.

| Nhóm kiểm thử | Số bài | Hành vi đã kiểm tra | Kết quả |
| --- | ---: | --- | --- |
| Tuần 2 nguyên bản | 10 | Trang chủ/search/category/detail, DB, giỏ, CSRF, tài khoản, admin/Seller, lỗi. | PASS |
| Tuần 2 cùng phần W3 | 10 | Dùng lại toàn bộ bài test gốc qua lớp kế thừa; app có Blueprint W3 vẫn qua các bài gốc. Không sửa `test_smoke.py`. | PASS |
| W3-010 | 6 | Thẻ sản phẩm, công khai, hai trang không trùng/bỏ sót, empty state, page lỗi và giữ query. | PASS |
| W3-011 | 11 | Form GET đúng tên, labels, value/selected, reset, page=1 khi gửi form, giữ query, lỗi giá/mã lạ, escape HTML, cấu hình danh mục và ghi chú UI mẫu. | PASS |
| Ghép hai phần | 5 | Factory gốc vẫn chỉ có Tuần 2; route mới đọc cùng DB; dùng base gốc/thẻ riêng; chia sẻ session login; không đè route `/products` đã có. | PASS |

Test mô phỏng gửi form bằng HTTP GET, không kiểm phím Enter vật lý. Fixture có thêm sản phẩm để kiểm hai trang, nhưng seed bàn giao vẫn giữ nguyên 10 sản phẩm. Các sort/filter mới chưa thay đổi dữ liệu, phù hợp phạm vi UI W3-011.

## Kiểm tra giữ nguyên file gốc

Đối chiếu ZIP gốc `Nhom6_WebGiayDep_Tuan2_DaGhep_NghiemThu (1)(1).zip` với bản đã ghép:

- 72 file gốc còn đầy đủ.
- 72 file giống từng byte; SHA-256 trùng nhau.
- 0 file gốc bị sửa; 0 file gốc bị xóa.
- 17 file được thêm vào path mới.
- Gói bổ sung chỉ có 17 path mới, không chứa path trùng file gốc.
- Dữ liệu của mọi file gốc trong ZIP đầy đủ được kiểm lại sau khi nén; ZIP không có entry lỗi.

`docs/W3_CHI_THEM_FILE_DOI_CHIEU.json` có hash ZIP nguồn, hash từng file gốc và danh sách file thêm. Đây là kết quả script đối chiếu, không phải chỉ mô tả dự kiến.

## Checklist thủ công — chưa chạy

| Thao tác | Kết quả cần thấy | Tình trạng |
| --- | --- | --- |
| Chạy `py run_w3.py`, mở `/products`. | Giao diện W3-010/W3-011, menu/chân trang của base tuần 2. | Chưa chạy browser |
| Mở `/`, `/product/1`, đăng nhập/quản trị/giỏ trên cùng server. | Các chức năng cũ vẫn dùng được cùng session/DB. | Đã kiểm test client; chưa chạy browser |
| Chạy `py run.py` sau khi dừng server W3. | Trang tuần 2 như cũ; `/products` không được nạp. | Đã kiểm factory; chưa chạy browser |
| Nhập từ khóa, chọn điều kiện, gửi form; reset. | Từ khóa tìm được SP; các lựa chọn giữ nguyên hoặc xóa khi reset. | Đã kiểm GET; chưa chạy browser |
| Xem ở 375px/768px/1280px và khi CDN không tải. | Ô lọc, nút, thẻ và phân trang không tràn/chồng. | Chưa chạy browser |
| Đối chiếu M2b/danh mục thật. | Mã, enum gender/sort khớp bản nhóm chốt. | Chưa nhận M2b |
| Kết nối SQL Server và ghép bộ lọc/sort thật. | Điều kiện/count/paging đúng; màu+size cùng biến thể. | Chưa chạy, ngoài tích hợp UI hiện tại |
