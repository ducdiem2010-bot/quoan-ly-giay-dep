"""Kiểm tra contract/trạng thái form W3-011, không nghiệm thu lọc SQL Server."""
from contextlib import closing
from html.parser import HTMLParser
from pathlib import Path
import sqlite3
import tempfile
import unittest
from urllib.parse import parse_qs, urlsplit

from run_w3 import create_w3_app as create_app


class FilterPageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.form = None
        self.in_form = False
        self.fields = {}
        self.labels = set()
        self.current_select = None
        self.reset_url = None
        self.next_url = None
        self.prev_url = None
        self.product_ids = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "article" and a.get("data-product-id"):
            self.product_ids.append(int(a["data-product-id"]))
        if tag == "a":
            if "filter-reset" in a.get("class", "").split():
                self.reset_url = a["href"]
            if a.get("rel") == "next":
                self.next_url = a["href"]
            if a.get("rel") == "prev":
                self.prev_url = a["href"]
        if tag == "form" and a.get("id") == "catalog-filter-form":
            self.form = a
            self.in_form = True
        if not self.in_form:
            return
        if tag == "label":
            self.labels.add(a.get("for"))
        if tag in ("input", "select") and a.get("name"):
            name = a["name"]
            self.fields[name] = {"attrs": a, "value": a.get("value", ""), "options": []}
            if tag == "select":
                self.current_select = name
        if tag == "option" and self.current_select:
            field = self.fields[self.current_select]
            field["options"].append(a)
            if "selected" in a:
                field["value"] = a.get("value", "")

    def handle_endtag(self, tag):
        if tag == "select":
            self.current_select = None
        if tag == "form" and self.in_form:
            self.in_form = False


class CatalogFilterUiTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.temp.name) / "filters.sqlite3")
        self.app = create_app({"TESTING": True, "DB_BACKEND": "sqlite",
                               "DATABASE": self.db, "SECRET_KEY": "w3-011-test-only"})
        self.client = self.app.test_client()
        with closing(sqlite3.connect(self.db)) as conn:
            conn.executemany(
                "INSERT INTO SanPham(MaDanhMuc,TenSanPham,GiaBan,ThuongHieu) VALUES(?,?,?,?)",
                [(1, "Giày kiểm thử W3-011 A", 100000, "Demo"),
                 (1, "Giày kiểm thử W3-011 B", 200000, "Demo")],
            )
            conn.commit()

    def tearDown(self):
        self.temp.cleanup()

    def page(self, url="/products", query=None):
        response = self.client.get(url, query_string=query)
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        parser = FilterPageParser()
        parser.feed(html)
        return parser, html

    def test_guest_get_form_has_canonical_fields_and_labels(self):
        p, html = self.page()
        self.assertEqual(p.form["method"].lower(), "get")
        self.assertEqual(p.form["action"], "/products")
        expected = {"q", "brand_id", "type_id", "gender", "color_id", "size_id",
                    "price_min", "price_max", "sort", "page"}
        self.assertEqual(set(p.fields), expected)
        self.assertEqual(p.fields["page"]["value"], "1")
        for name, field in p.fields.items():
            if name != "page":
                self.assertIn(field["attrs"]["id"], p.labels)
        self.assertNotIn("csrf_token", p.fields)
        self.assertNotIn('action="/login"', html)
        self.assertEqual({o["value"] for o in p.fields["sort"]["options"]},
                         {"", "price_asc", "price_desc", "name_asc", "brand_asc"})

    def test_all_values_are_restored_after_get(self):
        query = {"q": "Nike", "brand_id": "2", "type_id": "3", "gender": "female",
                 "color_id": "1", "size_id": "2", "price_min": "250000",
                 "price_max": "1500000", "sort": "price_desc"}
        p, html = self.page(query=query)
        for name, value in query.items():
            self.assertEqual(p.fields[name]["value"], value)
        self.assertIn("Lựa chọn đã lưu", html)
        self.assertIn("Giá giảm dần", html)
        self.assertIn("Không", p.fields["price_max"]["attrs"]["placeholder"])
        # q đang hoạt động; brand/type/gender đang được giữ ở UI, chưa lọc DB.
        self.assertEqual(p.product_ids, [1])

    def test_form_submission_resets_page_and_keeps_other_choices(self):
        query = {"page": "2", "brand_id": "2", "color_id": "1",
                 "size_id": "2", "sort": "price_desc"}
        p, html = self.page(query=query)
        self.assertIn("Trang 2 / 2", html)
        submitted = {name: field["value"] for name, field in p.fields.items()}
        self.assertEqual(submitted["page"], "1")
        first, html = self.page(p.form["action"], submitted)
        self.assertIn("Trang 1 / 2", html)
        self.assertEqual(len(first.product_ids), 10)
        self.assertIsNone(first.prev_url)
        for key in ("brand_id", "color_id", "size_id", "sort"):
            self.assertEqual(first.fields[key]["value"], query[key])

    def test_search_enter_submission_uses_q_and_keeps_choices(self):
        p, _ = self.page(query={"brand_id": "2", "gender": "male"})
        submitted = {name: field["value"] for name, field in p.fields.items()}
        submitted["q"] = "Converse"
        result, html = self.page(p.form["action"], submitted)
        self.assertEqual(result.product_ids, [7])
        self.assertEqual(result.fields["brand_id"]["value"], "2")
        self.assertEqual(result.fields["gender"]["value"], "male")
        self.assertIn("Converse Chuck Taylor", html)

    def test_previous_next_keep_every_filter_value(self):
        query = {"q": "", "brand_id": "1", "type_id": "2", "gender": "unisex",
                 "color_id": "1", "size_id": "2", "price_min": "0",
                 "price_max": "1", "sort": "brand_asc"}
        first, _ = self.page(query=query)
        self.assertIsNotNone(first.next_url)
        next_query = parse_qs(urlsplit(first.next_url).query, keep_blank_values=True)
        for key, value in query.items():
            self.assertEqual(next_query[key], [value])
        self.assertEqual(next_query["page"], ["2"])
        second, _ = self.page(first.next_url)
        self.assertEqual(len(second.product_ids), 2)
        for key, value in query.items():
            self.assertEqual(second.fields[key]["value"], value)
        back, _ = self.page(second.prev_url)
        self.assertEqual(back.product_ids, first.product_ids)

    def test_reset_clears_all_choices_and_returns_to_first_page(self):
        p, _ = self.page(query={"q": "Nike", "brand_id": "1", "sort": "price_asc"})
        self.assertEqual(p.reset_url, "/products")
        reset, html = self.page(p.reset_url)
        for key, field in reset.fields.items():
            self.assertEqual(field["value"], "1" if key == "page" else "")
        self.assertNotIn('id="selection-title"', html)
        self.assertIn("Trang 1 / 2", html)

    def test_invalid_prices_have_inline_message_without_server_error(self):
        cases = [({"price_min": "-1"}, "price_min", "Giá phải là số không âm."),
                 ({"price_max": "abc"}, "price_max", "Giá phải là số không âm."),
                 ({"price_min": "NaN"}, "price_min", "Giá phải là số không âm."),
                 ({"price_max": "Infinity"}, "price_max", "Giá phải là số không âm."),
                 ({"price_min": "900", "price_max": "100"}, "price_max",
                  "Giá đến phải lớn hơn hoặc bằng Giá từ.")]
        for query, field, message in cases:
            with self.subTest(query=query):
                p, html = self.page(query=query)
                self.assertEqual(p.fields[field]["value"], query[field])
                self.assertEqual(p.fields[field]["attrs"]["aria-invalid"], "true")
                self.assertIn(message, html)

    def test_unknown_codes_remain_visible_and_are_not_replaced(self):
        p, html = self.page(query={"brand_id": "701", "sort": "unapproved_sort"})
        self.assertEqual(p.fields["brand_id"]["value"], "701")
        self.assertEqual(p.fields["sort"]["value"], "unapproved_sort")
        self.assertIn("Mã chưa có trong danh mục: 701", html)
        self.assertIn("Kiểu sắp xếp này chưa có", html)

    def test_query_text_is_html_escaped(self):
        payload = '<script>alert("W3-011")</script>'
        p, html = self.page(query={"q": payload, "brand_id": payload, "sort": payload})
        self.assertNotIn(payload, html)
        self.assertIn("&lt;script&gt;", html)
        self.assertEqual(p.fields["q"]["value"], payload)
        self.assertEqual(p.fields["brand_id"]["value"], payload)
        self.assertEqual(p.fields["sort"]["value"], payload)

    def test_real_catalog_ids_can_be_supplied_without_rewriting_template(self):
        self.app.config["CATALOG_FILTER_OPTIONS"] = {
            "brand_id": [{"value": 701, "label": "Thương hiệu từ danh mục bàn giao"}],
            "gender": [{"value": "Nam", "label": "Nam"}],
        }
        p, html = self.page(query={"brand_id": "701", "gender": "Nam"})
        self.assertEqual(p.fields["brand_id"]["value"], "701")
        self.assertEqual(p.fields["gender"]["value"], "Nam")
        self.assertNotIn("aria-invalid", p.fields["brand_id"]["attrs"])
        self.assertNotIn("aria-invalid", p.fields["gender"]["attrs"])
        self.assertIn("Thương hiệu từ danh mục bàn giao", html)

    def test_preview_does_not_claim_or_simulate_database_filtering(self):
        p, html = self.page(query={"price_max": "1", "sort": "price_desc"})
        self.assertEqual(len(p.product_ids), 10)
        self.assertEqual(p.product_ids, list(range(1, 11)))
        self.assertIn("bộ lọc và sắp xếp hiện chỉ lưu lựa chọn", html)
        response = self.client.get("/static/css/product_filters.css")
        self.assertEqual(response.status_code, 200)
        response.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
