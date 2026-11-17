"""M1-M2: thử nghiệm riêng bằng DB tạm, không sửa database đang dùng."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from app import create_app
from app.services.new_arrivals import get_latest_products


class NewArrivalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='nhom6_new_')
        self.app = create_app({'TESTING': True, 'DB_BACKEND': 'sqlite',
                               'DATABASE': str(Path(self.temp.name) / 'test.sqlite3')})
        self.context = self.app.app_context()
        self.context.push()
        self.client = self.app.test_client()
        self.connection = sqlite3.connect(self.app.config['DATABASE'])
        self.connection.execute('UPDATE SanPham SET HienThi=0')
        for i in range(9):
            self.connection.execute("""INSERT INTO SanPham(MaDanhMuc,TenSanPham,GiaBan,ThuongHieu,HienThi,NgayTao)
                  VALUES(1,?,?,?,?,?)""", (f'Kiem thu moi {i}', 150000 + i, 'QA', 1,
                                          '2026-11-09 12:00:00' if i in (7,8) else f'2026-11-0{i+1} 10:00:00'))
        self.connection.commit()

    def tearDown(self):
        self.connection.close()
        self.context.pop()
        self.temp.cleanup()

    def test_limit_six(self):
        self.assertEqual(len(get_latest_products()), 6)

    def test_sort_by_date_then_id(self):
        rows = get_latest_products()
        self.assertTrue(rows[0]['TenSanPham'].endswith('8'))
        self.assertTrue(rows[1]['TenSanPham'].endswith('7'))

    def test_hidden_excluded(self):
        self.connection.execute("UPDATE SanPham SET HienThi=0 WHERE TenSanPham='Kiem thu moi 8'")
        self.connection.commit()
        self.assertFalse(any(x['TenSanPham']=='Kiem thu moi 8' for x in get_latest_products()))

    def test_empty(self):
        self.connection.execute('UPDATE SanPham SET HienThi=0')
        self.connection.commit()
        self.assertEqual(get_latest_products(), [])

    def test_two_products(self):
        self.connection.execute("UPDATE SanPham SET HienThi=0 WHERE TenSanPham NOT IN ('Kiem thu moi 7','Kiem thu moi 8')")
        self.connection.commit()
        self.assertEqual(len(get_latest_products()), 2)

    def test_route_ok_and_cards(self):
        response=self.client.get('/new-arrivals')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'product-card', response.data)
        self.assertLessEqual(response.data.count(b'class="product-card '), 6)

    def test_route_empty_state(self):
        self.connection.execute('UPDATE SanPham SET HienThi=0')
        self.connection.commit()
        response=self.client.get('/new-arrivals')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Chưa có sản phẩm', response.get_data(as_text=True))
