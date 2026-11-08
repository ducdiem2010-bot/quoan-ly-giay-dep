<<<<<<< HEAD
/* W4-004/014: UX và kiểm tra client. Backend vẫn xác thực và xử lý đơn. */
(() => {
  "use strict";
  const form = document.getElementById("checkout-form");
  if (!form) return;
  const summary = document.getElementById("checkout-errors");
  const delivery = document.getElementById("delivery-fields");
  const address = form.elements.address;
  const submit = form.querySelector('button[type="submit"]');
  const status = document.getElementById("checkout-submit-status");
  const ids = ["full_name", "phone", "email", "address", "note"];
  let submitted = false;
  form.noValidate = true; // Native required/minlength vẫn hoạt động khi JS không chạy.
  const textLength = value => Array.from(value).length;
  function errorFor(id, message) {
    const field = form.elements[id];
    const label = document.getElementById(id + "-error");
    if (field && typeof field.setCustomValidity === "function") {
      field.setCustomValidity(message);
      field.setAttribute("aria-invalid", String(Boolean(message)));
    }
    if (label) { label.textContent = message; label.hidden = !message; }
  }
  function validate(id) {
    const value = form.elements[id].value.trim();
    let message = "";
    if (id === "full_name" && (textLength(value) < 2 || textLength(value) > 100))
      message = "Họ tên phải từ 2 đến 100 ký tự, không chỉ có khoảng trắng.";
    if (id === "phone") {
      const digits = value.replace(/\D/g, "");
      if (!/^[+()\d\s.\-]+$/.test(value) || digits.length < 9 || digits.length > 12 || value.length > 20)
        message = "Nhập số điện thoại hợp lệ gồm 9–12 chữ số.";
    }
    if (id === "email" && value && (textLength(value) > 150 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)))
      message = "Nhập email đúng định dạng, ví dụ ban@example.com.";
    if (id === "address" && address.required && (textLength(value) < 8 || textLength(value) > 255))
      message = "Địa chỉ giao hàng phải từ 8 đến 255 ký tự.";
    if (id === "note" && textLength(value) > 500) message = "Ghi chú tối đa 500 ký tự.";
    errorFor(id, message);
    return message;
  }
  function choices() {
    const fulfillment = form.querySelector('input[name="fulfillment"]:checked');
    const payment = form.querySelector('input[name="payment_method"]:checked');
    const badFulfillment = !fulfillment || !["delivery", "pickup"].includes(fulfillment.value);
    const badPayment = !payment || !["cod", "bank_transfer"].includes(payment.value);
    errorFor("fulfillment", badFulfillment ? "Hãy chọn hình thức nhận hàng." : "");
    errorFor("payment_method", badPayment ? "Hãy chọn phương thức thanh toán đang được hỗ trợ." : "");
    return Number(badFulfillment) + Number(badPayment);
  }
  function refresh() {
    const isDelivery = form.querySelector('input[name="fulfillment"]:checked')?.value !== "pickup";
    const payment = form.querySelector('input[name="payment_method"]:checked')?.value;
    delivery.hidden = !isDelivery;
    address.required = isDelivery;
    address.disabled = !isDelivery; // Không để minlength của địa chỉ cũ chặn nhận tại cửa hàng.
    document.getElementById("shipping-summary").textContent = isDelivery ? "Chờ xác nhận" : "0 ₫";
    document.getElementById("shipping-help").textContent = isDelivery
      ? "Tổng tạm tính chưa bao gồm phí vận chuyển nếu chọn giao hàng."
      : "Nhận tại cửa hàng: không tính phí vận chuyển.";
    document.getElementById("payment-explain").textContent = payment === "bank_transfer"
      ? "Chỉ tạo đơn chờ xác nhận chuyển khoản. Chưa có thông tin nhận tiền và không ghi nhận đã thanh toán."
      : (isDelivery ? "Bạn thanh toán khi nhận hàng; cửa hàng sẽ xác nhận phí giao."
                    : "Bạn thanh toán khi đến nhận hàng tại cửa hàng.");
    if (!isDelivery) errorFor("address", "");
    else if (submitted || address.dataset.touched) validate("address");
    if (submitted) choices();
  }
  ids.forEach(id => {
    const field = form.elements[id];
    field.addEventListener("blur", () => { field.dataset.touched = "true"; validate(id); });
    field.addEventListener("input", () => {
      if (submitted || field.dataset.touched) validate(id);
      summary.hidden = true;
    });
  });
  form.querySelectorAll('input[name="fulfillment"], input[name="payment_method"]').forEach(input =>
    input.addEventListener("change", refresh));
  form.addEventListener("submit", event => {
    if (form.dataset.pending === "true") { event.preventDefault(); return; }
    submitted = true;
    const count = ids.filter(id => validate(id)).length + choices();
    if (count || !form.checkValidity()) {
      event.preventDefault();
      summary.textContent = "Chưa thể gửi yêu cầu. Hãy kiểm tra các trường được đánh dấu bên dưới.";
      summary.hidden = false;
      const invalid = form.querySelector('[aria-invalid="true"]') || form.querySelector(":invalid");
      if (invalid) invalid.focus(); else summary.focus();
      return;
    }
    form.dataset.pending = "true";
    submit.disabled = true; submit.setAttribute("aria-busy", "true");
    submit.textContent = "Đang gửi yêu cầu…";
    status.textContent = "Vui lòng chờ kết quả từ hệ thống. Chưa xác nhận đã thanh toán.";
  });
  window.addEventListener("pageshow", event => {
    if (event.persisted) { window.location.reload(); return; }
    form.dataset.pending = "false"; submit.disabled = false;
    submit.removeAttribute("aria-busy");
    submit.textContent = submit.dataset.idleLabel;
    status.textContent = "";
  });
=======
(() => {
  const delivery = document.getElementById('delivery-fields');
  const address = document.getElementById('address');
  const ship = document.getElementById('shipping-summary');
  const explain = document.getElementById('payment-explain');
  if (!delivery || !address || !ship || !explain) return;
  function refresh() {
    const fulfillment = document.querySelector('input[name="fulfillment"]:checked')?.value || 'delivery';
    const payment = document.querySelector('input[name="payment_method"]:checked')?.value || 'cod';
    const isDelivery = fulfillment === 'delivery';
    delivery.hidden = !isDelivery;
    address.required = isDelivery;
    ship.textContent = isDelivery ? 'Chờ xác nhận' : '0 ₫';
    explain.textContent = payment === 'bank_transfer'
      ? 'Chỉ tạo đơn chờ xác nhận chuyển khoản. Chưa có thông tin nhận tiền và không ghi nhận đã thanh toán.'
      : (isDelivery ? 'Bạn thanh toán khi nhận hàng; cửa hàng sẽ xác nhận phí giao.' : 'Bạn thanh toán khi đến nhận hàng tại cửa hàng.');
  }
  document.querySelectorAll('input[name="fulfillment"], input[name="payment_method"]').forEach(el => el.addEventListener('change', refresh));
>>>>>>> ba1d4e0 (Upload project)
  refresh();
})();
