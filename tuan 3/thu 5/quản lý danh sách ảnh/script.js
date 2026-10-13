
const MAX_SIZE = 5 * 1024 * 1024;
const MAX_IMAGES = 10;

const input = document.getElementById("imageInput");
const addBtn = document.getElementById("addBtn");
const list = document.getElementById("imageList");
const message = document.getElementById("message");
const count = document.getElementById("imageCount");
const productInput = document.getElementById("productId");

let images = [];

function uuid() {
    if (!crypto.randomUUID) {
        throw new Error("Trình duyệt cần hỗ trợ crypto.randomUUID().");
    }

    return crypto.randomUUID();
}

function getExtension(type) {
    return {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp"
    }[type];
}

// Kiểm tra chữ ký byte của ảnh.
async function detectType(file) {
    const b = new Uint8Array(
        await file.slice(0, 12).arrayBuffer()
    );

    if (b[0] === 255 && b[1] === 216 && b[2] === 255) {
        return "image/jpeg";
    }

    if ([137, 80, 78, 71, 13, 10, 26, 10]
        .every((v, i) => b[i] === v)) {
        return "image/png";
    }

    if (
        String.fromCharCode(...b.slice(0, 4)) === "RIFF" &&
        String.fromCharCode(...b.slice(8, 12)) === "WEBP"
    ) {
        return "image/webp";
    }

    return null;
}

async function validate(file) {
    const allowed = ["image/jpeg", "image/png", "image/webp"];

    if (!allowed.includes(file.type)) {
        throw new Error("Chỉ chấp nhận JPEG, PNG hoặc WebP.");
    }

    if (file.size === 0 || file.size > MAX_SIZE) {
        throw new Error("Ảnh phải có dung lượng không quá 5 MB.");
    }

    const actualType = await detectType(file);

    if (actualType !== file.type) {
        throw new Error("MIME không khớp chữ ký file.");
    }

    let bitmap;

    try {
        bitmap = await createImageBitmap(file);
    } catch {
        throw new Error("Nội dung ảnh bị lỗi hoặc không đọc được.");
    } finally {
        bitmap?.close();
    }

    return actualType;
}

function notify(text, error = false) {
    message.textContent = text;
    message.style.color = error ? "#dc2626" : "#15803d";
}

// Thêm nhiều ảnh.
addBtn.addEventListener("click", async () => {
    const productId = productInput.value.trim();
    const files = Array.from(input.files);

    if (!productId) {
        notify("Vui lòng nhập mã sản phẩm.", true);
        return;
    }

    if (!files.length) {
        notify("Vui lòng chọn ảnh cần thêm.", true);
        return;
    }

    if (images.length + files.length > MAX_IMAGES) {
        notify("Tổng số ảnh tối đa là 10.", true);
        return;
    }

    addBtn.disabled = true;
    const errors = [];
    let added = 0;

    try {
        for (const file of files) {
            try {
                const type = await validate(file);

                images.push({
                    id: uuid(),
                    productId,
                    fileName: uuid() + getExtension(type),
                    type,
                    size: file.size,
                    url: URL.createObjectURL(file),
                    isPrimary: images.length === 0
                });

                added++;
            } catch (e) {
                errors.push(file.name + ": " + e.message);
            }
        }

        render();

        notify(
            `Đã thêm ${added} ảnh.` +
            (errors.length ? "\n" + errors.join("\n") : ""),
            errors.length > 0 && added === 0
        );
    } finally {
        addBtn.disabled = false;
        input.value = "";
    }
});

// Thay một ảnh cụ thể bằng ảnh mới.
async function replaceImage(id, file) {
    try {
        const type = await validate(file);
        const oldImage = images.find(img => img.id === id);

        if (!oldImage) return;

        const newUrl = URL.createObjectURL(file);

        URL.revokeObjectURL(oldImage.url);

        oldImage.url = newUrl;
        oldImage.fileName = uuid() + getExtension(type);
        oldImage.type = type;
        oldImage.size = file.size;

        render();
        notify("Đã thay ảnh thành công.");
    } catch (e) {
        notify(e.message, true);
    }
}

// Chọn duy nhất một ảnh đại diện.
function setPrimary(id) {
    images.forEach(img => {
        img.isPrimary = img.id === id;
    });

    render();
    notify("Đã cập nhật ảnh đại diện.");
}

// Xóa từng ảnh.
function deleteImage(id) {
    const index = images.findIndex(img => img.id === id);

    if (index === -1) return;

    const wasPrimary = images[index].isPrimary;

    URL.revokeObjectURL(images[index].url);
    images.splice(index, 1);

    if (wasPrimary && images.length) {
        images[0].isPrimary = true;
    }

    render();
    notify("Đã xóa ảnh.");
}

// Hiển thị danh sách ảnh.
function render() {
    list.replaceChildren();
    count.textContent = `Số ảnh: ${images.length}/${MAX_IMAGES}`;

    images.forEach(img => {
        const card = document.createElement("div");
        card.className = "image-card";

        const preview = document.createElement("img");
        preview.src = img.url;
        preview.alt = "Ảnh sản phẩm " + img.productId;

        const title = document.createElement("p");
        title.textContent = img.fileName;

        const info = document.createElement("p");
        info.textContent =
            `${img.type} · ${(img.size / 1048576).toFixed(2)} MB`;

        const badge = document.createElement("span");
        badge.className = "badge";
        badge.textContent = img.isPrimary
            ? "Ảnh đại diện"
            : "Ảnh phụ";

        const actions = document.createElement("div");
        actions.className = "card-actions";

        const primary = document.createElement("button");
        primary.className = "primary-btn";
        primary.textContent = img.isPrimary
            ? "Đang là ảnh đại diện"
            : "Chọn đại diện";
        primary.disabled = img.isPrimary;
        primary.onclick = () => setPrimary(img.id);

        // Mỗi thẻ có một input riêng để thay đúng ảnh.
        const replaceInput = document.createElement("input");
        replaceInput.type = "file";
        replaceInput.accept = "image/jpeg,image/png,image/webp";
        replaceInput.hidden = true;

        const replace = document.createElement("button");
        replace.className = "replace-btn";
        replace.textContent = "Thay ảnh";
        replace.onclick = () => replaceInput.click();

        replaceInput.onchange = async () => {
            const file = replaceInput.files[0];

            if (file) {
                await replaceImage(img.id, file);
            }

            replaceInput.value = "";
        };

        const remove = document.createElement("button");
        remove.className = "delete-btn";
        remove.textContent = "Xóa ảnh";
        remove.onclick = () => {
            if (confirm("Bạn có chắc muốn xóa ảnh này?")) {
                deleteImage(img.id);
            }
        };

        actions.append(primary, replace, remove, replaceInput);
        card.append(preview, badge, title, info, actions);
        list.appendChild(card);
    });
}
