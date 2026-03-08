---
name: sync
description: >
  Unified cross-language consistency verification and documentation alignment.
  Phase A: verifies feature specs and protocol spec match all language implementations
  (classes, functions, parameters, return types) via itemized checklist comparison.
  Phase B: verifies all documentation (PRD, SRS, Tech Design, Test Plan, Feature Specs,
  PROTOCOL_SPEC, README, examples) is internally consistent and free of contradictions.
  Covers both apcore core SDKs and apcore-mcp bridges.
instructions: >
  The documentation repos (apcore/, apcore-mcp/) are the single source of truth.
  Phase A MUST complete before Phase B begins — Phase B uses Phase A's verified
  API surface as its reference. Never skip a phase. Never skip a checklist item.
  CHANGELOG is a release artifact, NOT a documentation consistency concern.
---

# Apcore Skills — Sync

Unified consistency verification across all apcore ecosystem documentation and implementations.

## Iron Law

**DOCUMENTATION REPOS ARE THE SINGLE SOURCE OF TRUTH. Phase A verifies code matches specs. Phase B verifies docs are internally consistent. Never skip a phase. Never skip a checklist item.**

## Anti-Rationalization Table

| Thought | Reality |
|---------|---------|
| "Python is the reference, just copy it" | The documentation repo is the authority. Python may have diverged too. |
| "This naming difference is just language convention" | Convention differences (snake_case vs camelCase) are expected. Semantic differences (get_module vs findModule) are bugs. |
| "Extra methods in one SDK are fine" | Language-specific additions are OK only if documented. Undocumented extras indicate drift. |
| "I'll just compare export counts" | Count matching is necessary but not sufficient. Signature-level comparison is required. |
| "Docs look close enough" | If the code says `get_module()` but the README says `find_module()`, that is a bug. Every symbol must match exactly. |
| "I can check docs without verifying code first" | Phase B depends on Phase A. If Phase A has not established ground truth, docs verification is comparing against potentially wrong code. |
| "Checking a few symbols is representative" | Build the complete checklist. Compare every item. Partial checks create false confidence. |
| "CHANGELOG has the wrong API name" | CHANGELOG is a release artifact, not documentation. Leave it to the release skill. |
| "PRD is product-level, no need to check against code" | If the PRD says a feature exists but no implementation matches, that is a gap. Every layer must agree. |

## When to Use

- After adding features to one SDK — verify all SDKs and their docs match
- Periodic consistency check across all language implementations
- Before a release to ensure all SDKs expose the same API surface and docs are accurate
- After API changes to sync usage examples and documentation across repos
- When a new SDK is nearing feature parity with existing ones
- After updating PRD/SRS/Tech Design — verify downstream docs and code still match

## Command Format

```
/apcore-skills:sync [repo1,repo2,...] [--phase a|b|all] [--fix] [--scope core|mcp|all] [--lang python,typescript,...] [--save]
```

| Argument / Flag | Default | Description |
|------|---------|-------------|
| positional repos | — | Comma-separated repo names to sync. See **Positional Repo Arguments** below. |
| `--phase` | `all` | Which phase to run: `a` (spec vs implementation), `b` (documentation internal consistency), `all` (A then B) |
| `--fix` | off | Auto-fix issues (naming, stubs, doc references) |
| `--scope` | **cwd** | Which group: `core`, `mcp`, `all`. **If omitted and no positional repos, defaults to the current working directory's repo only.** Use `--scope all` to scan all repos. |
| `--lang` | all discovered | Comma-separated list of languages to compare |
| `--save` | off | Save report to file |

### Positional Repo Arguments

Positional repo names control **exactly** which repos are included. They take priority over `--scope` and CWD-based defaults.

**Multiple repos (explicit set):**
```
/apcore-skills:sync apcore,apcore-typescript,apcore-python
```
Syncs exactly these 3 repos — no expansion, no auto-discovery. The doc repo and impl repos are determined from the provided list:
- If a `protocol` repo (e.g., `apcore`) is in the list → it becomes `doc_repo` for core scope
- If a `docs-site` repo (e.g., `apcore-mcp`) is in the list → it becomes `doc_repo` for mcp scope
- If no doc repo is in the list → auto-include the relevant doc repo based on the impl repos' scope group (a `core-sdk` repo implies `apcore/` as doc repo; a `mcp-bridge` repo implies `apcore-mcp/` as doc repo)
- All remaining repos become `impl_repos`

