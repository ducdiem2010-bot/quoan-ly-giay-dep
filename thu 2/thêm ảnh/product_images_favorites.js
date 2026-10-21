
"use strict";

// =============================================
// 1. CẤU HÌNH VÀ LẤY PHẦN TỬ HTML
// =============================================
const productContainer = document.getElementById("productContainer");
const favoritesList = document.getElementById("favoritesList");

const PRODUCT_KEY = "shoesProducts";
const IMAGE_KEY = "shoesProductImages";
const FAVORITE_KEY = "shoesFavoriteIds";

// Ảnh minh họa mẫu
const sampleProducts = [
    {
        id: "SP001",
        name: "Nike Air Max",
        brand: "Nike",
        price: 1850000,
        status: "Hiển thị"
    },
    {
        id: "SP002",
        name: "Adidas Ultraboost",
        brand: "Adidas",
        price: 2200000,
        status: "Hiển thị"
    },
    {
        id: "SP003",
        name: "Puma Running",
        brand: "Puma",
        price: 1450000,
        status: "Hiển thị"
    }
];

const sampleImages = {
    SP001: [
        "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=600&q=70"
    ],
    SP002: [
        "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=700&q=80"
    ],
    SP003: [
        "https://images.unsplash.com/photo-1556906781-9a412961c28c?auto=format&fit=crop&w=800&q=80"
    ]
};

// =============================================
// 2. HÀM ĐỌC VÀ LƯU LOCALSTORAGE
// =============================================
function readStorage(key, fallback) {
    try {
        const value = localStorage.getItem(key);
        return value ? JSON.parse(value) : fallback;
    } catch (error) {
        console.error("Lỗi đọc dữ liệu:", key, error);
        return fallback;
    }
}

function writeStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
        return true;
    } catch (error) {
        console.error("Lỗi lưu dữ liệu:", key, error);
        alert("Không thể lưu dữ liệu. Hãy kiểm tra trình duyệt.");
        return false;
    }
}

// =============================================
// 3. KHỞI TẠO DỮ LIỆU SẢN PHẨM
// =============================================
function loadProducts() {
    const savedProducts = readStorage(PRODUCT_KEY, null);

    if (Array.isArray(savedProducts) && savedProducts.length > 0) {
        return savedProducts
            .filter(p => p && p.id != null && p.status !== "Đã xóa")
            .map(p => ({
                id: String(p.id),
                name: String(p.name || "Sản phẩm chưa đặt tên"),
                brand: String(p.brand || "Chưa cập nhật"),
                price: Number(p.price) || 0,
                status: p.status || "Hiển thị"
            }))
            .filter(p => p.status === "Hiển thị");
    }

    return sampleProducts.map(p => ({ ...p }));
}

let products = loadProducts();

let productImages = readStorage(IMAGE_KEY, {});

if (
    !productImages ||
    typeof productImages !== "object" ||
    Array.isArray(productImages)
) {
    productImages = {};
}

let favoriteIds = readStorage(FAVORITE_KEY, []);

if (!Array.isArray(favoriteIds)) {
    favoriteIds = [];
}

favoriteIds = favoriteIds.map(String);

// Thêm ảnh mặc định nếu sản phẩm chưa có ảnh
products.forEach(product => {
    const id = String(product.id);

    if (!Array.isArray(productImages[id]) || productImages[id].length === 0) {
        productImages[id] = sampleImages[id]
            ? [...sampleImages[id]]
            : [...(sampleImages.SP001 || [])];
    }
});

// Lưu ảnh khởi tạo
writeStorage(IMAGE_KEY, productImages);

// =============================================
// 4. ĐỊNH DẠNG GIÁ
// =============================================
function formatPrice(price) {
    return Number(price).toLocaleString("vi-VN") + " đ";
}

// =============================================
// 5. TẠO NÚT
// =============================================
function createButton(text, className, onClick) {
    const button = document.createElement("button");

    button.type = "button";
    button.textContent = text;
    button.className = className;
    button.addEventListener("click", onClick);

    return button;
}

// =============================================
// 6. TẠO ẢNH AN TOÀN
// =============================================
function createImage(src, alt, className) {
    const img = document.createElement("img");

    img.src = src;
    img.alt = alt;
    img.className = className;
    img.loading = "lazy";

    img.addEventListener("error", function() {
        this.alt = "Không tải được ảnh sản phẩm";
        this.style.opacity = "0.35";
    });

    return img;
}

// =============================================
// 7. LẤY ẢNH CỦA SẢN PHẨM
// =============================================
function getImages(productId) {
    const images = productImages[String(productId)];
    return Array.isArray(images) ? images : [];
}

