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
    # Fail closed: a renamed or deleted runner must turn CI red, not green —
    # the agent merges on green.
    check("nothing to validate" not in validate and "if [ -f tests/run-tests.sh ]" not in validate,
          "validate.yml skips the suite when the runner is missing — a false green")
    check(re.search(r"^permissions:\s*\n\s*contents:\s*read\s*$", validate, re.M),
          "validate.yml must hold a read-only token")
    check(re.search(r"push:\s*\n\s*branches:\s*\[\s*main\s*\]", validate),
          "validate.yml should run on push to main only (PRs cover branches; "
          "both together run every PR twice)")

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
    upload_at = pages.find("uses: actions/upload-pages-artifact")
    check(build_at != -1 and upload_at != -1 and build_at < upload_at,
          "pages.yml uploads the artifact before validating it")

    for perm in ("pages: write", "id-token: write", "contents: read"):
        check(perm in pages, "pages.yml is missing the '%s' permission" % perm)
    # Deploy rights belong to the deploy job alone; the build job runs repo
    # code (the suite) and must not hold them.
    check(re.search(r"^permissions:\s*\{\}\s*$", pages, re.M),
          "pages.yml should grant nothing at the workflow level")
    build_job = pages[pages.find("  build:"):pages.find("  deploy:")]
    deploy_job = pages[pages.find("  deploy:"):]
    check("pages: write" not in build_job and "id-token: write" not in build_job,
          "pages.yml's build job holds deploy permissions while running repo code")
    check("pages: write" in deploy_job and "id-token: write" in deploy_job,
          "pages.yml's deploy job lost its deploy permissions")
    check("if: github.ref == 'refs/heads/main'" in deploy_job,
          "pages.yml would publish a manual run from any branch")

    # Publish the staged allowlist, dot-paths included — the repo root shipped
    # internals and left .well-known/security.txt behind.
    stage_at = pages.find("scripts/stage-site.sh _site")
    check(build_at != -1 and stage_at > build_at and stage_at < upload_at,
          "pages.yml must validate, then stage with scripts/stage-site.sh, then upload")
    check(re.search(r"path:\s*_site\b", pages), "pages.yml uploads something other than _site")
    check("include-hidden-files: true" in pages,
          "pages.yml drops dot-paths, so .well-known/security.txt would not be published")
    m = re.search(r"actions/upload-pages-artifact@v(\d+)", pages)
    check(m and int(m.group(1)) >= 5,
          "upload-pages-artifact before v5 has no include-hidden-files input")

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

# The newsletter's browser tests: both modes, read-only token, and triggered by
# every file the signup depends on.
NEWSLETTER = ".github/workflows/newsletter.yml"
check(exists(NEWSLETTER), "%s is missing" % NEWSLETTER)
if exists(NEWSLETTER):
    nl = read(NEWSLETTER)
    check("tests/browser/newsletter.cjs\n" in nl and "tests/browser/newsletter.cjs --live" in nl,
          "newsletter.yml must run the browser test both mocked and --live")
    check(re.search(r"^permissions:\s*\n\s*contents:\s*read\s*$", nl, re.M),
          "newsletter.yml should hold a read-only token")
    for dep in ("index.html", "newsletter-frame.html", "assets/js/site.js",
                "assets/js/newsletter-frame.js", "assets/css/site.css", "tests/browser/**"):
        check(nl.count("- " + dep) == 2,
              "newsletter.yml does not run on changes to %s (push and pull_request)" % dep)
    check("workflow_dispatch:" in nl, "newsletter.yml cannot be run on demand")
check(exists("tests/browser/newsletter.cjs"), "the newsletter browser test is missing")

# Node 20 is deprecated on the runners. These are the first majors of each
# action that run on Node 24; GitHub's own actions are pinned by major tag.
CURRENT = {"actions/checkout": 7, "actions/configure-pages": 6,
           "actions/upload-pages-artifact": 5, "actions/deploy-pages": 5}
for path in (VALIDATE, PAGES, NEWSLETTER):
    if not exists(path):
        continue
    text = read(path)
    for action, major in re.findall(r"uses:\s*([\w-]+/[\w-]+)@v(\d+)", text):
        if action in CURRENT:
            check(int(major) >= CURRENT[action],
                  "%s uses %s@v%s — older than v%d, which is on the deprecated Node 20"
                  % (path, action, major, CURRENT[action]))
    # The token is never needed after checkout; don't leave it in .git/config
    # while repository scripts run.
    checkouts = len(re.findall(r"uses:\s*actions/checkout@", text))
    check(text.count("persist-credentials: false") >= checkouts,
          "%s leaves the checkout token on disk (persist-credentials)" % path)

report("workflows")
