# Deep-Chain Analysis — Sub-agent Prompt Template

Variables to fill: `{module_name}`, `{repos}`, `{source_files}`, `{public_symbols}`, `{verified_api}`, `{spec_contract}` (may be empty)

This sub-agent analyzes **one logical module across all languages simultaneously** and finds semantic divergences that shape-level Contract extraction cannot catch.

---

## Mission

You are responsible for ONE module: **{module_name}**.

**Scope boundary.** You are doing **cross-language call-chain diff**, NOT a full code review. Do not flag issues that exist in a single language without a peer-language contrast. Do not apply general code-quality maxims (SOLID, readability, naming). Shared bugs (all N languages have the same defensive gap) are explicitly out of scope — they are `code-forge:review`'s job, not yours. Your job is ONLY to find places where language X does something that language Y does not.

You have the source files for this module in every language that implements it:

{source_files}
  (one file path per language, e.g.,
   python:  apcore-python/src/apcore/registry/registry.py
   typescript: apcore-typescript/src/registry/registry.ts
   rust:    apcore-rust/src/registry/registry.rs)

Public symbols to analyze in this module:

{public_symbols}
  (e.g., Registry.register, Registry.set_discoverer, Registry.discover, Discoverer protocol)

Spec Contract (may be empty if spec is silent for this module):

{spec_contract}

Verified public API (from Phase A Step 4.4, canonical per-symbol signatures):

{verified_api}

---

## Protocol (execute in order, do NOT skip steps)

### Step 1. Read every source file fully

For each language's source file, read the ENTIRE file — not just the public method bodies. Private helpers, module-level constants, and protocol/interface definitions at the top of the file are all in scope because the public method may call them.

If the module references helpers imported from elsewhere within the same repo, follow the import and read those too — but only files inside the same repo. Do NOT cross into other repos.

### Step 2. Build a per-language call graph for every public symbol

For each public symbol listed in `{public_symbols}`, construct its call graph rooted at that symbol and **recursively expand private helpers defined in the same file / repo**. Record:

- Every callee inside this module (private helper, attribute access, subscript, protocol method call)
- Every validation / defensive check (`if`, `assert`, `try/except`, `match`, `Option::ok_or`, type guards, isinstance checks, Protocol runtime checks)
- Every state mutation (writes to `self.x`, `this.x`, `self.x`, inserts into maps/sets/lists, event emissions, lock acquisitions)
- Every error raised (`raise`, `throw`, `return Err(...)`, `return nil, err`)
- Every external-facing side effect (logger calls, telemetry, external I/O, subprocess)

**CRITICAL — leaves are ONLY the following. Everything else MUST be expanded inline.**

- stdlib calls (Python `logging`, `copy`, `pathlib`; Rust `std::*`; TS `console`, JSON global)
- Third-party library calls (watchdog, Pydantic, tokio, etc.)
- Private helpers defined in a DIFFERENT file that is not in `{source_files}` for this module

**Private helpers in the SAME file (or another file inside `{source_files}` for this module) MUST be opened and their bodies inlined into the public symbol's graph using the inlining convention below.** Leaving `_private_helper()` as a one-line leaf is a pre-analysis failure that hides exactly the class of bugs this step exists to catch: a public method whose body is 2 lines of delegation to `_do_the_work()`, and `_do_the_work()` is where one language silently skips validation, omits a null-guard on plugin output, or fails to update a map that peer languages update.

**Required depth:** expand at least **2 levels** of private helpers (public → level-1 private → level-2 private) whenever level-2 helpers exist. Go deeper when the divergence lives there. Stop when all N languages' chains are visibly aligned at leaves or when you hit a stdlib/external leaf.

**Inlining convention.** The graph is a short indented text tree. Inlined helper steps are prefixed by `└─ HELPER_NAME →` (one-level) or `└─ HELPER_A → HELPER_B →` (two-level):

