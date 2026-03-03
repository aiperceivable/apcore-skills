---
name: sdk
description: >
  Bootstrap a new language SDK for the apcore ecosystem. Scaffolds the project
  structure, extracts the full API contract from the protocol spec and reference
  implementation, generates build configuration, and creates an implementation
  plan via code-forge:plan for each feature module.
---

# Apcore Skills — SDK

Bootstrap a new apcore core SDK or MCP bridge in a new language.

## Iron Law

**EVERY NEW SDK MUST IMPLEMENT THE FULL PROTOCOL API CONTRACT. No partial SDKs — if you ship it, it must cover all exported symbols from the reference implementation.**

## Anti-Rationalization Table

| Thought | Reality |
|---------|---------|
| "I'll start with just the core classes" | Start with a complete project skeleton. Feature implementation order is code-forge's job. |
| "Copy the Python structure exactly" | Use idiomatic target-language patterns. Same concepts, different structure. |
| "Tests can come later" | TDD is mandatory. Test infrastructure is set up in scaffolding. |
| "I'll figure out the naming as I go" | Naming is defined by conventions.md. Apply language rules from day one. |

## When to Use

- Starting a new apcore SDK in Go, Rust, Java, C#, etc.
- Starting a new apcore MCP bridge in a new language
- Re-scaffolding an existing SDK that needs restructuring

## Command Format

```
/apcore-skills:sdk <language> [--type core|mcp] [--ref apcore-python]
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `<language>` | Yes | — | Target language: `go`, `rust`, `java`, `csharp`, `kotlin`, `swift` |
| `--type` | No | `core` | What to scaffold: `core` (SDK) or `mcp` (MCP bridge) |
| `--ref` | No | auto-detect | Reference implementation to extract API from |

## Context Management

Steps 2 and 4 use sub-agents. Step 2 analyzes the reference implementation. Step 4 generates the project skeleton. The main context orchestrates and retains only summaries.

## Workflow

```
Step 0 (ecosystem) → 1 (parse args) → 2 (extract API contract) → 3 (tech stack) → 4 (scaffold) → 5 (feature specs) → 6 (plan generation) → 7 (summary)
```

## Detailed Steps

### Step 0: Ecosystem Discovery

@../shared/ecosystem.md

---

### Step 1: Parse Arguments

Parse `$ARGUMENTS`:

1. Extract `<language>` — required, use `AskUserQuestion` if missing
2. Extract `--type` — default `core`
3. Extract `--ref` — auto-detect:
   - For `core`: prefer `apcore-python` if exists, else `apcore-typescript`
   - For `mcp`: prefer `apcore-mcp-python` if exists, else `apcore-mcp-typescript`

Derive target repo name:
- Core SDK: `apcore-{lang}` (e.g., `apcore-go`, `apcore-java`)
- MCP bridge: `apcore-mcp-{lang}` (e.g., `apcore-mcp-go`)

Derive target path: `{ecosystem_root}/apcore-{type}-{lang}/` (or `{ecosystem_root}/{framework}-apcore/`)

Check if target directory already exists:
- If exists with source files: warn and ask — "Update scaffolding" / "Use as-is" / "Cancel"
- If exists but empty: proceed

Display:
```
SDK Bootstrap:
  Language:   {lang}
  Type:       {core|mcp}
  Reference:  {ref-repo} ({ref-lang})
  Target:     {target-path}
```

---

### Step 2: Extract API Contract (Sub-agent)

Spawn `Task(subagent_type="general-purpose")`:

**Sub-agent prompt:**
```
Extract the complete public API contract from the apcore reference implementation for porting to {lang}.

Reference repo: {ref_path}
Reference type: {core|mcp}

Read the following files and extract the full API surface:

For core SDK:
1. src/{package}/__init__.py (or src/index.ts) — all public exports
2. For each exported class: read source file, extract constructor + all public methods with full signatures
3. src/{package}/errors.py (or errors.ts) — all error classes and codes
4. src/{package}/middleware/ — middleware interfaces
5. src/{package}/registry/ — registry interfaces
6. src/{package}/schema/ — schema interfaces
7. src/{package}/observability/ — observability interfaces

