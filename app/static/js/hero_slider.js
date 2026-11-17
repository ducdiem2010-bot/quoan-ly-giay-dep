// Banner quảng cáo tự trượt: tự chạy 5 giây/slide, dừng khi rê chuột/focus, có nút trước-sau, chấm và vuốt trên điện thoại.
(function () {
  const root = document.getElementById('hero-slider');
  if (!root) return;
  const track = root.querySelector('.hero-track');
  const slides = Array.from(root.querySelectorAll('.hero-slide'));
  if (slides.length < 2) return;
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const DELAY = 5000;
  let index = 0, timer = null;

  const mk = (cls, label, html) => { const b = document.createElement('button'); b.type = 'button'; b.className = cls; b.setAttribute('aria-label', label); b.innerHTML = html; return b; };
  const prev = mk('hero-nav hero-prev', 'Slide trước', '&#8249;');
  const next = mk('hero-nav hero-next', 'Slide sau', '&#8250;');
  const dots = document.createElement('div'); dots.className = 'hero-dots';
  const dotBtns = slides.map((_, i) => { const d = mk('hero-dot', 'Đến slide ' + (i + 1), ''); d.addEventListener('click', () => { go(i); restart(); }); dots.appendChild(d); return d; });
  root.append(prev, next, dots);

  function go(i) {
    index = (i + slides.length) % slides.length;
    track.style.transform = 'translateX(' + (-100 * index) + '%)';
    slides.forEach((s, n) => { s.toggleAttribute('inert', n !== index); s.setAttribute('aria-hidden', n === index ? 'false' : 'true'); });
    dotBtns.forEach((d, n) => d.setAttribute('aria-current', n === index ? 'true' : 'false'));
  }
  function stop() { clearInterval(timer); timer = null; }
  function start() { if (!reduce && !timer) timer = setInterval(() => go(index + 1), DELAY); }
  function restart() { stop(); start(); }

  prev.addEventListener('click', () => { go(index - 1); restart(); });
  next.addEventListener('click', () => { go(index + 1); restart(); });
  root.addEventListener('mouseenter', stop);
  root.addEventListener('mouseleave', start);
  root.addEventListener('focusin', stop);
  root.addEventListener('focusout', start);
  document.addEventListener('visibilitychange', () => document.hidden ? stop() : start());

  let x0 = null;
  root.addEventListener('touchstart', e => { x0 = e.touches[0].clientX; stop(); }, { passive: true });
  root.addEventListener('touchend', e => {
    if (x0 !== null) { const dx = e.changedTouches[0].clientX - x0; if (Math.abs(dx) > 45) go(index + (dx < 0 ? 1 : -1)); }
    x0 = null; start();
  });

  go(0); start();
})();
