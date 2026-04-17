### Conformance Fixture Format

Shared input/output fixtures that every language SDK runs identically. The single authoritative source of "same inputs produce same outputs across all SDKs" — consumed by `tester` for cross-language behavioral equivalence.

#### Rationale

Per-language test generation is prone to false-green: each SDK writes its own tests with its own inputs and its own expected values, so "all tests pass in all languages" does not prove behavioral equivalence — it only proves each language is self-consistent.

Conformance fixtures fix this by providing a single **language-agnostic** input/output table that every SDK must satisfy. If Python returns `{"x": 1}` on input `{"a": 2}` but Go returns `{"x": "1"}`, the fixture runner flags the divergence regardless of whether each SDK's native tests pass.

Contract (`## Contract:` in feature specs, see `shared/contract-spec.md`) describes *what* a method does. Fixtures make that description *executable* across all languages.

#### Directory Layout

Each doc repo owns its own conformance suite:

```
apcore/                              # core doc repo
├── tests/
│   └── conformance/
│       ├── registry/
│       │   ├── register.yaml
│       │   ├── get_module.yaml
│       │   └── list_modules.yaml
│       ├── executor/
│       │   └── execute.yaml
│       └── config/
│           └── load.yaml
apcore-mcp/                          # mcp doc repo
├── tests/
│   └── conformance/
│       └── server/
│           ├── list_tools.yaml
│           └── call_tool.yaml
```

Each SDK implements a thin **runner** that:
1. Reads the fixture YAML files
2. For each case, invokes the declared method in the local SDK with the case's inputs
3. Emits a structured result line per case

```
apcore-python/
├── tests/
│   └── conformance_runner.py    # reads ../../apcore/tests/conformance/**/*.yaml
apcore-typescript/
├── tests/
│   └── conformance_runner.ts
apcore-rust/
├── tests/
│   └── conformance_runner.rs
```

#### Fixture YAML Format

One YAML file per public method. The filename matches the canonical (snake_case) method name. The file's top-level keys declare the method path and the list of cases.

```yaml
# apcore/tests/conformance/registry/register.yaml
method: Registry.register
contract_ref: docs/features/registry.md#Contract.Registry.register
version_introduced: "0.5.0"

setup:
  # steps run once before each case (shared state-establishing primitives)
  # primitives are language-agnostic — each SDK runner maps them to local code
  - op: new_registry
    bind: registry    # name to reference in cases

cases:
  - id: valid_registration
    description: "Register a valid module with a well-formed id"
    before:
      # per-case setup; runs after `setup` but before the method call
      - op: reset
        target: registry
    input:
      registry: $registry
      id: "foo"
      module:
        kind: mock
        name: "foo-module"
        version: "1.0"
    expect:
      returns: null
      side_effects:
        - registered_event(id="foo")
      post_state:
        - query: registry.has(id="foo")
          equals: true
        - query: registry.list().length
          equals: 1

  - id: duplicate_rejected
    description: "Re-registering the same id without overwrite raises DuplicateError"
    before:
      - op: reset
        target: registry
      - op: call
        target: registry
        method: register
        input: { id: "foo", module: { kind: mock, name: "foo", version: "1.0" } }
    input:
      registry: $registry
      id: "foo"
      module: { kind: mock, name: "foo-again", version: "1.0" }
    expect:
      error:
        code: DUPLICATE
        type_name_snake: duplicate_error   # canonical snake; each SDK maps to its error type
      post_state:
        - query: registry.list().length
          equals: 1                        # no partial mutation

  - id: invalid_id_rejected
    description: "Id not matching pattern is rejected"
    input:
      registry: $registry
      id: "1foo"
      module: { kind: mock, name: "x", version: "1.0" }
    expect:
      error:
        code: INVALID_ID
        type_name_snake: invalid_id_error

  - id: thread_safe_concurrent
    description: "Two concurrent register calls with distinct ids both succeed"
    concurrency:
      parallel: 2
      seeds: [1, 2]
    input_template:    # each parallel call gets its own input interpolated with seed
      registry: $registry
      id: "foo-${seed}"
      module: { kind: mock, name: "foo-${seed}", version: "1.0" }
    expect:
      returns: null  # each call returns successfully
      post_state:
        - query: registry.list().length
          equals: 2

properties_check:
  # top-level assertion that the method satisfies declared Contract properties
  idempotent: false     # explicit; cross-checked against Contract properties
  thread_safe: true
  async: false
  pure: false
```

#### Fixture Field Semantics

**Top-level:**
- `method` — `ClassName.method_name` in canonical (snake_case) form.
- `contract_ref` — path + anchor pointing to the `## Contract:` block this fixture validates. tester cross-checks that the fixture covers every input rule, every declared error, and every property from the referenced Contract. Missing coverage → WARNING.
- `version_introduced` — earliest SDK version on which this fixture is expected to pass. Runners may skip cases whose `version_introduced` is newer than the SDK under test, reporting SKIPPED with reason.
- `setup` — ordered list of setup primitives run once at the start of the file.
- `cases[]` — the list of conformance cases.
- `properties_check` — optional map asserting the method's behavioral properties. Cross-checked against the Contract's `### Properties` block; mismatch is a WARNING.

**Primitive operations (language-agnostic):**

Runners translate these to local code via a shared mapping. Each SDK's runner MUST implement the full set or explicitly report UNSUPPORTED for unimplemented ops.

