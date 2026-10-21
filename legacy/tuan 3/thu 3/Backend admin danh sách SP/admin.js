
const products = [
    { id: "SP01", name: "Nike Air Force 1", brand: "Nike", type: "Sneaker", gender: "Nam", price: 2200000, active: true },
    { id: "SP02", name: "Adidas Superstar", brand: "Adidas", type: "Sneaker", gender: "Unisex", price: 1800000, active: true },
    { id: "SP03", name: "Asics Gel Kayano", brand: "Asics", type: "Running", gender: "Nam", price: 2500000, active: true },
    { id: "SP04", name: "Puma Suede Classic", brand: "Puma", type: "Sneaker", gender: "Nam", price: 1500000, active: false },
    { id: "SP05", name: "Lacoste Court", brand: "Lacoste", type: "Sneaker", gender: "Unisex", price: 2100000, active: true },
    { id: "SP06", name: "Nike Dunk Low", brand: "Nike", type: "Sneaker", gender: "Unisex", price: 2400000, active: true },
    { id: "SP07", name: "Adidas Ultraboost", brand: "Adidas", type: "Running", gender: "Nam", price: 2800000, active: true }
];

// Demo quyền Admin trên giao diện.
// Khi kết nối backend, phải lấy quyền từ máy chủ.
let currentRole = "Admin";
let currentPage = 1;
const pageSize = 5;

const productList = document.getElementById("productList");
const searchInput = document.getElementById("searchInput");
const message = document.getElementById("message");

function canManage() {
    return currentRole === "Admin";
}

function formatPrice(price) {
    return price.toLocaleString("vi-VN") + " đ";
}

function getFilteredProducts() {
    const keyword = searchInput.value.trim().toLocaleLowerCase("vi");
    return products.filter(product =>
        product.name.toLocaleLowerCase("vi").includes(keyword)
    );
}

function renderProducts() {
    const filtered = getFilteredProducts();
    const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));

    currentPage = Math.min(currentPage, totalPages);

    const start = (currentPage - 1) * pageSize;
    const pageProducts = filtered.slice(start, start + pageSize);

    productList.innerHTML = "";

    if (pageProducts.length === 0) {
        productList.innerHTML = `
            <tr>
                <td colspan="8">Không tìm thấy sản phẩm.</td>
            </tr>`;
    }

    pageProducts.forEach(product => {
        const row = document.createElement("tr");

        const values = [
            product.id,
            product.name,
            product.brand,
            product.type,
            product.gender,
            formatPrice(product.price)
        ];

        values.forEach(value => {
            const cell = document.createElement("td");
            cell.textContent = value;
            row.appendChild(cell);
        });

        const statusCell = document.createElement("td");
        statusCell.textContent = product.active ? "Đang bán" : "Đã ẩn";
        statusCell.className = product.active ? "status" : "status hidden";
        row.appendChild(statusCell);

        const actionCell = document.createElement("td");

        if (canManage()) {
            const editBtn = document.createElement("button");
            editBtn.textContent = "Sửa";
            editBtn.className = "action-btn";
            editBtn.onclick = () => editProduct(product.id);

            const hideBtn = document.createElement("button");
            hideBtn.textContent = product.active ? "Ẩn" : "Hiện";
            hideBtn.className = "action-btn hide-btn";
            hideBtn.onclick = () => toggleProduct(product.id);

            actionCell.append(editBtn, hideBtn);
        } else {
            actionCell.textContent = "Chỉ xem";
        }

        row.appendChild(actionCell);
        productList.appendChild(row);
    });

    document.getElementById("pageInfo").textContent =
        `Trang ${currentPage}/${totalPages} — ${filtered.length} sản phẩm`;

    document.getElementById("prevBtn").disabled = currentPage <= 1;
    document.getElementById("nextBtn").disabled = currentPage >= totalPages;

    document.getElementById("addBtn").hidden = !canManage();
    document.getElementById("roleLabel").textContent =
        "Quyền: " + currentRole;
}

function editProduct(id) {
    if (!canManage()) {
        message.textContent = "Bạn không có quyền quản lý sản phẩm.";
        return;
    }

    const product = products.find(item => item.id === id);
    const name = prompt("Nhập tên sản phẩm:", product.name);

    if (name === null) return;

    if (!name.trim()) {
        message.textContent = "Tên sản phẩm không được để trống.";
        return;
    }

    product.name = name.trim();
    message.textContent = "Đã cập nhật tên sản phẩm (dữ liệu demo).";
    renderProducts();
}

function toggleProduct(id) {
    if (!canManage()) {
        message.textContent = "Bạn không có quyền quản lý sản phẩm.";
        return;
    }

    const product = products.find(item => item.id === id);
    product.active = !product.active;

    message.textContent = "Đã đổi trạng thái sản phẩm (dữ liệu demo).";
    renderProducts();
}

function addProduct() {
    if (!canManage()) {
        message.textContent = "Bạn không có quyền thêm sản phẩm.";
        return;
    }

    const name = prompt("Tên sản phẩm:");
    if (name === null) return;

    if (!name.trim()) {
        message.textContent = "Tên sản phẩm không được để trống.";
        return;
    }

    const brand = prompt("Thương hiệu:");
    if (brand === null) return;

    const type = prompt("Loại giày:");
    if (type === null) return;

    const priceText = prompt("Giá sản phẩm (VNĐ):");
    if (priceText === null) return;

    const price = Number(priceText);

    if (!brand.trim() || !type.trim() ||
        priceText.trim() === "" || !Number.isFinite(price) || price <= 0) {
        message.textContent = "Thương hiệu, loại và giá phải hợp lệ.";
        return;
    }

    const id = "SP" + String(
        Math.max(0, ...products.map(p =>
            Number(p.id.replace("SP", "")) || 0
        )) + 1
    ).padStart(2, "0");

    products.push({
        id,
        name: name.trim(),
        brand: brand.trim(),
        type: type.trim(),
        gender: "Nam",
        price,
        active: true
    });

    currentPage = 1;
    searchInput.value = "";
    message.textContent = "Đã thêm sản phẩm vào dữ liệu demo.";
    renderProducts();
}

document.getElementById("searchBtn").addEventListener("click", () => {
    currentPage = 1;
    message.textContent = "";
    renderProducts();
});

searchInput.addEventListener("input", () => {
    currentPage = 1;
    renderProducts();
});

document.getElementById("prevBtn").addEventListener("click", () => {
    if (currentPage > 1) {
        currentPage--;
        renderProducts();
    }
});

document.getElementById("nextBtn").addEventListener("click", () => {
    const totalPages = Math.max(
        1, Math.ceil(getFilteredProducts().length / pageSize)
    );

    if (currentPage < totalPages) {
        currentPage++;
        renderProducts();
    }
});

document.getElementById("addBtn").addEventListener("click", addProduct);

document.getElementById("logoutBtn").addEventListener("click", () => {
    window.location.href = "login.html";
});

renderProducts();
