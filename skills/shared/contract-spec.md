### Contract Specification Format

Canonical format for declaring **intent / behavioral contracts** in feature specs. Used by `sync` (Step 4B — Contract Parity) and `audit` (D10 — Contract Parity) to verify that language implementations agree on *what* each public method does, independent of *how* it is written.

#### Rationale

The apcore ecosystem deliberately does NOT enforce function-level (implementation) identity across languages — helper decomposition, control-flow shape, and idiom usage should follow each language's grain. But the **logic, purpose, and intent** of every public method MUST be identical. That identity is captured by a Contract.

Contracts complement Algorithms:

| Section | What it captures | Used by |
|---|---|---|
| `## Algorithm: X.method` | *HOW* — ordered checkpoint sequence inside the implementation | sync Step 4A (skeleton tier — optional, requires source instrumentation) |
| `## Contract: X.method` | *WHAT* — inputs, validation, errors, side effects, postconditions, invariants | sync Step 4B (contract tier — **default ON**) + audit D10 |

A feature spec SHOULD declare one `## Contract:` block per public method on every class/function in the feature. Methods without a Contract block are flagged by audit D4.

#### Canonical Contract Block

```markdown
## Contract: Registry.register

### Inputs
- id: string, required
  - validation: matches pattern `^[a-z][a-z0-9_]*$`
  - reject_with: InvalidIdError(code=INVALID_ID)
- module: Module, required
  - validation: satisfies Module interface
  - reject_with: TypeError
- overwrite: bool = false, optional

### Preconditions
- Registry has been initialized (constructor completed without error)
- If overwrite is false, id must not already be registered — reject_with: DuplicateError(code=DUPLICATE)

### Side Effects (ordered — observable to the caller or to later calls)
1. Acquire write lock on the module index
2. Validate all inputs (before any mutation)
3. Resolve transitive dependencies
4. Insert module record into the index
5. Emit `registered` event with payload `{id, version}`
6. Release write lock

### Postconditions
- `get_module(id)` returns the registered module
- `list_modules()` includes id
- If registration failed, no partial state is visible (atomicity)

### Errors
- InvalidIdError(code=INVALID_ID) — id does not match pattern
- TypeError — module does not satisfy Module interface
- DuplicateError(code=DUPLICATE) — id already registered and overwrite=false
- DependencyError(code=DEPENDENCY_MISSING) — a required dependency is absent

### Returns
- On success: None / void / () / unit
- On failure: raises the corresponding error type (each language uses its idiomatic error propagation)

### Properties
- idempotent: false
- thread_safe: true
- async: false
- pure: false
- reentrant: false
```

> **Property rationales** (for the example above — these explain *why* each value was chosen; they are not part of the block syntax):
> - `idempotent: false` — re-registering the same id raises `DuplicateError`, so the second call's outcome differs from the first
> - `thread_safe: true` — the internal write lock serializes concurrent callers
> - `pure: false` — the method mutates the registry index (observable state change)

#### Field Semantics

**`### Inputs`** — each bullet is one parameter.
- Required fields: `name: type, required|optional`, `validation`, `reject_with` (if validation exists), default value for optional.
- `reject_with` links validation failure to a specific error code. Every SDK MUST reject the same inputs with the same error code.

**`### Preconditions`** — state requirements that must hold BEFORE the method is called. Each precondition that can be checked at runtime SHOULD declare `reject_with`. Preconditions without `reject_with` are assumed to be enforced by the caller (document-only).

**`### Side Effects (ordered)`** — observable mutations in the order they occur. "Observable" means: visible through any public API, logged/traced, emitted as event, or written to external storage. Order matters because failure partway through may leave observable partial state — see Postconditions for atomicity guarantees.

**`### Postconditions`** — state guarantees that hold AFTER the method returns successfully. Include atomicity guarantees ("no partial state on failure") here.

**`### Errors`** — enumeration of every error type this method can raise, with error code. The spec is authoritative — implementations MUST raise exactly these error codes, and no others, under the conditions described.

**`### Returns`** — return value shape on success. Use canonical type names; language mapping is handled by `api-extraction.md` E.4.

**`### Properties`** — scalar behavioral flags. Each property must be **true**, **false**, or **null** (not a free-form string like `TODO`). `null` explicitly means "not yet determined" and is only valid in newly-scaffolded specs; parsers treat `null` as "unknown / cannot be compared" per sync Step 4B Properties parity rule. Strings like `"TODO"` or `"?"` are a spec-format violation and audit D4 flags them as `info` (contract_coverage / partial). When scaffolding a Contract skeleton where a property's value is not yet known, render it as:

```yaml
thread_safe: null  # TODO — fill during implementation (true if internal lock, false if races possible)
```

Supported properties:

| Property | Meaning | Typical divergence bug |
|---|---|---|
| `idempotent` | Calling twice with same inputs produces same result as calling once (including error outcome) | SDK-A treats second call as no-op, SDK-B raises error |
| `thread_safe` | Safe to call concurrently from multiple threads without external locking | SDK-A uses lock, SDK-B doesn't, producing races only in one language |
| `async` | Method is asynchronous in this language family (cross-cuts across `async def` / `async fn` / Promise / goroutine) | SDK-A is async, SDK-B is sync, same logical operation |
| `pure` | No side effects — result depends only on inputs | SDK-A caches state (impure), SDK-B doesn't |
| `reentrant` | Safe to call recursively from inside itself (e.g., inside a callback) | SDK-A deadlocks on re-entry, SDK-B recurses fine |

#### Extraction Rules (for sync Step 4B and audit D10)

Each language implementation must expose the contract's behavior. The checker extracts actual behavior from source and compares against the declared Contract:

