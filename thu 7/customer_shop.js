/**
 * ==========================================================================
 * SHOES STORE - BLACK & WHITE CUSTOMER SHOPPING CONTROLLER
 * Xử lý danh mục giày, giỏ hàng, tìm kiếm và lọc cho giao diện đen trắng
 * ==========================================================================
 */

(function () {
    "use strict";

    const CART_KEY = "shoesCart";
    const SESSION_KEY = "shoesCustomerSession";
    const COMPAT_SESSION_KEY = "loggedInCustomer";

    const DEFAULT_PRODUCTS = [
        {
            id: "SP1001",
            name: "NIKE AIR FORCE 1 '07 ALL WHITE",
            brand: "NIKE",
            category: "THỜI TRANG",
            price: 2690000,
            originalPrice: 3100000,
            image: "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?auto=format&fit=crop&w=800&q=80",
            description: "Thiết kế da kinh điển màu trắng tinh khiết với đế đệm khí Nike Air êm ái.",
            badge: "HOT",
            sizes: [39, 40, 41, 42, 43]
        },
        {
            id: "SP1002",
            name: "ADIDAS ULTRABOOST LIGHT CORE BLACK",
            brand: "ADIDAS",
            category: "CHẠY BỘ",
            price: 3200000,
            originalPrice: 3800000,
            image: "https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?auto=format&fit=crop&w=800&q=80",
            description: "Dòng giày chạy hàng đầu của Adidas với công nghệ đệm Boost trợ lực tối đa.",
            badge: "SALE",
            sizes: [40, 41, 42, 43]
        },
        {
            id: "SP1003",
            name: "PUMA RS-X REINVENTION CHUNKY",
            brand: "PUMA",
            category: "THỂ THAO",
            price: 1950000,
            originalPrice: 2400000,
            image: "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=800&q=80",
            description: "Phong cách Chunky Sneaker táo bạo với công nghệ đệm giảm xóc Running System.",
            badge: "NEW",
            sizes: [39, 40, 41]
        },
        {
            id: "SP1004",
            name: "NIKE AIR JORDAN 1 RETRO HIGH OG",
            brand: "NIKE",
            category: "THỜI TRANG",
            price: 4500000,
            originalPrice: 5200000,
            image: "https://images.unsplash.com/photo-1552346154-21d32810aba3?auto=format&fit=crop&w=800&q=80",
            description: "Huyền thoại bóng rổ đường phố với chất liệu da cao cấp và phối màu kinh điển.",
            badge: "HOT",
            sizes: [40, 41, 42]
        },
        {
            id: "SP1005",
            name: "ASICS GEL-KAYANO 29 RUNNING",
            brand: "ASICS",
            category: "CHẠY BỘ",
            price: 2890000,
            originalPrice: 3300000,
            image: "https://images.unsplash.com/photo-1539185441755-769473a23570?auto=format&fit=crop&w=800&q=80",
            description: "Độ ổn định vượt trội cùng công nghệ đệm FF Blast Plus và GEL êm ái.",
            badge: "SALE",
            sizes: [41, 42, 43]
        },
        {
            id: "SP1006",
            name: "NEW BALANCE 550 WHITE GREY",
            brand: "NEW BALANCE",
            category: "THỜI TRANG",
            price: 3100000,
            originalPrice: 3500000,
            image: "https://images.unsplash.com/photo-1551107696-a4b085a6d966?auto=format&fit=crop&w=800&q=80",
            description: "Thiết kế Retro thập niên 80 với chất liệu da bóng bẩy và phong cách thanh lịch.",
            badge: "HOT",
            sizes: [39, 40, 41, 42]
        },
        {
            id: "SP1007",
            name: "CONVERSE CHUCK 70 VINTAGE CANVAS",
            brand: "CONVERSE",
            category: "THỂ THAO",
            price: 1750000,
            originalPrice: 2000000,
            image: "https://images.unsplash.com/photo-1607522370275-f14206abe5d3?auto=format&fit=crop&w=800&q=80",
            description: "Vải canvas 12oz dầy dặn, đường chỉ kép gia cố và đế cao su phủ bóng vintage.",
            badge: "SALE",
            sizes: [39, 40, 41, 42, 43]
        },
        {
            id: "SP1008",
            name: "VANS OLD SKOOL BLACK & WHITE",
            brand: "VANS",
            category: "THỜI TRANG",
            price: 1650000,
            originalPrice: 1900000,
            image: "https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?auto=format&fit=crop&w=800&q=80",
            description: "Dải sóng da Sidestripe biểu tượng cùng đế cao su Waffle bám đường hoàn hảo.",
            badge: "HOT",
            sizes: [39, 40, 41, 42]
        }
    ];

    let products = [...DEFAULT_PRODUCTS];
    let cart = [];
    let activeBrand = "all";
    let searchQuery = "";
    let selectedSizes = {};

    function formatMoney(n) {
        return Number(n || 0).toLocaleString("vi-VN") + " VNĐ";
    }

    function loadProducts() {
        try {
            const raw = localStorage.getItem("shoesProducts");
            if (raw) {
                const parsed = JSON.parse(raw);
                if (Array.isArray(parsed) && parsed.length > 0) {
                    products = parsed.map((item, idx) => {
                        const fallback = DEFAULT_PRODUCTS[idx % DEFAULT_PRODUCTS.length];
                        return {
                            id: item.id || `SP${1001 + idx}`,
                            name: (item.name || fallback.name).toUpperCase(),
                            brand: (item.brand || fallback.brand).toUpperCase(),
                            category: (item.category || fallback.category).toUpperCase(),
                            price: Number(item.price) || fallback.price,
                            image: item.image && item.image.startsWith("http") ? item.image : fallback.image,
                            description: item.description || fallback.description,
                            badge: idx % 2 === 0 ? "HOT" : "NEW",
                            sizes: Array.isArray(item.variants) && item.variants.length > 0
                                ? item.variants.map(v => Number(v.size)).filter(Boolean)
                                : fallback.sizes
                        };
                    });
                    return;
                }
            }
        } catch {
            products = [...DEFAULT_PRODUCTS];
        }
    }

    function renderShopGrid() {
        const grid = document.getElementById("shopGrid");
        if (!grid) return;

        const filtered = products.filter(p => {
            if (activeBrand !== "all" && p.brand.toLowerCase() !== activeBrand.toLowerCase()) return false;
            if (searchQuery) {
                const q = searchQuery.toLowerCase().trim();
                return p.name.toLowerCase().includes(q) || p.brand.toLowerCase().includes(q);
            }
            return true;
        });

        if (filtered.length === 0) {
            grid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 60px 20px; border: 1px dashed var(--border-color); border-radius: 8px;">
                    <h3 style="font-size: 18px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase;">KHÔNG TÌM THẤY SẢN PHẨM</h3>
                    <p style="color: var(--text-secondary); margin-top: 6px;">Vui lòng thử lại với từ khóa khác hoặc chọn xem tất cả thương hiệu.</p>
                </div>
            `;
            return;
        }

        grid.innerHTML = filtered.map(p => {
            const curSize = selectedSizes[p.id] || p.sizes[0] || 40;
            return `
                <article class="card-shoe-mono">
                    <div class="card-img-box">
                        <img class="card-shoe-img" src="${p.image}" alt="${p.name}" loading="lazy">
                        <span class="card-badge-mono">${p.badge}</span>
                    </div>

                    <div class="card-body-mono">
                        <span class="card-brand-mono">${p.brand}</span>
                        <h3 class="card-title-mono">${p.name}</h3>
                        <div class="card-price-mono">${formatMoney(p.price)}</div>

                        <div class="card-sizes-mono">
                            <span style="font-size: 11px; font-weight: 800; color: var(--text-muted); text-transform: uppercase;">SIZE:</span>
                            ${p.sizes.map(s => `
                                <button type="button" class="size-pill-mono ${s === curSize ? 'selected' : ''}" onclick="window.MonoShop.selectSize('${p.id}', ${s}, this)">${s}</button>
                            `).join('')}
                        </div>

                        <div class="card-actions-mono">
                            <button type="button" class="mono-btn mono-btn-outline mono-btn-sm" onclick="window.MonoShop.addToCart('${p.id}')">
                                THÊM GIỎ
                            </button>
                            <button type="button" class="mono-btn mono-btn-sm" onclick="window.MonoShop.buyNow('${p.id}')">
                                MUA NGAY
                            </button>
                        </div>
                    </div>
                </article>
            `;
        }).join('');
    }

    function loadCart() {
        try {
            const raw = localStorage.getItem(CART_KEY);
            cart = raw ? JSON.parse(raw) : [];
        } catch {
            cart = [];
        }
        updateBadge();
    }

    function saveCart() {
        try {
            localStorage.setItem(CART_KEY, JSON.stringify(cart));
            localStorage.setItem("shoes_store_lien_ket_v1", JSON.stringify(cart));
        } catch (e) {
            console.error("Cart save error:", e);
        }
        updateBadge();
    }

    function updateBadge() {
        const total = cart.reduce((s, i) => s + (i.quantity || 1), 0);
        document.querySelectorAll("[data-cart-count], #cartCount").forEach(el => {
            el.textContent = total;
        });
    }

    function addToCart(id, customSize) {
        const product = products.find(p => p.id === id);
        if (!product) return;

        const size = customSize || selectedSizes[id] || product.sizes[0] || 40;
        const existing = cart.find(i => i.productId === id && i.size === size);

        if (existing) {
            existing.quantity += 1;
        } else {
            cart.push({
                productId: product.id,
                name: product.name,
                brand: product.brand,
                price: product.price,
                image: product.image,
                size: size,
                quantity: 1
            });
        }

        saveCart();
        openDrawer();
    }

    function buyNow(id) {
        addToCart(id);
        openDrawer();
    }

    function openDrawer() {
        renderDrawer();
        const drawer = document.getElementById("cartDrawer");
        const overlay = document.getElementById("cartOverlay");
        if (drawer && overlay) {
            drawer.classList.add("active");
            overlay.classList.add("active");
        }
    }

    function closeDrawer() {
        const drawer = document.getElementById("cartDrawer");
        const overlay = document.getElementById("cartOverlay");
        if (drawer && overlay) {
            drawer.classList.remove("active");
            overlay.classList.remove("active");
        }
    }

    function renderDrawer() {
        const body = document.getElementById("cartDrawerBody");
        const totalEl = document.getElementById("cartDrawerTotal");
        if (!body) return;

        if (cart.length === 0) {
            body.innerHTML = `
                <div style="text-align: center; padding: 60px 10px; color: var(--text-secondary);">
                    <h4 style="font-size: 15px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase;">GIỎ HÀNG TRỐNG</h4>
                    <p style="font-size: 13px; margin-top: 8px;">Vui lòng chọn mẫu giày để tiến hành mua hàng.</p>
                </div>
            `;
            if (totalEl) totalEl.textContent = "0 VNĐ";
            return;
        }

        let total = 0;
        body.innerHTML = cart.map((item, idx) => {
            total += item.price * item.quantity;
            return `
                <div class="mono-drawer-item">
                    <img src="${item.image}" alt="${item.name}">
                    <div style="flex: 1;">
                        <h4 style="font-size: 13px; font-weight: 800; letter-spacing: 0.5px;">${item.name}</h4>
                        <p style="font-size: 11px; color: var(--text-muted); margin: 3px 0 8px;">SIZE: ${item.size} • ĐƠN GIÁ: ${formatMoney(item.price)}</p>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="display: flex; align-items: center; border: 1px solid var(--border-color); border-radius: 2px;">
                                <button type="button" style="background: none; border: none; color: var(--text-primary); width: 24px; height: 24px; cursor: pointer;" onclick="window.MonoShop.updateQty(${idx}, -1)">-</button>
                                <span style="font-size: 12px; font-weight: 800; padding: 0 6px;">${item.quantity}</span>
                                <button type="button" style="background: none; border: none; color: var(--text-primary); width: 24px; height: 24px; cursor: pointer;" onclick="window.MonoShop.updateQty(${idx}, 1)">+</button>
                            </div>
                            <button type="button" style="background: none; border: none; color: var(--text-muted); font-size: 11px; cursor: pointer; text-decoration: underline;" onclick="window.MonoShop.removeItem(${idx})">XÓA</button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        if (totalEl) totalEl.textContent = formatMoney(total);
    }

    function checkCustomerSession() {
        const authBtn = document.getElementById("custAuthBtn");
        const accountBox = document.getElementById("custAccountBox");
        if (!authBtn || !accountBox) return;

        let session = null;
        try {
            const raw = sessionStorage.getItem(SESSION_KEY) || localStorage.getItem(SESSION_KEY) || sessionStorage.getItem(COMPAT_SESSION_KEY);
            if (raw) session = JSON.parse(raw);
        } catch {
            session = null;
        }

        if (session && session.name) {
            authBtn.style.display = "none";
            accountBox.style.display = "inline-flex";
            const nameEl = document.getElementById("custNameDisplay");
            if (nameEl) nameEl.textContent = session.name.toUpperCase();
        } else {
            authBtn.style.display = "inline-flex";
            accountBox.style.display = "none";
        }
    }

    document.addEventListener("DOMContentLoaded", () => {
        loadProducts();
        loadCart();
        checkCustomerSession();
        renderShopGrid();

        // Brand filter clicks
        document.querySelectorAll(".filter-tab-mono").forEach(tab => {
            tab.addEventListener("click", function () {
                document.querySelectorAll(".filter-tab-mono").forEach(t => t.classList.remove("active"));
                this.classList.add("active");
                activeBrand = this.getAttribute("data-brand") || "all";
                renderShopGrid();
            });
        });

        // Search
        const searchInput = document.getElementById("monoSearchInput");
        if (searchInput) {
            searchInput.addEventListener("input", function () {
                searchQuery = this.value;
                renderShopGrid();
            });
        }

        // Cart Drawer
        const cartBtn = document.getElementById("cartBtn");
        const closeBtn = document.getElementById("closeDrawerBtn");
        const overlay = document.getElementById("cartOverlay");
        if (cartBtn) cartBtn.addEventListener("click", openDrawer);
        if (closeBtn) closeBtn.addEventListener("click", closeDrawer);
        if (overlay) overlay.addEventListener("click", closeDrawer);

        // Theme toggle button (Black / White)
        const themeBtn = document.getElementById("themeToggleBtn");
        if (themeBtn) {
            themeBtn.addEventListener("click", () => {
                document.body.classList.toggle("theme-white");
                const isWhite = document.body.classList.contains("theme-white");
                themeBtn.textContent = isWhite ? "NỀN ĐEN" : "NỀN TRẮNG";
            });
        }

        // Logout
        const logoutBtn = document.getElementById("custLogoutBtn");
        if (logoutBtn) {
            logoutBtn.addEventListener("click", () => {
                sessionStorage.removeItem(SESSION_KEY);
                sessionStorage.removeItem(COMPAT_SESSION_KEY);
                localStorage.removeItem(SESSION_KEY);
                window.location.reload();
            });
        }
    });

    window.MonoShop = {
        addToCart,
        buyNow,
        openDrawer,
        closeDrawer,
        selectSize: function (id, size, btn) {
            selectedSizes[id] = size;
            const parent = btn.parentElement;
            if (parent) {
                parent.querySelectorAll(".size-pill-mono").forEach(p => p.classList.remove("selected"));
                btn.classList.add("selected");
            }
        },
        updateQty: function (idx, delta) {
            if (!cart[idx]) return;
            cart[idx].quantity += delta;
            if (cart[idx].quantity <= 0) cart.splice(idx, 1);
            saveCart();
            renderDrawer();
        },
        removeItem: function (idx) {
            if (!cart[idx]) return;
            cart.splice(idx, 1);
            saveCart();
            renderDrawer();
        }
    };
})();
