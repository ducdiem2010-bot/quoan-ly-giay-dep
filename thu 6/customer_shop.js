/**
 * ==========================================================================
 * SHOES STORE - CUSTOMER SHOPPING PAGE JAVASCRIPT
 * Đồng bộ sản phẩm từ backend API, giỏ hàng, wishlist và phiên khách hàng
 * ==========================================================================
 */

(function () {
    "use strict";

    // 1. Storage Keys
    const CART_STORAGE_KEY    = "shoesCart";
    const COMPAT_CART_KEY     = "shoes_store_lien_ket_v1";
    const PRODUCTS_KEY        = "shoesProducts";
    const CUSTOMER_SESSION_KEY = "shoesCustomerSession";
    const COMPAT_SESSION_KEY  = "loggedInCustomer";
    const WISHLIST_KEY        = "shoesWishlist";

    // 2. Backend API URL (chạy server.js ở localhost:3000 nếu có)
    const API_BASE = "http://localhost:3000";

    // 3. Danh mục sản phẩm mẫu chuẩn với ảnh thật độ nét cao
    const DEFAULT_CATALOG = [
        {
            id: "SP1001",
            name: "Nike Air Force 1 '07 All White",
            brand: "Nike", category: "Giày thời trang", gender: "Unisex",
            price: 2690000, originalPrice: 3100000, stock: 35,
            soldCount: 142, rating: 4.9,
            image: "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?auto=format&fit=crop&w=800&q=80",
            description: "Thiết kế huyền thoại với chất liệu da cao cấp màu trắng tinh tế, đệm khí Nike Air êm ái hỗ trợ tối đa cho việc đi lại hàng ngày.",
            badge: "hot", sizes: [39, 40, 41, 42, 43]
        },
        {
            id: "SP1002",
            name: "Adidas Ultraboost Light Core Black",
            brand: "Adidas", category: "Giày chạy bộ", gender: "Nam",
            price: 3200000, originalPrice: 3800000, stock: 22,
            soldCount: 98, rating: 5.0,
            image: "https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?auto=format&fit=crop&w=800&q=80",
            description: "Dòng giày chạy hàng đầu của Adidas trang bị đệm Boost siêu nhẹ, êm ái và trợ lực vượt trội cho mọi cự ly chạy.",
            badge: "sale", sizes: [40, 41, 42, 43]
        },
        {
            id: "SP1003",
            name: "Puma RS-X Reinvention Chunky",
            brand: "Puma", category: "Giày thể thao", gender: "Unisex",
            price: 1950000, originalPrice: 2400000, stock: 18,
            soldCount: 75, rating: 4.8,
            image: "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=800&q=80",
            description: "Phong cách Chunky Sneaker hầm hố, phối màu bắt mắt cùng công nghệ đệm RS giảm chấn tối đa khi vận động.",
            badge: "new", sizes: [39, 40, 41]
        },
        {
            id: "SP1004",
            name: "Nike Air Jordan 1 Retro High Chicago",
            brand: "Nike", category: "Giày thời trang", gender: "Unisex",
            price: 4500000, originalPrice: 5200000, stock: 8,
            soldCount: 210, rating: 5.0,
            image: "https://images.unsplash.com/photo-1552346154-21d32810aba3?auto=format&fit=crop&w=800&q=80",
            description: "Huyền thoại bóng rổ đường phố với phối màu Chicago cổ điển, phiên bản giới hạn da cao cấp cực kỳ ôm chân.",
            badge: "hot", sizes: [40, 41, 42]
        },
        {
            id: "SP1005",
            name: "Asics Gel-Kayano 29 Stability Running",
            brand: "Asics", category: "Giày chạy bộ", gender: "Nam",
            price: 2890000, originalPrice: 3300000, stock: 14,
            soldCount: 64, rating: 4.9,
            image: "https://images.unsplash.com/photo-1539185441755-769473a23570?auto=format&fit=crop&w=800&q=80",
            description: "Hỗ trợ ổn định bàn chân tối đa cho người chạy cự ly dài với công nghệ FF BLAST PLUS và đệm GEL siêu êm ái.",
            badge: "sale", sizes: [41, 42, 43]
        },
        {
            id: "SP1006",
            name: "New Balance 550 White Grey Vintage",
            brand: "New Balance", category: "Giày thời trang", gender: "Unisex",
            price: 3100000, originalPrice: 3500000, stock: 16,
            soldCount: 115, rating: 4.9,
            image: "https://images.unsplash.com/photo-1551107696-a4b085a6d966?auto=format&fit=crop&w=800&q=80",
            description: "Cơn sốt Retro Basketball thập niên 80-90 trở lại với da thật cao cấp phối màu trắng xám dễ phối mọi phong cách thời trang.",
            badge: "hot", sizes: [39, 40, 41, 42]
        },
        {
            id: "SP1007",
            name: "Converse Chuck 70 Vintage Canvas Black",
            brand: "Converse", category: "Giày thể thao", gender: "Unisex",
            price: 1750000, originalPrice: 2000000, stock: 40,
            soldCount: 320, rating: 4.8,
            image: "https://images.unsplash.com/photo-1607522370275-f14206abe5d3?auto=format&fit=crop&w=800&q=80",
            description: "Vải canvas 12oz dầy dặn, đường may gia cố tỉ mỉ, đế cao su phủ bóng vintage và lót đệm OrthoLite êm chân.",
            badge: "sale", sizes: [39, 40, 41, 42, 43]
        },
        {
            id: "SP1008",
            name: "Vans Old Skool Classic Skate Shoes",
            brand: "Vans", category: "Giày thời trang", gender: "Unisex",
            price: 1650000, originalPrice: 1900000, stock: 30,
            soldCount: 280, rating: 4.7,
            image: "https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?auto=format&fit=crop&w=800&q=80",
            description: "Thiết kế dải sóng da Sidestripe kinh điển của Vans với đế waffle chống trơn trượt hoàn hảo.",
            badge: "hot", sizes: [39, 40, 41, 42]
        }
    ];

    // State ứng dụng
    let products     = [];
    let cart         = [];
    let wishlist     = [];
    let activeBrand  = "all";
    let activeCategory = "all";
    let activePriceRange = "all";
    let activeSort   = "popular";
    let searchQuery  = "";
    let selectedSizes = {};
    let appliedDiscount = 0;
    let backendAvailable = false;

    /** Định dạng tiền tệ VNĐ */
    function formatCurrency(amount) {
        return Number(amount || 0).toLocaleString("vi-VN") + " đ";
    }

    // =========================================================================
    // ĐỒNG BỘ SẢN PHẨM TỪ BACKEND API
    // =========================================================================

    /**
     * Thử kết nối backend và tải sản phẩm từ API
     * Fallback: localStorage → DEFAULT_CATALOG
     */
    async function loadProductsFromAPI() {
        try {
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), 3000); // 3s timeout

            const res = await fetch(`${API_BASE}/api/products`, {
                signal: controller.signal
            });
            clearTimeout(timeout);

            if (!res.ok) throw new Error("API lỗi: " + res.status);

            const json = await res.json();
            if (json.success && Array.isArray(json.data) && json.data.length > 0) {
                backendAvailable = true;
                products = json.data.map((item, idx) => {
                    const fallback = DEFAULT_CATALOG[idx % DEFAULT_CATALOG.length];
                    return normalizeProduct(item, fallback, idx);
                });

                // Lưu vào localStorage để các lần sau tải nhanh hơn
                try {
                    localStorage.setItem(PRODUCTS_KEY, JSON.stringify(products));
                } catch (e) {}

                updateSyncBadge(true);
                renderProductGrid();
                return;
            }
        } catch (e) {
            backendAvailable = false;
        }

        // Fallback 1: localStorage
        loadProductsFromStorage();
        updateSyncBadge(false);
        renderProductGrid();
    }

    /** Fallback: Đọc từ localStorage (đã đồng bộ từ Admin) */
    function loadProductsFromStorage() {
        try {
            const raw = localStorage.getItem(PRODUCTS_KEY);
            if (raw) {
                const parsed = JSON.parse(raw);
                if (Array.isArray(parsed) && parsed.length > 0) {
                    products = parsed.map((item, idx) => {
                        const fallback = DEFAULT_CATALOG[idx % DEFAULT_CATALOG.length];
                        return normalizeProduct(item, fallback, idx);
                    });
                    return;
                }
            }
        } catch (e) {
            console.warn("Lỗi đọc sản phẩm từ localStorage:", e);
        }
        // Fallback cuối: danh mục mẫu
        products = [...DEFAULT_CATALOG];
    }

    /** Chuẩn hóa dữ liệu sản phẩm từ nhiều nguồn khác nhau */
    function normalizeProduct(item, fallback, idx) {
        const price = Number(item.price) || fallback.price;
        return {
            id:           item.id || `SP${1000 + idx}`,
            name:         item.name || fallback.name,
            brand:        item.brand || fallback.brand,
            category:     item.category || fallback.category,
            gender:       item.gender || fallback.gender,
            price:        price,
            originalPrice: item.originalPrice || Math.round(price * 1.15),
            stock:        item.stock !== undefined ? Number(item.stock) : fallback.stock,
            soldCount:    item.soldCount || fallback.soldCount || 50,
            rating:       item.rating || fallback.rating || 4.9,
            image:        (item.image && item.image.startsWith("http")) ? item.image : fallback.image,
            description:  item.description || fallback.description,
            badge:        item.badge || (idx % 3 === 0 ? "hot" : (idx % 2 === 0 ? "sale" : "new")),
            sizes:        (Array.isArray(item.variants) && item.variants.length > 0)
                ? item.variants.map(v => Number(v.size)).filter(Boolean)
                : (Array.isArray(item.sizes) ? item.sizes : fallback.sizes)
        };
    }

    /** Hiển thị badge đồng bộ backend trên header */
    function updateSyncBadge(online) {
        const badge = document.getElementById("syncStatusBadge");
        if (!badge) return;
        badge.innerHTML = online
            ? `<span class="sync-dot online"></span> Đồng bộ từ Backend`
            : `<span class="sync-dot offline"></span> Dùng dữ liệu offline`;
        badge.title = online
            ? `Dữ liệu sản phẩm đã được đồng bộ từ ${API_BASE}/api/products`
            : "Không kết nối được backend. Đang dùng dữ liệu đã lưu.";
    }

    // =========================================================================
    // WISHLIST (LƯU SẢN PHẨM YÊU THÍCH)
    // =========================================================================

    function loadWishlist() {
        try {
            const raw = localStorage.getItem(WISHLIST_KEY);
            wishlist = raw ? JSON.parse(raw) : [];
            if (!Array.isArray(wishlist)) wishlist = [];
        } catch { wishlist = []; }
    }

    function saveWishlist() {
        try {
            localStorage.setItem(WISHLIST_KEY, JSON.stringify(wishlist));
        } catch (e) {}
        updateWishlistBadge();
    }

    function isWishlisted(productId) {
        return wishlist.includes(productId);
    }

    function toggleWishlist(productId, btnEl) {
        const product = products.find(p => p.id === productId);
        if (!product) return;

        if (isWishlisted(productId)) {
            wishlist = wishlist.filter(id => id !== productId);
            showToast(`💔 Đã xóa <b>${product.name}</b> khỏi danh sách yêu thích`);
        } else {
            wishlist.push(productId);
            // Hiệu ứng pulse cho nút
            if (btnEl) {
                btnEl.classList.add("wishlist-pulse");
                setTimeout(() => btnEl.classList.remove("wishlist-pulse"), 600);
            }
            showToast(`❤️ Đã lưu <b>${product.name}</b> vào yêu thích!`);
        }

        saveWishlist();
        // Cập nhật trạng thái nút tim trên toàn trang
        document.querySelectorAll(`.btn-wishlist[data-id="${productId}"]`).forEach(btn => {
            btn.classList.toggle("active", isWishlisted(productId));
            btn.title = isWishlisted(productId) ? "Xóa khỏi yêu thích" : "Lưu vào yêu thích";
            btn.innerHTML = isWishlisted(productId) ? "❤️" : "🤍";
        });
    }

    function updateWishlistBadge() {
        const badge = document.getElementById("wishlistCount");
        if (badge) badge.textContent = wishlist.length;
    }

    // =========================================================================
    // LỌC & RENDER SẢN PHẨM
    // =========================================================================

    function getFilteredProducts() {
        return products.filter(p => {
            if (activeBrand !== "all" && p.brand.toLowerCase() !== activeBrand.toLowerCase()) return false;
            if (activeCategory !== "all" && p.category !== activeCategory) return false;
            if (activePriceRange === "under2m" && p.price >= 2000000) return false;
            if (activePriceRange === "2to3m" && (p.price < 2000000 || p.price > 3000000)) return false;
            if (activePriceRange === "over3m" && p.price <= 3000000) return false;
            if (searchQuery) {
                const q = searchQuery.toLowerCase().trim();
                if (!p.name.toLowerCase().includes(q) &&
                    !p.brand.toLowerCase().includes(q) &&
                    !(p.description || "").toLowerCase().includes(q)) return false;
            }
            return true;
        }).sort((a, b) => {
            if (activeSort === "price-asc")  return a.price - b.price;
            if (activeSort === "price-desc") return b.price - a.price;
            if (activeSort === "rating")     return b.rating - a.rating;
            return b.soldCount - a.soldCount;
        });
    }

    function renderProductGrid() {
        const grid = document.getElementById("productsGrid");
        const countBadge = document.getElementById("filterCountBadge");
        if (!grid) return;

        const items = getFilteredProducts();
        if (countBadge) {
            countBadge.textContent = `Hiển thị ${items.length} mẫu giày`;
        }

        if (items.length === 0) {
            grid.innerHTML = `
                <div class="products-empty">
                    <span>👟</span>
                    <h3>Không tìm thấy mẫu giày nào phù hợp!</h3>
                    <p style="color:#64748b; margin-top: 6px;">Hãy thử tìm kiếm với từ khóa khác hoặc xóa bộ lọc.</p>
                    <button type="button" class="btn-reset-filters" onclick="window.ShoesShop.resetFilters()" style="margin-top: 14px;">
                        Xóa tất cả bộ lọc
                    </button>
                </div>
            `;
            return;
        }

        grid.innerHTML = items.map(p => {
            const currentSize  = selectedSizes[p.id] || p.sizes[0] || 40;
            const badgeLabel   = p.badge === "hot" ? "🔥 Bán chạy" : (p.badge === "sale" ? "⚡ Giảm 15%" : "✨ Mới");
            const wishlisted   = isWishlisted(p.id);
            const outOfStock   = p.stock !== undefined && p.stock <= 0;
            const lowStock     = p.stock > 0 && p.stock <= 5;

            return `
                <article class="product-card${outOfStock ? ' out-of-stock' : ''}" data-id="${p.id}">
                    <div class="card-badges">
                        <span class="badge-tag ${p.badge}">${badgeLabel}</span>
                        ${outOfStock ? '<span class="badge-tag out">Hết hàng</span>' : ''}
                        ${lowStock ? '<span class="badge-tag low">⚠️ Còn ' + p.stock + '</span>' : ''}
                    </div>

                    <!-- Nút Wishlist (Lưu yêu thích) -->
                    <button
                        type="button"
                        class="btn-wishlist${wishlisted ? ' active' : ''}"
                        data-id="${p.id}"
                        title="${wishlisted ? 'Xóa khỏi yêu thích' : 'Lưu vào yêu thích'}"
                        onclick="window.ShoesShop.toggleWishlist('${p.id}', this)">
                        ${wishlisted ? '❤️' : '🤍'}
                    </button>

                    <div class="card-image-wrap" onclick="window.ShoesShop.openQuickView('${p.id}')">
                        <img class="card-image" src="${p.image}" alt="${p.name}" loading="lazy"
                            onerror="this.src='https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=800&q=80'">
                        <button type="button" class="card-quick-view">👁️ Xem nhanh</button>
                    </div>

                    <div class="card-body">
                        <div class="card-meta">
                            <span class="card-brand">${p.brand}</span>
                            <span class="card-rating">⭐ ${p.rating} (${p.soldCount})</span>
                        </div>

                        <h3 class="card-title">
                            <a href="javascript:void(0)" onclick="window.ShoesShop.openQuickView('${p.id}')">${p.name}</a>
                        </h3>

                        <div class="card-price-row">
                            <span class="card-price-current">${formatCurrency(p.price)}</span>
                            <span class="card-price-original">${formatCurrency(p.originalPrice)}</span>
                        </div>

                        <!-- Chọn size nhanh -->
                        <div class="card-sizes">
                            <span class="card-size-label">Size:</span>
                            ${p.sizes.map(s => `
                                <button type="button" class="card-size-chip ${s === currentSize ? 'selected' : ''}"
                                    onclick="window.ShoesShop.selectSize('${p.id}', ${s}, this)">${s}</button>
                            `).join('')}
                        </div>

                        <div class="card-actions">
                            <button type="button" class="btn-add-cart${outOfStock ? ' disabled' : ''}"
                                onclick="window.ShoesShop.addToCartAnimated('${p.id}', this)"
                                ${outOfStock ? 'disabled' : ''}>
                                <span>🛒</span> ${outOfStock ? 'Hết hàng' : 'Thêm giỏ'}
                            </button>
                            <button type="button" class="btn-buy-now${outOfStock ? ' disabled' : ''}"
                                onclick="window.ShoesShop.buyNow('${p.id}')"
                                ${outOfStock ? 'disabled' : ''}>
                                ⚡ Mua ngay
                            </button>
                        </div>
                    </div>
                </article>
            `;
        }).join('');
    }

    // =========================================================================
    // GIỎ HÀNG
    // =========================================================================

    function loadCart() {
        try {
            const raw = localStorage.getItem(CART_STORAGE_KEY) || sessionStorage.getItem(CART_STORAGE_KEY);
            cart = raw ? JSON.parse(raw) : [];
            if (!Array.isArray(cart)) cart = [];
        } catch { cart = []; }
        updateCartBadge();
    }

    function saveCart() {
        try {
            localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cart));
            sessionStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cart));
            // Đồng bộ sang chuẩn cũ
            const compatItems = cart.map(item => ({
                productId: item.productId,
                size: Number(item.size),
                quantity: Number(item.quantity)
            }));
            localStorage.setItem(COMPAT_CART_KEY, JSON.stringify(compatItems));
        } catch (e) { console.error("Lỗi lưu giỏ hàng:", e); }
        updateCartBadge();
    }

    function updateCartBadge() {
        const totalItems = cart.reduce((sum, item) => sum + (item.quantity || 1), 0);
        document.querySelectorAll("[data-cart-count], #headerCartCount").forEach(el => {
            el.textContent = totalItems;
        });
    }

    /** Thêm sản phẩm vào giỏ hàng */
    function addToCart(productId, customSize, customQty) {
        const product = products.find(p => p.id === productId);
        if (!product) return;
        if (product.stock !== undefined && product.stock <= 0) {
            showToast("⚠️ Sản phẩm này đã hết hàng!");
            return;
        }

        const size = customSize || selectedSizes[productId] || product.sizes[0] || 40;
        const qty  = customQty || 1;

        const existing = cart.find(item => item.productId === productId && item.size === size);
        if (existing) {
            existing.quantity += qty;
        } else {
            cart.push({
                productId: product.id,
                name:      product.name,
                brand:     product.brand,
                price:     product.price,
                image:     product.image,
                size:      size,
                quantity:  qty
            });
        }

        saveCart();
        showToast(`✅ Đã thêm <b>${product.name} (Size ${size})</b> vào giỏ hàng!`);
    }

    /**
     * Thêm giỏ hàng có hiệu ứng "bay" sản phẩm lên cart button
     */
    function addToCartAnimated(productId, btnEl) {
        addToCart(productId);
        flyToCart(btnEl);
    }

    /** Hiệu ứng fly-to-cart */
    function flyToCart(sourceEl) {
        if (!sourceEl) return;
        const cartBtn = document.getElementById("headerCartBtn");
        if (!cartBtn) return;

        const sourcRect = sourceEl.getBoundingClientRect();
        const cartRect  = cartBtn.getBoundingClientRect();

        const dot = document.createElement("div");
        dot.className = "fly-dot";
        dot.style.cssText = `
            position: fixed;
            left: ${sourcRect.left + sourcRect.width / 2}px;
            top: ${sourcRect.top + sourcRect.height / 2}px;
            width: 18px; height: 18px;
            background: #2563eb;
            border-radius: 50%;
            z-index: 9999;
            pointer-events: none;
            transition: all 0.65s cubic-bezier(0.22, 1, 0.36, 1);
            transform: scale(1);
        `;
        document.body.appendChild(dot);

        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                dot.style.left = `${cartRect.left + cartRect.width / 2}px`;
                dot.style.top  = `${cartRect.top + cartRect.height / 2}px`;
                dot.style.transform = "scale(0)";
                dot.style.opacity = "0.5";
            });
        });

        // Bounce cart badge
        const badge = document.getElementById("headerCartCount");
        if (badge) {
            badge.classList.add("cart-badge-bounce");
            setTimeout(() => badge.classList.remove("cart-badge-bounce"), 600);
        }

        setTimeout(() => {
            if (dot.parentNode) dot.parentNode.removeChild(dot);
        }, 700);
    }

    function buyNow(productId) {
        addToCart(productId);
        openCartDrawer();
    }

    // =========================================================================
    // CART DRAWER
    // =========================================================================

    function openCartDrawer() {
        renderCartDrawer();
        const drawer  = document.getElementById("cartDrawer");
        const overlay = document.getElementById("cartDrawerOverlay");
        if (drawer && overlay) {
            drawer.classList.add("active");
            overlay.classList.add("active");
        }
    }

    function closeCartDrawer() {
        const drawer  = document.getElementById("cartDrawer");
        const overlay = document.getElementById("cartDrawerOverlay");
        if (drawer && overlay) {
            drawer.classList.remove("active");
            overlay.classList.remove("active");
        }
    }

    function renderCartDrawer() {
        const body        = document.getElementById("cartDrawerBody");
        const subtotalEl  = document.getElementById("drawerSubtotal");
        const discountRow = document.getElementById("drawerDiscountRow");
        const discountEl  = document.getElementById("drawerDiscountVal");
        const totalEl     = document.getElementById("drawerTotal");
        if (!body) return;

        if (cart.length === 0) {
            body.innerHTML = `
                <div class="drawer-empty-msg">
                    <span>🛒</span>
                    <h4>Giỏ hàng của bạn đang trống!</h4>
                    <p>Hãy chọn mẫu giày ưng ý để đặt hàng ngay hôm nay.</p>
                    <a href="#danh-sach-giay" onclick="window.ShoesShop.closeCartDrawer()" class="drawer-shop-now-btn">
                        Mua sắm ngay →
                    </a>
                </div>
            `;
            if (subtotalEl) subtotalEl.textContent = "0 đ";
            if (totalEl)    totalEl.textContent    = "0 đ";
            if (discountRow) discountRow.style.display = "none";
            return;
        }

        let subtotal = 0;
        body.innerHTML = cart.map((item, idx) => {
            const itemTotal = item.price * item.quantity;
            subtotal += itemTotal;
            return `
                <div class="drawer-cart-item" data-idx="${idx}">
                    <img class="drawer-item-img" src="${item.image}" alt="${item.name}"
                        onerror="this.src='https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=200&q=60'">
                    <div class="drawer-item-details">
                        <div class="drawer-item-name">${item.name}</div>
                        <div class="drawer-item-meta">${item.brand} • Size: <b>${item.size}</b></div>
                        <div class="drawer-item-bottom">
                            <span class="drawer-item-price">${formatCurrency(item.price)}</span>
                            <div class="drawer-qty-control">
                                <button type="button" class="drawer-qty-btn" onclick="window.ShoesShop.updateCartQty(${idx}, -1)">-</button>
                                <span class="drawer-qty-val">${item.quantity}</span>
                                <button type="button" class="drawer-qty-btn" onclick="window.ShoesShop.updateCartQty(${idx}, 1)">+</button>
                            </div>
                            <button type="button" class="drawer-item-remove" onclick="window.ShoesShop.removeCartItem(${idx})" title="Xóa khỏi giỏ">🗑️</button>
                        </div>
                        <div class="drawer-item-subtotal">
                            Thành tiền: <strong>${formatCurrency(itemTotal)}</strong>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        // Voucher input trong drawer
        if (!document.getElementById("drawerVoucherInput")) {
            body.innerHTML += `
                <div class="drawer-voucher-wrap">
                    <input type="text" id="drawerVoucherInput" class="drawer-voucher-field"
                        placeholder="Nhập mã giảm giá (VD: CHAOBANMOI)" maxlength="30">
                    <button type="button" class="drawer-voucher-btn"
                        onclick="window.ShoesShop.applyVoucherCode(document.getElementById('drawerVoucherInput').value)">
                        Áp dụng
                    </button>
                </div>
            `;
        }

        const discountAmount = Math.round(subtotal * appliedDiscount);
        const finalTotal     = Math.max(0, subtotal - discountAmount);

        if (subtotalEl) subtotalEl.textContent = formatCurrency(subtotal);
        if (discountRow && discountEl) {
            if (appliedDiscount > 0) {
                discountRow.style.display = "flex";
                discountEl.textContent = `- ${formatCurrency(discountAmount)} (10%)`;
            } else {
                discountRow.style.display = "none";
            }
        }
        if (totalEl) totalEl.textContent = formatCurrency(finalTotal);
    }

    function updateCartQty(index, delta) {
        if (!cart[index]) return;
        cart[index].quantity += delta;
        if (cart[index].quantity <= 0) cart.splice(index, 1);
        saveCart();
        renderCartDrawer();
    }

    function removeCartItem(index) {
        if (!cart[index]) return;
        const name = cart[index].name;
        cart.splice(index, 1);
        saveCart();
        renderCartDrawer();
        showToast(`🗑️ Đã xóa <b>${name}</b> khỏi giỏ hàng`);
    }

    function applyVoucherCode(code) {
        code = (code || "").trim().toUpperCase();
        if (code === "CHAOBANMOI") {
            appliedDiscount = 0.1;
            renderCartDrawer();
            showToast("🎉 Áp dụng mã <b>CHAOBANMOI</b> thành công! Giảm 10% tổng đơn hàng.");
        } else if (code === "") {
            showToast("⚠️ Vui lòng nhập mã giảm giá!");
        } else {
            showToast("⚠️ Mã giảm giá không hợp lệ hoặc đã hết hạn!");
        }
    }

    // =========================================================================
    // QUICK VIEW MODAL
    // =========================================================================

    function openQuickView(productId) {
        const product = products.find(p => p.id === productId);
        if (!product) return;
        const modal = document.getElementById("quickViewModal");
        if (!modal) return;

        document.getElementById("qvImage").src   = product.image;
        document.getElementById("qvBrand").textContent = product.brand;
        document.getElementById("qvTitle").textContent = product.name;
        document.getElementById("qvPrice").textContent = formatCurrency(product.price);
        document.getElementById("qvDesc").textContent  = product.description;

        // Rating và sold count
        const qvRating = document.getElementById("qvRating");
        if (qvRating) qvRating.innerHTML = `⭐ ${product.rating} · ${product.soldCount} đã bán`;

        // Stock indicator
        const qvStock = document.getElementById("qvStock");
        if (qvStock) {
            if (product.stock <= 0) {
                qvStock.innerHTML = `<span style="color:#ef4444;font-weight:700">❌ Hết hàng</span>`;
            } else if (product.stock <= 5) {
                qvStock.innerHTML = `<span style="color:#f59e0b;font-weight:700">⚠️ Còn ${product.stock} đôi cuối</span>`;
            } else {
                qvStock.innerHTML = `<span style="color:#10b981;font-weight:700">✅ Còn hàng (${product.stock} đôi)</span>`;
            }
        }

        const currentSize  = selectedSizes[product.id] || product.sizes[0] || 40;
        window.ShoesShop.qvCurrentSize = currentSize;

        const sizeContainer = document.getElementById("qvSizes");
        if (sizeContainer) {
            sizeContainer.innerHTML = product.sizes.map(s => `
                <button type="button" class="qv-size-btn ${s === currentSize ? 'active' : ''}"
                    onclick="window.ShoesShop.selectQvSize(${s}, this)">${s}</button>
            `).join('');
        }

        // Wishlist button in quick view
        const qvWishBtn = document.getElementById("qvWishlistBtn");
        if (qvWishBtn) {
            const wl = isWishlisted(product.id);
            qvWishBtn.innerHTML = wl ? "❤️ Đã lưu" : "🤍 Lưu yêu thích";
            qvWishBtn.className = `qv-wishlist-btn${wl ? " active" : ""}`;
            qvWishBtn.onclick = () => {
                toggleWishlist(product.id, qvWishBtn);
                const wlNew = isWishlisted(product.id);
                qvWishBtn.innerHTML = wlNew ? "❤️ Đã lưu" : "🤍 Lưu yêu thích";
                qvWishBtn.className = `qv-wishlist-btn${wlNew ? " active" : ""}`;
            };
        }

        const btnAdd = document.getElementById("qvBtnAddCart");
        if (btnAdd) {
            if (product.stock <= 0) {
                btnAdd.disabled = true;
                btnAdd.innerHTML = "<span>❌</span> Hết hàng";
                btnAdd.style.opacity = "0.5";
            } else {
                btnAdd.disabled = false;
                btnAdd.innerHTML = "<span>🛒</span> Thêm vào giỏ hàng";
                btnAdd.style.opacity = "1";
                btnAdd.onclick = () => {
                    addToCart(product.id, window.ShoesShop.qvCurrentSize || currentSize);
                    flyToCart(btnAdd);
                    closeQuickView();
                    openCartDrawer();
                };
            }
        }

        modal.classList.add("active");
    }

    function closeQuickView() {
        const modal = document.getElementById("quickViewModal");
        if (modal) modal.classList.remove("active");
    }

    // =========================================================================
    // TOAST NOTIFICATION
    // =========================================================================

    let toastTimeout;
    function showToast(htmlMsg) {
        const toast = document.getElementById("shopToast");
        if (!toast) return;
        toast.innerHTML = htmlMsg;
        toast.className = "shop-toast show success";
        clearTimeout(toastTimeout);
        toastTimeout = setTimeout(() => {
            toast.className = "shop-toast";
        }, 3200);
    }

    // =========================================================================
    // PHIÊN KHÁCH HÀNG
    // =========================================================================

    function checkCustomerSession() {
        const authBtn   = document.getElementById("headerAuthBtn");
        const loggedPill = document.getElementById("headerLoggedPill");
        if (!authBtn || !loggedPill) return;

        let session = null;
        try {
            const raw = sessionStorage.getItem(CUSTOMER_SESSION_KEY) ||
                        localStorage.getItem(CUSTOMER_SESSION_KEY) ||
                        sessionStorage.getItem(COMPAT_SESSION_KEY);
            if (raw) session = JSON.parse(raw);
        } catch { session = null; }

        if (session && session.name) {
            authBtn.style.display = "none";
            loggedPill.style.display = "inline-flex";

            const nameEl    = document.getElementById("headerCustName");
            const tierEl    = document.getElementById("headerCustTier");
            const avatarEl  = document.getElementById("headerCustAvatar");
            const dropName  = document.getElementById("dropCustName");
            const dropPoints = document.getElementById("dropCustPoints");

            if (nameEl)     nameEl.textContent   = session.name;
            if (tierEl)     tierEl.textContent   = `Hạng ${session.tier || 'Thành viên'}`;
            if (avatarEl)   avatarEl.textContent = (session.name.charAt(0) || "K").toUpperCase();
            if (dropName)   dropName.textContent = session.name;
            if (dropPoints) dropPoints.textContent = `⭐ ${(session.points || 100).toLocaleString('vi-VN')} điểm`;
        } else {
            authBtn.style.display = "inline-flex";
            loggedPill.style.display = "none";
        }
    }

    function logoutCustomer() {
        sessionStorage.removeItem(CUSTOMER_SESSION_KEY);
        sessionStorage.removeItem(COMPAT_SESSION_KEY);
        localStorage.removeItem(CUSTOMER_SESSION_KEY);
        window.location.reload();
    }

    // =========================================================================
    // KHỞI TẠO
    // =========================================================================

    document.addEventListener("DOMContentLoaded", () => {
        loadWishlist();
        loadCart();
        checkCustomerSession();
        updateWishlistBadge();

        // Hiển thị catalog mặc định ngay lập tức (UX tốt)
        loadProductsFromStorage();
        renderProductGrid();

        // Sau đó đồng bộ từ API (nền)
        loadProductsFromAPI();

        // Brand tabs
        document.querySelectorAll(".brand-tab").forEach(tab => {
            tab.addEventListener("click", function () {
                document.querySelectorAll(".brand-tab").forEach(t => t.classList.remove("active"));
                this.classList.add("active");
                activeBrand = this.getAttribute("data-brand") || "all";
                renderProductGrid();
            });
        });

        // Category select
        const catSelect = document.getElementById("filterCategory");
        if (catSelect) catSelect.addEventListener("change", function () {
            activeCategory = this.value;
            renderProductGrid();
        });

        // Price select
        const priceSelect = document.getElementById("filterPrice");
        if (priceSelect) priceSelect.addEventListener("change", function () {
            activePriceRange = this.value;
            renderProductGrid();
        });

        // Sort select
        const sortSelect = document.getElementById("filterSort");
        if (sortSelect) sortSelect.addEventListener("change", function () {
            activeSort = this.value;
            renderProductGrid();
        });

        // Search input
        const searchInput = document.getElementById("shopSearchInput");
        const clearBtn    = document.getElementById("searchClearBtn");
        if (searchInput) {
            searchInput.addEventListener("input", function () {
                searchQuery = this.value;
                if (clearBtn) clearBtn.style.display = searchQuery ? "block" : "none";
                renderProductGrid();
            });
            if (clearBtn) {
                clearBtn.addEventListener("click", function () {
                    searchInput.value = "";
                    searchQuery = "";
                    clearBtn.style.display = "none";
                    renderProductGrid();
                });
            }
        }

        // Cart drawer
        const cartBtn      = document.getElementById("headerCartBtn");
        const closeCartBtn = document.getElementById("btnCloseCartDrawer");
        const overlay      = document.getElementById("cartDrawerOverlay");
        if (cartBtn)      cartBtn.addEventListener("click", openCartDrawer);
        if (closeCartBtn) closeCartBtn.addEventListener("click", closeCartDrawer);
        if (overlay)      overlay.addEventListener("click", closeCartDrawer);

        // Wishlist drawer button (nếu có)
        const wishlistBtn = document.getElementById("headerWishlistBtn");
        if (wishlistBtn) {
            wishlistBtn.addEventListener("click", () => {
                showToast(`❤️ Bạn có ${wishlist.length} sản phẩm yêu thích`);
            });
        }

        // Quick view close
        const closeQvBtn = document.getElementById("btnCloseQuickView");
        const qvOverlay  = document.getElementById("quickViewModal");
        if (closeQvBtn) closeQvBtn.addEventListener("click", closeQuickView);
        if (qvOverlay) {
            qvOverlay.addEventListener("click", e => {
                if (e.target === qvOverlay) closeQuickView();
            });
        }

        // Đăng xuất
        const logoutBtn = document.getElementById("dropLogoutBtn");
        if (logoutBtn) logoutBtn.addEventListener("click", logoutCustomer);

        // Copy voucher
        const voucherBtn = document.getElementById("btnCopyVoucher");
        if (voucherBtn) {
            voucherBtn.addEventListener("click", function () {
                navigator.clipboard?.writeText("CHAOBANMOI");
                showToast("📋 Đã copy mã giảm giá: <b>CHAOBANMOI</b> (-10%)!");
            });
        }

        // Sync button nếu có
        const syncBtn = document.getElementById("btnSyncShop");
        if (syncBtn) {
            syncBtn.addEventListener("click", () => {
                syncBtn.disabled = true;
                syncBtn.textContent = "🔄 Đang đồng bộ...";
                loadProductsFromAPI().finally(() => {
                    syncBtn.disabled = false;
                    syncBtn.textContent = "🔄 Đồng bộ";
                });
            });
        }

        // Keyboard: Esc để đóng modal / drawer
        document.addEventListener("keydown", e => {
            if (e.key === "Escape") {
                closeQuickView();
                closeCartDrawer();
            }
        });
    });

    // =========================================================================
    // PUBLIC API
    // =========================================================================
    window.ShoesShop = {
        loadProducts:       loadProductsFromAPI,
        renderProductGrid,
        addToCart,
        addToCartAnimated,
        buyNow,
        openCartDrawer,
        closeCartDrawer,
        openQuickView,
        closeQuickView,
        toggleWishlist,
        updateCartQty,
        removeCartItem,
        applyVoucherCode,
        qvCurrentSize: null,
        selectSize: function (id, size, btn) {
            selectedSizes[id] = size;
            const parent = btn.parentElement;
            if (parent) {
                parent.querySelectorAll(".card-size-chip").forEach(c => c.classList.remove("selected"));
                btn.classList.add("selected");
            }
        },
        selectQvSize: function (size, btn) {
            window.ShoesShop.qvCurrentSize = size;
            const parent = btn.parentElement;
            if (parent) {
                parent.querySelectorAll(".qv-size-btn").forEach(c => c.classList.remove("active"));
                btn.classList.add("active");
            }
        },
        resetFilters: function () {
            activeBrand = "all"; activeCategory = "all";
            activePriceRange = "all"; activeSort = "popular"; searchQuery = "";
            const searchInput = document.getElementById("shopSearchInput");
            if (searchInput) searchInput.value = "";
            document.querySelectorAll(".brand-tab").forEach(t => {
                t.classList.toggle("active", t.getAttribute("data-brand") === "all");
            });
            const catSelect   = document.getElementById("filterCategory");
            const priceSelect = document.getElementById("filterPrice");
            const sortSelect  = document.getElementById("filterSort");
            if (catSelect)   catSelect.value   = "all";
            if (priceSelect) priceSelect.value = "all";
            if (sortSelect)  sortSelect.value  = "popular";
            renderProductGrid();
        }
    };
})();
