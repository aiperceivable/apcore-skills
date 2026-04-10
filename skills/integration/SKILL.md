---
name: integration
description: >
  Bootstrap a new framework integration for apcore. Scaffolds the project with
  endpoint scanners, configuration system, context mapping, CLI commands, demo
  project, and Docker setup. Learns patterns from existing integrations
  (django-apcore, flask-apcore, nestjs-apcore).
---

# Apcore Skills — Integration

## ⚡ Execution Entry Point (READ THIS FIRST)

**When this skill is loaded, you MUST immediately begin executing the Workflow below — do not wait, do not summarize, do not ask "what should I do now". Skills are operational manuals, not reference documents.** Read the first executable step, perform it, then the next, etc., until the workflow completes or you reach an `AskUserQuestion` checkpoint.

If the harness shows you `Successfully loaded skill · N tools allowed`, that message means **the SKILL.md content was injected into your context** — it does NOT mean the skill has run. Skills do not "run" autonomously; you run them by executing the Detailed Steps below.

If you find yourself about to say "the skill didn't produce output", "skill 仍未输出", "falling back to manual bootstrap", "回退到手动 integration", or anything similar, **STOP**. You have misunderstood how skills work. Go directly to the first executable step and start.

The first user-visible action of this skill should be either (a) the output of the first step, or (b) an `AskUserQuestion` if the first step needs disambiguation. Never an apology, never a fallback, never silence.

---

Bootstrap a new framework integration that connects a web framework to the apcore ecosystem.

## Iron Law

**EVERY INTEGRATION MUST IMPLEMENT THE SAME 5 CORE CAPABILITIES: scan endpoints, register modules, map request context, serve via MCP, and export to OpenAI tools format.**

## Anti-Rationalization Table

| Thought | Reality |
|---------|---------|
| "This framework is different, it needs a different approach" | The 5 core capabilities are the same. Only the framework-specific adapters differ. |
| "I'll skip the demo project" | Demo projects are how users evaluate integrations. Always include one. |
| "CLI commands can come later" | CLI is the primary UX. `scan` and `serve` commands are required from day one. |
| "I'll just wrap the core SDK directly" | Integrations must use apcore-discovery for scanner logic to ensure consistency. |

## When to Use

- Creating a new framework integration (e.g., `fastapi-apcore`, `express-apcore`, `gin-apcore`)
- Re-scaffolding an existing integration that needs restructuring
- Evaluating what's needed for a new framework integration

## Command Format

```
/apcore-skills:integration <framework> [--lang python|typescript|go] [--ref django-apcore]
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `<framework>` | Yes | — | Target framework: `fastapi`, `express`, `gin`, `spring`, `actix`, etc. |
| `--lang` | No | auto-detect | Language of the framework |
| `--ref` | No | auto-detect | Reference integration to learn patterns from |

## 5 Core Capabilities

Every apcore framework integration must provide:

| # | Capability | Description | CLI Command |
|---|---|---|---|
| 1 | **Endpoint Scanner** | Discover framework routes and convert to apcore module definitions | `{framework} apcore scan` |
| 2 | **Module Registry** | Register scanned endpoints as apcore modules with metadata | (automatic) |
| 3 | **Context Mapping** | Map framework request objects to apcore `Context` | (automatic) |
| 4 | **MCP Server** | Start an MCP server exposing registered modules as tools | `{framework} apcore serve` |
| 5 | **OpenAI Export** | Export registered modules as OpenAI-compatible tool definitions | `{framework} apcore export` |

## Context Management

Steps 2 and 4 use sub-agents. Step 2 analyzes the reference integration. Step 4 generates the project skeleton. Main context retains only structured summaries.

## Workflow

```
Step 0 (ecosystem) → 1 (parse args) → 2 (analyze reference) → 3 (framework research) → 4 (scaffold) → 5 (demo project) → 6 (plan) → 7 (summary)
```

## Detailed Steps

### Step 0: Ecosystem Discovery

@../shared/ecosystem.md

---

### Step 1: Parse Arguments

Parse `$ARGUMENTS`:

1. Extract `<framework>` — required, use `AskUserQuestion` if missing
2. Extract `--lang` — auto-detect from framework:
   - Python frameworks: `fastapi`, `flask`, `django`, `starlette`, `falcon`, `tornado`
   - TypeScript frameworks: `express`, `fastify`, `nestjs`, `hono`, `koa`
   - Go frameworks: `gin`, `echo`, `fiber`, `chi`
   - Rust frameworks: `actix`, `axum`, `rocket`
   - Java frameworks: `spring`, `quarkus`, `micronaut`
   - PHP frameworks: `laravel`, `symfony`, `slim`, `lumen`
3. Extract `--ref` — resolve reference integration (priority order):
   - If `--ref` explicitly specified: use that
   - **If CWD is an existing integration repo** (e.g., in `django-apcore/`): use CWD repo as reference
   - Otherwise auto-detect: same-language integration preferred, fall back to any existing integration

Derive target repo name: `{framework}-apcore`
Derive target path: `{ecosystem_root}/{framework}-apcore/`

Display:
```
Integration Bootstrap:
  Framework:  {framework}
  Language:   {lang}
  Reference:  {ref-repo}
  Target:     {target-path}
