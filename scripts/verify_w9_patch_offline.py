"""Offline regression of W9 integration wiring and SQLite fixture only.

Does NOT exercise Flask requests, SQL Server, browser, auth or transactions through Flask.
Run with: python scripts/verify_w9_patch_offline.py
"""
import ast
from contextlib import closing
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sqlite3
import sys
import tempfile
import types
import unittest

from jinja2 import Environment

ROOT = Path(__file__).resolve().parents[1]


class W9OfflineChecks(unittest.TestCase):
    def test_every_python_file_compiles(self):
        files = list((ROOT / 'app').rglob('*.py')) + list((ROOT / 'tests').glob('test*.py'))
        files += list((ROOT / 'scripts').glob('*.py'))
        self.assertGreaterEqual(len(files), 20)
        for file in files:
            with self.subTest(file=str(file.relative_to(ROOT))):
                compile(file.read_bytes(), str(file), 'exec')

    def test_all_jinja_templates_parse(self):
        env = Environment()
        files = list((ROOT / 'app' / 'templates').rglob('*.html'))
        self.assertGreaterEqual(len(files), 20)
        for file in files:
            with self.subTest(file=str(file.relative_to(ROOT))):
                env.parse(file.read_text(encoding='utf-8'))

    def test_w4_blueprint_registered_and_config_defaults(self):
        tree = ast.parse((ROOT / 'app' / '__init__.py').read_text('utf-8'))
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
        self.assertTrue(any(isinstance(n.func, ast.Attribute) and n.func.attr == 'register_blueprint'
                            and n.args and isinstance(n.args[0], ast.Name) and n.args[0].id == 'tuan_w4_ui'
                            for n in calls))
        source = (ROOT / 'app' / '__init__.py').read_text('utf-8')
        self.assertIn('TUAN_ORDER_UI_PROVIDER=None', source)
        self.assertIn('TUAN_W4_PREVIEW=False', source)

    def test_w4_routes_are_defined_and_check_server_session(self):
        source = (ROOT / 'app' / 'tuan_w4_ui.py').read_text('utf-8')
        tree = ast.parse(source)
        funcs = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
        self.assertTrue({'my_orders', 'order_detail', 'cancel_order', '_customer', '_order'}.issubset(funcs))
        self.assertIn('session.get("user_id")', source)
        self.assertIn('"Customer"', source)
        self.assertIn('raw["user_id"] != uid', source)

    def test_all_96_unittest_cases_preserved(self):
        module_classes = {}
        for p in (ROOT / 'tests').glob('test*.py'):
            t = ast.parse(p.read_text('utf-8'))
            for cls in (n for n in t.body if isinstance(n, ast.ClassDef)):
                module_classes[cls.name] = cls
        def methods(name):
            cls = module_classes[name]
            current = {n.name for n in cls.body if isinstance(n, ast.FunctionDef) and n.name.startswith('test')}
            for base in cls.bases:
                if isinstance(base, ast.Name) and base.id in module_classes:
                    current |= methods(base.id)
            return current
        total = sum(len(methods(name)) for name in module_classes)
        self.assertEqual(total, 96)

    def test_database_init_seed_counts_and_handle_cleanup(self):
        # Load the REAL init_demo_database function, with ONLY current_app replaced
        # by a configuration container. This is not an HTTP/Flask app test.
        path = ROOT / 'app' / 'db.py'
        with tempfile.TemporaryDirectory() as tmp:
            dbpath = str(Path(tmp) / 'offline.sqlite3')
            flask_stub = types.ModuleType('flask')
            flask_stub.current_app = types.SimpleNamespace(config={'DB_BACKEND': 'sqlite', 'DATABASE': dbpath})
            previous = sys.modules.get('flask')
            try:
                sys.modules['flask'] = flask_stub
                spec = spec_from_file_location('w9_offline_db', path)
                module = module_from_spec(spec)
                spec.loader.exec_module(module)
                module.init_demo_database()
                # Run twice to check idempotency and absence of duplicate seed rows.
                module.init_demo_database()
            finally:
                if previous is None:
                    sys.modules.pop('flask', None)
                else:
                    sys.modules['flask'] = previous
            with closing(sqlite3.connect(dbpath)) as conn, conn:
                self.assertEqual(conn.execute('select count(*) from SanPham').fetchone()[0], 12)
                self.assertEqual(conn.execute('select count(*) from SanPham where HienThi=1').fetchone()[0], 11)
                self.assertEqual(conn.execute('select count(*) from sqlite_master where type="table" and name not like "sqlite_%"').fetchone()[0], 11)
                self.assertEqual(conn.execute('PRAGMA foreign_key_check').fetchall(), [])
            # The directory is deleted only after the connection has closed.
        self.assertFalse(Path(dbpath).exists())

    def test_sqlite_test_connections_use_explicit_close(self):
        for name in ('test_buy_now.py', 'test_checkout_update.py',
                     'test_integration_w3.py', 'test_account.py', 'test_w3_extensions.py'):
            source = (ROOT / 'tests' / name).read_text('utf-8')
            self.assertNotIn('with sqlite3.connect(', source, name)
            self.assertIn('with closing(sqlite3.connect(', source, name)


if __name__ == '__main__':
    unittest.main(verbosity=2)
