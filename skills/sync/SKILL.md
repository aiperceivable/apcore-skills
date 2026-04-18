---
name: sync
description: >
  Unified cross-language consistency verification and documentation alignment.
  Phase A: verifies feature specs and protocol spec match all language implementations
  (classes, functions, parameters, return types, trait/interface satisfaction,
  multi-constructor patterns, and optional algorithm-skeleton checkpoints) via
  itemized checklist comparison.
  Phase B: verifies all documentation (PRD, SRS, Tech Design, Test Plan, Feature Specs,
  PROTOCOL_SPEC, README, examples, tests) is internally consistent and free of contradictions.
  Includes cross-language example scenario coverage and test scenario coverage comparison.
  Optionally hands off behavioral equivalence to the `tester` skill.
  Covers both apcore core SDKs and apcore-mcp bridges.
instructions: >
  The documentation repos (apcore/, apcore-mcp/) are the single source of truth.
  Phase A MUST complete before Phase B begins — Phase B uses Phase A's verified
  API surface as its reference. Never skip a phase. Never skip a checklist item.
  Internal consistency is checked at the SKELETON level (algorithm checkpoint
  sequence) and the BEHAVIOR level (delegated to tester). Function-level identity
  is explicitly NOT a goal — it conflicts with each language's design philosophy.
  CHANGELOG is a release artifact, NOT a documentation consistency concern.
---

# Apcore Skills — Sync

## ⚡ Execution Entry Point (READ THIS FIRST)

**When this skill is loaded, you MUST immediately begin executing the Workflow below — do not wait, do not summarize, do not ask "what should I do now". Skills are operational manuals, not reference documents.** Read the first executable step (argument parsing / ecosystem discovery), then continue through Phase A and Phase B in order, until the workflow completes or you reach an `AskUserQuestion` checkpoint. Phase A MUST complete before Phase B begins.

If the harness shows you `Successfully loaded skill · N tools allowed`, that message means **the SKILL.md content was injected into your context** — it does NOT mean the skill has run. Skills do not "run" autonomously; you run them by executing the Detailed Steps below.

If you find yourself about to say "the skill didn't produce output", "skill 仍未输出", "falling back to manual sync", "回退到手动 sync", or anything similar, **STOP**. You have misunderstood how skills work. Go directly to the first executable step and start.

The first user-visible action of this skill should be either (a) the output of the first step / Phase A startup, or (b) an `AskUserQuestion` if scope detection needs disambiguation. Never an apology, never a fallback, never silence.

---

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
| "Doc examples are just illustrative" | If a code example calls a non-existent method or passes the wrong number of args, a user copying it will get a compile/runtime error. Doc examples ARE the onboarding API — treat them as code. |
| "Deprecated APIs in docs are just stale" | If CHANGELOG says an API was removed in v0.18.0 but docs still reference it, users following the docs will hit errors on the current version. Cross-check CHANGELOG Removed sections against doc examples. |
| "PRD is product-level, no need to check against code" | If the PRD says a feature exists but no implementation matches, that is a gap. Every layer must agree. |
| "Internal helpers should also be 1-to-1 across languages" | NO. Function-level identity (helper names, decomposition, line count) conflicts with each language's design (Rust ownership splits, Go's no-default-args, Python list comprehensions). **BUT** intent / logic / purpose MUST be identical across languages — that is enforced by the CONTRACT tier (default ON, Step 4B), the SKELETON tier (opt-in, Step 4A — algorithm checkpoint sequence), and the BEHAVIOR tier (opt-in, Step 7.5 — runtime equivalence via `tester`). Helper-name parity is never enforced at any tier. |
| "Same public signature means same intent" | NO. Two `register(id, module)` methods can share the same signature yet diverge in logic — one validates before mutating, another writes first and rolls back on error; one raises on duplicate, another silently overwrites; one is thread-safe, another races. These are intent-level bugs. The CONTRACT tier compares inputs validation rules, errors raised, side-effect order, return shape, and behavioral properties (async/thread-safe/pure/idempotent/reentrant) against the spec's `## Contract:` block — or cross-repo when spec is silent. |
| "Trait satisfaction is a Rust thing, skip it for other languages" | Every language has an equivalent: Python `__str__` / TS `toString()` / Go `String()` / Rust `impl Display`. The protocol spec defines required interface contracts; each language must satisfy them with its idiomatic mechanism. Build a dedicated checklist row. |
| "Multiple constructors are language-specific sugar" | Rust's `Self::new()` / `Self::with_config()` / `Self::from_env()` corresponds to Python `classmethod` factories, TS static factories, Go `NewX` / `NewXFromY`. If the spec defines multiple construction paths, every language must expose all of them. Treat constructors as a list, not a single entry. |
| "Contract extraction (4B) already catches intent divergence, deep-chain is redundant" | NO. 4B's sub-agent is **one-per-repo doing shape extraction** — it lists `inputs/errors/side_effects` as declared fields. It cannot see bugs that only appear when you read the code: bare dict subscripts that throw `KeyError` on malformed input, internal methods that silently skip validation, functions that fail to update a map the peer language updates. These are visible in the AST, not in the contract shape. Step 4C reads all N languages' source for one module **side-by-side** and diffs the call graphs — that is how the `_discover_custom` / `discover_internal` / `for...of null` class of bugs get caught. |
| "A sub-agent that reports 'no issues' means the module is fine" | NO. A polished 'all clear' report is the most dangerous output — it manufactures false confidence. Sub-agents MUST default to `inconclusive` when evidence is ambiguous and MUST cite `file:line:snippet` for every finding, including "no issue" claims. The orchestrator rejects any module report without per-symbol evidence citations and re-runs the sub-agent. |

## When to Use

- After adding features to one SDK — verify all SDKs and their docs match
- Periodic consistency check across all language implementations
- Before a release to ensure all SDKs expose the same API surface and docs are accurate
- After API changes to sync usage examples and documentation across repos
- When a new SDK is nearing feature parity with existing ones
- After updating PRD/SRS/Tech Design — verify downstream docs and code still match

## Command Format

```
/apcore-skills:sync [repo1,repo2,...] [--phase a|b|all] [--fix] [--scope core|mcp|all] [--lang python,typescript,...] [--internal-check none|contract|skeleton|behavior] [--deep-chain on|off] [--save]
```

| Argument / Flag | Default | Description |
|------|---------|-------------|
| positional repos | — | Comma-separated repo names to sync. See **Positional Repo Arguments** below. |
| `--phase` | `all` | Which phase to run: `a` (spec vs implementation), `b` (documentation internal consistency), `all` (A then B) |
| `--fix` | off | Auto-fix issues (naming, stubs, doc references) |
| `--scope` | **cwd** | Which group: `core`, `mcp`, `all`. **If omitted and no positional repos, defaults to the current working directory's repo only.** Use `--scope all` to scan all repos. |
| `--lang` | all discovered | Comma-separated list of languages to compare |
| `--internal-check` | `contract` | Internal consistency tier. `none` = public API only. `contract` = **DEFAULT** — also compare behavioral contracts (inputs validation, errors raised, side-effect order, return shape, properties) via Step 4B, static. `skeleton` = contract + algorithm checkpoint sequences (Step 4A, static, requires source instrumentation). `behavior` = all static tiers + hand off to `tester` skill for runtime behavioral equivalence (Step 7.5, dynamic). Higher tiers include lower tiers. Function-level (helper) identity is intentionally NOT supported — see Anti-Rationalization Table. |
| `--deep-chain` | `on` | Cross-language deep-chain analysis (Step 4C). When on, the orchestrator spawns one sub-agent **per logical module** and feeds it all N languages' source side-by-side. The sub-agent diffs call graphs, finds missing-validation / missing-registration / defensive-gap divergences that shape-level extraction (4B) cannot see. Forced off when `--internal-check=none`. Set `--deep-chain off` for fast sync (reduces sub-agent count, loses intent-level chain coverage). |
| `--save` | off | Save report to file |

