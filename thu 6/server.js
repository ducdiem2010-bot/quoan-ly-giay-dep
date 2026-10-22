/**
 * Shoes Store - Backend Server (Node.js)
 * Cung cấp REST API cho quản lý sản phẩm, tài khoản admin, khách hàng
 * Lắng nghe trên 0.0.0.0 để mọi máy trong mạng LAN đều truy cập được
 * Sử dụng thư viện chuẩn Node.js (Zero-dependency, không cần npm install)
 */

const http = require("http");
const fs = require("fs");
const path = require("path");
const url = require("url");
const os = require("os");

const PORT = process.env.PORT || 3000;
const DATA_FILE      = path.join(__dirname, "products.json");
const ADMINS_FILE    = path.join(__dirname, "admins.json");
const CUSTOMERS_FILE = path.join(__dirname, "customers.json");
const ORDERS_FILE    = path.join(__dirname, "orders.json");

// ==========================================
// TIỆN ÍCH ĐỌC / GHI FILE JSON
// ==========================================

function readJSON(filePath, defaultValue) {
    try {
        if (!fs.existsSync(filePath)) {
            fs.writeFileSync(filePath, JSON.stringify(defaultValue, null, 2), "utf8");
            return defaultValue;
        }
        const content = fs.readFileSync(filePath, "utf8");
        return JSON.parse(content || JSON.stringify(defaultValue));
    } catch (err) {
        console.error("Lỗi đọc file:", filePath, err.message);
        return defaultValue;
    }
}

function writeJSON(filePath, data) {
    try {
        fs.writeFileSync(filePath, JSON.stringify(data, null, 2), "utf8");
        return true;
    } catch (err) {
        console.error("Lỗi ghi file:", filePath, err.message);
        return false;
    }
}

// Đọc sản phẩm
function readProducts()         { return readJSON(DATA_FILE, []); }
function writeProducts(data)    { return writeJSON(DATA_FILE, data); }

// Đọc admins — khởi tạo tài khoản demo mặc định nếu chưa có
function readAdmins() {
    const DEFAULT_ADMIN = {
        id: "ADM_DEMO",
        name: "Admin Quản Trị",
        email: "admin@gmail.com",
        phone: "0901234567",
        password: "admin123",
        role: "admin",
        createdAt: 1704067200000
    };
    let admins = readJSON(ADMINS_FILE, [DEFAULT_ADMIN]);
    if (!Array.isArray(admins)) admins = [DEFAULT_ADMIN];
    const hasDemo = admins.some(a => (a.email || "").toLowerCase() === "admin@gmail.com");
    if (!hasDemo) { admins.unshift(DEFAULT_ADMIN); writeJSON(ADMINS_FILE, admins); }
    return admins;
}
function writeAdmins(data)      { return writeJSON(ADMINS_FILE, data); }

// Đọc khách hàng — khởi tạo danh sách mẫu nếu chưa có
function readCustomers() {
    const DEMO = [
        { id:"KH1001", name:"Nguyễn Văn An",   phone:"0901234567", email:"an.nguyen@gmail.com",  address:"123 Lê Lợi, Q1, TP.HCM",                password:"123456", tier:"Kim cương", points:1850, ordersCount:8, spent:18500000, status:"active", avatar:"https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=200&q=80", joinDate:"10/01/2026", notes:"Khách VIP thân thiết", createdAt:1704067200000 },
        { id:"KH1002", name:"Trần Minh Đức",   phone:"0987654321", email:"duc.tran@gmail.com",   address:"456 Nguyễn Thị Minh Khai, Q3, TP.HCM",    password:"123456", tier:"Vàng",      points:980,  ordersCount:5, spent:9800000,  status:"active", avatar:"https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=200&q=80", joinDate:"15/01/2026", notes:"Đam mê giày Adidas Ultraboost", createdAt:1704240000000 },
        { id:"KH1003", name:"Lê Hoàng Nam",    phone:"0912345678", email:"nam.le@gmail.com",     address:"789 Hoàng Diệu, Q4, TP.HCM",              password:"123456", tier:"Bạc",      points:465,  ordersCount:3, spent:4650000,  status:"active", avatar:"https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=200&q=80", joinDate:"20/02/2026", notes:"Thích Chunky Sneaker Puma",  createdAt:1740009600000 }
    ];
    let customers = readJSON(CUSTOMERS_FILE, DEMO);
    if (!Array.isArray(customers) || customers.length === 0) {
        customers = DEMO;
        writeJSON(CUSTOMERS_FILE, customers);
    }
    return customers;
}
function writeCustomers(data)   { return writeJSON(CUSTOMERS_FILE, data); }

