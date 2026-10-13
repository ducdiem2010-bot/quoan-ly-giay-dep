"""Dữ liệu trình bày cho khung danh sách W3-010.

Tạm chia danh sách do get_all_products trả về để kiểm tra UI. Phân trang
COUNT/OFFSET/FETCH trực tiếp trên SQL Server thuộc nhiệm vụ W3-018.
"""
from urllib.parse import urlencode

PAGE_SIZE = 10


def prepare_catalog_page(products, query_args, list_url):
    total = len(products)
    page_count = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    try:
        requested_page = int(query_args.get("page", "1"))
    except (TypeError, ValueError):
        requested_page = 1
    page = min(max(1, requested_page), page_count)
    start = (page - 1) * PAGE_SIZE
    items = products[start:start + PAGE_SIZE]

    # Giữ query hiện có. Không chuyển tên tham số do người dùng cung cấp
    # trực tiếp vào url_for, vì Flask có các tham số đặc biệt như _external.
    query = [(key, value) for key, value in query_args.items(multi=True)
             if key != "page"]

    def page_url(number):
        return list_url + "?" + urlencode(query + [("page", number)]) + "#catalog-products"

    pagination = {
        "page": page,
        "page_size": PAGE_SIZE,
        "total": total,
        "page_count": page_count,
        "first_item": start + 1 if total else 0,
        "last_item": start + len(items),
        "prev_url": page_url(page - 1) if page > 1 else None,
        "next_url": page_url(page + 1) if page < page_count else None,
    }
    return items, pagination
