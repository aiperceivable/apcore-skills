#!/usr/bin/env bash
# Drift guard for shared/scripts — runs every selftest + a shell syntax check.
#
# Run this before committing changes to ANY script in this directory OR to the
# companion markdown specs they mirror (ecosystem.md, scoring.md,
# api-extraction.md). CI runs the exact same command (.github/workflows/scripts.yml).
#
# Usage: skills/shared/scripts/test.sh
# Exit 0 = all green; non-zero = a selftest or syntax check failed.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON:-python3}"

echo "== discover.py --selftest =="
"$PY" "$HERE/discover.py" --selftest

echo "== score.py --selftest =="
"$PY" "$HERE/score.py" --selftest

echo "== audit-mechanical.py --selftest =="
"$PY" "$HERE/audit-mechanical.py" --selftest

echo "== extract-markers.sh (bash -n syntax) =="
bash -n "$HERE/extract-markers.sh"
echo "extract-markers.sh syntax: OK"

# Optional: shellcheck when present (CI installs it; local may not have it).
if command -v shellcheck >/dev/null 2>&1; then
  echo "== shellcheck extract-markers.sh / test.sh =="
  shellcheck "$HERE/extract-markers.sh" "$HERE/test.sh"
  echo "shellcheck: clean"
fi

echo ""
echo "All shared/scripts checks passed."
