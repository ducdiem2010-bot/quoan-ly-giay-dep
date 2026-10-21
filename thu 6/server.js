/**
 * Shoes Store - Backend Server (Node.js)
 * Cung cấp REST API cho quản lý sản phẩm, biến thể và ảnh đại diện
 * Sử dụng thư viện chuẩn Node.js (Zero-dependency, không cần npm install)
 */

const http = require("http");
const fs = require("fs");
const path = require("path");
const url = require("url");

const PORT = process.env.PORT || 3000;
const DATA_FILE = path.join(__dirname, "products.json");

// Đọc dữ liệu từ products.json
function readProducts() {
    try {
        if (!fs.existsSync(DATA_FILE)) {
            fs.writeFileSync(DATA_FILE, JSON.stringify([], null, 2), "utf8");
            return [];
        }
        const content = fs.readFileSync(DATA_FILE, "utf8");
        return JSON.parse(content || "[]");
    } catch (err) {
        console.error("Lỗi đọc file products.json:", err.message);
        return [];
    }
}

// Lưu dữ liệu vào products.json
function writeProducts(data) {
    try {
        fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2), "utf8");
        return true;
    } catch (err) {
        console.error("Lỗi ghi file products.json:", err.message);
        return false;
    }
}

// Bảng MIME Type phục vụ file tĩnh
const MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon"
};

// Đọc body của HTTP Request (JSON)
function parseRequestBody(req) {
    return new Promise((resolve, reject) => {
        let body = "";
        req.on("data", chunk => {
            body += chunk.toString();
            if (body.length > 20 * 1024 * 1024) { // Max 20MB (cho ảnh base64)
                reject(new Error("Dung lượng payload quá lớn"));
            }
        });
        req.on("end", () => {
            if (!body) return resolve({});
            try {
                resolve(JSON.parse(body));
            } catch (err) {
                resolve({ raw: body });
            }
        });
        req.on("error", reject);
    });
}

// Helper gửi JSON phản hồi
function sendJSON(res, statusCode, data) {
    res.writeHead(statusCode, {
        "Content-Type": "application/json; charset=utf-8",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization"
    });
    res.end(JSON.stringify(data));
}

