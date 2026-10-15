```javascript
"use strict";

document.addEventListener("DOMContentLoaded", function () {
    const DEMO_ORDERS = [
        {
            id: "DH001",
            customer: "Nguyễn Văn An",
            date: "14/10/2026",
            total: 1850000,
            status: "Hoàn thành"
        },
        {
            id: "DH002",
            customer: "Trần Minh Đức",
            date: "14/10/2026",
            total: 2450000,
            status: "Chờ xác nhận"
        },
        {
            id: "DH003",
            customer: "Lê Hoàng Nam",
            date: "13/10/2026",
            total: 1290000,
            status: "Hoàn thành"
        },
        {
            id: "DH004",
            customer: "Phạm Quốc Huy",
            date: "13/10/2026",
            total: 2100000,
            status: "Đã hủy"
        },
        {
            id: "DH005",
            customer: "Đỗ Thành Long",
            date: "12/10/2026",
            total: 1750000,
            status: "Chờ xác nhận"
        }
    ];

    function money(value) {
        return Number(value || 0).toLocaleString("vi-VN") + "đ";
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

    function renderProducts() {
        const products = readProducts();
        const totalProducts = products.filter(function (product) {
            return product.status !== "Đã xóa";
        }).length;

        document.getElementById("totalProducts").textContent =
            totalProducts;

        const tbody = document.getElementById("recentProducts");

        if (products.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="empty-row">
                        Chưa có sản phẩm. Hãy thêm sản phẩm tại trang quản lý.
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = products.slice(-5).reverse().map(function (p) {
            let statusClass = "status-pending";
            let statusText = p.status || "Chưa xác định";

            if (statusText === "Đang bán") {
                statusClass = "status-done";
            } else if (
                statusText === "Đã xóa" ||
                statusText === "Đang ẩn"
            ) {
                statusClass = "status-cancelled";
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
        const tbody = document.getElementById("recentOrders");

        tbody.innerHTML = DEMO_ORDERS.map(function (order) {
            let statusClass = "status-pending";

            if (order.status === "Hoàn thành") {
                statusClass = "status-done";
            } else if (order.status === "Đã hủy") {
                statusClass = "status-cancelled";
            }

            return `
                <tr>
                    <td><strong>${order.id}</strong></td>
                    <td>${escapeHTML(order.customer)}</td>
                    <td>${order.date}</td>
                    <td>${money(order.total)}</td>
                    <td>
                        <span class="status ${statusClass}">
                            ${escapeHTML(order.status)}
                        </span>
                    </td>
                </tr>
            `;
        }).join("");
    }

    function escapeHTML(value) {
        return String(value).replace(/[&<>"']/g, function (char) {
            return {
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#39;"
            }[char];
        });
    }

    // Hiển thị tên quản trị viên nếu đã đăng nhập demo.
    try {
        const user = JSON.parse(
            sessionStorage.getItem("loggedInUser") || "null"
        );

        if (user && (user.name || user.fullName || user.email)) {
            document.getElementById("adminName").textContent =
                user.name || user.fullName || user.email;
        }
    } catch (error) {
        console.warn("Không đọc được thông tin phiên demo.");
    }

    // Đăng xuất demo.
    document.getElementById("logoutBtn").addEventListener("click", function () {
        const confirmed = confirm("Bạn có chắc muốn đăng xuất không?");

        if (!confirmed) return;

        sessionStorage.removeItem("loggedInUser");
        sessionStorage.removeItem("isLoggedIn");
        window.location.href = "login.html";
    });

    renderProducts();
    renderOrders();
});
```