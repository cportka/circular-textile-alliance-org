#!/usr/bin/env bash
# Static site check — see tests/lib/accessibility.py
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
exec python3 tests/lib/accessibility.py