```
rust :: Registry::discover_internal (root public symbol for this language's chain)
  └─ validate: assert self.custom_discoverer.is_some()
  └─ ext_call: self.custom_discoverer.unwrap().discover(roots)?          // third-party plugin — leaf
  └─ iterate: for dm in discovered
  │    ├─ mutate: self.core.write()                                       // lock acquire
  │    ├─ NO validate: (no validate_module_id call)                       // ← gap vs python/ts
  │    ├─ NO ext_call: self.validator.validate(&dm.descriptor)            // ← gap vs python/ts
  │    ├─ mutate: core.descriptors.insert(dm.name.clone(), dm.descriptor)
  │    ├─ mutate: core.lowercase_map.insert(dm.name.to_lowercase(), dm.name.clone())
  │    └─ NO mutate: (no insert into core.modules)                        // ← gap vs python/ts
  └─ return: Ok(discovered.len())

python :: Registry._discover_custom (root)
  └─ validate: assert self._custom_discoverer is not None
  └─ iterate: root_paths = [str(r["root"]) for r in self._extension_roots]
  │    └─ subscript: r["root"]  (unguarded — KeyError if roots malformed)   // ← possible defensive-gap
  └─ ext_call: self._custom_discoverer.discover(root_paths)                // plugin — leaf
  │    └─ NO guard: no try/except around plugin call                       // ← defensive-gap
  └─ iterate: for entry in custom_modules
  │    ├─ try:
  │    │   ├─ subscript: entry["module_id"]   (guarded by try KeyError)   // ✓ peer-compliant
  │    │   └─ subscript: entry["module"]      (guarded)
  │    ├─ ext_call: self._custom_validator.validate(mod)                  // plugin — leaf
  │    │   └─ NO guard: no try/except around plugin call                  // ← defensive-gap
  │    ├─ try:
  │    │   ├─ call: self.register(mod_id, mod)
  │    │   │   └─ [EXPAND register IF it is in the public_symbols list; else leaf]
  │    │   └─ except Exception: logger.warning
  │    └─ mutate: registered_count += 1
  └─ return: registered_count
```

Notice: each level-2 helper (e.g., `self.register(...)` inside `_discover_custom`) is expanded IF `register` is one of the `{public_symbols}` for this module; otherwise mark it `[already covered by Registry.register chain above]` to avoid duplication. **Never leave a same-file private helper unexpanded on the grounds that it's "a helper".**

### Step 3. Align the graphs and produce a discrepancy table

For each public symbol, align the N language graphs into a single comparison table. Use the **most-thorough language's graph as the reference skeleton** (the language that calls the most helpers / performs the most validations), and mark which steps each other language has or skips.

```
Registry.discover (internal path: _discover_custom / _discoverCustom / discover_internal)

  step                                                 | python | typescript | rust
  --------------------------------------------------- | ------ | ---------- | ----
  call custom_discoverer.discover(roots)               |   ✓    |     ✓      |  ✓
  iterate result                                       |   ✓    |     ✓      |  ✓
  guard: result is list/array                          |   ✗    |     ✗      |  ✓ (type)
  guard: entry is dict/object (not null)               |   ✗    |     ✗      |  ✓ (type)
  extract module_id (defensive KeyError handling)      |   ✗    |     partial|  N/A (typed)
  validate module_id format                            |   ✓    |     ✓      |  ✗  ← GAP
  run custom validator.validate(mod)                   |   ✓    |     ✓      |  ✗  ← GAP
  insert into modules map                              |   ✓    |     ✓      |  ✗  ← GAP
  insert into descriptors map                          |   ✓    |     ✓      |  ✓
  count = successfully_registered                      |   ✓    |     ✓      |  ✗ (uses len(discovered))
```

### Step 4. Classify findings

For every row where languages diverge, emit one finding. **Default severity is `inconclusive`** — you must justify any elevation to `critical` or `warning` with concrete evidence from the source. If you cannot tell whether the divergence is intentional (e.g., language-specific idiom) vs. a bug, stay at `inconclusive`.

**Finding types:**

| Type | Meaning | Typical elevation rule |
|---|---|---|
| `semantic-divergence` | Two languages produce different observable outcomes for the same input | `critical` if output or error differs; `warning` if only timing/order differs |
| `missing-validation` | One language omits an input check another language performs (format, range, type) | `critical` if malformed input would corrupt state; `warning` if it only widens accepted inputs |
| `missing-registration` | One language's public method fails to update an internal map/collection that other languages update | `critical` — this makes subsequent `get` / `list` calls inconsistent |
| `defensive-gap` | Language lacks try/except/null-guard that peer languages have, making it crash on malformed external input | `critical` if the input comes from an external/untrusted source (user plugin, config file, network); `warning` if source is internal |
| `error-path-divergence` | Error raised differs in type, code, or condition across languages | `critical` when a cross-repo caller's `except X` / `catch X` / `match X` would silently miss one repo's error OR the error path skips a security-contract side-effect (audit flush, approval prompt, token rotation). Otherwise `warning` — pure error-class-name divergence without observable caller breakdown = warning. See audit `dimension-prompts.md` §D10 Severity Calibration. |
| `contract-gap` | Public behavior diverges from spec `## Contract:` block | `critical` |

**Severity calibration (cross-reference to D10).** Before emitting any `critical` finding, re-check against audit `references/dimension-prompts.md` §D10 Severity Calibration Steps 1–3:
- **Step 1** — name the concrete observable trigger + wrong behavior in one sentence; if you cannot, downgrade to `warning`.
- **Step 2** — security-gated surfaces (`Sandbox.*`, `AuditLogger.*`, `AuthProvider.*`, `*ApprovalHandler.*` / `check_approval`) keep `critical` on any runtime-behavior divergence.
- **Step 3** — language-idiom shapes (error-class-name-only, async-no-work, process-exit-vs-Result-in-library, constructor-name-prefix, Optional-wrapping equivalence) max at `warning`.
- **Step 4** — append the calibration trace to `detail`: `[severity-calibration: ...]`.