**Single repo name — smart expansion:**
```
/apcore-skills:sync apcore
```
A single repo name triggers **smart expansion** based on the repo's type:
- `protocol` repo (`apcore`) → expand to `apcore` + **all discovered `core-sdk` repos** (`apcore-{lang}`). Does NOT include `mcp-bridge` repos.
- `docs-site` repo (`apcore-mcp`) → expand to `apcore-mcp` + **all discovered `mcp-bridge` repos** (`apcore-mcp-{lang}`)
- `core-sdk` repo (`apcore-python`) → expand to this repo + its `doc_repo` (`apcore`). Only this single impl repo, not all core SDKs.
- `mcp-bridge` repo (`apcore-mcp-python`) → expand to this repo + its `doc_repo` (`apcore-mcp`). Only this single impl repo.
- `integration` repo → Phase A N/A, Phase B only on this repo
- `shared-lib` or `tooling` repo → Phase B only on this repo

Display: `"Scope: {repo-names} (from positional args)"`

**No positional repos:** Falls through to `--scope` or CWD-based default (see Step 1.1).

## Documentation and Implementation Repo Mapping

Each `--scope` group has one **documentation repo** (single source of truth) and one or more **implementation repos** (language-specific code):

| Scope | Documentation Repo | Contents | Implementation Repos |
|-------|-------------------|----------|---------------------|
| `core` | `apcore/` | PROTOCOL_SPEC.md, PRD, SRS, Tech Design, Test Plan, Feature Specs | `apcore-python/`, `apcore-typescript/`, ... |
| `mcp` | `apcore-mcp/` | PRD, SRS, Tech Design, Test Plan, Feature Specs | `apcore-mcp-python/`, `apcore-mcp-typescript/`, ... |

Implementation repos contain only code and a README. They do NOT contain PRD/SRS/Tech Design/Test Plan/Feature Specs — those live exclusively in the documentation repo.

## Context Management

**All per-repo operations use parallel sub-agents.** The main context ONLY handles:
1. Orchestration — determining scope, phase, and spawning sub-agents
2. Spec reference — reading the documentation repo (lightweight, structured docs)
3. Comparison logic — building and evaluating the checklist from structured summaries
4. Phase sequencing — Phase A must complete before Phase B begins
5. Reporting — formatting combined results

Phase A Step 2 spawns **one sub-agent per implementation repo, all simultaneously** for API extraction. Phase B Step 6 spawns **one sub-agent per documentation repo + one per implementation repo, all simultaneously** for documentation auditing. Fix steps spawn **one sub-agent per repo** for applying corrections.

## Workflow

```
Step 0 (ecosystem) → Step 1 (parse args) → PHASE A [Steps 2-5] → PHASE B [Steps 6-8] → Step 9 (combined report) → [Step 10 (fix)]
```

---

## Detailed Steps

### Step 0: Ecosystem Discovery

@../shared/ecosystem.md

Filter repos based on `--scope` and `--lang` flags. Identify documentation repos and implementation repos per scope group.

---

### Step 1: Parse Arguments and Determine Scope

Parse `$ARGUMENTS` for all flags and positional repo names. Determine:
- Active phases (a, b, or both)
- Scope groups and language filter
- Fix mode
- Target repos (from positional args, `--scope`, or CWD)

**Resolution priority:** Positional repo args > `--scope` flag > CWD-based default.

#### 1.0 Positional Repo Arguments

**If positional repo names are provided** (comma-separated, non-flag tokens in `$ARGUMENTS`):

1. Split by comma to get the repo name list
2. Validate each name against `repos[]` from ecosystem discovery. If a name is not found, report error: `"Repo '{name}' not found in ecosystem. Available: {repo names}"`
3. Apply the expansion rules from **Positional Repo Arguments** section above:
   - **Multiple repos** → use exactly as provided, auto-include doc repos if missing
   - **Single repo** → apply smart expansion based on repo type
4. Skip `--scope` and CWD-based default logic entirely
5. Display: `"Scope: {repo-names} (from positional args). {N} doc repos, {N} impl repos."`

#### 1.1 CWD-based Default Scope

**Only applies when NO positional repos are provided.**

