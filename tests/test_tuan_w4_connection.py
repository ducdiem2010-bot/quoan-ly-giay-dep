"""Kiểm tra đường ghép factory -> adapter -> UI bằng service giả lập có trạng thái.

Không xác nhận backend Nghĩa, SQL Server, transaction tồn hay online payment.
"""
from copy import deepcopy
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from flask import current_app
from app import create_app
from app.tuan_w4_connection import (
    OrderUIAdapter, OrderUIConnectionError, bind_order_ui_provider,
)
from app.tuan_w4_preview import preview_orders


class FixtureService:
    def __init__(self):
        self.rows = preview_orders()
        self.calls = []

    def list(self, *, user_id):
        self.calls.append(("list", user_id))
        return [deepcopy(row) for row in self.rows if row["user_id"] == user_id]

    def detail(self, *, user_id, order_id):
        self.calls.append(("get", user_id, order_id))
        return next((deepcopy(row) for row in self.rows
                     if row["user_id"] == user_id and row["id"] == order_id), None)

    def cancel(self, *, user_id, order_id):
        self.calls.append(("cancel", user_id, order_id))
        row = next((row for row in self.rows
                    if row["user_id"] == user_id and row["id"] == order_id), None)
        if row is None or not row["can_cancel"]:
            return {"ok": False}
        row.update(can_cancel=False, status_label="Đã hủy", delivery_stage="cancelled")
        return {"ok": True}

    def adapter(self, cancel=True):
        return OrderUIAdapter(list_orders=self.list, get_order=self.detail,
                              cancel_order=self.cancel if cancel else None)


class ConnectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {"TUAN_ORDER_UI_PROVIDER_FACTORY": ""})
        self.env.start()
        self.service = FixtureService()
        self.module = types.ModuleType("fixture_order_connection")
        self.module.create_provider = lambda app: self.service.adapter()
        self.modules = patch.dict(sys.modules, {"fixture_order_connection": self.module})
        self.modules.start()
        self.config = {"TESTING": True, "DB_BACKEND": "sqlite",
                       "DATABASE": str(Path(self.tmp.name) / "connection.sqlite3"),
                       "SECRET_KEY": "isolated-connection-test", "TUAN_W4_PREVIEW": False}

    def tearDown(self):
        self.modules.stop()
        self.env.stop()
        self.tmp.cleanup()

    def app(self, **config):
        return create_app(dict(self.config, **config))

    def connected(self, **config):
        return self.app(TUAN_ORDER_UI_PROVIDER_FACTORY=
                        "fixture_order_connection:create_provider", **config)

    def client(self, app, user_id=3):
        client = app.test_client()
        with client.session_transaction() as session:
            session.update(user_id=user_id, role="Customer", _csrf="connection-token")
        return client

    def test_default_remains_disconnected_preview_off(self):
        app = self.app()
        self.assertIsNone(app.config["TUAN_ORDER_UI_PROVIDER"])
        self.assertEqual(self.client(app).get("/my-orders").status_code, 503)
        self.assertEqual(app.test_client().get("/ui-preview/w4/orders").status_code, 404)

    def test_environment_factory_connects_list_and_detail(self):
        os.environ["TUAN_ORDER_UI_PROVIDER_FACTORY"] = "fixture_order_connection:create_provider"
        app = self.app()
        client = self.client(app)
        self.assertIn("Đơn #4101", client.get("/my-orders?user_id=99").get_data(as_text=True))
        self.assertEqual(client.get("/my-orders/4101").status_code, 200)
        self.assertIn(("list", 3), self.service.calls)
        self.assertIn(("get", 3, 4101), self.service.calls)
        self.assertFalse(app.config["TUAN_W4_PREVIEW"])

    def test_explicit_empty_config_disables_environment_factory(self):
        os.environ["TUAN_ORDER_UI_PROVIDER_FACTORY"] = "fixture_order_connection:create_provider"
        self.assertIsNone(self.app(TUAN_ORDER_UI_PROVIDER_FACTORY="").config["TUAN_ORDER_UI_PROVIDER"])

    def test_direct_provider_takes_priority_over_factory(self):
        provider = self.service.adapter()
        app = self.app(TUAN_ORDER_UI_PROVIDER=provider,
                       TUAN_ORDER_UI_PROVIDER_FACTORY="does.not.exist:create_provider")
        self.assertIs(app.config["TUAN_ORDER_UI_PROVIDER"], provider)

    def test_factory_runs_in_app_context(self):
        def factory(app):
            self.assertIs(current_app._get_current_object(), app)
            return self.service.adapter()
        self.module.create_provider = factory
        self.assertEqual(self.client(self.connected()).get("/my-orders").status_code, 200)

    def test_factory_is_not_cached_across_apps(self):
        self.module.create_provider = lambda app: FixtureService().adapter()
        first, second = self.connected(), self.connected()
        self.assertIsNot(first.config["TUAN_ORDER_UI_PROVIDER"],
                         second.config["TUAN_ORDER_UI_PROVIDER"])

    def test_invalid_factory_paths_and_missing_methods_fail_at_startup(self):
        for path in ["missing_separator", ":factory", "bad-module:factory",
                     "missing_backend_module:create_provider", "fixture_order_connection:missing"]:
            with self.subTest(path=path), self.assertRaises(OrderUIConnectionError):
                self.app(TUAN_ORDER_UI_PROVIDER_FACTORY=path)
        self.module.create_provider = lambda app: object()
        with self.assertRaises(OrderUIConnectionError):
            self.connected()

    def test_factory_private_exception_is_not_exposed(self):
        def fail(app):
            raise RuntimeError("secret-connection-details")
        self.module.create_provider = fail
        with self.assertRaises(OrderUIConnectionError) as error:
            self.connected()
        self.assertNotIn("secret-connection-details", str(error.exception))

    def test_read_only_adapter_has_no_cancel_action(self):
        self.module.create_provider = lambda app: self.service.adapter(cancel=False)
        client = self.client(self.connected())
        html = client.get("/my-orders/4101").get_data(as_text=True)
        self.assertNotIn("data-open-cancel", html)
        self.assertEqual(client.post("/my-orders/4101/cancel",
                         data={"csrf_token": "connection-token"}).status_code, 503)
        self.assertFalse(any(call[0] == "cancel" for call in self.service.calls))

    def test_connected_cancel_checks_csrf_owner_and_refreshes_state(self):
        app = self.connected()
        client = self.client(app)
        self.assertEqual(client.post("/my-orders/4101/cancel").status_code, 400)
        other = self.client(app, user_id=9)
        self.assertEqual(other.post("/my-orders/4101/cancel",
                         data={"csrf_token": "connection-token"}).status_code, 404)
        html = client.post("/my-orders/4101/cancel",
                           data={"csrf_token": "connection-token"},
                           follow_redirects=True).get_data(as_text=True)
        self.assertIn("Backend đã xác nhận hủy đơn", html)
        self.assertIn("Đã hủy", html)
        client.post("/my-orders/4101/cancel", data={"csrf_token": "connection-token"})
        self.assertEqual(sum(call[0] == "cancel" for call in self.service.calls), 1)

    def test_mapping_hook_and_missing_detail(self):
        raw = {"record": preview_orders()[0]}
        adapter = OrderUIAdapter(
            list_orders=lambda **kwargs: [raw], get_order=lambda **kwargs: None,
            to_order_view=lambda row: row["record"])
        app = self.app(TUAN_ORDER_UI_PROVIDER=adapter)
        client = self.client(app)
        self.assertEqual(client.get("/my-orders").status_code, 200)
        self.assertEqual(client.get("/my-orders/123").status_code, 404)

    def test_backend_error_is_not_an_empty_order_list(self):
        def fail(**kwargs):
            raise RuntimeError("private-backend-error")
        provider = OrderUIAdapter(list_orders=fail, get_order=self.service.detail)
        app = self.app(TUAN_ORDER_UI_PROVIDER=provider)
        response = self.client(app).get("/my-orders")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("Bạn chưa có đơn hàng", response.get_data(as_text=True))
        self.assertNotIn("private-backend-error", response.get_data(as_text=True))

    def test_can_bind_after_create_app_without_editing_ui(self):
        app = self.app()
        bind_order_ui_provider(app, self.service.adapter())
        self.assertEqual(self.client(app).get("/my-orders").status_code, 200)

    def test_adapter_rejects_non_callable_hooks(self):
        with self.assertRaises(OrderUIConnectionError):
            OrderUIAdapter(list_orders=None, get_order=self.service.detail)
        with self.assertRaises(OrderUIConnectionError):
            OrderUIAdapter(list_orders=self.service.list, get_order=self.service.detail,
                           cancel_order=True)
        with self.assertRaises(OrderUIConnectionError):
            OrderUIAdapter(list_orders=self.service.list, get_order=self.service.detail,
                           to_order_view=True)


if __name__ == "__main__":
    unittest.main()

