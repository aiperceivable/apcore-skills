# Audit Dimension Prompts — Sub-agent Templates

Each dimension is an independent sub-agent prompt. Variables common to all: `{repo_paths}`.

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

Error handling: If a repo path does not exist, skip it and report as info finding.

Return findings in this exact format:
DIMENSION: D4 — Documentation
FINDING_COUNT: {N}
FINDINGS:
- severity: {critical|warning|info}
  repo: {repo-name}
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

Required settings (must be present in all):
- APCORE_ENABLED, APCORE_DEBUG, APCORE_SCANNERS
- APCORE_INCLUDE_PATHS, APCORE_EXCLUDE_PATHS
- APCORE_MODULE_PREFIX, APCORE_AUTH_ENABLED
- APCORE_TRANSPORT, APCORE_HOST, APCORE_PORT

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