// Khởi tạo HTTP Server
const server = http.createServer(async (req, res) => {
    const parsedUrl = url.parse(req.url, true);
    const pathname = parsedUrl.pathname;
    const method = req.method.toUpperCase();

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
    // REST API ENDPOINTS
    // ==========================================

    // 1. GET /api/products - Lấy danh sách sản phẩm (kèm biến thể và ảnh đại diện)
    if (pathname === "/api/products" && method === "GET") {
        const products = readProducts();
        return sendJSON(res, 200, {
            success: true,
            total: products.length,
            data: products
        });
    }

    // 2. GET /api/products/:id - Lấy chi tiết 1 sản phẩm
    if (pathname.startsWith("/api/products/") && method === "GET") {
        const id = pathname.replace("/api/products/", "").trim();
        const products = readProducts();
        const found = products.find(p => String(p.id) === id);
        if (!found) {
            return sendJSON(res, 404, { success: false, message: "Không tìm thấy sản phẩm" });
        }
        return sendJSON(res, 200, { success: true, data: found });
    }

    // 3. POST /api/products - Thêm sản phẩm mới kèm biến thể và ảnh đại diện
    if (pathname === "/api/products" && method === "POST") {
        try {
            const body = await parseRequestBody(req);

            if (!body.name || !body.brand || !body.category) {
                return sendJSON(res, 400, {
                    success: false,
                    message: "Vui lòng nhập đầy đủ tên sản phẩm, thương hiệu và danh mục."
                });
            }

            const products = readProducts();

            // Tính toán tổng tồn kho dựa trên biến thể nếu có
            let variants = Array.isArray(body.variants) ? body.variants : [];
            let totalStock = Number(body.stock) || 0;
            if (variants.length > 0) {
                totalStock = variants.reduce((sum, v) => sum + (Number(v.stock) || 0), 0);
            }

            const newProduct = {
                id: body.id || ("SP" + (Date.now().toString().slice(-6))),
                name: String(body.name).trim(),
                brand: String(body.brand).trim(),
                category: String(body.category).trim(),
                gender: String(body.gender || "Unisex").trim(),
                price: Number(body.price) || 0,
                stock: totalStock,
                image: String(body.image || "").trim(), // Ảnh đại diện
                description: String(body.description || "").trim(),
                status: body.status === "hidden" ? "hidden" : "active",
                createdAt: Date.now(),
                updatedAt: Date.now(),
                variants: variants.map((v, index) => ({
                    id: v.id || `V-${Date.now().toString().slice(-4)}-${index + 1}`,
                    color: String(v.color || "Tiêu chuẩn").trim(),
                    size: String(v.size || "Free").trim(),
                    stock: Math.max(0, Number(v.stock) || 0),
                    price: Number(v.price) || Number(body.price) || 0,
                    sku: String(v.sku || `${newProduct?.id || 'SP'}-${v.size}`).trim()
                }))
            };

            // Kiểm tra trùng mã SP
            const existingIndex = products.findIndex(p => p.id === newProduct.id);
            if (existingIndex !== -1) {
                products[existingIndex] = newProduct;
            } else {
                products.unshift(newProduct);
            }

            writeProducts(products);

            return sendJSON(res, 201, {
                success: true,
                message: "Lưu sản phẩm, biến thể và ảnh đại diện thành công!",
                data: newProduct
            });
        } catch (err) {
            return sendJSON(res, 500, { success: false, message: err.message });
        }
    }

    // 4. PUT /api/products/:id - Cập nhật sản phẩm, biến thể và ảnh đại diện
    if (pathname.startsWith("/api/products/") && method === "PUT") {
        try {
            const id = pathname.replace("/api/products/", "").trim();
            const body = await parseRequestBody(req);
            const products = readProducts();
            const index = products.findIndex(p => String(p.id) === id);

            if (index === -1) {
                return sendJSON(res, 404, { success: false, message: "Không tìm thấy sản phẩm để cập nhật" });
            }

            let variants = Array.isArray(body.variants) ? body.variants : products[index].variants || [];
            let totalStock = Number(body.stock);
            if (variants.length > 0) {
                totalStock = variants.reduce((sum, v) => sum + (Number(v.stock) || 0), 0);
            }

            const updatedProduct = {
                ...products[index],
                ...body,
                id: id,
                stock: totalStock,
                variants: variants,
                updatedAt: Date.now()
            };

            products[index] = updatedProduct;
            writeProducts(products);

            return sendJSON(res, 200, {
                success: true,
                message: "Cập nhật sản phẩm thành công!",
                data: updatedProduct
            });
        } catch (err) {
            return sendJSON(res, 500, { success: false, message: err.message });
        }
    }

    // 5. DELETE /api/products/:id - Xóa sản phẩm
    if (pathname.startsWith("/api/products/") && method === "DELETE") {
        const id = pathname.replace("/api/products/", "").trim();
        const products = readProducts();
        const filtered = products.filter(p => String(p.id) !== id);

        if (filtered.length === products.length) {
            return sendJSON(res, 404, { success: false, message: "Không tìm thấy sản phẩm để xóa" });
        }

        writeProducts(filtered);
        return sendJSON(res, 200, { success: true, message: "Đã xóa sản phẩm thành công" });
    }

    // 6. POST /api/upload - Nhận upload ảnh đại diện (Base64)
    if (pathname === "/api/upload" && method === "POST") {
        try {
            const body = await parseRequestBody(req);
            if (!body.image) {
                return sendJSON(res, 400, { success: false, message: "Thiếu dữ liệu ảnh" });
            }
            // Lưu dữ liệu ảnh hoặc trả về data url
            return sendJSON(res, 200, {
                success: true,
                imageUrl: body.image,
                message: "Tải ảnh đại diện thành công"
            });
        } catch (err) {
            return sendJSON(res, 500, { success: false, message: err.message });
        }
    }

    // ==========================================
    // PHỤC VỤ STATIC FILES (HTML, CSS, JS)
    // ==========================================
    let filePath = path.join(__dirname, pathname === "/" ? "admin_products.html" : pathname);

    // Chuẩn hóa bảo mật tránh directory traversal
    if (!filePath.startsWith(__dirname)) {
        res.writeHead(403);
        return res.end("Forbidden");
    }

    fs.stat(filePath, (err, stats) => {
        if (err || !stats.isFile()) {
            res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
            return res.end("404 Not Found: " + pathname);
        }

        const ext = path.extname(filePath).toLowerCase();
        const contentType = MIME_TYPES[ext] || "application/octet-stream";

        res.writeHead(200, { "Content-Type": contentType });
        const stream = fs.createReadStream(filePath);
        stream.pipe(res);
    });
});

server.listen(PORT, () => {
    console.log(`=======================================================`);
    console.log(`🚀 Shoes Store Admin Server đang chạy tại:`);
    console.log(`👉 http://localhost:${PORT}/admin_products.html`);
    console.log(`👉 REST API: http://localhost:${PORT}/api/products`);
    console.log(`=======================================================`);
});
