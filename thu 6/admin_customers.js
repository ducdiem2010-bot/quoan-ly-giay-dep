/**
 * ==========================================================================
 * SHOES STORE - ADMIN CUSTOMERS JAVASCRIPT
 * Quản lý thông tin khách hàng, phân hạng thành viên, chi tiêu và liên hệ
 * ==========================================================================
 */

document.addEventListener("DOMContentLoaded", function () {
    "use strict";

    // 1. Cấu hình
    const STORAGE_KEY = "shoesCustomers";
    const SYNC_KEY_USERS = "shoesUsers";
    const PAGE_SIZE = 6;
    const $ = id => document.getElementById(id);

    // 2. DOM Elements
    const dom = {
        total: $("totalCustomers"),
        vip: $("vipCustomers"),
        active: $("activeCustomers"),
        spent: $("totalSpent"),

        search: $("searchCustomer"),
        tierFilter: $("filterTier"),
        statusFilter: $("filterStatus"),
        sort: $("sortCustomer"),
        resetFilters: $("btnResetFilters"),
        resultCount: $("resultCount"),
        btnResetDemo: $("btnResetDemo"),

        tbody: $("customerTableBody"),
        pageInfo: $("paginationInfo"),
        pageNumber: $("currentPage"),
        prevPage: $("btnPrevPage"),
        nextPage: $("btnNextPage"),

        btnAddCustomer: $("btnAddCustomer"),
        modal: $("customerModal"),
        modalTitle: $("modalTitle"),
        form: $("customerForm"),
        closeModalBtn: $("btnCloseModal"),
        cancelModalBtn: $("btnCancelModal"),
        saveCustomerBtn: $("btnSaveCustomer"),

        // Form fields
        id: $("customerId"),
        code: $("customerCode"),
        name: $("customerName"),
        phone: $("customerPhone"),
        email: $("customerEmail"),
        address: $("customerAddress"),
        tier: $("customerTier"),
        status: $("customerStatus"),
        spentInput: $("customerSpent"),
        ordersCountInput: $("customerOrdersCount"),
        avatarFile: $("customerAvatarFile"),
        avatarUrl: $("customerAvatarUrl"),
        avatarPreview: $("customerAvatarPreview"),
        notes: $("customerNotes"),

        // View Modal
        viewModal: $("viewCustomerModal"),
        viewTitle: $("viewCustomerTitle"),
        viewSubtitle: $("viewCustomerSubtitle"),
        viewBody: $("viewCustomerBody"),
        closeViewBtn: $("btnCloseViewCustomer"),
        closeViewBtn2: $("btnCloseViewCustomerBtn"),

        toastContainer: $("toastContainer")
    };

    // 3. State
    let customers = [];
    let currentPage = 1;
    let selectedAvatar = "";
    let readerToken = 0;

    // Dữ liệu mẫu khởi tạo chuẩn
    const demoCustomers = [
        {
            id: "KH1001",
            name: "Nguyễn Văn An",
            phone: "0901234567",
            email: "an.nguyen@gmail.com",
            address: "123 Lê Lợi, Phường Bến Nghé, Quận 1, TP. Hồ Chí Minh",
            tier: "Kim cương",
            ordersCount: 8,
            spent: 18500000,
            points: 1850,
            status: "active",
            avatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=200&q=80",
            joinDate: "10/01/2026",
            notes: "Khách VIP thân thiết, thường mua giày Nike size 41"
        },
        {
            id: "KH1002",
            name: "Trần Minh Đức",
            phone: "0987654321",
            email: "duc.tran@gmail.com",
            address: "456 Nguyễn Thị Minh Khai, Phường 5, Quận 3, TP. Hồ Chí Minh",
            tier: "Vàng",
            ordersCount: 5,
            spent: 9800000,
            points: 980,
            status: "active",
            avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=200&q=80",
            joinDate: "15/01/2026",
            notes: "Đam mê dòng giày chạy bộ Adidas Ultraboost"
        },
        {
            id: "KH1003",
            name: "Lê Hoàng Nam",
            phone: "0912345678",
            email: "nam.le@gmail.com",
            address: "789 Hoàng Diệu, Phường 12, Quận 4, TP. Hồ Chí Minh",
            tier: "Bạc",
            ordersCount: 3,
            spent: 4650000,
            points: 465,
            status: "active",
            avatar: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=200&q=80",
            joinDate: "20/02/2026",
            notes: "Thích phong cách Chunky Sneaker của Puma"
        },
        {
            id: "KH1004",
            name: "Phạm Quốc Bảo",
            phone: "0934567890",
            email: "bao.pham@gmail.com",
            address: "12 Trần Hưng Đạo, Phường Phan Chu Trinh, Hoàn Kiếm, Hà Nội",
            tier: "Kim cương",
            ordersCount: 6,
            spent: 14200000,
            points: 1420,
            status: "active",
            avatar: "https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?auto=format&fit=crop&w=200&q=80",
            joinDate: "05/01/2026",
            notes: "Chuyên sưu tầm các dòng Jordan 1 Retro phiên bản giới hạn"
        },
        {
            id: "KH1005",
            name: "Vũ Thị Mai",
            phone: "0945678901",
            email: "mai.vu@gmail.com",
            address: "88 Cầu Giấy, Phường Quan Hoa, Quận Cầu Giấy, Hà Nội",
            tier: "Đồng",
            ordersCount: 1,
            spent: 2890000,
            points: 289,
            status: "active",
            avatar: "https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=200&q=80",
            joinDate: "01/03/2026",
            notes: "Khách hàng mới mua đơn Asics Gel"
        },
        {
            id: "KH1006",
            name: "Đỗ Thành Long",
            phone: "0967890123",
            email: "long.do@gmail.com",
            address: "56 Nguyễn Trãi, Quận Thanh Xuân, Hà Nội",
            tier: "Đồng",
            ordersCount: 1,
            spent: 1800000,
            points: 180,
            status: "inactive",
            avatar: "",
            joinDate: "12/03/2026",
            notes: "Tài khoản đang tạm khóa do khách yêu cầu đổi số điện thoại"
        }
    ];

    // 4. Helpers
    function escapeHTML(str) {
        return String(str ?? "").replace(/[&<>"']/g, c => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        })[c]);
    }

    function formatMoney(amount) {
        return Number(amount || 0).toLocaleString("vi-VN") + " ₫";
    }

    function showToast(message, type = "success") {
        const toast = document.createElement("div");
        toast.className = `toast toast-${type}`;
        const icons = { success: "✓", error: "✕", warning: "⚠", info: "ℹ" };
        toast.innerHTML = `<span style="font-size:16px;">${icons[type] || "✓"}</span><span>${escapeHTML(message)}</span>`;
        dom.toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = "0";
            toast.style.transform = "translateX(50px)";
            toast.style.transition = "all 0.3s ease";
            setTimeout(() => toast.remove(), 300);
        }, 3200);
    }

    function generateCustomerCode() {
        return "KH" + (1000 + customers.length + 1);
    }

    function getInitials(name) {
        if (!name) return "KH";
        const parts = name.trim().split(" ");
        if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
        return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }

    function getTierBadge(tier) {
        switch (tier) {
            case "Kim cương":
                return `<span class="tier-badge tier-diamond">💎 Kim cương</span>`;
            case "Vàng":
                return `<span class="tier-badge tier-gold">🥇 Vàng</span>`;
            case "Bạc":
                return `<span class="tier-badge tier-silver">🥈 Bạc</span>`;
            default:
                return `<span class="tier-badge tier-bronze">🥉 Thành viên mới</span>`;
        }
    }

    // 5. Storage
    function loadCustomers() {
        try {
            const raw = localStorage.getItem(STORAGE_KEY);
            if (raw) {
                const parsed = JSON.parse(raw);
                if (Array.isArray(parsed) && parsed.length > 0) {
                    customers = parsed;
                } else {
                    customers = demoCustomers;
                    saveCustomers();
                }
            } else {
                customers = demoCustomers;
                saveCustomers();
            }
        } catch {
            customers = demoCustomers;
        }
        renderAll();
    }

    function saveCustomers() {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(customers));
            localStorage.setItem(SYNC_KEY_USERS, JSON.stringify(customers));
            return true;
        } catch (error) {
            console.error("Lỗi ghi dữ liệu khách hàng:", error);
            showToast("Không thể lưu dữ liệu vào bộ nhớ.", "error");
            return false;
        }
    }

    // 6. Avatar Preview Management
    function renderAvatarPreview(url) {
        selectedAvatar = url ? url.trim() : "";
        if (!selectedAvatar) {
            dom.avatarPreview.innerHTML = `<span>👤</span>`;
            return;
        }
        dom.avatarPreview.innerHTML = `<img src="${escapeHTML(selectedAvatar)}" alt="Avatar">`;
    }

    dom.avatarFile.addEventListener("change", function () {
        const file = dom.avatarFile.files[0];
        if (!file) return;

        if (!file.type.startsWith("image/")) {
            showToast("Vui lòng chọn file hình ảnh hợp lệ.", "error");
            dom.avatarFile.value = "";
            return;
        }

        const currentToken = ++readerToken;
        const reader = new FileReader();

        reader.onload = function (e) {
            if (currentToken !== readerToken) return;
            selectedAvatar = e.target.result;
            dom.avatarUrl.value = "";
            renderAvatarPreview(selectedAvatar);
        };
        reader.readAsDataURL(file);
    });

    dom.avatarUrl.addEventListener("input", function () {
        readerToken++;
        dom.avatarFile.value = "";
        renderAvatarPreview(dom.avatarUrl.value);
    });

    // 7. Render Stats & Table
    function renderStats() {
        dom.total.textContent = customers.length;
        dom.vip.textContent = customers.filter(c => c.tier === "Kim cương" || c.tier === "Vàng").length;
        dom.active.textContent = customers.filter(c => c.status === "active").length;

        const totalSpentAll = customers.reduce((sum, c) => sum + (Number(c.spent) || 0), 0);
        dom.spent.textContent = formatMoney(totalSpentAll);
    }

    function getFilteredCustomers() {
        const query = dom.search.value.trim().toLowerCase();
        const tier = dom.tierFilter.value;
        const status = dom.statusFilter.value;
        const sort = dom.sort.value;

        let result = customers.filter(c => {
            const matchQuery = !query ||
                (c.name && c.name.toLowerCase().includes(query)) ||
                (c.phone && c.phone.includes(query)) ||
                (c.email && c.email.toLowerCase().includes(query)) ||
                (c.id && c.id.toLowerCase().includes(query)) ||
                (c.address && c.address.toLowerCase().includes(query));

            const matchTier = !tier || c.tier === tier;
            const matchStatus = !status || c.status === status;

            return matchQuery && matchTier && matchStatus;
        });

        // Sắp xếp
        switch (sort) {
            case "spentDesc":
                result.sort((a, b) => (b.spent || 0) - (a.spent || 0));
                break;
            case "ordersDesc":
                result.sort((a, b) => (b.ordersCount || 0) - (a.ordersCount || 0));
                break;
            case "nameAsc":
                result.sort((a, b) => a.name.localeCompare(b.name, "vi"));
                break;
            default:
                // Mới nhất trước
                result.sort((a, b) => (b.id > a.id ? 1 : -1));
        }

        return result;
    }

    function renderTable() {
        const filtered = getFilteredCustomers();
        const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));

        currentPage = Math.min(currentPage, totalPages);
        const start = (currentPage - 1) * PAGE_SIZE;
        const currentItems = filtered.slice(start, start + PAGE_SIZE);

        dom.resultCount.textContent = `${filtered.length} khách hàng`;
        dom.pageNumber.textContent = currentPage;
        dom.pageInfo.textContent = filtered.length
            ? `Hiển thị ${start + 1}–${Math.min(start + PAGE_SIZE, filtered.length)} / ${filtered.length} khách hàng`
            : "Không tìm thấy khách hàng nào";

        dom.prevPage.disabled = currentPage <= 1;
        dom.nextPage.disabled = currentPage >= totalPages;

        if (currentItems.length === 0) {
            dom.tbody.innerHTML = `
                <tr>
                    <td colspan="9" style="text-align:center; padding:40px 20px; color:var(--text-muted);">
                        <div style="font-size:32px; margin-bottom:8px;">👥</div>
                        <h3 style="font-size:16px; color:var(--text-primary); margin-bottom:4px;">Không tìm thấy khách hàng</h3>
                        <p style="font-size:13px;">Thử thay đổi từ khóa tìm kiếm hoặc đặt lại bộ lọc.</p>
                    </td>
                </tr>
            `;
            return;
        }

        dom.tbody.innerHTML = currentItems.map(c => {
            const hasAvatar = c.avatar && c.avatar.trim() !== "";
            const avatarHtml = hasAvatar
                ? `<img src="${escapeHTML(c.avatar)}" alt="${escapeHTML(c.name)}">`
                : `<span>${getInitials(c.name)}</span>`;

            const statusHtml = c.status === "active"
                ? `<span class="status-badge active"><span style="font-size:8px;">●</span> Hoạt động</span>`
                : `<span class="status-badge inactive"><span style="font-size:8px;">●</span> Tạm khóa</span>`;

            const toggleLabel = c.status === "active" ? "Khóa" : "Mở";

            return `
                <tr>
                    <td>
                        <div class="customer-cell">
                            <div class="customer-avatar">
                                ${avatarHtml}
                            </div>
                            <div>
                                <div class="customer-name">${escapeHTML(c.name)}</div>
                                <div class="customer-email">${escapeHTML(c.email || "—")}</div>
                            </div>
                        </div>
                    </td>
                    <td>
                        <span class="customer-code">${escapeHTML(c.id)}</span>
                    </td>
                    <td>
                        <span class="customer-phone">${escapeHTML(c.phone || "—")}</span>
                    </td>
                    <td>
                        <div class="customer-address">${escapeHTML(c.address || "Chưa cập nhật")}</div>
                    </td>
                    <td>
                        ${getTierBadge(c.tier)}
                    </td>
                    <td>
                        <strong>${c.ordersCount || 0}</strong> đơn
                    </td>
                    <td>
                        <strong style="color:var(--primary); font-size:14px;">${formatMoney(c.spent)}</strong>
                    </td>
                    <td>
                        ${statusHtml}
                    </td>
                    <td>
                        <div class="action-group">
                            <button type="button" class="action-btn view-action" data-action="view" data-id="${escapeHTML(c.id)}" title="Xem chi tiết hồ sơ">
                                Hồ sơ
                            </button>
                            <button type="button" class="action-btn edit-action" data-action="edit" data-id="${escapeHTML(c.id)}" title="Chỉnh sửa thông tin">
                                Sửa
                            </button>
                            <button type="button" class="action-btn toggle-action" data-action="toggle" data-id="${escapeHTML(c.id)}" title="Khóa hoặc mở khóa tài khoản">
                                ${toggleLabel}
                            </button>
                            <button type="button" class="action-btn delete-action" data-action="delete" data-id="${escapeHTML(c.id)}" title="Xóa khách hàng">
                                Xóa
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join("");
    }

    function renderAll() {
        renderStats();
        renderTable();
    }

    // 8. Modal Management (Thêm / Sửa khách hàng)
    function openCustomerModal(customer = null) {
        dom.form.reset();
        selectedAvatar = "";
        renderAvatarPreview("");

        if (customer) {
            dom.modalTitle.textContent = "Chỉnh sửa thông tin khách hàng";
            dom.saveCustomerBtn.textContent = "💾 Cập nhật khách hàng";

            dom.id.value = customer.id;
            dom.code.value = customer.id;
            dom.name.value = customer.name || "";
            dom.phone.value = customer.phone || "";
            dom.email.value = customer.email || "";
            dom.address.value = customer.address || "";
            dom.tier.value = customer.tier || "Đồng";
            dom.status.value = customer.status || "active";
            dom.spentInput.value = customer.spent || 0;
            dom.ordersCountInput.value = customer.ordersCount || 0;
            dom.notes.value = customer.notes || "";

            if (customer.avatar) {
                dom.avatarUrl.value = customer.avatar.startsWith("data:") ? "" : customer.avatar;
                renderAvatarPreview(customer.avatar);
            }
        } else {
            dom.modalTitle.textContent = "Thêm khách hàng mới";
            dom.saveCustomerBtn.textContent = "💾 Lưu thông tin khách hàng";

            dom.id.value = "";
            dom.code.value = generateCustomerCode();
            dom.tier.value = "Đồng";
            dom.status.value = "active";
            dom.spentInput.value = 0;
            dom.ordersCountInput.value = 0;
        }

        dom.modal.classList.add("show");
        dom.modal.setAttribute("aria-hidden", "false");
        document.body.style.overflow = "hidden";
        dom.name.focus();
    }

    function closeCustomerModal() {
        dom.modal.classList.remove("show");
        dom.modal.setAttribute("aria-hidden", "true");
        document.body.style.overflow = "";
        dom.form.reset();
        renderAvatarPreview("");
    }

    dom.btnAddCustomer.addEventListener("click", () => openCustomerModal());
    dom.closeModalBtn.addEventListener("click", closeCustomerModal);
    dom.cancelModalBtn.addEventListener("click", closeCustomerModal);
    dom.modal.addEventListener("click", e => {
        if (e.target === dom.modal) closeCustomerModal();
    });

    // 9. Save Customer
    dom.form.addEventListener("submit", function (e) {
        e.preventDefault();

        const id = dom.id.value.trim() || dom.code.value.trim() || generateCustomerCode();
        const name = dom.name.value.trim();
        const phone = dom.phone.value.trim();
        const email = dom.email.value.trim();
        const address = dom.address.value.trim();
        const tier = dom.tier.value;
        const status = dom.status.value;
        const spent = Number(dom.spentInput.value) || 0;
        const ordersCount = Number(dom.ordersCountInput.value) || 0;
        const notes = dom.notes.value.trim();
        const avatar = selectedAvatar || dom.avatarUrl.value.trim() || "";

        if (!name || !phone || !email) {
            showToast("Vui lòng nhập đầy đủ họ tên, số điện thoại và email.", "error");
            return;
        }

        const existing = customers.find(c => c.id === id);

        const customerData = {
            id: id,
            name: name,
            phone: phone,
            email: email,
            address: address,
            tier: tier,
            status: status,
            spent: spent,
            ordersCount: ordersCount,
            points: Math.floor(spent / 10000), // 10k VND = 1 điểm
            avatar: avatar,
            notes: notes,
            joinDate: existing ? existing.joinDate : new Date().toLocaleDateString("vi-VN")
        };

        if (existing) {
            const index = customers.findIndex(c => c.id === id);
            customers[index] = customerData;
            showToast("Cập nhật thông tin khách hàng thành công!");
        } else {
            customers.unshift(customerData);
            showToast("Thêm mới khách hàng thành công!");
        }

        saveCustomers();
        closeCustomerModal();
        renderAll();
    });

    // 10. Table Actions (Xem hồ sơ, Sửa, Khóa, Xóa)
    dom.tbody.addEventListener("click", function (e) {
        const btn = e.target.closest("[data-action]");
        if (!btn) return;

        const action = btn.dataset.action;
        const customerId = btn.dataset.id;
        const customer = customers.find(c => c.id === customerId);
        if (!customer) return;

        if (action === "edit") {
            openCustomerModal(customer);
            return;
        }

        if (action === "view") {
            openViewModal(customer);
            return;
        }

        if (action === "toggle") {
            const nextStatus = customer.status === "active" ? "inactive" : "active";
            const confirmMsg = nextStatus === "inactive"
                ? `Bạn có chắc muốn tạm khóa tài khoản của khách hàng "${customer.name}"?`
                : `Mở khóa tài khoản cho khách hàng "${customer.name}"?`;

            if (confirm(confirmMsg)) {
                customer.status = nextStatus;
                saveCustomers();
                renderAll();
                showToast(nextStatus === "inactive" ? "Đã tạm khóa tài khoản." : "Đã kích hoạt lại tài khoản.", "info");
            }
            return;
        }

        if (action === "delete") {
            if (confirm(`Bạn có chắc chắn muốn xóa hồ sơ khách hàng "${customer.name}"?`)) {
                customers = customers.filter(c => c.id !== customerId);
                saveCustomers();
                renderAll();
                showToast(`Đã xóa khách hàng "${customer.name}".`, "success");
            }
            return;
        }
    });

    // 11. View Customer Profile Modal
    function openViewModal(customer) {
        dom.viewTitle.textContent = `Hồ sơ: ${customer.name}`;
        dom.viewSubtitle.textContent = `Mã khách hàng: ${customer.id} · Tham gia: ${customer.joinDate || "Gần đây"}`;

        const hasAvatar = customer.avatar && customer.avatar.trim() !== "";
        const avatarImg = hasAvatar
            ? `<img src="${escapeHTML(customer.avatar)}" alt="${escapeHTML(customer.name)}" style="width:72px; height:72px; border-radius:50%; object-fit:cover; border:3px solid var(--border);">`
            : `<div style="width:72px; height:72px; border-radius:50%; background:linear-gradient(135deg,#3b82f6,#1d4ed8); color:#fff; display:flex; align-items:center; justify-content:center; font-size:24px; font-weight:800;">${getInitials(customer.name)}</div>`;

        dom.viewBody.innerHTML = `
            <div style="display:flex; align-items:center; gap:18px; padding-bottom:18px; border-bottom:1px solid var(--border); margin-bottom:18px;">
                ${avatarImg}
                <div>
                    <h3 style="font-size:18px; font-weight:800; color:var(--text-primary); margin-bottom:4px;">${escapeHTML(customer.name)}</h3>
                    <div style="display:flex; gap:8px; align-items:center;">
                        ${getTierBadge(customer.tier)}
                        <span class="status-badge ${customer.status === 'active' ? 'active' : 'inactive'}">
                            ${customer.status === 'active' ? '● Đang hoạt động' : '● Tạm khóa'}
                        </span>
                    </div>
                </div>
            </div>

            <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:18px;">
                <div style="padding:12px; background:var(--bg-main); border-radius:8px; border:1px solid var(--border);">
                    <span style="font-size:12px; color:var(--text-muted); display:block;">Tổng chi tiêu</span>
                    <strong style="font-size:18px; color:var(--primary);">${formatMoney(customer.spent)}</strong>
                </div>
                <div style="padding:12px; background:var(--bg-main); border-radius:8px; border:1px solid var(--border);">
                    <span style="font-size:12px; color:var(--text-muted); display:block;">Số đơn hàng đã mua</span>
                    <strong style="font-size:18px; color:var(--text-primary);">${customer.ordersCount || 0} đơn</strong>
                </div>
            </div>

            <div style="display:flex; flex-direction:column; gap:10px; font-size:13px;">
                <div style="display:flex; justify-content:space-between; padding-bottom:8px; border-bottom:1px solid var(--border-light);">
                    <span style="color:var(--text-muted);">Số điện thoại:</span>
                    <strong>${escapeHTML(customer.phone || "—")}</strong>
                </div>
                <div style="display:flex; justify-content:space-between; padding-bottom:8px; border-bottom:1px solid var(--border-light);">
                    <span style="color:var(--text-muted);">Email:</span>
                    <strong>${escapeHTML(customer.email || "—")}</strong>
                </div>
                <div style="display:flex; justify-content:space-between; padding-bottom:8px; border-bottom:1px solid var(--border-light);">
                    <span style="color:var(--text-muted);">Điểm thưởng tích lũy:</span>
                    <strong style="color:var(--warning);">${customer.points || 0} điểm</strong>
                </div>
                <div style="display:flex; justify-content:space-between; padding-bottom:8px; border-bottom:1px solid var(--border-light);">
                    <span style="color:var(--text-muted);">Địa chỉ giao hàng:</span>
                    <span style="max-width:320px; text-align:right; font-weight:600;">${escapeHTML(customer.address || "Chưa cập nhật")}</span>
                </div>
                <div style="display:flex; justify-content:space-between; padding-top:4px;">
                    <span style="color:var(--text-muted);">Ghi chú nội bộ:</span>
                    <span style="max-width:320px; text-align:right; color:var(--text-secondary); font-style:italic;">${escapeHTML(customer.notes || "Không có")}</span>
                </div>
            </div>
        `;

        dom.viewModal.classList.add("show");
        dom.viewModal.setAttribute("aria-hidden", "false");
    }

    function closeViewModal() {
        dom.viewModal.classList.remove("show");
        dom.viewModal.setAttribute("aria-hidden", "true");
    }

    dom.closeViewBtn.addEventListener("click", closeViewModal);
    dom.closeViewBtn2.addEventListener("click", closeViewModal);

    // 12. Search & Filters
    function applyFilters() {
        currentPage = 1;
        renderTable();
    }

    dom.search.addEventListener("input", applyFilters);
    dom.tierFilter.addEventListener("change", applyFilters);
    dom.statusFilter.addEventListener("change", applyFilters);
    dom.sort.addEventListener("change", applyFilters);

    dom.resetFilters.addEventListener("click", function () {
        dom.search.value = "";
        dom.tierFilter.value = "";
        dom.statusFilter.value = "";
        dom.sort.value = "newest";
        currentPage = 1;
        renderTable();
        showToast("Đã đặt lại bộ lọc.");
    });

    // Reset demo data
    dom.btnResetDemo.addEventListener("click", function () {
        if (confirm("Khôi phục lại danh sách 6 khách hàng mẫu mặc định?")) {
            customers = [...demoCustomers];
            saveCustomers();
            renderAll();
            showToast("Đã khôi phục dữ liệu khách hàng mẫu thành công!");
        }
    });

    // Pagination
    dom.prevPage.addEventListener("click", () => {
        if (currentPage > 1) {
            currentPage--;
            renderTable();
        }
    });

    dom.nextPage.addEventListener("click", () => {
        const filtered = getFilteredCustomers();
        const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
        if (currentPage < totalPages) {
            currentPage++;
            renderTable();
        }
    });

    // Keydown Esc
    document.addEventListener("keydown", e => {
        if (e.key === "Escape") {
            if (dom.viewModal.classList.contains("show")) closeViewModal();
            else if (dom.modal.classList.contains("show")) closeCustomerModal();
        }
    });

    // 13. Khởi chạy
    loadCustomers();
});
