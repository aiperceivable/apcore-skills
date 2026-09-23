# Extract Public API — Sub-agent Prompt Template

Variables to fill: `{repo_path}`, `{package}`, `{output_path}`

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
   - **Behavioral contract (MANDATORY)**: for every public method and every top-level function, extract a `contract` object per the rules in `shared/api-extraction-protocol.md` Step E.4b. **Note the `errors_raised` / `errors_propagated` split** — an error thrown inside this method's own body and one thrown by a helper it calls go in different fields, in every language. Putting a delegated raise into `errors_raised` (or omitting it because it was delegated) is what produced confirmed false cross-language divergences; the boundary is not a matter of convenience. This captures the method's *intent* (inputs validation, errors raised, side effects, return shape, behavioral properties) as statically observable from source. It is not gated on any flag and MUST be returned for every method, regardless of whether the spec declares a `## Contract` block. See `shared/contract-spec.md` for field semantics.

**WHERE YOUR OUTPUT GOES.** Write the full extraction below to `{output_path}`
using Write (or append to it as you walk the module tree — you do not need to hold
the whole thing in your own context either). Your **reply** carries only the receipt
described under "What to return" at the end: the verification block, `FILE_MAP`, and
the path. Do not paste the extraction into your reply.

This repo may have hundreds of public symbols across ~100 files. That is expected and
it is not a reason to narrow your scan, summarise selectively, or suggest the work be
split — the file has no size limit. Extract everything; write it down as you go.

Write the extraction to `{output_path}` in this exact format:

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
        errors_raised: [{ErrorType}({code}), ...]        # thrown lexically in THIS body
        errors_propagated: [{ErrorType}({code}) via {callee}, ...]   # from same-repo callees, depth 2
        propagation_truncated: {true|false}              # true if you stopped before depth 2
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
    errors_propagated: [...]
    propagation_truncated: {true|false}
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

## Writing incrementally (expected for any repo above ~30 files)

Append to `{output_path}` as you go; do not hold the whole extraction and write it
once at the end. A single final write forfeits **everything** if you run out of
context or hit a rate limit — measured: the `apcore-rust` extraction sat at 807
bytes for 50 minutes and would have lost 341 KB of finished work to one 429.

Appending means section headers (`CLASSES:`, `FUNCTIONS:`, …) will repeat, once per
chunk. **That is allowed and expected.** Consumers union every occurrence. Two rules
make it unambiguous:

- Write `REPO:` / `LANGUAGE:` / `VERSION:` / `EXPORT_COUNT:` **once**, in the first chunk.
- Write `FILE_MAP:` (with the colon) and `EXTRACTION_VERIFICATION:` **once**, in the
  final chunk, after every symbol chunk. They summarise the whole file, so they are
  meaningless mid-stream.

Never let a chunk boundary fall inside a symbol's entry.

## What to return (your reply — keep under 1 KB)

Reply with ONLY this:

```
EXTRACTION: {repo-name}
OUTPUT_FILE: {output_path}
FILE_MAP_LINES: {first}-{last}          # where FILE_MAP sits inside OUTPUT_FILE
SYMBOLS: {N}   UNRESOLVED: {N}

EXTRACTION_VERIFICATION:
  ... (the block above, verbatim)
```

**Do NOT paste `FILE_MAP` into your reply.** It scales with the repo — at 285
symbols over 91 files it is ~7.5 KB, several times this whole reply budget. It
lives in `{output_path}` like the rest of the extraction; the orchestrator reads
it from there, by line range, only when a later step actually needs it (sync Step
4C.1). Report its line range and its unresolved count here; that is enough for the
coverage gate to act without loading it.

Everything except the verification block stays in the file.

Error handling:
- If the repo path does not exist, reply: REPO: {repo-name}, STATUS: NOT_FOUND
- If the main export file is missing or empty, reply: REPO: {repo-name}, STATUS: NO_EXPORTS, REASON: {description}
- If individual source files cannot be read, skip them and note it in the verification block
- If you cannot finish, write what you have to `{output_path}` and reply with the
  verification block showing the true (partial) coverage numbers. A partial extraction
  that reports itself as partial is recoverable; one that reports itself as complete
  corrupts every downstream comparison. Never round coverage up.
