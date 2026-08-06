#!/usr/bin/env bash
# Static site check — see tests/lib/contrast.py
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
exec python3 tests/lib/contrast.py
