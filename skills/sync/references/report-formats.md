# sync — report output formats

Rendering templates for `apcore-skills:sync`. Read this file when you reach a
report step; it is **not** needed to execute Phases A and B.

| Template | Rendered by | Emitted when |
|---|---|---|
| §1 Phase A Report | Step 5 | Always (then stop if `--phase a`) |
| §2 Phase B Report | Step 8 | Phase B ran |
| §3 Combined Report | Step 9 | Both phases ran — **after** the Step 9.0 noise-control pass |
| §4 Review-Compatible Issue Report | Step 9.1 | Always appended after §3 |

**Counts in §3 are post-consolidation.** Step 9.0 runs FIRST and its drop counts
feed the `Noise-Control:` header line and the SUMMARY block. Rendering §3 before
9.0 produces stale numbers — see Step 9.0's execution-order note.

**`--save` paths are not here.** Each step owns its own canonical output path
(`shared/ecosystem.md` §0.6a); those lines stay in SKILL.md next to the step.

---

## §1 Phase A Report (Step 5)

Sections whose gating flag is off are omitted entirely, not rendered empty.

```
═══ PHASE A: Spec ↔ Implementation Consistency ═══

Scope: {scope}
Doc repo: {doc_repo} → Impl repos: {impl1}, {impl2}, ...

Checklist: {total_items} items checked
  PASS: {n}
  FAIL: {n}
  WARN: {n}

Spec compliance:
  {impl-repo-1}:  {N}/{total} symbols ({pct}%) ✓
  {impl-repo-2}:  {N}/{total} symbols ({pct}%) ⚠ {missing} missing

Cross-implementation:
  Total symbols: {N}
  Matching: {N}
  Missing: {N}
  Signature mismatch: {N}
  Naming inconsistency: {N}
  Type mismatch: {N}
  Trait/interface satisfaction gaps: {N}
  Multi-constructor coverage gaps: {N}

Internal contract (--internal-check >= contract — DEFAULT):
  Methods with spec Contract: {N}
  Methods in cross-repo-only mode (spec silent): {N}
  Validation rule divergences: {N}
  Error raised divergences: {N}
  Side-effect order divergences: {N}
  Return shape divergences: {N}
  Property divergences: {N}

Internal skeleton (--internal-check >= skeleton):
  Methods with spec skeleton: {N}
  Methods passing checkpoint set+order: {N}
  Methods missing checkpoints: {N}
  Methods with reordered checkpoints: {N}
  Methods with no instrumentation: {N}

Cross-language deep-chain (--deep-chain=on — DEFAULT):
  Modules analyzed: {N}
  Modules complete: {N}  failed: {N}  inconclusive: {N}
  Findings: critical {N} / warning {N} / info {N} / inconclusive {N}
  Top finding types:
    semantic-divergence:    {N}
    missing-validation:     {N}
    missing-registration:   {N}
    defensive-gap:          {N}
    error-path-divergence:  {N}
    contract-gap:           {N}

FAIL items (expanded):
  ❌ Registry.scan_directory()
     Present in: spec, apcore-python
     Missing in: apcore-typescript
     Spec: defined in docs/features/registry.md

  ❌ Executor.execute() — param mismatch
     Spec:       (module_id: str, input: dict, context: Context | None = None) -> ExecutionResult
     Python:     (module_id: str, input: dict, context: Context | None = None) -> ExecutionResult  ✓
     TypeScript: (moduleId: string, input: Record<string, unknown>) -> ExecutionResult  ✗ missing context param

  ❌ [A-D-004] missing-registration — Registry.discover (module: registry)
     Divergence: Rust discover_internal only inserts into descriptors/lowercase_map;
                 Python _discover_custom and TS _discoverCustom both call register() which
                 inserts into the modules map.
     Evidence:
       python:     apcore-python/src/apcore/registry/registry.py:276 — self.register(mod_id, mod)
       typescript: apcore-typescript/src/registry/registry.ts:251 — this.register(moduleId, mod)
       rust:       apcore-rust/src/registry/registry.rs:865 — (no modules.insert call)
     Verification: static-inference

  ⚠️ [A-D-007] defensive-gap — Registry._discoverCustom (module: registry)
     Divergence: TS does not null-guard customModules; Python iterates via list comprehension
                 which tolerates generator-returning discoverers; Rust's type system enforces
                 a Vec.
     Evidence:
       python:     apcore-python/src/apcore/registry/registry.py:262 — for entry in (custom_modules or [])
       typescript: apcore-typescript/src/registry/registry.ts:232 — for (const entry of customModules) // crashes on null
       rust:       apcore-rust/src/registry/registry.rs:864 — discovered: Vec<DiscoveredModule> (typed)
     Verification: static-inference
```

