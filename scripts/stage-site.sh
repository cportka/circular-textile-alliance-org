#!/usr/bin/env bash
#
# stage-site.sh — copy exactly the public site into a directory for publishing.
#
# GitHub Pages publishes whatever directory it is handed. Handing it the repo
# root shipped README, CHANGELOG, the tests and CI bytecode, while
# upload-pages-artifact's dot-file exclusion silently dropped .well-known/ — so
# security.txt was never live. This is an allowlist instead: add a top-level
# file or folder here when the site gains one, or it will not be published.
# tests/cases/staging.sh stages into a temp dir and checks the result.
#
# Usage: scripts/stage-site.sh <out-dir>     (out-dir must not exist yet)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:?usage: stage-site.sh <out-dir>}"
[[ -e "$OUT" ]] && { echo "stage-site: $OUT already exists" >&2; exit 1; }

PUBLIC=(
  index.html publications.html news.html 404.html newsletter-frame.html
  assets
  .well-known
  robots.txt sitemap.xml site.webmanifest llms.txt
)

mkdir -p "$OUT"
for item in "${PUBLIC[@]}"; do
  [[ -e "$ROOT/$item" ]] || { echo "stage-site: missing $item" >&2; exit 1; }
  cp -R -- "$ROOT/$item" "$OUT/"
done
# Every HTML page at the root must be listed above — a new page that is not
# would otherwise silently never go live.
for page in "$ROOT"/*.html; do
  [[ -e "$OUT/$(basename "$page")" ]] || { echo "stage-site: $(basename "$page") is not in PUBLIC" >&2; exit 1; }
done
echo "stage-site: staged ${#PUBLIC[@]} entries into $OUT"
