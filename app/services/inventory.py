"""Quy tắc cảnh báo tồn kho. Không cập nhật số lượng trong CSDL."""

LOW_STOCK_THRESHOLD = 5  # 1..5: sắp hết; 0: hết hàng


def stock_status(quantity):
    """Đánh giá tổng tồn các biến thể của một sản phẩm."""
    amount = int(quantity or 0)
    if amount <= 0:
        return {"kind": "empty", "label": "Hết hàng"}
    if amount <= LOW_STOCK_THRESHOLD:
        return {"kind": "low", "label": "Sắp hết hàng"}
    return {"kind": "available", "label": "Còn hàng"}
