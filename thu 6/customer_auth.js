/**
 * ==========================================================================
 * SHOES STORE - CUSTOMER AUTHENTICATION (ĐĂNG KÝ & ĐĂNG NHẬP MUA HÀNG)
 * Quản lý tài khoản khách mua hàng, đồng bộ danh sách Admin & hỗ trợ mua sắm
 * ==========================================================================
 */

(function () {
    "use strict";

    const CUSTOMER_ACCOUNTS_KEY = "shoesCustomerAccounts";
    const CUSTOMER_SESSION_KEY = "shoesCustomerSession";
    const COMPAT_SESSION_KEY = "loggedInCustomer";
    const ADMIN_CUSTOMERS_KEY = "shoesCustomers";
    const SYNC_USERS_KEY = "shoesUsers";
    const REMEMBER_KEY = "shoesCustomerRemembered";
    const FLASH_KEY = "shoesCustomerAuthFlash";

    // Danh sách tài khoản khách hàng mẫu (đồng bộ từ admin_customers)
    const DEMO_CUSTOMERS = [
        {
            id: "KH1001",
            name: "Nguyễn Văn An",
            phone: "0901234567",
            email: "an.nguyen@gmail.com",
            address: "123 Lê Lợi, Phường Bến Nghé, Quận 1, TP. Hồ Chí Minh",
            password: "123456",
            tier: "Kim cương",
            points: 1850,
            ordersCount: 8,
            spent: 18500000,
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
            password: "123456",
            tier: "Vàng",
            points: 980,
            ordersCount: 5,
            spent: 9800000,
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
            password: "123456",
            tier: "Bạc",
            points: 465,
            ordersCount: 3,
            spent: 4650000,
            status: "active",
            avatar: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=200&q=80",
            joinDate: "20/02/2026",
            notes: "Thích phong cách Chunky Sneaker của Puma"
        }
    ];

    /**
     * Lấy danh sách tài khoản khách hàng từ localStorage
     */
    function getCustomerAccounts() {
        try {
            const raw = localStorage.getItem(CUSTOMER_ACCOUNTS_KEY);
            let accounts = raw ? JSON.parse(raw) : [];
            if (!Array.isArray(accounts) || accounts.length === 0) {
                accounts = [...DEMO_CUSTOMERS];
                localStorage.setItem(CUSTOMER_ACCOUNTS_KEY, JSON.stringify(accounts));
            }
            return accounts;
        } catch (e) {
            console.error("Lỗi đọc tài khoản khách hàng:", e);
            return [...DEMO_CUSTOMERS];
        }
    }

    /**
     * Lưu danh sách tài khoản khách hàng
     */
    function saveCustomerAccounts(accounts) {
        try {
            localStorage.setItem(CUSTOMER_ACCOUNTS_KEY, JSON.stringify(accounts));
            return true;
        } catch (e) {
            console.error("Lỗi lưu tài khoản khách hàng:", e);
            return false;
        }
    }

    /**
     * Đồng bộ tài khoản sang danh sách Khách hàng của Admin (admin_customers)
     */
    function syncToAdminCustomers(customer) {
        try {
            let adminList = [];
            const raw = localStorage.getItem(ADMIN_CUSTOMERS_KEY);
            if (raw) adminList = JSON.parse(raw);
            if (!Array.isArray(adminList)) adminList = [];

            const index = adminList.findIndex(
                c => (c.email && c.email.toLowerCase() === customer.email.toLowerCase()) ||
                     (c.phone && c.phone === customer.phone)
            );

            const adminRecord = {
                id: customer.id,
                name: customer.name,
                phone: customer.phone,
                email: customer.email,
                address: customer.address || "Chưa cập nhật địa chỉ",
                tier: customer.tier || "Đồng",
                ordersCount: customer.ordersCount || 0,
                spent: customer.spent || 0,
                points: customer.points || 100,
                status: "active",
                avatar: customer.avatar || "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=200&q=80",
                joinDate: customer.joinDate || new Date().toLocaleDateString("vi-VN"),
                notes: customer.notes || "Khách đăng ký mua hàng online"
            };

            if (index !== -1) {
                adminList[index] = { ...adminList[index], ...adminRecord };
            } else {
                adminList.unshift(adminRecord);
            }

            localStorage.setItem(ADMIN_CUSTOMERS_KEY, JSON.stringify(adminList));
            localStorage.setItem(SYNC_USERS_KEY, JSON.stringify(adminList));
        } catch (err) {
            console.warn("Lỗi đồng bộ khách hàng sang Admin:", err);
        }
    }

    /**
     * Hiển thị thông báo trên form khách hàng
     */
    function showCustomerAlert(elId, message, type = "error") {
        const el = document.getElementById(elId);
        if (!el) return;
        el.className = `auth-alert show ${type}`;
        const icon = type === "success" ? "🎉" : (type === "info" ? "💡" : "⚠️");
        el.innerHTML = `<span>${icon}</span><div>${message}</div>`;
    }

    /**
     * Đánh giá độ mạnh mật khẩu
     */
    function calcPasswordStrength(password) {
        if (!password) return { width: "0%", color: "#cbd5e1", label: "Chưa nhập" };
        let score = 0;
        if (password.length >= 6) score++;
        if (password.length >= 8) score++;
        if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score++;
        if (/\d/.test(password) && /[^A-Za-z0-9]/.test(password)) score++;

        switch (score) {
            case 1: return { width: "25%", color: "#ef4444", label: "Yếu" };
            case 2: return { width: "50%", color: "#f59e0b", label: "Trung bình" };
            case 3: return { width: "75%", color: "#10b981", label: "Mạnh" };
            case 4: return { width: "100%", color: "#059669", label: "Rất an toàn" };
            default: return { width: "10%", color: "#ef4444", label: "Quá ngắn" };
        }
    }

    /**
     * Lấy phiên đăng nhập hiện tại của khách hàng
     */
    function getCurrentCustomer() {
        try {
            const session = sessionStorage.getItem(CUSTOMER_SESSION_KEY) ||
                            localStorage.getItem(CUSTOMER_SESSION_KEY) ||
                            sessionStorage.getItem(COMPAT_SESSION_KEY);
            return session ? JSON.parse(session) : null;
        } catch {
            return null;
        }
    }

    /**
     * XỬ LÝ ĐĂNG KÝ TÀI KHOẢN KHÁCH HÀNG
     */
    function handleCustomerRegister(data) {
        const alertId = "registerAlert";
        const btn = document.getElementById("btnCustRegister");

        const name = (data.name || "").trim();
        const phone = (data.phone || "").trim().replace(/\s+/g, "");
        const email = (data.email || "").trim().toLowerCase();
        const address = (data.address || "").trim();
        const password = data.password || "";
        const confirmPassword = data.confirmPassword || "";
        const agreeTerms = data.agreeTerms;

        // 1. Kiểm tra họ tên
        if (!name || name.length < 2) {
            showCustomerAlert(alertId, "Vui lòng nhập họ và tên người nhận hàng (tối thiểu 2 ký tự).", "error");
            return false;
        }

        // 2. Kiểm tra số điện thoại (10 số, bắt đầu bằng 03, 05, 07, 08, 09)
        const phoneRegex = /^(03|05|07|08|09)\d{8}$/;
        if (!phone || !phoneRegex.test(phone)) {
            showCustomerAlert(alertId, "Số điện thoại nhận hàng không hợp lệ (cần 10 chữ số, ví dụ 0912345678).", "error");
            return false;
        }

        // 3. Kiểm tra email
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!email || !emailRegex.test(email)) {
            showCustomerAlert(alertId, "Vui lòng nhập email hợp lệ để nhận thông báo vận đơn và hóa đơn mua hàng.", "error");
            return false;
        }

        // 4. Kiểm tra địa chỉ giao hàng
        if (!address || address.length < 5) {
            showCustomerAlert(alertId, "Vui lòng nhập địa chỉ giao hàng cụ thể để hỗ trợ ship giày tận nơi.", "error");
            return false;
        }

        // 5. Kiểm tra mật khẩu
        if (password.length < 6) {
            showCustomerAlert(alertId, "Mật khẩu phải từ 6 ký tự trở lên.", "error");
            return false;
        }

        if (password !== confirmPassword) {
            showCustomerAlert(alertId, "Mật khẩu xác nhận không trùng khớp. Vui lòng kiểm tra lại!", "error");
            return false;
        }

        if (!agreeTerms) {
            showCustomerAlert(alertId, "Bạn vui lòng đồng ý với điều khoản mua hàng & chính sách của Shoes Store.", "error");
            return false;
        }

        // 6. Kiểm tra trùng email hoặc số điện thoại
        const accounts = getCustomerAccounts();
        const duplicate = accounts.find(
            acc => (acc.email && acc.email.toLowerCase() === email) ||
                   (acc.phone && acc.phone === phone)
        );

        if (duplicate) {
            const isPhone = duplicate.phone === phone;
            showCustomerAlert(
                alertId,
                `${isPhone ? "Số điện thoại" : "Email"} này đã được đăng ký. Bạn có thể <a href="javascript:void(0)" onclick="window.ShoesCustomerAuth.switchTab('login', '${isPhone ? phone : email}')" style="font-weight:700; color:#b91c1c; text-decoration:underline;">đăng nhập ngay tại đây</a>.`,
                "error"
            );
            return false;
        }

        // 7. Tạo tài khoản khách hàng mới
        const newCustomer = {
            id: "KH" + Math.floor(1000 + Math.random() * 9000),
            name: name,
            phone: phone,
            email: email,
            address: address,
            password: password,
            tier: "Đồng",
            points: 100, // Tặng ngay 100 điểm chào mừng
            ordersCount: 0,
            spent: 0,
            status: "active",
            avatar: "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=200&q=80",
            joinDate: new Date().toLocaleDateString("vi-VN"),
            notes: "Khách hàng đăng ký trực tuyến tại Shoes Store",
            createdAt: Date.now()
        };

        accounts.unshift(newCustomer);
        saveCustomerAccounts(accounts);

        // Đồng bộ trực tiếp vào cơ sở dữ liệu khách hàng Admin
        syncToAdminCustomers(newCustomer);

        // Lưu thông báo flash
        sessionStorage.setItem(FLASH_KEY, JSON.stringify({
            type: "success",
            identity: phone || email,
            name: name,
            message: `🎉 Chúc mừng <strong>${name}</strong> đã tạo tài khoản thành công! Tặng bạn <strong>100 điểm thưởng</strong> và mã giảm 10% <strong>CHAOBANMOI</strong>. Vui lòng đăng nhập để bắt đầu mua sắm!`
        }));

        showCustomerAlert(
            alertId,
            "Đăng ký thành công! Đang chuyển sang màn hình Đăng nhập...",
            "success"
        );

        if (btn) {
            btn.disabled = true;
            btn.innerHTML = `<span class="auth-spinner"></span> Đang chuyển sang Đăng nhập...`;
        }

        // Tự động chuyển tab hoặc chuyển trang sau 1s
        setTimeout(() => {
            if (typeof window.ShoesCustomerAuth.switchTab === "function") {
                window.ShoesCustomerAuth.switchTab("login", phone || email);
            } else {
                window.location.href = `./customer_login.html?registered=1&identity=${encodeURIComponent(phone || email)}`;
            }
        }, 1100);

        return true;
    }

    /**
     * XỬ LÝ ĐĂNG NHẬP KHÁCH HÀNG (Hỗ trợ Email hoặc Số điện thoại)
     */
    function handleCustomerLogin(identity, password, rememberMe) {
        const alertId = "loginAlert";
        const btn = document.getElementById("btnCustLogin");

        identity = (identity || "").trim();
        password = password || "";

        if (!identity) {
            showCustomerAlert(alertId, "Vui lòng nhập Email hoặc Số điện thoại mua hàng.", "error");
            return false;
        }

        if (!password) {
            showCustomerAlert(alertId, "Vui lòng nhập mật khẩu tài khoản.", "error");
            return false;
        }

        const accounts = getCustomerAccounts();
        const normalized = identity.toLowerCase();

        // Tìm kiếm theo email HOẶC số điện thoại
        const customer = accounts.find(
            acc => (acc.email && acc.email.toLowerCase() === normalized) ||
                   (acc.phone && acc.phone === identity)
        );

        if (!customer) {
            showCustomerAlert(
                alertId,
                `Không tìm thấy tài khoản với "${identity}". <a href="javascript:void(0)" onclick="window.ShoesCustomerAuth.switchTab('register')" style="font-weight:700; color:#b91c1c; text-decoration:underline;">Tạo tài khoản mới ngay</a>.`,
                "error"
            );
            return false;
        }

        if (customer.password !== password) {
            showCustomerAlert(alertId, "Mật khẩu không chính xác! Hãy kiểm tra lại hoặc nhấn 'Quên mật khẩu?'.", "error");
            return false;
        }

        // Tạo phiên làm việc khách hàng
        const session = {
            id: customer.id,
            name: customer.name,
            phone: customer.phone,
            email: customer.email,
            address: customer.address || "",
            tier: customer.tier || "Đồng",
            points: customer.points || 0,
            ordersCount: customer.ordersCount || 0,
            spent: customer.spent || 0,
            role: "customer",
            avatar: customer.avatar,
            loggedInAt: Date.now()
        };

        sessionStorage.setItem(CUSTOMER_SESSION_KEY, JSON.stringify(session));
        sessionStorage.setItem(COMPAT_SESSION_KEY, JSON.stringify(session));

        if (rememberMe) {
            localStorage.setItem(REMEMBER_KEY, identity);
            localStorage.setItem(CUSTOMER_SESSION_KEY, JSON.stringify(session));
        } else {
            localStorage.removeItem(REMEMBER_KEY);
            localStorage.removeItem(CUSTOMER_SESSION_KEY);
        }

        showCustomerAlert(
            alertId,
            `Xin chào <strong>${customer.name}</strong> (${customer.tier})! Đăng nhập thành công, đang chuẩn bị giỏ hàng...`,
            "success"
        );

        if (btn) {
            btn.disabled = true;
            btn.innerHTML = `<span class="auth-spinner"></span> Đang đăng nhập...`;
        }

        // Kiểm tra redirect URL (ví dụ giỏ hàng, thanh toán, hoặc trang mua hàng)
        const params = new URLSearchParams(window.location.search);
        const redirect = params.get("redirect");

        setTimeout(() => {
            if (redirect === "checkout") {
                window.location.href = "../legacy/anhtuan/checkout.html";
            } else if (redirect === "cart") {
                window.location.href = "../legacy/anhtuan/cart.html";
            } else if (redirect === "shop") {
                window.location.href = "./customer_shop.html";
            } else {
                // Hiển thị khung thông tin cá nhân đã đăng nhập
                renderLoggedInState(session);
            }
        }, 800);

        return true;
    }

    /**
     * Đăng xuất tài khoản khách hàng
     */
    function logoutCustomer() {
        sessionStorage.removeItem(CUSTOMER_SESSION_KEY);
        sessionStorage.removeItem(COMPAT_SESSION_KEY);
        localStorage.removeItem(CUSTOMER_SESSION_KEY);
        window.location.reload();
    }

    /**
     * Hiển thị trạng thái đã đăng nhập
     */
    function renderLoggedInState(customer) {
        const authCard = document.querySelector(".customer-auth-wrapper");
        const formCol = document.querySelector(".auth-form-column");
        const loggedCard = document.getElementById("custLoggedCard");

        if (loggedCard && formCol) {
            const loginSection = document.getElementById("loginSection");
            const registerSection = document.getElementById("registerSection");
            const navTabs = document.getElementById("authNavTabs");

            if (loginSection) loginSection.style.display = "none";
            if (registerSection) registerSection.style.display = "none";
            if (navTabs) navTabs.style.display = "none";

            document.getElementById("loggedName").textContent = customer.name;
            document.getElementById("loggedTier").textContent = `Hạng ${customer.tier} • ${customer.id}`;
            document.getElementById("loggedPoints").textContent = (customer.points || 0).toLocaleString("vi-VN") + " đ";
            document.getElementById("loggedOrders").textContent = (customer.ordersCount || 0) + " đơn";
            document.getElementById("loggedPhone").textContent = customer.phone || "---";
            document.getElementById("loggedAddress").textContent = customer.address || "Chưa có địa chỉ";

            loggedCard.classList.add("show");
        }
    }

    /**
     * Chuyển đổi giữa 2 tab Đăng nhập và Đăng ký
     */
    function switchTab(tab, prefillIdentity) {
        const loginTabBtn = document.getElementById("tabLoginBtn");
        const registerTabBtn = document.getElementById("tabRegisterBtn");
        const loginSection = document.getElementById("loginSection");
        const registerSection = document.getElementById("registerSection");

        if (!loginSection || !registerSection) return;

        if (tab === "login") {
            loginSection.style.display = "block";
            registerSection.style.display = "none";
            if (loginTabBtn) loginTabBtn.classList.add("active");
            if (registerTabBtn) registerTabBtn.classList.remove("active");

            if (prefillIdentity) {
                const input = document.getElementById("loginIdentity");
                const passInput = document.getElementById("loginPassword");
                if (input) input.value = prefillIdentity;
                if (passInput) passInput.focus();
            }
        } else {
            loginSection.style.display = "none";
            registerSection.style.display = "block";
            if (loginTabBtn) loginTabBtn.classList.remove("active");
            if (registerTabBtn) registerTabBtn.classList.add("active");

            if (prefillIdentity) {
                const emailInput = document.getElementById("custEmail");
                if (emailInput && prefillIdentity.includes("@")) emailInput.value = prefillIdentity;
            }
        }
    }

    /**
     * Khởi tạo giao diện khi DOM sẵn sàng
     */
    document.addEventListener("DOMContentLoaded", () => {
        // Đảm bảo dữ liệu demo có sẵn
        getCustomerAccounts();

        // 1. Kiểm tra trạng thái đã đăng nhập
        const currentCust = getCurrentCustomer();
        if (currentCust) {
            renderLoggedInState(currentCust);
        }

        // 2. Gắn sự kiện nút mắt xem mật khẩu
        document.querySelectorAll(".toggle-eye").forEach(btn => {
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

        // 3. Đo độ mạnh mật khẩu khi đăng ký
        const custPass = document.getElementById("custPassword");
        const meterFill = document.getElementById("custMeterFill");
        const meterLabel = document.getElementById("custMeterLabel");
        if (custPass && meterFill && meterLabel) {
            custPass.addEventListener("input", () => {
                const evalResult = calcPasswordStrength(custPass.value);
                meterFill.style.width = evalResult.width;
                meterFill.style.background = evalResult.color;
                meterLabel.textContent = `Độ mạnh: ${evalResult.label}`;
                meterLabel.style.color = evalResult.color;
            });
        }

        // 4. Bắt sự kiện Form Đăng ký
        const formRegister = document.getElementById("customerRegisterForm");
        if (formRegister) {
            formRegister.addEventListener("submit", (e) => {
                e.preventDefault();
                handleCustomerRegister({
                    name: document.getElementById("custName")?.value,
                    phone: document.getElementById("custPhone")?.value,
                    email: document.getElementById("custEmail")?.value,
                    address: document.getElementById("custAddress")?.value,
                    password: document.getElementById("custPassword")?.value,
                    confirmPassword: document.getElementById("custConfirmPassword")?.value,
                    agreeTerms: document.getElementById("custAgreeTerms")?.checked
                });
            });
        }

        // 5. Bắt sự kiện Form Đăng nhập
        const formLogin = document.getElementById("customerLoginForm");
        if (formLogin) {
            formLogin.addEventListener("submit", (e) => {
                e.preventDefault();
                handleCustomerLogin(
                    document.getElementById("loginIdentity")?.value,
                    document.getElementById("loginPassword")?.value,
                    document.getElementById("custRememberMe")?.checked
                );
            });
        }

        // 6. Xử lý thông báo Flash từ phiên trước
        let flash = null;
        try {
            flash = JSON.parse(sessionStorage.getItem(FLASH_KEY) || "null");
        } catch {
            flash = null;
        }

        const urlParams = new URLSearchParams(window.location.search);
        const urlIdentity = urlParams.get("identity") || urlParams.get("email");
        const urlRegistered = urlParams.get("registered") === "1";
        const urlTab = urlParams.get("tab");

        if (urlTab === "register") {
            switchTab("register");
        }

        if (flash && flash.message) {
            showCustomerAlert("loginAlert", flash.message, flash.type || "success");
            if (flash.identity) {
                const idInput = document.getElementById("loginIdentity");
                if (idInput) idInput.value = flash.identity;
                document.getElementById("loginPassword")?.focus();
            }
            sessionStorage.removeItem(FLASH_KEY);
        } else if (urlRegistered && urlIdentity) {
            showCustomerAlert(
                "loginAlert",
                `🎉 Tạo tài khoản thành công cho <strong>${urlIdentity}</strong>! Nhập mật khẩu để bắt đầu mua sắm.`,
                "success"
            );
            const idInput = document.getElementById("loginIdentity");
            if (idInput) idInput.value = urlIdentity;
            document.getElementById("loginPassword")?.focus();
        } else if (urlIdentity) {
            const idInput = document.getElementById("loginIdentity");
            if (idInput) idInput.value = urlIdentity;
        } else {
            // Tự điền tài khoản đã ghi nhớ
            const remembered = localStorage.getItem(REMEMBER_KEY);
            if (remembered) {
                const idInput = document.getElementById("loginIdentity");
                const remInput = document.getElementById("custRememberMe");
                if (idInput) idInput.value = remembered;
                if (remInput) remInput.checked = true;
            }
        }

        // 7. Gắn sự kiện chọn tài khoản mẫu nhanh
        document.querySelectorAll(".demo-chip").forEach(chip => {
            chip.addEventListener("click", function () {
                const ident = this.getAttribute("data-identity");
                const pass = this.getAttribute("data-password");
                const idInput = document.getElementById("loginIdentity");
                const passInput = document.getElementById("loginPassword");
                if (idInput) idInput.value = ident;
                if (passInput) passInput.value = pass;
                showCustomerAlert(
                    "loginAlert",
                    `Đã điền tài khoản khách hàng mẫu: <strong>${this.innerText.trim()}</strong>. Bấm "Đăng nhập mua hàng" để tiếp tục!`,
                    "info"
                );
            });
        });

        // 8. Nút đăng xuất
        const logoutBtn = document.getElementById("btnCustLogout");
        if (logoutBtn) {
            logoutBtn.addEventListener("click", () => {
                if (confirm("Bạn có chắc chắn muốn đăng xuất tài khoản mua hàng không?")) {
                    logoutCustomer();
                }
            });
        }
    });

    // Xuất ra global scope
    window.ShoesCustomerAuth = {
        getCustomerAccounts,
        getCurrentCustomer,
        handleCustomerRegister,
        handleCustomerLogin,
        logoutCustomer,
        switchTab,
        DEMO_CUSTOMERS
    };
})();
