---
name: sdk
description: >
  Bootstrap and implement a new language SDK for the apcore ecosystem. Scaffolds
  the project structure, extracts API contract, then automatically continues with
  code-forge:port (plan generation) and code-forge:impl (TDD implementation) to
  deliver a fully implemented SDK — not just stubs.
---

# Apcore Skills — SDK

## ⚡ Execution Entry Point (READ THIS FIRST)

**When this skill is loaded, you MUST immediately begin executing the Workflow below — do not wait, do not summarize, do not ask "what should I do now". Skills are operational manuals, not reference documents.** Read the first executable step, perform it, then the next, etc., until the workflow completes or you reach an `AskUserQuestion` checkpoint.

If the harness shows you `Successfully loaded skill · N tools allowed`, that message means **the SKILL.md content was injected into your context** — it does NOT mean the skill has run. Skills do not "run" autonomously; you run them by executing the Detailed Steps below.

If you find yourself about to say "the skill didn't produce output", "skill 仍未输出", "falling back to manual SDK bootstrap", "回退到手动 SDK", or anything similar, **STOP**. You have misunderstood how skills work. Go directly to the first executable step and start.

The first user-visible action of this skill should be either (a) the output of the first step, or (b) an `AskUserQuestion` if the first step needs disambiguation. Never an apology, never a fallback, never silence.

---

Bootstrap a new apcore project in a new language. The project type is auto-discovered from the reference implementation — no hardcoded type list.

## Iron Law

**EVERY NEW PROJECT MUST IMPLEMENT THE FULL API CONTRACT AND PASS THE POST-IMPL CONSISTENCY GATE (Step 9.5). No partial implementations — if you ship it, it must cover all exported symbols from the reference implementation, agree with the reference on Contract (inputs / errors / side effects / properties) AT BOTH the shape level (Contract tuples) AND the chain level (cross-language source diff), and pass shared conformance fixtures. "code-forge:impl finished" is NOT the completion bar — "Step 9.5 gate passed" is.**

## Anti-Rationalization Table

| Thought | Reality |
|---------|---------|
| "I'll start with just the core classes" | Start with a complete project skeleton. Feature implementation order is code-forge's job. |
| "Copy the Python structure exactly" | Use idiomatic target-language patterns. Same concepts, different structure. |
| "Tests can come later" | TDD is mandatory. Test infrastructure is set up in scaffolding. |
| "I'll figure out the naming as I go" | Naming is defined by conventions.md. Apply language rules from day one. |
| "Examples can be added after the API works" | Examples are ported from the reference implementation during scaffolding. Users need runnable code from day one. |
| "Step 9.5 passed with Contract tier — that's enough" | NO. Contract tier extracts declared shapes and diffs shapes. A just-bootstrapped SDK can pass Contract tier while having internal divergences that Contract extraction cannot see (internal method silently skips a validation call the reference performs; iteration path lacks a null-guard the reference has; public method fails to update a map the reference updates). Step 9.5.1 MUST run `--deep-chain=on` and Step 9.5.3 MUST treat any A-D-* finding — including `inconclusive` — as a FAIL. Passing the shape check while the chain diverges means the SDK ships with latent bugs. |
| "The code-forge:port plan said it would implement X, so it did" | Do not trust the plan's claim. Verify X exists, is wired through the public API, and is called from the same path the reference calls it from. Step 9.5's deep-chain check is what catches "the plan said it implemented validate_module_id, but it was only added to the impl file and never called from discover_internal". |

## When to Use

- Starting any new apcore project in a new language (any `--type` — auto-discovered from reference)
- Re-scaffolding an existing project that needs restructuring

## Command Format

