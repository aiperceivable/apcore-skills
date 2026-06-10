### API Extraction Protocol

Standard method for extracting and comparing public APIs across language implementations.

#### What Constitutes the Public API

The public API is defined by the **protocol specification** (`apcore/PROTOCOL_SPEC.md`) and **feature specs** (`apcore/docs/features/*.md`). Each SDK must implement these contracts.

Public API surface includes:
1. **Exported classes/structs** — listed in `__init__.py` (Python), `index.ts` (TypeScript), `lib.rs` (Rust), etc.
2. **Exported functions** — top-level functions in public modules
3. **Exported types/interfaces/traits** — type definitions, enums, error codes, trait definitions
4. **Constructor/new signatures** — parameter names, types, defaults
5. **Method signatures** — parameter names, types, return types, async flags
6. **Trait/interface implementations** — which structs/classes implement which traits/interfaces
7. **Error types** — names, codes, hierarchy, variants
8. **Configuration options** — setting names, types, defaults
9. **Module definition API** — decorators, binding formats, macros

#### Extraction Steps

For each SDK repository:

**Step E.1: Read public exports (language-specific deep scan)**

Each language requires a different extraction strategy. Surface-level scanning is NOT sufficient — follow module trees, re-exports, and implementation blocks.

##### Python
1. Read `src/<package>/__init__.py`, extract `__all__` or all non-underscore imports
2. Follow `from .submodule import X` chains to find the actual definitions
3. Scan all `.py` files for classes inheriting from ABC or Protocol (interface contracts)
4. Identify `@property`, `@staticmethod`, `@classmethod` decorators on methods
5. Extract type hints from function signatures and class attributes

##### TypeScript
1. Read `src/index.ts`, extract all `export` statements
2. Follow `export * from './module'` and `export { X } from './module'` re-export chains
3. Scan `.d.ts` declaration files if they exist (may define additional types)
4. Extract interface definitions and type aliases
5. Identify `abstract class` definitions (interface contracts)

##### Go
1. Read all `*.go` files in the root package, extract capitalized identifiers
2. Scan `internal/` packages — these are not public API but may define interfaces used publicly
3. Extract interface definitions — identify which structs satisfy them (implicit implementation)
4. Follow `type X = Y` aliases to their source
5. Identify exported struct fields (capitalized) vs. private fields

##### Rust — Deep Extraction Protocol

Rust requires the most thorough extraction due to its module system, trait system, and visibility rules.

**E.1.1: Follow the Module Tree**
1. Read `src/lib.rs` — this is the crate root
2. Find ALL `mod` declarations: `mod foo;`, `pub mod bar;`, `pub(crate) mod baz;`
3. For each `mod foo`, read `src/foo.rs` OR `src/foo/mod.rs`
4. Recursively process nested `mod` declarations within submodules
5. Build a complete module tree: `crate → mod auth → mod auth::middleware → mod auth::tokens`

**E.1.2: Track Re-exports**
1. Find all `pub use` statements in `lib.rs` and submodules
2. Follow each `pub use` to its source: `pub use auth::AuthConfig;` → read `auth.rs` for `AuthConfig` definition
3. Handle glob re-exports: `pub use auth::*;` → all pub items in `auth` become part of the crate API
4. Handle renamed re-exports: `pub use auth::Config as AuthConfig;`
5. The final public API = everything reachable via `pub use` from `lib.rs` + direct `pub` items in `lib.rs`

**E.1.3: Extract Pub Items**
For each module file, extract:
- `pub fn name(params) -> ReturnType` — public functions
- `pub struct Name { pub field: Type }` — public structs with public fields
- `pub enum Name { Variant1, Variant2(Type) }` — public enums with all variants
- `pub trait Name { fn method(&self, params) -> Type; }` — trait definitions with all methods (including default implementations)
- `pub type Name = Type;` — type aliases
- `pub const NAME: Type = value;` — constants
- `pub static NAME: Type = value;` — statics

**E.1.4: Extract Trait Implementations**
1. Find all `impl Trait for Struct` blocks across the entire crate
2. Record: which struct implements which trait, with what methods
3. Find all `impl Struct` blocks (inherent implementations)
4. Methods may be spread across MULTIPLE `impl` blocks in DIFFERENT files — collect all of them
5. Handle generic implementations: `impl<T: Display> Printable for Vec<T>` — record the trait bound