**If `--scope` is NOT specified:**
1. Detect the current working directory's repo name (basename of CWD, e.g., `apcore-python`)
2. Look up this repo in the discovered ecosystem:
   - If it's a `core-sdk` repo → set scope to `core`, filter `impl_repos` to **only this repo**
   - If it's a `mcp-bridge` repo → set scope to `mcp`, filter `impl_repos` to **only this repo**
   - If it's the `protocol` repo (`apcore/`) → set scope to `core`, include **all** core impl repos (user is editing the spec, so check all implementations against it)
   - If it's a `docs-site` repo (`apcore-mcp/`) → set scope to `mcp`, include **all** mcp impl repos
   - If it's an `integration` repo → Phase A is N/A (integrations don't have a protocol spec to compare against), run Phase B only on this repo
   - If it's a `shared-lib` or `tooling` repo → run Phase B only on this repo (no spec to compare against)
   - If CWD is not inside any discovered repo → use `AskUserQuestion` to ask: "CWD is not an apcore repo. Which repo do you want to sync?" with options from `repos[]` names + "All repos (full ecosystem scan)"
3. Display: "Scope: {repo-name} (from CWD). Use --scope all for full ecosystem scan."

**If `--scope` IS specified:** use the explicit scope as before.

#### 1.2 Resolve Repos

For each scope group, resolve:
- `doc_repo` — the documentation repo path (e.g., `apcore/` for core, `apcore-mcp/` for mcp)
- `impl_repos[]` — the implementation repo paths (may be a single repo if CWD-scoped)

**Single-SDK handling:** If a scope group contains fewer than 2 implementation repos:
- Skip cross-implementation comparison for that group
- Display: "Only 1 {scope} implementation found ({repo-name}). Cross-language comparison requires at least 2 implementations."
- Still run spec compliance check (Phase A) and documentation consistency check (Phase B) as single-repo validation

Display:
```
Sync scope: {scope} {("(from CWD)" if defaulted)}
Languages: {lang1}, {lang2}, ...
Doc repos: {doc_repo1}, {doc_repo2}
Impl repos: {impl_repo1}, {impl_repo2}, ...
Phases: {A only | B only | A then B}
Mode: {report only | auto-fix}
```

---

## PHASE A: Spec ↔ Implementation Consistency

Verify that the documentation repo's feature specs and protocol spec match what each language implementation actually exports. Build an explicit checklist, compare every item.

### Step 2: Extract Public APIs (Parallel Sub-agents — One per Implementation Repo)

Spawn one `Task(subagent_type="general-purpose")` **per implementation repo, all simultaneously in a single round of parallel Task calls**. Each sub-agent extracts the public API from one repo independently. Do NOT process repos sequentially.

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

### Step 3: Load Documentation Repo Reference

For each documentation repo in scope, read the authoritative specs:

**For `apcore/` (core scope):**
1. Read `{doc_repo_path}/PROTOCOL_SPEC.md` — extract the API contract sections
2. Scan `{doc_repo_path}/docs/features/*.md` — extract per-feature API definitions (classes, functions, parameters, return types)
3. If `{doc_repo_path}/docs/spec/type-mapping.md` exists — load cross-language type mappings

**For `apcore-mcp/` (mcp scope):**
1. Scan `{doc_repo_path}/docs/features/*.md` — extract per-feature API definitions
2. If a protocol or spec file exists — extract the API contract

Store as `spec_api[scope]` — the canonical API that all implementations in this scope must match.

---

### Step 4: Checklist Comparison (The Core of Phase A)

@../shared/api-extraction.md

Build an explicit per-symbol checklist and evaluate every single item. No shortcuts.

#### 4.1 Build the Master Checklist

From `spec_api` and all `api_summaries`, construct a union of all symbols. Apply canonical name normalization for matching, **differentiated by symbol kind**:

**Classes / Types / Enums / Interfaces** → normalize to `PascalCase`:
- Python, TypeScript, Go, Rust, Java, C#, Kotlin, Swift, PHP: `PascalCase` (pass through)

**Functions / Methods / Variables / Constants** → normalize to `snake_case`:
- Python: `snake_case` (pass through)
- TypeScript: `camelCase` → `snake_case`
- Go: `PascalCase` → `snake_case` (exported functions)
- Rust: `snake_case` (pass through)
- Java: `camelCase` → `snake_case`
- C#: `PascalCase` → `snake_case`
- Kotlin: `camelCase` → `snake_case`
- Swift: `camelCase` → `snake_case`
- PHP: `camelCase` → `snake_case`

