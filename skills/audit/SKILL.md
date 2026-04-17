---
name: audit
description: >
  Deep cross-repo consistency audit for the apcore ecosystem. Checks API surface
  alignment, naming conventions, version synchronization, documentation quality,
  test coverage, dependency alignment, and configuration consistency across all
  repos. Generates a detailed report with severity-classified findings.
---

# Apcore Skills — Audit

## ⚡ Execution Entry Point (READ THIS FIRST)

**When this skill is loaded, you MUST immediately begin executing the Workflow below — do not wait, do not summarize, do not ask "what should I do now". Skills are operational manuals, not reference documents.** Read Step 0 (Ecosystem Discovery), then Step 1 (Parse Arguments), then Step 2 (Execute Audit Dimensions), etc., until the workflow completes or you reach an `AskUserQuestion` checkpoint.

If the harness shows you `Successfully loaded skill · N tools allowed`, that message means **the SKILL.md content was injected into your context** — it does NOT mean the skill has run. Skills do not "run" autonomously; you run them by executing the Detailed Steps below.

If you find yourself about to say "the skill didn't produce output", "skill 仍未输出", "falling back to manual audit", "回退到手动 audit", or anything similar, **STOP**. You have misunderstood how skills work. Go directly to Step 0 and start executing.

The first user-visible action of this skill should be either (a) the output of Step 0 / Step 1, or (b) an `AskUserQuestion` if scope detection needs disambiguation. Never an apology, never a fallback, never silence.

---

Comprehensive consistency audit across all apcore ecosystem repositories.

## Iron Law

**AUDIT EVERY DIMENSION. CLASSIFY EVERY FINDING. A partial audit creates false confidence.**

## When to Use

- Before a major release to ensure ecosystem-wide consistency
- After adding a new SDK or integration to verify alignment
- Periodic health check (monthly recommended)
- When suspecting drift between implementations

## Command Format

```
/apcore-skills:audit [--scope core|mcp|integrations|all] [--fix] [--save report.md]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--scope` | **cwd** | Which repo group to audit. **If omitted, defaults to the current working directory's repo only.** Use `--scope all` for full ecosystem audit. |
| `--fix` | off | Auto-fix issues where safe |
| `--save` | off | Save report to file |

## Audit Dimensions

The audit covers 10 dimensions, each checking specific aspects:

| # | Dimension | Severity Range | Description |
|---|---|---|---|
| D1 | API Surface | critical-warning | Public API alignment across languages |
| D2 | Naming Conventions | critical-warning | File/class/function naming per language rules |
| D3 | Version Sync | critical-info | Version alignment within sync groups |
| D4 | Documentation | warning-info | README, CHANGELOG, docstring, **spec `## Contract:` coverage** |
| D5 | Test Coverage | warning-info | Test file existence and coverage metrics |
| D6 | Dependencies | critical-warning | Dependency versions and compatibility |
| D7 | Configuration | warning-info | APCORE_* settings consistency across integrations |
| D8 | Project Structure | warning-info | File/directory layout per conventions |
| D9 | **Bloat & Redundancy** | **critical-info** | **Dead exports, duplicate symbols, parallel implementations, LOC growth, unused config, scope creep** |
| D10 | **Contract Parity (Intent)** | **critical-warning** | **Behavioral contract parity — inputs validation, errors raised, side-effect order, return shape, async/thread-safe/pure/idempotent/reentrant properties — catches "same signature, different logic" bugs. Plus: integration consumer-contract check (does this integration USE the core SDK per its current Contract?).** |

## Severity Levels

| Level | Meaning | Action Required |
|---|---|---|
| `critical` | Breaking inconsistency — users will hit errors | Must fix before release |
| `warning` | Non-breaking inconsistency — confusing but functional | Should fix soon |
| `info` | Cosmetic or minor inconsistency | Nice to fix |

## Context Management

**All dimension audits and per-repo fixes are executed by parallel sub-agents.** The main context ONLY handles:
1. Orchestration — determining scope and spawning sub-agents
2. Aggregation — collecting structured findings from all sub-agents
3. Reporting — formatting and displaying the consolidated report

Step 2 spawns **up to 10 parallel sub-agents** (one per dimension, all simultaneously). Step 4 spawns **one parallel sub-agent per repo** for fixes. The main context never reads repo files directly.

