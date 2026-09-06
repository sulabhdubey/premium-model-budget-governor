const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const {pathToFileURL} = require('url');
(async()=>{
  const browser = await chromium.launch({headless:true});
  const results=[];
  try {
    for (const width of [1440,390,320]) {
      const page=await browser.newPage({viewport:{width,height:900}});
      const errors=[];
      page.on('pageerror',e=>errors.push(e.message));
      await page.goto(pathToFileURL(path.resolve('artifacts/benchmark-v3/dashboard.html')).href);
      await page.getByRole('heading',{name:'Ledger Snapshot'}).waitFor();
      const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
      const rows=await page.locator('tbody tr').count();
      if(overflow || errors.length || rows !== 1) throw new Error(JSON.stringify({width,overflow,errors,rows}));
      const table=page.getByRole('region',{name:'Task budgets'});
      await table.focus();
      if(!await table.evaluate(el=>el===document.activeElement)) throw new Error('table not keyboard reachable');
      await page.screenshot({path:`artifacts/benchmark-v3/dashboard-${width}.png`,fullPage:true});
      results.push({width,overflow,errors,rows,keyboard_reachable:true});
      await page.close();
    }
    fs.writeFileSync('artifacts/benchmark-v3/dashboard-qa.json',JSON.stringify(results,null,2));
    console.log(JSON.stringify(results));
  } finally {await browser.close();}
})();
