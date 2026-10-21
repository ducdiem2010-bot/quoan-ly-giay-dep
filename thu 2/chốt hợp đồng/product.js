
"use strict";

// =============================================
// 1. LẤY CÁC PHẦN TỬ HTML
// =============================================
const form = document.getElementById("productForm");
const productList = document.getElementById("productList");
const message = document.getElementById("message");
const searchInput = document.getElementById("search");
const saveButton = document.getElementById("saveButton");
const cancelButton = document.getElementById("cancelButton");

const fields = {
    id: document.getElementById("productId"),
    name: document.getElementById("name"),
    brand: document.getElementById("brand"),
    type: document.getElementById("type"),
    gender: document.getElementById("gender"),
    price: document.getElementById("price")
};

const STORAGE_KEY = "shoesProducts";

// =============================================
// 2. ĐỌC DỮ LIỆU ĐÃ LƯU
// =============================================
function loadProducts() {
    try {
        const data = JSON.parse(
            localStorage.getItem(STORAGE_KEY) || "[]"
        );

        if (!Array.isArray(data)) {
            return [];
        }

        // Chuẩn hóa dữ liệu cũ nếu chưa có trạng thái
        return data
            .filter(p => p && typeof p === "object" && p.id != null)
            .map(p => ({
                id: String(p.id),
                name: String(p.name || ""),
                brand: String(p.brand || ""),
                type: String(p.type || ""),
                gender: String(p.gender || ""),
                price: Number(p.price) || 0,
                status: ["Hiển thị", "Ẩn", "Đã xóa"].includes(p.status)
                    ? p.status
                    : "Hiển thị"
            }));
    } catch (error) {
        console.error("Không thể đọc dữ liệu sản phẩm:", error);
        return [];
    }
}

let products = loadProducts();

// =============================================
// 3. LƯU DỮ LIỆU
// =============================================
function saveData() {
    try {
        localStorage.setItem(
            STORAGE_KEY,
            JSON.stringify(products)
        );
        return true;
    } catch (error) {
        console.error("Không thể lưu dữ liệu:", error);
        showMessage(
            "Không thể lưu dữ liệu. Hãy kiểm tra dung lượng trình duyệt.",
            "error"
        );
        return false;
    }
}

// =============================================
// 4. HIỂN THỊ THÔNG BÁO
// =============================================
function showMessage(text, type = "success") {
    message.textContent = text;
    message.className = type === "error"
        ? "message-error"
        : "message-success";
}

// =============================================
// 5. ĐỊNH DẠNG GIÁ TIỀN
// =============================================
function formatPrice(price) {
    return Number(price).toLocaleString("vi-VN") + " đ";
}

// =============================================
// 6. TẠO NÚT THAO TÁC
// =============================================
function createButton(text, onClick, className = "") {
    const button = document.createElement("button");

    button.type = "button";
    button.textContent = text;

    if (className) {
        button.className = className;
    }

    button.addEventListener("click", onClick);

    return button;
}

// =============================================
// 7. HIỂN THỊ DANH SÁCH SẢN PHẨM
// =============================================
function renderProducts() {
    productList.replaceChildren();

    const keyword = searchInput.value.trim().toLowerCase();

    // Không hiển thị sản phẩm đã xóa trong danh sách chính
    const filteredProducts = products.filter(p =>
        p.status !== "Đã xóa" &&
        [
            p.id,
            p.name,
            p.brand,
            p.type,
            p.gender
        ].some(value =>
            String(value).toLowerCase().includes(keyword)
        )
    );

    if (filteredProducts.length === 0) {
        const tr = document.createElement("tr");
        const td = document.createElement("td");

        td.colSpan = 8;
        td.textContent = keyword
            ? "Không tìm thấy sản phẩm phù hợp."
            : "Chưa có sản phẩm nào.";

        td.style.textAlign = "center";
        td.style.padding = "20px";

        tr.appendChild(td);
        productList.appendChild(tr);
        return;
    }

    filteredProducts.forEach(p => {
        const tr = document.createElement("tr");

        const values = [
            p.id,
            p.name,
            p.brand,
            p.type,
            p.gender,
            formatPrice(p.price),
            p.status
        ];

        values.forEach((value, index) => {
            const td = document.createElement("td");
            td.textContent = value;

            if (index === 5) {
                td.className = "product-price";
            }

            if (index === 6) {
                td.className = p.status === "Hiển thị"
                    ? "visible-status"
                    : "hidden-status";
            }

            tr.appendChild(td);
        });

        // Cột thao tác
        const actions = document.createElement("td");

        const editButton = createButton(
            "Sửa",
            () => editProduct(p.id)
        );

        const toggleButton = createButton(
            p.status === "Hiển thị" ? "Ẩn" : "Hiện",
            () => toggleProduct(p.id)
        );

        const deleteButton = createButton(
            "Xóa",
            () => deleteProduct(p.id)
        );

        actions.append(
            editButton,
            toggleButton,
            deleteButton
        );

        tr.appendChild(actions);
        productList.appendChild(tr);
    });
}

