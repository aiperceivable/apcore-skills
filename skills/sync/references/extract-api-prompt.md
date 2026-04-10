# Extract Public API — Sub-agent Prompt Template

Variables to fill: `{repo_path}`, `{package}`

---

Extract the complete public API surface from {repo_path}.

Follow the API Extraction Protocol:

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
   - **Trait/interface implementations**: for each public class, the list of trait/interface contracts it satisfies (e.g., Rust `impl Display for Registry`, Python `class Registry(Hashable)`, Go `func (r *Registry) String() string`, TS `class Registry implements Serializable`). Use the equivalence table in Step 4.2 item 4 to recognize idiomatic forms.
   - **Multi-constructor patterns**: for each public class, the list of all construction paths (Rust `impl Self { fn new; fn with_…; fn from_… }`; Python `__init__` + every `@classmethod` factory; Go every `NewX*` function in the same package; TS constructor + static factories). Return as `constructors: [{name, params, return_type}, ...]`.
   - **Algorithm checkpoint markers**: for each public method body, grep for `checkpoint:[a-z_][a-z0-9_]*` literal strings (in `logger.debug` / `tracing::debug!` / `slog.Debug` / `span.AddEvent` / `tracer.startSpan` calls). Return them in source order as a `skeleton` field on each method object: `methods: [{name: "...", skeleton: [checkpoint_1, checkpoint_2, ...]}]`. Top-level functions get a sibling `skeleton` field. Do NOT invent — only report literally found markers. If none found for a method, return an empty list (`skeleton: []`).

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
    - ...
  trait_impls:
    - {ContractName}  (e.g., Display, Clone, Serialize, Iterator)

FUNCTIONS:
- {function_name}({params}) -> {return_type} [async]
  skeleton: [checkpoint_1, checkpoint_2, ...]

ENUMS:
- {EnumName}: {MEMBER1}={value1}, {MEMBER2}={value2}, ...

TYPES:
- {TypeName}: {field1}: {type1}, {field2}: {type2}, ...

ERRORS:
- {ErrorName}(code={CODE}, parent={ParentError})

CONSTANTS:
- {NAME}: {type} = {value}

Error handling:
- If the repo path does not exist, return: REPO: {repo-name}, STATUS: NOT_FOUND
- If the main export file is missing or empty, return: REPO: {repo-name}, STATUS: NO_EXPORTS, REASON: {description}
- If individual source files cannot be read, skip them and note in the summary

Keep the summary concise but complete. Target ~3-5KB.
