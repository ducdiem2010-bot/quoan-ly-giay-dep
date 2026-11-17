
const products = [
    {
        id: 1,
        name: "Nike Air Max",
        brand: "Nike",
        price: 1850000,
        images: [
            {
                src: "images/giay-nike.jpg",
                primary: true,
                local: false
            }
        ]
    },
    {
        id: 2,
        name: "Adidas Ultraboost",
        brand: "Adidas",
        price: 2200000,
        images: [
            {
                src: "images/giay-adidas.jpg",
                primary: true,
                local: false
            }
        ]
    }
];

const MAX_IMAGES = 10;
const MAX_SIZE = 5 * 1024 * 1024;
const ALLOWED_TYPES = [
    "image/jpeg",
    "image/png",
    "image/webp"
];

const productContainer = document.getElementById("productContainer");
const favoritesList = document.getElementById("favoritesList");

function loadFavorites() {
    try {
        const saved = JSON.parse(
            localStorage.getItem("shoesFavorites") || "[]"
        );

        if (!Array.isArray(saved)) return [];

        return [...new Set(saved.filter(id =>
            Number.isInteger(id) &&
            products.some(product => product.id === id)
        ))];
    } catch {
        return [];
    }
}

let favorites = loadFavorites();

function formatPrice(price) {
    return price.toLocaleString("vi-VN") + " đ";
}

function getPrimaryImage(product) {
    return product.images.find(image => image.primary)
        || product.images[0]
        || null;
}

function renderProducts() {
    productContainer.innerHTML = "";

    products.forEach(product => {
        const primary = getPrimaryImage(product);
        const card = document.createElement("article");

        card.className = "product-card";

        const mainImage = document.createElement("img");
        mainImage.className = "main-image";
        mainImage.id = `main-image-${product.id}`;
        mainImage.alt = product.name;
        mainImage.src = primary ? primary.src : "";

        const name = document.createElement("h3");
        name.className = "product-name";
        name.textContent = product.name;

        const brand = document.createElement("p");
        brand.textContent = "Thương hiệu: " + product.brand;

        const price = document.createElement("p");
        price.className = "product-price";
        price.textContent = formatPrice(product.price);

        const gallery = document.createElement("div");
        gallery.className = "image-gallery";
        gallery.id = `gallery-${product.id}`;

        const uploadLabel = document.createElement("label");
        uploadLabel.className = "upload-label";
        uploadLabel.htmlFor = `upload-${product.id}`;
        uploadLabel.textContent = "Tải ảnh sản phẩm";

        const upload = document.createElement("input");
        upload.className = "upload-input";
        upload.type = "file";
        upload.id = `upload-${product.id}`;
        upload.accept = "image/jpeg,image/png,image/webp";
        upload.multiple = true;

        const status = document.createElement("p");
        status.className = "status";
        status.id = `status-${product.id}`;
        status.textContent = `${product.images.length}/${MAX_IMAGES} ảnh`;

        const favorite = document.createElement("button");
        favorite.type = "button";
        favorite.id = `favorite-${product.id}`;
        favorite.className = "favorite-btn";

        updateFavoriteButton(favorite, product.id);

        favorite.addEventListener("click", () => {
            toggleFavorite(product.id);
        });

        upload.addEventListener("change", event => {
            handleUpload(product, event.target.files);
            event.target.value = "";
        });

        card.append(
            mainImage,
            name,
            brand,
            price,
            gallery,
            uploadLabel,
            upload,
            status,
            favorite
        );

        productContainer.appendChild(card);

        renderGallery(product);
    });

    renderFavorites();
}

function updateFavoriteButton(button, productId) {
    const active = favorites.includes(productId);

    button.classList.toggle("active", active);
    button.textContent = active
        ? "♥ Đã yêu thích"
        : "♡ Thêm yêu thích";
}

