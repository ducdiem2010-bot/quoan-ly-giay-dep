# Giải trình câu lệnh SQL Bán Chạy
**Người thực hiện:** Nguyễn Thái Nghĩa (Ngày 3)

## 1. Cơ chế hoạt động của truy vấn V1 (SQLite)
- Dùng `SUM(ct.SoLuong)` thay vì đếm (`COUNT`) để lấy chính xác số lượng thực tế đã bán.
- Lọc triệt để qua `dh.TrangThaiDon = 1` để loại trừ các đơn rác, đơn ảo, đơn bị hủy (như kịch bản QA ghi nhận đơn hủy +9 SP).
- Kết quả đối chiếu với file CSV: **Khớp 100% (Expected = Actual)**. Trang `/best-sellers` hiển thị đúng trạng thái rỗng khi chưa có đơn nào.

## 2. Truy vấn V2 (Cơ sở dữ liệu mới)
- **Trạng thái:** BLOCKED
- **Lý do:** Đang chờ DB thật V2 được khởi tạo hoàn thiện để map cột `DaHuy=0`, `TrangThaiGiao=1`. Hiện tại SQL V1 trên SQLite đã Pass toàn bộ Unit Test.