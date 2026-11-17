# Trả hàng v3 — yêu cầu chốt ngày 16/11/2026

> **Bổ sung 16/11/2026:** Nếu dùng phiên bản có trang in phiếu và nhóm trả hàng, hãy đọc thêm [`README_BO_SUNG_GIAO_DIEN_IN_PHIEU.md`](README_BO_SUNG_GIAO_DIEN_IN_PHIEU.md). Phiên bản mới **có migration cột `MaNhomTra`**, khác với bản v3 gốc dưới đây.


Hướng dẫn này thay thế các mô tả cũ về hủy khi đang giao/phân loại hàng trả.

## Chạy trên Windows PowerShell

Mở terminal ở thư mục chứa run.py:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements_sqlite.txt
$env:DB_BACKEND = "sqlite"
python run.py
```

Nếu PowerShell chặn Activate.ps1, dùng `.\.venv\Scripts\python.exe` thay `python`.
Địa chỉ và cổng theo thông báo terminal. Database hiện có giữ nguyên; sao lưu trước khi thay mã nguồn.

```powershell
$env:DB_BACKEND = "sqlite"
python -m unittest discover -s tests -p "test*.py" -v
```

## Luồng mới

Đơn Hoàn thành → Trả hàng → chọn số đôi và lý do → xác nhận đã nhận thực tế.
Máy chủ lấy giá trong đơn, cộng kho đúng biến thể, ghi khoản phải hoàn và giảm doanh thu thuần.
Sau khi thực sự trả tiền cho khách, xác nhận ĐÃ HOÀN TIỀN. Bước này không cộng kho/giảm doanh thu lần hai.
Đóng form không lưu; lưu thành công chuyển lại chi tiết đơn với form đóng. Lỗi giữ dữ liệu và mở lại form.
Đang giao không được hủy thông thường hoặc trả hàng.
Khách hàng/nhân viên không tự đổi mật khẩu; admin vẫn đặt lại mật khẩu nhân viên.

## Dữ liệu và tương thích

Không thêm bảng/cột trong v3, không cần migration mới nếu đã dùng đầy đủ bản đầu vào.
Giữ SoLuongTot/SoLuongHong cho lịch sử: giao dịch mới ghi SoLuongTot=SoLuong, SoLuongHong=0.
Các phiếu hủy/hoàn kho cũ vẫn được xử lý riêng. Không tự nhập lại hàng lỗi cũ.
Không sửa các phiếu cũ có tiền hoàn 0. Giao dịch demo cũ giữ lịch sử nhưng không tính vào tiền thật đã hoàn.
Chạy database/audit_legacy_returns.sql để liệt kê các mục cần đối soát trên database thực tế.
Tổng tiền hoàn được đối soát theo đơn; lịch sử từng dòng trả và từng giao dịch tiền đều được giữ.
Không có chức năng giảm giá trong checkout hiện tại: TongTien là tổng SoLuong × DonGia.

SQL Server: nếu database cũ chưa có bảng trả hàng, sao lưu và chạy migration hiện có
`database/migrate_returns_refunds_staff_sqlserver.sql` cùng các migration tiền đề của bản gốc.
V3 không tự chạy script SQL Server hoặc sửa dữ liệu lịch sử. SQL Server chưa được kiểm thử trực tiếp trong lần bàn giao này.

Các README/báo cáo cũ có nội dung khác chỉ là lịch sử dự án; quy tắc v3 ở trên là quy tắc hiện hành.
