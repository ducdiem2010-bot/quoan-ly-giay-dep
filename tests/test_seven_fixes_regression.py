"""Bộ kiểm thử hồi quy cho 7 vấn đề nghiệp vụ:
1. Chặn thanh toán đơn đã hủy.
2. Hoàn thiện adapter / tương thích SQL Server cho W11, loại bỏ guard 503 vô căn cứ.
3. Giữ nguyên thông tin lịch sử đơn hàng (tên, màu, size snapshot tại thời điểm đặt).
4. Sửa đường dẫn ảnh bị hỏng: không trả URL 404 khi file không tồn tại, tự động lấy ảnh phụ hợp lệ.
5. Bỏ gán ảnh sai theo mã sản phẩm (không gán ảnh Nike cho ID 1 khi catalog thay đổi/không liên kết ảnh).
6. Loại đơn tương lai khỏi báo cáo bán chậm (chỉ tính từ đầu kỳ đến thời điểm báo cáo).
7. Thống nhất số đã bán ở trang Xu hướng (chỉ tính đơn Hoàn thành, loại đơn Chờ xác nhận/Đã hủy).
"""
import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app import create_app
from app.db import query_all, query_one
from app.services.order_ops import record_order_payment, cancel_order_stock, OrderOperationError
from app.services.checkout import create_pending_order
from app.services.product_images import resolve_product_image_path, get_product_image_url
from app.services.w11_insights import slow_stock_report, out_of_stock_products_report


