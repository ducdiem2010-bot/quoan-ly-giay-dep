// Tuấn – W3-037: hỗ trợ form GET; không tự lọc dữ liệu hoặc lưu vào localStorage.
// Field theo kế hoạch: q, brand_id, type_id, gender, color_id, size_id,
// price_min, price_max, sort, page. Backend nhóm giữ selected sau khi gửi.
(() => {
  "use strict";
  const form = document.getElementById("catalog-filter-form");
  if (!form) return;
  const minimum = form.elements.namedItem("price_min");
  const maximum = form.elements.namedItem("price_max");
  const page = form.elements.namedItem("page");
  const keyword = form.elements.namedItem("q");

  function validatePriceRange() {
    if (!minimum || !maximum) return true;
    minimum.setCustomValidity("");
    maximum.setCustomValidity("");
    // Input type=number tự kiểm tra số và min=0; bỏ trống là không giới hạn.
    if (minimum.validity.badInput || maximum.validity.badInput) return false;
    const low = minimum.valueAsNumber;
    const high = maximum.valueAsNumber;
    if (minimum.value && low < 0) minimum.setCustomValidity("Giá từ không được âm.");
    if (maximum.value && high < 0) maximum.setCustomValidity("Giá đến không được âm.");
    if (minimum.value && maximum.value && Number.isFinite(low) &&
        Number.isFinite(high) && low > high) {
      maximum.setCustomValidity("Giá đến phải lớn hơn hoặc bằng Giá từ.");
    }
    return minimum.validity.valid && maximum.validity.valid;
  }
  [minimum, maximum].forEach((input) => {
    if (input) input.addEventListener("input", validatePriceRange);
  });
  form.addEventListener("submit", (event) => {
    if (page) page.value = "1";
    if (keyword) keyword.value = keyword.value.trim();
    if (!validatePriceRange() || !form.checkValidity()) {
      event.preventDefault();
      form.reportValidity();
    }
  });
  const clearSearch = form.querySelector("[data-clear-search]");
  if (clearSearch && keyword) {
    const updateClearButton = () => { clearSearch.hidden = !keyword.value; };
    keyword.addEventListener("input", updateClearButton);
    clearSearch.addEventListener("click", () => {
      // URL hiện tại là nguồn trạng thái; chỉ bỏ q và đặt lại trang 1.
      const target = new URL(form.action, window.location.href);
      const params = new URLSearchParams(window.location.search);
      params.delete("q");
      params.set("page", "1");
      target.search = params.toString();
      window.location.assign(target.href);
    });
    updateClearButton();
  }
  // Bỏ riêng từng điều kiện; các lựa chọn còn lại đi cùng GET tới server.
  const labelKeys = {
    "Từ khóa": "q", "Thương hiệu": "brand_id", "Loại sản phẩm": "type_id",
    "Giới tính": "gender", "Màu": "color_id", "Size": "size_id",
    "Giá từ": "price_min", "Giá đến": "price_max", "Sắp xếp": "sort"
  };
  document.querySelectorAll(".filter-selection-list li").forEach((chip) => {
    const label = chip.querySelector("span");
    const key = labelKeys[label ? label.textContent.replace(/:$/, "").trim() : ""];
    if (!key) return;
    const remove = document.createElement("a");
    const target = new URL(form.action, window.location.href);
    const params = new URLSearchParams(window.location.search);
    params.delete(key);
    params.set("page", "1");
    target.search = params.toString();
    remove.href = target.href;
    remove.className = "filter-remove-one";
    remove.textContent = " ×";
    remove.setAttribute("aria-label", "Bỏ " + label.textContent.replace(/:$/, "").trim());
    chip.appendChild(remove);
  });
  validatePriceRange();
})();