For each symbol, create a checklist row covering every checkable property.

#### 4.2 Checklist Evaluation Rules

**For each CLASS:**

```
┌────────────────────────┬──────────┬──────────┬──────────┬──────────┐
│ Check Item             │ Spec     │ Python   │ TypeScript│ Status   │
├────────────────────────┼──────────┼──────────┼──────────┼──────────┤
│ Registry               │          │          │          │          │
│  ├─ class exists       │ ✓        │ ✓        │ ✓        │ PASS     │
│  ├─ constructor params │          │          │          │          │
│  │  ├─ config: Config  │ required │ required │ required │ PASS     │
│  │  └─ discoverers     │ optional │ optional │ MISSING  │ FAIL     │
│  ├─ method: register   │          │          │          │          │
│  │  ├─ exists          │ ✓        │ ✓        │ ✓        │ PASS     │
│  │  ├─ name convention │ register │ register │ register │ PASS     │
│  │  ├─ params          │ (module) │ (module) │ (module) │ PASS     │
│  │  ├─ return type     │ None     │ None     │ void     │ PASS     │
│  │  └─ async           │ no       │ no       │ no       │ PASS     │
│  ├─ method: get_module │          │          │          │          │
│  │  ├─ exists          │ ✓        │ ✓        │ ✓        │ PASS     │
│  │  ├─ name convention │ get_mod  │ get_mod  │ getMod   │ PASS     │
│  │  ├─ params          │ (id)     │ (id)     │ (id)     │ PASS     │
│  │  └─ return type     │ Module?  │ Module?  │ Module?  │ PASS     │
│  ├─ method: scan_dir   │          │          │          │          │
│  │  ├─ exists          │ ✓        │ ✓        │ ✗        │ FAIL     │
│  │  ...                │          │          │          │          │
└────────────────────────┴──────────┴──────────┴──────────┴──────────┘
```

Checklist items per CLASS:
1. Class exists — present in spec? present in each implementation?
2. Constructor params — for each param: name convention ✓? type matches ✓? required/optional ✓? default value ✓?
3. Methods — for each method:
   a. Method exists in each implementation?
   b. Name follows language convention for the canonical name?
   c. Each parameter: name ✓, type ✓, required/optional ✓, default ✓
   d. Return type matches (using type mapping table)?
   e. Async flag matches?

**For each FUNCTION:**
1. Function exists — present in spec? present in each implementation?
2. Name follows language convention?
3. Each parameter: name ✓, type ✓, required/optional ✓, default ✓
4. Return type matches?
5. Async flag matches?

**For each ENUM:**
1. Enum exists in each implementation?
2. Each member: name matches ✓? value matches ✓?

**For each TYPE/INTERFACE:**
1. Type exists in each implementation?
2. Each field: name matches ✓? type matches ✓? required/optional ✓?

**For each ERROR CLASS:**
1. Error class exists in each implementation?
2. Error code value matches?
3. Parent class matches?

**For each CONSTANT:**
1. Constant exists in each implementation?
2. Type matches ✓? Value matches ✓?

#### 4.3 Protocol Compliance Check

For each implementation repo, compare against the spec API:
1. **Missing from spec** — implementation has symbols not defined in spec (language-specific additions)
2. **Missing from implementation** — spec defines symbols not in implementation
3. **Divergence** — implementation doesn't match spec definition

#### 4.4 Store Phase A Results

Store the full evaluated checklist as `phase_a_results`:
- `verified_api` — the spec-defined API surface with per-symbol verification status from implementations. Definition: the union of all symbols from the spec, annotated with which implementations have them and whether they match. For PASS symbols, the spec definition is confirmed correct. For FAIL symbols, the spec definition is still authoritative (implementations are wrong).
- `checklist` — every item with its PASS/FAIL/WARN status
- `findings` — structured list of all failures with severity

