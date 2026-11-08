"""Static/offline verification for the Admin products and variants UX patch.
Does not execute Flask routes in a browser and does not verify SQL Server connectivity.
"""
from pathlib import Path
import ast
import re
import sqlite3
import unittest

ROOT = Path(__file__).resolve().parent.parent

class AdminUXOfflineChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.routes = (ROOT / 'app/routes/admin.py').read_text('utf-8')
        cls.products = (ROOT / 'app/templates/admin/w3_products.html').read_text('utf-8')
        cls.variants = (ROOT / 'app/templates/admin/w3_variants.html').read_text('utf-8')
        cls.js = (ROOT / 'app/static/js/admin_product_feedback.js').read_text('utf-8')
        cls.css = (ROOT / 'app/static/css/admin_product_feedback.css').read_text('utf-8')

    def test_python_sources_parse(self):
        for path in (ROOT / 'app').rglob('*.py'):
            ast.parse(path.read_text('utf-8'), filename=str(path))

    def test_product_list_zero_stock_and_hidden_badge(self):
        self.assertIn('Hết hàng · tồn 0', self.products)
        self.assertIn('Đã ẩn', self.products)
        self.assertIn('Đang hiển thị', self.products)
        self.assertIn('data-stock-value', self.products)

    def test_visibility_post_keeps_csrf_and_confirmation(self):
        self.assertIn('data-w3-confirm=', self.products)
        self.assertIn('name="csrf_token"', self.products)
        self.assertIn("@admin_w3.post('/<int:product_id>/visibility')", self.routes)
        self.assertIn('SET HienThi=CASE WHEN HienThi=1 THEN 0 ELSE 1 END', self.routes)

    def test_variant_client_and_server_integer_validation(self):
        self.assertIn('step="1"', self.variants)
        self.assertIn('data-integer-stock', self.variants)
        self.assertIn('Number.isSafeInteger', self.js)
        self.assertIn(r'[0-9]+', self.js)
        self.assertIn('def _parse_nonnegative_integer', self.routes)
        self.assertIn('stock is None', self.routes)

    def test_invalid_variant_input_is_rendered_back(self):
        self.assertIn("variant_values.get('stock','0')", self.variants)
        self.assertIn('edit_values=values', self.routes)
        self.assertIn('dữ liệu bạn nhập vẫn được giữ', self.routes.lower())

    def test_csrf_hidden_inputs_remain(self):
        self.assertGreaterEqual(self.products.count('name="csrf_token"'), 1)
        self.assertGreaterEqual(self.variants.count('name="csrf_token"'), 2)

    def test_feedback_css_is_admin_scoped(self):
        self.assertIn('.w3-admin-page', self.css)
        self.assertNotIn('body {', self.css)
        self.assertIn('.w3-confirm-backdrop', self.css)

    def test_sqlite_stock_constraint_still_rejects_negative(self):
        db = sqlite3.connect(':memory:')
        db.execute('PRAGMA foreign_keys=ON')
        db.executescript((ROOT / 'database/schema_sqlite.sql').read_text('utf-8'))
        db.executescript((ROOT / 'database/seed_sqlite.sql').read_text('utf-8'))
        with self.assertRaises(sqlite3.IntegrityError):
            db.execute("INSERT INTO BienTheSanPham(MaSanPham,KichThuoc,MauSac,SoLuongTon) VALUES(1,'49','QA-NEG',-1)")
        db.close()

    def test_sql_server_v2_not_claimed_as_present(self):
        files = [p.name.lower() for p in (ROOT / 'database').glob('*')]
        self.assertFalse(any('v2' in name for name in files))

if __name__ == '__main__':
    unittest.main(verbosity=2)
