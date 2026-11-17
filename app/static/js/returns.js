(() => {
  const dialog = document.getElementById('return-dialog');
  if (!dialog) return;
  const form = document.getElementById('return-form');
  const fields = [...form.querySelectorAll('.return-qty')];
  const fmt = value => new Intl.NumberFormat('vi-VN',{style:'currency',currency:'VND'}).format(value);
  const update = () => {
    let total = 0;
    fields.forEach(input => {
      const amount = Math.max(0, Number(input.value) || 0) * Math.round(Number(input.dataset.price)*100);
      input.closest('tr').querySelector('.return-line-total').textContent = fmt(amount/100);
      total += amount;
    });
    document.getElementById('return-total').textContent = fmt(total/100);
  };
  document.getElementById('open-return')?.addEventListener('click', () => dialog.showModal());
  document.getElementById('close-return').addEventListener('click', () => dialog.close());
  fields.forEach(input => input.addEventListener('input', update));
  form.addEventListener('submit', event => {
    if (!fields.some(input => Number(input.value)>0)) {
      event.preventDefault(); alert('Chọn ít nhất một đôi để trả.'); return;
    }
    if (!confirm('Xác nhận đã nhận lại hàng thực tế? Hệ thống sẽ cộng kho và ghi khoản phải hoàn.')) {
      event.preventDefault(); return;
    }
    document.getElementById('submit-return').disabled = true;
  });
  window.addEventListener('pageshow', () => { document.getElementById('submit-return').disabled=false; });
  update();
  if (dialog.dataset.reopen === '1') dialog.showModal();
})();
