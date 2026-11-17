"""Đánh giá sản phẩm: kiểm thử theo kịch bản QA tối thiểu của đặc tả (chỉ SQLite)."""
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest

from app import create_app


class ProductReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dbpath = str(Path(self.tmp.name) / 'reviews.sqlite3')
        self.app = create_app({'TESTING': True, 'DB_BACKEND': 'sqlite', 'DATABASE': self.dbpath,
                               'SECRET_KEY': 'review-test-key'})
        self.c = self.app.test_client()
        # Khách (id 3) có đơn Hoàn thành chứa SP1 (biến thể 1) và đơn Chờ xác nhận chứa SP2 (biến thể 4).
        self.sql("INSERT INTO DonHang(MaDonHang,MaNguoiDung,TrangThai) VALUES (101,3,'Hoàn thành')")
        self.sql("INSERT INTO ChiTietDonHang(MaDonHang,MaBienThe,SoLuong,DonGia) VALUES (101,1,1,1250000)")
        self.sql("INSERT INTO DonHang(MaDonHang,MaNguoiDung,TrangThai) VALUES (102,3,'Chờ xác nhận')")
        self.sql("INSERT INTO ChiTietDonHang(MaDonHang,MaBienThe,SoLuong,DonGia) VALUES (102,4,1,990000)")

    def tearDown(self):
        self.tmp.cleanup()

    def sql(self, statement, params=()):
        with closing(sqlite3.connect(self.dbpath)) as db:
            cur = db.execute(statement, params)
            db.commit()
            return cur.fetchall() if statement.lstrip().upper().startswith('SELECT') else None

    def token(self):
        self.c.get('/login')
        with self.c.session_transaction() as s:
            return s['_csrf']

    def login(self, email):
        self.c.post('/login', data={'csrf_token': self.token(), 'email': email, 'password': 'Demo@12345'})

    def post_review(self, product_id=1, json=False, **fields):
        data = {'so_sao': '5', 'noi_dung': 'Giày êm chân, đi cả ngày không đau.'}
        data.update(fields)
        token = self.token()
        if json:
            return self.c.post(f'/product/{product_id}/reviews', json=data, headers={'X-CSRF-Token': token})
        data['csrf_token'] = token
        return self.c.post(f'/product/{product_id}/reviews', data=data)

    # ---------- Gửi đánh giá ----------
    def test_happy_path_saves_and_updates_average(self):
        self.login('khach@shop.vn')
        res = self.post_review(so_sao='5', noi_dung='Giày rất đẹp, vừa chân, giao nhanh!')
        self.assertEqual(res.status_code, 302)
        self.assertTrue(res.location.endswith('/product/1#reviews'))
        row = self.sql('SELECT SoSao,MaDonHang,TrangThaiHienThi FROM DanhGiaSanPham')[0]
        self.assertEqual(row, (5, 101, 1))
        html = self.c.get('/product/1').get_data(as_text=True)
        self.assertIn('5.0', html)
        self.assertIn('1 lượt đánh giá', html)
        self.assertIn('Giày rất đẹp', html)
        self.assertIn('Đã mua hàng', html)
        self.assertIn('Size 39', html)

    def test_json_success_is_201(self):
        self.login('khach@shop.vn')
        res = self.post_review(json=True)
        self.assertEqual(res.status_code, 201)
        self.assertIn('review_id', res.get_json())

    def test_guest_is_401(self):
        res = self.post_review(json=True)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.get_json()['code'], 401)
        self.assertEqual(self.sql('SELECT COUNT(*) FROM DanhGiaSanPham')[0][0], 0)

    def test_guest_form_redirects_to_login(self):
        res = self.post_review()
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.location)

    def test_seller_and_admin_are_403(self):
        for email in ('minh@shop.vn', 'admin@shop.vn'):
            self.c = self.app.test_client()
            self.login(email)
            self.assertEqual(self.post_review(json=True).status_code, 403, email)

    def test_not_purchased_or_order_not_completed_is_403(self):
        self.login('khach@shop.vn')
        self.assertEqual(self.post_review(product_id=3, json=True).status_code, 403)  # chưa mua
        self.assertEqual(self.post_review(product_id=2, json=True).status_code, 403)  # đơn Chờ xác nhận

    def test_other_users_order_is_403(self):
        self.sql("INSERT INTO DonHang(MaDonHang,MaNguoiDung,TrangThai) VALUES (103,1,'Hoàn thành')")
        self.sql("INSERT INTO ChiTietDonHang(MaDonHang,MaBienThe,SoLuong,DonGia) VALUES (103,7,1,250000)")
        self.login('khach@shop.vn')
        self.assertEqual(self.post_review(product_id=3, json=True, ma_don_hang='103').status_code, 403)

    def test_invalid_input_is_400(self):
        self.login('khach@shop.vn')
        for bad in ({'so_sao': '0'}, {'so_sao': '6'}, {'so_sao': 'abc'}, {'so_sao': '4.5'}, {'so_sao': ''},
                    {'noi_dung': 'ngắn'}, {'noi_dung': '<b></b>   '}, {'noi_dung': 'x' * 1001},
                    {'ma_don_hang': 'abc'}, {'tieu_de': 'y' * 151}):
            with self.subTest(bad=bad):
                self.assertEqual(self.post_review(json=True, **bad).status_code, 400)
        self.assertEqual(self.sql('SELECT COUNT(*) FROM DanhGiaSanPham')[0][0], 0)

    def test_duplicate_is_409(self):
        self.login('khach@shop.vn')
        self.assertEqual(self.post_review(json=True).status_code, 201)
        self.assertEqual(self.post_review(json=True).status_code, 409)
        self.assertEqual(self.post_review(json=True, ma_don_hang='101').status_code, 409)
        self.assertEqual(self.sql('SELECT COUNT(*) FROM DanhGiaSanPham')[0][0], 1)

    def test_auto_picks_latest_unreviewed_completed_order(self):
        self.sql("INSERT INTO DonHang(MaDonHang,MaNguoiDung,TrangThai,NgayDat) VALUES (104,3,'Hoàn thành','2099-01-01')")
        self.sql("INSERT INTO ChiTietDonHang(MaDonHang,MaBienThe,SoLuong,DonGia) VALUES (104,2,1,1250000)")
        self.login('khach@shop.vn')
        self.assertEqual(self.post_review(json=True).status_code, 201)
        self.assertEqual(self.sql('SELECT MaDonHang FROM DanhGiaSanPham')[0][0], 104)
        self.assertEqual(self.post_review(json=True).status_code, 201)   # đơn 101 còn lại
        self.assertEqual(self.post_review(json=True).status_code, 409)

    def test_missing_csrf_is_400(self):
        self.login('khach@shop.vn')
        res = self.c.post('/product/1/reviews', data={'so_sao': '5', 'noi_dung': 'Nội dung hợp lệ rồi.'})
        self.assertEqual(res.status_code, 400)

    def test_html_is_stripped_and_escaped(self):
        self.login('khach@shop.vn')
        self.post_review(noi_dung='<script>alert(1)</script>Giày dùng rất tốt', tieu_de='<b>Tuyệt</b>')
        html = self.c.get('/product/1').get_data(as_text=True)
        self.assertNotIn('<script>alert', html)
        stored = self.sql('SELECT NoiDung,TieuDe FROM DanhGiaSanPham')[0]
        self.assertNotIn('<', stored[0] + stored[1])

    # ---------- Hiển thị ----------
    def seed_reviews(self):
        for i, stars in enumerate((5, 4, 4, 1, 3), start=1):
            self.sql("INSERT INTO DonHang(MaDonHang,MaNguoiDung,TrangThai) VALUES (?,3,'Hoàn thành')", (200 + i,))
            self.sql("INSERT INTO ChiTietDonHang(MaDonHang,MaBienThe,SoLuong,DonGia) VALUES (?,1,1,1)", (200 + i,))
            self.sql("""INSERT INTO DanhGiaSanPham(MaSanPham,MaNguoiDung,MaDonHang,SoSao,NoiDung,NgayDanhGia)
                        VALUES (1,3,?,?,?,?)""", (200 + i, stars, f'Nhận xét số {i} đủ dài', f'2026-01-0{i} 10:00:00'))

    def test_empty_summary(self):
        html = self.c.get('/product/1').get_data(as_text=True)
        self.assertIn('0.0', html)
        self.assertIn('0 lượt đánh giá', html)
        self.assertIn('Chưa có đánh giá nào', html)

    def test_summary_filter_sort_and_pagination(self):
        self.seed_reviews()
        html = self.c.get('/product/1').get_data(as_text=True)
        self.assertIn('3.4', html)  # (5+4+4+1+3)/5 = 3.4
        self.assertIn('5 lượt đánh giá', html)
        self.assertLess(html.index('Nhận xét số 5'), html.index('Nhận xét số 1'))  # mới nhất trước
        only4 = self.c.get('/product/1?rating=4').get_data(as_text=True)
        self.assertIn('Nhận xét số 2', only4)
        self.assertNotIn('Nhận xét số 4', only4)
        low = self.c.get('/product/1?sort=lowest').get_data(as_text=True)
        self.assertLess(low.index('Nhận xét số 4'), low.index('Nhận xét số 1'))
        high = self.c.get('/product/1?sort=highest').get_data(as_text=True)
        self.assertLess(high.index('Nhận xét số 1'), high.index('Nhận xét số 4'))
        for q in ('?rating=99', '?sort=zzz', '?page=abc', '?page=999'):
            self.assertEqual(self.c.get('/product/1' + q).status_code, 200, q)
        self.assertEqual(self.c.get('/product/1?page=2').status_code, 200)

    def test_pagination_10_per_page(self):
        self.seed_reviews()
        for i in range(6, 16):
            self.sql("INSERT INTO DonHang(MaDonHang,MaNguoiDung,TrangThai) VALUES (?,3,'Hoàn thành')", (200 + i,))
            self.sql("""INSERT INTO DanhGiaSanPham(MaSanPham,MaNguoiDung,MaDonHang,SoSao,NoiDung)
                        VALUES (1,3,?,5,'Nhận xét thêm đủ dài')""", (200 + i,))
        p1 = self.c.get('/product/1').get_data(as_text=True)
        self.assertEqual(p1.count('class="rv-item"'), 10)
        self.assertIn('Trang 1 / 2', p1)
        self.assertEqual(self.c.get('/product/1?page=2').get_data(as_text=True).count('class="rv-item"'), 5)

    def test_hidden_product_and_unknown_product_are_404(self):
        self.assertEqual(self.c.get('/product/9999').status_code, 404)
        self.sql('UPDATE SanPham SET HienThi=0 WHERE MaSanPham=1')
        self.assertEqual(self.c.get('/product/1').status_code, 404)
        self.login('khach@shop.vn')
        self.assertEqual(self.post_review(json=True).status_code, 404)

    # ---------- Quản trị ----------
    def test_admin_toggle_hides_and_reply(self):
        self.seed_reviews()
        self.login('admin@shop.vn')
        token = self.token()
        res = self.c.post('/admin/reviews/1/toggle', data={'csrf_token': token, 'phan_hoi_shop': 'Cảm ơn bạn đã ủng hộ!'})
        self.assertEqual(res.status_code, 302)
        row = self.sql('SELECT TrangThaiHienThi,PhanHoiShop,NgayPhanHoi FROM DanhGiaSanPham WHERE MaDanhGia=1')[0]
        self.assertEqual(row[0], 0)
        self.assertEqual(row[1], 'Cảm ơn bạn đã ủng hộ!')
        self.assertIsNotNone(row[2])
        public = self.c.get('/product/1').get_data(as_text=True)
        self.assertNotIn('Nhận xét số 1', public)
        self.assertIn('4 lượt đánh giá', public)
        self.c.post('/admin/reviews/1/toggle', data={'csrf_token': token})  # bật lại
        self.assertEqual(self.sql('SELECT TrangThaiHienThi FROM DanhGiaSanPham WHERE MaDanhGia=1')[0][0], 1)
        self.assertIn('Cảm ơn bạn đã ủng hộ!', self.c.get('/product/1').get_data(as_text=True))

    def test_admin_reply_only_keeps_visibility_and_seller_allowed(self):
        self.seed_reviews()
        self.login('minh@shop.vn')
        res = self.c.post('/admin/reviews/2/reply', data={'csrf_token': self.token(), 'phan_hoi_shop': 'Shop xin cảm ơn'})
        self.assertEqual(res.status_code, 302)
        self.assertEqual(self.sql('SELECT TrangThaiHienThi,PhanHoiShop FROM DanhGiaSanPham WHERE MaDanhGia=2')[0], (1, 'Shop xin cảm ơn'))
        self.assertEqual(self.c.get('/admin/reviews').status_code, 200)

    def test_admin_routes_permissions_and_404(self):
        self.seed_reviews()
        guest = self.c.post('/admin/reviews/1/toggle', json={}, headers={'X-CSRF-Token': self.token()})
        self.assertEqual(guest.status_code, 401)
        self.login('khach@shop.vn')
        token = self.token()
        self.assertEqual(self.c.post('/admin/reviews/1/toggle', data={'csrf_token': token}).status_code, 403)
        self.assertEqual(self.c.get('/admin/reviews').status_code, 403)
        self.c = self.app.test_client()
        self.login('admin@shop.vn')
        self.assertEqual(self.c.post('/admin/reviews/9999/toggle', data={'csrf_token': self.token()}).status_code, 404)
        self.assertEqual(self.c.post('/admin/reviews/1/toggle', data={'csrf_token': self.token(), 'phan_hoi_shop': 'a' * 501}).status_code, 302)
        self.assertEqual(self.sql('SELECT TrangThaiHienThi FROM DanhGiaSanPham WHERE MaDanhGia=1')[0][0], 1)

    def test_admin_list_filters(self):
        self.seed_reviews()
        self.login('admin@shop.vn')
        self.assertIn('Nhận xét số 4', self.c.get('/admin/reviews?rating=1').get_data(as_text=True))
        self.assertEqual(self.c.get('/admin/reviews?status=9').status_code, 400)

    # ---------- Form trên trang sản phẩm ----------
    def test_form_visibility_by_role(self):
        page = self.c.get('/product/1').get_data(as_text=True)
        self.assertIn('đăng nhập</a> để đánh giá', page)
        self.assertNotIn('name="so_sao"', page)
        self.login('khach@shop.vn')
        self.assertIn('name="so_sao"', self.c.get('/product/1').get_data(as_text=True))
        self.assertNotIn('name="so_sao"', self.c.get('/product/3').get_data(as_text=True))  # chưa mua
        self.post_review()
        self.assertIn('Bạn đã đánh giá sản phẩm này', self.c.get('/product/1').get_data(as_text=True))


if __name__ == '__main__':
    unittest.main()