### Internal Consistency Tiers

Each tier is **cumulative** — higher tiers include all lower tiers.

| Tier | What is checked | How | Cost |
|------|----------------|-----|------|
| `none` | Public API surface only (Step 4) | Static signature comparison | Low |
| `contract` (**default**) | Public API + **behavioral contract** per method: inputs validation, errors raised, side-effect order, return shape, properties (async, thread_safe, pure, idempotent, reentrant) | Static — sub-agents extract contract per `shared/api-extraction.md` E.4b; main context compares each row against spec `## Contract:` block (if present) and cross-repo (always) | Low — no new runtime cost |
| `skeleton` | Contract tier + algorithm checkpoint sequence inside each public method | Static — grep `checkpoint:NAME` literal strings in source, compare ordered set against spec's `## Algorithm` section | Low — requires source instrumentation |
| `behavior` | All static tiers + runtime behavioral equivalence — same input → same observable output across all SDKs | Dynamic — invokes `/apcore-skills:tester --mode run --category protocol` (Step 7.5) and merges results | High — runs tests |

**Contract tier is the default** because it answers the question "do all SDKs agree on what the method DOES?" without requiring any source instrumentation or test execution. It captures intent (logic/purpose) divergence that pure signature comparison misses. See `shared/contract-spec.md` for the `## Contract:` block format.

**Deep-chain analysis (Step 4C, `--deep-chain on` by default) runs alongside every non-`none` tier.** It is **not** a `--internal-check` tier because it operates on a different axis: instead of comparing extracted **shape** (as contract/skeleton/behavior do), it compares actual **call graphs across languages**. A sub-agent reads all N languages' source for one module side-by-side and diffs the code directly. This catches bugs that shape extraction is structurally blind to (e.g., `for (const entry of customModules)` crashing on `null` when peer languages don't; internal methods skipping validation; maps missing an insert). See Step 4C.

**Function-level identity (helper names / count / decomposition) is explicitly NOT a tier.** It conflicts with each language's design philosophy (Rust ownership splits, Go's no-default-args, Python list comprehensions) and produces noise rather than signal.

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

**All per-repo AND per-module operations use parallel sub-agents.** The main context ONLY handles:
1. Orchestration — determining scope, phase, enumerating modules, tracking per-module progress, spawning sub-agents
2. Spec reference — reading the documentation repo (lightweight, structured docs)
3. Comparison logic — building and evaluating the checklist from structured summaries
4. Phase sequencing — Phase A must complete before Phase B begins
5. Reporting — formatting combined results

