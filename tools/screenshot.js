#!/usr/bin/env node
/**
 * Visual verification harness.
 *
 *   npx http-server -p 8099 -s . &
 *   node tools/screenshot.js [outDir] [url]
 *
 * Captures the page at desktop, tablet, wide and mobile widths (plus the
 * scrolled header and the open mobile menu) and reports any console error.
 *
 * The site hotlinks its photography from images.unsplash.com. Where egress to
 * that host is blocked — as it is in the sandbox this site was built in — the
 * remote images are fulfilled with generated stand-ins so layout and spacing
 * can still be checked. Set NOSTUB=1 to exercise the real remote-image path,
 * including the brand-coloured fallback behind each slot.
 *
 * Requires playwright (`npm i -D playwright`); deliberately not part of
 * `tests/run-tests.sh`, which stays browser-free so CI needs no extra install.
 */
'use strict';

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const OUT = process.argv[2] || '/tmp/shots';
const URL = process.argv[3] || 'http://127.0.0.1:8099/';

// Deterministic tonal stand-ins, generated rather than committed.
const TONES = [
  ['#20302c', '#607c74'], ['#463e34', '#96846e'], ['#2c3c48', '#7892a0'],
  ['#3c302c', '#8c7464'], ['#263830', '#6e8a80'], ['#342c3c', '#807090'],
  ['#42382c', '#9a866c'],
];
const stub = (i) => {
  const [a, b] = TONES[i % TONES.length];
  const rings = Array.from({ length: 9 }, (_, k) =>
    `<circle cx="${64 + k * 80}" cy="250" r="${60 + 28 * Math.sin(k)}" ` +
    `fill="none" stroke="${b}" stroke-opacity=".5" stroke-width="3"/>`).join('');
  return `<svg xmlns="http://www.w3.org/2000/svg" width="800" height="500">
    <defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="${a}"/><stop offset="1" stop-color="${b}"/>
    </linearGradient></defs>
    <rect width="800" height="500" fill="url(#g)"/>${rings}</svg>`;
};

const SHOTS = [
  ['desktop-full', 1440, 900, { full: true }],
  ['desktop-hero', 1440, 900, {}],
  ['desktop-scrolled', 1440, 900, { scrollTo: 300 }],
  ['wide-full', 1920, 1080, { full: true }],
  ['tablet-full', 834, 1112, { full: true }],
  ['mobile-full', 390, 844, { full: true }],
  ['mobile-hero', 390, 844, {}],
  ['mobile-menu', 390, 844, { openMenu: true, scrollTo: 200 }],
];

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();
  let failures = 0;

  for (const [name, width, height, opts] of SHOTS) {
    const ctx = await browser.newContext({ viewport: { width, height } });
    const page = await ctx.newPage();
    let served = 0;

    if (!process.env.NOSTUB) {
      await page.route('https://images.unsplash.com/**', (route) =>
        route.fulfill({ body: stub(served++), contentType: 'image/svg+xml' }));
    }

    const errors = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('pageerror', (e) => errors.push(String(e)));

    await page.goto(URL, { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);

    // Walk the page so loading="lazy" images actually fetch before capture.
    await page.evaluate(async () => {
      document.documentElement.style.scrollBehavior = 'auto';
      const step = window.innerHeight * 0.8;
      for (let y = 0; y < document.body.scrollHeight; y += step) {
        window.scrollTo(0, y);
        await new Promise((r) => setTimeout(r, 60));
      }
      window.scrollTo(0, 0);
    });
    await page.waitForLoadState('networkidle');

    if (opts.scrollTo) await page.evaluate((y) => window.scrollTo(0, y), opts.scrollTo);
    if (opts.openMenu) await page.click('#nav-toggle');
    await page.waitForTimeout(300);

    await page.screenshot({ path: path.join(OUT, `${name}.png`), fullPage: !!opts.full });

    if (errors.length) {
      failures += errors.length;
      console.error(`  FAIL ${name}: ${errors.length} console error(s)`);
      errors.slice(0, 5).forEach((e) => console.error(`       ${e.split('\n')[0]}`));
    } else {
      console.log(`  ok   ${name} (${width}x${height})`);
    }
    await ctx.close();
  }

  await browser.close();
  console.log(`\nscreenshots -> ${OUT}`);
  if (failures) {
    console.error(`${failures} console error(s) across the captures.`);
    process.exit(1);
  }
})();
