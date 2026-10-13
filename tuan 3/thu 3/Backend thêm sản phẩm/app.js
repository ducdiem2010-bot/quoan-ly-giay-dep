
const form = document.getElementById("productForm");
const message = document.getElementById("message");
const productList = document.getElementById("productList");

async function loadProducts() {
    try {
        const response = await fetch("/api/products");
        if (!response.ok) throw new Error("Không tải được sản phẩm");

        const products = await response.json();
        productList.replaceChildren();

        products.forEach(product => {
            const card = document.createElement("div");
            card.className = "product";

            const title = document.createElement("strong");
            title.textContent = product.name;

            const details = document.createElement("p");
            details.textContent =
                `${product.price.toLocaleString("vi-VN")} VNĐ | ` +
                `${product.brand} | ${product.type} | ` +
                `${product.gender} | ${product.status}`;

            const description = document.createElement("p");
            description.textContent = product.description;

            card.append(title, details, description);
            productList.appendChild(card);
        });
    } catch (error) {
        message.textContent = error.message;
    }
}

form.addEventListener("submit", async function (event) {
    event.preventDefault();
    message.textContent = "";

    const data = Object.fromEntries(new FormData(form).entries());
    data.price = Number(data.price);

    if (!data.name.trim() || !data.description.trim()) {
        message.textContent = "Vui lòng nhập đầy đủ tên và mô tả.";
        return;
    }

    if (!Number.isSafeInteger(data.price) || data.price <= 0) {
        message.textContent = "Giá phải là số nguyên dương hợp lệ.";
        return;
    }

    try {
        const response = await fetch("/api/products", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (!response.ok) {
            message.textContent = result.message ||
                (result.errors || []).join(", ") ||
                "Thêm sản phẩm thất bại.";
            return;
        }

        message.textContent = "Thêm sản phẩm thành công!";
        form.reset();
        await loadProducts();
    } catch (error) {
        message.textContent =
            "Không kết nối được server. Hãy kiểm tra Node.js.";
    }
});

loadProducts();
