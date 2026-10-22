/**
 * ==========================================================================
 * SHOES STORE - BLACK & WHITE CUSTOMER AUTHENTICATION CONTROLLER
 * Xử lý Đăng ký & Đăng nhập khách hàng phiên bản Đen Trắng
 * ==========================================================================
 */

(function () {
    "use strict";

    const ACCOUNTS_KEY = "shoesCustomerAccounts";
    const SESSION_KEY = "shoesCustomerSession";
    const ADMIN_CUST_KEY = "shoesCustomers";

    const DEMO_ACCOUNTS = [
        { id: "KH1001", name: "NGUYỄN VĂN AN", phone: "0901234567", email: "an.nguyen@gmail.com", address: "123 Lê Lợi, Quận 1, TP. HCM", password: "123456", tier: "KIM CƯƠNG", points: 1850 },
        { id: "KH1002", name: "TRẦN MINH ĐỨC", phone: "0987654321", email: "duc.tran@gmail.com", address: "456 Nguyễn Thị Minh Khai, Quận 3, TP. HCM", password: "123456", tier: "VÀNG", points: 980 }
    ];

    function getAccounts() {
        try {
            const raw = localStorage.getItem(ACCOUNTS_KEY);
            let accs = raw ? JSON.parse(raw) : [];
            if (!Array.isArray(accs) || accs.length === 0) {
                accs = [...DEMO_ACCOUNTS];
                localStorage.setItem(ACCOUNTS_KEY, JSON.stringify(accs));
            }
            return accs;
        } catch {
            return [...DEMO_ACCOUNTS];
        }
    }

    function saveAccounts(accs) {
        try {
            localStorage.setItem(ACCOUNTS_KEY, JSON.stringify(accs));
        } catch (e) {
            console.error("Save error:", e);
        }
    }

    function showAlert(msg, isSuccess) {
        const alertEl = document.getElementById("monoAlert");
        if (!alertEl) return;
        alertEl.style.display = "block";
        alertEl.style.color = isSuccess ? "#ffffff" : "#ff4444";
        alertEl.style.borderColor = isSuccess ? "#ffffff" : "#ff4444";
        alertEl.textContent = msg;
    }

    document.addEventListener("DOMContentLoaded", () => {
        getAccounts();

        // 1. Xử lý Đăng nhập
        const loginForm = document.getElementById("monoLoginForm");
        if (loginForm) {
            loginForm.addEventListener("submit", (e) => {
                e.preventDefault();
                const identity = document.getElementById("monoIdentity").value.trim().toLowerCase();
                const pass = document.getElementById("monoPassword").value;

                if (!identity || !pass) {
                    showAlert("VUI LÒNG NHẬP ĐẦY ĐỦ THÔNG TIN ĐĂNG NHẬP!", false);
                    return;
                }

                const accounts = getAccounts();
                const found = accounts.find(
                    a => (a.email && a.email.toLowerCase() === identity) ||
                         (a.phone && a.phone === identity)
                );

                if (!found) {
                    showAlert("TÀI KHOẢN KHÔNG TỒN TẠI! VUI LÒNG CHỌN TAB ĐĂNG KÝ.", false);
                    return;
                }

                if (found.password !== pass) {
                    showAlert("MẬT KHẨU KHÔNG CHÍNH XÁC!", false);
                    return;
                }

                // Lưu phiên đăng nhập
                const session = {
                    id: found.id,
                    name: found.name,
                    phone: found.phone,
                    email: found.email,
                    address: found.address,
                    tier: found.tier || "ĐỒNG",
                    points: found.points || 100,
                    role: "customer"
                };

                sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
                localStorage.setItem(SESSION_KEY, JSON.stringify(session));
                sessionStorage.setItem("loggedInCustomer", JSON.stringify(session));

                showAlert(`XIN CHÀO ${found.name}! ĐĂNG NHẬP THÀNH CÔNG. ĐANG VÀO CỬA HÀNG...`, true);

                setTimeout(() => {
                    window.location.href = "./customer_shop.html";
                }, 800);
            });
        }

        // 2. Xử lý Đăng ký
        const regForm = document.getElementById("monoRegisterForm");
        if (regForm) {
            regForm.addEventListener("submit", (e) => {
                e.preventDefault();
                const name = document.getElementById("regName").value.trim().toUpperCase();
                const phone = document.getElementById("regPhone").value.trim();
                const email = document.getElementById("regEmail").value.trim().toLowerCase();
                const address = document.getElementById("regAddress").value.trim();
                const pass = document.getElementById("regPassword").value;
                const confirm = document.getElementById("regConfirm").value;

                if (!name || !phone || !email || !address) {
                    showAlert("VUI LÒNG ĐIỀN ĐỦ THÔNG TIN GIAO HÀNG!", false);
                    return;
                }

                if (pass.length < 6) {
                    showAlert("MẬT KHẨU PHẢI TỪ 6 KÝ TỰ TRỞ LÊN!", false);
                    return;
                }

                if (pass !== confirm) {
                    showAlert("MẬT KHẨU XÁC NHẬN KHÔNG KHỚP!", false);
                    return;
                }

                const accounts = getAccounts();
                const dup = accounts.find(a => a.email === email || a.phone === phone);
                if (dup) {
                    showAlert("EMAIL HOẶC SỐ ĐIỆN THOẠI ĐÃ ĐƯỢC ĐĂNG KÝ!", false);
                    return;
                }

                const newCust = {
                    id: "KH" + Math.floor(1000 + Math.random() * 9000),
                    name: name,
                    phone: phone,
                    email: email,
                    address: address,
                    password: pass,
                    tier: "ĐỒNG",
                    points: 100
                };

                accounts.unshift(newCust);
                saveAccounts(accounts);

                // Đồng bộ sang Admin Customers
                try {
                    const rawCusts = localStorage.getItem(ADMIN_CUST_KEY);
                    let adminCusts = rawCusts ? JSON.parse(rawCusts) : [];
                    adminCusts.unshift({
                        id: newCust.id,
                        name: newCust.name,
                        phone: newCust.phone,
                        email: newCust.email,
                        tier: "ĐỒNG",
                        orders: 0,
                        spent: 0
                    });
                    localStorage.setItem(ADMIN_CUST_KEY, JSON.stringify(adminCusts));
                } catch {}

                showAlert("ĐĂNG KÝ THÀNH CÔNG! BẠN NHẬN ĐƯỢC 100 ĐIỂM THƯỞNG. ĐANG CHUYỂN VÀO ĐĂNG NHẬP...", true);

                setTimeout(() => {
                    if (typeof switchAuthTab === "function") {
                        switchAuthTab("login");
                        document.getElementById("monoIdentity").value = phone || email;
                        document.getElementById("monoPassword").focus();
                    }
                }, 1000);
            });
        }
    });
})();