// =============================================
// 8. HIỂN THỊ DANH SÁCH SẢN PHẨM
// =============================================
function renderProducts() {
    productContainer.replaceChildren();

    if (products.length === 0) {
        const empty = document.createElement("p");
        empty.className = "empty-message";
        empty.textContent = "Chưa có sản phẩm đang hiển thị.";
        productContainer.appendChild(empty);
        renderFavorites();
        return;
    }

    products.forEach(product => {
        const id = String(product.id);
        const images = getImages(id);

        if (images.length === 0) {
            images.push(
                "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=800&q=80"
            );
            productImages[id] = images;
        }

        const card = document.createElement("article");
        card.className = "product-card";

        // Ảnh đại diện và số lượng ảnh
        const imageWrapper = document.createElement("div");
        imageWrapper.className = "main-image-wrapper";

        const mainImage = createImage(
            images[0],
            product.name,
            "main-image"
        );

        mainImage.id = `main-image-${id}`;

        const imageCount = document.createElement("span");
        imageCount.className = "image-count";
        imageCount.textContent = `${images.length} ảnh`;

        imageWrapper.append(mainImage, imageCount);

        // Thông tin sản phẩm
        const info = document.createElement("div");
        info.className = "product-info";

        const name = document.createElement("h3");
        name.textContent = product.name;

        const brand = document.createElement("p");
        brand.className = "product-brand";
        brand.textContent = `Thương hiệu: ${product.brand}`;

        const price = document.createElement("p");
        price.className = "product-price";
        price.textContent = formatPrice(product.price);

        const galleryTitle = document.createElement("p");
        galleryTitle.className = "image-management-title";
        galleryTitle.textContent = "Thư viện ảnh";

        const gallery = document.createElement("div");
        gallery.className = "image-gallery";

        // Tạo ảnh nhỏ và nút thao tác
        images.forEach((src, index) => {
            const thumbnail = document.createElement("button");

            thumbnail.type = "button";
            thumbnail.className =
                "thumbnail-item" + (index === 0 ? " active" : "");
            thumbnail.title = `Chọn ảnh ${index + 1} làm ảnh đại diện`;
            thumbnail.setAttribute("aria-label", thumbnail.title);

            const thumbnailImage = createImage(
                src,
                `${product.name} - ảnh ${index + 1}`,
                ""
            );

            thumbnail.appendChild(thumbnailImage);

            thumbnail.addEventListener("click", () => {
                selectMainImage(id, index);
            });

            gallery.appendChild(thumbnail);
        });

        // Nhập URL ảnh
        const addImageForm = document.createElement("form");
        addImageForm.className = "add-image-form";

        const imageUrlInput = document.createElement("input");
        imageUrlInput.type = "url";
        imageUrlInput.placeholder = "Dán URL ảnh sản phẩm...";
        imageUrlInput.setAttribute("aria-label", "URL ảnh mới");
        imageUrlInput.required = true;

        const addImageButton = document.createElement("button");
        addImageButton.type = "submit";
        addImageButton.className = "btn btn-primary";
        addImageButton.textContent = "Thêm ảnh";

        addImageForm.append(imageUrlInput, addImageButton);

        addImageForm.addEventListener("submit", event => {
            event.preventDefault();

            const url = imageUrlInput.value.trim();

            if (!isValidImageUrl(url)) {
                alert("Vui lòng nhập URL ảnh HTTP hoặc HTTPS hợp lệ.");
                return;
            }

            const currentImages = getImages(id);

            if (currentImages.includes(url)) {
                alert("Ảnh này đã có trong thư viện.");
                return;
            }

            const updatedImages = [...currentImages, url];
            productImages[id] = updatedImages;

            if (!writeStorage(IMAGE_KEY, productImages)) {
                productImages[id] = currentImages;
                return;
            }

            renderProducts();
        });

        // Nút đổi thứ tự và xóa ảnh
        const imageActions = document.createElement("div");
        imageActions.className = "product-actions";

        const moveUpButton = createButton(
            "↑ Ảnh lên",
            "btn btn-secondary",
            () => moveImage(id, 0, -1)
        );

        const moveDownButton = createButton(
            "↓ Ảnh xuống",
            "btn btn-secondary",
            () => moveImage(id, 0, 1)
        );

        const deleteImageButton = createButton(
            "Xóa ảnh cuối",
            "btn btn-danger",
            () => deleteLastImage(id)
        );

        moveUpButton.title = "Đưa ảnh đại diện lên đầu danh sách";
        moveDownButton.title = "Đưa ảnh đại diện xuống dưới";

        imageActions.append(
            moveUpButton,
            moveDownButton,
            deleteImageButton
        );

        // Yêu thích
        const favoriteButton = createButton(
            favoriteIds.includes(id)
                ? "♥ Đã yêu thích"
                : "♡ Thêm yêu thích",
            "favorite-btn" +
                (favoriteIds.includes(id) ? " is-favorite" : ""),
            () => toggleFavorite(id)
        );

        info.append(
            name,
            brand,
            price,
            galleryTitle,
            gallery,
            addImageForm,
            imageActions,
            favoriteButton
        );

        card.append(imageWrapper, info);
        productContainer.appendChild(card);
    });

    renderFavorites();
}

