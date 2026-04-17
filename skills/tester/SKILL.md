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
| **`conformance`** | **Shared input/output fixtures run identically across every SDK — the authoritative cross-language equivalence signal** | **`{doc_repo}/tests/conformance/**/*.yaml` (per `shared/conformance-fixtures.md`)** |

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
   - `core-sdk` repo → test only this repo (spec: `apcore`)
   - `mcp-bridge` repo → test only this repo (spec: `apcore-mcp`)
   - `a2a-bridge` repo → test only this repo (spec: `apcore-a2a`)
   - `toolkit` repo → test only this repo (spec: `apcore-toolkit`)
   - `protocol` repo (`apcore`) → test ALL core-sdk repos
   - `docs-site` repo (`apcore-mcp`) → test ALL mcp-bridge repos
   - `docs-site` repo (`apcore-a2a`) → test ALL a2a-bridge repos
   - `integration` repo → test only this repo (spec: self)
   - Any other recognized type (e.g., `cli`, `tooling`, `shared-lib`) → test only this repo (spec: self — uses own docs/)
   - CWD not an apcore repo → use `AskUserQuestion` to ask which repos to test
3. Display: "Test scope: {repo-names} (from CWD). Specify repos explicitly for different scope."

#### 1.2 Resolve Spec Source for Target Repos

Each project type has its own authoritative spec location. Determine the **spec repo** and **spec files** for each target repo based on its type.

**Spec Source Resolution Table:**

| Target Repo Type | Spec Repo | Spec Files (search in order) |
|---|---|---|
| `core-sdk` (`apcore-python`, `apcore-typescript`, `apcore-rust`) | `apcore` | 1. `PROTOCOL_SPEC.md` (primary) 2. `docs/features/*.md` (per-feature) |
| `mcp-bridge` (`apcore-mcp-python`, `apcore-mcp-typescript`, `apcore-mcp-rust`) | `apcore-mcp` | 1. `docs/srs-apcore-mcp.md` (primary) 2. `docs/tech-design-apcore-mcp.md` (architecture) 3. `docs/examples-spec.md` (examples) |
| `a2a-bridge` (`apcore-a2a-python`, `apcore-a2a-typescript`) | `apcore-a2a` | 1. `docs/spec/*.md` (protocol spec) 2. `docs/features/*.md` (per-feature) |
| `toolkit` (`apcore-toolkit-python`, `apcore-toolkit-typescript`) | `apcore-toolkit` | 1. `docs/features/*.md` (per-feature) |
| `cli` (`apcore-cli`) | `apcore-cli` | 1. `docs/srs.md` (primary) 2. `docs/tech-design.md` (architecture) 3. `docs/features/*.md` (per-feature) |
| `integration` (`django-apcore`, `flask-apcore`, etc.) | self (each integration is its own spec) | 1. `docs/features/*.md` (if present) 2. `docs/{name}/*.md` (project docs) |

**Resolution steps:**

1. For each target repo, look up its type from `repos[]` (discovered in Step 0)
2. Map type → spec repo using the table above
3. Verify spec repo exists at `{ecosystem_root}/{spec_repo_name}/`
4. Scan for spec files in the listed order; collect all found files
5. If NO spec files found for a target repo: report as `SPEC_MISSING` warning and skip test generation for that repo (cannot generate tests without a spec)

**If `--spec` is specified:** filter to only feature specs matching the name (e.g., `--spec executor` → only `docs/features/*executor*.md` or SRS sections about executor).

Display:
```
Spec sources resolved:
  apcore-python         → apcore/PROTOCOL_SPEC.md + 10 feature specs
  apcore-mcp-python     → apcore-mcp/docs/srs-apcore-mcp.md + tech-design
  apcore-a2a-python     → apcore-a2a/docs/spec/ + 10 feature specs
  apcore-toolkit-python → apcore-toolkit/docs/features/ (6 specs)
  apcore-cli            → apcore-cli/docs/srs.md + tech-design + 9 feature specs
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

If a feature spec defines a public method but has **no `## Contract:` block**, emit a WARNING clause `"{file} declares {Method} with no Contract block — only narrative clauses generated, no contract-category tests"`. This surfaces spec debt directly in the tester report (and aligns with audit D4's finding).

#### 1.4 Load Shared Conformance Fixtures

Scan each scope's doc repo for `tests/conformance/**/*.yaml`:
- core scope: `apcore/tests/conformance/`
- mcp scope: `apcore-mcp/tests/conformance/`
- a2a scope: `apcore-a2a/tests/conformance/`
- toolkit scope: `apcore-toolkit/tests/conformance/`

