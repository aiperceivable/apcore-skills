# Audit Documentation Repo — Sub-agent Prompt Template

Variables to fill: `{doc_repo_path}`, `{verified_api}`, `{deprecated_api}`

---

Audit internal documentation consistency in {doc_repo_path}.

This is a DOCUMENTATION REPO containing specs and feature definitions. Check that
all documents are internally consistent — no contradictions between layers.

=== FINDING SUPPRESSION GATE (applies to every scope below) ===

Before emitting ANY finding, pass the candidate through:

1. **Concrete contradiction vs speculative drift** — A contradiction exists when two documents make opposing concrete claims about the same symbol (e.g., PRD says `scan()`, tech design says `discover()`). Different phrasings of the same concept, different level of detail, or one document elaborating beyond another are NOT contradictions. Drop findings that only show "documents say different words" without showing opposing claims.
2. **User-facing impact** — Is this contradiction reachable by any downstream reader (spec writer, SDK implementer, test author)? If one document is a stale draft nobody reads, that is a separate hygiene issue — flag as info, not critical.
3. **Severity calibration** —
   - `critical` = contradiction that will cause implementers to build the wrong thing (opposing signatures, opposing types, opposing behavior contracts)
   - `warning` = drift that creates confusion but is resolvable by context (terminology divergence, outdated description, section missing from one layer but implied elsewhere)
   - `info` = cosmetic / structural (formatting, cross-link rot, layer ordering)
   Missing sections in optional documents (PRD, SRS — which may legitimately not exist for small features) default to info, not warning.
4. **Zero findings is valid** — If the spec chain is internally consistent, emit the scope with a 1-2 line evidence note ("compared PRD §3, SRS §2.1, tech-design §4.2 for symbol X — all three agree on signature and behavior"). Do NOT pad with low-severity findings. Use `inconclusive` when a document's claim is ambiguous — never invent a contradiction.

=== SCOPE 1: Spec Chain Consistency ===

**⚠️ INDEX THE CORPUS — DO NOT READ IT WHOLE.** The spec chain on this ecosystem is
**~4.4 MB** (`PROTOCOL_SPEC.md` 713 KB, `docs/features/*.md` 870 KB, plus architecture,
concepts, glossary, guides and spec/). Reading it end to end does not fit, and an agent
that tries will truncate somewhere and report the surviving fraction as if it were the
whole — a clean-looking result on a partial corpus, which is the worst outcome available
here. Follow `shared/subagent-policy.md` P10.

Documents in the spec chain:
- PRD (if exists): docs/prd.md or similar
- SRS (if exists): docs/srs.md or similar
- Tech Design (if exists): docs/tech-design.md or similar
- Test Cases (if exists): docs/test-cases.md or similar
- Feature Specs: docs/features/*.md
- Protocol Spec (if exists): PROTOCOL_SPEC.md

**Work symbol-first, not document-first.** The check is "do the documents agree about
symbol X", so only the regions that mention a symbol matter, and only symbols mentioned
in **two or more** documents can disagree at all:

1. **Build the index with grep** (cheap, no bodies):
   ```
   grep -nE '\b[A-Z][A-Za-z0-9_]*\.[a-z_][A-Za-z0-9_]*\(' <each doc>   # Class.method( references
   grep -n  '^#+ ' <each doc>                                            # heading map, for slicing
   ```
   Build `symbol -> [(document, line), ...]`.
2. **Discard single-document symbols.** A symbol appearing in exactly one document has
   nothing to contradict. On a real corpus this removes the large majority of hits.
3. **For each surviving symbol**, read only the line ranges around its occurrences
   (heading to next heading), compare, then **discard those slices before the next
   symbol**. Never accumulate.
4. Compare: do all documents agree on the symbol's name, parameters, behavior, and types?
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

---

## Coverage self-report (MANDATORY — append to your output)

Without this the orchestrator cannot tell a thorough pass from a truncated one, and a
doc audit that quietly read half the corpus reports "no contradictions" just as
confidently as one that read all of it.

```
DOC_AUDIT_COVERAGE:
  Documents indexed: {N}/{M} spec-chain documents ({pct}%)
  Corpus size: {total KB} indexed, {KB} actually sliced and read
  Symbols indexed: {N} distinct
  Multi-document symbols: {N}  (the only ones that can contradict; all compared: yes/no)
  Symbols compared: {N}/{N}
  Skipped: {list any document you could not open or chose not to index, with the reason}
```

Report the real numbers. If you could not index a document, say so — a named gap is
recoverable, a silent one poisons every finding in this report. Never round coverage up,
and never report 100% you did not achieve.
