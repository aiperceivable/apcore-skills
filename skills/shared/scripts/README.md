# shared/scripts — deterministic fast paths

These scripts replace work that is **purely deterministic** but was previously
done by the LLM reading files token-by-token on every skill invocation. They cut
the scaffolding token cost and—more importantly—remove LLM error from
version parsing, git-status checks, and score arithmetic.

They cover **only** the mechanical scaffolding. The cross-language *semantic*
work (API normalization & comparison, contract extraction, deep-chain call-graph
diffing, severity calibration) stays LLM-driven by design — do not try to script
it.

## Fast-path / fallback contract

Each script has an authoritative markdown spec it mirrors. The markdown is the
**single source of truth and the fallback**; the script is the **fast path**.

| Script | Mirrors | Replaces in |
|---|---|---|
| `discover.py` | `shared/ecosystem.md` §0.1–0.7 | Step 0 of audit, sync, release, tester, sdk + the dashboard |
| `score.py` | `shared/scoring.md` | audit Step 3, release Step 2.5 gate, `/apcore-skills` dashboard |
| `extract-markers.sh` | `shared/api-extraction.md` §E.4a | sync Step 4A / Step 2 marker grep |

**A skill should:** try the script, parse its JSON/stdout; if Python/bash is
unavailable, the script errors, or output looks wrong, fall back to executing the
markdown rules directly. Never block on a missing script.

## Usage

> **Path note.** The examples below are written **repo-relative** (run them from
> the plugin repo root, e.g. in CI or local dev). At skill **runtime** the CWD is
> the *user's project*, not the plugin — so a skill must resolve the script via
> `$CLAUDE_PLUGIN_ROOT/skills/shared/scripts/<name>` (or the absolute path the
> skill was loaded from), never as a bare CWD-relative path. The scripts take the
> target to scan via `--root` / arguments and never write files, so they are safe
> to run from anywhere against any project.

```bash
# Ecosystem discovery (JSON to stdout). --root skips the upward search.
python3 skills/shared/scripts/discover.py --root /path/to/ecosystem
python3 skills/shared/scripts/discover.py            # auto-detect from $PWD

# Health scores + release gate (JSON in -> JSON out).
echo '{"d9":{"warning":8},"d10":{"critical":3},"d11":{"inconclusive":3},
       "gate":{"audit_critical":0,"sync_critical":0}}' \
  | python3 skills/shared/scripts/score.py

# Checkpoint markers (path:line:name, file order).
skills/shared/scripts/extract-markers.sh /path/to/apcore-python/src
```

Both Python scripts emit `{"error": ...}` JSON on failure so the caller can
detect it and fall back. `discover.py` returns exit 2 with
`ecosystem_root_not_found` when it cannot locate the root — the skill then uses
`AskUserQuestion` per ecosystem.md §0.1.

## Drift policy

The scripts duplicate rules that also live in markdown, so they CAN drift. One
command runs every guard rail:

```bash
skills/shared/scripts/test.sh
```

It runs `discover.py --selftest` (name→type classification + every version-string
parser), `score.py --selftest` (every formula, gate precedence, unrounded-boundary
behavior), and a `bash -n` syntax check on `extract-markers.sh` (plus `shellcheck`
when present). CI runs the **same command** on changes to `skills/shared/**`
(`.github/workflows/scripts.yml`), so local and CI never diverge.

Run it after editing either a script **or** its companion markdown table. If a
rule changes in `ecosystem.md` / `scoring.md`, update the script and its selftest
in the same commit. Per `scoring.md` §Change Control, a formula/threshold change
is a breaking change and must bump the apcore-skills minor version.

Stdlib/POSIX only — no `pip install`, no third-party deps.
