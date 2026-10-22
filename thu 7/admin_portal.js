/**
 * ==========================================================================
 * SHOES STORE - BLACK & WHITE ADMIN PORTAL CONTROLLER
 * Quản trị Dashboard, Sản phẩm giày, Đơn hàng và Khách hàng
 * ==========================================================================
 */

(function () {
    "use strict";

    const PRODUCTS_KEY = "shoesProducts";
    const ORDERS_KEY = "shoesOrders";
    const CUSTOMERS_KEY = "shoesCustomers";
    const SESSION_KEY = "shoesAdminSession";

    // Danh sách sản phẩm mặc định
    const DEFAULT_PRODUCTS = [
        {
            id: "SP1001",
            name: "NIKE AIR FORCE 1 '07",
            brand: "NIKE",
            category: "THỜI TRANG",
            price: 2690000,
            stock: 35,
            image: "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?auto=format&fit=crop&w=800&q=80",
            status: "active",
            soldCount: 142
        },
        {
            id: "SP1002",
            name: "ADIDAS ULTRABOOST LIGHT",
            brand: "ADIDAS",
            category: "CHẠY BỘ",
            price: 3200000,
            stock: 22,
            image: "https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?auto=format&fit=crop&w=800&q=80",
            status: "active",
            soldCount: 98
        },
        {
            id: "SP1003",
            name: "PUMA RS-X REINVENTION",
            brand: "PUMA",
            category: "THỂ THAO",
            price: 1950000,
            stock: 18,
            image: "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=800&q=80",
            status: "active",
            soldCount: 75
        },
        {
            id: "SP1004",
            name: "NIKE AIR JORDAN 1 RETRO",
            brand: "NIKE",
            category: "THỜI TRANG",
            price: 4500000,
            stock: 8,
            image: "https://images.unsplash.com/photo-1552346154-21d32810aba3?auto=format&fit=crop&w=800&q=80",
            status: "active",
            soldCount: 210
        },
        {
            id: "SP1005",
            name: "ASICS GEL-KAYANO 29",
            brand: "ASICS",
            category: "CHẠY BỘ",
            price: 2890000,
            stock: 14,
            image: "https://images.unsplash.com/photo-1539185441755-769473a23570?auto=format&fit=crop&w=800&q=80",
            status: "active",
            soldCount: 64
        }
    ];

    // Danh sách đơn hàng mẫu
    const DEFAULT_ORDERS = [
        {
            id: "DH1089",
            customerName: "Nguyễn Văn An",
            phone: "0901234567",
            shoeName: "NIKE AIR FORCE 1 '07",
            shoeImg: "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?auto=format&fit=crop&w=200&q=80",
            size: 42,
            qty: 1,
            total: 2690000,
            payment: "VIETQR",
            status: "COMPLETED",
            date: "21/10/2026"
        },
        {
            id: "DH1088",
            customerName: "Trần Minh Đức",
            phone: "0987654321",
            shoeName: "ADIDAS ULTRABOOST LIGHT",
            shoeImg: "https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?auto=format&fit=crop&w=200&q=80",
            size: 41,
            qty: 1,
            total: 3200000,
            payment: "COD",
            status: "SHIPPING",
            date: "20/10/2026"
        },
        {
            id: "DH1087",
            customerName: "Lê Hoàng Nam",
            phone: "0912345678",
            shoeName: "PUMA RS-X REINVENTION",
            shoeImg: "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=200&q=80",
            size: 40,
            qty: 1,
            total: 1950000,
            payment: "MOMO",
            status: "CONFIRMED",
            date: "19/10/2026"
        }
    ];

    // Danh sách khách hàng mẫu
    const DEFAULT_CUSTOMERS = [
        { id: "KH1001", name: "Nguyễn Văn An", phone: "0901234567", email: "an.nguyen@gmail.com", tier: "KIM CƯƠNG", orders: 8, spent: 18500000 },
        { id: "KH1002", name: "Trần Minh Đức", phone: "0987654321", email: "duc.tran@gmail.com", tier: "VÀNG", orders: 5, spent: 9800000 },
        { id: "KH1003", name: "Lê Hoàng Nam", phone: "0912345678", email: "nam.le@gmail.com", tier: "BẠC", orders: 3, spent: 4650000 }
    ];

    function formatMoney(amount) {
        return Number(amount || 0).toLocaleString("vi-VN") + " VNĐ";
    }

    function getProducts() {
        try {
            const raw = localStorage.getItem(PRODUCTS_KEY);
            return raw ? JSON.parse(raw) : DEFAULT_PRODUCTS;
        } catch {
            return DEFAULT_PRODUCTS;
        }
    }

    function saveProducts(list) {
        try {
            localStorage.setItem(PRODUCTS_KEY, JSON.stringify(list));
        } catch (e) {
            console.error("Save products error:", e);
        }
    }

    function getOrders() {
        try {
            const raw = localStorage.getItem(ORDERS_KEY);
            return raw ? JSON.parse(raw) : DEFAULT_ORDERS;
        } catch {
            return DEFAULT_ORDERS;
        }
    }

    function getCustomers() {
        try {
            const raw = localStorage.getItem(CUSTOMERS_KEY);
            return raw ? JSON.parse(raw) : DEFAULT_CUSTOMERS;
        } catch {
            return DEFAULT_CUSTOMERS;
        }
    }

    // 1. DASHBOARD INITIALIZATION
    function initDashboard() {
        const products = getProducts();
        const orders = getOrders();
        const customers = getCustomers();

        // Metrics
        const revEl = document.getElementById("dashTotalRev");
        const ordEl = document.getElementById("dashTotalOrders");
        const prodEl = document.getElementById("dashTotalProds");
        const custEl = document.getElementById("dashTotalCusts");

        const totalRevenue = orders.reduce((sum, o) => sum + (o.total || 0), 0) + 45000000;
        if (revEl) revEl.textContent = formatMoney(totalRevenue);
        if (ordEl) ordEl.textContent = orders.length + 18;
        if (prodEl) prodEl.textContent = products.length;
        if (custEl) custEl.textContent = customers.length + 32;

        // Recent orders table
        const orderBody = document.getElementById("dashRecentOrdersBody");
        if (orderBody) {
            orderBody.innerHTML = orders.map(o => `
                <tr>
                    <td style="font-weight: 800; font-family: monospace;">#${o.id}</td>
                    <td>
                        <div class="shoe-cell">
                            <img class="shoe-thumb-mono" src="${o.shoeImg}" alt="${o.shoeName}">
                            <div>
                                <div class="shoe-cell-name">${o.shoeName}</div>
                                <div class="shoe-cell-brand">SIZE: ${o.size} • SỐ LƯỢNG: ${o.qty}</div>
                            </div>
                        </div>
                    </td>
                    <td>
                        <div style="font-weight: 700;">${o.customerName}</div>
                        <small style="color: var(--text-muted);">${o.phone}</small>
                    </td>
                    <td style="font-weight: 800;">${formatMoney(o.total)}</td>
                    <td><span class="mono-badge active">${o.status}</span></td>
                    <td style="color: var(--text-muted); font-size: 12px;">${o.date}</td>
                </tr>
            `).join('');
        }

        // Top products table
        const topProdBody = document.getElementById("dashTopProdsBody");
        if (topProdBody) {
            topProdBody.innerHTML = products.slice(0, 4).map(p => `
                <tr>
                    <td>
                        <div class="shoe-cell">
                            <img class="shoe-thumb-mono" src="${p.image}" alt="${p.name}">
                            <div>
                                <div class="shoe-cell-name">${p.name}</div>
                                <div class="shoe-cell-brand">${p.brand} • ${p.category}</div>
                            </div>
                        </div>
                    </td>
                    <td style="font-weight: 800;">${formatMoney(p.price)}</td>
                    <td>${p.stock} ĐÔI</td>
                    <td style="font-weight: 800;">${p.soldCount || 100} ĐÃ BÁN</td>
                </tr>
            `).join('');
        }
    }

    // 2. PRODUCTS PAGE INITIALIZATION
    function initProductsPage() {
        const tbody = document.getElementById("adminProductsBody");
        if (!tbody) return;

        const products = getProducts();
        tbody.innerHTML = products.map((p, idx) => `
            <tr>
                <td style="font-weight: 800; font-family: monospace;">${p.id}</td>
                <td>
                    <div class="shoe-cell">
                        <img class="shoe-thumb-mono" src="${p.image}" alt="${p.name}">
                        <div>
                            <div class="shoe-cell-name">${p.name}</div>
                            <div class="shoe-cell-brand">${p.brand}</div>
                        </div>
                    </div>
                </td>
                <td style="text-transform: uppercase;">${p.category}</td>
                <td style="font-weight: 800;">${formatMoney(p.price)}</td>
                <td>${p.stock} ĐÔI</td>
                <td><span class="mono-badge active">ĐANG BÁN</span></td>
                <td>
                    <button type="button" class="mono-btn mono-btn-outline mono-btn-sm" style="font-size: 10px; padding: 4px 8px; margin-right: 4px;" onclick="window.MonoAdmin.deleteProduct(${idx})">XÓA</button>
                </td>
            </tr>
        `).join('');

        // Modal thêm sản phẩm mới
        const addBtn = document.getElementById("btnOpenAddProduct");
        const modal = document.getElementById("addProductModal");
        const closeBtn = document.getElementById("btnCloseProductModal");
        const form = document.getElementById("addProductForm");

        if (addBtn && modal) addBtn.onclick = () => modal.style.display = "flex";
        if (closeBtn && modal) closeBtn.onclick = () => modal.style.display = "none";

        if (form) {
            form.onsubmit = (e) => {
                e.preventDefault();
                const newP = {
                    id: "SP" + Math.floor(1000 + Math.random() * 9000),
                    name: document.getElementById("prodName").value.toUpperCase(),
                    brand: document.getElementById("prodBrand").value.toUpperCase(),
                    category: document.getElementById("prodCategory").value.toUpperCase(),
                    price: Number(document.getElementById("prodPrice").value) || 2000000,
                    stock: Number(document.getElementById("prodStock").value) || 10,
                    image: document.getElementById("prodImage").value || "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?auto=format&fit=crop&w=800&q=80",
                    status: "active",
                    soldCount: 0
                };
                products.unshift(newP);
                saveProducts(products);
                modal.style.display = "none";
                initProductsPage();
                alert("ĐÃ THÊM MẪU GIÀY MỚI THÀNH CÔNG!");
            };
        }
    }

    // 3. ORDERS PAGE INITIALIZATION
    function initOrdersPage() {
        const tbody = document.getElementById("adminOrdersBody");
        if (!tbody) return;

        const orders = getOrders();
        tbody.innerHTML = orders.map((o, idx) => `
            <tr>
                <td style="font-weight: 800; font-family: monospace;">#${o.id}</td>
                <td>
                    <div class="shoe-cell">
                        <img class="shoe-thumb-mono" src="${o.shoeImg}" alt="${o.shoeName}">
                        <div>
                            <div class="shoe-cell-name">${o.shoeName}</div>
                            <div class="shoe-cell-brand">SIZE: ${o.size} • SL: ${o.qty}</div>
                        </div>
                    </div>
                </td>
                <td>
                    <div style="font-weight: 700;">${o.customerName}</div>
                    <small style="color: var(--text-muted);">${o.phone}</small>
                </td>
                <td style="font-weight: 800;">${formatMoney(o.total)}</td>
                <td style="font-weight: 800; font-size: 11px;">${o.payment}</td>
                <td><span class="mono-badge active">${o.status}</span></td>
                <td>
                    <button type="button" class="mono-btn mono-btn-outline mono-btn-sm" style="font-size: 10px; padding: 4px 8px;" onclick="window.MonoAdmin.toggleOrderStatus(${idx})">ĐỔI TRẠNG THÁI</button>
                </td>
            </tr>
        `).join('');
    }

    // 4. CUSTOMERS PAGE INITIALIZATION
    function initCustomersPage() {
        const tbody = document.getElementById("adminCustomersBody");
        if (!tbody) return;

        const customers = getCustomers();
        tbody.innerHTML = customers.map(c => `
            <tr>
                <td style="font-weight: 800; font-family: monospace;">${c.id}</td>
                <td style="font-weight: 800;">${c.name}</td>
                <td>${c.phone}</td>
                <td>${c.email}</td>
                <td><span class="mono-badge active">${c.tier}</span></td>
                <td style="font-weight: 800;">${c.orders} ĐƠN</td>
                <td style="font-weight: 800;">${formatMoney(c.spent)}</td>
            </tr>
        `).join('');
    }

    // Check admin session
    function checkAdminSession() {
        const logoutBtn = document.getElementById("adminLogoutBtn");
        if (logoutBtn) {
            logoutBtn.addEventListener("click", () => {
                sessionStorage.removeItem(SESSION_KEY);
                window.location.href = "./admin_login.html";
            });
        }
    }

    document.addEventListener("DOMContentLoaded", () => {
        checkAdminSession();
        initDashboard();
        initProductsPage();
        initOrdersPage();
        initCustomersPage();
    });

    window.MonoAdmin = {
        deleteProduct: function (idx) {
            const list = getProducts();
            if (confirm("BẠN CÓ CHẮC MUỐN XÓA MẪU GIÀY NÀY KHÔNG?")) {
                list.splice(idx, 1);
                saveProducts(list);
                initProductsPage();
            }
        },
        toggleOrderStatus: function (idx) {
            const list = getOrders();
            const cur = list[idx].status;
            list[idx].status = cur === "COMPLETED" ? "SHIPPING" : (cur === "SHIPPING" ? "CONFIRMED" : "COMPLETED");
            try {
                localStorage.setItem(ORDERS_KEY, JSON.stringify(list));
            } catch {}
            initOrdersPage();
        }
    };
})();