```

---

### Step 2: Analyze Reference Integration (Sub-agent)

Spawn `Agent(subagent_type="general-purpose")`:

**Sub-agent prompt:**
```
Analyze the reference integration at {ref_path} to understand the pattern for apcore framework integrations.

Read the following key files:
1. Main extension/app file (extension.py, apps.py, or module entry)
2. Config file (config.py, settings.py) — extract all APCORE_* settings
3. Scanner directory (scanners/) — how framework endpoints are discovered
4. Context mapping (context.py) — how request → apcore Context works
5. Registry (registry.py) — how modules are registered
6. CLI commands (cli.py, management/) — what commands are available
7. Output writers (output/) — how bindings are written
8. README.md — for user-facing documentation patterns
9. examples/ or demo/ — demo project structure

Return a structured analysis:

INTEGRATION_PATTERN:
  framework: {framework}
  language: {lang}
  version: {version}

EXTENSION_MECHANISM:
  How the integration hooks into the framework: {description}
  Entry point: {file and class/function}

CONFIGURATION:
  Settings prefix: APCORE_
  Settings count: {N}
  Key settings:
    - {SETTING_NAME}: {type} = {default} — {description}

SCANNER_PATTERN:
  Scanner types: {list of scanner variants, e.g., DRF, django-ninja}
  How endpoints are discovered: {description}
  How params are extracted: {description}

CONTEXT_MAPPING:
  How framework request → apcore Context: {description}
  Authentication extraction: {description}

CLI_COMMANDS:
  - {command}: {description}

DEMO_STRUCTURE:
  - {file}: {purpose}

Error handling:
- If the reference repo path does not exist, return: STATUS: NOT_FOUND, REASON: "Reference integration not found at {path}"
- If expected directories (scanners/, output/) are missing, note them and analyze what IS available
- If config file not found, note it and continue with partial analysis
- If README.md is missing, skip documentation pattern analysis

Keep summary to ~3-4KB.
```

Store as `ref_analysis`. If sub-agent returns STATUS: NOT_FOUND, use `AskUserQuestion` to provide a different reference or proceed without reference (scaffold from conventions only).

---

### Step 3: Framework-Specific Research

Use `AskUserQuestion` to gather framework-specific information:

- Question 1: "Which {framework} routing mechanism should the scanner target?"
  - Options based on framework (e.g., for FastAPI: "Path operations (Recommended)" / "APIRouter" / "Both")
- Question 2: "Which authentication patterns should context mapping support?"
  - Options: "Bearer token (Recommended)" / "Session-based" / "Both" / "Custom"
- Question 3 (if framework has multiple API styles): "Which API definition style?"
  - Options depend on framework

Store `framework_config`.

---

### Step 4: Scaffold Project (Sub-agent)

@../shared/conventions.md (refer to "Framework Integration structure" section)

Spawn `Agent(subagent_type="general-purpose")`:

**Sub-agent prompt:**
```
Create the project skeleton for {framework}-apcore at {target-path}.

Language: {lang}
Framework: {framework}
Reference pattern: {ref_analysis summary}
Framework config: {framework_config}

## Required Structure

{target-path}/
├── {build-config}                           # pyproject.toml / package.json
├── .gitignore
├── README.md                                # Installation, Quick Start, Configuration, CLI
├── CHANGELOG.md
├── LICENSE                                  # Detect from ecosystem or ask user (MIT / Apache-2.0)
├── src/{package_name}/
│   ├── {main-module}                        # __init__.py / index.ts with public exports
│   ├── extension.{ext}                      # Framework integration entry point
│   │                                        # (or apps.py for Django-style)
│   ├── config.{ext}                         # APCORE_* configuration with all settings
│   │                                        # (include: ENABLED, DEBUG, SCANNERS, AUTH, TRANSPORT, etc.)
│   ├── registry.{ext}                       # Module registration from scanned endpoints
│   ├── context.{ext}                        # Request → apcore Context mapping
│   ├── scanners/
│   │   ├── {main-module}                    # Scanner exports
│   │   └── {framework-scanner}.{ext}        # Framework-specific endpoint scanner
│   ├── output/
│   │   ├── {main-module}
│   │   └── yaml_writer.{ext}               # YAML binding file writer
│   ├── cli.{ext}                            # CLI commands: scan, serve, export
│   └── observability.{ext}                  # Optional: framework-specific tracing
├── tests/
│   ├── {test-config}
│   ├── conftest.{ext}                       # Shared fixtures
│   ├── test_extension.{ext}
│   ├── test_config.{ext}
│   ├── test_scanner.{ext}
│   ├── test_context.{ext}
│   └── test_cli.{ext}
└── examples/
    └── demo/
        ├── {build-config}                   # Demo app build file
        ├── app.{ext}                        # Minimal framework app with sample endpoints
        ├── Dockerfile
        └── docker-compose.yml               # App + apcore-mcp server

