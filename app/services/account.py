"""Thông tin khách hàng: hồ sơ tài khoản, thông tin mặc định khi đặt hàng, lịch sử đơn.

Dùng chung cho trang /account và bước /checkout. Truy vấn đều tham số hóa bằng dấu ?.
Cột mở rộng của NguoiDung: Ho, Ten, GioiTinh, NgaySinh, TinhThanh, PhuongXa
(SQLite tự thêm khi khởi động; SQL Server chạy database/migrate_account_profile_sqlserver.sql).
"""
import re
from collections import defaultdict
from datetime import date

from ..db import execute, query_all, query_one

# 34 tỉnh/thành phố sau sắp xếp đơn vị hành chính (2025).
PROVINCES = [
    "Hà Nội", "TP. Hồ Chí Minh", "Hải Phòng", "Đà Nẵng", "Cần Thơ", "Huế",
    "An Giang", "Bắc Ninh", "Cà Mau", "Cao Bằng", "Đắk Lắk", "Điện Biên",
    "Đồng Nai", "Đồng Tháp", "Gia Lai", "Hà Tĩnh", "Hưng Yên", "Khánh Hòa",
    "Lai Châu", "Lâm Đồng", "Lạng Sơn", "Lào Cai", "Nghệ An", "Ninh Bình",
    "Phú Thọ", "Quảng Ngãi", "Quảng Ninh", "Quảng Trị", "Sơn La", "Tây Ninh",
    "Thái Nguyên", "Thanh Hóa", "Tuyên Quang", "Vĩnh Long",
]
GENDERS = ("Nam", "Nữ")

PROFILE_SQL = ("SELECT MaNguoiDung, HoVaTen, Ho, Ten, Email, SoDienThoai, DiaChi, "
               "GioiTinh, NgaySinh, TinhThanh, PhuongXa FROM NguoiDung WHERE MaNguoiDung=?")


class ProfileValidationError(ValueError):
    pass


def split_name(full_name):
    """'Nguyễn Văn An' -> ('Nguyễn Văn', 'An'): tên là từ cuối, họ là phần còn lại."""
    words = (full_name or "").split()
    if not words:
        return "", ""
    if len(words) == 1:
        return "", words[0]
    return " ".join(words[:-1]), words[-1]


def get_profile(user_id):
    row = query_one(PROFILE_SQL, (user_id,))
    if row is None:
        return None
    if not row.get("Ho") and not row.get("Ten"):
        row["Ho"], row["Ten"] = split_name(row.get("HoVaTen"))
    row["NgaySinh"] = str(row["NgaySinh"])[:10] if row.get("NgaySinh") else ""
    for key in ("SoDienThoai", "DiaChi", "GioiTinh", "TinhThanh", "PhuongXa"):
        row[key] = row.get(key) or ""
    return row


def initials(profile):
    letters = [(profile.get("Ho") or "").strip()[:1], (profile.get("Ten") or "").strip()[:1]]
    text = "".join(l for l in letters if l).upper()
    return text or (profile.get("Email") or "?")[:1].upper()


def compose_address(profile):
    """Gộp số nhà/đường + phường/xã + tỉnh/thành thành một chuỗi cho form đặt hàng."""
    parts = [profile.get("DiaChi"), profile.get("PhuongXa"), profile.get("TinhThanh")]
    return ", ".join(p.strip() for p in parts if p and p.strip())[:255]


def has_default_contact(profile):
    return bool(profile.get("SoDienThoai") or profile.get("DiaChi") or profile.get("PhuongXa"))


def checkout_defaults(profile):
    """Giá trị điền sẵn cho /checkout; khách vẫn sửa được toàn bộ."""
    return {"full_name": profile.get("HoVaTen") or "", "phone": profile.get("SoDienThoai") or "",
            "email": profile.get("Email") or "", "address": compose_address(profile)}


def form_values(profile):
    """Dữ liệu hiển thị trong form hồ sơ (từ database)."""
    y, m, d = (profile["NgaySinh"].split("-") + ["", "", ""])[:3] if profile["NgaySinh"] else ("", "", "")
    return {"ho": profile["Ho"], "ten": profile["Ten"], "gender": profile["GioiTinh"],
            "day": d.lstrip("0"), "month": m.lstrip("0"), "year": y,
            "province": profile["TinhThanh"], "ward": profile["PhuongXa"],
            "address": profile["DiaChi"], "phone": profile["SoDienThoai"], "email": profile["Email"]}


def form_values_from_request(form):
    keys = ("ho", "ten", "gender", "day", "month", "year", "province", "ward", "address", "phone", "email")
    return {k: str(form.get(k, "")).strip() for k in keys}


