# Extract Public API — Sub-agent Prompt Template

Variables to fill: `{repo_path}`, `{package}`

---

Extract the complete public API surface from {repo_path}.

**FIRST — read `shared/api-extraction-protocol.md`.** It is the normative
extraction protocol; the numbered summary below is a checklist, not a
replacement. In particular:

- **Step E.1** (+ E.1.1–E.1.8) — the language-specific deep scan. For Rust and
  TypeScript this is where module-tree walking, `pub use` / `export * from`
  re-export chains, visibility rules, generics and trait bounds, derive macros,
  and feature-flag-gated items are handled. Skipping it silently under-extracts
  the API surface, and every downstream comparison then runs against a partial
  surface — the failure is invisible, not loud.
- **Step E.2** — signature extraction detail.
- **Step E.5** — extraction verification. Run it before returning and include
  its coverage numbers in your summary (see "Extraction verification" below).

Then follow this checklist:

1. Read the main export file:
   - Python: src/{package}/__init__.py — extract all imports and __all__
   - TypeScript: src/index.ts — extract all export statements

2. For each exported symbol, read its source file and extract:
   - Kind: class | function | type | enum | constant | interface
   - Name (in this language's convention)
   - For classes: constructor params (name, type, required, default), all public methods with full signatures
   - For functions: params (name, type, required, default), return type, async flag
   - For enums: all member names and values
   - For types/interfaces: all fields (name, type, required)
   - For constants: name, type, value

3. Also extract:
   - Error classes: name, error code, parent class
   - Middleware interfaces: method signatures
   - Extension points: discoverer, validator, exporter interfaces
   - **Trait/interface implementations**: for each public class, the list of trait/interface contracts it satisfies (e.g., Rust `impl Display for Registry`, Python `class Registry(Hashable)`, Go `func (r *Registry) String() string`, TS `class Registry implements Serializable`). Use the equivalence table in `sync/references/checklist-tables.md` §2 to recognize idiomatic forms.
   - **Multi-constructor patterns**: for each public class, the list of all construction paths (Rust `impl Self { fn new; fn with_…; fn from_… }`; Python `__init__` + every `@classmethod` factory; Go every `NewX*` function in the same package; TS constructor + static factories). Return as `constructors: [{name, params, return_type}, ...]`.
   - **Algorithm checkpoint markers**: for each public method body, grep for `checkpoint:[a-z_][a-z0-9_]*` literal strings (in `logger.debug` / `tracing::debug!` / `slog.Debug` / `span.AddEvent` / `tracer.startSpan` calls). Return them in source order as a `skeleton` field on each method object: `methods: [{name: "...", skeleton: [checkpoint_1, checkpoint_2, ...]}]`. Top-level functions get a sibling `skeleton` field. Do NOT invent — only report literally found markers. If none found for a method, return an empty list (`skeleton: []`).
   - **Behavioral contract (MANDATORY)**: for every public method and every top-level function, extract a `contract` object per the rules in `shared/api-extraction-protocol.md` Step E.4b. This captures the method's *intent* (inputs validation, errors raised, side effects, return shape, behavioral properties) as statically observable from source. It is not gated on any flag and MUST be returned for every method, regardless of whether the spec declares a `## Contract` block. See `shared/contract-spec.md` for field semantics.

Return a structured summary in this exact format:

REPO: {repo-name}
LANGUAGE: {language}
VERSION: {version}
EXPORT_COUNT: {N}

CLASSES:
- {ClassName}
  constructors:
    - {ctor_name}({param1}: {type1}, {param2}: {type2} = {default})
    - {factory_name}({params}) -> Self
  methods:
    - {method_name}({params}) -> {return_type} [async]
      skeleton: [checkpoint_1, checkpoint_2, ...]
      contract:
        inputs:
          - {param}: {type}, {required|optional}[, default={val}], validates[{cond}], reject_with={ErrorType}
          - ...
        errors_raised: [{ErrorType}({code}), ...]
        side_effects: [{effect_1}, {effect_2}, ...]
        return_shape: {None|literal|ConstructedType|raises|mixed}
        properties: { async: {bool}, thread_safe: {bool|null}, pure: {bool}, idempotent: {bool|null}, reentrant: {bool|null} }
    - ...
  trait_impls:
    - {ContractName}  (e.g., Display, Clone, Serialize, Iterator)

FUNCTIONS:
- {function_name}({params}) -> {return_type} [async]
  skeleton: [checkpoint_1, checkpoint_2, ...]
  contract:
    inputs: [...]
    errors_raised: [...]
    side_effects: [...]
    return_shape: ...
    properties: { ... }

ENUMS:
- {EnumName}: {MEMBER1}={value1}, {MEMBER2}={value2}, ...

TYPES:
- {TypeName}: {field1}: {type1}, {field2}: {type2}, ...

ERRORS:
- {ErrorName}(code={CODE}, parent={ParentError})

CONSTANTS:
- {NAME}: {type} = {value}

Extraction verification (Step E.5 — MANDATORY before returning):

Run the E.5 checks from `shared/api-extraction-protocol.md` and append the result
block to your summary. A low module/re-export coverage number is the signal that
the deep scan missed part of the surface — report it rather than returning a
confident-looking partial extraction.

```
EXTRACTION_VERIFICATION:
  Module tree: {N}/{N} modules scanned ({pct}%)
  Re-exports: {N}/{N} chains resolved ({pct}%)
  Files: {N}/{N} source files read ({pct}%)
  Symbols: {N} public items ({avg} per file)
  Trait impls: {N} traits defined, {N} impl blocks found
```

Error handling:
- If the repo path does not exist, return: REPO: {repo-name}, STATUS: NOT_FOUND
- If the main export file is missing or empty, return: REPO: {repo-name}, STATUS: NO_EXPORTS, REASON: {description}
- If individual source files cannot be read, skip them and note in the summary

Keep the summary concise but complete. Target ~3-5KB.
