"""A3 - Bộ sưu tập giày và A6 - gợi ý sản phẩm cho khách."""
from flask import Blueprint, render_template, session
from ..data import get_all_products, get_categories, get_products_by_category
from ..db import query_all
from ..services.best_sellers import get_best_selling_products
from ..services.new_arrivals import get_latest_products

collections = Blueprint("collections", __name__)

@collections.get("/collections")
def index():
    groups = []
    for category in get_categories():
        products = get_products_by_category(category["MaDanhMuc"])
        if products:
            groups.append({"category": category, "products": products[:8]})
    return render_template("collections.html", groups=groups,
        latest_products=get_latest_products(), best_selling_products=get_best_selling_products())

@collections.get("/recommendations")
def recommendations():
    products = get_all_products()
    excluded, preferred_category = set(), None
    user_id = session.get("user_id")
    if user_id and session.get("role") == "Customer":
        try:
            favs = query_all("""SELECT sp.MaSanPham, sp.MaDanhMuc FROM YeuThich yt
                JOIN SanPham sp ON sp.MaSanPham=yt.MaSanPham WHERE yt.MaNguoiDung=?""", (user_id,))
            excluded.update(int(x["MaSanPham"]) for x in favs)
            if favs:
                preferred_category = favs[0]["MaDanhMuc"]
        except Exception:
            pass
    cart = session.get("cart", {})
    if cart:
        try:
            ids = [int(x) for x in cart if str(x).isdigit()]
            if ids:
                marks = ",".join("?" for _ in ids)
                rows = query_all(f"""SELECT DISTINCT sp.MaSanPham, sp.MaDanhMuc FROM BienTheSanPham bt
                    JOIN SanPham sp ON sp.MaSanPham=bt.MaSanPham WHERE bt.MaBienThe IN ({marks})""", tuple(ids))
                excluded.update(int(x["MaSanPham"]) for x in rows)
                if preferred_category is None and rows:
                    preferred_category = rows[0]["MaDanhMuc"]
        except Exception:
            pass
    recommended = [p for p in products if int(p["MaSanPham"]) not in excluded
                   and preferred_category is not None
                   and int(p["MaDanhMuc"]) == int(preferred_category)]
    seen = {int(p["MaSanPham"]) for p in recommended}
    for p in get_best_selling_products() + get_latest_products() + products:
        pid = int(p["MaSanPham"])
        if pid not in excluded and pid not in seen:
            recommended.append(p); seen.add(pid)
        if len(recommended) >= 12:
            break
    return render_template("recommendations.html", products=recommended[:12],
        personalized=preferred_category is not None)
