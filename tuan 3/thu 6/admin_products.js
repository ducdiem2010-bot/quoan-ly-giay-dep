/**
 * ==========================================================================
 * SHOES STORE - ADMIN PRODUCTS JAVASCRIPT
 * Quản lý sản phẩm, biến thể (size, màu sắc) và ảnh đại diện
 * Kết nối linh hoạt giữa REST API Backend và LocalStorage Offline
 * ==========================================================================
 */

document.addEventListener("DOMContentLoaded", function () {
    "use strict";

    // ======================================================================
    // 1. CẤU HÌNH & KHỞI TẠO CÁC PHẦN TỬ DOM
    // ======================================================================
    const STORAGE_KEY = "shoesStoreProducts";
    const SYNC_KEY_THU3 = "shoesProducts";
    const API_ENDPOINT = "/api/products";
    const PAGE_SIZE = 6;
    const MAX_IMAGE_SIZE = 5 * 1024 * 1024; // 5MB

    const $ = id => document.getElementById(id);

    const dom = {
        // Stats
        total: $("totalProducts"),
        active: $("activeProducts"),
        hidden: $("hiddenProducts"),
        lowStock: $("lowStockProducts"),

        // Filters & Toolbar
        search: $("searchProduct"),
        brandFilter: $("filterBrand"),
        categoryFilter: $("filterCategory"),
        sort: $("sortProduct"),
        resetFilters: $("btnResetFilters"),
        resultCount: $("resultCount"),
        syncBackend: $("btnSyncBackend"),

        // Chế độ xem & Lưới sản phẩm
        btnViewGrid: $("btnViewGrid"),
        btnViewTable: $("btnViewTable"),
        productGrid: $("productGrid"),
        productTableWrapper: $("productTableWrapper"),

        // Table & Pagination
        tbody: $("productTableBody"),
        pageInfo: $("paginationInfo"),
        pageNumber: $("currentPage"),
        prevPage: $("btnPrevPage"),
        nextPage: $("btnNextPage"),

        // Backend Status
        backendStatusText: $("backendStatusText"),
        backendStatusDot: $("backendStatusDot"),

        // Main Modal
        addProductBtn: $("btnAddProduct"),
        modal: $("productModal"),
        modalTitle: $("modalTitle"),
        form: $("productForm"),
        closeModalBtn: $("btnCloseModal"),
        cancelModalBtn: $("btnCancelModal"),
        saveProductBtn: $("btnSaveProduct"),

        // Form Fields
        id: $("productId"),
        name: $("productName"),
        code: $("productCode"),
        brand: $("productBrand"),
        category: $("productCategory"),
        gender: $("productGender"),
        price: $("productPrice"),
        status: $("productStatus"),
        description: $("productDescription"),

        // Avatar Fields
        imageFile: $("productImageFile"),
        imageUrl: $("productImageUrl"),
        previewContent: $("imagePreviewContent"),
        previewBox: $("avatarPreviewBox"),
        presetBtns: document.querySelectorAll(".preset-btn"),

        // Variant Fields
        variantTableBody: $("variantTableBody"),
        btnAddVariantRow: $("btnAddVariantRow"),
        btnOpenQuickVariants: $("btnOpenQuickVariants"),
        totalVariantsCount: $("totalVariantsCount"),
        totalVariantsStock: $("totalVariantsStock"),

        // Quick Variant Modal
        quickModal: $("quickVariantModal"),
        closeQuickModalBtn: $("btnCloseQuickModal"),
        cancelQuickModalBtn: $("btnCancelQuickModal"),
        btnGenerateVariants: $("btnGenerateVariants"),
        sizeChips: $("sizeChips"),
        colorChips: $("colorChips"),
        customColorInput: $("customColorInput"),
        defaultStockInput: $("defaultStockInput"),
        defaultPriceInput: $("defaultPriceInput"),

        // View Variants Modal
        viewModal: $("viewVariantsModal"),
        viewTitle: $("viewVariantsTitle"),
        viewSubtitle: $("viewVariantsSubtitle"),
        viewBody: $("viewVariantsBody"),
        closeViewBtn: $("btnCloseViewVariants"),
        closeViewBtn2: $("btnCloseViewVariantsBtn"),

        // Toast
        toastContainer: $("toastContainer")
    };

    // ======================================================================
    // 2. STATE ỨNG DỤNG
    // ======================================================================
    let products = [];
    let currentPage = 1;
    let selectedAvatar = "";
    let backendMode = "local"; // "api" hoặc "local"
    let currentViewMode = "grid"; // Mặc định là ô vuông (grid) thay vì dạng dài
    let readerToken = 0;

    // Dữ liệu mẫu khởi tạo chuẩn khi chưa có dữ liệu
    const sampleProducts = [
        {
            id: "SP1001",
            name: "Nike Air Force 1 '07",
            brand: "Nike",
            category: "Giày thời trang",
            gender: "Unisex",
            price: 2690000,
            stock: 35,
            image: "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?auto=format&fit=crop&w=800&q=80",
            description: "Thiết kế huyền thoại với chất liệu da cao cấp màu trắng tinh tế, đệm khí Nike Air êm ái.",
            status: "active",
            createdAt: Date.now() - 500000,
            variants: [
                { id: "V1001-1", color: "Trắng", size: "39", stock: 8, price: 2690000, sku: "AF1-WHT-39" },
                { id: "V1001-2", color: "Trắng", size: "40", stock: 12, price: 2690000, sku: "AF1-WHT-40" },
                { id: "V1001-3", color: "Trắng", size: "41", stock: 10, price: 2690000, sku: "AF1-WHT-41" },
                { id: "V1001-4", color: "Trắng", size: "42", stock: 5, price: 2690000, sku: "AF1-WHT-42" }
            ]
        },
        {
            id: "SP1002",
            name: "Adidas Ultraboost Light",
            brand: "Adidas",
            category: "Giày chạy bộ",
            gender: "Nam",
            price: 3200000,
            stock: 22,
            image: "https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?auto=format&fit=crop&w=800&q=80",
            description: "Dòng giày chạy hàng đầu của Adidas trang bị đệm Boost siêu nhẹ, êm ái và trợ lực vượt trội.",
            status: "active",
            createdAt: Date.now() - 400000,
            variants: [
                { id: "V1002-1", color: "Đen", size: "40", stock: 6, price: 3200000, sku: "UB-BLK-40" },
                { id: "V1002-2", color: "Đen", size: "41", stock: 8, price: 3200000, sku: "UB-BLK-41" },
                { id: "V1002-3", color: "Xám", size: "42", stock: 5, price: 3200000, sku: "UB-GRY-42" },
                { id: "V1002-4", color: "Xám", size: "43", stock: 3, price: 3200000, sku: "UB-GRY-43" }
            ]
        },
        {
            id: "SP1003",
            name: "Puma RS-X Reinvention",
            brand: "Puma",
            category: "Giày thể thao",
            gender: "Unisex",
            price: 1950000,
            stock: 18,
            image: "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=800&q=80",
            description: "Phong cách Chunky Sneaker hầm hố, phối màu bắt mắt cùng công nghệ đệm RS giảm chấn tối đa.",
            status: "active",
            createdAt: Date.now() - 300000,
            variants: [
                { id: "V1003-1", color: "Đỏ/Trắng", size: "39", stock: 4, price: 1950000, sku: "RSX-RED-39" },
                { id: "V1003-2", color: "Đỏ/Trắng", size: "40", stock: 6, price: 1950000, sku: "RSX-RED-40" },
                { id: "V1003-3", color: "Đỏ/Trắng", size: "41", stock: 8, price: 1950000, sku: "RSX-RED-41" }
            ]
        },
        {
            id: "SP1004",
            name: "Nike Jordan 1 Retro High",
            brand: "Jordan",
            category: "Giày thời trang",
            gender: "Unisex",
            price: 4500000,
            stock: 4,
            image: "https://images.unsplash.com/photo-1552346154-21d32810aba3?auto=format&fit=crop&w=800&q=80",
            description: "Huyền thoại bóng rổ đường phố với phối màu Chicago cổ điển, phiên bản giới hạn.",
            status: "active",
            createdAt: Date.now() - 200000,
            variants: [
                { id: "V1004-1", color: "Đỏ/Đen", size: "41", stock: 2, price: 4500000, sku: "AJ1-CHI-41" },
                { id: "V1004-2", color: "Đỏ/Đen", size: "42", stock: 2, price: 4500000, sku: "AJ1-CHI-42" }
            ]
        },
        {
            id: "SP1005",
            name: "Asics Gel-Kayano 29",
            brand: "Asics",
            category: "Giày chạy bộ",
            gender: "Nam",
            price: 2890000,
            stock: 14,
            image: "https://images.unsplash.com/photo-1539185441755-769473a23570?auto=format&fit=crop&w=800&q=80",
            description: "Hỗ trợ ổn định bàn chân tối đa cho người chạy cự ly dài với công nghệ FF BLAST PLUS và GEL.",
            status: "hidden",
            createdAt: Date.now() - 100000,
            variants: [
                { id: "V1005-1", color: "Xanh dương", size: "41", stock: 7, price: 2890000, sku: "GEL-BLU-41" },
                { id: "V1005-2", color: "Xanh dương", size: "42", stock: 7, price: 2890000, sku: "GEL-BLU-42" }
            ]
        }
    ];

    // ======================================================================
    // 3. CÁC HÀM TIỆN ÍCH (HELPERS)
    // ======================================================================
    function escapeHTML(str) {
        return String(str ?? "").replace(/[&<>"']/g, c => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        })[c]);
    }

    function formatPrice(number) {
        return Number(number || 0).toLocaleString("vi-VN") + " ₫";
    }

    function showToast(message, type = "success") {
        const toast = document.createElement("div");
        toast.className = `toast toast-${type}`;
        const icons = {
            success: "✓",
            error: "✕",
            warning: "⚠",
            info: "ℹ"
        };
        toast.innerHTML = `<span style="font-size:16px;">${icons[type] || "✓"}</span><span>${escapeHTML(message)}</span>`;
        dom.toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = "0";
            toast.style.transform = "translateX(50px)";
            toast.style.transition = "all 0.3s ease";
            setTimeout(() => toast.remove(), 300);
        }, 3200);
    }

    function generateCode() {
        return "SP" + Math.floor(1000 + Math.random() * 9000);
    }

    // ======================================================================
    // 4. BACKEND INTEGRATION LAYER (REST API + LOCALSTORAGE FALLBACK)
    // ======================================================================

    // Kiểm tra kết nối Backend REST API Server
    async function checkBackendConnection() {
        try {
            // Đặt timeout 1.5s để phản hồi nhanh
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 1500);

            const res = await fetch(API_ENDPOINT, {
                method: "GET",
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            if (res.ok) {
                const json = await res.json();
                backendMode = "api";
                dom.backendStatusText.textContent = "REST API Backend (Đã kết nối)";
                dom.backendStatusDot.className = "status-dot";
                if (Array.isArray(json.data) && json.data.length > 0) {
                    products = json.data;
                    saveToLocalStorage(products);
                } else {
                    // Nếu server rỗng, đồng bộ dữ liệu mẫu lên
                    await syncLocalToApi(products.length ? products : sampleProducts);
                }
                return;
            }
        } catch (err) {
            // Không kết nối được API server -> Chuyển sang LocalStorage Mode
        }

        backendMode = "local";
        dom.backendStatusText.textContent = "LocalStorage Mode (Lưu trữ trình duyệt)";
        dom.backendStatusDot.className = "status-dot local";
    }

    // Đồng bộ lên API Server khi server online
    async function syncLocalToApi(dataList) {
        for (const item of dataList) {
            try {
                await fetch(API_ENDPOINT, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(item)
                });
            } catch (e) {
                break;
            }
        }
    }

    // Đọc danh sách sản phẩm
    async function loadProducts() {
        // Đọc từ LocalStorage trước để render ngay
        try {
            const raw = localStorage.getItem(STORAGE_KEY);
            if (raw) {
                const parsed = JSON.parse(raw);
                if (Array.isArray(parsed) && parsed.length > 0) {
                    products = parsed;
                } else {
                    products = sampleProducts;
                    saveToLocalStorage(products);
                }
            } else {
                products = sampleProducts;
                saveToLocalStorage(products);
            }
        } catch (e) {
            products = sampleProducts;
        }

        renderAll();

        // Kiểm tra kết nối API server ngầm
        await checkBackendConnection();
        renderAll();
    }

    // Lưu vào LocalStorage và đồng bộ các tab khác
    function saveToLocalStorage(data) {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
            // Đồng bộ sang key của bài thực hành Thứ 3
            localStorage.setItem(SYNC_KEY_THU3, JSON.stringify(data));
            return true;
        } catch (error) {
            console.error("Lỗi ghi LocalStorage:", error);
            showToast("Bộ nhớ trình duyệt đầy. Hãy chọn ảnh có dung lượng nhỏ hơn.", "warning");
            return false;
        }
    }

    // Backend Save: Lưu sản phẩm (hỗ trợ cả REST API lẫn LocalStorage)
    async function saveProductBackend(product) {
        // 1. Lưu vào LocalStorage
        const existingIdx = products.findIndex(p => p.id === product.id);
        if (existingIdx !== -1) {
            products[existingIdx] = product;
        } else {
            products.unshift(product);
        }
        saveToLocalStorage(products);

        // 2. Nếu Backend REST API đang chạy, gửi request lưu lên server
        if (backendMode === "api") {
            try {
                const method = existingIdx !== -1 ? "PUT" : "POST";
                const url = existingIdx !== -1 ? `${API_ENDPOINT}/${product.id}` : API_ENDPOINT;

                const response = await fetch(url, {
                    method: method,
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(product)
                });

                if (response.ok) {
                    console.log("Đã đồng bộ lên REST API Server thành công");
                }
            } catch (err) {
                console.warn("Không gửi được lên REST API, đã lưu an toàn trong LocalStorage.");
            }
        }
    }

    // Backend Delete: Xóa sản phẩm
    async function deleteProductBackend(productId) {
        products = products.filter(p => p.id !== productId);
        saveToLocalStorage(products);

        if (backendMode === "api") {
            try {
                await fetch(`${API_ENDPOINT}/${productId}`, { method: "DELETE" });
            } catch (err) {
                console.warn("Lỗi xóa trên server:", err);
            }
        }
    }

    // ======================================================================
    // 5. QUẢN LÝ ẢNH ĐẠI DIỆN (AVATAR PREVIEW & UPLOAD)
    // ======================================================================
    function renderAvatarPreview(url) {
        selectedAvatar = url ? url.trim() : "";

        if (!selectedAvatar) {
            dom.previewContent.innerHTML = `
                <div style="color:var(--text-light); text-align:center;">
                    <div style="font-size:32px; margin-bottom:4px;">👟</div>
                    <span style="font-size:12px;">Chưa chọn ảnh</span>
                </div>
            `;
            return;
        }

        dom.previewContent.innerHTML = `
            <img src="${escapeHTML(selectedAvatar)}" alt="Ảnh đại diện">
            <button type="button" id="btnClearAvatar" style="position:absolute; bottom:8px; right:8px; padding:4px 8px; font-size:11px; background:rgba(220,38,38,0.85); color:#fff; border-radius:4px; font-weight:700;">
                Xóa ảnh
            </button>
        `;

        const clearBtn = $("btnClearAvatar");
        if (clearBtn) {
            clearBtn.addEventListener("click", function (e) {
                e.stopPropagation();
                clearAvatar();
            });
        }
    }

    function clearAvatar() {
        selectedAvatar = "";
        dom.imageFile.value = "";
        dom.imageUrl.value = "";
        renderAvatarPreview("");
    }

    // Chọn ảnh từ máy tính (Tự động đọc Base64)
    dom.imageFile.addEventListener("change", function () {
        const file = dom.imageFile.files[0];
        if (!file) return;

        if (!file.type.startsWith("image/")) {
            showToast("Vui lòng chọn file hình ảnh (JPG, PNG, WebP).", "error");
            dom.imageFile.value = "";
            return;
        }

        if (file.size > MAX_IMAGE_SIZE) {
            showToast("Kích thước ảnh không được vượt quá 5MB.", "error");
            dom.imageFile.value = "";
            return;
        }

        const currentToken = ++readerToken;
        const reader = new FileReader();

        reader.onload = function (e) {
            if (currentToken !== readerToken) return;
            selectedAvatar = e.target.result;
            dom.imageUrl.value = "";
            renderAvatarPreview(selectedAvatar);
            showToast("Đã chọn ảnh đại diện từ máy tính.", "info");
        };

        reader.onerror = () => showToast("Không đọc được file ảnh.", "error");
        reader.readAsDataURL(file);
    });

    // Dán URL ảnh trực tiếp
    dom.imageUrl.addEventListener("input", function () {
        readerToken++;
        dom.imageFile.value = "";
        const url = dom.imageUrl.value.trim();
        renderAvatarPreview(url);
    });

    // Chọn ảnh mẫu có sẵn
    dom.presetBtns.forEach(btn => {
        btn.addEventListener("click", function () {
            const url = this.dataset.url;
            dom.imageUrl.value = url;
            dom.imageFile.value = "";
            renderAvatarPreview(url);
            showToast(`Đã áp dụng ảnh mẫu ${this.textContent.trim()}`, "info");
        });
    });

    // ======================================================================
    // 6. QUẢN LÝ BIẾN THỂ (SIZE & MÀU SẮC) TRONG MODAL
    // ======================================================================

    // Cập nhật tổng số lượng tồn kho tự động từ các dòng biến thể
    function updateVariantsStockSummary() {
        const rows = dom.variantTableBody.querySelectorAll(".variant-row");
        let count = rows.length;
        let totalStock = 0;

        rows.forEach(row => {
            const stockInput = row.querySelector(".var-stock");
            const stockVal = Number(stockInput?.value) || 0;
            totalStock += stockVal;
        });

        dom.totalVariantsCount.textContent = count;
        dom.totalVariantsStock.textContent = totalStock;
    }

    // Thêm một dòng biến thể vào bảng
    function addVariantRow(data = {}) {
        const row = document.createElement("tr");
        row.className = "variant-row";

        const color = data.color || "Trắng";
        const size = data.size || "40";
        const stock = data.stock !== undefined ? data.stock : 10;
        const price = data.price !== undefined ? data.price : (Number(dom.price.value) || 0);
        const sku = data.sku || "";

        row.innerHTML = `
            <td>
                <input type="text" class="var-color" value="${escapeHTML(color)}" placeholder="Màu sắc" required>
            </td>
            <td>
                <input type="text" class="var-size" value="${escapeHTML(size)}" placeholder="39, 40, 41..." required>
            </td>
            <td>
                <input type="number" class="var-stock" min="0" value="${stock}" required>
            </td>
            <td>
                <input type="number" class="var-price" min="0" step="1000" value="${price}" placeholder="Giá bán">
            </td>
            <td style="text-align: center;">
                <button type="button" class="btn-remove-variant" title="Xóa biến thể này">✕</button>
            </td>
        `;

        // Lắng nghe sự kiện thay đổi tồn kho để cập nhật tổng
        const stockInput = row.querySelector(".var-stock");
        stockInput.addEventListener("input", updateVariantsStockSummary);

        // Sự kiện xóa dòng biến thể
        row.querySelector(".btn-remove-variant").addEventListener("click", () => {
            row.remove();
            updateVariantsStockSummary();
        });

        dom.variantTableBody.appendChild(row);
        updateVariantsStockSummary();
    }

    // Mở modal tạo nhanh biến thể
    dom.btnOpenQuickVariants.addEventListener("click", () => {
        dom.quickModal.classList.add("show");
        dom.quickModal.setAttribute("aria-hidden", "false");
    });

    function closeQuickModal() {
        dom.quickModal.classList.remove("show");
        dom.quickModal.setAttribute("aria-hidden", "true");
    }

    dom.closeQuickModalBtn.addEventListener("click", closeQuickModal);
    dom.cancelQuickModalBtn.addEventListener("click", closeQuickModal);

    // Xử lý tạo danh sách biến thể tự động từ kích thước và màu đã chọn
    dom.btnGenerateVariants.addEventListener("click", () => {
        const checkedSizes = Array.from(
            dom.sizeChips.querySelectorAll("input[type='checkbox']:checked")
        ).map(cb => cb.value);

        const checkedColors = Array.from(
            dom.colorChips.querySelectorAll("input[type='checkbox']:checked")
        ).map(cb => cb.value);

        const customColor = dom.customColorInput.value.trim();
        if (customColor && !checkedColors.includes(customColor)) {
            checkedColors.push(customColor);
        }

        if (checkedSizes.length === 0) {
            showToast("Vui lòng chọn ít nhất 1 kích cỡ (Size).", "warning");
            return;
        }

        if (checkedColors.length === 0) {
            showToast("Vui lòng chọn hoặc nhập ít nhất 1 màu sắc.", "warning");
            return;
        }

        const defaultStock = Math.max(0, Number(dom.defaultStockInput.value) || 0);
        const defaultPrice = Number(dom.defaultPriceInput.value) || Number(dom.price.value) || 0;

        let addedCount = 0;
        checkedColors.forEach(color => {
            checkedSizes.forEach(size => {
                addVariantRow({
                    color: color,
                    size: size,
                    stock: defaultStock,
                    price: defaultPrice
                });
                addedCount++;
            });
        });

        closeQuickModal();
        showToast(`Đã tự động tạo thêm ${addedCount} biến thể!`, "success");
    });

    // Thêm 1 dòng biến thể đơn
    dom.btnAddVariantRow.addEventListener("click", () => {
        addVariantRow();
    });

    // Lấy danh sách biến thể từ bảng trong Modal
    function collectVariantsFromTable() {
        const rows = dom.variantTableBody.querySelectorAll(".variant-row");
        const list = [];

        rows.forEach((row, idx) => {
            const color = row.querySelector(".var-color")?.value.trim() || "Tiêu chuẩn";
            const size = row.querySelector(".var-size")?.value.trim() || "Free";
            const stock = Math.max(0, Number(row.querySelector(".var-stock")?.value) || 0);
            const price = Number(row.querySelector(".var-price")?.value) || Number(dom.price.value) || 0;
            const code = dom.code.value.trim() || "SP";

            list.push({
                id: `V-${Date.now().toString().slice(-4)}-${idx + 1}`,
                color: color,
                size: size,
                stock: stock,
                price: price,
                sku: `${code}-${size}-${color.slice(0, 3).toUpperCase()}`
            });
        });

        return list;
    }

    // ======================================================================
    // 7. RENDER BẢNG DỮ LIỆU & THỐNG KÊ
    // ======================================================================
    function renderStats() {
        dom.total.textContent = products.length;
        dom.active.textContent = products.filter(p => p.status === "active").length;
        dom.hidden.textContent = products.filter(p => p.status === "hidden").length;
        dom.lowStock.textContent = products.filter(p => {
            const stock = Number(p.stock) || 0;
            return p.status === "active" && stock <= 5;
        }).length;
    }

    function getFilteredProducts() {
        const query = dom.search.value.trim().toLowerCase();
        const brand = dom.brandFilter.value;
        const category = dom.categoryFilter.value;
        const sort = dom.sort.value;

        let result = products.filter(p => {
            // Tìm theo tên, mã sản phẩm
            const matchQuery = !query ||
                p.name.toLowerCase().includes(query) ||
                (p.id && p.id.toLowerCase().includes(query)) ||
                (p.variants && p.variants.some(v =>
                    v.size.toLowerCase().includes(query) ||
                    v.color.toLowerCase().includes(query)
                ));

            const matchBrand = !brand || p.brand === brand;
            const matchCategory = !category || p.category === category;

            return matchQuery && matchBrand && matchCategory;
        });

        // Sắp xếp
        switch (sort) {
            case "nameAsc":
                result.sort((a, b) => a.name.localeCompare(b.name, "vi"));
                break;
            case "priceAsc":
                result.sort((a, b) => a.price - b.price);
                break;
            case "priceDesc":
                result.sort((a, b) => b.price - a.price);
                break;
            case "stockAsc":
                result.sort((a, b) => (a.stock || 0) - (b.stock || 0));
                break;
            case "stockDesc":
                result.sort((a, b) => (b.stock || 0) - (a.stock || 0));
                break;
            default:
                result.sort((a, b) => (b.createdAt || 0) - (a.createdAt || 0));
        }

        return result;
    }

    function renderProductsDisplay() {
        const filtered = getFilteredProducts();
        const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));

        currentPage = Math.min(currentPage, totalPages);
        const start = (currentPage - 1) * PAGE_SIZE;
        const currentItems = filtered.slice(start, start + PAGE_SIZE);

        dom.resultCount.textContent = `${filtered.length} sản phẩm`;
        dom.pageNumber.textContent = currentPage;
        dom.pageInfo.textContent = filtered.length
            ? `Hiển thị ${start + 1}–${Math.min(start + PAGE_SIZE, filtered.length)} / ${filtered.length} sản phẩm`
            : "Không tìm thấy sản phẩm nào";

        dom.prevPage.disabled = currentPage <= 1;
        dom.nextPage.disabled = currentPage >= totalPages;

        // CHẾ ĐỘ 1: DẠNG Ô VUÔNG (GRID VIEW) - MẶC ĐỊNH
        if (currentViewMode === "grid") {
            if (dom.productGrid) dom.productGrid.style.display = "grid";
            if (dom.productTableWrapper) dom.productTableWrapper.style.display = "none";

            if (currentItems.length === 0) {
                if (dom.productGrid) {
                    dom.productGrid.innerHTML = `
                        <div style="grid-column: 1 / -1; text-align:center; padding:40px; color:var(--text-muted);">
                            <div style="font-size:36px; margin-bottom:8px;">👟</div>
                            <h3>Không tìm thấy sản phẩm nào</h3>
                            <p>Thử tìm kiếm với từ khóa khác hoặc bấm "Xóa bộ lọc"</p>
                        </div>
                    `;
                }
                return;
            }

            if (dom.productGrid) {
                dom.productGrid.innerHTML = currentItems.map(p => {
                    const hasAvatar = p.image && p.image.trim() !== "";
                    const avatarHtml = hasAvatar
                        ? `<img src="${escapeHTML(p.image)}" alt="${escapeHTML(p.name)}">`
                        : `<span class="card-img-placeholder">👟</span>`;

                    const variants = Array.isArray(p.variants) ? p.variants : [];
                    const variantCount = variants.length;

                    let variantSummaryHtml = "";
                    if (variantCount > 0) {
                        const uniqueSizes = Array.from(new Set(variants.map(v => v.size))).slice(0, 3);
                        variantSummaryHtml = `
                            <div class="card-variants-row">
                                <button type="button" class="card-variant-btn" data-action="view-variants" data-id="${escapeHTML(p.id)}">
                                    📦 ${variantCount} biến thể
                                </button>
                                <span style="font-size:11px; color:var(--text-muted);">Size: ${uniqueSizes.join(", ")}</span>
                            </div>
                        `;
                    } else {
                        variantSummaryHtml = `
                            <div class="card-variants-row" style="background:transparent; border:none; padding:4px 0;">
                                <span style="font-size:11px; color:var(--text-light);">Chưa có biến thể</span>
                            </div>
                        `;
                    }

                    const stockVal = Number(p.stock) || 0;
                    const isStockLow = stockVal <= 5;
                    const toggleLabel = p.status === "active" ? "Ẩn" : "Hiện";

                    return `
                        <div class="product-card" data-id="${escapeHTML(p.id)}">
                            <!-- Ô VUÔNG CHỨA ẢNH ĐẠI DIỆN (TỶ LỆ 1:1) -->
                            <div class="card-img-wrapper">
                                ${avatarHtml}
                                <span class="card-brand-badge">${escapeHTML(p.brand || 'Giày')}</span>
                                <span class="card-status-badge ${p.status === 'active' ? 'active' : 'hidden'}">
                                    ${p.status === 'active' ? '● Đang bán' : '● Đang ẩn'}
                                </span>
                            </div>

                            <!-- THÔNG TIN PHÍA DƯỚI ẢNH ĐẠI DIỆN -->
                            <div class="card-body">
                                <div class="card-code">${escapeHTML(p.id)}</div>
                                <h3 class="card-title" title="${escapeHTML(p.name)}">${escapeHTML(p.name)}</h3>
                                <div class="card-meta">
                                    <span>${escapeHTML(p.category || 'Giày')}</span>
                                    <span>·</span>
                                    <span>${escapeHTML(p.gender || 'Unisex')}</span>
                                </div>

                                ${variantSummaryHtml}

                                <!-- GIÁ TIỀN PHÍA DƯỚI TO RÕ RÀNG -->
                                <div class="card-price-container">
                                    <div>
                                        <div class="card-price-label">Giá bán</div>
                                        <div class="card-price-val">${formatPrice(p.price)}</div>
                                    </div>
                                    <div class="card-stock-val ${isStockLow ? 'low' : ''}">
                                        Tồn: <strong>${stockVal} đôi</strong>
                                    </div>
                                </div>

                                <!-- CÁC NÚT THAO TÁC -->
                                <div class="card-actions-grid">
                                    <button type="button" class="card-btn edit" data-action="edit" data-id="${escapeHTML(p.id)}" title="Sửa sản phẩm">
                                        ✏️ Sửa
                                    </button>
                                    <button type="button" class="card-btn toggle" data-action="toggle" data-id="${escapeHTML(p.id)}" title="Ẩn/Hiện sản phẩm">
                                        ${toggleLabel}
                                    </button>
                                    <button type="button" class="card-btn delete" data-action="delete" data-id="${escapeHTML(p.id)}" title="Xóa sản phẩm">
                                        🗑️ Xóa
                                    </button>
                                </div>
                            </div>
                        </div>
                    `;
                }).join("");
            }
        }
        // CHẾ ĐỘ 2: DẠNG BẢNG DÀI (TABLE VIEW)
        else {
            if (dom.productGrid) dom.productGrid.style.display = "none";
            if (dom.productTableWrapper) dom.productTableWrapper.style.display = "block";

            if (currentItems.length === 0) {
                dom.tbody.innerHTML = `
                    <tr>
                        <td colspan="8" class="empty-state">
                            <div class="empty-icon">👟</div>
                            <h3>Không tìm thấy sản phẩm nào</h3>
                            <p>Thử tìm kiếm với từ khóa khác hoặc bấm "Xóa bộ lọc"</p>
                        </td>
                    </tr>
                `;
                return;
            }

            dom.tbody.innerHTML = currentItems.map(p => {
                const hasAvatar = p.image && p.image.trim() !== "";
                const avatarHtml = hasAvatar
                    ? `<img src="${escapeHTML(p.image)}" alt="${escapeHTML(p.name)}">`
                    : `<span class="product-thumb-placeholder">👟</span>`;

                const variants = Array.isArray(p.variants) ? p.variants : [];
                const variantCount = variants.length;

                // Tóm tắt biến thể
                let variantHtml = "";
                if (variantCount > 0) {
                    const uniqueSizes = Array.from(new Set(variants.map(v => v.size))).slice(0, 4);
                    const uniqueColors = Array.from(new Set(variants.map(v => v.color))).slice(0, 2);

                    variantHtml = `
                        <div class="variant-cell-box">
                            <button type="button" class="variant-count-badge" data-action="view-variants" data-id="${escapeHTML(p.id)}" title="Nhấn để xem chi tiết các biến thể">
                                📦 ${variantCount} biến thể
                            </button>
                            <div class="variant-chips-summary">
                                ${uniqueSizes.map(s => `<span class="variant-chip">Sz ${escapeHTML(s)}</span>`).join("")}
                                ${uniqueColors.map(c => `<span class="variant-chip" style="background:#e0f2fe; color:#0369a1;">${escapeHTML(c)}</span>`).join("")}
                            </div>
                        </div>
                    `;
                } else {
                    variantHtml = `<span style="color:var(--text-light); font-size:12px;">Chưa có biến thể</span>`;
                }

                const stockVal = Number(p.stock) || 0;
                const stockClass = stockVal <= 5 ? "stock-low" : "stock-val";
                const stockBadge = stockVal === 0 ? '<small style="color:var(--danger); display:block;">(Hết hàng)</small>' : '';

                const statusHtml = p.status === "active"
                    ? `<span class="status-badge active"><span style="font-size:8px;">●</span> Đang bán</span>`
                    : `<span class="status-badge hidden"><span style="font-size:8px;">●</span> Đang ẩn</span>`;

                const toggleLabel = p.status === "active" ? "Ẩn" : "Hiện";

                return `
                    <tr>
                        <td>
                            <div class="product-cell">
                                <div class="product-thumb">
                                    ${avatarHtml}
                                </div>
                                <div class="product-cell-info">
                                    <div class="product-name">${escapeHTML(p.name)}</div>
                                    <div class="product-meta">
                                        <span>${escapeHTML(p.category || "Giày")}</span>
                                        <span>·</span>
                                        <span>${escapeHTML(p.gender || "Unisex")}</span>
                                    </div>
                                </div>
                            </div>
                        </td>
                        <td>
                            <span class="product-code">${escapeHTML(p.id)}</span>
                        </td>
                        <td>
                            <strong>${escapeHTML(p.brand || "Khác")}</strong>
                        </td>
                        <td>
                            <span class="product-price">${formatPrice(p.price)}</span>
                        </td>
                        <td>
                            ${variantHtml}
                        </td>
                        <td>
                            <span class="${stockClass}">${stockVal} đôi</span>
                            ${stockBadge}
                        </td>
                        <td>
                            ${statusHtml}
                        </td>
                        <td>
                            <div class="action-group">
                                <button type="button" class="action-btn edit-action" data-action="edit" data-id="${escapeHTML(p.id)}" title="Chỉnh sửa sản phẩm">
                                    Sửa
                                </button>
                                <button type="button" class="action-btn toggle-action" data-action="toggle" data-id="${escapeHTML(p.id)}" title="Bật/Tắt hiển thị">
                                    ${toggleLabel}
                                </button>
                                <button type="button" class="action-btn delete-action" data-action="delete" data-id="${escapeHTML(p.id)}" title="Xóa sản phẩm">
                                    Xóa
                                </button>
                            </div>
                        </td>
                    </tr>
                `;
            }).join("");
        }
    }

    function renderAll() {
        renderStats();
        renderProductsDisplay();
    }

    const renderTable = renderProductsDisplay;

    // ======================================================================
    // 8. XỬ LÝ MODAL THÊM / CẬP NHẬT SẢN PHẨM & BIẾN THỂ
    // ======================================================================
    function openProductModal(product = null) {
        dom.form.reset();
        dom.variantTableBody.innerHTML = "";
        clearAvatar();

        if (product) {
            dom.modalTitle.textContent = "Cập nhật sản phẩm & biến thể";
            dom.saveProductBtn.textContent = "💾 Cập nhật thay đổi";

            dom.id.value = product.id;
            dom.name.value = product.name || "";
            dom.code.value = product.id || "";
            dom.brand.value = product.brand || "";
            dom.category.value = product.category || "";
            dom.gender.value = product.gender || "Unisex";
            dom.price.value = product.price || "";
            dom.status.value = product.status || "active";
            dom.description.value = product.description || "";

            // Nạp ảnh đại diện
            if (product.image) {
                dom.imageUrl.value = product.image.startsWith("data:") ? "" : product.image;
                renderAvatarPreview(product.image);
            }

            // Nạp biến thể hiện có
            if (Array.isArray(product.variants) && product.variants.length > 0) {
                product.variants.forEach(v => addVariantRow(v));
            } else {
                // Tạo sẵn 2 dòng biến thể mẫu nếu chưa có
                addVariantRow({ color: "Trắng", size: "40", stock: 10, price: product.price });
                addVariantRow({ color: "Trắng", size: "41", stock: 10, price: product.price });
            }
        } else {
            dom.modalTitle.textContent = "Thêm sản phẩm mới";
            dom.saveProductBtn.textContent = "💾 Lưu sản phẩm & biến thể";
            dom.id.value = "";
            dom.code.value = generateCode();
            dom.status.value = "active";

            // Tạo sẵn 3 biến thể mẫu cho người dùng dễ hình dung
            addVariantRow({ color: "Trắng", size: "39", stock: 5 });
            addVariantRow({ color: "Trắng", size: "40", stock: 10 });
            addVariantRow({ color: "Trắng", size: "41", stock: 10 });
        }

        dom.modal.classList.add("show");
        dom.modal.setAttribute("aria-hidden", "false");
        document.body.style.overflow = "hidden";
        dom.name.focus();
    }

    function closeProductModal() {
        dom.modal.classList.remove("show");
        dom.modal.setAttribute("aria-hidden", "true");
        document.body.style.overflow = "";
        dom.form.reset();
        clearAvatar();
    }

    dom.addProductBtn.addEventListener("click", () => openProductModal());
    dom.closeModalBtn.addEventListener("click", closeProductModal);
    dom.cancelModalBtn.addEventListener("click", closeProductModal);

    dom.modal.addEventListener("click", e => {
        if (e.target === dom.modal) closeProductModal();
    });

    // ======================================================================
    // 9. XỬ LÝ LƯU SẢN PHẨM, BIẾN THỂ VÀ ẢNH ĐẠI DIỆN
    // ======================================================================
    dom.form.addEventListener("submit", async function (event) {
        event.preventDefault();

        const id = dom.id.value.trim() || dom.code.value.trim() || generateCode();
        const name = dom.name.value.trim();
        const brand = dom.brand.value;
        const category = dom.category.value;
        const gender = dom.gender.value;
        const price = Number(dom.price.value);
        const status = dom.status.value;
        const description = dom.description.value.trim();

        // Kiểm tra dữ liệu bắt buộc
        if (!name || !brand || !category) {
            showToast("Vui lòng nhập đầy đủ tên sản phẩm, thương hiệu và danh mục.", "error");
            return;
        }

        if (isNaN(price) || price <= 0) {
            showToast("Giá bán phải là số lớn hơn 0.", "error");
            return;
        }

        // Lấy danh sách biến thể từ bảng
        const variants = collectVariantsFromTable();

        // Tính toán tổng tồn kho
        let totalStock = 0;
        if (variants.length > 0) {
            totalStock = variants.reduce((sum, v) => sum + v.stock, 0);
        }

        // Ảnh đại diện (từ file upload hoặc URL dán vào)
        const finalAvatar = selectedAvatar || dom.imageUrl.value.trim() || "";

        const existing = products.find(p => p.id === id);

        const productData = {
            id: id,
            name: name,
            brand: brand,
            category: category,
            gender: gender,
            price: price,
            stock: totalStock,
            image: finalAvatar, // Lưu ảnh đại diện
            description: description,
            status: status,
            createdAt: existing ? existing.createdAt : Date.now(),
            updatedAt: Date.now(),
            variants: variants // Lưu danh sách biến thể
        };

        // Vô hiệu hóa nút trong khi lưu
        dom.saveProductBtn.disabled = true;
        dom.saveProductBtn.textContent = "⏳ Đang lưu...";

        try {
            await saveProductBackend(productData);
            closeProductModal();
            renderAll();
            showToast(existing ? "Cập nhật sản phẩm, biến thể và ảnh đại diện thành công!" : "Thêm mới sản phẩm, biến thể và ảnh đại diện thành công!", "success");
        } catch (err) {
            showToast("Có lỗi xảy ra khi lưu: " + err.message, "error");
        } finally {
            dom.saveProductBtn.disabled = false;
            dom.saveProductBtn.textContent = "💾 Lưu sản phẩm & biến thể";
        }
    });

    // ======================================================================
    // 10. THAO TÁC TRÊN SẢN PHẨM (SỬA, ẨN/HIỆN, XÓA, XEM BIẾN THỂ)
    // Hỗ trợ cả 2 chế độ: Lưới Ô vuông và Bảng danh sách
    // ======================================================================
    async function handleProductAction(event) {
        const targetBtn = event.target.closest("[data-action]");
        if (!targetBtn) return;

        const action = targetBtn.dataset.action;
        const productId = targetBtn.dataset.id;
        const product = products.find(p => p.id === productId);

        if (!product) return;

        // 1. Sửa sản phẩm
        if (action === "edit") {
            openProductModal(product);
            return;
        }

        // 2. Bật/Tắt ẩn hiện
        if (action === "toggle") {
            const nextStatus = product.status === "active" ? "hidden" : "active";
            const confirmMsg = nextStatus === "hidden"
                ? `Bạn có chắc muốn ẩn sản phẩm "${product.name}" khỏi cửa hàng?`
                : `Hiển thị lại sản phẩm "${product.name}"?`;

            if (confirm(confirmMsg)) {
                product.status = nextStatus;
                await saveProductBackend(product);
                renderAll();
                showToast(nextStatus === "hidden" ? "Đã ẩn sản phẩm." : "Đã bật hiển thị sản phẩm.", "info");
            }
            return;
        }

        // 3. Xóa sản phẩm
        if (action === "delete") {
            if (confirm(`Bạn có chắc chắn muốn xóa vĩnh viễn sản phẩm "${product.name}" và toàn bộ biến thể liên quan?`)) {
                await deleteProductBackend(productId);
                renderAll();
                showToast(`Đã xóa sản phẩm "${product.name}".`, "success");
            }
            return;
        }

        // 4. Xem chi tiết các biến thể của sản phẩm
        if (action === "view-variants") {
            openViewVariantsModal(product);
            return;
        }
    }

    if (dom.tbody) dom.tbody.addEventListener("click", handleProductAction);
    if (dom.productGrid) dom.productGrid.addEventListener("click", handleProductAction);

    // Chuyển đổi giữa chế độ Ô vuông (Mặc định) và Bảng dài
    if (dom.btnViewGrid) {
        dom.btnViewGrid.addEventListener("click", () => {
            currentViewMode = "grid";
            dom.btnViewGrid.classList.add("active");
            if (dom.btnViewTable) dom.btnViewTable.classList.remove("active");
            renderProductsDisplay();
        });
    }

    if (dom.btnViewTable) {
        dom.btnViewTable.addEventListener("click", () => {
            currentViewMode = "table";
            dom.btnViewTable.classList.add("active");
            if (dom.btnViewGrid) dom.btnViewGrid.classList.remove("active");
            renderProductsDisplay();
        });
    }

    // Modal xem chi tiết biến thể
    function openViewVariantsModal(product) {
        dom.viewTitle.textContent = `Biến thể: ${product.name}`;
        dom.viewSubtitle.textContent = `Mã SP: ${product.id} · Thương hiệu: ${product.brand} · Giá gốc: ${formatPrice(product.price)}`;

        const variants = Array.isArray(product.variants) ? product.variants : [];

        if (variants.length === 0) {
            dom.viewBody.innerHTML = `
                <div style="text-align:center; padding:30px; color:var(--text-muted);">
                    <p>Sản phẩm này chưa được thiết lập biến thể riêng.</p>
                </div>
            `;
        } else {
            dom.viewBody.innerHTML = `
                <table class="variants-table" style="width:100%; border:1px solid var(--border); border-radius:var(--radius-md);">
                    <thead>
                        <tr>
                            <th>MÃ SKU</th>
                            <th>MÀU SẮC</th>
                            <th>SIZE</th>
                            <th>GIÁ BÁN</th>
                            <th>TỒN KHO</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${variants.map(v => `
                            <tr>
                                <td><code>${escapeHTML(v.sku || `${product.id}-${v.size}`)}</code></td>
                                <td><strong>${escapeHTML(v.color)}</strong></td>
                                <td><span class="variant-chip">Size ${escapeHTML(v.size)}</span></td>
                                <td style="color:var(--primary); font-weight:700;">${formatPrice(v.price || product.price)}</td>
                                <td><strong style="color:${v.stock <= 3 ? 'var(--danger)' : 'var(--text-primary)'};">${v.stock} đôi</strong></td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
                <div style="margin-top:14px; text-align:right; font-weight:600; color:var(--text-secondary);">
                    Tổng cộng: <strong>${variants.length} biến thể</strong> · Tổng tồn kho: <strong>${product.stock} đôi</strong>
                </div>
            `;
        }

        dom.viewModal.classList.add("show");
        dom.viewModal.setAttribute("aria-hidden", "false");
    }

    function closeViewVariantsModal() {
        dom.viewModal.classList.remove("show");
        dom.viewModal.setAttribute("aria-hidden", "true");
    }

    dom.closeViewBtn.addEventListener("click", closeViewVariantsModal);
    dom.closeViewBtn2.addEventListener("click", closeViewVariantsModal);

    // ======================================================================
    // 11. BỘ LỌC, TÌM KIẾM & PHÂN TRANG
    // ======================================================================
    function applyFilterAndResetPage() {
        currentPage = 1;
        renderTable();
    }

    dom.search.addEventListener("input", applyFilterAndResetPage);
    dom.brandFilter.addEventListener("change", applyFilterAndResetPage);
    dom.categoryFilter.addEventListener("change", applyFilterAndResetPage);
    dom.sort.addEventListener("change", applyFilterAndResetPage);

    dom.resetFilters.addEventListener("click", () => {
        dom.search.value = "";
        dom.brandFilter.value = "";
        dom.categoryFilter.value = "";
        dom.sort.value = "newest";
        currentPage = 1;
        renderTable();
        showToast("Đã thiết lập lại toàn bộ bộ lọc.");
    });

    dom.prevPage.addEventListener("click", () => {
        if (currentPage > 1) {
            currentPage--;
            renderTable();
        }
    });

    dom.nextPage.addEventListener("click", () => {
        const filtered = getFilteredProducts();
        const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
        if (currentPage < totalPages) {
            currentPage++;
            renderTable();
        }
    });

    // Đồng bộ lại backend
    dom.syncBackend.addEventListener("click", async () => {
        dom.backendStatusText.textContent = "Đang kiểm tra kết nối...";
        await checkBackendConnection();
        showToast("Đã hoàn tất đồng bộ dữ liệu!", "success");
    });

    // Phím Esc đóng modal
    document.addEventListener("keydown", e => {
        if (e.key === "Escape") {
            if (dom.quickModal.classList.contains("show")) {
                closeQuickModal();
            } else if (dom.viewModal.classList.contains("show")) {
                closeViewVariantsModal();
            } else if (dom.modal.classList.contains("show")) {
                closeProductModal();
            }
        }
    });

    // ======================================================================
    // 12. KHỞI CHẠY ỨNG DỤNG
    // ======================================================================
    loadProducts();
});
