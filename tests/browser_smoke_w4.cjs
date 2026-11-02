/* Chạy với Playwright đã cài riêng. Chỉ dùng server/DB TEST và preview được bật. */
const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");
const {chromium} = require("playwright");
const base = process.env.W4_BASE_URL || "http://127.0.0.1:5000";
const output = process.env.W4_EVIDENCE_DIR || path.join(__dirname, "../docs/evidence/w4");

(async () => {
  fs.mkdirSync(output, {recursive: true});
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.W4_CHROMIUM_EXECUTABLE || undefined,
    args: ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--no-zygote"],
  });
  const context = await browser.newContext({viewport: {width: 1280, height: 900}});
  // Cố ý kiểm tra CSS nội bộ khi CDN không truy cập được; không coi lỗi CDN là lỗi JS.
  await context.route("https://cdn.jsdelivr.net/**", route => route.abort());
  const page = await context.newPage();
  const errors = [];
  const checks = [];
  const metrics = [];
  let posts = 0;
  page.on("pageerror", error => errors.push(String(error)));
  page.on("request", request => {
    if (request.method() === "POST" && new URL(request.url()).pathname === "/checkout") posts++;
  });
  async function goto(url) {
    const response = await page.goto(base + url, {waitUntil: "networkidle"});
    return response.status();
  }
  async function login(email) {
    await goto("/login");
    await page.fill('input[name="email"]', email);
    await page.fill('input[name="password"]', process.env.W4_TEST_PASSWORD || "Demo@12345");
    await Promise.all([page.waitForNavigation({waitUntil: "networkidle"}),
      page.locator('.auth-card button[type="submit"]').click()]);
  }
  async function addCart() {
    await goto("/product/1");
    await page.selectOption("#variant-color", "Đen");
    await page.selectOption("#variant-size", "39");
    await page.fill("#quantity", "1");
    await Promise.all([page.waitForURL("**/cart"),
      page.locator('.buy-form button[type="submit"]').click()]);
  }
  async function measure(name, url, width, expected = 200, screenshot = true) {
    await page.setViewportSize({width, height: 900});
    assert.equal(await goto(url), expected, name);
    const sizes = await page.evaluate(() => ({
      width: innerWidth, scrollWidth: document.documentElement.scrollWidth,
      brokenImages: [...document.images].filter(i => !i.complete || i.naturalWidth === 0).map(i => i.src),
    }));
    metrics.push({name, url, expectedHttp: expected, ...sizes});
    assert.ok(sizes.scrollWidth <= width, name + " overflows at " + width + ": " + sizes.scrollWidth);
    assert.deepEqual(sizes.brokenImages, [], name + " broken images");
    if (screenshot) await page.screenshot({path: path.join(output, name + "_" + width + ".png"), fullPage: true});
  }
  await login(process.env.W4_TEST_EMAIL || "khach@shop.vn");
  await addCart();
  const views = [
    ["home", "/"], ["catalog", "/products"], ["search", "/products?q=Converse"],
    ["paging", "/products?page=2"], ["detail", "/product/1"], ["cart", "/cart"],
    ["checkout", "/checkout"], ["orders_sample", "/ui-preview/w4/orders"],
    ["order_detail_sample", "/ui-preview/w4/detail"],
    ["payment_failed_sample", "/ui-preview/w4/failed"],
    ["cancelled_sample", "/ui-preview/w4/cancelled"],
    ["empty_sample", "/ui-preview/w4/empty"],
  ];
  for (const width of [375, 768, 1280]) {
    for (const [name, url] of views)
      await measure(name, url, width, 200, ["checkout", "order_detail_sample", "orders_sample",
        "payment_failed_sample", "cancelled_sample", "empty_sample"].includes(name));
    await measure("orders_backend_unavailable", "/my-orders", width, 503);
  }
  await page.setViewportSize({width: 375, height: 900});
  await goto("/checkout");
  await page.fill("#full_name", "A");
  await page.fill("#phone", "abc");
  await page.fill("#address", "abc");
  const beforeInvalid = posts;
  await page.locator(".checkout-submit").click();
  assert.equal(posts, beforeInvalid, "Invalid form was submitted");
  assert.ok(await page.locator("#full_name-error").isVisible());
  assert.ok(await page.locator("#phone-error").isVisible());
  assert.ok(await page.locator("#address-error").isVisible());
  await page.screenshot({path: path.join(output, "checkout_invalid_375.png"), fullPage: true});
  checks.push("Invalid client form: blocked POST, inline errors visible");
  await page.check('input[name="fulfillment"][value="pickup"]');
  assert.equal(await page.locator("#address").evaluate(e => e.required), false);
  assert.equal(await page.locator("#address").evaluate(e => e.disabled), true);
  assert.equal(await page.locator("#delivery-fields").isVisible(), false);
  assert.equal(await page.locator("#shipping-summary").innerText(), "0 ₫");
  checks.push("Pickup: no required address, no shipping fee");
  await page.check('input[name="payment_method"][value="bank_transfer"]');
  assert.ok((await page.locator("#payment-explain").innerText()).includes("không ghi nhận đã thanh toán"));
  checks.push("Bank transfer: pending explanation, no paid claim");
  await page.fill("#full_name", "Khach Kiem Thu");
  await page.fill("#phone", "0900000000");
  await page.route("**/checkout", async route => {
    if (route.request().method() === "POST") await new Promise(resolve => setTimeout(resolve, 200));
    await route.continue();
  });
  const beforeValid = posts;
  await Promise.all([page.waitForURL("**/checkout/success"),
    page.evaluate(() => {const f = document.getElementById("checkout-form"); f.requestSubmit(); f.requestSubmit();})]);
  assert.equal(posts, beforeValid + 1, "Client duplicate-submit guard");
  assert.ok((await page.locator("body").innerText()).includes("Trạng thái tại thời điểm gửi"));
  checks.push("Valid pickup checkout: one POST, real SQLite order, snapshot-labelled response");
  await page.screenshot({path: path.join(output, "checkout_result_375.png"), fullPage: true});
  await goto("/ui-preview/w4/detail");
  await page.locator("[data-open-cancel]").click();
  assert.equal(await page.locator("#cancel-dialog").evaluate(e => e.open), true);
  await page.locator("[data-close-cancel]").click();
  assert.equal(await page.locator("#cancel-dialog").evaluate(e => e.open), false);
  checks.push("Sample cancellation dialog: opens/closes without sending cancellation");
  await Promise.all([page.waitForNavigation({waitUntil: "networkidle"}),
    page.locator('form[action="/logout"] button').click()]);
  await login("admin@shop.vn");
  await goto("/admin");
  const add = page.getByRole("link", {name: "＋ Thêm sản phẩm", exact: true});
  assert.ok(await add.isVisible());
  await Promise.all([page.waitForURL("**/admin/products/new"), add.click()]);
  checks.push("Admin dashboard add link reaches real W3 product form");
  assert.deepEqual(errors, [], "JavaScript page errors");
  const report = {browser: await browser.version(), database: "isolated SQLite demo",
    cssMode: "local CSS; Bootstrap CDN blocked deliberately", metrics, checks, pageErrors: errors,
    sqlServer: "NOT RUN", liveOrderBackend: "BLOCKED; sample previews are not integration proof"};
  fs.writeFileSync(path.join(output, "browser_results.json"), JSON.stringify(report, null, 2));
  console.log(JSON.stringify({views: metrics.length, checks: checks.length, pageErrors: errors,
    browser: report.browser, output}));
  await browser.close();
})().catch(error => {console.error(error); process.exit(1);});
