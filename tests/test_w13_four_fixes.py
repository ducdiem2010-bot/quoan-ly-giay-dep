"""W13: hồi quy bốn lỗi. Dùng database SQLite TẠM, không đụng dữ liệu người dùng."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import create_app
from app.db import get_db_connection, query_one
from app.services.account import count_orders, list_orders
from app.services.cart_availability import cart_unavailable_reason
from app.services.checkout import create_pending_order
from app.services.order_ops import (
    confirm_order_stock, record_order_payment, OrderOperationError
)


class FourFixRegression(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / 'fix4.sqlite3')
        self.app = create_app({'TESTING': True, 'DB_BACKEND': 'sqlite',
                               'DATABASE': self.db_path, 'SECRET_KEY': 'test-fix4-secret'})
        self.client = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def _order(self, method='cod'):
        with self.app.app_context():
            return create_pending_order({
                'full_name': 'Nguyễn Văn Kiểm Thử', 'phone': '0987654321',
                'email': '', 'fulfillment': 'delivery', 'address': '123 Kiểm thử, Hà Nội',
                'payment_method': method, 'note': ''
            }, {1: 1}, user_id=3)

    def _edit(self, sql, params=()):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(sql, params)

    def _get(self, sql, params=()):
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute(sql, params).fetchone()

    def _cart(self, payload):
        with self.client.session_transaction() as sess:
            sess['cart'] = payload

    def test_payment_missing_transaction_does_not_create_fake(self):
        order = self._order()
        with self.app.app_context():
            confirm_order_stock(order, 1)
        self._edit('DELETE FROM ThongTinGiaoDich WHERE MaDonHang=?', (order,))
        with self.app.app_context():
            with self.assertRaises(OrderOperationError):
                record_order_payment(order, 1)
        self.assertEqual(self._get('SELECT COUNT(*) FROM ThongTinGiaoDich WHERE MaDonHang=?', (order,))[0], 0)

    def test_bank_transfer_before_delivery_can_be_confirmed(self):
        order = self._order('bank_transfer')
        with self.app.app_context():
            confirm_order_stock(order, 1)
            self.assertTrue(record_order_payment(order, 2))
        tx = self._get('SELECT TrangThaiThanhToan,NguoiThuTien,ThoiGianThanhToan FROM ThongTinGiaoDich WHERE MaDonHang=?', (order,))
        self.assertEqual(tx[0:2], ('Đã thanh toán', 2))
        self.assertTrue(tx[2])
        self.assertEqual(self._get('SELECT TrangThaiGiaoHang FROM DonHang WHERE MaDonHang=?', (order,))[0], 'Chưa giao')
        with self.app.app_context():
            with self.assertRaises(OrderOperationError):
                record_order_payment(order, 2)

    def test_cod_not_marked_paid_automatically(self):
        order = self._order('cod')
        with self.app.app_context():
            confirm_order_stock(order, 1)
        self.assertEqual(self._get('SELECT TrangThaiThanhToan FROM ThongTinGiaoDich WHERE MaDonHang=?', (order,))[0], 'Chưa thanh toán')

    def test_placeholder_recipient_is_blocked(self):
        order = self._order()
        self._edit("UPDATE ThongTinGiaoDich SET HoTen='Khách hàng', SoDienThoai='0000000000' WHERE MaDonHang=?", (order,))
        with self.app.app_context():
            confirm_order_stock(order, 1)
            with self.assertRaises(OrderOperationError):
                record_order_payment(order, 1)
        self.assertEqual(self._get('SELECT TrangThaiThanhToan FROM ThongTinGiaoDich WHERE MaDonHang=?', (order,))[0], 'Chưa thanh toán')

    def test_seed_visibility_price_persist_across_startup(self):
        self._edit("UPDATE SanPham SET HienThi=1, GiaBan=789000 WHERE TenSanPham='Giày Thể Thao Mẫu Ẩn'")
        self.app = create_app({'TESTING': True, 'DB_BACKEND': 'sqlite',
                               'DATABASE': self.db_path, 'SECRET_KEY': 'test-fix4-secret'})
        self.assertEqual(self._get("SELECT HienThi,GiaBan FROM SanPham WHERE TenSanPham='Giày Thể Thao Mẫu Ẩn'"), (1, 789000))
        self._edit("UPDATE SanPham SET HienThi=0 WHERE TenSanPham='Giày Thể Thao Mẫu Ẩn'")
        create_app({'TESTING': True, 'DB_BACKEND': 'sqlite',
                    'DATABASE': self.db_path, 'SECRET_KEY': 'test-fix4-secret'})
        self.assertEqual(self._get("SELECT HienThi FROM SanPham WHERE TenSanPham='Giày Thể Thao Mẫu Ẩn'")[0], 0)

    def test_orders_db_limited_and_pages_not_duplicated(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany("INSERT INTO DonHang(MaNguoiDung, TrangThai, TongTien) VALUES(3,'Chờ xác nhận',0)", [() for _ in range(59)])
        with self.app.app_context():
            self.assertGreater(count_orders(3), 50)
            page1, page2 = list_orders(3, limit=50, page=1), list_orders(3, limit=50, page=2)
        self.assertEqual(len(page1), 50)
        self.assertEqual(len(page2), 10)
        ids1 = {x['MaDonHang'] for x in page1}
        ids2 = {x['MaDonHang'] for x in page2}
        self.assertFalse(ids1 & ids2)
        self.assertEqual(len(ids1 | ids2), 60)

    def test_list_orders_sqlserver_uses_offset_fetch(self):
        class FakeApp:
            config = {'DB_BACKEND': 'sqlserver'}
        with patch('flask.current_app', FakeApp()), patch('app.services.account.query_all', return_value=[]) as query:
            list_orders(3, limit=50, page=2)
            sql, params = query.call_args.args
        self.assertIn('OFFSET ? ROWS FETCH NEXT ? ROWS ONLY', sql)
        self.assertEqual(params, (3, 50, 50))

    def test_hidden_product_warning_and_no_checkout(self):
        self._cart({'1': 1})
        self._edit('UPDATE SanPham SET HienThi=0 WHERE MaSanPham=1')
        r = self.client.get('/cart')
        self.assertEqual(r.status_code, 200)
        self.assertIn('Sản phẩm hiện không còn được bán', r.get_data(as_text=True))
        self.assertIn('Chưa thể thanh toán', r.get_data(as_text=True))
        self.assertEqual(self.client.get('/checkout').status_code, 302)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess['cart'], {'1': 1})

    def test_stock_shortage_warning_and_no_checkout(self):
        self._cart({'1': 99})
        text = self.client.get('/cart').get_data(as_text=True)
        self.assertIn('Tồn kho hiện chỉ còn', text)
        self.assertIn('Chưa thể thanh toán', text)
        self.assertIn('/cart', self.client.get('/checkout').headers['Location'])

    def test_deleted_variant_remains_removable(self):
        self._cart({'9999999': 1})
        body = self.client.get('/cart').get_data(as_text=True)
        self.assertIn('Sản phẩm hoặc size/màu này không còn tồn tại', body)
        self.assertIn('cart/remove/9999999', body)
        self.client.get('/cart')
        with self.client.session_transaction() as sess:
            token = sess['_csrf']
        r = self.client.post('/cart/remove/9999999', data={'csrf_token':token})
        self.assertEqual(r.status_code, 302)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess['cart'], {})

    def test_visible_available_item_keeps_real_current_price(self):
        self._cart({'1': 1})
        self._edit('UPDATE SanPham SET GiaBan=1350000 WHERE MaSanPham=1')
        html = self.client.get('/cart').get_data(as_text=True)
        self.assertIn('1.350.000', html)
        self.assertNotIn('Chưa thể thanh toán', html)

    def test_cart_helper(self):
        self.assertIn('hết hàng', cart_unavailable_reason({'HienThi': 1, 'SoLuongTon': 0, 'quantity': 1}))
        self.assertEqual('', cart_unavailable_reason({'HienThi': 1, 'SoLuongTon': 3, 'quantity': 2}))

if __name__ == '__main__':
    unittest.main()
