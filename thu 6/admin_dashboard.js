"use strict";

document.addEventListener("DOMContentLoaded", function () {
    const DEMO_ORDERS = [
        {
            id: "DH1001",
            customer: "Nguyễn Văn An",
            date: "19/10/2026",
            total: 2690000,
            status: "Đang vận chuyển",
            paymentMethod: "VNPay",
            paymentStatus: "Đã thanh toán"
        },
        {
            id: "DH1002",
            customer: "Trần Minh Đức",
            date: "18/10/2026",
            total: 3200000,
            status: "Đang vận chuyển",
            paymentMethod: "MoMo",
            paymentStatus: "Đã thanh toán"
        },
        {
            id: "DH1003",
            customer: "Lê Hoàng Nam",
            date: "19/10/2026",
            total: 3900000,
            status: "Chờ xác nhận",
            paymentMethod: "VietQR",
            paymentStatus: "Chờ thanh toán"
        },
        {
            id: "DH1004",
            customer: "Phạm Quốc Bảo",
            date: "17/10/2026",
            total: 4500000,
            status: "Hoàn thành",
            paymentMethod: "Visa / Master",
            paymentStatus: "Đã thanh toán"
        },
        {
            id: "DH1005",
            customer: "Vũ Thị Mai",
            date: "19/10/2026",
            total: 2890000,
            status: "Đang chuẩn bị hàng",
            paymentMethod: "VietQR",
            paymentStatus: "Đã thanh toán"
        }
    ];

    function money(value) {
        return Number(value || 0).toLocaleString("vi-VN") + " ₫";
    }

    function readProducts() {
        try {
            const data = JSON.parse(
                localStorage.getItem("shoesProducts") || "[]"
            );
            return Array.isArray(data) ? data : [];
        } catch (error) {
            console.error("Không đọc được dữ liệu sản phẩm:", error);
            return [];
        }
    }

    function readOrders() {
        try {
            const data = JSON.parse(
                localStorage.getItem("shoesOrders") || "[]"
            );
            if (Array.isArray(data) && data.length > 0) return data;
        } catch (error) {
            console.error("Không đọc được dữ liệu đơn hàng:", error);
        }
        return DEMO_ORDERS;
    }

    function renderProducts() {
        const products = readProducts();
        const totalProducts = products.filter(function (product) {
            return product.status !== "Đã xóa";
        }).length;

        const totalProductsEl = document.getElementById("totalProducts");
        if (totalProductsEl) {
            totalProductsEl.textContent = totalProducts;
        }

        const tbody = document.getElementById("recentProducts");
        if (!tbody) return;

        if (products.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="empty-row" style="text-align:center; padding:20px; color:#64748b;">
                        Chưa có sản phẩm. Hãy thêm sản phẩm tại trang quản lý.
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = products.slice(-5).reverse().map(function (p) {
            let statusClass = "status-done";
            let rawStatus = String(p.status || "active").toLowerCase().trim();
            let statusText = "Còn hàng";

            if (rawStatus === "hidden" || rawStatus === "hết hàng" || rawStatus === "đang ẩn" || rawStatus === "đã xóa") {
                statusClass = "status-cancelled";
                statusText = "Hết hàng";
            } else {
                statusClass = "status-done";
                statusText = "Còn hàng";
            }

            return `
                <tr>
                    <td>${escapeHTML(p.name || "Chưa đặt tên")}</td>
                    <td>${escapeHTML(p.brand || "Chưa có")}</td>
                    <td>${money(p.price)}</td>
                    <td>
                        <span class="status ${statusClass}">
                            ${escapeHTML(statusText)}
                        </span>
                    </td>
                </tr>
            `;
        }).join("");
    }

    function renderOrders() {
        const orders = readOrders();
        const totalOrdersEl = document.getElementById("totalOrders");
        if (totalOrdersEl) {
            totalOrdersEl.textContent = orders.length;
        }

        const tbody = document.getElementById("recentOrders");
        if (!tbody) return;

        tbody.innerHTML = orders.slice(0, 5).map(function (order) {
            let statusClass = "status-pending";

            if (order.status === "Hoàn thành") {
                statusClass = "status-done";
            } else if (order.status === "Đã hủy") {
                statusClass = "status-cancelled";
            } else if (order.status === "Đang vận chuyển") {
                statusClass = "status-done";
            }

            return `
                <tr>
                    <td><strong>#${escapeHTML(order.id)}</strong></td>
                    <td>${escapeHTML(order.customer)}</td>
                    <td>${escapeHTML(order.date || "—")}</td>
                    <td><strong>${money(order.total)}</strong></td>
                    <td>
                        <span class="status ${statusClass}">
                            ${escapeHTML(order.status || "Chờ xử lý")}
                        </span>
                    </td>
                </tr>
            `;
        }).join("");
    }

    function escapeHTML(value) {
        return String(value ?? "").replace(/[&<>"']/g, function (char) {
            return {
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#39;"
            }[char];
        });
    }

    // Hiển thị tên quản trị viên nếu đã đăng nhập demo
    try {
        let session = JSON.parse(sessionStorage.getItem("shoesAdminSession") || "null");
        if (!session) {
            session = JSON.parse(sessionStorage.getItem("loggedInUser") || "null");
        }
        if (session && (session.name || session.fullName || session.email)) {
            const adminNameEl = document.getElementById("adminName");
            if (adminNameEl) {
                adminNameEl.textContent = session.name || session.fullName || session.email;
            }
        }
    } catch (error) {
        console.warn("Không đọc được thông tin phiên demo.");
    }

    // Đăng xuất demo
    const logoutBtn = document.getElementById("logoutBtn");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", function () {
            if (confirm("Bạn có chắc muốn đăng xuất không?")) {
                sessionStorage.removeItem("shoesAdminSession");
                sessionStorage.removeItem("loggedInUser");
                window.location.replace("./admin_login.html");
            }
        });
    }

    renderProducts();
    renderOrders();
});