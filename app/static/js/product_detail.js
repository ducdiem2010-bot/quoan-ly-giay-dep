// Tuấn – W3-025: gallery ảnh; không thay đổi giá hay tồn kho trong JS.
(() => {
  "use strict";
  const mainImage = document.getElementById("product-main-image");
  if (!mainImage) return;
  const thumbnails = document.querySelectorAll("[data-gallery-src]");
  function useFallback(img) {
    const fallback = img.dataset.fallbackSrc;
    if (!fallback || img.dataset.fallbackApplied === "true") return;
    img.dataset.fallbackApplied = "true";
    img.src = fallback;
    if (img === mainImage) img.alt = "Ảnh minh họa sản phẩm";
  }
  document.querySelectorAll(".detail-gallery img[data-fallback-src]").forEach((img) => {
    img.addEventListener("error", () => useFallback(img));
    if (img.complete && img.naturalWidth === 0) useFallback(img);
  });
  thumbnails.forEach((button) => {
    button.addEventListener("click", () => {
      mainImage.dataset.fallbackApplied = "false";
      mainImage.src = button.dataset.gallerySrc;
      mainImage.alt = button.dataset.galleryAlt || "Ảnh sản phẩm";
      thumbnails.forEach((item) => item.setAttribute("aria-pressed", String(item === button)));
    });
  });
})();
