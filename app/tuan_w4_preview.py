"""Dữ liệu hư cấu chỉ cho preview UI; không ghi DB hoặc gắn vào provider thật."""
from copy import deepcopy


def preview_orders():
    base = {
        "id": 4101, "user_id": 3, "created_at": "01/11/2026 09:00",
        "status_label": "Chờ xác nhận", "payment_status": "pending",
        "payment_status_label": "Chưa thanh toán", "delivery_stage": "pending",
        "fulfillment": "delivery", "payment_method_label": "Thanh toán khi nhận hàng",
        "items_total": 1250000, "shipping_fee": None, "total": 1250000,
        "can_cancel": True,
        "receiver": {"name": "Khách minh họa", "phone": "••••••1234",
                     "address": "Địa chỉ minh họa — không phải địa chỉ thật"},
        "items": [{"product_name": "Nike Air Zoom Pegasus", "size": "39", "color": "Đen",
                   "quantity": 1, "unit_price": 1250000, "subtotal": 1250000}],
    }
    variants = [
        {},
        {"id": 4102, "status_label": "Đang vận chuyển", "delivery_stage": "shipping",
         "can_cancel": False},
        {"id": 4103, "status_label": "Hoàn thành", "delivery_stage": "completed",
         "payment_status": "paid", "payment_status_label": "Đã thanh toán", "can_cancel": False},
        {"id": 4104, "status_label": "Chờ xử lý", "payment_status": "failed",
         "payment_status_label": "Thanh toán thất bại", "can_cancel": False,
         "payment_method_label": "Cổng thanh toán — dữ liệu mẫu"},
        {"id": 4105, "status_label": "Đã hủy", "delivery_stage": "cancelled",
         "payment_status": "cancelled", "payment_status_label": "Giao dịch đã hủy",
         "can_cancel": False},
    ]
    return [dict(deepcopy(base), **changes) for changes in variants]
