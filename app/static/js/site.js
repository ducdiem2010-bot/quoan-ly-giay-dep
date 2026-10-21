// JavaScript Tuần 2: chưa cần AJAX; các form/giỏ hàng gửi về route Flask.
// Cố ý KHÔNG dùng cùng lúc shop.js localStorage cũ vì gây hai nguồn giỏ hàng khác nhau.
document.querySelectorAll('form').forEach(form => {
  form.addEventListener('submit', () => {
    const btn = form.querySelector('button[type="submit"]');
    if (btn && !btn.disabled) btn.setAttribute('aria-busy', 'true');
  });
});
