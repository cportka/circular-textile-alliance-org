#!/usr/bin/env node
/* Newsletter signup, exercised in a real browser.

   Default mode answers every Mailchimp request from inside the browser
   (Playwright routes), so it runs offline and covers each outcome: success
   with and without double opt-in, already subscribed, too many attempts,
   invalid address, captcha, an unrecognised answer, unreachable, no callback,
   a relay frame that never starts, timeout and a late answer, double submits
   and double presses after a handoff, a hostile reply sealed inside the
   sandboxed relay, both forms independently, the no-script form, and that
   every message the script writes fits the reserved row.

   --live talks to the real Mailchimp audience, and only with an address on
   the reserved .invalid TLD (RFC 2606), which can never be a real mailbox, so
   Mailchimp must refuse it and no contact is ever created. What it proves is
   the round trip: the CSP admits the JSONP script and the form post, the
   endpoint answers, and the answer reaches the status line.

   Run:  NODE_PATH="$(npm root -g)" node tests/browser/newsletter.cjs [--live]
   (CI installs Playwright into a temp prefix and points NODE_PATH there.) */
'use strict';

const http = require('http');
const fs = require('fs');
const path = require('path');
const playwright = require('playwright');
const { chromium, request: apiRequest } = playwright;
// BROWSER=chromium|firefox|webkit picks the engine for the mocked run; CI runs
// all three, since the relay depends on how each engine treats a sandboxed
// frame. The live run is Chromium only.
const ENGINE = process.env.BROWSER || 'chromium';
if (!['chromium', 'firefox', 'webkit'].includes(ENGINE)) throw new Error('unknown BROWSER ' + ENGINE);

const ROOT = path.resolve(__dirname, '..', '..');
const LIVE = process.argv.includes('--live');
// --base <url>: run the live checks against a deployed copy of the site (e.g.
// the GitHub Pages URL) instead of a local server, so Mailchimp sees the real
// origin. Mocked mode always uses the local server.
const BASE_ARG = process.argv.indexOf('--base');
const REMOTE_BASE = BASE_ARG > -1 ? String(process.argv[BASE_ARG + 1] || '').replace(/\/+$/, '') : '';
const HOST = 'https://circulartextilealliance.us16.list-manage.com';
const U = 'ea29d1a908ff6356342abbd84';
const ID = '81fed3ffc1';
const TRAP = 'b_' + U + '_' + ID;
const FORMS = ['#newsletter-form-about', '#newsletter-form'];

// The copy the script writes, read from site.js so the two cannot drift.
const SITE_JS = fs.readFileSync(path.join(ROOT, 'assets/js/site.js'), 'utf8');
const block = SITE_JS.match(/var MESSAGES = \{([\s\S]*?)\};/);
if (!block) throw new Error('could not find the MESSAGES table in site.js');
const MESSAGES = {};
for (const m of block[1].matchAll(/(\w+):\s*'([^']*)'/g)) MESSAGES[m[1]] = m[2];

let failures = 0;
let passes = 0;
const ok = (cond, label, detail) => {
  if (cond) { passes++; console.log('  PASS  ' + label); }
  else { failures++; console.log('  FAIL  ' + label + (detail ? '\n        ' + detail : '')); }
};

// --- A static server for the repo root -----------------------------------
const TYPES = {
  '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript',
  '.svg': 'image/svg+xml', '.webp': 'image/webp', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.woff2': 'font/woff2', '.webmanifest': 'application/manifest+json', '.txt': 'text/plain',
  '.xml': 'application/xml', '.ico': 'image/x-icon',
};
const server = http.createServer((req, res) => {
  const rel = decodeURIComponent(new URL(req.url, 'http://x').pathname).replace(/^\/+/, '') || 'index.html';
  const file = path.join(ROOT, rel);
  if (!file.startsWith(ROOT + path.sep) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
    res.writeHead(404); res.end('not found'); return;
  }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});

// --- Helpers ---------------------------------------------------------------
const jsonpBody = (url, payload) => new URL(url).searchParams.get('c') + '(' + JSON.stringify(payload) + ')';

