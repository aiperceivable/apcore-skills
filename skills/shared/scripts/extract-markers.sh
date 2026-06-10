#!/usr/bin/env bash
# apcore-skills checkpoint-marker extractor — deterministic fast path for the
# algorithm-skeleton check (api-extraction.md §E.4a, sync Step 4A).
#
# Emits every `checkpoint:NAME` marker found in source, in file/line order, as:
#     path:line:name
#
# This replaces "spawn a sub-agent to grep" with an actual grep. Per-method
# scoping (mapping each marker to its enclosing method) remains the caller's job
# using the file:line plus the API summary — a shell script cannot reliably
# parse method boundaries across five languages. Comment-only lines are dropped
# best-effort; the caller refines.
#
# Usage:
#   extract-markers.sh <dir>
#   extract-markers.sh <dir1> <dir2> ...
#
# Exit 0 with no output when there are no markers (a method with zero markers is
# a valid result per §E.4a rule 2).

set -uo pipefail

PATTERN='checkpoint:[a-z_][a-z0-9_]*'

if [ "$#" -eq 0 ]; then
  set -- "."
fi

# awk filter: drop obvious comment-only lines, extract the marker name.
emit() {
  awk '
  {
    # grep/rg output is path:line:content — recover content after 2 colons.
    content = $0
    sub(/^[^:]*:[^:]*:/, "", content)
    c = content
    sub(/^[[:space:]]+/, "", c)
    if (c ~ /^#/ || c ~ /^\/\// || c ~ /^\*/ || c ~ /^\/\*/) next
    # path:line prefix is everything before the recovered content.
    prefix = substr($0, 1, length($0) - length(content))
    while (match(content, /checkpoint:[a-z_][a-z0-9_]*/)) {
      name = substr(content, RSTART + 11, RLENGTH - 11)   # 11 = len("checkpoint:")
      print prefix name
      content = substr(content, RSTART + RLENGTH)
    }
  }'
}

if command -v rg >/dev/null 2>&1; then
  rg --no-heading -n "$PATTERN" "$@" 2>/dev/null | emit
else
  grep -rEn "$PATTERN" "$@" 2>/dev/null | emit
fi

exit 0