// Đọc đơn hàng
function readOrders()           { return readJSON(ORDERS_FILE, []); }
function writeOrders(data)      { return writeJSON(ORDERS_FILE, data); }

// ==========================================
// MIME TYPES
// ==========================================
const MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css":  "text/css; charset=utf-8",
    ".js":   "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png":  "image/png",
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif":  "image/gif",
    ".svg":  "image/svg+xml",
    ".ico":  "image/x-icon"
};

// ==========================================
// ĐỌC BODY HTTP REQUEST
// ==========================================
function parseRequestBody(req) {
    return new Promise((resolve, reject) => {
        let body = "";
        req.on("data", chunk => {
            body += chunk.toString();
            if (body.length > 20 * 1024 * 1024) reject(new Error("Payload quá lớn"));
        });
        req.on("end", () => {
            if (!body) return resolve({});
            try { resolve(JSON.parse(body)); }
            catch { resolve({ raw: body }); }
        });
        req.on("error", reject);
    });
}

// ==========================================
// GỬI PHẢN HỒI JSON
// ==========================================
function sendJSON(res, statusCode, data) {
    res.writeHead(statusCode, {
        "Content-Type": "application/json; charset=utf-8",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization"
    });
    res.end(JSON.stringify(data));
}

// ==========================================
// HTTP SERVER
// ==========================================
const server = http.createServer(async (req, res) => {
    const parsedUrl = url.parse(req.url, true);
    const pathname  = parsedUrl.pathname;
    const method    = req.method.toUpperCase();

    // CORS pre-flight
    if (method === "OPTIONS") {
        res.writeHead(204, {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        });
        return res.end();
    }

    // ==========================================
    // API: PRODUCTS
    // ==========================================

    // GET /api/products
    if (pathname === "/api/products" && method === "GET") {
        const products = readProducts();
        return sendJSON(res, 200, { success: true, total: products.length, data: products });
    }

    // GET /api/products/:id
    if (pathname.startsWith("/api/products/") && method === "GET") {
        const id = pathname.replace("/api/products/", "").trim();
        const found = readProducts().find(p => String(p.id) === id);
        if (!found) return sendJSON(res, 404, { success: false, message: "Không tìm thấy sản phẩm" });
        return sendJSON(res, 200, { success: true, data: found });
    }

    // POST /api/products
    if (pathname === "/api/products" && method === "POST") {
        try {
            const body = await parseRequestBody(req);
            if (!body.name || !body.brand || !body.category)
                return sendJSON(res, 400, { success: false, message: "Vui lòng nhập đầy đủ tên, thương hiệu và danh mục." });

            const products = readProducts();
            let variants = Array.isArray(body.variants) ? body.variants : [];
            let totalStock = Number(body.stock) || 0;
            if (variants.length > 0) totalStock = variants.reduce((s, v) => s + (Number(v.stock) || 0), 0);

            const newProduct = {
                id: body.id || ("SP" + Date.now().toString().slice(-6)),
                name: String(body.name).trim(), brand: String(body.brand).trim(),
                category: String(body.category).trim(), gender: String(body.gender || "Unisex").trim(),
                price: Number(body.price) || 0, stock: totalStock,
                image: String(body.image || "").trim(), description: String(body.description || "").trim(),
                status: body.status === "hidden" ? "hidden" : "active",
                createdAt: Date.now(), updatedAt: Date.now(),
                variants: variants.map((v, i) => ({
                    id: v.id || `V-${Date.now().toString().slice(-4)}-${i+1}`,
                    color: String(v.color || "Tiêu chuẩn").trim(),
                    size:  String(v.size  || "Free").trim(),
                    stock: Math.max(0, Number(v.stock) || 0),
                    price: Number(v.price) || Number(body.price) || 0,
                    sku:   String(v.sku || "").trim()
                }))
            };

            const idx = products.findIndex(p => p.id === newProduct.id);
            if (idx !== -1) products[idx] = newProduct; else products.unshift(newProduct);
            writeProducts(products);
            return sendJSON(res, 201, { success: true, message: "Lưu sản phẩm thành công!", data: newProduct });
        } catch (err) {
            return sendJSON(res, 500, { success: false, message: err.message });
        }
    }

    // PUT /api/products/:id
    if (pathname.startsWith("/api/products/") && method === "PUT") {
        try {
            const id = pathname.replace("/api/products/", "").trim();
            const body = await parseRequestBody(req);
            const products = readProducts();
            const index = products.findIndex(p => String(p.id) === id);
            if (index === -1) return sendJSON(res, 404, { success: false, message: "Không tìm thấy sản phẩm" });

            let variants = Array.isArray(body.variants) ? body.variants : products[index].variants || [];
            let totalStock = Number(body.stock);
            if (variants.length > 0) totalStock = variants.reduce((s, v) => s + (Number(v.stock) || 0), 0);

            products[index] = { ...products[index], ...body, id, stock: totalStock, variants, updatedAt: Date.now() };
            writeProducts(products);
            return sendJSON(res, 200, { success: true, message: "Cập nhật sản phẩm thành công!", data: products[index] });
        } catch (err) {
            return sendJSON(res, 500, { success: false, message: err.message });
        }
    }

    // DELETE /api/products/:id
    if (pathname.startsWith("/api/products/") && method === "DELETE") {
        const id = pathname.replace("/api/products/", "").trim();
        const products = readProducts();
        const filtered = products.filter(p => String(p.id) !== id);
        if (filtered.length === products.length)
            return sendJSON(res, 404, { success: false, message: "Không tìm thấy sản phẩm để xóa" });
        writeProducts(filtered);
        return sendJSON(res, 200, { success: true, message: "Đã xóa sản phẩm thành công" });
    }

    // ==========================================
    // API: ADMIN ACCOUNTS
    // ==========================================

    // GET /api/admins — danh sách tài khoản admin (ẩn password)
    if (pathname === "/api/admins" && method === "GET") {
        const admins = readAdmins().map(({ password, ...rest }) => rest);
        return sendJSON(res, 200, { success: true, data: admins });
    }

    // POST /api/admins/login — đăng nhập admin
    if (pathname === "/api/admins/login" && method === "POST") {
        try {
            const { email, password } = await parseRequestBody(req);
            if (!email || !password)
                return sendJSON(res, 400, { success: false, message: "Thiếu email hoặc mật khẩu" });
            const admins = readAdmins();
            const account = admins.find(a => (a.email || "").toLowerCase() === email.trim().toLowerCase());
            if (!account)
                return sendJSON(res, 401, { success: false, message: "Email chưa được đăng ký trong hệ thống" });
            if (account.password !== password)
                return sendJSON(res, 401, { success: false, message: "Mật khẩu không chính xác" });
            const { password: _pw, ...safeAccount } = account;
            return sendJSON(res, 200, { success: true, message: "Đăng nhập thành công", data: safeAccount });
        } catch (err) {
            return sendJSON(res, 500, { success: false, message: err.message });
        }
    }

    // POST /api/admins/register — đăng ký admin mới
    if (pathname === "/api/admins/register" && method === "POST") {
        try {
            const body = await parseRequestBody(req);
            const { name, email, phone, password } = body;
            if (!name || !email || !password)
                return sendJSON(res, 400, { success: false, message: "Thiếu thông tin bắt buộc" });
            const admins = readAdmins();
            const exists = admins.find(a => (a.email || "").toLowerCase() === email.trim().toLowerCase());
            if (exists)
                return sendJSON(res, 409, { success: false, message: "Email này đã được đăng ký" });
            const newAdmin = {
                id: "ADM_" + Date.now(),
                name: name.trim(), email: email.trim().toLowerCase(),
                phone: (phone || "").trim(), password,
                role: "admin", createdAt: Date.now()
            };
            admins.push(newAdmin);
            writeAdmins(admins);
            const { password: _pw, ...safe } = newAdmin;
            return sendJSON(res, 201, { success: true, message: "Đăng ký tài khoản admin thành công", data: safe });
        } catch (err) {
            return sendJSON(res, 500, { success: false, message: err.message });
        }
    }

    // ==========================================
    // API: CUSTOMERS
    // ==========================================

    // GET /api/customers — danh sách khách hàng (ẩn password)
    if (pathname === "/api/customers" && method === "GET") {
        const customers = readCustomers().map(({ password, ...rest }) => rest);
        return sendJSON(res, 200, { success: true, total: customers.length, data: customers });
    }

    // POST /api/customers/login — đăng nhập khách hàng
    if (pathname === "/api/customers/login" && method === "POST") {
        try {
            const { identity, password } = await parseRequestBody(req);
            if (!identity || !password)
                return sendJSON(res, 400, { success: false, message: "Thiếu thông tin đăng nhập" });
            const customers = readCustomers();
            const normalized = identity.trim().toLowerCase();
            const customer = customers.find(c =>
                (c.email && c.email.toLowerCase() === normalized) ||
                (c.phone && c.phone === identity.trim())
            );
            if (!customer)
                return sendJSON(res, 401, { success: false, message: `Không tìm thấy tài khoản với "${identity}"` });
            if (customer.password !== password)
                return sendJSON(res, 401, { success: false, message: "Mật khẩu không chính xác" });
            if (customer.status === "blocked")
                return sendJSON(res, 403, { success: false, message: "Tài khoản đã bị khóa. Vui lòng liên hệ hỗ trợ." });
            const { password: _pw, ...safe } = customer;
            return sendJSON(res, 200, { success: true, message: "Đăng nhập thành công", data: safe });
        } catch (err) {
            return sendJSON(res, 500, { success: false, message: err.message });
        }
    }

    // POST /api/customers/register — đăng ký khách hàng mới
    if (pathname === "/api/customers/register" && method === "POST") {
        try {
            const body = await parseRequestBody(req);
            const { name, phone, email, address, password } = body;
            if (!name || !phone || !password)
                return sendJSON(res, 400, { success: false, message: "Thiếu thông tin bắt buộc" });
            const customers = readCustomers();
            const dup = customers.find(c =>
                (email && c.email && c.email.toLowerCase() === email.trim().toLowerCase()) ||
                (c.phone === phone.trim())
            );
            if (dup)
                return sendJSON(res, 409, { success: false, message: `${dup.phone === phone.trim() ? "Số điện thoại" : "Email"} này đã được đăng ký` });

            const newCustomer = {
                id: "KH" + Math.floor(1000 + Math.random() * 9000),
                name: name.trim(), phone: phone.trim(),
                email: (email || "").trim().toLowerCase(),
                address: (address || "").trim(), password,
                tier: "Đồng", points: 100,
                ordersCount: 0, spent: 0, status: "active",
                avatar: "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=200&q=80",
                joinDate: new Date().toLocaleDateString("vi-VN"),
                notes: "Khách hàng đăng ký trực tuyến",
                createdAt: Date.now()
            };
            customers.unshift(newCustomer);
            writeCustomers(customers);
            const { password: _pw, ...safe } = newCustomer;
            return sendJSON(res, 201, { success: true, message: "Đăng ký tài khoản thành công! Tặng 100 điểm chào mừng.", data: safe });
        } catch (err) {
            return sendJSON(res, 500, { success: false, message: err.message });
        }
    }

    // PUT /api/customers/:id — cập nhật thông tin khách hàng
    if (pathname.startsWith("/api/customers/") && method === "PUT") {
        try {
            const id = pathname.replace("/api/customers/", "").trim();
            const body = await parseRequestBody(req);
            const customers = readCustomers();
            const index = customers.findIndex(c => String(c.id) === id);
            if (index === -1) return sendJSON(res, 404, { success: false, message: "Không tìm thấy khách hàng" });
            customers[index] = { ...customers[index], ...body, id, updatedAt: Date.now() };
            writeCustomers(customers);
            const { password: _pw, ...safe } = customers[index];
            return sendJSON(res, 200, { success: true, message: "Cập nhật thành công", data: safe });
        } catch (err) {
            return sendJSON(res, 500, { success: false, message: err.message });
        }
    }

    // ==========================================
    // API: ORDERS
    // ==========================================

    // GET /api/orders
    if (pathname === "/api/orders" && method === "GET") {
        const orders = readOrders();
        return sendJSON(res, 200, { success: true, total: orders.length, data: orders });
    }

    // POST /api/orders — tạo đơn hàng mới
    if (pathname === "/api/orders" && method === "POST") {
        try {
            const body = await parseRequestBody(req);
            const orders = readOrders();
            const newOrder = {
                id: "DH" + Date.now().toString().slice(-8),
                ...body,
                createdAt: Date.now(),
                updatedAt: Date.now()
            };
            orders.unshift(newOrder);
            writeOrders(orders);
            return sendJSON(res, 201, { success: true, message: "Tạo đơn hàng thành công", data: newOrder });
        } catch (err) {
            return sendJSON(res, 500, { success: false, message: err.message });
        }
    }

    // PUT /api/orders/:id
    if (pathname.startsWith("/api/orders/") && method === "PUT") {
        try {
            const id = pathname.replace("/api/orders/", "").trim();
            const body = await parseRequestBody(req);
            const orders = readOrders();
            const index = orders.findIndex(o => String(o.id) === id);
            if (index === -1) return sendJSON(res, 404, { success: false, message: "Không tìm thấy đơn hàng" });
            orders[index] = { ...orders[index], ...body, id, updatedAt: Date.now() };
            writeOrders(orders);
            return sendJSON(res, 200, { success: true, message: "Cập nhật đơn hàng thành công", data: orders[index] });
        } catch (err) {
            return sendJSON(res, 500, { success: false, message: err.message });
        }
    }

    // ==========================================
    // API: UPLOAD ẢNH (Base64)
    // ==========================================
    if (pathname === "/api/upload" && method === "POST") {
        try {
            const body = await parseRequestBody(req);
            if (!body.image) return sendJSON(res, 400, { success: false, message: "Thiếu dữ liệu ảnh" });
            return sendJSON(res, 200, { success: true, imageUrl: body.image, message: "Tải ảnh thành công" });
        } catch (err) {
            return sendJSON(res, 500, { success: false, message: err.message });
        }
    }

    // ==========================================
    // PHỤC VỤ FILE TĨNH (HTML, CSS, JS)
    // ==========================================
    let filePath = path.join(__dirname, pathname === "/" ? "customer_shop.html" : pathname);

    if (!filePath.startsWith(__dirname)) {
        res.writeHead(403); return res.end("Forbidden");
    }

    fs.stat(filePath, (err, stats) => {
        if (err || !stats.isFile()) {
            res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
            return res.end("404 Not Found: " + pathname);
        }
        const ext = path.extname(filePath).toLowerCase();
        const contentType = MIME_TYPES[ext] || "application/octet-stream";
        res.writeHead(200, { "Content-Type": contentType });
        fs.createReadStream(filePath).pipe(res);
    });
});