| Op | Purpose | Fields |
|---|---|---|
| `new_registry` | Create fresh Registry | `bind` — name to reference later |
| `new_executor` | Create fresh Executor | `bind`, `config` (optional) |
| `call` | Invoke a method | `target`, `method`, `input` (map) |
| `reset` | Reset bound object to initial state | `target` |
| `sleep_ms` | Pause execution | `duration` |
| `tick_clock` | Advance mocked clock | `amount` |

Additional ops can be declared in `shared/conformance-ops.md` (future) — for now these six cover all current features.

**Case `input` field:**
- Object — shape matches the method signature, keys in canonical snake_case. Runner maps to target-language parameter names (snake → camel for JS, etc.).
- `$name` references point to bindings declared in `setup` or `before`.
- Nested objects use literal maps (YAML naturally handles them).

**Case `expect` field (one of):**

```yaml
# Success case
expect:
  returns: <value|null|$binding>
  side_effects:
    - <effect_descriptor>    # canonical form: "registered_event(id=\"foo\")"
  post_state:
    - query: <path-expression on bound object>
      equals: <value>
```

```yaml
# Error case
expect:
  error:
    code: <ERROR_CODE>                 # must match code in Contract's ### Errors
    type_name_snake: <canonical>       # e.g., duplicate_error; each SDK maps
    message_contains: <substring>      # optional
```

**Concurrency cases:** declared with `concurrency.parallel` ≥ 2 and `input_template` (instead of `input`). Runners spawn N concurrent invocations; each gets a distinct `$seed` substituted into the template. Concurrency cases verify `thread_safe` claims.

#### Runner Contract

Each SDK's `conformance_runner.{ext}` is invoked by `tester` (or manually) and MUST:

1. **Locate fixtures.** Default: resolve the doc repo from ecosystem layout (`apcore/` for core, `apcore-mcp/` for mcp), scan `tests/conformance/**/*.yaml`. Override via CLI flag `--fixtures <path>`.
2. **For each fixture file, for each case:**
   a. Run `setup` primitives once at file start; store bindings.
   b. Run `before` primitives (if any).
   c. Resolve `input` (substitute `$bindings`, runtime seeds).
   d. Invoke the target method with local-SDK calling convention.
   e. Compare against `expect`:
      - Success path: returns value matches, every side_effect descriptor observed (in order), every post_state query passes.
      - Error path: correct error type mapped from `type_name_snake`, matching error code, optional message substring.
3. **Emit one result line per case**, in this exact format (parseable by `tester`):

```
CONFORMANCE_CASE
  file: {relative path from repo root}
  method: Registry.register
  case_id: valid_registration
  status: PASS | FAIL | SKIPPED | UNSUPPORTED | ERROR
  details:
    actual_return: <value>
    actual_error: <type>(code=<code>)
    unmet_expectation: <description>      # only on FAIL
    skipped_reason: <description>         # only on SKIPPED
    unsupported_op: <op-name>             # only on UNSUPPORTED
    exception: <trace>                    # only on ERROR (runner bug, not test failure)
  duration_ms: <int>
END
```

4. **Exit codes:**
   - `0` — all cases PASS or SKIPPED
   - `1` — at least one FAIL
   - `2` — at least one ERROR (runner bug)
   - `3` — fixtures not found

5. **Concurrency cases:** runner spawns `concurrency.parallel` threads/coroutines/goroutines using the language's native primitive. All must complete; post_state queries run after all threads join.

#### Consumed by tester

`tester --category conformance` (new category) does:

1. Run each SDK's `conformance_runner.{ext}` in parallel sub-agents.
2. Parse `CONFORMANCE_CASE` blocks into a matrix:
   ```
   Case                                | Python | TypeScript | Rust
   registry/register.yaml: valid       | PASS   | PASS       | PASS
   registry/register.yaml: duplicate   | PASS   | FAIL       | PASS
   registry/register.yaml: invalid_id  | PASS   | PASS       | FAIL
   registry/register.yaml: concurrent  | PASS   | FAIL       | PASS
   ```
3. Any row with mixed PASS/FAIL → CRITICAL behavioral divergence finding.
4. Emit a Cross-Language Conformance section in the tester report.

`tester --category all` includes conformance by default.

#### Coverage Check (tester verifies fixture ↔ Contract alignment)

Before running fixtures, tester cross-checks each fixture against its `contract_ref`:

1. Every `### Inputs` validation rule with `reject_with` → there must be a case with that rejection as `expect.error`. Missing → WARNING `"fixture {F} does not cover input validation rule {param}.{condition} from Contract"`.
2. Every `### Errors` entry → there must be at least one case producing that error. Missing → WARNING.
3. Every `### Properties` true value → there must be a case validating it (e.g., `thread_safe: true` → at least one concurrency case; `idempotent: true` → at least one case that re-invokes).
4. `properties_check` values in fixture must match Contract's `### Properties`. Mismatch → WARNING `"fixture claims {prop}={val} but Contract says {val2}"`.

Coverage gaps go into the tester report's Coverage Gaps section — they don't fail the run, but signal the fixture is incomplete.

#### Relationship to Other Skills

- **spec-forge**: when generating feature specs with Contract blocks, optionally scaffold a matching empty fixture YAML.
- **sdk**: new SDK bootstrap includes a stub `conformance_runner.{ext}` that reads fixtures and reports UNSUPPORTED for every op. The runner is filled in as the SDK matures.
- **tester**: primary consumer. See `skills/tester/SKILL.md` Step 1.4 (load fixtures) and Step 3.5 (run conformance runners).
- **sync**: `--internal-check=behavior` optionally consumes the tester conformance report as a higher-fidelity signal than per-language unit tests.
- **audit**: D10 may cross-check that extracted repo contracts don't declare properties contradicted by fixture results.
