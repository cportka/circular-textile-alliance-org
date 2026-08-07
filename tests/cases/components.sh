#!/usr/bin/env bash
# UI regression guards — see tests/lib/components.py
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
exec python3 tests/lib/components.py
