"""Guards for specific UI regressions that shipped once and must not return.

Each block names the bug it prevents. These are structural assertions rather
than rendered proof: they pin the rule, the selector or the geometry whose
absence caused the bug, so the edit that would silently reintroduce it fails
here. Confirming how the result actually looks is a matter of opening the page.
"""

import re
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from sitecheck import Document, check, read, report  # noqa: E402

css = read("assets/css/site.css")
doc = Document("index.html")

# --- Header CTA hover -------------------------------------------------------
# Bug: `.site-header.is-scrolled .btn--outline-ink { color: var(--ink) }` is more
# specific than `.btn--outline-ink:hover`, so hovering filled the button with
# --ink while the label stayed --ink — invisible text. Each header state needs
# its own hover rule at matching specificity.
for selector in (r"\.site-header \.btn--outline-ink:hover",
                 r"\.site-header\.is-scrolled \.btn--outline-ink:hover"):
    check(re.search(selector, css) is not None,
          "missing state-specific hover rule %r — the generic .btn--outline-ink:hover "
          "loses to the header's resting-colour rules and the label goes invisible"
          % selector.replace("\\", ""))

scrolled_hover = re.search(
    r"\.site-header\.is-scrolled \.btn--outline-ink:hover\s*\{([^}]*)\}", css)
if check(scrolled_hover is not None, "scrolled header hover rule not found"):
    body = scrolled_hover.group(1)
    check("background: var(--ink)" in body and "color: var(--cream)" in body,
          "scrolled header hover must pair an --ink fill with a --cream label; got: %s"
          % " ".join(body.split()))

hero_hover = re.search(r"\.site-header \.btn--outline-ink:hover\s*\{([^}]*)\}", css)
if check(hero_hover is not None, "over-hero header hover rule not found"):
    body = hero_hover.group(1)
    check("background: var(--cream)" in body and "color: var(--ink)" in body,
          "over-hero header hover must pair a --cream fill with an --ink label; got: %s"
          % " ".join(body.split()))

# --- Markup and stylesheet agree -------------------------------------------
# 0.4.0 deleted .hero__lede along with the hero paragraph it styled, but
# 404.html still carried the class on its lede — which silently lost its type
# size, line height and colour. Nothing caught it, because every check looked
# the other way: CSS that nothing uses. This looks for markup that nothing
# styles.
STRUCTURAL = {
    # Applied by assets/js/site.js, so it never appears in the markup.
    "is-scrolled",
}
code = re.sub(r"/\*.*?\*/", "", css, flags=re.S)   # a name in a comment is not a rule
used = set()
for page in ("index.html", "404.html", "publications.html"):
    for attr in re.findall(r'class="([^"]+)"', read(page)):
        used.update(attr.split())
for name in sorted(used - STRUCTURAL):
    check(re.search(r"\.%s\b" % re.escape(name), code) is not None,
          "class %r is used in the markup but has no rule in site.css — either it "
          "lost its styling to a deletion, or it should come out of the markup" % name)

# --- Board ------------------------------------------------------------------
# The supplied reference shows names flowing down one column and into the next,
# so a group of seven reads 3/2/2. A grid would place them across and leave a
# ragged final row, so the column rule is the requirement, not a preference.
groups = [el for el in doc.elements if "board__group" in el.classes()]
check(len(groups) == 3, "expected 3 board groups, found %d" % len(groups))
for mod in ("exec", "member", "advisory"):
    check(any("board__group--%s" % mod in g.classes() for g in groups),
          "board group modifier --%s is missing" % mod)
    check(re.search(r"\.board__group--%s\s*\{[^}]*color:" % mod, css),
          ".board__group--%s has no colour, so its dot and label inherit" % mod)
check(len(re.findall(r"\.board__people\s*\{[^}]*\}|\.board__people\s*\{", css)) >= 1,
      ".board__people rule is missing")
check(len(re.findall(r"\.board__people\s*\{[^}]*columns:\s*\d", css)) >= 2,
      "the board list must declare `columns` at more than one breakpoint — that "
      "flow is what spaces the names horizontally")
check(re.search(r"\.board__people li\s*\{[^}]*break-inside:\s*avoid", css),
      "board names must not break across a column boundary")

# --- Programmes -------------------------------------------------------------
# The section is long-form prose now, not a card grid, and two of the seven
# areas carry figures that were asked for by name and position.
progs = [el for el in doc.elements if el.classes() == ["prog"]]
check(len(progs) == 7, "expected 7 programme articles, found %d" % len(progs))

src = doc.source
trans = src.index("Transparency &amp; Traceability")
recovery = src.index("Textile Recovery Infrastructure</h3>")
check(trans < recovery, "Textile Recovery Infrastructure should follow Transparency")

pair = src[trans:recovery]
for photo in ("1711_MEX_VKN_GARMENT_076.webp", "1711_MEX_HONGHO_GARMENT_25.webp"):
    check(photo in pair, "%s belongs at the end of Transparency & Traceability" % photo)
check(pair.index("1711_MEX_VKN_GARMENT_076.webp") < pair.index("1711_MEX_HONGHO_GARMENT_25.webp"),
      "the Transparency figures are in the wrong order — VKN_076 comes first")
check(re.search(r'class="prog__figures"', pair),
      "the two Transparency photographs must sit in a .prog__figures pair, which is "
      "what puts them side by side")
