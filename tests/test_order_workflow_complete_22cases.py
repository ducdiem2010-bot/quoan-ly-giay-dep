"""Bộ kiểm thử tự động toàn diện 22 ca kiểm thử (TC01 - TC22) cho Quy trình Đơn hàng,
Giao nhận, Thanh toán, Tồn kho, Bảo mật phân quyền và Thống kê.
Dự án: Website Quản lý Cửa hàng Giày dép - Nhóm 6.
"""
import sqlite3
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app import create_app
from app.db import query_all, query_one
from app.services.order_ops import (
    confirm_order_stock, start_order_shipping, mark_order_delivered,
    record_order_payment, complete_order_status, cancel_order_stock,
    ensure_order_transaction_info, OrderOperationError
)
from app.services.checkout import create_pending_order
from app.services.dashboard import get_dashboard_stats
from app.services.best_sellers import get_best_sellers_v1


class TestOrderWorkflowComplete22Cases(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "test_workflow_22.sqlite3")
        self.app = create_app({
            "TESTING": True,
            "DATABASE": self.db_path,
            "SECRET_KEY": "test-workflow-22-secret",
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

    def _create_sample_order(self, qty=1, variant_id=1, user_id=3, full_name="Nguyễn Văn Test", phone="0987654321"):
        form_data = {
            "full_name": full_name,
            "phone": phone,
            "email": "test@example.com",
            "fulfillment": "delivery",
            "address": "123 Đường Test, Hà Nội",
            "payment_method": "cod",
            "note": "Giao giờ hành chính"
        }
        return create_pending_order(form_data, {variant_id: qty}, user_id=user_id)

    # --------------------------------------------------------------------------
    # TC01: Thanh toán đơn 'Chờ xác nhận' bị từ chối (Lỗi 1)
    # --------------------------------------------------------------------------
    def test_tc01_payment_rejected_on_pending_order(self):
        with self.app.app_context():
            order_id = self._create_sample_order()
            order = query_one("SELECT TrangThai FROM DonHang WHERE MaDonHang=?", (order_id,))
            self.assertEqual(order["TrangThai"], "Chờ xác nhận")

            with self.assertRaises(OrderOperationError) as ctx:
                record_order_payment(order_id, user_id=1)
            self.assertIn("Chờ xác nhận", str(ctx.exception))

            tg = query_one("SELECT TrangThaiThanhToan FROM ThongTinGiaoDich WHERE MaDonHang=?", (order_id,))
            self.assertEqual(tg["TrangThaiThanhToan"], "Chưa thanh toán")

    # --------------------------------------------------------------------------
    # TC02: Hoàn thành đơn 'Chờ xác nhận' bị từ chối
    # --------------------------------------------------------------------------
    def test_tc02_complete_rejected_on_pending_order(self):
        with self.app.app_context():
            order_id = self._create_sample_order()
            with self.assertRaises(OrderOperationError) as ctx:
                complete_order_status(order_id, user_id=1)
            self.assertIn("Chờ xác nhận", str(ctx.exception))

            order = query_one("SELECT TrangThai FROM DonHang WHERE MaDonHang=?", (order_id,))
            self.assertEqual(order["TrangThai"], "Chờ xác nhận")

    # --------------------------------------------------------------------------
    # TC03: Hoàn thành đơn chưa thanh toán bị từ chối (Lỗi 2)
    # --------------------------------------------------------------------------
    def test_tc03_complete_rejected_when_unpaid(self):
        with self.app.app_context():
            order_id = self._create_sample_order()
            confirm_order_stock(order_id, user_id=1)
            start_order_shipping(order_id, user_id=1)
            mark_order_delivered(order_id, user_id=1)

            # Đơn đã xác nhận, đã giao nhưng chưa thanh toán
            with self.assertRaises(OrderOperationError) as ctx:
                complete_order_status(order_id, user_id=1)
            self.assertIn("chưa được thanh toán", str(ctx.exception))

            order = query_one("SELECT TrangThai FROM DonHang WHERE MaDonHang=?", (order_id,))
            self.assertEqual(order["TrangThai"], "Đã xác nhận")

    # --------------------------------------------------------------------------
    # TC04: Xác nhận đơn hợp lệ (trừ kho, lưu NguoiXacNhan/ThoiGianXacNhan)
    # --------------------------------------------------------------------------
    def test_tc04_confirm_order_deducts_stock_and_records_actor(self):
        with self.app.app_context():
            stock_before = query_one("SELECT SoLuongTon FROM BienTheSanPham WHERE MaBienThe=1")["SoLuongTon"]
            order_id = self._create_sample_order(qty=2, variant_id=1)

            res = confirm_order_stock(order_id, user_id=2)
            self.assertTrue(res)

            order = query_one("SELECT TrangThai, NguoiXacNhan, ThoiGianXacNhan, LichSuXuLy FROM DonHang WHERE MaDonHang=?", (order_id,))
            self.assertEqual(order["TrangThai"], "Đã xác nhận")
            self.assertEqual(order["NguoiXacNhan"], 2)
            self.assertIsNotNone(order["ThoiGianXacNhan"])
            self.assertIn("Xác nhận", order["LichSuXuLy"])

            stock_after = query_one("SELECT SoLuongTon FROM BienTheSanPham WHERE MaBienThe=1")["SoLuongTon"]
            self.assertEqual(stock_after, stock_before - 2)

    # --------------------------------------------------------------------------
    # TC05: Chặn thanh toán trùng trên đơn đã thanh toán
    # --------------------------------------------------------------------------
    def test_tc05_prevent_double_payment(self):
        with self.app.app_context():
            order_id = self._create_sample_order()
            confirm_order_stock(order_id, user_id=1)
            # Thanh toán lần 1
            res1 = record_order_payment(order_id, user_id=1)
            self.assertTrue(res1)

            # Thanh toán lần 2 -> từ chối
            with self.assertRaises(OrderOperationError) as ctx:
                record_order_payment(order_id, user_id=1)
            self.assertIn("không thể ghi trùng", str(ctx.exception))

    # --------------------------------------------------------------------------
    # TC06: Chặn thanh toán đơn đã hủy
    # --------------------------------------------------------------------------
    def test_tc06_payment_rejected_on_cancelled_order(self):
        with self.app.app_context():
            order_id = self._create_sample_order()
            cancel_order_stock(order_id, user_id=1, reason="Khách hủy đơn")

            with self.assertRaises(OrderOperationError) as ctx:
                record_order_payment(order_id, user_id=1)
            self.assertIn("đã bị hủy", str(ctx.exception))

            tg = query_one("SELECT TrangThaiThanhToan FROM ThongTinGiaoDich WHERE MaDonHang=?", (order_id,))
            self.assertEqual(tg["TrangThaiThanhToan"], "Chưa thanh toán")

    # --------------------------------------------------------------------------
    # TC07: Chặn thanh toán đơn đã hoàn thành (Lỗi 3)
    # --------------------------------------------------------------------------
    def test_tc07_payment_rejected_on_completed_order(self):
        with self.app.app_context():
            order_id = self._create_sample_order()
            confirm_order_stock(order_id, user_id=1)
            record_order_payment(order_id, user_id=1)
            start_order_shipping(order_id, user_id=1)
            mark_order_delivered(order_id, user_id=1)
            complete_order_status(order_id, user_id=1)

            order = query_one("SELECT TrangThai FROM DonHang WHERE MaDonHang=?", (order_id,))
            self.assertEqual(order["TrangThai"], "Hoàn thành")

            # Cố thanh toán lần nữa khi đã hoàn thành
            with self.assertRaises(OrderOperationError) as ctx:
                record_order_payment(order_id, user_id=1)
            self.assertTrue("đã hoàn thành" in str(ctx.exception) or "không thể ghi trùng" in str(ctx.exception))

    # --------------------------------------------------------------------------
    # TC08: Chặn nhảy cóc giao hàng từ 'Chưa giao' sang 'Đã giao' (Lỗi 5)
    # --------------------------------------------------------------------------
    def test_tc08_prevent_shipping_skip_to_delivered(self):
        with self.app.app_context():
            order_id = self._create_sample_order()
            confirm_order_stock(order_id, user_id=1)

            # Cố gọi mark_order_delivered khi chưa bắt đầu giao (chưa qua 'Đang giao')
            with self.assertRaises(OrderOperationError) as ctx:
                mark_order_delivered(order_id, user_id=1)
            self.assertIn("chưa xuất kho giao hàng", str(ctx.exception))

            order = query_one("SELECT TrangThaiGiaoHang FROM DonHang WHERE MaDonHang=?", (order_id,))
            self.assertEqual(order["TrangThaiGiaoHang"], "Chưa giao")

    # --------------------------------------------------------------------------
    # TC09: Đơn đã giao nhưng chưa thanh toán không được hoàn thành (Lỗi 2, Lỗi 5)
    # --------------------------------------------------------------------------
    def test_tc09_delivered_but_unpaid_cannot_complete(self):
        with self.app.app_context():
            order_id = self._create_sample_order()
            confirm_order_stock(order_id, user_id=1)
            start_order_shipping(order_id, user_id=1)
            mark_order_delivered(order_id, user_id=1)

            tg = query_one("SELECT TrangThaiThanhToan FROM ThongTinGiaoDich WHERE MaDonHang=?", (order_id,))
            self.assertEqual(tg["TrangThaiThanhToan"], "Chưa thanh toán")

            with self.assertRaises(OrderOperationError) as ctx:
                complete_order_status(order_id, user_id=1)
            self.assertIn("chưa được thanh toán", str(ctx.exception))

    # --------------------------------------------------------------------------
    # TC10: Đơn chưa giao hàng (hoặc đang giao) không được hoàn thành (Lỗi 5)
    # --------------------------------------------------------------------------
    def test_tc10_undelivered_cannot_complete(self):
        with self.app.app_context():
            order_id = self._create_sample_order()
            confirm_order_stock(order_id, user_id=1)
            record_order_payment(order_id, user_id=1)

            # 1. Khi đang 'Chưa giao'
            with self.assertRaises(OrderOperationError) as ctx:
                complete_order_status(order_id, user_id=1)
            self.assertIn("chưa được giao thành công", str(ctx.exception))

            # 2. Khi đang 'Đang giao'
            start_order_shipping(order_id, user_id=1)
            with self.assertRaises(OrderOperationError) as ctx:
                complete_order_status(order_id, user_id=1)
            self.assertIn("chưa được giao thành công", str(ctx.exception))

    # --------------------------------------------------------------------------
    # TC11: Hoàn thành đơn khi đủ mọi điều kiện
    # --------------------------------------------------------------------------
    def test_tc11_complete_order_success_all_conditions_met(self):
        with self.app.app_context():
            order_id = self._create_sample_order()
            confirm_order_stock(order_id, user_id=2)
            start_order_shipping(order_id, user_id=2)
            mark_order_delivered(order_id, user_id=2)
            record_order_payment(order_id, user_id=2)

            res = complete_order_status(order_id, user_id=1)
            self.assertTrue(res)

            order = query_one("""SELECT TrangThai, TrangThaiGiaoHang, NguoiHoanThanh, ThoiGianHoanThanh
                                 FROM DonHang WHERE MaDonHang=?""", (order_id,))
            self.assertEqual(order["TrangThai"], "Hoàn thành")
            self.assertEqual(order["TrangThaiGiaoHang"], "Đã giao")
            self.assertEqual(order["NguoiHoanThanh"], 1)
            self.assertIsNotNone(order["ThoiGianHoanThanh"])

    # --------------------------------------------------------------------------
    # TC12: Quy trình COD chuẩn
    # Chờ xác nhận -> Đã xác nhận (trừ kho) -> Đang giao -> Đã giao -> Đã thanh toán -> Hoàn thành
    # --------------------------------------------------------------------------
    def test_tc12_cod_standard_workflow(self):
        with self.app.app_context():
            order_id = self._create_sample_order()
            # 1. Chờ xác nhận
            o = query_one("SELECT TrangThai, TrangThaiGiaoHang FROM DonHang WHERE MaDonHang=?", (order_id,))
            self.assertEqual(o["TrangThai"], "Chờ xác nhận")
            self.assertEqual(o["TrangThaiGiaoHang"], "Chưa giao")

            # 2. Xác nhận đơn & trừ kho
            confirm_order_stock(order_id, user_id=2)
            o = query_one("SELECT TrangThai FROM DonHang WHERE MaDonHang=?", (order_id,))
            self.assertEqual(o["TrangThai"], "Đã xác nhận")

            # 3. Chuyển giao hàng
            start_order_shipping(order_id, user_id=2)
            o = query_one("SELECT TrangThaiGiaoHang FROM DonHang WHERE MaDonHang=?", (order_id,))
            self.assertEqual(o["TrangThaiGiaoHang"], "Đang giao")

            # 4. Giao hàng thành công
            mark_order_delivered(order_id, user_id=2)
            o = query_one("SELECT TrangThaiGiaoHang FROM DonHang WHERE MaDonHang=?", (order_id,))
            self.assertEqual(o["TrangThaiGiaoHang"], "Đã giao")

            # 5. Thu tiền COD
            record_order_payment(order_id, user_id=2)
            tg = query_one("SELECT TrangThaiThanhToan FROM ThongTinGiaoDich WHERE MaDonHang=?", (order_id,))
            self.assertEqual(tg["TrangThaiThanhToan"], "Đã thanh toán")

            # 6. Hoàn thành
            complete_order_status(order_id, user_id=1)
            o = query_one("SELECT TrangThai FROM DonHang WHERE MaDonHang=?", (order_id,))
            self.assertEqual(o["TrangThai"], "Hoàn thành")

    # --------------------------------------------------------------------------
    # TC13: Quy trình trả trước chuẩn (Prepaid)
    # Chờ xác nhận -> Đã xác nhận (trừ kho) -> Đã thanh toán -> Đang giao -> Đã giao -> Hoàn thành
    # --------------------------------------------------------------------------
    def test_tc13_prepaid_standard_workflow(self):
        with self.app.app_context():
            order_id = self._create_sample_order()
            # 1. Xác nhận đơn & trừ kho
            confirm_order_stock(order_id, user_id=2)

            # 2. Khách chuyển khoản trước / ghi nhận thanh toán
            record_order_payment(order_id, user_id=2)
            tg = query_one("SELECT TrangThaiThanhToan FROM ThongTinGiaoDich WHERE MaDonHang=?", (order_id,))
            self.assertEqual(tg["TrangThaiThanhToan"], "Đã thanh toán")

            # 3. Đóng gói & xuất kho giao
            start_order_shipping(order_id, user_id=2)
            o = query_one("SELECT TrangThaiGiaoHang FROM DonHang WHERE MaDonHang=?", (order_id,))
            self.assertEqual(o["TrangThaiGiaoHang"], "Đang giao")

            # 4. Khách nhận hàng thành công
            mark_order_delivered(order_id, user_id=2)
            o = query_one("SELECT TrangThaiGiaoHang FROM DonHang WHERE MaDonHang=?", (order_id,))
            self.assertEqual(o["TrangThaiGiaoHang"], "Đã giao")

            # 5. Hoàn thành
            complete_order_status(order_id, user_id=1)
            o = query_one("SELECT TrangThai FROM DonHang WHERE MaDonHang=?", (order_id,))
            self.assertEqual(o["TrangThai"], "Hoàn thành")

    # --------------------------------------------------------------------------
    # TC14: không cho ghi thanh toán bằng người nhận giả thay cho giao dịch thật.
    # --------------------------------------------------------------------------
    def test_tc14_demo_fake_data_cannot_confirm_payment(self):
        with self.app.app_context():
            order_id = self._create_sample_order(full_name="Khách hàng", phone="0000000000")
            confirm_order_stock(order_id, user_id=1)
            with self.assertRaises(OrderOperationError):
                record_order_payment(order_id, user_id=1)
            tx = query_one('SELECT TrangThaiThanhToan FROM ThongTinGiaoDich WHERE MaDonHang=?', (order_id,))
            self.assertEqual(tx['TrangThaiThanhToan'], 'Chưa thanh toán')

    # --------------------------------------------------------------------------
    # TC15: Giả lập xác nhận thanh toán khi demo hoạt động đúng
    # --------------------------------------------------------------------------
    def test_tc15_simulated_payment_action_by_staff_or_admin(self):
        with self.app.app_context():
            order_id = self._create_sample_order()
            confirm_order_stock(order_id, user_id=2)

            # Seller/Admin thực hiện ghi nhận thanh toán giả lập
            record_order_payment(order_id, user_id=2)
            tg = query_one("SELECT TrangThaiThanhToan, NguoiThuTien, ThoiGianThanhToan FROM ThongTinGiaoDich WHERE MaDonHang=?", (order_id,))
            self.assertEqual(tg["TrangThaiThanhToan"], "Đã thanh toán")
            self.assertEqual(tg["NguoiThuTien"], 2)
            self.assertIsNotNone(tg["ThoiGianThanhToan"])

    # --------------------------------------------------------------------------
    # TC16: Hoàn thành đơn khi thiếu thông tin giao dịch bị từ chối (Lỗi 4)
    # --------------------------------------------------------------------------
    def test_tc16_complete_rejected_when_transaction_info_missing(self):
        with self.app.app_context():
            order_id = self._create_sample_order()
            confirm_order_stock(order_id, user_id=1)
            start_order_shipping(order_id, user_id=1)
            mark_order_delivered(order_id, user_id=1)

            # Xóa hoặc làm rỗng thông tin ThongTinGiaoDich
            conn = sqlite3.connect(self.db_path)
            conn.execute("UPDATE ThongTinGiaoDich SET HoTen='', SoDienThoai='' WHERE MaDonHang=?", (order_id,))
            conn.commit()
            conn.close()

            with self.assertRaises(OrderOperationError) as ctx:
                complete_order_status(order_id, user_id=1)
            self.assertIn("chưa có thông tin giao dịch", str(ctx.exception))

            # Bổ sung thông tin demo qua ensure_order_transaction_info
            ensure_order_transaction_info(order_id, user_id=1, full_name="Khách Hàng Mới", phone="0912345678")
            record_order_payment(order_id, user_id=1)
            res = complete_order_status(order_id, user_id=1)
            self.assertTrue(res)

    # --------------------------------------------------------------------------
    # TC17: Thống kê chính xác: đơn chưa hoàn thành hoặc chưa giao/thanh toán không tính doanh thu
    # --------------------------------------------------------------------------
    def test_tc17_statistics_excludes_incomplete_or_future_orders(self):
        with self.app.app_context():
            # Đơn 1: Đã xác nhận nhưng chưa hoàn thành
            order1 = self._create_sample_order(qty=1, variant_id=1)
            confirm_order_stock(order1, user_id=1)

            # Đơn 2: Đã hoàn thành hợp lệ (đầy đủ giao + thanh toán) cho sản phẩm 2 (biến thể 4)
            order2 = self._create_sample_order(qty=1, variant_id=4)
            confirm_order_stock(order2, user_id=1)
            start_order_shipping(order2, user_id=1)
            mark_order_delivered(order2, user_id=1)
            record_order_payment(order2, user_id=1)
            complete_order_status(order2, user_id=1)

            # Đơn 3: Hoàn thành giả tạo nhưng chưa thanh toán cho sản phẩm 3 (biến thể 7)
            conn = sqlite3.connect(self.db_path)
            conn.execute("INSERT INTO DonHang (MaDonHang, MaNguoiDung, NgayDat, TrangThai, TrangThaiGiaoHang, TongTien) VALUES (777, 1, CURRENT_TIMESTAMP, 'Hoàn thành', 'Đã giao', 5000000)")
            conn.execute("INSERT INTO ThongTinGiaoDich (MaDonHang, HoTen, SoDienThoai, HinhThucNhanHang, PhuongThucThanhToan, TrangThaiThanhToan) VALUES (777, 'A', '1', 'delivery', 'cod', 'Chưa thanh toán')")
            conn.execute("INSERT INTO ChiTietDonHang (MaDonHang, MaBienThe, SoLuong, DonGia) VALUES (777, 7, 5, 1000000)")
            conn.commit()
            conn.close()

            # Thống kê Dashboard
            stats = get_dashboard_stats()
            # completed_order_value không được tính đơn 777
            self.assertLess(stats["completed_order_value"], 5000000)

            # Bestsellers chỉ có sản phẩm 2 từ đơn 2, không được tính sản phẩm 3 từ đơn 777
            best = get_best_sellers_v1(10)
            best_pids = [b["MaSanPham"] for b in best]
            prod7 = query_one("SELECT MaSanPham FROM BienTheSanPham WHERE MaBienThe=7")["MaSanPham"]
            self.assertNotIn(prod7, best_pids)
            self.assertIn(2, best_pids)

    # --------------------------------------------------------------------------
    # TC18: Lịch sử thao tác không bị ghi đè (Preserve Actor History)
    # --------------------------------------------------------------------------
    def test_tc18_actor_history_preserved_without_overwriting(self):
        with self.app.app_context():
            order_id = self._create_sample_order()
            # User 1 xác nhận
            confirm_order_stock(order_id, user_id=1)
            # User 2 giao hàng
            start_order_shipping(order_id, user_id=2)
            # User 2 xác nhận giao
            mark_order_delivered(order_id, user_id=2)
            # User 1 thu tiền
            record_order_payment(order_id, user_id=1)
            # User 1 hoàn thành
            complete_order_status(order_id, user_id=1)

            order = query_one("""SELECT NguoiXacNhan, NguoiGiaoHang, NguoiXacNhanGiao, NguoiHoanThanh, LichSuXuLy
                                 FROM DonHang WHERE MaDonHang=?""", (order_id,))
            self.assertEqual(order["NguoiXacNhan"], 1)
            self.assertEqual(order["NguoiGiaoHang"], 2)
            self.assertEqual(order["NguoiXacNhanGiao"], 2)
            self.assertEqual(order["NguoiHoanThanh"], 1)

            tg = query_one("SELECT NguoiThuTien FROM ThongTinGiaoDich WHERE MaDonHang=?", (order_id,))
            self.assertEqual(tg["NguoiThuTien"], 1)

            # Lịch sử xử lý ghi nhận đầy đủ tất cả các bước
            log = order["LichSuXuLy"]
            self.assertIn("Xác nhận", log)
            self.assertIn("Bắt đầu giao", log)
            self.assertIn("Xác nhận giao hàng", log)
            self.assertIn("thu tiền", log)
            self.assertIn("Hoàn thành", log)

    # --------------------------------------------------------------------------
    # TC19: Bảo mật và phân quyền: Khách hàng / Truy cập trái phép bị chặn
    # --------------------------------------------------------------------------
    def test_tc19_unauthorized_direct_post_blocked(self):
        with self.app.app_context():
            order_id = self._create_sample_order()

        # 1. Chưa đăng nhập gọi POST /orders/<id>/confirm -> chuyển hướng login
        res = self.client.post(f"/orders/{order_id}/confirm", data={"csrf_token": "fake"}, follow_redirects=False)
        self.assertIn(res.status_code, (302, 400))

        # 2. Khách hàng thường gọi POST /orders/<id>/confirm -> bị 403 Forbidden
        self._login("khach@shop.vn")
        with self.client.session_transaction() as sess:
            token = sess["_csrf"]
        res = self.client.post(f"/orders/{order_id}/confirm", data={"csrf_token": token}, follow_redirects=False)
        self.assertEqual(res.status_code, 403)

        # 3. Nhân viên gọi đúng quyền -> 302 chuyển hướng thành công
        self.client.post("/logout", data={"csrf_token": token})
        self._login("minh@shop.vn")
        with self.client.session_transaction() as sess:
            token = sess["_csrf"]
        res = self.client.post(f"/orders/{order_id}/confirm", data={"csrf_token": token}, follow_redirects=False)
        self.assertEqual(res.status_code, 302)

    # --------------------------------------------------------------------------
    # TC20: Xử lý đồng thời (Concurrency): không race condition / không âm kho
    # --------------------------------------------------------------------------
    def test_tc20_concurrency_order_confirmation(self):
        with self.app.app_context():
            # Đặt tồn kho biến thể 8 là đúng 1
            conn = sqlite3.connect(self.db_path)
            conn.execute("UPDATE BienTheSanPham SET SoLuongTon=1 WHERE MaBienThe=8")
            conn.commit()
            conn.close()

            # Tạo 2 đơn hàng riêng biệt cùng mua 1 chiếc biến thể 8
            order1 = self._create_sample_order(qty=1, variant_id=8)
            order2 = self._create_sample_order(qty=1, variant_id=8)

            success_list = []
            error_list = []

            def try_confirm(oid):
                with self.app.app_context():
                    try:
                        confirm_order_stock(oid, user_id=1)
                        success_list.append(oid)
                    except Exception as exc:
                        error_list.append(str(exc))

            t1 = threading.Thread(target=try_confirm, args=(order1,))
            t2 = threading.Thread(target=try_confirm, args=(order2,))
            t1.start()
            t2.start()
            t1.join()
            t2.join()

            # Chỉ đúng 1 đơn thành công, đơn kia bị chặn thiếu hàng
            self.assertEqual(len(success_list), 1)
            self.assertEqual(len(error_list), 1)
            self.assertTrue("không đủ hàng tồn kho" in error_list[0] or "busy" in error_list[0].lower() or "locked" in error_list[0].lower())

            stock_final = query_one("SELECT SoLuongTon FROM BienTheSanPham WHERE MaBienThe=8")["SoLuongTon"]
            self.assertEqual(stock_final, 0)  # Tồn kho không bao giờ bị âm

    # --------------------------------------------------------------------------
    # TC21: Chặn hủy đơn đã thanh toán
    # --------------------------------------------------------------------------
    def test_tc21_cancel_paid_order_waits_for_refund(self):
        with self.app.app_context():
            order_id = self._create_sample_order()
            confirm_order_stock(order_id, user_id=1)
            record_order_payment(order_id, user_id=1)

            cancel_order_stock(order_id, user_id=1, reason="Khách đổi ý")
            order = query_one("SELECT TrangThai,TrangThaiHoanTien FROM DonHang WHERE MaDonHang=?", (order_id,))
            self.assertEqual(order["TrangThai"], "Đã hủy")
            self.assertEqual(order["TrangThaiHoanTien"], "Chờ xử lý hoàn tiền")
            self.assertEqual(query_one('SELECT COUNT(*) AS n FROM HoanTienGiaoDich WHERE MaDonHang=?',(order_id,))['n'],0)

    # --------------------------------------------------------------------------
    # TC22: Chặn hoàn thành hoặc hủy đơn đã ở trạng thái kết thúc (Đã hủy / Hoàn thành)
    # --------------------------------------------------------------------------
    def test_tc22_cannot_transition_from_terminal_states(self):
        with self.app.app_context():
            # 1. Đơn đã hủy không thể hoàn thành hoặc hủy lại
            order_cancel = self._create_sample_order()
            cancel_order_stock(order_cancel, user_id=1)

            with self.assertRaises(OrderOperationError) as ctx1:
                complete_order_status(order_cancel, user_id=1)
            self.assertIn("đã bị hủy", str(ctx1.exception))

            with self.assertRaises(OrderOperationError) as ctx2:
                cancel_order_stock(order_cancel, user_id=1)
            self.assertIn("đã bị hủy", str(ctx2.exception))

            # 2. Đơn hoàn thành không thể hủy hoặc hoàn thành lại
            order_complete = self._create_sample_order()
            confirm_order_stock(order_complete, user_id=1)
            start_order_shipping(order_complete, user_id=1)
            mark_order_delivered(order_complete, user_id=1)
            record_order_payment(order_complete, user_id=1)
            complete_order_status(order_complete, user_id=1)

            with self.assertRaises(OrderOperationError) as ctx3:
                cancel_order_stock(order_complete, user_id=1)
            self.assertIn("đã hoàn thành", str(ctx3.exception))

            with self.assertRaises(OrderOperationError) as ctx4:
                complete_order_status(order_complete, user_id=1)
            self.assertIn("đã ở trạng thái 'Hoàn thành'", str(ctx4.exception))


if __name__ == "__main__":
    unittest.main()
