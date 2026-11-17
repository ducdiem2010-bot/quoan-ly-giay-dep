
const STORAGE_KEY = "shoes_products";

const sampleProduct = {
    id: 1,
    name: "Nike Air Max",
    description: "Giày thể thao chính hãng",
    price: 2500000,
    brand: "Nike",
    type: "Thể thao",
    gender: "Nam",
    status: "Đang bán",
    variants: [
        { color: "Đen", size: 40 },
        { color: "Trắng", size: 41 }
    ]
};

let products = JSON.parse(
    localStorage.getItem(STORAGE_KEY) || "null"
);

if (!Array.isArray(products)) {
    products = [sampleProduct];
    localStorage.setItem(STORAGE_KEY, JSON.stringify(products));
}

const productId = Number(
    new URLSearchParams(location.search).get("id") || 1
);

const product = products.find(p => p.id === productId);
const form = document.getElementById("productForm");
const message = document.getElementById("message");

if (!product) {
    form.hidden = true;
    message.textContent = "Không tìm thấy sản phẩm.";
} else {
    document.getElementById("name").value = product.name;
    document.getElementById("description").value =
        product.description;
    document.getElementById("price").value = product.price;
    document.getElementById("brand").value = product.brand;
    document.getElementById("type").value = product.type;
    document.getElementById("gender").value = product.gender;
    document.getElementById("status").value = product.status;
}

form.addEventListener("submit", function (event) {
    event.preventDefault();

    if (!product) return;

    const name = document.getElementById("name").value.trim();
    const description =
        document.getElementById("description").value.trim();
    const priceInput = document.getElementById("price").value;
    const price = Number(priceInput);
    const brand = document.getElementById("brand").value;
    const type = document.getElementById("type").value;
    const gender = document.getElementById("gender").value;
    const status = document.getElementById("status").value;

    // Validate dữ liệu trước khi lưu
    if (!name || name.length > 150) {
        return showError("Tên sản phẩm phải có 1–150 ký tự.");
    }

    if (!description || description.length > 2000) {
        return showError("Mô tả không được trống hoặc quá 2000 ký tự.");
    }

    if (
        priceInput.trim() === "" ||
        !Number.isSafeInteger(price) ||
        price <= 0
    ) {
        return showError("Giá phải là số nguyên dương hợp lệ.");
    }

    if (!["Nike", "Adidas", "Puma", "Asics"].includes(brand)) {
        return showError("Thương hiệu không hợp lệ.");
    }

    if (!["Thể thao", "Chạy bộ", "Sneaker", "Giày da"].includes(type)) {
        return showError("Loại giày không hợp lệ.");
    }

    if (!["Nam", "Nữ", "Unisex"].includes(gender)) {
        return showError("Giới tính không hợp lệ.");
    }

    if (!["Đang bán", "Ngừng bán", "Ẩn"].includes(status)) {
        return showError("Trạng thái không hợp lệ.");
    }

    // Chỉ cập nhật các trường được phép sửa.
    // Không ghi đè id, variants hoặc giá riêng của màu/size.
    const updatedProduct = {
        ...product,
        name,
        description,
        price,
        brand,
        type,
        gender,
        status
    };

    const index = products.findIndex(p => p.id === productId);
    if (index === -1) {
        return showError("Sản phẩm không còn tồn tại.");
    }

    products[index] = updatedProduct;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(products));

    message.style.color = "green";
    message.textContent = "Sửa sản phẩm thành công!";
});

function showError(text) {
    message.style.color = "red";
    message.textContent = text;
}
