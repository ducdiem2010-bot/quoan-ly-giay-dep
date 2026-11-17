document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("product-images");
  const preview = document.getElementById("image-preview");
  if (!input || !preview) return;
  const allowed = new Set(["image/jpeg", "image/png", "image/webp"]);
  input.addEventListener("change", () => {
    preview.replaceChildren();
    const files = Array.from(input.files || []);
    for (const file of files) {
      if (!allowed.has(file.type) || file.size > 5 * 1024 * 1024) {
        alert(`Tệp ${file.name} không hợp lệ. Chỉ nhận JPG/PNG/WebP tối đa 5 MB.`);
        input.value = ""; preview.replaceChildren(); return;
      }
    }
    files.forEach(file => {
      const card = document.createElement("div"); card.className = "preview-image";
      const img = document.createElement("img"); img.alt = "Xem trước " + file.name;
      const label = document.createElement("span"); label.textContent = file.name;
      const reader = new FileReader(); reader.onload = e => { img.src = e.target.result; }; reader.readAsDataURL(file);
      card.append(img, label); preview.append(card);
    });
  });
});
