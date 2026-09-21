"""WCAG 2.1 contrast for every text/background pairing the design actually uses.

The values are read out of the stylesheet's custom properties rather than
hard-coded here, so retuning a token re-runs the maths instead of silently
drifting away from it.
"""

import re
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from sitecheck import check, read, report  # noqa: E402

AA_NORMAL = 4.5
AA_LARGE = 3.0

css = read("assets/css/site.css")
root = re.search(r":root\s*\{(.*?)\}", css, re.S).group(1)
TOKENS = dict(re.findall(r"--([a-z0-9-]+):\s*(#[0-9a-fA-F]{6})\s*;", root))


def rgb(value):
    value = TOKENS.get(value.lstrip("-"), value).lstrip("#")
    return tuple(int(value[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def luminance(value):
    def channel(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(c) for c in rgb(value))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(fg, bg):
    a, b = luminance(fg), luminance(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def blend(fg, bg, alpha):
    f, b = rgb(fg), rgb(bg)
    mixed = tuple(f[i] * alpha + b[i] * (1 - alpha) for i in range(3))
    return "#%02X%02X%02X" % tuple(round(c * 255) for c in mixed)


for name in ("cream", "cream-dark", "ink", "ink-deep", "ink-light", "ink-muted",
             "peach", "peach-text", "sage", "sage-text", "sage-light", "border"):
    check(name in TOKENS, "design token --%s is not defined in :root" % name)

# (label, foreground, background, minimum) — solid pairings.
SOLID = [
    ("card body text on cream",            "ink-muted",  "cream",      AA_NORMAL),
    ("card body text on cream-dark",       "ink-muted",  "cream-dark", AA_NORMAL),
    ("about body text on cream",           "ink-light",  "cream",      AA_NORMAL),
    ("program body on cream-dark",      "ink-light",  "cream-dark", AA_NORMAL),
    ("nav links (scrolled) on cream",      "ink-light",  "cream",      AA_NORMAL),
    ("headings on cream",                  "ink",        "cream",      AA_NORMAL),
    ("headings on cream-dark",             "ink",        "cream-dark", AA_NORMAL),
    ("peach eyebrow label on cream",       "peach-text", "cream",      AA_NORMAL),
    ("peach eyebrow label on cream-dark",  "peach-text", "cream-dark", AA_NORMAL),
    ("sage label on cream",                "sage-text",  "cream",      AA_NORMAL),
    ("sage label on cream-dark",           "sage-text",  "cream-dark", AA_NORMAL),
    ("primary button label on peach fill", "ink",        "peach",      AA_NORMAL),
    ("hero headline on ink",               "cream",      "ink",        AA_NORMAL),
    ("hero eyebrow on ink",                "sage",       "ink",        AA_NORMAL),
    ("hero accent headline on ink",        "peach",      "ink",        AA_LARGE),
    ("members headings on ink",            "peach",      "ink",        AA_NORMAL),
    ("board exec label on ink",            "peach",      "ink",        AA_NORMAL),
    ("board member label on ink",          "sage",       "ink",        AA_NORMAL),
    ("board advisory label on ink",        "sage-light", "ink",        AA_NORMAL),
    ("board names on ink",                 "cream",      "ink",        AA_NORMAL),
    ("why-join titles on ink",             "sage",       "ink",        AA_NORMAL),
    ("hero subhead on ink",                "sage",       "ink",        AA_NORMAL),
    ("mission/vision titles on ink",       "sage",       "ink",        AA_NORMAL),
    ("mission/vision body on ink",         "cream",      "ink",        AA_NORMAL),
    ("footer headings on ink-deep",        "cream",      "ink-deep",   AA_NORMAL),
]

for label, fg, bg, minimum in SOLID:
    r = ratio(fg, bg)
    check(r >= minimum, "%s: %.2f:1 (need %.1f:1) — --%s on --%s" % (label, r, minimum, fg, bg))

# Translucent text: composite over the known backdrop first.
ALPHA = [
    ("hero intro copy on ink",       "cream", "ink",      0.75, AA_NORMAL),
    ("members body on ink",          "cream", "ink",      0.85, AA_NORMAL),
    ("newsletter note on ink",       "cream", "ink",      0.65, AA_NORMAL),
    ("newsletter placeholder on ink", "cream", "ink",     0.55, AA_NORMAL),
    ("footer blurb on ink-deep",     "cream", "ink-deep", 0.60, AA_NORMAL),
    ("footer column titles",         "cream", "ink-deep", 0.60, AA_NORMAL),
    ("footer link text",             "cream", "ink-deep", 0.60, AA_NORMAL),
    ("footer social chips",          "cream", "ink-deep", 0.60, AA_NORMAL),
    ("footer legal / policies",      "cream", "ink-deep", 0.55, AA_NORMAL),
]

for label, fg, bg, alpha, minimum in ALPHA:
    effective = blend(fg, bg, alpha)
    r = ratio(effective, bg)
    check(r >= minimum,
          "%s: %.2f:1 (need %.1f:1) — %s at %.0f%% over --%s" % (label, r, minimum, fg, alpha * 100, bg))

# Guard against the pre-fix Figma values creeping back in.
REGRESSIONS = {
    "ink-muted": "#6b7e7a",
    "peach-text": "#e8936a",
    "sage-text": "#7eada0",
}
for token, bad in REGRESSIONS.items():
    check(TOKENS.get(token, "").lower() != bad,
          "--%s reverted to the Figma value %s, which fails AA on the cream backgrounds"
          % (token, bad))

# Sweep every translucent *text* colour in the stylesheet, so a hand edit that
# lowers one below the audited floor is caught even if it is not listed above.
# Scoped to `color:` declarations — borders and fills are governed by the
# non-text rule below, which has a different threshold.
for value in re.findall(r"^\s*color:\s*rgb\(250 248 243 / (0\.\d+)\)", css, re.M):
    check(float(value) >= 0.55,
          "stylesheet sets text to cream at %s alpha on a dark ground — below the "
          "audited floor of 0.55" % value)

# WCAG 1.4.11: the visual boundary of an interactive control needs 3:1 against
# its background. These two are cream-at-alpha over ink, so they need checking
# separately from the text pairings.
UI_BOUNDARIES = [
    ("ghost button border on the hero", r"\.btn--ghost-light\s*\{[^}]*?border-color:\s*rgb\(250 248 243 / (0\.\d+)\)", "ink"),
    ("newsletter input border", r"\.newsletter__input\s*\{[^}]*?border:\s*1px solid rgb\(250 248 243 / (0\.\d+)\)", "ink"),
]
for label, pattern, bg in UI_BOUNDARIES:
    m = re.search(pattern, css, re.S)
    if not check(m is not None, "could not locate the %s declaration" % label):
        continue
    alpha = float(m.group(1))
    r = ratio(blend("cream", bg, alpha), bg)
    check(r >= 3.0, "%s: %.2f:1 (need 3.0:1 for a control boundary) at %.0f%% alpha"
          % (label, r, alpha * 100))

report("colour contrast")
