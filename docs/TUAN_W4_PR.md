> Cập nhật bộ nối: đọc [bàn giao backend](TUAN_W4_BACKEND_HANDOFF.md). Đã có factory/adapter tự gắn provider; backend thật và nghiệm thu E2E vẫn chờ bàn giao.

# Hoàn thiện frontend checkout và giao diện đơn khách tuần 4

Task: W4-004, W4-009, W4-014, W4-019, W4-024. Owner: Tuấn. Review/test: Điểm; Khải review link UI admin dùng chung.

Checkout trước đây chỉ có kiểm tra native cơ bản và trang kết quả ghi cố định trạng thái. Bản này thêm lỗi gần trường, giao/nhận đúng yêu cầu địa chỉ, trạng thái đang gửi và phản hồi được ghi rõ là snapshot. Thêm giao diện danh sách/chi tiết đơn, các trạng thái rỗng/lỗi/payment và dialog hủy qua provider backend riêng, mặc định chưa kết nối.

Không có SQL, thay đổi schema, xử lý tồn hoặc gateway mới. Provider/transaction thuộc backend vẫn cần ghép trước khi nghiệm thu luồng đơn thật.

## File thay đổi

Xem TUAN_W4_CHANGES.json và TUAN_W4_HANDOFF.md. Có 1 thay đổi Python đăng ký blueprint/config UI trong app/__init__.py; controller UI mới không truy vấn DB.
File UI admin/index.html chỉ đổi link Thêm sản phẩm sang form lưu W3 và cập nhật mô tả.

## Chạy / dữ liệu test

Theo README_W4_TUAN.md. SQLite test seed gốc, SP1 màu Đen size39, SL1. Preview bật riêng bằng TUAN_W4_PREVIEW=1 và luôn có nhãn.
Kết quả test thực chạy: W4_VERIFICATION.md, evidence/w4/unittest_results.txt, browser_results.json.

## Lỗi đã biết / phụ thuộc

Provider list/detail/cancel chưa được Nghĩa bàn giao; gateway online chưa có; kho chưa trừ/hoàn; SP ẩn trong giỏ vẫn có thể đặt.
Các lỗi nghiệp vụ này không được che bằng UI hoặc ghi PASS. SQL Server chưa kiểm.
Chưa push/merge; mô tả này để nhóm dùng khi tạo PR sau review.
