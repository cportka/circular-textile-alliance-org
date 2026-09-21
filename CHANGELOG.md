# Changelog

All notable changes to this project are documented here. The format follows Keep a Changelog
(https://keepachangelog.com) and the project uses Semantic Versioning (https://semver.org).
Every change bumps the version and adds an entry below.

## [0.10.0] - 2026-09-21

### Added
- **`publications.html` — a dedicated Reports & Publications page.** Same header
  and footer as the home page, its own title, description, canonical and Open
  Graph metadata, and its own entry in `sitemap.xml` and `llms.txt`. It carries
  "Knowledge for a Changing Textile Economy", the five kinds of publication CTA
  may produce, the approach to knowledge, and the full library.
- **`Full Library →` is a real link now**, not a placeholder.
- The four supplied publications, on both pages: LA Recovered Textile Hub, SB
  707 Explained, SB-707 Responsible Textile Recovery Act of 2024, and the EU
  Digital Product Passport study. The home page shows the same four the library
  does, since four is the whole list for now.

### Fixed
- **Jake Slayton's surname**, missing from the board listing.
- **404.html's lede lost its type in 0.4.0.** Deleting the hero's lede paragraph
  took `.hero__lede` with it, but `404.html` still carried the class, and
  `.notfound__lede` only set a width and a margin. The size, line height and
  0.65 alpha are restored on `.notfound__lede` itself and the dead class is off
  the markup.
- **`links-assets` read an outbound link as a third-party request.** It checked
  every `href` and `src` against one allowlist, so a link to a publication's
  source looked identical to loading a script from it. Subresources — `src`, and
  `href` on `<link>`/`<script>` — must still be same-origin; `<a href>` may
  leave, must be https, and the hosts are reported.

### Changed
- Publication rows drop the type badge, year, description and page count: none
  were supplied, and none should be invented. The left rail names the **host**
  instead, which is derived from the link and tells a reader it leaves the site.
  `.pub__type`, `.pub__year`, `.pub__desc` and `.pub__pages` are deleted; they
  can come back when there are CTA publications with that metadata.
- Publication titles are links; each row's action link carries an `aria-label`
  naming the publication and its host, so it is not announced as a bare "Read".
- Placeholder count 13 → 8.

### Added — tests
- **Every class in the markup must have a rule in `site.css`.** This is the
  check that would have caught the 404 regression above: every existing check
  looked for CSS that nothing uses, and none looked for markup that nothing
  styles. Verified by re-breaking 404.html exactly as 0.4.0 did and watching it
  fail.
- `publications.html` joins the structure, links, accessibility and SEO suites —
  the last asserting it does not reuse the home page's title or description, and
  that it is registered in `sitemap.xml` and `llms.txt`.
- The outbound `↗` glyph joins the decorative glyphs that must be `aria-hidden`.

## [0.9.0] - 2026-09-21

Members becomes the alliance's own copy, keeping its ink ground.

### Changed
- **The Figma's member roster is replaced.** 140+ organizations in three named
  tiers, the chips listing them and the "Apply for Membership" button that went
  nowhere are gone. In their place: who can take part, the current board, why
  join, the partnership philosophy, and how to get involved.
- The eyebrow and the footer column are renamed **Membership → Members**.
- **Headings are `--peach`**, per the supplied reference. That measures 6.21:1
  on `--ink`, so it clears AA for normal text and not only for the large sizes
  it is used at — worth stating, because the same peach is a 2.04:1 failure on
  cream and ships there as `--peach-text` instead.
- **The board's three group markers keep the design's peach / sage / third-tone
  scheme** at 6.21, 5.90 and 8.02 to 1. The reference tints the third group
  blue; there is no blue in this palette, so `--sage-light` holds that slot, as
  it already did for the associate tier.
- `.tier*`, `.chips`, `.chip`, `.members__grid`, `.members__lede`,
  `.members__intro` and `.members__tiers` had no remaining markup and are
  deleted.
- `llms.txt` and the README's dead-links deviation updated: two of the Figma's
  placeholders have now gone with the sections that carried them.

### Added
- **`.board__people` uses CSS columns rather than a grid.** Names flow down one
  column and into the next, so the seven-name group fills 3/2/2 instead of
  leaving a ragged final row — which is what the supplied board screenshot
  shows. One column on a phone, two from 704px, three from 1024px.
- `.why` — the five reasons to join, 1-up then 2-up then 3-up.
- `.on-dark .about__list`, so the participant list reads light on ink while
  keeping the peach marker introduced in 0.6.0.

### Added — tests
- Three board groups, each with a colour on its modifier; `columns` declared at
  more than one breakpoint; `break-inside: avoid` on the names. Verified by
  deleting the three-column rule and watching the breakpoint assertion fail.
- Contrast pairs for every new on-ink colour: peach headings, the three group
  labels, board names, why-join titles, and body copy at 0.85.
- Placeholder count 14 → 13; the copy assertions follow the new headings.

### Notes
- **"Jake , CEO Goodwill Bakersfield" has no surname.** Rendered as "Jake, CEO,
  Goodwill Bakersfield" — the stray space and missing comma fixed — but a board
  listing with a first name only needs the rest before it is public.
- "Catherine Compitello, CEO, CEO, Plentiful / …" carried **CEO twice**; it
  appears once.
- The supplied text labels the middle board group **"Members"**, while the
  reference screenshot labels it **"Strategic Members"**. The text wins, so the
  page reads "Members" — inside a block headed "Current Board Members".
- The heading is **"A Network for Shared Progress"**: the supplied text says
  "for", the screenshot says "of".

## [0.8.0] - 2026-09-21

Programmes stops being a card grid and becomes the alliance's own prose.

### Changed
- **The four programme cards are replaced by seven areas of long-form text**:
  Consumer Education, Research & Innovation, Industry Collaboration, Policy
  Implementation, Manufacturing & Workforce Development, Transparency &
  Traceability, Textile Recovery Infrastructure — each a heading, its prose, and
  where the copy has one, an "Our work may include" list.
- The cards' photography, region badges, tags and hairline grid are gone with
  them, as is the `All Programmes →` placeholder: every area is on the page now,
  so there is nowhere further to send anyone. `.card` survives because News
  still uses it; `.badge`, `.tags`, `.card__meta`, `.card__region`,
  `.card-grid--bleed` and `.section-head__title` had no remaining markup and are
  deleted.
- **The footer's Programmes column and the JSON-LD `knowsAbout` list** named the
  four that just left — EPR Readiness, Recycling Pathways, Digital Passports,
  Collection Systems. Both now name the seven.
- `llms.txt`'s Programmes section rewritten to match.

### Added
- **`assets/img/textile-recovery-infrastructure.webp`** — the supplied lifecycle
  diagram, centred at the end of Textile Recovery Infrastructure on a cream
  plate with a hairline rule. It is line art on white, which would otherwise
  float unbounded on `--cream-dark`.
- The two requested photographs side by side at the end of Transparency &
  Traceability, stacking on narrow screens.
- `.prog__*` styles, and a 2-up figure pair sharing the 704px breakpoint the
  principles grid introduced in 0.7.0.

### Added — tests
- Seven programme articles; the Transparency pair present, in `.prog__figures`,
  and in the requested left-to-right order; the diagram inside Textile Recovery
  Infrastructure; `.prog__diagram` keeping the auto margins that centre it.
  Verified by swapping the two photographs and watching the order assertion
  fail.
- A contrast pair for programme body text on `--cream-dark`, which the suite had
  only measured on `--cream`.
- Article count 11 → 14, placeholder count 15 → 14.

### Notes
- **The copy says "six interconnected areas" but lists seven.** The page reads
  "seven", because a reader counting the headings finds seven. If the intent was
  six — perhaps Textile Recovery Infrastructure sitting apart, as the one area
  with no "Our work may include" list — it is a one-word change either way.
- The two Transparency photographs ship at their full 1920x1280 (285 KB for the
  pair) into slots about 400px wide. They were requested by filename and this
  environment has no image tooling to resize them; purpose-made crops would cut
  most of that weight.

## [0.7.0] - 2026-09-21

### Changed
- **The approach section's principles are replaced and expanded, four to
  five**: Education Before Advocacy, Collaboration Over Competition,
  Transparency Builds Trust, Innovation With Purpose, Responsible Markets. The
  previous four (Industry Convening, Evidence-Based Policy, Standards &
  Traceability, Pilot & Scale) came from the Figma and described activities;
  these are the alliance's stated principles.
- **The grid is rebuilt for an odd count.** It was 1-up below 1024px and 4-up
  above, which suited four cards exactly. Five into any even column count
  leaves a hole — and in a hairline grid a hole is not blank space, it is a
  solid block of the `--border` bed showing through where a card should be. The
  layout is now 1-up, 2-up from 704px and 3-up from 1024px, with the last card
  spanning the rest of its row at both multi-column widths. That also suits it:
  Responsible Markets carries by far the longest body.
- A 2-up state is new. With four short cards a single column up to 1024px was
  tolerable; with five longer ones it was a long scroll on a tablet.
- `llms.txt` — "What the Alliance does" becomes "How the Alliance works" and
  lists the five principles. It had been describing the four activities, which
  no longer appear anywhere on the site.

### Added — tests
- A `components` guard on the grid: five cards, and if the count is odd, the
  `:last-child` span must exist at every multi-column breakpoint. Verified by
  deleting the rule and watching both assertions fail.

### Notes
- Card bodies are wrapped with `break_on_hyphens=False`. A line break inside
  "decision-making" is invisible in the source but renders as "decision-
  making", because HTML collapses the newline to a space. The first pass had
  exactly that bug in two cards.

## [0.6.0] - 2026-09-21

### Added
- **A *Who We Are* section**, between the hero's statement band and the
  approach section: "A Coalition Built on *Shared Purpose*", the founding
  paragraph, *What We Do* with the six roles CTA serves, and *Contribute To Our
  Mission & Work*.
- `.about__list` — the six roles as a real `<ul>`. The reset sets
  `list-style: none`, so the marker is drawn as a peach dot that matches the
  eyebrow rule rather than reverting the reset for a browser bullet.

### Changed
- **The approach section is now `#approach`, and `#about` belongs to *Who We
  Are*.** The nav's "About" link therefore lands on the alliance's description
  rather than on its four principles, which is what it had been doing since the
  copy moved into the hero.
- Its eyebrow changes from "What We Do" to "Our Approach" — *Who We Are* now
  has a *What We Do* heading of its own, and two of them on one page reads as a
  mistake.
- **The founding year is 2025, everywhere.** The Figma said 2019 and so did the
  JSON-LD `foundingDate`, the hero eyebrow and `llms.txt`. The supplied copy
  says 2025, and the hero cannot read "Est. 2019" directly above a paragraph
  reading "Founded in 2025".

### Notes
- **The subheads deviate from the reference's colours, deliberately.** It
  renders *What We Do* and *Contribute To Our Mission & Work* in the undarkened
  brand values — 2.15:1 and 2.04:1 on cream, failures at any size. They ship as
  `--sage-text` and `--peach-text`, same hue, 4.51:1, consistent with the three
  tokens already retuned in 0.1.0.
- ***Contribute* has no copy and no link yet.** "Tbd copy + GIVE BUTTER LINK"
  is not something to publish, so the section renders its heading and an inert
  Givebutter button described by the shared placeholder note. The markup
  carries a comment saying exactly what to swap when the campaign page exists.
- "An educational resource" is the first list item rather than trailing the
  "CTA serves as:" sentence, where the supplied copy had left it. The six read
  as one parallel list.

### Changed — tests
- `SECTIONS` gains `approach`; the copy assertions gain the new headings.
- The placeholder count moves 14 → 15 for the pending Givebutter control.

## [0.5.0] - 2026-09-21

0.4.0 put the new copy in the About section. It belongs in the dark band under
the headline, which is where it now is.

### Changed
- **The introduction, Our Mission and Our Vision moved into the hero**, below
  "Closing the Loop on Textile Waste", on the dark ground — the place the
  removed elements occupied.
- **The hero is now two bands.** `.hero__stage` is the first screen and the only
  place the photograph appears. `.hero__statement` sits beneath it on flat
  `--ink` and carries the copy.

  This is a contrast requirement, not a layout preference. `.hero__media` is
  cream at 0.22 over ink, so the brightest parts of the photograph lift the
  ground to roughly `#4B5855`. Against that, the sage subhead measures
  **2.96:1** and the introduction **4.26:1** — both failing AA — while against
  flat `--ink` they are 5.90:1 and 8.48:1. No static colour check would have
  caught it, because the colours themselves are correct; only the ground was
  wrong. Splitting the bands makes the pairs the suite measures the pairs that
  actually render.
- **Colours follow the supplied reference**: sage for the subhead and for the
  Our Mission / Our Vision titles, cream at 0.75 for the introduction, and full
  cream for the mission and vision text, so those read as the firmer statements.
- **About is now the approach section** — eyebrow "What We Do", heading "How We
  Work" — holding the four principles that were always there. Its id and
  `aria-labelledby` are unchanged, so the nav anchor still resolves.

### Added — tests
- A `components` guard on the band split: `.hero__statement` must come after
  `.hero__stage`, `.hero__media` must be inside the stage and absent from the
  statement, and `.hero__statement` must keep its solid `--ink` background.
  Verified by reintroducing the fault and watching it fail.
- Contrast pairs for the new on-ink copy: the sage subhead, the sage
  mission/vision titles, the cream mission/vision body, and the introduction at
  0.75.

## [0.4.0] - 2026-09-21

The alliance's own copy replaces the design's placeholder text, and the hero
reduces to photograph and headline.

### Removed
- **The hero's lede paragraph, its two buttons and the stats bar.** The four
  figures (140+ member organizations, 38 countries, 2.4M t diverted, 12 active
  programmes) were the Figma's placeholders, not the alliance's numbers. The
  hero is now the photograph, the eyebrow and the headline — it already had
  `min-height: 100svh` with its content bottom-aligned, so it keeps its full
  presence with the new image showing rather than collapsing.
- The CSS for every removed element, including the two breakpoint rules that
  existed only to keep the stats bar from overflowing a phone.

### Changed
- **About now carries the alliance's real positioning.** "A Coalition Built on
  Shared Purpose" and the 2019 founding blurb are replaced by "Building a
  stronger, more resilient textile economy" and four paragraphs on what CTA is
  and why the textile system needs bridging.
- **Our Mission and Our Vision are stated on the page**, in a new
  `.about__pillars` column, rather than being a button pointing elsewhere. A
  sage rule marks them as statements of intent without adding a surface colour;
  both use existing tokens, so the contrast suite already covers them.
- About's grid re-proportions to suit the longer copy: intro 7 columns,
  mission/vision 5, and the four principles become a full-width four-up band
  beneath rather than a 2x2 block in a 7-column well.
- **Metadata rewritten to match.** The meta description, `og:description`,
  `twitter:description`, the JSON-LD `description` and `llms.txt` all quoted
  copy that no longer exists — the hero lede verbatim, and the stats figures.
  `llms.txt` now carries the mission and vision in place of its "At a glance"
  line, whose four figures were about to exist nowhere else on the site.

### Fixed
- The "Explore our programmes" link is now `justify-self: start`. As a direct
  grid item an `inline-flex` link is blockified and stretches to the column, and
  its underline rule stretches with it.

### Changed — tests
- The copy assertions follow the new headings, and now also pin "Our Mission"
  and "Our Vision".
- The two contrast pairs for the hero lede and the stat labels are dropped with
  the elements they measured.

## [0.3.3] - 2026-09-20

### Removed
- **`tools/screenshot.js` and the "Visual checks" section of the README.** The
  Playwright harness existed to prove the port matched the Figma design while
  that match was still in question. It isn't any more — the site is the
  reference now, and changes to it get judged by looking at it. What remains is
  a tool with a two-step install, a browser binary and a documentation section
  that had already been mistaken for the way to view the site.

  Nothing in CI used it: `tests/run-tests.sh` has always been browser-free, and
  all 400+ assertions still run unchanged. The `components` suite keeps the
  structural guards on the bugs the harness helped find — the hover rules, the
  newsletter field/status separation, the logo geometry — so the regressions it
  caught stay caught.
- The `/shots/` entry in `.gitignore`, which only ever ignored that tool's
  output.

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
