const { chromium } = require("playwright");
const path = require("path");
const fs = require("fs");
const { pathToFileURL } = require("url");
const assert = require("assert/strict");

(async () => {
  const root = path.resolve(__dirname, "..");
  const output = path.join(root, "artifacts", "site-qa");
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const records = [];
  try {
    for (const viewport of [{ width: 1440, height: 1000 }, { width: 390, height: 844 }, { width: 320, height: 740 }]) {
      const page = await browser.newPage({ viewport });
      const errors = [];
      page.on("pageerror", e => errors.push(e.message));
      page.on("console", m => { if (m.type() === "error") errors.push(m.text()); });
      await page.goto(process.env.QA_URL || pathToFileURL(path.join(root, "site", "index.html")).href, { waitUntil: "load" });
      assert.equal(await page.locator("#recommended-model").textContent(), "Astra direct");
      await page.getByLabel("Weekly capacity remaining").fill("10");
      assert.equal(await page.locator("#recommended-model").textContent(), "Needs replan");
      await page.getByLabel("Explicit premium approval").check();
      assert.equal(await page.locator("#recommended-model").textContent(), "Astra direct");
      await page.getByLabel("Total task budget").fill("1");
      assert.equal(await page.locator("#recommended-model").textContent(), "Needs replan");
      await page.getByLabel("Total task budget").fill("12");
      await page.getByLabel("Host input floor").selectOption("0");
      assert.equal(await page.locator("#recommended-model").textContent(), "Needs replan");
      await page.getByLabel("Host input floor").selectOption("24000");
      await page.getByLabel("Workflow preference").selectOption("economy");
      assert.equal(await page.locator("#recommended-model").textContent(), "Sol direct");
      await page.getByLabel("Workflow preference").selectOption("astra_preferred");
      await page.getByLabel("Required evidence prepared").uncheck();
      assert.equal(await page.locator("#recommended-model").textContent(), "Needs replan");
      await page.getByLabel("Required evidence prepared").check();
      if (viewport.width < 600) {
        await page.getByRole("button", { name: "Open navigation" }).click();
        assert(await page.locator("#mobile-menu").isVisible());
        await page.keyboard.press("Escape");
        assert(!(await page.locator("#mobile-menu").isVisible()));
      }
      const dimensions = await page.evaluate(() => ({ width: innerWidth, scroll: document.documentElement.scrollWidth }));
      assert(dimensions.scroll <= dimensions.width, "horizontal overflow");
      assert(await page.locator(".hero-visual img").evaluate(i => i.complete && i.naturalWidth > 1000), "hero asset missing");
      assert.deepEqual(errors, []);
      await page.screenshot({ path: path.join(output, `${viewport.width}.png`), fullPage: true });
      records.push({ viewport, dimensions, errors, controls_passed: true, hero_loaded: true });
      await page.close();
    }
  } finally {
    await browser.close();
  }
  fs.writeFileSync(path.join(output, "results.json"), JSON.stringify(records, null, 2));
  console.log(JSON.stringify(records, null, 2));
})().catch(e => { console.error(e); process.exit(1); });
