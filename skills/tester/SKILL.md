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
  not a code fix. Fixes are delegated to code-forge:tdd or code-forge:fixbug.
---

# Apcore Skills — Tester

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
/apcore-skills:tester [<repos...>] [--spec <feature>] [--mode generate|run|full] [--category unit|integration|boundary|protocol|all] [--save report.md]
```

| Flag | Default | Description |
|------|---------|-------------|
| `<repos...>` | **cwd** | Positional repo names to test. If omitted, defaults to CWD repo. |
| `--spec` | all features | Specific feature spec to test (e.g., `executor`, `registry`, `acl`). Resolved against the target repo's spec source — see Step 1.2 for mapping. |
| `--mode` | `full` | `generate` = create test files only. `run` = execute existing tests only. `full` = generate then run. |
| `--category` | `all` | Test category filter: `unit` (single-module), `integration` (cross-module), `boundary` (edge cases + error paths), `protocol` (cross-language equivalence), `all`. |
| `--save` | off | Save test report to file. |

## Test Categories

| Category | What It Covers | Example |
|----------|----------------|---------|
| `unit` | Single class/function behavior against spec | `Executor.execute()` returns `ExecutionResult` with correct fields |
| `integration` | Cross-module interaction | Registry → Executor → Module pipeline works end-to-end |
| `boundary` | Edge cases, error paths, limits | Empty input, null context, max recursion depth, invalid module_id |
| `protocol` | Cross-language behavioral equivalence | Same input → same output across Python, TypeScript, Rust |

## Context Management

**Test generation and test execution are performed by parallel sub-agents.** The main context ONLY handles:
1. Spec analysis — reading protocol spec and feature specs
2. Orchestration — determining scope, building test matrix, spawning sub-agents
3. Aggregation — collecting results and producing the behavioral consistency report

Step 2 spawns **one sub-agent per target repo** (each generates all applicable categories). Step 3 spawns **one sub-agent per repo** for test execution. The main context never writes test files or runs tests directly.

## Workflow

```
Step 0 (ecosystem) → Step 1 (parse args + load specs) → Step 2 (generate tests) → Step 3 (run tests) → Step 4 (cross-language diff) → Step 5 (report)
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

For each resolved spec file, extract testable clauses:
- **Behavioral requirements** — "MUST", "SHALL", "SHOULD" statements
- **Input/output contracts** — parameter types, return types, error conditions
- **State transitions** — before/after conditions
- **Error specifications** — which errors for which conditions, error codes

**Extraction differs by spec format:**

| Spec Format | Clause Extraction Strategy |
|---|---|
| `PROTOCOL_SPEC.md` | Scan for RFC 2119 keywords (MUST/SHALL/SHOULD). Each keyword sentence = 1 clause. |
| `srs.md` / `srs-*.md` | Scan for requirement IDs (e.g., `REQ-xxx`, `FR-xxx`, `NFR-xxx`) and their descriptions. Each requirement = 1 clause. |
| `tech-design.md` / `tech-design-*.md` | Scan for interface definitions, method signatures, and behavioral descriptions in API sections. Each interface method + its described behavior = 1 clause. |
| `docs/features/*.md` | Scan for behavioral descriptions, acceptance criteria, and expected outcomes. Each distinct behavior = 1 clause. |
| `docs/spec/*.md` | Same as PROTOCOL_SPEC — scan for RFC 2119 keywords. |

Store as `spec_clauses[]`:
```
{
  "id": "EXEC-001",
  "source": "features/executor.md",
  "spec_repo": "apcore",
  "section": "Module Execution",
  "requirement": "execute() MUST return ExecutionResult with status='success' when module returns valid output",
  "category": "unit",
  "inputs": { "module_id": "valid", "input": "valid dict", "context": "optional" },
  "expected": { "status": "success", "output": "module return value" },
  "error_path": false
}
```

#### 1.4 Build Test Matrix

Cross `spec_clauses[]` × `target_repos[]` × `categories[]`:

```
Test Matrix:
  Clauses: {count} testable requirements
  Repos: {repo-names}
  Categories: {selected categories}
  Total test cases: {clauses × repos} (before dedup)
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
1. Has a docstring/comment with the clause ID (e.g., "Tests EXEC-001")
2. Sets up minimal required state
3. Exercises the exact behavior described in the clause
4. Asserts the expected outcome using the spec's defined output
5. For error-path clauses: asserts the correct error type and code

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

### Step 4: Cross-Language Behavioral Diff

After collecting results from all repos, compare test outcomes across languages for the same clause IDs.

For each clause ID tested in multiple repos:
1. Extract pass/fail status from each repo
2. If all pass → **consistent** (good)
3. If all fail with same reason → **spec gap** (spec may need updating, or feature not implemented anywhere)
4. If mixed (pass in some, fail in others) → **BEHAVIORAL INCONSISTENCY** (critical finding)

Build the consistency matrix:

```
Cross-Language Behavioral Consistency:

Clause ID   | Python | TypeScript | Rust | Status
EXEC-001    | PASS   | PASS       | PASS | consistent
EXEC-002    | PASS   | FAIL       | —    | INCONSISTENT
REG-005     | FAIL   | FAIL       | —    | spec-gap
ACL-003     | PASS   | PASS       | FAIL | INCONSISTENT
...

Consistent: {N}/{total} ({pct}%)
Inconsistent: {N} (CRITICAL — requires investigation)
Spec gaps: {N} (feature not implemented in any repo)
Not tested: {N} (clause not covered by generated tests)
```

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

═══ FAILING TESTS AS BUG REPORTS ═══

  {count} failing tests written to repos as executable bug reports.
  To fix: run /code-forge:fixbug in the affected repo.
  To re-verify after fix: run /apcore-skills:tester --mode run
```

If `--save` flag: write full report to specified path.

---

## Coordination with Other Skills

| Skill | Relationship |
|-------|-------------|
| `apcore-skills:audit` | Audit checks static consistency. Tester checks runtime consistency. Run audit first for structural alignment, then tester for behavioral verification. |
| `apcore-skills:sync` | Sync verifies spec ↔ implementation alignment at the API surface level. Tester verifies at the behavioral level. Sync findings can inform which spec clauses need extra test coverage. |
| `code-forge:tdd` | Tester generates the test suite. When a test fails, `code-forge:tdd` is used to implement the fix (red → green → refactor). |
| `code-forge:fixbug` | When tester finds a behavioral inconsistency, the failing test IS the bug report. `fixbug` traces the root cause and applies the TDD fix. |
| `code-forge:verify` | After fixes are applied, `verify` ensures the claim "tests pass" is backed by fresh evidence. |
| `apcore-skills:sdk` | When a new SDK is bootstrapped, tester generates its full test suite from the spec, giving immediate coverage of the protocol contract. |
