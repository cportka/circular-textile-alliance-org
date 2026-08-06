"""CI/CD workflow invariants.

Deliberately regex-based rather than YAML-parsed: the runner is not guaranteed
to have pyyaml, and these are structural facts about the files, not deep schema
checks. GitHub validates the schema itself.
"""

import re
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from sitecheck import check, exists, read, report  # noqa: E402

VALIDATE = ".github/workflows/validate.yml"
PAGES = ".github/workflows/pages.yml"

for path in (VALIDATE, PAGES):
    check(exists(path), "%s is missing" % path)

if exists(VALIDATE):
    validate = read(VALIDATE)
    check("pull_request:" in validate, "validate.yml no longer runs on pull_request")
    check("push:" in validate, "validate.yml no longer runs on push")
    # A run lost to infrastructure must be retriggerable without an empty commit.
    check("workflow_dispatch:" in validate,
          "validate.yml lost its workflow_dispatch escape hatch")
    check("tests/run-tests.sh" in validate, "validate.yml no longer runs the suite")

if exists(PAGES):
    pages = read(PAGES)

    check("workflow_dispatch:" in pages, "pages.yml cannot be retriggered on demand")
    check(re.search(r"branches:\s*\[\s*main\s*\]", pages),
          "pages.yml does not publish from main")

    # The point of moving off branch-based publishing: the suite gates the deploy.
    check("tests/run-tests.sh" in pages,
          "pages.yml does not run the test suite before publishing — a failing "
          "site could reach production")

    build_at = pages.find("tests/run-tests.sh")
    upload_at = pages.find("upload-pages-artifact")
    check(build_at != -1 and upload_at != -1 and build_at < upload_at,
          "pages.yml uploads the artifact before validating it")

    for perm in ("pages: write", "id-token: write", "contents: read"):
        check(perm in pages, "pages.yml is missing the '%s' permission" % perm)

    for action in ("actions/configure-pages", "actions/upload-pages-artifact",
                   "actions/deploy-pages"):
        check(action in pages, "pages.yml does not use %s" % action)

    check("needs: build" in pages, "pages.yml deploy job does not depend on build")
    check(re.search(r"name:\s*github-pages", pages),
          "pages.yml deploy job is not bound to the github-pages environment")

    # Two concurrent publishes would race on the same Pages deployment; and
    # cancelling one mid-flight can leave the live site half-updated.
    check(re.search(r"concurrency:\s*\n\s*group:\s*pages", pages),
          "pages.yml has no concurrency group — two publishes could race")
    check(re.search(r"group:\s*pages\s*\n\s*cancel-in-progress:\s*false", pages),
          "pages.yml cancels in-flight deploys, which can leave Pages half-updated")

# Node 20 is deprecated on the runners; v4 of checkout still targets it.
for path in (VALIDATE, PAGES):
    if not exists(path):
        continue
    for ref in re.findall(r"uses:\s*actions/checkout@v(\d+)", read(path)):
        check(int(ref) >= 5,
              "%s pins actions/checkout@v%s — v4 targets the deprecated Node 20" % (path, ref))

report("workflows")