---

## §2 Phase B Report (Step 8)

```
═══ PHASE B: Documentation Internal Consistency ═══

--- Documentation Repos ---

{doc_repo_1} ({scope}):
  Spec chain layers: {list}
  Contradictions: {N}
  Completeness gaps: {N}
  Cross-ref issues: {N}
  Code example mismatches: {N}
  Deprecated API refs: {N}

  CONTRADICTIONS:
    ⚠ PRD §3.2 says "Registry supports glob patterns"
      but feature spec registry.md defines no glob parameter
    ⚠ SRS REQ-012 references "Executor.run()"
      but tech design §4.1 calls it "Executor.execute()"

--- Implementation Repos ---

  Repo                    | README | API Refs | Examples | Tests  | Cross-Doc
  apcore-python           |  PASS  |   PASS   |  PASS    |  PASS  |   PASS
  apcore-typescript       |  WARN  |   FAIL   |  WARN    |  WARN  |   FAIL
  apcore-rust             |  PASS  |   PASS   |  PASS    |  PASS  |   PASS
  apcore-mcp-python       |  PASS  |   PASS   |  PASS    |  PASS  |   PASS
  apcore-mcp-typescript   |  WARN  |   PASS   |  PASS    |  WARN  |   PASS

  MISMATCHES:
    ❌ apcore-typescript README Quick Start uses `findModule()`
       but verified API says `getModule()`
    ❌ apcore-typescript docs/usage.md says `execute(moduleId, input)`
       but verified API says `execute(moduleId, input, context?)`

--- Cross-Repo Examples ---

  Example scenario coverage:
    "basic_usage":     Python ✓  TypeScript ✓  Rust ✓
    "custom_config":   Python ✓  TypeScript ✗  Rust ✓
    "error_handling":  Python ✓  TypeScript ✓  Rust ✗

--- Cross-Repo Tests ---

  Test Coverage Matrix:
    Feature Area      | Python | TypeScript | Rust
    registry          |   12   |     10     |   8   ⚠ missing: scan_glob, bulk_register
    executor          |    8   |      8     |   8   ✓
    config            |    5   |      3     |   5   ⚠ missing: env_override, nested_merge

--- Behavioral Equivalence (--internal-check=behavior) ---

  Tester report: tester-{date}.md
  Protocol-category tests: {N} run
  Cross-language pass: {N}/{N}
  Divergences: {N}
    ❌ Executor.execute({"x": 1}) → Python returns {"y": 2}, TypeScript returns {"y": "2"}
    ❌ Registry.scan(empty) → Python returns [], Rust returns Err(NoModules)

--- Cross-Repo ---

  Cross-repo contradictions: {N}
  Link consistency: {PASS|FAIL}
```

---

## §3 Combined Report (Step 9)

Render only after Step 9.0 has run — the `Noise-Control:` line and SUMMARY carry
post-consolidation counts.

