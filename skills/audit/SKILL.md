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

**APPLY EVERY APPLICABLE DIMENSION. EVIDENCE EVERY FINDING. A dimension returning zero findings — with a short note of what was checked — IS a valid result. Quota-filling manufactures false positives; unreachable / speculative findings are noise, not signal.**

## When to Use

- Before a major release to ensure ecosystem-wide consistency
- After adding a new SDK or integration to verify alignment
- Periodic health check (monthly recommended)
- When suspecting drift between implementations

## Command Format

```
/apcore-skills:audit [--scope core|mcp|integrations|all] [--fix] [--no-deep-chain] [--save report.md]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--scope` | **cwd** | Which repo group to audit. **If omitted, defaults to the current working directory's repo only.** Use `--scope all` for full ecosystem audit. |
| `--fix` | off | Auto-fix issues where safe |
| `--no-deep-chain` | off (D11 runs by default) | Skip D11 (cross-language deep-chain analysis). Use for fast audits where you only need D1–D10 shape-level checks. D11 adds one sub-agent per logical module; disabling saves time on large module sets. |
| `--save` | off | Save report to file |

## Audit Dimensions

The audit covers 11 dimensions, each checking specific aspects:

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
| D10 | **Contract Parity (Intent — SHAPE-LEVEL)** | **critical-warning** | **Behavioral contract parity — inputs validation, errors raised, side-effect order, return shape, async/thread-safe/pure/idempotent/reentrant properties — catches "same signature, different logic" bugs at the Contract tuple level. Plus: integration consumer-contract check (does this integration USE the core SDK per its current Contract?).** |
| D11 | **Deep-Chain Parity (Intent — CHAIN-LEVEL)** | **critical-inconclusive** | **Cross-language call-graph diff per logical module. Reads all N language implementations' source for the same module side-by-side and finds divergences that shape-level Contract comparison (D10) cannot see: bare-subscript / null-guard gaps, internal methods skipping validation that peers call, missing-registration into maps. Delegates to sync Step 4C — audit surfaces the findings as D11-{seq} entries. Runs when ≥2 same-type repos are in scope.** |

**D10 vs D11 — why both.** D10 extracts a shape (inputs/errors/side_effects tuples) from each repo and diffs the shapes. D11 reads the actual source code across languages and diffs call graphs. They are **complementary, not redundant** — D10 catches divergences visible in the declared contract; D11 catches divergences that only appear when you read the code. A bug where one language's public method silently skips an internal validation call its peers perform will pass D10 (the declared contract matches) but fail D11 (the call graph shows the skip). Both run by default; disabling either is opt-out.

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

Step 2 spawns **up to 11 parallel sub-agents** (one per dimension, all simultaneously) — D1–D10 run as parallel dimension sub-agents; **D11 delegates to `sync` Step 4C** (which itself spawns one sub-agent per logical module under its own orchestrator). D11's progress updates surface in the audit orchestrator's log just like any other dimension. Step 4 spawns **one parallel sub-agent per repo** for fixes. The main context never reads repo files directly.

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
| `core` | Core SDKs + `apcore/` doc repo | D1-D3, D5-D6, D8-D11 (D4 covers `apcore/` only) |
| `mcp` | MCP bridges + `apcore-mcp/` doc repo | D1-D3, D5-D6, D8-D11 (D4 covers `apcore-mcp/` only) |
| `integrations` | Framework integrations + auto-pulled core SDKs (per-integration language) + `apcore/` doc repo as read-only peers | D2-D9 on integration repos; **D10 Consumer Contract Check** verifies each integration uses its matching core SDK per the core SDK's current Contract. **D11 skipped** (integrations are single-language; no cross-language chain to diff). |
| `all` | All repos | All dimensions including D11 on core + mcp groups |

**D9 (Bloat & Redundancy) is always included.** It applies to every scope and every repo type — it is the apcore ecosystem's primary defense against the additive bias of skill-driven feature work.

