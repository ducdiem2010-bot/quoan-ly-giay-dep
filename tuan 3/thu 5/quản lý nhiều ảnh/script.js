
const imageInput = document.getElementById("imageInput");
const chooseBtn = document.getElementById("chooseBtn");
const clearBtn = document.getElementById("clearBtn");
const imageList = document.getElementById("imageList");
const imageCount = document.getElementById("imageCount");
const featuredInfo = document.getElementById("featuredInfo");
const message = document.getElementById("message");
const uploadArea = document.querySelector(".upload-area");

const MAX_SIZE = 5 * 1024 * 1024; // 5 MB mỗi ảnh

const ALLOWED_TYPES = {
    "image/jpeg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WebP"
};

let images = [];
let featuredId = null;
let replacingId = null;

// Tạo UUID ngẫu nhiên
function createUUID() {
    if (crypto.randomUUID) {
        return crypto.randomUUID();
    }

    // Dự phòng cho trình duyệt cũ
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(
        /[xy]/g,
        function (c) {
            const r = Math.random() * 16 | 0;
            const v = c === "x" ? r : (r & 3 | 8);
            return v.toString(16);
        }
    );
}

// Hiển thị thông báo
function showMessage(text, type = "success") {
    message.textContent = text;
    message.className = "message " + type;
}

// Kiểm tra chữ ký thực tế của file
async function detectImageType(file) {
    const buffer = await file.slice(0, 12).arrayBuffer();
    const bytes = new Uint8Array(buffer);

    // JPEG: FF D8 FF
    if (
        bytes.length >= 3 &&
        bytes[0] === 0xFF &&
        bytes[1] === 0xD8 &&
        bytes[2] === 0xFF
    ) {
        return "image/jpeg";
    }

    // PNG: 89 50 4E 47 0D 0A 1A 0A
    const pngSignature = [
        0x89, 0x50, 0x4E, 0x47,
        0x0D, 0x0A, 0x1A, 0x0A
    ];

    if (
        bytes.length >= 8 &&
        pngSignature.every((value, index) => bytes[index] === value)
    ) {
        return "image/png";
    }

    // WebP: RIFF ở vị trí 0 và WEBP ở vị trí 8
    if (
        bytes.length >= 12 &&
        String.fromCharCode(...bytes.slice(0, 4)) === "RIFF" &&
        String.fromCharCode(...bytes.slice(8, 12)) === "WEBP"
    ) {
        return "image/webp";
    }

    return null;
}

// Kiểm tra định dạng, MIME và dung lượng
async function validateImage(file) {
    if (!file || file.size === 0) {
        throw new Error("File rỗng hoặc không hợp lệ.");
    }

    if (file.size > MAX_SIZE) {
        throw new Error("Ảnh vượt quá giới hạn 5 MB.");
    }

    if (!Object.hasOwn(ALLOWED_TYPES, file.type)) {
        throw new Error("Chỉ chấp nhận JPEG, PNG và WebP.");
    }

    const actualType = await detectImageType(file);

    if (!actualType) {
        throw new Error("Nội dung file không phải ảnh hợp lệ.");
    }

    if (actualType !== file.type) {
        throw new Error("MIME không khớp với nội dung ảnh.");
    }

    // Thử giải mã ảnh trước khi chấp nhận
    const url = URL.createObjectURL(file);

    try {
        await new Promise((resolve, reject) => {
            const img = new Image();

            img.onload = () => {
                if (img.naturalWidth > 0 && img.naturalHeight > 0) {
                    resolve();
                } else {
                    reject(new Error("Ảnh không có kích thước hợp lệ."));
                }
            };

            img.onerror = () => {
                reject(new Error("File ảnh bị hỏng hoặc không giải mã được."));
            };

            img.src = url;
        });
    } finally {
        URL.revokeObjectURL(url);
    }

    return actualType;
}

// Đọc và xử lý các file được chọn
async function handleFiles(fileList) {
    const files = Array.from(fileList);

    if (files.length === 0) return;

    let added = 0;
    let failed = 0;
    const errors = [];

    for (const file of files) {
        try {
            const type = await validateImage(file);

            // Nếu đang thay ảnh thì giữ nguyên ID của ảnh cũ
            const oldImage = replacingId
                ? images.find(img => img.id === replacingId)
                : null;

            const newImage = {
                id: oldImage ? oldImage.id : createUUID(),
                originalName: file.name,
                storedName: createUUID() + "." + (
                    type === "image/jpeg" ? "jpg" :
                    type === "image/png" ? "png" : "webp"
                ),
                type: type,
                size: file.size,
                file: file,
                url: URL.createObjectURL(file)
            };

            if (oldImage) {
                URL.revokeObjectURL(oldImage.url);

                const index = images.findIndex(
                    img => img.id === replacingId
                );

                images[index] = newImage;
                replacingId = null;
            } else {
                images.push(newImage);

                if (!featuredId) {
                    featuredId = newImage.id;
                }
            }

            added++;
        } catch (error) {
            failed++;
            errors.push(file.name + ": " + error.message);
        }
    }

    imageInput.value = "";
    replacingId = null;

    renderImages();

    if (failed > 0) {
        showMessage(
            `Đã xử lý ${added} ảnh, ${failed} ảnh bị từ chối.\n` +
            errors.join("\n"),
            "error"
        );
    } else {
        showMessage(`Đã xử lý thành công ${added} ảnh.`, "success");
    }
}