```
apcore-skills sync — Unified Consistency Report

Scope: {scope} | Languages: {langs} | Date: {date}
Mode: {"strict (all findings)" if STRICT_MODE else "lean (style/idiom/verify-spec suppressed — pass --strict for all)"}
Phases: A (spec ↔ code) + B (documentation)
Noise-Control: {n_warning_consolidated + n_info_nitpick + n_strict_suppressed} suppressed · {n_warning_consolidated} warnings-consolidated · {n_info_nitpick} info-nitpick · {n_strict_suppressed} strict-only ({"hidden — pass --strict to see" if !STRICT_MODE else "shown"})
{if n_warning_consolidated > 0:} Consolidated root-cause groups: {(file, category) pairs, comma-separated}

Finding ID namespaces:
  A-EXT-{seq} Phase A extraction-coverage warnings (Step 2 gate — the audit's own
              reliability, not a defect in the audited repo). A repo carrying one
              of these has an incomplete extracted surface; its other Phase A
              counts are lower bounds, not totals.
  A-{seq}     Phase A signature / type / naming findings (Step 4.1–4.3)
  A-S-{seq}   Phase A skeleton findings (Step 4A — only when --internal-check >= skeleton)
  A-C-{seq}   Phase A contract findings (Step 4B — default when --internal-check >= contract)
  A-D-{seq}   Phase A deep-chain findings (Step 4C — default when --deep-chain=on)
  B-{seq}     Phase B documentation findings (Steps 6–8)
  All IDs are stable within a single run; regenerated per invocation.

═══ PHASE A: Spec ↔ Implementation ═══

Checklist: {N} items | PASS: {n} | FAIL: {n} | WARN: {n}

{checklist table — only FAIL/WARN items expanded}

Spec compliance:
  {impl-repo-1}: {N}/{total} ({pct}%)
  {impl-repo-2}: {N}/{total} ({pct}%)

Cross-implementation:
  Total: {N} | Match: {N} | Missing: {N} | Mismatch: {N} | Naming: {N} | Type: {N}
  Trait/interface gaps: {N} | Multi-constructor gaps: {N}

Internal contract (--internal-check >= contract — DEFAULT):
  Methods checked: {N} | Pass: {N} | Validation divergences: {N} | Error divergences: {N}
  Side-effect divergences: {N} | Return-shape divergences: {N} | Property divergences: {N}
  (omitted entirely if --internal-check=none)

Internal skeleton (--internal-check >= skeleton):
  Methods checked: {N} | Pass: {N} | Missing checkpoint: {N} | Reordered: {N} | No instrumentation: {N}
  (omitted entirely if --internal-check=none or --internal-check=contract, or if no spec skeletons defined)

Cross-language deep-chain (--deep-chain=on — DEFAULT):
  Modules: {N} analyzed | {N} complete | {N} failed | {N} inconclusive
  Findings: critical {N} | warning {N} | info {N} | inconclusive {N}
  By type: semantic-divergence {N} | missing-validation {N} | missing-registration {N} |
           defensive-gap {N} | error-path-divergence {N} | contract-gap {N}
  (omitted entirely if --deep-chain=off or --internal-check=none or <2 implementations)

═══ PHASE B: Documentation Consistency ═══

Doc repo internal:
  {doc-repo}: {N} contradictions, {N} gaps

Implementation repo docs:
  Repo                  | README | API Refs | Examples | Tests  | Cross-Doc
  (matrix)

Cross-repo examples: {N} missing scenarios
Cross-repo tests: {N} missing scenarios, {N} missing feature areas
Cross-repo contradictions: {N}

Behavioral equivalence (--internal-check=behavior):
  Tester report: tester-{date}.md
  Protocol tests: {N} run | Pass: {N} | Divergences: {N} | Flaky: {N}
  (omitted entirely if --internal-check != behavior)

═══ COMBINED FINDINGS (sorted by severity) ═══

CRITICAL:
  [A-001] Missing API: Registry.scan_directory()
    Repo: apcore-typescript
    Spec: defined in apcore/docs/features/registry.md
    Phase A — present in spec + Python, missing in TypeScript

  [B-001] Spec chain contradiction
    Doc repo: apcore
    PRD says "glob patterns" but feature spec has no glob param
    Phase B — internal documentation inconsistency

  [B-002] API reference mismatch
    Repo: apcore-typescript
    README uses findModule(), verified API says getModule()
    Phase B — implementation doc does not match verified code

WARNING:
  [A-002] ...
  [B-003] ...

INFO:
  ...

═══ SUMMARY ═══
  Phase A: {N} findings (critical: {n}, warning: {n}, info: {n}, inconclusive: {n})
    ├─ signature/type/naming (A-): {n}
    ├─ contract (A-C-): {n}
    ├─ skeleton (A-S-): {n}
    └─ deep-chain (A-D-): {n}
  Phase B: {N} findings (critical: {n}, warning: {n}, info: {n})
  Total: {N} findings
  Contradictions (doc internal): {N}
  Contradictions (cross-repo): {N}
```

