---
name: audit
description: >
  Deep cross-repo consistency audit for the apcore ecosystem. Checks API surface
  alignment, naming conventions, version synchronization, documentation quality,
  test coverage, dependency alignment, and configuration consistency across all
  repos. Generates a detailed report with severity-classified findings.
---

# Apcore Skills — Audit

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
| `--scope` | `all` | Which repo group to audit |
| `--fix` | off | Auto-fix issues where safe |
| `--save` | off | Save report to file |

## Audit Dimensions

The audit covers 8 dimensions, each checking specific aspects:

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

Step 2 spawns **up to 8 parallel sub-agents** (one per dimension, all simultaneously). Step 4 spawns **one parallel sub-agent per repo** for fixes. The main context never reads repo files directly.

## Workflow

```
Step 0 (ecosystem) → Step 1 (parse args) → Step 2 (parallel audits) → Step 3 (report) → [Step 4 (fix)]
```

## Detailed Steps

### Step 0: Ecosystem Discovery

@../shared/ecosystem.md

---

### Step 1: Parse Arguments and Plan Audit

Parse `$ARGUMENTS` for flags. Determine which repos and dimensions to audit based on scope.

| Scope | Repos | Dimensions |
|---|---|---|
| `core` | Core SDKs | D1-D3, D5-D6, D8 |
| `mcp` | MCP bridges | D1-D3, D5-D6, D8 |
| `integrations` | Framework integrations | D2-D8 (no cross-API sync) |
| `all` | All repos | All dimensions |

Display:
```
Audit scope: {scope}
Repos: {count} repositories
Dimensions: D1-D8 (all)
```

---

### Step 2: Execute Audit Dimensions (Sub-agents)

Spawn **all dimension sub-agents in parallel (up to 8 simultaneously)**. Each sub-agent audits exactly 1 dimension. All dimensions are fully independent — no batching or serialization needed.

#### Sub-agent: D1 — API Surface Audit

**Prompt:**
```
Audit API surface consistency across apcore SDK implementations.

Repos to compare: {repo_paths}

For each repo:
1. Read the main export file (__init__.py / index.ts)
2. Count total exports
3. Categorize: classes, functions, types, enums, constants, errors
4. For each class: list constructor params and public method names

Compare across repos:
- Missing symbols (in one, not the other)
- Method count mismatches per class
- Constructor param count mismatches

Return findings in format:
DIMENSION: D1 — API Surface
FINDING_COUNT: {N}
FINDINGS:
- severity: {critical|warning|info}
  repo: {repo-name}
  detail: {description}
  location: {file:line if applicable}
  fix: {suggested fix}
```

#### Sub-agent: D2 — Naming Conventions Audit

**Prompt:**
```
Audit naming conventions across apcore ecosystem repos.

Repos: {repo_paths}

Check against conventions:
- Python: snake_case files, snake_case functions, PascalCase classes
- TypeScript: kebab-case files, camelCase functions, PascalCase classes
- Package names match convention (snake_case for Python, kebab-case for npm)
- Error class names end with "Error"
- Enum names are PascalCase, enum values are UPPER_SNAKE

Scan all source files in each repo:
1. Check filenames in src/ directory
2. Grep for class/function definitions and verify naming
3. Check import/export names in main module file
4. Verify error classes follow naming pattern

Error handling: If a repo path does not exist or has no src/ directory, report as:
- severity: info, detail: "Repo {name} has no source files to audit"

Return findings in this exact format:
DIMENSION: D2 — Naming Conventions
FINDING_COUNT: {N}
FINDINGS:
- severity: {critical|warning|info}
  repo: {repo-name}
  detail: {description}
  location: {file:line if applicable}
  fix: {suggested fix}
```

#### Sub-agent: D3 — Version Sync Audit

