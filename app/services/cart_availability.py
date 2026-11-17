"""Xác định biến thể giỏ còn được bán hay không; không ghi thay đổi DB/session."""


def cart_unavailable_reason(row):
    if row.get('missing'):
        return 'Sản phẩm hoặc size/màu này không còn tồn tại.'
    if not bool(row.get('HienThi', 0)):
        return 'Sản phẩm hiện không còn được bán.'
    try:
        stock = int(row.get('SoLuongTon') or 0)
        quantity = int(row.get('quantity') or 0)
    except (TypeError, ValueError):
        return 'Số lượng giỏ hàng không hợp lệ.'
    if stock <= 0:
        return 'Biến thể đã hết hàng.'
    if quantity <= 0 or quantity > 99:
        return 'Số lượng giỏ hàng không hợp lệ.'
    if quantity > stock:
        return f'Tồn kho hiện chỉ còn {stock} đôi; vui lòng cập nhật số lượng.'
    return ''
