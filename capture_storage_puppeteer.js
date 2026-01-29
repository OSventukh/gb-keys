const fs = require("fs");
const path = require("path");
const readline = require("readline");
const puppeteer = require("puppeteer-extra");
const StealthPlugin = require("puppeteer-extra-plugin-stealth");

puppeteer.use(StealthPlugin());

function ask(question) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  return new Promise((resolve) => rl.question(question, (ans) => {
    rl.close();
    resolve(ans);
  }));
}

async function main() {
  const labelArg = process.argv.find((a) => a.startsWith("--label="));
  const label = labelArg ? labelArg.split("=")[1] : null;
  if (!label) {
    console.error("Usage: node capture_storage_puppeteer.js --label=eur");
    process.exit(1);
  }

  const url = "https://gameboost.com/keys";
  const outDir = path.join(process.cwd(), "storage_dumps");
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir);

  const browser = await puppeteer.launch({ headless: false });
  const page = await browser.newPage();
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 });

  console.log("\nПереключи валюту у хедері, потім натисни Enter тут...");
  await ask("");

  const cookies = await page.cookies();
  const localStorage = await page.evaluate(() => {
    const o = {};
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i);
      o[k] = localStorage.getItem(k);
    }
    return o;
  });
  const sessionStorage = await page.evaluate(() => {
    const o = {};
    for (let i = 0; i < sessionStorage.length; i++) {
      const k = sessionStorage.key(i);
      o[k] = sessionStorage.getItem(k);
    }
    return o;
  });

  const payload = { url, cookies, localStorage, sessionStorage };
  const outFile = path.join(outDir, `state_${label}.json`);
  fs.writeFileSync(outFile, JSON.stringify(payload, null, 2), "utf-8");
  console.log(`Збережено: ${outFile}`);

  await browser.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
