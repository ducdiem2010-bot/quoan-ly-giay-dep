/* JavaScript dùng chung cho 4 trang HTML; dữ liệu mẫu, chưa kết nối backend. */
(function (root, factory) {
    const api = factory(root);
    if (typeof module === 'object' && module.exports) module.exports = api;
    if (root.document) {
        root.ShoesStore = api;
        if (root.document.readyState === 'loading') {
            root.document.addEventListener('DOMContentLoaded', api.init);
        } else {
            api.init();
        }
    }
})(typeof window !== 'undefined' ? window : globalThis, function (root) {
    'use strict';

    const STORAGE_KEY = 'shoes_store_lien_ket_v1';
    const SIZES = [39, 40, 41, 42, 43];
    const MAX_QUANTITY = 99;
    const CATALOG = [
        { id: 'SP001', name: 'Nike Air Force 1', brand: 'Nike', price: 2500000,
          description: 'Giày Nike Air Force 1 thiết kế trẻ trung, phù hợp sử dụng hàng ngày.' },
        { id: 'SP002', name: 'Adidas Superstar', brand: 'Adidas', price: 2000000,
          description: 'Mẫu Adidas Superstar trong danh sách sản phẩm của SHOES STORE.' },
        { id: 'SP003', name: 'Puma Suede', brand: 'Puma', price: 1800000,
          description: 'Mẫu Puma Suede trong danh sách sản phẩm của SHOES STORE.' },
        { id: 'SP004', name: 'Asics Gel', brand: 'Asics', price: 2300000,
          description: 'Mẫu Asics Gel trong danh sách sản phẩm của SHOES STORE.' }
    ];
    const SAMPLE_CART = [
        { productId: 'SP001', size: 42, quantity: 1 },
        { productId: 'SP002', size: 41, quantity: 1 }
    ];
    let cart = null;
    let initialized = false;

    function productById(id) {
        return CATALOG.find(function (product) { return product.id === id; });
    }
    function validQuantity(value) {
        if (typeof value === 'string' && !/^[1-9]\d*$/.test(value.trim())) return false;
        if (typeof value !== 'string' && typeof value !== 'number') return false;
        const number = Number(value);
        return Number.isInteger(number) && number >= 1 && number <= MAX_QUANTITY;
    }
    function itemKey(item) { return item.productId + ':' + item.size; }
    function normalizeCart(items) {
        if (!Array.isArray(items)) return [];
        const result = [];
        items.forEach(function (item) {
            if (!item || typeof item !== 'object') return;
            if (!productById(item.productId) || !SIZES.includes(Number(item.size))) return;
            if (!validQuantity(item.quantity)) return;
            const clean = { productId: item.productId, size: Number(item.size), quantity: Number(item.quantity) };
            const existing = result.find(function (row) { return itemKey(row) === itemKey(clean); });
            if (existing) existing.quantity = Math.min(MAX_QUANTITY, existing.quantity + clean.quantity);
            else result.push(clean);
        });
        return result;
    }
    function totals(items) {
        return normalizeCart(items).reduce(function (sum, item) {
            sum.quantity += item.quantity;
            sum.amount += productById(item.productId).price * item.quantity;
            return sum;
        }, { quantity: 0, amount: 0 });
    }
    function money(amount) { return Number(amount).toLocaleString('vi-VN') + ' VNĐ'; }
    function validateContact(name, phone) {
        const errors = {};
        if (String(name || '').trim().length < 2 || String(name).trim().length > 60) {
            errors.name = 'Vui lòng nhập họ tên từ 2 đến 60 ký tự.';
        }
        const cleanPhone = String(phone || '').replace(/[\s().-]/g, '');
        if (!/^0\d{9}$/.test(cleanPhone)) {
            errors.phone = 'Số điện thoại cần có 10 chữ số và bắt đầu bằng 0.';
        }
        return errors;
    }
    function isFilePage() { return root.location && root.location.protocol === 'file:'; }
    function loadCart() {
        // Khi mở file trực tiếp, liên kết mang theo giỏ để các trang vẫn dùng cùng dữ liệu.
        if (isFilePage()) {
            try {
                const incoming = new URL(root.location.href).searchParams.get('gio');
                if (incoming !== null) {
                    const parsed = JSON.parse(incoming);
                    if (Array.isArray(parsed)) return normalizeCart(parsed);
                }
            } catch (error) { /* Tiếp tục đọc giỏ đã lưu nếu tham số không hợp lệ. */ }
        }
        try {
            const stored = root.localStorage.getItem(STORAGE_KEY);
            if (stored !== null) {
                const parsed = JSON.parse(stored);
                if (Array.isArray(parsed)) return normalizeCart(parsed);
            }
        } catch (error) { /* Vẫn dùng được giỏ trong bộ nhớ nếu không có localStorage. */ }
        return normalizeCart(SAMPLE_CART);
    }
    function getCart() {
        if (cart === null) cart = loadCart();
        return cart.map(function (item) { return Object.assign({}, item); });
    }
    function writeCart(items) {
        cart = normalizeCart(items);
        try { root.localStorage.setItem(STORAGE_KEY, JSON.stringify(cart)); } catch (error) {}
        if (isFilePage()) {
            try {
                const url = new URL(root.location.href);
                url.searchParams.set('gio', JSON.stringify(cart));
                root.history.replaceState(null, '', url.href);
            } catch (error) {}
        }
        refresh();
    }
    function add(productId, size, quantity) {
        if (!productById(productId)) return { ok: false, message: 'Sản phẩm không tồn tại.' };
        if (!SIZES.includes(Number(size))) return { ok: false, message: 'Vui lòng chọn size.' };
        if (!validQuantity(quantity)) return { ok: false, message: 'Số lượng phải là số nguyên từ 1 đến 99.' };
        const items = getCart();
        const selected = { productId: productId, size: Number(size), quantity: Number(quantity) };
        const existing = items.find(function (item) { return itemKey(item) === itemKey(selected); });
        if (existing && existing.quantity + selected.quantity > MAX_QUANTITY) {
            return { ok: false, message: 'Số lượng của một sản phẩm cùng size không được vượt quá 99.' };
        }
        if (existing) existing.quantity += selected.quantity;
        else items.push(selected);
        writeCart(items);
        return { ok: true, message: 'Đã thêm sản phẩm vào giỏ hàng.' };
    }
    function setQuantity(key, value) {
        if (!validQuantity(value)) return false;
        const items = getCart();
        const item = items.find(function (row) { return itemKey(row) === key; });
        if (!item) return false;
        item.quantity = Number(value);
        writeCart(items);
        return true;
    }
    function remove(key) {
        writeCart(getCart().filter(function (item) { return itemKey(item) !== key; }));
    }
    function fileLink(path) {
        if (!isFilePage()) return path;
        const url = new URL(path, root.location.href);
        url.searchParams.set('gio', JSON.stringify(getCart()));
        return url.href;
    }
    function navigate(path) { root.location.assign(fileLink(path)); }
    function element(tag, className, text) {
        const node = root.document.createElement(tag);
        if (className) node.className = className;
        if (text !== undefined) node.textContent = text;
        return node;
    }
    function message(id, text, isError) {
        const node = root.document.getElementById(id);
        if (!node) return;
        node.textContent = text;
        node.classList.toggle('is-error', Boolean(isError));
        node.hidden = !text;
    }
    function detailPath(id) { return 'product_detail.html?id=' + encodeURIComponent(id); }
    function updateBadge() {
        const count = totals(getCart()).quantity;
        root.document.querySelectorAll('[data-cart-count]').forEach(function (node) { node.textContent = count; });
    }
    function renderCart() {
        const doc = root.document;
        const items = getCart();
        const sum = totals(items);
        doc.getElementById('cartEmpty').hidden = items.length > 0;
        doc.getElementById('cartContent').hidden = items.length === 0;
        doc.getElementById('subtotal').textContent = money(sum.amount);
        doc.getElementById('total').textContent = money(sum.amount);
        const list = doc.getElementById('cartItems');
        list.replaceChildren();
        items.forEach(function (item) {
            const product = productById(item.productId);
            const row = element('article', 'cart-item');
            row.dataset.key = itemKey(item);
            const photo = element('a', 'product-image', 'Ảnh giày');
            photo.href = detailPath(product.id);
            photo.setAttribute('aria-label', 'Xem ' + product.name);
            const info = element('div', 'product-info');
            const heading = element('h3');
            const link = element('a', '', product.name);
            link.href = detailPath(product.id);
            heading.append(link);
            info.append(heading, element('p', '', 'Size: ' + item.size),
                element('p', 'price', 'Đơn giá: ' + money(product.price)),
                element('p', 'item-total', 'Thành tiền: ' + money(product.price * item.quantity)));
            const controls = element('div', 'quantity');
            const minus = element('button', '', '−');
            minus.type = 'button';
            minus.dataset.action = 'minus';
            minus.disabled = item.quantity === 1;
            minus.setAttribute('aria-label', 'Giảm số lượng ' + product.name);
            const input = element('input');
            input.type = 'number'; input.min = '1'; input.max = '99'; input.step = '1'; input.value = item.quantity;
            input.dataset.action = 'quantity';
            input.setAttribute('aria-label', 'Số lượng ' + product.name + ', size ' + item.size);
            const plus = element('button', '', '+');
            plus.type = 'button'; plus.dataset.action = 'plus'; plus.disabled = item.quantity === 99;
            plus.setAttribute('aria-label', 'Tăng số lượng ' + product.name);
            controls.append(minus, input, plus);
            info.append(controls);
            const removeButton = element('button', 'remove', 'Xóa');
            removeButton.type = 'button'; removeButton.dataset.action = 'remove';
            removeButton.setAttribute('aria-label', 'Xóa ' + product.name + ', size ' + item.size);
            row.append(photo, info, removeButton);
            list.append(row);
        });
    }
    function renderCheckout() {
        const doc = root.document;
        const items = getCart();
        doc.getElementById('checkoutEmpty').hidden = items.length > 0;
        doc.getElementById('checkoutForm').hidden = items.length === 0;
        doc.getElementById('checkoutTotal').textContent = money(totals(items).amount);
        const list = doc.getElementById('orderItems');
        list.replaceChildren();
        items.forEach(function (item) {
            const product = productById(item.productId);
            const row = element('div', 'order-item');
            row.append(element('span', '', product.name + ' · Size ' + item.size + ' × ' + item.quantity),
                element('span', '', money(product.price * item.quantity)));
            list.append(row);
        });
        message('checkoutMessage', '', false);
    }
    function refresh() {
        if (!root.document) return;
        updateBadge();
        const page = root.document.body.dataset.page;
        if (page === 'cart') renderCart();
        if (page === 'checkout') renderCheckout();
    }
    function bindCart() {
        const list = root.document.getElementById('cartItems');
        list.addEventListener('click', function (event) {
            const button = event.target.closest('button[data-action]');
            if (!button) return;
            const key = button.closest('[data-key]').dataset.key;
            if (button.dataset.action === 'remove') { remove(key); message('cartMessage', 'Đã xóa sản phẩm.', false); return; }
            const item = getCart().find(function (row) { return itemKey(row) === key; });
            setQuantity(key, item.quantity + (button.dataset.action === 'plus' ? 1 : -1));
            message('cartMessage', '', false);
        });
        list.addEventListener('change', function (event) {
            if (event.target.dataset.action !== 'quantity') return;
            const key = event.target.closest('[data-key]').dataset.key;
            if (!setQuantity(key, event.target.value)) {
                const item = getCart().find(function (row) { return itemKey(row) === key; });
                event.target.value = item.quantity;
                message('cartMessage', 'Số lượng phải là số nguyên từ 1 đến 99.', true);
            } else message('cartMessage', '', false);
        });
    }
    function bindProduct() {
        const doc = root.document;
        const requestedId = new URL(root.location.href).searchParams.get('id') || 'SP001';
        const product = productById(requestedId);
        if (!product) {
            doc.getElementById('productName').textContent = 'Không tìm thấy sản phẩm';
            doc.getElementById('productCode').textContent = '';
            doc.getElementById('productPrice').textContent = '';
            doc.getElementById('productIntro').textContent = '';
            doc.getElementById('productLongDescription').textContent = '';
            doc.getElementById('addCart').disabled = true;
            doc.getElementById('buyNow').disabled = true;
            message('productMessage', 'Không tìm thấy sản phẩm. Vui lòng quay lại danh sách sản phẩm.', true);
            return;
        }
        doc.title = product.name + ' - Shoes Store';
        doc.getElementById('productName').textContent = product.name;
        doc.getElementById('productCode').textContent = 'Mã sản phẩm: ' + product.id;
        doc.getElementById('productPrice').textContent = money(product.price);
        doc.getElementById('productIntro').textContent = product.description;
        if (product.id !== 'SP001') doc.getElementById('productLongDescription').textContent = product.description;
        let selectedSize = null;
        doc.querySelectorAll('[data-size]').forEach(function (button) {
            button.addEventListener('click', function () {
                selectedSize = Number(button.dataset.size);
                doc.querySelectorAll('[data-size]').forEach(function (other) {
                    other.setAttribute('aria-pressed', String(other === button));
                });
                message('productMessage', '', false);
            });
        });
        const input = doc.getElementById('productQuantity');
        doc.getElementById('productMinus').addEventListener('click', function () {
            input.value = Math.max(1, (validQuantity(input.value) ? Number(input.value) : 1) - 1);
        });
        doc.getElementById('productPlus').addEventListener('click', function () {
            input.value = Math.min(99, (validQuantity(input.value) ? Number(input.value) : 1) + 1);
        });
        function addSelected(goToCart) {
            const result = add(product.id, selectedSize, input.value);
            message('productMessage', result.message, !result.ok);
            if (result.ok && goToCart) navigate('cart.html');
        }
        doc.getElementById('addCart').addEventListener('click', function () { addSelected(false); });
        doc.getElementById('buyNow').addEventListener('click', function () { addSelected(true); });
        const related = doc.getElementById('relatedList');
        related.replaceChildren();
        CATALOG.filter(function (other) { return other.id !== product.id; }).forEach(function (other) {
            const card = element('a', 'product-card');
            card.href = detailPath(other.id);
            card.append(element('div', 'card-image', 'ẢNH SP'), element('h3', '', other.name), element('p', '', money(other.price)));
            related.append(card);
        });
    }
    function bindHome() {
        const doc = root.document;
        const input = doc.getElementById('searchInput');
        function plain(value) { return value.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd'); }
        function search() {
            const query = plain(input.value.trim());
            let count = 0;
            doc.querySelectorAll('[data-product-card]').forEach(function (card) {
                const product = productById(card.dataset.productCard);
                card.hidden = !plain(product.name + ' ' + product.brand).includes(query);
                if (!card.hidden) count++;
            });
            doc.getElementById('searchStatus').textContent = count ? 'Có ' + count + ' sản phẩm.' : 'Không tìm thấy sản phẩm phù hợp.';
        }
        input.addEventListener('input', search);
        doc.getElementById('searchForm').addEventListener('submit', function (event) { event.preventDefault(); search(); });
    }
    function bindCheckout() {
        const doc = root.document;
        const form = doc.getElementById('checkoutForm');
        form.addEventListener('submit', function (event) {
            event.preventDefault();
            if (!getCart().length) { message('checkoutMessage', 'Giỏ hàng đang trống.', true); return; }
            const errors = validateContact(doc.getElementById('fullName').value, doc.getElementById('phone').value);
            doc.getElementById('fullName').setCustomValidity(errors.name || '');
            doc.getElementById('phone').setCustomValidity(errors.phone || '');
            if (!form.reportValidity()) { message('checkoutMessage', errors.name || errors.phone || 'Vui lòng kiểm tra thông tin đã nhập.', true); return; }
            message('checkoutMessage', 'Thông tin hợp lệ. Đây là bản mẫu; chưa gửi đơn đến cửa hàng.', false);
        });
        ['fullName', 'phone'].forEach(function (id) {
            doc.getElementById(id).addEventListener('input', function (event) { event.target.setCustomValidity(''); message('checkoutMessage', '', false); });
        });
    }
    function init() {
        if (initialized) return;
        initialized = true;
        getCart();
        const page = root.document.body.dataset.page;
        if (page === 'home') bindHome();
        if (page === 'product') bindProduct();
        if (page === 'cart') bindCart();
        if (page === 'checkout') bindCheckout();
        // Truyền giỏ qua liên kết file://; trên Live Server các trang dùng localStorage chung.
        root.document.addEventListener('click', function (event) {
            if (!isFilePage()) return;
            const anchor = event.target.closest('a[href]');
            if (!anchor) return;
            const url = new URL(anchor.getAttribute('href'), root.location.href);
            const current = new URL(root.location.href);
            if (url.protocol === 'file:' && url.pathname.endsWith('.html') &&
                url.pathname.slice(0, url.pathname.lastIndexOf('/')) === current.pathname.slice(0, current.pathname.lastIndexOf('/'))) {
                anchor.href = fileLink(url.href);
            }
        }, true);
        root.addEventListener('storage', function (event) {
            if (event.key === STORAGE_KEY && !isFilePage()) { cart = loadCart(); refresh(); }
        });
        refresh();
    }
    return { init: init, add: add, getCart: getCart, setQuantity: setQuantity, remove: remove,
        normalizeCart: normalizeCart, totals: totals, validQuantity: validQuantity,
        validateContact: validateContact, fileLink: fileLink, productById: productById };
});
