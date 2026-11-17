"""Regression: render Jinja templates with representative data (no Flask server required).

This catches runtime-only errors that a Jinja syntax/compile check cannot detect,
including dictionary key collisions such as `plan.items` -> dict.items().
"""
from pathlib import Path
from types import SimpleNamespace
import unittest

from jinja2 import Environment, FileSystemLoader


TEMPLATES = Path(__file__).resolve().parents[1] / 'app' / 'templates'


def fake_url_for(endpoint, **kwargs):
    suffix = '/' + '/'.join(f'{k}-{v}' for k, v in kwargs.items()) if kwargs else ''
    return '/' + endpoint.replace('.', '/') + suffix


class W13TemplateRenderTests(unittest.TestCase):
    def setUp(self):
        self.env = Environment(loader=FileSystemLoader(str(TEMPLATES)), autoescape=True)
        self.env.filters['vnd'] = lambda value: f'{float(value or 0):,.0f} đ'.replace(',', '.')
        self.env.filters['vn_datetime'] = lambda value: str(value or '')
        self.env.globals['url_for'] = fake_url_for
        self.env.globals['get_flashed_messages'] = lambda **_kwargs: []
        self.env.globals['product_image_url'] = lambda product: '/static/images/storefront/test-shoe.jpg'
        self.common = {
            'request': SimpleNamespace(url_rule=None, endpoint='w13_tuan.reorder'),
            'session': {'user_id': 3, 'user_name': 'Khách demo', 'role': 'Customer'},
            'categories': [], 'cart_count': 0, 'tab': 'orders',
            'csrf_token': 'fake-csrf-token',
            'store_info': SimpleNamespace(zalo_group_name='Hỗ trợ', staff_support_label='Hỗ trợ',
                                          zalo_url='#', hotline_is_active=False,
                                          hotline_tel='', hotline=''),
        }

    def render(self, filename, **kwargs):
        return self.env.get_template(filename).render(**(self.common | kwargs))

    def test_reorder_preview_renders_product_rows_and_form(self):
        plan = {'order': {'MaDonHang': 25}, 'items': [
            {'MaBienThe': 101, 'TenSanPham': 'Giày đen thử nghiệm', 'KichThuoc': '42',
             'MauSac': 'Đen', 'SoLuongMua': 2, 'in_cart': 0, 'current_price': 175000,
             'available_to_add': 2, 'reason': ''},
            {'MaBienThe': 102, 'TenSanPham': 'Giày trắng thử nghiệm', 'KichThuoc': '39',
             'MauSac': 'Trắng', 'SoLuongMua': 1, 'in_cart': 0, 'current_price': 220000,
             'available_to_add': 0, 'reason': 'Hết hàng'}]}
        output = self.render('w13/reorder_preview.html', plan=plan, reorder_token='dummy')
        self.assertIn('Giày đen thử nghiệm', output)
        self.assertIn('Giày trắng thử nghiệm', output)
        self.assertIn('name="qty_101"', output)
        self.assertIn('name="qty_102"', output)
        self.assertIn('Xác nhận thêm vào giỏ', output)

    def test_reorder_preview_empty_plan_renders_without_500(self):
        output = self.render('w13/reorder_preview.html',
                             plan={'order': {'MaDonHang': 25}, 'items': []},
                             reorder_token='dummy')
        self.assertIn('Đơn chưa có sản phẩm', output)
        self.assertIn('disabled', output)

    def test_recent_page_renders_in_account(self):
        context = dict(self.common)
        context['request'] = SimpleNamespace(url_rule=None, endpoint='w13_tuan.recently_viewed_page')
        output = self.env.get_template('w13/recent_page.html').render(**context)
        self.assertIn('Sản phẩm vừa xem', output)
        self.assertIn('Lịch sử đơn hàng', output)
        self.assertIn('w13_recently_viewed.js', output)

    def test_account_order_history_renders_links(self):
        order = {
            'MaDonHang': 25, 'NgayDat': '2026-11-17 06:00:00',
            'TrangThai': 'Hoàn thành', 'TrangThaiGiaoHang': 'Đã giao',
            'TrangThaiThanhToan': 'Đã thanh toán', 'DiaChiGiaoHang': '',
            'TongTien': 175000, 'SoLuongDaTra': 0, 'TienDaHoan': 0,
            'TienGiamDaDuyet': 0, 'TongTienSauTra': 175000,
            'return_status': 'Chưa trả hàng', 'returns': [], 'refund_history': [],
            'refund_summary': {'status': 'Chưa hoàn tiền', 'approved': 0, 'refunded': 0, 'remaining': 0},
            'can_cancel': False,
            'items': [{'MaSanPham': 1, 'MaBienThe': 11, 'HienThiHienTai': 1, 'TonHienTai': 3, 'GiaHienTai': 200000, 'TenSanPham': 'Giày đen thử nghiệm',
                       'KichThuoc': '42', 'MauSac': 'Đen', 'SoLuong': 1,
                       'DaTra': 0, 'DonGia': 175000}],
        }
        output = self.render('account_orders.html', orders=[order])
        self.assertIn('Giày đen thử nghiệm', output)
        self.assertNotIn('Chọn sản phẩm mua lại', output)
        self.assertIn('/product_detail/product_id-1', output)
        self.assertNotIn('add_order_item_to_cart', output)
        self.assertNotIn('<form method="post"', output.split('w13-bought-list', 1)[1].split('</ul>',1)[0])
        self.assertIn('test-shoe.jpg', output)
        self.assertIn('Xem chi tiết sản phẩm', output)
        self.assertIn('Xem tiến trình đơn', output)

    def test_hidden_product_has_no_link_and_out_of_stock_product_still_links(self):
        order = {
            'MaDonHang': 25, 'NgayDat': '2026-11-17 06:00:00',
            'TrangThai': 'Đã xác nhận', 'TrangThaiGiaoHang': 'Chưa giao',
            'TrangThaiThanhToan': 'Chưa thanh toán', 'DiaChiGiaoHang': '',
            'TongTien': 175000, 'SoLuongDaTra': 0, 'TienDaHoan': 0,
            'TienGiamDaDuyet': 0, 'TongTienSauTra': 175000,
            'return_status': 'Chưa trả hàng', 'returns': [], 'refund_history': [],
            'refund_summary': {'status': 'Không cần hoàn', 'approved': 0, 'refunded': 0, 'remaining': 0},
            'can_cancel': False,
            'items': [
                {'MaSanPham': 11, 'MaBienThe': 10, 'HienThiHienTai': 1, 'TonHienTai': 0,
                 'GiaHienTai': 200000, 'TenSanPham': 'Giày hết hàng',
                 'KichThuoc':'42','MauSac':'Đen','SoLuong':1,'DaTra':0,'DonGia':175000},
                {'MaSanPham': 12, 'MaBienThe': 11, 'HienThiHienTai': 0, 'TonHienTai': 3,
                 'GiaHienTai': 200000, 'TenSanPham':'Giày đã ẩn',
                 'KichThuoc':'42','MauSac':'Đen','SoLuong':1,'DaTra':0,'DonGia':175000}
            ]
        }
        html = self.render('account_orders.html', orders=[order])
        self.assertIn('/product_detail/product_id-11', html)
        self.assertNotIn('/product_detail/product_id-12', html)
        self.assertIn('Sản phẩm không còn hiển thị', html)
        self.assertNotIn('add_order_item_to_cart', html)

    def test_timeline_page_renders_real_events(self):
        output = self.render('w13/timeline_page.html', info={
            'order_id': 25, 'status': 'Đã xác nhận', 'shipping_status': 'Chưa giao',
            'events': [{'name': 'Đã đặt hàng', 'timestamp': '2026-11-17 06:00:00'}],
            'has_unknown_times': True})
        self.assertIn('Tiến trình đơn #25', output)
        self.assertIn('Đã đặt hàng', output)
        self.assertNotIn('Giày đen thử nghiệm', output)


if __name__ == '__main__':
    unittest.main()
