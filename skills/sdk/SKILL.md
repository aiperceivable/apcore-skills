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

## Sub-agent Dispatch Policy

@../shared/subagent-policy.md

> **If you cannot see `<!-- SUBAGENT-POLICY-LOADED -->` above, this include did not expand** — some
> hosts do not support `@`-includes. Read `skills/shared/subagent-policy.md` directly before continuing; it is
> normative, not background reading. Proceeding without it silently drops the rules it
> carries.

**sdk-specific bindings:**

- **P2 ceiling: 4.** Flags that reduce it: n/a
- **P1/P3 plan:** Bootstrap is inherently small - one contract-extraction agent plus one scaffold agent.
- **P5:** a 429 aborts this run; persist finished units first, then report how to resume. This skill previously had **no** rate-limit handling.

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

- Adding a language package to Core or an existing Surface component
- Re-scaffolding an existing project that needs restructuring

## Command Format

```
/apcore-skills:sdk <language> [--type <type>] [--ref <repo>]
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `<language>` | Yes | — | Language directory recognized by discovery, e.g.  `rust`, `typescript`, `python` |
| `--type` | No | `core` | Component: `core`, `mcp`, `a2a`, `cli`, or `toolkit`. |
| `--ref` | No | auto-detect | Reference implementation to extract API from |

**Example:**
```
/apcore-skills:sdk rust --type mcp
→ Discovers apcore-mcp-python as reference
→ Extracts API contract (server/, auth/, adapters/, converters/, cli, explorer)
→ Scaffolds apcore-surfaces/mcp/rust/ (target ID apcore-mcp-rust)
```

## Context Management

Steps 2 and 4 use sub-agents. Step 2 analyzes the reference implementation. Step 4 generates the project skeleton. Steps 8–9 invoke code-forge skills which manage their own sub-agents. The main context orchestrates and retains only summaries.

## Workflow

```
Step 0 (ecosystem) → 1 (parse args) → 2 (extract API contract) → 3 (tech stack) → 4 (scaffold) → 5 (feature specs w/ Contract blocks) → 6 (code-forge config) → 7 (register and commit in monorepo) → 8 (port) → 9 (impl) → 9.5 (consistency gate — sync + tester) → 10 (summary)
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

1. Extract `<language>` and `--type` (`core` by default). Use a language key
   recognized by shared discovery. Normalize aliases such as `python` → `py`
   and `ts` → `typescript` before choosing the directory or target ID.
2. Resolve the selected component's documentation record from `repos[]` and
   use its `path` as `spec_root` and its `git_root` as the owning checkout.
   If the component record is missing, report which checkout or spec must be
   present before bootstrapping.

   | Component | Path relative to ecosystem root | Target ID |
   |---|---|---|
   | Core | `apcore/<lang>/` | `apcore-<lang>` |
   | MCP, A2A, CLI, Toolkit | `apcore-surfaces/<component>/<lang>/` | `apcore-<component>-<lang>` |

   Set `target-path` to `<spec_root>/<lang>` and use `git rev-parse --show-toplevel`
   from the component to confirm its owning checkout.
3. Resolve `--ref` as a discovered package ID or the path of a discovered
   package in this component. If omitted, resolve `cwd_repo.name` in `repos[]`
   and prefer that package when its record shares the same `spec_root` and
   differs from the target. Otherwise
   use its configured reference or the component's Python package. If neither
   is suitable, select another discovered implementation of the component.
   Resolve `ref_path` from the selected record's `path`.

**Data flow:** Step 1 adds `lang`, `type`, `spec_root`, `git_root`, `ref_path`,
`ref-repo-name`, `target-repo-name`, `target-path`, and the component's
`conformance_path` from its discovery record.

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

Spawn `Agent(subagent_type="general-purpose")` with the prompt from `references/extract-api-contract.md`, filling in `{lang}`, `{ref_path}`, `{type}`, `{protocol_path}`, and `{spec_root}`.

Store result as `api_contract`. If the sub-agent returns STATUS: NOT_FOUND or NO_EXPORTS, display error and ask the user to either provide a different reference or abort.

---

### Step 3: Confirm Tech Stack

Ask the user to confirm the target language tech stack.

@../shared/conventions.md (refer to "Testing Conventions" and "Dependency Conventions" sections)

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

Spawn `Agent(subagent_type="general-purpose")` with the prompt from `references/scaffold-project.md`, filling in: `{target-repo-name}`, `{target-path}`, `{lang}`, `{type}`, `{tech_stack}`, `{package_name}`, `{api_contract}`, `{ref_path}`, `{spec_root}`, `{conformance_path}`, `{conventions_path}` (= resolved path to `../shared/conventions.md`).