// =============================================
// 8. KIỂM TRA DỮ LIỆU NHẬP
// =============================================
function validateProduct() {
    const name = fields.name.value.trim();
    const brand = fields.brand.value;
    const type = fields.type.value;
    const gender = fields.gender.value;
    const rawPrice = fields.price.value.trim();
    const price = Number(rawPrice);

    if (!name || !brand || !type || !gender || !rawPrice) {
        showMessage("Vui lòng nhập đầy đủ thông tin.", "error");
        return null;
    }

    if (!Number.isSafeInteger(price) || price <= 0) {
        showMessage(
            "Giá bán phải là số nguyên lớn hơn 0.",
            "error"
        );
        return null;
    }

    return {
        name,
        brand,
        type,
        gender,
        price
    };
}

// =============================================
// 9. THÊM VÀ CẬP NHẬT SẢN PHẨM
// =============================================
form.addEventListener("submit", function(event) {
    event.preventDefault();

    const data = validateProduct();

    if (!data) return;

    const id = fields.id.value;

    if (id) {
        // Cập nhật sản phẩm
        const product = products.find(p => p.id === id);

        if (!product || product.status === "Đã xóa") {
            showMessage(
                "Không tìm thấy sản phẩm cần sửa.",
                "error"
            );
            return;
        }

        Object.assign(product, data);

        if (!saveData()) return;

        showMessage("Cập nhật sản phẩm thành công.");
    } else {
        // Thêm sản phẩm mới
        const newProduct = {
            id: createProductId(),
            ...data,
            status: "Hiển thị"
        };

        products.push(newProduct);

        if (!saveData()) {
            products.pop();
            return;
        }

        showMessage("Thêm sản phẩm thành công.");
    }

    resetForm();
    renderProducts();
});

// =============================================
// 10. TẠO MÃ SẢN PHẨM
// =============================================
function createProductId() {
    let id;

    do {
        id = "SP" + Date.now().toString() +
            Math.random().toString(36).slice(2, 6).toUpperCase();
    } while (products.some(p => p.id === id));

    return id;
}

// =============================================
// 11. SỬA SẢN PHẨM
// =============================================
function editProduct(id) {
    const p = products.find(item => item.id === id);

    if (!p || p.status === "Đã xóa") {
        showMessage(
            "Sản phẩm không tồn tại hoặc đã bị xóa.",
            "error"
        );
        return;
    }

    fields.id.value = p.id;
    fields.name.value = p.name;
    fields.brand.value = p.brand;
    fields.type.value = p.type;
    fields.gender.value = p.gender;
    fields.price.value = p.price;

    saveButton.textContent = "Lưu thay đổi";
    cancelButton.hidden = false;

    showMessage("Đang sửa sản phẩm: " + p.name);

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}

// =============================================
// 12. ẨN HOẶC HIỆN SẢN PHẨM
// =============================================
function toggleProduct(id) {
    const p = products.find(item => item.id === id);

    if (!p || p.status === "Đã xóa") {
        showMessage("Không thể thay đổi sản phẩm này.", "error");
        return;
    }

    const oldStatus = p.status;

    p.status = oldStatus === "Hiển thị"
        ? "Ẩn"
        : "Hiển thị";

    if (!saveData()) {
        p.status = oldStatus;
        return;
    }

    renderProducts();

    showMessage(
        p.status === "Hiển thị"
            ? "Đã hiển thị sản phẩm."
            : "Đã ẩn sản phẩm."
    );
}

// =============================================
// 13. XÓA MỀM SẢN PHẨM
// =============================================
function deleteProduct(id) {
    const p = products.find(item => item.id === id);

    if (!p || p.status === "Đã xóa") return;

    const confirmed = confirm(
        `Bạn có chắc muốn chuyển "${p.name}" sang trạng thái Đã xóa?`
    );

    if (!confirmed) return;

    const oldStatus = p.status;
    p.status = "Đã xóa";

    if (!saveData()) {
        p.status = oldStatus;
        return;
    }

    // Nếu đang sửa sản phẩm vừa xóa, thoát chế độ sửa
    if (fields.id.value === p.id) {
        resetForm();
    }

    renderProducts();
    showMessage("Đã chuyển sản phẩm sang trạng thái Đã xóa.");
}

// =============================================
// 14. LÀM MỚI FORM
// =============================================
function resetForm() {
    form.reset();

    fields.id.value = "";
    saveButton.textContent = "Thêm sản phẩm";
    cancelButton.hidden = true;
}

// =============================================
// 15. HỦY SỬA
// =============================================
cancelButton.addEventListener("click", function() {
    resetForm();
    message.textContent = "";
    message.className = "";
});

// =============================================
// 16. TÌM KIẾM
// =============================================
searchInput.addEventListener("input", renderProducts);

// =============================================
// 17. KHỞI TẠO TRANG
// =============================================
renderProducts();
