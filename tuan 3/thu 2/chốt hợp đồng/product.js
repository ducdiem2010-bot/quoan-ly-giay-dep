
const form = document.getElementById("productForm");
const productList = document.getElementById("productList");
const message = document.getElementById("message");

const fields = {
    id: document.getElementById("productId"),
    name: document.getElementById("name"),
    brand: document.getElementById("brand"),
    type: document.getElementById("type"),
    gender: document.getElementById("gender"),
    price: document.getElementById("price")
};

let products = JSON.parse(
    localStorage.getItem("shoesProducts") || "[]"
);

function saveData() {
    localStorage.setItem("shoesProducts", JSON.stringify(products));
}

function renderProducts() {
    productList.replaceChildren();

    const keyword = document.getElementById("search").value
        .trim().toLowerCase();

    products
        .filter(p => p.name.toLowerCase().includes(keyword))
        .forEach(p => {
            const tr = document.createElement("tr");

            const values = [
                p.id,
                p.name,
                p.brand,
                p.type,
                p.gender,
                Number(p.price).toLocaleString("vi-VN") + " đ",
                p.status
            ];

            values.forEach((value, index) => {
                const td = document.createElement("td");
                td.textContent = value;

                if (index === 6) {
                    td.className = p.status === "Hiển thị"
                        ? "visible-status" : "hidden-status";
                }

                tr.appendChild(td);
            });

            const actions = document.createElement("td");

            const edit = document.createElement("button");
            edit.textContent = "Sửa";
            edit.onclick = () => editProduct(p.id);

            const toggle = document.createElement("button");
            toggle.textContent = p.status === "Hiển thị" ? "Ẩn" : "Hiện";
            toggle.style.marginLeft = "5px";
            toggle.onclick = () => toggleProduct(p.id);

            const remove = document.createElement("button");
            remove.textContent = "Xóa";
            remove.style.marginLeft = "5px";
            remove.onclick = () => deleteProduct(p.id);

            actions.append(edit, toggle, remove);
            tr.appendChild(actions);
            productList.appendChild(tr);
        });
}

form.addEventListener("submit", function(event) {
    event.preventDefault();
    message.textContent = "";

    const name = fields.name.value.trim();
    const brand = fields.brand.value;
    const type = fields.type.value;
    const gender = fields.gender.value;
    const price = Number(fields.price.value);

    if (!name || !brand || !type || !gender ||
        !Number.isSafeInteger(price) || price <= 0) {
        message.textContent = "Vui lòng nhập dữ liệu hợp lệ.";
        return;
    }

    const id = fields.id.value;

    if (id) {
        const product = products.find(p => p.id === id);
        if (!product) {
            message.textContent = "Không tìm thấy sản phẩm cần sửa.";
            return;
        }

        Object.assign(product, { name, brand, type, gender, price });
        message.textContent = "Cập nhật sản phẩm thành công.";
    } else {
        products.push({
            id: String(Date.now()) + Math.random().toString(36).slice(2, 6),
            name, brand, type, gender, price,
            status: "Hiển thị"
        });
        message.textContent = "Thêm sản phẩm thành công.";
    }

    saveData();
    form.reset();
    fields.id.value = "";
    document.getElementById("saveButton").textContent = "Thêm sản phẩm";
    document.getElementById("cancelButton").hidden = true;
    renderProducts();
});

function editProduct(id) {
    const p = products.find(item => item.id === id);
    if (!p) return;

    fields.id.value = p.id;
    fields.name.value = p.name;
    fields.brand.value = p.brand;
    fields.type.value = p.type;
    fields.gender.value = p.gender;
    fields.price.value = p.price;

    document.getElementById("saveButton").textContent = "Lưu thay đổi";
    document.getElementById("cancelButton").hidden = false;
    message.textContent = "Đang sửa sản phẩm: " + p.name;

    window.scrollTo({ top: 0, behavior: "smooth" });
}

function toggleProduct(id) {
    const p = products.find(item => item.id === id);
    if (!p) return;

    p.status = p.status === "Hiển thị" ? "Ẩn" : "Hiển thị";
    saveData();
    renderProducts();
}

function deleteProduct(id) {
    const p = products.find(item => item.id === id);
    if (!p) return;

    if (!confirm(
        `Bạn muốn chuyển "${p.name}" sang trạng thái Đã xóa?`
    )) return;

    // Xóa mềm: giữ lại bản ghi và trạng thái để bảo toàn dữ liệu.
    p.status = "Đã xóa";
    saveData();
    renderProducts();
}

document.getElementById("cancelButton").addEventListener("click", () => {
    form.reset();
    fields.id.value = "";
    document.getElementById("saveButton").textContent = "Thêm sản phẩm";
    document.getElementById("cancelButton").hidden = true;
    message.textContent = "";
});

document.getElementById("search").addEventListener("input", renderProducts);

renderProducts();