**E.1.5: Handle Visibility**
| Visibility | API Level | Extract? |
|-----------|-----------|----------|
| `pub` | Public (external users can access) | YES — primary API |
| `pub(crate)` | Crate-internal (tests can access, users cannot) | YES — mark as internal |
| `pub(super)` | Parent module only | NO — skip |
| (no modifier) | Private | NO — skip |

**E.1.6: Handle Generics and Trait Bounds**
1. Record generic type parameters: `fn process<T>(item: T)` → `T` is generic
2. Record trait bounds: `fn process<T: Handler + Send>(item: T)` → `T` must implement `Handler` and `Send`
3. Record where clauses: `fn process<T>(item: T) where T: Handler + Send`
4. Record associated types: `type Output` in trait definitions
5. For nested generics (`Result<Vec<T>, Error>`), represent the full type structure

**E.1.7: Handle Derive Macros**
1. Record `#[derive(...)]` attributes on structs and enums
2. Common derives that generate testable behavior:
   - `Serialize` / `Deserialize` — serialization contract
   - `Clone` — cloneability contract
   - `PartialEq` / `Eq` — equality comparison contract
   - `Hash` — hashing contract
   - `Default` — default construction contract
3. Custom derive macros (e.g., `#[derive(Builder)]`) — note them for manual review

**E.1.8: Handle Feature Flags**
1. Read `[features]` section in `Cargo.toml`
2. Find `#[cfg(feature = "...")]` conditional compilation blocks
3. Record which API items are conditional on which features
4. Mark conditional items: `pub fn connect() [feature: "async"]`

##### Java
1. Read package-level exports or `module-info.java`
2. Scan all public classes in the package
3. Extract interface definitions and abstract classes
4. Identify implemented interfaces per class

**Step E.2: Extract signatures**

For each exported symbol, extract:
```
{
  "name": "Registry",
  "kind": "class",
  "language_name": "Registry",          // actual name in this language
  "canonical_name": "Registry",         // protocol-defined name
  "module_path": "crate::registry",     // where it's defined (for Rust)
  "visibility": "pub",                  // pub | pub(crate) | exported
  "generics": [],                       // generic type parameters + bounds
  "derives": ["Clone", "Debug"],        // Rust derive macros
  "feature_flag": null,                 // conditional compilation feature
  "constructors": [                     // LIST — every construction path the spec declares
    {
      "name": "new",                    // canonical: "new" | "with_config" | "from_env" | ...
      "params": [
        {"name": "config", "type": "Config", "required": true, "default": null}
      ],
      "return_type": "Self"
    },
    {
      "name": "with_defaults",
      "params": [],
      "return_type": "Self"
    }
  ],
  "methods": [
    {
      "name": "register",
      "params": [...],
      "return_type": "None",
      "async": false,
      "skeleton": [                     // ordered checkpoint markers found in source body
        "validate_id_format",
        "check_duplicate",
        "resolve_dependencies",
        "acquire_write_lock",
        "insert_into_index",
        "emit_registered_event",
        "release_write_lock"
      ]
    }
  ],
  "trait_impls": [                      // Idiomatic interface contracts satisfied by this class
    {"contract": "Display", "method": "fmt"},        // Rust
    {"contract": "Serializable", "method": "to_dict"} // Python
  ]
}
```

**Trait/interface satisfaction extraction (per language).**

| Language | How to detect satisfaction |
|---|---|
| Python | Class inherits from `ABC` / `Protocol`; class implements dunder methods (`__str__`, `__eq__`, `__hash__`, `__iter__`, `__enter__`/`__exit__`); class has a `to_dict` / `from_dict` pair |
| TypeScript | `class X implements Y`; class has `toString()`, `[Symbol.iterator]`, `[Symbol.dispose]`; class has `toJSON()` |
| Go | Method set satisfies a known interface — grep for receiver methods like `String() string`, `Error() string`, `MarshalJSON() ([]byte, error)`, `Equal(other) bool`, `Close() error` |
| Rust | `impl Trait for X` blocks across the entire crate (Step E.1.4); `#[derive(...)]` macros (Step E.1.7) — derives count as satisfaction |
| Java | `class X implements Y`; presence of `equals/hashCode`, `toString`, `compareTo`, `iterator()` |

**Multi-constructor extraction (per language).**

| Language | What to collect |
|---|---|
| Python | `__init__` + every `@classmethod` returning `cls(...)` instance (e.g., `from_dict`, `from_env`, `default`) |
| TypeScript | `constructor(...)` + every `static` method returning an instance of the same class |
| Go | Every top-level `NewX*` function in the same package returning `*X` or `X` |
| Rust | Every `fn` in `impl X` blocks returning `Self` or `X` (e.g., `new`, `with_config`, `from_env`, `default`) |
| Java | All overloaded constructors + every `static` factory method returning the class type |