async function openPage(browser, base, opts = {}) {
  // Reduced motion turns off the site's smooth scrolling; otherwise a click can
  // land while the page is still gliding the button into view, and under load
  // Playwright then waits on a target that never holds still.
  const context = await browser.newContext({
    javaScriptEnabled: opts.js !== false,
    viewport: { width: 1280, height: 900 },
    reducedMotion: 'reduce',
    ...(opts.userAgent ? { userAgent: opts.userAgent } : {}),
  });
  const page = await context.newPage();
  // Violations are gathered from every frame, the sandboxed relay included —
  // through the console, and through a binding the init script reports to.
  const csp = [];
  page.on('console', (msg) => { if (/Content.Security.Policy/i.test(msg.text())) csp.push(msg.text()); });
  if (opts.js !== false) {
    await context.exposeBinding('__cspReport', (source, line) => csp.push(line));
    await context.addInitScript(() => {
      document.addEventListener('securitypolicyviolation', (e) => {
        window.__cspReport(e.effectiveDirective + ' ' + e.blockedURI + ' in ' + location.pathname);
      });
    });
  }
  if (opts.frame) await context.route('**/newsletter-frame.html', opts.frame);
  if (process.env.TRACE) {
    context.on('request', (r) => console.log('        [trace ' + ENGINE + '] → ' + r.method() + ' ' + r.url().slice(0, 120)));
    context.on('requestfailed', (r) => console.log('        [trace ' + ENGINE + '] ✗ ' + r.url().slice(0, 120) + ' ' + (r.failure() || {}).errorText));
  }
  if (opts.clock) await page.clock.install();
  if (opts.route) await context.route(HOST + '/**', opts.route);
  await page.goto(base + '/index.html');
  return { context, page, csp };
}

const statusOf = (page, form) => page.locator(form + ' .newsletter__status');

async function submit(page, form, email) {
  await page.fill(form + ' .newsletter__input', email);
  await page.click(form + ' .newsletter__submit');
}

async function waitForStatus(page, form, text, timeout = 5000) {
  try {
    await page.waitForFunction(([f, t]) => {
      const el = document.querySelector(f + ' .newsletter__status');
      return el && el.textContent === t;
    }, [form, text], { timeout });
    return true;
  } catch (e) {
    return false;
  }
}

const cspViolations = async (page, seen) => seen;

const relayFrames = (page) => page.locator('iframe[src="newsletter-frame.html"]').count();
const SHOWN = new Set(Object.values(MESSAGES).concat(['']));

