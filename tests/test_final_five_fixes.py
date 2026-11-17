"""Bộ kiểm thử xác thực 5 vấn đề cuối cùng và hoàn thiện đóng gói - Nhóm 6."""
import os
import re
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch
from werkzeug.security import generate_password_hash

from app import create_app
from app.db import get_db_connection, init_demo_database
from app.services.checkout import create_pending_order, CheckoutValidationError


class FinalFiveFixesTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_five.sqlite3")
        self.app = create_app({
            "TESTING": True,
            "DATABASE": self.db_path,
            "DB_BACKEND": "sqlite",
            "SECRET_KEY": "test-secret-key-five-fixes-32-chars-min",
        })
        self.client_a = self.app.test_client()
        self.client_b = self.app.test_client()
        with self.app.app_context():
            init_demo_database()
            conn = get_db_connection()
            pwd = generate_password_hash("Password123")
            conn.execute(
                "INSERT INTO NguoiDung (MaVaiTro, HoVaTen, Email, MatKhauHash, TrangThai) VALUES (3, 'Khách A', 'khacha@shop.vn', ?, 1)",
                (pwd,),
            )
            conn.execute(
                "INSERT INTO NguoiDung (MaVaiTro, HoVaTen, Email, MatKhauHash, TrangThai) VALUES (3, 'Khách B', 'khachb@shop.vn', ?, 1)",
                (pwd,),
            )
            self.user_a_id = conn.execute("SELECT MaNguoiDung FROM NguoiDung WHERE Email='khacha@shop.vn'").fetchone()[0]
            self.user_b_id = conn.execute("SELECT MaNguoiDung FROM NguoiDung WHERE Email='khachb@shop.vn'").fetchone()[0]
            conn.commit()
            conn.close()

    def tearDown(self):
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def _get_csrf_and_checkout_token(self, client):
        resp = client.get("/checkout")
        html = resp.get_data(as_text=True)
        csrf_m = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
        tok_m = re.search(r'name="checkout_token"\s+value="([^"]+)"', html)
        return (csrf_m.group(1) if csrf_m else ""), (tok_m.group(1) if tok_m else "")

    # --------------------------------------------------------------------------
    # LỖI 1: CHECKOUT TOKEN - KIỂM TRA QUYỀN SỞ HỮU & CHỐNG TRÙNG
    # --------------------------------------------------------------------------
    def test_1_customer_a_uses_own_token_succeeds_and_replay_is_idempotent(self):
        with self.client_a.session_transaction() as sess:
            sess["user_id"] = self.user_a_id
            sess["user_name"] = "Khách A"
            sess["role"] = "Customer"
            sess["cart"] = {"1": 1}

        csrf_a, tok_a = self._get_csrf_and_checkout_token(self.client_a)
        self.assertTrue(tok_a)

        # Khách A đặt hàng thành công bằng token của A
        resp1 = self.client_a.post("/checkout", data={
            "csrf_token": csrf_a,
            "checkout_token": tok_a,
            "full_name": "Khách A",
            "phone": "0911111111",
            "fulfillment": "pickup",
            "payment_method": "cod",
        }, follow_redirects=False)
        self.assertEqual(resp1.status_code, 302)
        self.assertIn("/checkout/success", resp1.location)

        with self.app.app_context():
            conn = get_db_connection()
            orders_a = conn.execute("SELECT MaDonHang FROM DonHang WHERE CheckoutToken=?", (tok_a,)).fetchall()
            self.assertEqual(len(orders_a), 1)
            order_a_id = orders_a[0][0]
            conn.close()

        # Gửi lại token hợp lệ của chính phiên A (ví dụ bấm Back và gửi lại) -> không tạo đơn thứ 2
        with self.client_a.session_transaction() as sess:
            sess["cart"] = {"1": 1}
        resp2 = self.client_a.post("/checkout", data={
            "csrf_token": csrf_a,
            "checkout_token": tok_a,
            "full_name": "Khách A",
            "phone": "0911111111",
            "fulfillment": "pickup",
            "payment_method": "cod",
        }, follow_redirects=False)
        self.assertEqual(resp2.status_code, 302)
        self.assertIn("/checkout/success", resp2.location)

        with self.app.app_context():
            conn = get_db_connection()
            orders_after = conn.execute("SELECT MaDonHang FROM DonHang WHERE CheckoutToken=?", (tok_a,)).fetchall()
            self.assertEqual(len(orders_after), 1)
            self.assertEqual(orders_after[0][0], order_a_id)
            conn.close()

    def test_2_customer_b_replays_customer_a_token_is_rejected_and_cart_preserved(self):
        # 1. Khách A đặt đơn thành công với token A
        with self.client_a.session_transaction() as sess:
            sess["user_id"] = self.user_a_id
            sess["user_name"] = "Khách A"
            sess["role"] = "Customer"
            sess["cart"] = {"1": 1}

        csrf_a, tok_a = self._get_csrf_and_checkout_token(self.client_a)
        self.client_a.post("/checkout", data={
            "csrf_token": csrf_a,
            "checkout_token": tok_a,
            "full_name": "Khách A",
            "phone": "0911111111",
            "fulfillment": "pickup",
            "payment_method": "cod",
        }, follow_redirects=False)

        # 2. Khách B đăng nhập phiên riêng, có giỏ hàng riêng
        with self.client_b.session_transaction() as sess:
            sess["user_id"] = self.user_b_id
            sess["user_name"] = "Khách B"
            sess["role"] = "Customer"
            sess["cart"] = {"2": 2}

        csrf_b, tok_b = self._get_csrf_and_checkout_token(self.client_b)
        self.assertNotEqual(tok_a, tok_b)

        # 3. Khách B gửi lại token của A
        resp_b = self.client_b.post("/checkout", data={
            "csrf_token": csrf_b,
            "checkout_token": tok_a,
            "full_name": "Khách B",
            "phone": "0922222222",
            "fulfillment": "pickup",
            "payment_method": "cod",
        }, follow_redirects=False)

        # Bị từ chối: không chuyển đến /checkout/success
        self.assertEqual(resp_b.status_code, 302)
        self.assertNotIn("/checkout/success", resp_b.location)

        # Giỏ hàng của B không bị xóa và session B không bị gán đơn của A
        with self.client_b.session_transaction() as sess:
            self.assertEqual(sess.get("cart"), {"2": 2})
            self.assertIsNone(sess.get("last_checkout_order"))

    def test_3_fake_and_empty_tokens_create_no_order_and_keep_cart(self):
        with self.client_b.session_transaction() as sess:
            sess["user_id"] = self.user_b_id
            sess["user_name"] = "Khách B"
            sess["role"] = "Customer"
            sess["cart"] = {"1": 1}

        csrf_b, _ = self._get_csrf_and_checkout_token(self.client_b)

        for bad_token in ("", "fake-token-xyz-999"):
            resp = self.client_b.post("/checkout", data={
                "csrf_token": csrf_b,
                "checkout_token": bad_token,
                "full_name": "Khách B",
                "phone": "0922222222",
                "fulfillment": "pickup",
                "payment_method": "cod",
            }, follow_redirects=False)
            self.assertNotIn("/checkout/success", resp.location)

        with self.client_b.session_transaction() as sess:
            self.assertEqual(sess.get("cart"), {"1": 1})

    def test_4_concurrent_requests_same_token_create_at_most_one_order(self):
        token = "concurrent-token-123456789"
        form_data = {
            "full_name": "Khách Đồng Thời",
            "phone": "0933333333",
            "email": "c@shop.vn",
            "fulfillment": "pickup",
            "address": "",
            "payment_method": "cod",
            "note": "",
        }
        results = []
        errors = []

        def worker():
            try:
                with self.app.app_context():
                    oid = create_pending_order(form_data, {1: 1}, user_id=self.user_a_id, checkout_token=token)
                    results.append(oid)
            except Exception as exc:
                errors.append(exc)

        t1 = threading.Thread(target=worker)
        t2 = threading.Thread(target=worker)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(len(errors), 0, f"Unexpected errors: {errors}")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], results[1])

        with self.app.app_context():
            conn = get_db_connection()
            count = conn.execute("SELECT COUNT(*) FROM DonHang WHERE CheckoutToken=?", (token,)).fetchone()[0]
            self.assertEqual(count, 1)
            conn.close()

    def test_5_service_blocks_stolen_token_cross_user(self):
        token = "service-ownership-token-999"
        form_data = {
            "full_name": "Khách A",
            "phone": "0911111111",
            "email": "",
            "fulfillment": "pickup",
            "address": "",
            "payment_method": "cod",
            "note": "",
        }
        with self.app.app_context():
            create_pending_order(form_data, {1: 1}, user_id=self.user_a_id, checkout_token=token)
            with self.assertRaises(CheckoutValidationError):
                create_pending_order(form_data, {1: 1}, user_id=self.user_b_id, checkout_token=token)

    # --------------------------------------------------------------------------
    # LỖI 2 & 4: DOCKER, SECRET_KEY & HOST CONFIGURATION
    # --------------------------------------------------------------------------
    def test_6_docker_compose_no_hardcoded_secret_and_has_host_0000(self):
        with open("docker-compose.yml", "r", encoding="utf-8") as f:
            dc = f.read()
        self.assertIn("${SECRET_KEY", dc)
        self.assertNotIn("cf94a821e8d641c888927429188371ef", dc)
        self.assertIn("HOST=0.0.0.0", dc)
        self.assertIn("PORT=5000", dc)

        with open("Dockerfile", "r", encoding="utf-8") as f:
            df = f.read()
        self.assertIn("HOST=0.0.0.0", df)
        self.assertIn("PORT=5000", df)

    def test_7_env_example_uses_placeholder_and_production_blocks_it(self):
        with open(".env.example", "r", encoding="utf-8") as f:
            env_ex = f.read()
        self.assertIn("replace-with-random-secret-key", env_ex)
        self.assertNotIn("ec79a61b8f04df9c2c6e7a2b9a1e05d4", env_ex)

        with open(".gitignore", "r", encoding="utf-8") as f:
            gi = f.read()
        self.assertIn(".env", gi)

        with patch.dict(os.environ, {
            "FLASK_ENV": "production",
            "SECRET_KEY": "replace-with-random-secret-key-min-32-chars",
        }):
            with self.assertRaises(RuntimeError):
                create_app()

    # --------------------------------------------------------------------------
    # LỖI 3: SCRIPT SQL SERVER CO CHECKOUTTOKEN & UNIQUE INDEX
    # --------------------------------------------------------------------------
    def test_8_sqlserver_scripts_contain_checkout_token_and_safe_unique_index(self):
        with open("database/init_database_sqlserver.sql", "r", encoding="utf-8") as f:
            init_sql = f.read()
        self.assertIn("CheckoutToken NVARCHAR(100) NULL", init_sql)
        self.assertIn("IX_DonHang_CheckoutToken", init_sql)

        with open("database/upgrade_existing_sqlserver.sql", "r", encoding="utf-8") as f:
            upg_sql = f.read()
        self.assertIn("COL_LENGTH('DonHang', 'CheckoutToken')", upg_sql)
        self.assertIn("IX_DonHang_CheckoutToken", upg_sql)
        self.assertIn("GROUP BY CheckoutToken", upg_sql)


    # --------------------------------------------------------------------------
    # LỖI 1 (BỔ SUNG): KIỂM THỬ NGOẠI LỆ UNIQUE VÀ KHÁCH VÃNG LAI ĐA PHIÊN
    # --------------------------------------------------------------------------
    def test_9_unique_constraint_exception_branch_blocks_unauthorized_user(self):
        token = "token-test-unique-branch-123"
        form_data = {
            "full_name": "Khách A",
            "phone": "0911111111",
            "email": "",
            "fulfillment": "pickup",
            "address": "",
            "payment_method": "cod",
            "note": "",
        }
        with self.app.app_context():
            # 1. Tạo đơn hàng đầu tiên của Khách A với token này
            order_a_id = create_pending_order(form_data, {1: 1}, user_id=self.user_a_id, checkout_token=token)
            self.assertIsInstance(order_a_id, int)

            # 2. Giả lập nhánh ngoại lệ: bỏ qua check đầu và ép gọi INSERT gây lỗi UNIQUE
            # Khách B cố tình dùng token của A -> phải bị từ chối bằng CheckoutValidationError tại nhánh except
            from unittest.mock import patch
            orig_execute = sqlite3.Cursor.execute

            # Lần gọi INSERT gây lỗi UNIQUE constraint
            with patch("app.services.checkout.CHECKOUT_META_SQLITE", "-- skip"):
                # Khi Khách B gọi, nếu pre-check bị bypass hoặc race condition xảy ra:
                with self.assertRaises(CheckoutValidationError) as cm:
                    create_pending_order(form_data, {1: 1}, user_id=self.user_b_id, checkout_token=token)
                self.assertIn("không thuộc về tài khoản hiện tại", str(cm.exception))

            # 3. Khi chính Khách A gửi lại cùng token (idempotency an toàn) -> nhận lại đúng order_a_id
            order_replay = create_pending_order(form_data, {1: 1}, user_id=self.user_a_id, checkout_token=token)
            self.assertEqual(order_replay, order_a_id)

    def test_10_two_different_guest_sessions_cannot_share_checkout_token(self):
        client_guest1 = self.app.test_client()
        client_guest2 = self.app.test_client()

        with client_guest1.session_transaction() as sess1:
            sess1["cart"] = {"1": 1}
        with client_guest2.session_transaction() as sess2:
            sess2["cart"] = {"2": 1}

        csrf1, tok1 = self._get_csrf_and_checkout_token(client_guest1)
        csrf2, tok2 = self._get_csrf_and_checkout_token(client_guest2)
        self.assertNotEqual(tok1, tok2)

        # Guest 1 đặt hàng thành công với tok1
        resp1 = client_guest1.post("/checkout", data={
            "csrf_token": csrf1,
            "checkout_token": tok1,
            "full_name": "Khách Vãng Lai 1",
            "phone": "0988111222",
            "fulfillment": "pickup",
            "payment_method": "cod",
        }, follow_redirects=False)
        self.assertEqual(resp1.status_code, 302)
        self.assertIn("/checkout/success", resp1.location)

        # Guest 2 gửi lại token của Guest 1 -> bị từ chối
        resp2 = client_guest2.post("/checkout", data={
            "csrf_token": csrf2,
            "checkout_token": tok1,
            "full_name": "Khách Vãng Lai 2",
            "phone": "0988333444",
            "fulfillment": "pickup",
            "payment_method": "cod",
        }, follow_redirects=False)
        self.assertEqual(resp2.status_code, 302)
        self.assertNotIn("/checkout/success", resp2.location)

        # Giỏ hàng Guest 2 được bảo toàn nguyên vẹn
        with client_guest2.session_transaction() as sess2:
            self.assertEqual(sess2.get("cart"), {"2": 1})
            self.assertIsNone(sess2.get("last_checkout_order"))

    # --------------------------------------------------------------------------
    # LỖI 2 (BỔ SUNG): MẬT KHẨU ADMIN / DEMO SQL SERVER KHỚP Demo@12345
    # --------------------------------------------------------------------------
    def test_11_sqlserver_admin_demo_password_matches_demo12345(self):
        from werkzeug.security import check_password_hash
        with open("database/init_database_sqlserver.sql", "r", encoding="utf-8") as f:
            content = f.read()

        # Trích xuất dòng seed tài khoản
        admin_match = re.search(r"admin@shop\.vn',\s*'([^']+)'", content)
        self.assertIsNotNone(admin_match, "Không tìm thấy tài khoản admin@shop.vn trong script SQL Server")
        admin_hash = admin_match.group(1)

        minh_match = re.search(r"minh@shop\.vn',\s*'([^']+)'", content)
        self.assertIsNotNone(minh_match, "Không tìm thấy tài khoản minh@shop.vn trong script SQL Server")
        minh_hash = minh_match.group(1)

        khach_match = re.search(r"khach@shop\.vn',\s*'([^']+)'", content)
        self.assertIsNotNone(khach_match, "Không tìm thấy tài khoản khach@shop.vn trong script SQL Server")
        khach_hash = khach_match.group(1)

        # Cả 3 tài khoản demo phải xác thực thành công với Demo@12345
        self.assertTrue(check_password_hash(admin_hash, "Demo@12345"), "Hash của admin@shop.vn không khớp với Demo@12345")
        self.assertTrue(check_password_hash(minh_hash, "Demo@12345"), "Hash của minh@shop.vn không khớp với Demo@12345")
        self.assertTrue(check_password_hash(khach_hash, "Demo@12345"), "Hash của khach@shop.vn không khớp với Demo@12345")


if __name__ == "__main__":
    unittest.main()
