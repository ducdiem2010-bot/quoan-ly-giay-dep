// JavaScript Tuần 2: chưa cần AJAX; các form/giỏ hàng gửi về route Flask.
// Cố ý KHÔNG dùng cùng lúc shop.js localStorage cũ vì gây hai nguồn giỏ hàng khác nhau.
document.querySelectorAll('form').forEach(form => {
  form.addEventListener('submit', () => {
    const btn = form.querySelector('button[type="submit"]');
    if (btn && !btn.disabled) btn.setAttribute('aria-busy', 'true');
  });
});

// Menu tài khoản: đóng khi bấm ra ngoài hoặc nhấn Esc; tự focus ô email khi mở.
(function () {
  const menu = document.getElementById('account-menu');
  if (!menu) return;
  menu.addEventListener('toggle', () => {
    if (menu.open) { const f = menu.querySelector('#hd-email'); if (f) f.focus(); }
  });
  document.addEventListener('click', e => { if (menu.open && !menu.contains(e.target)) menu.open = false; });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && menu.open) { menu.open = false; menu.querySelector('summary').focus(); } });
})();
