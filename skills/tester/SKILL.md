---
name: tester
description: >
  Spec-driven test generation and cross-language test verification for the apcore
  ecosystem. Reads the authoritative spec for each project type (PROTOCOL_SPEC.md for
  core, SRS/Tech Design for MCP/A2A/CLI, feature specs for toolkit) to generate test
  cases, runs them across all language implementations in parallel, and reports behavioral
  inconsistencies. Acts as the ecosystem's quality gatekeeper — audit checks static
  consistency, tester checks runtime correctness.
instructions: >
  This skill generates and runs tests — it does NOT implement production code.
  When a test fails, the output is a failing test case (Bug-as-failing-test),
  not a code fix. Fixes are delegated to code-forge:tdd or code-forge:fix.
---

# Apcore Skills — Tester


## ⚡ Execution Entry Point (READ THIS FIRST)

**When this skill is loaded, you MUST immediately begin executing the Workflow below — do not wait, do not summarize, do not ask "what should I do now". Skills are operational manuals, not reference documents.** Read the first executable step, perform it, then the next, etc., until the workflow completes or you reach an `AskUserQuestion` checkpoint.

If the harness shows you `Successfully loaded skill · N tools allowed`, that message means **the SKILL.md content was injected into your context** — it does NOT mean the skill has run. Skills do not "run" autonomously; you run them by executing the Detailed Steps below.

If you find yourself about to say "the skill didn't produce output", "skill 仍未输出", "falling back to manual testing", "回退到手动 tester", or anything similar, **STOP**. You have misunderstood how skills work. Go directly to the first executable step and start.

The first user-visible action of this skill should be either (a) the output of the first step, or (b) an `AskUserQuestion` if the first step needs disambiguation. Never an apology, never a fallback, never silence.

---

Spec-driven test generation and cross-language behavioral verification.

## Sub-agent Dispatch Policy

@../shared/subagent-policy.md

> **If you cannot see `<!-- SUBAGENT-POLICY-LOADED -->` above, this include did not expand** — some
> hosts do not support `@`-includes. Read `skills/shared/subagent-policy.md` directly before continuing; it is
> normative, not background reading. Proceeding without it silently drops the rules it
> carries.

**tester-specific bindings:**

- **P2 ceiling: 3 x repos.** Limit the selected targets with positional target IDs or narrow the tests with `--category`.
- **P1/P3 plan:** Step 2 = one per target repo (generation) - Step 3 = one per repo (execution) - Step 4 = one per repo (verification). The three passes are sequential, so at most `repos` are ever in flight.
- **P5:** a 429 aborts this run; persist finished units first, then report how to resume. This skill previously had **no** rate-limit handling.

## Iron Law

**EVERY TEST MUST TRACE TO A SPEC CLAUSE. Tests without spec traceability are noise — they verify accidents, not contracts.**

## Anti-Rationalization Table

| Thought | Reality |
|---------|---------|
| "The audit already checks API surface — tests are redundant" | Audit checks static structure (exports, signatures). Tester checks runtime behavior (does `execute()` actually return the right result?). They are complementary. |
| "I'll just write a few happy-path tests" | Happy-path tests give false confidence. Boundary conditions, error paths, and concurrency are where cross-language drift actually hides. |
| "I can skip running tests in language X — it probably works" | "Probably works" is not evidence. Run in every language or don't claim consistency. |
| "The test already exists so I don't need to regenerate it" | Existing tests may be stale if the spec evolved. Always diff against current spec before skipping generation. |
| "I'll mock the executor to speed up tests" | Mocks hide real behavioral differences. Use real code paths wherever possible. Only mock external services (network, filesystem, time). |
| "It's a green `it()`/`def test_`, so the clause is enforced in that language" | A green test only proves enforcement if it *asserts* enforcement. A test named `…: SKIP — emit() does not validate…` whose body is `expect(true).toBe(true)` is a **documented-skip placeholder** — it documents NON-enforcement and passes vacuously. Counting it as PASS fabricates a cross-language divergence. Before declaring a clause divergence, verify each side is a *real* PASS (non-trivial assertion of the behavior), a *real* SKIP (`it.skip`/`@pytest.mark.skip`/`#[ignore]`), or a placeholder — see Step 4's skip-vs-placeholder gate. Reclassify placeholders to SKIP. |

## When to Use

- After spec changes to generate/update tests across all implementations
- Before release to verify cross-language behavioral consistency
- When adding a new SDK to generate its full test suite from the spec
- When a bug is found in one language to verify all others aren't affected
- Periodic behavioral regression check (complement to `/apcore-skills:audit`)

## Command Format

```
/apcore-skills:tester [<repos...>] [--spec <feature>] [--mode generate|run|full] [--category unit|integration|boundary|protocol|contract|conformance|all] [--save report.md]
```

