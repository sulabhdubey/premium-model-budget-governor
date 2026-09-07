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
      const command="python install_governor.py install --wheel premium_model_budget_governor-0.4.0rc3-py3-none-any.whl";
      assert.equal(await page.locator("#install-command").textContent(),command);
      let copied;
      await page.exposeFunction("recordCopiedCommand", value=>{copied=value;});
      await page.evaluate(()=>Object.defineProperty(navigator,"clipboard",{configurable:true,value:{writeText:value=>window.recordCopiedCommand(value)}}));
      await page.locator("#copy-command").click();
      await page.getByText("Install command copied.",{exact:true}).waitFor();
      assert.equal(copied,command);
      await page.locator("#install").evaluate(el=>el.scrollIntoView({block:"start",behavior:"instant"}));
      assert(await page.evaluate(()=>document.querySelector("#install-title").getBoundingClientRect().top>=document.querySelector(".site-header").getBoundingClientRect().bottom),"sticky header covers installation heading");
      await page.screenshot({path:path.join(output,`installation-${viewport.width}.png`)});
      await page.evaluate(()=>Object.defineProperty(navigator,"clipboard",{configurable:true,value:{writeText:()=>Promise.reject(new Error("fixture denied"))}}));
      await page.locator("#copy-command").click();
      await page.getByText("Clipboard unavailable. Select the command to copy it.",{exact:true}).waitFor();
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
      records.push({ viewport, dimensions, errors, controls_passed: true, hero_loaded: true,release_specific_install_preview:true,simulated_clipboard_success_and_failure:true });
      await page.close();
    }
  } finally {
    await browser.close();
  }
  fs.writeFileSync(path.join(output, "results.json"), JSON.stringify(records, null, 2));
  console.log(JSON.stringify(records, null, 2));
})().catch(e => { console.error(e); process.exit(1); });
