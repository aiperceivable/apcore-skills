# Audit Fix — Sub-agent Prompt Template

Variables to fill: `{repo_path}`, fixable findings from Step 3

---

Apply audit fixes for {repo_path}.

Fixable findings:
{all fixable findings for this repo from Step 3}

Fix principles — **Mini · Short · Integrated**:
- **Mini:** Touch only the smallest set of files and lines needed to resolve the root cause; no opportunistic refactors or scope creep.
- **Short:** Prefer deleting dead/redundant code and fixing logic directly over stacking compatibility wrappers, flags, or empty `TODO` stubs.
- **Integrated:** When multiple findings in this repo share one root cause (e.g., a renamed symbol affecting code, exports, tests, and README), resolve them together cleanly within existing abstractions and language idioms.

Fix rules (apply in order):
1. BLOAT FIXES (D9) — Apply BEFORE structural fixes so we don't add scaffolding around dead code:
   - dead_export → delete the symbol and any tests for it
   - unused_internal → delete the symbol
   - duplicate (intra-repo) → keep one, replace callers of the other, delete the duplicate
   - wrapper / passthrough → inline at the call site
   - stale (commented-out blocks ≥ 10 lines, ancient TODOs) → delete
   - unused_config → remove the config key from defaults and validation
   - unused_dep → remove from pyproject.toml / package.json / Cargo.toml and lockfile
   - stub_noop (critical, spec promises behavior) → implement the method per spec if small and self-contained; otherwise skip and report for `/code-forge:fix` or `/code-forge:plan` rather than leaving a partial stub
   Skip (leave for human): parallel_impl (needs design decision), scope_creep (needs spec discussion), cross-repo duplicates (needs shared-lib coordination), stub_noop with severity warning/info (may be intentional placeholders)
2. NAMING FIXES (D2) — Rename files/symbols to match conventions and update all internal references and exports in one pass
3. VERSION FIXES (D3) — Update version strings for consistency
4. STRUCTURE FIXES (D8) — Create only minimal required structural markers/config files (e.g., missing package entry or required doc skeleton). Do **NOT** generate empty `TODO` code stubs for missing behavioral modules — report those in `DEFERRED_MANUAL` so they don't immediately fail D9 bloat checks on the next audit
5. DOC FIXES (D4) — Add missing README sections, fix CHANGELOG format, and ensure quick-start examples are self-contained and copy-pasteable for a first-time developer (no assumed internal knowledge)

After all fixes:
- Run the full test suite (detect language: pytest | npx vitest run | go test ./... | cargo test | mvn test | gradle test | dotnet test | swift test | vendor/bin/phpunit | mix test)
- If tests fail: identify which fix caused it, revert ONLY that fix
- Leave all changes uncommitted

Error handling: If test runner is not available, skip verification and note it.

Return:
REPO: {repo-name}
FIXES_APPLIED: {count}
FIXES_REVERTED: {count}
TEST_RESULT: {pass|fail|skipped}
TEST_COUNTS: {passed}/{total}
CHANGES:
- dimension: {D2|D3|D4|D8|D9}
  file: {path}
  action: {what was changed}
LOC_REMOVED_BY_BLOAT_FIXES: {N}
DEFERRED_MANUAL: {list of missing behavioral modules or non-trivial stubs deferred to human / code-forge, or "none"}
