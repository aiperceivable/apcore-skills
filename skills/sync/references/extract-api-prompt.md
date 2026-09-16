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

1. Read the main export file (the crate/package root — the entry point every
   public symbol must be reachable from):
   - **Python**: `src/{package}/__init__.py` — extract `__all__`, or all non-underscore
     imports when `__all__` is absent. Follow `from .submodule import X` chains to
     the definition (protocol Step E.1, Python).
   - **TypeScript**: `src/index.ts` — extract every `export` statement, then resolve
     `export * from './mod'` and `export { X } from './mod'` re-export chains to the
     defining module (protocol Step E.1, TypeScript).
   - **Rust**: `src/lib.rs` — the crate root. This is the deepest of the three and
     the one most often under-extracted: you must walk the **module tree** (E.1.1 —
     every `mod foo;` resolves to `src/foo.rs` *or* `src/foo/mod.rs`, recursively),
     resolve **every `pub use`** including glob (`pub use auth::*`) and renamed
     (`pub use auth::Config as AuthConfig`) forms (E.1.2), and apply the visibility
     table (E.1.5 — `pub(crate)` / `pub(super)` are NOT public API). A Rust crate's
     public surface is "everything reachable via `pub use` from `lib.rs`, plus direct
     `pub` items in `lib.rs`" — reading `lib.rs` alone and stopping is the classic
     partial extraction, and it fails silently because `lib.rs` looks complete.

   These three are the languages currently in scope. If you are pointed at a repo in
   another language, follow the matching `##### {Language}` section of protocol Step
   E.1 rather than guessing an analogue of the above.

2. For each exported symbol, read its source file and extract:
   - Kind: class | function | type | enum | constant | interface
   - Name (in this language's convention)
   - **`source_file` (MANDATORY)** — the repo-root-relative path of the file where
     the symbol is *defined*. You already open that file in this step; record the
     path instead of discarding it. Follow re-exports to the definition — never
     record the barrel file (`__init__.py`, `index.ts`, `lib.rs`) unless the symbol
     is genuinely defined there. See `shared/api-extraction-protocol.md` Step E.2
     for why this field is not optional.

     Per language, the definition site is the end of the re-export chain, not its start:
     | Language | Barrel (do NOT record) | Record instead |
     |---|---|---|
     | Python | `src/{package}/__init__.py` | the module the `from .x import Y` chain ends at, e.g. `src/apcore/registry/registry.py` |
     | TypeScript | `src/index.ts` | the module the `export {…} from './x'` chain ends at, e.g. `src/registry/registry.ts` |
     | Rust | `src/lib.rs` | the file the `pub use` resolves to — `src/registry.rs` **or** `src/registry/mod.rs`, whichever actually exists (E.1.1). For `pub use auth::Config as AuthConfig`, record where `Config` is defined, not where it is renamed. |
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

FILE_MAP:
- {repo-root-relative-path}: {Symbol1}, {Symbol2}, ...
- {repo-root-relative-path}: {Symbol3}, ...

`FILE_MAP` is the serialized form of every symbol's `source_file` field, grouped
by file so that symbols sharing a file cost one path instead of many. **It is
mandatory and must cover every top-level symbol listed above** — classes,
functions, enums, types, errors and constants alike. A symbol appearing in
`CLASSES:` but not in any `FILE_MAP` line is an incomplete extraction, not a
stylistic choice.

If a symbol's defining file genuinely cannot be determined (generated code,
dynamic registration), list it under the literal path `(unresolved)` rather than
guessing a plausible path. `(unresolved)` here is the text-format spelling of the
protocol's `"source_file": null` — same state, two serializations. A wrong path is worse than a missing one: it sends
sync's Step 4C sub-agent to the wrong source, which then reports no divergence
and looks like a clean pass.

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
  Source files: {N}/{N} symbols mapped to a defining file ({pct}%)
  Trait impls: {N} traits defined, {N} impl blocks found
```

Error handling:
- If the repo path does not exist, return: REPO: {repo-name}, STATUS: NOT_FOUND
- If the main export file is missing or empty, return: REPO: {repo-name}, STATUS: NO_EXPORTS, REASON: {description}
- If individual source files cannot be read, skip them and note in the summary

Keep the summary concise but complete. Target ~3-6KB (`FILE_MAP` is grouped by file precisely so this stays a few hundred bytes, not a path per symbol).
