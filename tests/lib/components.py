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
