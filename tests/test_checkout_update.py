"""Kiểm thử sửa checkout và Trạng thái trên SQLite demo; không kiểm tra cổng thanh toán thực."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from app import create_app


class CheckoutUpdateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.database = str(Path(self.tmp.name) / 'shop.sqlite3')
        self.app = create_app({'TESTING': True, 'DATABASE': self.database, 'SECRET_KEY':'test-checkout'})
        self.c = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def add_cart(self, variant_id=1, quantity=2):
        with self.c.session_transaction() as sess:
            sess['cart'] = {str(variant_id): quantity}
        page = self.c.get('/checkout')
        self.assertEqual(page.status_code, 200)
        with self.c.session_transaction() as sess:
            return sess['_csrf']

    def submit(self, token, **overrides):
        fields = dict(csrf_token=token,full_name='Nguyen Thi Test',phone='0912345678',
                      email='test@example.com',fulfillment='delivery',
                      address='Số 1 đường Test, Hà Nội',payment_method='cod',note='')
        fields.update(overrides)
        return self.c.post('/checkout',data=fields,follow_redirects=True)

    def test_product_status_in_stock(self):
        page = self.c.get('/product/1').get_data(as_text=True)
        self.assertIn('<dt>Trạng thái</dt>', page)
        self.assertIn('Còn hàng', page)
        self.assertNotIn('<dt>Giới tính</dt>', page)

    def test_product_status_sold_out(self):
        with sqlite3.connect(self.database) as conn:
            conn.execute('UPDATE BienTheSanPham SET SoLuongTon=0 WHERE MaSanPham=1')
        page = self.c.get('/product/1').get_data(as_text=True)
        self.assertIn('<dt>Trạng thái</dt><dd><span class="availability sold-out">Hết hàng</span>',page)

    def test_checkout_has_shipping_and_payment(self):
        self.add_cart()
        page = self.c.get('/checkout').get_data(as_text=True)
        for piece in ('Giao hàng tận nơi','Nhận tại cửa hàng','Địa chỉ giao hàng',
                      'Thanh toán khi nhận hàng','Chuyển khoản ngân hàng','value="gateway" disabled',
                      'Phí vận chuyển','Tổng tạm tính'):
            self.assertIn(piece, page)
        self.assertNotIn('Thông tin nhận tại cửa hàng', page)

    def test_checkout_csrf_block(self):
        self.add_cart()
        self.assertEqual(self.submit('invalid').status_code,400)

    def test_checkout_validate_address(self):
        token = self.add_cart()
        response = self.submit(token,address='')
        self.assertIn('Hãy nhập địa chỉ giao hàng',response.get_data(as_text=True))
        with sqlite3.connect(self.database) as c:
            self.assertEqual(c.execute("SELECT COUNT(*) FROM DonHang").fetchone()[0],1)

    def test_checkout_validate_invalid_payment(self):
        token = self.add_cart()
        response = self.submit(token,payment_method='gateway')
        self.assertIn('Cổng online chưa hoạt động',response.get_data(as_text=True))
        with sqlite3.connect(self.database) as c:
            self.assertEqual(c.execute("SELECT COUNT(*) FROM DonHang").fetchone()[0],1)

    def test_checkout_validate_phone(self):
        token = self.add_cart()
        response = self.submit(token,phone='abc')
        self.assertIn('Số điện thoại không hợp lệ',response.get_data(as_text=True))

    def test_checkout_pickup_persists_order_not_paid(self):
        token = self.add_cart(quantity=2)
        response = self.submit(token,fulfillment='pickup',address='',payment_method='cod')
        self.assertEqual(response.status_code,200)
        self.assertIn('Đã ghi nhận yêu cầu đặt hàng',response.get_data(as_text=True))
        self.assertIn('Chưa thanh toán',response.get_data(as_text=True))
        with sqlite3.connect(self.database) as c:
            order = c.execute('SELECT MaDonHang,TongTien,TrangThai FROM DonHang ORDER BY MaDonHang DESC LIMIT 1').fetchone()
            info = c.execute('SELECT HinhThucNhanHang,DiaChiGiaoHang,PhuongThucThanhToan,TrangThaiThanhToan,PhiVanChuyen FROM ThongTinGiaoDich WHERE MaDonHang=?',(order[0],)).fetchone()
            self.assertEqual(order[1],2500000)
            self.assertEqual(order[2],'Chờ xác nhận')
            self.assertEqual(info,('pickup',None,'cod','Chưa thanh toán',0))
            self.assertEqual(c.execute('SELECT SoLuongTon FROM BienTheSanPham WHERE MaBienThe=1').fetchone()[0],8)  # W4-008: tồn bị trừ 2
        with self.c.session_transaction() as sess:
            self.assertEqual(sess['cart'],{})

    def test_checkout_delivery_bank_transfer_pending(self):
        token=self.add_cart(quantity=1)
        response=self.submit(token,payment_method='bank_transfer')
        self.assertIn('Chuyển khoản ngân hàng',response.get_data(as_text=True))
        with sqlite3.connect(self.database) as c:
            info=c.execute('SELECT HinhThucNhanHang,DiaChiGiaoHang,TrangThaiThanhToan,PhiVanChuyen FROM ThongTinGiaoDich ORDER BY MaDonHang DESC LIMIT 1').fetchone()
            self.assertEqual(info,('delivery','Số 1 đường Test, Hà Nội','Chưa thanh toán',None))

    def test_checkout_insufficient_stock_no_order(self):
        token=self.add_cart(quantity=2)
        with sqlite3.connect(self.database) as c:
            c.execute('UPDATE BienTheSanPham SET SoLuongTon=1 WHERE MaBienThe=1')
        r=self.submit(token)
        self.assertIn('không đủ hàng',r.get_data(as_text=True))
        with sqlite3.connect(self.database) as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM DonHang').fetchone()[0],1)

    def test_success_not_public_without_session(self):
        r=self.c.get('/checkout/success')
        self.assertEqual(r.status_code,302)
        self.assertIn('/cart',r.location)


if __name__=='__main__':unittest.main(verbosity=2)
