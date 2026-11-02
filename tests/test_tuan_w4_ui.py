"""Contract/UI tests với provider giả lập, không chứng minh backend đơn hàng đã có."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from app import create_app
from app.tuan_w4_preview import preview_orders


class FakeProvider:
    def __init__(self):
        self.orders = preview_orders()
        self.calls = []
        self.reject_cancel = False

    def list_orders(self, *, user_id):
        self.calls.append(("list", user_id))
        return [deepcopy(x) for x in self.orders if x["user_id"] == user_id]

    def get_order(self, *, user_id, order_id):
        self.calls.append(("get", user_id, order_id))
        return next((deepcopy(x) for x in self.orders
                     if x["id"] == order_id and x["user_id"] == user_id), None)

    def cancel_order(self, *, user_id, order_id):
        self.calls.append(("cancel", user_id, order_id))
        if self.reject_cancel:
            return {"ok": False}
        order = next(x for x in self.orders if x["id"] == order_id and x["user_id"] == user_id)
        order.update(can_cancel=False, status_label="Đã hủy", delivery_stage="cancelled")
        return {"ok": True}


class TuanW4UITests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = create_app({"TESTING": True, "DB_BACKEND": "sqlite",
                               "DATABASE": str(Path(self.tmp.name) / "ui.sqlite3"),
                               "SECRET_KEY": "w4-ui-tests", "TUAN_W4_PREVIEW": False})
        self.c = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def customer(self, uid=3, role="Customer"):
        with self.c.session_transaction() as s:
            s.update(user_id=uid, role=role, _csrf="test-ui-token")

    def connect(self):
        p = FakeProvider()
        self.app.config["TUAN_ORDER_UI_PROVIDER"] = p
        self.customer()
        return p

    def test_guest_redirect_keeps_internal_next(self):
        r = self.c.get("/my-orders/4101")
        self.assertEqual(r.status_code, 302)
        self.assertIn("next=/my-orders/4101", r.location)

    def test_seller_has_no_customer_order_page(self):
        self.customer(2, "Seller")
        r = self.c.get("/my-orders")
        self.assertEqual(r.status_code, 403)
        self.assertIn("tài khoản khách hàng", r.get_data(as_text=True))

    def test_missing_provider_is_unavailable_not_empty_list(self):
        self.customer()
        r = self.c.get("/my-orders")
        self.assertEqual(r.status_code, 503)
        self.assertIn("Chưa kết nối", r.get_data(as_text=True))
        self.assertNotIn("Bạn chưa có đơn hàng", r.get_data(as_text=True))

    def test_preview_is_disabled_by_default(self):
        self.assertEqual(self.c.get("/ui-preview/w4/detail").status_code, 404)

    def test_all_preview_scenarios_are_explicit_samples(self):
        self.app.config["TUAN_W4_PREVIEW"] = True
        for scenario in ["orders", "detail", "shipping", "completed", "failed", "cancelled",
                         "empty", "unavailable", "forbidden", "not-found"]:
            with self.subTest(scenario=scenario):
                r = self.c.get("/ui-preview/w4/" + scenario)
                self.assertEqual(r.status_code, 200)
                self.assertIn("DỮ LIỆU MẪU — CHƯA TÍCH HỢP BACKEND", r.get_data(as_text=True))
        self.assertEqual(self.c.post("/ui-preview/w4/detail").status_code, 400)

    def test_list_uses_session_owner_not_query_user(self):
        p = self.connect()
        r = self.c.get("/my-orders?user_id=999")
        self.assertEqual(r.status_code, 200)
        self.assertIn(("list", 3), p.calls)
        self.assertIn("Đơn #4101", r.get_data(as_text=True))

    def test_empty_list_requires_connected_provider(self):
        p = self.connect()
        p.orders = []
        self.assertIn("Bạn chưa có đơn hàng", self.c.get("/my-orders").get_data(as_text=True))

    def test_other_customer_cannot_read_order(self):
        self.connect()
        self.customer(7)
        self.assertEqual(self.c.get("/my-orders/4101").status_code, 404)

    def test_rejects_provider_leaking_another_owner(self):
        p = self.connect()
        p.get_order = lambda **kw: dict(preview_orders()[0], user_id=8)
        self.assertEqual(self.c.get("/my-orders/4101").status_code, 404)
        p.list_orders = lambda **kw: [dict(preview_orders()[0], user_id=8)]
        self.assertEqual(self.c.get("/my-orders").status_code, 404)

    def test_provider_exception_has_safe_unavailable_screen(self):
        p = self.connect()
        def failure(**kw):
            raise RuntimeError("private-db-info")
        p.get_order = failure
        r = self.c.get("/my-orders/4101")
        self.assertEqual(r.status_code, 503)
        self.assertNotIn("private-db-info", r.get_data(as_text=True))

    def test_payment_failure_never_claims_success(self):
        self.connect()
        text = self.c.get("/my-orders/4104").get_data(as_text=True)
        self.assertIn("Thanh toán thất bại", text)
        self.assertNotIn("Backend đã xác nhận hủy", text)
        self.assertNotIn('data-open-cancel', text)

    def test_invalid_money_is_rejected(self):
        p = self.connect()
        p.orders[0]["total"] = "NaN"
        self.assertEqual(self.c.get("/my-orders/4101").status_code, 503)

    def test_cancel_requires_csrf(self):
        p = self.connect()
        self.assertEqual(self.c.post("/my-orders/4101/cancel").status_code, 400)
        self.assertFalse(any(x[0] == "cancel" for x in p.calls))

    def test_cancel_cannot_target_another_owner(self):
        p = self.connect()
        self.customer(7)
        r = self.c.post("/my-orders/4101/cancel", data={"csrf_token": "test-ui-token"})
        self.assertEqual(r.status_code, 404)
        self.assertFalse(any(x[0] == "cancel" for x in p.calls))

    def test_ineligible_cancel_never_calls_write_provider(self):
        p = self.connect()
        r = self.c.post("/my-orders/4102/cancel", data={"csrf_token": "test-ui-token"},
                        follow_redirects=True)
        self.assertIn("không đủ điều kiện hủy", r.get_data(as_text=True))
        self.assertFalse(any(x[0] == "cancel" for x in p.calls))

    def test_backend_rejection_is_not_success(self):
        p = self.connect()
        p.reject_cancel = True
        text = self.c.post("/my-orders/4101/cancel", data={"csrf_token": "test-ui-token"},
                           follow_redirects=True).get_data(as_text=True)
        self.assertIn("Chưa hủy được đơn", text)
        self.assertNotIn("Backend đã xác nhận hủy đơn", text)

    def test_cancel_refreshes_state_and_disables_second_attempt(self):
        p = self.connect()
        data = {"csrf_token": "test-ui-token"}
        text = self.c.post("/my-orders/4101/cancel", data=data,
                           follow_redirects=True).get_data(as_text=True)
        self.assertIn("Backend đã xác nhận hủy đơn", text)
        self.assertIn("Đã hủy", text)
        self.c.post("/my-orders/4101/cancel", data=data)
        self.assertEqual(sum(x[0] == "cancel" for x in p.calls), 1)


if __name__ == "__main__":
    unittest.main()
