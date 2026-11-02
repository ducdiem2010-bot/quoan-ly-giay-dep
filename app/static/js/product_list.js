// Tuấn – W3-052: ảnh lỗi dùng ảnh minh họa sẵn có của nhóm.
// Danh sách và phân trang vẫn do Flask/Jinja2 cung cấp.
(() => {
  "use strict";
  const images = document.querySelectorAll("[data-product-image]");
  images.forEach((img) => {
    const showFallback = () => {
      if (img.dataset.fallbackApplied === "true") return;
      img.dataset.fallbackApplied = "true";
      const fallback = img.dataset.fallbackSrc;
      if (fallback) { img.src = fallback; img.alt = "Ảnh minh họa sản phẩm"; }
    };
    img.addEventListener("error", showFallback);
    if (img.complete && img.naturalWidth === 0) showFallback();
  });
})();