| Flag | Default | Description |
|------|---------|-------------|
| `<repos...>` | **cwd** | Positional repo names to test. If omitted, defaults to CWD repo. |
| `--spec` | all features | Specific feature spec to test (e.g., `executor`, `registry`, `acl`). Resolved against the target repo's spec source — see Step 1.2 for mapping. |
| `--mode` | `full` | `generate` = create test files only. `run` = execute existing tests only. `full` = generate then run. |
| `--category` | `all` | Test category filter: `unit`, `integration`, `boundary`, `protocol`, **`contract`** (Contract-block-derived tests per method: each input validation, each error, each property), **`conformance`** (shared fixtures from doc repo — cross-language golden tests), `all`. |
| `--save` | off | Save test report to file. |

## Test Categories

| Category | What It Covers | Source |
|----------|----------------|---------|
| `unit` | Single class/function behavior against spec | RFC 2119 clauses + REQ-xxx |
| `integration` | Cross-module interaction | Spec interaction diagrams |
| `boundary` | Edge cases, error paths, limits | Empty/null/max inputs; concurrency |
| `protocol` | Cross-language behavioral equivalence via per-SDK unit tests with same clause IDs | clause-ID tagging |
| **`contract`** | **Each `## Contract:` block → one test per input validation rule (assert correct error+code is raised), one per declared error (assert code), one per `### Properties` true value (assert async / thread-safe / idempotent / reentrant), one per `### Side Effects` (assert observable effects in order)** | **`## Contract:` blocks in feature specs (per `shared/contract-spec.md`)** |
| **`conformance`** | **Shared input/output fixtures run identically across every SDK — the authoritative cross-language equivalence signal** | **`repos[].conformance_path` (see `shared/conformance-fixtures.md`)** |

## Context Management

**Test generation and test execution are performed by parallel sub-agents.** The main context ONLY handles:
1. Spec analysis — reading protocol spec and feature specs
2. Orchestration — determining scope, building test matrix, spawning sub-agents
3. Aggregation — collecting results and producing the behavioral consistency report

Step 2 spawns **one sub-agent per target repo** (each generates all applicable categories). Step 3 spawns **one sub-agent per repo** for test execution. The main context never writes test files or runs tests directly.

## Workflow

```
Step 0 (ecosystem) → Step 1 (parse args + load specs + load Contracts + load conformance fixtures) → Step 2 (generate clause tests) → Step 3 (run clause tests + run conformance fixtures) → Step 4 (cross-language diff + fixture matrix) → Step 5 (report)
```

## Detailed Steps

### Step 0: Ecosystem Discovery

@../shared/ecosystem.md

---

### Step 1: Parse Arguments and Load Specs

#### 1.1 CWD-based Default Scope

**If no positional repos specified:**
1. Detect CWD repo from `cwd_repo` (Step 0)
2. Scope by CWD repo type:
   - Core SDK or Surface package → test only this package.
   - Core protocol or Surface documentation target → test the implementations that share its `spec_root`.
   - Integration or other independent implementation → test only this target and use its own documentation.
   - CWD not an apcore repo → use `AskUserQuestion` to ask which repos to test
3. Display: "Test scope: {repo-names} (from CWD). Specify repos explicitly for different scope."

#### 1.2 Resolve Spec Source for Target Repos

Resolve each target ID in `repos[]`. Use `path` for source and test commands.
Use `spec_root` for normative documents, or the target's own `path` for an
independent project. A monorepo package with a missing `spec_root` yields
`SPEC_MISSING`. Use the resolved directory for all spec reads and evidence.

| Target Type | Spec Files (search in order, relative to the resolved spec root) |
|---|---|
| `core-sdk` | `PROTOCOL_SPEC.md`, `docs/features/*.md` |
| `mcp-bridge` | `docs/srs-apcore-mcp.md`, `docs/tech-design-apcore-mcp.md`, `docs/features/*.md`, `docs/examples-spec.md` |
| `a2a-bridge` | `docs/spec/*.md`, `docs/features/*.md` |
| `toolkit` | `docs/features/*.md` and the component's normative requirements and design docs |
| `cli` | `docs/srs.md`, `docs/tech-design.md`, `docs/features/*.md` |
| Other independent targets | `docs/features/*.md`, then project-specific docs |

If no applicable spec files exist, emit `SPEC_MISSING` and skip clause generation
for that target. Existing tests and conformance can still run.

**If `--spec` is specified:** filter to only feature specs matching the name (e.g., `--spec executor` → only `docs/features/*executor*.md` or SRS sections about executor).

Display:
```
Spec sources resolved:
  apcore-python         → apcore/PROTOCOL_SPEC.md + 10 feature specs
  apcore-mcp-python     → apcore-surfaces/mcp/docs/srs-apcore-mcp.md + tech-design
  apcore-a2a-python     → apcore-surfaces/a2a/docs/spec/ + 10 feature specs
  apcore-toolkit-python → apcore-surfaces/toolkit/docs/features/ (6 specs)
  apcore-cli-python     → apcore-surfaces/cli/docs/srs.md + tech-design + 9 feature specs
```

