"""Trạng thái form GET W3-011; không tạo điều kiện lọc hoặc ORDER BY SQL."""
from decimal import Decimal, InvalidOperation

SELECT_FIELDS = (
    ("brand_id", "Thương hiệu"),
    ("type_id", "Loại sản phẩm"),
    ("gender", "Giới tính"),
    ("color_id", "Màu"),
    ("size_id", "Size"),
)
SORT_OPTIONS = (
    {"value": "price_asc", "label": "Giá tăng dần"},
    {"value": "price_desc", "label": "Giá giảm dần"},
    {"value": "name_asc", "label": "Tên A–Z"},
    {"value": "brand_asc", "label": "Thương hiệu A–Z"},
)
FORM_KEYS = ("q", "brand_id", "type_id", "gender", "color_id", "size_id",
             "price_min", "price_max", "sort")


def prepare_filter_ui(query_args, option_catalogs):
    """Giữ chuỗi đã nhập để Jinja render value/selected; page do form đặt về 1.

    Danh mục có dạng {query_key: [{value: id_thật, label: tên_hiển_thị}, ...]}.
    Các lỗi bên dưới chỉ giải thích trạng thái form. Validation và truy vấn
    thật khi tích hợp bộ lọc thuộc backend W3-031/032/033.
    """
    values = {key: query_args.get(key, "", type=str) for key in FORM_KEYS}
    # Cùng quy tắc từ khóa với route Tuần 2/W3-010.
    values["q"] = values["q"].strip()[:80]
    errors, selects, chosen = {}, [], []
    if values["q"]:
        chosen.append({"label": "Từ khóa", "value": values["q"]})

    for key, label in SELECT_FIELDS:
        options = [{"value": str(item["value"]), "label": str(item["label"])}
                   for item in option_catalogs.get(key, [])]
        labels = {item["value"]: item["label"] for item in options}
        selected = values[key]
        if selected and selected not in labels:
            # Giữ giá trị trên URL, không âm thầm đổi sang một mã khác.
            unknown_label = "Mã chưa có trong danh mục: " + selected
            options.append({"value": selected, "label": unknown_label})
            labels[selected] = unknown_label
            errors[key] = "Lựa chọn này chưa có trong danh mục hiện tại."
        if selected:
            chosen.append({"label": label, "value": labels[selected]})
        selects.append({"name": key, "label": label, "options": options,
                        "selected": selected})

    prices = {}
    for key, label in (("price_min", "Giá từ"), ("price_max", "Giá đến")):
        raw = values[key]
        if not raw:
            continue
        chosen.append({"label": label, "value": raw + " ₫"})
        try:
            price = Decimal(raw)
            if not price.is_finite() or price < 0:
                raise InvalidOperation
            prices[key] = price
        except (InvalidOperation, ValueError):
            errors[key] = "Giá phải là số không âm."
    if ("price_min" in prices and "price_max" in prices
            and prices["price_min"] > prices["price_max"]):
        errors["price_max"] = "Giá đến phải lớn hơn hoặc bằng Giá từ."

    sort_options = [dict(item) for item in SORT_OPTIONS]
    sort_labels = {item["value"]: item["label"] for item in sort_options}
    if values["sort"]:
        if values["sort"] not in sort_labels:
            sort_label = "Kiểu chưa có trong danh sách: " + values["sort"]
            sort_options.append({"value": values["sort"], "label": sort_label})
            sort_labels[values["sort"]] = sort_label
            errors["sort"] = "Kiểu sắp xếp này chưa có trong danh sách hiện tại."
        chosen.append({"label": "Sắp xếp", "value": sort_labels[values["sort"]]})

    return {"values": values, "selects": selects, "sort_options": sort_options,
            "chosen": chosen, "errors": errors}