For MCP bridge:
1. src/{package}/__init__.py (or src/index.ts) — all public exports
2. src/{package}/server/ — server factory, transport interfaces
3. src/{package}/auth/ — authentication interfaces
4. src/{package}/adapters/ — adapter interfaces
5. src/{package}/converters/ — converter interfaces

Also read:
- {protocol_path}/PROTOCOL_SPEC.md — for authoritative definitions
- {protocol_path}/docs/spec/type-mapping.md — if exists, for type translations

Return a structured API contract in this format:

API_CONTRACT:
  type: {core|mcp}
  source: {ref-repo}
  source_version: {version}
  export_count: {N}
  module_count: {N} (number of source files/modules)

MODULES:
- module: {module-name} (e.g., "executor", "registry", "schema")
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

Error handling:
- If the reference repo path does not exist, return: STATUS: NOT_FOUND, REASON: "Reference repo not found at {path}"
- If __init__.py/index.ts is missing or empty, return: STATUS: NO_EXPORTS, REASON: "No public exports found"
- If PROTOCOL_SPEC.md is missing, proceed with reference implementation only and note: "Protocol spec not found, using reference impl as sole authority"
- If individual source files cannot be read, skip them and note in the summary

Target ~5-8KB summary.
```

Store as `api_contract`. If the sub-agent returns STATUS: NOT_FOUND or NO_EXPORTS, display error and use `AskUserQuestion` to either provide a different reference or abort.

---

### Step 3: Confirm Tech Stack

Use `AskUserQuestion` to confirm the target language tech stack.

@../shared/conventions.md (refer to "Testing Conventions" and "Dependency Conventions" sections)

**For Go:**
- Go version: "1.21+ (Recommended)" / "1.22+"
- Module path: default `github.com/aipartnerup/apcore-go`
- Test extras: "Standard testing (Recommended)" / "testify"
- Schema validation: "go-jsonschema (Recommended)" / "gojsonschema" / "Other"

**For Rust:**
- Rust edition: "2021 (Recommended)" / "2024"
- Async runtime: "tokio (Recommended)" / "async-std" / "None (sync only)"
- Serialization: "serde (Recommended)" / "Other"
- Schema: "schemars (Recommended)" / "Other"

**For Java:**
- Java version: "17+ (Recommended)" / "21+"
- Build tool: "Gradle (Recommended)" / "Maven"
- Schema validation: "Jackson (Recommended)" / "Gson"
- Test framework: "JUnit 5 (Recommended)" / "TestNG"

**For other languages:** Single open-ended question about tech stack preferences.

Store `tech_stack` decisions.

---

### Step 4: Scaffold Project (Sub-agent)

Spawn `Task(subagent_type="general-purpose")`:

**Sub-agent prompt:**
```
Create the project skeleton for {target-repo-name} at {target-path}.

Language: {lang}
Type: {core|mcp}
Tech stack: {tech_stack decisions}
Package name: {derived package name per conventions}

## Project Structure

Follow the apcore project structure convention:

{For core SDK:}
{target-path}/
├── {build-config}                    # pyproject.toml / package.json / go.mod / Cargo.toml
├── .gitignore                        # language-appropriate patterns
├── README.md                         # project name, description, installation, link to docs
├── CHANGELOG.md                      # empty "## [Unreleased]" section
├── LICENSE                           # Detect from existing ecosystem repos or ask user (MIT / Apache-2.0)
├── src/                              # or language-appropriate source dir
│   ├── {main-module-file}            # exports (empty stubs with TODO)
│   ├── executor.{ext}               # stub
│   ├── context.{ext}                # stub
│   ├── module.{ext}                 # stub
│   ├── config.{ext}                 # stub
│   ├── errors.{ext}                 # stub with ErrorCode enum and base error
│   ├── acl.{ext}                    # stub
│   ├── approval.{ext}              # stub
│   ├── async_task.{ext}            # stub
│   ├── bindings.{ext}              # stub
│   ├── decorator.{ext}             # stub
│   ├── extensions.{ext}            # stub
│   ├── middleware/                   # stub directory
│   ├── registry/                    # stub directory
│   ├── schema/                      # stub directory
│   ├── observability/               # stub directory
│   └── utils/                       # stub directory
└── tests/
    └── {test-config}                # pytest.ini / vitest.config / test runner config