#### 1.3 Extract Testable Clauses from Specs

For each resolved spec file, extract testable clauses. Two complementary sources:

**A) Narrative / requirement-ID clauses** (legacy — still useful for top-level behaviors):

| Spec Format | Clause Extraction Strategy |
|---|---|
| `PROTOCOL_SPEC.md` | Scan for RFC 2119 keywords (MUST/SHALL/SHOULD). Each keyword sentence = 1 clause. |
| `srs.md` / `srs-*.md` | Scan for requirement IDs (e.g., `REQ-xxx`, `FR-xxx`, `NFR-xxx`) and their descriptions. Each requirement = 1 clause. |
| `tech-design.md` / `tech-design-*.md` | Scan for interface definitions, method signatures, and behavioral descriptions in API sections. Each interface method + its described behavior = 1 clause. |
| `docs/features/*.md` | Scan for behavioral descriptions, acceptance criteria, and expected outcomes. Each distinct behavior = 1 clause. |
| `docs/spec/*.md` | Same as PROTOCOL_SPEC — scan for RFC 2119 keywords. |

**B) `## Contract:` block clauses (PRIMARY source when present — see `shared/contract-spec.md`):**

For every `## Contract: ClassName.method_name` block in any feature spec, generate **deterministic** clauses:

1. **One clause per `### Inputs` rule with `reject_with`** — deterministic id `{method_canonical}.input.{param}.{condition_slug}`:
   - requirement: "{method} rejects {param} when {condition} with {error_type}(code={code})"
   - category: `contract`
   - inputs: a synthesized value that fails `condition`
   - expected: error with that code

2. **One clause per `### Errors` entry** — id `{method_canonical}.error.{error_code}`:
   - requirement: "{method} raises {error_type} with code {code} when {trigger condition from Contract}"
   - category: `contract`
   - inputs: a synthesized value that triggers the error
   - expected: error with code matching

3. **One clause per `### Properties` true value** — id `{method_canonical}.property.{property_name}`:
   - `async`: clause tests that the method is awaitable (Python `await`, TS await, Go goroutine, Rust `.await`)
   - `thread_safe: true`: clause runs N parallel calls with distinct inputs, asserts no race (all complete, final state consistent)
   - `idempotent: true`: clause calls the method twice with identical inputs, asserts second call's outcome matches the first (same return, same observable state, no new errors)
   - `reentrant: true`: clause invokes the method from inside a callback the method itself calls, asserts no deadlock and correct result
   - `pure: true`: clause calls the method twice on the same state, asserts no self-mutation visible via any other public query
   - category: `contract`

4. **One clause per `### Side Effects` ordered step** — id `{method_canonical}.side_effect.{N}.{effect_slug}`:
   - requirement: "{method} executes {effect} at position {N} in source order"
   - category: `contract`
   - generation uses tracing/event-capture test scaffolding (the test observes the effect via public API — emitted event, post-state query, logged checkpoint, etc.)

Each Contract-derived clause carries the field `contract_source: {file}#Contract.{ClassName}.{method}` for traceability back to the spec.

**Clause de-duplication:** if a narrative clause and a Contract clause refer to the same behavior, keep the Contract-derived one (it is stricter and has deterministic inputs/outputs). Narrative clauses that are NOT covered by any Contract clause remain and are tagged `category: unit` or `boundary`.

Store as `spec_clauses[]`:
```
{
  "id": "registry.register.input.id.invalid_pattern",
  "source": "features/registry.md",
  "contract_source": "features/registry.md#Contract.Registry.register",
  "spec_repo": "apcore",
  "section": "Contract: Registry.register",
  "requirement": "register rejects id when pattern match fails with InvalidIdError(code=INVALID_ID)",
  "category": "contract",
  "inputs": { "id": "1invalid", "module": {"kind": "mock"} },
  "expected": { "error_type_snake": "invalid_id_error", "error_code": "INVALID_ID" },
  "error_path": true
}
```

If a feature spec defines a public method but has **no `## Contract:` block**, DO NOT emit this as a clause (it would pollute `spec_clauses[]` with an entry that has no inputs / expected / category). Instead, append an entry to a separate `spec_warnings[]` list:

```
{
  id: "no-contract-{file-slug}-{method-slug}",
  severity: "warning",
  kind: "no_contract_block",
  source_file: "{file}",
  symbol: "{Method}",
  detail: "{file} declares {Method} with no Contract block — only narrative clauses generated, no contract-category tests",
  fix: "Add a ## Contract: block per shared/contract-spec.md (see skill reference for template)"
}
```

`spec_warnings[]` is consumed by Step 5.1 review-compatible output (severity `warning`, file = `{source_file}`, suggestion = the Contract block template), parallel to D4's finding in audit. Keeps `spec_clauses[]` type-pure — every entry has a usable input/expected shape.

