"""SEO, social-sharing and structured-data metadata."""

import json
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from sitecheck import Document, check, exists, read, report  # noqa: E402

SITE = "https://cportka.github.io/circular-textile-alliance-org/"

doc = Document("index.html")

title = doc.first("title").text.strip()
check(10 <= len(title) <= 65, "<title> is %d chars; aim for 10-65" % len(title))

description = doc.meta(name="description")
check(description is not None, "meta description missing")
if description:
    check(70 <= len(description) <= 320,
          "meta description is %d chars; aim for 70-320" % len(description))

canonical = doc.first("link", rel="canonical")
check(canonical is not None and canonical.get("href") == SITE,
      "canonical link missing or not %s" % SITE)

for prop in ("og:type", "og:title", "og:description", "og:url", "og:image",
             "og:site_name", "og:image:alt"):
    check(doc.meta(prop=prop), "Open Graph %s missing" % prop)

for name in ("twitter:card", "twitter:title", "twitter:description", "twitter:image"):
    check(doc.meta(name=name), "Twitter card %s missing" % name)

check(doc.meta(name="twitter:card") == "summary_large_image",
      "twitter:card should be summary_large_image for a 1200x630 image")

og_image = doc.meta(prop="og:image") or ""
check(og_image.startswith("https://"), "og:image must be an absolute URL")
check(exists(og_image.replace(SITE, "")), "og:image does not resolve to a committed file")

# Icons and manifest.
check(doc.first("link", rel="icon") is not None, "favicon link missing")
check(doc.first("link", rel="manifest") is not None, "web manifest link missing")
manifest = json.loads(read("site.webmanifest"))
for key in ("name", "short_name", "start_url", "icons", "theme_color", "background_color"):
    check(key in manifest, "site.webmanifest missing %r" % key)
for icon in manifest["icons"]:
    check(exists(icon["src"]), "manifest icon %s does not exist" % icon["src"])

# JSON-LD must parse and describe the organisation.
blocks = [el for el in doc.find("script") if el.get("type") == "application/ld+json"]
check(len(blocks) >= 1, "no JSON-LD block")
raw = re.search(r'<script type="application/ld\+json">(.*?)</script>', doc.source, re.S)
check(raw is not None, "could not extract the JSON-LD block")
if raw:
    try:
        data = json.loads(raw.group(1))
        check(True, "")
    except ValueError as exc:
        data = None
        check(False, "JSON-LD does not parse: %s" % exc)
    if data:
        check(data.get("@context") == "https://schema.org", "JSON-LD @context is not schema.org")
        types = []
        for node in data.get("@graph", []):
            t = node.get("@type")
            types.extend(t if isinstance(t, list) else [t])
        check("Organization" in types, "JSON-LD has no Organization node")
        check("WebSite" in types, "JSON-LD has no WebSite node")

# robots.txt and sitemap must agree with the canonical host.
robots = read("robots.txt")
check("Sitemap:" in robots, "robots.txt does not advertise the sitemap")
check(SITE in robots, "robots.txt sitemap URL does not match the canonical host")
check("Disallow: /\n" not in robots, "robots.txt blocks the whole site")

tree = ET.fromstring(read("sitemap.xml"))
locs = [e.text for e in tree.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
check(SITE in locs, "sitemap.xml does not list the home page at %s" % SITE)

# llms.txt: the AI-readability convention this repo family uses.
llms = read("llms.txt")
check(llms.startswith("# "), "llms.txt should open with an H1 title")
check("> " in llms, "llms.txt should carry a blockquote summary")
check(SITE in llms, "llms.txt does not reference the canonical URL")

# RFC 9116 security contact.
check(exists(".well-known/security.txt"), "no /.well-known/security.txt")
if exists(".well-known/security.txt"):
    sec = read(".well-known/security.txt")
    check(re.search(r"^Contact:\s*\S+", sec, re.M), "security.txt has no Contact field")
    m = re.search(r"^Expires:\s*(\d{4})-", sec, re.M)
    check(m is not None, "security.txt has no Expires field (required by RFC 9116)")
    if m:
        check(int(m.group(1)) >= 2027, "security.txt Expires date has lapsed — refresh it")

# 404 must not be indexable.
notfound = Document("404.html")
check((notfound.meta(name="robots") or "").find("noindex") >= 0,
      "404.html is missing meta robots noindex")

# Absolute URLs across the metadata should all agree on one host.
hosts = set(re.findall(r"https://([a-z0-9.-]+)/circular-textile-alliance-org", doc.source))
check(len(hosts) <= 1, "metadata references more than one host: %s" % sorted(hosts))

# --- publications.html ------------------------------------------------------
pubs = Document("publications.html")
ptitle = pubs.first("title").text.strip()
check(10 <= len(ptitle) <= 65,
      "[publications.html] <title> is %d chars; aim for 10-65" % len(ptitle))
check(ptitle != title, "[publications.html] reuses the home page's <title>")

pdesc = pubs.meta(name="description")
check(pdesc is not None, "[publications.html] meta description missing")
if pdesc:
    check(70 <= len(pdesc) <= 320,
          "[publications.html] meta description is %d chars; aim for 70-320" % len(pdesc))
    check(pdesc != description,
          "[publications.html] reuses the home page's meta description")

canonical = pubs.first("link", rel="canonical")
check(canonical is not None and canonical.get("href") == SITE + "publications.html",
      "[publications.html] canonical does not point at itself: %r"
      % (canonical and canonical.get("href")))
for prop, want in (("og:url", SITE + "publications.html"),):
    check(pubs.meta(prop=prop) == want,
          "[publications.html] %s is %r, expected %r" % (prop, pubs.meta(prop=prop), want))
for prop in ("og:type", "og:title", "og:description", "og:image"):
    check(pubs.meta(prop=prop), "[publications.html] %s missing" % prop)

check(SITE + "publications.html" in read("sitemap.xml"),
      "publications.html is not listed in sitemap.xml")
check("publications.html" in read("llms.txt"),
      "publications.html is not mentioned in llms.txt")

report("seo metadata")
