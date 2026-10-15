# CHECKLIST CÀI ĐẶT VÀ SẴN SÀNG DEMO 5 MÁY (W3-060)

## 1. Kết quả kiểm tra máy hiện tại

| Hạng mục | Trạng thái | Chi tiết |
|---|---|---|
| Thư viện Python cốt lõi | **PASS** | Đã cài đặt đầy đủ các gói cần thiết. |
| Thư mục tài nguyên Static (CSS/JS/Ảnh) | **PASS** | Đầy đủ css, js, images. |
| Luồng duyệt Public trang chủ | **PASS** | Trang chủ tải thành công (HTTP 200), hiển thị danh sách sản phẩm. |
| Kiểm chứng cài đặt trên 5 máy thành viên | **BLOCKED / CẦN THỰC HIỆN** | Hiện tại mới kiểm tra trên máy Điểm. Minh, Nghĩa, Khải, Tuấn phải tự clone và chạy lệnh kiểm thử trên máy riêng để lấy bằng chứng. |

## 2. Kế hoạch kiểm chứng 5 máy độc lập

| Máy thành viên | Người phụ trách | Phiên bản Python | Dịch vụ SQL Server | Kết quả Test (PASS/FAIL) | Ảnh chụp minh chứng |
|---|---|---|---|---|---|
| Máy 1 | **Điểm** (Trưởng nhóm) | Python 3.13 | Local / SQLite Demo | Đạt | `docs/w3_diem/evidence/may1_diem.png` |
| Máy 2 | **Minh** (Backend DB) | Cần kiểm tra | SQL Server Developer | Chưa xác minh | Cần Minh gửi |
| Máy 3 | **Nghĩa** (Biến thể/Kho) | Cần kiểm tra | Cần kiểm tra | Chưa xác minh | Cần Nghĩa gửi |
| Máy 4 | **Khải** (Admin/Ảnh) | Cần kiểm tra | Cần kiểm tra | Chưa xác minh | Cần Khải gửi |
| Máy 5 | **Tuấn** (Giao diện UI) | Cần kiểm tra | Cần kiểm tra | Chưa xác minh | Cần Tuấn gửi |
