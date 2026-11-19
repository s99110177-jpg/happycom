// node capture.js <seed> <frames> <outDir>  — render.html 을 열어 프레임 PNG 를 저장
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");
(async () => {
  const [seed = "20261120", n = "165", out = "frames"] = process.argv.slice(2);
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto("file://" + path.resolve(__dirname, "render.html") + "?seed=" + seed);
  await page.waitForFunction(() => window.ready === true, null, { timeout: 60000 });
  for (let i = 0; i < +n; i++) {
    const url = await page.evaluate(() => window.nextFrame());
    fs.writeFileSync(path.join(out, String(i).padStart(4, "0") + ".png"), Buffer.from(url.split(",")[1], "base64"));
  }
  await browser.close();
  console.log("frames:", n);
})();
