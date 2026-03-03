---
name: docs
description: >
  Documentation synchronization across all apcore ecosystem repositories. Ensures
  READMEs have consistent structure, API references match implementations,
  usage examples work, CHANGELOGs follow the standard format, and all docs
  reference the correct versions and API signatures.
instructions: >
  All per-repo audit and fix operations MUST use parallel sub-agents (one per repo).
  NEVER iterate repos serially in the main context. The main context only orchestrates
  and aggregates results.
---

# Apcore Skills — Docs

Synchronize documentation across all apcore ecosystem repositories.

## Iron Law

**DOCUMENTATION MUST MATCH THE CODE. If the code says `get_module()` but the README says `find_module()`, that's a bug.**

## When to Use

- After a release to ensure all docs reference the correct version
- After API changes to sync usage examples across repos
- Periodic documentation quality check
- When adding a new SDK/integration and need to update cross-references

## Command Format

```
/apcore-skills:docs [--scope readme|changelog|api|examples|all] [--fix]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--scope` | `all` | What to check: `readme`, `changelog`, `api`, `examples`, or `all` |
| `--fix` | off | Auto-fix documentation issues |
| `--save` | off | Save report to file |

## Documentation Standards

### README.md Structure (all repos)

Every repo README must contain these sections in order:

1. **Title and badges** — Package name, version badge, coverage badge, license badge
2. **Description** — One-paragraph description of what this package does
3. **Installation** — Package manager install commands with correct package name
4. **Quick Start** — Minimal working code example (must use current API)
5. **Features** — Bullet list of key features
6. **Configuration** — Key configuration options (for integrations: APCORE_* settings table)
7. **API Overview** — Key classes/functions with brief descriptions
8. **Documentation** — Link to full docs (apcore docs site)
9. **Contributing** — Link to contribution guide
10. **License** — MIT

### CHANGELOG.md Format

