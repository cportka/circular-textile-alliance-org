# circular-textile-alliance-org

> **Version:** 0.3.0 · **Design:** [Figma Make — Redesign Institutional Website](https://www.figma.com/make/pYrwXChqTORzVAjL3X3DI5/Redesign-Institutional-Website) · **Security:** [SECURITY.md](./SECURITY.md) · **Changelog:** [CHANGELOG.md](./CHANGELOG.md)

The website for the **Circular Textile Alliance** — a static, single-page
institutional site built from the Figma design above, published to GitHub Pages
by an Actions workflow on every push to `main`.

No build step, no framework, no package manager. `index.html` is the site; open
it and you are looking at production.

---

## Layout of the repository

```
index.html                 the entire site — one page, seven sections
404.html                   styled not-found page
assets/
  css/site.css             every style, including the @font-face block
  js/site.js               progressive enhancement only (header state, menu, form guard)
  fonts/*.woff2            self-hosted Inter + Playfair Display (SIL OFL, licences alongside)
  img/                     logo, favicon, app icons, Open Graph card
  img/photos/*.webp        the alliance's own photography (see below)
site.webmanifest           PWA/install metadata
robots.txt  sitemap.xml    crawler metadata
llms.txt                   plain-language site map for AI crawlers
.well-known/security.txt   RFC 9116 security contact
.nojekyll                  serve files verbatim; skip Jekyll processing
tests/                     the check suite CI runs (see below)
```

## Running it locally

Any static file server will do — the page uses relative paths throughout:

```sh
npx http-server -p 8099 -s .      # then open http://127.0.0.1:8099/
```

Opening `index.html` directly off the filesystem mostly works, but the
Content-Security-Policy and the web manifest behave differently under `file://`,
so prefer the server.

## Tests

```sh
bash tests/run-tests.sh
```

400+ assertions, stdlib Python only, no browser and no network — so the same
command runs locally, in CI (`.github/workflows/validate.yml`, on every push and
pull request) and as the gate in front of every deploy. Seven suites live in
`tests/cases/`, backed by `tests/lib/`:

| Suite | What it holds to account |
| :-- | :-- |
| `html-structure` | one `<h1>`, one `<main>`, heading levels never skip, every section anchor and its `aria-labelledby` exist, design copy still present, **no inline `style`/`<script>`** (which the CSP would silently drop) |
| `links-assets` | every local `href`/`src` and every `url()` in the CSS resolves to a real file, every `#anchor` has a target, no `href="#"` survives, shipped fonts and referenced fonts agree, licences present |
| `accessibility` | alt attributes, labelled form controls, named buttons, ARIA references that point at real ids, disclosure state, unique nav labels, skip link, live region, decorative layers hidden, reduced-motion and focus styling |
| `contrast` | every text/background pair in the design measured against WCAG AA, translucent colours composited first, control boundaries against 1.4.11's 3:1, plus a regression guard on the three retuned tokens |
| `components` | guards for UI bugs that shipped once: the header CTA's hover rules exist per header state (a specificity trap made the label invisible), the newsletter field is isolated from its status message, the status row reserves its height, and the logo keeps its dash-gap interlock and gradients — with `favicon.svg`'s geometry pinned to `logo.svg`'s |
| `workflows` | both workflows still trigger where they should, keep their `workflow_dispatch` escape hatch, hold the Pages permissions and concurrency group, **validate before uploading the artifact**, and pin non-deprecated action versions |
| `seo-metadata` | title/description lengths, canonical, full Open Graph and Twitter sets, manifest and its icons, JSON-LD parses and carries `Organization` + `WebSite`, robots/sitemap/llms.txt agree on one host, `404` is `noindex`, security.txt valid |

### Visual checks

Screenshot verification needs a browser and is deliberately **not** part of the
CI suite. To run it locally:

```sh
npx http-server -p 8099 -s . &
node tools/screenshot.js /tmp/shots http://127.0.0.1:8099/
```

Every asset is same-origin, so the capture needs no network beyond the local
server — what it records is exactly what a visitor sees.

## Deployment

GitHub Pages, published **from GitHub Actions** by
`.github/workflows/pages.yml` on every push to `main`. Requires
**Settings → Pages → Source = "GitHub Actions"**.

The workflow runs `tests/run-tests.sh` *before* uploading the artifact, so a
commit that fails validation never reaches the live site — a gate the older
"deploy from a branch" path had no way to provide. It can also be re-run on
demand from the Actions tab, which matters: when a run is lost to a GitHub
incident rather than to a real failure, the branch-based
`pages build and deployment` workflow cannot be retriggered at all.

**Custom domain.** The site is currently addressed as
`https://cportka.github.io/circular-textile-alliance-org/`, and that URL is
baked into the canonical link, Open Graph tags, JSON-LD, `robots.txt`,
`sitemap.xml` and `llms.txt`. To move to `circulartextilealliance.org`:

1. Point DNS at GitHub Pages **first** (`A` records to GitHub's four apex IPs,
   or a `CNAME` for `www`).
2. Add a `CNAME` file at the repository root containing the bare domain.
3. Replace `https://cportka.github.io/circular-textile-alliance-org` with
   `https://circulartextilealliance.org` across the files listed above, and drop
   the `/circular-textile-alliance-org` prefix from the four root-absolute URLs
   in `404.html`.

Committing `CNAME` before DNS resolves takes the site offline, which is why it
is not committed here.

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
| Primary button label | cream on peach | **ink** on peach (fill unchanged) | 2.25:1 | 6.19:1 |
| Associate-members tier | `--ink` on `--ink` | `--sage-light` | 1.00:1 | 8.48:1 |
| Footer text alphas | 0.30 / 0.35 / 0.40 / 0.45 | 0.55 / 0.60 | 2.61:1 | ≥ 4.9:1 |
| Ghost button + input borders | 0.30 / 0.20 alpha | 0.40 alpha | 2.61:1 | 3.42:1 |

**Header over the hero.** The design renders the wordmark and the nav links in
`--ink` (`#1A2B28`) on a near-black hero photograph — roughly 1.1:1, effectively
invisible. The header now starts light-on-dark and swaps to the design's
ink-on-cream once scrolled, which is the state the design already specifies.

**Dead links.** The design carries 25 links pointing at `href="#"`, which
scrolls to the top of the page. The 14 that read as controls (`All Programmes
→`, `Full Library →`, `All News →`, `Apply for Membership`, four `↓ Download`
buttons, three social links, three policy links) render identically but are
inert `<span>`/`disabled` elements described by a shared visually-hidden note.
The 20 footer list items are rendered as plain text. To wire one up, swap the
`<span class="ph">` for an `<a href="…">` and drop the `aria-describedby`.

**Responsive corrections.** Two places in the design set a fixed inline
`gridTemplateColumns` that overrides the responsive class beside it, so they
overflow on a phone: the hero stats bar (pinned to 4 columns; now 2-up then
4-up, which its own class list asked for) and the newsletter row (`1fr auto`;
now stacked below 640px). The publications rows (`200px 1fr auto`) stack below
768px for the same reason.

**Newsletter form.** No subscription endpoint exists. Rather than fake a success
state, submitting reports plainly that nothing was recorded. Give the `<form>` a
real `action` and delete the guard in `assets/js/site.js` to activate it.

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

The programmes grid shows three cards in the first row and one in the second
with two empty cells. That is what the design's `auto-fill` track sizing
produces at this container width, and it has been left alone.

## Imagery

The hero and the seven card images are the alliance's own photographs of the
work — a spinning mill floor, a machinist at an industrial sewing machine, a
yarn shade card, undyed cotton awaiting processing, and sorted offcut bales.
They live in `assets/img/photos/` and are served from this origin.

**The site therefore contacts no third party at all.** Fonts are self-hosted,
photography is local, there is no analytics, no tag manager, no tracking pixel
and no cookie. `img-src` in the Content-Security-Policy is `'self' data:`, and
a test fails the build if any remote host reappears in the markup or the CSP.

Five source photographs cover eight slots, so each is cropped for its slot
rather than reused whole — the shade card appears once as a wide spread and
once as a tight column, and the mill floor once as a room and once close on the
winding frames. Regenerating them is a matter of re-cropping the originals to
the sizes in the table below and re-exporting as WebP.

| Slot | File | Size |
| :-- | :-- | :-- |
| Hero background (`.hero__media`) | `hero-mill.webp` | 1800×1200 |
| Programme — EPR Readiness | `programme-epr.webp` | 800×500 |
| Programme — Recycling Pathways | `programme-recycling.webp` | 800×500 |
| Programme — Digital Product Passport | `programme-passport.webp` | 800×500 |
| Programme — Collection Infrastructure | `programme-collection.webp` | 800×500 |
| News — Policy | `news-policy.webp` | 600×400 |
| News — Partnership | `news-partnership.webp` | 600×400 |
| News — Event | `news-event.webp` | 600×400 |

WebP at quality 82 keeps the whole set to ~516 KB, and every card image is
`loading="lazy"`, so only the hero is fetched up front. Each card image also
sits on a brand-coloured backing, so a slot reads as a palette block rather
than a gap while it loads.

Because these are documentary photographs rather than decorative stock, each
one carries descriptive `alt` text saying what is pictured — deliberately not a
restatement of the heading beside it.

## Licence

Site content and design are the Circular Textile Alliance's. The bundled
typefaces are licensed under the SIL Open Font License 1.1 — see
`assets/fonts/Inter-LICENSE.txt` and `assets/fonts/PlayfairDisplay-LICENSE.txt`.
