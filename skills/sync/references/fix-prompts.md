# Sync Fix — Sub-agent Prompt Templates

## Fix Implementation Repo

Variables to fill: `{repo_path}`, `{language}`, Phase A/B findings

---

Apply sync fixes for {repo_path} ({language}).

Phase A findings to fix:
{naming, missing, type issues from Phase A}

Phase B findings to fix:
{readme, api-ref, examples issues from Phase B}

Fix rules (apply in order):

PHASE A FIXES (code):
1. NAMING FIXES — For each naming inconsistency:
   - Canonical name: {canonical} → language convention: {expected_name}
   - Rename the function/method/class in its source file using Edit
   - Update the export in __init__.py / index.ts
   - Update any internal references within the same repo

2. MISSING API STUBS — For each missing symbol:
   - Generate a stub implementation in {language} with TODO markers
   - Match the signature from the spec (canonical form)
   - Add the export to the main module file
   - Create a corresponding test stub in tests/

3. MISSING TRAIT/INTERFACE SATISFACTION — For each missing contract:
   - Look up the language's idiomatic mechanism in Step 4.2 item 4 equivalence table
     (e.g., `Display` → Python `__str__`, TS `toString()`, Go `String() string`, Rust `impl Display`, Java `toString()`)
   - Generate a stub implementation with a TODO marker explaining the contract
   - For Rust derive-eligible contracts (`Clone`, `Debug`, `PartialEq`, `Hash`, `Default`, `Serialize`), prefer adding the appropriate `#[derive(...)]` attribute
   - Add a corresponding test asserting the contract is satisfied (e.g., `str(obj)` returns non-empty)

4. MISSING CONSTRUCTOR VARIANT — For each spec-declared constructor missing from the implementation:
   - Generate a stub matching the spec signature, using the language's idiomatic factory mechanism
     (Python `@classmethod`, TS `static`, Go `NewX*` function in same package, Rust `impl Self { fn with_… }`, Java `static` factory or overloaded constructor)
   - Add to the main export and create a test stub

5. MISSING CHECKPOINT INSTRUMENTATION — For each method whose implementation has no checkpoint markers but spec declares an `## Algorithm` section:
   - For each spec-declared checkpoint, insert a logger/tracer call at the textually appropriate position in the method body, using the language-specific marker form from Step 4A's table
     (Python `logger.debug("checkpoint:NAME")`, TS `logger.debug("checkpoint:NAME")`, Go `slog.Debug("checkpoint:NAME")`, Rust `tracing::debug!("checkpoint:NAME")`, Java `logger.debug("checkpoint:NAME")`)
   - Position is BEST-EFFORT — insert the marker just before the line that performs the named work, when identifiable
   - If position cannot be inferred from existing code, group all markers at the top of the method body in spec order, with a TODO comment

6. CHECKPOINT REORDERING — **MANUAL REVIEW ONLY, do NOT auto-fix.**
   - If implementation order differs from spec order, the algorithm semantics may differ deliberately. Reordering checkpoints could introduce a bug.
   - Add the finding to MANUAL_REVIEW_ITEMS with the diff and let the operator decide whether the spec or the implementation is correct.

7. VERIFY — After all Phase A fixes:
   - Run the full test suite: {pytest --tb=short -q | npx vitest run}
   - If any test fails due to a fix: revert ONLY that specific fix and note it

PHASE B FIXES (docs, examples, tests):
8. README FIXES — Add missing sections, update API names to match verified API, update version references
9. API REFERENCE FIXES — Update symbol names, param names, import paths in all markdown files
10. EXAMPLE FIXES — Update API usage and dependency versions in example code. For missing example scenarios identified in cross-repo comparison: generate stub example files with TODO markers showing expected scenario.
11. TEST FIXES — Update API usage in tests to match verified API (renamed methods, updated params). For missing test scenarios identified in cross-repo comparison: generate test stub files with TODO markers showing expected test cases and the reference implementation's test for guidance.
12. CONTRADICTION FIXES — Resolve contradictions by aligning all docs to verified API
13. BEHAVIORAL DIVERGENCE — **MANUAL REVIEW ONLY, do NOT auto-fix.**
    - Add tester divergence findings to MANUAL_REVIEW_ITEMS with the failing input/output diff. Behavioral fixes require understanding spec intent, not pattern matching.

