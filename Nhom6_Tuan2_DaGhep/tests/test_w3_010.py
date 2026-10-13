"""Kiểm tra khung UI W3-010 trên DB tạm; không thay dữ liệu bàn giao."""
from contextlib import closing
from html.parser import HTMLParser
from pathlib import Path
import sqlite3
import tempfile
import unittest
from urllib.parse import parse_qs, urlsplit

from run_w3 import create_w3_app as create_app


class CatalogParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.product_ids = []
        self.next_url = None
        self.prev_url = None
        self.disabled = 0
        self.images = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "article" and a.get("data-product-id"):
            self.product_ids.append(int(a["data-product-id"]))
        if tag == "a" and a.get("rel") == "next":
            self.next_url = a["href"]
        if tag == "a" and a.get("rel") == "prev":
            self.prev_url = a["href"]
        if a.get("aria-disabled") == "true":
            self.disabled += 1
        if tag == "img" and a.get("alt", "").startswith("Ảnh minh họa"):
            self.images += 1


class CatalogUiTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp.name) / "catalog.sqlite3")
        self.app = create_app({
            "TESTING": True, "DB_BACKEND": "sqlite", "DATABASE": self.db_path,
            "SECRET_KEY": "w3-010-local-test-only",
        })
        self.client = self.app.test_client()
        # 10 SP gốc + 2 SP thử, đủ kiểm nút Trước/Sau với 10 SP/trang.
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.executemany(
                "INSERT INTO SanPham(MaDanhMuc,TenSanPham,GiaBan,ThuongHieu,MoTa) VALUES(?,?,?,?,?)",
                [(1, "Giày kiểm tra UI A", 100000, "Demo", "Dữ liệu kiểm thử"),
                 (1, "Giày kiểm tra UI B", 200000, "Demo", "Dữ liệu kiểm thử")],
            )
            conn.commit()

    def tearDown(self):
        self.temp.cleanup()

    def page(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        parser = CatalogParser()
        parser.feed(response.get_data(as_text=True))
        return parser, response.get_data(as_text=True)

    def test_public_cards_before_login(self):
        p, html = self.page("/products")
        self.assertEqual(len(p.product_ids), 10)
        self.assertEqual(p.images, 10)
        self.assertIn("Nike Air Zoom Pegasus", html)
        self.assertIn("1.250.000 ₫", html)
        self.assertIn('href="/product/1"', html)
        self.assertIn("Trang 1 / 2", html)
        self.assertIsNone(p.prev_url)
        self.assertIsNotNone(p.next_url)

    def test_two_pages_have_no_missing_or_duplicate_cards(self):
        first, _ = self.page("/products")
        second, html = self.page(first.next_url)
        self.assertEqual(len(second.product_ids), 2)
        self.assertTrue(set(first.product_ids).isdisjoint(second.product_ids))
        self.assertEqual(set(first.product_ids + second.product_ids), set(range(1, 13)))
        self.assertIn("Trang 2 / 2", html)
        self.assertIsNone(second.next_url)
        self.assertIsNotNone(second.prev_url)
        back, _ = self.page(second.prev_url)
        self.assertEqual(back.product_ids, first.product_ids)

    def test_empty_database_has_clear_message_and_disabled_controls(self):
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.executescript("""PRAGMA foreign_keys=ON;
                DELETE FROM ChiTietDonHang;
                DELETE FROM ChiTietGioHang;
                DELETE FROM BienTheSanPham;
                DELETE FROM SanPham;""")
        p, html = self.page("/products")
        self.assertEqual(p.product_ids, [])
        self.assertIn("Chưa có sản phẩm", html)
        self.assertIn("0 sản phẩm", html)
        self.assertEqual(p.disabled, 2)
        self.assertIsNone(p.next_url)
        self.assertIsNone(p.prev_url)

    def test_search_without_results(self):
        p, html = self.page("/products?q=KHONG_CO_SAN_PHAM_010")
        self.assertEqual(p.product_ids, [])
        self.assertIn("Không tìm thấy sản phẩm", html)
        self.assertIn("Xem tất cả sản phẩm", html)
        self.assertEqual(p.disabled, 2)

    def test_invalid_and_out_of_range_page_do_not_fail(self):
        for value in ("0", "-2", "abc", "999999999999"):
            with self.subTest(page=value):
                p, html = self.page("/products?page=" + value)
                expected = 2 if value == "999999999999" else 1
                self.assertIn(f"Trang {expected} / 2", html)
                self.assertEqual(len(p.product_ids), 2 if expected == 2 else 10)

    def test_paging_preserves_encoded_query_and_local_url(self):
        keyword = "Giày kiểm thử A & B"
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.executemany(
                "INSERT INTO SanPham(MaDanhMuc,TenSanPham,GiaBan,ThuongHieu) VALUES(?,?,?,?)",
                [(1, f"{keyword} {n}", 100000, "Demo") for n in range(12)],
            )
            conn.commit()
        response = self.client.get("/products", query_string={
            "q": keyword, "brand_id": "7", "sort": "price_asc",
            "_external": "true", "_scheme": "javascript",
        })
        self.assertEqual(response.status_code, 200)
        p = CatalogParser()
        p.feed(response.get_data(as_text=True))
        self.assertIsNotNone(p.next_url)
        url = urlsplit(p.next_url)
        self.assertEqual(url.path, "/products")
        self.assertEqual(url.scheme, "")
        self.assertEqual(url.netloc, "")
        query = parse_qs(url.query)
        self.assertEqual(query["q"], [keyword])
        self.assertEqual(query["brand_id"], ["7"])
        self.assertEqual(query["sort"], ["price_asc"])
        self.assertEqual(query["page"], ["2"])
        second, _ = self.page(p.next_url)
        self.assertEqual(len(second.product_ids), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
