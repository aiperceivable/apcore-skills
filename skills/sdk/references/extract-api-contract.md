# Extract API Contract — Sub-agent Prompt Template

Variables to fill: `{lang}`, `{ref_path}`, `{type}`, `{protocol_path}`, `{spec_root}`

---

Extract the complete public API contract from the apcore reference implementation for porting to {lang}.

Reference repo: {ref_path}
Project type: {type}

## Discovery Process (type-agnostic)

1. Read the main entry point: `src/{package}/__init__.py` (or `src/index.ts`, `src/lib.rs`, `src/main.go`) — extract all public exports
2. For each exported class/function: read its source file, extract constructor + all public methods with full signatures
3. Walk `src/{package}/` recursively — discover ALL subdirectories and source files. Record the directory tree structure (this is what the target project will mirror).
4. Find error classes/codes (typically in `errors.py` / `errors.ts` or similar)
5. Find extension points / interfaces that consumers are expected to implement

Also read:
- {spec_root}/docs/features/ and the component's normative spec files — for component contracts
- {protocol_path}/PROTOCOL_SPEC.md — for shared Core definitions when available
- {protocol_path}/docs/spec/type-mapping.md — if exists, for type translations
- {ref_path}/examples/ — list all example files, directories, and their purpose (for porting)
- {ref_path}/tests/ — list complete test directory structure and all test file names (for mirroring)

## Output Format

Return a structured API contract:

API_CONTRACT:
  type: {type}
  source: {ref-repo}
  source_version: {version}
  export_count: {N}
  module_count: {N} (number of source files/modules)

SOURCE_TREE:
  # Complete directory structure of src/ — this drives the scaffold
  src/
    {main-module-file}
    {file-or-dir}: {one-line purpose}
    {subdir}/
      {file}: {one-line purpose}
    ...

MODULES:
- module: {module-name}
  file: {source-file}
  classes:
    - {ClassName}:
        constructor: ({params with types and defaults})
        methods:
          - {name}({params}) -> {return} [async] [static]
  functions:
    - {name}({params}) -> {return} [async]
  types:
    - {TypeName}: {definition}
  constants:
    - {NAME}: {type} = {value}

ERROR_HIERARCHY:
  base: {BaseErrorName}
  codes: {ErrorCodeEnum with all values}
  classes:
    - {ErrorName}(code={CODE}, parent={Parent})

EXTENSION_POINTS:
  - {interface-name}: {method signatures}

EXAMPLES:
  # Complete directory tree of examples/
  - {path}: {one-line description of what it demonstrates}

TESTS:
  # Complete directory tree of tests/
  structure: {list of all test subdirectories}
  files:
    - {test-filename}: {what it tests}
  total_count: {N}

## Error Handling

- If the reference repo path does not exist, return: STATUS: NOT_FOUND, REASON: "Reference repo not found at {path}"
- If the main entry point is missing or empty, return: STATUS: NO_EXPORTS, REASON: "No public exports found"
- If PROTOCOL_SPEC.md is missing, proceed with reference implementation only and note: "Core protocol spec not found; use the component specs and reference implementation"
- If individual source files cannot be read, skip them and note in the summary

Target ~6-10KB summary.
