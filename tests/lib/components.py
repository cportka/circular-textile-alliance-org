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
# --ink while the label stayed --ink — invisible text. Every header state that
# sets a resting colour needs its own hover rule at matching specificity, and
# there are three of them now: over a dark hero, scrolled, and solid (a page
# with no dark hero to sit over).
_code = re.sub(r"/\*.*?\*/", "", css, flags=re.S)

def rule_body(selector):
    """The declarations of the rule whose selector list contains `selector`."""
    for m in re.finditer(r"([^{}]+)\{([^}]*)\}", _code):
        if selector in [x.strip() for x in m.group(1).split(",")]:
            return m.group(2)
    return None

for selector, fill, label in (
    (".site-header .btn--outline-ink:hover", "var(--cream)", "var(--ink)"),
    (".site-header.is-scrolled .btn--outline-ink:hover", "var(--ink)", "var(--cream)"),
    (".site-header--solid .btn--outline-ink:hover", "var(--ink)", "var(--cream)"),
):
    body = rule_body(selector)
    if check(body is not None,
             "missing state-specific hover rule %r — the header's resting-colour "
             "rules outrank the generic .btn--outline-ink:hover, so the label goes "
             "invisible" % selector):
        check("background: %s" % fill in body and "color: %s" % label in body,
              "%s must pair a %s fill with a %s label; got: %s"
              % (selector, fill, label, " ".join(body.split())))

# The solid state exists so a page that does not open on a dark hero still shows
# its wordmark: publications.html painted cream on cream until it did.
for selector in (".site-header--solid",
                 ".site-header--solid .brand__name",
                 ".site-header--solid .nav__link",
                 ".site-header--solid .nav-toggle__bar"):
    check(rule_body(selector) is not None,
          "%r has no rule — a page using .site-header--solid would fall back to "
          "the over-hero treatment and lose that text against a light ground"
          % selector)
check('class="site-header site-header--solid"' in read("publications.html"),
      "publications.html opens on a cream section, so its header must carry "
      ".site-header--solid or the wordmark is cream on cream")

# --- Mobile disclosure ------------------------------------------------------
# It is a panel hung off the right of the bar, not a full-bleed sheet, so it
# needs to be positioned, bounded, right-aligned — and dismissable by a click
# beside it, which a full-width sheet never needed.
nav_mobile = rule_body(".nav-mobile")
if check(nav_mobile is not None, ".nav-mobile rule not found"):
    for prop in ("position: absolute", "text-align: right", "width: min("):
        check(prop in nav_mobile,
              ".nav-mobile is missing %r — it would go back to a full-width sheet"
              % prop)
    # The panel reaches up around the toggle rather than hanging below it, so
    # its top padding has to clear the icon or the first link lands under it.
    check("top: 100%" not in nav_mobile,
          ".nav-mobile hangs below the bar again — it should start at the top so "
          "the toggle sits inside it")
    check(re.search(r"padding:\s*[3-9]", nav_mobile),
          ".nav-mobile needs enough top padding to clear the toggle overlapping it")
    check("transition:" in nav_mobile,
          ".nav-mobile lost its open/close transition")
check("@starting-style" in css,
      "no @starting-style, so the menu appears without animating in")
check("allow-discrete" in css,
      "without transition-behavior: allow-discrete the menu vanishes on close "
      "instead of animating out")
check(rule_body(".nav-toggle") and "z-index" in rule_body(".nav-toggle"),
      ".nav-toggle must be lifted above .nav-mobile or the panel paints over it")
check(rule_body('.nav-toggle[aria-expanded="true"] .nav-toggle__bar') is not None,
      "the open toggle needs its own bar colour — the panel is cream, and over "
      "the hero the header's bars are cream too, so the X would be invisible")
js = read("assets/js/site.js")
check("#nav-mobile, #nav-toggle" in js,
      "site.js no longer dismisses the menu on an outside click, which a small "
      "dropdown needs and a full-width sheet did not")

# --- Policy dialogs ---------------------------------------------------------
# Each footer policy opens a real <dialog>; showModal() supplies the centring,
# backdrop, focus containment and Escape, so only the wiring is ours to check.
for page in ("index.html", "publications.html"):
    d = Document(page)
    ids = d.ids()
    dialogs = d.find("dialog")
    openers = [el for el in d.elements if "policy-open" in el.classes()]
    check(len(dialogs) == 3, "[%s] expected 3 policy dialogs, found %d" % (page, len(dialogs)))
    check(len(openers) == 3, "[%s] expected 3 policy buttons, found %d" % (page, len(openers)))
    for el in openers:
        target = el.get("data-policy")
        check(target and target in ids,
              "[%s] a policy button points at %r, which is not on the page" % (page, target))
        check(el.get("type") == "button",
              "[%s] a policy button has no type=button and would submit a form" % page)
    for dlg in dialogs:
        check((dlg.get("aria-labelledby") or "") in ids,
              "[%s] a dialog's aria-labelledby does not resolve" % page)

js = read("assets/js/site.js")
check("showModal" in js, "site.js no longer opens the policy dialogs")
check("event.target === dialog" in js,
      "clicking the backdrop no longer closes a policy dialog")
for token in ("@starting-style", "allow-discrete"):
    check(token in css, "policy dialogs need %s to animate in and out" % token)

# --- Scroll containers keep their closing space ------------------------------
# A scroll container's bottom padding is not part of its scrollable overflow in
# every engine. The disclosure panel lost the bottom border of "Become a Member"
# to exactly that, so both scrollers put the space on their last child instead.
nav_rule = rule_body(".nav-mobile") or ""
check(re.search(r"padding:[^;]*\s0;", nav_rule),
      ".nav-mobile has bottom padding again — it scrolls, so that space can be "
      "dropped and clip the last item's border")
check(rule_body(".nav-mobile > :last-child") is not None,
      ".nav-mobile needs the closing space as a margin on its last child")
policy_rule = rule_body(".policy") or ""
check("overflow-y: auto" in policy_rule,
      ".policy must scroll — a long policy would otherwise overflow the viewport")
check(rule_body(".policy__inner") and "2rem 2rem 0" in rule_body(".policy__inner"),
      ".policy__inner must leave its bottom space to .policy__close's margin, "
      "for the same reason .nav-mobile does")

# --- Footer -----------------------------------------------------------------
for page in ("index.html", "publications.html"):
    d = Document(page)
    cols = [el for el in d.elements if "footer-col" in el.classes()]
    check(len(cols) == 2, "[%s] expected 2 footer columns, found %d" % (page, len(cols)))

# --- Spelling ---------------------------------------------------------------
# The Figma used the British "Programmes"; the alliance uses "Programs".
for page in ("index.html", "publications.html", "404.html"):
    check("rogramme" not in read(page),
          "%s still says 'Programme' somewhere" % page)

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

# --- Programs -------------------------------------------------------------
# The section is long-form prose now, not a card grid, and two of the seven
# areas carry figures that were asked for by name and position.
progs = [el for el in doc.elements if el.classes() == ["prog"]]
check(len(progs) == 7, "expected 7 program articles, found %d" % len(progs))

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