**Prompt:**
```
Audit version synchronization across apcore ecosystem.

Repos: {repo_paths with types}

Check:
1. Core SDK versions must match (major.minor): {core repos}
2. MCP bridge versions must match (major.minor): {mcp repos}
3. Within each repo, version must be consistent across all version files
   - Python: pyproject.toml version == __init__.py __version__
   - TypeScript: package.json version == src/index.ts VERSION (if present)
4. Integration repos: dependency versions reference compatible core SDK versions

Error handling: If a build config file is missing or malformed, report as a warning finding rather than failing.

Return findings in this exact format:
DIMENSION: D3 — Version Sync
FINDING_COUNT: {N}
FINDINGS:
- severity: {critical|warning|info}
  repo: {repo-name}
  detail: {description}
  location: {file:line if applicable}
  fix: {suggested fix}
```

#### Sub-agent: D4 — Documentation Audit

**Prompt:**
```
Audit documentation quality across apcore ecosystem.

Repos: {repo_paths}

For each repo check:
1. README.md exists and contains: description, installation, quick start, link to docs
2. CHANGELOG.md exists and follows Keep a Changelog format
3. LICENSE file exists
4. Key source files have docstrings/JSDoc
5. Public API methods have parameter documentation
6. Examples directory exists (for integrations)

Error handling: If a repo path does not exist, skip it and report as info finding.

Return findings in this exact format:
DIMENSION: D4 — Documentation
FINDING_COUNT: {N}
FINDINGS:
- severity: {critical|warning|info}
  repo: {repo-name}
  detail: {description}
  location: {file if applicable}
  fix: {suggested fix}
```

#### Sub-agent: D5 — Test Coverage Audit

**Prompt:**
```
Audit test coverage across apcore ecosystem.

Repos: {repo_paths}

For each repo:
1. Check tests/ directory exists
2. Count test files
3. Map source files to test files (check for coverage gaps)
4. Run test suite and capture results:
   - Python: first check if pytest is available (`python -m pytest --version`); if not, report as finding instead of running
   - TypeScript: first check if vitest is available (`npx vitest --version`); if not, report as finding instead of running
   - Python: `pytest --tb=short -q`
   - TypeScript: `npx vitest run`
5. If coverage tool available, capture coverage percentage

Error handling:
- If dependencies are not installed (import errors, module not found), report as: severity=warning, detail="Test dependencies not installed for {repo}"
- If test runner is not found, report as: severity=warning, detail="Test runner not available for {repo}"
- Do NOT fail the entire audit if one repo's tests can't run

Return findings in this exact format:
DIMENSION: D5 — Test Coverage
FINDING_COUNT: {N}
FINDINGS:
- severity: {critical|warning|info}
  repo: {repo-name}
  detail: {description}
  location: {file if applicable}
  fix: {suggested fix}
TEST_RESULTS:
- repo: {repo-name}
  status: {pass|fail|skipped}
  total: {N}
  passed: {N}
  failed: {N}
  coverage: {pct or "unknown"}
```

#### Sub-agent: D6 — Dependencies Audit

**Prompt:**
```
Audit dependency alignment across apcore ecosystem.

Repos: {repo_paths}

Check:
1. Core SDK dependencies: schema validation lib versions match expectations
2. MCP bridge dependencies: MCP SDK versions are compatible
3. Integration dependencies: core SDK version references are up-to-date
4. No duplicate dependencies with different versions across repos
5. Dev dependencies include linter (ruff/eslint), type checker (mypy/tsc), test framework
6. No known vulnerability patterns in pinned versions

Error handling: If a build config file is missing, report as: severity=warning, detail="No build config found for {repo}"

Return findings in this exact format:
DIMENSION: D6 — Dependencies
FINDING_COUNT: {N}
FINDINGS:
- severity: {critical|warning|info}
  repo: {repo-name}
  detail: {description}
  location: {file:line if applicable}
  fix: {suggested fix}
```

#### Sub-agent: D7 — Configuration Audit (integrations only)

