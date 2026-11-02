// Tuấn – W3-066: native POST + CSRF và flash của backend nhóm.
// Không tự đảo saved trước khi server trả về; không đoán JSON/endpoint của Khải.
(() => {
  "use strict";
  const records = [];
  document.querySelectorAll("[data-favorite-form]").forEach((form) => {
    const button = form.querySelector('button[type="submit"]');
    const label = form.querySelector("[data-favorite-label]");
    const status = form.querySelector("[data-favorite-status]");
    if (!button || !label || button.disabled) return;
    const originalText = label.textContent;
    records.push({form, button, label, status, originalText});
    form.addEventListener("submit", (event) => {
      if (form.dataset.pending === "true") { event.preventDefault(); return; }
      const target = new URL(form.action, window.location.href);
      if (target.origin !== window.location.origin) {
        event.preventDefault();
        if (status) status.textContent = "Chưa thể xử lý yêu thích. Vui lòng tải lại trang.";
        return;
      }
      const token = form.querySelector('input[name="csrf_token"]');
      if (!token || !token.value) {
        event.preventDefault();
        if (status) status.textContent = "Phiên biểu mẫu đã hết hạn. Vui lòng tải lại trang.";
        return;
      }
      form.dataset.pending = "true";
      button.disabled = true;
      button.setAttribute("aria-busy", "true");
      label.textContent = "Đang xử lý…";
      if (status) status.textContent = "Đang gửi yêu cầu.";
    });
  });
  window.addEventListener("pageshow", (event) => {
    // Quay lại từ bfcache phải đọc trạng thái saved mới từ server.
    if (event.persisted) { window.location.reload(); return; }
    records.forEach(({form, button, label, status, originalText}) => {
      form.dataset.pending = "false";
      button.disabled = false;
      button.removeAttribute("aria-busy");
      label.textContent = originalText;
      if (status) status.textContent = "";
    });
  });
})();