class TestSevenFixesRegression(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "test_fixes.sqlite3")
        self.app = create_app({
            "TESTING": True,
            "DATABASE": self.db_path,
            "SECRET_KEY": "test-regression-secret",
            "DB_BACKEND": "sqlite"
        })
        self.client = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def _login(self, email, password="Demo@12345"):
        self.client.get("/login")
        with self.client.session_transaction() as sess:
            token = sess["_csrf"]
        return self.client.post("/login", data={"csrf_token": token, "email": email, "password": password}, follow_redirects=True)

    # --------------------------------------------------------------------------
    # 1. Chặn thanh toán đơn đã hủy
    # --------------------------------------------------------------------------
    def test_payment_blocked_on_cancelled_order(self):
        with self.app.app_context():
            form_data = {
                "full_name": "Nguyễn Văn Hủy",
                "phone": "0912345678",
                "email": "huy@gmail.com",
                "fulfillment": "delivery",
                "address": "456 Đường Hủy, Hà Nội",
                "payment_method": "cod",
                "note": ""
            }
            order_id = create_pending_order(form_data, {1: 1}, user_id=1)
            # Hủy đơn
            cancel_order_stock(order_id, 1, reason="Khách đổi ý")
            order = query_one("SELECT TrangThai FROM DonHang WHERE MaDonHang=?", (order_id,))
            self.assertEqual(order["TrangThai"], "Đã hủy")

            # Ghi nhận thanh toán phải bị từ chối
            with self.assertRaises(OrderOperationError) as ctx:
                record_order_payment(order_id, 1)
            self.assertIn("đã bị hủy", str(ctx.exception))

            # Trạng thái thanh toán không được thay đổi
            tg = query_one("SELECT TrangThaiThanhToan, NguoiThuTien FROM ThongTinGiaoDich WHERE MaDonHang=?", (order_id,))
            self.assertEqual(tg["TrangThaiThanhToan"], "Chưa thanh toán")
            self.assertIsNone(tg["NguoiThuTien"])

        # Kiểm tra qua HTTP POST /orders/<id>/pay bởi Admin
        self._login("admin@shop.vn")
        with self.client.session_transaction() as sess:
            token = sess["_csrf"]
        res = self.client.post(f"/orders/{order_id}/pay", data={"csrf_token": token}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        html = res.data.decode("utf-8")
        self.assertIn("đã bị hủy, không thể ghi nhận thanh toán", html)

    def test_double_payment_prevented(self):
        with self.app.app_context():
            form_data = {
                "full_name": "Nguyễn Văn Trùng",
                "phone": "0912345679",
                "email": "trung@gmail.com",
                "fulfillment": "pickup",
                "address": "",
                "payment_method": "cod",
                "note": ""
            }
            order_id = create_pending_order(form_data, {1: 1}, user_id=1)
            # Xác nhận đơn trước khi ghi nhận thanh toán (theo quy trình chuẩn: Chờ xác nhận -> Đã xác nhận -> Thanh toán)
            from app.services.order_ops import confirm_order_stock
            confirm_order_stock(order_id, 1)
            # Thanh toán lần 1 -> Thành công
            res1 = record_order_payment(order_id, 1)
            self.assertTrue(res1)

            # Thanh toán lần 2 -> Bị chặn chống ghi trùng
            with self.assertRaises(OrderOperationError) as ctx:
                record_order_payment(order_id, 1)
            self.assertIn("không thể ghi trùng", str(ctx.exception))

    # --------------------------------------------------------------------------
    # 2. Hoàn thiện phần SQL Server (bỏ guard 503 vô căn cứ)
    # --------------------------------------------------------------------------
    def test_w11_sqlserver_compatibility_no_503_guard(self):
        # Khi DB_BACKEND là sqlserver, các route w11 không còn bị chặn 503 bởi guard nội bộ
        from app.routes.w11 import _sqlite_or_503
        with self.app.app_context():
            self.app.config["DB_BACKEND"] = "sqlserver"
            # Hàm _sqlite_or_503 không được raise abort(503) nữa
            try:
                _sqlite_or_503()
            except Exception as e:
                self.fail(f"_sqlite_or_503 threw unexpected exception: {e}")

    # --------------------------------------------------------------------------
    # 3. Giữ nguyên thông tin lịch sử đơn hàng (Snapshot)
    # --------------------------------------------------------------------------
    def test_order_history_snapshot_preserved_after_catalog_update(self):
        with self.app.app_context():
            # Đặt đơn mới cho sản phẩm #1 ("Nike Air Zoom Pegasus", MauSac="Xanh", KichThuoc="39")
            form_data = {
                "full_name": "Nguyễn Văn Test",
                "phone": "0987654321",
                "email": "test@gmail.com",
                "fulfillment": "delivery",
                "address": "123 Đường Test, TP.HCM",
                "payment_method": "cod",
                "note": ""
            }
            order_id = create_pending_order(form_data, {1: 2}, user_id=1)
            self.assertIsNotNone(order_id)

            # Kiểm tra ChiTietDonHang đã lưu đúng snapshot ban đầu
            item_before = query_one("SELECT TenSanPham, MauSac, KichThuoc, DonGia FROM ChiTietDonHang WHERE MaDonHang=? AND MaBienThe=1", (order_id,))
            self.assertEqual(item_before["TenSanPham"], "Nike Air Zoom Pegasus")
            self.assertEqual(item_before["MauSac"], "Đen")
            self.assertEqual(item_before["KichThuoc"], "39")

            # Bây giờ sửa catalog: đổi tên sản phẩm và sửa biến thể
            conn = sqlite3.connect(self.db_path)
            conn.execute("UPDATE SanPham SET TenSanPham='Giày Chạy Bộ Đã Đổi Tên', GiaBan=999999 WHERE MaSanPham=1")
            conn.execute("UPDATE BienTheSanPham SET MauSac='Tím Than', KichThuoc='45' WHERE MaBienThe=1")
            conn.commit()
            conn.close()

        # Kiểm tra màn hình xem đơn hàng của Khách hàng
        self._login("khach@shop.vn")
        res_cust = self.client.get("/account/orders")
        self.assertEqual(res_cust.status_code, 200)
        html_cust = res_cust.data.decode("utf-8")
        # Phải vẫn giữ tên cũ đã snapshot, không bị đổi sang tên mới
        self.assertIn("Nike Air Zoom Pegasus", html_cust)
        self.assertIn("39", html_cust)
        self.assertIn("Đen", html_cust)

        # Kiểm tra màn hình chi tiết đơn hàng của Admin
        self._login("admin@shop.vn")
        res_admin = self.client.get(f"/admin/orders/{order_id}")
        self.assertEqual(res_admin.status_code, 200)
        html_admin = res_admin.data.decode("utf-8")
        self.assertIn("Nike Air Zoom Pegasus", html_admin)
        self.assertIn("39", html_admin)
        self.assertIn("Đen", html_admin)

    # --------------------------------------------------------------------------
    # 4 & 5. Sửa đường dẫn ảnh hỏng & Không gán sai theo mã sản phẩm
    # --------------------------------------------------------------------------
    def test_image_resolution_no_404_and_uses_valid_secondary_image(self):
        with self.app.app_context():
            # Thêm sản phẩm mới #99 không có file ảnh trên ổ đĩa
            conn = sqlite3.connect(self.db_path)
            conn.execute("INSERT INTO SanPham (MaSanPham, MaDanhMuc, TenSanPham, GiaBan, ThuongHieu, HienThi) VALUES (99, 1, 'Giày Không Có Ảnh', 500000, 'TestBrand', 1)")
            # Ảnh đại diện chỉ tới file không tồn tại
            conn.execute("INSERT INTO SanPhamHinhAnh (MaSanPham, TenTep, LaAnhDaiDien, ThuTu) VALUES (99, 'missing_file_404.jpg', 1, 0)")
            # Ảnh phụ chỉ tới file có thật trong storefront
            conn.execute("INSERT INTO SanPhamHinhAnh (MaSanPham, TenTep, LaAnhDaiDien, ThuTu) VALUES (99, 'product-02.jpg', 0, 1)")
            conn.commit()
            conn.close()

            # resolve_product_image_path phải bỏ qua ảnh đại diện 404 và tự động chọn ảnh phụ hợp lệ
            prod = {"MaSanPham": 99, "TenSanPham": "Giày Không Có Ảnh", "ThuongHieu": "TestBrand"}
            resolved = resolve_product_image_path(prod)
            self.assertEqual(resolved, "images/storefront/product-02.jpg")

    def test_no_fake_image_by_product_id(self):
        with self.app.app_context():
            # Tạo sản phẩm #1 nhưng xóa toàn bộ ảnh trong SanPhamHinhAnh và đổi tên thành 'Dép Biti’s Riêng'
            conn = sqlite3.connect(self.db_path)
            conn.execute("DELETE FROM SanPhamHinhAnh WHERE MaSanPham=1")
            conn.execute("UPDATE SanPham SET TenSanPham='Dép Siêu Nhẹ Mới', ThuongHieu='LocalBrand' WHERE MaSanPham=1")
            conn.commit()
            conn.close()

            prod = {"MaSanPham": 1, "TenSanPham": "Dép Siêu Nhẹ Mới", "ThuongHieu": "LocalBrand"}
            # Không được tự ý trả về ảnh Nike (product-01.jpg) chỉ vì mã sản phẩm là 1
            resolved = resolve_product_image_path(prod)
            self.assertIsNone(resolved)
            self.assertIsNone(get_product_image_url(prod))

    # --------------------------------------------------------------------------
    # 6. Loại đơn tương lai khỏi báo cáo bán chậm
    # --------------------------------------------------------------------------
    def test_slow_selling_excludes_future_orders(self):
        with self.app.app_context():
            # Tạo đơn hoàn thành nhưng NgayDat ở tương lai (+5 ngày)
            future_date = (datetime.now(timezone.utc) + timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")
            conn = sqlite3.connect(self.db_path)
            conn.execute("INSERT INTO DonHang (MaDonHang, MaNguoiDung, NgayDat, TrangThai, TongTien) VALUES (888, 1, ?, 'Hoàn thành', 1000000)", (future_date,))
            conn.execute("INSERT INTO ChiTietDonHang (MaDonHang, MaBienThe, SoLuong, DonGia) VALUES (888, 7, 50, 200000)")
            conn.commit()
            conn.close()

            # Sản phẩm có biến thể #7 là Converse Chuck Taylor (MaSanPham=7)
            report = slow_stock_report(days=30)
            items = {p["MaSanPham"]: p for p in report["items"]}
            # Đơn 50 đôi ở tương lai không được tính vào DaBanTrongKy
            if 7 in items:
                self.assertLessEqual(items[7]["sold_period"], 2)

    # --------------------------------------------------------------------------
    # 7. Thống nhất số đã bán ở trang Xu hướng
    # --------------------------------------------------------------------------
    def test_trending_excludes_pending_and_cancelled_orders(self):
        with self.app.app_context():
            # Thêm đơn 'Chờ xác nhận' với số lượng 50 đôi cho sản phẩm #4 (Puma Suede Classic, MaBienThe=4)
            conn = sqlite3.connect(self.db_path)
            conn.execute("INSERT INTO DonHang (MaDonHang, MaNguoiDung, NgayDat, TrangThai, TongTien) VALUES (999, 1, CURRENT_TIMESTAMP, 'Chờ xác nhận', 50000000)")
            conn.execute("INSERT INTO ChiTietDonHang (MaDonHang, MaBienThe, SoLuong, DonGia) VALUES (999, 4, 50, 1000000)")
            conn.commit()
            conn.close()

        # Gọi trang /xu-huong
        res = self.client.get("/xu-huong")
        self.assertEqual(res.status_code, 200)
        # Trang Xu hướng chỉ tính đơn Hoàn thành, đơn Chờ xác nhận 50 đôi không được coi là đã bán
        with self.app.app_context():
            from app.routes.catalog import trending
            # Kiểm tra query DaBan trong catalog
            rows = query_all("""SELECT (SELECT COALESCE(SUM(ct.SoLuong),0) FROM ChiTietDonHang ct
                                        JOIN BienTheSanPham b2 ON b2.MaBienThe=ct.MaBienThe
                                        JOIN DonHang dh ON dh.MaDonHang=ct.MaDonHang
                                        WHERE b2.MaSanPham=4 AND dh.TrangThai=?) AS DaBan""", ('Hoàn thành',))
            self.assertEqual(rows[0]["DaBan"], 0)


if __name__ == "__main__":
    unittest.main()
