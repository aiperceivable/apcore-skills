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
  "constructor": {
    "params": [
      {"name": "config", "type": "Config", "required": true, "default": null},
      {"name": "discoverers", "type": "List[Discoverer]", "required": false, "default": "[]"}
    ]
  },
  "methods": [
    {
      "name": "register",
      "params": [...],
      "return_type": "None",
      "async": false
    }
  ],
  "trait_impls": [                      // Rust: which traits this struct implements
    {"trait": "Display", "methods": ["fmt"]},
    {"trait": "From<Config>", "methods": ["from"]}
  ]
}
```

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