// =============================================
// 9. CHỌN ẢNH ĐẠI DIỆN
// =============================================
function selectMainImage(productId, imageIndex) {
    const images = getImages(productId);

    if (imageIndex < 0 || imageIndex >= images.length) return;

    // Chuyển ảnh được chọn lên đầu danh sách
    const selectedImage = images[imageIndex];
    const updatedImages = [
        selectedImage,
        ...images.filter((_, index) => index !== imageIndex)
    ];

    const oldImages = productImages[productId];
    productImages[productId] = updatedImages;

    if (!writeStorage(IMAGE_KEY, productImages)) {
        productImages[productId] = oldImages;
        return;
    }

    renderProducts();
}

// =============================================
// 10. ĐỔI THỨ TỰ ẢNH
// =============================================
function moveImage(productId, index, direction) {
    const images = [...getImages(productId)];
    const newIndex = index + direction;

    if (newIndex < 0 || newIndex >= images.length) {
        alert("Ảnh đã ở vị trí đầu hoặc cuối danh sách.");
        return;
    }

    [images[index], images[newIndex]] =
        [images[newIndex], images[index]];

    const oldImages = productImages[productId];
    productImages[productId] = images;

    if (!writeStorage(IMAGE_KEY, productImages)) {
        productImages[productId] = oldImages;
        return;
    }

    renderProducts();
}

// =============================================
// 11. XÓA ẢNH CUỐI
// =============================================
function deleteLastImage(productId) {
    const images = [...getImages(productId)];

    if (images.length <= 1) {
        alert("Mỗi sản phẩm cần giữ lại ít nhất một ảnh.");
        return;
    }

    if (!confirm("Bạn có chắc muốn xóa ảnh cuối cùng?")) {
        return;
    }

    const oldImages = productImages[productId];
    images.pop();

    productImages[productId] = images;

    if (!writeStorage(IMAGE_KEY, productImages)) {
        productImages[productId] = oldImages;
        return;
    }

    renderProducts();
}

// =============================================
// 12. KIỂM TRA URL ẢNH
// =============================================
function isValidImageUrl(value) {
    try {
        const url = new URL(value);
        return url.protocol === "https:" || url.protocol === "http:";
    } catch {
        return false;
    }
}

// =============================================
// 13. THÊM HOẶC BỎ YÊU THÍCH
// =============================================
function toggleFavorite(productId) {
    const id = String(productId);
    const oldFavorites = [...favoriteIds];

    if (favoriteIds.includes(id)) {
        favoriteIds = favoriteIds.filter(item => item !== id);
    } else {
        favoriteIds.push(id);
    }

    if (!writeStorage(FAVORITE_KEY, favoriteIds)) {
        favoriteIds = oldFavorites;
        return;
    }

    renderProducts();
}

// =============================================
// 14. HIỂN THỊ DANH SÁCH YÊU THÍCH
// =============================================
function renderFavorites() {
    favoritesList.replaceChildren();

    const favorites = products.filter(product =>
        favoriteIds.includes(String(product.id))
    );

    if (favorites.length === 0) {
        const empty = document.createElement("p");
        empty.className = "empty-message";
        empty.textContent =
            "Bạn chưa có sản phẩm yêu thích nào.";
        favoritesList.appendChild(empty);
        return;
    }

    favorites.forEach(product => {
        const id = String(product.id);
        const images = getImages(id);

        const card = document.createElement("article");
        card.className = "favorite-card";

        const image = createImage(
            images[0] || "",
            product.name,
            ""
        );

        const name = document.createElement("h3");
        name.textContent = product.name;

        const price = document.createElement("p");
        price.className = "product-price";
        price.textContent = formatPrice(product.price);

        const removeButton = createButton(
            "♥ Bỏ yêu thích",
            "btn btn-danger",
            () => toggleFavorite(id)
        );

        card.append(image, name, price, removeButton);
        favoritesList.appendChild(card);
    });
}

// =============================================
// 15. KHỞI CHẠY
// =============================================
renderProducts();
renderFavorites();
    