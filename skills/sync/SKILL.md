---
name: sync
description: >
  Cross-language API consistency check and fix. Compares public API surfaces across
  all SDK implementations (Python, TypeScript, future languages), identifies gaps,
  signature mismatches, naming inconsistencies, and type misalignment. Can auto-fix
  naming issues and generate stubs for missing APIs.
instructions: >
  The protocol spec (PROTOCOL_SPEC.md) is the single source of truth.
  When implementations disagree, the protocol spec wins. Apply language-specific
  naming conventions when comparing (snake_case Python vs camelCase TypeScript
  is expected, but semantic differences like get_module vs findModule are bugs).
---

# Apcore Skills — Sync

Compare and synchronize public APIs across all language implementations of apcore core SDKs and MCP bridges.

## Iron Law

**THE PROTOCOL SPEC IS THE SINGLE SOURCE OF TRUTH. When implementations disagree, the protocol spec wins.**

## Anti-Rationalization Table

| Thought | Reality |
|---------|---------|
| "Python is the reference, just copy it" | The protocol spec is the authority. Python may have diverged too. |
| "This naming difference is just language convention" | Convention differences (snake_case vs camelCase) are expected. Semantic differences (get_module vs findModule) are bugs. |
| "Extra methods in one SDK are fine" | Language-specific additions are OK only if documented. Undocumented extras indicate drift. |
| "I'll just compare export counts" | Count matching is necessary but not sufficient. Signature-level comparison is required. |

## When to Use

- After adding features to one SDK and need to verify the other SDKs match
- Periodic consistency check across all language implementations
- Before a release to ensure all SDKs expose the same API surface
- When a new SDK is nearing feature parity with existing ones

## Command Format

```
/apcore-skills:sync [--fix] [--scope core|mcp|all] [--lang python,typescript,...]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--fix` | off | Auto-fix naming inconsistencies and generate stubs for missing APIs |
| `--scope` | `all` | Which repo group to sync: `core` (SDKs), `mcp` (bridges), `all` |
| `--lang` | all discovered | Comma-separated list of languages to compare |
| `--save` | off | Save report to file |

## Context Management

**All per-repo operations use parallel sub-agents.** The main context ONLY handles:
1. Orchestration — determining scope and spawning sub-agents
2. Protocol reference — reading the canonical spec (lightweight, one file)
3. Comparison logic — comparing structured summaries (not raw code)
4. Reporting — formatting results

Step 2 spawns **one sub-agent per repo, all simultaneously** for API extraction. Step 6 (auto-fix) spawns **one sub-agent per repo, all simultaneously** for applying fixes. The main context never reads repo source files directly.

## Workflow

```
Step 0 (ecosystem) → Step 1 (parse args) → Step 2 (extract APIs) → Step 3 (protocol reference) → Step 4 (compare) → Step 5 (report) → [Step 6 (fix)]
```

## Detailed Steps

### Step 0: Ecosystem Discovery

@../shared/ecosystem.md

Filter repos based on `--scope` and `--lang` flags.

---

### Step 1: Parse Arguments and Determine Scope

Parse `$ARGUMENTS` for flags:
- `--fix` → enable auto-fix mode
- `--scope core|mcp|all` → filter repo groups
- `--lang python,typescript,...` → filter languages

Determine comparison pairs:

| Scope | Repos to compare |
|---|---|
| `core` | All `core-sdk` repos (apcore-python, apcore-typescript, ...) |
| `mcp` | All `mcp-bridge` repos (apcore-mcp-python, apcore-mcp-typescript, ...) |
| `all` | Both groups separately |

**Single-SDK handling:** If a scope group contains fewer than 2 repos:
- Skip cross-implementation comparison for that group
- Display: "Only 1 {scope} repo found ({repo-name}). Cross-language comparison requires at least 2 implementations."
- Still run protocol compliance check (Step 3 + Step 4.3) as single-repo validation

Display:
```
Sync scope: {scope}
Languages: {lang1}, {lang2}, ...
Repos: {repo1}, {repo2}, ...
Mode: {report only | auto-fix}
```