**Step E.3: Normalize for comparison**

Apply naming convention translation for comparison:

| Concept | Python | TypeScript | Go | Rust | Java |
|---|---|---|---|---|---|
| Class name | `PascalCase` | `PascalCase` | `PascalCase` | `PascalCase` | `PascalCase` |
| Method name | `snake_case` | `camelCase` | `PascalCase` | `snake_case` | `camelCase` |
| Function name | `snake_case` | `camelCase` | `PascalCase` | `snake_case` | `camelCase` |
| Constant | `UPPER_SNAKE` | `UPPER_SNAKE` | `PascalCase` | `UPPER_SNAKE` | `UPPER_SNAKE` |
| Parameter | `snake_case` | `camelCase` | `camelCase` | `snake_case` | `camelCase` |
| Package | `snake_case` | `kebab-case` | `lowercase` | `snake_case` | `dot.separated` |
| File | `snake_case.py` | `kebab-case.ts` | `snake_case.go` | `snake_case.rs` | `PascalCase.java` |

To compare across languages, convert all names to a canonical form (`snake_case`) for matching.

**Step E.4: Type mapping**

Check if `apcore/docs/spec/type-mapping.md` exists. If so, use it for cross-language type equivalence.

Default type mappings:

| Concept | Python | TypeScript | Go | Rust | Java | PHP |
|---|---|---|---|---|---|---|
| String | `str` | `string` | `string` | `String` / `&str` | `String` | `string` |
| Integer | `int` | `number` | `int` / `int64` | `i64` | `long` | `int` |
| Float | `float` | `number` | `float64` | `f64` | `double` | `float` |
| Boolean | `bool` | `boolean` | `bool` | `bool` | `boolean` | `bool` |
| List | `list[T]` | `T[]` | `[]T` | `Vec<T>` | `List<T>` | `array` |
| Dict/Map | `dict[K,V]` | `Record<K,V>` | `map[K]V` | `HashMap<K,V>` | `Map<K,V>` | `array` |
| Optional | `T \| None` | `T \| undefined` | `*T` | `Option<T>` | `Optional<T>` | `?T` |
| Any/Dynamic | `Any` | `unknown` | `any` / `interface{}` | `Box<dyn Any>` | `Object` | `mixed` |
| Result/Error | raise Exception | throw Error | `error` | `Result<T,E>` | throw Exception | throw Exception |
| Async | `async def` | `async function` | goroutine | `async fn` | `CompletableFuture` | `Fiber` / `Promise` |
| Callback | `Callable` | `(...) => T` | `func(...)` | `Fn(...)` / `FnMut(...)` / `FnOnce(...)` | `Function<T,R>` | `callable` |

> **Note:** This table covers common single-level generics. For nested generics (e.g., `Result<Option<Vec<T>>, E>`), represent the full type structure. When structural equivalence is ambiguous, flag for manual review rather than guessing.

**Default value equivalence (across languages).**

When the spec declares a parameter default, each language expresses it differently. The following are considered EQUIVALENT during checklist comparison — do NOT flag as mismatch:

| Concept | Python | TypeScript | Go | Rust | Java |
|---|---|---|---|---|---|
| Empty list | `[]` / `None` (sentinel) | `[]` / `undefined` | `nil` slice / zero-length | `Vec::new()` / `vec![]` / `Default::default()` | `Collections.emptyList()` / `null` |
| Empty map | `{}` / `None` | `{}` / `undefined` | `nil` map / `make(map[K]V)` | `HashMap::new()` / `Default::default()` | `Collections.emptyMap()` / `null` |
| Empty string | `""` | `""` | `""` | `String::new()` / `""` | `""` |
| Zero number | `0` / `0.0` | `0` | `0` | `0` / `0.0` / `Default::default()` | `0` / `0L` / `0.0` |
| False | `False` | `false` | `false` | `false` | `false` |
| None / null | `None` | `undefined` / `null` | `nil` (zero value) | `None` (Option) | `null` / `Optional.empty()` |
| Builder default | `cls()` no-arg | `new X()` no-arg | `&X{}` zero-value | `X::default()` / `X::new()` | `new X()` no-arg |
| Function/callback no-op | `lambda *a, **kw: None` / `None` | `() => {}` / `undefined` | `nil` func / no-op closure | `\|\| {}` / `None` | `() -> {}` / `null` |
| Current time | `datetime.now()` | `new Date()` | `time.Now()` | `Instant::now()` | `Instant.now()` |

