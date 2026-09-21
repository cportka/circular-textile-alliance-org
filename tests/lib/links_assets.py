"""Every reference resolves: local files exist, in-page anchors have targets, and
no link is left pointing at the href="#" placeholder the Figma export used."""

import os
import re
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from sitecheck import ROOT, Document, check, exists, read, report  # noqa: E402

# The site is fully same-origin: photography is the alliance's own, fonts are
# self-hosted. Nothing here should ever contact a third party again.
ALLOWED_REMOTE_HOSTS = set()

for page in ["index.html", "404.html"]:
    doc = Document(page)
    tag = "[%s]" % page
    ids = doc.ids()

    for value, attr, tagname in doc.local_refs():
        if not value:
            continue
        target = value.lstrip("/")
        # 404.html uses root-absolute paths that include the project-pages prefix.
        target = re.sub(r"^circular-textile-alliance-org/", "", target)
        check(exists(target), "%s <%s %s=\"%s\"> does not resolve to a file"
              % (tag, tagname, attr, value))

    for el in doc.elements:
        href = el.get("href")
        if not href:
            continue
        check(href != "#", "%s <%s> still points at the placeholder href=\"#\"" % (tag, el.tag))
        if href.startswith("#") and len(href) > 1:
            check(href[1:] in ids, "%s in-page link %s has no matching id" % (tag, href))

    for el in doc.elements:
        for attr in ("href", "src"):
            val = el.get(attr) or ""
            m = re.match(r"^https?://([^/]+)", val)
            if m:
                host = m.group(1)
                if host.endswith("cportka.github.io") or host == "schema.org":
                    continue
                check(host in ALLOWED_REMOTE_HOSTS,
                      "%s contacts third-party host %s — the site is meant to be fully "
                      "same-origin; add it to the CSP and ALLOWED_REMOTE_HOSTS only "
                      "deliberately" % (tag, host))

# --- Stylesheet url() references ------------------------------------------
css = read("assets/css/site.css")
for url in re.findall(r"url\(\s*['\"]?([^'\")]+)['\"]?\s*\)", css):
    if url.startswith("http") or url.startswith("data:"):
        continue
    resolved = os.path.normpath(os.path.join("assets/css", url))
    check(exists(resolved), "site.css references a missing file: %s" % url)

# Every font file shipped is actually referenced, and vice versa.
fonts_dir = os.path.join(ROOT, "assets/fonts")
on_disk = {f for f in os.listdir(fonts_dir) if f.endswith(".woff2")}
referenced = {os.path.basename(u) for u in re.findall(r"url\('\.\./fonts/([^']+)'\)", css)}
check(on_disk == referenced,
      "font files on disk and referenced in CSS disagree: only-on-disk=%s only-in-css=%s"
      % (sorted(on_disk - referenced), sorted(referenced - on_disk)))
check(exists("assets/fonts/Inter-LICENSE.txt"), "Inter licence not shipped alongside the font")
check(exists("assets/fonts/PlayfairDisplay-LICENSE.txt"),
      "Playfair Display licence not shipped alongside the font")

# --- Placeholders are inert, not fake links -------------------------------
doc = Document("index.html")
placeholders = [el for el in doc.elements if "ph" in el.classes()]
# 3 "All … →" links, 4 publication downloads, 1 membership button, 3 social
# links and 3 policy links — every href="#" the Figma export carried, minus the
# 20 footer list items, which are rendered as plain text rather than controls —
# plus the Givebutter donate button, whose campaign page does not exist yet.
check(len(placeholders) == 15,
      "expected 15 .ph placeholders matching the Figma's dead destinations plus "
      "the pending Givebutter link, found %d" % len(placeholders))
for el in placeholders:
    check(el.get("href") is None,
          "a .ph placeholder carries an href (%r) — it should be inert" % el.get("href"))
    check(el.get("aria-describedby") == "ph-note",
          "a .ph placeholder is not described by #ph-note")
check("ph-note" in doc.ids(), "#ph-note explanation node is missing")

# --- Photography ----------------------------------------------------------
photos_dir = os.path.join(ROOT, "assets/img/photos")
on_disk_photos = {f for f in os.listdir(photos_dir) if not f.startswith(".")}
referenced_photos = set(re.findall(r"assets/img/photos/([\w.-]+)", doc.source))
referenced_photos |= {os.path.basename(u) for u in
                      re.findall(r"url\('\.\./img/photos/([^']+)'\)", css)}
# These two directions are not the same kind of problem, and an earlier version
# of this check conflated them into one equality — which made adding photography
# ahead of using it a build failure, and blocked a deploy.
#
# A reference with no file behind it renders a broken image: fatal.
missing = sorted(referenced_photos - on_disk_photos)
check(not missing,
      "referenced but missing from assets/img/photos/: %s" % missing)

# A file nothing references breaks nothing — it is a library shot waiting to be
# used. It does still ship in the Pages artifact, so report the weight rather
# than failing, and let whoever is curating the imagery decide.
unused = sorted(on_disk_photos - referenced_photos)
if unused:
    weight = sum(os.path.getsize(os.path.join(photos_dir, f)) for f in unused)
    print("  note: %d of %d photo(s) are unreferenced — %.1f MB published but "
          "never fetched by the page: %s"
          % (len(unused), len(on_disk_photos), weight / 1e6, ", ".join(unused)))
check(all(f.endswith(".webp") for f in on_disk_photos),
      "photos should ship as .webp: %s" % sorted(f for f in on_disk_photos
                                                 if not f.endswith(".webp")))

# --- Files GitHub Pages needs ---------------------------------------------
for required in [".nojekyll", "robots.txt", "sitemap.xml", "404.html", "site.webmanifest",
                 "llms.txt", "index.html"]:
    check(exists(required), "%s is missing from the repository root" % required)

report("links and assets")