**D10 (Contract Parity) is included in two modes:**
1. **Parity mode** — runs whenever ≥2 same-type repos are in scope (e.g., multiple core SDKs, multiple MCP bridges). Detects intent divergence across language implementations — the bug class where public signatures match but logic/purpose differs (e.g., one SDK validates inputs and the other doesn't; one emits an event and the other doesn't; one is thread-safe and the other isn't).
2. **Consumer Contract mode** — runs whenever at least one `integration` repo is in scope. The audit auto-pulls the matching core SDK (by language) and the `apcore/` doc repo as read-only peers, then verifies each integration uses the core SDK per its current Contract (input completeness, error handling, thread-safety assumption, deprecated API usage). See `references/dimension-prompts.md` D10 Step 4.

Both modes can run in the same audit invocation — a `--scope all` run exercises both. When the current scope has only 1 same-type repo AND no integrations, D10 is skipped with an INFO finding.

**D11 (Deep-Chain Parity) trigger rule.** Runs whenever ≥2 same-type impl repos are in scope AND D10's Parity mode is active (they share the "need peers to compare against" precondition). Skipped with INFO when:
- Only 1 impl repo in scope (no peer)
- Scope is `integrations` only (single-language chain analysis is code-forge:review's job)
- User passes `--no-deep-chain` (escape hatch for fast audits)

Display:
```
Audit scope: {scope} {("(from CWD)" if defaulted)}
Repos: {count} repositories
Dimensions: {list}
```

---

### Step 2: Execute Audit Dimensions (Sub-agents)

Spawn **all dimension sub-agents in parallel**. Dimensions D1–D10 each run as one parallel sub-agent (up to 10 simultaneously). **D11 runs as a delegated invocation of `sync` Step 4C** (see Step 2.D11 below) — the delegation itself is one sub-agent from the audit orchestrator's POV, which internally fans out to module-level sub-agents. All dimensions are fully independent.

**Sub-agent prompts:** Use the dimension-specific prompt templates from `@references/dimension-prompts.md`. Each dimension (D1–D10) has its own section with the full prompt template. Fill in `{repo_paths}` (and `{integration_repo_paths}` for D7, `{doc_repo_path}` for D10) from the scope determined in Step 1.

#### Step 2.D11: Deep-Chain Parity (delegates to sync Step 4C)

**Skip conditions** (all three must be false for D11 to run):
- `--no-deep-chain` flag present
- <2 impl repos in scope (after `--scope` resolution) OR scope is `integrations`-only
- D10 Parity mode was skipped (same precondition)

**Invocation.** Spawn a single `Agent(subagent_type="general-purpose")` tasked with running sync Step 4C internally. The prompt is:

```
Run /apcore-skills:sync {impl_repo_1},{impl_repo_2},...,{doc_repo} --phase a --internal-check=contract --deep-chain=on --save {ecosystem_root}/audit-d11-{YYYY-MM-DD}.md

Do NOT execute Phase B. Do NOT execute tester. Only Phase A is required, and within Phase A only Step 4C findings are needed — the rest (4.1–4.3, 4A, 4B) may run but will be discarded.

Return the parsed Step 4C findings in this exact format:

D11_MODULES_ANALYZED: {N}
D11_MODULES_FAILED: {N}
D11_MODULES_INCONCLUSIVE: {N}
D11_FINDINGS:
  - finding_id: A-D-{seq}
    severity: critical|warning|info|inconclusive
    type: semantic-divergence|missing-validation|missing-registration|defensive-gap|error-path-divergence|contract-gap|inconclusive
    module: {module_name}
    symbol: {ClassName.method_name}
    summary: {one-line}
    evidence: { {lang}: { file, line, snippet } }
    recommendation: {text}
    verification: static-inference
```

**Result merging.** Renumber the incoming `A-D-{seq}` ids as `D11-{seq}` to fit audit's dimension-id namespace. Preserve `verification: static-inference` on every merged finding. The full deep-chain details remain in `{audit-d11-{date}.md}` — audit's Step 3 report only shows the summary block (see §D11 SUMMARY in Step 3 report template).

**Failure modes.**
- If the delegated sync invocation fails entirely → emit one CRITICAL finding `[D11-FATAL] sync Step 4C delegation failed — manual run required` and include the sync invocation's error output in the report. Do NOT pretend D11 passed.
- If sync returns ≥1 `module_failed` or `module_inconclusive` → emit those modules as CRITICAL `[D11-{seq}]` findings with the reason. A module the skill could not analyze is itself a signal.
- If sync returns zero findings AND zero `module_failed` AND `confidence_notes` is empty → audit treats this as suspicious and emits a WARNING `[D11-SUSPECT] deep-chain returned clean but without trace evidence — re-run with higher verbosity`.

---

### Step 2.5: Noise-Control Validation (MANDATORY before Step 3)

After all dimension sub-agents return and findings are collected, run this validation pass over the merged findings BEFORE formatting the Step 3 report. The pass applies the Gate 6 (Factual Verifiability) and info-inflation rules from `@references/dimension-prompts.md` to every finding the sub-agents emitted — the gate is enforced at emission time by each sub-agent, but this orchestrator pass is the final line of defense against sub-agents that summarized evidence instead of pasting it.

Track drop counts per bucket — they surface in the Step 3 report summary.

**2.5.1 D10/D11 cross-dimension deduplication (applies FIRST, before gate 6):**

D10 (Contract Parity — shape-level) and D11 (Deep-Chain Parity — chain-level) are designed to be complementary, but by construction they can catch the same bug from two angles — D10 sees a spec-shape divergence and D11 sees the call-graph divergence underlying it. The same root-cause defect then appears as two findings, inflating both the critical and warning counts.

Scan every D11 finding's `detail` field for cross-reference markers:

- **Explicit mapping markers:** `(maps to D10-NNN)`, `(maps to D10-\d+)`, `(same as D10-NNN)`, `(see D10-NNN)`
- **Implicit same-root markers:** the D11 finding's `symbol` + `category` pair matches an existing D10 finding's `symbol` + `category` pair AND the D11 `detail` is a more specific instance of the D10 `detail` (contains the same defect keyword: same divergent method name, same error type, same canonicalization algorithm, etc.)

**Dedup rule — preserve D10, drop D11 dup:**

When a D11 finding is identified as a duplicate:
1. Find the target D10 finding by id (explicit) or by `(symbol, category)` pair (implicit).
2. Append D11's `location` AND D11's call-graph evidence to the D10 finding's `evidence` field as an **additional** citation block. Prefix with `[from D11-NNN chain-level]` so the reviewer can see both angles in one finding.
3. Drop the D11 finding from the findings list.
4. Track the drop as `n_d10_d11_dedup`.

**Rationale for preserving D10 over D11:**
- D10 carries the trust-boundary / contract-specification context that matters for severity calibration (Gate 3 analog)
- D10 findings are more actionable — they point to the spec shape that must align, not just one implementation's call chain
- The merged evidence (D10's shape-level + D11's chain-level) is strictly more useful than either alone

**Implicit-match safeguard — do NOT dedup when:**
- The two findings have different `severity` AND the difference represents a genuine severity disagreement (e.g., D10 flagged as warning, D11 flagged as critical because the chain reveals a reachable trigger D10 missed). In this case, **keep the higher-severity finding and drop the lower-severity one** — still count as dedup.
- The D11 finding is in a separate module from the D10 symbol and the `category` is `missing-registration` or `defensive-gap` (these are chain-specific defects that D10's shape-level view genuinely cannot see — not duplicates).

**Never dedup across dimensions other than D10↔D11.** Do not merge D9 dead-export findings into a D10 contract finding even if the root cause is the same stub function — different dimensions serve different consumers and severity audit trails.

Track the count. Surface in the Noise-Control header.

---

**2.5.2 Gate 6 verification scan (applies to critical, warning, info — all severities):**

Scan every finding's `detail`, `category`, and `evidence` fields for Gate 6 trigger phrases:

```
dead export | dead code | unused | unused_internal | unused_config | unused_dep
duplicate | duplicates | parallel_impl | parallel implementation | reimplements | copy of
only used in | only referenced in | never called | never invoked
zero references | zero reads | no callers
reachability | stale | scope creep | stub | noop | no-op
\d+ lines? | exceeds \d+ lines?
```

When a trigger matches, the finding MUST carry ONE of:
- A search command line (e.g., `grep -rn`, `rg`, equivalent) **PLUS** at least one matched-output line (format `{file}:{line}:{content}`, OR the explicit string `0 matches` / `no matches`)
- Explicit `{repo}/{path}:{line}` citations — for cross-repo claims both sides must be cited; for "only used in" claims the single site MUST be accompanied by a grep proving absence elsewhere
- For `dead_export` / `unused` / `reachability` claims, the evidence must span at least `src/` AND `tests/` (and `examples/` if present) — state the scope in evidence, e.g. `"grep -rn X src/ tests/ examples/"`

Findings failing this check are **dropped** (not downgraded — the factual claim is the load-bearing part of the finding; without verification it has no substance). Track as `n_unverified_claim`.

**2.5.3 Info-level nitpick blocklist (DROP rule, applies to severity=info only):**

Info findings are cosmetic by definition — they never reach `/code-forge:fix --review` (audit Step 3.1 severity map drops info) but they still consume reader attention in the ecosystem report. Drop info findings whose `detail` matches:

- Pure rename-for-clarity: `rename \w+ to \w+` without a named concrete ambiguity
- Style swap without named downside: `consider using X instead of Y`, `prefer X over Y`
- Pure formatting/casing: `camelCase vs snake_case` without the symbol crossing a language boundary (cross-language is a D2 issue and belongs at warning, not info)
- Packaging / binary name preferences: npm scope, bin name, `*.py` vs `*.pyi` layout — unless the audit scope explicitly includes packaging
- Comment-style: `add a comment explaining X` where X is described by the code's own name
- File-layout preferences: `move X to utils/`, `consolidate X under lib/` without a concrete coupling-cost demonstration

Track as `n_info_nitpick`.

**2.5.4 Info consolidation (MERGE rule):**

Group surviving info findings by `(repo, dimension, category)`. When a group has ≥3 findings, merge them into ONE themed info entry listing every site. Do NOT merge across repos or across dimensions — cross-repo / cross-dimension repetition often signals a real pattern worth preserving as distinct entries.

Themed merge format:
```
- severity: info
  repo: {repo-name}
  category: {dimension_category}
  detail: "{N} instances of {theme}: {brief theme description}. Sites: {file:line, file:line, ...}"
  fix: "{one consolidated fix instruction covering all sites}"
  evidence: "{the search command that enumerates the sites, plus the matched-line list}"
```

Track merged-away entries (original count − 1 per group) as `n_info_consolidated`.

**2.5.5 Track totals and surface in Step 3 header:**

Compute `n_total_drops = n_d10_d11_dedup + n_unverified_claim + n_info_nitpick + n_info_consolidated` and include a one-line `Noise-Control` header in the Step 3 report:

```
Noise-Control: {n_total_drops} findings suppressed · {n_d10_d11_dedup} d10-d11-deduplicated · {n_unverified_claim} unverified-factual-claim · {n_info_nitpick} info-nitpick · {n_info_consolidated} info-consolidated
```

If `n_unverified_claim > 0`, also print a per-dimension breakdown so the operator can see which sub-agent prompt is under-producing evidence (this feeds back into skill tuning):

```
  Unverified factual claims dropped by dimension: D9:{N}  D10:{N}  D1:{N}  ...
```

---

### Step 3: Aggregate and Display Report

Collect all findings from sub-agents. Aggregate by severity.

```
apcore-skills audit — Ecosystem Consistency Report

Date: {date}
Scope: {scope}
Repos audited: {count}
Noise-Control: {n_total_drops} findings suppressed · {n_d10_d11_dedup} d10-d11-deduplicated · {n_unverified_claim} unverified-factual-claim · {n_info_nitpick} info-nitpick · {n_info_consolidated} info-consolidated
{if n_unverified_claim > 0:}
  Unverified claims dropped by dimension: {D9: N, D10: N, D1: N, ...}

═══ SUMMARY ═══

  Dimension              | Critical | Warning | Info | Inconclusive
  D1 API Surface         |    2     |    3    |   1  |      —
  D2 Naming Conventions  |    0     |    5    |   3  |      —
  D3 Version Sync        |    1     |    0    |   0  |      —
  D4 Documentation       |    0     |    2    |   4  |      —
  D5 Test Coverage       |    0     |    1    |   2  |      —
  D6 Dependencies        |    1     |    2    |   0  |      —
  D7 Configuration       |    0     |    3    |   1  |      —
  D8 Project Structure   |    0     |    1    |   2  |      —
  D9 Bloat & Redundancy  |    1     |    8    |   5  |      —
  D10 Contract Parity    |    3     |    4    |   2  |      —
  D11 Deep-Chain Parity  |    5     |    2    |   0  |      3
  ─────────────────────────────────────────────────────────────
  TOTAL                  |   13     |   31    |  20  |      3

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

═══ CONTRACT PARITY REPORT (D10 — SHAPE-LEVEL) ═══

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

═══ DEEP-CHAIN PARITY REPORT (D11 — CHAIN-LEVEL) ═══

  Delegated to: sync Step 4C (report saved: {audit-d11-{date}.md})
  Modules analyzed: {N}
  Modules complete / failed / inconclusive: {n} / {n} / {n}
  Findings: critical {n} / warning {n} / info {n} / inconclusive {n}

  By finding type:
    semantic-divergence:    {N}
    missing-validation:     {N}
    missing-registration:   {N}
    defensive-gap:          {N}
    error-path-divergence:  {N}
    contract-gap:           {N}

  Top divergences (act on these first):
    1. [D11-004] missing-registration — Registry.discover (Rust discover_internal skips modules map insert)
    2. [D11-007] defensive-gap — Registry._discoverCustom (TS crashes on null discoverer result)
    3. [D11-011] missing-validation — Registry._discover_custom (Python bare subscript on entry["module_id"])

  D11 findings are cross-language intent divergences. All are MANUAL_REVIEW_ONLY — auto-fix cannot port logic semantics safely.

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
  Deep-Chain Parity (D11): {score}/100 — see shared/scoring.md for formula
```

**Score formulas:** Leanness (D9) and Contract Parity (D10) formulas are defined canonically in `shared/scoring.md`. Use those formulas — do not re-implement. Any threshold change (e.g., release-gate BLOCK threshold) must be updated there, not inline here.

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
| D4 | info (category=`contract_coverage`, detail mentions missing Contract fields) | warning | **Exception to the info-skip rule** — Contract block exists but is missing required fields (Inputs / Errors / Returns / Properties). These are actionable partial-contract gaps that should reach `/code-forge:fix --review`. Detect by matching `category == "contract_coverage"` AND detail mentions "missing field" or "incomplete". |
| D4 | info (other) | _(skip)_ | Minor docstring gaps, missing CHANGELOG badge, etc. |
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
| **D11** | **critical** | **blocker** | **`missing-registration`** — public method fails to update a map/collection peers update (breaks later `get`/`list` semantics) |
| **D11** | **critical** | **critical** | **`semantic-divergence` / `missing-validation` / `defensive-gap` / `error-path-divergence` / `contract-gap`** (cross-language chain divergences) |
| **D11** | **warning** | **warning** | **Order-only divergence** (same mutations, different order); **extra checkpoint/mutation in one language not in peers** |
| **D11** | **inconclusive** | **warning** | **Deep-chain sub-agent flagged uncertainty** — emit as warning with title prefix `[inconclusive]` and suggestion `"manual review required — static analysis could not determine whether divergence is intentional"`. Never silently dropped. |
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
- **Deep-chain fixes (D11 — MANUAL REVIEW ONLY, never auto-fix.)** Chain-level divergences require porting logic semantics between languages, which pattern-matching cannot do safely. Surface in MANUAL_REVIEW_ITEMS with the full evidence block and sub-agent recommendation. The operator may pipe the Step 3.1 review output to `/code-forge:fix --review`, but the fix agent itself must treat D11 findings as requiring human authorship — not copy-paste translation.
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
