# Security policy

## What this site is

The Circular Textile Alliance site — served at
`https://cportka.github.io/circular-textile-alliance-org/` until it moves to
`circulartextilealliance.org` — is a **static** site: hand-authored HTML, CSS and
two small progressive-enhancement scripts, served by GitHub Pages. There is no
backend, no database, no authentication, no session state and no user accounts.
No personal data is collected, stored or processed by the site itself; the one
thing a visitor can choose to send anywhere is an email address to the
newsletter, which goes to Mailchimp (below).

## Third-party requests

**Browsing: none.** Every byte a visitor loads while reading comes from this
origin. **Subscribing: Mailchimp**, and only after someone presses Subscribe.

| Host | When | What it receives | CSP source |
| :-- | :-- | :-- | :-- |
| `circulartextilealliance.us16.list-manage.com` (Intuit Mailchimp) | a visitor presses **Subscribe** on the home page | the address typed, Mailchimp's empty bot-trap field, and what every request carries (IP address, user agent, this site's origin as referrer) | `form-action` the host, on `index.html` (the no-script post); scripts only inside the sandboxed `newsletter-frame.html` (the JSONP reply) |

**Why the newsletter runs in a sandboxed frame.** Mailchimp sends no CORS
headers, so the only way to read its answer in-page is JSONP — a reply that is
a *script*, and runs with the full rights of whatever document loads it. This
site is served from `https://cportka.github.io`, an origin it shares with every
other Pages site on that account, so a hostile or compromised reply loaded into
a page here could read those sites' pages and storage. So no page loads it:

- Each request goes through `newsletter-frame.html`, framed by `site.js` with
  `sandbox="allow-scripts"` and nothing else. Without `allow-same-origin` the
  frame's origin is opaque: a reply running there gets `SecurityError` on the
  page, on storage, on cookies and on `top.location` (the browser test proves
  each). The frame is created on Subscribe and removed once it has answered.
- The frame's own policy is `default-src 'none'; script-src *` — it can load
  scripts and fetch, frame or submit nothing else. The script list is open on
  purpose: WebKit (Safari) does not match `'self'` inside a sandboxed frame, so
  a tighter list refused the relay's own script and Safari never used it. The
  sandbox, not the script list, is what contains Mailchimp's reply.
- The pages' policies admit **no third-party script at all**. `index.html`
  adds only `form-action` for the no-script post, by host because paths stop
  counting after a redirect.
- The frame and the page trust each other only by `event.source`. What comes
  back is a message, and Mailchimp's wording in it is only *matched* against
  known answers to pick one of the site's own fixed messages; it is never
  parsed or shown. The suite fails if either script gains an HTML sink
  (`innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `eval`,
  `new Function`, `createContextualFragment`, `setHTMLUnsafe`,
  `parseHTMLUnsafe`, `srcdoc`, `DOMParser`).
- With script off, if the frame doesn't start within 4 s, if Mailchimp doesn't
  answer within 15 s, or if it answers with anything unrecognised, the form is a
  plain post to Mailchimp's hosted page in a new tab (`rel="noopener"`), which
  runs nothing here.

The browser test runs every newsletter path in Chromium, Firefox and WebKit,
and its mocked runs are sealed off from the network so a missed mock can never
reach the real Mailchimp. If a browser ever refuses the relay anyway, the 4 s
fallback hands the visitor to Mailchimp's own page.

Fonts are self-hosted, so no request reaches Google Fonts or any other font CDN.
Photography is the alliance's own, served from `assets/img/photos/`. There is no
analytics, no tag manager, no tracking pixel and no cookie of any kind — the
site sets none and needs no consent banner.

`img-src` in the Content-Security-Policy is `'self'`. The test suite fails
the build if any page fetches a subresource (`src`, or `href` on `<link>` /
`<script>`) from a remote host, or if any page's policy names a remote source
beyond the newsletter's `form-action`, so this cannot regress unnoticed.

A Content-Security-Policy is declared in the page head. It permits no inline
styles or scripts and no origin other than the site itself, save that one
`form-action`. A CSP delivered as a
response header is stronger than one in a `<meta>` tag; if this site later moves
behind a CDN or a host that can set headers, promote it (and add
`frame-ancestors`, which a meta-delivered CSP ignores).

## Reporting a vulnerability

Please report privately through GitHub Security Advisories:

**<https://github.com/cportka/circular-textile-alliance-org/security/advisories/new>**

Do not open a public issue for a security report. Expect an acknowledgement
within a few working days.

Machine-readable contact details are published at
[`/.well-known/security.txt`](./.well-known/security.txt) per RFC 9116.

## Scope

In scope: anything served from this repository — the markup, stylesheet,
scripts, fonts and images — and the GitHub Actions workflows that validate and
publish them. What is served is exactly what `scripts/stage-site.sh` stages.

Out of scope: vulnerabilities that require a compromised GitHub account or a
modified local clone.