```
/apcore-skills:sdk <language> [--type <type>] [--ref <repo>]
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `<language>` | Yes | — | Target language: `go`, `rust`, `java`, `csharp`, `kotlin`, `swift`, `php` |
| `--type` | No | `core` | Project type (e.g., `core`, `mcp`, `a2a`, `toolkit`). Any string — new types are auto-supported via reference discovery. |
| `--ref` | No | auto-detect | Reference implementation to extract API from |

**Example:**
```
/apcore-skills:sdk go --type mcp
→ Discovers apcore-mcp-python as reference
→ Extracts API contract (server/, auth/, adapters/, converters/, cli, explorer)
→ Scaffolds apcore-mcp-go/ with Go source stubs, test stubs, and ported examples
```

## Context Management

Steps 2 and 4 use sub-agents. Step 2 analyzes the reference implementation. Step 4 generates the project skeleton. Steps 8–9 invoke code-forge skills which manage their own sub-agents. The main context orchestrates and retains only summaries.

## Workflow

```
Step 0 (ecosystem) → 1 (parse args) → 2 (extract API contract) → 3 (tech stack) → 4 (scaffold) → 5 (feature specs w/ Contract blocks) → 6 (code-forge config) → 7 (git init) → 8 (port) → 9 (impl) → 9.5 (consistency gate — sync + tester) → 10 (summary)
```

## Bundled References

- `references/extract-api-contract.md` — Sub-agent prompt template for Step 2
- `references/scaffold-project.md` — Sub-agent prompt template for Step 4

## Detailed Steps

### Step 0: Ecosystem Discovery

@../shared/ecosystem.md

**Data flow:** Step 0 produces the following variables used by subsequent steps:
- `ecosystem_root` — absolute path to the parent directory containing all apcore repos
- `protocol_path` — path to the `apcore` protocol spec repo (e.g., `{ecosystem_root}/apcore/`)
- `repos[]` — list of discovered repos with metadata
- `config` — merged configuration object

---

### Step 1: Parse Arguments

Parse `$ARGUMENTS`:

1. Extract `<language>` — required, ask the user if missing
2. Extract `--type` — default `core`
3. Extract `--ref` — resolve reference repo (priority order):
   - If `--ref` explicitly specified: use that
   - **If CWD is a same-type apcore repo** (e.g., in `apcore-python/` and `--type core`): use CWD repo as reference
   - Otherwise auto-detect: look for `apcore-{type}-python` in ecosystem root (for `core` type, look for `apcore-python`)

Derive target repo name using the naming pattern:
- `core` type → `apcore-{lang}` (special case: no type infix)
- All other types → `apcore-{type}-{lang}` (e.g., `apcore-mcp-go`, `apcore-a2a-rust`, `apcore-toolkit-java`)

Derive target path: `{ecosystem_root}/{target-repo-name}/`

**Data flow:** Step 1 adds: `lang`, `type`, `ref_path`, `target-repo-name`, `target-path`

Check if target directory already exists:
- If exists with source files: warn and ask — "Update scaffolding" / "Use as-is" / "Cancel"
- If exists but empty: proceed

Display:
```
SDK Bootstrap:
  Language:   {lang}
  Type:       {type}
  Reference:  {ref-repo} ({ref-lang})
  Target:     {target-path}
