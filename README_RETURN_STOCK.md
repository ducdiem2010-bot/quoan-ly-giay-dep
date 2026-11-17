> Cập nhật v3: xem [README_TRA_HANG_V3.md](README_TRA_HANG_V3.md) cho quy tắc hiện hành. Mô tả phân loại hàng trả/hủy khi đang giao bên dưới thuộc phiên bản cũ.

# Chức năng hủy đơn đang giao và xác nhận hoàn kho

Website Nhóm 6 giữ nguyên quy tắc: **Xác nhận đơn = cửa hàng chấp nhận đơn**;
**Hoàn thành = đã giao/nhận và đã thu tiền**. Cho phép ghi nhận thu tiền trước khi giao.

## Hủy đơn và hoàn kho

- Chưa xác nhận: hủy đơn, không có tồn kho đã trừ để hoàn.
- Đã xác nhận và chưa giao: hủy, hoàn ngay số lượng đã trừ kho.
- Đang giao: nhân viên được hủy ngay, đơn chuyển `Đã hủy`, hệ thống lập phiếu
  `HoanKhoChiTiet` theo từng biến thể, **chưa cộng tồn kho**.
- Khi hàng trở về: vào trang chi tiết đơn đã hủy, nhập số lượng **bán lại được** và
  **hàng hỏng/không bán được** rồi nhấn **Xác nhận hoàn kho**. Có thể nhập nhiều lần.
  Hệ thống không cho xử lý quá số lượng cần hoàn; lưu nhật ký người và thời gian.
- Đã giao thành công / Hoàn thành: không hủy trực tiếp theo quy trình thường.
- Đơn đã thanh toán **đang giao** được hủy, nhưng tiền không được hoàn tự động;
  trạng thái `Chờ xử lý hoàn tiền` được ghi lại để đối soát riêng.
- Đơn đã thanh toán nhưng **chưa xuất giao** vẫn giữ quy tắc chặn hủy của bản trước.

**Lưu ý vận hành:** Nút hoàn kho là xác nhận của nhân viên dựa trên việc hàng thực tế
đã quay về; hệ thống không tự xác minh việc giao nhận thực ngoài cửa hàng.

## Khởi tạo và cập nhật database

**SQLite:** `init_demo_database()` sẽ tạo 2 bảng `HoanKhoChiTiet`, `LichSuHoanKho`
và trường `TrangThaiHoanTien` khi khởi động ứng dụng; giữ nguyên dữ liệu hiện có.

**SQL Server:** Với database mới, dùng `database/init_database_sqlserver.sql`.
Với database đã có, sao lưu trước và chạy `database/upgrade_existing_sqlserver.sql`
hoặc migration `database/migrate_return_stock_sqlserver.sql` nếu các phần nâng cấp khác
đã được áp dụng. Script chỉ bổ sung cấu trúc, không tự hủy hoặc hoàn kho đơn cũ.

## Các thống kê đã sửa

Bán chạy, bán chậm, Xu hướng và giá trị đơn hoàn thành chỉ tính đơn **Hoàn thành**,
**Đã giao**, có bản ghi `ThongTinGiaoDich.TrangThaiThanhToan='Đã thanh toán'`.
Tiền đã thu là chỉ số riêng, được ghi nhận ngay sau khi thanh toán, kể cả đơn chưa giao.

## Chạy test

PowerShell:

```powershell
$env:DB_BACKEND = "sqlite"
$env:SECRET_KEY = "khoa-kiem-thu-rieng-khong-dung-production"
python -m unittest discover -s tests -p "test*.py" -v
```

Không sửa phí giao hàng, quên mật khẩu hoặc xóa dữ liệu demo hợp lệ.
SQL Server và Docker phải kiểm thử thực tế trên máy có cài đặt phù hợp.
