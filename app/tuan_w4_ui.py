"""W4-009: UI đơn hàng, nối backend qua provider được nhóm bàn giao.

Không có SQL, không tự quyết định trạng thái/hủy/trừ kho. Mặc định chưa nối
provider và preview tắt. Xem docs/TUAN_W4_ORDER_UI_CONTRACT.md.
"""
from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from flask import (Blueprint, abort, current_app, flash, redirect,
                   render_template, session, url_for, request)
from werkzeug.exceptions import HTTPException

tuan_w4_ui = Blueprint("tuan_w4_ui", __name__)


@tuan_w4_ui.record_once
def connect_order_backend(state):
    """Gắn adapter khi ứng dụng khởi tạo; mặc định vẫn chờ backend thật."""
    from .tuan_w4_connection import configure_order_ui
    configure_order_ui(state.app)


def _customer():
    uid = session.get("user_id")
    if type(uid) is not int or uid < 1:
        return None, redirect(url_for("login", next=request.path))
    if session.get("role") != "Customer":
        return None, (render_template("orders/unavailable.html",
                      reason="forbidden"), 403)
    return uid, None


def _provider():
    return current_app.config.get("TUAN_ORDER_UI_PROVIDER")


def _money(value):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError("Invalid display amount") from None
    if not result.is_finite() or result < 0:
        raise ValueError("Invalid display amount")
    return result


def _order(raw, uid):
    """Kiểm tra contract hiển thị. Backend vẫn phải kiểm quyền ngay khi truy vấn."""
    if not isinstance(raw, Mapping):
        raise ValueError("Order UI provider must return a mapping")
    if type(raw.get("id")) is not int or raw["id"] < 1:
        raise ValueError("Missing order id")
    if type(raw.get("user_id")) is not int or raw["user_id"] != uid:
        abort(404)  # Không tiết lộ đơn thuộc người khác.
    result = dict(raw)
    result["total"] = _money(raw["total"])
    result["items_total"] = _money(raw["items_total"])
    result["shipping_fee"] = None if raw.get("shipping_fee") is None else _money(raw["shipping_fee"])
    result["can_cancel"] = raw.get("can_cancel") is True
    items = raw.get("items", [])
    if not isinstance(items, (list, tuple)):
        raise ValueError("Invalid items")
    result["items"] = []
    for item in items:
        if not isinstance(item, Mapping) or type(item.get("quantity")) is not int or item["quantity"] < 1:
            raise ValueError("Invalid item quantity")
        result["items"].append(dict(item, unit_price=_money(item["unit_price"]),
                                    subtotal=_money(item["subtotal"])))
    result["receiver"] = dict(raw.get("receiver") or {})
    return result


def _unavailable():
    return render_template("orders/unavailable.html", reason="backend"), 503


@tuan_w4_ui.app_context_processor
def shared_order_ui():
    return {"order_ui_connected": _provider() is not None}


@tuan_w4_ui.get("/my-orders")
def my_orders():
    uid, response = _customer()
    if response is not None:
        return response
    provider = _provider()
    if provider is None:
        return _unavailable()
    try:
        raw = provider.list_orders(user_id=uid)
        if not isinstance(raw, (list, tuple)):
            raise ValueError("Invalid order list")
        orders = [_order(item, uid) for item in raw]
    except (ValueError, KeyError, TypeError):
        current_app.logger.error("Order UI provider returned an invalid contract")
        return _unavailable()
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise
        current_app.logger.error("Order UI provider list unavailable")
        return _unavailable()
    return render_template("orders/list.html", orders=orders)


@tuan_w4_ui.get("/my-orders/<int:order_id>")
def order_detail(order_id):
    uid, response = _customer()
    if response is not None:
        return response
    provider = _provider()
    if provider is None:
        return _unavailable()
    try:
        raw = provider.get_order(user_id=uid, order_id=order_id)
        if raw is None:
            abort(404)
        order = _order(raw, uid)
        if order["id"] != order_id:
            raise ValueError("Wrong order id")
    except (ValueError, KeyError, TypeError):
        current_app.logger.error("Invalid order detail contract")
        return _unavailable()
    except HTTPException:
        raise
    except Exception:
        current_app.logger.error("Order UI provider detail unavailable")
        return _unavailable()
    return render_template("orders/detail.html", order=order,
                           cancel_connected=callable(getattr(provider, "cancel_order", None)))


@tuan_w4_ui.post("/my-orders/<int:order_id>/cancel")
def cancel_order(order_id):
    # prepare_csrf() của dự án bảo vệ mọi POST trước khi vào route này.
    uid, response = _customer()
    if response is not None:
        return response
    provider = _provider()
    if provider is None:
        return _unavailable()
    cancel = getattr(provider, "cancel_order", None)
    if not callable(cancel):
        return _unavailable()
    try:
        raw = provider.get_order(user_id=uid, order_id=order_id)
        if raw is None:
            abort(404)
        order = _order(raw, uid)
        if order["id"] != order_id:
            abort(404)
    except HTTPException:
        raise
    except Exception:
        current_app.logger.error("Order UI provider cancellation lookup unavailable")
        return _unavailable()
    if not order["can_cancel"]:
        flash("Đơn hiện không đủ điều kiện hủy. Vui lòng kiểm tra trạng thái mới nhất.", "warning")
        return redirect(url_for("tuan_w4_ui.order_detail", order_id=order_id))
    try:
        # Provider phải tự kiểm lại owner/state trong transaction; UI không thay thế bước đó.
        result = cancel(user_id=uid, order_id=order_id)
    except Exception:
        current_app.logger.error("Order cancellation provider unavailable")
        flash("Chưa nhận được kết quả hủy. Hãy tải lại trạng thái đơn trước khi thử tiếp.", "warning")
    else:
        if isinstance(result, Mapping) and result.get("ok") is True:
            flash("Backend đã xác nhận hủy đơn. Kiểm tra trạng thái cập nhật bên dưới.", "success")
        else:
            flash("Chưa hủy được đơn. Đơn có thể đã thay đổi trạng thái; vui lòng kiểm tra lại.", "warning")
    return redirect(url_for("tuan_w4_ui.order_detail", order_id=order_id))


@tuan_w4_ui.get("/ui-preview/w4/<scenario>")
def preview(scenario):
    if not current_app.config.get("TUAN_W4_PREVIEW"):
        abort(404)
    from .tuan_w4_preview import preview_orders
    orders = preview_orders()
    context = {"preview_mode": True, "preview_scenario": scenario}
    if scenario in {"orders", "empty"}:
        return render_template("orders/list.html", orders=orders if scenario == "orders" else [], **context)
    if scenario in {"detail", "shipping", "completed", "failed", "cancelled"}:
        index = {"detail": 0, "shipping": 1, "completed": 2, "failed": 3, "cancelled": 4}[scenario]
        return render_template("orders/detail.html", order=orders[index], cancel_connected=False, **context)
    if scenario in {"unavailable", "forbidden", "not-found"}:
        return render_template("orders/unavailable.html",
                               reason={"unavailable": "backend", "forbidden": "forbidden",
                                       "not-found": "not-found"}[scenario], **context)
    abort(404)
