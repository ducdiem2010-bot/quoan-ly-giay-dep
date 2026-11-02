"""Kiểm thử tự động SQLite thử nghiệm W3; KHÔNG xác minh SQL Server."""
import tempfile,unittest,sqlite3,re
from pathlib import Path
from app import create_app

class IntegrationW3(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.db_path=str(Path(self.temp.name)/'test.sqlite3')
        self.app=create_app({'TESTING':True,'DATABASE':self.db_path,'SECRET_KEY':'only-tests'})
        self.c=self.app.test_client()
    def tearDown(self):self.temp.cleanup()
    def get(self,p):return self.c.get(p)
    def token(self,p='/'):
        page=self.get(p).get_data(as_text=True)
        match=re.search(r'name="csrf_token" value="([^\"]+)"',page)
        self.assertIsNotNone(match,p)
        return match.group(1)
    def admin(self):
        tok=self.token('/login')
        resp=self.c.post('/login',data={'csrf_token':tok,'email':'admin@shop.vn','password':'Demo@12345'},follow_redirects=True)
        self.assertEqual(resp.status_code,200)
    def test_public_catalog(self):
        r=self.get('/products');self.assertEqual(r.status_code,200)
        self.assertIn('Danh sách sản phẩm',r.get_data(as_text=True))
    def test_search_existing(self):
        t=self.get('/products?q=Converse').get_data(as_text=True)
        self.assertIn('Converse Chuck Taylor',t);self.assertNotIn('Nike Air Zoom Pegasus',t)
    def test_search_empty(self):
        t=self.get('/products?q=KHONG_CO_999999').get_data(as_text=True)
        self.assertIn('Không tìm thấy sản phẩm',t)
    def test_paging(self):
        r=self.get('/products?page=2');self.assertEqual(r.status_code,200)
        self.assertIn('Trang 2 / 2',r.get_data(as_text=True))
    def test_filter_category_brand(self):
        t=self.get('/products?type_id=2&brand=Adidas').get_data(as_text=True)
        self.assertIn('Adidas Originals Superstar',t);self.assertNotIn('Nike Air Zoom Pegasus',t)
    def test_variant_same_row(self):
        t=self.get('/products?color=%C4%90en&size=40').get_data(as_text=True)
        self.assertIn('Không tìm thấy sản phẩm',t)
    def test_sort_price_asc(self):
        t=self.get('/products?sort=price_asc').get_data(as_text=True)
        self.assertLess(t.index('Biti’s Hunter Sandal'),t.index('Crocs Classic Clog'))
    def test_detail(self):
        t=self.get('/product/1').get_data(as_text=True)
        self.assertIn('Màu, size và tồn kho',t)
    def test_admin_unauth(self):
        r=self.get('/admin/products');self.assertEqual(r.status_code,302)
        self.assertIn('/login',r.location)
    def test_admin_seller_forbidden(self):
        tok=self.token('/login')
        self.c.post('/login',data={'csrf_token':tok,'email':'minh@shop.vn','password':'Demo@12345'})
        self.assertEqual(self.get('/admin/products').status_code,403)
    def test_admin_form_and_crud(self):
        self.admin()
        self.assertEqual(self.get('/admin/products/new').status_code,200)
        tok=self.token('/admin/products/new')
        r=self.c.post('/admin/products/new',data={'csrf_token':tok,'name':'Test W3 Giày thử','category_id':'1','price':'320000','brand':'Nhóm 6','description':'Dữ liệu test'},follow_redirects=True)
        self.assertEqual(r.status_code,200)
        self.assertIn('Test W3 Giày thử',r.get_data(as_text=True))
        with sqlite3.connect(self.db_path) as con:
            pid=con.execute('SELECT MaSanPham FROM SanPham WHERE TenSanPham=?',('Test W3 Giày thử',)).fetchone()[0]
        tok=self.token(f'/admin/products/{pid}/edit')
        r=self.c.post(f'/admin/products/{pid}/edit',data={'csrf_token':tok,'name':'Giày đã sửa W3','category_id':'1','price':'350000','brand':'Nhóm 6','description':'Sửa thành công'},follow_redirects=True)
        self.assertIn('Giày đã sửa W3',r.get_data(as_text=True))
        tok=self.token('/admin/products')
        self.c.post(f'/admin/products/{pid}/visibility',data={'csrf_token':tok})
        self.assertEqual(self.get(f'/product/{pid}').status_code,404)
        self.assertNotIn('Giày đã sửa W3',self.get('/products').get_data(as_text=True))
    def test_admin_negative_price_rollback(self):
        self.admin()
        tok=self.token('/admin/products/new')
        self.c.post('/admin/products/new',data={'csrf_token':tok,'name':'Sản phẩm giá âm','category_id':'1','price':'-7'})
        with sqlite3.connect(self.db_path) as c:
            self.assertEqual(c.execute("SELECT COUNT(*) FROM SanPham WHERE TenSanPham='Sản phẩm giá âm'").fetchone()[0],0)
    def test_admin_add_variant_duplicate_rejected(self):
        self.admin()
        tok=self.token('/admin/products/1/variants')
        self.c.post('/admin/products/1/variants',data={'csrf_token':tok,'size':'45','color':'Tím','stock':'5'})
        tok=self.token('/admin/products/1/variants')
        r=self.c.post('/admin/products/1/variants',data={'csrf_token':tok,'size':'45','color':'Tím','stock':'5'},follow_redirects=True)
        self.assertIn('Không thêm được',r.get_data(as_text=True))
        with sqlite3.connect(self.db_path) as c:
            self.assertEqual(c.execute("SELECT COUNT(*) FROM BienTheSanPham WHERE MaSanPham=1 AND KichThuoc='45' AND MauSac='Tím'").fetchone()[0],1)
    def test_csrf_block(self):
        self.admin()
        self.assertEqual(self.c.post('/admin/products/new',data={}).status_code,400)

if __name__=='__main__':unittest.main(verbosity=2)
