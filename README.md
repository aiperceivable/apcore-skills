# apcore-skills

> Part of [aipartnerup/apcore-skills](https://github.com/aipartnerup/apcore-skills)

Apcore ecosystem management skill for Claude Code. Handles cross-language SDK synchronization, framework integration scaffolding, multi-repo audits, spec-driven test generation, coordinated releases, and documentation alignment.

## Portability

Authored for Claude Code; installable for Codex as a skill tree (`.codex/INSTALL.md`).
Four host-specific constructs exist and are inventoried in **`PORTABILITY.md`** — none
of them fails loudly, so each carries a documented fallback, and `selfcheck.py` fails if
the inventory grows undeclared. Everything under `skills/shared/scripts/`, the extraction
cache, and every report format is host-neutral.

## Design policy — single operator, no compatibility layers

This plugin has **one user**. Flags, output formats, cache schemas and report layouts are
changed **in place**: rename it, delete the old spelling, done. Do not add a deprecated
alias, a transitional no-op, or a "kept so existing commands keep working" shim — there
are no existing commands but the operator's own, and they are edited in the same sitting.

Every compat layer left behind is a second spelling that must be kept consistent forever,
and this plugin's dominant defect class is exactly that: **a normative document changed
and a consumer did not** (six such defects in one refactor, see
`skills/shared/scripts/README.md`). A compatibility shim manufactures more of them for a
benefit nobody here collects.

What still applies, and is not compatibility:
- **Cache version tags** (`sync-extract-v4`, `sync-deepchain-v2`) — these invalidate stale
  *data*, not old *commands*. Bumping one is how a schema change stays honest; it is
  enforced mechanically by `selfcheck.py`'s `tag-covers` check.
- **Deprecation notices in the user's own SDKs** — those have downstream consumers. This
  policy is about the plugin, not about `apcore-*`.

## Commands

| Command | Usage | Description |
|---------|-------|-------------|
| `/apcore-skills` | | Ecosystem dashboard — versions, git status, health, all commands |
| `/apcore-skills:sync` | `[repos...] [--skip-docs] [--fix] [--scope core\|mcp\|integrations\|all] [--lang python,typescript,...] [--internal-check none\|contract\|skeleton\|behavior] [--deep-chain on\|off] [--modules mod1,mod2,...] [--no-cache] [--save]` | Cross-language API + **contract/intent** + **call-chain (deep-chain)** + documentation consistency check & fix |
| `/apcore-skills:sdk` | `<language> [--type core\|mcp\|a2a\|cli\|toolkit] [--ref <existing-sdk>]` | Bootstrap a language package in its monorepo |
| `/apcore-skills:integration` | `<framework> [--lang python\|typescript\|go] [--ref <existing-integration>]` | Bootstrap a new framework integration |
| `/apcore-skills:audit` | `[--repo <target-id> \| --scope core\|mcp\|integrations\|all] [--fix] [--deep-chain on\|off] [--strict] [--save report.md]` | Deep cross-repo consistency audit — 11 dimensions including **D10 Contract Parity** (shape-level intent) and **D11 Deep-Chain Parity** (chain-level intent — cross-language call-graph diff). Emits review-compatible output consumable by `/code-forge:fix --review`. |
| `/apcore-skills:tester` | `[<repos...>] [--spec <feature>] [--mode generate\|run\|full] [--category unit\|integration\|boundary\|protocol\|contract\|conformance\|all] [--save report.md]` | Spec-driven test generation & cross-language behavioral verification (incl. Contract-derived tests and shared conformance fixtures) |
| `/apcore-skills:release` | `<version> [--scope core\|mcp\|integrations\|all] [--dry-run]` | Coordinated multi-repo release pipeline |

## Ecosystem

Core and Surface implementations live in two Git checkouts. Each component
currently ships Python, Rust, and TypeScript packages.

| Component | Specification target | Package paths | Package target IDs |
|---|---|---|---|
| Core | `apcore` | `apcore/<lang>/` | `apcore-<lang>` |
| MCP | `apcore-mcp` | `apcore-surfaces/mcp/<lang>/` | `apcore-mcp-<lang>` |
| A2A | `apcore-a2a` | `apcore-surfaces/a2a/<lang>/` | `apcore-a2a-<lang>` |
| CLI | `apcore-cli` | `apcore-surfaces/cli/<lang>/` | `apcore-cli-<lang>` |
| Toolkit | `apcore-toolkit` | `apcore-surfaces/toolkit/<lang>/` | `apcore-toolkit-<lang>` |

Here `<lang>` is `python`, `rust`, or `typescript`. Framework integrations such as
`django-apcore` and shared libraries such as `apcore-discovery-python` may live in
independent sibling checkouts.

## Prerequisites

1. Keep the checkouts in a common parent directory. Either monorepo can be discovered on its own.
2. Use `apcore/PROTOCOL_SPEC.md` for Core workflows. Surface specifications and fixtures live under `apcore-surfaces/<component>/`.
3. Discovery walks up from CWD and identifies packages by their monorepo paths and build files.
4. From a separate directory, set `ecosystem_root` in `.apcore-skills.json` there or pass `--root` to `discover.py`.
5. Use the optional ecosystem-level `.apcore-skills.json` for reference and version group configuration.
6. **[code-forge](https://github.com/tercel/code-forge)** skill required for `sdk` and `integration` commands (generates `.code-forge.json` and uses `code-forge:port`, `code-forge:plan`, `code-forge:impl`)

## Breaking Changes (v0.10+)

- **sync `--internal-check` default changed from `none` to `contract`.** Every `/apcore-skills:sync` invocation without an explicit flag now runs Phase A signatures *plus* the contract-tier comparison (Step 4B). This is a stricter default than v0.9 and may surface pre-existing L2 intent divergences in repos that had never opted into contract checking.
- **To preserve v0.9 behavior** (Phase A signatures only), pass `--internal-check=none` explicitly: `/apcore-skills:sync --internal-check=none`.
- **audit D4** now warns when a feature spec's public symbol has no `## Contract:` block. Existing specs without Contract blocks will produce new warnings until filled in.
- **release Step 2.5** consistency gate is mandatory before version bump. Critical audit/sync findings block release unless explicitly overridden with rationale (logged).

## Performance: Extraction Cache

`sync`'s Step 2 (per-repo API extraction) and Step 4C (per-module deep-chain analysis) cache their sub-agent output under `{ecosystem_root}/.apcore-skills-cache/sync/`, keyed by a content hash of exactly the local files each sub-agent would read (`shared/scripts/extract_cache.py` — purely local, no git, no network). On a repeat run where a repo or module hasn't changed since the last sync, the cached output is reused byte-for-byte instead of re-spawning that sub-agent — this is the main lever for cutting sync's cost on large multi-language, multi-module ecosystems, and it does **not** reduce what gets checked: every symbol and module still gets evaluated, just from cached extraction instead of a fresh one when nothing changed. Cache is on by default; pass `--no-cache` to force a full re-extraction. sync itself keeps the cache directory's `.gitignore` entry current at runtime (see `shared/ecosystem.md` §0.6b).

**Known limitation:** the hash covers file content only — Go's and Swift's versions are git-tag-derived (`ecosystem.md` §0.5), which the cache cannot observe without invoking git (deliberately out of scope). A tag-only version bump with no source change can leave a stale `VERSION:` field in a cached extraction; `sync` never compares versions itself (that's `audit`'s job), so this only affects a cosmetic field, not any finding. To manually wipe a suspect cache directory outright (distinct from a single `--no-cache` run): `python3 skills/shared/scripts/extract_cache.py clear --cache-dir {ecosystem_root}/.apcore-skills-cache/sync`.

## Consistency Layers

The ecosystem enforces consistency at three distinct layers — each layer has a different goal and a different skill responsible for it:

| Layer | What must be identical | What may differ | Enforced by |
|---|---|---|---|
| **L1 Implementation** | — nothing required — | Helper names, function decomposition, control-flow shape, line count, idiom usage | *Not enforced.* Each language follows its own grain. |
| **L2 Intent / Contract (SHAPE)** | Inputs validation rules, errors raised (and codes), side-effect order, return shape, behavioral properties (async, thread_safe, pure, idempotent, reentrant) | Implementation details, helper structure | **sync Step 4B** (contract tier — default on) + **audit D10** (Contract Parity) |
| **L2.5 Intent / Call-Chain (CHAIN)** | Which internal calls each public method makes, in what order, producing which state mutations. Catches "signatures match + declared contract matches, but internal call graph diverges" — e.g., one language's public method silently skips a validation call peers perform, or lacks a null-guard peers have | Helper decomposition, exact control-flow shape | **sync Step 4C** (deep-chain — default on) + **audit D11** (Deep-Chain Parity) |
| **L3 Public Signature** | Class/function names (with language convention), parameter names/types, return types, trait/interface contracts, multi-constructor coverage | Internal type choices, private helpers | **sync Step 4** (Phase A checklist) + **audit D1** (API Surface) |

Feature specs at the discovered specification root declare L2 contracts in `## Contract: ClassName.method` blocks. See `skills/shared/contract-spec.md` for the format. Audit D4 flags public symbols whose feature specifications lack a Contract block.

When sync or audit detects an L2 divergence, its review-compatible output (`# Project Review:`) can be piped directly to `/code-forge:fix --review` for automated patching.

## Integration with Other Skills

- **spec-forge** — Generate specifications for new features before implementing; specs should include `## Contract:` blocks for every public method (see `skills/shared/contract-spec.md`)
- **code-forge:plan / code-forge:impl** — Plan and implement features within individual repos
- **code-forge:port** — Port features from one language SDK to another
- **code-forge:fix --review** — Directly consumes audit (Step 3.1) and sync (Step 9.1) review-compatible output to patch L2/L3 divergences across repos
- **code-forge:tdd / code-forge:fix** — Fix failures surfaced by `tester` via TDD red-green cycle
- **code-forge:verify** — Verify test results before claiming fixes are complete
- **apcore-skills** — Ecosystem-level operations that span multiple repos
