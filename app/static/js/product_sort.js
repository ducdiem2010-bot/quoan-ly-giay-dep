// Tuấn – W3-038: GET tới backend; không sắp xếp giả bằng JS.
(() => {
  "use strict";
  const allowed = new Set(["", "price_asc", "price_desc", "name_asc", "brand_asc"]);
  const form = document.getElementById("catalog-filter-form");
  const sort = document.getElementById("filter-sort");
  if (form && sort) {
    if (!allowed.has(sort.value)) sort.value = "";
    sort.addEventListener("change", () => {
      if (!allowed.has(sort.value)) sort.value = "";
      const page = form.elements.namedItem("page");
      if (page) page.value = "1";
      form.requestSubmit();
    });
  }
  const keys = ["q", "brand_id", "type_id", "gender", "color_id", "size_id", "price_min", "price_max", "sort"];
  document.querySelectorAll(".catalog-pagination a.page-link").forEach((link) => {
    const target = new URL(link.href, window.location.href);
    if (target.origin !== window.location.origin) return;
    const current = new URLSearchParams(window.location.search);
    // Giữ giá trị đã chuẩn hóa bởi backend nếu link đã có; bổ sung tham số bị thiếu.
    keys.forEach((key) => {
      if (!target.searchParams.has(key) && current.has(key)) target.searchParams.set(key, current.get(key));
    });
    if (!allowed.has(target.searchParams.get("sort") || "")) target.searchParams.delete("sort");
    link.href = target.href;
  });
})();
