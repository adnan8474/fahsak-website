// End-to-end verification that the Ops Central analytics beacon actually fires.
//
// Serves the local files as if they were https://www.sihtak.com/ (so the host gate in
// analytics.js passes) AND applies the real Content-Security-Policy from
// staticwebapp.config.json, so a CSP that blocks App Insights fails this test
// rather than silently recording zero traffic in production.
//
// This sends ONE real page view to the sihtak App Insights component.
//
// Usage: node verify-analytics.js [path]      e.g. node verify-analytics.js /articles/
const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const ROOT = __dirname;
const WANT = process.argv[2] || '/';

const CSP = JSON.parse(fs.readFileSync(path.join(ROOT, 'staticwebapp.config.json'), 'utf8'))
  .globalHeaders['Content-Security-Policy'];

const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.ico': 'image/x-icon',
  '.webp': 'image/webp',
  '.json': 'application/json',
};

(async () => {
  const browser = await chromium.launch({ executablePath: CHROME, headless: true });
  const page = await browser.newPage();

  await page.route('**://*.sihtak.com/**', route => {
    const u = new URL(route.request().url());
    let p = decodeURIComponent(u.pathname);
    if (p.endsWith('/')) p += 'index.html';
    const file = path.join(ROOT, p.replace(/^\/+/, ''));
    if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) {
      return route.fulfill({ status: 404, body: 'nf' });
    }
    route.fulfill({
      status: 200,
      contentType: TYPES[path.extname(file).toLowerCase()] || 'application/octet-stream',
      headers: { 'Content-Security-Policy': CSP },   // exactly what production sends
      body: fs.readFileSync(file),
    });
  });

  const track = [];
  const sdk = [];
  const csp = [];
  page.on('request', r => { if (/\/v2\/track/.test(r.url())) track.push('REQ ' + r.method()); });
  page.on('response', async r => {
    if (/\/v2\/track/.test(r.url())) track.push('RES ' + r.status() + ' ' + (await r.text().catch(() => '')).slice(0, 120));
    if (/js\.monitor\.azure\.com/.test(r.url())) sdk.push('SDK script ' + r.status());
  });
  page.on('requestfailed', r => {
    if (/\/v2\/track|js\.monitor/.test(r.url())) track.push('FAILED ' + ((r.failure() || {}).errorText || '?'));
  });
  page.on('console', m => {
    const t = m.text();
    if (/Content Security Policy|Refused to/i.test(t)) csp.push(t.slice(0, 180));
  });
  page.on('pageerror', e => track.push('PAGEERROR ' + String(e).slice(0, 140)));

  await page.goto('https://www.sihtak.com' + WANT, { waitUntil: 'load', timeout: 60000 });
  await page.waitForTimeout(12000);

  const state = await page.evaluate(() => ({
    ai: typeof window.sihtakAI,
    ms: typeof (window.Microsoft && window.Microsoft.ApplicationInsights),
  }));

  console.log('path tested        :', WANT);
  console.log('SDK script loaded  :', sdk.length ? sdk.join(', ') : 'NO');
  console.log('window.sihtakAI    :', state.ai);
  console.log('MS SDK namespace   :', state.ms);
  if (csp.length) {
    console.log('--- CSP violations (these would silently kill telemetry in production) ---');
    csp.forEach(c => console.log('  ' + c));
  }
  console.log('--- telemetry ---');
  if (!track.length) console.log('  NO BEACON FIRED');
  track.forEach(t => console.log('  ' + t));

  const ok = track.some(t => /^RES 2\d\d/.test(t)) && !csp.some(c => /js\.monitor|applicationinsights/i.test(c));
  console.log('\nRESULT:', ok ? 'PASS - pageview accepted by Azure, CSP allows it' : 'FAIL');
  await browser.close();
  process.exit(ok ? 0 : 1);
})();