def validate_profile(form):
    v = form_values_from_request(form)
    if not 1 <= len(v["ho"]) <= 60 or not 1 <= len(v["ten"]) <= 60:
        raise ProfileValidationError("Vui lòng nhập Họ và Tên (tối đa 60 ký tự mỗi ô).")
    if len(f"{v['ho']} {v['ten']}") > 100:
        raise ProfileValidationError("Họ và tên quá dài (tối đa 100 ký tự).")
    if v["gender"] and v["gender"] not in GENDERS:
        raise ProfileValidationError("Giới tính không hợp lệ.")
    birth = None
    if v["day"] or v["month"] or v["year"]:
        try:
            birth = date(int(v["year"]), int(v["month"]), int(v["day"]))
        except (TypeError, ValueError):
            raise ProfileValidationError("Ngày sinh không hợp lệ. Hãy chọn đủ ngày, tháng, năm.")
        if birth > date.today() or birth.year < 1900:
            raise ProfileValidationError("Ngày sinh không hợp lệ.")
    if v["province"] and v["province"] not in PROVINCES:
        raise ProfileValidationError("Hãy chọn Tỉnh / Thành phố trong danh sách.")
    if len(v["ward"]) > 100:
        raise ProfileValidationError("Phường / Xã tối đa 100 ký tự.")
    if len(v["address"]) > 150:
        raise ProfileValidationError("Số nhà, tên đường tối đa 150 ký tự.")
    if v["phone"]:
        digits = re.sub(r"\D", "", v["phone"])
        if not 9 <= len(digits) <= 12 or len(v["phone"]) > 20:
            raise ProfileValidationError("Số điện thoại không hợp lệ.")
    v["email"] = v["email"].lower()
    if len(v["email"]) > 150 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", v["email"]):
        raise ProfileValidationError("Email không hợp lệ.")
    v["birth"] = birth.isoformat() if birth else None
    return v


def update_profile(user_id, data):
    if query_one("SELECT MaNguoiDung FROM NguoiDung WHERE Email=? AND MaNguoiDung<>?", (data["email"], user_id)):
        raise ProfileValidationError("Email này đã được tài khoản khác sử dụng.")
    full_name = f"{data['ho']} {data['ten']}"
    execute("""UPDATE NguoiDung SET HoVaTen=?, Ho=?, Ten=?, GioiTinh=?, NgaySinh=?, TinhThanh=?,
               PhuongXa=?, DiaChi=?, SoDienThoai=?, Email=? WHERE MaNguoiDung=?""",
            (full_name, data["ho"], data["ten"], data["gender"] or None, data["birth"],
             data["province"] or None, data["ward"] or None, data["address"] or None,
             data["phone"] or None, data["email"], user_id))
    return full_name


def save_checkout_defaults(user_id, order):
    """Sau khi đặt hàng: lấy thông tin vừa nhập làm mặc định cho các lần mua sau.

    Không đổi email (email là tên đăng nhập). Địa chỉ chỉ ghi khi khác địa chỉ đang lưu.
    """
    profile = get_profile(user_id)
    if profile is None:
        return
    name, address = order["full_name"], profile["DiaChi"]
    province, ward = profile["TinhThanh"], profile["PhuongXa"]
    if order["fulfillment"] == "delivery" and order["address"] and order["address"] != compose_address(profile):
        address, province, ward = order["address"], "", ""
    if name != (profile.get("HoVaTen") or ""):
        ho, ten = split_name(name)
    else:
        ho, ten = profile["Ho"], profile["Ten"]
    execute("""UPDATE NguoiDung SET HoVaTen=?, Ho=?, Ten=?, SoDienThoai=?, DiaChi=?, TinhThanh=?, PhuongXa=?
               WHERE MaNguoiDung=?""",
            (name, ho, ten, order["phone"], address or None, province or None, ward or None, user_id))


def list_orders(user_id, limit=50):
    orders = query_all("SELECT MaDonHang, NgayDat, TrangThai, TongTien FROM DonHang "
                       "WHERE MaNguoiDung=? ORDER BY MaDonHang DESC", (user_id,))[:limit]
    if not orders:
        return []
    ids = [int(o["MaDonHang"]) for o in orders]
    rows = query_all("""SELECT ct.MaDonHang, sp.MaSanPham, sp.TenSanPham, bt.KichThuoc, bt.MauSac,
                        ct.SoLuong, ct.DonGia
                        FROM ChiTietDonHang ct JOIN BienTheSanPham bt ON bt.MaBienThe=ct.MaBienThe
                        JOIN SanPham sp ON sp.MaSanPham=bt.MaSanPham
                        WHERE ct.MaDonHang IN (""" + ",".join("?" for _ in ids) + ") ORDER BY ct.MaChiTietDon",
                     tuple(ids))
    grouped = defaultdict(list)
    for r in rows:
        grouped[int(r["MaDonHang"])].append(r)
    for o in orders:
        o["items"] = grouped.get(int(o["MaDonHang"]), [])
    return orders