---

### Step 2: Extract Public APIs (Parallel Sub-agents — One per Repo)

Spawn one `Task(subagent_type="general-purpose")` **per repo, all simultaneously in a single round of parallel Task calls**. Each sub-agent extracts the public API from one repo independently. Do NOT process repos sequentially.

**Sub-agent prompt:**

```
Extract the complete public API surface from {repo_path}.

Follow the API Extraction Protocol:

1. Read the main export file:
   - Python: src/{package}/__init__.py — extract all imports and __all__
   - TypeScript: src/index.ts — extract all export statements

2. For each exported symbol, read its source file and extract:
   - Kind: class | function | type | enum | constant | interface
   - Name (in this language's convention)
   - For classes: constructor params (name, type, required, default), all public methods with full signatures
   - For functions: params (name, type, required, default), return type, async flag
   - For enums: all member names and values
   - For types/interfaces: all fields (name, type, required)
   - For constants: name, type, value

3. Also extract:
   - Error classes: name, error code, parent class
   - Middleware interfaces: method signatures
   - Extension points: discoverer, validator, exporter interfaces

Return a structured summary in this exact format:

REPO: {repo-name}
LANGUAGE: {language}
VERSION: {version}
EXPORT_COUNT: {N}

CLASSES:
- {ClassName}
  constructor({param1}: {type1}, {param2}: {type2} = {default})
  methods:
    - {method_name}({params}) -> {return_type} [async]
    - ...

FUNCTIONS:
- {function_name}({params}) -> {return_type} [async]

ENUMS:
- {EnumName}: {MEMBER1}={value1}, {MEMBER2}={value2}, ...

TYPES:
- {TypeName}: {field1}: {type1}, {field2}: {type2}, ...

ERRORS:
- {ErrorName}(code={CODE}, parent={ParentError})

CONSTANTS:
- {NAME}: {type} = {value}

Error handling:
- If the repo path does not exist, return: REPO: {repo-name}, STATUS: NOT_FOUND
- If the main export file is missing or empty, return: REPO: {repo-name}, STATUS: NO_EXPORTS, REASON: {description}
- If individual source files cannot be read, skip them and note in the summary

Keep the summary concise but complete. Target ~3-5KB.
```

**Main context retains:** Each repo's structured API summary. Store as `api_summaries[repo_name]`.

---

### Step 3: Load Protocol Reference

Read the protocol spec for authoritative API definitions:

1. Read `{protocol_path}/PROTOCOL_SPEC.md` — extract the API contract sections
2. If `{protocol_path}/docs/features/*.md` exist — scan for additional API definitions
3. If `{protocol_path}/docs/spec/type-mapping.md` exists — load cross-language type mappings

Store as `protocol_api` — the canonical API that all implementations should match.

---

### Step 4: Compare APIs

@../shared/api-extraction.md

Apply the comparison protocol across all extracted APIs:

#### 4.1 Canonical Name Normalization

Convert all names to `snake_case` canonical form for matching:
- Python names: already snake_case (pass through)
- TypeScript names: camelCase → snake_case
- Go names: PascalCase → snake_case
- Rust names: snake_case (pass through)
- Java names: camelCase → snake_case

#### 4.2 Cross-Repo Comparison

For each pair of repos in the same scope group:

1. **Missing symbols** — present in one, absent in the other
2. **Signature mismatches** — same symbol, different params (after name normalization)
3. **Naming inconsistencies** — same symbol, but names don't follow convention translation
4. **Type mismatches** — same param, incompatible types (using type mapping table)
5. **Extra symbols** — present in one but not in protocol spec (language-specific additions)

#### 4.3 Protocol Compliance Check

For each repo, compare against the protocol API:
1. **Missing from protocol** — repo has symbols not defined in protocol
2. **Missing from repo** — protocol defines symbols not in repo
3. **Divergence** — repo implementation doesn't match protocol definition

---

### Step 5: Generate Report

Display the sync report:

