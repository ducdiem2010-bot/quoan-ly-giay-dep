"""W3 QA offline checks: standard-library only. Does not validate Flask/SQL Server."""
from pathlib import Path
import sqlite3, ast, unittest
ROOT=Path(__file__).resolve().parent.parent
class OfflineSchemaW3(unittest.TestCase):
    def setUp(self):
        self.con=sqlite3.connect(':memory:')
        self.con.execute('PRAGMA foreign_keys=ON')
        self.con.executescript((ROOT/'database/schema_sqlite.sql').read_text('utf-8'))
        self.con.executescript((ROOT/'database/seed_sqlite.sql').read_text('utf-8'))
    def tearDown(self): self.con.close()
    def test_at_least_twelve_footwear_products(self):
        self.assertGreaterEqual(self.con.execute('SELECT COUNT(*) FROM SanPham').fetchone()[0],12)
    def test_hidden_product_in_seed(self):
        self.assertGreaterEqual(self.con.execute('SELECT COUNT(*) FROM SanPham WHERE HienThi=0').fetchone()[0],1)
    def test_out_of_stock_variant(self):
        self.assertGreaterEqual(self.con.execute('SELECT COUNT(*) FROM BienTheSanPham WHERE SoLuongTon=0').fetchone()[0],1)
    def test_same_variant_row_required(self):
        n=self.con.execute('''SELECT COUNT(*) FROM SanPham sp WHERE EXISTS
            (SELECT 1 FROM BienTheSanPham bt WHERE bt.MaSanPham=sp.MaSanPham
              AND bt.MauSac='Đen' AND bt.KichThuoc='40')''').fetchone()[0]
        self.assertEqual(n,0)
    def test_variant_uniqueness_and_check(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.con.execute("INSERT INTO BienTheSanPham(MaSanPham,KichThuoc,MauSac,SoLuongTon) VALUES(1,'39','Đen',2)")
        with self.assertRaises(sqlite3.IntegrityError):
            self.con.execute("INSERT INTO BienTheSanPham(MaSanPham,KichThuoc,MauSac,SoLuongTon) VALUES(1,'50','Tím',-1)")
    def test_favorite_owner_and_uniqueness(self):
        self.con.execute('INSERT INTO YeuThich (MaNguoiDung,MaSanPham) VALUES(3,1)')
        self.assertEqual(self.con.execute('SELECT COUNT(*) FROM YeuThich WHERE MaNguoiDung=3').fetchone()[0],1)
        with self.assertRaises(sqlite3.IntegrityError):
            self.con.execute('INSERT INTO YeuThich(MaNguoiDung,MaSanPham) VALUES(3,1)')
        with self.assertRaises(sqlite3.IntegrityError):
            self.con.execute('INSERT INTO YeuThich(MaNguoiDung,MaSanPham) VALUES(999,1)')
    def test_atomic_rollback_sample(self):
        before=self.con.execute('SELECT COUNT(*) FROM SanPham').fetchone()[0]
        self.con.execute('SAVEPOINT test_sp')
        self.con.execute("INSERT INTO SanPham(MaDanhMuc,TenSanPham,GiaBan) VALUES(1,'Không lưu',500000)")
        self.con.execute('ROLLBACK TO test_sp'); self.con.execute('RELEASE test_sp')
        self.assertEqual(before,self.con.execute('SELECT COUNT(*) FROM SanPham').fetchone()[0])
    def test_python_syntax(self):
        for p in (ROOT/'app').rglob('*.py'):
            ast.parse(p.read_text('utf-8'),filename=str(p))
if __name__=='__main__':unittest.main(verbosity=2)