For each fixture file found:
1. Parse per `shared/conformance-fixtures.md`. Extract `method`, `contract_ref`, `setup`, `cases[]`, `properties_check`.
2. Cross-check fixture coverage against the referenced Contract block:
   - Every `### Inputs` validation with `reject_with` must have at least one matching case → else WARNING `"fixture {F} does not cover input rule {rule} from Contract"`.
   - Every `### Errors` entry must have at least one case → else WARNING.
   - Every `### Properties` true value must have a corresponding case (concurrency for `thread_safe`, repeat-call for `idempotent`, etc.) → else WARNING.
3. Store as `conformance_fixtures[method] = fixture_obj`.

If no fixtures found, emit INFO finding `"no conformance fixtures in {doc_repo}/tests/conformance/ — cross-language equivalence will be checked only via per-language clause tests (lower fidelity). Create fixtures per shared/conformance-fixtures.md."`

Missing fixtures do not fail the run. They only reduce the confidence of the "protocol" and "conformance" categories.

#### 1.5 Build Test Matrix

Cross `spec_clauses[]` × `target_repos[]` × `categories[]`, plus conformance fixtures × target_repos[]:

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
  Total conformance cases to run: {cases × repos}
```

---

### Step 2: Generate Tests (Sub-agents)

**Skip if `--mode run`.**

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

**Skip if `--mode generate`.**

Spawn **one sub-agent per target repo**, all in parallel.

#### Sub-agent: Run Tests for {repo}

**Prompt:**
```
Run the full test suite for {repo_path}.

Language: {language}
Test command: {test_command}
  Python: cd {repo_path} && python -m pytest tests/ -v --tb=short 2>&1
  TypeScript: cd {repo_path} && npx vitest run --reporter=verbose 2>&1
  Go: cd {repo_path} && go test -v -count=1 ./... 2>&1
  Rust: cd {repo_path} && cargo test -- --nocapture 2>&1

Capture:
1. Full test output (stdout + stderr)
2. Pass/fail status per test
3. Total counts: passed, failed, skipped, errored
4. Failure details: test name, assertion message, expected vs actual
5. Coverage if available (append --cov for pytest, --coverage for vitest)

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
PASSED: {N}
FAILED: {N}
SKIPPED: {N}
COVERAGE: {pct or "unknown"}
FAILURES:
- test: {test_name}
  clause_id: {CLAUSE-ID from test docstring/comment, or "unknown"}
  message: {assertion error message}
  expected: {expected value}
  actual: {actual value}
  location: {file:line}
---
```

---

### Step 3.5: Run Shared Conformance Fixtures (Sub-agents)

**Skip if** `--category` excludes `conformance` AND `all`, OR no fixtures loaded in Step 1.4.

Spawn **one sub-agent per target repo**, all in parallel.

#### Sub-agent: Run Conformance Runner for {repo}

**Prompt:**
```
Run the conformance-fixture runner for {repo_path}.

Runner location (detect which exists):
  Python:     {repo_path}/tests/conformance_runner.py
  TypeScript: {repo_path}/tests/conformance_runner.ts
  Go:         {repo_path}/tests/conformance_runner.go
  Rust:       {repo_path}/tests/conformance_runner.rs

Fixture location: {doc_repo_path}/tests/conformance/

Invocation:
  Python:     cd {repo_path} && python tests/conformance_runner.py --fixtures {doc_repo_path}/tests/conformance/ 2>&1
  TypeScript: cd {repo_path} && npx tsx tests/conformance_runner.ts --fixtures {doc_repo_path}/tests/conformance/ 2>&1
  Go:         cd {repo_path} && go run ./tests/conformance_runner.go --fixtures {doc_repo_path}/tests/conformance/ 2>&1
  Rust:       cd {repo_path} && cargo run --bin conformance_runner -- --fixtures {doc_repo_path}/tests/conformance/ 2>&1

Parse CONFORMANCE_CASE blocks from output per shared/conformance-fixtures.md format.

Error handling:
- If runner does not exist: report STATUS: NO_RUNNER with detail "Repo {R} has no conformance_runner.{ext}. Bootstrap one by copying the pattern from the reference SDK and implementing the setup/call/reset/... primitives."
- If runner crashes: report STATUS: RUNNER_ERROR with full stderr
- If runner reports UNSUPPORTED for an op: pass the case's UNSUPPORTED through — it's a runner-completeness gap, not a test failure
- Capture ALL cases even on first failure (do not stop at first fail)

Return:
REPO: {repo-name}
STATUS: {completed|no_runner|runner_error}
TOTAL_CASES: {N}
PASS: {N}
FAIL: {N}
SKIPPED: {N}
UNSUPPORTED: {N}
ERROR: {N}
CASES:
- file: {relative path}
  method: {Class.method}
  case_id: {id}
  status: PASS|FAIL|SKIPPED|UNSUPPORTED|ERROR
  details: {as emitted by runner}
  duration_ms: {int}