// --- Mocked scenarios --------------------------------------------------------
async function mocked(browser, base) {
  const replies = [
    ['success, double opt-in', { result: 'success', msg: 'Almost finished... We need to confirm your email address. To complete the subscription process, please click the link in the email we just sent you.' }, MESSAGES.confirm, true],
    ['success, single opt-in', { result: 'success', msg: 'Thank you for subscribing!' }, MESSAGES.subscribed, true],
    ['already subscribed, profile updated', { result: 'success', msg: "You're already subscribed, your profile has been updated. Thank you!" }, MESSAGES.already, true],
    ['already subscribed', { result: 'error', msg: 'reader@example.org is already subscribed to list Circular Textile Alliance. <a href="https://circulartextilealliance.us16.list-manage.com/subscribe/send-email?u=x">Click here to update your profile</a>' }, MESSAGES.already, true],
    ['too many attempts', { result: 'error', msg: 'Too many subscribe attempts for this email address. Please try again in about 5 minutes. (#4567)' }, MESSAGES.tooMany, false],
    ['invalid address', { result: 'error', msg: '0 - The domain portion of the email address is invalid (the portion after the @: nowhere)' }, MESSAGES.invalid, false],
    ['looks fake', { result: 'error', msg: 'This email address looks fake or invalid. Please enter a real email address.' }, MESSAGES.invalid, false],
    ['empty address', { result: 'error', msg: '0 - Please enter a value' }, MESSAGES.invalid, false],
    ['captcha requested', { result: 'error', msg: 'captcha' }, MESSAGES.captcha, false],
    ['unrecognised answer', { result: 'error', msg: 'This email cannot be added to this list. Please enter a different email address.' }, MESSAGES.unknown, false],
  ];

  for (const [label, payload, expected, clears] of replies) {
    for (const form of FORMS) {
      const seen = [];
      const { context, page, csp } = await openPage(browser, base, {
        route: (route) => {
          seen.push(route.request().url());
          route.fulfill({ status: 200, contentType: 'application/javascript', body: jsonpBody(route.request().url(), payload) });
        },
      });
      await submit(page, form, '  reader@example.org ');
      const shown = await waitForStatus(page, form, expected);
      ok(shown, `${label} [${form}] → "${expected}"`, 'status was: ' + (await statusOf(page, form).textContent()));
      const field = await page.inputValue(form + ' .newsletter__input');
      ok(clears ? field === '' : field === 'reader@example.org', `${label} [${form}] field ${clears ? 'cleared' : 'kept (trimmed)'}`, 'field: ' + JSON.stringify(field));
      if (form === FORMS[0] && label === replies[0][0] && seen.length) {
        const u = new URL(seen[0]);
        ok(u.pathname === '/subscribe/post-json', 'JSONP goes to /subscribe/post-json', u.pathname);
        ok(u.searchParams.get('u') === U && u.searchParams.get('id') === ID && u.searchParams.get('f_id') === '00fcc2e1f0',
          'JSONP carries the audience (u, id, f_id)', u.search);
        ok(u.searchParams.get('EMAIL') === 'reader@example.org', 'JSONP sends the trimmed address as EMAIL', u.searchParams.get('EMAIL'));
        ok(u.searchParams.get(TRAP) === '', 'JSONP sends the empty bot trap', String(u.searchParams.get(TRAP)));
        ok(/^relay\d+$/.test(u.searchParams.get('c') || ''), 'JSONP names its callback with c=', u.searchParams.get('c'));
        const other = FORMS[1];
        ok((await statusOf(page, other).textContent()) === '', 'the other form is untouched');
        ok((await relayFrames(page)) === 0, 'the relay frame is removed once it has answered');
        ok((await page.locator('script[src*="list-manage"]').count()) === 0, 'no Mailchimp script ever enters the page itself');
      }
      ok(seen.length === 1, `${label} [${form}] exactly one request`, String(seen.length));
      const text = await statusOf(page, form).textContent();
      ok(SHOWN.has(text), `${label} [${form}] shows only the site's own copy`, text);
      const v = await cspViolations(page, csp);
      ok(v.length === 0, `${label} [${form}] no CSP violation`, v.join(' | '));
      await context.close();
    }
  }

  // A hostile reply runs sealed inside the sandboxed relay: no page, no
  // storage, no cookies — and what it says is never shown.
  {
    const probe = `(function () {
      var r = {};
      try { parent.document.body.setAttribute('data-pwned', '1'); r.parent = 'reached'; } catch (e) { r.parent = e.name; }
      try { localStorage.setItem('pwned', '1'); r.storage = 'written'; } catch (e) { r.storage = e.name; }
      try { r.cookie = document.cookie; } catch (e) { r.cookie = e.name; }
      try { r.top = top.location.href; } catch (e) { r.top = e.name; }
      r.origin = String(self.origin);
      CALLBACK({ result: 'success', msg: '<img src=x onerror=alert(1)>' + JSON.stringify(r) });
    })();`;
    const { context, page, csp } = await openPage(browser, base, {
      route: (route) => route.fulfill({
        status: 200, contentType: 'application/javascript',
        body: probe.replace('CALLBACK', new URL(route.request().url()).searchParams.get('c')),
      }),
    });
    await page.evaluate(() => {
      window.__replies = [];
      window.addEventListener('message', (e) => { if (e.data && e.data.relay === 'reply') window.__replies.push(e.data.msg); });
      localStorage.setItem('mine', 'kept');
    });
    await submit(page, FORMS[0], 'reader@example.org');
    ok(await waitForStatus(page, FORMS[0], MESSAGES.subscribed), 'hostile reply: the page shows only its own copy', await statusOf(page, FORMS[0]).textContent());
    const said = await page.evaluate(() => window.__replies[0] || '');
    const r = JSON.parse(said.slice(said.indexOf('{')) || '{}');
    console.log('        inside the relay: ' + JSON.stringify(r));
    ok(r.parent === 'SecurityError', 'hostile reply: cannot touch the page', r.parent);
    ok(r.storage === 'SecurityError', 'hostile reply: has no storage of its own to reach', r.storage);
    // Chromium throws; other engines may hand an opaque origin an empty jar.
    ok(r.cookie === 'SecurityError' || r.cookie === '', 'hostile reply: has no cookies to read', r.cookie);
    ok(r.top === 'SecurityError', 'hostile reply: cannot read where the visitor is', r.top);
    ok(r.origin === 'null', 'hostile reply: runs in an opaque origin', r.origin);
    ok((await page.evaluate(() => document.body.getAttribute('data-pwned'))) === null, 'hostile reply: page DOM untouched');
    ok((await page.evaluate(() => [localStorage.getItem('pwned'), localStorage.getItem('mine')].join())) === ',kept', 'hostile reply: page storage untouched');
    ok((await page.locator(FORMS[0] + ' .newsletter__status *').count()) === 0, 'hostile reply: no markup reaches the status line');
    ok((await cspViolations(page, csp)).length === 0, 'hostile reply: no CSP violation');
    await context.close();
  }

  // Client-side validation never contacts Mailchimp.
  for (const bad of ['', '   ', 'not-an-email', 'two@@signs.org']) {
    let contacted = 0;
    const { context, page } = await openPage(browser, base, { route: (r) => { contacted++; r.abort(); } });
    await submit(page, FORMS[1], bad);
    ok(await waitForStatus(page, FORMS[1], MESSAGES.invalid), `validation: ${JSON.stringify(bad)} → "${MESSAGES.invalid}"`);
    ok(contacted === 0, `validation: ${JSON.stringify(bad)} made no request`, String(contacted));
    ok(await page.evaluate((f) => document.activeElement === document.querySelector(f + ' .newsletter__input'), FORMS[1]),
      `validation: ${JSON.stringify(bad)} returns focus to the field`);
    await context.close();
  }

  // A second press while the first request is in flight is ignored.
  {
    const held = [];
    const { context, page } = await openPage(browser, base, { route: (r) => held.push(r) });
    await submit(page, FORMS[0], 'reader@example.org');
    ok(await waitForStatus(page, FORMS[0], MESSAGES.sending), 'in flight → "' + MESSAGES.sending + '"');
    ok((await page.getAttribute(FORMS[0], 'aria-busy')) === 'true', 'in flight → form is aria-busy');
    ok(await page.evaluate((f) => document.querySelector(f + ' .newsletter__input').readOnly, FORMS[0]), 'in flight → the field is read-only');
    await page.click(FORMS[0] + ' .newsletter__submit');
    await page.press(FORMS[0] + ' .newsletter__input', 'Enter');
    await page.waitForTimeout(300);
    ok(held.length === 1, 'double submit sends one request', String(held.length));
    await held[0].fulfill({ status: 200, contentType: 'application/javascript', body: jsonpBody(held[0].request().url(), { result: 'success', msg: 'Thank you for subscribing!' }) });
    ok(await waitForStatus(page, FORMS[0], MESSAGES.subscribed), 'held request completes');
    ok((await page.getAttribute(FORMS[0], 'aria-busy')) === null, 'aria-busy cleared afterwards');
    ok(!(await page.evaluate((f) => document.querySelector(f + ' .newsletter__input').readOnly, FORMS[0])), 'the field is editable again afterwards');
    await context.close();
  }

  // Unreachable, captcha, a reply that never calls back, and a timeout all
  // hand the next press to Mailchimp's hosted page.
  const fallbacks = [
    ['unreachable', (r) => r.abort('internetdisconnected'), MESSAGES.offline],
    ['captcha requested', (r) => r.fulfill({ status: 200, contentType: 'application/javascript', body: jsonpBody(r.request().url(), { result: 'error', msg: 'captcha' }) }), MESSAGES.captcha],
    ['unrecognised answer', (r) => r.fulfill({ status: 200, contentType: 'application/javascript', body: jsonpBody(r.request().url(), { result: 'error', msg: 'Something else entirely' }) }), MESSAGES.unknown],
    ['no callback in reply', (r) => r.fulfill({ status: 200, contentType: 'application/javascript', body: '/* not jsonp */' }), MESSAGES.offline],
  ];
  for (const [label, jsonpHandler, expected] of fallbacks) {
    const posts = [];
    const jsonp = [];
    const { context, page, csp } = await openPage(browser, base, {
      route: (route) => {
        const req = route.request();
        if (req.method() === 'POST') {
          posts.push(req.postData() || '');
          return route.fulfill({ status: 200, contentType: 'text/html', body: '<!doctype html><title>Mailchimp</title>hosted page' });
        }
        jsonp.push(req.url());
        return jsonpHandler(route);
      },
    });
    await submit(page, FORMS[1], 'reader@example.org');
    ok(await waitForStatus(page, FORMS[1], expected), `${label} → "${expected}"`, await statusOf(page, FORMS[1]).textContent());
    // A double click: the first press hands off, the second must do nothing.
    const [popup] = await Promise.all([
      context.waitForEvent('page', { timeout: 5000 }).catch(() => null),
      page.dblclick(FORMS[1] + ' .newsletter__submit'),
    ]);
    if (popup) await popup.waitForLoadState().catch(() => {});
    await page.waitForTimeout(300);
    ok(popup && popup.url().startsWith(HOST + '/subscribe/post?'), `${label} → next press opens the hosted page in a new tab`, popup ? popup.url() : 'no popup');
    ok(context.pages().length === 2 && posts.length === 1 && jsonp.length === 1,
      `${label} → a double press opens one tab and sends nothing else`, `pages=${context.pages().length} posts=${posts.length} jsonp=${jsonp.length}`);
    const body = new URLSearchParams(posts[0] || '');
    ok(body.get('EMAIL') === 'reader@example.org' && body.get(TRAP) === '', `${label} → hosted page receives EMAIL and the empty trap`, posts[0]);
    ok(await waitForStatus(page, FORMS[1], MESSAGES.handoff), `${label} → status says so`);
    ok(popup && (await popup.evaluate(() => window.opener)) === null, `${label} → hosted page gets no window.opener`);
    ok((await cspViolations(page, csp)).length === 0, `${label} → no CSP violation`);
    await context.close();
  }

  // Timeout, on a fake clock rather than 15 real seconds. A success that
  // arrives late still counts — unless the visitor has acted on the fallback.
  for (const actFirst of [false, true]) {
    const held = [];
    const posts = [];
    const { context, page } = await openPage(browser, base, {
      clock: true,
      route: (r) => {
        if (r.request().method() === 'POST') {
          posts.push(r.request().postData());
          return r.fulfill({ status: 200, contentType: 'text/html', body: '<!doctype html><title>Mailchimp</title>hosted page' });
        }
        held.push(r);
      },
    });
    const tag = actFirst ? 'timeout, then handoff' : 'timeout';
    await submit(page, FORMS[0], 'reader@example.org');
    ok(await waitForStatus(page, FORMS[0], MESSAGES.sending), `${tag}: request pending`);
    await page.waitForFunction(() => document.querySelector('iframe[src="newsletter-frame.html"]'));
    await page.waitForTimeout(300);   // the relay announces itself in real time
    await page.clock.runFor(14000);
    ok((await statusOf(page, FORMS[0]).textContent()) === MESSAGES.sending, `${tag}: still waiting at 14 s`);
    await page.clock.runFor(1500);
    ok(await waitForStatus(page, FORMS[0], MESSAGES.offline), `${tag}: gives up at 15 s → "${MESSAGES.offline}"`);
    if (actFirst) {
      await Promise.all([context.waitForEvent('page', { timeout: 5000 }).catch(() => null), page.click(FORMS[0] + ' .newsletter__submit')]);
      ok(await waitForStatus(page, FORMS[0], MESSAGES.handoff), `${tag}: the visitor finishes on Mailchimp`);
    }
    await held[0].fulfill({ status: 200, contentType: 'application/javascript', body: jsonpBody(held[0].request().url(), { result: 'success', msg: 'Thank you for subscribing!' }) });
    await page.waitForTimeout(300);
    const after = await statusOf(page, FORMS[0]).textContent();
    if (actFirst) {
      ok(after === MESSAGES.handoff, `${tag}: a late success changes nothing once they have`, after);
    } else {
      ok(after === MESSAGES.subscribed, `${tag}: a late success still counts`, after);
      ok((await page.inputValue(FORMS[0] + ' .newsletter__input')) === '', `${tag}: and clears the field`);
    }
    await context.close();
  }

  // A relay frame that never starts (blocked, or its script refused) gives up
  // after 4 s, not 15.
  {
    let contacted = 0;
    const { context, page } = await openPage(browser, base, {
      clock: true,
      frame: (r) => r.fulfill({ status: 200, contentType: 'text/html', body: '<!doctype html><title>silent</title>' }),
      route: (r) => { contacted++; r.abort(); },
    });
    await submit(page, FORMS[1], 'reader@example.org');
    ok(await waitForStatus(page, FORMS[1], MESSAGES.sending), 'silent relay: request pending');
    await page.clock.runFor(3500);
    ok((await statusOf(page, FORMS[1]).textContent()) === MESSAGES.sending, 'silent relay: still waiting at 3.5 s');
    await page.clock.runFor(1000);
    ok(await waitForStatus(page, FORMS[1], MESSAGES.offline), `silent relay: gives up at 4 s → "${MESSAGES.offline}"`);
    ok(contacted === 0, 'silent relay: Mailchimp was never contacted', String(contacted));
    await context.close();
  }

  // The relay is sandboxed to scripts only, and the page itself runs no
  // third-party script: its CSP refuses Mailchimp's endpoint outright.
  {
    const held = [];
    const { context, page, csp } = await openPage(browser, base, { route: (r) => held.push(r) });
    await submit(page, FORMS[0], 'reader@example.org');
    await page.waitForFunction(() => document.querySelector('iframe[src="newsletter-frame.html"]'));
    const attrs = await page.evaluate(() => {
      const f = document.querySelector('iframe[src="newsletter-frame.html"]');
      return { sandbox: f.getAttribute('sandbox'), hidden: f.hidden, aria: f.getAttribute('aria-hidden') };
    });
    ok(attrs.sandbox === 'allow-scripts' && attrs.hidden && attrs.aria === 'true', 'relay frame: sandbox="allow-scripts" only, hidden', JSON.stringify(attrs));
    const blocked = await page.evaluate((host) => new Promise((resolve) => {
      const s = document.createElement('script');
      s.src = host + '/subscribe/post-json?c=x';
      s.onload = () => resolve(false);
      s.onerror = () => resolve(true);
      document.head.appendChild(s);
    }), HOST);
    await page.waitForTimeout(200);
    ok(blocked && held.length === 1, "the page's own CSP refuses Mailchimp's endpoint", `blocked=${blocked} requests=${held.length}`);
    ok(csp.some((x) => /script-src/.test(x)), 'that refusal is a script-src violation', csp.join(' | '));
    await context.close();
  }

  // Without script: the browser validates, then posts to the hosted page.
  {
    const posts = [];
    const { context, page } = await openPage(browser, base, {
      js: false,
      route: (route) => {
        posts.push(route.request().postData() || '');
        route.fulfill({ status: 200, contentType: 'text/html', body: '<!doctype html><title>Mailchimp</title>hosted page' });
      },
    });
    await page.fill(FORMS[0] + ' .newsletter__input', 'not-an-email');
    const noPopup = await Promise.all([
      context.waitForEvent('page', { timeout: 1500 }).catch(() => null),
      page.click(FORMS[0] + ' .newsletter__submit'),
    ]);
    ok(noPopup[0] === null && posts.length === 0, 'no script: the browser refuses an invalid address');
    await page.fill(FORMS[0] + ' .newsletter__input', 'reader@example.org');
    const [popup] = await Promise.all([
      context.waitForEvent('page', { timeout: 5000 }).catch(() => null),
      page.click(FORMS[0] + ' .newsletter__submit'),
    ]);
    if (popup) await popup.waitForLoadState().catch(() => {});
    ok(popup && popup.url().startsWith(HOST + '/subscribe/post?u=' + U + '&id=' + ID), 'no script: posts to the hosted page in a new tab', popup ? popup.url() : 'no popup');
    const body = new URLSearchParams(posts[0] || '');
    ok(body.get('EMAIL') === 'reader@example.org' && body.get(TRAP) === '', 'no script: EMAIL and the empty trap are posted', posts[0]);
    await context.close();
  }

  // Every message the script can write fits the row reserved for it, measured
  // in the real typeface (the fallback is narrower, so it must have loaded).
  // 481px is the narrowest width that still reserves a single line.
  {
    const { context, page } = await openPage(browser, base, {});
    await page.evaluate(() => document.fonts.ready);
    ok(await page.evaluate(() => document.fonts.check('400 13px Inter')), 'Inter has loaded before measuring');
    for (const width of [1440, 1024, 768, 600, 481, 480, 390, 360, 320]) {
      await page.setViewportSize({ width, height: 900 });
      // WebKit re-evaluates media queries a frame after a resize, so measure
      // only once the page agrees on the new width (and two frames have run).
      await page.waitForFunction((w) => window.innerWidth === w
        && window.matchMedia('(max-width: 30em)').matches === (w <= 480), width);
      await page.evaluate(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))));
      for (const form of FORMS) {
        const overflow = await page.evaluate(([f, texts]) => {
          const el = document.querySelector(f + ' .newsletter__status');
          const reserved = parseFloat(getComputedStyle(el).minHeight);
          const bad = [];
          for (const t of texts) {
            el.textContent = t;
            const h = el.getBoundingClientRect().height;
            if (h > reserved + 0.5) bad.push(Math.round(h) + 'px > ' + reserved + 'px: ' + t);
          }
          el.textContent = '';
          return bad;
        }, [form, Object.values(MESSAGES)]);
        ok(overflow.length === 0, `every message fits the status row at ${width}px [${form}]`, overflow.join('\n        '));
      }
    }
    // The trap is in the form but off-canvas, and adds no horizontal scroll.
    await page.setViewportSize({ width: 375, height: 800 });
    const trap = await page.evaluate((name) => {
      const input = document.querySelector('input[name="' + name + '"]');
      const r = input.getBoundingClientRect();
      return { right: r.right, scroll: document.documentElement.scrollWidth, client: document.documentElement.clientWidth };
    }, TRAP);
    ok(trap.right < 0, 'bot trap sits off-canvas', JSON.stringify(trap));
    ok(trap.scroll <= trap.client, 'bot trap adds no horizontal scroll', JSON.stringify(trap));
    await context.close();
  }
}

