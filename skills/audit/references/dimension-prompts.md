# Audit Dimension Prompts — Sub-agent Templates

Each dimension is an independent sub-agent prompt. Variables common to all: `{repo_paths}`.

---

## Finding Suppression Gate (applies to every dimension below)

Before emitting ANY finding, each sub-agent MUST pass the candidate through these six checks. A finding that fails any check is dropped or downgraded, not reported as-is.

1. **Reachability** — Is this failure reachable under the project's actual use case? Not a hypothetical attacker, not a contrived input, not a "what if someone...". If you cannot cite a real call site or real config source that triggers this path, drop it.
2. **Trust boundary** — If this is a security finding (injection, SSRF, path traversal, deserialization exec, etc.), is the input source genuinely external (network / untrusted user / cross-trust-boundary file upload)? Internal dev-tool data flow (the project's own files, hard-coded values, type-checked internal calls, scanner output from developer-owned source) does NOT qualify as a trust boundary. Drop security findings on internal flows, or downgrade to warning with an explicit "trust-boundary: internal" note.
3. **Concrete vs speculative** — Drop findings whose justification begins with "if X ever happens", "could theoretically", "in case someone...", "a malicious Y might...", or similar. Speculation is not evidence. If the failure requires a contrived input nobody produces today, it is not a bug.
4. **Severity calibration** —
   - `critical` = demonstrable bug with a reproducible failure mode under the project's actual use case (cite the call site)
   - `warning` = real but non-breaking (inconsistency across repos, style divergence, defensive-improvement opportunity, edge case in internal code)
   - `info` = cosmetic or trend signal
   Design-preference disagreements, defensive-code style divergences, and "this could be more robust" suggestions MAX OUT at warning. Never escalate them to critical. A finding whose only impact is "the other SDK is stricter" is warning, not critical.
5. **Zero findings is valid** — If every check in a dimension passes, emit `FINDING_COUNT: 0` with a 1-2 line note of what you checked and why it is clean (show the verification: `"grep -rn 'register' src/apcore/registry/*.py → 7 matches, all with RE_ID guard at line before insert"`, not a narrative summary). Do NOT fabricate low-severity findings to pad the report. An evidenced empty dimension is a stronger signal than a padded one. When evidence is genuinely ambiguous, emit `inconclusive` with a reason — never invent a finding to fill the slot.
6. **Factual verifiability** — If the finding's `detail` or `category` makes a falsifiable claim about the codebase, the finding MUST include the verification artifact in `evidence` or `detail`. Trigger phrases: `dead export`, `dead code`, `unused`, `unused_internal`, `unused_config`, `unused_dep`, `duplicate`, `duplicates`, `parallel_impl`, `parallel implementation`, `reimplements`, `copy of`, `only used in`, `only referenced in`, `never called`, `never invoked`, `zero references`, `zero reads`, `no callers`, `reachability`, `stale`, `scope creep`, `N lines`, `exceeds N lines`. When triggered, the finding MUST carry ONE of:
   - **(a) Command + output** — a `grep -rn` / `rg` / equivalent search command line AND at least one matched-line from its output (or the explicit string `0 matches` when claiming absence). A narrative paraphrase like `"grep returns only the declaration"` or `"scanned src/, no callers"` is NOT evidence — paste the actual output lines.
   - **(b) Explicit file:line citations** — for cross-repo claims (`duplicate`, `parallel_impl`, `inconsistent with`), cite BOTH sides with `{repo}/{path}:{line}` so the reviewer can verify both exist. For "only used in X", cite the original definition AND the grep proving no other uses. For "N lines" / "exceeds N lines", cite the start:end line range.
   - **(c) Cross-directory scope for dead-code claims** — `dead_export` / `unused` claims must search at least `src/` + `tests/` (and the examples directory if present). A dead-code claim whose verification is limited to one directory will be dropped by the orchestrator. State the search scope explicitly: `"grep -rn 'ErrorCodeMap' src/ tests/ examples/ → only matches in src/registry.ts:111"`.

   Failure mode this gate exists to catch: a sub-agent writes `"grep returns only the declaration; ERROR_CODE_MAP has zero reads"` when the symbol is actually read elsewhere in the same file. The only defense is to require the command output to be visible in the finding.

Apply this gate to every candidate finding, in every dimension, before formatting the output block.

### Finding format — evidence field (all dimensions)

The uniform finding format for D1–D10 is:

```
- severity: {critical|warning|info}
  repo: {repo-name}
  detail: {description — what is wrong}
  location: {file:line when applicable}
  fix: {suggested fix}
  evidence: {REQUIRED when detail/category matches any Gate 6 trigger phrase — paste the grep/rg command AND matched-line output, OR explicit cross-site file:line citations. A narrative summary is insufficient.}
```

D9 (`category` field is mandatory) and D10 (`spec_says` / `repos_disagree` / `symbol` fields) extend this base format; the evidence rule applies equally. For D9 findings whose `category` is one of `dead_export | unused_internal | duplicate | parallel_impl | reachability | scope_creep | stub_noop | loc_growth | unused_config | unused_dep` — Gate 6 is ALWAYS triggered; evidence MUST be present.

**Acceptable evidence example (D9 dead_export):**
```yaml
- severity: warning
  repo: apcore-typescript
  category: dead_export
  detail: "Registry.scanLegacyDir is exported but has no external callers"
  location: "src/registry.ts:156"
  fix: "Delete the method and its export; the only internal call at src/registry.ts:203 is itself inside a dead code path."
  evidence: |
    grep -rn "scanLegacyDir" apcore-typescript/ --include='*.ts'
    apcore-typescript/src/registry.ts:156:  scanLegacyDir(path: string): Module[] {
    apcore-typescript/src/registry.ts:203:    // return this.scanLegacyDir(fallback);  <-- commented out
    apcore-typescript/src/index.ts:42:export { Registry } from "./registry.js";
    → Only the definition and one commented-out self-reference; no external callers
      in src/, tests/, or examples/. Verified across 3 directories.
```

**Rejected evidence example (would be dropped by Gate 6):**
```yaml
detail: "Registry.scanLegacyDir appears unused"
evidence: "grep returns only the definition"
```
The second example is dropped because the grep command AND the actual output are not visible — the claim cannot be verified from the finding alone.

---

## D1 — API Surface Audit

```
Audit API surface consistency across apcore SDK implementations.

Repos to compare: {repo_paths}

For each repo:
1. Read the main export file (__init__.py / index.ts)
2. Count total exports
3. Categorize: classes, functions, types, enums, constants, errors
4. For each class: list constructor params and public method names

Compare across repos:
- Missing symbols (in one, not the other)
- Method count mismatches per class
- Constructor param count mismatches
- **Method param count mismatches** — for each shared method, compare the number of
  parameters across implementations. If Python `call()` has 4 params but TypeScript
  `call()` has 3, flag it. Use the spec/canonical definition as reference when available.
- **Global wrapper alignment** — if a language provides module-level convenience functions
  (e.g., Python `apcore.call()` wrapping `APCore.call()`), verify the wrapper has the
  SAME parameter count as the class method it wraps. A wrapper with fewer params silently
  drops functionality (e.g., missing `version_hint`). Check:
  - Python: compare `__init__.py` top-level functions against `client.py` class methods
  - TypeScript: compare default export functions against class methods
  Severity: warning for param count mismatch in wrappers

Return findings in format:
Error handling:
- If a repo path does not exist, skip it and report as: severity=warning, detail="Repo not found at {path}"
- If main export file is missing, report as: severity=warning, detail="No exports found in {repo}"

DIMENSION: D1 — API Surface
FINDING_COUNT: {N}
FINDINGS:
- severity: {critical|warning|info}
  repo: {repo-name}
  detail: {description}
  location: {file:line if applicable}
  fix: {suggested fix}
```

---

## D2 — Naming Conventions Audit

```
Audit naming conventions across apcore ecosystem repos.

Repos: {repo_paths}

Check against conventions:
- Python: snake_case files, snake_case functions, PascalCase classes
- TypeScript: kebab-case files, camelCase functions, PascalCase classes
- Package names match convention (snake_case for Python, kebab-case for npm)
- Error class names end with "Error"
- Enum names are PascalCase, enum values are UPPER_SNAKE

Scan all source files in each repo:
1. Check filenames in src/ directory
2. Grep for class/function definitions and verify naming
3. Check import/export names in main module file
4. Verify error classes follow naming pattern

Error handling: If a repo path does not exist or has no src/ directory, report as:
- severity: info, detail: "Repo {name} has no source files to audit"

Return findings in this exact format:
DIMENSION: D2 — Naming Conventions
FINDING_COUNT: {N}
FINDINGS:
- severity: {critical|warning|info}
  repo: {repo-name}
  detail: {description}
  location: {file:line if applicable}
  fix: {suggested fix}
```

---

## D3 — Version Sync Audit

```
Audit version synchronization across apcore ecosystem.

Repos: {repo_paths with types}

Check:
1. Core SDK versions must match (major.minor): {core repos}
2. MCP bridge versions must match (major.minor): {mcp repos}
3. Within each repo, version must be consistent across all version files
   - Python: pyproject.toml version == __init__.py __version__
   - TypeScript: package.json version == src/index.ts VERSION (if present)
4. Integration repos: dependency versions reference compatible core SDK versions

Error handling: If a build config file is missing or malformed, report as a warning finding rather than failing.

Return findings in this exact format:
DIMENSION: D3 — Version Sync
FINDING_COUNT: {N}
FINDINGS:
- severity: {critical|warning|info}
  repo: {repo-name}
  detail: {description}
  location: {file:line if applicable}
  fix: {suggested fix}
```

---

## D4 — Documentation Audit

```
Audit documentation quality across apcore ecosystem.

Repos: {repo_paths}

For each repo check:
1. README.md exists and contains: description, installation, quick start, link to docs
2. CHANGELOG.md exists and follows Keep a Changelog format
3. LICENSE file exists
4. Key source files have docstrings/JSDoc
5. Public API methods have parameter documentation
6. Examples directory exists (for integrations)

For documentation repos (apcore/, apcore-mcp/) additionally check:
7. **Contract coverage in feature specs**. For each `docs/features/*.md` file, identify every public class/function/method declared (by header pattern `## Class:`, `## Function:`, or API reference table). For each declared public symbol, check that a `## Contract:` block exists per `shared/contract-spec.md`. A Contract block MUST contain: `### Inputs`, `### Errors`, `### Returns`, `### Properties`. If a public symbol has no Contract block, report as WARNING with detail "feature spec {file} declares {Symbol} but has no ## Contract: block — intent parity cannot be verified". If a Contract block exists but is missing required fields, report as INFO.
8. **Algorithm section coverage** (optional — INFO only). Feature specs MAY have `## Algorithm:` blocks for methods that have complex internal sequences. Not required, but missing Algorithm prevents skeleton-tier sync. Report as INFO only.

Error handling: If a repo path does not exist, skip it and report as info finding.

Return findings in this exact format:
DIMENSION: D4 — Documentation
FINDING_COUNT: {N}
FINDINGS:
- severity: {critical|warning|info}
  repo: {repo-name}
  category: {readme|changelog|license|docstrings|contract_coverage|algorithm_coverage|...}
  detail: {description}
  location: {file if applicable}
  fix: {suggested fix}
```

---

## D5 — Test Coverage Audit

```
Audit test coverage across apcore ecosystem.

Repos: {repo_paths}

For each repo:
1. Check tests/ directory exists
2. Count test files
3. Map source files to test files (check for coverage gaps)
4. Run test suite and capture results (detect language from build config, check runner availability first):
   - Python: `pytest --tb=short -q`
   - TypeScript: `npx vitest run`
   - Go: `go test -cover ./...`
   - Rust: `cargo test`
   - Java (Maven): `mvn test -q`
   - Java (Gradle): `gradle test`
   - C#: `dotnet test`
   - Swift: `swift test`
   - PHP: `vendor/bin/phpunit`
   - Elixir: `mix test`
   If the test runner is not available, report as a finding instead of running.
5. If coverage tool available, capture coverage percentage

Error handling:
- If dependencies are not installed (import errors, module not found), report as: severity=warning, detail="Test dependencies not installed for {repo}"
- If test runner is not found, report as: severity=warning, detail="Test runner not available for {repo}"
- Do NOT fail the entire audit if one repo's tests can't run

Return findings in this exact format:
DIMENSION: D5 — Test Coverage
FINDING_COUNT: {N}
FINDINGS:
- severity: {critical|warning|info}
  repo: {repo-name}
  detail: {description}
  location: {file if applicable}
  fix: {suggested fix}
TEST_RESULTS:
- repo: {repo-name}
  status: {pass|fail|skipped}
  total: {N}
  passed: {N}
  failed: {N}
  coverage: {pct or "unknown"}
```

---

## D6 — Dependencies Audit

```
Audit dependency alignment across apcore ecosystem.

Repos: {repo_paths}

Check:
1. Core SDK dependencies: schema validation lib versions match expectations
2. MCP bridge dependencies: MCP SDK versions are compatible
3. Integration dependencies: core SDK version references are up-to-date
4. No duplicate dependencies with different versions across repos
5. Dev dependencies include linter (ruff/eslint), type checker (mypy/tsc), test framework
6. No known vulnerability patterns in pinned versions

Error handling: If a build config file is missing, report as: severity=warning, detail="No build config found for {repo}"

Return findings in this exact format:
DIMENSION: D6 — Dependencies
FINDING_COUNT: {N}
FINDINGS:
- severity: {critical|warning|info}
  repo: {repo-name}
  detail: {description}
  location: {file:line if applicable}
  fix: {suggested fix}
```

---

## D7 — Configuration Audit (integrations only)

```
Audit APCORE_* configuration consistency across framework integrations.

Repos: {integration_repo_paths}

For each integration:
1. Read config.py/config.ts — search in src/{package}/ directory
2. Extract all APCORE_* settings with types and defaults
3. Compare settings across integrations — same settings should have same types and defaults

Required settings (must be present in all — canonical list in shared/conventions.md → "Framework Integration Configuration"):
- APCORE_ENABLED, APCORE_DEBUG, APCORE_SCANNERS
- APCORE_INCLUDE_PATHS, APCORE_EXCLUDE_PATHS
- APCORE_MODULE_PREFIX, APCORE_AUTH_ENABLED, APCORE_AUTH_STRATEGY
- APCORE_TRANSPORT, APCORE_HOST, APCORE_PORT

Canonical defaults (mismatch with these is CRITICAL, not warning):
- ENABLED=True, DEBUG=False, SCANNERS=["auto"], INCLUDE_PATHS=[], EXCLUDE_PATHS=[]
- MODULE_PREFIX="", AUTH_ENABLED=False, AUTH_STRATEGY="bearer"
- TRANSPORT="stdio", HOST="0.0.0.0", PORT=8808

New settings policy (additional check):
- Any bare APCORE_* setting NOT in the canonical list above → CRITICAL "unauthorized canonical setting {NAME} — use APCORE_{FRAMEWORK}_* prefix for framework-specific settings, or propose an addition to shared/conventions.md"
- Any APCORE_{FRAMEWORK}_* setting → OK if documented in that integration's docs/features/config.md under a Framework-specific settings heading; else WARNING

Error handling: If config file not found in a repo, report as: severity=warning, detail="Config file not found for {repo}"

Return findings in this exact format:
DIMENSION: D7 — Configuration
FINDING_COUNT: {N}
FINDINGS:
- severity: {critical|warning|info}
  repo: {repo-name}
  detail: {description}
  location: {file:line if applicable}
  fix: {suggested fix}
CONFIG_MATRIX:
- setting: {APCORE_SETTING}
  {repo-1}: {type}={default}
  {repo-2}: {type}={default}
  consistent: true|false

Target ~2-3KB. If more than 20 settings exist, only list inconsistent settings in the matrix and summarize consistent ones as a count.
```

---

## D8 — Project Structure Audit

```
Audit project structure consistency across apcore ecosystem.

Repos: {repo_paths}

Check against conventions:
- Core SDKs: has src/ with expected subdirectories (middleware/, registry/, schema/, observability/, utils/)
- MCP bridges: has src/ with expected subdirectories (server/, auth/, adapters/, converters/)
- Integrations: has src/ with expected structure (scanners/, output/, cli)
- All repos: has tests/, .gitignore, README.md, CHANGELOG.md, LICENSE, build config

Error handling: If a repo directory does not exist or is empty, report as: severity=info, detail="Repo {name} is empty or placeholder"

Return findings in this exact format:
DIMENSION: D8 — Project Structure
FINDING_COUNT: {N}
FINDINGS:
- severity: {critical|warning|info}
  repo: {repo-name}
  detail: {description}
  location: {directory or file}
  fix: {suggested fix}
```

---

## D9 — Bloat & Redundancy Audit

```
Audit code bloat and redundancy across apcore ecosystem repos.

Repos: {repo_paths}

This dimension is the primary defense against additive bias from skill-driven workflows
(spec-forge / code-forge / apcore-skills) that bias toward "add new" over "reuse existing".
Be thorough — bloat does not surface in any other audit dimension.

For each repo, perform ALL of the following checks:

1. DEAD EXPORTS — public symbols (classes, functions, constants, types) declared in the
   main export file (__init__.py / index.ts / lib.rs / mod.rs) that have zero callers
   anywhere in the ecosystem. Cross-check against ALL repos in scope when possible — a
   symbol exported by core-sdk but never imported by any integration or downstream repo
   is a strong dead-export signal.
   - severity: warning (zero internal + zero external callers)
   - severity: critical (entire submodule with no callers)

2. UNUSED INTERNAL SYMBOLS — non-exported functions, classes, helpers, or methods inside
   src/ that are defined but never referenced in the same repo. Use grep across the repo
   for each candidate. Skip test fixtures and __all__-listed symbols.
   - severity: warning per unused symbol
   - severity: critical if a whole file is dead

3. DUPLICATE / NEAR-DUPLICATE FUNCTIONS — within a repo, look for functions with
   structurally identical bodies (≥ 5 statements) that differ only in literals or naming.
   Across repos in the same language, look for utility functions that have been
   independently reimplemented (string utils, path utils, type guards, schema helpers).
   - severity: warning (intra-repo duplicates)
   - severity: critical (cross-repo duplicates of utility code that should live in shared-lib)

4. PARALLEL IMPLEMENTATIONS — two or more modules within a repo that implement the same
   concept slightly differently (e.g., two HTTP client wrappers, two config loaders, two
   logger adapters). This is the most common bloat pattern from feature-by-feature
   planning.
   - severity: critical — propose merging

5. STALE / COMMENTED-OUT CODE — large commented-out blocks (≥ 10 lines), files containing
   only TODOs older than the most recent release tag, modules marked deprecated with no
   removal date.
   - severity: info (small blocks)
   - severity: warning (large blocks or files)

6. UNUSED CONFIG / FLAGS — APCORE_* settings, CLI flags, environment variables, or
   .code-forge.json keys that are declared but never read by any code path. Grep for the
   key name across the repo (and across the ecosystem for cross-repo settings).
   - severity: warning

7. UNUSED DEPENDENCIES — packages declared in pyproject.toml / package.json / Cargo.toml
   that are never imported. Use the project's dependency analyzer if available, otherwise
   grep for import statements.
   - severity: warning
   - severity: critical if the unused dependency is large or has known CVEs

8. WRAPPER / PASSTHROUGH FUNCTIONS — functions whose entire body is a single call to
   another function with the same arguments, or that only rename fields. Often introduced
   "for future flexibility" but never extended.
   - severity: warning

9. SCOPE CREEP DETECTION — for each feature directory under planning/ (if present), read
   plan.md and check whether the actual implementation introduced files, modules, or
   public APIs not mentioned in the plan. Cross-reference state.json `tasks[].commits` if
   available.
   - severity: warning (extra files)
   - severity: critical (extra public API)

10. LOC GROWTH SIGNAL — compute total source LOC of the repo (excluding tests, vendor,
    generated code). If git history is available, compare against the LOC at the previous
    release tag. Surface as INFO finding regardless of magnitude — this is a trend signal,
    not a defect by itself.

11. NET-TO-USEFUL-CODE RATIO — for each src/ directory, compute the ratio of (lines that
    are reachable from a public export) to (total lines). If reachability cannot be
    determined statically, skip this check and note it.

12. STUB / NO-OP IMPLEMENTATIONS — public methods that have the correct signature but do
    nothing meaningful. These pass API surface checks (D1) and sync Phase A but provide
    no actual functionality. Detect by looking for:
    a. Methods whose ENTIRE body (excluding comments) is a single return statement with a
       default/zero value: `return Ok(default_value)`, `return {}`, `return 0`, `return []`,
       `return None`, `Ok(())`, `pass`, or equivalent. A method that performs work THEN
       returns `Ok(())` is NOT a stub — only flag methods where the return is the ONLY statement.
    b. Methods that silently discard named parameters via `let _ = param_name` (Rust),
       `_ = param` (Python), or unused parameter prefixes (`_param`) while the spec
       implies the parameter should affect behavior
    c. Methods with a `// TODO`, `// no-op`, `// stub`, `// reserved for future use`
       comment as the only meaningful content
    d. Async methods that never actually await anything (sync body in async wrapper)
    For each detected stub, check if the spec/docs promise the method does something:
    - If spec describes actual behavior but implementation is a stub → severity: critical
    - If implementation is a stub with a clear "reserved for future" note → severity: warning
    - If the method is a lifecycle hook (on_load, on_unload, shutdown) with empty body → severity: info

Use Grep extensively. Read files at signature level when needed. Do NOT trust naming
alone — verify with actual references.

Error handling:
- If a repo path does not exist, report as: severity=info, detail="Repo not found at {path}"
- If git history is unavailable, skip LOC growth check and note it
- Do NOT fail the entire audit if reachability analysis fails for one repo

Return findings in this exact format:
DIMENSION: D9 — Bloat & Redundancy
FINDING_COUNT: {N}
FINDINGS:
- severity: {critical|warning|info}
  repo: {repo-name}
  category: {dead_export|unused_internal|duplicate|parallel_impl|stale|unused_config|unused_dep|wrapper|scope_creep|loc_growth|reachability|stub_noop}
  detail: {description}
  location: {file:line if applicable}
  fix: {suggested fix — deletion, merge, inline, etc.}
  evidence: |
    {MANDATORY for every D9 finding — Gate 6 always triggered on D9 categories.
     Paste the actual grep/rg command AND its matched-line output (or "0 matches"),
     covering at least src/ + tests/ + examples/ for dead-code claims.
     For duplicate / parallel_impl / reimplements: cite BOTH sides with {repo}/{path}:{line}.
     A narrative summary like "grep returns only the declaration" is insufficient — it will
     be dropped by the orchestrator's Step 2.5.2 verification scan.}
BLOAT_SUMMARY:
- repo: {repo-name}
  total_loc: {N}
  loc_at_last_release: {N or "unknown"}
  delta: {N or "unknown"}
  dead_exports: {N}
  unused_internal: {N}
  duplicates: {N}
  parallel_impls: {N}
  unused_config: {N}
  unused_deps: {N}
  scope_creep_files: {N}
  stub_noops: {N}
```

---

## D10 — Contract Parity (Intent / Logic Consistency)

~~~
Audit behavioral-contract parity across apcore SDK implementations of the same type.

Repos to compare: {repo_paths}
Doc repo (spec authority): {doc_repo_path} — may be empty for integration-only audits

This dimension catches the bug class "public signatures match but logic/intent differs".
It does NOT check helper-name parity (that is explicitly out of scope — see sync Anti-Rationalization Table).
It DOES check that every SDK agrees on: input validation rules, errors raised and their codes,
side-effect order, return shape, and behavioral properties (async, thread-safe, pure, idempotent, reentrant).

Read `shared/contract-spec.md` for the authoritative Contract block format.
Read `shared/api-extraction.md` Step E.4b for the per-method contract extraction protocol.

=== Step 1: Load spec Contracts (if doc repo provided) ===

For each `docs/features/*.md` in {doc_repo_path}:
1. Find every `## Contract: ClassName.method_name` block
2. Parse `### Inputs`, `### Preconditions`, `### Side Effects`, `### Postconditions`, `### Errors`, `### Returns`, `### Properties`
3. Store as `spec_contracts[scope][symbol]` — canonical two-level keying per `shared/contract-spec.md` §Canonical Storage Shape. `scope` is the doc-repo group (derived from `{doc_repo_path}` — e.g., `apcore/` → `core`, `apcore-mcp/` → `mcp`). `symbol` is `ClassName.method_name` in canonical snake_case.

If {doc_repo_path} is empty OR no Contract blocks found, enter cross-repo-only mode (compare repos
against each other without spec authority — any divergence is still a bug).

=== Step 2: Extract per-repo contracts ===

For each repo in {repo_paths}:
1. Identify the main export file (__init__.py / index.ts / lib.rs / mod.rs)
2. For each public class and every public method on it, AND for each top-level public function:
   a. Extract inputs validations — scan the first N non-comment lines (or every line before the
      first mutating call / I/O call, whichever is shorter) for guard clauses like
      `if <cond>: raise E` / `if (<cond>) throw new E(...)` / `if <cond> { return Err(E) }`.
      Record `[{param, condition, reject_with}]`.
   b. Extract errors_raised — grep the entire method body for `raise X`, `throw new X`,
      `return Err(X)`, `return ..., errX`, `?` operator on `Result<_, X>`. Deduplicate.
      Resolve error codes where statically possible (find the error class definition, extract
      its code field / constant).
   c. Extract side_effects (ordered) — detect lock acquire/release, emit/publish calls, index
      mutations, I/O writes, self/this field assignments. Normalize each to a short snake_case
      descriptor. Return in source order.
   d. Extract return_shape — None/void/unit, literal, ConstructedType(...), raises, mixed.
   e. Extract properties — async (from signature), thread_safe (lock usage + mutation),
      pure (no mutations + no I/O + no argument mutation), idempotent (null unless obvious),
      reentrant (null unless obvious).
3. Store per repo as repo_contracts[repo_name][symbol]

=== Step 3: Compare ===

For every (symbol) that appears in spec_contracts OR in more than one repo_contracts:

1. Inputs validation parity:
   - Spec-declared: every repo must have matching {condition, reject_with} for each spec input.
     Missing validation → CRITICAL. Wrong error type → CRITICAL.
   - Spec silent: cross-repo. Divergence is WARNING by default — defensive-style differences (one repo validates early and raises E, another lets the same input reach the underlying call and raise via a different path) max at warning. **Escalate to CRITICAL only when the divergence produces OBSERVABLE contract divergence**: the same input triggers a different error *class* (a caller's `except E` would catch in one repo but not another), a different return shape, or a different side-effect ordering. Pure "stricter vs looser defensive check with the same ultimate outcome" = warning.

2. Errors raised parity:
   - Spec-declared: set of error types must equal spec's ### Errors. Extra → WARNING. Missing → CRITICAL. Wrong code → CRITICAL.
   - Spec silent: set equality across repos. Divergence is WARNING by default. **Escalate to CRITICAL only when a caller written against one repo's error types would silently fail against another** — e.g., one repo raises `DuplicateError`, another raises generic `ValueError`, and no common superclass covers both (user's `except DuplicateError` misses the other repo). Same-superclass divergences (e.g., both subclass `ApcoreError`) with identical error codes = warning.

3. Side-effect order parity:
   - Spec-declared: LCS diff between spec order and each repo. Missing → CRITICAL. Reordered → CRITICAL. Extra → WARNING.
   - Spec silent: cross-repo order. Divergence → CRITICAL.

4. Return shape parity:
   - Mismatch with spec → CRITICAL. Cross-repo divergence when spec silent → CRITICAL.

5. Properties parity:
   - true-vs-false mismatch → CRITICAL.
   - null-vs-true/false → WARNING (extraction limit).
   - All-null → skip.

6. Cross-check with ## Algorithm (if Contract AND Algorithm both exist for the symbol):
   - Side-effect order in Contract should correspond to checkpoint order in Algorithm.
   - Mismatch → WARNING at the spec level (spec is internally inconsistent).

Severity guidance:
- critical: intent divergence — implementation will produce different observable outcomes for the same input
- warning: spec is silent / extraction cannot determine / extra behavior that may be a language-specific enhancement
- info: cosmetic divergence (condition phrasing differs but error type matches)

**Severity calibration (MANDATORY — apply after classifying by the table above, BEFORE emitting the finding):**

Cross-language SDK audits have a systemic bias toward over-escalating language-idiom differences to `critical`. Apply this four-step re-check to every candidate `critical` finding (Steps 1–3 decide severity; Step 4 is the audit trail):

**Step 1 — Observable-wrong-behavior test.** Can you name a concrete trigger input + the resulting observable divergence that a downstream caller / end user would encounter? "Observable" means: different exit code, different error *class hierarchy* (not just different name), different returned data shape *as consumed by a caller*, different side-effect ordering that a downstream test could detect, different audit-log content, different security posture. If you cannot name the concrete trigger AND the observable divergence in one sentence → downgrade to `warning`.

**Step 2 — Security-gate exception.** The following contract surfaces are security-gated by design; any runtime-behavior divergence on them REMAINS `critical` even if the divergence is "only" naming / type-shape / defensive-check depth:
- `Sandbox.*` — subprocess isolation, env whitelisting, resource limits
- `AuditLogger.*` — log writes, hash input canonicalization, user resolution
- `AuthProvider.*` — credential read, API-key precedence, token construction, header mutation
- `*ApprovalHandler.*` / `check_approval` — prompt, timeout vs denial distinction, audit-flush-on-denial

Divergences on these surfaces keep `critical` regardless of Step 1. A non-security contract (e.g. `ExposureFilter.from_config` error class name) does NOT get this exemption.

**Step 3 — Language-idiom drop list (max severity = `warning`, often drop to `info` or skip):**

Candidates matching any of these SHAPES are language-idiom differences, not bugs:
- **Cross-language error-class-name divergence with same semantic role** — e.g. Python `click.BadParameter` vs TS `Error` vs Rust `Err(String)`, all raised for "invalid mode", all causing the caller to receive an error-type value. → `warning`. Escalate to `critical` ONLY when a documented cross-repo caller's `except X` / `catch (e: X)` / `match X` would silently miss one repo's error (provide the caller location as evidence).
- **Async vs sync signature divergence where no language performs real async I/O** — TS marked `async` for parity with a Promise-returning API surface but body does zero await, other languages sync. → `warning`. The fix is "remove async", not "align all three".
- **`process::exit` / `sys.exit` vs `Result` return in library code** — a hygiene issue (can't embed in a longer CLI) but only `critical` when a documented embedding contract explicitly promises "caller controls exit". If the function is purely a CLI-entrypoint with no embedding promise → `warning`.
- **Constructor-name language idioms** — e.g. Rust `try_from_yaml` vs Py/TS `from_yaml`; Rust's `try_` prefix convention for fallible constructors is idiomatic. Missing peer only matters if it creates a behavioral parity gap (fallible-vs-infallible semantics). If both versions are fallible, just with different naming → `warning`. If Rust has an infallible `from_yaml` too (which is the case when `try_from_yaml` is added alongside) → `info`.
- **Defensive depth difference where the excess check in the stricter repo catches inputs that the looser repo would reject one step later with the same error class** → `warning`. Only `critical` when the looser repo returns/succeeds where the stricter one would error, OR when the error classes genuinely differ per the rule above.
- **Struct-field or config-key superset/subset across repos where the missing field is a TODO/stub with no consumer yet** → `warning` (belongs under D9 dead-code anyway). The D10-critical slot is for divergent RUNTIME BEHAVIOR, not for "language X is missing a future field".
- **Return-type wrapping difference where the wrapping is a language-idiomatic type that exposes the same data** — e.g. Python `Optional[str]` vs TS `string | null` vs Rust `Option<String>` all hold the same semantics. → `info` (drop, not a bug). BUT: Rust `Option<String>` vs Py `Any` / TS `unknown` where native YAML types (int/bool/list) are stringified on Rust IS a critical divergence (see D10-002 example — this is NOT the same as the above).

**Step 4 — Record the calibration step in the finding's `detail` for reviewer transparency.** After emitting the finding, append ONE `[severity-calibration: ...]` line. Choose ONE value depending on what happened:

| Situation | Trace value to append |
|---|---|
| Finding passed Step 1 cleanly (no downgrade needed) | `[severity-calibration: observable-divergence verified]` |
| Finding was `critical` and survived via Step 2 security-gate exception | `[severity-calibration: critical preserved — security-gated surface ({Sandbox|AuditLogger|AuthProvider|ApprovalHandler})]` |
| Finding was downgraded per Step 3 language-idiom rule | `[severity-calibration: downgraded from critical — {error-class-name-only|async-no-work|embedding-hygiene|constructor-name-idiom|defensive-depth|stub-field|type-wrapping}]` — pick the SINGLE matching rule name, not the whole list |
| Finding was downgraded per Step 1 (could not name observable divergence) | `[severity-calibration: downgraded from critical — no observable trigger]` |

Example good trace: `detail: "... [severity-calibration: downgraded from critical — async-no-work]"` (short, machine-parseable, reviewer can scan the `detail` field to audit the calibration itself).

The orchestrator's Step 2.5 gate does not re-run this calibration — the sub-agent must apply it at emission time. A `critical` finding lacking the calibration trace in `detail` after the next audit cycle will be flagged for sub-agent prompt reinforcement.

Error handling:
- If a repo path does not exist, skip it and report as INFO finding "Repo not found at {path}"
- If a method's body cannot be statically analyzed (e.g., defined via macro/codegen), report WARNING "Method {M} in repo {R} not statically analyzable — contract extraction skipped"
- If NO repos have extractable contracts (all methods too dynamic), report INFO "Contract parity check yielded no comparisons"
- Do NOT fail the entire audit if one repo's extraction fails

Return findings in this exact format:
DIMENSION: D10 — Contract Parity
FINDING_COUNT: {N}
FINDINGS:
- severity: {critical|warning|info}
  repo: {repo-name-of-outlier}   # for spec-silent findings, the outlier repo
  symbol: {ClassName.method_name}
  category: {inputs_validation|errors_raised|side_effect_order|return_shape|property_mismatch|spec_silent|algorithm_contract_mismatch}
  detail: {what specifically differs}
  spec_says: {spec value, or "(not declared)" if spec is silent}
  repos_disagree:
    {repo-1}: {value}
    {repo-2}: {value}
  location: {file:line in the outlier repo that needs changing}
  fix: {concrete change instruction — e.g., "Add `if not RE.match(id): raise InvalidIdError(code=INVALID_ID)` before existing validation"}

CONTRACT_MATRIX:
- symbol: {ClassName.method_name}
  spec_contract_present: true|false
  repos_compared: [{repo-1}, {repo-2}, ...]
  rows:
    - row: inputs.{param}.validation
      spec: {value or "—"}
      {repo-1}: {value}
      {repo-2}: {value}
      status: PASS|FAIL|WARN
    - row: inputs.{param}.reject_with
      ...
    - row: errors.{ErrorType}
      ...
    - row: side_effect[{N}] {effect_name}
      ...
    - row: return.on_success
      ...
    - row: property.{async|thread_safe|pure|idempotent|reentrant}
      ...

Target output size: keep CONTRACT_MATRIX to at most **15 symbols** (the ones with most severe divergences first — critical before warning). Additionally cap total byte count at **20 kB**: stop emitting CONTRACT_MATRIX rows once the cumulative bytes reach 20 kB and append a tail:

    TRUNCATED_SYMBOLS: [symbol1, symbol2, ...]   # names only, no per-row expansion
    TRUNCATION_REASON: "exceeded 15-symbol limit | exceeded 20 kB byte budget | both"

Summarize fully-passing symbols as a count "N symbols fully match, not listed". A follow-up `/apcore-skills:audit` run filtered to specific symbols can expand the truncated entries if needed.

=== Step 4 (integration-specific): Consumer Contract Check ===

**Runs only when an integration repo is in {repo_paths} AND a core SDK repo is also in {repo_paths} (or reachable via --scope all).** Skip otherwise.

For each integration repo, verify it USES the core SDK according to the core SDK's current Contract:

1. Find every call site into the core SDK:
   - Python integrations: grep for `from apcore import` / `import apcore.`; then find every method call on imported symbols (`Registry(...)`, `Executor(...).execute(...)`, `Context(...)`, etc.)
   - TypeScript integrations: grep for `from "apcore-js"` / `from "apcore"`; find every method call
   - Go integrations: grep for `"github.com/aipartnerup/apcore-go"` imports; find every call
   - Rust integrations: (a) parse `Cargo.toml` `[dependencies]` for any crate named `apcore` or matching `apcore-*` — this is the ground truth for which crates are in use; (b) grep source for `use apcore`, `use apcore_`, `apcore::`, `apcore_[a-z]+::` to find the call sites; (c) also check any project-specific prelude module (typically `src/prelude.rs` or re-exports in `lib.rs`) for pub-use chains that hide direct `apcore::` references. A workspace or prelude re-export still counts as a call site.

2. For each call site, extract:
   - What public method is invoked (canonical method name)
   - What arguments are passed (at least type info)
   - What errors the integration catches / handles (try/except, try/catch, match on Result)

3. Cross-check against the core SDK's spec_contracts[method]:
   a. **Input completeness**: required parameters from spec are all provided → CRITICAL if any required param missing (call won't type-check or will fail at runtime)
   b. **Input validation awareness**: for every declared `### Inputs.{param}.reject_with=E`, check whether the integration validates / sanitizes before the call OR has a catch for E. If neither → WARNING `"{integration} calls {method} but does not handle declared {E} — users will see unhandled exception"`
   c. **Error coverage**: for every error in the core SDK's `### Errors`, check whether the integration has a handler (try/except, catch, match). Missing handler for a documented error → WARNING
   d. **Property assumption**: if integration calls a method marked `thread_safe: false` from concurrent request handlers (common in async frameworks) → CRITICAL `"{integration} calls non-thread-safe {method} from concurrent handlers — add external locking or rework"`
   e. **Deprecated usage**: if integration calls a method that was in core-sdk CHANGELOG's `### Deprecated` or `### Removed` at or before the integration's pinned core-sdk version → WARNING / CRITICAL (removed = critical; deprecated = warning)

4. Emit findings with `category: consumer_contract`, `repo: {integration-repo}`, and `location` pointing to the integration file's call site.

Additional fields in CONTRACT_MATRIX for integration consumer rows (indented block — already inside the outer prompt):

    - symbol: {method}
      consumer_repo: {integration-name}
      core_sdk_contract_ref: apcore/docs/features/{file}.md#Contract.{Class}.{method}
      call_sites: [{file:line}, ...]
      rows:
        - row: input.completeness
          status: PASS|FAIL
          missing: [{param1}, ...]
        - row: error.handling.{ErrorType}
          status: PASS|FAIL|WARN
          handled_at: {file:line or "(none)"}
        - row: property.{thread_safe|idempotent|...}
          integration_assumes: true|false|null
          core_sdk_declares:   true|false
          status: PASS|FAIL
~~~
