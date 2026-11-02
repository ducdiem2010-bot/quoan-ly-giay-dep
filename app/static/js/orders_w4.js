/* W4-009: chỉ điều khiển dialog/gửi form; không tự đổi trạng thái đơn. */
(() => {
  "use strict";
  const dialog = document.getElementById("cancel-dialog");
  const opener = document.querySelector("[data-open-cancel]");
  if (!dialog || !opener) return;
  opener.addEventListener("click", () => dialog.showModal());
  dialog.querySelectorAll("[data-close-cancel]").forEach(button =>
    button.addEventListener("click", () => { dialog.close(); opener.focus(); }));
  const form = dialog.querySelector("[data-cancel-form]");
  if (!form) return;
  const submit = form.querySelector('button[type="submit"]');
  const status = form.querySelector("[data-cancel-status]");
  form.addEventListener("submit", event => {
    if (form.dataset.pending === "true") { event.preventDefault(); return; }
    form.dataset.pending = "true";
    submit.disabled = true;
    submit.setAttribute("aria-busy", "true");
    status.textContent = "Đang gửi yêu cầu hủy. Chờ kết quả từ hệ thống…";
  });
  window.addEventListener("pageshow", event => {
    if (event.persisted) { window.location.reload(); return; }
    form.dataset.pending = "false"; submit.disabled = false;
    submit.removeAttribute("aria-busy"); status.textContent = "";
  });
})();