{For MCP bridge:}
{target-path}/
├── {build-config}
├── .gitignore
├── README.md
├── CHANGELOG.md
├── LICENSE
├── src/
│   ├── {main-module-file}
│   ├── server/                      # factory, transport stubs
│   ├── auth/                        # JWT stub
│   ├── adapters/                    # adapter stubs
│   ├── converters/                  # converter stubs
│   └── cli.{ext}                   # CLI entry point stub
└── tests/
    └── {test-config}

## Stub File Content

Each stub file should contain:
1. Module/file header comment referencing the protocol spec section
2. Import of base types from the main module
3. Class/function stubs with correct signatures from the API contract
4. TODO comments indicating what needs to be implemented
5. Type annotations matching the language convention

## API Contract Reference
{api_contract from Step 2}

## Naming
Apply {lang} naming conventions:
- Python: snake_case for functions/methods, PascalCase for classes
- TypeScript: camelCase for functions/methods, PascalCase for classes
- Go: PascalCase for public, camelCase for private
- Rust: snake_case for functions/methods, PascalCase for types
- Java: camelCase for methods, PascalCase for classes

Create ALL files listed above. Return the list of files created.
```

After sub-agent completes, verify:
- Build config file exists
- Main module file exists with exports
- At least 5 source files exist
- Tests directory exists
- README.md exists

---

### Step 5: Generate Feature Specs

Check if feature specs already exist at `{protocol_path}/docs/features/*.md`.

If they exist:
- Link to them via `.code-forge.json` configuration
- Display: `Feature specs found: {N} specs in {protocol_path}/docs/features/`

If they don't exist:
- Extract module list from the API contract
- Generate lightweight feature specs at `{target-path}/docs/features/`:
  - One per module (executor, registry, schema, etc.)
  - Each spec contains: module purpose, public API surface, acceptance criteria
- Display: `Feature specs generated: {N} specs in docs/features/`

---

### Step 6: Generate .code-forge.json and Trigger Planning

Write `{target-path}/.code-forge.json`:
```json
{
  "_tool": {
    "name": "code-forge",
    "description": "Transform documentation into actionable development plans",
    "url": "https://github.com/tercel/code-forge",
    "skills_collection": "https://github.com/tercel/claude-code-skills"
  },
  "directories": {
    "base": "./",
    "input": "{relative-path-to-feature-specs}",
    "output": "planning/"
  },
  "reference_docs": {
    "sources": ["{relative-path-to-ref}/planning/*/plan.md"]
  },
  "port": {
    "source_docs": "{relative-path-to-protocol}",
    "reference_impl": "{relative-path-to-ref}",
    "target_lang": "{lang}"
  },
  "execution": {
    "default_mode": "ask",
    "auto_tdd": true,
    "task_granularity": "medium"
  }
}
```

Initialize git:
```bash
cd {target-path} && git init && git add . && git commit -m "chore: initialize {target-repo-name} project skeleton"
```

---

### Step 7: Display Summary and Next Steps

```
apcore-skills:sdk — SDK Bootstrap Complete

Target: {target-path}
Language: {lang}
Type: {core|mcp}
Modules: {N} source files scaffolded
Feature specs: {N} specs available
API contract: {N} public symbols to implement

Project structure:
  {tree output of key files}

Next steps:
  cd {target-path}
  /code-forge:port @{protocol-path} --ref {ref-repo} --lang {lang}    Generate implementation plans
  /code-forge:impl {first-feature}                                      Start implementing
  /apcore-skills:sync --lang {lang},{ref-lang}                           Verify API consistency
```

## Coordination with Other Skills

- **After sdk:** Use `code-forge:port` to generate implementation plans for each feature
- **During implementation:** Use `code-forge:impl` to execute TDD tasks
- **After implementation:** Use `apcore-skills:sync` to verify cross-language consistency
- **Before release:** Use `apcore-skills:audit` for comprehensive check
- **For release:** Use `apcore-skills:release` for coordinated version bump
