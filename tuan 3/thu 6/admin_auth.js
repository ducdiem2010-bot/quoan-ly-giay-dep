
const ACCOUNT_KEY = "shoesAdminAccounts";
const SESSION_KEY = "shoesAdminSession";

// Đọc danh sách tài khoản
function getAccounts() {
    try {
        const data = JSON.parse(localStorage.getItem(ACCOUNT_KEY) || "[]");
        return Array.isArray(data) ? data : [];
    } catch {
        return [];
    }
}

// Đăng ký tài khoản quản trị
function registerAdmin(name, email, password, confirmPassword) {
    name = name.trim();
    email = email.trim().toLowerCase();

    if (!name || !email || !password || !confirmPassword) {
        alert("Vui lòng nhập đầy đủ thông tin!");
        return;
    }

    if (password !== confirmPassword) {
        alert("Mật khẩu xác nhận không khớp!");
        return;
    }

    const accounts = getAccounts();

    if (accounts.some(account =>
        account.email.toLowerCase() === email
    )) {
        alert("Email này đã được đăng ký!");
        return;
    }

    accounts.push({
        id: Date.now(),
        name,
        email,
        password,
        role: "admin"
    });

    localStorage.setItem(ACCOUNT_KEY, JSON.stringify(accounts));

    alert("Đăng ký thành công! Hãy đăng nhập.");
    window.location.href = "./admin_login.html";
}

// Đăng nhập quản trị
function loginAdmin(email, password) {
    email = email.trim().toLowerCase();

    const accounts = getAccounts();

    const account = accounts.find(item =>
        item.email.toLowerCase() === email &&
        item.password === password &&
        item.role === "admin"
    );

    if (!account) {
        alert("Email hoặc mật khẩu không đúng. Hãy kiểm tra lại.");
        return;
    }

    // Lưu phiên đăng nhập
    const session = {
        id: account.id,
        name: account.name,
        email: account.email,
        role: "admin",
        loggedInAt: Date.now()
    };

    sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));

    // Kiểm tra đã lưu thành công chưa
    const savedSession = sessionStorage.getItem(SESSION_KEY);

    if (!savedSession) {
        alert("Không thể lưu phiên đăng nhập. Hãy thử lại.");
        return;
    }

    window.location.href = "./admin_base.html";
}

// Kiểm tra phiên đăng nhập ở trang admin
function requireAdminLogin() {
    let session = null;

    try {
        session = JSON.parse(
            sessionStorage.getItem(SESSION_KEY) || "null"
        );
    } catch {
        session = null;
    }

    if (!session || !session.id || session.role !== "admin") {
        window.location.replace("./admin_login.html");
        return false;
    }

    return true;
}

// Đăng xuất
function logoutAdmin() {
    sessionStorage.removeItem(SESSION_KEY);
    window.location.replace("./admin_login.html");
}