check("textile-recovery-infrastructure.webp" in src[recovery:],
      "the recovery diagram belongs at the end of Textile Recovery Infrastructure")
check(re.search(r"\.prog__diagram\s*\{[^}]*margin:\s*[^;]*auto", css),
      ".prog__diagram must keep its auto inline margins — the diagram is meant to "
      "be centred")

# --- Principles grid --------------------------------------------------------
# The hairline grid draws its rules as 1px gaps over a --border bed, so an empty
# cell is not blank — it is a solid block of border colour. With an odd number of
# cards every even column count leaves one, hence the last-child span.
cards = [el for el in doc.elements if el.classes() == ["principle"]]
check(len(cards) == 5, "expected 5 principle cards, found %d" % len(cards))
if len(cards) % 2:
    check(re.search(r"\.principles \.principle:last-child\s*\{[^}]*grid-column:\s*span 2", css),
          "an odd number of principle cards needs .principles .principle:last-child to "
          "span the rest of its row, or the hairline grid shows a block of --border "
          "where the missing card would be")
check(len(re.findall(r"\.principles \.principle:last-child", css)) >= 2,
      "the last-child span must be declared at every multi-column breakpoint, "
      "not just one")

# --- Hero statement ground --------------------------------------------------
# The statement copy is sage and cream at 0.75 on ink. Those ratios hold against
# flat --ink; over the brightest part of the hero photograph (cream at 0.22) the
# subhead falls to 2.96:1. So the copy must stay out of the photograph's band.
src = doc.source
stage = src.index('<div class="hero__stage">')
statement = src.index('<div class="hero__statement">')
check(stage < statement,
      "the hero statement must come after the photograph's stage, not inside it")
check("hero__media" in src[stage:statement],
      ".hero__media is no longer inside .hero__stage")
check("hero__media" not in src[statement:],
      "the hero statement now has the photograph behind it — its copy is measured "
      "against flat --ink and would fail AA over a bright patch of the image")
check(re.search(r"\.hero__statement\s*\{[^}]*background:\s*var\(--ink\)", css),
      ".hero__statement lost its solid --ink background, which is what makes the "
      "measured contrast pairs the ones that actually render")

# --- Newsletter -------------------------------------------------------------
# Bug: input and button were siblings in one wrapping flex container alongside
# the status message, so submitting reflowed the button to another line.
field = doc.first("div", class_="newsletter__field")
check(field is not None,
      "the newsletter input and submit button must sit in their own "
      ".newsletter__field row, isolated from the status message")
if field:
    check(any("newsletter__input" in c.classes() for c in field.children),
          ".newsletter__field does not contain the input")
    check(any("newsletter__submit" in c.classes() for c in field.children),
          ".newsletter__field does not contain the submit button")

status = doc.first("p", id="newsletter-status")
check(status is not None, "newsletter status node missing")
if status:
    check(status.get("role") == "status", "newsletter status lost role=status")
    # role="status" is already an implicitly polite live region.
    check(status.get("aria-live") is None,
          "aria-live on a role=status node is redundant and can double-announce")
    check("newsletter__status" in status.classes(), "status node lost its class")

check(re.search(r"\.newsletter__status\s*\{[^}]*min-height:", css),
      ".newsletter__status has no min-height — the panel grows on submit and, "
      "because the row is centre-aligned, the heading beside it jumps")

# A percentage max-width inside an `auto` grid track is cyclic, so the track
# resolved to the form's full 26rem and overflowed the viewport on a phone.
check(re.search(r"\.newsletter\s*\{[^}]*grid-template-columns:\s*minmax\(0,\s*1fr\)", css),
      ".newsletter must declare an explicit minmax(0, 1fr) column; an auto track "
      "cannot shrink below the form's fixed width and overflows small screens")
check(re.search(r"\.newsletter__form\s*\{[^}]*max-width:\s*26rem", css),
      ".newsletter__form should cap at 26rem via max-width, not a fixed width")

# --- Logo -------------------------------------------------------------------
logo = read("assets/img/logo.svg")

# Bug: the interlock was an overdrawn arc clipped by a rectangle, whose edge cut
# through the overlap and left a visible notch. One real dash gap has no seam.
check("clip-path" not in logo,
      "logo.svg is back to clipping an overdrawn arc — the clip edge cuts the "
      "overlap and shows as a notch; use a dash gap in the sage ring instead")
check("stroke-dasharray" in logo and "stroke-dashoffset" in logo,
      "logo.svg no longer uses the dash gap that forms the interlock")
check(len(re.findall(r"<circle", logo)) == 2,
      "logo.svg should draw exactly two circles — peach whole, sage with a gap")

for grad in ("cta-peach", "cta-sage"):
    check(grad in logo, "logo.svg is missing the %s gradient" % grad)
check(logo.count('gradientUnits="userSpaceOnUse"') == 2,
      "logo gradients must use userSpaceOnUse so they map identically "
      "regardless of each element's bounding box")

# favicon.svg reuses logo.svg's geometry under a transform; if someone retunes
# one set of numbers the two marks would silently diverge.
favicon = read("assets/img/favicon.svg")
for value in ('r="27.45"', 'stroke-width="11.09"',
              'stroke-dasharray="159.93 12.57"', 'stroke-dashoffset="55.36"'):
    check(value in logo, "logo.svg lost its geometry value %s" % value)
    check(value in favicon,
          "favicon.svg geometry drifted from logo.svg — expected %s" % value)

report("components")
