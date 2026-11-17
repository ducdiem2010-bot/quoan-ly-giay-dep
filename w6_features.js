async function applyW6Voucher(subtotal) {
  const input = document.getElementById("w6-voucher-code");
  const csrfInput = document.querySelector('input[name="csrf_token"]');
  const msgEl = document.getElementById("w6-voucher-msg");
  const discountEl = document.getElementById("w6-discount-display");
  const finalEl = document.getElementById("w6-final-total-display");
  if (!input) return;

  const formData = new URLSearchParams();
  formData.append("code", input.value.trim());
  formData.append("subtotal", String(Number(subtotal) || 0));
  if (csrfInput) {
    formData.append("csrf_token", csrfInput.value);
  }

  try {
    const res = await fetch("/api/w6/voucher/apply", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData.toString(),
    });
    const data = await res.json();
    if (msgEl) {
      msgEl.textContent = data.message || "";
      msgEl.style.color = data.ok ? "#16a34a" : "#dc2626";
    }
    if (discountEl) {
      discountEl.textContent = "-" + Number(data.discount || 0).toLocaleString("vi-VN") + " ₫";
    }
    if (finalEl && data.final_total !== undefined) {
      finalEl.textContent = Number(data.final_total).toLocaleString("vi-VN") + " ₫";
    }
  } catch (err) {
    if (msgEl) {
      msgEl.textContent = "Lỗi kết nối khi kiểm tra mã giảm giá.";
      msgEl.style.color = "#dc2626";
    }
  }
}