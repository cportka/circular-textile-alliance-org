"""Static accessibility checks — the subset that can be settled from the markup."""

import re
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from sitecheck import Document, check, report  # noqa: E402

doc = Document("index.html")
ids = doc.ids()

# Images: alt is mandatory. Decorative photography carries alt="" on purpose —
# the card heading already names the thing — but the attribute must be present.
for img in doc.find("img"):
    check(img.get("alt") is not None,
          "<img src=%r> has no alt attribute" % img.get("src"))

# Every form control needs a programmatic label.
labels_for = {el.get("for") for el in doc.find("label") if el.get("for")}
for field in doc.find("input"):
    if field.get("type") in ("hidden", "submit", "button"):
        continue
    fid = field.get("id")
    has_label = fid in labels_for or field.get("aria-label") or field.get("aria-labelledby")
    check(bool(has_label), "<input id=%r> has no associated label" % fid)

# Buttons need an accessible name from text, aria-label, or aria-labelledby.
for btn in doc.find("button"):
    name = btn.all_text() or btn.get("aria-label") or btn.get("aria-labelledby")
    check(bool(name), "<button> has no accessible name (id=%r)" % btn.get("id"))

# ARIA relationships must point at nodes that exist.
for el in doc.elements:
    for attr in ("aria-controls", "aria-labelledby", "aria-describedby"):
        val = el.get(attr)
        if val:
            for token in val.split():
                check(token in ids, "%s=%r on <%s> targets a missing id" % (attr, token, el.tag))

# The disclosure button must expose its state and its target.
toggle = doc.first("button", id="nav-toggle")
check(toggle is not None, "mobile nav toggle is missing")
if toggle:
    check(toggle.get("aria-expanded") == "false", "nav toggle has no initial aria-expanded state")
    check(toggle.get("aria-controls") == "nav-mobile", "nav toggle does not control #nav-mobile")
    check(toggle.get("type") == "button", "nav toggle lacks type=button (would submit a form)")

menu = doc.first("div", id="nav-mobile")
check(menu is not None and menu.get("hidden") is not None,
      "#nav-mobile should start hidden so it is not exposed before JS runs")

# Multiple navs need distinguishing labels.
navs = doc.find("nav")
check(len(navs) >= 1, "no <nav> landmark")
labels = [n.get("aria-label") for n in navs]
check(all(labels), "every <nav> needs an aria-label when there is more than one")
check(len(labels) == len(set(labels)), "two <nav> landmarks share the same label: %r" % labels)

# Skip link, and a target for it.
skip = doc.first("a", href="#main")
check(skip is not None and "skip-link" in (skip.classes() if skip else []),
      "skip link to #main is missing")
check("main" in ids, "#main target for the skip link is missing")

# Live region for the newsletter response. role="status" is an implicitly
# polite live region, so an explicit aria-live alongside it is redundant (and
# can double-announce) — accept either, require one.
status = doc.first("p", id="newsletter-status")
check(status is not None, "newsletter status node is missing")
if status:
    check(status.get("role") == "status" or status.get("aria-live") == "polite",
          "newsletter status is not a polite live region")

# Decorative layers must be hidden from the accessibility tree.
for el in doc.elements:
    if "hero__ring" in el.classes() or "hero__media" in el.classes():
        check(el.get("role") == "presentation" or el.get("aria-hidden") == "true",
              "decorative layer %r is exposed to assistive tech" % el.classes())

# Arrow glyphs are decoration next to real words; they should not be announced.
for el in doc.elements:
    if el.text.strip() in ("→", "↓") and el.tag == "span":
        check(el.get("aria-hidden") == "true",
              "decorative %r glyph is not aria-hidden" % el.text.strip())

# Reduced motion must be honoured — the design turns on smooth scrolling.
css = open(__file__.rsplit("/tests/", 1)[0] + "/assets/css/site.css", encoding="utf-8").read()
check("prefers-reduced-motion" in css, "no prefers-reduced-motion block in the stylesheet")
check(re.search(r"prefers-reduced-motion[^}]*}\s*[^@]*scroll-behavior:\s*auto", css, re.S)
      or "scroll-behavior: auto" in css,
      "smooth scrolling is not disabled under prefers-reduced-motion")
check(":focus-visible" in css, "no visible focus styling defined")

report("accessibility")