## Implementation Requirements

1. **extension.{ext}**: Framework plugin/extension class that:
   - Initializes apcore Registry on startup
   - Runs scanner to discover endpoints
   - Registers discovered modules

2. **config.{ext}**: Configuration class with ALL standard APCORE_* settings:
   APCORE_ENABLED (bool, True)
   APCORE_DEBUG (bool, False)
   APCORE_SCANNERS (list, ["auto"])
   APCORE_INCLUDE_PATHS (list, [])
   APCORE_EXCLUDE_PATHS (list, [])
   APCORE_MODULE_PREFIX (str, "")
   APCORE_AUTH_ENABLED (bool, False)
   APCORE_AUTH_STRATEGY (str, "bearer")
   APCORE_TRANSPORT (str, "stdio")
   APCORE_HOST (str, "0.0.0.0")
   APCORE_PORT (int, 8808)
   {Add framework-specific settings}

3. **scanners/{scanner}.{ext}**: Scanner that:
   - Walks framework route table
   - Extracts: path, method, params (name, type, required, default), description
   - Converts to apcore module definitions
   - Respects include/exclude path patterns

4. **context.{ext}**: Context factory that:
   - Maps framework request → apcore Context
   - Extracts auth info (Bearer token, session, etc.)
   - Handles async/sync appropriately

5. **cli.{ext}**: Commands:
   - `scan` — Discover endpoints and display/write bindings
   - `serve` — Start MCP server with discovered modules
   - `export` — Export to OpenAI tools JSON format

All files should have proper stubs with TODO markers for implementation.

Naming conventions:
- Python: snake_case for functions/methods, PascalCase for classes
- TypeScript: camelCase for functions/methods, PascalCase for classes
- Go: PascalCase for public, camelCase for private
- Rust: snake_case for functions/methods, PascalCase for types
- Java: camelCase for methods, PascalCase for classes

Error handling:
- If {target-path} is not writable, return: STATUS: WRITE_ERROR, REASON: "{description}"
- If a file cannot be created, skip it and include in the return as "{file} (SKIPPED: {reason})"
- If the framework is not recognized, proceed with generic scaffold and note: "Unknown framework — used generic pattern"

Create ALL files listed. Return file list.
```

Verify after sub-agent:
- Build config exists
- At least scanner, config, extension, context, cli files exist
- Tests directory has test files
- Examples/demo directory exists

---

### Step 5: Generate Demo Project

If demo directory wasn't fully created by Step 4, create it:

Write a minimal demo app that:
1. Creates a {framework} app with 3-5 sample CRUD endpoints
2. Integrates apcore via the extension
3. Includes `docker-compose.yml` with:
   - App service
   - Optional: MCP server service (using apcore-mcp)
4. Includes `README.md` with setup instructions

---

### Step 6: Generate Code-Forge Config and Feature Specs

Write `.code-forge.json` and generate feature specs for code-forge planning:

Feature specs to generate (one per core capability):
1. `scanner.md` — Endpoint scanning for this framework
2. `config.md` — Configuration system
3. `context.md` — Request-to-context mapping
4. `registry.md` — Module registration
5. `cli.md` — CLI commands (scan, serve, export)
6. `observability.md` — Framework-specific tracing (optional)

Write to `{target-path}/docs/features/`.

Initialize git and create the skeleton commit automatically:

```bash
cd {target-path}
git init
git add .
git commit -m "chore: initialize {framework}-apcore project skeleton"
```

Display:
```
Git initialized with skeleton commit.
```

---

### Step 7: Display Summary and Next Steps

```
apcore-skills:integration — Integration Bootstrap Complete

Target: {target-path}
Framework: {framework} ({lang})
Source files: {N} scaffolded
Test files: {N} scaffolded
Feature specs: {N} generated
Demo project: examples/demo/

Core Capabilities:
  [stub] Endpoint Scanner     — scanners/{scanner}.{ext}
  [stub] Module Registry      — registry.{ext}
  [stub] Context Mapping      — context.{ext}
  [stub] MCP Server           — cli.{ext} (serve command)
  [stub] OpenAI Export        — cli.{ext} (export command)

Configuration: {N} APCORE_* settings defined

Next steps:
  cd {target-path}
  /code-forge:plan @docs/features/scanner.md       Plan scanner implementation
  /code-forge:impl scanner                          Implement scanner
  /apcore-skills:sync                                Verify consistency with other integrations
```

## Coordination with Other Skills

- **After integration:** Use `code-forge:plan` per feature spec to plan implementation
- **During implementation:** Use `code-forge:impl` to execute TDD tasks
- **After each feature:** Use `code-forge:review` to review quality
- **Cross-integration consistency:** Use `apcore-skills:audit --scope integrations`
- **For release:** Use `apcore-skills:release` (integration versions are independent)
