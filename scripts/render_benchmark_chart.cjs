const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const browser = await chromium.launch({headless:true});
  try {
    const page = await browser.newPage({viewport:{width:900,height:620},deviceScaleFactor:1});
    await page.setContent(`<!doctype html><html><style>body{font:20px Arial;margin:40px;background:white;color:#172328}h1{font-size:30px;margin-bottom:8px}.row{display:grid;grid-template-columns:90px 1fr;gap:12px;margin:35px 0}.bars{display:grid;gap:8px}.bar{height:32px;background:#137d75;color:white;padding:5px;box-sizing:border-box}.output{background:#98430f}small{font-size:17px}</style><h1>Fixture Workload</h1><p>Thousands of tokens</p><small>Cold input: green &nbsp; Output: rust</small><div class=row>Astra<div class=bars><div class=bar style=width:480px>24</div><div class="bar output" style=width:160px>8</div></div></div><div class=row>Sol<div class=bars><div class=bar style=width:360px>18</div><div class="bar output" style=width:120px>6</div></div></div><div class=row>Terra<div class=bars><div class=bar style=width:400px>20</div><div class="bar output" style=width:80px>4</div></div></div><small>Synthetic visual fixture. Not measured model performance.</small></html>`);
    await page.screenshot({path:path.resolve('examples/benchmark_v3.png')});
  } finally {await browser.close();}
})();
