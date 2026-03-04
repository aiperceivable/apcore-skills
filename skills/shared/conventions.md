### Apcore Ecosystem Conventions

Canonical conventions that all apcore repositories must follow. Used by audit, sync, and scaffolding skills.

#### Version Synchronization Rules

**Sync Groups** — versions within a group MUST match (major.minor):

| Group | Repos | Rationale |
|---|---|---|
| `core` | apcore-python, apcore-typescript, (future core SDKs) | Same protocol, same API surface |
| `mcp` | apcore-mcp-python, apcore-mcp-typescript, (future MCP bridges) | Same MCP contract |

**Integration versions** are independent — they follow their own release cadence.

**Version files per language:**

| Language | Files to update |
|---|---|
| Python | `pyproject.toml` → `[project] version`, `src/*/__init__.py` → `__version__` |
| TypeScript | `package.json` → `"version"`, `src/index.ts` → `VERSION` constant (if present) |
| Go | `go.mod` (no version), use git tags `v{X.Y.Z}` |
| Rust | `Cargo.toml` → `[package] version` |
| Java | `pom.xml` → `<version>`, or `build.gradle` → `version` |

#### Naming Conventions

**Repository naming:**
- Core SDKs: `apcore-{language}` (e.g., `apcore-python`, `apcore-go`, `apcore-java`)
- MCP bridges: `apcore-mcp-{language}` (e.g., `apcore-mcp-python`, `apcore-mcp-go`)
- Framework integrations: `{framework}-apcore` (e.g., `django-apcore`, `flask-apcore`, `nestjs-apcore`)
- Shared libraries: `apcore-{purpose}-{language}` (e.g., `apcore-discovery-python`)

**Package naming:**
| Language | Core SDK | MCP Bridge | Integration |
|---|---|---|---|
| Python (PyPI) | `apcore` | `apcore-mcp` | `{framework}-apcore` |
| TypeScript (npm) | `apcore-js` | `apcore-mcp` | `{framework}-apcore` |
| Go (module) | `github.com/aipartnerup/apcore-go` | `github.com/aipartnerup/apcore-mcp-go` | — |
| Rust (crates) | `apcore` | `apcore-mcp` | — |
| Java (Maven) | `com.aipartnerup:apcore` | `com.aipartnerup:apcore-mcp` | — |

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

**Core SDK structure:**
```
apcore-{lang}/
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
├── tests/
├── docs/
├── {build-config}           # pyproject.toml / package.json / go.mod / Cargo.toml
├── README.md
├── CHANGELOG.md
├── LICENSE
└── .gitignore
```

**MCP Bridge structure:**
```
apcore-mcp-{lang}/
├── src/
│   ├── {main module}
│   ├── server/              # factory, listener, router, transport
│   ├── auth/                # JWT, claims mapping
│   ├── adapters/            # annotations, approval, errors, schema
│   ├── converters/          # OpenAI format export
│   ├── cli.{ext}            # CLI entry point
│   └── explorer/            # optional: web UI
├── tests/
├── {build-config}
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

#### Git Conventions

- **Commit format:** Conventional Commits — `feat|fix|docs|style|refactor|perf|test|chore|ci(scope): message`
- **Scope examples:** `core`, `registry`, `schema`, `acl`, `middleware`, `mcp`, `auth`, `scanner`
- **Branch naming:** `feat/{feature}`, `fix/{issue}`, `release/v{X.Y.Z}`
- **Tag format:** `v{X.Y.Z}` (e.g., `v0.8.0`)

#### Testing Conventions

| Language | Framework | Command | Coverage Target |
|---|---|---|---|
| Python | pytest + pytest-asyncio | `pytest --cov` | 90%+ |
| TypeScript | vitest | `npx vitest run --coverage` | 90%+ |
| Go | testing | `go test -cover ./...` | 80%+ |
| Rust | cargo test | `cargo test` + `cargo tarpaulin` | 80%+ |
| Java | JUnit 5 | `mvn test` / `gradle test` | 80%+ |

#### Documentation Conventions

- **README.md:** Must include: badge (version, coverage), installation, quick start, API overview, link to full docs
- **CHANGELOG.md:** Keep a Changelog format, grouped by version, categories: Added, Changed, Fixed, Breaking
- **API docs:** Inline docstrings/JSDoc, auto-generated reference where possible
- **Protocol reference:** Always link back to `apcore/PROTOCOL_SPEC.md` for authoritative definitions

#### Dependency Conventions

**Core SDKs depend on:**
- Schema validation: Pydantic (Python), TypeBox (TypeScript)
- YAML parsing: PyYAML (Python), js-yaml (TypeScript)
- No framework dependencies

**MCP Bridges depend on:**
- Their respective core SDK
- MCP SDK: `mcp` (Python), `@modelcontextprotocol/sdk` (TypeScript)
- JWT: `pyjwt` (Python), `jsonwebtoken` (TypeScript)

**Integrations depend on:**
- Their respective core SDK
- Their respective MCP bridge (optional)
- The target framework
- `apcore-discovery-{lang}` (if shared scanner utils exist)