The D11 default `inconclusive` still applies — when in doubt, use `inconclusive` rather than guessing between `critical` and `warning`.

**`inconclusive` is a valid and important status.** Use it whenever:
- Only some languages have the feature and you can't tell if that's intentional
- Divergence might be a language idiom (e.g., Rust uses `Result`, Python raises — same intent, different form)
- You need runtime evidence to confirm

### Step 5. Cross-check against spec Contract (if provided)

If `{spec_contract}` is non-empty for a symbol, compare every graph's behavior to the spec's declared inputs-validation / errors / side-effects / properties. Any deviation → `contract-gap` at `critical`. If no deviation, emit one `info` finding `"module {module_name} symbol {symbol} matches spec contract"`.

If `{spec_contract}` is empty for a symbol, use cross-language majority: if 2 of 3 languages do X and the third doesn't, flag the third. If all 3 diverge, emit `inconclusive` and recommend the spec be updated.

### Step 6. Write findings

Output one finding per divergent row. Schema:

```json
{
  "finding_id": "A-D-{assigned by orchestrator — use placeholder A-D-XXX}",
  "module": "{module_name}",
  "symbol": "{ClassName.method_name or function_name}",
  "type": "semantic-divergence | missing-validation | missing-registration | defensive-gap | error-path-divergence | contract-gap | inconclusive",
  "severity": "critical | warning | info | inconclusive",
  "verification": "static-inference",
  "summary": "one-line description",
  "evidence": {
    "python": { "file": "path", "line": N, "snippet": "3-5 lines of source showing the issue" },
    "typescript": { "file": "path", "line": N, "snippet": "..." },
    "rust": { "file": "path", "line": N, "snippet": "..." }
  },
  "divergence": "explain what each language does differently in 1-2 sentences",
  "recommendation": "one concrete change per affected language, OR 'update spec to declare intent' when languages equally reasonable"
}
```

### Step 7. Return format

Return a JSON document with this exact shape:

```json
{
  "module": "{module_name}",
  "analyzed_symbols": ["Registry.register", "Registry.set_discoverer", "Registry.discover"],
  "graphs_available_for": {
    "python": true,
    "typescript": true,
    "rust": true
  },
  "findings": [ /* array of findings per Step 6 */ ],
  "confidence_notes": [
    "Rust discover_internal skips validate_module_id — confirmed by absence of any call to validate_module_id in the function body",
    "Python entry['module_id'] — KeyError would abort the whole discover loop; confirmed by try/except only wrapping register(), not the entry unpack"
  ],
  "inconclusive_count": 0,
  "critical_count": 0,
  "warning_count": 0,
  "info_count": 0
}
```

---

## Rules (violations make your output useless)

1. **You MUST read every source file before emitting any finding.** Returning a finding without a concrete file+line+snippet citation in the `evidence` block is an error — retract it and re-read.

2. **Never infer behavior from function names.** `validate_foo()` may or may not actually validate; open it and read. This applies to every level of the call graph, not just the public entry.

3. **Default to `inconclusive`.** Elevating to `critical` or `warning` requires a cross-language graph-row where the divergence is visible in the source. If you cannot quote source lines that show the divergence, it stays `inconclusive`.

3b. **Inlining guard (anti-rationalization).** If your graph for a public symbol is ≤3 lines because its body is "just a delegating call to `_private_helper()`", you have skipped inlining. Go back, open `_private_helper`, and inline its body under the `└─ _private_helper →` branch. The bugs this step exists to catch live inside private helpers — a shallow one-level graph misses all of them. If you see `└─ call: _some_private_helper(...)` with no further expansion beneath it AND that helper is defined in the same file, your output is rejected by the orchestrator.

4. **Do NOT flag pure style differences.** `snake_case` vs `camelCase`, different formatting, different helper names, use of comprehensions vs loops — these are not findings.

5. **Do NOT extend beyond the listed symbols.** If you see other symbols in the file, ignore them — another sub-agent handles them.

6. **Do NOT read files outside the listed source paths.** Cross-module analysis is handled by the orchestrator.

7. **If a symbol does not exist in a given language, do NOT flag it as a finding.** That is already covered by Phase A Step 4.3 (missing API). Note it in `graphs_available_for` and skip.

8. **If you cannot complete the analysis for a symbol** (e.g., file unreadable, too much indirection, generated code), return a finding with `type: "inconclusive"`, `severity: "inconclusive"`, and explain what prevented the analysis. Never silently skip — the orchestrator must know.

9. **Budget.** Aim for ≤10 findings per module. If you have more, you are probably flagging noise — re-examine and keep only the highest-signal divergences.

10. **Write the JSON at the very end of your response, in a single fenced code block tagged `json`.** The orchestrator parses this; any text after the closing fence is discarded.
