"""W13/Tuấn: chỉ hiển thị dấu thời gian có trong DB, không nội suy lịch sử."""
from .w13_reorder import OrderAccessError


def build_timeline(order, user_id):
    if int(order.get('MaNguoiDung') or -1) != int(user_id):
        raise OrderAccessError(403)
    status = (order.get('TrangThai') or 'Không xác định').strip()
    events = []
    mapping = (
        ('Đã đặt hàng', 'NgayDat'),
        ('Đã xác nhận', 'ThoiGianXacNhan'),
        ('Đang giao hàng', 'ThoiGianBatDauGiao'),
        ('Hoàn thành', 'ThoiGianHoanThanh'),
    )
    for label, field in mapping:
        if order.get(field):
            events.append({'name': label, 'timestamp': order[field], 'field': field})
    if status == 'Đã hủy':
        events.append({'name': 'Đã hủy', 'timestamp': order.get('ThoiGianHuy'), 'field': 'ThoiGianHuy'})
    return {'order_id': order['MaDonHang'], 'status': status,
            'shipping_status': order.get('TrangThaiGiaoHang') or 'Chưa giao',
            'events': events, 'complete_history': all(order.get(f) for _,f in mapping),
            'has_unknown_times': any(not order.get(f) for _,f in mapping)}


def get_timeline(order_id, user_id, query_one_fn=None):
    if query_one_fn is None:
        from ..db import query_one
        query_one_fn = query_one
    order = query_one_fn('''SELECT MaDonHang, MaNguoiDung, TrangThai, TrangThaiGiaoHang,
               NgayDat, ThoiGianXacNhan, ThoiGianBatDauGiao, ThoiGianGiaoThanhCong,
               ThoiGianHoanThanh, ThoiGianHuy
               FROM DonHang WHERE MaDonHang=?''', (order_id,))
    if order is None:
        raise OrderAccessError(404)
    return build_timeline(order, user_id)