// Mở hộp thoại chọn ảnh
chooseBtn.addEventListener("click", () => {
    replacingId = null;
    imageInput.click();
});

uploadArea.addEventListener("click", () => {
    replacingId = null;
});

// Xử lý upload hoặc thay ảnh
imageInput.addEventListener("change", async () => {
    await handleFiles(imageInput.files);
});

// Kéo thả ảnh vào vùng upload
uploadArea.addEventListener("dragover", event => {
    event.preventDefault();
    uploadArea.classList.add("dragging");
});

uploadArea.addEventListener("dragleave", () => {
    uploadArea.classList.remove("dragging");
});

uploadArea.addEventListener("drop", async event => {
    event.preventDefault();
    uploadArea.classList.remove("dragging");
    replacingId = null;

    await handleFiles(event.dataTransfer.files);
});

// Chọn ảnh đại diện
function setFeatured(id) {
    featuredId = id;
    renderImages();
    showMessage("Đã chọn ảnh đại diện.", "success");
}

// Thay một ảnh cụ thể
function replaceImage(id) {
    replacingId = id;
    imageInput.multiple = false;
    imageInput.click();
}

// Xóa một ảnh
function deleteImage(id) {
    const image = images.find(img => img.id === id);
    if (!image) return;

    URL.revokeObjectURL(image.url);
    images = images.filter(img => img.id !== id);

    if (featuredId === id) {
        featuredId = images.length > 0 ? images[0].id : null;
    }

    renderImages();
    showMessage("Đã xóa ảnh.", "success");
}

// Xóa toàn bộ ảnh
clearBtn.addEventListener("click", () => {
    if (images.length === 0) {
        showMessage("Danh sách ảnh đang trống.", "error");
        return;
    }

    if (!confirm("Bạn có chắc muốn xóa tất cả ảnh?")) return;

    images.forEach(img => URL.revokeObjectURL(img.url));

    images = [];
    featuredId = null;
    replacingId = null;

    renderImages();
    showMessage("Đã xóa toàn bộ ảnh.", "success");
});

// Tạo phần tử HTML an toàn
function createElement(tag, className, text = "") {
    const element = document.createElement(tag);
    element.className = className;
    element.textContent = text;
    return element;
}

// Hiển thị danh sách ảnh
function renderImages() {
    imageList.replaceChildren();
    imageCount.textContent = images.length + " ảnh";

    if (images.length === 0) {
        imageList.appendChild(
            createElement(
                "div",
                "empty",
                "Chưa có ảnh nào. Hãy tải ảnh lên để bắt đầu."
            )
        );

        featuredInfo.textContent = "Chưa chọn ảnh đại diện.";
        return;
    }

    images.forEach(image => {
        const isFeatured = image.id === featuredId;

        const card = createElement(
            "article",
            "image-card" + (isFeatured ? " featured" : "")
        );

        const preview = document.createElement("img");
        preview.className = "image-preview";
        preview.src = image.url;
        preview.alt = "Ảnh sản phẩm " + image.originalName;

        const content = createElement("div", "card-content");

        if (isFeatured) {
            content.appendChild(
                createElement("span", "featured-label", "★ Ảnh đại diện")
            );
        }

        content.appendChild(
            createElement("div", "image-name", image.originalName)
        );

        content.appendChild(
            createElement("div", "image-meta", "Định dạng: " + image.type)
        );

        content.appendChild(
            createElement(
                "div",
                "image-meta",
                "Dung lượng: " + (image.size / 1024).toFixed(1) + " KB"
            )
        );

        content.appendChild(
            createElement("div", "image-meta", "UUID: " + image.id)
        );

        content.appendChild(
            createElement("div", "image-meta", "Tên lưu: " + image.storedName)
        );

        const actions = createElement("div", "card-actions");

        const featureBtn = createElement(
            "button",
            "btn primary",
            isFeatured ? "Đang đại diện" : "Chọn đại diện"
        );

        featureBtn.type = "button";
        featureBtn.disabled = isFeatured;
        featureBtn.addEventListener("click", () => setFeatured(image.id));

        const replaceBtn = createElement(
            "button",
            "btn secondary",
            "Thay ảnh"
        );

        replaceBtn.type = "button";
        replaceBtn.addEventListener("click", () => replaceImage(image.id));

        const deleteBtn = createElement(
            "button",
            "btn danger",
            "Xóa ảnh"
        );

        deleteBtn.type = "button";
        deleteBtn.addEventListener("click", () => deleteImage(image.id));

        actions.append(featureBtn, replaceBtn, deleteBtn);
        content.appendChild(actions);
        card.append(preview, content);
        imageList.appendChild(card);
    });

    const featured = images.find(img => img.id === featuredId);

    if (featured) {
        featuredInfo.replaceChildren();

        featuredInfo.appendChild(
            createElement("strong", "", featured.originalName)
        );

        featuredInfo.appendChild(
            createElement("p", "", "UUID: " + featured.id)
        );

        featuredInfo.appendChild(
            createElement("p", "", "Tên lưu: " + featured.storedName)
        );

        featuredInfo.appendChild(
            createElement("p", "", "Định dạng: " + featured.type)
        );
    }
}

// Khởi tạo giao diện
renderImages();
