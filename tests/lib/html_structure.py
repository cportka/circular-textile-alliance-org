"""Document structure: landmarks, headings, sections, and CSP-compatible markup."""

import re
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from sitecheck import Document, check, report  # noqa: E402

PAGES = ["index.html", "404.html"]
SECTIONS = ["about", "programmes", "members", "publications", "news"]

for page in PAGES:
    doc = Document(page)
    tag = "[%s]" % page

    root = doc.first("html")
    check(root is not None and root.get("lang") == "en", "%s <html lang=\"en\"> missing" % tag)

    check(doc.first("meta", charset="utf-8") is not None, "%s charset missing" % tag)
    check(doc.meta(name="viewport") is not None, "%s viewport missing" % tag)

    title = doc.first("title")
    check(title is not None and title.text.strip(), "%s <title> missing or empty" % tag)

    h1s = doc.find("h1")
    check(len(h1s) == 1, "%s expected exactly one <h1>, found %d" % (tag, len(h1s)))

    check(len(doc.find("main")) == 1, "%s expected exactly one <main>" % tag)

    # The Content-Security-Policy forbids inline style/script, so any of either
    # would silently stop applying in a real browser. Guard it here.
    check(not re.search(r'\sstyle\s*=\s*"', doc.source),
          "%s has an inline style attribute — blocked by style-src 'self'" % tag)
    check(not doc.find("style"), "%s has an inline <style> — blocked by style-src 'self'" % tag)
    for script in doc.find("script"):
        is_json_ld = script.get("type") == "application/ld+json"
        check(bool(script.get("src")) or is_json_ld,
              "%s has an inline <script> — blocked by script-src 'self'" % tag)

    csp = None
    for el in doc.find("meta"):
        if (el.get("http-equiv") or "").lower() == "content-security-policy":
            csp = el.get("content")
    check(csp is not None, "%s Content-Security-Policy meta missing" % tag)
    if csp:
        check("'unsafe-inline'" not in csp, "%s CSP weakened with 'unsafe-inline'" % tag)
        check("'unsafe-eval'" not in csp, "%s CSP weakened with 'unsafe-eval'" % tag)
        # frame-ancestors is inert in a meta CSP; keeping it invites false confidence.
        check("frame-ancestors" not in csp,
              "%s CSP declares frame-ancestors, which meta-delivered CSP ignores" % tag)

# --- index.html specifics -------------------------------------------------
doc = Document("index.html")
ids = doc.ids()

for section in SECTIONS:
    check(section in ids, "index.html missing #%s section anchor" % section)
    el = doc.first("section", id=section)
    check(el is not None, "#%s is not a <section>" % section)
    if el:
        labelled = el.get("aria-labelledby")
        check(labelled in ids, "#%s aria-labelledby points at a missing id (%r)" % (section, labelled))

# Heading order must never skip a level.
levels = [int(el.tag[1]) for el in doc.elements if re.match(r"^h[1-6]$", el.tag)]
previous = 0
for i, lvl in enumerate(levels):
    if previous:
        check(lvl <= previous + 1,
              "heading level jumps from h%d to h%d (position %d)" % (previous, lvl, i))
    previous = lvl
check(levels and levels[0] == 1, "the first heading on the page is not the h1")

# Every section heading the design specifies, still present.
text = doc.source
for phrase in [
    "Closing the Loop on",
    "A Coalition Built on",
    "Where We Direct Our Collective Effort",
    "140+ Organizations Moving Together",
    "Reports &amp; Publications",
    "From the Alliance",
    "Stay Informed",
]:
    check(phrase in text, "design copy missing from the page: %r" % phrase)

# All four programmes, four publications and three news items made it across.
check(len(doc.find("article")) == 11,
      "expected 11 <article> cards (4 programmes + 4 publications + 3 news), found %d"
      % len(doc.find("article")))

report("html structure")