Follow [Keep a Changelog](https://keepachangelog.com/) format:
```markdown
# Changelog

## [X.Y.Z] - YYYY-MM-DD
### Added
### Changed
### Fixed
### Breaking
```

### API Reference Accuracy

Code examples in README and docs must:
- Use actual exported function/class names (not outdated names)
- Use correct parameter names and order
- Use correct import paths
- Be runnable without modification

## Context Management

**All per-repo work is offloaded to parallel sub-agents.** The main context ONLY handles:
1. Orchestration — deciding which scopes to audit and which repos to target
2. Aggregation — collecting structured results from sub-agents
3. Reporting — formatting and displaying the consolidated report

For each scope in Step 2, spawn **one sub-agent per repo, all simultaneously**. This ensures:
- No context window bloat from reading multiple repos' files
- Maximum parallelism across repos
- Consistent structured output from each sub-agent

For Step 4 (fix), spawn **one sub-agent per repo** to apply all fixes for that repo in parallel.

## Workflow

```
Step 0 (ecosystem) → 1 (parse args) → 2 (parallel audit per scope) → 3 (report) → [4 (parallel fix per repo)]
```

## Detailed Steps

### Step 0: Ecosystem Discovery

@../shared/ecosystem.md

---

### Step 1: Parse Arguments

Parse `$ARGUMENTS` for scope and fix flags. Determine which repos and documentation aspects to check.

Determine active scopes:
- `--scope readme` → only readme audit
- `--scope changelog` → only changelog audit
- `--scope api` → only API cross-reference audit
- `--scope examples` → only examples audit
- `--scope all` (default) → all 4 scopes

---

### Step 2: Audit Documentation (Parallel Sub-agents per Scope)

For each active scope, spawn **all repo sub-agents simultaneously in a single round of parallel `Task` calls**. Do NOT iterate repos one at a time.

#### Scope: readme

Spawn one `Task(subagent_type="general-purpose")` **per repo, all in parallel**:

**Sub-agent prompt:**
```
Audit README.md in {repo_path}.

1. Read README.md
2. Check for required sections (Title, Installation, Quick Start, Features, Configuration, API Overview, Docs link, License)
3. For Installation section: verify package name matches build config (pyproject.toml/package.json)
4. For Quick Start: extract code examples and verify import names match actual exports in __init__.py/index.ts
5. For API Overview: verify listed classes/functions exist in public API
6. For version references: verify they match current version in build config

Read the actual source files to verify:
- {repo_path}/src/{package}/__init__.py or src/index.ts (for API verification)
- {repo_path}/pyproject.toml or package.json (for version/package name)

Error handling: If README.md does not exist, return SECTIONS_MISSING: [all].

Return findings in this exact format:
SCOPE: readme
REPO: {repo-name}
SECTIONS_PRESENT: {list}
SECTIONS_MISSING: {list}
API_MISMATCHES: {list of outdated API references with correct values}
VERSION_MISMATCHES: {list}
INSTALL_CORRECT: true|false
FINDING_COUNT: {N}
FINDINGS:
- severity: {warning|info}
  detail: {description}
  location: {file:section}
  fix: {suggested fix}
```

Wait for all repo sub-agents to complete. Collect results into `readme_findings[]`.

#### Scope: changelog

Spawn one `Task(subagent_type="general-purpose")` **per repo, all in parallel**:

**Sub-agent prompt:**
```
Audit CHANGELOG.md in {repo_path}.

1. Check CHANGELOG.md exists and is non-empty
2. Read the build config to get current version (pyproject.toml or package.json)
3. Verify latest CHANGELOG entry matches current version
4. Check format: follows Keep a Changelog (## [X.Y.Z] - YYYY-MM-DD)
5. Check date format: YYYY-MM-DD
6. Check categories are standard (Added, Changed, Fixed, Breaking)
7. Check for empty sections (header present but no content)

Error handling: If CHANGELOG.md does not exist, report as single finding.

Return findings in this exact format:
SCOPE: changelog
REPO: {repo-name}
CURRENT_VERSION: {version from build config}
CHANGELOG_LATEST: {version from latest CHANGELOG entry, or "missing"}
FORMAT_VALID: true|false
FINDING_COUNT: {N}
FINDINGS:
- severity: {warning|info}
  detail: {description}
  location: CHANGELOG.md:{line if applicable}
  fix: {suggested fix}
```

Wait for all repo sub-agents to complete. Collect results into `changelog_findings[]`.

#### Scope: api

Spawn one `Task(subagent_type="general-purpose")` **per repo, all in parallel**:

**Sub-agent prompt:**
```
Cross-reference documentation with actual API in {repo_path}.

1. Read the main export file to get the actual public API:
   - Python: src/{package}/__init__.py — extract all public names
   - TypeScript: src/index.ts — extract all export names
2. Search ALL markdown files in the repo (README.md, docs/**/*.md) for references to API symbols:
   - Class names, function names, method names, enum values
   - Import statements in code examples
   - Parameter names in usage examples
3. For each API reference found in docs:
   - Check if the symbol actually exists in the current public API
   - Check if parameter names/order match the actual signature
   - Check if import paths are correct
4. Flag any outdated, renamed, or removed API references

Error handling: If no public API exports found (empty __init__.py or no index.ts), return FINDING_COUNT: 0 with note.

Return findings in this exact format:
SCOPE: api
REPO: {repo-name}
PUBLIC_API_COUNT: {N symbols in actual API}
DOC_REFERENCES_CHECKED: {N references found in docs}
FINDING_COUNT: {N}
FINDINGS:
- severity: {critical|warning|info}
  detail: {description}
  location: {file:line}
  actual_api: {correct name/signature}
  doc_says: {what the doc currently says}
  fix: {suggested fix}
```

Wait for all repo sub-agents to complete. Collect results into `api_findings[]`.

#### Scope: examples

Spawn one `Task(subagent_type="general-purpose")` **per repo that has examples/ or demo/ directory, all in parallel**:

**Sub-agent prompt:**
```
Audit example code in {repo_path}.

1. Scan for example directories: examples/, demo/, example/
2. For each example found:
   a. Read example source files (*.py, *.ts, *.js)
   b. Extract import statements and API usage
   c. Cross-reference against actual public API in src/
   d. Check if example dependencies (in example's build config) reference correct versions
3. Check Docker files if present:
   a. Dockerfile uses reasonable base image
   b. docker-compose.yml references correct service names
4. Check example README exists with setup instructions

Error handling: If no examples directory exists, return FINDING_COUNT: 0 with note "No examples directory".

Return findings in this exact format:
SCOPE: examples
REPO: {repo-name}
EXAMPLE_DIRS: {list of example directories found}
FINDING_COUNT: {N}
FINDINGS:
- severity: {warning|info}
  detail: {description}
  location: {file:line}
  fix: {suggested fix}
```

Wait for all repo sub-agents to complete. Collect results into `examples_findings[]`.

---

### Step 3: Generate Report

Aggregate all findings from all scopes. Display consolidated report:

```
apcore-skills docs — Documentation Sync Report

Date: {date}
Scope: {scope}
Repos checked: {count}

═══ SUMMARY ═══

  Repo                    | README | CHANGELOG | API Refs | Examples
  apcore-python           |   ✓    |     ✓     |    ✓     |    —
  apcore-typescript        |   ⚠    |     ✓     |    ⚠     |    —
  django-apcore           |   ✓    |     ✓     |    ✓     |    ✓
  flask-apcore            |   ⚠    |     ⚠     |    ✓     |    ✓

═══ FINDINGS ═══

[README] apcore-typescript
  ⚠ Missing section: Configuration
  ⚠ Quick Start uses `findModule()` but API exports `getModule()`
  ⚠ Installation shows version 0.6.0, current is 0.7.1

[CHANGELOG] flask-apcore
  ⚠ Latest entry is v0.2.0 but current version is v0.3.0 — missing changelog entry

[API] apcore-typescript
  ⚠ docs/api/registry.md references `Registry.scanDir()` but actual method is `Registry.scanDirectory()`

Total findings: {N} (README: {n}, CHANGELOG: {n}, API: {n}, Examples: {n})
```

If `--save` flag: write report to specified path.

---

### Step 4: Auto-Fix (only with --fix flag)

Spawn one `Task(subagent_type="general-purpose")` **per repo that has findings, all in parallel**:

**Sub-agent prompt:**
```
Apply documentation fixes for {repo_path}.

Findings to fix:
{all findings for this repo from Step 2, across all scopes}

Fix rules:

README fixes:
- Add missing sections with template content (use existing repo context for content)
- Update version references to {current_version}
- Update package name to {correct_package_name}
- Update API references: rename outdated names to current names (preserve surrounding context)

CHANGELOG fixes:
- If latest version has no entry, add: ## [{current_version}] - {today} with empty categories
- Fix date format to YYYY-MM-DD
- Add missing standard categories (Added, Changed, Fixed)

API reference fixes:
- Update function/class/method names to match current public API
- Update parameter names in code examples
- Update import paths

Example fixes:
- Update dependency versions in example build configs
- Update API usage in example code

After applying fixes:
1. List all files modified with a summary of changes
2. Do NOT commit — leave changes staged for user review

Return:
REPO: {repo-name}
FILES_MODIFIED: {count}
CHANGES:
- file: {path}
  action: {what was changed}
```

Wait for all repo fix sub-agents to complete.

Display consolidated fix results:
```
Documentation fixes applied:
  apcore-typescript: 2 files modified
    README.md: updated Quick Start (findModule → getModule), version (0.6.0 → 0.7.1)
    docs/api/registry.md: updated method name (scanDir → scanDirectory)
  flask-apcore: 1 file modified
    CHANGELOG.md: added v0.3.0 entry stub

Changes are uncommitted. Review with:
  cd {repo} && git diff
```