// --- Live scenarios ----------------------------------------------------------
// The live address must be one Mailchimp REFUSES, so a live run can never add
// a contact. Two things that looked safe were not: Mailchimp accepted
// newsletter-smoke-test@circulartextilealliance.invalid (single opt-in, first
// run), and a filled bot trap still came back "profile updated". An address
// with no top-level domain fails Mailchimp's own syntax check while passing
// the browser's, and the test fails loudly if Mailchimp ever accepts it.
const LIVE_ADDRESS = 'newsletter-smoke-test@localhost';
const LIVE_TRAP = 'smoke-test';

// Log every request to Mailchimp's host, with redirects and failures, so a
// failing run says why.
function traceMailchimp(context) {
  const lines = [];
  context.on('request', (r) => {
    if (!r.url().includes('list-manage.com')) return;
    const from = r.redirectedFrom();
    lines.push(`→ ${r.method()} ${r.url()}${from ? ' (redirected from ' + from.url() + ')' : ''}`);
  });
  context.on('response', async (r) => {
    if (!r.url().includes('list-manage.com')) return;
    const h = r.headers();
    lines.push(`← ${r.status()} ${r.url().slice(0, 100)} type=${h['content-type'] || ''}${h.location ? ' location=' + h.location : ''}`);
  });
  context.on('requestfailed', (r) => {
    if (r.url().includes('list-manage.com')) lines.push(`✗ ${r.url().slice(0, 120)} ${r.failure() && r.failure().errorText}`);
  });
  return lines;
}