```

---

### Step 2: Extract API Contract (Sub-agent)

Spawn `Agent(subagent_type="general-purpose")` with the prompt from `references/extract-api-contract.md`, filling in: `{lang}`, `{ref_path}`, `{type}`, `{protocol_path}`.

Store result as `api_contract`. If the sub-agent returns STATUS: NOT_FOUND or NO_EXPORTS, display error and ask the user to either provide a different reference or abort.

---

### Step 3: Confirm Tech Stack

Ask the user to confirm the target language tech stack.

@../shared/conventions.md (refer to "Testing Conventions" and "Dependency Conventions" sections)

**For Go:**
- Go version: "1.21+ (Recommended)" / "1.22+"
- Module path: default `github.com/aipartnerup/{target-repo-name}`
- Test extras: "Standard testing (Recommended)" / "testify"
- Schema validation: "go-jsonschema (Recommended)" / "gojsonschema" / "Other"

**For Rust:**
- Rust edition: "2021 (Recommended)" / "2024"
- Async runtime: "tokio (Recommended)" / "async-std" / "None (sync only)"
- Serialization: "serde (Recommended)" / "Other"
- Schema: "schemars (Recommended)" / "Other"

**For Java:**
- Java version: "17+ (Recommended)" / "21+"
- Build tool: "Gradle (Recommended)" / "Maven"
- Schema validation: "Jackson (Recommended)" / "Gson"
- Test framework: "JUnit 5 (Recommended)" / "TestNG"

**For other languages:** Single open-ended question about tech stack preferences.

Store `tech_stack` decisions.

---

### Step 4: Scaffold Project (Sub-agent)

Spawn `Agent(subagent_type="general-purpose")` with the prompt from `references/scaffold-project.md`, filling in: `{target-repo-name}`, `{target-path}`, `{lang}`, `{type}`, `{tech_stack}`, `{package_name}`, `{api_contract}`, `{ref_path}`, `{conventions_path}` (= resolved path to `../shared/conventions.md`).

After sub-agent completes, verify:
- Build config file exists
- Main module file exists with exports
- At least 3 source files exist
- Tests directory exists with test stubs
- Test helper/fixture file exists
- Examples directory exists (only if reference had examples/)
- README.md exists

---

### Step 5: Generate Feature Specs

Check if feature specs already exist at `{protocol_path}/docs/features/*.md`.

If they exist:
- Link to them via `.code-forge.json` configuration
- Display: `Feature specs found: {N} specs in {protocol_path}/docs/features/`

If they don't exist:
- Extract module list from the API contract
- Generate feature specs at `{target-path}/docs/features/`:
  - One per module (executor, registry, schema, etc.)
  - Each spec contains:
    - Module purpose
    - Public API surface (classes, functions, signatures)
    - Acceptance criteria
    - **One `## Contract: ClassName.method_name` block per public method** — per `shared/contract-spec.md`. Fields generated from what can be inferred from the reference implementation:
      - `### Inputs` — from reference method parameter list + any visible validation guards in reference source (grep for `if not X: raise`, early-return patterns); leave `validation` / `reject_with` as `TODO` when the reference has no guard
      - `### Errors` — from `raise X`/`throw new X`/`return Err(X)` sites in the reference method; resolve codes where visible
      - `### Returns` — from reference return type
      - `### Properties` — fill `async` from reference signature; others render as `null` with an inline `# TODO — fill during implementation` comment (never as the literal string `"TODO"` — that violates the contract-spec format; see `shared/contract-spec.md` §Properties)
      - `### Side Effects` / `### Preconditions` / `### Postconditions` — emit as a bulleted `TODO — fill in during implementation` placeholder (these are free-form prose sections, so a literal TODO comment is fine — only the scalar Properties field requires `null`)
- **Never emit an empty Contract block.** If literally no inference is possible, skip the method and surface it in the summary as "Contract skeleton not generated for {method} — insufficient reference signal; fill by hand".
- Display: `Feature specs generated: {N} specs, {M} Contract blocks (filled: {filled}, TODO: {todo})`

---

### Step 6: Generate .code-forge.json

Write `{target-path}/.code-forge.json`:
```json
{
  "directories": {
    "base": "./",
    "input": "{relative-path-to-feature-specs}",
    "output": "planning/"
  },
  "port": {
    "source_docs": "{relative-path-to-protocol}",
    "reference_impl": "{relative-path-to-ref}",
    "target_lang": "{lang}"
  },
  "execution": {
    "default_mode": "ask",
    "auto_tdd": true,
    "task_granularity": "medium"
  }
}
```

Optionally add `reference_docs.sources` if the reference repo has `planning/` output. After writing, resolve each relative path (`input`, `reference_impl`, `source_docs`) and warn if any don't exist yet. Missing paths are acceptable (they may be created later) but should be noted.

---

### Step 7: Git Initialization

Initialize git and create the skeleton commit automatically:

```bash
cd {target-path}
git init
git add .
git commit -m "chore: initialize {target-repo-name} project skeleton"
```

Display:
```
Git initialized with skeleton commit.
```

---

### Step 8: Auto-Port — Generate Implementation Plans

Display:
```
Scaffolding complete. Continuing with implementation plan generation...
```

Invoke `/code-forge:port` with the following context:
- `source_docs`: `{protocol_path}`
- `reference_impl`: `{ref_path}`
- `target_lang`: `{lang}`
- Working directory: `{target-path}`

This generates per-feature implementation plans with TDD task breakdowns in `{target-path}/planning/`.

Wait for port to complete before proceeding.

---

### Step 9: Auto-Impl — Execute TDD Implementation

Display:
```
Implementation plans generated. Starting TDD implementation...
```

Invoke `/code-forge:impl` to execute all planned features sequentially. Each feature follows the TDD Red-Green-Refactor cycle:
1. Run failing tests (red — already created in Step 4)
2. Write minimal implementation to pass (green)
3. Refactor for idiom and clarity

Continue until all features are implemented or a blocking error occurs. If a blocking error occurs, stop and display the error with context so the user can intervene.

After each feature completes, commit the implementation:
```bash
git add .
git commit -m "feat({module}): implement {feature-name} for {target-repo-name}"
```

---

### Step 9.5: Post-Impl Consistency Gate (MANDATORY)

Once `code-forge:impl` has finished all planned features, run the full consistency suite against the reference implementation. This is non-negotiable — an SDK that hasn't been verified for Contract parity is not an SDK, it's a draft.

#### 9.5.1 Sync vs Reference

```
/apcore-skills:sync {target-repo-name},{ref-repo-name} --phase all --internal-check=contract --deep-chain=on --save {ecosystem_root}/sdk-bootstrap-sync-{target-repo-name}.md
```

This compares the new SDK against the reference for:
- Public API signatures (Phase A Steps 4.1–4.3)
- Behavioral contracts — SHAPE-LEVEL (Step 4B: inputs validation tuples, errors, side effects, return shape, properties)
- **Call graphs — CHAIN-LEVEL (Step 4C: cross-language source diff per module — catches bugs that shape extraction is blind to, like internal methods skipping validation, defensive gaps on null/malformed inputs, missing map-inserts)**
- Documentation (Phase B)

Parse the saved report for:
- CRITICAL findings count
- Contract-tier divergence count (A-C-* namespace)
- **Deep-chain divergence count (A-D-* namespace)**

#### 9.5.2 Tester Run

Only run if the reference has a conformance suite:

```
/apcore-skills:tester {target-repo-name} --mode full --category all --save {ecosystem_root}/sdk-bootstrap-tester-{target-repo-name}.md
```

If the reference has `tests/conformance/` fixtures, the new SDK's conformance runner must have been scaffolded in Step 4. Verify it runs and emits CONFORMANCE_CASE blocks. If the runner is missing or emits UNSUPPORTED for many ops, surface as "Conformance runner incomplete — implement missing primitives in tests/conformance_runner.{ext}".

Parse the saved report for:
- Cross-language divergences (Matrix B)
- Authenticity-blocked stubs

#### 9.5.3 Gate Decision

**Rule:** PASS if and only if **all four** of the following are zero:
- `sync_critical` — CRITICAL findings from `/apcore-skills:sync` (Phase A + Phase B + contract tier + deep-chain tier)
- `contract_divergences` — sync Step 4B / audit D10 findings (counted from the sync report's Contract tier section, A-C-* namespace)
- **`deep_chain_divergences` — sync Step 4C / audit D11 findings (counted from the sync report's Deep-Chain Parity section, A-D-* namespace). Any critical OR warning OR inconclusive finding counts. Info findings do not count.**
- `fixture_divergences` — cross-language conformance matrix mismatches from tester (Matrix B in tester Step 4)

If any of the four is greater than zero → **FAIL**. Present the highest-severity findings first.

Rationale: all four counts measure distinct failure modes:
- **signature mismatch** (shape) — Phase A Steps 4.1–4.3
- **intent mismatch, shape-level** — Phase A Step 4B (declared contract tuples diverge)
- **intent mismatch, chain-level** — Phase A Step 4C (actual source code diverges in ways the Contract block does not capture; this is the failure mode that blind-spots shape-level checks)
- **behavioral mismatch** — tester runtime

None of them is acceptable in a just-bootstrapped SDK; tolerating one silently defeats the post-impl gate's purpose. **Chain-level `inconclusive` counts because a just-bootstrapped SDK should leave zero uncertainty** — if the deep-chain sub-agent could not determine whether the new SDK matches the reference, the operator must resolve the uncertainty before shipping.

On FAIL, display the top findings and use `AskUserQuestion`:
- "Run /code-forge:fix --review" — consumes the sync + tester review-compatible outputs and auto-patches
- "Manual fix — I'll do it" — stops here; user re-runs `/apcore-skills:sdk` after fixing (step 9.5 will re-run)
- "Accept and continue (NOT RECOMMENDED)" — requires rationale logged to `{ecosystem_root}/sdk-gate-overrides.md`

Only after the gate passes does Step 10 declare the SDK complete.

---

### Step 10: Display Summary

```
apcore-skills:sdk — SDK Complete

Target: {target-path}
Language: {lang}
Type: {type}
Modules: {N} source files implemented
Tests: {N} tests passing
Examples: {N} runnable examples
Feature specs: {N} specs

Implementation status:
  {feature-1}: ✅ implemented
  {feature-2}: ✅ implemented
  ...

Next steps:
  /apcore-skills:sync --lang {lang},{ref-lang}    Verify API consistency
  /apcore-skills:audit                              Comprehensive ecosystem check
  /apcore-skills:release                            Coordinated release
```

## Coordination with Other Skills

- **After sdk:** Use `apcore-skills:sync` to verify cross-language consistency
- **Before release:** Use `apcore-skills:audit` for comprehensive check
- **For release:** Use `apcore-skills:release` for coordinated version bump
