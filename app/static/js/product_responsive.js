// Tuấn – W3-066: thu/mở bộ lọc bằng touch hoặc bàn phím trên mobile.
(() => {
  "use strict";
  const toggle = document.querySelector("[data-filter-toggle]");
  const form = document.getElementById("catalog-filter-form");
  if (!toggle || !form) return;
  const mobile = window.matchMedia("(max-width: 600px)");
  function expand(show) {
    form.hidden = !show;
    toggle.setAttribute("aria-expanded", String(show));
    toggle.textContent = show ? "Thu gọn bộ lọc" : "Mở bộ lọc";
  }
  function adapt() { toggle.hidden = !mobile.matches; expand(true); }
  toggle.addEventListener("click", () => expand(form.hidden));
  form.addEventListener("invalid", () => expand(true), true);
  mobile.addEventListener("change", adapt);
  window.addEventListener("pageshow", adapt);
  adapt();
})();
