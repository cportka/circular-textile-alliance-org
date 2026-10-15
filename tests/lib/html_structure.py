"""Document structure: landmarks, headings, sections, and CSP-compatible markup."""

import re
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from sitecheck import Document, check, read, report  # noqa: E402

PAGES = ["index.html", "404.html", "publications.html", "news.html"]
SECTIONS = ["about", "approach", "programs", "members", "publications", "news"]

MAILCHIMP = "https://circulartextilealliance.us16.list-manage.com"
REMOTE_CSP = {
    # The newsletter forms' no-script post. No page admits a remote script.
    "index.html": {"form-action": [MAILCHIMP]},
}

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
        # Everything is same-origin except the newsletter: the home page — the
        # one page with a form — may post to Mailchimp's host (paths stop
        # counting after a redirect, so a path there buys nothing). Its JSONP
        # runs in the sandboxed relay, checked below, never in a page.
        directives = {}
        for part in csp.split(";"):
            bits = part.split()
            if bits:
                directives[bits[0]] = bits[1:]
        remote = {}
        for name, sources in directives.items():
            far = [src for src in sources if re.match(r"^(https?:|\*|[\w-]+\.)", src)]
            if far:
                remote[name] = far
        expected = REMOTE_CSP.get(page, {})
        check(remote == expected,
              "%s CSP names remote sources %r; the only deliberate ones are %r"
              % (tag, remote, expected))
        if page not in REMOTE_CSP:
            check(directives.get("form-action") == ["'none'"],
                  "%s has no form, so its CSP should keep form-action 'none'" % tag)
        # The floor every page keeps, asserted rather than assumed: removing
        # one of these weakens the policy without tripping any check above.
        for name, want in (("default-src", ["'self'"]), ("img-src", ["'self'"]),
                           ("script-src", ["'self'"]), ("style-src", ["'self'"]),
                           ("object-src", ["'none'"]), ("base-uri", ["'self'"])):
            check(directives.get(name) == want,
                  "%s CSP %s is %r, expected %r" % (tag, name, directives.get(name), want))
        # frame-ancestors is inert in a meta CSP; keeping it invites false confidence.
        check("frame-ancestors" not in csp,
              "%s CSP declares frame-ancestors, which meta-delivered CSP ignores" % tag)

# --- The newsletter relay ------------------------------------------------------
# newsletter-frame.html is the only document that may run Mailchimp's JSONP,
# and it runs sandboxed in an opaque origin. Its policy admits exactly that
# endpoint and its own script, and nothing else at all.
FRAME = "newsletter-frame.html"
frame = Document(FRAME)
frame_csp = None
for el in frame.find("meta"):
    if (el.get("http-equiv") or "").lower() == "content-security-policy":
        frame_csp = el.get("content")
# script-src is * because WebKit refuses 'self' inside a sandboxed frame (the
# relay never started in Safari); everything else stays 'none'.
check(frame_csp == "default-src 'none'; script-src *; base-uri 'none'; form-action 'none'",
      "[%s] CSP is %r — scripts only, nothing else" % (FRAME, frame_csp))
check(frame.meta(name="robots") == "noindex", "[%s] must be noindex" % FRAME)
scripts = frame.find("script")
check([s.get("src") for s in scripts] == ["assets/js/newsletter-frame.js"],
      "[%s] should load assets/js/newsletter-frame.js and nothing else" % FRAME)
check(not frame.find("style") and not re.search(r'\sstyle\s*=\s*"', frame.source),
      "[%s] has inline style" % FRAME)

# --- Well-formedness --------------------------------------------------------
# This suite's parser repairs a mismatched close by searching the stack, the way
# a browser does — but browsers and parsers repair *differently*, and a stray
# </div> that the tests forgave closed .wrap early on publications.html, putting
# two whole sections outside it at x=0. Every suite stayed green across three
# rounds of the bug being reported. So this check does not use that parser.
VOID = {"img", "br", "hr", "meta", "link", "input", "source", "area", "base",
        "col", "embed", "param", "track", "wbr"}

def strip_uninteresting(text):
    """Blank comments and script bodies, keeping line numbers intact."""
    blank = lambda m: re.sub(r"[^\n]", " ", m.group(0))
    text = re.sub(r"<!--.*?-->", blank, text, flags=re.S)
    return re.sub(r"(?<=>)([^<]*)(?=</script>)", blank, text)

for page in PAGES:
    raw = strip_uninteresting(read(page))
    stack = []
    for m in re.finditer(r"<(/?)([a-zA-Z][\w-]*)([^>]*?)(/?)>", raw):
        closing, tag, selfclose = m.group(1), m.group(2).lower(), m.group(4)
        if tag in VOID or selfclose:
            continue
        line = raw.count("\n", 0, m.start()) + 1
        if not closing:
            stack.append((tag, line))
            continue
        if not stack:
            check(False, "[%s] line %d: </%s> closes nothing" % (page, line, tag))
        elif stack[-1][0] != tag:
            check(False, "[%s] line %d: </%s> does not match <%s> opened at line %d — "
                         "the browser will close elements you did not mean to close"
                  % (page, line, tag, stack[-1][0], stack[-1][1]))
            stack.pop()
        else:
            stack.pop()
    check(not stack, "[%s] never closed: %s"
          % (page, ", ".join("<%s> at line %d" % (t, l) for t, l in stack)))

# --- Unique ids --------------------------------------------------------------
# Duplicating a block duplicates its ids, and a repeated id makes `for=`,
# aria-labelledby and getElementById resolve to whichever comes first — the
# second copy silently stops working. The home page carries two newsletter forms.
for page in PAGES:
    seen = {}
    for m in re.finditer(r'\sid="([^"]+)"', strip_uninteresting(read(page))):
        seen[m.group(1)] = seen.get(m.group(1), 0) + 1
    dupes = sorted(k for k, n in seen.items() if n > 1)
    check(not dupes, "[%s] ids used more than once: %s" % (page, dupes))

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
    "Building a stronger, more resilient textile economy",
    "How We Work",
    "A Coalition Built on",
    "What We Do",
    "Contribute To Our Mission",
    "Turning Knowledge Into Action",
    "Consumer Education",
    "Textile Recovery Infrastructure",
    "Our Mission",
    "Our Vision",
    "Where We Direct Our Collective Effort",
    "A Network for Shared Progress",
    "Who Can Participate",
    "Current Board Members",
    "Why Join CTA?",
    "What&rsquo;s Happening at CTA",
    "Reports &amp; Publications",
    "Stay Informed",
]:
    check(phrase in text, "design copy missing from the page: %r" % phrase)

# Seven program areas, plus four publications and four news items — the home
# page shows the first four of each list, and both lists are four long for now.
check(len(doc.find("article")) == 15,
      "expected 15 <article> elements (7 programs + 4 publications + 4 news), found %d"
      % len(doc.find("article")))

report("html structure")