---

## §4 Review-Compatible Issue Report (Step 9.1)

Converts every CRITICAL and WARNING finding from both phases into
`code-forge:review` format. Schema follows `code-forge/skills/review/SKILL.md` —
if that format changes, update this mapping.

> ⚠️ **Emit as raw markdown, NOT inside a fenced code block.** `code-forge:fix
> --review` parses it out of the conversation context; wrapping it in a fence
> makes it unparseable. The fences below delimit the *template*, not the output.

Use the `# Project Review:` header with a **dynamic scope description** derived
from Step 1 (repo name, scope group, or `all`).

```markdown
# Project Review: {scope_description}

## Consistency

{For each finding from Phase A and Phase B with severity critical or warning, emit one issue entry:}

- severity: <blocker | critical | warning>
  file: {target file path — the file that needs to be fixed}
  line: {line number or range, use 1 if unknown}
  title: [{finding_id}] {short title}
  description: {what is inconsistent and why it matters — include cross-reference to spec or other repo}
  suggestion: {concrete fix instruction — what to change, what to match against}
```

### Severity mapping — sync finding → review severity

| Sync Severity | Review Severity | Condition |
|---------------|-----------------|-----------|
| critical | blocker | Missing API (symbol defined in spec but absent from implementation); missing trait/interface satisfaction; missing constructor variant; **deep-chain `missing-registration`** (Step 4C — one language's public method fails to update a map peers update, breaking later `get`/`list` calls) |
| critical | critical | Signature mismatch, type mismatch, spec chain contradiction; **contract validation/error/side-effect/return/property divergence** (Step 4B); **skeleton checkpoint missing or reordered** (Step 4A); **behavioral divergence** from tester (Step 7.5); **deep-chain `semantic-divergence` / `missing-validation` / `defensive-gap` / `error-path-divergence` / `contract-gap`** (Step 4C) |
| warning | warning | Naming inconsistency, doc mismatch, missing README section; **spec silent on Contract (cross-repo-only mode)**; **contract property null vs true/false** (extraction limit); **skeleton has extra checkpoint not in spec**; **flaky behavior test** from tester; **deep-chain order-only divergence** (Step 4C — same mutations, different order) |
| inconclusive | warning | **deep-chain `inconclusive` findings** (Step 4C) surface as review warnings with title prefix `[inconclusive]` and suggestion `"manual review required — static analysis could not determine whether divergence is intentional"`. Never silently dropped. |
| info | _(skip)_ | Not included — info-level findings are not actionable bugs |

### Deep-chain finding rendering

A deep-chain finding cites multiple languages' evidence in one logical
divergence. Emit **one review issue per non-reference language** — the
"reference language" is the one whose behavior matches the spec Contract, or the
majority if the spec is silent. Each issue's `file` points at the offending
language's source; include peer evidence in `description` so the fix agent sees
the full picture:

```markdown
- severity: critical
  file: apcore-rust/src/registry/registry.rs
  line: 865
  title: [A-D-004] missing-registration — Registry.discover_internal skips modules map insert
  description: |
    Python (apcore-python/src/apcore/registry/registry.py:276) and TypeScript (apcore-typescript/src/registry/registry.ts:251) both call
    `register(module_id, module)` which inserts into the `modules` map. Rust `discover_internal`
    only inserts into `descriptors` and `lowercase_map`, never into `modules`. Subsequent `get(name)`
    will return None for discovered modules.
    Verification: static-inference.
  suggestion: |
    Inside the for-loop at registry.rs:867, after building the descriptor, call the internal
    registration path that updates core.modules (mirroring how Python's _discover_custom ends in
    self.register(mod_id, mod)). Do not add a new method — use the existing internal register path.
```

### Rules

- Group issues by file for efficient batch fixing
- The `file` field MUST point to the **implementation or doc file that needs changing** (not the spec file)
- The `suggestion` field MUST be concrete enough for code-forge:fix to act on directly (e.g., "Rename `findModule` to `getModule` to match spec" rather than "fix naming")
- For missing API stubs, include the expected signature from the spec in the `suggestion`
- For doc mismatches, include the correct value from `verified_api` in the `suggestion`

### Example output

```markdown
# Project Review: {scope_description}

## Consistency

- severity: blocker
  file: apcore-typescript/src/registry.ts
  line: 1
  title: [A-001] Missing API — Registry.scanDirectory()
  description: Registry.scan_directory() is defined in apcore/docs/features/registry.md and implemented in apcore-python, but missing from apcore-typescript.
  suggestion: Add `scanDirectory(path: string, options?: ScanOptions): Promise<Module[]>` method to Registry class, matching the spec signature.

- severity: critical
  file: apcore-typescript/src/executor.ts
  line: 42
  title: [A-003] Param mismatch — Executor.execute() missing context param
  description: Spec defines execute(moduleId, input, context?) but TypeScript implementation only has execute(moduleId, input). Missing optional context parameter.
  suggestion: Add optional `context?: Context` as third parameter to `execute()` method.

- severity: critical
  file: apcore/docs/prd.md
  line: 87
  title: [B-001] Spec chain contradiction — glob patterns
  description: PRD §3.2 says "Registry supports glob patterns" but feature spec registry.md defines no glob parameter. Documents disagree.
  suggestion: Remove glob pattern reference from PRD §3.2 to match feature spec, or add glob parameter to feature spec if the capability is intended.

- severity: warning
  file: apcore-typescript/README.md
  line: 35
  title: [B-002] API reference mismatch — findModule vs getModule
  description: README Quick Start uses `findModule()` but verified API says `getModule()`.
  suggestion: Replace `findModule(` with `getModule(` in README Quick Start code example.
```

### Empty case

If no CRITICAL or WARNING findings exist, still emit the header with a note:

```markdown
# Project Review: {scope_description}

## Consistency

_(No actionable issues found — all checks passed.)_
```

---

## §5 Deep-chain finding render (Step 4C.5)

How each Step 4C deep-chain finding renders inside §1 (Phase A Report) and §3
(Combined Report):

```
[{A-D-{seq}}] {severity} — {type}
  Module: {module_name}
  Symbol: {symbol}
  Divergence: {divergence}
  Evidence:
    python:     {file}:{line} — {one-line snippet excerpt}
    typescript: {file}:{line} — {one-line snippet excerpt}
    rust:       {file}:{line} — {one-line snippet excerpt}
  Recommendation: {recommendation}
  Verification: static-inference
```

The `Verification: static-inference` line is **MANDATORY** on every deep-chain
finding. It signals to downstream consumers (tester, fix) that this is a static
conclusion — tester MAY re-verify at runtime when `--internal-check=behavior` is
also active.