Parallelism fan-out:
- **Step 2** — one sub-agent per implementation repo (per-repo, simultaneous) for public API extraction
- **Step 4C** — one sub-agent per **logical module** (cross-language — each sub-agent reads all N languages' source for its module), dispatched in batches by the orchestrator with bounded concurrency. Progress table is maintained in main context
- **Step 6** — one sub-agent per documentation repo + one per implementation repo (simultaneous) for documentation auditing
- **Step 10** — one sub-agent per repo with fixable findings (simultaneous)

**Orchestrator progress tracking (Step 4C).** The main context keeps a table `module_progress[module] = {status: pending|in_progress|complete|failed|inconclusive, findings_count, inconclusive_count, assigned_sub_agent_id}`. As each sub-agent returns, the orchestrator updates the row and prints one line: `[4C] {module}: {N} findings ({critical}/{warning}/{info}/{inconclusive})`. If any module comes back `failed` or entirely `inconclusive`, the orchestrator emits a visible warning — a module that cannot be analyzed is itself a risk indicator, not a quiet success.

## Workflow

```
Step 0 (ecosystem) → Step 1 (parse args) → PHASE A [Steps 2-5, including 4A/4B/4C] → PHASE B [Steps 6-8] → Step 9 (combined report + review-compatible output) → [Step 10 (fix)]
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

Spawn one `Agent(subagent_type="general-purpose")` **per implementation repo, all simultaneously in a single round of parallel Agent calls**. Each sub-agent extracts the public API from one repo independently. Do NOT process repos sequentially.

**Sub-agent prompt:** Use the template from `@references/extract-api-prompt.md`, filling in `{repo_path}` and `{package}` for each repo.

**Main context retains:** Each repo's structured API summary. Store as `api_summaries[repo_name]`.

---

### Step 3: Load Documentation Repo Reference

For each documentation repo in scope, read the authoritative specs:

**For `apcore/` (core scope):**
1. Read `{doc_repo_path}/PROTOCOL_SPEC.md` — extract the API contract sections
2. Scan `{doc_repo_path}/docs/features/*.md` — extract per-feature API definitions (classes, functions, parameters, return types, **trait/interface contracts**, **multi-constructor patterns**)
3. If `{doc_repo_path}/docs/tech-design.md` (or `docs/tech-design/*.md`) exists — extract any internal interface contracts marked as normative. Tag them with `internal_contract: true` so Step 4A knows they apply to internal symbols, not just public API.
4. From each feature spec, parse any `## Algorithm` section — extract the ordered checkpoint list for each public method. Store as `spec_skeletons[scope][symbol] = [checkpoint_1, checkpoint_2, ...]`. This is the input for Step 4A.
4b. **From each feature spec, parse any `## Contract:` section** — extract the behavioral contract per `shared/contract-spec.md`. For each spec Contract block, capture `{inputs[], preconditions[], side_effects[], postconditions[], errors[], returns, properties{}}`. Store as `spec_contracts[scope][symbol] = {...}`. This is the input for Step 4B.
5. If `{doc_repo_path}/docs/spec/type-mapping.md` exists — load cross-language type mappings

**For `apcore-mcp/` (mcp scope):**
1. Scan `{doc_repo_path}/docs/features/*.md` — extract per-feature API definitions, `## Algorithm` checkpoint sections, **and `## Contract:` behavioral contract sections**
2. If `{doc_repo_path}/docs/tech-design.md` exists — extract internal interface contracts
3. If a protocol or spec file exists — extract the API contract

Store as:
- `spec_api[scope]` — canonical API surface (signatures)
- `spec_skeletons[scope][symbol]` — algorithm checkpoint sequences
- `spec_contracts[scope][symbol]` — behavioral contracts (inputs validation, errors, side effects, properties)

All three must be matched by implementations. If a public method has no `## Contract:` block in any feature spec, Step 4B still runs — it compares across implementations (cross-repo mode) and emits a `warning` finding `"no spec Contract declared for {method} — compared across repos only"` pointing to the doc repo.

**For all documentation repos:**

6. Read `{doc_repo_path}/CHANGELOG.md` — extract all symbols listed under `### Removed` or `### Deprecated` sections, grouped by version. Store as `deprecated_api[scope]` = list of `{symbol, version, section}` entries. These are used in Phase B Step 6 to flag doc examples that reference removed/deprecated APIs.

   CHANGELOG is NOT checked for its own correctness (that remains a release artifact). It is used ONLY as a **signal source** to detect stale references in documentation examples.

**Algorithm section format (convention).** Feature specs SHOULD declare algorithm skeletons in this form so that Step 4A can parse them:

```markdown
## Algorithm: Registry.register

1. validate_id_format
2. check_duplicate
3. resolve_dependencies
4. acquire_write_lock
5. insert_into_index
6. emit_registered_event
7. release_write_lock
```

If a feature spec has no `## Algorithm` section for a given method, Step 4A skips skeleton checking for that method (with INFO finding "no spec skeleton declared").

---

### Step 4: Checklist Comparison (The Core of Phase A)

@../shared/api-extraction.md

Build an explicit per-symbol checklist and evaluate every single item. No shortcuts.

Step 4 has four substeps that run in order:
- **4.1–4.3** — signature / type / naming checklist (always runs)
- **4A** — skeleton checkpoint comparison (runs only when `--internal-check` is `skeleton` or `behavior`)
- **4B** — contract parity (runs by default — `--internal-check` is `contract`, `skeleton`, or `behavior`)
- **4C** — cross-language deep-chain analysis (runs when `--deep-chain=on` AND `--internal-check != none`; default is on)

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
2. **Constructors (list, not single entry)** — the spec may declare multiple construction paths (Rust `Self::new` / `Self::with_config` / `Self::from_env`; Python `classmethod` factories; Go `NewX` / `NewXFromY`; TS static factories). For each spec-declared constructor:
   a. Constructor exists in each implementation under the language-idiomatic mechanism?
   b. Each param: name convention ✓, type ✓, required/optional ✓, default value ✓ (use the default-value mapping table in api-extraction.md E.4)
3. Methods — for each method:
   a. Method exists in each implementation?
   b. Name follows language convention for the canonical name?
   c. Each parameter: name ✓, type ✓, required/optional ✓, default ✓
   d. Return type matches (using type mapping table)?
   e. Async flag matches?
4. **Trait / Interface satisfaction** — for each trait/interface contract the spec declares this class must satisfy (e.g., `Display`, `Serializable`, `Clone`, `Iterator`):
   a. Each implementation must expose the equivalent contract using the language's idiomatic mechanism. Equivalence table:
      | Spec contract | Python | TypeScript | Go | Rust | Java |
      |---|---|---|---|---|---|
      | `Display` (string repr) | `__str__` | `toString()` | `String() string` | `impl Display` | `toString()` |
      | `Debug` (debug repr) | `__repr__` | `[util.inspect.custom]` | `GoString() string` | `impl Debug` | `toString()` (debug variant) |
      | `Equality` | `__eq__` + `__hash__` | `equals()` + `hashCode()` (or value-equality lib) | `Equal(other) bool` | `impl PartialEq + Eq + Hash` | `equals()` + `hashCode()` |
      | `Clone` | `__copy__` / `copy.copy` | `clone()` method | explicit copy func | `impl Clone` | `clone()` (Cloneable) |
      | `Default construction` | classmethod `default()` | static `default()` | `NewX()` zero-value | `impl Default` | no-arg constructor |
      | `Serialize` | `to_dict` / pydantic | `toJSON` / class-transformer | `MarshalJSON` | `impl Serialize` | Jackson annotations |
      | `Iterator` | `__iter__` + `__next__` | `[Symbol.iterator]` | `Next() (T, bool)` channel | `impl Iterator` | `Iterator<T>` |
      | `Context manager` | `__enter__` + `__exit__` | `Symbol.dispose` / `using` | `defer` + Close() | `impl Drop` | try-with-resources (`AutoCloseable`) |
   b. If the spec contract has no row in this table, fall back to: "implementation exposes a method whose canonical-snake-case name matches the contract's spec name"
   c. Missing equivalent → FAIL with severity `critical`

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

#### 4A: Internal Skeleton Consistency (when --internal-check >= skeleton)

**Purpose:** verify that each public method's *internal algorithm* follows the same checkpoint sequence across languages, without requiring helper-function identity. This is the only static check sync performs on internal implementation.

**Skip conditions:**
- `--internal-check=none` → skip this entire substep
- `spec_skeletons[scope]` is empty (no feature spec in this scope declares any `## Algorithm` section) → skip the entire substep with a single INFO finding `"no spec skeletons defined for scope {scope} — skeleton tier is a no-op until feature specs add ## Algorithm sections"`. Do NOT emit per-method findings in this case.
- A given method has no `## Algorithm` section in its feature spec (but other methods in the same scope do) → skip just this method with INFO finding `"no spec skeleton declared for {method}"`

**Checkpoint extraction.** Each implementation must mark its algorithm steps with structured trace/log calls so they can be statically grepped. Convention:

| Language | Marker form | Example |
|---|---|---|
| Python | `logger.debug("checkpoint:NAME")` or `tracer.start_as_current_span("checkpoint:NAME")` (OpenTelemetry) | `logger.debug("checkpoint:validate_id_format")` |
| TypeScript | `logger.debug("checkpoint:NAME")` or `tracer.startSpan("checkpoint:NAME")` (OpenTelemetry) | `logger.debug("checkpoint:validate_id_format")` |
| Go | `slog.Debug("checkpoint:NAME")` or `span.AddEvent("checkpoint:NAME")` | `slog.Debug("checkpoint:validate_id_format")` |
| Rust | `tracing::debug!("checkpoint:NAME")` or `tracing::trace_span!("checkpoint:NAME")` | `tracing::debug!("checkpoint:validate_id_format")` |
| Java | `logger.debug("checkpoint:NAME")` or `Span.current().addEvent("checkpoint:NAME")` | `logger.debug("checkpoint:validate_id_format")` |

> **Note:** The example call sites above are *illustrative*. The normative extraction rule is the regex in `shared/api-extraction.md` E.4a, which matches any string literal of the form `"checkpoint:NAME"` regardless of which logger/tracer API wraps it. Any new logging or tracing library that accepts string arguments will automatically work without updating this table.

The literal prefix is `checkpoint:` followed by a snake_case identifier. Sub-agents in Step 2 grep for `checkpoint:[a-z_][a-z0-9_]*` inside each public method's source body and return them in their natural source order as a `skeleton` field on each method object. Main context flattens to `repo_skeletons[repo_name][symbol] = method.skeleton` after all sub-agents return.

**Skeleton comparison rules.** For each `(symbol, repo)` pair where both `spec_skeletons[scope][symbol]` and `repo_skeletons[repo][symbol]` exist and are non-empty:

1. **Set equality** — every checkpoint in spec must appear in implementation, and vice versa. Missing → FAIL `critical` "Repo {R} method {M} missing checkpoint `{C}` declared in spec". Extra → WARN "Repo {R} method {M} has undeclared checkpoint `{C}` (consider adding to spec)".
2. **Order equality** — the relative order of common checkpoints must match the spec. Order divergence → FAIL `critical` "Repo {R} method {M} executes `{A}` before `{B}` but spec orders them `{B}` before `{A}`". Use longest-common-subsequence diff to report minimum changes.
3. **Cross-repo consistency** — independent of spec, all repos must agree with each other on order. If two repos disagree even when both match the spec (e.g., spec has `[A,B]` but one repo has `[A,X,B]` and another has `[A,Y,B]`), this is allowed (X and Y are language-specific extras), but flag as INFO.

**Output format:**
```
┌────────────────────────────────┬──────┬────────┬──────┬──────┬────────┐
│ Registry.register skeleton     │ Spec │ Python │  TS  │  Go  │  Rust  │
├────────────────────────────────┼──────┼────────┼──────┼──────┼────────┤
│ validate_id_format             │  #1  │ #1 ✓   │ #1 ✓ │ #1 ✓ │ #1 ✓   │
│ check_duplicate                │  #2  │ #2 ✓   │ #2 ✓ │ MISS │ #2 ✓   │
│ resolve_dependencies           │  #3  │ #3 ✓   │ #3 ✓ │ #2 ✓ │ #3 ✓   │
│ acquire_write_lock             │  #4  │ #4 ✓   │ #4 ✓ │ #3 ✓ │ #4 ✓   │
│ insert_into_index              │  #5  │ #5 ✓   │ #5 ✓ │ #4 ✓ │ #5 ✓   │
│ emit_registered_event          │  #6  │ #6 ✓   │ #7 ⚠ │ #5 ✓ │ #6 ✓   │
│   ↑ TS reordered after release_write_lock                              │
│ release_write_lock             │  #7  │ #7 ✓   │ #6 ⚠ │ #6 ✓ │ #7 ✓   │
└────────────────────────────────┴──────┴────────┴──────┴──────┴────────┘
```

**Anti-pattern guard.** Sub-agents MUST NOT invent checkpoints — only report what is literally in the source. If a method has zero checkpoint markers, report `repo_skeletons[repo][symbol] = []` and let comparison logic decide (it produces `WARN: implementation has no checkpoint instrumentation but spec declares {N} checkpoints`).

**Store as `phase_a_skeleton_results`** for inclusion in Step 5 and Step 9 reports.

#### 4B: Contract Parity Check (DEFAULT — runs unless --internal-check=none)

**Purpose:** verify that every public method's *intent* (inputs validation, errors raised, side effects, return shape, behavioral properties) agrees across all implementations and with the spec's `## Contract:` block (when declared). This is the primary defense against the bug class the user cares about: "signatures match but logic/intent differs".

**Skip conditions:**
- `--internal-check=none` → skip this entire substep.
- No other skip conditions. Unlike skeleton, contract tier runs even when the spec declares no Contract block — in that case it runs in **cross-repo mode** (compare implementations against each other) and emits a `warning` that spec is incomplete.

**Inputs to this step:**
- `spec_contracts[scope][symbol]` from Step 3 (may be empty or partial)
- `repo_contracts[repo_name][symbol]` — flattened from each sub-agent's `contract` field on every method/function (see Step 2 and `shared/api-extraction.md` E.4b)

**Comparison rules.** For each `(symbol, repo)` pair:

1. **Inputs validation parity.**
   - If spec declares Contract: for each spec input, every repo must have a matching `{condition, reject_with}` entry. Missing validation → FAIL `critical` `"Repo {R} method {M} does not reject {param} when {condition} — spec requires reject_with={ErrorType}"`. Wrong error type → FAIL `critical`. Condition phrasing differs → `info` (the important thing is that the rejection exists with the correct error).
   - If spec is silent: cross-repo comparison. If any repo has a validation that another repo lacks for the same parameter, flag as `critical` `"Repo {R1} rejects {param} when {cond} (raises {E}) but repo {R2} does not — intent divergence"`.

2. **Errors raised parity.**
   - Spec-declared: the set of error types raised by each repo must equal the spec's `### Errors` set. Extra error → `warning` `"Repo {R} raises {E} from {M} which is not in spec contract"`. Missing error → FAIL `critical`. Error code mismatch (error type name matches but code differs) → FAIL `critical`.
   - Spec silent: set equality across repos. Any divergence → `critical`.

3. **Side-effect order parity.**
   - Spec-declared: use longest-common-subsequence diff between spec `### Side Effects` and each repo's extracted `side_effects[]`. Missing effect → `critical`. Reordered effect (e.g., spec says validate → acquire_lock, repo says acquire_lock → validate) → `critical` — order matters because partial-failure observability depends on it. Extra effect → `warning`.
   - Spec silent: cross-repo order comparison. Divergence → `critical`.

4. **Return shape parity.**
   - Spec-declared: repo's extracted return shape must match spec's `### Returns`. Mismatch → `critical`.
   - Spec silent: cross-repo. Divergence → `critical`.

5. **Properties parity.** For each of `async`, `thread_safe`, `pure`, `idempotent`, `reentrant`:
   - Spec-declared: repo's extracted value must match spec (true/false/null semantics — `null` from repo means "not statically determinable" and is compared only to other `null`s, not to true/false). Mismatch true-vs-false → `critical`. Mismatch true/false-vs-null → `warning` (extraction limit, not necessarily a bug).
   - Spec silent: cross-repo. Any repo declaring opposite of another → `critical`. All null → skip (not inferable in any language, defer to behavior tier).

6. **Cross-reference with Algorithm (skeleton tier).** If both Contract and Algorithm are declared for the same method, verify the Algorithm checkpoint sequence corresponds to the Contract's Side Effects order. Divergence → `warning` `"Contract side_effects order does not match Algorithm checkpoint order for {M} — spec is internally inconsistent"`. This is a spec-consistency finding, not per-repo.

**Output format:**

```
┌──────────────────────────────┬──────┬────────┬──────┬──────┬──────┐
│ Registry.register — Contract │ Spec │ Python │  TS  │  Go  │ Rust │
├──────────────────────────────┼──────┼────────┼──────┼──────┼──────┤
│ inputs.id.validation         │ REQ  │  ✓     │  ✓   │ MISS │  ✓   │
│ inputs.id.reject_with        │INVID │ INVID  │ INVID│ ERR  │INVID │
│ errors.DuplicateError        │ REQ  │  ✓     │  ✓   │  ✓   │  ✓   │
│ errors.DependencyError       │ REQ  │  ✓     │ MISS │  ✓   │  ✓   │
│ side_effect[1] acquire_lock  │ REQ  │  ✓     │ MISS │  ✓   │  ✓   │
│ side_effect[5] emit event    │ REQ  │  ✓     │  ✓   │ MISS │  ✓   │
│ return.on_success            │ None │ None   │ void │ error│ ()   │
│ property.thread_safe         │ true │ true   │ false│ true │ true │
│ property.idempotent          │false │ false  │ true │false │ false│
└──────────────────────────────┴──────┴────────┴──────┴──────┴──────┘
```

**Anti-pattern guard.** Sub-agents MUST NOT infer properties they cannot observe — return `null` rather than guessing. Main context's comparison logic treats `null` as "unknown", not as "false".

**Store as `phase_a_contract_results`** for inclusion in Step 5 and Step 9 reports. Every FAIL / WARN row becomes a finding with the structure:
```
{
  finding_id: "A-C-{seq}",
  severity: critical|warning|info,
  symbol: "Registry.register",
  row: "inputs.id.reject_with",
  spec_says: "InvalidIdError(INVALID_ID)",
  repos_disagree: {python: "InvalidIdError(INVALID_ID)", typescript: "InvalidIdError(INVALID_ID)", go: "Error(generic)", rust: "InvalidIdError(INVALID_ID)"},
  location: "apcore-go/src/registry.go",
  fix_hint: "Go implementation should raise InvalidIdError with code INVALID_ID (not generic error) when id fails pattern match"
}
```

**Emit rule: one finding per divergent repo, not one finding with a multi-repo `location` list.** The `location` field is a single file path. Rationale:

- Spec-authority divergence with 3 non-matching repos → emit 3 findings, each with its own `location` pointing at that repo's offending file. Share the same `symbol` + `row` + `spec_says` across the three; each gets a distinct `finding_id` (e.g., `A-C-017`, `A-C-018`, `A-C-019`).
- Spec-silent cross-repo divergence → pick the outlier repo (the one that disagrees with the majority, or with the most-reference repo `apcore-python`) and emit a single finding for that repo. If no clear outlier (even split), emit one finding per dissenting repo.

This keeps `location` as a single string (compatible with `/code-forge:fix --review` schema) and keeps every finding directly actionable on exactly one file.

---

#### 4C: Cross-Language Deep-Chain Analysis (DEFAULT ON — unless --deep-chain=off or --internal-check=none)

**Purpose.** The preceding substeps (4, 4A, 4B) all compare **extracted shapes** — signatures, checkpoint lists, contract tuples. Shape extraction is structurally blind to a class of bugs where the shape matches across languages but the **actual code inside the method** diverges:

- One language's public method silently omits an internal validation call that peer languages perform
- One language's iteration-over-external-input lacks a null guard that peer languages have
- One language's method updates only some of the maps/events that peer languages update
- One language's subscript/indexing path throws on malformed input where peer languages recover

Step 4C fills this gap by dispatching **one sub-agent per logical module** that reads all N languages' source for that module **side-by-side** and diffs the call graphs directly.

**Scope and boundary.** Step 4C does NOT perform a full single-repo code review — that is `code-forge:review`'s job. Step 4C is ONLY a **cross-language call-chain diff**: it reports divergences between languages for the same public method. Shared bugs (all N languages have the same defensive gap) are out of scope — run `code-forge:review` per-repo to catch those.

**Skip conditions:**
- `--deep-chain=off` → skip entire substep with INFO finding `"deep-chain analysis disabled by flag"`
- `--internal-check=none` → forced off, skip with INFO finding
- Only 1 implementation repo in scope (no peer to diff against) → skip with INFO finding `"deep-chain requires ≥2 implementations, only {repo} in scope"`

##### 4C.1 Enumerate Modules

Derive the list of logical modules to analyze. Each module corresponds to one `## Feature:` block in the documentation repo (i.e., one file under `{doc_repo}/docs/features/*.md`). For each feature spec file:

1. Parse the frontmatter / heading to extract the logical module name (e.g., `registry`, `executor`, `config`, `middleware`)
2. From `api_summaries[repo_name]` (Step 2 output), locate the source file(s) in each impl repo that contain the symbols belonging to that module. The mapping is: module name → set of symbols → set of source files per language.
3. Store as `modules_to_analyze = [{module_name, public_symbols, source_files_per_lang, spec_contract_block}]`

If a feature spec has no corresponding symbols in ≥2 implementations, skip that module (already flagged by Step 4.3 as missing-implementation).

##### 4C.2 Orchestrate Per-Module Sub-agents

Initialize `module_progress[module_name] = {status: pending, findings_count: 0, inconclusive_count: 0}` for every module.

Dispatch sub-agents in **batches of at most 5 simultaneously** (bounded concurrency — too many parallel sub-agents starve the orchestrator's tool budget). For each batch:

1. Launch `Agent(subagent_type="general-purpose")` for each module in the batch, all in a single round of parallel Agent calls
2. Each sub-agent uses the template from `@references/deep-chain-prompt.md`, with these variables filled:
   - `{module_name}` — the logical module
   - `{repos}` — list of implementation repo names
   - `{source_files}` — map of `{lang: file_path}` for this module
   - `{public_symbols}` — the list of public symbols (from Step 4.1 / `spec_api`) scoped to this module
   - `{verified_api}` — the per-repo verified signature rows for this module (so the sub-agent does NOT re-verify signatures — that is Step 4's job)
   - `{spec_contract}` — the `## Contract:` block from the feature spec if present; else empty
3. Mark `module_progress[module_name].status = in_progress` and record the sub-agent's assigned id
4. As each sub-agent returns:
   - Parse the JSON payload in the final fenced code block
   - Validate it has the required shape (`module`, `findings[]`, `graphs_available_for`, `analyzed_symbols`). If malformed, mark `status = failed`, print a visible warning, and do NOT retry silently — emit a CRITICAL finding `"deep-chain sub-agent for module {M} returned malformed output — manual review required"` so the failure surfaces in the report
   - Assign sequential `finding_id` values `A-D-{seq}` to each finding
   - Update `module_progress[module_name]` with the finding counts and set `status = complete` (or `inconclusive` if `inconclusive_count == findings.length` and `findings.length > 0`)
   - Print one progress line: `[4C] {module}: {critical}/{warning}/{info}/{inconclusive} findings — {status}`
5. When the batch completes, start the next batch until all modules have been dispatched

Store the flat finding list as `phase_a_deep_chain_results = [finding1, finding2, ...]`.

##### 4C.3 Severity Rules

The sub-agent proposes severities; the orchestrator MAY downgrade based on global context but MUST NOT upgrade without re-verifying:

- `critical` — keep as-is. These are cross-language divergences with concrete file:line:snippet citations showing one language does X and another skips it.
- `warning` — keep as-is. Typically order-of-side-effects divergences or extra-validation-in-one-repo.
- `info` — keep as-is.
- `inconclusive` — emit to the report as-is. **Do NOT convert `inconclusive` to `info` or drop it.** An entire module returning mostly `inconclusive` is a signal that either (a) the sub-agent lacked context, or (b) the languages genuinely diverge in ways that need human judgment. Both cases require visibility.

##### 4C.4 Anti-Pattern Guards

- **No silent success.** A module reporting zero findings must have a non-empty `confidence_notes` field proving the sub-agent actually traced the call chains. If `confidence_notes` is empty AND `findings` is empty, the orchestrator emits a WARNING `"deep-chain module {M} returned empty report with no confidence trace — sub-agent may not have read the source"` and does NOT accept the clean result.
- **No cross-module leakage.** If a sub-agent's finding cites files outside its assigned module's source set, drop that finding and emit WARNING `"deep-chain sub-agent leaked out of module scope — finding discarded"`.
- **No shape-only findings.** Findings MUST cite `file:line` in the `evidence` block for every language involved. Shape-only findings (those that could have been produced by Step 4B) are discarded — Step 4B already runs; Step 4C is for depth, not redundancy.
- **No shallow chains.** If the sub-agent's per-language graph for a public symbol contains `call: _private_helper(...)` leaves with no expansion beneath them AND the helper is defined in the same file / same repo / same module source set, the orchestrator rejects the report and re-invokes the sub-agent with an explicit reminder: *"Your graph for {symbol} left `_private_helper` unexpanded. Per `deep-chain-prompt.md` Rule 3b, same-file private helpers MUST be inlined — the bugs this step catches live inside those helpers. Re-run and inline the helper body."* Retry at most twice; after the second failure mark the module `failed` and surface as CRITICAL `[A-D-FATAL-{module}] deep-chain sub-agent could not produce expanded graphs — manual review required`. A sub-agent that repeatedly returns shallow chains is a dangerous signal (produces fluent but empty reports) and must be visible to the user, never accepted silently.

##### 4C.5 Output Format

For Step 5 and Step 9, each deep-chain finding renders as:

```
[{A-D-{seq}}] {severity} — {type}
  Module: {module_name}
  Symbol: {symbol}
  Divergence: {divergence}
  Evidence:
    python:     {file}:{line} — {one-line snippet excerpt}
    typescript: {file}:{line} — {one-line snippet excerpt}
    rust:       {file}:{line} — {one-line snippet excerpt}
  Recommendation: {recommendation}
  Verification: static-inference
```

The `Verification: static-inference` line is MANDATORY on every deep-chain finding. It signals to downstream consumers (tester, fix) that this is a static conclusion — tester MAY re-verify at runtime when `--internal-check=behavior` is also active.

---

#### 4.4 Store Phase A Results

Store the full evaluated checklist as `phase_a_results`:
- `verified_api` — the spec-defined API surface with per-symbol verification status from implementations. Definition: the union of all symbols from the spec, annotated with which implementations have them and whether they match. For PASS symbols, the spec definition is confirmed correct. For FAIL symbols, the spec definition is still authoritative (implementations are wrong).
- `checklist` — every item with its PASS/FAIL/WARN status
- `findings` — structured list of all failures with severity. This list is the UNION of Steps 4.1–4.3 (namespace `A-`), 4A (namespace `A-S-`), 4B (namespace `A-C-`), and 4C (namespace `A-D-`). All four namespaces share the same finding schema (`finding_id`, `severity`, `symbol`, `location`, `fix_hint`), and Step 4C findings additionally carry `type`, `evidence.{lang}`, `verification: "static-inference"`
- `module_progress` — per-module deep-chain orchestrator state (status + counts) from Step 4C, kept for the Phase A report and for the orchestrator to surface failed/inconclusive modules as visible warnings. Does NOT feed into Phase B directly.

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
  Trait/interface satisfaction gaps: {N}
  Multi-constructor coverage gaps: {N}

Internal contract (--internal-check >= contract — DEFAULT):
  Methods with spec Contract: {N}
  Methods in cross-repo-only mode (spec silent): {N}
  Validation rule divergences: {N}
  Error raised divergences: {N}
  Side-effect order divergences: {N}
  Return shape divergences: {N}
  Property divergences: {N}

Internal skeleton (--internal-check >= skeleton):
  Methods with spec skeleton: {N}
  Methods passing checkpoint set+order: {N}
  Methods missing checkpoints: {N}
  Methods with reordered checkpoints: {N}
  Methods with no instrumentation: {N}

Cross-language deep-chain (--deep-chain=on — DEFAULT):
  Modules analyzed: {N}
  Modules complete: {N}  failed: {N}  inconclusive: {N}
  Findings: critical {N} / warning {N} / info {N} / inconclusive {N}
  Top finding types:
    semantic-divergence:    {N}
    missing-validation:     {N}
    missing-registration:   {N}
    defensive-gap:          {N}
    error-path-divergence:  {N}
    contract-gap:           {N}

FAIL items (expanded):
  ❌ Registry.scan_directory()
     Present in: spec, apcore-python
     Missing in: apcore-typescript
     Spec: defined in docs/features/registry.md

  ❌ Executor.execute() — param mismatch
     Spec:       (module_id: str, input: dict, context: Context | None = None) -> ExecutionResult
     Python:     (module_id: str, input: dict, context: Context | None = None) -> ExecutionResult  ✓
     TypeScript: (moduleId: string, input: Record<string, unknown>) -> ExecutionResult  ✗ missing context param

  ❌ [A-D-004] missing-registration — Registry.discover (module: registry)
     Divergence: Rust discover_internal only inserts into descriptors/lowercase_map;
                 Python _discover_custom and TS _discoverCustom both call register() which
                 inserts into the modules map.
     Evidence:
       python:     apcore-python/src/apcore/registry/registry.py:276 — self.register(mod_id, mod)
       typescript: apcore-typescript/src/registry/registry.ts:251 — this.register(moduleId, mod)
       rust:       apcore-rust/src/registry/registry.rs:865 — (no modules.insert call)
     Verification: static-inference

  ⚠️ [A-D-007] defensive-gap — Registry._discoverCustom (module: registry)
     Divergence: TS does not null-guard customModules; Python iterates via list comprehension
                 which tolerates generator-returning discoverers; Rust's type system enforces
                 a Vec.
     Evidence:
       python:     apcore-python/src/apcore/registry/registry.py:262 — for entry in (custom_modules or [])
       typescript: apcore-typescript/src/registry/registry.ts:232 — for (const entry of customModules) // crashes on null
       rust:       apcore-rust/src/registry/registry.rs:864 — discovered: Vec<DiscoveredModule> (typed)
     Verification: static-inference
```

If `--save` flag: write report to the canonical default from `shared/ecosystem.md` §0.6a: `{ecosystem_root}/sync-report-phase-a-{YYYY-MM-DD}.md` (or the explicit path if one was provided).

If `--phase a` only: display this report and stop. Otherwise continue to Phase B.

---

## PHASE B: Documentation Internal Consistency

Phase B runs ONLY after Phase A completes. It verifies two things:
1. The documentation repo's internal documents are consistent with each other (no contradictions)
2. Implementation repos' README and examples are consistent with `verified_api` from Phase A

### Step 6: Audit Documentation (Parallel Sub-agents)

Spawn sub-agents in parallel: **one per documentation repo** + **one per implementation repo**, all simultaneously.

#### Sub-agent for Documentation Repo (apcore/ or apcore-mcp/)

**Sub-agent prompt:** Use the template from `@references/audit-doc-repo-prompt.md`, filling in `{doc_repo_path}`, injecting `{verified_api}` from Step 4.4, and `{deprecated_api}` from Step 3.

#### Sub-agent for Implementation Repo (apcore-python/, apcore-typescript/, etc.)

**Sub-agent prompt:** Use the template from `@references/audit-impl-repo-prompt.md`, filling in `{impl_repo_path}` and injecting the `{verified_api}` for that repo from Step 4.4.

**Main context retains:** Structured findings per repo.

---

### Step 7: Cross-Repo Documentation, Examples, and Tests Consistency

After collecting all per-repo findings, the main context performs cross-repo checks:

1. **Cross-repo API description consistency** — if apcore-python's README describes `Registry.get_module()` with certain behavior, and apcore-typescript's README describes `Registry.getModule()` differently, flag it (semantic description should match even if name differs by convention)
2. **Shared documentation links** — do all implementation repos link to the same docs site version?
3. **Doc repo vs implementation README alignment** — do implementation READMEs accurately reflect what the documentation repo's feature specs define?
4. **Cross-repo example scenario coverage** — compare example scenario inventories across implementation repos:
   - Each scenario present in one implementation should exist in ALL implementations
   - Missing scenario → WARNING: `"{scenario}" exists in {repo-A} examples but missing from {repo-B}`
   - Scenarios should demonstrate equivalent behavior (same API flow, same inputs → same outputs)
5. **Cross-repo test scenario coverage** — compare test scenario inventories across implementation repos:
   - For each feature area, compare the set of test scenarios across all implementations
   - Missing test scenario → WARNING: `"test_{scenario}" exists in {repo-A} but missing from {repo-B}"`
   - Missing feature area → CRITICAL: `"No tests for {feature_area} in {repo-B}, but {repo-A} has {N} tests"`
   - Report a cross-language test coverage matrix:
     ```
     Test Coverage Matrix:
       Feature Area      | Python | TypeScript | Rust
       registry          |   12   |     10     |   8   ⚠ missing: scan_glob, bulk_register
       executor          |    8   |      8     |   8   ✓
       config            |    5   |      3     |   5   ⚠ missing: env_override, nested_merge
     ```

---

### Step 7.5: Behavioral Equivalence Hand-off (only when --internal-check=behavior)

**Skip if `--internal-check` is `none` or `skeleton`.** This step runs ONLY when the operator opts into the behavior tier.

Sync alone cannot verify that two implementations produce the same outputs for the same inputs — that is the `tester` skill's job. When this tier is enabled, the main context invokes `tester` as a sub-step and merges its findings into Phase B.

**Deep-chain findings carry a `verification: "static-inference"` field intended as a future runtime-verification hook.** Today, tester does NOT consume Step 4C findings — it runs its standard `--category protocol` suite built from feature-spec Contract blocks. When that suite incidentally exercises a code path that a deep-chain finding flagged (e.g., a protocol test that happens to pass a malformed discoverer result), any resulting divergence surfaces as a tester finding in its own right; operators correlate by `(module, symbol)` manually.

**Roadmap (not implemented):** a future tester extension `--deep-chain-targets={sync-report-path}` would parse A-D-* findings and synthesize minimal inputs per finding, upgrading `verification` to `"runtime-verified"` when confirmed or `"static-inference-disputed"` when contradicted. The `static-inference` field is emitted today so that, when that extension lands, existing sync reports remain consumable without a format bump.

**Invocation contract.**

1. **Pre-filter implementation repos by `--lang`.** `tester` does NOT accept a `--lang` flag — it takes positional repo names. Resolve `impl_repos` to the language-filtered subset before invocation.
2. **Build the command** (positional repos are space-separated, matching `tester` SKILL.md Command Format):
   ```
   /apcore-skills:tester {repo1} {repo2} {repo3} --mode run --category protocol --save tester-{date}.md
   ```
3. **Concrete example.** For `/apcore-skills:sync --lang python,rust --internal-check=behavior` with discovered repos `apcore-python`, `apcore-typescript`, `apcore-rust`:
   ```
   /apcore-skills:tester apcore-python apcore-rust --mode run --category protocol --save tester-2026-04-07.md
   ```
   (`apcore-typescript` is excluded by the language pre-filter.)

**Result merging.**

1. Capture the tester report and parse its `Cross-Language Equivalence` section
2. Merge any FAIL findings into Phase B findings under scope `behavior` with severity mapping:
   - tester `divergence` → sync `critical`
   - tester `flaky` → sync `warning`
   - tester `skipped` → sync `info`
3. Each merged finding's `location` is the implementation file under test; `fix` is "see tester report {tester-{date}.md} for failing input/output diff"
4. **Failure modes:**
   - If `tester` skill is not installed → emit a single WARN finding `"behavior tier requested but tester skill not available"` and continue
   - If `tester` invocation runs but exits with errors → emit a single CRITICAL finding `"tester invocation failed: {error}"` and include the tester output in the report
   - If pre-filter leaves zero repos (all filtered out) → skip the entire step with INFO `"behavior tier skipped: --lang filter excluded all repos"`

Store merged findings in `phase_b_behavior_findings` for inclusion in Step 8 and Step 9 reports.

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
  Code example mismatches: {N}
  Deprecated API refs: {N}

  CONTRADICTIONS:
    ⚠ PRD §3.2 says "Registry supports glob patterns"
      but feature spec registry.md defines no glob parameter
    ⚠ SRS REQ-012 references "Executor.run()"
      but tech design §4.1 calls it "Executor.execute()"

--- Implementation Repos ---

  Repo                    | README | API Refs | Examples | Tests  | Cross-Doc
  apcore-python           |  PASS  |   PASS   |  PASS    |  PASS  |   PASS
  apcore-typescript       |  WARN  |   FAIL   |  WARN    |  WARN  |   FAIL
  apcore-rust             |  PASS  |   PASS   |  PASS    |  PASS  |   PASS
  apcore-mcp-python       |  PASS  |   PASS   |  PASS    |  PASS  |   PASS
  apcore-mcp-typescript   |  WARN  |   PASS   |  PASS    |  WARN  |   PASS

  MISMATCHES:
    ❌ apcore-typescript README Quick Start uses `findModule()`
       but verified API says `getModule()`
    ❌ apcore-typescript docs/usage.md says `execute(moduleId, input)`
       but verified API says `execute(moduleId, input, context?)`

--- Cross-Repo Examples ---

  Example scenario coverage:
    "basic_usage":     Python ✓  TypeScript ✓  Rust ✓
    "custom_config":   Python ✓  TypeScript ✗  Rust ✓
    "error_handling":  Python ✓  TypeScript ✓  Rust ✗

--- Cross-Repo Tests ---

  Test Coverage Matrix:
    Feature Area      | Python | TypeScript | Rust
    registry          |   12   |     10     |   8   ⚠ missing: scan_glob, bulk_register
    executor          |    8   |      8     |   8   ✓
    config            |    5   |      3     |   5   ⚠ missing: env_override, nested_merge

--- Behavioral Equivalence (--internal-check=behavior) ---

  Tester report: tester-{date}.md
  Protocol-category tests: {N} run
  Cross-language pass: {N}/{N}
  Divergences: {N}
    ❌ Executor.execute({"x": 1}) → Python returns {"y": 2}, TypeScript returns {"y": "2"}
    ❌ Registry.scan(empty) → Python returns [], Rust returns Err(NoModules)

--- Cross-Repo ---

  Cross-repo contradictions: {N}
  Link consistency: {PASS|FAIL}
```

If `--save` flag: write report to the canonical default from `shared/ecosystem.md` §0.6a: `{ecosystem_root}/sync-report-phase-b-{YYYY-MM-DD}.md` (or the explicit path if one was provided).

---

### Step 9: Combined Report

```
apcore-skills sync — Unified Consistency Report

Scope: {scope} | Languages: {langs} | Date: {date}
Phases: A (spec ↔ code) + B (documentation)

Finding ID namespaces:
  A-{seq}     Phase A signature / type / naming findings (Step 4.1–4.3)
  A-S-{seq}   Phase A skeleton findings (Step 4A — only when --internal-check >= skeleton)
  A-C-{seq}   Phase A contract findings (Step 4B — default when --internal-check >= contract)
  A-D-{seq}   Phase A deep-chain findings (Step 4C — default when --deep-chain=on)
  B-{seq}     Phase B documentation findings (Steps 6–8)
  All IDs are stable within a single run; regenerated per invocation.

═══ PHASE A: Spec ↔ Implementation ═══

Checklist: {N} items | PASS: {n} | FAIL: {n} | WARN: {n}

{checklist table — only FAIL/WARN items expanded}

Spec compliance:
  {impl-repo-1}: {N}/{total} ({pct}%)
  {impl-repo-2}: {N}/{total} ({pct}%)

Cross-implementation:
  Total: {N} | Match: {N} | Missing: {N} | Mismatch: {N} | Naming: {N} | Type: {N}
  Trait/interface gaps: {N} | Multi-constructor gaps: {N}

Internal contract (--internal-check >= contract — DEFAULT):
  Methods checked: {N} | Pass: {N} | Validation divergences: {N} | Error divergences: {N}
  Side-effect divergences: {N} | Return-shape divergences: {N} | Property divergences: {N}
  (omitted entirely if --internal-check=none)

Internal skeleton (--internal-check >= skeleton):
  Methods checked: {N} | Pass: {N} | Missing checkpoint: {N} | Reordered: {N} | No instrumentation: {N}
  (omitted entirely if --internal-check=none or --internal-check=contract, or if no spec skeletons defined)

Cross-language deep-chain (--deep-chain=on — DEFAULT):
  Modules: {N} analyzed | {N} complete | {N} failed | {N} inconclusive
  Findings: critical {N} | warning {N} | info {N} | inconclusive {N}
  By type: semantic-divergence {N} | missing-validation {N} | missing-registration {N} |
           defensive-gap {N} | error-path-divergence {N} | contract-gap {N}
  (omitted entirely if --deep-chain=off or --internal-check=none or <2 implementations)

═══ PHASE B: Documentation Consistency ═══

Doc repo internal:
  {doc-repo}: {N} contradictions, {N} gaps

Implementation repo docs:
  Repo                  | README | API Refs | Examples | Tests  | Cross-Doc
  (matrix)

Cross-repo examples: {N} missing scenarios
Cross-repo tests: {N} missing scenarios, {N} missing feature areas
Cross-repo contradictions: {N}

Behavioral equivalence (--internal-check=behavior):
  Tester report: tester-{date}.md
  Protocol tests: {N} run | Pass: {N} | Divergences: {N} | Flaky: {N}
  (omitted entirely if --internal-check != behavior)

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
  Phase A: {N} findings (critical: {n}, warning: {n}, info: {n}, inconclusive: {n})
    ├─ signature/type/naming (A-): {n}
    ├─ contract (A-C-): {n}
    ├─ skeleton (A-S-): {n}
    └─ deep-chain (A-D-): {n}
  Phase B: {N} findings (critical: {n}, warning: {n}, info: {n})
  Total: {N} findings
  Contradictions (doc internal): {N}
  Contradictions (cross-repo): {N}
```

If `--save` flag: write report to the canonical default from `shared/ecosystem.md` §0.6a: `{ecosystem_root}/sync-report-{YYYY-MM-DD}.md` (or the explicit path if one was provided).

#### 9.1 Review-Compatible Issue Report

**After the Combined Report, ALWAYS append a review-compatible report so that `/code-forge:fix --review` can directly consume it.**

Convert all CRITICAL and WARNING findings from both phases into `code-forge:review` format. Format follows `code-forge:review` output schema (see `code-forge/skills/review/SKILL.md`). If the review format changes, update this mapping accordingly.

Use the `# Project Review:` header with a **dynamic scope description** (derived from Step 1 — e.g., repo name, scope group, or "all") and structured issue entries. Output the review-compatible report as **raw markdown** (not inside a fenced code block) so that code-forge:fix can parse it from the conversation context.

```markdown
# Project Review: {scope_description}

## Consistency

{For each finding from Phase A and Phase B with severity critical or warning, emit one issue entry:}

- severity: <blocker | critical | warning>
  file: {target file path — the file that needs to be fixed}
  line: {line number or range, use 1 if unknown}
  title: [{finding_id}] {short title}
  description: {what is inconsistent and why it matters — include cross-reference to spec or other repo}
  suggestion: {concrete fix instruction — what to change, what to match against}
```

**Severity mapping from sync findings to review format:**

| Sync Severity | Review Severity | Condition |
|---------------|-----------------|-----------|
| critical | blocker | Missing API (symbol defined in spec but absent from implementation); missing trait/interface satisfaction; missing constructor variant; **deep-chain `missing-registration`** (Step 4C — one language's public method fails to update a map peers update, breaking later `get`/`list` calls) |
| critical | critical | Signature mismatch, type mismatch, spec chain contradiction; **contract validation/error/side-effect/return/property divergence** (Step 4B); **skeleton checkpoint missing or reordered** (Step 4A); **behavioral divergence** from tester (Step 7.5); **deep-chain `semantic-divergence` / `missing-validation` / `defensive-gap` / `error-path-divergence` / `contract-gap`** (Step 4C) |
| warning | warning | Naming inconsistency, doc mismatch, missing README section; **spec silent on Contract (cross-repo-only mode)**; **contract property null vs true/false** (extraction limit); **skeleton has extra checkpoint not in spec**; **flaky behavior test** from tester; **deep-chain order-only divergence** (Step 4C — same mutations, different order) |
| inconclusive | warning | **deep-chain `inconclusive` findings** (Step 4C) surface as review warnings with title prefix `[inconclusive]` and suggestion `"manual review required — static analysis could not determine whether divergence is intentional"`. Never silently dropped. |
| info | _(skip)_ | Not included — info-level findings are not actionable bugs |

**Deep-chain finding rendering.** Because a deep-chain finding cites multiple languages' evidence in a single logical divergence, emit **one review issue per non-reference language** (the "reference language" is the one whose behavior matches the spec Contract, or the majority if spec is silent). Each issue's `file` points at the offending language's source. Include the peer evidence in `description` so the fix agent sees the full picture:

```markdown
- severity: critical
  file: apcore-rust/src/registry/registry.rs
  line: 865
  title: [A-D-004] missing-registration — Registry.discover_internal skips modules map insert
  description: |
    Python (apcore-python/src/apcore/registry/registry.py:276) and TypeScript (apcore-typescript/src/registry/registry.ts:251) both call
    `register(module_id, module)` which inserts into the `modules` map. Rust `discover_internal`
    only inserts into `descriptors` and `lowercase_map`, never into `modules`. Subsequent `get(name)`
    will return None for discovered modules.
    Verification: static-inference.
  suggestion: |
    Inside the for-loop at registry.rs:867, after building the descriptor, call the internal
    registration path that updates core.modules (mirroring how Python's _discover_custom ends in
    self.register(mod_id, mod)). Do not add a new method — use the existing internal register path.
```

**Rules:**
- Group issues by file for efficient batch fixing
- The `file` field MUST point to the **implementation or doc file that needs changing** (not the spec file)
- The `suggestion` field MUST be concrete enough for code-forge:fix to act on directly (e.g., "Rename `findModule` to `getModule` to match spec" rather than "fix naming")
- For missing API stubs, include the expected signature from the spec in the `suggestion`
- For doc mismatches, include the correct value from `verified_api` in the `suggestion`

**Example output:**

```markdown
# Project Review: {scope_description}

## Consistency

- severity: blocker
  file: apcore-typescript/src/registry.ts
  line: 1
  title: [A-001] Missing API — Registry.scanDirectory()
  description: Registry.scan_directory() is defined in apcore/docs/features/registry.md and implemented in apcore-python, but missing from apcore-typescript.
  suggestion: Add `scanDirectory(path: string, options?: ScanOptions): Promise<Module[]>` method to Registry class, matching the spec signature.

- severity: critical
  file: apcore-typescript/src/executor.ts
  line: 42
  title: [A-003] Param mismatch — Executor.execute() missing context param
  description: Spec defines execute(moduleId, input, context?) but TypeScript implementation only has execute(moduleId, input). Missing optional context parameter.
  suggestion: Add optional `context?: Context` as third parameter to `execute()` method.

- severity: critical
  file: apcore/docs/prd.md
  line: 87
  title: [B-001] Spec chain contradiction — glob patterns
  description: PRD §3.2 says "Registry supports glob patterns" but feature spec registry.md defines no glob parameter. Documents disagree.
  suggestion: Remove glob pattern reference from PRD §3.2 to match feature spec, or add glob parameter to feature spec if the capability is intended.

- severity: warning
  file: apcore-typescript/README.md
  line: 35
  title: [B-002] API reference mismatch — findModule vs getModule
  description: README Quick Start uses `findModule()` but verified API says `getModule()`.
  suggestion: Replace `findModule(` with `getModule(` in README Quick Start code example.
```

If no CRITICAL or WARNING findings exist, still output the header with a note:

```markdown
# Project Review: {scope_description}

## Consistency

_(No actionable issues found — all checks passed.)_
```

---

### Step 10: Auto-Fix (only with --fix flag)

Group all findings from both phases by repo. Spawn one `Agent(subagent_type="general-purpose")` **per repo that has fixable findings, all in parallel**.

**Sub-agent prompts:** Use the templates from `@references/fix-prompts.md`. The file contains two prompt templates:
- **Fix Implementation Repo** — for each implementation repo with findings, fill in `{repo_path}`, `{language}`, and inject the Phase A/B findings.
- **Fix Documentation Repo** — for each documentation repo with findings, fill in `{doc_repo_path}` and inject the Phase B findings.

Wait for all sub-agents to complete. Display consolidated results:

```
Auto-fix results:

Implementation repos:
  apcore-typescript: Phase A: 3 naming fixes, 1 stub | Phase B: 2 readme, 1 example, 2 test fixes
    Tests: 287/287 ✓
    Files: 8 changed
  apcore-mcp-typescript: Phase A: 1 naming fix | Phase B: 0 readme, 0 example, 1 test fix
    Tests: 112/112 ✓
    Files: 2 changed

Documentation repos:
  apcore: 2 contradiction fixes, 1 flagged for manual review
    Files: 2 changed
    Manual review: PRD §3.2 vs feature spec — need human decision on glob pattern scope

Uncommitted changes — review with:
  cd {repo} && git diff
```
