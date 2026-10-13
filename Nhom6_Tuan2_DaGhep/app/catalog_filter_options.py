"""Danh mục MẪU cho giao diện W3-011, chưa phải mã từ SQL Server.

Chưa nhận danh mục/M2b đã chốt của Minh và Nghĩa. Các id và gender bên
dưới chỉ dùng để thao tác với form GET. Khi ghép backend, truyền danh mục
thật qua app.config['CATALOG_FILTER_OPTIONS']; không lấy thứ tự trong list
để suy ra khóa ngoại, không đưa các id mẫu này vào truy vấn SQL.
"""

DEMO_FILTER_OPTIONS = {
    "brand_id": [
        {"value": "1", "label": "Nike"},
        {"value": "2", "label": "Adidas"},
        {"value": "3", "label": "Biti’s"},
        {"value": "4", "label": "Puma"},
        {"value": "5", "label": "Crocs"},
        {"value": "6", "label": "New Balance"},
        {"value": "7", "label": "Converse"},
        {"value": "8", "label": "Asics"},
        {"value": "9", "label": "Teva"},
    ],
    "type_id": [
        {"value": "1", "label": "Giày thể thao"},
        {"value": "2", "label": "Giày sneaker"},
        {"value": "3", "label": "Dép & sandal"},
    ],
    "gender": [
        {"value": "male", "label": "Nam"},
        {"value": "female", "label": "Nữ"},
        {"value": "unisex", "label": "Unisex"},
    ],
    "color_id": [
        {"value": "1", "label": "Đen"},
        {"value": "2", "label": "Trắng"},
        {"value": "3", "label": "Xám"},
    ],
    "size_id": [
        {"value": "1", "label": "39"},
        {"value": "2", "label": "40"},
        {"value": "3", "label": "41"},
    ],
}
