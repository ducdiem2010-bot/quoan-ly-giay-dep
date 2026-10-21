
document.addEventListener("DOMContentLoaded", function () {
    "use strict";

    // ================================
    // 1. LẤY CÁC PHẦN TỬ HTML
    // ================================
    const searchInput = document.getElementById("searchInput");
    const searchBtn = document.getElementById("searchBtn");
    const addBtn = document.getElementById("addBtn");
    const productList = document.getElementById("productList");
    const message = document.getElementById("message");
    const pageInfo = document.getElementById("pageInfo");
    const prevBtn = document.getElementById("prevBtn");
    const nextBtn = document.getElementById("nextBtn");
    const logoutBtn = document.getElementById("logoutBtn");
    const roleLabel = document.getElementById("roleLabel");

    // ================================
    // 2. CẤU HÌNH
    // ================================
    const STORAGE_KEY = "shoesProducts";
    const PAGE_SIZE = 5;

    let currentPage = 1;
    let searchKeyword = "";

    // ================================
    // 3. DỮ LIỆU MẪU
    // Chỉ tạo dữ liệu mẫu khi chưa có dữ liệu
    // ================================
    function getSampleProducts() {
        return [
            {
                id: "SP001",
                name: "Nike Air Max",
                brand: "Nike",
                type: "Giày thể thao",
                gender: "Nam",
                price: 2500000,
                status: "Đang bán"
            },
            {
                id: "SP002",
                name: "Adidas Ultraboost",
                brand: "Adidas",
                type: "Giày chạy bộ",
                gender: "Nam",
                price: 3200000,
                status: "Đang bán"
            },
            {
                id: "SP003",
                name: "Puma Suede Classic",
                brand: "Puma",
                type: "Giày thời trang",
                gender: "Unisex",
                price: 1800000,
                status: "Đang bán"
            },
            {
                id: "SP004",
                name: "Asics Gel",
                brand: "Asics",
                type: "Giày chạy bộ",
                gender: "Nam",
                price: 2900000,
                status: "Đang bán"
            },
            {
                id: "SP005",
                name: "Lacoste Sneaker",
                brand: "Lacoste",
                type: "Giày thời trang",
                gender: "Nam",
                price: 2100000,
                status: "Đang bán"
            },
            {
                id: "SP006",
                name: "Nike Revolution",
                brand: "Nike",
                type: "Giày chạy bộ",
                gender: "Nữ",
                price: 1600000,
                status: "Đang bán"
            }
        ];
    }

    // ================================
    // 4. ĐỌC VÀ LƯU DỮ LIỆU
    // ================================
    function loadProducts() {
        try {
            const savedData = localStorage.getItem(STORAGE_KEY);

            if (savedData === null) {
                const sampleProducts = getSampleProducts();
                localStorage.setItem(
                    STORAGE_KEY,
                    JSON.stringify(sampleProducts)
                );
                return sampleProducts;
            }

            const products = JSON.parse(savedData);

            if (!Array.isArray(products)) {
                throw new Error("Dữ liệu sản phẩm không hợp lệ.");
            }

            return products;
        } catch (error) {
            console.error("Lỗi đọc sản phẩm:", error);
            showMessage(
                "Không đọc được dữ liệu sản phẩm trong trình duyệt.",
                "error"
            );
            return [];
        }
    }

    function saveProducts(products) {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(products));
            return true;
        } catch (error) {
            console.error("Lỗi lưu sản phẩm:", error);
            showMessage("Không thể lưu dữ liệu sản phẩm.", "error");
            return false;
        }
    }

    // ================================
    // 5. THÔNG BÁO
    // ================================
    function showMessage(text, type = "success") {
        if (!message) return;

        message.textContent = text;
        message.className = type === "error"
            ? "message error"
            : "message success";
    }

    function clearMessage() {
        if (!message) return;

        message.textContent = "";
        message.className = "";
    }

    // ================================
    // 6. ĐỊNH DẠNG GIÁ TIỀN
    // ================================
    function formatPrice(price) {
        return Number(price).toLocaleString("vi-VN") + " đ";
    }

    // ================================
    // 7. HIỂN THỊ DANH SÁCH
    // ================================
    function renderProducts() {
        const products = loadProducts();

        const filteredProducts = products.filter(function (product) {
            const keyword = searchKeyword.toLowerCase();

            const searchableText = [
                product.id,
                product.name,
                product.brand,
                product.type,
                product.gender
            ].join(" ").toLowerCase();

            // Ẩn các sản phẩm đã xóa mềm
            return product.status !== "Đã xóa"
                && searchableText.includes(keyword);
        });

        const totalPages = Math.max(
            1,
            Math.ceil(filteredProducts.length / PAGE_SIZE)
        );

        if (currentPage > totalPages) {
            currentPage = totalPages;
        }

        const startIndex = (currentPage - 1) * PAGE_SIZE;
        const pageProducts = filteredProducts.slice(
            startIndex,
            startIndex + PAGE_SIZE
        );

        productList.replaceChildren();

        if (pageProducts.length === 0) {
            const row = document.createElement("tr");
            const cell = document.createElement("td");

            cell.colSpan = 8;
            cell.textContent = "Không tìm thấy sản phẩm.";
            cell.style.textAlign = "center";
            cell.style.padding = "24px";

            row.appendChild(cell);
            productList.appendChild(row);
        } else {
            pageProducts.forEach(function (product) {
                const row = document.createElement("tr");

                appendCell(row, product.id);
                appendCell(row, product.name);
                appendCell(row, product.brand);
                appendCell(row, product.type);
                appendCell(row, product.gender);
                appendCell(row, formatPrice(product.price));

                const statusCell = document.createElement("td");
                const statusBadge = document.createElement("span");

                statusBadge.textContent = product.status || "Đang bán";
                statusBadge.className =
                    product.status === "Đang bán"
                        ? "status active"
                        : "status inactive";

                statusCell.appendChild(statusBadge);
                row.appendChild(statusCell);

                const actionCell = document.createElement("td");

                const editButton = createButton(
                    "Sửa",
                    "action-btn edit-btn",
                    function () {
                        editProduct(product.id);
                    }
                );

                const toggleButton = createButton(
                    product.status === "Đang bán" ? "Ẩn" : "Hiện",
                    "action-btn hide-btn",
                    function () {
                        toggleProduct(product.id);
                    }
                );

                const deleteButton = createButton(
                    "Xóa",
                    "action-btn delete-btn",
                    function () {
                        deleteProduct(product.id);
                    }
                );

                actionCell.append(
                    editButton,
                    document.createTextNode(" "),
                    toggleButton,
                    document.createTextNode(" "),
                    deleteButton
                );

                row.appendChild(actionCell);
                productList.appendChild(row);
            });
        }

        if (pageInfo) {
            pageInfo.textContent =
                `Trang ${currentPage}/${totalPages} · ` +
                `${filteredProducts.length} sản phẩm`;
        }

        if (prevBtn) prevBtn.disabled = currentPage <= 1;
        if (nextBtn) nextBtn.disabled = currentPage >= totalPages;
    }

    function appendCell(row, value) {
        const cell = document.createElement("td");
        cell.textContent = value ?? "";
        row.appendChild(cell);
    }

    function createButton(text, className, onClick) {
        const button = document.createElement("button");

        button.type = "button";
        button.textContent = text;
        button.className = className;
        button.addEventListener("click", onClick);

        return button;
    }

    // ================================
    // 8. TÌM KIẾM SẢN PHẨM
    // ================================
    function searchProducts() {
        searchKeyword = searchInput.value.trim();
        currentPage = 1;
        clearMessage();
        renderProducts();
    }

    searchBtn.addEventListener("click", searchProducts);

    searchInput.addEventListener("keydown", function (event) {
        if (event.key === "Enter") {
            searchProducts();
        }
    });

    searchInput.addEventListener("input", function () {
        if (searchInput.value.trim() === "") {
            searchKeyword = "";
            currentPage = 1;
            renderProducts();
        }
    });

    // ================================
    // 9. THÊM SẢN PHẨM
    // ================================
    addBtn.addEventListener("click", function () {
        window.location.href = "admin_product_add.html";
    });

    // ================================
    // 10. SỬA SẢN PHẨM
    // ================================
    function editProduct(productId) {
        const products = loadProducts();

        const product = products.find(function (item) {
            return item.id === productId;
        });

        if (!product) {
            showMessage("Không tìm thấy sản phẩm.", "error");
            return;
        }

        // Lưu sản phẩm cần sửa để trang form có thể đọc
        sessionStorage.setItem(
            "editingShoeProduct",
            JSON.stringify(product)
        );

        window.location.href = "admin_product_add.html";
    }

    // ================================
    // 11. ẨN / HIỆN SẢN PHẨM
    // ================================
    function toggleProduct(productId) {
        const products = loadProducts();

        const index = products.findIndex(function (item) {
            return item.id === productId;
        });

        if (index === -1) {
            showMessage("Không tìm thấy sản phẩm.", "error");
            return;
        }

        products[index].status =
            products[index].status === "Đang bán"
                ? "Đang ẩn"
                : "Đang bán";

        if (saveProducts(products)) {
            showMessage(
                products[index].status === "Đang bán"
                    ? "Đã hiển thị sản phẩm."
                    : "Đã ẩn sản phẩm."
            );
            renderProducts();
        }
    }

    // ================================
    // 12. XÓA MỀM SẢN PHẨM
    // ================================
    function deleteProduct(productId) {
        const confirmed = window.confirm(
            "Bạn có chắc muốn ẩn sản phẩm này khỏi danh sách không?"
        );

        if (!confirmed) return;

        const products = loadProducts();

        const index = products.findIndex(function (item) {
            return item.id === productId;
        });

        if (index === -1) {
            showMessage("Không tìm thấy sản phẩm.", "error");
            return;
        }

        // Không xóa dữ liệu vĩnh viễn
        products[index].status = "Đã xóa";

        if (saveProducts(products)) {
            showMessage("Đã xóa mềm sản phẩm.");
            renderProducts();
        }
    }

    // ================================
    // 13. PHÂN TRANG
    // ================================
    prevBtn.addEventListener("click", function () {
        if (currentPage > 1) {
            currentPage--;
            renderProducts();
        }
    });

    nextBtn.addEventListener("click", function () {
        currentPage++;
        renderProducts();
    });

    // ================================
    // 14. ĐĂNG XUẤT
    // ================================
    logoutBtn.addEventListener("click", function () {
        const confirmed = window.confirm("Bạn muốn đăng xuất?");

        if (!confirmed) return;

        // Xóa trạng thái đăng nhập demo.
        // Không xóa dữ liệu sản phẩm.
        sessionStorage.removeItem("loggedInUser");
        sessionStorage.removeItem("editingShoeProduct");

        window.location.href = "login.html";
    });

    // ================================
    // 15. HIỂN THỊ QUYỀN
    // ================================
    const currentUser = JSON.parse(
        sessionStorage.getItem("loggedInUser") || "null"
    );

    if (roleLabel && currentUser && currentUser.role) {
        roleLabel.textContent = "Quyền: " + currentUser.role;
    }

    // ================================
    // 16. KHỞI CHẠY
    // ================================
    renderProducts();
});
