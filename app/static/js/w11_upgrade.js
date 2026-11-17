/* W11: chỉ đọc thông tin sản phẩm; không ghi giỏ hàng hoặc thay đổi dữ liệu. */
(() => {
  'use strict';
  const modal = document.getElementById('w11-quick-view');
  let opener = null;
  let requestId = 0;
  const text = (id, value) => {
    const node = document.getElementById(id);
    if (node) node.textContent = value == null ? '' : String(value);
  };
  function closeModal() {
    if (!modal || modal.hidden) return;
    modal.hidden = true;
    document.body.classList.remove('w11-modal-open');
    requestId += 1; // Không ghi dữ liệu từ response đã lỗi thời.
    if (opener && opener.isConnected) opener.focus();
  }
  function openModal(button) {
    if (!modal) return;
    opener = button;
    const image = button.closest('.product-card')?.querySelector('.product-visual img');
    const modalImage = document.getElementById('w11-modal-image');
    // Ảnh lấy từ thẻ sản phẩm hiện tại (đã có fallback hợp lệ của W10).
    modalImage.src = image?.currentSrc || image?.src || '/static/images/no-product-image.svg';
    modalImage.alt = image?.alt || 'Ảnh giày dép';
    modal.hidden = false;
    document.body.classList.add('w11-modal-open');
    text('w11-modal-title', 'Đang tải sản phẩm...');
    for (const id of ['w11-modal-category', 'w11-modal-price', 'w11-modal-stock',
                      'w11-modal-colors', 'w11-modal-sizes', 'w11-modal-description']) text(id, '');
    const detail = document.getElementById('w11-modal-detail');
    detail.hidden = true;
    modal.querySelector('.w11-modal-close').focus();
    const request = ++requestId;
    fetch(button.dataset.w11Url, {headers: {'Accept': 'application/json'}})
      .then(res => {
        if (!res.ok) throw new Error('Không tải được sản phẩm');
        return res.json();
      })
      .then(p => {
        if (request !== requestId || modal.hidden) return;
        if (p.image_url) {
          modalImage.src = p.image_url;
        }
        text('w11-modal-title', p.name);
        text('w11-modal-category', [p.brand, p.category].filter(Boolean).join(' · '));
        text('w11-modal-price', p.price_text);
        text('w11-modal-stock', p.stock > 0 ? `Còn ${p.stock} sản phẩm (tổng mọi biến thể)` : 'Đã hết hàng');
        text('w11-modal-colors', p.colors.length ? p.colors.join(' · ') : 'Chưa có màu còn hàng');
        text('w11-modal-sizes', p.sizes.length ? p.sizes.join(' · ') : 'Chưa có size còn hàng');
        text('w11-modal-description', p.description);
        detail.href = p.detail_url;
        detail.hidden = false;
      })
      .catch(() => {
        if (request !== requestId || modal.hidden) return;
        text('w11-modal-title', 'Không thể tải thông tin sản phẩm');
        text('w11-modal-description', 'Sản phẩm có thể đã bị ẩn hoặc kết nối bị gián đoạn. Vui lòng thử lại.');
      });
  }
  document.addEventListener('click', event => {
    const trigger = event.target.closest('[data-w11-quick]');
    if (trigger) { event.preventDefault(); openModal(trigger); return; }
    if (event.target.closest('[data-w11-close]')) { closeModal(); }
  });
  document.addEventListener('keydown', event => {
    if (!modal || modal.hidden) return;
    if (event.key === 'Escape') { event.preventDefault(); closeModal(); return; }
    if (event.key !== 'Tab') return;
    const focusable = [...modal.querySelectorAll('button:not([disabled]):not([hidden]), a[href]:not([hidden])')]
      .filter(el => el.getClientRects().length && !el.closest('[hidden]'));
    if (!focusable.length) return;
    if (event.shiftKey && document.activeElement === focusable[0]) {
      event.preventDefault(); focusable[focusable.length - 1].focus();
    } else if (!event.shiftKey && document.activeElement === focusable[focusable.length - 1]) {
      event.preventDefault(); focusable[0].focus();
    }
  });

  const topButton = document.getElementById('w11-back-to-top');
  if (topButton) topButton.addEventListener('click', () => {
    window.scrollTo({top: 0, behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'});
  });

  const form = document.querySelector('[data-w11-finder]');
  if (form) {
    const steps = [...form.querySelectorAll('[data-w11-step]')];
    const indicators = [...document.querySelectorAll('.w11-steps > span')];
    let step = 0;
    function setStep(next) {
      step = Math.min(steps.length - 1, Math.max(0, next));
      steps.forEach((el, index) => {el.hidden = index !== step;});
      indicators.forEach((el, index) => el.classList.toggle('active', index <= step));
      steps[step]?.querySelector('select')?.focus();
    }
    form.addEventListener('click', event => {
      if (event.target.closest('[data-w11-next]')) setStep(step + 1);
      if (event.target.closest('[data-w11-prev]')) setStep(step - 1);
    });
  }
})();
