### Apcore Ecosystem Conventions

<!-- CONVENTIONS-LOADED -->


Canonical conventions that all apcore repositories must follow. Used by audit, sync, and scaffolding skills.

#### Version Synchronization Rules

For each configured `version_groups` entry, package versions must agree on
major.minor. Discovery creates default groups for Core, MCP, A2A, and CLI as
defined in [shared discovery §0.4](ecosystem.md#04-load-configuration). Toolkit
packages are checked individually by D3 by default. Framework integrations
follow their own release cadence.

Cross-language API and behavioral comparisons group packages by shared
`spec_root`, including Toolkit.

**Version files per language:**

| Language | Files to update |
|---|---|
| Python | `pyproject.toml` → `[project] version`, `src/*/__init__.py` → `__version__` |
| TypeScript | `package.json` → `"version"`, `src/index.ts` → `VERSION` constant (if present) |
| Go | Version from the configured package tag, e.g. `mcp/go/v1.2.3` |
| Rust | `Cargo.toml` → `[package] version` |
| Java | `pom.xml` → `<version>`, or `build.gradle` → `version` |

#### Naming Conventions

**Target IDs and checkout paths:**

| Target | ID | Path relative to the ecosystem root |
|---|---|---|
| Core SDK | `apcore-<lang>` | `apcore/<lang>/` |
| MCP, A2A, CLI, Toolkit | `apcore-<component>-<lang>` | `apcore-surfaces/<component>/<lang>/` |
| Framework integration | `<framework>-apcore` | `<framework>-apcore/` |

**Package naming:**

Surface package names use `apcore-{type}`. Published names come from the local
package manifest.

| Language | Core SDK | Other types (e.g., mcp, a2a, toolkit) | Integration |
|---|---|---|---|
| Python (PyPI) | `apcore` | `apcore-{type}` | `{framework}-apcore` |
| TypeScript (npm) | `apcore-js` | `apcore-{type}` | `{framework}-apcore` |
| Rust (crates) | `apcore` | `apcore-{type}` | — |

**Code naming (cross-language canonical forms):**

All public API names originate from the protocol spec. When implementing in a language, apply that language's convention:

| Canonical (snake_case) | Python | TypeScript | Go | Rust | Java | C# | Kotlin | Swift | PHP |
|---|---|---|---|---|---|---|---|---|---|
| `module_id` | `module_id` | `moduleId` | `ModuleID` / `moduleID` | `module_id` | `moduleId` | `ModuleId` | `moduleId` | `moduleId` | `$moduleId` |
| `get_module` | `get_module` | `getModule` | `GetModule` | `get_module` | `getModule` | `GetModule` | `getModule` | `getModule` | `getModule` |
| `execute_module` | `execute_module` | `executeModule` | `ExecuteModule` | `execute_module` | `executeModule` | `ExecuteModule` | `executeModule` | `executeModule` | `executeModule` |
| `ErrorCode` | `ErrorCode` | `ErrorCode` | `ErrorCode` | `ErrorCode` | `ErrorCode` | `ErrorCode` | `ErrorCode` | `ErrorCode` | `ErrorCode` |
| `BINDING_NOT_FOUND` | `BINDING_NOT_FOUND` | `BINDING_NOT_FOUND` | `ErrBindingNotFound` | `BINDING_NOT_FOUND` | `BINDING_NOT_FOUND` | `BindingNotFound` | `BINDING_NOT_FOUND` | `bindingNotFound` | `BINDING_NOT_FOUND` |

#### Project Structure Convention

The structures below illustrate typical package layouts. Follow the selected
reference implementation and the target language's conventions when scaffolding.
Core and Surface packages keep shared feature specs and fixtures under their
component's `spec_root`.

**Core SDK structure:**
```
apcore/<lang>/
├── src/                     # or language-appropriate source dir
│   ├── {main module}        # __init__.py / index.ts / lib.rs / main.go
│   ├── executor.{ext}
│   ├── context.{ext}
│   ├── module.{ext}
│   ├── config.{ext}
│   ├── errors.{ext}
│   ├── acl.{ext}
│   ├── approval.{ext}
│   ├── async_task.{ext}     # or async-task.{ext} for TS
│   ├── bindings.{ext}
│   ├── decorator.{ext}
│   ├── extensions.{ext}
│   ├── cancel.{ext}                # cancellation support
│   ├── trace_context.{ext}         # or trace-context.{ext} for TS
│   ├── middleware/
│   ├── registry/
│   ├── schema/
│   ├── observability/
│   └── utils/
├── tests/                   # one test file per source module + subdirs
│   ├── {test-config}        # pytest.ini / vitest.config / test runner config
│   ├── {helpers}            # conftest.py / helpers.ts — shared fixtures
│   ├── integration/         # cross-component integration tests
│   ├── registry/            # registry-specific tests
│   ├── schema/              # schema validation tests
│   └── observability/       # metrics, tracing, logging tests
├── examples/                # runnable usage examples
│   ├── simple_client.{ext}  # basic executor + module + execute flow
│   ├── bindings/            # binding module examples with YAML config
│   └── modules/             # decorator-based module examples
├── docs/                    # optional language-specific docs
├── {build-config}           # pyproject.toml / package.json / go.mod / Cargo.toml
├── .unirelease.toml
├── README.md
├── CHANGELOG.md
├── LICENSE
└── .gitignore
```

**MCP Bridge structure:**
```
apcore-surfaces/mcp/<lang>/
├── src/
│   ├── {main module}
│   ├── server/              # factory, listener, router, transport
│   ├── auth/                # JWT, claims mapping
│   ├── adapters/            # annotations, approval, errors, schema
│   ├── converters/          # OpenAI format export
│   ├── cli.{ext}            # CLI entry point
│   └── explorer/            # optional: web UI
├── tests/                   # mirrors src/ structure + integration tests
│   ├── {test-config}
│   ├── {helpers}            # shared fixtures
│   ├── server/              # server implementation tests
│   ├── auth/                # auth middleware tests
│   ├── adapters/            # adapter tests
│   ├── converters/          # converter tests
│   └── explorer/            # explorer tests
├── examples/                # runnable MCP server examples
│   ├── run.{ext}            # start server with example extensions
│   ├── README.md            # setup and usage instructions
│   ├── extensions/          # example extensions (greeting, math, text)
│   └── binding_demo/        # YAML-based extension registration
├── {build-config}
├── .unirelease.toml
├── README.md
├── CHANGELOG.md
└── LICENSE
```

**A2A Bridge structure:**
```
apcore-surfaces/a2a/<lang>/
├── src/
│   ├── {main module}
│   ├── server/              # factory, executor, router, streaming, task manager
│   ├── auth/                # JWT, middleware, protocol
│   ├── adapters/            # agent card, skill mapper, schema/error/part converters
│   ├── client/              # A2A client, card fetcher
│   ├── storage/             # task storage (memory, protocol)
│   ├── cli.{ext}            # CLI entry point
│   └── explorer/            # optional: web UI
├── tests/                   # mirrors src/ structure + integration tests
│   ├── {test-config}
│   ├── {helpers}            # shared fixtures
│   ├── server/              # server tests (executor, factory, router, streaming, task manager)
│   ├── auth/                # auth tests (JWT, middleware)
│   ├── adapters/            # adapter tests (agent card, skill mapper, schema, errors, parts)
│   ├── client/              # client tests
│   ├── storage/             # storage tests
│   └── explorer/            # explorer tests
├── examples/                # runnable A2A server examples
│   ├── run.{ext}            # start server with example extensions
│   ├── README.md            # setup and usage instructions
│   ├── extensions/          # example extensions (greeting, math, text)
│   └── binding_demo/        # binding configuration examples
├── {build-config}
├── .unirelease.toml
├── README.md
├── CHANGELOG.md
└── LICENSE
```

**Toolkit structure:**
```
apcore-surfaces/toolkit/<lang>/
├── src/
│   ├── {main module}
│   ├── scanner.{ext}        # base scanner interface
│   ├── types.{ext}          # shared types (ScannedModule, WriteResult)
│   ├── schema_utils.{ext}   # schema enrichment utilities
│   ├── serializers.{ext}    # module serialization
│   ├── ai_enhancer.{ext}    # AI-powered schema description enrichment
│   ├── openapi.{ext}        # OpenAPI spec parsing
│   ├── formatting/          # output formatters
│   │   └── markdown.{ext}
│   └── output/              # writers and verifiers
│       ├── factory.{ext}
│       ├── {lang}_writer.{ext}
│       ├── yaml_writer.{ext}
│       ├── registry_writer.{ext}
│       ├── verifiers.{ext}
│       ├── types.{ext}
│       └── errors.{ext}
├── tests/                   # one test file per source module
│   ├── {test-config}
│   ├── {helpers}
│   ├── {test-scanner}
│   ├── {test-types}
│   ├── {test-schema-utils}
│   ├── {test-serializers}
│   ├── {test-ai-enhancer}
│   ├── {test-openapi}
│   ├── {test-markdown}
│   ├── {test-yaml-writer}
│   ├── {test-lang-writer}
│   ├── {test-registry-writer}
│   ├── {test-verifiers}
│   └── {test-output-factory}
├── {build-config}
├── .unirelease.toml
├── README.md
├── CHANGELOG.md
└── LICENSE
```

**Framework Integration structure:**
```
{framework}-apcore/
├── src/
│   ├── {main module}
│   ├── extension.{ext}     # or apps.py for Django
│   ├── config.{ext}        # APCORE_* settings
│   ├── registry.{ext}      # module discovery
│   ├── context.{ext}       # request → apcore context mapping
│   ├── scanners/            # framework-specific endpoint scanners
│   ├── output/              # binding writers
│   ├── cli.{ext}            # management commands
│   └── observability.{ext}  # optional: framework-specific tracing
├── tests/
├── examples/                # demo project with Docker
├── {build-config}
├── README.md
├── CHANGELOG.md
└── LICENSE
```

#### Framework Integration Configuration (`APCORE_*`)

All framework integrations MUST implement these settings with identical names, types, and default values. audit D7 enforces this. New settings that are truly framework-specific use the prefix `APCORE_{FRAMEWORK}_*` (e.g., `APCORE_FASTAPI_ROUTE_PREFIX`), never bare `APCORE_*`.

| Setting | Type | Default | Purpose |
|---|---|---|---|
| `APCORE_ENABLED` | bool | `True` | Master switch |
| `APCORE_DEBUG` | bool | `False` | Verbose logging / introspection |
| `APCORE_SCANNERS` | list[str] | `["auto"]` | Enabled scanner identifiers |
| `APCORE_INCLUDE_PATHS` | list[str] | `[]` | Route patterns to include (empty = all) |
| `APCORE_EXCLUDE_PATHS` | list[str] | `[]` | Route patterns to exclude |
| `APCORE_MODULE_PREFIX` | str | `""` | Prefix prepended to generated module ids |
| `APCORE_AUTH_ENABLED` | bool | `False` | Require auth for MCP/A2A endpoints |
| `APCORE_AUTH_STRATEGY` | str | `"bearer"` | `bearer` / `session` / `custom` |
| `APCORE_TRANSPORT` | str | `"stdio"` | MCP transport: `stdio` / `http` / `sse` |
| `APCORE_HOST` | str | `"0.0.0.0"` | Bind address when transport is not stdio |
| `APCORE_PORT` | int | `8808` | Bind port when transport is not stdio |

Defaults are authoritative: changing a default in one integration (e.g., `APCORE_PORT = 9000`) without changing it here is an audit D7 critical finding.

#### Git Conventions

- **Commit format:** Conventional Commits — `feat|fix|docs|style|refactor|perf|test|chore|ci(scope): message`
- **Scope examples:** `core`, `registry`, `schema`, `acl`, `middleware`, `mcp`, `auth`, `scanner`
- **Branch naming:** `feat/{feature}`, `fix/{issue}`, `release/v{X.Y.Z}`
- **Tag format:** Append `X.Y.Z` to the package's `release_tag_prefix` from `.unirelease.toml`, e.g. `core/python/v0.34.0` or `mcp/rust/v0.24.0`. Independent checkouts default to the prefix `v`.
- **Go module tags:** Use the module directory relative to the owning Git checkout followed by `/v`, e.g. `go/v1.2.3` for Core or `mcp/go/v1.2.3` for MCP. Derive the module path from the owning remote and the same relative directory.

#### Testing Conventions

| Language | Framework | Command | Coverage Target |
|---|---|---|---|
| Python | pytest + pytest-asyncio | `pytest --cov` | 90%+ |
| TypeScript | vitest | `pnpm exec vitest run --coverage` in monorepo packages | 90%+ |
| Go | testing | `go test -cover ./...` | 80%+ |
| Rust | cargo test | `cargo test` + `cargo tarpaulin` | 80%+ |
| Java | JUnit 5 | `mvn test` / `gradle test` | 80%+ |

#### Documentation Conventions

- **README.md:** Must include: badge (version, coverage), installation, quick start, API overview, link to full docs
- **CHANGELOG.md:** Keep a Changelog format, grouped by version, categories: Added, Changed, Fixed, Breaking
- **API docs:** Inline docstrings/JSDoc, auto-generated reference where possible
- **Specification reference:** Link to the target's discovered `spec_root`. Link to `apcore/PROTOCOL_SPEC.md` for Core definitions.

#### Dependency Conventions

**General rule:** All non-core project types depend on the published Core SDK for
their language. Protocol-specific types also depend on the relevant protocol SDK.

**Core SDKs** — no external SDK dependencies:
- Schema validation: Pydantic (Python), TypeBox (TypeScript)
- YAML parsing: PyYAML (Python), js-yaml (TypeScript)

**Protocol bridge types** (mcp, a2a, etc.) — core SDK + protocol SDK:
- MCP: `mcp` (Python), `@modelcontextprotocol/sdk` (TypeScript)
- A2A: `a2a-sdk` (Python), `a2a-sdk` (TypeScript)
- JWT (common for bridges): `pyjwt` (Python), `jsonwebtoken` (TypeScript)

**Utility types** (toolkit, etc.) — core SDK + domain libraries:
- Schema: Pydantic (Python), TypeBox (TypeScript)
- YAML: PyYAML (Python), js-yaml (TypeScript)

**Integrations** — core SDK + target framework:
- Their respective MCP bridge (optional)
- `apcore-discovery-{lang}` (if shared scanner utils exist)