## Workflow

```
Step 0 (ecosystem) → Step 1 (parse args) → Step 2 (parallel audits) → Step 3 (report) → Step 3.1 (review-compatible output) → [Step 4 (fix)]
```

## Detailed Steps

### Step 0: Ecosystem Discovery

@../shared/ecosystem.md

---

### Step 1: Parse Arguments and Plan Audit

Parse `$ARGUMENTS` for flags.

#### 1.1 CWD-based Default Scope

**If `--scope` is NOT specified:**
1. Detect CWD repo name (basename of CWD)
2. Look up in discovered ecosystem:
   - `core-sdk` repo → audit this repo + sibling core-sdks in the same sync group, dimensions D1-D3, D5-D6, D8-D10 (D10 needs ≥2 repos in the same group to compare)
   - `mcp-bridge` repo → audit this repo + sibling mcp-bridges, dimensions D1-D3, D5-D6, D8-D10
   - `integration` repo → audit this repo, dimensions D2-D10. For D10, auto-pull in the relevant core SDK (matching the integration's language — e.g., django-apcore → apcore-python; nestjs-apcore → apcore-typescript) AND the `apcore/` doc repo as **read-only peers** for the Consumer Contract Check (Step 4 of the D10 prompt). Dimensions D2–D9 still apply only to the integration repo itself.
   - `protocol`/`docs-site` repo → audit documentation dimensions (D4) and bloat (D9) for this repo
   - `shared-lib`/`tooling` repo → audit D2 (naming), D4 (docs), D5 (tests), D8 (structure), D9 (bloat) for this repo
   - CWD not an apcore repo → use `AskUserQuestion` to ask: "CWD is not an apcore repo. Which repo do you want to audit?" with options from `repos[]` names + "All repos (full ecosystem audit)"
3. Display: "Scope: {repo-name} (from CWD). Use --scope all for full ecosystem audit."

**If `--scope` IS specified:** use explicit scope.

#### 1.2 Scope → Repos & Dimensions

| Scope | Repos | Dimensions |
|---|---|---|
| `core` | Core SDKs + `apcore/` doc repo | D1-D3, D5-D6, D8-D10 (D4 covers `apcore/` only) |
| `mcp` | MCP bridges + `apcore-mcp/` doc repo | D1-D3, D5-D6, D8-D10 (D4 covers `apcore-mcp/` only) |
| `integrations` | Framework integrations + auto-pulled core SDKs (per-integration language) + `apcore/` doc repo as read-only peers | D2-D9 on integration repos; **D10 Consumer Contract Check** verifies each integration uses its matching core SDK per the core SDK's current Contract |
| `all` | All repos | All dimensions |

**D9 (Bloat & Redundancy) is always included.** It applies to every scope and every repo type — it is the apcore ecosystem's primary defense against the additive bias of skill-driven feature work.

**D10 (Contract Parity) is included in two modes:**
1. **Parity mode** — runs whenever ≥2 same-type repos are in scope (e.g., multiple core SDKs, multiple MCP bridges). Detects intent divergence across language implementations — the bug class where public signatures match but logic/purpose differs (e.g., one SDK validates inputs and the other doesn't; one emits an event and the other doesn't; one is thread-safe and the other isn't).
2. **Consumer Contract mode** — runs whenever at least one `integration` repo is in scope. The audit auto-pulls the matching core SDK (by language) and the `apcore/` doc repo as read-only peers, then verifies each integration uses the core SDK per its current Contract (input completeness, error handling, thread-safety assumption, deprecated API usage). See `references/dimension-prompts.md` D10 Step 4.

Both modes can run in the same audit invocation — a `--scope all` run exercises both. When the current scope has only 1 same-type repo AND no integrations, D10 is skipped with an INFO finding.

Display:
```
Audit scope: {scope} {("(from CWD)" if defaulted)}
Repos: {count} repositories
Dimensions: {list}
```

---

### Step 2: Execute Audit Dimensions (Sub-agents)

Spawn **all dimension sub-agents in parallel (up to 10 simultaneously)**. Each sub-agent audits exactly 1 dimension. All dimensions are fully independent — no batching or serialization needed.

**Sub-agent prompts:** Use the dimension-specific prompt templates from `@references/dimension-prompts.md`. Each dimension (D1–D10) has its own section with the full prompt template. Fill in `{repo_paths}` (and `{integration_repo_paths}` for D7, `{doc_repo_path}` for D10) from the scope determined in Step 1.

---

### Step 3: Aggregate and Display Report

Collect all findings from sub-agents. Aggregate by severity.

```
apcore-skills audit — Ecosystem Consistency Report

Date: {date}
Scope: {scope}
Repos audited: {count}

═══ SUMMARY ═══

  Dimension              | Critical | Warning | Info
  D1 API Surface         |    2     |    3    |   1
  D2 Naming Conventions  |    0     |    5    |   3
  D3 Version Sync        |    1     |    0    |   0
  D4 Documentation       |    0     |    2    |   4
  D5 Test Coverage       |    0     |    1    |   2
  D6 Dependencies        |    1     |    2    |   0
  D7 Configuration       |    0     |    3    |   1
  D8 Project Structure   |    0     |    1    |   2
  D9 Bloat & Redundancy  |    1     |    8    |   5
  D10 Contract Parity    |    3     |    4    |   2
  ─────────────────────────────────────────────────
  TOTAL                  |    8     |   29    |  20

═══ CRITICAL FINDINGS ═══

[D1-001] Missing API: Registry.scan_directory()
  Repo: apcore-typescript
  Detail: Present in apcore-python (src/apcore/registry/registry.py:45) but missing from TypeScript SDK
  Fix: Add scan_directory method to src/registry/registry.ts

[D3-001] Version mismatch in core sync group
  Repos: apcore-python=0.7.0, apcore-typescript=0.7.1
  Fix: Align versions before release

...

═══ WARNING FINDINGS ═══
(grouped by dimension)

═══ INFO FINDINGS ═══
(grouped by dimension)

═══ BLOAT REPORT (D9) ═══

  Repo                  | LOC    | Δ vs last | Dead | Dup | Parallel | Unused Cfg | Unused Dep | Scope Creep
  apcore-python         | 12450  | +2310     |  4   |  3  |    1     |     2      |     1      |      0
  apcore-typescript     | 11200  | +1980     |  6   |  2  |    0     |     1      |     0      |      2
  django-apcore         |  4500  |  +890     |  2   |  1  |    0     |     0      |     0      |      1
  flask-apcore          |  3800  |  +710     |  1   |  0  |    0     |     0      |     0      |      0
  ──────────────────────────────────────────────────────────────────────────────────────────────────────────
  TOTAL                 | 31950  | +5890     | 13   |  6  |    1     |     3      |     1      |      3

  Top bloat hotspots (act on these first):
    1. apcore-typescript: 6 dead exports — see [D9-002] through [D9-007]
    2. apcore-python: parallel HTTP client implementations — see [D9-014]
    3. django-apcore: scope creep in user-auth feature (+3 unplanned files)

═══ CONTRACT PARITY REPORT (D10) ═══

  Symbols compared: {N}
  Fully matching: {N}
  With divergence: {N}

  Top divergences (act on these first):
    1. Registry.register — TS missing DuplicateError raise [D10-001]
    2. Executor.execute — Go skips input validation present in Python/Rust [D10-002]
    3. Config.load — Python thread_safe=true, TS thread_safe=false [D10-003]

  Contract rows with divergence (summary):
    inputs.validation:    {N}
    errors.raised:        {N}
    side_effect.order:    {N}
    return.shape:         {N}
    property.*:           {N}

═══ HEALTH SCORE ═══

  Overall: {score}/100
  API Consistency: {score}/100
  Naming: {score}/100
  Version Sync: {score}/100
  Documentation: {score}/100
  Test Coverage: {score}/100
  Dependencies: {score}/100
  Leanness (D9):     {score}/100
  Contract Parity (D10): {score}/100
```

**Leanness score formula:** Start at 100. Subtract 5 per `critical` D9 finding, 2 per `warning`, 0.5 per `info`. Floor at 0. A leanness score below 70 indicates the repo needs a dedicated cleanup pass before the next release.

**Contract Parity score formula:** Start at 100. Subtract 8 per `critical` D10 finding (intent divergence is a severe bug class), 3 per `warning`, 0.5 per `info`. Floor at 0. A contract parity score below 80 means at least one implementation is silently doing something different from its peers — must be fixed before release.

If `--save` flag is passed with an explicit path, write to that path. If `--save` is passed without a path, write to the canonical default from `shared/ecosystem.md` §0.6a: `{ecosystem_root}/audit-report-{YYYY-MM-DD}.md`.

---

### Step 3.1: Review-Compatible Issue Report (ALWAYS EMITTED)

**After the consolidated report, ALWAYS append a review-compatible report so that `/code-forge:fix --review` can directly consume audit output.**

Convert all CRITICAL and WARNING findings across dimensions D1–D10 into `code-forge:review` format. Format matches `code-forge:review` output schema and mirrors sync's Step 9.1 so that a single downstream consumer can ingest either skill's output.

Use the `# Project Review:` header with a dynamic scope description (derived from Step 1 — e.g., repo name, scope group, or "all"). Output the review-compatible report as **raw markdown** (not inside a fenced code block) so that code-forge:fix can parse it from the conversation context.

```markdown
# Project Review: {scope_description}

## Consistency

{For each finding from D1–D10 with severity critical or warning, emit one issue entry:}

- severity: <blocker | critical | warning>
  file: {target file path — the file that needs to be fixed}
  line: {line number or range, use 1 if unknown}
  title: [{dimension_id}-{finding_id}] {short title}
  description: {what is inconsistent and why it matters — include cross-reference to spec or peer repo}
  suggestion: {concrete fix instruction — what to change, what to match against}
```

**Severity mapping from audit findings to review format:**

| Dimension | Audit Severity | Review Severity | Notes |
|---|---|---|---|
| D1 | critical | blocker | Missing API symbol from a peer repo |
| D1 | critical | critical | Signature mismatch (param count, type) |
| D1 | warning | warning | Wrapper param count mismatch, naming divergence within signature |
| D2 | critical | critical | Public symbol violates language naming convention |
| D2 | warning | warning | Non-public or cosmetic naming issue |
| D3 | critical | blocker | Version mismatch within sync group before release |
| D3 | warning | warning | Version file inconsistency within a repo |
| D4 | warning | warning | Spec lacks `## Contract:` block for a public symbol; README section missing |
| D4 | info | _(skip)_ | Minor docstring gaps |
| D5 | critical | critical | Tests fail |
| D5 | warning | warning | Test runner unavailable / deps missing |
| D6 | critical | blocker | Incompatible SDK version referenced |
| D6 | warning | warning | Unused / mismatched dependency |
| D7 | warning | warning | APCORE_* setting divergence across integrations |
| D8 | warning | warning | Project structure deviation |
| D9 | critical | critical | Parallel implementation / duplicate code / stub no-op method with spec-declared behavior |
| D9 | warning | warning | Dead export / unused internal / wrapper / scope creep |
| **D10** | **critical** | **blocker** | **Missing input validation or missing raised error type** — users hit silent bugs; **integration missing required arg into core SDK**; **integration calling removed core SDK API** |
| **D10** | **critical** | **critical** | **Side-effect order divergence, return shape divergence, thread_safe/async property divergence**; **integration calling non-thread-safe core SDK method from concurrent handlers** |
| **D10** | **warning** | **warning** | **Spec silent on Contract (cross-repo-only mode); extraction limit (null vs true/false); extra error raised beyond spec**; **integration missing handler for a documented core SDK error**; **integration calling deprecated core SDK API** |
| any | info | _(skip)_ | info-level findings are not actionable bugs |

**Rules:**
- Group issues by file for efficient batch fixing
- The `file` field MUST point to the **implementation or doc file that needs changing**. For D10 cross-repo findings where spec is silent, the `file` is the implementation file of the **outlier repo** (the one that diverges from the majority or from the most-reference repo `apcore-python`). For spec-authoritative D10 findings, every non-matching repo emits its own issue entry (one per repo).
- The `suggestion` field MUST be concrete — e.g., "Add `if not RE_ID.match(id): raise InvalidIdError(code=INVALID_ID)` at line {L}, before the existing `self._index[id] = module` assignment" rather than "fix validation".
- For D10 intent divergences, include the correct contract row from `spec_contracts` (or from the non-outlier repo, if spec silent) directly in the suggestion.
- For D4 spec-contract-missing findings, the `file` is the feature spec that needs the `## Contract:` block added; the `suggestion` includes a ready-to-paste Contract skeleton using `shared/contract-spec.md` format.

**Example output:**

```markdown
# Project Review: apcore core (full ecosystem audit)

## Consistency

- severity: blocker
  file: apcore-go/src/registry.go
  line: 42
  title: [D10-001] Contract — Registry.register missing DuplicateError raise
  description: Spec contract (apcore/docs/features/registry.md §Contract.Registry.register) declares error `DuplicateError(code=DUPLICATE)` when id is already registered and overwrite=false. apcore-python and apcore-typescript raise it; apcore-go silently overwrites. Intent divergence — user deduplication semantics break on Go.
  suggestion: Add before line 42 (before the index insert): `if _, exists := r.index[id]; exists && !overwrite { return ErrDuplicate(id) }`. Ensure ErrDuplicate resolves to error code "DUPLICATE".

- severity: critical
  file: apcore-typescript/src/executor.ts
  line: 87
  title: [D10-003] Contract — Executor.execute thread_safe divergence
  description: apcore-python and apcore-rust declare and implement `thread_safe=true` for Executor.execute (internal lock acquired before mutating shared state). apcore-typescript has no lock / concurrent-safe wrapper — two parallel calls can interleave writes. Spec `## Properties: thread_safe: true` is not satisfied.
  suggestion: Wrap the mutating section (lines 90-105) in a lock — use the existing `this._mu` mutex. Match apcore-python/src/apcore/executor.py:44-62 pattern.

- severity: warning
  file: apcore/docs/features/config.md
  line: 1
  title: [D4-007] Spec — Config.load missing ## Contract: block
  description: Feature spec declares Config.load as a public method but has no `## Contract:` block. Intent parity across language SDKs cannot be verified against spec — D10 fell back to cross-repo-only mode for this method.
  suggestion: Add a Contract block per shared/contract-spec.md. Template:
    ```
    ## Contract: Config.load
    ### Inputs
    - path: str, required, validates[exists], reject_with=FileNotFoundError
    ### Errors
    - FileNotFoundError(code=CONFIG_NOT_FOUND) — path does not exist
    - InvalidConfigError(code=CONFIG_INVALID) — path exists but cannot be parsed
    ### Returns
    - On success: Config
    - On failure: raises
    ### Properties
    - async: false
    - thread_safe: true
    ```
```

If no CRITICAL or WARNING findings exist, still output the header with a note:

```markdown
# Project Review: {scope_description}

## Consistency

_(No actionable issues found — all checks passed.)_
```

---

### Step 4: Auto-Fix (only with --fix flag)

Group fixable findings by repo. Separate unfixable findings for reporting.

**Unfixable (skip and report):**
- API surface fixes (complex — delegate to `/apcore-skills:sync --phase a --fix`)
- Contract parity fixes (D10 — delegate to `/apcore-skills:sync --internal-check=contract --fix`, or pipe the review-compatible output from Step 3.1 to `/code-forge:fix --review`)
- Dependency fixes (risky — show as recommendations only)

**Fixable (per-repo parallel sub-agents):**

Spawn one `Agent(subagent_type="general-purpose")` **per repo that has fixable findings, all in parallel**.

**Sub-agent prompt:** Use the template from `@references/fix-prompt.md`, filling in `{repo_path}` and injecting the fixable findings for that repo from Step 3.

Wait for all repo fix sub-agents to complete.

Display consolidated results:
```
Auto-fix applied:
  {repo-1}: {N} fixes (naming: 2, version: 1, structure: 0, docs: 1)
  {repo-2}: {N} fixes (naming: 0, version: 1, structure: 2, docs: 0)

Tests after fix:
  {repo-1}: {pass}/{total} passing ✓
  {repo-2}: {pass}/{total} passing ✓

Unfixed (manual action needed):
  [D1-001] API surface gap — use /apcore-skills:sync --phase a --fix
  [D4-xxx] Doc inconsistency — use /apcore-skills:sync --phase b for deep check
  [D6-002] Dependency version — manually update {package}

Review changes:
  cd {repo-1} && git diff
  cd {repo-2} && git diff
```
