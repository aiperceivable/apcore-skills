# Scaffold Project — Sub-agent Prompt Template

Variables to fill: `{target-repo-name}`, `{target-path}`, `{lang}`, `{type}`, `{tech_stack}`, `{package_name}`, `{api_contract}`, `{ref_path}`, `{spec_root}`, `{conformance_path}`, `{conventions_path}`

---

Create the project skeleton for {target-repo-name} at {target-path}.

Language: {lang}
Type: {type}
Tech stack: {tech_stack decisions}
Package name: {package_name}

## Project Structure — Derived from Reference

The API contract (below) contains a SOURCE_TREE, TESTS, and EXAMPLES section discovered from the reference implementation. Use these to drive the scaffold:

1. **src/** — Mirror the SOURCE_TREE structure, translating each file and directory to {lang} idioms:
   - Convert file extensions to {lang} equivalent
   - Apply {lang} naming conventions (see Naming section below)
   - Each source file becomes a stub with correct signatures from MODULES

2. **tests/** — Mirror the TESTS structure from the API contract:
   - Create one test file per source module using {lang} test naming convention
   - Preserve all subdirectories from the reference test tree
   - Each test file is a failing stub (TDD red phase)

3. **examples/** — Mirror the EXAMPLES structure from the API contract (if present):
   - Port each example to {lang} with complete, runnable code
   - Preserve the directory structure
   - If the reference has no examples/, skip this directory

4. **Project boilerplate:**
   - {build-config} (pyproject.toml / package.json / go.mod / Cargo.toml / pom.xml / etc.)
   - .gitignore (language-appropriate patterns)
   - README.md (project name, description, installation, link to the shared docs at {spec_root})
   - CHANGELOG.md (empty "## [Unreleased]" section)
   - License metadata matching the owning checkout
   - Package-local `.unirelease.toml` using the component's existing prefix convention (`<component>/<lang>/v`), or `<package-relative-path>/v` for a Go module

## Stub File Content

**Source stubs** — each file should contain:
1. Module/file header comment referencing the protocol spec section
2. Import of base types from the main module
3. Class/function stubs with correct signatures from the API contract
4. TODO comments indicating what needs to be implemented
5. Type annotations matching the language convention

**Test stubs** — each test file should contain:
1. Import of the module under test and test framework
2. One test class/describe block per public class or function group
3. One failing stub test per public method: asserts `False` / `expect(false)` / `t.Fatal("not implemented")` — TDD red phase
4. Helper file (conftest.py / helpers.ts) with shared fixtures: mock executor, sample context, sample module config
5. Integration test directory with at least one placeholder test for end-to-end flow

**Conformance test stubs** — identify which existing tests load the component's
`{conformance_path}`. Port their case coverage using the target framework and the
same shared JSON files, keeping case IDs visible in test names or failures. Add
failing tests for behavior the skeleton has not implemented yet. See
`shared/conformance-fixtures.md` for execution and reporting.

**Example files** — each example should contain:
1. Complete, runnable code (not stubs) that demonstrates one usage pattern
2. Inline comments explaining each step
3. Port examples from the reference implementation, adapting to target language idioms

## Reference Sync

Read examples and tests from the reference implementation at {ref_path}:

1. **Examples**: Read `{ref_path}/examples/` — port each example file to {lang}, preserving the same usage patterns and directory structure. Adapt naming conventions and idioms to the target language.
2. **Tests**: Read `{ref_path}/tests/` — create corresponding test stubs for every test file. Do NOT copy test logic; instead create failing stubs (TDD red phase) that mirror the reference test structure and coverage scope. Preserve all subdirectory organization.
3. If the reference has no examples/ or tests/ directory, fall back to the API contract to generate them from scratch.

## API Contract Reference
{api_contract}

## Naming

Read the naming conventions file at `{conventions_path}` for the authoritative code naming and test file naming rules. Key points for {lang}:

**Code naming:** Apply {lang}'s idiomatic casing to all canonical API names (see "Code naming" table in conventions).

**Test file naming per language:**
- Python: `test_{module}.py` (pytest discovery)
- TypeScript: `{module}.test.ts` (vitest discovery)
- Go: `{module}_test.go` (go test discovery)
- Rust: `test_{module}.rs` in tests/ for integration tests; also add `#[cfg(test)] mod tests {}` blocks in source files for unit tests
- Java: `{Module}Test.java` with `@Test` methods named `shouldDoX()`
- C#: `{Module}Tests.cs` with `[Fact]` or `[Test]` methods
- Kotlin: `{Module}Test.kt`
- Swift: `{Module}Tests.swift`
- PHP: `{Module}Test.php`

## Error Handling

- If {target-path} is not writable, return: STATUS: WRITE_ERROR, REASON: "{description}"
- If a file cannot be created, skip it and include in the return as "{file} (SKIPPED: {reason})"
- If the language is not recognized, return: STATUS: UNSUPPORTED_LANG, REASON: "No scaffold template for {lang}"

Create ALL files. Return the list of files created.
