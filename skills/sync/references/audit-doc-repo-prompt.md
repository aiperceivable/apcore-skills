# Audit Documentation Repo — Sub-agent Prompt Template

Variables to fill: `{doc_repo_path}`, `{verified_api}`, `{deprecated_api}`

---

Audit internal documentation consistency in {doc_repo_path}.

This is a DOCUMENTATION REPO containing specs and feature definitions. Check that
all documents are internally consistent — no contradictions between layers.

=== SCOPE 1: Spec Chain Consistency ===

Read all available documents from the spec chain:
- PRD (if exists): docs/prd.md or similar
- SRS (if exists): docs/srs.md or similar
- Tech Design (if exists): docs/tech-design.md or similar
- Test Cases (if exists): docs/test-cases.md or similar
- Feature Specs: docs/features/*.md
- Protocol Spec (if exists): PROTOCOL_SPEC.md

For each API symbol (class, function, parameter, return type) mentioned across multiple documents:
1. Collect ALL references: which document, what section, what it says
2. Compare: do all documents agree on the symbol's name, parameters, behavior, and types?
3. Flag contradictions:
   - PRD says feature X has capability A, but feature spec says no such capability
   - SRS requirement REQ-001 references function foo(), but tech design calls it bar()
   - Test plan tests for param "timeout" but feature spec defines it as "max_wait"
   - Feature spec A says Registry has method scan(), feature spec B says it's discover()

=== SCOPE 2: Feature Spec Completeness ===

For each feature spec in docs/features/:
1. Does it define clear API symbols (classes, functions, params, return types)?
2. Are there features mentioned in PRD/SRS that have NO corresponding feature spec?
3. Are there feature specs that are NOT referenced by any higher-level document?

=== SCOPE 3: Cross-Document Reference Integrity ===

Check all internal cross-references:
1. Do documents reference sections/features that actually exist?
2. Are version numbers consistent across documents?
3. Are terminology and naming consistent (same concept uses same name everywhere)?

=== SCOPE 4: Documentation Code Example Correctness ===

Extract ALL fenced code blocks from docs/**/*.md files (getting-started.md, api/*.md,
features/*.md, guides/*.md). For each code block:

1. Identify the language (from the fenced block language tag: python, typescript, rust)
2. Extract API calls — class instantiation, method invocations, function calls, imports
3. Cross-reference each extracted symbol against the VERIFIED API from Phase A:
   a. Does the class/function exist in the verified API?
   b. Does the method exist on the class?
   c. Does the argument COUNT match the verified signature? (e.g., `call(a, b)` but
      verified signature is `call(a, b, c, d)` → FAIL: missing args)
   d. For Rust examples: does the code use `Box::new(...)` where the API expects
      `Box<dyn Trait>`? Does it use `.await` on async methods? Does it use `?` for
      Result returns? Does it use `let mut` when calling `&mut self` methods?
   e. For TypeScript examples: does it use `await` on async/Promise methods?
   f. Does the import path match what the SDK actually exports?

4. Cross-reference code blocks in the SAME section across language tabs:
   - If the Python tab calls `client.call("math.add", {"a": 1})` and the Rust tab
     calls `client.call("math.add", json!({"a": 1}))`, do both pass the same number
     of arguments? (Rust may have extra None/None for optional params)
   - Are all three language tabs present where the project's documentation rules
     require them? (Cross-language example convention)

5. Check for language-specific API adaptations documented in client-api.md §10:
   - If a Rust example calls `.use()` — that is a reserved keyword, should be `.use_middleware()`
   - If a Rust example shows `futures::StreamExt` — verify `futures` is in Cargo.toml
   - If a Rust example uses a proc-macro `#[apcore::module]` — verify it actually exists

Severity:
- Code example references a non-existent method or class → critical
- Argument count mismatch (fewer args than required params) → critical
- Missing `await`/`?`/`Box::new` in Rust/TypeScript → warning
- Missing language tab where cross-language tabs are required → warning
- Import path incorrect → warning

=== SCOPE 5: Deprecated API Detection in Examples ===

Using the deprecated_api list from Step 3 (extracted from CHANGELOG.md):

1. For each deprecated or removed symbol, grep ALL docs/**/*.md files for references
2. If a code example uses a symbol that was listed under `### Removed` in any
   CHANGELOG version up to and including the current version → critical
3. If a code example uses a symbol listed under `### Deprecated` → warning

This catches the pattern where a CHANGELOG removes an event name (e.g., `module_health_changed`)
but a docs/features/*.md example still references it.

Return findings in this exact format:
DOC_REPO: {repo-name}
DOCUMENTS_FOUND: {list of documents checked with paths}

SPEC_CHAIN:
  LAYERS_CHECKED: {list: prd, srs, tech-design, test-cases, feature-specs, protocol-spec}
  CONTRADICTIONS: {N}
  GAPS: {N}

FINDING_COUNT: {N}
FINDINGS:
- severity: {critical|warning|info}
  scope: {spec-chain|completeness|cross-ref|code-example|deprecated-api}
  detail: {description}
  locations:
    - {file1:section} says: "{quote1}"
    - {file2:section} says: "{quote2}"
  contradiction: {what disagrees}
  fix: {which document should be authoritative and what to change}

CODE_EXAMPLES:
  FILES_SCANNED: {N}
  CODE_BLOCKS_CHECKED: {N}
  API_MISMATCHES: {N}
  MISSING_LANG_TABS: {N}
  DEPRECATED_REFS: {N}

Error handling:
- If the documentation repo path does not exist, return: DOC_REPO: {repo-name}, STATUS: NOT_FOUND
- If no spec chain documents are found (no PRD, SRS, tech design, feature specs), return: DOC_REPO: {repo-name}, STATUS: NO_DOCS, DOCUMENTS_FOUND: []
- If individual files cannot be read, skip them and list in DOCUMENTS_FOUND as "{path} (unreadable)"
- If CHANGELOG.md is missing or has no Removed/Deprecated sections, skip SCOPE 5 and report DEPRECATED_REFS: 0
