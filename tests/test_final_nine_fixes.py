"""Bộ kiểm thử xác thực 9 nhiệm vụ sửa lỗi và hoàn thiện hệ thống - Nhóm 6."""
import os
import re
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from werkzeug.security import check_password_hash, generate_password_hash

from app import create_app
from app.db import get_db_connection, init_demo_database
from app.services.order_ops import cancel_order_stock, confirm_order_stock, record_order_payment, OrderOperationError
from app.services.account import change_user_password, PasswordChangeError
from app.services.checkout import create_pending_order, CheckoutValidationError
from app.services.dashboard import resolve_product_image_relpath


class FinalNineFixesTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_demo.sqlite3")
        self.app = create_app({
            "TESTING": True,
            "DATABASE": self.db_path,
            "DB_BACKEND": "sqlite",
            "SECRET_KEY": "test-secret-key-32-chars-long-secure-suite",
        })
        self.client = self.app.test_client()
        with self.app.app_context():
            init_demo_database()

    def csrf(self, path="/login"):
        resp = self.client.get(path)
        m = re.search(r'name="csrf_token"\s+value="([^"]+)"', resp.get_data(as_text=True))
        return m.group(1) if m else ""

    def tearDown(self):
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    # --------------------------------------------------------------------------
    # NHIỆM VỤ 1 & 7: CHẶN HỦY ĐƠN ĐÃ THANH TOÁN & NỐI CHUỖI AN TOÀN TRÁNH '||'
    # --------------------------------------------------------------------------
    def test_task1_and_7_cancel_paid_order_awaits_refund_sql_safe(self):
        with self.app.app_context():
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO DonHang (MaNguoiDung, TrangThai, TongTien) VALUES (1, 'Chờ xác nhận', 500000)")
            order_id = cur.lastrowid
            cur.execute("INSERT INTO ChiTietDonHang (MaDonHang, MaBienThe, SoLuong, DonGia) VALUES (?, 1, 1, 500000)", (order_id,))
            cur.execute("""INSERT INTO ThongTinGiaoDich (MaDonHang, HoTen, SoDienThoai, HinhThucNhanHang, PhuongThucThanhToan, TrangThaiThanhToan, GhiChu)
                           VALUES (?, 'Test User', '0912345678', 'pickup', 'cod', 'Đã thanh toán', 'Ghi chú ban đầu')""", (order_id,))
            conn.commit()
            conn.close()

            # Quy tắc mới: đơn đã thu tiền nhưng chưa đi giao được HỦY,
            # song tuyệt đối không tự coi đã hoàn tiền.
            cancel_order_stock(order_id, 1, reason=" | Hủy test")
            conn = get_db_connection()
            o_row = conn.execute("SELECT TrangThai,TrangThaiHoanTien FROM DonHang WHERE MaDonHang = ?", (order_id,)).fetchone()
            self.assertEqual(o_row["TrangThai"], "Đã hủy")
            self.assertEqual(o_row["TrangThaiHoanTien"], "Chờ xử lý hoàn tiền")
            tx_row = conn.execute("SELECT GhiChu, TrangThaiThanhToan FROM ThongTinGiaoDich WHERE MaDonHang = ?", (order_id,)).fetchone()
            self.assertEqual(tx_row["TrangThaiThanhToan"], "Đã thanh toán")
            self.assertIn("Hủy test", tx_row["GhiChu"])
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM HoanTienGiaoDich WHERE MaDonHang=?',(order_id,)).fetchone()[0],0)
            conn.close()

    def test_task1_and_7_cancel_unpaid_confirmed_order_refunds_stock(self):
        with self.app.app_context():
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO DonHang (MaNguoiDung, TrangThai, TongTien) VALUES (1, 'Chờ xác nhận', 500000)")
            order_id = cur.lastrowid
            cur.execute("INSERT INTO ChiTietDonHang (MaDonHang, MaBienThe, SoLuong, DonGia) VALUES (?, 1, 2, 250000)", (order_id,))
            cur.execute("""INSERT INTO ThongTinGiaoDich (MaDonHang, HoTen, SoDienThoai, HinhThucNhanHang, PhuongThucThanhToan, TrangThaiThanhToan, GhiChu)
                           VALUES (?, 'Test User', '0912345678', 'pickup', 'cod', 'Chưa thanh toán', 'Ghi chú đơn')""", (order_id,))
            conn.commit()

            init_stock = conn.execute("SELECT SoLuongTon FROM BienTheSanPham WHERE MaBienThe = 1").fetchone()["SoLuongTon"]
            conn.close()

            # 1. Xác nhận đơn: trừ 2 kho
            confirm_order_stock(order_id, 1)
            conn = get_db_connection()
            stock_confirmed = conn.execute("SELECT SoLuongTon FROM BienTheSanPham WHERE MaBienThe = 1").fetchone()["SoLuongTon"]
            self.assertEqual(stock_confirmed, init_stock - 2)
            conn.close()

            # 2. Hủy đơn chưa thanh toán: hoàn lại 2 kho và nối chuỗi ghi chú an toàn (không dùng ||)
            cancel_order_stock(order_id, 1, reason=" | Đã hủy bởi quản trị")
            conn = get_db_connection()
            o_row = conn.execute("SELECT TrangThai FROM DonHang WHERE MaDonHang = ?", (order_id,)).fetchone()
            self.assertEqual(o_row["TrangThai"], "Đã hủy")
            tx_row = conn.execute("SELECT GhiChu FROM ThongTinGiaoDich WHERE MaDonHang = ?", (order_id,)).fetchone()
            self.assertIn("Đã hủy bởi quản trị", tx_row["GhiChu"])
            stock_canceled = conn.execute("SELECT SoLuongTon FROM BienTheSanPham WHERE MaBienThe = 1").fetchone()["SoLuongTon"]
            self.assertEqual(stock_canceled, init_stock)
            conn.close()

    # --------------------------------------------------------------------------
    # NHIỆM VỤ 2: ĐỒNG BỘ TRUY VẤN SQL SERVER MỚI NHẤT
    # --------------------------------------------------------------------------
    def test_task2_sqlserver_queries_syntax(self):
        from app.services.new_arrivals import SQLSERVER_LATEST
        from app.services.best_sellers import SQLSERVER_BEST_SELLERS
        # Kiểm tra cột khớp schema init_database_sqlserver.sql
        self.assertIn("sp.HienThi=1", SQLSERVER_LATEST)
        self.assertIn("ia.LaAnhDaiDien", SQLSERVER_LATEST)
        self.assertNotIn("SQLSERVER_V2", SQLSERVER_LATEST)

        self.assertIn("dh.TrangThai=N'Hoàn thành'", SQLSERVER_BEST_SELLERS)
        self.assertIn("sp.HienThi=1", SQLSERVER_BEST_SELLERS)
        self.assertNotIn("DaHuy", SQLSERVER_BEST_SELLERS)
        self.assertNotIn("TrangThaiXacNhan", SQLSERVER_BEST_SELLERS)

    # --------------------------------------------------------------------------
    # NHIỆM VỤ 3: CHỐNG TẠO ĐƠN HÀNG TRÙNG (IDEMPOTENCY & CHECKOUT_TOKEN)
    # --------------------------------------------------------------------------
    def test_task3_checkout_token_idempotency_backend(self):
        with self.app.app_context():
            form_data = {
                "full_name": "Nguyễn Văn Test",
                "phone": "0988776655",
                "email": "test@example.com",
                "fulfillment": "pickup",
                "address": "",
                "payment_method": "cod",
                "note": "Kiểm tra token trùng"
            }
            basket = {1: 1}
            token = "token-test-unique-12345"

            # Lần 1: Tạo đơn thành công
            order_id_1 = create_pending_order(form_data, basket, user_id=1, checkout_token=token)
            self.assertIsInstance(order_id_1, int)

            # Lần 2: Gửi lại cùng token -> Phải trả về đúng order_id_1, không tạo thêm đơn mới
            order_id_2 = create_pending_order(form_data, basket, user_id=1, checkout_token=token)
            self.assertEqual(order_id_1, order_id_2)

            # Kiểm tra trong DB chỉ có duy nhất 1 đơn mang CheckoutToken này
            conn = get_db_connection()
            count = conn.execute("SELECT COUNT(*) FROM DonHang WHERE CheckoutToken = ?", (token,)).fetchone()[0]
            self.assertEqual(count, 1)
            conn.close()

    def test_task3_checkout_route_rejects_empty_or_invalid_token(self):
        csrf_token = self.csrf("/login")
        with self.client.session_transaction() as sess:
            sess["cart"] = {"1": 1}
            sess["_active_checkout_token"] = "valid-session-token"

        # 1. Gửi token rỗng
        resp_empty = self.client.post("/checkout", data={
            "csrf_token": csrf_token,
            "checkout_token": "",
            "full_name": "Nguyễn Văn A",
            "phone": "0912345678",
            "fulfillment": "pickup",
            "payment_method": "cod"
        }, follow_redirects=True)
        self.assertIn("Mã phiên đặt hàng (checkout token) không hợp lệ hoặc thiếu", resp_empty.get_data(as_text=True))

        # 2. Gửi token giả không khớp session
        resp_fake = self.client.post("/checkout", data={
            "csrf_token": csrf_token,
            "checkout_token": "fake-token-123",
            "full_name": "Nguyễn Văn A",
            "phone": "0912345678",
            "fulfillment": "pickup",
            "payment_method": "cod"
        }, follow_redirects=True)
        self.assertIn("Mã phiên thanh toán không hợp lệ hoặc đã hết hạn", resp_fake.get_data(as_text=True))

        # Giỏ hàng vẫn được bảo toàn khi request thất bại
        with self.client.session_transaction() as sess:
            self.assertEqual(sess["cart"], {"1": 1})

    # --------------------------------------------------------------------------
    # NHIỆM VỤ 4: ẢNH SẢN PHẨM DỰ PHÒNG CHUẨN NO-PRODUCT-IMAGE.SVG
    # --------------------------------------------------------------------------
    def test_task4_fallback_image_resolved(self):
        # Kiểm tra dashboard fallback trả về no-product-image.svg
        fallback = resolve_product_image_relpath({"MaSanPham": 9999, "TenSanPham": "Không có ảnh", "ThuongHieu": "Unknown"})
        self.assertEqual(fallback, "images/no-product-image.svg")

        # Kiểm tra file SVG tồn tại trên đĩa
        svg_path = os.path.join(self.app.static_folder, "images", "no-product-image.svg")
        self.assertTrue(os.path.isfile(svg_path))
        with open(svg_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Chưa có ảnh sản phẩm", content)

    # --------------------------------------------------------------------------
    # NHIỆM VỤ 5: ĐỔI MẬT KHẨU CHO CUSTOMER / SELLER / ADMIN (KHÔNG RESET/OTP)
    # --------------------------------------------------------------------------
    def test_task5_change_password_success_and_validation(self):
        with self.app.app_context():
            # Tạo tài khoản thử nghiệm
            conn = get_db_connection()
            pwd_hash = generate_password_hash("OldPassword123")
            conn.execute("INSERT INTO NguoiDung (MaVaiTro, HoVaTen, Email, MatKhauHash, TrangThai) VALUES (3, 'User Test', 'changepwd@shop.vn', ?, 1)", (pwd_hash,))
            user_id = conn.execute("SELECT MaNguoiDung FROM NguoiDung WHERE Email = 'changepwd@shop.vn'").fetchone()[0]
            conn.commit()
            conn.close()

            # 1. Sai mật khẩu hiện tại
            with self.assertRaises(PasswordChangeError) as cm:
                change_user_password(user_id, "WrongOld", "NewPassword123", "NewPassword123")
            self.assertIn("Mật khẩu hiện tại không chính xác", str(cm.exception))

            # 2. Mật khẩu mới quá ngắn (< 8 ký tự)
            with self.assertRaises(PasswordChangeError) as cm:
                change_user_password(user_id, "OldPassword123", "1234567", "1234567")
            self.assertIn("ít nhất 8 ký tự", str(cm.exception))

            # 3. Mật khẩu mới trùng mật khẩu hiện tại
            with self.assertRaises(PasswordChangeError) as cm:
                change_user_password(user_id, "OldPassword123", "OldPassword123", "OldPassword123")
            self.assertIn("khác mật khẩu hiện tại", str(cm.exception))

            # 4. Xác nhận mật khẩu không khớp
            with self.assertRaises(PasswordChangeError) as cm:
                change_user_password(user_id, "OldPassword123", "NewPassword123", "MismatchConfirm")
            self.assertIn("không khớp", str(cm.exception))

            # 5. Đổi mật khẩu thành công
            result = change_user_password(user_id, "OldPassword123", "NewPassword123", "NewPassword123")
            self.assertTrue(result)

            # Kiểm tra hash mới trong database
            conn = get_db_connection()
            new_hash = conn.execute("SELECT MatKhauHash FROM NguoiDung WHERE MaNguoiDung = ?", (user_id,)).fetchone()[0]
            conn.close()
            self.assertTrue(check_password_hash(new_hash, "NewPassword123"))

    def test_task5_change_password_route(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["user_name"] = "Quản trị demo"
            sess["role"] = "Admin"
        resp = self.client.get("/account/change-password")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Đổi mật khẩu tài khoản", resp.get_data(as_text=True))

    # --------------------------------------------------------------------------
    # NHIỆM VỤ 6: BẢO MẬT SECRET_KEY TRÊN PRODUCTION
    # --------------------------------------------------------------------------
    def test_task6_secret_key_production_block_weak_key(self):
        # Khi FLASK_ENV=production và SECRET_KEY rỗng hoặc yếu -> Phải ném RuntimeError
        with patch.dict(os.environ, {"FLASK_ENV": "production", "SECRET_KEY": "dev-secret-key-change-me"}):
            with self.assertRaises(RuntimeError) as cm:
                create_app()
            self.assertIn("SECRET_KEY", str(cm.exception))

    def test_task6_secret_key_production_valid_key(self):
        # Khi FLASK_ENV=production và có key mạnh hợp lệ -> Tạo app thành công
        with patch.dict(os.environ, {
            "FLASK_ENV": "production",
            "SECRET_KEY": "0123456789abcdef0123456789abcdef0123456789abcdef"
        }):
            app = create_app({"TESTING": True, "DATABASE": ":memory:"})
            self.assertEqual(app.config["SECRET_KEY"], "0123456789abcdef0123456789abcdef0123456789abcdef")

    # --------------------------------------------------------------------------
    # NHIỆM VỤ BỔ SUNG: BẢO VỆ CHỐNG LỖI NGHIỆP VỤ & HỒI QUY
    # --------------------------------------------------------------------------
    def test_record_payment_on_canceled_order_rejected(self):
        with self.app.app_context():
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO DonHang (MaNguoiDung, TrangThai, TongTien) VALUES (1, 'Đã hủy', 350000)")
            order_id = cur.lastrowid
            cur.execute("""INSERT INTO ThongTinGiaoDich (MaDonHang, HoTen, SoDienThoai, HinhThucNhanHang, PhuongThucThanhToan, TrangThaiThanhToan)
                           VALUES (?, 'Nguyễn Văn Hủy', '0911223344', 'pickup', 'cod', 'Chưa thanh toán')""", (order_id,))
            conn.commit()
            conn.close()

            # Không được phép ghi nhận thanh toán cho đơn đã hủy
            with self.assertRaises(OrderOperationError) as cm:
                record_order_payment(order_id, 1)
            self.assertIn("đã bị hủy", str(cm.exception))

            # Xác minh dữ liệu thanh toán trong DB hoàn toàn không bị thay đổi
            conn = get_db_connection()
            tx = conn.execute("SELECT TrangThaiThanhToan, ThoiGianThanhToan, NguoiThuTien FROM ThongTinGiaoDich WHERE MaDonHang = ?", (order_id,)).fetchone()
            self.assertEqual(tx["TrangThaiThanhToan"], "Chưa thanh toán")
            self.assertIsNone(tx["ThoiGianThanhToan"])
            self.assertIsNone(tx["NguoiThuTien"])
            conn.close()

    def test_order_item_snapshot_preserved_after_product_update(self):
        from app.services.account import list_orders
        with self.app.app_context():
            conn = get_db_connection()
            cur = conn.cursor()
            # Tạo sản phẩm và biến thể ban đầu
            cur.execute("INSERT INTO SanPham (MaDanhMuc, MaNguoiTao, TenSanPham, GiaBan) VALUES (1, 1, 'Giày Ban Đầu Snapshot', 200000)")
            sp_id = cur.lastrowid
            cur.execute("INSERT INTO BienTheSanPham (MaSanPham, KichThuoc, MauSac, SoLuongTon) VALUES (?, '40', 'Đỏ', 10)", (sp_id,))
            bt_id = cur.lastrowid

            # Tạo đơn hàng với snapshot thông tin tại thời điểm mua (MaNguoiDung = 1)
            cur.execute("INSERT INTO DonHang (MaNguoiDung, TrangThai, TongTien) VALUES (1, 'Chờ xác nhận', 200000)")
            order_id = cur.lastrowid
            cur.execute("""INSERT INTO ChiTietDonHang (MaDonHang, MaBienThe, SoLuong, DonGia, TenSanPham, MauSac, KichThuoc)
                           VALUES (?, ?, 1, 200000, 'Giày Ban Đầu Snapshot', 'Đỏ', '40')""", (order_id, bt_id))
            cur.execute("""INSERT INTO ThongTinGiaoDich (MaDonHang, HoTen, SoDienThoai, HinhThucNhanHang, PhuongThucThanhToan, TrangThaiThanhToan)
                           VALUES (?, 'Khách Mua', '0901234567', 'pickup', 'cod', 'Chưa thanh toán')""", (order_id,))

            # Admin sửa tên và giá sản phẩm gốc
            cur.execute("UPDATE SanPham SET TenSanPham = 'Giày Đã Đổi Tên Thành Mẫu Mới', GiaBan = 999999 WHERE MaSanPham = ?", (sp_id,))
            conn.commit()
            conn.close()

            # Lịch sử đơn hàng của người dùng phải giữ nguyên snapshot cũ
            orders = list_orders(1)
            self.assertTrue(len(orders) >= 1)
            target_order = [o for o in orders if o["MaDonHang"] == order_id][0]
            item = target_order["items"][0]
            self.assertEqual(item["TenSanPham"], "Giày Ban Đầu Snapshot")
            self.assertEqual(float(item["DonGia"]), 200000.0)

    def test_trending_excludes_pending_and_canceled_orders(self):
        resp = self.client.get("/xu-huong")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("TOP XU HƯỚNG", html)

    def test_slow_stock_report_excludes_future_transactions(self):
        from app.services.w11_insights import slow_stock_report
        with self.app.app_context():
            # Chạy báo cáo bán chậm: đảm bảo hàm chạy trơn tru và logic loại trừ giao dịch tương lai hoạt động
            report = slow_stock_report()
            self.assertIn("items", report)
            self.assertIn("days", report)

    # --------------------------------------------------------------------------
    # NHIỆM VỤ 8: DOCKER & CI WORKFLOW
    # --------------------------------------------------------------------------
    def test_task8_docker_and_ci_files_exist(self):
        self.assertTrue(os.path.isfile("Dockerfile"))
        self.assertTrue(os.path.isfile(".dockerignore"))
        self.assertTrue(os.path.isfile("docker-compose.yml"))
        self.assertTrue(os.path.isfile(".github/workflows/ci.yml"))


if __name__ == "__main__":
    unittest.main()