// ==========================================
// LẤY ĐỊA CHỈ IP LAN ĐỂ IN RA MÀN HÌNH
// ==========================================
function getLanIP() {
    const interfaces = os.networkInterfaces();
    for (const name of Object.keys(interfaces)) {
        for (const iface of interfaces[name]) {
            if (iface.family === "IPv4" && !iface.internal) {
                return iface.address;
            }
        }
    }
    return "localhost";
}

// Lắng nghe trên 0.0.0.0 → mọi máy trong mạng LAN đều kết nối được
server.listen(PORT, "0.0.0.0", () => {
    const lanIP = getLanIP();
    console.log(`=======================================================`);
    console.log(`🚀 Shoes Store Server đang chạy!`);
    console.log(``);
    console.log(`📦 TRANG KHÁCH HÀNG:`);
    console.log(`   Máy này    : http://localhost:${PORT}/customer_shop.html`);
    console.log(`   Máy khác   : http://${lanIP}:${PORT}/customer_shop.html`);
    console.log(``);
    console.log(`🛠️  TRANG ADMIN:`);
    console.log(`   Máy này    : http://localhost:${PORT}/admin_login.html`);
    console.log(`   Máy khác   : http://${lanIP}:${PORT}/admin_login.html`);
    console.log(``);
    console.log(`🔌 REST API   : http://${lanIP}:${PORT}/api/products`);
    console.log(`=======================================================`);
    console.log(`💡 Chia sẻ địa chỉ IP trên cho máy khác trong cùng mạng WiFi/LAN`);
});