14. DEEP-CHAIN FINDINGS (A-D-* namespace) — **MANUAL REVIEW ONLY, do NOT auto-fix.**
    - Deep-chain findings describe cross-language divergences in call-graph behavior (missing validation, missing registration, defensive gaps, error-path divergences). Fixing them correctly requires porting logic semantics between languages, which pattern-matching auto-fix cannot do safely.
    - Add every A-D-* finding to MANUAL_REVIEW_ITEMS with:
      - The finding summary
      - The evidence block (all languages' file:line:snippet)
      - The sub-agent's `recommendation` field verbatim
    - Do NOT modify source for these findings. Report them to the operator for human-written fixes.
    - Exception: if the finding is `inconclusive` severity, include it in MANUAL_REVIEW_ITEMS but prefix with `[inconclusive]` so the operator knows the original sub-agent itself flagged uncertainty.

After all fixes:
1. List all files modified with a summary of changes
2. Do NOT commit — leave changes for user review

Error handling: If test runner is not available, skip verification and note it.

Return:
REPO: {repo-name}
PHASE_A_FIXES: {count} (naming: {n}, stubs: {n}, traits: {n}, constructors: {n}, checkpoints: {n})
PHASE_B_FIXES: {count} (readme: {n}, api-refs: {n}, examples: {n}, tests: {n}, contradictions: {n})
DEEP_CHAIN_DEFERRED: {count} — all A-D-* findings are manual-review-only, reported in MANUAL_REVIEW_ITEMS
TEST_RESULT: {pass|fail|skipped}
TEST_COUNTS: {passed}/{total}
REVERTED_FIXES: {list or "none"}
MANUAL_REVIEW_ITEMS: {list — checkpoint reorderings, behavioral divergences, ambiguous trait stubs, deep-chain findings with evidence and recommendation}
FILES_MODIFIED: {list}

---

## Fix Documentation Repo

Variables to fill: `{doc_repo_path}`, Phase B findings

---

Apply documentation consistency fixes for {doc_repo_path}.

Phase B findings to fix:
{spec chain contradictions, completeness gaps, cross-ref issues from Phase B}

Fix rules:

1. SPEC CHAIN CONTRADICTIONS — For each contradiction between documents:
   - Identify which document is the higher-authority source:
     Authority order: Feature Specs > Tech Design > SRS > PRD
     (Feature specs are closest to implementation, PRD is most abstract)
   - Update the lower-authority document to match the higher-authority one
   - If the contradiction is between documents at the same level: flag for manual review, do NOT auto-fix

2. COMPLETENESS GAPS — For features mentioned in PRD/SRS but missing feature specs:
   - Do NOT generate feature specs automatically (too complex for auto-fix)
   - Add a TODO note in the appropriate location

3. CROSS-REFERENCE FIXES — Fix broken internal references:
   - Update section references to point to correct locations
   - Fix terminology inconsistencies to use the canonical name

4. CODE EXAMPLE FIXES — For each code example mismatch found in SCOPE 4:
   - Fix method names, parameter counts, and import paths to match verified API
   - Add missing `await`, `?`, `Box::new()`, `let mut` as needed for Rust/TypeScript
   - Add missing language tabs where cross-language convention requires them
   - Replace deprecated API references with their canonical replacements from CHANGELOG

5. DEPRECATED API CLEANUP — For each deprecated/removed API reference found in SCOPE 5:
   - Replace with the canonical replacement symbol (look up in CHANGELOG's corresponding Added/Changed section)
   - If no replacement exists, remove the example or mark with an admonition

After all fixes:
1. List all files modified
2. Do NOT commit

Error handling:
- If the doc repo path does not exist, return: DOC_REPO: {repo-name}, STATUS: NOT_FOUND
- If a file is unwritable, skip it and list in MANUAL_REVIEW_ITEMS
- If same-level contradiction (ambiguous authority): flag for manual review, do NOT auto-fix

Return:
DOC_REPO: {repo-name}
FIXES_APPLIED: {count}
FLAGGED_FOR_MANUAL_REVIEW: {count}
FILES_MODIFIED: {list}
MANUAL_REVIEW_ITEMS:
- {description of what needs human decision}
