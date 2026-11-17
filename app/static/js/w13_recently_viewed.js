/* W13 Tuấn — history only numeric product IDs (no personal data), max 8. */
(() => {
  'use strict';
  const KEY = 'shoes_store_w13_recent_ids';
  const MAX = 8;
  const numericId = n => Number.isSafeInteger(n) && n > 0;
  function read() {
    try {
      const raw = JSON.parse(localStorage.getItem(KEY) || '[]');
      return Array.isArray(raw) ? [...new Set(raw.map(Number).filter(numericId))].slice(0, MAX) : [];
    } catch (_) { return []; }
  }
  function save(ids) {
    try { localStorage.setItem(KEY, JSON.stringify([...new Set(ids)].slice(0, MAX))); }
    catch (_) { /* Storage disabled: leave site usable */ }
  }
  const viewed = document.querySelector('[data-w13-view-product]');
  if (viewed) {
    const id = Number(viewed.getAttribute('data-w13-view-product'));
    if (numericId(id)) save([id, ...read().filter(i => i !== id)]);
  }
  const root = document.querySelector('[data-w13-recent]');
  if (!root) return;
  const list = root.querySelector('[data-w13-list]');
  const message = root.querySelector('[data-w13-message]');
  const clear = root.querySelector('[data-w13-clear]');
  function say(text) { message.textContent = text; }
  function card(p) {
    // Never render API strings through innerHTML: DOM text and validated local route only.
    const a = document.createElement('a');
    a.className = 'w13-recent-item';
    a.href = p.url;
    const img = document.createElement('img');
    img.src = p.image;
    img.alt = p.name;
    img.loading = 'lazy';
    img.width = 240;
    img.height = 220;
    img.onerror = () => { img.onerror = null; img.src = '/static/images/no-product-image.svg'; };
    const title = document.createElement('strong');
    title.textContent = p.name;
    const price = document.createElement('span');
    price.textContent = new Intl.NumberFormat('vi-VN', {maximumFractionDigits: 0}).format(p.price) + ' đ';
    a.append(img, title, price);
    return a;
  }
  async function show() {
    list.replaceChildren();
    const ids = read();
    if (!ids.length) { say('Chưa có sản phẩm vừa xem trên thiết bị này.'); return; }
    say('Đang tải sản phẩm hợp lệ...');
    try {
      const url = new URL(root.dataset.api, window.location.origin);
      url.searchParams.set('ids', ids.join(','));
      const res = await fetch(url, {credentials: 'same-origin', headers: {'Accept':'application/json'}});
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      const products = Array.isArray(data.products) ? data.products : [];
      save(products.map(p => p.id)); // Drop hidden/deleted products, preserve server order.
      products.forEach(p => list.appendChild(card(p)));
      say(products.length ? '' : 'Các sản phẩm đã xem hiện không còn được bán.');
    } catch (_) { say('Chưa thể tải sản phẩm vừa xem, hãy thử lại.'); }
  }
  if (clear) clear.addEventListener('click', () => { save([]); list.replaceChildren(); say('Đã xóa lịch sử trên thiết bị này.'); });
  show();
})();