This `verified_api` becomes the input truth for Phase B. When injecting into Phase B sub-agent prompts, format as:
```
VERIFIED API ({repo-name}):
CLASSES:
- {ClassName}: constructor({params}), methods: {method1}({params}) -> {ret}, ...
FUNCTIONS:
- {func_name}({params}) -> {ret}
TYPES:
- {TypeName}: {field1}: {type1}, {field2}: {type2}, ...
ENUMS:
- {EnumName}: {MEMBERS}
CONSTANTS:
- {NAME}: {type} = {value}
ERRORS:
- {ErrorName}(code={CODE})
```

---

### Step 5: Phase A Report

```
═══ PHASE A: Spec ↔ Implementation Consistency ═══

Scope: {scope}
Doc repo: {doc_repo} → Impl repos: {impl1}, {impl2}, ...

Checklist: {total_items} items checked
  PASS: {n}
  FAIL: {n}
  WARN: {n}

Spec compliance:
  {impl-repo-1}:  {N}/{total} symbols ({pct}%) ✓
  {impl-repo-2}:  {N}/{total} symbols ({pct}%) ⚠ {missing} missing

Cross-implementation:
  Total symbols: {N}
  Matching: {N}
  Missing: {N}
  Signature mismatch: {N}
  Naming inconsistency: {N}
  Type mismatch: {N}

FAIL items (expanded):
  ❌ Registry.scan_directory()
     Present in: spec, apcore-python
     Missing in: apcore-typescript
     Spec: defined in docs/features/registry.md

  ❌ Executor.execute() — param mismatch
     Spec:       (module_id: str, input: dict, context: Context | None = None) -> ExecutionResult
     Python:     (module_id: str, input: dict, context: Context | None = None) -> ExecutionResult  ✓
     TypeScript: (moduleId: string, input: Record<string, unknown>) -> ExecutionResult  ✗ missing context param
```

If `--save` flag: write report to `{ecosystem_root}/sync-report-phase-a-{date}.md`.

If `--phase a` only: display this report and stop. Otherwise continue to Phase B.

---

## PHASE B: Documentation Internal Consistency

Phase B runs ONLY after Phase A completes. It verifies two things:
1. The documentation repo's internal documents are consistent with each other (no contradictions)
2. Implementation repos' README and examples are consistent with `verified_api` from Phase A

### Step 6: Audit Documentation (Parallel Sub-agents)

Spawn sub-agents in parallel: **one per documentation repo** + **one per implementation repo**, all simultaneously.

#### Sub-agent for Documentation Repo (apcore/ or apcore-mcp/)

**Sub-agent prompt:**

```
Audit internal documentation consistency in {doc_repo_path}.

This is a DOCUMENTATION REPO containing specs and feature definitions. Check that
all documents are internally consistent — no contradictions between layers.

=== SCOPE 1: Spec Chain Consistency ===

Read all available documents from the spec chain:
- PRD (if exists): docs/prd.md or similar
- SRS (if exists): docs/srs.md or similar
- Tech Design (if exists): docs/tech-design.md or similar
- Test Plan (if exists): docs/test-plan.md or similar
- Feature Specs: docs/features/*.md
- Protocol Spec (if exists): PROTOCOL_SPEC.md

For each API symbol (class, function, parameter, return type) mentioned across multiple documents:
1. Collect ALL references: which document, what section, what it says
2. Compare: do all documents agree on the symbol's name, parameters, behavior, and types?
3. Flag contradictions:
   - PRD says feature X has capability A, but feature spec says no such capability
   - SRS requirement REQ-001 references function foo(), but tech design calls it bar()
   - Test plan tests for param "timeout" but feature spec defines it as "max_wait"
   - Feature spec A says Registry has method scan(), feature spec B says it's discover()

=== SCOPE 2: Feature Spec Completeness ===

For each feature spec in docs/features/:
1. Does it define clear API symbols (classes, functions, params, return types)?
2. Are there features mentioned in PRD/SRS that have NO corresponding feature spec?
3. Are there feature specs that are NOT referenced by any higher-level document?

=== SCOPE 3: Cross-Document Reference Integrity ===

Check all internal cross-references:
1. Do documents reference sections/features that actually exist?
2. Are version numbers consistent across documents?
3. Are terminology and naming consistent (same concept uses same name everywhere)?

Return findings in this exact format:
DOC_REPO: {repo-name}
DOCUMENTS_FOUND: {list of documents checked with paths}

SPEC_CHAIN:
  LAYERS_CHECKED: {list: prd, srs, tech-design, test-plan, feature-specs, protocol-spec}
  CONTRADICTIONS: {N}
  GAPS: {N}

FINDING_COUNT: {N}
FINDINGS:
- severity: {critical|warning|info}
  scope: {spec-chain|completeness|cross-ref}
  detail: {description}
  locations:
    - {file1:section} says: "{quote1}"
    - {file2:section} says: "{quote2}"
  contradiction: {what disagrees}
  fix: {which document should be authoritative and what to change}

Error handling:
- If the documentation repo path does not exist, return: DOC_REPO: {repo-name}, STATUS: NOT_FOUND
- If no spec chain documents are found (no PRD, SRS, tech design, feature specs), return: DOC_REPO: {repo-name}, STATUS: NO_DOCS, DOCUMENTS_FOUND: []
- If individual files cannot be read, skip them and list in DOCUMENTS_FOUND as "{path} (unreadable)"
```

