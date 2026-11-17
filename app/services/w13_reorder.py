"""W13/Tuấn: kế hoạch mua lại chỉ đọc đơn cũ; không sao chép giá hoặc đặt đơn.
Dùng truy vấn ? tương thích SQLite và pyodbc SQL Server.
"""

class OrderAccessError(ValueError):
    def __init__(self, status_code=403):
        self.status_code = status_code
        super().__init__('Không có quyền truy cập đơn hàng này')


def build_reorder_plan(order_id, user_id, query_one_fn=None, query_all_fn=None):
    """Đối soát mỗi biến thể với tồn kho và giá hiện hành, chưa làm thay đổi DB/session."""
    if query_one_fn is None or query_all_fn is None:
        from ..db import query_one, query_all
        query_one_fn, query_all_fn = query_one, query_all
    order = query_one_fn('SELECT MaDonHang, MaNguoiDung, TrangThai FROM DonHang WHERE MaDonHang=?', (order_id,))
    if order is None:
        raise OrderAccessError(404)
    if int(order['MaNguoiDung'] or -1) != int(user_id):
        raise OrderAccessError(403)
    rows = query_all_fn('''SELECT ct.MaBienThe, ct.SoLuong AS SoLuongMua,
                COALESCE(ct.TenSanPham,sp.TenSanPham) AS TenSanPham,
                COALESCE(ct.KichThuoc,bt.KichThuoc) AS KichThuoc,
                COALESCE(ct.MauSac,bt.MauSac) AS MauSac,
                sp.GiaBan, sp.HienThi, bt.SoLuongTon, bt.MaSanPham
            FROM ChiTietDonHang ct
            LEFT JOIN BienTheSanPham bt ON bt.MaBienThe=ct.MaBienThe
            LEFT JOIN SanPham sp ON sp.MaSanPham=bt.MaSanPham
            WHERE ct.MaDonHang=? ORDER BY ct.MaChiTietDon''', (order_id,))
    items = []
    for row in rows:
        item = dict(row)
        stock = max(0, int(item['SoLuongTon'] or 0))
        active = item['MaSanPham'] is not None and int(item['HienThi'] or 0) == 1
        purchased = int(item['SoLuongMua'])
        addable = min(purchased, stock, 99) if active else 0
        if not active:
            reason = 'Sản phẩm không còn được bán'
        elif stock == 0:
            reason = 'Biến thể đã hết hàng'
        elif addable < purchased:
            reason = 'Tồn kho hiện tại thấp hơn số lượng đã mua'
        else:
            reason = ''
        item.update(quantity_addable=addable, reason=reason,
                    current_price=float(item['GiaBan'] or 0) if active else None)
        items.append(item)
    return {'order': order, 'items': items}


def add_plan_to_cart(plan, existing_cart):
    """Trả về giỏ MỚI + các dòng đã thêm và lý do bỏ qua. Không tự ghi session/DB.
    Tồn kho có thể đổi sau bước này; checkout phải xác nhận lại trước khi tạo đơn.
    """
    cart = dict(existing_cart or {})
    added, skipped = [], []
    for item in plan['items']:
        if item['MaBienThe'] is None:
            skipped.append({'variant_id': None, 'reason': 'Biến thể gốc không còn tồn tại'})
            continue
        key = str(int(item['MaBienThe']))
        stock = max(0, int(item['SoLuongTon'] or 0))
        in_cart = max(0, int(cart.get(key, 0)))
        can_add = max(0, min(int(item['quantity_addable']), stock - in_cart, 99 - in_cart))
        if can_add:
            cart[key] = in_cart + can_add
            added.append({'variant_id': int(key), 'quantity': can_add, 'current_price': item['current_price']})
        if can_add < int(item['SoLuongMua']):
            skipped.append({'variant_id': int(key), 'reason': item['reason'] or 'Giỏ hàng đã có sản phẩm hoặc không đủ tồn kho'})
    return cart, added, skipped


class ReorderValidationError(ValueError):
    """Dữ liệu mua lại không hợp lệ hoặc tồn kho đã thay đổi."""


def select_reorder_quantities(plan, existing_cart, requested):
    """Kiểm tra toàn bộ lựa chọn TRƯỚC KHI sửa giỏ hàng.

    requested: mapping MaBienThe (chuỗi) -> số đôi (chuỗi).
    Số 0 có nghĩa bỏ qua dòng đó; không tự thêm hàng hết tồn hoặc hàng bị ẩn.
    Hàm không gây side effect và không tạo đơn hàng mới.
    """
    cart = dict(existing_cart or {})
    allowed = {}
    for item in plan['items']:
        if item['MaBienThe'] is not None:
            key = str(int(item['MaBienThe']))
            allowed[key] = item

    if not isinstance(requested, dict) or set(requested) - set(allowed):
        raise ReorderValidationError('Danh sách biến thể không hợp lệ. Vui lòng tải lại trang.')
    added = []
    for key, item in allowed.items():
        raw = requested.get(key, '0')
        if not isinstance(raw, str) or not raw.isascii() or not raw.isdecimal() or len(raw) > 3:
            raise ReorderValidationError('Số đôi mua lại phải là số nguyên từ 0 đến 99.')
        qty = int(raw)
        if qty < 0 or qty > 99:
            raise ReorderValidationError('Số đôi mua lại phải trong khoảng 0–99.')
        if not qty:
            continue
        if item['quantity_addable'] <= 0:
            raise ReorderValidationError(f"{item['TenSanPham']} không còn bán hoặc đã hết hàng.")
        try:
            before = int(cart.get(key, 0))
        except (ValueError, TypeError):
            raise ReorderValidationError('Giỏ hàng có số lượng không hợp lệ. Vui lòng kiểm tra giỏ.')
        if before < 0 or before > 99:
            raise ReorderValidationError('Giỏ hàng có số lượng không hợp lệ. Vui lòng kiểm tra giỏ.')
        stock = max(0, int(item['SoLuongTon'] or 0))
        limit = min(int(item['quantity_addable']), stock-before, 99-before)
        if qty > limit:
            raise ReorderValidationError(
                f"{item['TenSanPham']} (size {item['KichThuoc']}, màu {item['MauSac']}) "
                f"chỉ thêm được tối đa {max(0, limit)} đôi; hãy tải lại và chọn số lượng.")
        cart[key] = before + qty
        added.append({'variant_id': int(key), 'quantity': qty, 'current_price': item['current_price']})
    if not added:
        raise ReorderValidationError('Bạn chưa chọn sản phẩm nào để mua lại.')
    return cart, added
