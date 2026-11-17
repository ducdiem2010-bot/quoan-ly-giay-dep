"""N1-N2: test số lượng bán bằng DB SQLite test biệt lập."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from app import create_app
from app.services.best_sellers import get_best_selling_products


class BestSellerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='nhom6_best_')
        self.app = create_app({'TESTING': True, 'DB_BACKEND': 'sqlite',
                               'DATABASE': str(Path(self.temp.name) / 'test.sqlite3')})
        self.context = self.app.app_context()
        self.context.push()
        self.client = self.app.test_client()
        self.db = sqlite3.connect(self.app.config['DATABASE'])
        self.db.execute('UPDATE SanPham SET HienThi=0')
        cur = self.db.execute("INSERT INTO SanPham(MaDanhMuc,TenSanPham,GiaBan,ThuongHieu,HienThi) VALUES (1,'Giay kiem thu ban chay',250000,'QA',1)")
        self.pid=cur.lastrowid
        v1=self.db.execute('INSERT INTO BienTheSanPham(MaSanPham,KichThuoc,MauSac,SoLuongTon) VALUES (?, ?, ?, ?)', (self.pid,'40','Đen',6)).lastrowid
        v2=self.db.execute('INSERT INTO BienTheSanPham(MaSanPham,KichThuoc,MauSac,SoLuongTon) VALUES (?, ?, ?, ?)', (self.pid,'41','Trắng',8)).lastrowid
        done=self.db.execute("INSERT INTO DonHang(TrangThai) VALUES ('Hoàn thành')").lastrowid
        self.db.execute('INSERT INTO ChiTietDonHang(MaDonHang,MaBienThe,SoLuong,DonGia) VALUES(?,?,?,?)', (done,v1,2,250000))
        self.db.execute('INSERT INTO ChiTietDonHang(MaDonHang,MaBienThe,SoLuong,DonGia) VALUES(?,?,?,?)', (done,v2,3,250000))
        # Fixture bán thành công phải có giao hàng và thanh toán; không dùng ngoại lệ legacy.
        self.db.execute("UPDATE DonHang SET TrangThaiGiaoHang='Đã giao' WHERE MaDonHang=?", (done,))
        self.db.execute('''INSERT INTO ThongTinGiaoDich (MaDonHang,HoTen,SoDienThoai,HinhThucNhanHang,PhuongThucThanhToan,TrangThaiThanhToan) VALUES (?,'QA','0000000000','delivery','cod','Đã thanh toán')''', (done,))
        cancelled=self.db.execute("INSERT INTO DonHang(TrangThai) VALUES ('Đã hủy')").lastrowid
        self.db.execute('INSERT INTO ChiTietDonHang(MaDonHang,MaBienThe,SoLuong,DonGia) VALUES(?,?,?,?)', (cancelled,v1,9,250000))
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.context.pop()
        self.temp.cleanup()

    def test_two_variants_sum_five(self):
        self.assertEqual(get_best_selling_products()[0]['TongDaBan'], 5)

    def test_cancelled_nine_not_counted(self):
        self.assertNotEqual(get_best_selling_products()[0]['TongDaBan'], 14)

    def test_aggregate_has_one_product(self):
        self.assertEqual(len(get_best_selling_products()), 1)

    def test_hidden_excluded(self):
        self.db.execute('UPDATE SanPham SET HienThi=0 WHERE MaSanPham=?', (self.pid,))
        self.db.commit()
        self.assertEqual(get_best_selling_products(), [])

    def test_empty_without_completed_orders(self):
        self.db.execute("UPDATE DonHang SET TrangThai='Đã xác nhận' WHERE TrangThai='Hoàn thành'")
        self.db.commit()
        self.assertEqual(get_best_selling_products(), [])

    def test_limit_at_most_six(self):
        self.assertLessEqual(len(get_best_selling_products(limit=100)), 6)

    def test_route_works(self):
        response=self.client.get('/best-sellers')
        self.assertEqual(response.status_code,200)
        self.assertIn('Đã bán:',response.get_data(as_text=True))

    def test_route_empty_message(self):
        self.db.execute("UPDATE DonHang SET TrangThai='Đã xác nhận' WHERE TrangThai='Hoàn thành'")
        self.db.commit()
        response=self.client.get('/best-sellers')
        self.assertEqual(response.status_code,200)
        self.assertIn('Chưa có đơn hoàn thành',response.get_data(as_text=True))
