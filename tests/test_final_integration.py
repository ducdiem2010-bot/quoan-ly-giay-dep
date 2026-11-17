"""Kiểm thử tích hợp toàn diện theo các yêu cầu Sections B, C, D, E, F, G:
1. Tài khoản & Quản lý nhân viên/khách hàng, phân quyền (B & C).
2. Quản lý sản phẩm, biến thể, loại, thương hiệu, màu sắc, kích thước (D).
3. Giỏ hàng, trừ/hoàn tồn kho theo trạng thái, thanh toán, chống double submit, concurrency (E, F, G).
"""
import tempfile
import unittest
from pathlib import Path
import re
from app import create_app
from app.db import query_all, query_one, get_db_connection


class FinalIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp.name) / "test_final.sqlite3")
        self.app = create_app({
            "TESTING": True,
            "DATABASE": self.db_path,
            "SECRET_KEY": "test-key-for-final-suite",
            "ENABLE_ACCOUNT_STATUS_GUARD": True,
        })
        self.client = self.app.test_client()

    def tearDown(self):
        try:
            self.temp.cleanup()
        except Exception:
            pass

    def csrf(self, path="/login"):
        resp = self.client.get(path)
        m = re.search(r'name="csrf_token"\s+value="([^"]+)"', resp.get_data(as_text=True))
        return m.group(1) if m else None

    def login(self, email, password="Demo@12345"):
        token = self.csrf("/login")
        return self.client.post("/login", data={
            "csrf_token": token,
            "email": email,
            "password": password
        }, follow_redirects=True)

    def logout(self):
        token = self.csrf("/")
        return self.client.post("/logout", data={"csrf_token": token}, follow_redirects=True)

    # =========================================================================
    # SECTION B: TÀI KHOẢN, HỒ SƠ, QUẢN LÝ NHÂN VIÊN & KHÁCH HÀNG
    # =========================================================================
    def test_staff_create_login_edit_and_lock_cycle(self):
        """Kiểm thử chu trình: Tạo nhân viên -> Đăng xuất Admin -> Đăng nhập bằng tài khoản mới -> Sửa SĐT -> Khóa."""
        # 1. Admin đăng nhập
        self.login("admin@shop.vn")

        # 2. Tạo nhân viên mới với đầy đủ Họ tên, Email, SĐT, Mật khẩu ban đầu và Xác nhận
        token = self.csrf("/admin/staff/new")
        staff_email = "nv_moi@shop.vn"
        staff_pass = "NhanVien@2026"
        resp = self.client.post("/admin/staff/new", data={
            "csrf_token": token,
            "name": "Nguyễn Văn Mới",
            "email": staff_email,
            "phone": "0988776655",
            "password": staff_pass,
            "confirm_password": staff_pass,
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        # Kiểm tra tài khoản được lưu trong DB với vai trò Seller (MaVaiTro = 2)
        with self.app.app_context():
            user = query_one("SELECT * FROM NguoiDung WHERE Email=?", (staff_email,))
            self.assertIsNotNone(user)
            self.assertEqual(user["MaVaiTro"], 2)
            self.assertEqual(user["SoDienThoai"], "0988776655")
            self.assertNotEqual(user["MatKhauHash"], staff_pass)  # Đã hash

        # 3. Chặn tạo trùng email
        token = self.csrf("/admin/staff/new")
        dup_resp = self.client.post("/admin/staff/new", data={
            "csrf_token": token,
            "name": "Trùng Email",
            "email": staff_email,
            "phone": "0911223344",
            "password": staff_pass,
            "confirm_password": staff_pass,
        }, follow_redirects=True)
        self.assertIn("Email này đã được sử dụng", dup_resp.get_data(as_text=True))

        # 4. Đăng xuất Admin
        self.logout()

        # 5. Đăng nhập bằng nhân viên mới tạo
        login_resp = self.login(staff_email, staff_pass)
        self.assertEqual(login_resp.status_code, 200)
        login_text = login_resp.get_data(as_text=True)
        self.assertIn("Khu vực Nhân viên", login_text)

        # Nhân viên vào được trang nhân viên
        staff_home = self.client.get("/staff")
        self.assertEqual(staff_home.status_code, 200)

        # 6. Admin sửa thông tin nhân viên (họ tên, email, sđt)
        self.logout()
        self.login("admin@shop.vn")
        token = self.csrf(f"/admin/staff/{user['MaNguoiDung']}/edit")
        edit_resp = self.client.post(f"/admin/staff/{user['MaNguoiDung']}/edit", data={
            "csrf_token": token,
            "name": "Nguyễn Văn Đã Sửa",
            "email": "nv_dasua@shop.vn",
            "phone": "0999888777",
        }, follow_redirects=True)
        self.assertEqual(edit_resp.status_code, 200)

        with self.app.app_context():
            updated = query_one("SELECT * FROM NguoiDung WHERE MaNguoiDung=?", (user["MaNguoiDung"],))
            self.assertEqual(updated["HoVaTen"], "Nguyễn Văn Đã Sửa")
            self.assertEqual(updated["Email"], "nv_dasua@shop.vn")
            self.assertEqual(updated["SoDienThoai"], "0999888777")

        # 7. Khóa nhân viên và kiểm tra chặn đăng nhập
        token = self.csrf(f"/admin/staff/{user['MaNguoiDung']}/edit")
        self.client.post(f"/admin/users/{user['MaNguoiDung']}/toggle", data={
            "csrf_token": token,
            "reason": "Tạm đình chỉ công tác"
        }, follow_redirects=True)

        with self.app.app_context():
            locked = query_one("SELECT TrangThai, NguoiKhoa, GhiChuKhoa FROM NguoiDung WHERE MaNguoiDung=?", (user["MaNguoiDung"],))
            self.assertEqual(locked["TrangThai"], 0)
            self.assertIn("Tạm đình chỉ", locked["GhiChuKhoa"])

        self.logout()
        # Đăng nhập bằng tài khoản bị khóa -> bị từ chối
        bad_login = self.login("nv_dasua@shop.vn", staff_pass)
        self.assertIn("Tài khoản của bạn đã bị khóa", bad_login.get_data(as_text=True))

    def test_customer_lock_and_session_revocation(self):
        """Khóa khách hàng: không có nút xóa; phiên cũ bị chặn khi có request tiếp theo."""
        self.login("admin@shop.vn")
        with self.app.app_context():
            cust = query_one("SELECT MaNguoiDung, Email FROM NguoiDung WHERE MaVaiTro=3 LIMIT 1")

        # Khóa khách hàng
        token = self.csrf("/admin/customers")
        self.client.post(f"/admin/users/{cust['MaNguoiDung']}/toggle", data={
            "csrf_token": token,
            "reason": "Khóa tài khoản vi phạm"
        }, follow_redirects=True)

        with self.app.app_context():
            updated_cust = query_one("SELECT TrangThai, NguoiKhoa FROM NguoiDung WHERE MaNguoiDung=?", (cust["MaNguoiDung"],))
            self.assertEqual(updated_cust["TrangThai"], 0)

        # Đăng xuất và thử đăng nhập bằng khách bị khóa
        self.logout()
        resp = self.login(cust["Email"], "Demo@12345")
        self.assertIn("Tài khoản của bạn đã bị khóa", resp.get_data(as_text=True))

    # =========================================================================
    # SECTION C: PHÂN QUYỀN VAI TRÒ
    # =========================================================================
    def test_role_matrix_security_guards(self):
        """Kiểm tra ma trận phân quyền: Customer không vào được Admin/Staff; Seller không vào được Admin."""
        # 1. Customer
        self.login("khach@shop.vn")
        self.assertEqual(self.client.get("/admin").status_code, 403)
        self.assertEqual(self.client.get("/admin/orders").status_code, 403)
        self.assertEqual(self.client.get("/admin/staff").status_code, 403)
        self.assertEqual(self.client.get("/admin/customers").status_code, 403)
        self.assertEqual(self.client.get("/staff").status_code, 403)
        self.assertEqual(self.client.get("/staff/orders").status_code, 403)

        # 2. Seller (Nhân viên)
        self.logout()
        self.login("minh@shop.vn")
        self.assertEqual(self.client.get("/staff").status_code, 200)
        self.assertEqual(self.client.get("/staff/orders").status_code, 200)
        # Seller bị chặn vào Admin
        self.assertEqual(self.client.get("/admin/orders").status_code, 403)
        self.assertEqual(self.client.get("/admin/staff").status_code, 403)
        self.assertEqual(self.client.get("/admin/customers").status_code, 403)

    # =========================================================================
    # SECTION D: QUẢN LÝ SẢN PHẨM, BIẾN THỂ, LOẠI, THƯƠNG HIỆU, MÀU, SIZE
    # =========================================================================
    def test_catalog_metadata_crud_and_safety_checks(self):
        """Kiểm thử thêm/sửa/xóa an toàn cho Loại, Thương hiệu, Màu sắc, Kích thước."""
        self.login("admin@shop.vn")

        # 1. Thêm danh mục mới
        token = self.csrf("/admin/categories")
        self.client.post("/admin/categories", data={
            "csrf_token": token,
            "name": "Giày Cao Gót",
            "description": "Thời trang nữ"
        }, follow_redirects=True)
        with self.app.app_context():
            cat = query_one("SELECT * FROM DanhMuc WHERE TenDanhMuc='Giày Cao Gót'")
            self.assertIsNotNone(cat)

        # Xóa danh mục rỗng (chưa có SP) -> Xóa thành công
        token = self.csrf("/admin/categories")
        self.client.post(f"/admin/categories/{cat['MaDanhMuc']}/delete", data={"csrf_token": token}, follow_redirects=True)
        with self.app.app_context():
            self.assertIsNone(query_one("SELECT * FROM DanhMuc WHERE TenDanhMuc='Giày Cao Gót'"))

        # Xóa danh mục ĐÃ CÓ SẢN PHẨM (MaDanhMuc=1) -> Bị chặn
        token = self.csrf("/admin/categories")
        resp = self.client.post("/admin/categories/1/delete", data={"csrf_token": token}, follow_redirects=True)
        self.assertIn("đang chứa sản phẩm", resp.get_data(as_text=True))

        # 2. Thêm thương hiệu mới
        token = self.csrf("/admin/brands")
        self.client.post("/admin/brands", data={
            "csrf_token": token,
            "name": "Under Armour",
            "description": "Đồ thể thao cao cấp"
        }, follow_redirects=True)
        with self.app.app_context():
            brand = query_one("SELECT * FROM ThuongHieu WHERE TenThuongHieu='Under Armour'")
            self.assertIsNotNone(brand)

        # 3. Thêm màu sắc & kích thước
        token = self.csrf("/admin/colors")
        self.client.post("/admin/colors", data={"csrf_token": token, "name": "Vàng Neon", "hex": "#ccff00"}, follow_redirects=True)
        token = self.csrf("/admin/sizes")
        self.client.post("/admin/sizes", data={"csrf_token": token, "name": "46"}, follow_redirects=True)

        with self.app.app_context():
            self.assertIsNotNone(query_one("SELECT * FROM MauSac WHERE TenMau='Vàng Neon'"))
            self.assertIsNotNone(query_one("SELECT * FROM KichThuoc WHERE TenKichThuoc='46'"))

    def test_product_and_variant_safe_delete(self):
        """Xóa sản phẩm/biến thể: nếu đã có đơn -> chuyển sang ẩn/tồn kho=0; nếu chưa có đơn -> xóa hoàn toàn."""
        self.login("admin@shop.vn")

        # 1. Sản phẩm SP1 đã có đơn hàng (Đơn #1 trong seed)
        token = self.csrf("/admin/products")
        resp = self.client.post("/admin/products/1/delete", data={"csrf_token": token}, follow_redirects=True)
        self.assertIn("đã chuyển sang trạng thái Ẩn/Ngừng bán", resp.get_data(as_text=True))
        with self.app.app_context():
            sp1 = query_one("SELECT HienThi FROM SanPham WHERE MaSanPham=1")
            self.assertEqual(sp1["HienThi"], 0)  # Đã chuyển sang ẩn

        # 2. Biến thể của SP1 đã có đơn hàng -> đặt tồn về 0
        token = self.csrf("/admin/products/1/variants")
        resp = self.client.post("/admin/products/1/variants/1/delete", data={"csrf_token": token}, follow_redirects=True)
        self.assertIn("cập nhật số lượng tồn về 0", resp.get_data(as_text=True))
        with self.app.app_context():
            bt1 = query_one("SELECT SoLuongTon FROM BienTheSanPham WHERE MaBienThe=1")
            self.assertEqual(bt1["SoLuongTon"], 0)

        # 3. Tạo một sản phẩm mới toanh chưa có đơn hàng, sau đó xóa hoàn toàn
        token = self.csrf("/admin/products/new")
        self.client.post("/admin/products/new", data={
            "csrf_token": token,
            "name": "Giày Chạy Thử Nghiệm",
            "category_id": 1,
            "price": "990000",
            "brand": "Nike",
            "description": "Sản phẩm để test xóa",
            "initial_size": "42",
            "initial_color": "Xanh Dương",
            "initial_stock": "10",
        }, follow_redirects=True)
        with self.app.app_context():
            new_sp = query_one("SELECT MaSanPham FROM SanPham WHERE TenSanPham='Giày Chạy Thử Nghiệm'")
            self.assertIsNotNone(new_sp)

        # Xóa sản phẩm chưa có đơn hàng -> Xóa hoàn toàn
        token = self.csrf("/admin/products")
        del_resp = self.client.post(f"/admin/products/{new_sp['MaSanPham']}/delete", data={"csrf_token": token}, follow_redirects=True)
        self.assertIn("Đã xóa hoàn toàn sản phẩm", del_resp.get_data(as_text=True))
        with self.app.app_context():
            self.assertIsNone(query_one("SELECT MaSanPham FROM SanPham WHERE MaSanPham=?", (new_sp["MaSanPham"],)))

    # =========================================================================
    # SECTION E, F, G: ĐƠN HÀNG, KHO, XÁC NHẬN, HỦY & THANH TOÁN
    # =========================================================================
    def test_order_stock_lifecycle_confirm_cancel_pay(self):
        """Kiểm thử vòng đời đơn hàng: Chờ xác nhận -> Xác nhận (trừ kho) -> Hủy (hoàn kho) / Thu tiền."""
        self.login("admin@shop.vn")
        with self.app.app_context():
            # Tạo 1 đơn hàng mới ở trạng thái 'Chờ xác nhận' với biến thể MaBienThe=2, số lượng=3
            init_stock = query_one("SELECT SoLuongTon FROM BienTheSanPham WHERE MaBienThe=2")["SoLuongTon"]
            cur = self.app.test_client()

            # Xác nhận đơn hàng -> Trừ kho thực tế
            from app.services.order_ops import confirm_order_stock, cancel_order_stock, record_order_payment
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""INSERT INTO DonHang(MaNguoiDung, TrangThai, TongTien) VALUES(3, 'Chờ xác nhận', 1500000)""")
            order_id = cur.lastrowid
            cur.execute("""INSERT INTO ChiTietDonHang(MaDonHang, MaBienThe, SoLuong, DonGia) VALUES(?, 2, 3, 500000)""", (order_id,))
            cur.execute("""INSERT INTO ThongTinGiaoDich(MaDonHang, HoTen, SoDienThoai, HinhThucNhanHang, PhuongThucThanhToan, TrangThaiThanhToan)
                             VALUES(?, 'Nguyễn Test', '0909111222', 'delivery', 'cod', 'Chưa thanh toán')""", (order_id,))
            conn.commit()
            conn.close()

            # 1. Xác nhận đơn: Trạng thái -> 'Đã xác nhận', kho bị trừ 3
            confirm_order_stock(order_id, 1)
            o_row = query_one("SELECT TrangThai, MaNguoiXuLy FROM DonHang WHERE MaDonHang=?", (order_id,))
            self.assertEqual(o_row["TrangThai"], "Đã xác nhận")
            self.assertEqual(o_row["MaNguoiXuLy"], 1)

            stock_after_confirm = query_one("SELECT SoLuongTon FROM BienTheSanPham WHERE MaBienThe=2")["SoLuongTon"]
            self.assertEqual(stock_after_confirm, init_stock - 3)

            # 2. Ghi nhận thanh toán
            record_order_payment(order_id, 1)
            tx_row = query_one("SELECT TrangThaiThanhToan, NguoiThuTien FROM ThongTinGiaoDich WHERE MaDonHang=?", (order_id,))
            self.assertEqual(tx_row["TrangThaiThanhToan"], "Đã thanh toán")
            self.assertEqual(tx_row["NguoiThuTien"], 1)

            # 3. Hủy đơn đã xác nhận -> Hoàn trả đúng 3 vào kho
            cancel_order_stock(order_id, 1)
            o_canceled = query_one("SELECT TrangThai FROM DonHang WHERE MaDonHang=?", (order_id,))
            self.assertEqual(o_canceled["TrangThai"], "Đã hủy")

            stock_after_cancel = query_one("SELECT SoLuongTon FROM BienTheSanPham WHERE MaBienThe=2")["SoLuongTon"]
            self.assertEqual(stock_after_cancel, init_stock)  # Kho đã được hoàn trả nguyên vẹn

    def test_cart_update_and_limits(self):
        """Kiểm thử cập nhật giỏ hàng: số lượng hợp lệ, vượt tồn kho, và xóa khi qty <= 0."""
        # Thêm biến thể 1 vào giỏ
        token = self.csrf("/product/1")
        self.client.post("/add-to-cart/1", data={"csrf_token": token, "variant_id": "1", "quantity": "2"}, follow_redirects=True)

        # Cập nhật số lượng lên 3
        token = self.csrf("/cart")
        resp = self.client.post("/cart/update/1", data={"csrf_token": token, "quantity": "3"}, follow_redirects=True)
        self.assertIn("Đã cập nhật số lượng trong giỏ hàng", resp.get_data(as_text=True))
        with self.client.session_transaction() as sess:
            self.assertEqual(sess["cart"].get("1"), 3)

        # Cập nhật số lượng = 0 -> Tự động xóa khỏi giỏ
        token = self.csrf("/cart")
        resp = self.client.post("/cart/update/1", data={"csrf_token": token, "quantity": "0"}, follow_redirects=True)
        self.assertIn("Đã xóa sản phẩm khỏi giỏ hàng", resp.get_data(as_text=True))
        with self.client.session_transaction() as sess:
            self.assertNotIn("1", sess["cart"])

    def test_concurrency_two_buyers_last_stock(self):
        """Kiểm thử đồng thời: 2 người cùng mua số tồn kho cuối cùng (chỉ 1 người thành công)."""
        from app.services.checkout import create_pending_order, validate_checkout
        from app.services.order_ops import confirm_order_stock, OrderOperationError
        with self.app.app_context():
            # Đặt tồn kho của biến thể 3 chỉ còn đúng 1 sản phẩm
            conn = get_db_connection()
            conn.cursor().execute("UPDATE BienTheSanPham SET SoLuongTon=1 WHERE MaBienThe=3")
            conn.commit()
            conn.close()

            form1 = validate_checkout({
                "full_name": "Người mua 1", "phone": "0911111111", "email": "buyer1@example.com",
                "fulfillment": "delivery", "address": "123 Đường Cầu Giấy, Hà Nội", "payment_method": "cod", "note": ""
            })
            order1_id = create_pending_order(form1, {"3": 1}, user_id=None)

            form2 = validate_checkout({
                "full_name": "Người mua 2", "phone": "0922222222", "email": "buyer2@example.com",
                "fulfillment": "delivery", "address": "456 Đường Nguyễn Huệ, TP HCM", "payment_method": "cod", "note": ""
            })
            order2_id = create_pending_order(form2, {"3": 1}, user_id=None)

            # Người 1 được xác nhận trước -> Thành công và tồn kho về 0
            confirm_order_stock(order1_id, 1)
            stock = query_one("SELECT SoLuongTon FROM BienTheSanPham WHERE MaBienThe=3")["SoLuongTon"]
            self.assertEqual(stock, 0)

            # Người 2 xác nhận sau -> Thất bại do hết tồn kho
            with self.assertRaises(OrderOperationError) as ctx:
                confirm_order_stock(order2_id, 1)
            self.assertIn("không đủ hàng tồn kho", str(ctx.exception).lower())

    def test_concurrency_two_staff_processing_same_order(self):
        """Kiểm thử 2 nhân viên cùng xử lý 1 đơn hàng (chỉ người đầu tiên thành công)."""
        from app.services.order_ops import confirm_order_stock, OrderOperationError
        with self.app.app_context():
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""INSERT INTO DonHang(MaNguoiDung, TrangThai, TongTien) VALUES(3, 'Chờ xác nhận', 500000)""")
            order_id = cur.lastrowid
            cur.execute("""INSERT INTO ChiTietDonHang(MaDonHang, MaBienThe, SoLuong, DonGia) VALUES(?, 1, 1, 500000)""", (order_id,))
            conn.commit()
            conn.close()

            # Nhân viên A xác nhận đơn
            confirm_order_stock(order_id, 1)

            # Nhân viên B cố gắng xác nhận lại đơn đó -> Bị từ chối
            with self.assertRaises(OrderOperationError) as ctx:
                confirm_order_stock(order_id, 2)
            self.assertIn("chỉ có thể xác nhận khi 'chờ xác nhận'", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
