### Step 0: Ecosystem Discovery and Configuration

**Important:** Detect the ecosystem layout before any operation.

#### 0.1 Detect Ecosystem Root

Search for the ecosystem root by looking for the `apcore` protocol specification repo. Search strategy:

1. Check current directory for `.apcore-skills.json` — if found, read `ecosystem_root` from it
2. Search upward from the current directory, checking each ancestor directory for an `apcore/` subdirectory containing `PROTOCOL_SPEC.md`. Continue until the filesystem root is reached or a match is found.
3. If not found: use `AskUserQuestion` to ask for ecosystem root path

Store `ecosystem_root` — the parent directory containing all apcore repos.

#### 0.2 Discover Repositories

Scan `ecosystem_root` for known repository patterns:

**Core Protocol:**
| Directory Pattern | Repo Type | Role |
|---|---|---|
| `apcore/` | `protocol` | Protocol specification and docs (reference authority) |

**Core SDKs:**
| Directory Pattern | Repo Type | Language | Package Name |
|---|---|---|---|
| `apcore-python/` | `core-sdk` | Python | `apcore` |
| `apcore-typescript/` | `core-sdk` | TypeScript | `apcore-js` |
| `apcore-{lang}/` | `core-sdk` | `{lang}` | varies |

**MCP Bridges:**
| Directory Pattern | Repo Type | Language | Package Name |
|---|---|---|---|
| `apcore-mcp-python/` | `mcp-bridge` | Python | `apcore-mcp` |
| `apcore-mcp-typescript/` | `mcp-bridge` | TypeScript | `apcore-mcp` |
| `apcore-mcp-{lang}/` | `mcp-bridge` | `{lang}` | varies |

**Framework Integrations:**
| Directory Pattern | Repo Type | Language | Framework |
|---|---|---|---|
| `django-apcore/` | `integration` | Python | Django |
| `flask-apcore/` | `integration` | Python | Flask |
| `nestjs-apcore/` | `integration` | TypeScript | NestJS |
| `tiptap-apcore/` | `integration` | TypeScript | TipTap |
| `express-apcore/` | `integration` | TypeScript | Express |
| `{framework}-apcore/` | `integration` | varies | `{framework}` |

**Shared Libraries:**
| Directory Pattern | Repo Type | Language |
|---|---|---|
| `apcore-discovery-python/` | `shared-lib` | Python |
| `apcore-toolkit-python/` | `shared-lib` | Python |

**Documentation Sites:**
| Directory Pattern | Repo Type | Description |
|---|---|---|
| `apcore-mcp/` (with `mkdocs.yml`, no `src/`) | `docs-site` | MCP documentation site |
| `apcore-zh/` | `docs-site` | Chinese localization of apcore docs |
| `aipartnerup-docs/` | `docs-site` | Organization-level documentation |

**Placeholder/Early-stage:**
| Directory Pattern | Repo Type | Status |
|---|---|---|
| `comfyui-apcore/` | `integration` | Early stage (may have only `ideas/` dir) |
| `express-apcore/` | `integration` | Placeholder (may be empty) |
| `apcore-studio/` | `tooling` | Placeholder |

**Exclude from ecosystem scans** (not apcore SDK/integration repos):
- `aphub*`, `apflow*`, `apdev*`, `aipartnerup-website/` — separate product lines, not part of apcore SDK ecosystem

For each discovered directory:
1. Check if it contains a valid project (has `pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`, `pom.xml`, `build.gradle`, `mix.exs`, `Package.swift`, or `*.csproj`)
2. Skip `docs-site` type repos (no build config, only `mkdocs.yml` or markdown files)
3. Flag `placeholder` repos (directory exists but no source files — report as "empty/placeholder")
4. Extract version from the build config file
5. Detect language from build config
6. Check git status (clean / dirty / uncommitted changes)

Store `repos[]` — list of discovered repository objects with: `name`, `path`, `type`, `language`, `version`, `package_name`, `git_status`.

#### 0.3 Load Configuration

Load configuration by priority (deep-merge):

1. **System defaults:**
   - `ecosystem_root` = detected root
   - `protocol_repo` = `"apcore"`
   - `reference_sdk.python` = `"apcore-python"`
   - `reference_sdk.typescript` = `"apcore-typescript"`
   - `reference_mcp.python` = `"apcore-mcp-python"`
   - `reference_mcp.typescript` = `"apcore-mcp-typescript"`
   - `version_groups.core` = `["apcore-python", "apcore-typescript"]`
   - `version_groups.mcp` = `["apcore-mcp-python", "apcore-mcp-typescript"]`

2. **User global config** (`~/.apcore-skills.json`, if exists) → deep-merge

3. **Project config** (`<ecosystem_root>/.apcore-skills.json`, if exists) → deep-merge

#### 0.4 Version Extraction Rules

| File | Version Location |
|---|---|
| `pyproject.toml` | `[project] version = "X.Y.Z"` |
| `package.json` | `"version": "X.Y.Z"` |
| `Cargo.toml` | `[package] version = "X.Y.Z"` |
| `go.mod` | Tag-based (check git tags) |
| `pom.xml` | `<version>X.Y.Z</version>` |
| `__init__.py` / `_version.py` | `__version__ = "X.Y.Z"` |
| `src/*/index.ts` | `export const VERSION = "X.Y.Z"` |

For Python projects, also check `src/*/__init__.py` for `__version__`.

#### 0.5 Display Discovery Summary

```
apcore-skills — Ecosystem Dashboard

Ecosystem root: /path/to/aipartnerup/
Repos discovered: {count}

  Type          | Repo                    | Lang       | Version | Status
  protocol      | apcore                  | —          | —       | clean
  core-sdk      | apcore-python           | Python     | 0.7.0   | clean
  core-sdk      | apcore-typescript       | TypeScript | 0.7.1   | dirty
  mcp-bridge    | apcore-mcp-python       | Python     | 0.8.1   | clean
  mcp-bridge    | apcore-mcp-typescript   | TypeScript | 0.8.1   | clean
  integration   | django-apcore           | Python     | 0.2.0   | clean
  integration   | flask-apcore            | Python     | 0.3.0   | clean
  integration   | nestjs-apcore           | TypeScript | 0.1.0   | clean
  integration   | tiptap-apcore           | TypeScript | 0.1.0   | clean
  shared-lib    | apcore-discovery-python | Python     | —       | clean
```

#### 0.6 Store Ecosystem Context

Track resolved values for subsequent steps:
- `config` — final merged configuration object
- `ecosystem_root` — absolute path
- `repos[]` — discovered repositories with metadata
- `protocol_path` — path to apcore protocol repo
- `core_sdks[]` — core SDK repos (for sync operations)
- `mcp_bridges[]` — MCP bridge repos (for sync operations)
- `integrations[]` — framework integration repos