#### Sub-agent for Implementation Repo (apcore-python/, apcore-typescript/, etc.)

**Sub-agent prompt:**

```
Audit documentation in {impl_repo_path} for consistency with the verified API surface.

This is an IMPLEMENTATION REPO. It should contain only code and a README (plus optional examples).
It does NOT contain PRD/SRS/Tech Design/Test Plan/Feature Specs.

VERIFIED API (ground truth from Phase A):
{verified_api for this repo — the confirmed-correct API symbols, signatures, types}

=== SCOPE 1: README ===

1. Read README.md
2. Check required sections: Title/badges, Description, Installation, Quick Start, Features, API Overview, Docs link, License
3. For Installation: verify package name matches build config (pyproject.toml/package.json)
4. For Quick Start code examples: extract all API references, verify they match verified API
   - Import names correct?
   - Class names correct?
   - Method names correct?
   - Parameter names and order correct?
5. For API Overview: verify listed classes/functions exist in verified API with correct descriptions
6. For version references: verify they match current version in build config

=== SCOPE 2: API References in Markdown ===

Search ALL markdown files in the repo (README.md, docs/**/*.md) for API symbol references:
1. For EACH symbol reference found:
   a. Does the symbol exist in the verified API?
   b. Do parameter names/order match the verified signature?
   c. Are import paths correct?
   d. Are return types correctly described?
2. Cross-check: do different markdown files contradict each other?
   - If README says `get_module(id)` but docs/usage.md says `get_module(module_id)` → CONTRADICTION

=== SCOPE 3: Example Code ===

1. Scan examples/, demo/, example/ directories
2. For each example source file (*.py, *.ts, *.js):
   a. Extract import statements and API usage
   b. Cross-reference against verified API — correct class names, method names, params?
   c. Check dependency versions reference correct SDK version
3. Check example README exists with setup instructions

=== SCOPE 4: Cross-Document Contradiction Detection ===

For every API symbol mentioned in more than one place within this repo:
1. Collect all references (file, line, what it says)
2. Compare: do all references agree on name, params, behavior?
3. Flag any contradictions between documents

Return findings in this exact format:
REPO: {repo-name}

README:
  SECTIONS_PRESENT: {list}
  SECTIONS_MISSING: {list}
  API_MISMATCHES: {list of references that don't match verified API}
  VERSION_MISMATCHES: {list}
  INSTALL_CORRECT: true|false

API_REFS:
  REFERENCES_CHECKED: {N}
  MISMATCHES: {N}

EXAMPLES:
  EXAMPLE_DIRS: {list or "none"}
  MISMATCHES: {N}

CONTRADICTIONS: {N}
  {list of cases where different docs within this repo say different things}

FINDING_COUNT: {N}
FINDINGS:
- severity: {critical|warning|info}
  scope: {readme|api-refs|examples|contradiction}
  detail: {description}
  location: {file:section or file:line}
  verified_api_says: {correct value from Phase A}
  doc_says: {what the doc currently says}
  fix: {suggested fix}

Error handling:
- If the repo path does not exist, return: REPO: {repo-name}, STATUS: NOT_FOUND
- If README.md is missing, report SECTIONS_PRESENT: [], SECTIONS_MISSING: ["all"], and continue checking other scopes
- If no markdown files are found, skip API_REFS scope and report REFERENCES_CHECKED: 0
- If no example directories exist, report EXAMPLE_DIRS: "none", MISMATCHES: 0
```

