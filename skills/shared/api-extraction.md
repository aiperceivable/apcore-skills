### API Extraction Protocol

Standard method for extracting and comparing public APIs across language implementations.

> **Extraction protocol lives in `shared/api-extraction-protocol.md`.**
> This file holds only what the *comparison* side needs (E.3, E.4). Steps
> E.1, E.2, E.4a, E.4b, E.5 are executed by extraction sub-agents and are
> deliberately NOT here — sync `@`-includes this file at Step 4, so anything
> placed here loads on every run whether or not it is used. The definition of
> what counts as public API also lives there — it governs extraction, not
> comparison.

#### Comparison Tables

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

