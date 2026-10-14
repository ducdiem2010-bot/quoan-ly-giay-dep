# NHỮNG VIỆC KHÔNG ĐƯỢC BÁO “ĐÃ NGHIỆM THU” KHI CHƯA XÁC MINH

1. **Điểm:** Clone repository thật trên GitHub, đối chiếu nhánh/main với ZIP bàn giao, chạy `python run.py` trên từng máy. Repo URL không được xác nhận bằng ZIP.
2. **Minh:** Mở `database/schema.sql` và `database/seed.sql` trên SQL Server/SSMS thật, xác nhận đủ bảng và dữ liệu; cập nhật ERP/schema/data dictionary đồng bộ. Bảng ghi “8 bảng” nhưng thực tế có 9; xin xác nhận thay đổi.
3. **Nghĩa:** Soát lại `.drawio` nhánh giỏ/đơn (các mối quan hệ N-N đã giải qua bảng chi tiết); kiểm thử giao dịch CSDL và trigger tổng tiền trên SQL Server, không chỉ SQLite.
4. **Tuấn:** Kiểm tra trực tiếp giao diện tại **375px và 768px** trên trình duyệt của ít nhất 1–2 điện thoại/DevTools; chụp bằng chứng không có thanh kéo ngang. Xác nhận Wireframe tái dựng có đúng thiết kế nhóm không.
5. **Khải:** Xác nhận `admin_base.html`, Form thêm sản phẩm có đủ trường và quyền Admin; không nói đã hoàn thành chức năng INSERT sản phẩm vì mới chuẩn bị form. File `admin html.htm` nguồn là trang GitHub, không phải mã Admin thật.
6. **Cả nhóm:** Thực hiện Demo Milestone 1 ở **5 máy**, ghi ảnh/video kiểm thử, thông tin Python/Flask/SQL Server mỗi máy và lỗi nếu có. Hiện chỉ có 10 bài kiểm thử backend ở máy đóng gói.
7. **Tính đúng phạm vi:** Checkout mới là giao diện, không tạo đơn hoặc thanh toán; nhận tại cửa hàng, không ship/online payment. Không tự cộng thêm chức năng bên ngoài yêu cầu tuần.
