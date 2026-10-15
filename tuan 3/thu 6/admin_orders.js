/**
 * SHOES STORE - ADMIN ORDERS MANAGEMENT JAVASCRIPT
 */

"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const sessionKey = "shoesAdminSession";
    const orderKey = "shoesOrders";

    // 1. Kiểm tra phiên đăng nhập demo (Tự động khởi tạo phiên demo nếu mở trực tiếp)
    let session;
    try {
        session = JSON.parse(sessionStorage.getItem(sessionKey) || "null");
    } catch {
        session = null;
    }

    if (!session || session.role !== "admin") {
        session = {
            id: 1,
            name: "Admin Quản Trị",
            email: "admin@gmail.com",
            role: "admin"
        };
        sessionStorage.setItem(sessionKey, JSON.stringify(session));
    }

    const adminNameEl = document.getElementById("adminName") || document.getElementById("adminUser");
    if (adminNameEl) {
        adminNameEl.textContent = session.name || "Quản trị hệ thống";
    }

    const logoutBtn = document.getElementById("logoutBtn");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", () => {
            if (confirm("Bạn có chắc muốn đăng xuất?")) {
                sessionStorage.removeItem(sessionKey);
                window.location.replace("./admin_login.html");
            }
        });
    }

    // 2. DOM Elements
    const orderListTbody = document.getElementById("orderList") || document.getElementById("orderTable");
    const preorderListTbody = document.getElementById("preorderList");
    const modal = document.getElementById("detailModal") || document.getElementById("orderModal");
    const orderDetailContent = document.getElementById("orderDetail") || document.getElementById("orderDetails");
    const notice = document.getElementById("notice");
    const searchInput = document.getElementById("searchOrder") || document.getElementById("searchInput");
    const statusFilter = document.getElementById("statusFilter");
    const typeFilter = document.getElementById("typeFilter");
    const closeModalBtn = document.getElementById("closeModal") || document.getElementById("closeModalBtn");
    const closeDetailBtn = document.getElementById("closeDetailBtn") || document.getElementById("cancelModalBtn");

    const totalOrdersEl = document.getElementById("totalOrders");
    const preorderCountEl = document.getElementById("preorderCount");
    const pendingCountEl = document.getElementById("pendingCount") || document.getElementById("pendingOrders");
    const completedCountEl = document.getElementById("completedCount") || document.getElementById("completedOrders");

    const waitingStockEl = document.getElementById("waitingStockCount");
    const arrivedCountEl = document.getElementById("arrivedCount");
    const readyCountEl = document.getElementById("readyCount");

    // 3. Dữ liệu mẫu khởi tạo chuẩn
    function createDemoOrders() {
        const today = new Date().toLocaleDateString("vi-VN");
        return [
            {
                id: "DH1001",
                customer: "Nguyễn Văn An",
                phone: "0901234567",
                product: "Nike Air Force 1 '07",
                variant: "Trắng / Size 41",
                quantity: 1,
                date: today,
                expectedDate: "20/10/2026",
                total: 2690000,
                type: "Pre-order",
                preorderStatus: "Đang chờ hàng",
                status: "Pre-order"
            },
            {
                id: "DH1002",
                customer: "Trần Minh Đức",
                phone: "0987654321",
                product: "Adidas Ultraboost Light",
                variant: "Đen / Size 42",
                quantity: 1,
                date: today,
                expectedDate: "18/10/2026",
                total: 3200000,
                type: "Pre-order",
                preorderStatus: "Hàng đã về",
                status: "Đã có hàng"
            },
            {
                id: "DH1003",
                customer: "Lê Hoàng Nam",
                phone: "0912345678",
                product: "Puma RS-X Reinvention",
                variant: "Đỏ/Trắng / Size 40",
                quantity: 2,
                date: today,
                expectedDate: "—",
                total: 3900000,
                type: "Có sẵn",
                preorderStatus: "—",
                status: "Chờ xác nhận"
            },
            {
                id: "DH1004",
                customer: "Phạm Quốc Bảo",
                phone: "0934567890",
                product: "Nike Jordan 1 Retro High",
                variant: "Đỏ/Đen / Size 42",
                quantity: 1,
                date: today,
                expectedDate: "—",
                total: 4500000,
                type: "Có sẵn",
                preorderStatus: "—",
                status: "Hoàn thành"
            },
            {
                id: "DH1005",
                customer: "Vũ Thị Mai",
                phone: "0945678901",
                product: "Asics Gel-Kayano 29",
                variant: "Xanh dương / Size 39",
                quantity: 1,
                date: today,
                expectedDate: "22/10/2026",
                total: 2890000,
                type: "Pre-order",
                preorderStatus: "Sẵn sàng nhận",
                status: "Sẵn sàng nhận"
            }
        ];
    }

    let orders = loadOrders();

    function loadOrders() {
        try {
            const saved = JSON.parse(localStorage.getItem(orderKey) || "null");
            if (Array.isArray(saved) && saved.length > 0) {
                return saved;
            }
        } catch {
            // fallback
        }
        const initial = createDemoOrders();
        localStorage.setItem(orderKey, JSON.stringify(initial));
        return initial;
    }

    function saveOrders() {
        localStorage.setItem(orderKey, JSON.stringify(orders));
    }

    function escapeHTML(value) {
        return String(value ?? "").replace(/[&<>"']/g, char => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        })[char]);
    }

    function money(value) {
        return Number(value || 0).toLocaleString("vi-VN") + " ₫";
    }

    function showNotice(message, type = "success") {
        if (!notice) return;
        notice.textContent = message;
        notice.className = "notice show " + type;
        setTimeout(() => {
            notice.className = "notice";
        }, 3000);
    }

    function getBadgeClass(status) {
        if (status === "Hoàn thành") return "badge-success";
        if (status === "Đã hủy") return "badge-danger";
        if (status === "Chờ xác nhận" || status === "Đang chuẩn bị hàng") return "badge-warning";
        return "badge-info";
    }

    function renderStats() {
        if (totalOrdersEl) totalOrdersEl.textContent = orders.length;
        if (preorderCountEl) preorderCountEl.textContent = orders.filter(o => o.type === "Pre-order").length;
        if (pendingCountEl) pendingCountEl.textContent = orders.filter(o => o.status === "Chờ xác nhận").length;
        if (completedCountEl) completedCountEl.textContent = orders.filter(o => o.status === "Hoàn thành").length;

        // Thống kê Pre-order
        if (waitingStockEl) waitingStockEl.textContent = orders.filter(o => o.preorderStatus === "Đang chờ hàng").length;
        if (arrivedCountEl) arrivedCountEl.textContent = orders.filter(o => o.preorderStatus === "Hàng đã về").length;
        if (readyCountEl) readyCountEl.textContent = orders.filter(o => o.preorderStatus === "Sẵn sàng nhận").length;
    }

    function renderPreorders() {
        if (!preorderListTbody) return;
        const preorders = orders.filter(o => o.type === "Pre-order");

        if (preorders.length === 0) {
            preorderListTbody.innerHTML = `<tr><td colspan="4" style="text-align:center; padding:20px; color:#64748b;">Chưa có đơn đặt trước (Pre-order).</td></tr>`;
            return;
        }

        preorderListTbody.innerHTML = preorders.map(o => `
            <tr>
                <td><strong>#${escapeHTML(o.id)}</strong></td>
                <td>
                    <span class="product-name">${escapeHTML(o.product)}</span>
                    <span class="sub-text">${escapeHTML(o.variant)}</span>
                </td>
                <td>${escapeHTML(o.expectedDate || "Đang cập nhật")}</td>
                <td>
                    <span class="badge ${o.preorderStatus === 'Sẵn sàng nhận' ? 'badge-success' : 'badge-warning'}">
                        ${escapeHTML(o.preorderStatus || "Đang chờ hàng")}
                    </span>
                </td>
            </tr>
        `).join("");
    }

    function renderOrders() {
        if (!orderListTbody) return;

        const keyword = searchInput ? searchInput.value.trim().toLowerCase() : "";
        const statusVal = statusFilter ? statusFilter.value : "";
        const typeVal = typeFilter ? typeFilter.value : "";

        const filtered = orders.filter(order => {
            const text = [
                order.id,
                order.customer,
                order.phone,
                order.product,
                order.variant
            ].join(" ").toLowerCase();

            const matchKeyword = !keyword || text.includes(keyword);
            const matchStatus = !statusVal || order.status === statusVal;
            const matchType = !typeVal || order.type === typeVal;

            return matchKeyword && matchStatus && matchType;
        });

        if (filtered.length === 0) {
            orderListTbody.innerHTML = `
                <tr>
                    <td colspan="8" style="text-align:center; padding:30px; color:#64748b;">
                        Không tìm thấy đơn hàng phù hợp.
                    </td>
                </tr>
            `;
            renderStats();
            return;
        }

        orderListTbody.innerHTML = filtered.map(order => `
            <tr>
                <td><strong>#${escapeHTML(order.id)}</strong></td>
                <td>
                    <span class="product-name">${escapeHTML(order.customer || "Khách hàng")}</span>
                    <span class="sub-text">${escapeHTML(order.phone || "—")}</span>
                </td>
                <td>
                    <span class="product-name">${escapeHTML(order.product || "Sản phẩm")}</span>
                    <span class="sub-text">${escapeHTML(order.variant || "")} ${order.quantity ? `· SL: ${order.quantity}` : ""}</span>
                </td>
                <td>${escapeHTML(order.date || "—")}</td>
                <td class="price">${money(order.total)}</td>
                <td>
                    <span class="badge ${order.type === 'Pre-order' ? 'badge-info' : 'badge-secondary'}">
                        ${escapeHTML(order.type || "Có sẵn")}
                    </span>
                </td>
                <td>
                    <span class="badge ${getBadgeClass(order.status)}">
                        ${escapeHTML(order.status || "Chờ xác nhận")}
                    </span>
                </td>
                <td>
                    <button class="btn btn-secondary" type="button" data-action="view" data-id="${escapeHTML(order.id)}">
                        Chi tiết
                    </button>
                </td>
            </tr>
        `).join("");

        renderStats();
        renderPreorders();
    }

    function openOrderDetail(order) {
        if (!modal || !orderDetailContent) return;

        orderDetailContent.innerHTML = `
            <div class="form-group">
                <label>Mã đơn hàng</label>
                <div>#${escapeHTML(order.id)}</div>
            </div>
            <div class="form-group">
                <label>Khách hàng</label>
                <div>${escapeHTML(order.customer || "Khách hàng")}</div>
            </div>
            <div class="form-group">
                <label>Số điện thoại</label>
                <div>${escapeHTML(order.phone || "Chưa cập nhật")}</div>
            </div>
            <div class="form-group">
                <label>Sản phẩm</label>
                <div>${escapeHTML(order.product || "Sản phẩm")}</div>
            </div>
            <div class="form-group">
                <label>Biến thể (Size / Màu)</label>
                <div>${escapeHTML(order.variant || "Tiêu chuẩn")} (${order.quantity || 1} đôi)</div>
            </div>
            <div class="form-group">
                <label>Ngày đặt hàng</label>
                <div>${escapeHTML(order.date || "—")}</div>
            </div>
            <div class="form-group">
                <label>Loại đơn hàng</label>
                <div>${escapeHTML(order.type || "Hàng có sẵn")}</div>
            </div>
            <div class="form-group">
                <label>Trạng thái</label>
                <div>
                    <select id="modalOrderStatus" style="padding:6px 10px; border:1px solid #cbd5e1; border-radius:6px; font-weight:600;">
                        <option value="Chờ xác nhận" ${order.status === "Chờ xác nhận" ? "selected" : ""}>Chờ xác nhận</option>
                        <option value="Đang chuẩn bị hàng" ${order.status === "Đang chuẩn bị hàng" ? "selected" : ""}>Đang chuẩn bị hàng</option>
                        <option value="Đã có hàng" ${order.status === "Đang có hàng" || order.status === "Đã có hàng" ? "selected" : ""}>Đã có hàng</option>
                        <option value="Sẵn sàng nhận" ${order.status === "Sẵn sàng nhận" ? "selected" : ""}>Sẵn sàng nhận</option>
                        <option value="Hoàn thành" ${order.status === "Hoàn thành" ? "selected" : ""}>Hoàn thành</option>
                        <option value="Đã hủy" ${order.status === "Đã hủy" ? "selected" : ""}>Đã hủy</option>
                    </select>
                </div>
            </div>
            <div class="form-group" style="border-bottom:none; margin-top:10px;">
                <label>Tổng thanh toán</label>
                <div class="price" style="font-size:16px;">${money(order.total)}</div>
            </div>
        `;

        const statusSelect = document.getElementById("modalOrderStatus");
        if (statusSelect) {
            statusSelect.addEventListener("change", () => {
                order.status = statusSelect.value;
                if (order.type === "Pre-order") {
                    if (order.status === "Sẵn sàng nhận") order.preorderStatus = "Sẵn sàng nhận";
                    else if (order.status === "Đã có hàng") order.preorderStatus = "Hàng đã về";
                    else if (order.status === "Hoàn thành") order.preorderStatus = "Đã hoàn thành";
                }
                saveOrders();
                renderOrders();
                showNotice("Đã cập nhật trạng thái đơn hàng thành công!");
            });
        }

        modal.removeAttribute("hidden");
    }

    function closeModal() {
        if (modal) modal.setAttribute("hidden", "");
    }

    if (closeModalBtn) closeModalBtn.addEventListener("click", closeModal);
    if (closeDetailBtn) closeDetailBtn.addEventListener("click", closeModal);
    if (modal) {
        modal.addEventListener("click", e => {
            if (e.target === modal) closeModal();
        });
    }

    if (searchInput) searchInput.addEventListener("input", renderOrders);
    if (statusFilter) statusFilter.addEventListener("change", renderOrders);
    if (typeFilter) typeFilter.addEventListener("change", renderOrders);

    if (orderListTbody) {
        orderListTbody.addEventListener("click", e => {
            const btn = e.target.closest("button[data-action='view']");
            if (!btn) return;
            const orderId = btn.dataset.id;
            const order = orders.find(o => String(o.id) === String(orderId));
            if (order) openOrderDetail(order);
        });
    }

    renderOrders();
});