1. **Inputs validation extraction.** For each public method body, find all early-return / raise / throw statements that occur before the main logic and record `{condition, error_code}`. Compare this list to the Contract's `### Inputs` + `### Preconditions` with `reject_with`.

   Examples of recognized patterns:
   - Python: `if not id: raise InvalidIdError(...)`, `if not isinstance(module, Module): raise TypeError(...)`
   - TypeScript: `if (!id) throw new InvalidIdError(...)`, `if (!(module instanceof Module)) throw new TypeError(...)`
   - Go: `if id == "" { return ErrInvalidId }`
   - Rust: `if !RE.is_match(&id) { return Err(InvalidIdError.into()) }`

2. **Error path extraction.** Find all `raise X` / `throw new X` / `return Err(X)` / `return nil, errX` sites in the method and collect the set of error types raised. Compare to Contract's `### Errors`. Extra errors or missing errors → finding.

3. **Side-effect extraction.** Look for:
   - Writes to instance state (`self.x = ...`, `this.x = ...`, `s.x = ...`, `self.x = ...`)
   - Method calls with effect keywords (`emit`, `publish`, `write`, `acquire`, `release`, `insert`, `delete`, `update`)
   - External I/O (file, network, database)

   Return them in source order. Compare to Contract's `### Side Effects` — set equality AND order equality.

4. **Properties extraction.** Detect from source signals:
   - `thread_safe` true iff method body (or a wrapping decorator/block) acquires a lock before mutating state; false if it mutates shared state without locking.
   - `async` true iff declared with `async def` / `async fn` / returns Promise / returns `impl Future`.
   - `idempotent` — HARD to infer statically. Only compare if Contract declares it explicitly and a divergence is syntactically obvious (e.g., method always raises on repeat call in one SDK, returns success in another — this requires testing, so it is checked only at behavior tier unless the repeat-call branch is literally visible in source).
   - `pure` true iff no `self.x = ` writes AND no external I/O AND no mutation of arguments.
   - `reentrant` — HARD to infer statically. Only checked at behavior tier.

   Hard-to-infer properties (idempotent, reentrant) in contract tier are checked only for **self-consistency across repos** — if SDK-A's source obviously implies `idempotent=true` but SDK-B's source obviously implies `idempotent=false`, flag it. Otherwise defer to behavior tier.

5. **Return shape extraction.** Capture the return type from the signature (already extracted in api-extraction Step E.2) AND the success-path return expression(s) (e.g., `return None` vs `return result_obj`). Compare against `### Returns`.

#### Parity Comparison Output

For each `(method, repo)` pair where both `spec_contracts[scope][method]` and the repo's extracted contract exist:

```
┌──────────────────────────────┬──────┬────────┬──────┬──────┬──────┐
│ Registry.register — Contract │ Spec │ Python │  TS  │  Go  │ Rust │
├──────────────────────────────┼──────┼────────┼──────┼──────┼──────┤
│ inputs.id.validation         │ REQ  │  ✓     │  ✓   │ MISS │  ✓   │
│ inputs.id.reject_with        │INVID │ INVID  │ INVID│ ERR  │INVID │
│ errors.DuplicateError        │ REQ  │  ✓     │  ✓   │  ✓   │  ✓   │
│ errors.DependencyError       │ REQ  │  ✓     │ MISS │  ✓   │  ✓   │
│ side_effect[1] acquire_lock  │ REQ  │  ✓     │ MISS │  ✓   │  ✓   │
│ side_effect[5] emit event    │ REQ  │  ✓     │  ✓   │ MISS │  ✓   │
│ property.thread_safe         │ true │ true   │ false│ true │ true │
│ property.idempotent          │false │ false  │ true │false │ false│
└──────────────────────────────┴──────┴────────┴──────┴──────┴──────┘
```

Each MISS / mismatch row produces a finding at severity `critical` (default — intent divergence is by definition a bug).

#### Required Fields

A Contract block MUST contain at minimum:
- `### Inputs` (or explicit `### Inputs\n_(none)_` if truly no params)
- `### Errors` (or `_(none — infallible)_`)
- `### Returns`
- `### Properties` with at least `thread_safe` and `async`

Optional fields (`### Preconditions`, `### Postconditions`, `### Side Effects`) are recommended but not enforced.

#### Canonical Storage Shape

Skills that parse `## Contract:` blocks MUST store them using the canonical shape:

```
spec_contracts[scope][symbol] = {
  inputs: [...],
  preconditions: [...],
  side_effects: [...],
  postconditions: [...],
  errors: [...],
  returns: {...},
  properties: {async, thread_safe, pure, idempotent, reentrant}
}
```

Where:
- `scope` ∈ {`core`, `mcp`, `a2a`, `toolkit`, …} — the doc-repo group the Contract was parsed from
- `symbol` = canonical `ClassName.method_name` (snake_case method, PascalCase class)

Skills consuming spec contracts (audit D10, sync Step 4B, tester Step 1.3) MUST use this two-level keying. A single-level flat `spec_contracts[symbol]` is a bug — it breaks cross-scope isolation (e.g., `Registry.register` exists with different contracts in `core` and `mcp`).

#### Interaction with Algorithm Sections

`## Algorithm:` and `## Contract:` are complementary, not redundant:

- A method MAY have both — Algorithm describes checkpoint sequence (requires code instrumentation), Contract describes behavior (requires no instrumentation)
- A method SHOULD have Contract (mandatory when audit D4 enforces this)
- A method MAY omit Algorithm (skeleton tier is opt-in)

If both are present, they MUST be consistent — the Algorithm's checkpoint sequence should correspond to the Contract's Side Effects order. sync flags inconsistency as `warning`.
