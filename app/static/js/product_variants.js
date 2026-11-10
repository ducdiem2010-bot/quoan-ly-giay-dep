// Tuấn – W3-066. Nguồn dữ liệu: options do Jinja render từ BienTheSanPham.
// Chỉ chọn một MaBienThe có thật; không sửa giá, không cập nhật/trừ tồn.
(() => {
  "use strict";
  const original = document.getElementById("variant_id");
  const color = document.getElementById("variant-color");
  const size = document.getElementById("variant-size");
  const stockLabel = document.getElementById("variant-stock");
  const quantity = document.getElementById("quantity");
  const enhanced = document.querySelector("[data-variant-enhanced]");
  const fallback = document.querySelector("[data-variant-fallback]");
  const form = original ? original.closest("form") : null;
  const submitButtons = form ? Array.from(form.querySelectorAll('button[type="submit"]')) : [];
  const submit = submitButtons.length ? {
    set disabled(value) { submitButtons.forEach(button => { button.disabled = value; }); }
  } : null;
  if (!original || !color || !size || !stockLabel || !quantity || !enhanced || !fallback || !form || !submit) return;

  const sourceOptions = Array.from(original.options).filter(option => option.value);
  const hasDataset = sourceOptions.some(option => option.dataset.stock !== undefined);
  const variants = Array.from(original.options).filter(option => option.value).map(option => ({
    id: option.value, color: option.dataset.color, size: option.dataset.size,
    stock: Number(option.dataset.stock), stockText: option.dataset.stock
  })).filter(v => /^\d+$/.test(v.id) && Number(v.id) > 0 && v.color && v.size &&
    /^\d+$/.test(v.stockText || "") && Number.isSafeInteger(v.stock) && v.stock >= 0);
  // Nếu chưa có dataset đúng contract, giữ nguyên select cặp size/màu của nhóm.
  if (!variants.length) {
    // Template cũ thiếu dataset: giữ native select. Dataset đã có nhưng sai: chặn chọn.
    if (hasDataset) {
      enhanced.hidden = false;
      fallback.hidden = true;
      original.required = false;
      original.value = "";
      quantity.disabled = true;
      submit.disabled = true;
      stockLabel.dataset.state = "error";
      stockLabel.textContent = "Chưa tải được thông tin màu và size. Vui lòng tải lại trang.";
    }
    return;
  }

  function option(value, text) {
    const node = document.createElement("option");
    node.value = value;
    node.textContent = text;
    return node;
  }
  color.replaceChildren(option("", "-- Chọn màu --"));
  [...new Set(variants.map(v => v.color))].forEach(name => color.appendChild(option(name, name)));
  enhanced.hidden = false;
  fallback.hidden = true;
  // Select gốc vẫn là field gửi variant_id, tránh lỗi focus trên input ẩn.
  original.required = false;

  function selection() {
    const matches = variants.filter(v => v.color === color.value && v.size === size.value);
    return matches.length === 1 ? matches[0] : null;
  }
  function refreshStock() {
    const selected = selection();
    quantity.setCustomValidity("");
    original.value = selected ? selected.id : "";
    const available = selected !== null && selected.stock > 0;
    submit.disabled = !available;
    quantity.disabled = !available;
    quantity.max = selected ? String(Math.min(selected.stock, 99)) : "99";
    stockLabel.dataset.state = selected ? (available ? "ready" : "empty") : "error";
    if (!color.value) stockLabel.textContent = "Vui lòng chọn màu và size.";
    else if (!size.value) stockLabel.textContent = "Vui lòng chọn size phù hợp với màu đã chọn.";
    else if (!selected) stockLabel.textContent = "Không có tổ hợp màu và size này.";
    else stockLabel.textContent = available ? "Còn " + selected.stock + " sản phẩm cho màu và size đã chọn." : "Hết hàng ở màu và size đã chọn.";
    if (available) {
      const number = Number(quantity.value);
      if (!quantity.value) quantity.setCustomValidity("Vui lòng nhập số lượng.");
      else if (!Number.isSafeInteger(number) || number < 1) quantity.setCustomValidity("Số lượng phải là số nguyên từ 1 trở lên.");
      else if (number > Math.min(selected.stock, 99)) quantity.setCustomValidity("Số lượng tối đa cho lần chọn này là " + Math.min(selected.stock, 99) + ".");
    }
  }
  function refreshSizes() {
    const previous = size.value;
    size.replaceChildren(option("", "-- Chọn size --"));
    const pairs = variants.filter(v => v.color === color.value);
    [...new Set(pairs.map(v => v.size))].forEach(name => {
      const choices = pairs.filter(v => v.size === name);
      const allEmpty = choices.every(v => v.stock === 0);
      size.appendChild(option(name, name + (allEmpty ? " (Hết hàng)" : "")));
    });
    size.disabled = !pairs.length;
    size.value = pairs.some(v => v.size === previous) ? previous : "";
    refreshStock();
  }
  color.addEventListener("change", refreshSizes);
  size.addEventListener("change", refreshStock);
  quantity.addEventListener("input", refreshStock);
  form.addEventListener("submit", (event) => {
    refreshStock();
    const selected = selection();
    if (!selected || selected.stock === 0 || !form.checkValidity()) {
      event.preventDefault();
      form.reportValidity();
    }
  });
  window.addEventListener("pageshow", (event) => {
    if (event.persisted) window.location.reload();
    else refreshStock();
  });
  refreshSizes();
})();
