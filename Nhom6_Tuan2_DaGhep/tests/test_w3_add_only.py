"""Kiểm tra phần W3 nạp thêm và các chức năng gốc cùng hoạt động."""
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest

from app import create_app
from app.w3_routes import register_w3_routes
from run_w3 import create_w3_app
import test_smoke as week2_tests


class Week2WithW3Test(week2_tests.Week2SmokeTest):
    """Chạy lại 10 bài test Tuần 2 trên app có Blueprint W3.

    Không sửa một dòng của tests/test_smoke.py; chỉ dùng lại bài test có sẵn.
    """
    def setUp(self):
        super().setUp()
        register_w3_routes(self.app)


class AddOnlyIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.temp.name) / "same_app.sqlite3")
        self.config = {"TESTING": True, "DB_BACKEND": "sqlite", "DATABASE": self.db,
                       "SECRET_KEY": "w3-add-only-test"}
        self.app = create_w3_app(self.config)
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp.cleanup()

    def test_old_factory_still_serves_week2_and_has_no_w3_route(self):
        original = create_app(self.config).test_client()
        home = original.get("/")
        self.assertEqual(home.status_code, 200)
        self.assertNotIn('href="/products"', home.get_data(as_text=True))
        self.assertEqual(original.get("/products").status_code, 404)
        self.assertEqual(self.client.get("/products").status_code, 200)

    def test_old_and_new_pages_read_same_database(self):
        name = "Giày kiểm thử cùng DB Tuần 2 và Tuần 3"
        with closing(sqlite3.connect(self.db)) as conn:
            conn.execute(
                "INSERT INTO SanPham(MaDanhMuc,TenSanPham,GiaBan,ThuongHieu) VALUES(?,?,?,?)",
                (1, name, 750000, "Demo"),
            )
            conn.commit()
        for path in ("/", "/products"):
            result = self.client.get(path, query_string={"q": name})
            self.assertEqual(result.status_code, 200)
            self.assertIn(name, result.get_data(as_text=True))

    def test_new_page_inherits_original_base_and_old_card_stays_in_use(self):
        home = self.client.get("/").get_data(as_text=True)
        catalog = self.client.get("/products").get_data(as_text=True)
        self.assertIn("Demo Tuần 2", home)
        self.assertIn("Demo Tuần 2", catalog)
        self.assertNotIn("data-product-id", home)
        self.assertIn('data-product-id="1"', catalog)
        self.assertIn('href="/product/1"', catalog)

    def test_week2_login_session_is_shared_with_w3_page(self):
        self.client.get("/login")
        with self.client.session_transaction() as session:
            token = session["_csrf"]
        response = self.client.post("/login", data={"csrf_token": token,
            "email": "admin@shop.vn", "password": "Demo@12345"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get("/admin").status_code, 200)
        catalog = self.client.get("/products")
        self.assertEqual(catalog.status_code, 200)
        self.assertIn("Đăng xuất", catalog.get_data(as_text=True))
        self.assertIn('href="/admin"', catalog.get_data(as_text=True))

    def test_existing_products_route_is_not_overridden(self):
        app = create_app(self.config)
        @app.get("/products")
        def existing_catalog():
            return "Existing catalog"
        with self.assertRaisesRegex(RuntimeError, "đã có route /products"):
            register_w3_routes(app)
        self.assertEqual(app.test_client().get("/products").get_data(as_text=True),
                         "Existing catalog")


if __name__ == "__main__":
    unittest.main(verbosity=2)
