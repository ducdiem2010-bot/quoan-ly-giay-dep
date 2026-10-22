/**
 * ==========================================================================
 * SHOES STORE - ADMIN AUTHENTICATION JAVASCRIPT
 * Xử lý Đăng ký, Đăng nhập, Phiên làm việc (Session) & Liên kết giữa 2 trang
 * ==========================================================================
 */

(function () {
    "use strict";

    const ACCOUNT_KEY = "shoesAdminAccounts";
    const SESSION_KEY = "shoesAdminSession";
    const REMEMBER_KEY = "shoesAdminRememberedEmail";
    const FLASH_KEY = "shoesAuthFlash";

    // Tài khoản Admin mặc định demo
    const DEFAULT_ADMIN = {
        id: "ADM_DEMO",
        name: "Admin Quản Trị",
        email: "admin@gmail.com",
        phone: "0901234567",
        password: "admin123",
        role: "admin",
        createdAt: 1704067200000
    };

    /**
     * Lấy danh sách tài khoản đã đăng ký trong localStorage
     */
    function getAccounts() {
        try {
            const raw = localStorage.getItem(ACCOUNT_KEY);
            let accounts = raw ? JSON.parse(raw) : [];
            if (!Array.isArray(accounts)) accounts = [];

            // Đảm bảo tài khoản demo luôn có sẵn
            const hasDemo = accounts.some(
                acc => (acc.email || "").toLowerCase() === DEFAULT_ADMIN.email.toLowerCase()
            );
            if (!hasDemo) {
                accounts.unshift(DEFAULT_ADMIN);
                localStorage.setItem(ACCOUNT_KEY, JSON.stringify(accounts));
            }
            return accounts;
        } catch (err) {
            console.error("Lỗi đọc danh sách tài khoản:", err);
            return [DEFAULT_ADMIN];
        }
    }

    /**
     * Lưu danh sách tài khoản vào localStorage
     */
    function saveAccounts(accounts) {
        try {
            localStorage.setItem(ACCOUNT_KEY, JSON.stringify(accounts));
            return true;
        } catch (err) {
            console.error("Lỗi ghi danh sách tài khoản:", err);
            return false;
        }
    }

    /**
     * Tìm tài khoản theo email
     */
    function findAccountByEmail(email) {
        if (!email) return null;
        const normalized = email.trim().toLowerCase();
        const accounts = getAccounts();
        return accounts.find(acc => (acc.email || "").trim().toLowerCase() === normalized) || null;
    }

    /**
     * Hiển thị thông báo trên form
     */
    function showMessage(elId, message, type = "error") {
        const el = document.getElementById(elId);
        if (!el) return;

        el.className = `message show ${type}`;
        const icon = type === "success" ? "✅" : (type === "info" ? "ℹ️" : "⚠️");
        el.innerHTML = `<span>${icon}</span><div>${message}</div>`;
    }

    /**
     * Đánh giá độ mạnh mật khẩu (1 - 4)
     */
    function evaluatePasswordStrength(password) {
        if (!password) return { score: 0, label: "Chưa nhập", color: "#cbd5e1", width: "0%" };

        let score = 0;
        if (password.length >= 6) score += 1;
        if (password.length >= 8) score += 1;
        if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score += 1;
        if (/[0-9]/.test(password) && /[^A-Za-z0-9]/.test(password)) score += 1;

        switch (score) {
            case 1:
                return { score, label: "Yếu", color: "#dc2626", width: "25%" };
            case 2:
                return { score, label: "Trung bình", color: "#f59e0b", width: "50%" };
            case 3:
                return { score, label: "Mạnh", color: "#10b981", width: "75%" };
            case 4:
                return { score, label: "Rất mạnh", color: "#16a34a", width: "100%" };
            default:
                return { score: 0, label: "Quá ngắn", color: "#dc2626", width: "10%" };
        }
    }

    /**
     * XỬ LÝ ĐĂNG KÝ ADMIN
     */
    function handleRegister(name, email, phone, password, confirmPassword) {
        const messageEl = "registerMessage";
        const submitBtn = document.getElementById("registerButton");

        name = (name || "").trim();
        email = (email || "").trim().toLowerCase();
        phone = (phone || "").trim();
        password = password || "";
        confirmPassword = confirmPassword || "";

        // Kiểm tra hợp lệ dữ liệu
        if (!name || name.length < 2) {
            showMessage(messageEl, "Vui lòng nhập họ và tên hợp lệ (tối thiểu 2 ký tự).", "error");
            return false;
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!email || !emailRegex.test(email)) {
            showMessage(messageEl, "Vui lòng nhập địa chỉ email hợp lệ.", "error");
            return false;
        }

        if (password.length < 6) {
            showMessage(messageEl, "Mật khẩu phải có độ dài ít nhất 6 ký tự.", "error");
            return false;
        }

        if (password !== confirmPassword) {
            showMessage(messageEl, "Mật khẩu xác nhận không trùng khớp!", "error");
            return false;
        }

        // Kiểm tra trùng email
        const existing = findAccountByEmail(email);
        if (existing) {
            showMessage(
                messageEl,
                `Email <strong>${email}</strong> đã được đăng ký. Bạn có thể <a href="./admin_login.html?email=${encodeURIComponent(email)}" style="font-weight:700; color:#dc2626; text-decoration:underline;">đăng nhập ngay tại đây</a>.`,
                "error"
            );
            return false;
        }

        // Tạo tài khoản mới
        const newAccount = {
            id: "ADM_" + Date.now(),
            name: name,
            email: email,
            phone: phone,
            password: password,
            role: "admin",
            createdAt: Date.now()
        };

        const accounts = getAccounts();
        accounts.push(newAccount);
        saveAccounts(accounts);

        // Lưu thông báo liên kết sang trang đăng nhập
        sessionStorage.setItem(FLASH_KEY, JSON.stringify({
            type: "success",
            email: email,
            message: `🎉 Đăng ký thành công tài khoản <strong>${email}</strong>! Vui lòng đăng nhập để bắt đầu.`
        }));

        showMessage(
            messageEl,
            "Đăng ký thành công! Đang chuyển hướng sang trang đăng nhập...",
            "success"
        );

        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = `<span class="spinner"></span> Đang chuyển sang đăng nhập...`;
        }

        // Tự động chuyển sang trang đăng nhập sau 1.2s kèm email vừa đăng ký
        setTimeout(() => {
            window.location.href = `./admin_login.html?registered=1&email=${encodeURIComponent(email)}`;
        }, 1200);

        return true;
    }

    /**
     * XỬ LÝ ĐĂNG NHẬP ADMIN
     */
    function handleLogin(email, password, rememberMe) {
        const messageEl = "loginMessage";
        const submitBtn = document.getElementById("loginButton");

        email = (email || "").trim().toLowerCase();
        password = password || "";

        if (!email) {
            showMessage(messageEl, "Vui lòng nhập email đăng nhập.", "error");
            return false;
        }

        if (!password) {
            showMessage(messageEl, "Vui lòng nhập mật khẩu.", "error");
            return false;
        }

        const account = findAccountByEmail(email);

        if (!account) {
            showMessage(
                messageEl,
                `Email này chưa được đăng ký trong hệ thống. <a href="./admin_register.html?email=${encodeURIComponent(email)}" style="font-weight:700; color:#dc2626; text-decoration:underline;">Nhấn vào đây để đăng ký tài khoản mới</a>.`,
                "error"
            );
            return false;
        }

        if (account.password !== password) {
            showMessage(messageEl, "Mật khẩu không chính xác! Vui lòng kiểm tra lại.", "error");
            return false;
        }

        // Tạo phiên làm việc Admin
        const session = {
            id: account.id,
            name: account.name || "Admin Quản Trị",
            email: account.email,
            phone: account.phone || "",
            role: "admin",
            loggedInAt: Date.now()
        };

        sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));

        // Xử lý "Ghi nhớ đăng nhập"
        if (rememberMe) {
            localStorage.setItem(REMEMBER_KEY, account.email);
        } else {
            localStorage.removeItem(REMEMBER_KEY);
        }

        showMessage(
            messageEl,
            `Xin chào <strong>${session.name}</strong>! Đăng nhập thành công, đang vào trang quản trị...`,
            "success"
        );

        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = `<span class="spinner"></span> Đang vào hệ thống...`;
        }

        // Chuyển hướng vào trang quản trị
        setTimeout(() => {
            window.location.href = "./admin_base.html";
        }, 800);

        return true;
    }

    /**
     * Gắn bộ bật/tắt hiển thị mật khẩu
     */
    function setupPasswordToggles() {
        document.querySelectorAll(".toggle-password").forEach(btn => {
            btn.addEventListener("click", function () {
                const targetId = this.getAttribute("data-target");
                const input = document.getElementById(targetId);
                if (!input) return;

                if (input.type === "password") {
                    input.type = "text";
                    this.textContent = "🙈";
                    this.title = "Ẩn mật khẩu";
                } else {
                    input.type = "password";
                    this.textContent = "👁️";
                    this.title = "Hiện mật khẩu";
                }
            });
        });
    }

    /**
     * Kiểm tra trạng thái đã đăng nhập trên các trang Admin
     */
    function requireAdminLogin() {
        let session = null;
        try {
            session = JSON.parse(sessionStorage.getItem(SESSION_KEY) || "null");
        } catch {
            session = null;
        }

        if (!session || !session.id || session.role !== "admin") {
            window.location.replace("./admin_login.html");
            return false;
        }
        return true;
    }

    /**
     * Đăng xuất khỏi hệ thống
     */
    function logoutAdmin() {
        sessionStorage.removeItem(SESSION_KEY);
        window.location.replace("./admin_login.html");
    }

    // Khởi tạo các sự kiện khi DOM sẵn sàng
    document.addEventListener("DOMContentLoaded", () => {
        // Đảm bảo tài khoản demo mặc định luôn sẵn sàng
        getAccounts();
        setupPasswordToggles();

        // 1. TRANG ĐĂNG KÝ (admin_register.html)
        const registerForm = document.getElementById("registerForm");
        if (registerForm) {
            const nameInput = document.getElementById("registerName");
            const emailInput = document.getElementById("registerEmail");
            const phoneInput = document.getElementById("registerPhone");
            const passInput = document.getElementById("registerPassword");
            const confirmInput = document.getElementById("confirmPassword");
            const meterFill = document.getElementById("meterFill");
            const meterText = document.getElementById("meterText");

            // Đọc email gợi ý từ URL nếu có
            const params = new URLSearchParams(window.location.search);
            if (params.has("email") && emailInput) {
                emailInput.value = params.get("email");
            }

            // Đo độ mạnh mật khẩu realtime
            if (passInput && meterFill && meterText) {
                passInput.addEventListener("input", () => {
                    const evaluation = evaluatePasswordStrength(passInput.value);
                    meterFill.style.width = evaluation.width;
                    meterFill.style.background = evaluation.color;
                    meterText.textContent = `Độ mạnh: ${evaluation.label}`;
                    meterText.style.color = evaluation.color;
                });
            }

            registerForm.addEventListener("submit", (e) => {
                e.preventDefault();
                handleRegister(
                    nameInput ? nameInput.value : "",
                    emailInput ? emailInput.value : "",
                    phoneInput ? phoneInput.value : "",
                    passInput ? passInput.value : "",
                    confirmInput ? confirmInput.value : ""
                );
            });
        }

        // 2. TRANG ĐĂNG NHẬP (admin_login.html)
        const loginForm = document.getElementById("loginForm");
        if (loginForm) {
            const emailInput = document.getElementById("email");
            const passInput = document.getElementById("password");
            const rememberInput = document.getElementById("rememberMe");
            const demoBox = document.getElementById("demoBox");

            // Kiểm tra thông báo chuyển từ Đăng ký sang
            let flash = null;
            try {
                flash = JSON.parse(sessionStorage.getItem(FLASH_KEY) || "null");
            } catch {
                flash = null;
            }

            const urlParams = new URLSearchParams(window.location.search);
            const paramEmail = urlParams.get("email");
            const isJustRegistered = urlParams.get("registered") === "1";

            if (flash && flash.message) {
                showMessage("loginMessage", flash.message, flash.type || "success");
                if (flash.email && emailInput) {
                    emailInput.value = flash.email;
                    if (passInput) passInput.focus();
                }
                sessionStorage.removeItem(FLASH_KEY);
            } else if (isJustRegistered && paramEmail) {
                showMessage(
                    "loginMessage",
                    `🎉 Đăng ký thành công tài khoản <strong>${paramEmail}</strong>! Mời bạn nhập mật khẩu để đăng nhập.`,
                    "success"
                );
                if (emailInput) {
                    emailInput.value = paramEmail;
                    if (passInput) passInput.focus();
                }
            } else if (paramEmail && emailInput) {
                emailInput.value = paramEmail;
            } else {
                // Kiểm tra tài khoản đã ghi nhớ trước đó
                const remembered = localStorage.getItem(REMEMBER_KEY);
                if (remembered && emailInput) {
                    emailInput.value = remembered;
                    if (rememberInput) rememberInput.checked = true;
                }
            }

            // Click vào box demo để tự điền nhanh
            if (demoBox) {
                demoBox.addEventListener("click", () => {
                    if (emailInput) emailInput.value = DEFAULT_ADMIN.email;
                    if (passInput) passInput.value = DEFAULT_ADMIN.password;
                    showMessage(
                        "loginMessage",
                        "Đã điền thông tin tài khoản demo quản trị!",
                        "info"
                    );
                });
            }

            loginForm.addEventListener("submit", (e) => {
                e.preventDefault();
                handleLogin(
                    emailInput ? emailInput.value : "",
                    passInput ? passInput.value : "",
                    rememberInput ? rememberInput.checked : false
                );
            });
        }
    });

    // Xuất ra global namespace
    window.ShoesAuth = {
        getAccounts,
        findAccountByEmail,
        handleRegister,
        handleLogin,
        requireAdminLogin,
        logoutAdmin,
        DEFAULT_ADMIN
    };
})();
