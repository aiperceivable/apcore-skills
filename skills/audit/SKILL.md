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

The audit covers 9 dimensions, each checking specific aspects:

| # | Dimension | Severity Range | Description |
|---|---|---|---|
| D1 | API Surface | critical-warning | Public API alignment across languages |
| D2 | Naming Conventions | critical-warning | File/class/function naming per language rules |
| D3 | Version Sync | critical-info | Version alignment within sync groups |
| D4 | Documentation | warning-info | README, CHANGELOG, docstring completeness |
| D5 | Test Coverage | warning-info | Test file existence and coverage metrics |
| D6 | Dependencies | critical-warning | Dependency versions and compatibility |
| D7 | Configuration | warning-info | APCORE_* settings consistency across integrations |
| D8 | Project Structure | warning-info | File/directory layout per conventions |
| D9 | **Bloat & Redundancy** | **critical-info** | **Dead exports, duplicate symbols, parallel implementations, LOC growth, unused config, scope creep** |

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

Step 2 spawns **up to 9 parallel sub-agents** (one per dimension, all simultaneously). Step 4 spawns **one parallel sub-agent per repo** for fixes. The main context never reads repo files directly.

## Workflow

```
Step 0 (ecosystem) → Step 1 (parse args) → Step 2 (parallel audits) → Step 3 (report) → [Step 4 (fix)]
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
   - `core-sdk` repo → audit only this repo, dimensions D1-D3, D5-D6, D8-D9
   - `mcp-bridge` repo → audit only this repo, dimensions D1-D3, D5-D6, D8-D9
   - `integration` repo → audit only this repo, dimensions D2-D9
   - `protocol`/`docs-site` repo → audit documentation dimensions (D4) and bloat (D9) for this repo
   - `shared-lib`/`tooling` repo → audit D2 (naming), D4 (docs), D5 (tests), D8 (structure), D9 (bloat) for this repo
   - CWD not an apcore repo → use `AskUserQuestion` to ask: "CWD is not an apcore repo. Which repo do you want to audit?" with options from `repos[]` names + "All repos (full ecosystem audit)"
3. Display: "Scope: {repo-name} (from CWD). Use --scope all for full ecosystem audit."

**If `--scope` IS specified:** use explicit scope.

#### 1.2 Scope → Repos & Dimensions

| Scope | Repos | Dimensions |
|---|---|---|
| `core` | Core SDKs | D1-D3, D5-D6, D8-D9 |
| `mcp` | MCP bridges | D1-D3, D5-D6, D8-D9 |
| `integrations` | Framework integrations | D2-D9 (no cross-API sync) |
| `all` | All repos | All dimensions |

**D9 (Bloat & Redundancy) is always included.** It applies to every scope and every repo type — it is the apcore ecosystem's primary defense against the additive bias of skill-driven feature work.

Display:
```
Audit scope: {scope} {("(from CWD)" if defaulted)}
Repos: {count} repositories
Dimensions: {list}
```

---

### Step 2: Execute Audit Dimensions (Sub-agents)

Spawn **all dimension sub-agents in parallel (up to 9 simultaneously)**. Each sub-agent audits exactly 1 dimension. All dimensions are fully independent — no batching or serialization needed.

**Sub-agent prompts:** Use the dimension-specific prompt templates from `@references/dimension-prompts.md`. Each dimension (D1–D9) has its own section with the full prompt template. Fill in `{repo_paths}` (and `{integration_repo_paths}` for D7) from the scope determined in Step 1.

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
  ─────────────────────────────────────────────────
  TOTAL                  |    5     |   25    |  18

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

═══ HEALTH SCORE ═══

  Overall: {score}/100
  API Consistency: {score}/100
  Naming: {score}/100
  Version Sync: {score}/100
  Documentation: {score}/100
  Test Coverage: {score}/100
  Dependencies: {score}/100
  Leanness (D9):     {score}/100
```

**Leanness score formula:** Start at 100. Subtract 5 per `critical` D9 finding, 2 per `warning`, 0.5 per `info`. Floor at 0. A leanness score below 70 indicates the repo needs a dedicated cleanup pass before the next release.

If `--save` flag: write full report to specified path.

---

### Step 4: Auto-Fix (only with --fix flag)

Group fixable findings by repo. Separate unfixable findings for reporting.

**Unfixable (skip and report):**
- API surface fixes (complex — delegate to `/apcore-skills:sync --phase a --fix`)
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
