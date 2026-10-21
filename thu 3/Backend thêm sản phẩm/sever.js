/**
 * Backend thêm sản phẩm - Shoes Admin (Node.js & Express / Native HTTP)
 */

const http = require("http");
const fs = require("fs");
const path = require("path");

const PORT = 3000;
let products = [
    {
        name: "Nike Air Max 270",
        description: "Đệm khí lớn nhất của Nike mang lại sự thoải mái cả ngày.",
        price: 3500000,
        brand: "Nike",
        type: "Giày thể thao",
        gender: "Nam",
        status: "Đang bán"
    }
];

const MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8"
};

const server = http.createServer((req, res) => {
    const url = new URL(req.url, `http://${req.headers.host}`);
    const pathname = url.pathname;

    // API lấy danh sách sản phẩm
    if (pathname === "/api/products" && req.method === "GET") {
        res.writeHead(200, { "Content-Type": "application/json; charset=utf-8" });
        return res.end(JSON.stringify(products));
    }

    // API thêm sản phẩm mới
    if (pathname === "/api/products" && req.method === "POST") {
        let body = "";
        req.on("data", chunk => { body += chunk.toString(); });
        req.on("end", () => {
            try {
                const data = JSON.parse(body || "{}");
                if (!data.name || !data.price) {
                    res.writeHead(400, { "Content-Type": "application/json; charset=utf-8" });
                    return res.end(JSON.stringify({ message: "Thiếu tên hoặc giá sản phẩm" }));
                }
                products.push(data);
                res.writeHead(201, { "Content-Type": "application/json; charset=utf-8" });
                return res.end(JSON.stringify({ message: "Thêm thành công!", product: data }));
            } catch (err) {
                res.writeHead(500, { "Content-Type": "application/json; charset=utf-8" });
                return res.end(JSON.stringify({ message: "Lỗi server: " + err.message }));
            }
        });
        return;
    }

    // Phục vụ file tĩnh
    let filePath = path.join(__dirname, pathname === "/" ? "index.html" : pathname);
    fs.readFile(filePath, (err, data) => {
        if (err) {
            res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
            return res.end("404 Not Found");
        }
        const ext = path.extname(filePath).toLowerCase();
        res.writeHead(200, { "Content-Type": MIME_TYPES[ext] || "text/plain" });
        res.end(data);
    });
});

server.listen(PORT, () => {
    console.log(`Backend server đang chạy tại: http://localhost:${PORT}`);
});