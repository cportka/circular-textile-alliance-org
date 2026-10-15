# circular-textile-alliance-org

> **Version:** 0.15.4 · **Design:** [Figma Make — Redesign Institutional Website](https://www.figma.com/make/pYrwXChqTORzVAjL3X3DI5/Redesign-Institutional-Website) · **Security:** [SECURITY.md](./SECURITY.md) · **Changelog:** [CHANGELOG.md](./CHANGELOG.md)

The website for the **Circular Textile Alliance** — a static, single-page
institutional site built from the Figma design above, published to GitHub Pages
by an Actions workflow on every push to `main`.

No build step, no framework, no package manager. `index.html` is the site; open
it and you are looking at production.

---

## Layout of the repository

```
index.html                 the home page — eight sections
publications.html          Reports & Publications — the full library
news.html                  News — the full list
404.html                   styled not-found page
newsletter-frame.html      sandboxed relay for the newsletter's Mailchimp JSONP (never shown)
assets/
  css/site.css             every style, including the @font-face block
  js/site.js               progressive enhancement only (header state, menu, dialogs, newsletter)
  js/newsletter-frame.js   the relay's script — the only code that talks to Mailchimp
  fonts/*.woff2            self-hosted Inter + Playfair Display (SIL OFL, licences alongside)
  img/                     logo, favicon, app icons, Open Graph card
  img/photos/*.webp        the alliance's own photography (see below)
site.webmanifest           PWA/install metadata
robots.txt  sitemap.xml    crawler metadata
llms.txt                   plain-language site map for AI crawlers
.well-known/security.txt   RFC 9116 security contact
scripts/stage-site.sh      copies exactly the public files into _site/ for the deploy
tests/                     the check suite CI runs (see below)
```

## Running it locally

Any static file server will do — the page uses relative paths throughout:

```sh
npx http-server -p 8099 -o        # -o opens your browser at the site
```

`Ctrl-C` stops it. `-o` matters: a server on its own never opens a window, so
without it nothing appears to happen. Avoid `-s` (silent) here too — it
suppresses the "Available on: …" line, leaving no clue the server started.

Opening `index.html` directly off the filesystem mostly works, but the
Content-Security-Policy and the web manifest behave differently under `file://`,
so prefer the server.

## Tests

```sh
bash tests/run-tests.sh
```

1,000+ assertions, stdlib Python only, no browser and no network — so the same
command runs locally, in CI (`.github/workflows/validate.yml`, on every push and
pull request) and as the gate in front of every deploy. Eight suites live in
`tests/cases/`, backed by `tests/lib/`:

| Suite | What it holds to account |
| :-- | :-- |
| `html-structure` | **every tag closes the element it opened** — the suite's own parser repairs mismatches the way a browser does, so a stray `</div>` went unnoticed for three releases while it closed `.wrap` early and pushed two sections outside it; this check parses strictly instead. Also one `<h1>`, one `<main>`, heading levels never skip, every section anchor and its `aria-labelledby` exist, design copy still present, **no inline `style`/`<script>`** (which the CSP would silently drop) |
| `links-assets` | every local `href`/`src` and every `url()` in the CSS resolves to a real file, every `#anchor` has a target, no `href="#"` survives, shipped fonts and referenced fonts agree, licences present. A photo **referenced but missing** fails; a photo **committed but unreferenced** is a library shot, so it only reports its weight in the published artifact |
| `accessibility` | alt attributes, labelled form controls, named buttons, ARIA references that point at real ids, disclosure state, unique nav labels, skip link, live region, decorative layers hidden, reduced-motion and focus styling |
| `contrast` | every text/background pair in the design measured against WCAG AA, translucent colours composited first, control boundaries against 1.4.11's 3:1, plus a regression guard on the three retuned tokens |
| `components` | **every `<img>` declares the shape of the file it loads** — width/height are read against the file's real size, so replacing an image at a new aspect ratio fails until the markup follows. **Every class in the markup has a rule in `site.css`** — a deletion that orphans a class is how the 404 lede lost its type in 0.4.0. Plus guards for UI bugs that shipped once: the header CTA's hover rules exist per header state (a specificity trap made the label invisible), the newsletter field is isolated from its status message, the status row reserves its height, and the logo keeps its dash-gap interlock and gradients — with `favicon.svg`'s geometry pinned to `logo.svg`'s. Also that the hero's statement band stays off the photograph, which is what makes its measured contrast the rendered contrast |
| `workflows` | the workflows still trigger where they should and keep their `workflow_dispatch` escape hatch; `validate` **fails closed** with a read-only token; Pages deploy rights sit on the deploy job alone, which publishes only from `main`; the deploy **validates, stages, then uploads** `_site` with dot-paths included; no checkout leaves its token on disk; every action is on its Node 24 major |
| `staging` | runs `scripts/stage-site.sh` and checks **what would actually be published**: every page and `.well-known/security.txt` present, no README/CHANGELOG/tests/scripts/bytecode, and every local reference in the published pages and stylesheet resolving inside the published tree |
| `seo-metadata` | title/description lengths, canonical, full Open Graph and Twitter sets, manifest and its icons, JSON-LD parses and carries `Organization` + `WebSite`, robots/sitemap/llms.txt agree on one host, `404` is `noindex`, security.txt valid |

The newsletter signup is also tested **in real browsers** — Chromium, Firefox
and WebKit (Safari's engine) — by `tests/browser/newsletter.cjs` (Playwright;
`BROWSER=firefox|webkit` picks the engine), which
`.github/workflows/newsletter.yml` runs whenever the home page, the relay, their
scripts, `site.css` or the test itself changes, and on demand:

```sh
NODE_PATH="$(npm root -g)" node tests/browser/newsletter.cjs          # mocked Mailchimp
NODE_PATH="$(npm root -g)" node tests/browser/newsletter.cjs --live   # the real audience
NODE_PATH="$(npm root -g)" node tests/browser/newsletter.cjs --live \
  --base https://cportka.github.io/circular-textile-alliance-org         # …from the deployed site
```

Mailchimp's server treats the no-script post differently by origin — from a
local `http://127.0.0.1` test server it resets the connection — so against a
local server the live run only reports whether Mailchimp's page loaded, and
`--base` (or the workflow's `base_url` input on a manual run) is the check of
what visitors actually get.

The default mode answers Mailchimp from inside the browser and walks every
outcome — success with and without double opt-in, already subscribed, too many
attempts, invalid, captcha, an unrecognised answer, unreachable, no callback, a
relay that never starts and a timeout (both on a fake clock), a late success,
double submits and double presses after a handoff, both forms independently,
the no-script form — with zero CSP violations in any frame. A hostile reply is
run inside the relay to prove the sandbox holds (no page, storage, cookies or
`top`), and every message the script can write is measured against the status
row at nine widths, in the loaded typeface. `--live` runs the real
round trip against the audience — the relay, the no-script post, and the
fallback post — with an address Mailchimp's own syntax check refuses
(`…@localhost`: no top-level domain, which the browser allows), and fails loudly
if Mailchimp ever accepts it. Neither an undeliverable `.invalid` address nor a
filled bot trap kept Mailchimp from processing a signup, so nothing weaker will
do. It traces every request to Mailchimp, redirects included, and presents as
ordinary desktop Chrome, since Mailchimp's bot protection resets a headless
browser's form post.

## Deployment

GitHub Pages, published **from GitHub Actions** by
`.github/workflows/pages.yml` on every push to `main`. Requires
**Settings → Pages → Source = "GitHub Actions"**.

The workflow runs `tests/run-tests.sh` *before* uploading the artifact, so a
commit that fails validation never reaches the live site — a gate the older
"deploy from a branch" path had no way to provide. It then publishes an
**allowlist**, not the repository: `scripts/stage-site.sh` copies the pages,
`assets/`, `.well-known/` and the crawler files into `_site/`, which is
uploaded with dot-paths included. (Uploading the repo root, as before 0.15.1,
published the README, CHANGELOG and tests while silently dropping
`.well-known/security.txt`.) A new top-level file or folder must be added to
the script's list to go live; the `staging` suite fails if a page is missing
from it. It can also be re-run on
demand from the Actions tab, which matters: when a run is lost to a GitHub
incident rather than to a real failure, the branch-based
`pages build and deployment` workflow cannot be retriggered at all.

**Custom domain.** The site is currently addressed as
`https://cportka.github.io/circular-textile-alliance-org/`, and that URL is
baked into the canonical link, Open Graph tags, JSON-LD, `robots.txt`,
`sitemap.xml`, `llms.txt` and `.well-known/security.txt`. To move to
`circulartextilealliance.org`, in this order — DNS last, because a domain
pointed at Pages but not yet claimed by a repository can be claimed by anyone:

1. **Verify the domain** for the account: GitHub → Settings → Pages → *Add a
   domain*, then publish the TXT record it gives you. Verification stops any
   other account from taking it over.
2. **Claim it for this repository**: the repo's Settings → Pages → *Custom
   domain*. No `CNAME` file is needed — an Actions deploy ignores one.
3. **Only then point DNS** at Pages: `A`/`AAAA` records to GitHub's apex
   addresses, a `CNAME` for `www` to `cportka.github.io`, and no wildcard.
4. Tick **Enforce HTTPS** once the certificate is issued.
5. Replace `https://cportka.github.io/circular-textile-alliance-org` with
   `https://circulartextilealliance.org` across the files listed above, and drop
   the `/circular-textile-alliance-org` prefix from the four root-absolute URLs
   in `404.html`.

Steps 1–4 are GitHub/DNS settings for the owner. The move also gives the site
an origin of its own, rather than one shared with every other
`cportka.github.io` site, and puts `security.txt` and `robots.txt` at the
origin root where scanners and crawlers look for them.

---

## Relationship to the Figma design

The design is a Figma Make project: React + Vite + Tailwind, one `App.tsx` and
eight components, styled almost entirely with inline `style` objects. That was
ported to static HTML/CSS rather than shipped as-is: the repository root *is*
the published site, so a build step would mean committing `dist/` output on
every change.

The `@theme` block in the design's `index.css` became the `:root` custom
properties in `assets/css/site.css`, one for one. Section structure, copy,
spacing, type scale and layout follow the design.

### Deliberate deviations

Every one of these is marked `DEVIATION:` at its site in the stylesheet.

**Colour contrast.** Several of the design's text colours fail WCAG AA. The
fixes keep each colour's hue and saturation and lower only its lightness, so
the palette still reads as the same palette. The undarkened brand values stay in
use for fills, rules and dots, where contrast rules do not apply.

| What | Figma | Shipped | Was | Now |
| :-- | :-- | :-- | --: | --: |
| Muted body text (`--ink-muted`) | `#6B7E7A` | `#5F6F6C` | 3.68:1 | 4.53:1 |
| Peach label text (`--peach-text`) | `#E8936A` | `#B34D1C` | 2.04:1 | 4.51:1 |
| Sage label text (`--sage-text`) | `#7EADA0` | `#4A7469` | 2.15:1 | 4.51:1 |
| *Who We Are* subheads | `#7EADA0` / `#E8936A` | `--sage-text` / `--peach-text` | 2.15:1 / 2.04:1 | 4.51:1 |
| Primary button label | cream on peach | **ink** on peach (fill unchanged) | 2.25:1 | 6.19:1 |
| Third board group | `--ink` on `--ink` | `--sage-light` | 1.00:1 | 8.02:1 |
| Footer text alphas | 0.30 / 0.35 / 0.40 / 0.45 | 0.55 / 0.60 | 2.61:1 | ≥ 4.9:1 |
| Ghost button + input borders | 0.30 / 0.20 alpha | 0.40 alpha | 2.61:1 | 3.42:1 |

**Header over the hero.** The design renders the wordmark and the nav links in
`--ink` (`#1A2B28`) on a near-black hero photograph — roughly 1.1:1, effectively
invisible. The header now starts light-on-dark and swaps to the design's
ink-on-cream once scrolled, which is the state the design already specifies.

That resting state assumes a dark hero underneath it. A page without one —
`publications.html` opens straight onto a cream section — gets
`.site-header--solid`, which is the scrolled treatment applied permanently.
Without it the cream wordmark and cream nav links paint onto cream. **Any new
page that does not open on a dark hero needs that class**, and a `components`
assertion holds `publications.html` to it.

**Dead links.** The design carries 25 links pointing at `href="#"`, which
scrolls to the top of the page. Three still read as controls (the LinkedIn
and Instagram links, and the pending Givebutter button); they render identically
but are inert `<span>`/`disabled` elements described by a shared
visually-hidden note. The rest gained real destinations as their sections gained
real content, and the footer's link lists are now genuine in-page anchors rather
than plain text. To wire one up, swap the
`<span class="ph">` for an `<a href="…">` and drop the `aria-describedby`.

**Responsive corrections.** The design sets a fixed inline
`gridTemplateColumns` that overrides the responsive class beside it on the
newsletter row (`1fr auto`), so it overflowed on a phone; it now stacks below
640px. The publications rows (`200px 1fr auto`) stack below 768px for the same
reason. (The hero stats bar had the same fault and the same fix, until the bar
itself was removed — see *Copy* below.)

**Copy.** The hero and About copy are the alliance's own, no longer the
design's. The design's hero lede, its two buttons and the four-figure stats bar
(140+ / 38 / 2.4M t / 12) are gone — those figures were placeholders, not the
alliance's numbers. In their place the hero carries the real positioning: the
headline over the photograph, then *Building a stronger, more resilient textile
economy*, the introduction, and *Our Mission* and *Our Vision* stated on the page
rather than linked to. About is now the approach section (*How We Work*) holding
the five principles. The meta description, Open Graph and Twitter descriptions,
JSON-LD and `llms.txt` were rewritten to match, since each quoted copy that no
longer exists.

**Hero is two bands, for contrast.** `.hero__stage` is the first screen and the
only place the photograph appears; `.hero__statement` below it is flat `--ink`.
That split is not cosmetic. The statement's sage subhead measures 5.90:1 on
`--ink`, but the photograph is cream at 0.22 opacity over ink, and over its
brightest areas the same text falls to **2.96:1** — a WCAG failure that no
static colour check would catch, because the colours themselves are fine. Keeping
the copy off the image is what makes the measured pairs the rendered pairs, and
the `components` suite fails if the two bands are merged again.

**Founding year.** The Figma placed the alliance's founding in 2019. The
supplied *Who We Are* copy says **2025**, so 2025 is what the page, the JSON-LD
`foundingDate`, the hero eyebrow and `llms.txt` all now say — a date stated in
four places cannot disagree with itself.

**The Givebutter button is inert.** *Contribute To Our Mission & Work* has a
heading and a control but no copy and no destination yet. Rather than publish
the literal "Tbd copy + GIVE BUTTER LINK", the control renders as a disabled
placeholder like the other 14, described by the shared visually-hidden note.
Swap the `<button>` for `<a class="btn btn--primary" href="https://givebutter.com/…">`
and drop the `aria-describedby` when the campaign page exists.

**Programs is long-form, not cards.** The Figma gave it four image cards with
region badges and tags. The supplied copy is seven areas of prose, each with its
own list, so the cards, their photography and the hairline grid are gone and the
section reads as text. `.badge`, `.tags`, `.card__meta`, `.card__region` and
`.card-grid--bleed` went with them; `.card` itself stays, because News still uses
it. The "All Programs →" placeholder went too: every area is on the page now,
so there is nowhere further to send anyone.

**Two figures are placed by name.** The Transparency & Traceability pair and the
Textile Recovery Infrastructure diagram were requested at specific positions, so
a `components` assertion holds them there — including the order of the pair,
which reads left to right.

**Members is the alliance's own copy.** The Figma's member roster — 140+
organizations in three named tiers, chips, and an "Apply for Membership" button
that went nowhere — is replaced by who can take part, the current board, why
join, the partnership philosophy and how to get involved. The section keeps its
ink ground. Headings are `--peach`, which the reference asks for and which
measures 6.21:1 on `--ink`, clearing AA for normal text and not only for the
large sizes it is used at. The board's three group markers keep the design's
peach / sage / third-tone scheme at 6.21, 5.90 and 8.02 to 1; the reference's
blue for the third is not in this palette, so `--sage-light` holds that slot as
it already did.

**Board names use CSS columns, not a grid.** Names flow down one column and into
the next, so a group of seven fills 3/2/2 rather than leaving a ragged final
row — which is what the supplied board screenshot shows.

**Publications are external, and links out are not subresources.** The four
entries in the library point at calpsc.org, anthesisgroup.com,
leginfo.legislature.ca.gov and europarl.europa.eu. That does not weaken the
same-origin claim: the site still *fetches* nothing from a third party. The
`links-assets` suite used to treat every `href` and `src` alike, so it read an
outbound link as a third-party request; it now separates the two — subresources
(`src`, and `href` on `<link>`/`<script>`) must be same-origin, while `<a href>`
may leave, must be https, and is reported.

With no descriptions, years or page counts supplied, each row's left rail names
the **host** instead. That is derived from the link rather than invented, and it
tells a reader the link leaves the site.

**Policies are dialogs, not pages.** Privacy Policy, Terms of Use and Cookie
Settings open a native `<dialog>` via `showModal()`, which supplies the
centring, backdrop, focus containment and Escape handling; only the appearance
and the animation are ours. Their text describes what this site actually does —
no cookies, no storage, no analytics, no third-party requests while browsing — which is the
same claim the `links-assets` suite enforces — save the newsletter, which
both the privacy and the cookie text name. **It has not been through a
lawyer**; treat it as an accurate technical description rather than a reviewed
legal notice.

**Bottom padding on a scroll container.** Two elements scroll — the mobile
disclosure panel and the policy dialog — and in both the closing space is a
margin on the last child, not padding on the container, since a scroll
container's bottom padding is not part of its scrollable overflow in every
engine. (This was *not* the cause of the missing border on "Become a Member",
as 0.12.0 claimed; see below. The arrangement is still the safer one.)

**The menu's CTA button is styled twice over.** `.nav-mobile nav a` is scoped to
the `<nav>` on purpose: as `.nav-mobile a` it also matched "Become a Member",
and at (0,1,1) it outranked `.btn--outline-ink` at (0,1,0), replacing the
button's bottom border with the link divider. And `.site-header
.btn--outline-ink` at (0,2,0) paints that button `--cream` for the over-hero
header, which is invisible on a cream panel — so it takes `--ink` from a
(0,3,0) rule instead. Both are held by `components` assertions.

**News and publications share one row component.** Both lists are external
links with no supplied dates, categories, descriptions or page counts, so both
use `.pubs`/`.pub`: host in the left rail, title as the link, a `Read` action
carrying an `aria-label` that names the item and its host. The News section's
photographs and the whole `.card` family went with the change — `.card`,
`.card-grid`, `.card__media`, `.card__title` and the four `.news-card__*` rules
had no markup left once Programs and News both stopped using them.

**Newsletter form.** Both forms sign up to the alliance's Mailchimp audience,
built from Mailchimp's embed code but keeping only what the audience uses — the
`EMAIL` field and Mailchimp's bot trap. The embed's stylesheet, jQuery,
`mc-validate.js`, inline styles and script, SMS/phone fields (all disabled on
the audience) and referral badge are gone; the forms keep the site's own look.

Without script, each form is a plain `POST` to Mailchimp's hosted signup page in
a new tab. With script, the same fields go to Mailchimp's `post-json` endpoint as
**JSONP** — Mailchimp sends no CORS headers, so `fetch` could not read the
answer — and the result appears in the form's own status line, always in the
site's own short copy. A JSONP reply is a script, so it never runs in the page:
`site.js` relays each request through `newsletter-frame.html` in a frame
sandboxed to `allow-scripts` alone, an opaque origin from which the reply can
reach nothing (see [SECURITY.md](./SECURITY.md) for why that matters on a shared
`github.io` origin). While a request is in flight the field is read-only and
repeat presses are ignored; success clears the field.

**Expected in private windows and with blockers.** Firefox lists
`list-manage.com` as an email tracker, so its private windows and Strict
tracking protection — and ad-blockers like uBlock Origin — block the in-page
request ("blocked because Enhanced Tracking Protection is enabled" in the
console). The block arrives within a fraction of a second, while the browser
still counts the visitor's press as fresh (transient user activation, ~5 s),
so `site.js` opens Mailchimp's own page in a new tab on that same press — a
tab the visitor opens is not blocked — and the form says "Continuing on
Mailchimp's page, in a new tab". No static-site design avoids this: any request from the
page to Mailchimp's domain is blocked, and only a server on this domain could
proxy it. Firefox's default (Standard) protection labels the request but
allows it.

Any failure within 3 s of the press — blocked, unreachable, a captcha or an
unrecognised answer — opens Mailchimp's page the same way. A slower one (the
relay not starting within 4 s, no answer within 15 s) can no longer open a
tab by itself, so the form says "Couldn't reach Mailchimp — press Subscribe to
finish there" and the next press goes through natively —
and a success that arrives late still counts unless the visitor has already
done that. The home page's CSP admits Mailchimp's host for `form-action` only;
the relay's admits scripts and nothing else; the other pages keep
`form-action 'none'`. The audience is named in places that must change together:
both forms' `action`, the trap field's `name`, the host in `index.html`'s
`form-action`, and the host in `newsletter-frame.js`.

**Fonts.** The design loads Inter and Playfair Display from
`static.figma.com`, which is not a public font CDN. Both are SIL OFL, so they
are self-hosted here as `latin` + `latin-ext` woff2 subsets (~125 KB for the
latin path, fetched per-subset via `unicode-range`) with their licences
alongside. This also keeps visitor IPs away from a third-party font host.

**Logo.** The design's logo is a PNG stored via Git LFS, and the Figma MCP
surface returns only the LFS pointer, so the original bytes were never
retrievable. `assets/img/logo.svg` reproduces the mark as vector art on a
transparent ground, redrawn from supplied artwork: two interlocking rings with
matching diagonal gradients, stroke at 0.168 of the outer diameter and centres
0.52 of an outer diameter apart. Peach passes in front at the upper crossing,
sage at the lower.

The interlock is one real break — the sage ring carries a `stroke-dasharray`
gap at the upper crossing — rather than an overdrawn patch. An earlier version
clipped a second copy of the peach arc to a rectangle, and the clip edge cut
through the overlap and showed as a notch. `r`, `stroke-width`,
`stroke-dasharray` and `stroke-dashoffset` are a single derived set: change one
and all four must be recomputed together. `favicon.svg` reuses the same numbers
under a transform so the two marks cannot drift, and the tests pin them
together.

**Photography.** The design specifies stock imagery hotlinked from Unsplash.
The site ships the alliance's own photographs of the work instead — see
[Imagery](#imagery). Composition and crop follow the design's slots; only the
pictures differ.

**Additions the design does not specify.** A skip link, visible focus styling,
`prefers-reduced-motion` handling, a print stylesheet, `scroll-padding-top` so
the fixed header does not cover anchor targets, and a Content-Security-Policy.
None of them change how the page looks at rest.

### Known non-deviation

The programs grid shows three cards in the first row and one in the second
with two empty cells. That is what the design's `auto-fill` track sizing
produces at this container width, and it has been left alone.

## Imagery

The photographs are the alliance's own pictures of the work, from garment
factories in Mexico. They live in `assets/img/photos/` and are served from this
origin.

**Browsing the site therefore contacts no third party.** Fonts are self-hosted,
photography is local, there is no analytics, no tag manager, no tracking pixel
and no cookie. `img-src` in the Content-Security-Policy is `'self'`, and
a test fails the build if any page fetches a subresource from a remote host, or
if a CSP names a remote source beyond the two the newsletter needs (the home
page's `form-action`, the relay's `script-src`).

Four images are on the page. Each is sized to the largest box it renders in at
2x — not to the camera original — and the markup declares its exact size:

| Slot | File | Size | Bytes |
| :-- | :-- | :-- | --: |
| Hero background (`.hero__media`, drawn at 22% opacity) | `1711_MEX_HONGHO_GARMENT_02-hero.webp` | 1920×1280, q50 | 74 KB |
| Transparency & Traceability, left | `1711_MEX_VKN_GARMENT_076.webp` | 1280×853, q80 | 76 KB |
| Transparency & Traceability, right | `1711_MEX_HONGHO_GARMENT_25.webp` | 1280×853, q80 | 40 KB |
| Textile Recovery Infrastructure diagram | `textile-recovery-infrastructure.webp` (in `assets/img/`) | 1600×1280, alpha | 121 KB |

The hero is a derived file: at 22% opacity under an ink scrim, quality 50 is
indistinguishable from the original (PSNR ~53 dB on the rendered screen) at
half the bytes, and it is the one photograph every visit downloads up front.
`1711_MEX_HONGHO_GARMENT_02.webp`, the full-quality original, stays in the
library. The two program figures never render wider than ~632 CSS px, so 1280
wide covers them at 2x; the 1920-wide originals are in git history (0.15.0).
Everything below the fold is `loading="lazy"` and `decoding="async"`.

`assets/img/photos/` holds more than the page uses — unreferenced shots are a
library, not an error, and the suite reports how much they add to the
published artifact so the cost stays visible.

Because these are documentary photographs rather than decorative stock, each
one carries descriptive `alt` text saying what is pictured — deliberately not a
restatement of the heading beside it.

## Licence

Site content and design are the Circular Textile Alliance's. The bundled
typefaces are licensed under the SIL Open Font License 1.1 — see
`assets/fonts/Inter-LICENSE.txt` and `assets/fonts/PlayfairDisplay-LICENSE.txt`.