```
apcore-skills sync — Cross-Language API Consistency Report

Scope: {scope} | Languages: {langs} | Date: {date}

═══ CORE SDKs ═══

Protocol compliance:
  apcore-python:     {N}/{total} symbols ({pct}%) ✓
  apcore-typescript:  {N}/{total} symbols ({pct}%) ⚠ {missing} missing

Cross-implementation comparison:
  Total symbols: {N}
  Matching: {N}
  Missing: {N}
  Signature mismatch: {N}
  Naming inconsistency: {N}
  Type mismatch: {N}

MISSING (in one but not the other):
  ❌ Registry.scan_directory()
     Present in: apcore-python
     Missing in: apcore-typescript
     Protocol: defined in PROTOCOL_SPEC.md §4.2

  ❌ Executor.executeWithTimeout()
     Present in: apcore-typescript
     Missing in: apcore-python
     Protocol: NOT in protocol (language-specific)

SIGNATURE MISMATCH:
  ⚠ Executor.execute()
    apcore-python:     (module_id: str, input: dict, context: Context | None = None) -> ExecutionResult
    apcore-typescript:  (moduleId: string, input: Record<string, unknown>) -> ExecutionResult
    Diff: missing `context` parameter in TypeScript

NAMING INCONSISTENCY:
  ⚠ Registry method: get_module (Python) vs findModule (TypeScript)
    Expected: get_module / getModule (canonical: get_module)

═══ MCP BRIDGES ═══
(same format)

═══ UNIMPLEMENTED PROTOCOL APIs ═══
(APIs defined in PROTOCOL_SPEC.md but not yet in ANY implementation)
  - {SymbolName} — defined in PROTOCOL_SPEC.md §{section}, 0 implementations
  - ...

═══ SUMMARY ═══
  Total issues: {N}
  Critical (missing/mismatch): {N}
  Warning (naming): {N}
  Info (extra symbols): {N}
  Unimplemented protocol APIs: {N}
```

If `--save` flag: write report to `{ecosystem_root}/sync-report-{date}.md`.

---

### Step 6: Auto-Fix (only with --fix flag)

If `--fix` was specified:

Group all findings by repo. Then spawn one `Task(subagent_type="general-purpose")` **per repo that has fixable findings, all in parallel**:

**Sub-agent prompt:**
```
Apply API sync fixes for {repo_path} ({language}).

Findings to fix:
{all findings for this repo from Step 5 — naming, missing, type issues}

Fix rules:

1. NAMING FIXES — For each naming inconsistency:
   - Canonical name: {canonical} → language convention: {expected_name}
   - Rename the function/method/class in its source file using Edit
   - Update the export in __init__.py / index.ts
   - Update any internal references within the same repo

2. MISSING API STUBS — For each missing symbol:
   - Generate a stub implementation in {language} with TODO markers
   - Match the signature from the reference implementation (canonical form)
   - Add the export to the main module file
   - Create a corresponding test stub in tests/

3. VERIFY — After all fixes:
   - Run the full test suite: {pytest --tb=short -q | npx vitest run}
   - If any test fails due to a fix: revert ONLY that specific fix and note it

Error handling: If test runner is not available, skip verification and note it.

Return:
REPO: {repo-name}
NAMING_FIXES: {count}
STUBS_GENERATED: {count}
TEST_RESULT: {pass|fail|skipped}
TEST_COUNTS: {passed}/{total}
REVERTED_FIXES: {list of fixes reverted due to test failure, or "none"}
FILES_MODIFIED: {list of files changed}
```

Wait for all repo fix sub-agents to complete.

Display consolidated results:
```
Auto-fix results:
  apcore-typescript: 3 naming fixes, 1 stub generated, tests 287/287 ✓
  apcore-mcp-typescript: 1 naming fix, 0 stubs, tests 112/112 ✓

Modified repos (uncommitted):
  apcore-typescript: 4 files changed
  apcore-mcp-typescript: 1 file changed

Next steps:
  Review changes: cd {repo} && git diff
  Commit: /apcore-skills:release or manual git commit
```
