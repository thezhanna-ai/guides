// Faithful, local article preview. Screenshots are written only after font checks pass.
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');

async function readyArticle(page, url) {
  const fontResponses = [];
  const failedFonts = [];
  page.on('response', response => {
    if (/\.woff2(?:\?|$)/.test(response.url())) fontResponses.push({url: response.url(), status: response.status()});
  });
  page.on('requestfailed', request => {
    if (/\.woff2(?:\?|$)/.test(request.url())) failedFonts.push(request.url());
  });
  const response = await page.goto(url, {waitUntil: 'networkidle'});
  assert.equal(response.status(), 200, 'Article must load from the real local site');
  const result = await page.evaluate(async () => {
    const faces = [
      ['300 18px Spectral', 'Текст 0123456789'],
      ['400 18px Spectral', 'Текст 0123456789'],
      ['600 18px Spectral', 'Текст 0123456789'],
      ['700 32px Unbounded', 'Заголовок 0123456789'],
      ['500 14px "JetBrains Mono"', 'Команда 0123456789'],
      ['700 14px "JetBrains Mono"', 'Команда 0123456789'],
    ];
    const loaded = [];
    for (const [font, text] of faces) {
      const values = await document.fonts.load(font, text);
      loaded.push({font, count: values.length, ready: values.length > 0 && values.every(face => face.status === 'loaded') && document.fonts.check(font, text)});
    }
    await document.fonts.ready;
    const body = getComputedStyle(document.body);
    const paragraph = document.querySelector('main p') || document.querySelector('p');
    const text = paragraph && getComputedStyle(paragraph);
    return {
      status: document.fonts.status, loaded,
      family: body.fontFamily,
      paragraphFamily: text && text.fontFamily,
      numerals: body.fontFeatureSettings,
      paragraphNumerals: text && text.fontFeatureSettings,
      headingFamily: getComputedStyle(document.querySelector('h1')).fontFamily,
      overflow: document.documentElement.scrollWidth > innerWidth,
    };
  });
  assert.equal(result.status, 'loaded');
  assert.ok(result.loaded.every(face => face.ready), JSON.stringify(result.loaded));
  assert.match(result.family, /Spectral/i, 'Use the actual article font');
  assert.match(result.headingFamily, /Unbounded/i, 'Use the actual article heading');
  assert.match(result.numerals, /"lnum"(?: 1)?/, 'Use lining numerals');
  assert.match(result.paragraphNumerals, /"lnum"(?: 1)?/, 'Article text must inherit lining numerals');
  assert.ok(fontResponses.length > 0, 'Observe actual font network responses');
  assert.ok(fontResponses.every(response => response.status === 200), JSON.stringify(fontResponses));
  assert.deepEqual(failedFonts, []);
  assert.equal(result.overflow, false, 'Article must fit the viewport');
  return {...result, fontResponses};
}

function serveSite() {
  const types = {'.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.woff2': 'font/woff2', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.png': 'image/png', '.ico': 'image/x-icon'};
  return http.createServer((request, response) => {
    try {
      const url = new URL(request.url, 'http://localhost');
      let filename = path.resolve(root, '.' + decodeURIComponent(url.pathname));
      if (filename !== root && !filename.startsWith(root + path.sep)) throw new Error('Outside site');
      if (fs.statSync(filename).isDirectory()) filename = path.join(filename, 'index.html');
      if (!fs.realpathSync(filename).startsWith(root + path.sep)) throw new Error('Outside site');
      response.writeHead(200, {'Content-Type': types[path.extname(filename)] || 'application/octet-stream'});
      fs.createReadStream(filename).pipe(response);
    } catch {
      response.writeHead(404); response.end('Not found');
    }
  });
}

async function main() {
  const [slug, output] = process.argv.slice(2);
  const registry = JSON.parse(fs.readFileSync(path.join(root, 'data/statyi.json'), 'utf8')).statyi;
  assert.ok(slug && registry.some(article => article.slug === slug), 'Pass an existing article slug');
  assert.ok(output, 'Pass an output directory');
  const {chromium} = require(process.env.SITE_PLAYWRIGHT_MODULE || 'playwright');
  const server = serveSite();
  let browser;
  try {
    await new Promise((resolve, reject) => { server.once('error', reject); server.listen(0, '127.0.0.1', resolve); });
    browser = await chromium.launch({headless: true, ...(process.env.SITE_CHROMIUM ? {executablePath: process.env.SITE_CHROMIUM} : {})});
    const results = [];
    fs.mkdirSync(output, {recursive: true});
    for (const viewport of [{width: 390, height: 844}, {width: 1440, height: 1000}]) {
      const context = await browser.newContext({viewport, deviceScaleFactor: 1});
      try {
        const page = await context.newPage();
        const fonts = await readyArticle(page, `http://127.0.0.1:${server.address().port}/claude-ai/${slug}/`);
        const filename = path.join(output, `${slug}-${viewport.width}x${viewport.height}.png`);
        await page.screenshot({path: filename});
        results.push({viewport, filename, fonts});
      } finally { await context.close(); }
    }
    fs.writeFileSync(path.join(output, 'fonts.json'), JSON.stringify(results, null, 2) + '\n');
    console.log('Article preview: fonts, lnum and both screenshots PASS');
  } finally {
    if (browser) await browser.close();
    server.close();
  }
}

module.exports = {readyArticle, serveSite};
if (require.main === module) main().catch(error => { console.error(error); process.exitCode = 1; });
