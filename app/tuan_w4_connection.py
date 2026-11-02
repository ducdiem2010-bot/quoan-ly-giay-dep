"""Điểm ghép UI Tuấn với backend Nghĩa. Không có SQL hay nghiệp vụ kho/hủy.

Factory tùy chọn: TUAN_ORDER_UI_PROVIDER_FACTORY=app.nghia_order_ui:create_provider
Factory nhận app và trả provider list_orders/get_order/cancel_order (tùy chọn).
"""
import importlib
import os


class OrderUIConnectionError(RuntimeError):
    """Cấu hình bộ nối không hợp lệ; không mở ứng dụng với adapter sai."""


class OrderUIAdapter:
    """Bọc các hàm backend, tùy chọn đổi dữ liệu qua to_order_view.

    Callback backend nhận user_id/order_id dạng keyword và tự kiểm quyền.
    Callback hủy phải tự kiểm trạng thái trong transaction, trả {"ok": bool}.
    Không có callback hủy thì UI chỉ đọc, không cung cấp nút hủy.
    """

    def __init__(self, *, list_orders, get_order, cancel_order=None,
                 to_order_view=None):
        if not callable(list_orders) or not callable(get_order):
            raise OrderUIConnectionError("Cần hàm backend list_orders và get_order.")
        if cancel_order is not None and not callable(cancel_order):
            raise OrderUIConnectionError("cancel_order phải là hàm hoặc None.")
        if to_order_view is not None and not callable(to_order_view):
            raise OrderUIConnectionError("to_order_view phải là hàm hoặc None.")
        self._list_orders = list_orders
        self._get_order = get_order
        self._to_view = to_order_view or (lambda order: order)
        self.cancel_order = cancel_order

    def list_orders(self, *, user_id):
        rows = self._list_orders(user_id=user_id)
        if not isinstance(rows, (list, tuple)):
            raise ValueError("Backend phải trả list/tuple đơn, [] khi thực sự rỗng.")
        return [self._to_view(row) for row in rows]

    def get_order(self, *, user_id, order_id):
        row = self._get_order(user_id=user_id, order_id=order_id)
        return None if row is None else self._to_view(row)


def bind_order_ui_provider(app, provider):
    """Gắn provider thật vào app, dùng cả khi backend ghép trực tiếp bằng Python."""
    if provider is None or isinstance(provider, type):
        raise OrderUIConnectionError("Provider phải là một instance backend.")
    for method in ("list_orders", "get_order"):
        if not callable(getattr(provider, method, None)):
            raise OrderUIConnectionError("Provider thiếu hàm " + method + ".")
    cancel = getattr(provider, "cancel_order", None)
    if cancel is not None and not callable(cancel):
        raise OrderUIConnectionError("Provider có cancel_order không hợp lệ.")
    app.config["TUAN_ORDER_UI_PROVIDER"] = provider
    return provider


def configure_order_ui(app):
    """Ưu tiên provider trực tiếp, sau đó factory trong config hoặc biến môi trường.

    Không cấu hình -> provider None và UI trả 503 như bản trước.
    Cấu hình sai -> lỗi khởi động rõ ràng, không tự chuyển sang provider mẫu.
    Mỗi app tạo provider riêng, không cache toàn cục và không bật preview.
    """
    provider = app.config.get("TUAN_ORDER_UI_PROVIDER")
    if provider is not None:
        return bind_order_ui_provider(app, provider)
    path = app.config.get("TUAN_ORDER_UI_PROVIDER_FACTORY",
                          os.getenv("TUAN_ORDER_UI_PROVIDER_FACTORY", ""))
    if path is None or path == "":
        return None
    if not isinstance(path, str):
        raise OrderUIConnectionError("Factory phải có dạng module:ten_ham.")
    module, separator, function = path.strip().partition(":")
    if (not separator or not module or not function.isidentifier()
            or not all(part.isidentifier() for part in module.split("."))):
        raise OrderUIConnectionError("Factory phải có dạng module:ten_ham.")
    try:
        factory = getattr(importlib.import_module(module), function)
        if not callable(factory):
            raise TypeError("Factory not callable")
        with app.app_context():
            provider = factory(app)
        return bind_order_ui_provider(app, provider)
    except Exception:
        # Không đưa chuỗi lỗi DB/credentials của backend ra log công khai.
        raise OrderUIConnectionError(
            "Không khởi tạo được provider đơn hàng. Kiểm tra module factory, "
            "các callback và cấu hình DB test của backend."
        ) from None

