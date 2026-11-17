"""W13 K3 – SQL dữ liệu tạm: không thay đổi đơn gốc."""
import sqlite3
import unittest
from app.services.w13_reorder import build_reorder_plan, add_plan_to_cart, select_reorder_quantities, ReorderValidationError, OrderAccessError


class ReorderTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
        CREATE TABLE DonHang (MaDonHang INTEGER, MaNguoiDung INTEGER, TrangThai TEXT);
        CREATE TABLE SanPham (MaSanPham INTEGER, TenSanPham TEXT, GiaBan REAL, HienThi INTEGER);
        CREATE TABLE BienTheSanPham (MaBienThe INTEGER, MaSanPham INTEGER, KichThuoc TEXT, MauSac TEXT, SoLuongTon INTEGER);
        CREATE TABLE ChiTietDonHang (MaChiTietDon INTEGER, MaDonHang INTEGER, MaBienThe INTEGER, SoLuong INTEGER, TenSanPham TEXT, KichThuoc TEXT, MauSac TEXT);
        INSERT INTO DonHang VALUES (12, 7, 'Hoàn thành');
        INSERT INTO SanPham VALUES (3, 'Giày thử A', 550000, 1), (4,'Giày thử B',450000,1);
        INSERT INTO BienTheSanPham VALUES (31,3,'42','Đen',1),(41,4,'41','Trắng',0);
        INSERT INTO ChiTietDonHang VALUES (1,12,31,3,'Giày thử A','42','Đen'),(2,12,41,1,'Giày thử B','41','Trắng');
        ''')
    def tearDown(self):
        self.db.close()
    def one(self, sql, args):
        r = self.db.execute(sql, args).fetchone()
        return dict(r) if r else None
    def all(self, sql, args):
        return [dict(r) for r in self.db.execute(sql,args).fetchall()]
    def plan(self, user=7):
        return build_reorder_plan(12,user,self.one,self.all)

    def test_only_owner(self):
        with self.assertRaises(OrderAccessError) as e: self.plan(8)
        self.assertEqual(e.exception.status_code,403)
    def test_missing_order(self):
        with self.assertRaises(OrderAccessError) as e: build_reorder_plan(999,7,self.one,self.all)
        self.assertEqual(e.exception.status_code,404)
    def test_current_price_stock_and_soldout(self):
        a,b=self.plan()['items']
        self.assertEqual(a['current_price'],550000)
        self.assertEqual(a['quantity_addable'],1)
        self.assertEqual(b['quantity_addable'],0)
        self.assertIn('hết hàng',b['reason'])
    def test_changed_price_is_current(self):
        self.db.execute('UPDATE SanPham SET GiaBan=620000 WHERE MaSanPham=3')
        self.assertEqual(self.plan()['items'][0]['current_price'],620000)
    def test_hidden_product(self):
        self.db.execute('UPDATE SanPham SET HienThi=0 WHERE MaSanPham=3')
        self.assertEqual(self.plan()['items'][0]['quantity_addable'],0)
    def test_cart_has_no_checkout_side_effect(self):
        before = self.db.execute('SELECT COUNT(*) FROM DonHang').fetchone()[0]
        cart,added,skipped=add_plan_to_cart(self.plan(),{})
        after = self.db.execute('SELECT COUNT(*) FROM DonHang').fetchone()[0]
        self.assertEqual(before,after)
        self.assertEqual(cart,{'31':1})
        self.assertEqual(len(added),1)
        self.assertTrue(skipped)
    def test_not_exceed_cart_and_stock(self):
        cart,added,skipped=add_plan_to_cart(self.plan(),{'31':1})
        self.assertEqual(cart['31'],1)
        self.assertFalse(added)
    def test_selected_quantity_only_adds_selected_variant(self):
        cart, added = select_reorder_quantities(self.plan(), {}, {'31':'1','41':'0'})
        self.assertEqual(cart, {'31': 1})
        self.assertEqual(added[0]['quantity'], 1)

    def test_selected_quantity_does_not_overflow_stock(self):
        with self.assertRaises(ReorderValidationError):
            select_reorder_quantities(self.plan(), {'31':1}, {'31':'1'})

    def test_invalid_selection_never_mutates_original_cart(self):
        existing = {'31': 1}
        for raw in ('-1','abc','100','2'):
            with self.assertRaises(ReorderValidationError):
                select_reorder_quantities(self.plan(), existing, {'31':raw})
        self.assertEqual(existing, {'31':1})

    def test_forged_variant_and_empty_selection_rejected(self):
        with self.assertRaises(ReorderValidationError):
            select_reorder_quantities(self.plan(), {}, {'999':'1'})
        with self.assertRaises(ReorderValidationError):
            select_reorder_quantities(self.plan(), {}, {'31':'0'})

    def test_hidden_item_cannot_be_purchased_again(self):
        self.db.execute('UPDATE SanPham SET HienThi=0 WHERE MaSanPham=3')
        with self.assertRaises(ReorderValidationError):
            select_reorder_quantities(self.plan(), {}, {'31':'1'})

    def test_single_item_click_adds_one_to_existing_cart_not_entire_order(self):
        self.db.execute('UPDATE BienTheSanPham SET SoLuongTon=5 WHERE MaBienThe=31')
        old_count = self.db.execute('SELECT COUNT(*) FROM DonHang').fetchone()[0]
        cart, added = select_reorder_quantities(self.plan(), {'31': 2}, {'31': '1'})
        self.assertEqual(cart, {'31': 3})
        self.assertEqual(len(added), 1)
        self.assertEqual(added[0]['quantity'], 1)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM DonHang').fetchone()[0], old_count)

    def test_missing_variant_not_added(self):
        self.db.execute('DELETE FROM BienTheSanPham WHERE MaBienThe=31')
        plan=self.plan()
        self.assertEqual(plan['items'][0]['quantity_addable'],0)
        cart,added,skip=add_plan_to_cart(plan,{})
        self.assertFalse(added)
        self.assertEqual(cart,{})

if __name__=='__main__': unittest.main()