**Default value semantic categories.** When comparing defaults, classify each into one of: `empty_collection`, `zero`, `none`, `default_construct`, `noop_callback`, `current_time`, `literal`. Two defaults match iff they fall into the same category — exact textual form doesn't matter. For `literal`, the literal value must match (e.g., `timeout=30` in all languages).

**Sentinel pattern (Python-specific):** Python often uses `def f(items=None): items = items or []` because `[]` as a default is mutable. When comparing, treat `param=None` + first-line `items = items or []` as `empty_collection` default, NOT as `none`.

**Step E.4a: Algorithm Checkpoint Extraction**

For each public method body, extract the ordered list of `checkpoint:NAME` markers literally present in the source. This is the input for sync's Step 4A skeleton consistency check.

> **Fast path (preferred).** Instead of spawning a sub-agent to grep, run:
>
> ```
> <scripts_dir>/extract-markers.sh <repo>/src [<more dirs>...]
> ```
>
> **Locating `<scripts_dir>`** — `extract-markers.sh` is bundled beside this file
> under `shared/scripts/` (Claude Code: `$CLAUDE_PLUGIN_ROOT/skills/shared/scripts`;
> Codex / bundled: `shared/scripts/` relative to this skill, rewritten by the
> bundler), NOT in the user's project. Its **arguments** are the user-project
> source dirs to scan; output goes to stdout only. If you cannot locate it, fall
> back to the per-language grep patterns below.
>
> It emits `path:line:name` for every marker in file/line order and drops
> obvious comment-only lines. Map each `path:line` to its enclosing method using
> the API summary (per-method scoping stays your job — a grep cannot parse method
> boundaries across five languages). The per-language patterns below are the spec
> and the fallback.

**Marker conventions (per language).** Sub-agents grep for these literal patterns inside the method body, in source order:

| Language | Pattern (regex) | Example call site |
|---|---|---|
| Python | `["']checkpoint:([a-z_][a-z0-9_]*)["']` | `logger.debug("checkpoint:validate_id_format")` |
| TypeScript | `["'\`]checkpoint:([a-z_][a-z0-9_]*)["'\`]` | `logger.debug("checkpoint:validate_id_format")` |
| Go | `"checkpoint:([a-z_][a-z0-9_]*)"` | `slog.Debug("checkpoint:validate_id_format")` |
| Rust | `"checkpoint:([a-z_][a-z0-9_]*)"` | `tracing::debug!("checkpoint:validate_id_format")` |
| Java | `"checkpoint:([a-z_][a-z0-9_]*)"` | `logger.debug("checkpoint:validate_id_format")` |

**Rules:**
1. **Source-order only** — return checkpoints in the order they textually appear in the method body, NOT in any inferred runtime order. If a checkpoint appears inside an `if` branch, still record it at its textual position.
2. **No invention** — only return checkpoints that are literally in the source. If a method has zero markers, return `[]`.
3. **Per-method scope** — checkpoints belong to the smallest enclosing function/method. Don't bubble up to outer scopes.
4. **Loops and branches** — if a checkpoint appears inside a loop, record it once at its textual position. If branches have different checkpoints, list them in textual order — the comparison logic will handle subsetting.
5. **Comments and disabled code** — ignore checkpoints inside `//`, `#`, `/* */`, or string literals that are NOT inside a logger call.

This pairs with Step 4A in `skills/sync/SKILL.md`.

**Step E.4b: Contract Extraction (Intent Parity)**

Extract the **behavioral contract** of every public method from source. This is the input for sync's Step 4B (contract tier — DEFAULT ON) and audit's D10 (Contract Parity) dimension. It captures *what* the method does — not *how* — so that cross-language divergence in logic/intent can be detected even when the Contract spec section is missing (degraded mode) or present (full parity check).

See `shared/contract-spec.md` for the authoritative Contract block format and semantics. The extraction must produce a structured record for every public method, regardless of whether the spec declares a Contract — if the spec is silent, the extracted record is still useful for cross-implementation comparison (detect divergence even when spec is incomplete).

For each public method, extract and return the following `contract` object:

