# Điểm D1.2 — Hợp đồng tích hợp

- URL công khai: `/new-arrivals` (`new_arrivals.show`); `/best-sellers` (`best_sellers.show`).
- Home `/` nhận chính xác `latest_products`, `best_selling_products` từ service; mỗi sản phẩm: `MaSanPham`, `TenSanPham`, `GiaBan`, `ThuongHieu`, `TenDanhMuc`, `TongTon`, `AnhDaiDien`.
- SQLite/V1: HienThi=1, trạng thái đơn `Hoàn thành`; SQL Server V2: TrangThai=1, DaHuy=0 + Đã xác nhận + Đã giao, **thanh toán còn chờ chốt**.
- Minh duy nhất sửa `app/__init__.py` và `app/routes/public.py` ở bước M3.1; Nghĩa tạo service/route riêng; Khải chỉ sửa giao diện Admin; Tuấn chỉ sửa storefront; Điểm QA.
- Tránh route trùng, CSS tràn phạm vi, SQL sinh doanh số giả và dữ liệu lộ sản phẩm ẩn.
- Không thay đổi schema/seed hay sửa quyền người dùng để làm test PASS.