function renderGallery(product) {
    const gallery = document.getElementById(`gallery-${product.id}`);
    if (!gallery) return;

    gallery.innerHTML = "";

    product.images.forEach((image, index) => {
        const item = document.createElement("div");
        item.className = "thumbnail-item";

        const thumbnail = document.createElement("img");
        thumbnail.className = "thumbnail";
        thumbnail.alt = `Ảnh ${index + 1} ${product.name}`;
        thumbnail.src = image.src;

        if (image.primary) {
            thumbnail.classList.add("primary");
        }

        thumbnail.addEventListener("click", () => {
            product.images.forEach(img => img.primary = false);
            image.primary = true;
            renderProducts();
        });

        const label = document.createElement("span");
        label.className = "primary-label";
        label.textContent = image.primary
            ? "Ảnh đại diện"
            : `Ảnh ${index + 1}`;

        const actions = document.createElement("div");
        actions.className = "image-actions";

        const up = createButton("↑", "Đưa ảnh lên", () => {
            moveImage(product, index, index - 1);
        });
        up.disabled = index === 0;

        const down = createButton("↓", "Đưa ảnh xuống", () => {
            moveImage(product, index, index + 1);
        });
        down.disabled = index === product.images.length - 1;

        const remove = createButton("X", "Xóa ảnh", () => {
            deleteImage(product, index);
        });

        actions.append(up, down, remove);
        item.append(thumbnail, label, actions);
        gallery.appendChild(item);
    });
}

function createButton(text, title, callback) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = text;
    button.title = title;
    button.addEventListener("click", callback);
    return button;
}

function showStatus(product, message, error = false) {
    const status = document.getElementById(`status-${product.id}`);
    if (!status) return;

    status.textContent = message;
    status.classList.toggle("error", error);
}

async function handleUpload(product, files) {
    for (const file of Array.from(files)) {
        if (product.images.length >= MAX_IMAGES) {
            showStatus(product, `Tối đa ${MAX_IMAGES} ảnh mỗi sản phẩm.`, true);
            break;
        }

        if (!ALLOWED_TYPES.includes(file.type)) {
            showStatus(product, "Chỉ chấp nhận JPEG, PNG hoặc WebP.", true);
            continue;
        }

        if (file.size <= 0 || file.size > MAX_SIZE) {
            showStatus(product, "Ảnh phải lớn hơn 0 và không quá 5 MB.", true);
            continue;
        }

        const imageURL = URL.createObjectURL(file);

        try {
            await validateImage(imageURL);

            const newImage = {
                src: imageURL,
                primary: product.images.length === 0,
                local: true
            };

            product.images.push(newImage);
            renderProducts();

            showStatus(product, `Đã thêm ảnh: ${file.name}`);
        } catch {
            URL.revokeObjectURL(imageURL);
            showStatus(product, `File ${file.name} không phải ảnh hợp lệ.`, true);
        }
    }
}

function validateImage(src) {
    return new Promise((resolve, reject) => {
        const img = new Image();

        img.onload = () => {
            if (img.naturalWidth > 0 && img.naturalHeight > 0) {
                resolve();
            } else {
                reject(new Error("Ảnh không hợp lệ"));
            }
        };

        img.onerror = reject;
        img.src = src;
    });
}

function moveImage(product, from, to) {
    if (to < 0 || to >= product.images.length) return;

    const [image] = product.images.splice(from, 1);
    product.images.splice(to, 0, image);

    renderProducts();
}

function deleteImage(product, index) {
    const image = product.images[index];

    if (image.local) {
        URL.revokeObjectURL(image.src);
    }

    product.images.splice(index, 1);

    if (
        product.images.length > 0 &&
        !product.images.some(img => img.primary)
    ) {
        product.images[0].primary = true;
    }

    renderProducts();
}

function toggleFavorite(productId) {
    if (favorites.includes(productId)) {
        favorites = favorites.filter(id => id !== productId);
    } else {
        favorites.push(productId);
    }

    try {
        localStorage.setItem("shoesFavorites", JSON.stringify(favorites));
    } catch {
        alert("Không thể lưu danh sách yêu thích trong trình duyệt.");
    }

    renderProducts();
}

function renderFavorites() {
    favoritesList.innerHTML = "";

    const favoriteProducts = products.filter(product =>
        favorites.includes(product.id)
    );

    if (favoriteProducts.length === 0) {
        const empty = document.createElement("p");
        empty.className = "empty-message";
        empty.textContent = "Bạn chưa có sản phẩm yêu thích.";
        favoritesList.appendChild(empty);
        return;
    }

    favoriteProducts.forEach(product => {
        const item = document.createElement("div");
        item.className = "favorite-item";

        const image = getPrimaryImage(product);
        const img = document.createElement("img");
        img.src = image ? image.src : "";
        img.alt = product.name;

        const info = document.createElement("div");

        const name = document.createElement("strong");
        name.textContent = product.name;

        const price = document.createElement("p");
        price.textContent = formatPrice(product.price);

        const remove = createButton("Bỏ yêu thích", "Bỏ yêu thích", () => {
            toggleFavorite(product.id);
        });

        info.append(name, price, remove);
        item.append(img, info);
        favoritesList.appendChild(item);
    });
}

// Khởi chạy
renderProducts();
