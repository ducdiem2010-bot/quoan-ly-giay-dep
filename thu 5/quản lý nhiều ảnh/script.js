
document.addEventListener("DOMContentLoaded", async function () {
    "use strict";

    const PRODUCT_KEY = "shoesProducts";
    const DB_NAME = "ShoesStoreImageDB";
    const STORE_NAME = "productImages";
    const MAX_SIZE = 5 * 1024 * 1024;

    const productSelect = document.getElementById("productSelect");
    const selectedProductInfo =
        document.getElementById("selectedProductInfo");
    const imageInput = document.getElementById("imageInput");
    const chooseBtn = document.getElementById("chooseBtn");
    const clearBtn = document.getElementById("clearBtn");
    const uploadArea = document.getElementById("uploadArea");
    const imageList = document.getElementById("imageList");
    const imageCount = document.getElementById("imageCount");
    const featuredInfo = document.getElementById("featuredInfo");
    const message = document.getElementById("message");

    let db;
    let products = [];
    let currentImages = [];
    let objectUrls = [];

    // ==============================
    // 1. THÔNG BÁO
    // ==============================
    function showMessage(text, isError = false) {
        message.textContent = text;
        message.className = isError
            ? "message error"
            : "message success";
    }

    // ==============================
    // 2. ĐỌC DANH SÁCH SẢN PHẨM
    // ==============================
    function loadProducts() {
        try {
            const data = JSON.parse(
                localStorage.getItem(PRODUCT_KEY) || "[]"
            );

            if (!Array.isArray(data)) {
                throw new Error("Danh sách sản phẩm không hợp lệ.");
            }

            return data.filter(product =>
                product.status !== "Đã xóa"
            );
        } catch (error) {
            console.error(error);
            showMessage(
                "Không đọc được danh sách sản phẩm. Hãy kiểm tra trang quản lý sản phẩm.",
                true
            );
            return [];
        }
    }

    function populateProducts() {
        products = loadProducts();
        productSelect.replaceChildren();

        const placeholder = document.createElement("option");
        placeholder.value = "";
        placeholder.textContent = "-- Chọn sản phẩm --";
        productSelect.appendChild(placeholder);

        products.forEach(product => {
            const option = document.createElement("option");
            option.value = String(product.id);
            option.textContent =
                `${product.id} - ${product.name}`;

            productSelect.appendChild(option);
        });

        if (products.length === 0) {
            selectedProductInfo.textContent =
                "Chưa có sản phẩm. Hãy thêm sản phẩm ở trang quản lý sản phẩm trước.";
        }
    }

    function getSelectedProduct() {
        return products.find(
            product => String(product.id) === productSelect.value
        );
    }

    function updateSelectedProductInfo() {
        const product = getSelectedProduct();

        if (!product) {
            selectedProductInfo.textContent =
                "Vui lòng chọn sản phẩm.";
            return;
        }

        selectedProductInfo.textContent =
            `Mã: ${product.id} | Tên: ${product.name} | ` +
            `Thương hiệu: ${product.brand || "Chưa cập nhật"}`;
    }

    // ==============================
    // 3. KHỞI TẠO INDEXEDDB
    // ==============================
    function openDatabase() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(DB_NAME, 1);

            request.onupgradeneeded = function () {
                const database = request.result;

                if (!database.objectStoreNames.contains(STORE_NAME)) {
                    database.createObjectStore(STORE_NAME, {
                        keyPath: "id"
                    });
                }
            };

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    function getAllImages() {
        return new Promise((resolve, reject) => {
            const transaction = db.transaction(STORE_NAME, "readonly");
            const store = transaction.objectStore(STORE_NAME);
            const request = store.getAll();

            request.onsuccess = () => resolve(request.result || []);
            request.onerror = () => reject(request.error);
        });
    }

    function saveImage(image) {
        return new Promise((resolve, reject) => {
            const transaction = db.transaction(STORE_NAME, "readwrite");
            transaction.objectStore(STORE_NAME).put(image);

            transaction.oncomplete = () => resolve();
            transaction.onerror = () => reject(transaction.error);
            transaction.onabort = () => reject(transaction.error);
        });
    }

    function deleteImage(imageId) {
        return new Promise((resolve, reject) => {
            const transaction = db.transaction(STORE_NAME, "readwrite");
            transaction.objectStore(STORE_NAME).delete(imageId);

            transaction.oncomplete = () => resolve();
            transaction.onerror = () => reject(transaction.error);
        });
    }

    async function deleteImagesForProduct(productId) {
        const images = await getAllImages();
        const targets = images.filter(
            image => String(image.productId) === String(productId)
        );

        await new Promise((resolve, reject) => {
            const transaction = db.transaction(STORE_NAME, "readwrite");
            const store = transaction.objectStore(STORE_NAME);

            targets.forEach(image => store.delete(image.id));

            transaction.oncomplete = () => resolve();
            transaction.onerror = () => reject(transaction.error);
        });
    }

    // ==============================
    // 4. TẢI ẢNH CỦA SẢN PHẨM
    // ==============================
    async function loadSelectedImages() {
        const product = getSelectedProduct();

        clearObjectUrls();
        currentImages = [];

        if (!product) {
            renderImages();
            updateSelectedProductInfo();
            return;
        }

        const allImages = await getAllImages();

        currentImages = allImages
            .filter(image =>
                String(image.productId) === String(product.id)
            )
            .sort((a, b) => a.createdAt - b.createdAt);

        updateSelectedProductInfo();
        renderImages();
    }

    function clearObjectUrls() {
        objectUrls.forEach(url => URL.revokeObjectURL(url));
        objectUrls = [];
    }

    // ==============================
    // 5. HIỂN THỊ DANH SÁCH ẢNH
    // ==============================
    function renderImages() {
        imageList.replaceChildren();

        imageCount.textContent = `${currentImages.length} ảnh`;

        const featured = currentImages.find(image => image.isFeatured);

        if (featured) {
            featuredInfo.textContent =
                `Ảnh đại diện: ${featured.name}`;
        } else {
            featuredInfo.textContent = "Chưa chọn ảnh đại diện.";
        }

        if (currentImages.length === 0) {
            const empty = document.createElement("div");
            empty.className = "empty";
            empty.textContent = getSelectedProduct()
                ? "Sản phẩm này chưa có ảnh."
                : "Hãy chọn sản phẩm để xem danh sách ảnh.";

            imageList.appendChild(empty);
            return;
        }

        currentImages.forEach(image => {
            const card = document.createElement("article");
            card.className = "image-card";

            const preview = document.createElement("img");
            preview.alt = image.name;
            preview.src = URL.createObjectURL(image.blob);
            objectUrls.push(preview.src);

            const details = document.createElement("div");
            details.className = "image-details";

            const name = document.createElement("p");
            name.className = "image-name";
            name.textContent = image.name;

            const size = document.createElement("p");
            size.className = "image-size";
            size.textContent =
                `${(image.blob.size / 1024).toFixed(1)} KB`;

            details.append(name, size);

            const actions = document.createElement("div");
            actions.className = "image-actions";

            if (image.isFeatured) {
                const badge = document.createElement("span");
                badge.className = "badge featured-badge";
                badge.textContent = "Ảnh đại diện";
                actions.appendChild(badge);
            } else {
                actions.appendChild(createButton(
                    "Chọn làm đại diện",
                    "btn primary",
                    () => setFeatured(image.id)
                ));
            }

            actions.appendChild(createButton(
                "Xóa ảnh",
                "btn danger",
                () => removeOneImage(image.id)
            ));

            card.append(preview, details, actions);
            imageList.appendChild(card);
        });
    }

    function createButton(text, className, handler) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = className;
        button.textContent = text;
        button.addEventListener("click", handler);
        return button;
    }

    // ==============================
    // 6. CHỌN ẢNH ĐẠI DIỆN
    // ==============================
    async function setFeatured(imageId) {
        try {
            const product = getSelectedProduct();
            if (!product) return;

            const images = await getAllImages();

            for (const image of images) {
                if (String(image.productId) !== String(product.id)) {
                    continue;
                }

                image.isFeatured = image.id === imageId;
                await saveImage(image);
            }

            await loadSelectedImages();
            showMessage("Đã cập nhật ảnh đại diện.");
        } catch (error) {
            console.error(error);
            showMessage("Không thể cập nhật ảnh đại diện.", true);
        }
    }

    // ==============================
    // 7. KIỂM TRA FILE ẢNH
    // ==============================
    function validateImage(file) {
        const allowedTypes = [
            "image/jpeg",
            "image/png",
            "image/webp"
        ];

        if (!allowedTypes.includes(file.type)) {
            return "Chỉ chấp nhận ảnh JPEG, PNG hoặc WebP.";
        }

        if (file.size > MAX_SIZE) {
            return "Mỗi ảnh không được vượt quá 5 MB.";
        }

        if (file.size === 0) {
            return "File ảnh không hợp lệ hoặc rỗng.";
        }

        return null;
    }

    // ==============================
    // 8. THÊM ẢNH VÀ LƯU
    // ==============================
    async function handleFiles(fileList) {
        const product = getSelectedProduct();

        if (!product) {
            showMessage("Bạn phải chọn sản phẩm trước khi thêm ảnh.", true);
            return;
        }

        const files = Array.from(fileList || []);

        if (files.length === 0) return;

        let successCount = 0;
        const errors = [];

        try {
            for (const file of files) {
                const error = validateImage(file);

                if (error) {
                    errors.push(`${file.name}: ${error}`);
                    continue;
                }

                const image = {
                    id: crypto.randomUUID
                        ? crypto.randomUUID()
                        : `${Date.now()}-${Math.random()}`,
                    productId: product.id,
                    name: file.name,
                    type: file.type,
                    blob: file,
                    isFeatured: false,
                    createdAt: Date.now() + successCount
                };

                const alreadyHasFeatured = currentImages.some(
                    item => item.isFeatured
                );

                if (currentImages.length === 0 && successCount === 0) {
                    image.isFeatured = true;
                } else if (!alreadyHasFeatured && successCount === 0) {
                    image.isFeatured = true;
                }

                await saveImage(image);
                successCount++;
            }

            await loadSelectedImages();

            if (errors.length > 0) {
                showMessage(
                    `Đã lưu ${successCount} ảnh. ` + errors.join(" "),
                    successCount === 0
                );
            } else {
                showMessage(`Đã lưu ${successCount} ảnh cho ${product.name}.`);
            }
        } catch (error) {
            console.error(error);
            showMessage(
                "Không thể lưu ảnh. Hãy kiểm tra dung lượng lưu trữ của trình duyệt.",
                true
            );
        } finally {
            imageInput.value = "";
        }
    }

    // ==============================
    // 9. XÓA MỘT ẢNH
    // ==============================
    async function removeOneImage(imageId) {
        const image = currentImages.find(item => item.id === imageId);
        if (!image) return;

        if (!confirm(`Bạn có chắc muốn xóa ảnh "${image.name}"?`)) {
            return;
        }

        try {
            await deleteImage(imageId);

            const remaining = currentImages.filter(
                item => item.id !== imageId
            );

            if (image.isFeatured && remaining.length > 0) {
                await setFeatured(remaining[0].id);
            } else {
                await loadSelectedImages();
            }

            showMessage("Đã xóa ảnh.");
        } catch (error) {
            console.error(error);
            showMessage("Không thể xóa ảnh.", true);
        }
    }

    // ==============================
    // 10. XÓA TẤT CẢ ẢNH CỦA SẢN PHẨM
    // ==============================
    clearBtn.addEventListener("click", async function () {
        const product = getSelectedProduct();

        if (!product) {
            showMessage("Vui lòng chọn sản phẩm trước.", true);
            return;
        }

        if (currentImages.length === 0) {
            showMessage("Sản phẩm chưa có ảnh.", true);
            return;
        }

        if (!confirm(
            `Xóa tất cả ${currentImages.length} ảnh của "${product.name}"?`
        )) {
            return;
        }

        try {
            await deleteImagesForProduct(product.id);
            await loadSelectedImages();
            showMessage("Đã xóa tất cả ảnh của sản phẩm.");
        } catch (error) {
            console.error(error);
            showMessage("Không thể xóa ảnh.", true);
        }
    });

    // ==============================
    // 11. SỰ KIỆN GIAO DIỆN
    // ==============================
    chooseBtn.addEventListener("click", function () {
        if (!getSelectedProduct()) {
            showMessage("Hãy chọn sản phẩm trước khi tải ảnh lên.", true);
            return;
        }

        imageInput.click();
    });

    imageInput.addEventListener("change", event => {
        handleFiles(event.target.files);
    });

    productSelect.addEventListener("change", async function () {
        message.textContent = "";
        await loadSelectedImages();
    });

    uploadArea.addEventListener("dragover", event => {
        event.preventDefault();
        uploadArea.classList.add("dragover");
    });

    uploadArea.addEventListener("dragleave", () => {
        uploadArea.classList.remove("dragover");
    });

    uploadArea.addEventListener("drop", event => {
        event.preventDefault();
        uploadArea.classList.remove("dragover");
        handleFiles(event.dataTransfer.files);
    });

    // ==============================
    // 12. KHỞI CHẠY
    // ==============================
    try {
        if (!("indexedDB" in window)) {
            throw new Error("Trình duyệt không hỗ trợ IndexedDB.");
        }

        db = await openDatabase();
        populateProducts();
        await loadSelectedImages();
    } catch (error) {
        console.error(error);
        showMessage(
            "Không khởi tạo được nơi lưu ảnh. Hãy thử mở bằng Live Server trên trình duyệt hiện đại.",
            true
        );
    }
});