After sub-agent completes, rerun discovery. The new target ID must resolve to
`target-path` and report the expected `git_root`, `spec_root`, and
`release_tag_prefix`. Verify:
- Build config file exists
- Main module file exists with exports
- At least 3 source files exist
- Tests directory exists with test stubs
- Test helper/fixture file exists
- Examples directory exists (only if reference had examples/)
- README.md exists

---

### Step 5: Generate Feature Specs

Check if feature specs already exist at `{spec_root}/docs/features/*.md`.

If they exist:
- Link to them via `.code-forge.json` configuration
- Display: `Feature specs found: {N} specs in {spec_root}/docs/features/`

If they don't exist:
- Extract module list from the API contract
- Generate shared feature specs at `{spec_root}/docs/features/`:
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

Create a package-local relative symlink `{target-path}/.apcore-specs` pointing
to `{spec_root}/docs/features/`. Preserve a pre-existing link if it already
points there. This lets code-forge resolve the shared files through a relative
input path accepted by its directory validator.

Write `{target-path}/.code-forge.json`:
```json
{
  "directories": {
    "base": "./",
    "input": ".apcore-specs",
    "output": "planning/"
  },
  "port": {
    "source_docs": "{relative-path-to-component-spec-root}",
    "reference_impl": "{relative-path-to-ref}",
    "target_lang": "{lang}"
  },
  "git": {
    "auto_commit": false
  },
  "execution": {
    "default_mode": "ask",
    "auto_tdd": true,
    "task_granularity": "medium"
  }
}
```

Resolve the configuration from `target-path` and verify it reads shared feature
specs, selects the intended reference package, and keeps planning output under
the target package.

---

### Step 7: Register and Commit the Package

Use the owning monorepo's Git history and CI. Follow its workflow conventions
and register the new package in the applicable test and distribution workflows.
Extend a shared job or matrix when it already supports the language. Otherwise
add the smallest language-specific job needed to run the new package's tests
from its package directory, including shared conformance.

Gather the files edited for this package, including shared spec or CI files
from this bootstrap. Stage and commit the explicit repository-relative paths
from `git_root`. Use the same path-scoped commit procedure after implementation.
Preserve existing edits and verify the commit's file list after staging.

---

### Step 8: Auto-Port — Generate Implementation Plans

Display:
```
Scaffolding complete. Continuing with implementation plan generation...
```

Invoke `/code-forge:port` with the following context:
- `source_docs`: `{spec_root}`
- `reference_impl`: the absolute discovered `{ref_path}` passed as `--ref`
- `target_lang`: `{lang}`
- Working directory: `{target-path}`

Pass the existing package directory as the custom target and select **Use as-is**
when port offers to initialize or update it. Retain the package configuration
from Step 6 and the owning monorepo's Git checkout.

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

After each feature completes, commit the explicit feature paths from `git_root` as in Step 7.

---

### Step 9.5: Post-Impl Consistency Gate (MANDATORY)

Once `code-forge:impl` has finished all planned features, run the full consistency suite against the reference implementation. This is non-negotiable — an SDK that hasn't been verified for Contract parity is not an SDK, it's a draft.

#### 9.5.1 Sync vs Reference

```
/apcore-skills:sync {target-repo-name},{ref-repo-name} --internal-check=contract --deep-chain on --save {ecosystem_root}/sdk-bootstrap-sync-{target-repo-name}.md
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

Run when the component has a discovered conformance suite. Use both package IDs to compare the same cases:

```
/apcore-skills:tester {target-repo-name} {ref-repo-name} --mode run --category conformance --save {ecosystem_root}/sdk-bootstrap-tester-{target-repo-name}.md
```

Verify the new package's native tests ran the requested shared cases. Record
conformance divergences, suite errors, and cases with missing execution evidence
for the new package from the tester report.

#### 9.5.3 Gate Decision

**Rule:** PASS if and only if all of the following are zero:
- `sync_critical` — CRITICAL findings from `/apcore-skills:sync` (Phase A + Phase B + contract tier + deep-chain tier)
- `contract_divergences` — sync Step 4B / audit D10 findings (counted from the sync report's Contract tier section, A-C-* namespace)
- **`deep_chain_divergences` — sync Step 4C / audit D11 findings (counted from the sync report's Deep-Chain Parity section, A-D-* namespace). Any critical OR warning OR inconclusive finding counts. Info findings do not count.**
- `fixture_divergences` — cross-language conformance matrix mismatches from tester (Matrix B in tester Step 4)
- `fixture_gaps` — cases expected of the new package without a proven PASS, including failed assertions or unavailable suites

If any is greater than zero → **FAIL**. Present the highest-severity findings first.

The gate covers distinct failure modes:
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