**Prompt:**
```
Audit APCORE_* configuration consistency across framework integrations.

Repos: {integration_repo_paths}

For each integration:
1. Read config.py/config.ts — search in src/{package}/ directory
2. Extract all APCORE_* settings with types and defaults
3. Compare settings across integrations — same settings should have same types and defaults

Required settings (must be present in all):
- APCORE_ENABLED, APCORE_DEBUG, APCORE_SCANNERS
- APCORE_INCLUDE_PATHS, APCORE_EXCLUDE_PATHS
- APCORE_MODULE_PREFIX, APCORE_AUTH_ENABLED
- APCORE_TRANSPORT, APCORE_HOST, APCORE_PORT

Error handling: If config file not found in a repo, report as: severity=warning, detail="Config file not found for {repo}"

Return findings in this exact format:
DIMENSION: D7 — Configuration
FINDING_COUNT: {N}
FINDINGS:
- severity: {critical|warning|info}
  repo: {repo-name}
  detail: {description}
  location: {file:line if applicable}
  fix: {suggested fix}
CONFIG_MATRIX:
- setting: {APCORE_SETTING}
  {repo-1}: {type}={default}
  {repo-2}: {type}={default}
  consistent: true|false

Target ~2-3KB. If more than 20 settings exist, only list inconsistent settings in the matrix and summarize consistent ones as a count.
```

#### Sub-agent: D8 — Project Structure Audit

**Prompt:**
```
Audit project structure consistency across apcore ecosystem.

Repos: {repo_paths}

Check against conventions:
- Core SDKs: has src/ with expected subdirectories (middleware/, registry/, schema/, observability/, utils/)
- MCP bridges: has src/ with expected subdirectories (server/, auth/, adapters/, converters/)
- Integrations: has src/ with expected structure (scanners/, output/, cli)
- All repos: has tests/, .gitignore, README.md, CHANGELOG.md, LICENSE, build config

Error handling: If a repo directory does not exist or is empty, report as: severity=info, detail="Repo {name} is empty or placeholder"

Return findings in this exact format:
DIMENSION: D8 — Project Structure
FINDING_COUNT: {N}
FINDINGS:
- severity: {critical|warning|info}
  repo: {repo-name}
  detail: {description}
  location: {directory or file}
  fix: {suggested fix}
```

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
  ─────────────────────────────────────────────────
  TOTAL                  |    4     |   17    |  13

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

═══ HEALTH SCORE ═══

  Overall: {score}/100
  API Consistency: {score}/100
  Naming: {score}/100
  Version Sync: {score}/100
  Documentation: {score}/100
  Test Coverage: {score}/100
  Dependencies: {score}/100
```

If `--save` flag: write full report to specified path.

---

### Step 4: Auto-Fix (only with --fix flag)

Group fixable findings by repo. Separate unfixable findings for reporting.

**Unfixable (skip and report):**
- API surface fixes (complex — delegate to `/apcore-skills:sync --fix`)
- Dependency fixes (risky — show as recommendations only)

**Fixable (per-repo parallel sub-agents):**

Spawn one `Task(subagent_type="general-purpose")` **per repo that has fixable findings, all in parallel**:

**Sub-agent prompt:**
```
Apply audit fixes for {repo_path}.

Fixable findings:
{all fixable findings for this repo from Step 3}

Fix rules (apply in order):
1. NAMING FIXES (D2) — Rename files/symbols to match conventions
2. VERSION FIXES (D3) — Update version strings for consistency
3. STRUCTURE FIXES (D8) — Create missing directories/files with stubs
4. DOC FIXES (D4) — Add missing README sections, fix CHANGELOG format

After all fixes:
- Run the full test suite ({pytest --tb=short -q | npx vitest run})
- If tests fail: identify which fix caused it, revert ONLY that fix
- Leave all changes uncommitted

Error handling: If test runner is not available, skip verification and note it.

Return:
REPO: {repo-name}
FIXES_APPLIED: {count}
FIXES_REVERTED: {count}
TEST_RESULT: {pass|fail|skipped}
TEST_COUNTS: {passed}/{total}
CHANGES:
- dimension: {D2|D3|D4|D8}
  file: {path}
  action: {what was changed}
```

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
  [D1-001] API surface gap — use /apcore-skills:sync --fix
  [D6-002] Dependency version — manually update {package}

Review changes:
  cd {repo-1} && git diff
  cd {repo-2} && git diff
```