#### 1.4 Load Shared Conformance Fixtures

For each selected package, use its discovered `conformance_path`. Index each
unique suite once and associate it with the packages that share that path. Read
the suite's `README.md` and fixture schema when present, then inventory its JSON fixtures under
`fixtures/`. Use the suite's documented case layout and existing test drivers.
Only run YAML inputs when an existing driver uses them as test data.

Cross-check fixture coverage against a Contract block when a source links the
fixture to that block. Record missing checks against the actual fixture path.
Report an absent suite as `NO_FIXTURES` for the affected target. A null path is
expected for independent integrations without a shared suite.

#### 1.5 Build Test Matrix

Cross clauses with the selected implementations for their spec root and category. Cross each conformance suite only with its associated packages:

```
Test Matrix:
  Narrative clauses: {count}
  Contract-derived clauses: {count}
    inputs:       {N}
    errors:       {N}
    properties:   {N}
    side_effects: {N}
  Conformance fixtures: {count} files, {total_cases} cases
  Repos: {repo-names}
  Categories: {selected categories}
  Total test cases to generate: {clauses × repos}
  Total conformance cases to run: {sum of cases across the corresponding packages}
```

---

### Step 2: Generate Tests (Sub-agents)

**Skip if `--mode run` or `--category conformance`.**

Spawn **one sub-agent per target repo**, all in parallel. Each sub-agent generates all test files for its assigned repo.

#### Sub-agent: Generate Tests for {repo}

**Prompt:**
```
Generate test cases for {repo_path} based on the following spec clauses.

Language: {language}
Test framework: {framework} (Python: pytest + pytest-asyncio, TypeScript: vitest, Go: testing, Rust: cargo test)
Existing tests directory: {repo_path}/tests/

Spec clauses to cover:
{spec_clauses as structured list}

Test conventions (from ecosystem conventions):
- Python: pytest + pytest-asyncio, `pytest --cov`, 90%+ coverage target
- TypeScript: vitest, `npx vitest run --coverage`, 90%+ coverage target
- Go: testing, `go test -cover ./...`, 80%+ coverage target
- Rust: cargo test, `cargo test` + `cargo tarpaulin`, 80%+ coverage target
- Java: JUnit 5, `mvn test` / `gradle test`, 80%+ coverage target

For each spec clause, generate a test that:
1. Has a docstring/comment with the clause ID (e.g., "Tests EXEC-001" or "Tests registry.register.input.id.invalid_pattern")
2. Sets up minimal required state
3. Exercises the exact behavior described in the clause
4. Asserts the expected outcome using the spec's defined output
5. For error-path clauses: asserts the correct error type AND the correct error code (not just the type — the code field must match exactly)
6. **For contract-category clauses specifically:**
   a. `input.{param}.{slug}` clauses: construct an input that fails the rule, assert the declared error type+code is raised. The test name MUST include the clause ID verbatim so cross-language diff can match.
   b. `error.{CODE}` clauses: construct conditions that trigger the error, assert code matches.
   c. `property.async` clauses: assert the method is awaitable in this language (`await method()` succeeds).
   d. `property.thread_safe` clauses: launch N concurrent invocations (use language primitive — asyncio.gather / Promise.all / goroutines / tokio::spawn), assert no exception, assert final state consistent.
   e. `property.idempotent` clauses: call method twice with identical inputs, assert identical outcome (return value, observable state).
   f. `property.pure` clauses: call method twice on same input, assert no observable state change between calls.
   g. `side_effect.{N}.{slug}` clauses: observe the effect via public API (emitted event, logged checkpoint, post-state query), assert order.

**Test authenticity requirement (ANTI-STUB GUARD):**
Every generated test MUST perform at least one non-trivial assertion. The following are forbidden test bodies:
- Single line `assert True`, `expect(true).toBe(true)`, `t.Log("ok")`, `# TODO`
- Empty body after setup
- Assertion only on a variable's existence with no value check

If a clause cannot produce a meaningful test (e.g., spec is too vague), emit a skip with explicit reason:
- Python: `pytest.skip("Clause {id} lacks concrete acceptance criteria — deferred")`
- TypeScript: `it.skip(...)` with reason comment
- Go: `t.Skip(...)` with reason
- Rust: `#[ignore = "..."]`

Skipped tests are surfaced in the report as "needs spec clarification" — they are NOT counted as passing.

Test file organization:
- One test file per feature spec (e.g., test_executor.py, executor.test.ts)
- Group related tests in describe/class blocks by spec section
- Place in tests/ directory, mirroring the source structure

Test naming:
- Python: test_{clause_id_lowercase}_{brief_description}
- TypeScript: it("{clause_id}: {brief description}")
- Go: Test{ClauseID}_{BriefDescription}
- Rust: #[test] fn {clause_id_lowercase}_{brief_description}

