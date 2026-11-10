"""W4-008: kiểm thử transaction tồn kho (trừ/hoàn đúng 1 lần, hết tồn, rollback, đồng thời).

Chạy trên SQLite test tạo trong thư mục tạm. SQL Server (UPDLOCK/ROWLOCK) CHƯA được chạy thật.
"""
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path

from app import create_app
from app.services import order_inventory as inv
from app.services.checkout import CheckoutValidationError, create_pending_order

CONTACT = dict(full_name='Nguyen Test', phone='0912 345 678', email='', fulfillment='delivery',
               address='Số 1 đường Test, Hà Nội', payment_method='cod', note='')
CUSTOMER, STAFF = 3, 2          # khach@shop.vn (Customer), minh@shop.vn (Seller) trong seed


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.tmp.name) / 'inv.sqlite3')
        self.app = create_app({'TESTING': True, 'DATABASE': self.db, 'SECRET_KEY': 'x'})
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()
        self.tmp.cleanup()

    def q(self, sql, *args):
        with sqlite3.connect(self.db) as c:
            return c.execute(sql, args).fetchall()

    def stock(self, vid):
        return self.q('SELECT SoLuongTon FROM BienTheSanPham WHERE MaBienThe=?', vid)[0][0]

    def order(self, basket, method='cod', user=CUSTOMER):
        return create_pending_order(dict(CONTACT, payment_method=method), basket, user)

    def row(self, oid):
        return self.q('SELECT TrangThai,TrangThaiXacNhan,TrangThaiGiaoHang,TrangThaiThanhToan,DaHuy,DaTruKho '
                      'FROM DonHang WHERE MaDonHang=?', oid)[0]

    # --- trừ tồn ---
    def test_place_order_deducts_per_variant_and_records_snapshot(self):
        before1, before4 = self.stock(1), self.stock(4)
        oid = self.order({'1': 2, '4': 1})
        self.assertEqual((self.stock(1), self.stock(4)), (before1 - 2, before4 - 1))
        self.assertEqual(self.row(oid), ('Chờ xác nhận', 'Chờ xác nhận', 'Chưa giao', 'Chưa thanh toán', 0, 1))
        self.assertEqual(self.q('SELECT TongTien,SdtNguoiNhan,PhuongThucThanhToan FROM DonHang WHERE MaDonHang=?', oid)[0],
                         (2 * 1250000 + 990000, '0912345678', 'COD'))
        snap = self.q('SELECT TenSanPham,MauSac,KichThuoc FROM ChiTietDonHang WHERE MaDonHang=? AND MaBienThe=1', oid)[0]
        self.assertEqual(snap, ('Nike Air Zoom Pegasus', 'Đen', '39'))
        self.assertEqual(self.q('SELECT TrangThai,SoTien FROM GiaoDichThanhToan WHERE MaDonHang=?', oid),
                         [('Chờ xử lý', 3490000.0)])

    # --- hết tồn / rollback ---
    def test_insufficient_stock_rolls_back_everything(self):
        s1, s4 = self.stock(1), self.stock(4)
        orders = self.q('SELECT COUNT(*) FROM DonHang')[0][0]
        with self.assertRaises(CheckoutValidationError):
            self.order({'1': 1, '4': s4 + 1})           # dòng 1 hợp lệ, dòng 2 thiếu hàng
        self.assertEqual((self.stock(1), self.stock(4)), (s1, s4))
        self.assertEqual(self.q('SELECT COUNT(*) FROM DonHang')[0][0], orders)

    def test_sold_out_and_hidden_variants_cannot_be_ordered(self):
        sold_out = self.q('SELECT MaBienThe FROM BienTheSanPham WHERE SoLuongTon=0 LIMIT 1')[0][0]
        hidden = self.q('SELECT bt.MaBienThe FROM BienTheSanPham bt JOIN SanPham sp ON sp.MaSanPham=bt.MaSanPham '
                        'WHERE sp.HienThi=0 LIMIT 1')[0][0]
        for vid in (sold_out, hidden):
            with self.assertRaises(CheckoutValidationError):
                self.order({str(vid): 1})
        self.assertGreaterEqual(min(r[0] for r in self.q('SELECT SoLuongTon FROM BienTheSanPham')), 0)

    def test_invalid_basket_rejected(self):
        for bad in ({}, {'1': 0}, {'1': 100}, {'abc': 1}, {'-3': 1}):
            with self.assertRaises(CheckoutValidationError):
                self.order(bad)

    # --- hoàn tồn đúng 1 lần ---
    def test_customer_cancel_restores_once(self):
        before = self.stock(1)
        oid = self.order({'1': 3})
        inv.cancel_order(oid, customer_id=CUSTOMER)
        self.assertEqual(self.stock(1), before)
        self.assertEqual(self.row(oid), ('Đã hủy', 'Chờ xác nhận', 'Chưa giao', 'Chưa thanh toán', 1, 0))
        with self.assertRaises(inv.InvalidOrderStateError):
            inv.cancel_order(oid, customer_id=CUSTOMER)  # lần 2 không được hoàn thêm
        self.assertEqual(self.stock(1), before)

    def test_reject_restores_once_and_blocks_further_cancel(self):
        before = self.stock(4)
        oid = self.order({'4': 2})
        inv.reject_order(oid, STAFF)
        self.assertEqual(self.stock(4), before)
        self.assertEqual(self.row(oid)[:2], ('Đã hủy', 'Từ chối'))
        for call in (lambda: inv.reject_order(oid, STAFF), lambda: inv.cancel_order(oid, staff_id=STAFF)):
            with self.assertRaises(inv.InvalidOrderStateError):
                call()
        self.assertEqual(self.stock(4), before)

    def test_payment_failed_restores_once_and_marks_transaction(self):
        before = self.stock(1)
        oid = self.order({'1': 2}, method='bank_transfer')
        inv.mark_payment_failed(oid)
        self.assertEqual(self.stock(1), before)
        self.assertEqual(self.q('SELECT TrangThai FROM GiaoDichThanhToan WHERE MaDonHang=?', oid), [('Thất bại',)])
        with self.assertRaises(inv.InvalidOrderStateError):
            inv.mark_payment_failed(oid)
        self.assertEqual(self.stock(1), before)

    def test_cod_has_no_online_payment_failure(self):
        oid = self.order({'1': 1})
        with self.assertRaises(inv.InvalidOrderStateError):
            inv.mark_payment_failed(oid)

    def test_confirm_keeps_stock_deducted_and_customer_cannot_cancel_confirmed(self):
        before = self.stock(1)
        oid = self.order({'1': 1})
        inv.confirm_order(oid, STAFF)
        self.assertEqual(self.stock(1), before - 1)
        with self.assertRaises(inv.InvalidOrderStateError):
            inv.cancel_order(oid, customer_id=CUSTOMER)
        inv.cancel_order(oid, staff_id=STAFF)            # nhân viên vẫn hủy được trước khi giao
        self.assertEqual(self.stock(1), before)

    def test_cancel_paid_order_marks_refund(self):
        oid = self.order({'1': 1}, method='bank_transfer')
        inv.mark_paid(oid, 'FT0001')
        self.assertEqual(self.row(oid)[3], 'Đã thanh toán')
        inv.cancel_order(oid, staff_id=STAFF)
        self.assertEqual(self.row(oid)[3], 'Hoàn tiền')
        self.assertEqual(self.q('SELECT TrangThai FROM GiaoDichThanhToan WHERE MaDonHang=?', oid), [('Hoàn tiền',)])

    def test_permissions(self):
        oid = self.order({'1': 1})
        with self.assertRaises(inv.InvalidOrderStateError):
            inv.cancel_order(oid, customer_id=999)       # không phải chủ đơn
        with self.assertRaises(inv.InvalidOrderStateError):
            inv.confirm_order(oid, CUSTOMER)             # khách không được xác nhận

    def test_payment_reference_unique(self):
        a, b = self.order({'1': 1}, 'bank_transfer'), self.order({'4': 1}, 'bank_transfer')
        inv.mark_paid(a, 'FT-DUP')
        with self.assertRaises(inv.InvalidOrderStateError):
            inv.mark_paid(b, 'FT-DUP')
        self.assertEqual(self.row(b)[3], 'Chưa thanh toán')  # rollback, không đánh dấu nửa chừng
        with self.assertRaises(inv.InvalidOrderStateError):
            inv.mark_paid(a, 'FT-OTHER')                      # không thu tiền hai lần

    # --- đồng thời ---
    def test_concurrent_orders_never_oversell(self):
        with sqlite3.connect(self.db) as c:
            c.execute('UPDATE BienTheSanPham SET SoLuongTon=5 WHERE MaBienThe=1')
        results, barrier = [], threading.Barrier(10)

        def buy():
            with self.app.app_context():
                barrier.wait()
                try:
                    self.order({'1': 1})
                    results.append('ok')
                except CheckoutValidationError:
                    results.append('het')
        threads = [threading.Thread(target=buy) for _ in range(10)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        self.assertEqual((results.count('ok'), results.count('het')), (5, 5))
        self.assertEqual(self.stock(1), 0)
        self.assertEqual(self.q("SELECT COUNT(*) FROM DonHang WHERE DaTruKho=1")[0][0], 5)

    def test_legacy_orders_migrated_not_lost(self):
        row = self.q('SELECT TrangThai,TrangThaiXacNhan,TongTien,LaDonCu,DaTruKho FROM DonHang WHERE MaDonHang=1')[0]
        self.assertEqual(row, ('Đã xác nhận', 'Đã xác nhận', 3490000.0, 1, 0))
        self.assertEqual(self.q('SELECT COUNT(*) FROM ChiTietDonHang WHERE TenSanPham IS NULL')[0][0], 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