**Main context retains:** Structured findings per repo.

---

### Step 7: Cross-Repo Documentation Consistency

After collecting all per-repo findings, the main context performs cross-repo checks:

1. **Cross-repo API description consistency** — if apcore-python's README describes `Registry.get_module()` with certain behavior, and apcore-typescript's README describes `Registry.getModule()` differently, flag it (semantic description should match even if name differs by convention)
2. **Shared documentation links** — do all implementation repos link to the same docs site version?
3. **Doc repo vs implementation README alignment** — do implementation READMEs accurately reflect what the documentation repo's feature specs define?

---

### Step 8: Phase B Report

```
═══ PHASE B: Documentation Internal Consistency ═══

--- Documentation Repos ---

{doc_repo_1} ({scope}):
  Spec chain layers: {list}
  Contradictions: {N}
  Completeness gaps: {N}
  Cross-ref issues: {N}

  CONTRADICTIONS:
    ⚠ PRD §3.2 says "Registry supports glob patterns"
      but feature spec registry.md defines no glob parameter
    ⚠ SRS REQ-012 references "Executor.run()"
      but tech design §4.1 calls it "Executor.execute()"

--- Implementation Repos ---

  Repo                    | README | API Refs | Examples | Cross-Doc
  apcore-python           |  PASS  |   PASS   |    —     |   PASS
  apcore-typescript       |  WARN  |   FAIL   |    —     |   FAIL
  apcore-mcp-python       |  PASS  |   PASS   |    —     |   PASS
  apcore-mcp-typescript   |  WARN  |   PASS   |    —     |   PASS

  MISMATCHES:
    ❌ apcore-typescript README Quick Start uses `findModule()`
       but verified API says `getModule()`
    ❌ apcore-typescript docs/usage.md says `execute(moduleId, input)`
       but verified API says `execute(moduleId, input, context?)`

--- Cross-Repo ---

  Cross-repo contradictions: {N}
  Link consistency: {PASS|FAIL}
```

If `--save` flag: write report to `{ecosystem_root}/sync-report-phase-b-{date}.md`.

---

### Step 9: Combined Report

```
apcore-skills sync — Unified Consistency Report

Scope: {scope} | Languages: {langs} | Date: {date}
Phases: A (spec ↔ code) + B (documentation)

═══ PHASE A: Spec ↔ Implementation ═══

Checklist: {N} items | PASS: {n} | FAIL: {n} | WARN: {n}

{checklist table — only FAIL/WARN items expanded}

Spec compliance:
  {impl-repo-1}: {N}/{total} ({pct}%)
  {impl-repo-2}: {N}/{total} ({pct}%)

Cross-implementation:
  Total: {N} | Match: {N} | Missing: {N} | Mismatch: {N} | Naming: {N} | Type: {N}

═══ PHASE B: Documentation Consistency ═══

Doc repo internal:
  {doc-repo}: {N} contradictions, {N} gaps

Implementation repo docs:
  Repo                  | README | API Refs | Examples | Cross-Doc
  (matrix)

Cross-repo: {N} contradictions

═══ COMBINED FINDINGS (sorted by severity) ═══

CRITICAL:
  [A-001] Missing API: Registry.scan_directory()
    Repo: apcore-typescript
    Spec: defined in apcore/docs/features/registry.md
    Phase A — present in spec + Python, missing in TypeScript

  [B-001] Spec chain contradiction
    Doc repo: apcore
    PRD says "glob patterns" but feature spec has no glob param
    Phase B — internal documentation inconsistency

  [B-002] API reference mismatch
    Repo: apcore-typescript
    README uses findModule(), verified API says getModule()
    Phase B — implementation doc does not match verified code

WARNING:
  [A-002] ...
  [B-003] ...

INFO:
  ...

═══ SUMMARY ═══
  Phase A: {N} findings (critical: {n}, warning: {n}, info: {n})
  Phase B: {N} findings (critical: {n}, warning: {n}, info: {n})
  Total: {N} findings
  Contradictions (doc internal): {N}
  Contradictions (cross-repo): {N}
```

If `--save` flag: write report to `{ecosystem_root}/sync-report-{date}.md`.

---

### Step 10: Auto-Fix (only with --fix flag)

Group all findings from both phases by repo. Spawn one `Task(subagent_type="general-purpose")` **per repo that has fixable findings, all in parallel**.

