"""Kiểm thử tự động nghiệm thu Tuần 2 (SQLite demo, KHÔNG thay SQL Server)."""
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from html.parser import HTMLParser

class SelectorParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.csrf = None
        self.cards = 0
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "input" and a.get("name") == "csrf_token":
            self.csrf = a.get("value")
        if "product-card" in (a.get("class") or "").split():
            self.cards += 1

def parse_html(blob):
    p = SelectorParser()
    p.feed(blob.decode("utf-8") if isinstance(blob, bytes) else blob)
    return p
from app import create_app


class Week2SmokeTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp.name) / "demo.sqlite3")
        self.app = create_app({"TESTING": True, "DATABASE": self.db_path, "SECRET_KEY": "test-secret-only"})
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp.cleanup()

    def csrf(self, path="/"):
        html = self.client.get(path).data.decode("utf-8")
        field = parse_html(html).csrf
        self.assertIsNotNone(field)
        return field

    def test_seed_and_integrity(self):
        with closing(sqlite3.connect(self.db_path)) as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM SanPham").fetchone()[0], 10)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM DanhMuc").fetchone()[0], 3)
            self.assertGreaterEqual(con.execute("SELECT COUNT(*) FROM NguoiDung").fetchone()[0], 2)
            self.assertEqual(con.execute("PRAGMA foreign_key_check").fetchall(), [])
            self.assertEqual(con.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchone()[0], 9)
            self.assertEqual(con.execute("SELECT TongTien FROM DonHang WHERE MaDonHang=1").fetchone()[0], 3490000)

    def test_home_db_and_search(self):
        page = self.client.get("/")
        self.assertEqual(page.status_code, 200)
        self.assertIn("Nike Air Zoom Pegasus", page.get_data(as_text=True))
        self.assertEqual(parse_html(page.data).cards, 10)
        page = self.client.get("/?q=Converse")
        self.assertEqual(parse_html(page.data).cards, 1)

    def test_category_filter(self):
        page = self.client.get("/category/3")
        self.assertEqual(page.status_code, 200)
        soup = parse_html(page.data)
        self.assertEqual(soup.cards, 4)
        self.assertIn("Dép &amp; Sandal", page.get_data(as_text=True))
        self.assertEqual(self.client.get("/category/444").status_code, 404)

    def test_details_404_and_static(self):
        page = self.client.get("/product/1")
        self.assertEqual(page.status_code, 200)
        html = page.get_data(as_text=True)
        self.assertIn("Nike Air Zoom Pegasus", html)
        self.assertIn('name="quantity"', html)
        self.assertIn('name="variant_id"', html)
        self.assertEqual(self.client.get("/product/99999").status_code, 404)
        self.assertEqual(self.client.get("/abc/def").status_code, 404)
        static_response = self.client.get("/static/images/shoe-1.svg")
        self.assertEqual(static_response.status_code, 200)
        static_response.close()

    def test_cart_session_and_remove(self):
        token = self.csrf("/product/1")
        response = self.client.post("/add-to-cart/1", data={"csrf_token": token, "variant_id": "1", "quantity": "2"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        text = response.get_data(as_text=True)
        self.assertIn("Nike Air Zoom Pegasus", text)
        self.assertIn("2.500.000", text)
        self.assertEqual(self.client.get("/checkout").status_code, 200)
        token = self.csrf("/cart")
        response = self.client.post("/cart/remove/1", data={"csrf_token":token}, follow_redirects=True)
        self.assertIn("Giỏ hàng đang trống", response.get_data(as_text=True))

    def test_cart_guard(self):
        self.assertEqual(self.client.post("/add-to-cart/1", data={"variant_id":1}).status_code, 400)
        token = self.csrf("/product/1")
        self.assertEqual(self.client.post("/add-to-cart/1", data={"csrf_token":token,"variant_id":"1","quantity":"0"}).status_code, 400)
        page = self.client.post("/add-to-cart/1", data={"csrf_token":token,"variant_id":"1","quantity":"60"}, follow_redirects=True)
        self.assertIn("Không đủ tồn kho", page.get_data(as_text=True))

    def test_admin_guard_and_login(self):
        res = self.client.get("/admin")
        self.assertEqual(res.status_code,302)
        self.assertIn("/login",res.location)
        token = self.csrf("/login")
        bad = self.client.post("/login", data={"csrf_token":token,"email":"admin@shop.vn","password":"wrong"},follow_redirects=True)
        self.assertIn("chưa đúng",bad.get_data(as_text=True))
        token=self.csrf("/login")
        res=self.client.post("/login",data={"csrf_token":token,"email":"admin@shop.vn","password":"Demo@12345"},follow_redirects=True)
        self.assertEqual(res.status_code,200)
        self.assertIn("Quản trị sản phẩm",res.get_data(as_text=True))
        admin=self.client.get("/admin/product/add")
        self.assertEqual(admin.status_code,200)
        html=admin.get_data(as_text=True)
        for field in ('name="name"','name="price"','name="stock"','name="category_id"','name="image"'):
            self.assertIn(field,html)
        token=self.csrf("/admin/product/add")
        submit=self.client.post("/admin/product/add",data={"csrf_token":token,"name":"Mẫu mới","price":"10000","stock":"2","category_id":"1","image":"shoe-1.svg"},follow_redirects=True)
        self.assertIn("CHƯA lưu sản phẩm",submit.get_data(as_text=True))
        with closing(sqlite3.connect(self.db_path)) as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM SanPham").fetchone()[0],10)

    def test_seller_cannot_admin(self):
        token=self.csrf("/login")
        self.client.post("/login",data={"csrf_token":token,"email":"minh@shop.vn","password":"Demo@12345"})
        self.assertEqual(self.client.get("/admin").status_code,403)

    def test_register_and_login(self):
        token=self.csrf("/register")
        res=self.client.post("/register",data={"csrf_token":token,"full_name":"Bạn Kiểm Thử","email":"testuser@example.com","password":"ABCD@12345"},follow_redirects=True)
        self.assertEqual(res.status_code,200)
        self.assertIn("Đăng ký thành công",res.get_data(as_text=True))
        token=self.csrf("/login")
        self.client.post("/login",data={"csrf_token":token,"email":"testuser@example.com","password":"ABCD@12345"})
        self.assertEqual(self.client.get("/admin").status_code,403)

    def test_custom_500(self):
        @self.app.get("/__temporary_fault_test")
        def forced_error():
            raise RuntimeError("expected test exception")
        self.app.config["TESTING"] = False
        self.app.config["PROPAGATE_EXCEPTIONS"] = False
        self.app.logger.disabled = True  # lỗi 500 được tạo có chủ đích khi kiểm thử
        response=self.client.get("/__temporary_fault_test")
        self.assertEqual(response.status_code, 500)
        self.assertIn("Hệ thống tạm thời gặp sự cố",response.get_data(as_text=True))
        self.assertNotIn("expected test exception",response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main(verbosity=2)