```

Wait for all runners to complete. Store as `conformance_results[repo]`.

---

### Step 4: Cross-Language Behavioral Diff

After collecting results from all repos, compare test outcomes across languages for the same clause IDs **and** for the same conformance case IDs.

For each clause ID tested in multiple repos:
1. Extract pass/fail status from each repo
2. If all pass → **consistent** (good)
3. If all fail with same reason → **spec gap** (spec may need updating, or feature not implemented anywhere)
4. If mixed (pass in some, fail in others) → **BEHAVIORAL INCONSISTENCY** (critical finding)

Build two consistency matrices.

**Matrix A — Per-language Unit / Contract Clause Diff (clause-ID based):**

```
Cross-Language Behavioral Consistency (Clause):

Clause ID                                       | Python | TypeScript | Rust | Status
EXEC-001                                        | PASS   | PASS       | PASS | consistent
registry.register.input.id.invalid_pattern      | PASS   | PASS       | FAIL | INCONSISTENT
registry.register.error.DUPLICATE               | PASS   | FAIL       | PASS | INCONSISTENT
registry.register.property.thread_safe          | PASS   | FAIL       | PASS | INCONSISTENT
...

Consistent: {N}/{total} ({pct}%)
Inconsistent: {N} (CRITICAL — requires investigation)
Spec gaps: {N}
Not tested: {N}
```

**Matrix B — Conformance Fixture Diff (fixture case-id based — HIGHEST FIDELITY):**

This matrix is the authoritative cross-language equivalence signal because every SDK runs the **same** inputs and is compared against the **same** expected outputs.

```
Cross-Language Conformance (Shared Fixtures):

File/Case                                              | Python | TypeScript | Rust
registry/register.yaml: valid_registration             | PASS   | PASS       | PASS
registry/register.yaml: duplicate_rejected             | PASS   | FAIL       | PASS
registry/register.yaml: invalid_id_rejected            | PASS   | PASS       | FAIL
registry/register.yaml: thread_safe_concurrent         | PASS   | FAIL       | PASS
executor/execute.yaml: valid_execution                 | PASS   | PASS       | PASS
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

  Fixture files loaded: {N} (from {doc_repo}/tests/conformance/)
  Total cases: {N}

  Per-repo results:
    apcore-python:       {pass}/{total} PASS, {N} UNSUPPORTED, {N} SKIPPED
    apcore-typescript:   {pass}/{total} PASS, {N} UNSUPPORTED, {N} SKIPPED
    apcore-rust:         {pass}/{total} PASS, {N} UNSUPPORTED, {N} SKIPPED

  DIVERGENCES (CRITICAL — cross-language golden test mismatch):
    [registry/register.yaml:duplicate_rejected]
      apcore-python: PASS (raised DuplicateError, code=DUPLICATE)
      apcore-typescript: FAIL (silently overwrote, returned null)
      apcore-rust: PASS
      Action: Fix TypeScript register() to raise DuplicateError when id exists and overwrite=false

  COVERAGE GAPS (fixtures vs Contract):
    [registry/register.yaml] does not cover Contract rule: inputs.module.type_check / reject_with=TypeError
      Add a case with non-Module value for `module` and expect error code TYPE_ERROR

═══ TEST AUTHENTICITY ═══

  Total generated tests: {N}
  Non-trivial assertions: {N}
  Stub detected (rejected): {N}     — blocked from commit, rewritten via fallback
  Skipped with explicit reason: {N} — listed below for spec clarification

  Skips needing spec clarification:
    - {clause-id}: {skip reason}

═══ FAILING TESTS AS BUG REPORTS ═══

  {count} failing tests written to repos as executable bug reports.
  {count} divergent conformance cases flagged.
  To fix: run /code-forge:fix in the affected repo.
  To re-verify after fix: run /apcore-skills:tester --mode run
```

If `--save` flag is passed with an explicit path, write to that path. If `--save` is passed without a path, write to the canonical default from `shared/ecosystem.md` §0.6a: `{ecosystem_root}/tester-report-{YYYY-MM-DD}.md`.

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
  file: {doc_repo}/tests/conformance/{fixture_file}
  line: 1
  title: [T-F-003] Fixture coverage gap — Contract rule not exercised
  description: Fixture does not cover Contract rule {rule}. Adding a case would make cross-language divergence in this rule detectable.
  suggestion: Append case skeleton (see shared/conformance-fixtures.md).
```

Severity mapping:

| Signal | Review Severity |
|---|---|
| Matrix B (fixture) divergence | blocker |
| Matrix A inconsistency on `contract`-category clause | critical |
| Matrix A inconsistency on `unit` / `boundary` clause | critical |
| Authenticity-blocked stub (test body was trivial) | warning |
| Fixture coverage gap | warning |
| Spec missing `## Contract:` block (from Step 1.3 warning) | warning |

If no divergences, still emit the header with `_(No actionable issues found — all tests pass and cross-language conformance is green.)_`.

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