```json
{
  "method": "Registry.register",
  "contract": {
    "inputs": [
      {
        "name": "id",
        "type": "str",
        "required": true,
        "default": null,
        "validations": [
          {"condition": "matches pattern ^[a-z][a-z0-9_]*$", "reject_with": "InvalidIdError"}
        ]
      },
      {"name": "module", "type": "Module", "required": true, "default": null,
       "validations": [{"condition": "isinstance(module, Module)", "reject_with": "TypeError"}]}
    ],
    "errors_raised": [
      {"type": "InvalidIdError", "code": "INVALID_ID"},
      {"type": "DuplicateError", "code": "DUPLICATE"},
      {"type": "DependencyError", "code": "DEPENDENCY_MISSING"}
    ],
    "side_effects": [
      "acquire_write_lock",
      "validate_inputs",
      "resolve_dependencies",
      "insert_into_index",
      "emit_registered_event",
      "release_write_lock"
    ],
    "return_shape": {"on_success": "None", "on_failure": "raises"},
    "properties": {
      "async": false,
      "thread_safe": true,
      "pure": false,
      "idempotent": null,
      "reentrant": null
    }
  }
}
```

**Extraction rules by field:**

1. **`inputs[].validations[]`** — scan the first ~20 non-comment lines of the method body (OR every line before the first mutating call / I/O call, whichever is shorter). Collect every guard clause of the form `if <condition>: raise X` / `if <cond> { throw X }` / `if <cond> { return Err(X) }`. Record each as `{condition: human-readable, reject_with: ErrorTypeName}`. The `condition` field is the literal source text of the condition (or a concise normalization — keep it short, max 120 chars).

2. **`errors_raised[]`** — grep the entire method body for error-raising patterns in the target language:
   - Python: `raise X(...)`, `raise X` — extract X
   - TypeScript: `throw new X(...)`, `throw X` — extract X
   - Go: `return ..., X` where X is an error value / `return ..., fmt.Errorf(...)` — extract X or the `Err*` sentinel name
   - Rust: `return Err(X)`, `Err(X)?`, `?` on a `Result<_, X>` — extract X
   - Java: `throw new X(...)` — extract X

   Deduplicate. For each, attempt to resolve the error code constant (grep the error class definition for a `code = "..."` / `const code` / derive macro parameter). Record as `{type, code}`. If code cannot be statically resolved, record `{type, code: null}`.

3. **`side_effects[]`** — in source order, collect calls matching these observable-effect patterns:
   - Lock acquisition: `lock.acquire()`, `mu.Lock()`, `self.lock.lock()`, `with self._lock:`, `Arc::clone`'s owned mutations
   - Lock release: `lock.release()`, `mu.Unlock()`, end of `with` block
   - Event emission: `emit(`, `publish(`, `dispatch(`, `notify(`
   - Index / storage mutation: `self._index[...] = ...`, `this.index.set(`, `m[k] = v`, `index.insert(`
   - I/O: `open(`, `write(`, `fs.writeFile(`, `io.Write(`, `sqlx::query!`, `http.Post(`
   - Self-state mutation: `self.x = ...` / `this.x = ...` / `s.x = ...` (Rust/Go with `&mut self`)

   Normalize each to a short snake_case descriptor (e.g., `acquire_write_lock`, `emit_registered_event`, `insert_into_index`). Return in source order. If a side effect occurs inside a branch, still record it at its textual position (same rule as checkpoint extraction).

4. **`return_shape`** — look at every `return` / implicit-return expression reachable without an error. Classify:
   - `None` / `void` / `()` / `unit`
   - `<literal>` (primitive literal)
   - `<type_constructor>(...)` (constructed object — record the type)
   - `raises` (method always throws — never returns)
   - `mixed` (multiple different shapes — flag as concern)

5. **`properties`**:
   - `async` — true iff signature declares async / returns Promise / returns `impl Future`
   - `thread_safe` — true iff method body (or a wrapping decorator / with-block) acquires a lock before any state mutation, OR method is pure, OR method operates only on stack-local data. Otherwise false. If ambiguous, return `null`.
   - `pure` — true iff no self/this writes, no external I/O, no argument mutation. Otherwise false.
   - `idempotent` — return `null` (cannot be inferred statically in general). Exception: if the method body is literally `if X in self._set: return; self._set.add(X)` or equivalent obvious dedup pattern, return true.
   - `reentrant` — return `null` (cannot be inferred statically without reachability analysis).

**Structural sub-agent output.** In the API summary returned by each repo's sub-agent (see sync `references/extract-api-prompt.md`), add a `CONTRACT:` sub-block for every method inside every class, and for every top-level function:

