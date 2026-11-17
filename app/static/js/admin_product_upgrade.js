/* Khải K1-K2: kiểm tra trên client, không bỏ qua CSRF/kiểm tra server. */
(() => {
  'use strict';
  document.querySelectorAll('[data-admin-visibility]').forEach(form => {
    form.addEventListener('submit', event => {
      const verb = form.dataset.actionLabel || 'thay đổi hiển thị';
      const name = form.dataset.productName || 'sản phẩm';
      if (!window.confirm(`Xác nhận ${verb} sản phẩm "${name}"?`)) event.preventDefault();
    });
  });
  document.querySelectorAll('[data-admin-variant-form]').forEach(form => {
    const stock = form.elements.namedItem('stock');
    const color = form.elements.namedItem('color');
    const size = form.elements.namedItem('size');
    const message = document.createElement('p');
    message.className = 'admin-ux-form-message';
    message.setAttribute('role', 'alert');
    message.hidden = true;
    form.appendChild(message);

    function validate() {
      const raw = stock ? stock.value.trim() : '';
      let error = '';
      if (!/^\d+$/.test(raw) || !Number.isSafeInteger(Number(raw))) {
        error = 'Tồn kho phải là số nguyên không âm (ví dụ 0, 1, 2).';
      } else if (!size?.value.trim() || !color?.value.trim()) {
        error = 'Vui lòng nhập đủ size và màu sắc.';
      } else if (!form.dataset.variantId) {
        // Chỉ cảnh báo trùng khi đang thêm, server/DB vẫn kiểm tra bắt buộc.
        const conflict = [...document.querySelectorAll('[data-admin-variant-row]')].some(row =>
          row.dataset.variantSize?.trim().toLowerCase() === size.value.trim().toLowerCase() &&
          row.dataset.variantColor?.trim().toLowerCase() === color.value.trim().toLowerCase()
        );
        if (conflict) error = 'Biến thể màu/size này đã tồn tại.';
      }
      if (stock) stock.setCustomValidity(error);
      message.textContent = error;
      message.hidden = !error;
      return !error;
    }
    form.addEventListener('submit', event => {
      if (!validate()) { event.preventDefault(); stock?.reportValidity(); }
    });
    for (const field of [stock, size, color]) {
      field?.addEventListener('input', () => {
        if (stock) stock.setCustomValidity('');
        message.hidden = true;
      });
    }
  });
})();
