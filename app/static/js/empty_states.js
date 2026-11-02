// Tuấn – W3-052: nếu cả ảnh thật và ảnh thay thế đều lỗi, hiện lời nhắc.
(() => {
  "use strict";
  document.querySelectorAll("img[data-fallback-src]").forEach((img) => {
    let message = null;
    function inspectImage() {
      if (!img.complete || img.naturalWidth > 0) {
        if (img.naturalWidth > 0) { img.hidden = false; if (message) message.hidden = true; }
        return;
      }
      if (img.dataset.fallbackApplied !== "true") return;
      // Khi sự kiện ảnh gốc kích hoạt, JS khác vừa đổi src sang fallback.
      // Chỉ đánh giá URL đang thực sự lỗi, tránh ẩn ảnh fallback còn đang tải.
      if (img.currentSrc && img.currentSrc !== img.src) return;
      if (!message) {
        message = document.createElement("span");
        message.className = "product-image-unavailable";
        message.textContent = "Ảnh hiện chưa khả dụng";
        img.insertAdjacentElement("afterend", message);
      }
      img.hidden = true;
      message.hidden = false;
    }
    img.addEventListener("error", inspectImage);
    img.addEventListener("load", inspectImage);
    inspectImage();
  });
})();