**Sub-agent prompt for implementation repos:**

```
Apply sync fixes for {repo_path} ({language}).

Phase A findings to fix:
{naming, missing, type issues from Phase A}

Phase B findings to fix:
{readme, api-ref, examples issues from Phase B}

Fix rules (apply in order):

PHASE A FIXES (code):
1. NAMING FIXES — For each naming inconsistency:
   - Canonical name: {canonical} → language convention: {expected_name}
   - Rename the function/method/class in its source file using Edit
   - Update the export in __init__.py / index.ts
   - Update any internal references within the same repo

2. MISSING API STUBS — For each missing symbol:
   - Generate a stub implementation in {language} with TODO markers
   - Match the signature from the spec (canonical form)
   - Add the export to the main module file
   - Create a corresponding test stub in tests/

3. VERIFY — After all Phase A fixes:
   - Run the full test suite: {pytest --tb=short -q | npx vitest run}
   - If any test fails due to a fix: revert ONLY that specific fix and note it

PHASE B FIXES (docs):
4. README FIXES — Add missing sections, update API names to match verified API, update version references
5. API REFERENCE FIXES — Update symbol names, param names, import paths in all markdown files
6. EXAMPLE FIXES — Update API usage and dependency versions in example code
7. CONTRADICTION FIXES — Resolve contradictions by aligning all docs to verified API

After all fixes:
1. List all files modified with a summary of changes
2. Do NOT commit — leave changes for user review

Error handling: If test runner is not available, skip verification and note it.

Return:
REPO: {repo-name}
PHASE_A_FIXES: {count} (naming: {n}, stubs: {n})
PHASE_B_FIXES: {count} (readme: {n}, api-refs: {n}, examples: {n}, contradictions: {n})
TEST_RESULT: {pass|fail|skipped}
TEST_COUNTS: {passed}/{total}
REVERTED_FIXES: {list or "none"}
FILES_MODIFIED: {list}
```

**Sub-agent prompt for documentation repos:**

```
Apply documentation consistency fixes for {doc_repo_path}.

Phase B findings to fix:
{spec chain contradictions, completeness gaps, cross-ref issues from Phase B}

Fix rules:

1. SPEC CHAIN CONTRADICTIONS — For each contradiction between documents:
   - Identify which document is the higher-authority source:
     Authority order: Feature Specs > Tech Design > SRS > PRD
     (Feature specs are closest to implementation, PRD is most abstract)
   - Update the lower-authority document to match the higher-authority one
   - If the contradiction is between documents at the same level: flag for manual review, do NOT auto-fix

2. COMPLETENESS GAPS — For features mentioned in PRD/SRS but missing feature specs:
   - Do NOT generate feature specs automatically (too complex for auto-fix)
   - Add a TODO note in the appropriate location

3. CROSS-REFERENCE FIXES — Fix broken internal references:
   - Update section references to point to correct locations
   - Fix terminology inconsistencies to use the canonical name

After all fixes:
1. List all files modified
2. Do NOT commit

Error handling:
- If the doc repo path does not exist, return: DOC_REPO: {repo-name}, STATUS: NOT_FOUND
- If a file is unwritable, skip it and list in MANUAL_REVIEW_ITEMS
- If same-level contradiction (ambiguous authority): flag for manual review, do NOT auto-fix

Return:
DOC_REPO: {repo-name}
FIXES_APPLIED: {count}
FLAGGED_FOR_MANUAL_REVIEW: {count}
FILES_MODIFIED: {list}
MANUAL_REVIEW_ITEMS:
- {description of what needs human decision}
```

Wait for all sub-agents to complete. Display consolidated results:

```
Auto-fix results:

Implementation repos:
  apcore-typescript: Phase A: 3 naming fixes, 1 stub | Phase B: 2 readme fixes
    Tests: 287/287 ✓
    Files: 5 changed
  apcore-mcp-typescript: Phase A: 1 naming fix | Phase B: 0
    Tests: 112/112 ✓
    Files: 1 changed

Documentation repos:
  apcore: 2 contradiction fixes, 1 flagged for manual review
    Files: 2 changed
    Manual review: PRD §3.2 vs feature spec — need human decision on glob pattern scope

Uncommitted changes — review with:
  cd {repo} && git diff
```