async function live(browser, base) {
  const quiet = new Set([MESSAGES.sending, MESSAGES.offline, '']);
  // An ordinary desktop Chrome, not "HeadlessChrome": Mailchimp's bot
  // protection resets a headless browser's form post (ERR_HTTP2_PROTOCOL_ERROR).
  const userAgent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/'
    + browser.version() + ' Safari/537.36';

  {
    const { context, page, csp } = await openPage(browser, base, { userAgent });
    const trace = traceMailchimp(context);
    const replies = [];
    page.on('response', async (r) => {
      if (r.url().startsWith(HOST + '/subscribe/post-json')) {
        replies.push({ status: r.status(), type: r.headers()['content-type'], body: await r.text().catch(() => '') });
      }
    });
    await page.fill(FORMS[0] + ' input[name="' + TRAP + '"]', LIVE_TRAP, { force: true });
    await submit(page, FORMS[0], LIVE_ADDRESS);
    await page.waitForFunction((f) => {
      const t = document.querySelector(f + ' .newsletter__status').textContent;
      return t && t !== 'Subscribing…';
    }, FORMS[0], { timeout: 20000 }).catch(() => {});
    const shown = await statusOf(page, FORMS[0]).textContent();
    console.log('        trace:\n          ' + trace.join('\n          '));
    console.log('        Mailchimp replied: ' + JSON.stringify(replies));
    console.log('        status line: ' + JSON.stringify(shown));
    const sentTrap = trace.find((l) => l.includes('/subscribe/post-json')) || '';
    ok(sentTrap.includes(TRAP + '=' + LIVE_TRAP), 'live: the request carried the filled bot trap', sentTrap);
    ok(replies.length === 1 && replies[0].status === 200, 'live: the JSONP request reached Mailchimp and was answered');
    const result = ((replies[0] || {}).body || '').match(/"result":"(\w+)"/);
    ok(result && result[1] === 'error',
      'live: Mailchimp refused the smoke-test address (if this fails, Mailchimp ACCEPTED it — remove ' + LIVE_ADDRESS + ' from the audience)',
      result ? result[1] : 'no result');
    ok(/^relay\d+\(/.test((replies[0] || {}).body || ''), 'live: the answer is JSONP for our callback');
    ok(!quiet.has(shown) && SHOWN.has(shown), 'live: Mailchimp’s answer reached the status line', shown);
    const v = await cspViolations(page, csp);
    ok(v.length === 0, 'live: no CSP violation', v.join(' | '));
    await context.close();
  }

  // Mailchimp's bot protection resets a *headless* browser's form post
  // (ERR_HTTP2_PROTOCOL_ERROR) whatever its user agent says — headless
  // Chromium still announces itself in its client hints — while a plain
  // HTTP/1.1 post from the same origin gets the page. So the hosted-page checks
  // run headed when there is a display (CI wraps the live run in xvfb-run).
  const headed = process.env.DISPLAY ? await chromium.launch({ headless: false }) : null;
  const hostBrowser = headed || browser;
  console.log(`        hosted-page checks run ${headed ? 'headed (DISPLAY=' + process.env.DISPLAY + ')' : 'headless — expect Mailchimp to reset the post'}`);

  for (const js of [false, true]) {
    // The hosted page, reached two ways: a no-script post, and the fallback
    // after the relay is made to fail (its frame never starts).
    const tag = js ? 'live, fallback' : 'live, no script';
    const { context, page, csp } = await openPage(hostBrowser, base, js
      ? { userAgent, frame: (r) => r.fulfill({ status: 200, contentType: 'text/html', body: '<!doctype html><title>silent</title>' }) }
      : { userAgent, js: false });
    const trace = traceMailchimp(context);
    await page.fill(FORMS[1] + ' input[name="' + TRAP + '"]', LIVE_TRAP, { force: true });
    if (js) {
      await submit(page, FORMS[1], LIVE_ADDRESS);
      await waitForStatus(page, FORMS[1], MESSAGES.offline, 8000);
    } else {
      await page.fill(FORMS[1] + ' .newsletter__input', LIVE_ADDRESS);
    }
    const [popup] = await Promise.all([
      context.waitForEvent('page', { timeout: 10000 }).catch(() => null),
      page.click(FORMS[1] + ' .newsletter__submit'),
    ]);
    let landed = '';
    if (popup) {
      await popup.waitForLoadState('domcontentloaded', { timeout: 20000 }).catch(() => {});
      await popup.waitForTimeout(1000);
      landed = popup.url();
      const text = (await popup.locator('body').innerText().catch(() => '')).replace(/\s+/g, ' ').slice(0, 400);
      console.log(`        [${tag}] hosted page: ${landed}\n        says: ${JSON.stringify(text)}`);
    }
    console.log(`        [${tag}] trace:\n          ` + trace.join('\n          '));
    const posted = trace.find((l) => l.startsWith('→ POST')) || '';
    ok(posted.includes('/subscribe/post?u=' + U), `${tag}: the form posts to Mailchimp's hosted signup`, posted);
    ok(csp.length === 0, `${tag}: no CSP violation`, csp.join(' | '));
    // Asserted headed, or against a deployed copy; headless it is only
    // reported, since there Mailchimp refuses the browser, not the site.
    const landedOk = /^https:\/\/[^/]*list-manage\.com\//.test(landed);
    if (REMOTE_BASE || headed) ok(landedOk, `${tag}: the new tab shows Mailchimp's page`, landed);
    else console.log(`        note: [${tag}] Mailchimp's page ${landedOk ? 'loaded' : 'did not load (' + landed + ')'} headless; run under a display to check what visitors get`);
    await context.close();
  }
  if (headed) await headed.close();

  await diagnose(base);
}

// Printed, never asserted: how Mailchimp answers the hosted post depending on
// the Origin it sees and the HTTP version. Plain HTTP/1.1 requests from Node,
// not a browser, with no redirects followed.
async function diagnose(base) {
  const api = await apiRequest.newContext();
  const action = HOST + '/subscribe/post?u=' + U + '&id=' + ID + '&f_id=00fcc2e1f0';
  const form = { EMAIL: LIVE_ADDRESS, [TRAP]: LIVE_TRAP };
  for (const origin of ['', base, 'https://cportka.github.io']) {
    const headers = origin ? { Origin: origin, Referer: origin + '/' } : {};
    try {
      const r = await api.post(action, { form, headers, maxRedirects: 0, timeout: 15000 });
      const body = (await r.text()).replace(/\s+/g, ' ');
      const title = (body.match(/<title>([^<]*)/i) || [])[1] || '';
      console.log(`        diagnose: Origin ${origin || '(none)'} → ${r.status()} ${r.headers()['content-type'] || ''}${r.headers().location ? ' location=' + r.headers().location : ''} title=${JSON.stringify(title.trim())}`);
    } catch (e) {
      console.log(`        diagnose: Origin ${origin || '(none)'} → ${String(e.message).split('\n')[0]}`);
    }
  }
  await api.dispose();
}

(async () => {
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  const base = 'http://127.0.0.1:' + server.address().port;
  // Mocked runs must never reach the internet: anything a route doesn't
  // answer goes to a dead proxy and fails, instead of quietly reaching the real
  // Mailchimp (in Firefox, once, a route missed the sandboxed frame's request).
  // (Playwright sends Chromium's loopback through the proxy unless told not to.)
  process.env.PLAYWRIGHT_DISABLE_FORCED_CHROMIUM_PROXIED_LOOPBACK = '1';
  const browser = await (LIVE ? chromium : playwright[ENGINE]).launch(LIVE ? {} : {
    proxy: { server: 'http://127.0.0.1:9', bypass: '127.0.0.1,localhost' },
  });
  try {
    console.log(LIVE ? 'newsletter — live against Mailchimp' : 'newsletter — mocked Mailchimp, ' + ENGINE + ' ' + browser.version());
    await (LIVE ? live : mocked)(browser, LIVE && REMOTE_BASE ? REMOTE_BASE : base);
  } finally {
    await browser.close();
    server.close();
  }
  console.log(`\n${passes} passed, ${failures} failed`);
  process.exit(failures ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