Boundary tests (if category includes "boundary"):
- Null/undefined/None inputs where spec says "optional"
- Empty collections where spec says "list"
- Maximum length strings, deeply nested objects
- Concurrent execution (if spec mentions async)
- Duplicate registrations, missing modules, expired contexts

Integration tests (if category includes "integration"):
- Full pipeline: config → registry → executor → module → result
- Multi-module execution chains
- Middleware pipeline ordering

DO NOT mock core apcore classes. Only mock:
- External network calls
- File system operations
- Time/clock (use freezegun/vi.useFakeTimers)

For EACH generated test file, return:
FILE: {relative path from repo root}
STATUS: new|updated
CLAUSE_IDS: {comma-separated clause IDs covered}
TEST_COUNT: {number of test functions}
CONTENT:
{full file content}
---

Error handling:
- If a spec clause references a class/method that doesn't exist in this repo, generate
  the test anyway (it will fail — that's the point: Bug-as-failing-test)
- If the existing tests/ directory has conflicting files, generate with suffix _spec
  (e.g., test_executor_spec.py) to avoid overwriting user tests
```

After all sub-agents return, write generated test files to disk.

Display:
```
Tests generated:
  {repo-1}: {N} files, {M} test cases ({K} new, {J} updated)
  {repo-2}: {N} files, {M} test cases ({K} new, {J} updated)

Clause coverage:
  {covered}/{total} spec clauses have tests across all repos
  Uncovered: {list of clause IDs without tests, if any}
```

---

### Step 3: Run Tests (Sub-agents)

**Skip if `--mode generate` or `--category conformance`.**

Spawn **one sub-agent per target repo**, all in parallel.

#### Sub-agent: Run Tests for {repo}

**Prompt:**
```
Run the full test suite for {repo_path}.

Language: {language}
Test command: {test_command}
  Python: cd {repo_path} && python -m pytest tests/ -v --tb=short 2>&1
  TypeScript: use the package's test command and package manager. For the
              monorepo Vitest packages, use pnpm with the CI setup.
  Go: cd {repo_path} && go test -v -count=1 ./... 2>&1
  Rust: run cargo test with the package or checkout's configured options.

Capture:
1. Full test output (stdout + stderr)
2. Pass/fail status per test
3. Total counts: passed, failed, skipped, errored
4. Failure details: test name, assertion message, expected vs actual
5. Coverage if available (append --cov for pytest, --coverage for vitest)

**Documented-skip placeholder detection (run on every test reported PASS):**
A test runner reports a test as PASS whenever it executes without a failing assertion — including tests that assert nothing meaningful. Such "green placeholders" must NOT be reported as a true PASS, because Step 4 would read them as "behavior enforced in this language" and fabricate a divergence. For each PASS test, inspect its name/description AND its source body, and reclassify it to `PLACEHOLDER` if EITHER holds:
  a. The name/description contains `SKIP`/`SKIPPED`/`NOT ENFORCED`/`does not validate`/`no-op`/`fire-and-forget` (case-insensitive) but the test is NOT a real skip construct (`it.skip` / `test.skip` / `@pytest.mark.skip` / `pytest.skip(...)` / `#[ignore]` / `t.Skip(...)`). A green `it(...)`/`def test_...` whose *name* announces a skip is a placeholder documenting non-enforcement, not enforcement.
  b. The body is a trivial tautology or empty after setup: `expect(true).toBe(true)`, `assert True`, `assert 1 == 1`, `t.Log(...)` with no assertion, `assert x is not None` as the only check, or no assertion at all.
To inspect the body, open the test file at the reported location and read the function/`it` block. When in doubt (cannot locate the body, or assertion is ambiguous), classify as `PLACEHOLDER` and explain — under-counting enforcement is safe; over-counting it invents divergences.

Error handling:
- If dependencies not installed: report STATUS: DEPS_MISSING and list missing packages
- If test runner not found: report STATUS: RUNNER_MISSING
- If tests timeout (>5 min): kill and report STATUS: TIMEOUT
- Always capture partial output even on failure

Return in this exact format:
REPO: {repo-name}
LANGUAGE: {language}
STATUS: {pass|fail|deps_missing|runner_missing|timeout}
TOTAL: {N}
PASSED: {N}             # true PASS only — placeholders excluded
FAILED: {N}
SKIPPED: {N}
PLACEHOLDER: {N}        # green tests reclassified as documented-skip placeholders
COVERAGE: {pct or "unknown"}
FAILURES:
- test: {test_name}
  clause_id: {CLAUSE-ID from test docstring/comment, or "unknown"}
  message: {assertion error message}
  expected: {expected value}
  actual: {actual value}
  location: {file:line}
PLACEHOLDERS:
- test: {test_name}
  clause_id: {CLAUSE-ID from test docstring/comment, or "unknown"}
  reason: {name_announces_skip|trivial_tautology|empty_body}
  evidence: {the offending body line, e.g. `expect(true).toBe(true)`, or the skip-announcing name fragment}
  location: {file:line}
---
```

Report each placeholder under `PLACEHOLDERS` and exclude it from `PASSED`. A clause whose ONLY test in this repo is a placeholder is **not enforced** here — treat it as effectively SKIP for Step 4, never as PASS.

---

### Step 3.5: Run Shared Conformance Fixtures (Sub-agents)

**Run in `run` or `full` mode when the category is `conformance` or `all`.**

Spawn one sub-agent per selected package with fixtures. Give it `path`,
`git_root`, `conformance_path`, and the fixture inventory. Use the entry point
in the package's tests or CI as described in `shared/conformance-fixtures.md`.
Reuse Step 3 output only when it includes the same fixture-driven tests under
the required setup. Return the executed command, suite status and test counts,
and per-case results with fixture path, case ID, native test evidence and
assertion failure details. An existing adapter that emits `CONFORMANCE_CASE`
blocks can supply per-case results using the same fields.

Distinguish `COMPLETED`, `NO_FIXTURES`, `NO_RUNNER` and `RUNNER_ERROR` at suite
level. Preserve failed tests and partial output. Mark cases without evidence of
execution `UNVERIFIED`. A suite exit of zero alone is insufficient to populate
`PASS` in a case row.

Store results as `conformance_results[repo]`, including the resolved fixture
root and the gap statuses for packages that could not run the suite.

---

### Step 4: Cross-Language Behavioral Diff

After collecting results from all repos, compare test outcomes across languages for the same clause IDs **and** for the same conformance case IDs.

For each clause ID tested in multiple repos:
1. Extract pass/fail status from each repo
2. If all pass → **consistent** (good)
3. If all fail with same reason → **spec gap** (spec may need updating, or feature not implemented anywhere)
4. If mixed (pass in some, fail in others) → **BEHAVIORAL INCONSISTENCY** (critical finding)

**Skip-vs-placeholder gate (run BEFORE step 4 above declares any divergence):**
The per-clause status from Step 3 has four values, not two: `PASS`, `FAIL`, `SKIP`, `PLACEHOLDER`. **Normalize `PLACEHOLDER` → `SKIP` before comparing.** A green placeholder documents NON-enforcement; if you leave it as PASS you will read a clause that NO language enforces as "enforced here, missing there" and report a phantom divergence (this is exactly the T-B-001 false-positive class — a TS `it('…: SKIP — emit() does not validate…', () => expect(true).toBe(true))` counted as "enforced in TS" against fire-and-forget Python/Rust).

Apply this rule to a mixed row before calling it INCONSISTENT:
- A row is a divergence ONLY if at least one side is a **real PASS** (non-trivial assertion of the behavior) and at least one side is a **real FAIL** (the behavior was asserted and the assertion failed). 
- `SKIP` and `PLACEHOLDER` sides are **"not enforced here"**, not "enforced differently." A row that is all-`SKIP`/`PLACEHOLDER` (plus optionally real PASS where the behavior genuinely IS enforced) is a **coverage/consistency note**, not a behavioral inconsistency — confirm by checking whether the spec clause actually mandates the behavior (RFC 2119 MUST/SHALL) before escalating.
- If a row looks like a divergence, **open the green side's test body** and confirm it is a real PASS, not a placeholder, before writing the finding. Cite the asserting line in the finding's evidence. If you cannot point to a non-trivial assertion on the PASS side, downgrade the row to a placeholder/coverage note.

Build two consistency matrices.

**Matrix A — Per-language Unit / Contract Clause Diff (clause-ID based):**

```
Cross-Language Behavioral Consistency (Clause):

Cell values: PASS (real, asserts the behavior) | FAIL | SKIP (real skip construct, OR placeholder normalized from Step 3) | — (no test).
Never write PASS for a Step 3 PLACEHOLDER — it is rendered as SKIP here.

Clause ID                                       | Python | TypeScript | Rust | Status
EXEC-001                                        | PASS   | PASS       | PASS | consistent
registry.register.input.id.invalid_pattern      | PASS   | PASS       | FAIL | INCONSISTENT
registry.register.error.DUPLICATE               | PASS   | FAIL       | PASS | INCONSISTENT
registry.register.property.thread_safe          | PASS   | FAIL       | PASS | INCONSISTENT
event_system.emit.input.event_type.not_empty    | SKIP   | SKIP       | SKIP | not-enforced (no divergence — all fire-and-forget; was a phantom INCONSISTENT before placeholder normalization)
...

Consistent: {N}/{total} ({pct}%)
Inconsistent: {N} (CRITICAL — requires investigation)
Spec gaps: {N}
Not enforced (all SKIP/placeholder — uniform, NOT a divergence): {N}
Not tested: {N}
```

**Matrix B — Conformance Fixture Diff (fixture case-id based — HIGHEST FIDELITY):**

Group rows by suite and key each row by fixture-relative path and case ID. Compare only results backed by the same shared input and expectation. Show skipped, unsupported, errored and unverified cases separately from PASS and FAIL.

```
Cross-Language Conformance (Shared Fixtures):

File/Case                                              | Python | TypeScript | Rust
registry_ordering.json: valid_registration             | PASS   | PASS       | PASS
registry_ordering.json: duplicate_rejected             | PASS   | FAIL       | PASS
registry_ordering.json: invalid_id_rejected            | PASS   | PASS       | FAIL
registry_ordering.json: thread_safe_concurrent         | PASS   | FAIL       | PASS
call_chain.json: valid_execution                 | PASS   | PASS       | PASS
...

Conformance pass rate:
  apcore-python:       {N}/{total} ({pct}%)
  apcore-typescript:   {N}/{total} ({pct}%)
  apcore-rust:         {N}/{total} ({pct}%)

Divergent cases (act on these FIRST — golden-test divergence is unambiguous):
  {N} cases with mixed PASS/FAIL across languages
```

Any row in Matrix B with mixed PASS/FAIL is a **CRITICAL** behavioral divergence finding — this is the "same input produces different output" bug class that unit tests cannot catch.

When Matrix A and Matrix B disagree (e.g., Matrix A says consistent but Matrix B says divergent), trust Matrix B. Likely cause: per-language clause tests used different inputs, masking the divergence.

---

### Step 5: Report

Display consolidated report:

```
apcore-skills tester — Behavioral Consistency Report

Date: {date}
Scope: {repos tested}
Mode: {generate|run|full}
Spec sources: {spec_repo_names and doc counts}

═══ TEST EXECUTION SUMMARY ═══

  Repo                  | Status | Passed | Failed | Skipped | Coverage
  apcore-python         | pass   |   142  |    0   |    3    |   92%
  apcore-typescript     | fail   |   138  |    4   |    2    |   88%
  apcore-rust           | pass   |    95  |    0   |   12    |   78%

═══ CROSS-LANGUAGE CONSISTENCY ═══

  Behavioral consistency: {N}/{total} clauses ({pct}%)

  INCONSISTENCIES (action required):

  [EXEC-002] execute() with null context
    Python: PASS — returns ExecutionResult(status='success', context=None)
    TypeScript: FAIL — throws TypeError: Cannot read property 'traceId' of undefined
    Clause: "execute() SHOULD accept null context and create a default empty context"
    Action: Fix TypeScript implementation — see tests/test_executor_spec.ts:45

  [ACL-003] permission check with wildcard pattern
    Python: PASS — matches wildcard correctly
    Rust: FAIL — wildcard pattern not implemented
    Clause: "ACL MUST support wildcard patterns in permission strings"
    Action: Implement wildcard matching in apcore-rust/src/acl.rs

═══ SPEC GAPS (not implemented anywhere) ═══

  [BIND-007] Dynamic binding reload
    All repos: FAIL
    Clause: "Bindings SHOULD support hot-reload without executor restart"
    Action: Feature not yet implemented — track in backlog

═══ COVERAGE GAPS ═══

  Clauses without tests: {list}
  Repos with <80% coverage: {list}

═══ SHARED CONFORMANCE FIXTURES ═══

  Fixture files loaded: {N} (from {conformance_path}/)
  Total cases: {N}

  Per-repo results:
    apcore-python:       {pass}/{total} PASS, {N} UNSUPPORTED, {N} SKIPPED
    apcore-typescript:   {pass}/{total} PASS, {N} UNSUPPORTED, {N} SKIPPED
    apcore-rust:         {pass}/{total} PASS, {N} UNSUPPORTED, {N} SKIPPED

  DIVERGENCES (CRITICAL — cross-language golden test mismatch):
    [registry_ordering.json:duplicate_rejected]
      apcore-python: PASS (raised DuplicateError, code=DUPLICATE)
      apcore-typescript: FAIL (silently overwrote, returned null)
      apcore-rust: PASS
      Action: Fix TypeScript register() to raise DuplicateError when id exists and overwrite=false

  COVERAGE GAPS (fixtures vs Contract):
    [registry_ordering.json] does not cover Contract rule: inputs.module.type_check / reject_with=TypeError
      Add a case with non-Module value for `module` and expect error code TYPE_ERROR

═══ TEST AUTHENTICITY ═══

  Total generated tests: {N}
  Non-trivial assertions: {N}
  Stub detected (rejected): {N}     — auto-converted to skip("needs spec clarification — clause too vague") with the clause-id preserved so re-run can detect when the spec is fixed
  Skipped with explicit reason: {N} — listed below for spec clarification
  Documented-skip placeholders (Step 3, pre-existing tests): {N} — green tests reclassified to SKIP because they assert nothing / their name announces a skip. NOT counted as PASS; cannot establish cross-language enforcement.

  Skips needing spec clarification:
    - {clause-id}: {skip reason}

  Placeholders found in existing tests (reclassified, not phantom PASS):
    - {repo}/{location} [{clause-id}]: {reason} — {evidence}

═══ FAILING TESTS AS BUG REPORTS ═══

  {count} failing tests written to repos as executable bug reports.
  {count} divergent conformance cases flagged.
  To fix: run /code-forge:fix in the affected repo.
  To re-verify after fix: run /apcore-skills:tester --mode run
```

If `--save` flag is passed with an explicit path, write to that path. If `--save` is passed without a path, write to the canonical default from `shared/ecosystem.md` §0.6a: `{ecosystem_root}/tester-report-{cwd_repo}-{YYYY-MM-DD}.md`, where `{cwd_repo}` is the session's CWD repo/dir name resolved in Step 0. Including `{cwd_repo}` keeps same-day runs from different repos in separate files (no cross-scope overwrite) while a re-run of the same scope on the same day overwrites its own file idempotently (clean regeneration, never appended to history). The Write is always a full-file overwrite — reports are never concatenated with prior runs.

#### 5.1 Review-Compatible Issue Report

**ALWAYS append a review-compatible report so that `/code-forge:fix --review` can directly consume tester output.**

Convert every divergence (both Matrix A inconsistencies and Matrix B divergences) plus every authenticity-blocked stub into `code-forge:review` format. Same schema as sync Step 9.1 and audit Step 3.1.

```markdown
# Project Review: {scope_description} (tester)

## Behavior

- severity: blocker
  file: {outlier_repo}/{path-to-impl-file}
  line: {line}
  title: [T-B-001] Conformance divergence — {fixture_file}:{case_id}
  description: Shared fixture case `{case_id}` in `{fixture_file}` produces different outcomes. Python: PASS. TypeScript: FAIL ({unmet_expectation}). Rust: PASS. Same input → different output = intent divergence.
  suggestion: {concrete fix — cite the Contract's ### Errors entry or the non-outlier SDK's implementation as reference}

- severity: critical
  file: {repo}/{path-to-impl}
  line: 1
  title: [T-P-002] Property divergence — {method}.property.{name}
  description: Contract declares property.{name}=true; generated property test fails in {repo}. {observed behavior description}.
  suggestion: {concrete fix}

- severity: warning
  file: {conformance_path}/{fixture_file}
  line: 1
  title: [T-F-003] Fixture coverage gap — Contract rule not exercised
  description: Fixture does not cover Contract rule {rule}. Adding a case would make cross-language divergence in this rule detectable.
  suggestion: Add a case in the fixture's documented JSON format.
```

Severity mapping:

| Signal | Review Severity |
|---|---|
| Matrix B (fixture) divergence | blocker |
| Matrix A inconsistency on `contract`-category clause | critical |
| Matrix A inconsistency on `unit` / `boundary` clause | critical |
| Authenticity-blocked stub (test body was trivial) | warning — **aggregate one finding per repo**, not per stub; list the clause-ids in `description`. N stubs in one repo produce 1 review entry, not N. |
| Documented-skip placeholder in a **pre-existing** test (Step 3 reclassified a green test to SKIP) | warning — **aggregate one finding per repo**; list the clause-ids + locations in `description`. Title `[T-A-00x] Documented-skip placeholders masquerading as PASS`. Suggestion: convert to a real skip construct (`it.skip`/`@pytest.mark.skip`/`#[ignore]`) with a reason, or replace the tautology with a real assertion of the clause. Do NOT raise this as a behavioral divergence. |
| Fixture coverage gap | warning |
| Spec missing `## Contract:` block (from Step 1.3 warning) | warning |

If there are no findings, emit the header and summarize the test and conformance execution coverage. Report unverified suites separately.

---

## Coordination with Other Skills

| Skill | Relationship |
|-------|-------------|
| `apcore-skills:audit` | Audit checks static consistency. Tester checks runtime consistency. Run audit first for structural alignment, then tester for behavioral verification. |
| `apcore-skills:sync` | Sync verifies spec ↔ implementation alignment at the API surface level. Tester verifies at the behavioral level. Sync findings can inform which spec clauses need extra test coverage. |
| `code-forge:tdd` | Tester generates the test suite. When a test fails, `code-forge:tdd` is used to implement the fix (red → green → refactor). |
| `code-forge:fix` | When tester finds a behavioral inconsistency, the failing test IS the bug report. `fix` traces the root cause and applies the TDD fix. |
| `code-forge:verify` | After fixes are applied, `verify` ensures the claim "tests pass" is backed by fresh evidence. |
| `apcore-skills:sdk` | When a new SDK is bootstrapped, tester generates its full test suite from the spec, giving immediate coverage of the protocol contract. |
