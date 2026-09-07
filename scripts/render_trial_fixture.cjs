const {chromium} = require("playwright");
const path = require("path");
const {pathToFileURL} = require("url");
const fs = require("fs");
const {createHash} = require("crypto");
(async () => {
  const directory = path.resolve(__dirname, "../examples/field-trial");
  const browser = await chromium.launch({headless:true});
  try {
    const page = await browser.newPage({viewport:{width:800,height:560},deviceScaleFactor:1});
    await page.goto(pathToFileURL(path.join(directory,"queue-chart.html")).href);
    await page.screenshot({path:path.join(directory,"queue-chart.png"),fullPage:true});
    const suite = JSON.parse(fs.readFileSync(path.join(directory,"suite.json"),"utf8"));
    const names = [...new Set(["suite.json", ...suite.tasks.flatMap(task=>task.inputs)])].sort();
    const files = Object.fromEntries(names.map(name=>[name,createHash("sha256").update(fs.readFileSync(path.join(directory,name))).digest("hex")]));
    fs.writeFileSync(path.join(directory,"snapshot.json"),JSON.stringify({suite_id:suite.id,files},null,2)+"\n");
    console.log("Rendered authored queue fixture; no model call.");
  } finally { await browser.close(); }
})().catch(error => { console.error(error.message); process.exit(1); });
