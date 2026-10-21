/**
 * SHOES STORE - ADMIN ORDERS, ONLINE PAYMENT & SHIPPING MANAGEMENT
 * Quản lý đơn hàng, Thanh toán trực tuyến (VNPay/MoMo/VietQR) & Vận chuyển (GHN/GHTK/ViettelPost)
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
    const orderListTbody = document.getElementById("orderList");
    const preorderListTbody = document.getElementById("preorderList");
    const notice = document.getElementById("notice");

    // Thống kê Stats
    const totalOrdersEl = document.getElementById("totalOrders");
    const onlinePaidCountEl = document.getElementById("onlinePaidCount");
    const onlinePaidAmountEl = document.getElementById("onlinePaidAmount");
    const shippingCountEl = document.getElementById("shippingCount");
    const preorderCountEl = document.getElementById("preorderCount");
    const completedCountEl = document.getElementById("completedCount");
    const pendingCountEl = document.getElementById("pendingCount");

    // Thống kê Pre-order
    const waitingStockEl = document.getElementById("waitingStockCount");
    const arrivedCountEl = document.getElementById("arrivedCount");
    const readyCountEl = document.getElementById("readyCount");

    // Bộ lọc Filters
    const searchInput = document.getElementById("searchOrder");
    const statusFilter = document.getElementById("statusFilter");
    const paymentStatusFilter = document.getElementById("paymentStatusFilter");
    const paymentMethodFilter = document.getElementById("paymentMethodFilter");
    const shippingCarrierFilter = document.getElementById("shippingCarrierFilter");
    const shippingStatusFilter = document.getElementById("shippingStatusFilter");
    const typeFilter = document.getElementById("typeFilter");
    const resetFiltersBtn = document.getElementById("resetFiltersBtn");
    const exportOrdersBtn = document.getElementById("exportOrdersBtn");

    // Topbar Actions
    const btnCreateOrder = document.getElementById("btnCreateOrder");
    const btnSettings = document.getElementById("btnSettings");

    // Modals
    const detailModal = document.getElementById("detailModal");
    const orderDetailContent = document.getElementById("orderDetail");
    const closeModalBtn = document.getElementById("closeModal");
    const closeDetailBtn = document.getElementById("closeDetailBtn");
    const btnPrintWaybillFromDetail = document.getElementById("btnPrintWaybillFromDetail");

    const trackingModal = document.getElementById("trackingModal");
    const trackingModalBody = document.getElementById("trackingModalBody");
    const closeTrackingModal = document.getElementById("closeTrackingModal");
    const btnCloseTracking = document.getElementById("btnCloseTracking");
    const btnSimulateNextStep = document.getElementById("btnSimulateNextStep");

    const paymentModal = document.getElementById("paymentModal");
    const paymentModalBody = document.getElementById("paymentModalBody");
    const closePaymentModal = document.getElementById("closePaymentModal");
    const btnClosePayment = document.getElementById("btnClosePayment");
    const btnSimulatePaid = document.getElementById("btnSimulatePaid");

    const createOrderModal = document.getElementById("createOrderModal");
    const createOrderForm = document.getElementById("createOrderForm");
    const closeCreateModal = document.getElementById("closeCreateModal");
    const btnCancelCreate = document.getElementById("btnCancelCreate");
    const newOrderProduct = document.getElementById("newOrderProduct");
    const newOrderQuantity = document.getElementById("newOrderQuantity");
    const newShippingCarrier = document.getElementById("newShippingCarrier");
    const newOrderCalculatedTotal = document.getElementById("newOrderCalculatedTotal");

    const printWaybillModal = document.getElementById("printWaybillModal");
    const waybillPrintContent = document.getElementById("waybillPrintContent");
    const closePrintModal = document.getElementById("closePrintModal");
    const btnClosePrint = document.getElementById("btnClosePrint");
    const btnPrintExecute = document.getElementById("btnPrintExecute");

    const settingsModal = document.getElementById("settingsModal");
    const closeSettingsModal = document.getElementById("closeSettingsModal");
    const btnCloseSettings = document.getElementById("btnCloseSettings");

    // State
    let activeOrderForTracking = null;
    let activeOrderForPayment = null;
    let activeOrderForDetail = null;
    let countdownInterval = null;

    // 3. Dữ liệu mẫu khởi tạo chuẩn (Có sẵn đầy đủ thông tin thanh toán online & vận chuyển)
    function createDemoOrders() {
        const today = new Date().toLocaleDateString("vi-VN");
        return [
            {
                id: "DH1001",
                customer: "Nguyễn Văn An",
                phone: "0901234567",
                address: "123 Nguyễn Trãi, Phường Bến Thành, Quận 1, TP. Hồ Chí Minh",
                product: "Nike Air Force 1 '07",
                variant: "Trắng / Size 41",
                quantity: 1,
                itemPrice: 2660000,
                shippingFee: 30000,
                total: 2690000,
                date: "19/10/2026 09:30",
                expectedDate: "20/10/2026",
                type: "Có sẵn",
                status: "Đang vận chuyển",
                preorderStatus: "—",
                // Thanh toán trực tuyến
                paymentMethod: "VNPay",
                paymentStatus: "Đã thanh toán",
                transactionId: "VNP20261019-98124",
                paidAt: "19/10/2026 09:35",
                paymentGateway: "Cổng thanh toán VNPay-QR",
                // Vận chuyển
                shippingCarrier: "GHN",
                trackingCode: "GHN8829104VN",
                shippingStatus: "Đang giao hàng",
                shipperName: "Lê Văn Hùng",
                shipperPhone: "0988.112.233",
                estimatedDelivery: "20/10/2026",
                trackingTimeline: [
                    { time: "19/10/2026 09:30", title: "Đơn hàng khởi tạo thành công", desc: "Hệ thống Shoes Store xác nhận thanh toán trực tuyến thành công", done: true },
                    { time: "19/10/2026 11:15", title: "Đã đóng gói & Bàn giao bưu tá", desc: "Bưu tá GHN Lê Văn Hùng đã nhận kiện hàng tại kho Q1", done: true },
                    { time: "19/10/2026 16:40", title: "Nhập kho phân loại Tân Bình", desc: "Kiện hàng đã qua máy quét phân loại và chuyển đến bưu cục phát", done: true },
                    { time: "20/10/2026 08:15", title: "Bưu tá đang giao hàng", desc: "Shipper đang trên đường giao hàng đến 123 Nguyễn Trãi, Q1", done: true }
                ]
            },
            {
                id: "DH1002",
                customer: "Trần Minh Đức",
                phone: "0987654321",
                address: "45 Hoàng Hoa Thám, Phường 13, Quận Tân Bình, TP. Hồ Chí Minh",
                product: "Adidas Ultraboost Light",
                variant: "Đen / Size 42",
                quantity: 1,
                itemPrice: 3172000,
                shippingFee: 28000,
                total: 3200000,
                date: "18/10/2026 15:20",
                expectedDate: "21/10/2026",
                type: "Pre-order",
                status: "Đang vận chuyển",
                preorderStatus: "Hàng đã về",
                // Thanh toán trực tuyến
                paymentMethod: "MoMo",
                paymentStatus: "Đã thanh toán",
                transactionId: "MOMO-99283120",
                paidAt: "18/10/2026 15:22",
                paymentGateway: "Ví điện tử MoMo",
                // Vận chuyển
                shippingCarrier: "GHTK",
                trackingCode: "GHTK-SG091244",
                shippingStatus: "Đang luân chuyển",
                shipperName: "Trần Văn Nam",
                shipperPhone: "0912.445.678",
                estimatedDelivery: "21/10/2026",
                trackingTimeline: [
                    { time: "18/10/2026 15:20", title: "Đơn Pre-order được ghi nhận", desc: "Khách hàng thanh toán toàn phần qua Ví MoMo", done: true },
                    { time: "19/10/2026 10:00", title: "Hàng Pre-order đã về kho", desc: "Kiểm tra chất lượng và dán tem niêm phong thành công", done: true },
                    { time: "19/10/2026 14:30", title: "GHTK đã lấy hàng", desc: "Kiện hàng đang trung chuyển tại Hub Phân Loại GHTK Bình Tân", done: true }
                ]
            },
            {
                id: "DH1003",
                customer: "Lê Hoàng Nam",
                phone: "0912345678",
                address: "78 Cầu Giấy, Phường Quan Hoa, Quận Cầu Giấy, Hà Nội",
                product: "Puma RS-X Reinvention",
                variant: "Đỏ/Trắng / Size 40",
                quantity: 2,
                itemPrice: 3875000,
                shippingFee: 25000,
                total: 3900000,
                date: "19/10/2026 14:05",
                expectedDate: "22/10/2026",
                type: "Có sẵn",
                status: "Chờ xác nhận",
                preorderStatus: "—",
                // Thanh toán trực tuyến
                paymentMethod: "VietQR",
                paymentStatus: "Chờ thanh toán",
                transactionId: "Chưa có",
                paidAt: "—",
                paymentGateway: "Chuyển khoản VietQR (Napas 24/7)",
                // Vận chuyển
                shippingCarrier: "Viettel Post",
                trackingCode: "VTP-982103VN",
                shippingStatus: "Chờ lấy hàng",
                shipperName: "Đang điều phối",
                shipperPhone: "1900.8095",
                estimatedDelivery: "22/10/2026",
                trackingTimeline: [
                    { time: "19/10/2026 14:05", title: "Đã tạo đơn hàng", desc: "Đơn hàng đang chờ khách hàng quét mã VietQR thanh toán", done: true }
                ]
            },
            {
                id: "DH1004",
                customer: "Phạm Quốc Bảo",
                phone: "0934567890",
                address: "22 Bà Triệu, Phường Hàng Bài, Quận Hoàn Kiếm, Hà Nội",
                product: "Nike Jordan 1 Retro High",
                variant: "Đỏ/Đen / Size 42",
                quantity: 1,
                itemPrice: 4473000,
                shippingFee: 27000,
                total: 4500000,
                date: "17/10/2026 10:30",
                expectedDate: "19/10/2026",
                type: "Có sẵn",
                status: "Hoàn thành",
                preorderStatus: "—",
                // Thanh toán trực tuyến
                paymentMethod: "Visa / Master",
                paymentStatus: "Đã thanh toán",
                transactionId: "VISA-44920199",
                paidAt: "17/10/2026 10:32",
                paymentGateway: "Cổng Thẻ Quốc Tế 3D-Secure",
                // Vận chuyển
                shippingCarrier: "Shopee Xpress",
                trackingCode: "SPX-VN884210",
                shippingStatus: "Giao thành công",
                shipperName: "Vũ Đình Trọng",
                shipperPhone: "0933.221.199",
                estimatedDelivery: "19/10/2026",
                trackingTimeline: [
                    { time: "17/10/2026 10:30", title: "Thanh toán thẻ thành công", desc: "Giao dịch bảo mật qua cổng quốc tế Visa", done: true },
                    { time: "17/10/2026 14:00", title: "Bàn giao Shopee Xpress", desc: "Kiện hàng đã rời trung tâm kho miền Nam", done: true },
                    { time: "18/10/2026 21:00", title: "Đã tới bưu cục Hoàn Kiếm", desc: "Chuẩn bị lịch giao phát ca sáng", done: true },
                    { time: "19/10/2026 10:15", title: "Giao hàng thành công", desc: "Khách hàng Phạm Quốc Bảo đã ký nhận đầy đủ", done: true }
                ]
            },
            {
                id: "DH1005",
                customer: "Vũ Thị Mai",
                phone: "0945678901",
                address: "88 Lê Duẩn, Phường Thạch Thang, Quận Hải Châu, Đà Nẵng",
                product: "Asics Gel-Kayano 29",
                variant: "Xanh dương / Size 39",
                quantity: 1,
                itemPrice: 2845000,
                shippingFee: 45000,
                total: 2890000,
                date: "19/10/2026 11:20",
                expectedDate: "20/10/2026",
                type: "Pre-order",
                status: "Đang chuẩn bị hàng",
                preorderStatus: "Sẵn sàng nhận",
                // Thanh toán trực tuyến
                paymentMethod: "VietQR",
                paymentStatus: "Đã thanh toán",
                transactionId: "NPS-7749102",
                paidAt: "19/10/2026 11:25",
                paymentGateway: "Chuyển khoản VietQR (Napas 24/7)",
                // Vận chuyển
                shippingCarrier: "Ahamove",
                trackingCode: "AHA-489201",
                shippingStatus: "Chờ lấy hàng",
                shipperName: "Nguyễn Tuấn Anh",
                shipperPhone: "0909.554.433",
                estimatedDelivery: "20/10/2026",
                trackingTimeline: [
                    { time: "19/10/2026 11:20", title: "Đơn hàng đã đặt trước", desc: "Khách đã thanh toán trực tuyến qua VietQR Napas", done: true },
                    { time: "19/10/2026 16:00", title: "Đang đóng gói hỏa tốc", desc: "Shoes Store đang đóng hộp chuẩn bị giao tài xế Ahamove", done: true }
                ]
            },
            {
                id: "DH1006",
                customer: "Đỗ Thành Long",
                phone: "0977889900",
                address: "15 Phan Chu Trinh, Phường 2, TP. Vũng Tàu",
                product: "New Balance 550 Vintage",
                variant: "Xanh lá / Size 42.5",
                quantity: 1,
                itemPrice: 2420000,
                shippingFee: 30000,
                total: 2450000,
                date: "16/10/2026 08:45",
                expectedDate: "18/10/2026",
                type: "Có sẵn",
                status: "Đã hủy",
                preorderStatus: "—",
                // Thanh toán trực tuyến
                paymentMethod: "ZaloPay",
                paymentStatus: "Đã hoàn tiền",
                transactionId: "ZLP-110293",
                paidAt: "16/10/2026 08:47",
                paymentGateway: "Ví điện tử ZaloPay",
                // Vận chuyển
                shippingCarrier: "GHN",
                trackingCode: "GHN5521094VN",
                shippingStatus: "Giao không thành công",
                shipperName: "Đã hủy vận đơn",
                shipperPhone: "—",
                estimatedDelivery: "—",
                trackingTimeline: [
                    { time: "16/10/2026 08:45", title: "Thanh toán ZaloPay", desc: "Giao dịch thành công", done: true },
                    { time: "16/10/2026 14:00", title: "Khách yêu cầu hủy đơn", desc: "Đã xử lý hoàn tiền 100% về ví ZaloPay của khách", done: true }
                ]
            }
        ];
    }

    let orders = loadOrders();

    function loadOrders() {
        try {
            const saved = JSON.parse(localStorage.getItem(orderKey) || "null");
            if (Array.isArray(saved) && saved.length > 0) {
                // Tự động kiểm tra và nâng cấp dữ liệu nếu là dữ liệu cũ thiếu trường thanh toán/vận chuyển
                const migrated = saved.map(order => {
                    if (!order.paymentMethod) {
                        order.paymentMethod = "VietQR";
                        order.paymentStatus = order.status === "Hoàn thành" ? "Đã thanh toán" : "Chờ thanh toán";
                        order.transactionId = order.paymentStatus === "Đã thanh toán" ? "NPS-" + Math.floor(100000 + Math.random() * 900000) : "Chưa có";
                        order.paymentGateway = "Chuyển khoản VietQR (Napas 24/7)";
                    }
                    if (!order.shippingCarrier) {
                        order.shippingCarrier = "GHN";
                        order.trackingCode = "GHN" + Math.floor(1000000 + Math.random() * 9000000) + "VN";
                        order.shippingStatus = order.status === "Hoàn thành" ? "Giao thành công" : "Đang giao hàng";
                        order.shipperName = "Lê Văn Hùng";
                        order.shipperPhone = "0988.112.233";
                        order.shippingFee = 30000;
                        order.address = order.address || "123 Nguyễn Trãi, Quận 1, TP. Hồ Chí Minh";
                        order.trackingTimeline = [
                            { time: order.date || "19/10/2026", title: "Đã tiếp nhận đơn hàng", desc: "Hệ thống Shoes Store đã đóng gói và tạo vận đơn", done: true },
                            { time: order.date || "19/10/2026", title: "Bưu tá đã nhận hàng", desc: "Kiện hàng đang trên đường vận chuyển", done: true }
                        ];
                    }
                    return order;
                });
                localStorage.setItem(orderKey, JSON.stringify(migrated));
                return migrated;
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

    // Helper functions
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
        }, 3500);
    }

    function getOrderStatusBadgeClass(status) {
        if (status === "Hoàn thành") return "badge-success";
        if (status === "Đã hủy") return "badge-danger";
        if (status === "Đang vận chuyển") return "badge-info";
        if (status === "Chờ xác nhận" || status === "Đang chuẩn bị hàng") return "badge-warning";
        return "badge-secondary";
    }

    function getPaymentPillClass(method) {
        const m = String(method || "").toLowerCase();
        if (m.includes("vnpay")) return "vnpay";
        if (m.includes("momo")) return "momo";
        if (m.includes("vietqr") || m.includes("ck")) return "vietqr";
        if (m.includes("zalopay")) return "zalopay";
        if (m.includes("visa") || m.includes("master")) return "visa";
        return "cod";
    }

    function getPaymentStatusClass(status) {
        if (status === "Đã thanh toán") return "pay-status-paid";
        if (status === "Đã hoàn tiền") return "pay-status-refunded";
        return "pay-status-pending";
    }

    function getCarrierPillClass(carrier) {
        const c = String(carrier || "").toLowerCase();
        if (c.includes("ghn")) return "ghn";
        if (c.includes("ghtk")) return "ghtk";
        if (c.includes("viettel")) return "vtp";
        if (c.includes("shopee") || c.includes("spx")) return "spx";
        if (c.includes("aha")) return "aha";
        return "pickup";
    }

    function getShippingStatusBadgeClass(status) {
        if (status === "Giao thành công") return "badge-success";
        if (status === "Giao không thành công") return "badge-danger";
        if (status === "Đang giao hàng" || status === "Đang luân chuyển") return "badge-info";
        return "badge-warning";
    }

    // Render Stats
    function renderStats() {
        if (totalOrdersEl) totalOrdersEl.textContent = orders.length;

        // Thống kê thanh toán trực tuyến
        const onlinePaidOrders = orders.filter(o => o.paymentStatus === "Đã thanh toán" && o.paymentMethod !== "COD");
        const onlinePaidTotal = onlinePaidOrders.reduce((sum, o) => sum + (Number(o.total) || 0), 0);
        if (onlinePaidCountEl) onlinePaidCountEl.textContent = onlinePaidOrders.length;
        if (onlinePaidAmountEl) onlinePaidAmountEl.textContent = money(onlinePaidTotal) + " qua cổng TT";

        // Thống kê vận chuyển
        const shippingOrders = orders.filter(o => o.status === "Đang vận chuyển" || o.shippingStatus === "Đang giao hàng" || o.shippingStatus === "Đang luân chuyển");
        if (shippingCountEl) shippingCountEl.textContent = shippingOrders.length;

        // Thống kê Pre-order & Khác
        if (preorderCountEl) preorderCountEl.textContent = orders.filter(o => o.type === "Pre-order").length;
        if (completedCountEl) completedCountEl.textContent = orders.filter(o => o.status === "Hoàn thành").length;
        if (pendingCountEl) pendingCountEl.textContent = orders.filter(o => o.status === "Chờ xác nhận").length + " chờ xử lý";

        // Thống kê chi tiết Pre-order
        if (waitingStockEl) waitingStockEl.textContent = orders.filter(o => o.preorderStatus === "Đang chờ hàng").length;
        if (arrivedCountEl) arrivedCountEl.textContent = orders.filter(o => o.preorderStatus === "Hàng đã về").length;
        if (readyCountEl) readyCountEl.textContent = orders.filter(o => o.preorderStatus === "Sẵn sàng nhận").length;
    }

    // Render Bảng Pre-order
    function renderPreorders() {
        if (!preorderListTbody) return;
        const preorders = orders.filter(o => o.type === "Pre-order");

        if (preorders.length === 0) {
            preorderListTbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:20px; color:#64748b;">Chưa có đơn đặt trước (Pre-order).</td></tr>`;
            return;
        }

        preorderListTbody.innerHTML = preorders.map(o => `
            <tr>
                <td><strong>#${escapeHTML(o.id)}</strong></td>
                <td>
                    <span class="product-name">${escapeHTML(o.product)}</span>
                    <span class="sub-text">${escapeHTML(o.variant)} · SL: ${o.quantity || 1}</span>
                </td>
                <td>
                    <span class="pay-pill ${getPaymentPillClass(o.paymentMethod)}">
                        💳 ${escapeHTML(o.paymentMethod || "VietQR")}
                    </span>
                    <span class="badge ${getPaymentStatusClass(o.paymentStatus)}" style="margin-left:4px;">
                        ${escapeHTML(o.paymentStatus || "Chờ thanh toán")}
                    </span>
                </td>
                <td>
                    <span class="carrier-pill ${getCarrierPillClass(o.shippingCarrier)}">
                        🚚 ${escapeHTML(o.shippingCarrier || "GHN")}
                    </span>
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

    // Render Bảng Tất cả Đơn Hàng (Đầy đủ Cột Thanh toán Online & Vận chuyển)
    function renderOrders() {
        if (!orderListTbody) return;

        const keyword = searchInput ? searchInput.value.trim().toLowerCase() : "";
        const statusVal = statusFilter ? statusFilter.value : "";
        const payStatusVal = paymentStatusFilter ? paymentStatusFilter.value : "";
        const payMethodVal = paymentMethodFilter ? paymentMethodFilter.value : "";
        const carrierVal = shippingCarrierFilter ? shippingCarrierFilter.value : "";
        const shipStatusVal = shippingStatusFilter ? shippingStatusFilter.value : "";
        const typeVal = typeFilter ? typeFilter.value : "";

        const filtered = orders.filter(order => {
            const text = [
                order.id,
                order.customer,
                order.phone,
                order.address,
                order.product,
                order.variant,
                order.trackingCode,
                order.transactionId,
                order.shippingCarrier,
                order.paymentMethod
            ].join(" ").toLowerCase();

            const matchKeyword = !keyword || text.includes(keyword);
            const matchStatus = !statusVal || order.status === statusVal;
            const matchPayStatus = !payStatusVal || order.paymentStatus === payStatusVal;
            const matchPayMethod = !payMethodVal || (order.paymentMethod && order.paymentMethod.includes(payMethodVal));
            const matchCarrier = !carrierVal || (order.shippingCarrier && order.shippingCarrier.includes(carrierVal));
            const matchShipStatus = !shipStatusVal || order.shippingStatus === shipStatusVal;
            const matchType = !typeVal || order.type === typeVal;

            return matchKeyword && matchStatus && matchPayStatus && matchPayMethod && matchCarrier && matchShipStatus && matchType;
        });

        const pageInfo = document.getElementById("pageInfo");
        if (pageInfo) {
            pageInfo.textContent = `Hiển thị ${filtered.length} / ${orders.length} đơn hàng`;
        }

        if (filtered.length === 0) {
            orderListTbody.innerHTML = `
                <tr>
                    <td colspan="9" style="text-align:center; padding:35px; color:#64748b;">
                        🔍 Không tìm thấy đơn hàng nào phù hợp với điều kiện tìm kiếm và lọc.
                    </td>
                </tr>
            `;
            renderStats();
            return;
        }

        orderListTbody.innerHTML = filtered.map(order => `
            <tr>
                <td>
                    <div style="display:flex; flex-direction:column; gap:4px;">
                        <span style="font-weight:800; color:var(--text-primary); font-size:13.5px;">#${escapeHTML(order.id)}</span>
                        ${order.trackingCode ? `
                            <button type="button" class="tracking-code-btn" data-action="track" data-id="${escapeHTML(order.id)}" title="Bấm để xem hành trình vận chuyển">
                                🚚 ${escapeHTML(order.trackingCode)}
                            </button>
                        ` : ""}
                    </div>
                </td>

                <td>
                    <div class="customer-cell">
                        <span class="customer-name">${escapeHTML(order.customer || "Khách hàng")}</span>
                        <span class="customer-sub">📞 ${escapeHTML(order.phone || "—")}</span>
                        <span class="customer-sub customer-addr" title="${escapeHTML(order.address || "")}">
                            📍 ${escapeHTML(order.address || "Tại cửa hàng")}
                        </span>
                    </div>
                </td>

                <td>
                    <span class="product-name">${escapeHTML(order.product || "Sản phẩm")}</span>
                    <span class="sub-text">${escapeHTML(order.variant || "Tiêu chuẩn")} · SL: <strong>${order.quantity || 1}</strong></span>
                </td>

                <td>
                    <span style="font-size:12.5px; color:#475569;">${escapeHTML(order.date || "—")}</span>
                </td>

                <!-- CỘT THANH TOÁN TRỰC TUYẾN -->
                <td>
                    <div style="display:flex; flex-direction:column; gap:4px; align-items:flex-start;">
                        <span class="pay-pill ${getPaymentPillClass(order.paymentMethod)}">
                            💳 ${escapeHTML(order.paymentMethod || "VietQR")}
                        </span>
                        <div style="display:flex; align-items:center; gap:4px;">
                            <span class="badge ${getPaymentStatusClass(order.paymentStatus)}">
                                ${escapeHTML(order.paymentStatus || "Chờ thanh toán")}
                            </span>
                            <button type="button" class="btn-icon-sm" data-action="pay" data-id="${escapeHTML(order.id)}" title="Mở cổng thanh toán / Quét mã QR" style="padding:2px 6px;">
                                📱 QR
                            </button>
                        </div>
                    </div>
                </td>

                <!-- CỘT VẬN CHUYỂN -->
                <td>
                    <div style="display:flex; flex-direction:column; gap:4px; align-items:flex-start;">
                        <span class="carrier-pill ${getCarrierPillClass(order.shippingCarrier)}">
                            🚚 ${escapeHTML(order.shippingCarrier || "GHN")}
                        </span>
                        <span class="badge ${getShippingStatusBadgeClass(order.shippingStatus)}">
                            ${escapeHTML(order.shippingStatus || "Chờ lấy hàng")}
                        </span>
                    </div>
                </td>

                <!-- CỘT TỔNG TIỀN -->
                <td>
                    <span class="price">${money(order.total)}</span>
                    <span class="price-sub">Ship: ${order.shippingFee ? money(order.shippingFee) : "0 ₫"}</span>
                </td>

                <!-- CỘT TRẠNG THÁI ĐƠN -->
                <td>
                    <span class="badge ${getOrderStatusBadgeClass(order.status)}">
                        ${escapeHTML(order.status || "Chờ xác nhận")}
                    </span>
                    ${order.type === "Pre-order" ? `<span class="badge badge-purple" style="margin-top:4px; display:inline-block;">Pre-order</span>` : ""}
                </td>

                <!-- CỘT THAO TÁC -->
                <td>
                    <div class="action-btn-group">
                        <button class="btn-icon-sm primary" type="button" data-action="view" data-id="${escapeHTML(order.id)}" title="Xem chi tiết đơn hàng">
                            Chi tiết
                        </button>
                        <button class="btn-icon-sm" type="button" data-action="track" data-id="${escapeHTML(order.id)}" title="Tra cứu lộ trình giao hàng">
                            🚚 Vận đơn
                        </button>
                        <button class="btn-icon-sm" type="button" data-action="print" data-id="${escapeHTML(order.id)}" title="In phiếu gửi hàng cho shipper">
                            🖨 In
                        </button>
                    </div>
                </td>
            </tr>
        `).join("");

        renderStats();
        renderPreorders();
    }

    // ==========================================================================
    // 4. MODAL CHI TIẾT ĐƠN HÀNG TOÀN DIỆN
    // ==========================================================================
    function openOrderDetail(order) {
        if (!detailModal || !orderDetailContent) return;
        activeOrderForDetail = order;

        const modalDetailTitle = document.getElementById("modalDetailTitle");
        if (modalDetailTitle) {
            modalDetailTitle.innerHTML = `📦 Chi tiết đơn hàng <strong>#${escapeHTML(order.id)}</strong>`;
        }

        orderDetailContent.innerHTML = `
            <!-- KHỐI 1: KHÁCH HÀNG & ĐỊA CHỈ NHẬN HÀNG -->
            <div class="modal-section">
                <div class="modal-section-title">
                    <span>👤 Thông tin người nhận & Địa chỉ giao hàng</span>
                    <span class="badge ${getOrderStatusBadgeClass(order.status)}">${escapeHTML(order.status)}</span>
                </div>
                <div class="modal-grid-2">
                    <div class="form-group-item">
                        <label>Họ tên người nhận</label>
                        <div class="value-text">${escapeHTML(order.customer || "Khách hàng")}</div>
                    </div>
                    <div class="form-group-item">
                        <label>Số điện thoại liên hệ</label>
                        <div class="value-text">📞 ${escapeHTML(order.phone || "Chưa cập nhật")}</div>
                    </div>
                    <div class="form-group-item" style="grid-column:span 2;">
                        <label>Địa chỉ giao hàng</label>
                        <div class="value-text">📍 ${escapeHTML(order.address || "Nhận tại cửa hàng")}</div>
                    </div>
                </div>
            </div>

            <!-- KHỐI 2: SẢN PHẨM & GIÁ TRỊ THANH TOÁN -->
            <div class="modal-section">
                <div class="modal-section-title">
                    <span>👟 Sản phẩm & Chi phí</span>
                    <span>Ngày đặt: ${escapeHTML(order.date || "—")}</span>
                </div>
                <div class="modal-grid-2">
                    <div class="form-group-item">
                        <label>Sản phẩm giày</label>
                        <div class="value-text" style="color:var(--primary); font-size:14px;">${escapeHTML(order.product || "Sản phẩm")}</div>
                    </div>
                    <div class="form-group-item">
                        <label>Biến thể (Size / Màu) & Số lượng</label>
                        <div class="value-text">${escapeHTML(order.variant || "Tiêu chuẩn")} · <strong>${order.quantity || 1} đôi</strong></div>
                    </div>
                    <div class="form-group-item">
                        <label>Tiền hàng</label>
                        <div class="value-text">${money(order.itemPrice || (order.total - (order.shippingFee || 0)))}</div>
                    </div>
                    <div class="form-group-item">
                        <label>Phí vận chuyển giao tận nơi</label>
                        <div class="value-text" style="color:#ea580c;">+ ${money(order.shippingFee || 0)}</div>
                    </div>
                    <div class="form-group-item" style="grid-column:span 2; background:#ffffff; padding:10px 14px; border-radius:8px; border:1px solid var(--border); display:flex; justify-content:space-between; align-items:center;">
                        <strong style="font-size:14px;">Tổng tiền thanh toán:</strong>
                        <strong class="price" style="font-size:18px;">${money(order.total)}</strong>
                    </div>
                </div>
            </div>

            <!-- KHỐI 3: QUẢN LÝ THANH TOÁN TRỰC TUYẾN -->
            <div class="modal-section" style="border-left: 4px solid #2563eb;">
                <div class="modal-section-title">
                    <span>💳 Quản lý Thanh toán trực tuyến (Online Payment)</span>
                    <button type="button" class="btn-icon-sm primary" id="btnOpenQRFromDetail">
                        📱 Mở mã QR thanh toán
                    </button>
                </div>
                <div class="modal-grid-2">
                    <div class="form-group-item">
                        <label>Phương thức thanh toán</label>
                        <select id="modalPaymentMethod">
                            <option value="VietQR" ${order.paymentMethod === "VietQR" ? "selected" : ""}>Chuyển khoản VietQR (Napas 24/7)</option>
                            <option value="VNPay" ${order.paymentMethod === "VNPay" ? "selected" : ""}>Cổng VNPay (QR / Thẻ ATM)</option>
                            <option value="MoMo" ${order.paymentMethod === "MoMo" ? "selected" : ""}>Ví điện tử MoMo</option>
                            <option value="ZaloPay" ${order.paymentMethod === "ZaloPay" ? "selected" : ""}>Ví điện tử ZaloPay</option>
                            <option value="Visa / Master" ${order.paymentMethod === "Visa / Master" ? "selected" : ""}>Thẻ Quốc Tế (Visa/Mastercard)</option>
                            <option value="COD" ${order.paymentMethod === "COD" ? "selected" : ""}>Tiền mặt khi nhận hàng (COD)</option>
                        </select>
                    </div>

                    <div class="form-group-item">
                        <label>Trạng thái thanh toán</label>
                        <select id="modalPaymentStatus">
                            <option value="Đã thanh toán" ${order.paymentStatus === "Đã thanh toán" ? "selected" : ""}>✅ Đã thanh toán (Paid)</option>
                            <option value="Chờ thanh toán" ${order.paymentStatus === "Chờ thanh toán" ? "selected" : ""}>⏳ Chờ thanh toán (Pending)</option>
                            <option value="Đã hoàn tiền" ${order.paymentStatus === "Đã hoàn tiền" ? "selected" : ""}>↩️ Đã hoàn tiền (Refunded)</option>
                        </select>
                    </div>

                    <div class="form-group-item">
                        <label>Mã giao dịch trực tuyến (Txn ID)</label>
                        <div class="value-text" style="font-family:monospace; color:#0284c7;">
                            ${escapeHTML(order.transactionId || "Chưa có")}
                        </div>
                    </div>

                    <div class="form-group-item">
                        <label>Thời gian thanh toán xác nhận</label>
                        <div class="value-text">
                            ${escapeHTML(order.paidAt || "Chưa hoàn tất")}
                        </div>
                    </div>
                </div>
            </div>

            <!-- KHỐI 4: QUẢN LÝ VẬN CHUYỂN & GIAO HÀNG -->
            <div class="modal-section" style="border-left: 4px solid #ea580c;">
                <div class="modal-section-title">
                    <span>🚚 Quản lý Vận chuyển & Giao nhận (Logistics)</span>
                    <button type="button" class="btn-icon-sm" id="btnOpenTrackFromDetail">
                        🔍 Xem lộ trình bưu tá
                    </button>
                </div>
                <div class="modal-grid-2">
                    <div class="form-group-item">
                        <label>Đối tác vận chuyển</label>
                        <select id="modalShippingCarrier">
                            <option value="GHN" ${order.shippingCarrier === "GHN" ? "selected" : ""}>Giao Hàng Nhanh (GHN)</option>
                            <option value="GHTK" ${order.shippingCarrier === "GHTK" ? "selected" : ""}>Giao Hàng Tiết Kiệm (GHTK)</option>
                            <option value="Viettel Post" ${order.shippingCarrier === "Viettel Post" ? "selected" : ""}>Viettel Post</option>
                            <option value="Shopee Xpress" ${order.shippingCarrier === "Shopee Xpress" ? "selected" : ""}>Shopee Xpress (SPX)</option>
                            <option value="Ahamove" ${order.shippingCarrier === "Ahamove" ? "selected" : ""}>Hỏa tốc Ahamove</option>
                            <option value="Nhận tại cửa hàng" ${order.shippingCarrier === "Nhận tại cửa hàng" ? "selected" : ""}>Nhận tại cửa hàng</option>
                        </select>
                    </div>

                    <div class="form-group-item">
                        <label>Mã vận đơn bưu phẩm</label>
                        <div class="value-text" style="font-family:monospace; font-weight:700; color:#2563eb;">
                            ${escapeHTML(order.trackingCode || "Chưa tạo")}
                        </div>
                    </div>

                    <div class="form-group-item">
                        <label>Trạng thái vận chuyển</label>
                        <select id="modalShippingStatus">
                            <option value="Chờ lấy hàng" ${order.shippingStatus === "Chờ lấy hàng" ? "selected" : ""}>📦 Chờ lấy hàng</option>
                            <option value="Đang luân chuyển" ${order.shippingStatus === "Đang luân chuyển" ? "selected" : ""}>🔄 Đang luân chuyển qua kho</option>
                            <option value="Đang giao hàng" ${order.shippingStatus === "Đang giao hàng" ? "selected" : ""}>🚚 Đang giao hàng (Shipper)</option>
                            <option value="Giao thành công" ${order.shippingStatus === "Giao thành công" ? "selected" : ""}>✅ Giao thành công</option>
                            <option value="Giao không thành công" ${order.shippingStatus === "Giao không thành công" ? "selected" : ""}>❌ Giao không thành công / Hoàn hàng</option>
                        </select>
                    </div>

                    <div class="form-group-item">
                        <label>Bưu tá phụ trách</label>
                        <div class="value-text">
                            ${escapeHTML(order.shipperName || "Lê Văn Hùng")} (📞 ${escapeHTML(order.shipperPhone || "0988.112.233")})
                        </div>
                    </div>
                </div>
            </div>

            <!-- KHỐI 5: CẬP NHẬT TRẠNG THÁI ĐƠN HÀNG CHUNG -->
            <div class="modal-section">
                <div class="modal-section-title">
                    <span>📋 Trạng thái tiến độ đơn hàng tổng thể</span>
                </div>
                <div class="modal-grid-2">
                    <div class="form-group-item">
                        <label>Trạng thái đơn hàng</label>
                        <select id="modalOrderStatus">
                            <option value="Chờ xác nhận" ${order.status === "Chờ xác nhận" ? "selected" : ""}>Chờ xác nhận</option>
                            <option value="Đang chuẩn bị hàng" ${order.status === "Đang chuẩn bị hàng" ? "selected" : ""}>Đang chuẩn bị hàng</option>
                            <option value="Đang vận chuyển" ${order.status === "Đang vận chuyển" ? "selected" : ""}>Đang vận chuyển</option>
                            <option value="Hoàn thành" ${order.status === "Hoàn thành" ? "selected" : ""}>Hoàn thành</option>
                            <option value="Đã hủy" ${order.status === "Đã hủy" ? "selected" : ""}>Đã hủy</option>
                        </select>
                    </div>
                    <div class="form-group-item">
                        <label>Thao tác nhanh</label>
                        <div style="margin-top:6px;">
                            <button type="button" class="btn-success" id="btnQuickSaveDetail" style="width:100%; padding:9px;">
                                💾 Lưu cập nhật thay đổi
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Event listeners trong modal chi tiết
        document.getElementById("btnOpenQRFromDetail")?.addEventListener("click", () => {
            detailModal.setAttribute("hidden", "");
            openPaymentModal(order);
        });

        document.getElementById("btnOpenTrackFromDetail")?.addEventListener("click", () => {
            detailModal.setAttribute("hidden", "");
            openTrackingModal(order);
        });

        document.getElementById("btnQuickSaveDetail")?.addEventListener("click", () => {
            order.paymentMethod = document.getElementById("modalPaymentMethod").value;
            order.paymentStatus = document.getElementById("modalPaymentStatus").value;
            order.shippingCarrier = document.getElementById("modalShippingCarrier").value;
            order.shippingStatus = document.getElementById("modalShippingStatus").value;
            order.status = document.getElementById("modalOrderStatus").value;

            if (order.paymentStatus === "Đã thanh toán" && (!order.transactionId || order.transactionId === "Chưa có")) {
                order.transactionId = "VNP" + Math.floor(1000000 + Math.random() * 9000000);
                order.paidAt = new Date().toLocaleString("vi-VN");
            }

            if (order.shippingStatus === "Giao thành công" && order.status !== "Hoàn thành") {
                order.status = "Hoàn thành";
            }

            saveOrders();
            renderOrders();
            showNotice("Đã cập nhật đơn hàng #" + order.id + " thành công!");
            detailModal.setAttribute("hidden", "");
        });

        detailModal.removeAttribute("hidden");
    }

    if (btnPrintWaybillFromDetail) {
        btnPrintWaybillFromDetail.addEventListener("click", () => {
            if (activeOrderForDetail) {
                detailModal.setAttribute("hidden", "");
                openPrintWaybillModal(activeOrderForDetail);
            }
        });
    }

    // ==========================================================================
    // 5. MODAL TRA CỨU HÀNH TRÌNH VẬN CHUYỂN (TRACKING TIMELINE & STEPPER)
    // ==========================================================================
    function openTrackingModal(order) {
        if (!trackingModal || !trackingModalBody) return;
        activeOrderForTracking = order;

        // Tính toán bước hiện tại cho Stepper (1 đến 4)
        let stepIndex = 1;
        let progressWidth = "0%";
        const s = order.shippingStatus || "Chờ lấy hàng";

        if (s === "Chờ lấy hàng") {
            stepIndex = 1;
            progressWidth = "15%";
        } else if (s === "Đang luân chuyển") {
            stepIndex = 2;
            progressWidth = "50%";
        } else if (s === "Đang giao hàng") {
            stepIndex = 3;
            progressWidth = "80%";
        } else if (s === "Giao thành công") {
            stepIndex = 4;
            progressWidth = "100%";
        }

        const timelineList = Array.isArray(order.trackingTimeline) && order.trackingTimeline.length > 0
            ? order.trackingTimeline
            : [
                { time: order.date || "19/10/2026", title: "Khởi tạo đơn hàng", desc: "Người gửi đã lên đơn trên hệ thống Shoes Store", done: true }
            ];

        trackingModalBody.innerHTML = `
            <div class="tracking-hero-card">
                <div class="tracking-hero-info">
                    <h3>Đơn vị vận chuyển: <strong>${escapeHTML(order.shippingCarrier || "GHN Express")}</strong></h3>
                    <div class="tracking-hero-code">
                        <span>${escapeHTML(order.trackingCode || "GHN-DEMO")}</span>
                        <button type="button" class="copy-mini-btn" id="btnCopyTrackingCode" title="Sao chép mã vận đơn">
                            Sao chép
                        </button>
                    </div>
                    <div style="font-size:12px; color:#cbd5e1; margin-top:6px;">
                        Người nhận: <strong>${escapeHTML(order.customer)}</strong> (${escapeHTML(order.phone)})
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:11px; text-transform:uppercase; color:#94a3b8; font-weight:700;">Dự kiến giao</div>
                    <div style="font-size:18px; font-weight:800; color:#38bdf8;">${escapeHTML(order.estimatedDelivery || "20/10/2026")}</div>
                    <span class="badge ${getShippingStatusBadgeClass(order.shippingStatus)}" style="margin-top:4px;">
                        ${escapeHTML(order.shippingStatus || "Chờ lấy hàng")}
                    </span>
                </div>
            </div>

            <!-- STEPPER 4 BƯỚC TRỰC QUAN -->
            <div class="tracking-stepper">
                <div class="stepper-progress-line" style="width: ${progressWidth};"></div>

                <div class="step-item ${stepIndex >= 1 ? 'completed' : ''} ${stepIndex === 1 ? 'active' : ''}">
                    <div class="step-circle">${stepIndex > 1 ? '✓' : '1'}</div>
                    <div class="step-label">Chờ lấy hàng</div>
                </div>

                <div class="step-item ${stepIndex >= 2 ? 'completed' : ''} ${stepIndex === 2 ? 'active' : ''}">
                    <div class="step-circle">${stepIndex > 2 ? '✓' : '2'}</div>
                    <div class="step-label">Nhập kho Hub</div>
                </div>

                <div class="step-item ${stepIndex >= 3 ? 'completed' : ''} ${stepIndex === 3 ? 'active' : ''}">
                    <div class="step-circle">${stepIndex > 3 ? '✓' : '3'}</div>
                    <div class="step-label">Đang giao</div>
                </div>

                <div class="step-item ${stepIndex >= 4 ? 'completed' : ''} ${stepIndex === 4 ? 'active' : ''}">
                    <div class="step-circle">${stepIndex === 4 ? '✓' : '4'}</div>
                    <div class="step-label">Đã giao</div>
                </div>
            </div>

            <!-- THÔNG TIN SHIPPER PHỤ TRÁCH -->
            <div style="background:#f1f5f9; padding:12px 16px; border-radius:8px; margin-bottom:18px; display:flex; justify-content:space-between; align-items:center;">
                <div style="font-size:13px;">
                    🛵 Shipper: <strong>${escapeHTML(order.shipperName || "Lê Văn Hùng")}</strong> · SĐT: <strong>${escapeHTML(order.shipperPhone || "0988.112.233")}</strong>
                </div>
                <span style="font-size:11px; background:#e2e8f0; padding:3px 8px; border-radius:4px; font-weight:600;">
                    Đã tiêm chủng & định vị GPS
                </span>
            </div>

            <!-- TIMELINE LỊCH TRÌNH CHI TIẾT -->
            <div style="font-size:13px; font-weight:700; color:var(--text-primary); margin-bottom:6px;">
                📍 Lịch trình luân chuyển chi tiết
            </div>

            <div class="tracking-timeline-list">
                ${timelineList.map((item, idx) => `
                    <div class="timeline-event ${idx === timelineList.length - 1 ? 'latest' : ''}">
                        <div class="timeline-dot"></div>
                        <div class="timeline-title">${escapeHTML(item.title)}</div>
                        <div class="timeline-desc">${escapeHTML(item.desc)}</div>
                        <div class="timeline-time">${escapeHTML(item.time)}</div>
                    </div>
                `).reverse().join("")}
            </div>
        `;

        document.getElementById("btnCopyTrackingCode")?.addEventListener("click", () => {
            navigator.clipboard.writeText(order.trackingCode || "").then(() => {
                showNotice("Đã sao chép mã vận đơn " + order.trackingCode);
            }).catch(() => {
                showNotice("Mã vận đơn: " + order.trackingCode);
            });
        });

        trackingModal.removeAttribute("hidden");
    }

    // Nút giả lập chuyển bước giao hàng tiếp theo (Dành cho demo)
    if (btnSimulateNextStep) {
        btnSimulateNextStep.addEventListener("click", () => {
            if (!activeOrderForTracking) return;
            const nowStr = new Date().toLocaleString("vi-VN");

            if (activeOrderForTracking.shippingStatus === "Chờ lấy hàng") {
                activeOrderForTracking.shippingStatus = "Đang luân chuyển";
                activeOrderForTracking.status = "Đang vận chuyển";
                activeOrderForTracking.trackingTimeline.push({
                    time: nowStr,
                    title: "Bưu tá đã lấy hàng thành công",
                    desc: "Kiện hàng đang trung chuyển qua Kho Hub Phân Loại Trung Tâm",
                    done: true
                });
            } else if (activeOrderForTracking.shippingStatus === "Đang luân chuyển") {
                activeOrderForTracking.shippingStatus = "Đang giao hàng";
                activeOrderForTracking.trackingTimeline.push({
                    time: nowStr,
                    title: "Bưu tá đang trên đường phát hàng",
                    desc: "Shipper " + (activeOrderForTracking.shipperName || "Lê Văn Hùng") + " đang giao đến người nhận",
                    done: true
                });
            } else if (activeOrderForTracking.shippingStatus === "Đang giao hàng") {
                activeOrderForTracking.shippingStatus = "Giao thành công";
                activeOrderForTracking.status = "Hoàn thành";
                if (activeOrderForTracking.paymentStatus === "Chờ thanh toán") {
                    activeOrderForTracking.paymentStatus = "Đã thanh toán";
                }
                activeOrderForTracking.trackingTimeline.push({
                    time: nowStr,
                    title: "Giao hàng thành công",
                    desc: "Khách hàng " + activeOrderForTracking.customer + " đã nhận hàng và ký nhận",
                    done: true
                });
            } else {
                showNotice("Đơn hàng này đã giao thành công trọn vẹn!");
                return;
            }

            saveOrders();
            renderOrders();
            openTrackingModal(activeOrderForTracking);
            showNotice("Đã cập nhật tiến độ bưu gửi: " + activeOrderForTracking.shippingStatus);
        });
    }

    // ==========================================================================
    // 6. MODAL CỔNG THANH TOÁN TRỰC TUYẾN & QUÉT MÃ QR (ONLINE PAYMENT GATEWAY)
    // ==========================================================================
    function openPaymentModal(order) {
        if (!paymentModal || !paymentModalBody) return;
        activeOrderForPayment = order;

        let activeTab = "vietqr";
        if (order.paymentMethod === "VNPay") activeTab = "vnpay";
        else if (order.paymentMethod === "MoMo") activeTab = "momo";
        else if (order.paymentMethod === "Visa / Master") activeTab = "visa";

        function renderPaymentTab(tab) {
            activeTab = tab;
            const amount = Number(order.total) || 0;
            const transferContent = `THANH TOAN ${order.id}`;

            // Tạo mã QR VietQR chuẩn
            const vietQrUrl = `https://img.vietqr.io/image/MB-090123456789-compact2.png?amount=${amount}&addInfo=${encodeURIComponent(transferContent)}&accountName=SHOES%20STORE%20OFFICIAL`;

            let tabContentHTML = "";

            if (tab === "vietqr") {
                tabContentHTML = `
                    <div class="qr-box-container">
                        <div class="countdown-box">
                            ⏱ Phiên thanh toán bảo mật: <span id="paymentCountdown">14:59</span>
                        </div>

                        <div class="qr-frame">
                            <img src="${vietQrUrl}" alt="Mã VietQR thanh toán" class="qr-image-display" onerror="this.onerror=null; this.src='https://api.qrserver.com/v1/create-qr-code/?size=210x210&data=${encodeURIComponent('https://shoes-store.vn/pay/' + order.id)}';">
                        </div>

                        <div style="font-size:12.5px; color:var(--text-muted); margin-bottom:8px;">
                            Mở ứng dụng Ngân hàng (MB, VCB, Techcom, BIDV...) quét mã để thanh toán tự động
                        </div>

                        <div class="bank-details-box">
                            <div class="bank-detail-row">
                                <label>Ngân hàng nhận:</label>
                                <strong>MB Bank (Quân Đội)</strong>
                            </div>
                            <div class="bank-detail-row">
                                <label>Số tài khoản:</label>
                                <strong>
                                    090123456789
                                    <button type="button" class="copy-mini-btn" id="copyBankAcc">Copy</button>
                                </strong>
                            </div>
                            <div class="bank-detail-row">
                                <label>Chủ tài khoản:</label>
                                <strong>SHOES STORE OFFICIAL</strong>
                            </div>
                            <div class="bank-detail-row">
                                <label>Số tiền:</label>
                                <strong style="color:var(--primary); font-size:15px;">${money(amount)}</strong>
                            </div>
                            <div class="bank-detail-row">
                                <label>Nội dung chuyển khoản:</label>
                                <strong style="color:#d97706;">
                                    ${transferContent}
                                    <button type="button" class="copy-mini-btn" id="copyTransferContent">Copy</button>
                                </strong>
                            </div>
                        </div>
                    </div>
                `;
            } else if (tab === "vnpay") {
                tabContentHTML = `
                    <div class="qr-box-container" style="border-top:4px solid #0284c7;">
                        <div style="font-size:16px; font-weight:800; color:#0369a1; margin-bottom:6px;">
                            VNPAY-QR · Cổng thanh toán Quốc gia
                        </div>
                        <div class="qr-frame">
                            <img src="https://api.qrserver.com/v1/create-qr-code/?size=210x210&data=${encodeURIComponent('VNPAY_PAYMENT_' + order.id + '_' + amount)}" alt="VNPay QR" class="qr-image-display">
                        </div>
                        <div style="font-size:13px; font-weight:600; color:var(--text-primary); margin-bottom:4px;">
                            Quét VNPAY-QR trên hơn 40 App Ngân hàng & Ví điện tử
                        </div>
                        <div style="font-size:14px; font-weight:700; color:#0284c7; margin:8px 0;">
                            Số tiền thanh toán: ${money(amount)}
                        </div>
                        <div style="background:#eff6ff; padding:10px 14px; border-radius:8px; font-size:12px; color:#1e40af; text-align:left; width:100%;">
                            • Mã giao dịch VNPAY tạm tính: <strong>VNP${order.id}</strong><br>
                            • Giảm ngay đến 50.000₫ khi nhập mã khuyến mãi tại App ngân hàng
                        </div>
                    </div>
                `;
            } else if (tab === "momo") {
                tabContentHTML = `
                    <div class="qr-box-container" style="border-top:4px solid #db2777;">
                        <div style="font-size:16px; font-weight:800; color:#be185d; margin-bottom:6px;">
                            Ví Điện Tử MoMo · Quét Mã Thanh Toán
                        </div>
                        <div class="qr-frame" style="border-color:#fbcfe8;">
                            <img src="https://api.qrserver.com/v1/create-qr-code/?size=210x210&data=${encodeURIComponent('momo://payment?id=' + order.id + '&amount=' + amount)}" alt="MoMo QR" class="qr-image-display">
                        </div>
                        <div style="font-size:14px; font-weight:700; color:#be185d; margin:6px 0;">
                            Số tiền thanh toán: ${money(amount)}
                        </div>
                        <div style="background:#fdf2f8; padding:10px 14px; border-radius:8px; font-size:12px; color:#9d174d; text-align:left; width:100%;">
                            Tài khoản đối tác MoMo: <strong>SHOES STORE VIETNAM</strong><br>
                            Xác thực tức thì không cần nhập số tiền!
                        </div>
                    </div>
                `;
            } else if (tab === "visa") {
                tabContentHTML = `
                    <div style="background:#ffffff; border:1px solid var(--border); border-radius:12px; padding:20px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
                            <span style="font-weight:700; font-size:14px;">💳 Thẻ Tín Dụng / Ghi Nợ Quốc Tế</span>
                            <span style="font-size:18px;">💳 🔒</span>
                        </div>
                        <div class="form-group-item" style="margin-bottom:12px;">
                            <label>Số thẻ (16 chữ số)</label>
                            <input type="text" placeholder="4123 •••• •••• 8899" value="4123 9988 7766 5544" readonly>
                        </div>
                        <div class="modal-grid-2" style="margin-bottom:12px;">
                            <div class="form-group-item">
                                <label>Hết hạn (MM/YY)</label>
                                <input type="text" placeholder="12/28" value="10/28" readonly>
                            </div>
                            <div class="form-group-item">
                                <label>Mã CVV/CVC</label>
                                <input type="password" placeholder="•••" value="888" readonly>
                            </div>
                        </div>
                        <div class="form-group-item">
                            <label>Tên chủ thẻ</label>
                            <input type="text" value="${escapeHTML(order.customer.toUpperCase())}" readonly>
                        </div>
                        <div style="margin-top:14px; text-align:right;">
                            <span style="font-size:13px; color:var(--text-muted);">Tổng thanh toán: </span>
                            <strong class="price" style="font-size:16px;">${money(amount)}</strong>
                        </div>
                    </div>
                `;
            }

            paymentModalBody.innerHTML = `
                <!-- TABS CỔNG THANH TOÁN -->
                <div class="payment-tabs-nav">
                    <button type="button" class="payment-tab-btn ${activeTab === 'vietqr' ? 'active' : ''}" data-tab="vietqr">
                        🏦 VietQR Napas
                    </button>
                    <button type="button" class="payment-tab-btn ${activeTab === 'vnpay' ? 'active' : ''}" data-tab="vnpay">
                        🔹 VNPAY-QR
                    </button>
                    <button type="button" class="payment-tab-btn ${activeTab === 'momo' ? 'active' : ''}" data-tab="momo">
                        🌸 Ví MoMo
                    </button>
                    <button type="button" class="payment-tab-btn ${activeTab === 'visa' ? 'active' : ''}" data-tab="visa">
                        💳 Thẻ Visa/Master
                    </button>
                </div>

                <div style="margin-bottom:14px; font-size:13px; color:var(--text-secondary); display:flex; justify-content:space-between; align-items:center;">
                    <span>Mã đơn hàng: <strong>#${escapeHTML(order.id)}</strong></span>
                    <span>Trạng thái hiện tại: <strong class="badge ${getPaymentStatusClass(order.paymentStatus)}">${escapeHTML(order.paymentStatus || "Chờ thanh toán")}</strong></span>
                </div>

                ${tabContentHTML}
            `;

            // Tab event listeners
            paymentModalBody.querySelectorAll(".payment-tab-btn").forEach(btn => {
                btn.addEventListener("click", () => {
                    renderPaymentTab(btn.dataset.tab);
                });
            });

            // Copy buttons
            document.getElementById("copyBankAcc")?.addEventListener("click", () => {
                navigator.clipboard.writeText("090123456789").then(() => showNotice("Đã sao chép STK: 090123456789"));
            });

            document.getElementById("copyTransferContent")?.addEventListener("click", () => {
                navigator.clipboard.writeText(transferContent).then(() => showNotice("Đã sao chép nội dung: " + transferContent));
            });

            // Countdown timer (15 phút)
            let secondsLeft = 15 * 60;
            clearInterval(countdownInterval);
            countdownInterval = setInterval(() => {
                secondsLeft--;
                const timerEl = document.getElementById("paymentCountdown");
                if (timerEl) {
                    const m = Math.floor(secondsLeft / 60).toString().padStart(2, "0");
                    const s = (secondsLeft % 60).toString().padStart(2, "0");
                    timerEl.textContent = `${m}:${s}`;
                }
                if (secondsLeft <= 0) clearInterval(countdownInterval);
            }, 1000);
        }

        renderPaymentTab(activeTab);
        paymentModal.removeAttribute("hidden");
    }

    // Giả lập thanh toán thành công qua Webhook
    if (btnSimulatePaid) {
        btnSimulatePaid.addEventListener("click", () => {
            if (!activeOrderForPayment) return;
            const nowStr = new Date().toLocaleString("vi-VN");
            activeOrderForPayment.paymentStatus = "Đã thanh toán";
            activeOrderForPayment.transactionId = "VNP" + Math.floor(1000000 + Math.random() * 9000000);
            activeOrderForPayment.paidAt = nowStr;

            if (activeOrderForPayment.status === "Chờ xác nhận") {
                activeOrderForPayment.status = "Đang chuẩn bị hàng";
            }

            saveOrders();
            renderOrders();
            showNotice("✅ Đã nhận Webhook thanh toán thành công đơn #" + activeOrderForPayment.id + "! Mã GD: " + activeOrderForPayment.transactionId);
            paymentModal.setAttribute("hidden", "");
        });
    }

    // ==========================================================================
    // 7. MODAL TẠO ĐƠN HÀNG MỚI & VẬN ĐƠN (CREATE ORDER)
    // ==========================================================================
    function updateNewOrderCalculatedTotal() {
        if (!newOrderProduct || !newOrderQuantity || !newShippingCarrier || !newOrderCalculatedTotal) return;
        const selectedProd = newOrderProduct.options[newOrderProduct.selectedIndex];
        const price = Number(selectedProd?.dataset?.price || 2690000);
        const qty = Number(newOrderQuantity.value || 1);
        const selectedCarrier = newShippingCarrier.options[newShippingCarrier.selectedIndex];
        const fee = Number(selectedCarrier?.dataset?.fee || 30000);

        const total = price * qty + fee;
        newOrderCalculatedTotal.textContent = money(total) + ` (Hàng: ${money(price * qty)} + Ship: ${money(fee)})`;
    }

    if (newOrderProduct) newOrderProduct.addEventListener("change", updateNewOrderCalculatedTotal);
    if (newOrderQuantity) newOrderQuantity.addEventListener("input", updateNewOrderCalculatedTotal);
    if (newShippingCarrier) newShippingCarrier.addEventListener("change", updateNewOrderCalculatedTotal);

    if (btnCreateOrder) {
        btnCreateOrder.addEventListener("click", () => {
            if (createOrderModal) {
                createOrderForm.reset();
                updateNewOrderCalculatedTotal();
                createOrderModal.removeAttribute("hidden");
            }
        });
    }

    if (createOrderForm) {
        createOrderForm.addEventListener("submit", (e) => {
            e.preventDefault();

            const customerName = document.getElementById("newCustomerName").value.trim();
            const customerPhone = document.getElementById("newCustomerPhone").value.trim();
            const customerAddress = document.getElementById("newCustomerAddress").value.trim();
            const selectedProd = newOrderProduct.options[newOrderProduct.selectedIndex];
            const productName = selectedProd.value;
            const price = Number(selectedProd.dataset.price || 2690000);
            const variant = document.getElementById("newOrderVariant").value.trim() || "Tiêu chuẩn";
            const qty = Number(newOrderQuantity.value || 1);
            const orderType = document.getElementById("newOrderType").value;
            const paymentMethod = document.getElementById("newPaymentMethod").value;
            const paymentStatus = document.getElementById("newPaymentStatus").value;
            const selectedCarrier = newShippingCarrier.options[newShippingCarrier.selectedIndex];
            const carrierName = selectedCarrier.value;
            const shippingFee = Number(selectedCarrier.dataset.fee || 30000);
            const total = price * qty + shippingFee;

            // Sinh mã đơn và mã vận đơn tự động
            const maxIdNum = orders.reduce((max, o) => {
                const match = String(o.id).match(/\d+/);
                const num = match ? parseInt(match[0], 10) : 0;
                return num > max ? num : max;
            }, 1000);

            const newId = "DH" + (maxIdNum + 1);
            const carrierPrefix = carrierName === "GHN" ? "GHN" : carrierName === "GHTK" ? "GHTK-" : carrierName === "Viettel Post" ? "VTP-" : "SPX-";
            const newTrackingCode = carrierPrefix + Math.floor(1000000 + Math.random() * 9000000) + "VN";
            const now = new Date();
            const dateStr = now.toLocaleDateString("vi-VN") + " " + now.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });

            const newOrder = {
                id: newId,
                customer: customerName,
                phone: customerPhone,
                address: customerAddress,
                product: productName,
                variant: variant,
                quantity: qty,
                itemPrice: price * qty,
                shippingFee: shippingFee,
                total: total,
                date: dateStr,
                expectedDate: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toLocaleDateString("vi-VN"),
                type: orderType,
                status: paymentStatus === "Đã thanh toán" ? "Đang chuẩn bị hàng" : "Chờ xác nhận",
                preorderStatus: orderType === "Pre-order" ? "Đang chờ hàng" : "—",
                paymentMethod: paymentMethod,
                paymentStatus: paymentStatus,
                transactionId: paymentStatus === "Đã thanh toán" ? "TXN-" + Math.floor(100000 + Math.random() * 900000) : "Chưa có",
                paidAt: paymentStatus === "Đã thanh toán" ? dateStr : "—",
                paymentGateway: paymentMethod === "VietQR" ? "Chuyển khoản VietQR" : paymentMethod === "VNPay" ? "Cổng VNPAY-QR" : paymentMethod === "MoMo" ? "Ví MoMo" : "Tiền mặt COD",
                shippingCarrier: carrierName,
                trackingCode: newTrackingCode,
                shippingStatus: "Chờ lấy hàng",
                shipperName: "Lê Văn Hùng",
                shipperPhone: "0988.112.233",
                estimatedDelivery: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toLocaleDateString("vi-VN"),
                trackingTimeline: [
                    { time: dateStr, title: "Tạo đơn hàng thành công", desc: "Hệ thống Shoes Store đã cấp mã vận đơn " + newTrackingCode, done: true }
                ]
            };

            orders.unshift(newOrder);
            saveOrders();
            renderOrders();

            showNotice(`Đã tạo thành công đơn hàng #${newId} & Phát hành vận đơn ${newTrackingCode}!`);
            createOrderModal.setAttribute("hidden", "");
        });
    }

    // ==========================================================================
    // 8. MODAL IN PHIẾU GỬI HÀNG & VẬN ĐƠN (WAYBILL PRINT)
    // ==========================================================================
    function openPrintWaybillModal(order) {
        if (!printWaybillModal || !waybillPrintContent) return;

        const codAmount = order.paymentStatus === "Đã thanh toán" ? 0 : order.total;

        waybillPrintContent.innerHTML = `
            <div class="waybill-container">
                <div class="waybill-top">
                    <div>
                        <div class="waybill-carrier-logo">
                            📦 ${escapeHTML(order.shippingCarrier || "GHN EXPRESS")}
                        </div>
                        <div style="font-size:12px; font-weight:700; color:#475569;">
                            DỊCH VỤ VẬN CHUYỂN THƯƠNG MẠI ĐIỆN TỬ
                        </div>
                    </div>
                    <div class="waybill-barcode-box">
                        <div class="waybill-barcode-lines">||| | |||| | ||| |||| |</div>
                        <div class="waybill-tracking-num">${escapeHTML(order.trackingCode || "GHN-DEMO-CODE")}</div>
                        <div style="font-size:11px; color:#64748b;">MÃ ĐƠN HÀNG: #${escapeHTML(order.id)}</div>
                    </div>
                </div>

                <div class="waybill-grid-address">
                    <div class="waybill-addr-col">
                        <h4>TỪ (NGƯỜI GỬI):</h4>
                        <strong>SHOES STORE OFFICIAL</strong><br>
                        SĐT: 0900.888.999<br>
                        Kho hàng: 180 Cao Lỗ, Phường 4, Quận 8, TP. Hồ Chí Minh
                    </div>
                    <div class="waybill-addr-col">
                        <h4>ĐẾN (NGƯỜI NHẬN):</h4>
                        <strong style="font-size:14px;">${escapeHTML(order.customer)}</strong><br>
                        SĐT: <strong>${escapeHTML(order.phone)}</strong><br>
                        Địa chỉ: <strong>${escapeHTML(order.address || "Nhận tại bưu cục")}</strong>
                    </div>
                </div>

                <table class="waybill-items-table">
                    <thead>
                        <tr>
                            <th>TÊN HÀNG HÓA</th>
                            <th style="width:70px; text-align:center;">SL</th>
                            <th style="width:130px; text-align:right;">GIÁ TRỊ</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>
                                <strong>${escapeHTML(order.product)}</strong><br>
                                <span style="font-size:11px; color:#64748b;">${escapeHTML(order.variant)} · Phí ship: ${money(order.shippingFee || 0)}</span>
                            </td>
                            <td style="text-align:center; font-weight:700;">${order.quantity || 1}</td>
                            <td style="text-align:right; font-weight:700;">${money(order.total)}</td>
                        </tr>
                    </tbody>
                </table>

                <div class="waybill-cod-box">
                    <div>
                        <div style="font-size:11px; text-transform:uppercase; font-weight:700; color:#475569;">
                            TIỀN THU NGƯỜI NHẬN (COD):
                        </div>
                        <div style="font-size:12px; color:#64748b;">
                            ${order.paymentStatus === "Đã thanh toán"
                                ? `✅ Đã thanh toán trực tuyến qua <strong>${escapeHTML(order.paymentMethod)}</strong> - KHÔNG THU TIỀN`
                                : `⚠️ Thu tiền mặt khi giao hàng (Bao gồm tiền hàng + Ship)`
                            }
                        </div>
                    </div>
                    <div class="waybill-cod-amount">
                        ${money(codAmount)}
                    </div>
                </div>

                <div style="display:flex; justify-content:space-between; margin-top:20px; font-size:11.5px; text-align:center;">
                    <div style="width:45%;">
                        <strong>CHỮ KÝ NGƯỜI GỬI</strong><br>
                        <span style="font-size:10px; color:#64748b;">(Xác nhận hàng nguyên vẹn)</span>
                        <div style="height:40px;"></div>
                        <span>Shoes Admin</span>
                    </div>
                    <div style="width:45%;">
                        <strong>CHỮ KÝ NGƯỜI NHẬN</strong><br>
                        <span style="font-size:10px; color:#64748b;">(Đồng kiểm và nhận hàng)</span>
                        <div style="height:40px;"></div>
                        <span>${escapeHTML(order.customer)}</span>
                    </div>
                </div>
            </div>
        `;

        printWaybillModal.removeAttribute("hidden");
    }

    if (btnPrintExecute) {
        btnPrintExecute.addEventListener("click", () => {
            window.print();
        });
    }

    // ==========================================================================
    // 9. XUẤT DANH SÁCH & ĐẶT LẠI BỘ LỌC
    // ==========================================================================
    if (resetFiltersBtn) {
        resetFiltersBtn.addEventListener("click", () => {
            if (searchInput) searchInput.value = "";
            if (statusFilter) statusFilter.value = "";
            if (paymentStatusFilter) paymentStatusFilter.value = "";
            if (paymentMethodFilter) paymentMethodFilter.value = "";
            if (shippingCarrierFilter) shippingCarrierFilter.value = "";
            if (shippingStatusFilter) shippingStatusFilter.value = "";
            if (typeFilter) typeFilter.value = "";
            renderOrders();
            showNotice("Đã đặt lại bộ lọc tìm kiếm!");
        });
    }

    if (exportOrdersBtn) {
        exportOrdersBtn.addEventListener("click", () => {
            const headers = ["Mã đơn", "Khách hàng", "Số điện thoại", "Địa chỉ", "Sản phẩm", "Biến thể", "Số lượng", "Tổng tiền", "Thanh toán", "Trạng thái TT", "ĐV Vận chuyển", "Mã vận đơn", "Trạng thái giao", "Trạng thái đơn"];
            const rows = orders.map(o => [
                o.id,
                `"${o.customer}"`,
                o.phone,
                `"${o.address}"`,
                `"${o.product}"`,
                `"${o.variant}"`,
                o.quantity || 1,
                o.total,
                o.paymentMethod,
                o.paymentStatus,
                o.shippingCarrier,
                o.trackingCode,
                o.shippingStatus,
                o.status
            ]);

            const csvContent = "\uFEFF" + [headers.join(","), ...rows.map(r => r.join(","))].join("\n");
            const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `Danh_Sach_Don_Hang_${new Date().toISOString().slice(0, 10)}.csv`;
            a.click();
            URL.revokeObjectURL(url);
            showNotice("Đã xuất file CSV đơn hàng thành công!");
        });
    }

    // Modal Cài đặt
    if (btnSettings && settingsModal) {
        btnSettings.addEventListener("click", () => settingsModal.removeAttribute("hidden"));
    }
    if (closeSettingsModal && settingsModal) {
        closeSettingsModal.addEventListener("click", () => settingsModal.setAttribute("hidden", ""));
    }
    if (btnCloseSettings && settingsModal) {
        btnCloseSettings.addEventListener("click", () => settingsModal.setAttribute("hidden", ""));
    }

    // Modal Close generic
    function setupModalClose(modalEl, closeButtons) {
        if (!modalEl) return;
        closeButtons.forEach(btn => {
            if (btn) btn.addEventListener("click", () => modalEl.setAttribute("hidden", ""));
        });
        modalEl.addEventListener("click", (e) => {
            if (e.target === modalEl) modalEl.setAttribute("hidden", "");
        });
    }

    setupModalClose(detailModal, [closeModalBtn, closeDetailBtn]);
    setupModalClose(trackingModal, [closeTrackingModal, btnCloseTracking]);
    setupModalClose(paymentModal, [closePaymentModal, btnClosePayment]);
    setupModalClose(createOrderModal, [closeCreateModal, btnCancelCreate]);
    setupModalClose(printWaybillModal, [closePrintModal, btnClosePrint]);
    setupModalClose(settingsModal, [closeSettingsModal, btnCloseSettings]);

    // Lắng nghe sự kiện bộ lọc
    if (searchInput) searchInput.addEventListener("input", renderOrders);
    if (statusFilter) statusFilter.addEventListener("change", renderOrders);
    if (paymentStatusFilter) paymentStatusFilter.addEventListener("change", renderOrders);
    if (paymentMethodFilter) paymentMethodFilter.addEventListener("change", renderOrders);
    if (shippingCarrierFilter) shippingCarrierFilter.addEventListener("change", renderOrders);
    if (shippingStatusFilter) shippingStatusFilter.addEventListener("change", renderOrders);
    if (typeFilter) typeFilter.addEventListener("change", renderOrders);

    // Lắng nghe click các nút thao tác trên bảng
    if (orderListTbody) {
        orderListTbody.addEventListener("click", e => {
            const btn = e.target.closest("button[data-action]");
            if (!btn) return;
            const action = btn.dataset.action;
            const orderId = btn.dataset.id;
            const order = orders.find(o => String(o.id) === String(orderId));
            if (!order) return;

            if (action === "view") {
                openOrderDetail(order);
            } else if (action === "track") {
                openTrackingModal(order);
            } else if (action === "pay") {
                openPaymentModal(order);
            } else if (action === "print") {
                openPrintWaybillModal(order);
            }
        });
    }

    // Khởi tạo hiển thị ban đầu
    renderOrders();
});