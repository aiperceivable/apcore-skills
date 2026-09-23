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
| `extract-markers.sh` | `shared/api-extraction-protocol.md` §E.4a | sync Step 4A / Step 2 marker grep |
| `audit-mechanical.py` | `audit/references/dimension-prompts.md` D2, D3, D6, D7, D8 | audit Step 2a — replaces **five** per-dimension sub-agents with one call |
| `extract_cache.py` | `shared/ecosystem.md` §0.6b | sync Step 2.0/2.2 (API extraction) and Step 4C.2.0/4C.2.2 (deep-chain) — skips a sub-agent entirely on an unchanged-input cache hit |
| `selfcheck.py` | — (this file) | `test.sh` and CI — holds the cross-file invariants that no single document states. Run after editing any SKILL.md, reference prompt, or shared doc. |

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

# Mechanical audit dimensions (JSON to stdout). All five by default.
python3 skills/shared/scripts/audit-mechanical.py --root /path/to/ecosystem
python3 skills/shared/scripts/audit-mechanical.py --only D3,D8      # subset
python3 skills/shared/scripts/audit-mechanical.py --repos apcore-python,django-apcore

# sync's extraction cache — check/put are called by sync itself (Step 2 / 4C).
# `clear` is the manual recovery path if a cache directory is ever suspected
# corrupt or stale beyond what a single `--no-cache` run should fix:
python3 skills/shared/scripts/extract_cache.py clear --cache-dir /path/to/ecosystem/.apcore-skills-cache/sync
python3 skills/shared/scripts/extract_cache.py clear --cache-dir /path/to/ecosystem/.apcore-skills-cache/sync --kind deepchain
```

### Why `audit-mechanical.py` does not carry the Suppression Gate

The gate in `dimension-prompts.md` guards against **LLM** failure modes:
speculation, security theater on internal data flow, padded findings, and claims
about greps that were never run. A deterministic checker cannot fail gates
1/3/5/6 — it reports exactly what it matched, cites `file:line` by construction,
and never pads. Gate 2 does not apply (these five dimensions emit no security
findings) and gate 4 is encoded as a fixed severity per rule. So the 9 KB gate
is **not** prepended to this fast path; it stays with the semantic sub-agents
(D1, D4, D5, D9, D10, D11) that actually need it.

### `not_covered` is load-bearing

Each dimension in the output carries `checked[]` and `not_covered[]`.
`not_covered` lists rules from the markdown that this run did **not** evaluate
(e.g. D6 vulnerability patterns, D3 semver-range compatibility). The audit
orchestrator must surface these so a fast-path run is never mistaken for full
coverage. Never delete an entry from `not_covered` without implementing the
rule it names.

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
behavior), `audit-mechanical.py --selftest`, `extract_cache.py --selftest` (hash
stability, exclusion list, `--extra` participation, check/put/clear round-trip),
and a `bash -n` syntax check on `extract-markers.sh` (plus `shellcheck` when
present). CI runs the **same command** on changes to `skills/shared/**`
(`.github/workflows/scripts.yml`), so local and CI never diverge.

Run it after editing either a script **or** its companion markdown table. If a
rule changes in `ecosystem.md` / `scoring.md`, update the script and its selftest
in the same commit. Per `scoring.md` §Change Control, a formula/threshold change
is a breaking change and must bump the apcore-skills minor version.

Stdlib/POSIX only — no `pip install`, no third-party deps.

---

## `selfcheck.py` — why it exists

`audit-mechanical.py` checks the user's SDK repos. `selfcheck.py` checks **this plugin**,
for one specific class of defect:

> a normative document changed, and a consumer that depends on it did not.

That failure occurred **five times** during one refactor of this plugin, and every time
it was caught by a person reading files, never by a tool. The invariants it breaks are
real but live *between* files, so no single document can hold them:

| Check | The failure it would have caught |
|---|---|
| `include-resolves` | an `@../shared/x.md` pointing at nothing |
| `flag-spelling` | `--deep-chain on\|off` in one skill, `--no-deep-chain` in another |
| `flag-default-drift` | flipping a default in the flag table while three prose paragraphs still asserted the old one |
| `namespace-registry` | emitting `[A-DS-{seq}]` findings that `report-formats.md` had no row for, so the report could not render them |
| `field-consumers` | adding `errors_propagated` to the extraction output format while all four downstream consumers still read only `errors_raised` — the fix shipped **inert** |
| `tag-covers` | editing `extract-api-prompt.md` after bumping the cache tag, so `v2` entries missing a field would be served into a comparison that reads it |

### The manifest

`selfcheck.json` records the dependencies that are otherwise implicit: which fields must
have consumers, which files each cache tag covers (by content hash), and which
conventional negative flags are allowlisted. Each entry carries a `_why`.

**When a check fires, the manifest is usually not what is wrong.** Wire the field up, or
bump the tag — then record the new hash. Editing the manifest to silence a finding is
the one move that defeats the point.

### Adding a check

Add it when a cross-file invariant breaks **in reality**, not in theory. Every check here
is named after an incident. A checker full of speculative rules gets ignored, and an
ignored checker is worse than none — it converts a real signal into noise the next reader
learns to scroll past.
