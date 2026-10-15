"""What actually gets published: stage the site exactly as pages.yml does, then
check the staged tree rather than the repo.

The repo copy of .well-known/security.txt passed every check for two months
while the deploy silently left it out — upload-pages-artifact drops dot-paths —
and the same deploy published README, CHANGELOG and the tests. Checks against
the repository could not see either problem; these look at the artifact.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from sitecheck import ROOT, Document, check, report  # noqa: E402

tmp = tempfile.mkdtemp(prefix="stage-")
out = os.path.join(tmp, "_site")
try:
    run = subprocess.run(["bash", os.path.join(ROOT, "scripts/stage-site.sh"), out],
                         capture_output=True, text=True)
    check(run.returncode == 0, "scripts/stage-site.sh failed: %s" % (run.stderr or run.stdout).strip())

    staged = set()
    for dirpath, _, files in os.walk(out):
        for name in files:
            staged.add(os.path.relpath(os.path.join(dirpath, name), out))

    # What a visitor (or a scanner) must be able to fetch.
    for need in ("index.html", "publications.html", "news.html", "404.html",
                 "newsletter-frame.html", "assets/css/site.css", "assets/js/site.js",
                 "assets/js/newsletter-frame.js", ".well-known/security.txt",
                 "robots.txt", "sitemap.xml", "site.webmanifest", "llms.txt"):
        check(need in staged, "the published site is missing %s" % need)

    # What must never ship.
    for path in sorted(staged):
        top = path.split(os.sep)[0]
        check(top not in ("tests", "scripts", ".github", ".claude", ".git")
              and not path.endswith((".md", ".pyc", ".py", ".sh"))
              and top not in ("VERSION", ".gitignore", ".nojekyll"),
              "the published site would include %s" % path)

    # Every page in the repo root is published, and every local reference in
    # the published pages and stylesheet resolves inside the published tree.
    for page in sorted(f for f in os.listdir(ROOT) if f.endswith(".html")):
        check(page in staged, "%s is in the repo but would not be published" % page)
    for page in sorted(p for p in staged if p.endswith(".html")):
        doc = Document(os.path.join(out, page))
        for value, attr, tag in doc.local_refs():
            if not value:
                continue
            target = re.sub(r"^/?circular-textile-alliance-org/", "", value).lstrip("/")
            if target == "" or target.endswith("/"):
                target += "index.html"   # a directory link serves its index
            check(os.path.normpath(target) in staged,
                  "[published %s] <%s %s=%r> is not in the published site" % (page, tag, attr, value))
    css = open(os.path.join(out, "assets/css/site.css"), encoding="utf-8").read()
    for url in re.findall(r"url\(\s*['\"]?([^'\")]+)['\"]?\s*\)", css):
        if url.startswith(("http", "data:")):
            continue
        target = os.path.normpath(os.path.join("assets/css", url))
        check(target in staged, "[published site.css] url(%s) is not in the published site" % url)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

report("published site")
