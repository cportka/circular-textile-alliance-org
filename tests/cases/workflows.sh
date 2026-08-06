#!/usr/bin/env bash
# CI/CD workflow invariants — see tests/lib/workflows.py
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
exec python3 tests/lib/workflows.py