```
CLASSES:
- Registry
  methods:
    - register(id: str, module: Module) -> None
      skeleton: [...]
      contract:
        inputs:
          - id: str, required, validates[match_pattern], reject_with=InvalidIdError
          - module: Module, required, validates[isinstance], reject_with=TypeError
        errors_raised: [InvalidIdError(INVALID_ID), DuplicateError(DUPLICATE), DependencyError(DEPENDENCY_MISSING)]
        side_effects: [acquire_write_lock, validate_inputs, resolve_dependencies, insert_into_index, emit_registered_event, release_write_lock]
        return_shape: None
        properties: { async: false, thread_safe: true, pure: false, idempotent: null, reentrant: null }
```

**Rules:**
1. **Mandatory for every public method** — unlike skeleton, contract extraction is not gated on any flag or spec declaration. Every sub-agent MUST return a `contract` object per method.
2. **Conservative inference** — if a field cannot be statically determined, return `null`. Never invent.
3. **Degraded-mode usefulness** — even when the spec has no `## Contract` block, the extracted contract records from multiple repos can be cross-compared to surface divergence (e.g., Python raises `DuplicateError` but TS silently returns — surfaced as cross-repo finding even with no spec authority).
4. **Budget** — keep the total `contract` block under ~500 bytes per method to stay within sub-agent output limits.

**Step E.5: Extraction Verification**

After extraction, verify completeness before proceeding to comparison:

1. **Module coverage** (Rust): Count `mod` declarations in `lib.rs` vs. modules actually scanned. If any `mod` was declared but not scanned → ERROR, re-scan.
2. **Re-export coverage** (Rust/TS): Count `pub use` / `export * from` statements vs. resolved sources. Unresolved re-exports → ERROR.
3. **File coverage**: Count source files in `src/` vs. files actually read. Report percentage. If < 80% → WARNING, investigate.
4. **Symbol count sanity**: Compare extracted symbol count against typical density (2-10 public symbols per source file). Major deviation → WARNING.
5. **Trait implementation coverage** (Rust): Count trait definitions vs. found `impl Trait for X` blocks. Missing implementations → flag.

Report verification results:
```
Extraction Verification: apcore-rust
  Module tree: 15/15 modules scanned (100%) ✓
  Re-exports: 8/8 pub use chains resolved (100%) ✓
  Files: 22/24 source files read (92%) — 2 files in examples/ skipped ✓
  Symbols: 47 public items extracted (3.1 per file — reasonable) ✓
  Trait impls: 5 traits defined, 12 impl blocks found ✓
```

#### Comparison Output Format

```
API Comparison: {sdk-a} vs {sdk-b}

MISSING in {sdk-b}:
  - Registry.scan_directory() — present in {sdk-a} but not {sdk-b}
  - ErrorCode.BINDING_NOT_FOUND — enum value missing

SIGNATURE MISMATCH:
  - Executor.execute()
    {sdk-a}: (module_id: str, input: dict, context: Context | None = None) -> ExecutionResult
    {sdk-b}: (moduleId: string, input: Record<string, unknown>) -> ExecutionResult
    Issues: missing `context` parameter in {sdk-b}

NAMING INCONSISTENCY:
  - {sdk-a}: Registry.get_module() vs {sdk-b}: Registry.findModule()
    Expected: get_module / getModule (same canonical name)

TYPE MISMATCH:
  - Config.timeout: {sdk-a} uses float, {sdk-b} uses number (OK — equivalent)
  - Config.max_retries: {sdk-a} uses int, {sdk-b} uses string (MISMATCH)

TRAIT/INTERFACE MISMATCH:
  - {sdk-a}: Registry implements Display trait
  - {sdk-b}: Registry does NOT implement equivalent (toString/String)

GENERIC CONSTRAINT MISMATCH:
  - {sdk-a}: process<T: Handler + Send>(item: T)
  - {sdk-b}: process(item: Handler) — missing Send constraint equivalent

FEATURE FLAG DIVERGENCE:
  - {sdk-a}: connect() requires feature "async"
  - {sdk-b}: connect() always available — no equivalent conditional compilation

EXTRA in {sdk-b} (not in {sdk-a}):
  - Registry.clearCache() — language-specific addition (OK if documented)

Summary: {N} missing, {N} mismatched, {N} naming issues, {N} type issues, {N} trait issues
Extraction coverage: {sdk-a} {N}% files, {sdk-b} {N}% files
```
