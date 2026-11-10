"""Kiểm tra form đặt hàng và tạo đơn chờ xác nhận (demo). Không thu tiền thật.

Từ W4-008: tạo đơn TRỪ tồn kho trong transaction; hủy / từ chối / thanh toán thất bại sẽ hoàn lại
(xem order_inventory.py). SQLite tự tạo bảng phụ ThongTinGiaoDich khi đặt hàng.
SQL Server: chạy migration_checkout_sqlserver.sql rồi migration_w4_giao_dich_sqlserver.sql trước.
"""
import re
from .order_inventory import InventoryError, place_order

CHECKOUT_META_SQLITE = """
CREATE TABLE IF NOT EXISTS ThongTinGiaoDich (
    MaDonHang INTEGER PRIMARY KEY REFERENCES DonHang(MaDonHang) ON DELETE CASCADE,
    HoTen TEXT NOT NULL, SoDienThoai TEXT NOT NULL, Email TEXT,
    HinhThucNhanHang TEXT NOT NULL CHECK(HinhThucNhanHang IN ('delivery','pickup')),
    DiaChiGiaoHang TEXT, PhuongThucThanhToan TEXT NOT NULL
      CHECK(PhuongThucThanhToan IN ('cod','bank_transfer')),
    TrangThaiThanhToan TEXT NOT NULL DEFAULT 'Chưa thanh toán',
    PhiVanChuyen REAL,
    GhiChu TEXT, NgayTao TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

class CheckoutValidationError(ValueError):
    pass


def validate_checkout(form):
    data = {key: str(form.get(key, '')).strip() for key in
            ('full_name', 'phone', 'email', 'fulfillment', 'address', 'payment_method', 'note')}
    if not 2 <= len(data['full_name']) <= 100:
        raise CheckoutValidationError('Họ tên phải từ 2 đến 100 ký tự.')
    digits = re.sub(r'\D', '', data['phone'])
    if not 9 <= len(digits) <= 12 or len(data['phone']) > 20:
        raise CheckoutValidationError('Số điện thoại không hợp lệ.')
    if data['email'] and (len(data['email']) > 150 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', data['email'])):
        raise CheckoutValidationError('Email không hợp lệ.')
    if data['fulfillment'] not in {'pickup', 'delivery'}:
        raise CheckoutValidationError('Hãy chọn hình thức nhận hàng.')
    if data['fulfillment'] == 'delivery' and not 8 <= len(data['address']) <= 255:
        raise CheckoutValidationError('Hãy nhập địa chỉ giao hàng đầy đủ (8–255 ký tự).')
    if data['payment_method'] not in {'cod', 'bank_transfer'}:
        raise CheckoutValidationError('Chỉ hỗ trợ COD và yêu cầu chuyển khoản chờ xác nhận. Cổng online chưa hoạt động.')
    if len(data['note']) > 500:
        raise CheckoutValidationError('Ghi chú tối đa 500 ký tự.')
    if data['fulfillment'] == 'pickup':
        data['address'] = ''
    return data


def create_pending_order(form_data, basket, user_id=None):
    """Tạo đơn chờ xác nhận. Toàn bộ nằm trong MỘT transaction (xem order_inventory.place_order):
    kiểm tra + TRỪ tồn theo biến thể, ghi đơn/chi tiết/giao dịch thanh toán; thiếu hàng ở bất kỳ dòng nào thì
    rollback hết (không có đơn, không dòng nào bị trừ). Trả về mã đơn mới.

    Không có webhook/PSP: trạng thái thanh toán luôn CHƯA THANH TOÁN, giao dịch thanh toán ở 'Chờ xử lý'.
    Phí vận chuyển = 0 (chưa tính) cho đến khi cửa hàng xác nhận.
    """
    try:
        return place_order(form_data, basket, user_id)
    except InventoryError as exc:        # InsufficientStockError cũng là InventoryError
        raise CheckoutValidationError(str(exc)) from exc
