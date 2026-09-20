# Changelog

All notable changes to this project are documented here. The format follows Keep a Changelog
(https://keepachangelog.com) and the project uses Semantic Versioning (https://semver.org).
Every change bumps the version and adds an entry below.

## [0.3.2] - 2026-09-20

### Fixed
- **An over-strict test blocked the deploy when photographs were added.**
  `links-assets` asserted that committed and referenced photos be *equal*, so
  adding images to `assets/img/photos/` ahead of using them failed the suite —
  and because that suite gates publishing, the Pages run for "Add new photos"
  failed and the site stayed on the previous commit.

  The two directions are not the same kind of problem, and are now treated
  differently:
  - **referenced but missing** renders a broken image, so it stays fatal;
  - **committed but unreferenced** breaks nothing — it is a library shot
    waiting to be used. The suite now reports how many there are and what
    they weigh in the published artifact, and passes.

  The current library: 18 of 26 photographs unreferenced, 4.4 MB published but
  never fetched by the page.

## [0.3.1] - 2026-09-20

Documentation fixes, from a first-run report on a clean Mac.

### Fixed
- **"Running it locally" produced no visible result.** The command used `-s`
  (silent) and no `-o`, so `http-server` started, printed nothing, and opened
  no window — indistinguishable from failing. It is now
  `npx http-server -p 8099 -o`, with a note that a server never opens a browser
  by itself and that `-s` hides the "Available on: …" line.
- **The "Visual checks" snippet could not work as written.** It said
  `npm i -D playwright` but omitted `npx playwright install chromium`, so the
  browser binary was never fetched. It also sat close enough to the local-run
  section to be copied as the way to view the site, which is how it was hit:
  the reader got `Cannot find module 'playwright'` while only wanting to look
  at the page. The section now leads by saying it is optional and not needed to
  view the site, and gives both installs.
- Playwright is now installed globally in the documented path, with
  `NODE_PATH=$(npm root -g)`. `npm i -D` in this repo would create a
  `package.json` and a lockfile — neither of which is git-ignored — purely to
  run a dev-only tool, in a repo whose first claim is that it has no package
  manager. The local alternative is still documented for anyone who prefers it.
- `tools/screenshot.js`'s own header carried the same two-install gap and is
  corrected to match.

## [0.3.0] - 2026-08-07

The site's photography is now the alliance's own, and with it the last
third-party request disappears.

### Added
- **`assets/img/photos/` — eight images cropped from five supplied
  photographs**: a spinning mill floor, a machinist at an industrial sewing
  machine, a yarn shade card, undyed cotton awaiting processing, and sorted
  offcut bales. Each slot gets its own crop rather than a reused whole, so the
  shade card reads as a wide spread in the programmes grid and a tight column
  in the news grid, and the mill floor as a room in the hero and close on the
  winding frames in news. WebP at quality 82, ~516 KB for the set.
- Descriptive `alt` text on every photograph. These are documentary images
  rather than decorative stock, so each says what is pictured without
  restating the heading beside it — and a test now requires it.

### Changed
- **The site contacts no third party at all.** `images.unsplash.com` is gone
  from the markup, the stylesheet, the `preconnect` hint and the
  Content-Security-Policy, whose `img-src` is now `'self' data:`. Combined with
  the self-hosted fonts, every byte a visitor loads comes from this origin.
- `tools/screenshot.js` no longer needs to stub remote images: with everything
  same-origin, a capture is exactly what a visitor sees.
- `SECURITY.md` and `llms.txt` updated — the third-party table is now empty.

### Added — tests
- The allowed-remote-host set is empty, and a failure message explains that
  adding to it is a deliberate act.
- The CSP may not name any remote origin, on either page.
- Committed photos and referenced photos must agree exactly in both directions,
  so an orphaned file or a dangling reference fails the build.
- Photographs must ship as WebP and carry non-trivial `alt` text.

## [0.2.1] - 2026-08-07

Three fixes from review of the live site.

### Fixed
- **The header's "Become a Member" button had an invisible label on hover once
  the page was scrolled.** `.site-header.is-scrolled .btn--outline-ink` sets the
  resting colour at higher specificity than `.btn--outline-ink:hover`, so the
  hover rule filled the button with `--ink` while the label stayed `--ink`. Each
  header state now carries its own hover pair: cream-on-ink when scrolled,
  ink-on-cream over the hero — 13.93:1 either way.
- **The Subscribe button moved when clicked.** The input, the button and the
  status message shared one wrapping flex container, so the message appearing
  reflowed the button onto another line. Input and button now sit in their own
  `.newsletter__field` row, isolated from the message, and the status row
  reserves its height so the panel does not grow on submit. Verified stable at
  320 / 390 / 480 / 900 / 1440px.
- **The newsletter form overflowed the viewport on a phone.** Its `max-width:
  100%` was resolving inside an `auto` grid track — a cyclic percentage, so the
  track sized to the form's full 26rem. The panel now declares an explicit
  `minmax(0, 1fr)` column.

### Changed
- **The logo is redrawn from supplied artwork.** Both rings carry matching
  diagonal gradients; stroke is 0.168 of the outer diameter and the centres sit
  0.52 of an outer diameter apart. Peach passes in front at the upper crossing
  and sage at the lower — the reverse of the previous version, which had been
  inferred from a 30px crop of the design render.
  - The interlock is now one real `stroke-dasharray` gap in the sage ring
    instead of a second peach arc clipped to a rectangle. The old clip edge cut
    through the overlap and showed as a notch.
  - `favicon.svg` reuses `logo.svg`'s geometry under a transform rather than a
    second hand-computed set of numbers, and the tests pin the two together.
  - The favicon, 192/512 app icons and the Open Graph card are regenerated.
- The newsletter's "not connected" message is shortened to one line at the
  form's width, so it fits the reserved row.
- `role="status"` on the newsletter message is left to imply its own politeness;
  the redundant `aria-live` that could double-announce is removed.

### Added
- **`components` test suite** (30 assertions) pinning all three fixes: the
  per-state hover rules and their colour pairs, the field/status separation and
  reserved height, the explicit grid column, and the logo's gradients, dash-gap
  interlock and geometry-sharing with the favicon.

## [0.2.0] - 2026-08-06

Publishing moves from GitHub Pages' "deploy from a branch" path to an Actions
workflow, after Settings → Pages → Source was switched to "GitHub Actions".

### Added
- **`.github/workflows/pages.yml`** — builds and deploys the site on every push
  to `main`, using `actions/configure-pages`, `actions/upload-pages-artifact`
  and `actions/deploy-pages`, bound to the `github-pages` environment.
  - **The suite gates the deploy.** `tests/run-tests.sh` runs *before* the
    artifact is uploaded, so a commit that fails validation never reaches the
    live site. Branch-based publishing offered no such hook.
  - `workflow_dispatch`, so a publish can be retriggered on demand. The
    branch-based `pages build and deployment` workflow could not be: when its
    run was lost to the GitHub Actions incident on 2026-08-06 it sat queued
    until cancelled, with no way to re-run it.
  - A `pages` concurrency group with `cancel-in-progress: false`, so two
    publishes cannot race and an in-flight deploy is never cut off partway.
- **`workflows` test suite** (`tests/cases/workflows.sh`) — 22 assertions
  holding both workflows to their triggers, the `workflow_dispatch` escape
  hatch, the Pages permissions and concurrency settings, the validate-before-
  upload ordering, and non-deprecated action versions.

### Changed
- `actions/checkout` pinned to `v5` in both workflows. `v4` targets Node 20,
  which the runners now force onto Node 24 with a deprecation warning.

## [0.1.0] - 2026-08-06

Initial site, ported from the Figma Make design
[Redesign Institutional Website](https://www.figma.com/make/pYrwXChqTORzVAjL3X3DI5/Redesign-Institutional-Website).

### Added
- **The site.** `index.html` — a single page with seven sections (hero, about,
  programmes, members, publications, news, footer), built as static HTML/CSS/JS
  so GitHub Pages can serve `main` directly with no build step.
- **Design tokens.** The design's `@theme` block ported one-for-one to `:root`
  custom properties in `assets/css/site.css`.
- **Self-hosted typefaces.** Inter and Playfair Display as `latin` + `latin-ext`
  woff2 subsets (SIL OFL, licences shipped alongside), replacing the design's
  `static.figma.com` font URLs. No third-party font CDN is contacted.
- **Logo.** `assets/img/logo.svg` — the interlocking-rings mark redrawn as vector
  art on a transparent ground, plus favicon, 192/512 app icons and a 1200×630
  Open Graph card.
- **Metadata.** Canonical link, full Open Graph and Twitter card sets, JSON-LD
  (`Organization` + `WebSite`), `robots.txt`, `sitemap.xml`, `site.webmanifest`,
  `llms.txt`, `.well-known/security.txt` (RFC 9116) and a styled `404.html`.
- **Content-Security-Policy** declared in the page head, with no `unsafe-inline`
  — the page carries no inline styles or scripts.
- **Test suite.** 350+ stdlib-Python assertions across five suites in
  `tests/cases/` covering document structure, link and asset resolution, static
  accessibility, WCAG contrast and SEO metadata. Runs browser-free so CI needs
  no extra install.
- **`tools/screenshot.js`** — Playwright harness capturing eight viewport/state
  combinations and failing on any console error. Not part of CI.
- **Repository scaffold** via repo-bootstrap (Portka standard): branch-per-change
  workflow, enforced SemVer sync, and CI.

### Changed — deviations from the design

Each is marked `DEVIATION:` in the stylesheet and tabulated in `README.md`.

- **Contrast.** Nine of the design's text and border colours fail WCAG AA or
  1.4.11. Fixes preserve each colour's hue and saturation and lower only
  lightness: `--ink-muted` `#6B7E7A`→`#5F6F6C`, new `--peach-text` `#B34D1C` and
  `--sage-text` `#4A7469` for small text on light grounds, ink rather than cream
  as the primary button label (2.25:1 → 6.19:1, fill unchanged), the associate
  members tier from `--ink`-on-`--ink` to `--sage-light`, footer text alphas
  raised from 0.30–0.45 to 0.55–0.60, and control borders from 0.20–0.30 to 0.40.
- **Header over the hero.** The design puts `--ink` text on a near-black
  photograph (~1.1:1). The header now starts light-on-dark and swaps to the
  design's ink-on-cream when scrolled.
- **Dead links.** The design's 25 `href="#"` links no longer scroll to the top:
  14 render identically as inert controls described by a shared visually-hidden
  note, and the 20 footer items render as plain text.
- **Responsive.** The hero stats bar and the newsletter row had fixed inline
  grid columns overriding their own responsive classes and overflowed on a
  phone; both now stack. Publications rows stack below 768px.
- **Newsletter.** No endpoint exists, so submitting reports plainly that nothing
  was recorded rather than faking success.

### Added — beyond the design

Skip link, visible focus styling, `prefers-reduced-motion` handling, a print
stylesheet, and `scroll-padding-top` so the fixed header does not cover anchor
targets. None change the page's resting appearance.

### Notes

- Photography is hotlinked from `images.unsplash.com` as the design specifies,
  each slot backed by a brand colour so a failed load degrades to a palette
  block. `README.md` documents how to vendor the images locally.
- The site is addressed at `https://cportka.github.io/circular-textile-alliance-org/`.
  No `CNAME` is committed — publishing one before DNS resolves would take the
  site offline. `README.md` has the cutover steps for
  `circulartextilealliance.org`.
