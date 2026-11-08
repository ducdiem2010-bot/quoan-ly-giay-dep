"""Flask integration scenarios; run only after Flask installed.
Do not mark PASS based on existence of this file."""
import unittest, tempfile, sqlite3, re
from pathlib import Path
from app import create_app

class ExtensionsW3(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=str(Path(self.temp.name)/'demo.sqlite3')
        self.app=create_app({'TESTING':True, 'DATABASE':self.path,'SECRET_KEY':'test-only'})
        self.c=self.app.test_client()
    def tearDown(self): self.temp.cleanup()
    def token(self,url):
        html=self.c.get(url).get_data(as_text=True)
        match=re.search(r'name="csrf_token" value="([^"]+)"', html)
        self.assertIsNotNone(match)
        return match.group(1)
    def login(self, email):
        t=self.token('/login')
        r=self.c.post('/login',data={'csrf_token':t,'email':email,'password':'Demo@12345'})
        self.assertIn(r.status_code,(302,303))
    def test_12_seed_and_hidden(self):
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('select count(*) from SanPham').fetchone()[0],12)
            self.assertEqual(db.execute('select count(*) from SanPham where HienThi=0').fetchone()[0],1)
        self.assertEqual(self.c.get('/product/12').status_code,404)
    def test_variant_api_same_row(self):
        resp=self.c.get('/api/products/1/variants?color=%C4%90en&size=40')
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.get_json()['variants'],[])
        self.assertEqual(self.c.get('/api/products/12/variants').status_code,404)
    def test_favorite_toggle(self):
        self.login('khach@shop.vn')
        t=self.token('/product/1')
        self.assertEqual(self.c.post('/favorites/1/toggle',data={'csrf_token':t}).status_code,302)
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('select count(*) from YeuThich where MaNguoiDung=3 and MaSanPham=1').fetchone()[0],1)
        self.c.post('/favorites/1/toggle',data={'csrf_token':t})
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('select count(*) from YeuThich where MaNguoiDung=3 and MaSanPham=1').fetchone()[0],0)
    def test_seller_no_favorite(self):
        self.login('minh@shop.vn')
        t=self.token('/product/1')
        self.assertEqual(self.c.post('/favorites/1/toggle',data={'csrf_token':t}).status_code,403)
    def test_variant_edit_admin(self):
        self.login('admin@shop.vn')
        t=self.token('/admin/products/1/variants')
        r=self.c.post('/admin/products/1/variants/1/edit',data={'csrf_token':t,'size':'39','color':'Đen','stock':'3'})
        self.assertEqual(r.status_code,302)
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('select SoLuongTon from BienTheSanPham where MaBienThe=1').fetchone()[0],3)
    def test_atomic_product_variant_failure(self):
        self.login('admin@shop.vn')
        t=self.token('/admin/products/new')
        self.c.post('/admin/products/new',data={'csrf_token':t,'name':'Test rollback W3','category_id':'1','price':'200000','initial_size':'40','initial_color':'','initial_stock':'1'})
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("select count(*) from SanPham where TenSanPham='Test rollback W3'").fetchone()[0],0)

if __name__=='__main__': unittest.main(verbosity=2)
