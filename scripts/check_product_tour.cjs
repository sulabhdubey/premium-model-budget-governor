// Optional browser QA: install Playwright or set PMBG_PLAYWRIGHT to its module path.
const { chromium } = require(process.env.PMBG_PLAYWRIGHT || 'playwright');
const { pathToFileURL } = require('node:url');
const path = require('node:path');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const output = path.join(root, 'build', 'product-tour-qa');
fs.mkdirSync(output, { recursive: true });

(async () => {
  const browser = await chromium.launch({ headless: true });
  const results = [];
  try {
    for (const width of [1440, 390, 320]) {
      const page = await browser.newPage({ viewport: { width, height: 1000 } });
      const errors = [];
      page.on('pageerror', e => errors.push(e.message));
      await page.goto(process.env.PMBG_SITE_URL || pathToFileURL(path.join(root, 'site/index.html')).href);
      await page.screenshot({ path: path.join(output, `hero-${width}.png`) });
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, `overflow ${width}`);
      await page.locator('#tour').scrollIntoViewIfNeeded();
      await page.locator('#tour-image').evaluate(img => img.decode());
      await page.locator('#tour').screenshot({ path: path.join(output, `tour-${width}.png`) });
      if (width === 1440 && !process.env.PMBG_SITE_URL) {
        await page.locator('#tour').screenshot({ path: path.join(root, 'site/assets/tour-poster.png') });
      }
      assert.equal(await page.locator('#tour-play').getAttribute('aria-pressed'), 'false');
      await page.locator('#tour-tab-1').click();
      assert.equal(await page.locator('#tour-tab-1').getAttribute('aria-selected'), 'true');
      await page.locator('#tour-image').evaluate(img => img.decode());
      assert.match(await page.locator('#tour-image').getAttribute('src'), /prepared/);
      await page.locator('#tour-tab-1').press('ArrowRight');
      assert.equal(await page.locator('#tour-tab-2').getAttribute('aria-selected'), 'true');
      await page.locator('#tour-image').evaluate(img => img.decode());
      await page.locator('#tour-tab-2').press('Home');
      await page.locator('#tour-play').click();
      await page.waitForTimeout(5300);
      assert.equal(await page.locator('#tour-tab-1').getAttribute('aria-selected'), 'true');
      await page.locator('#tour-play').click();
      assert.equal(await page.locator('#tour-play').getAttribute('aria-pressed'), 'false');
      await page.locator('#tour-play').click();
      await page.locator('#tour-play').press('Escape');
      assert.equal(await page.locator('#tour-play').getAttribute('aria-pressed'), 'false');
      await page.locator('#tour-play').click();
      await page.locator('#install').scrollIntoViewIfNeeded();
      await page.waitForFunction(() => document.querySelector('#tour-play').getAttribute('aria-pressed') === 'false');
      await page.emulateMedia({ reducedMotion: 'reduce' });
      await page.locator('#tour-tab-2').click();
      assert.equal(await page.locator('#tour-panel').evaluate(el => el.getAnimations().length), 0);
      await page.locator('#task-budget').fill('0');
      await page.locator('#route-form').dispatchEvent('input');
      assert.equal(await page.locator('#recommended-model').innerText(), 'Needs replan');
      await page.locator('#task-budget').fill('12');
      await page.locator('#host-context').selectOption('0');
      assert.equal(await page.locator('#context-action').innerText(), 'Measure first');
      await page.locator('#host-context').selectOption('24000');
      await page.locator('#remaining-budget').fill('10');
      assert.match(await page.locator('#decision-reason').innerText(), /explicit approval/);
      await page.locator('#explicit-approval').check();
      assert.equal(await page.locator('#recommended-model').innerText(), 'Astra direct');
      assert.deepEqual(errors, []);
      results.push({ width, keyboard: 'passed', playback: 'passed', reducedMotion: 'passed', offscreenStop: 'passed', planner: 'passed', pageErrors: errors });
      await page.close();
    }
    fs.writeFileSync(path.join(output, 'results.json'), JSON.stringify(results, null, 2));
    console.log(JSON.stringify(results));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
