### API Extraction Protocol

Standard method for extracting and comparing public APIs across language implementations.

#### What Constitutes the Public API

The public API is defined by the **protocol specification** (`apcore/PROTOCOL_SPEC.md`) and **feature specs** (`apcore/docs/features/*.md`). Each SDK must implement these contracts.

Public API surface includes:
1. **Exported classes** — listed in `__init__.py` (Python) or `index.ts` (TypeScript)
2. **Exported functions** — top-level functions in `__init__.py` / `index.ts`
3. **Exported types/interfaces** — type definitions, enums, error codes
4. **Constructor signatures** — parameter names, types, defaults
5. **Method signatures** — parameter names, types, return types
6. **Error classes** — names, codes, hierarchy
7. **Configuration options** — setting names, types, defaults
8. **Module definition API** — decorators, binding formats

#### Extraction Steps

For each SDK repository:

**Step E.1: Read public exports**

- Python: Read `src/<package>/__init__.py`, extract `__all__` or all non-underscore imports
- TypeScript: Read `src/index.ts`, extract all `export` statements
- Go: Read all `*.go` files in root package, extract capitalized identifiers
- Rust: Read `src/lib.rs`, extract `pub` items
- Java: Read package-level exports or module-info.java

**Step E.2: Extract signatures**

For each exported symbol, extract:
```
{
  "name": "Registry",
  "kind": "class",
  "language_name": "Registry",          // actual name in this language
  "canonical_name": "Registry",         // protocol-defined name
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

| Concept | Python | TypeScript | Go | Rust | Java |
|---|---|---|---|---|---|
| String | `str` | `string` | `string` | `String` / `&str` | `String` |
| Integer | `int` | `number` | `int` / `int64` | `i64` | `long` |
| Float | `float` | `number` | `float64` | `f64` | `double` |
| Boolean | `bool` | `boolean` | `bool` | `bool` | `boolean` |
| List | `list[T]` | `T[]` | `[]T` | `Vec<T>` | `List<T>` |
| Dict/Map | `dict[K,V]` | `Record<K,V>` | `map[K]V` | `HashMap<K,V>` | `Map<K,V>` |
| Optional | `T \| None` | `T \| undefined` | `*T` | `Option<T>` | `Optional<T>` |
| Any/Dynamic | `Any` | `unknown` | `any` / `interface{}` | `Box<dyn Any>` | `Object` |
| Result/Error | raise Exception | throw Error | `error` | `Result<T,E>` | throw Exception |
| Async | `async def` | `async function` | goroutine | `async fn` | `CompletableFuture` |
| Callback | `Callable` | `(...) => T` | `func(...)` | `Fn(...)` | `Function<T,R>` |

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

EXTRA in {sdk-b} (not in {sdk-a}):
  - Registry.clearCache() — language-specific addition (OK if documented)

Summary: {N} missing, {N} mismatched, {N} naming issues, {N} type issues
```
