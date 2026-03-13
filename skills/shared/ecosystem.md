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

**Other project types** (A2A bridges, toolkits, and future types follow the `apcore-{type}-{lang}` pattern):
| Directory Pattern | Repo Type | Language | Package Name |
|---|---|---|---|
| `apcore-{type}-{lang}/` | `{type}` | `{lang}` | `apcore-{type}` |

**Match priority:** Specific patterns (core-sdk, mcp-bridge, shared-lib, integration, docs-site, placeholder) are checked first. The `apcore-{type}-{lang}` wildcard is a fallback for repos that don't match any specific pattern.

**Framework Integrations:**
| Directory Pattern | Repo Type | Language | Framework |
|---|---|---|---|
| `django-apcore/` | `integration` | Python | Django |
| `flask-apcore/` | `integration` | Python | Flask |
| `nestjs-apcore/` | `integration` | TypeScript | NestJS |
| `tiptap-apcore/` | `integration` | TypeScript | TipTap |
| `{framework}-apcore/` | `integration` | varies | `{framework}` |

**Shared Libraries:**
| Directory Pattern | Repo Type | Language |
|---|---|---|
| `apcore-discovery-python/` | `shared-lib` | Python |

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
| `express-apcore/` | `integration` | Placeholder — matched by `{framework}-apcore/` wildcard when ready |
| `apcore-studio/` | `tooling` | Placeholder |

**Exclude from ecosystem scans** (not apcore SDK/integration repos):
- `aphub*`, `apflow*`, `apdev*`, `aipartnerup-website/` — separate product lines, not part of apcore SDK ecosystem

For each discovered directory:
1. Check if it contains a valid project (has `pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`, `pom.xml`, `build.gradle`, `build.gradle.kts`, `composer.json`, `mix.exs`, `Package.swift`, or `*.csproj`)
2. Skip `docs-site` type repos (no build config, only `mkdocs.yml` or markdown files)
3. Flag `placeholder` repos (directory exists but no source files — report as "empty/placeholder")
4. Extract version from the build config file
5. Detect language from build config
6. Check git status (clean / dirty / uncommitted changes)

Store `repos[]` — list of discovered repository objects with: `name`, `path`, `type`, `language`, `version`, `package_name`, `git_status`.

#### 0.3 Detect CWD Repo

Determine `cwd_repo` — the repo the user is currently working in:
1. Get CWD basename (e.g., `apcore-python`)
2. Match against `repos[]` by name
3. If matched, store `cwd_repo = { name, type, language, scope_group }`:
   - `core-sdk` → `scope_group = "core"`
   - `mcp-bridge` → `scope_group = "mcp"`
   - `a2a-bridge` → `scope_group = "a2a"`
   - `toolkit` → `scope_group = "toolkit"`
   - `integration` → `scope_group = "integrations"`
   - `protocol` / `docs-site` → `scope_group = "docs"`
   - `shared-lib` → `scope_group = "shared"`
   - `tooling` → `scope_group = "tooling"`
   - Other `apcore-{type}-{lang}` patterns → `scope_group = "{type}"`
4. If not matched, `cwd_repo = null`

This is used by sync, audit, and release as the **default scope** when `--scope` is not specified. If `cwd_repo` is null (CWD is not an apcore repo), each skill should use `AskUserQuestion` to let the user pick a target repo instead of silently scanning everything.

#### 0.4 Load Configuration

Load configuration by priority (deep-merge):

1. **System defaults:**
   - `ecosystem_root` = detected root
   - `protocol_repo` = `"apcore"`
   - `reference_sdk.python` = `"apcore-python"`
   - `reference_sdk.typescript` = `"apcore-typescript"`
   - `reference_mcp.python` = `"apcore-mcp-python"`
   - `reference_mcp.typescript` = `"apcore-mcp-typescript"`
   - `version_groups.core` = auto-populated from all discovered `core-sdk` repos (e.g., `["apcore-python", "apcore-typescript", "apcore-rust", ...]`)
   - `version_groups.mcp` = auto-populated from all discovered `mcp-bridge` repos (e.g., `["apcore-mcp-python", "apcore-mcp-typescript", ...]`)
   - Other `version_groups.{type}` are auto-populated from discovered `apcore-{type}-{lang}` repos

2. **User global config** (`~/.apcore-skills.json`, if exists) → deep-merge

3. **Project config** (`<ecosystem_root>/.apcore-skills.json`, if exists) → deep-merge

#### 0.5 Version Extraction Rules

| File | Version Location |
|---|---|
| `pyproject.toml` | `[project] version = "X.Y.Z"` |
| `package.json` | `"version": "X.Y.Z"` |
| `Cargo.toml` | `[package] version = "X.Y.Z"` |
| `go.mod` | Tag-based (check `git tag -l 'v*'` for latest) |
| `pom.xml` | `<version>X.Y.Z</version>` |
| `build.gradle` | `version = 'X.Y.Z'` or `version 'X.Y.Z'` |
| `build.gradle.kts` | `version = "X.Y.Z"` |
| `mix.exs` | `version: "X.Y.Z"` in `project/0` |
| `Package.swift` | Version constant or git tag-based |
| `*.csproj` | `<Version>X.Y.Z</Version>` |
| `composer.json` | `"version": "X.Y.Z"` |
| `__init__.py` / `_version.py` | `__version__ = "X.Y.Z"` |
| `src/*/index.ts` | `export const VERSION = "X.Y.Z"` |

For Python projects, also check `src/*/__init__.py` for `__version__`.

#### 0.6 Display Discovery Summary

```
apcore-skills — Ecosystem Dashboard

Ecosystem root: /path/to/aipartnerup/
Repos discovered: {count}

  Type          | Repo                    | Lang       | Version | Status
  protocol      | apcore                  | —          | —       | clean
  core-sdk      | apcore-python           | Python     | 0.7.0   | clean
  core-sdk      | apcore-typescript       | TypeScript | 0.7.1   | dirty
  core-sdk      | apcore-rust             | Rust       | 0.1.0   | clean
  mcp-bridge    | apcore-mcp-python       | Python     | 0.8.1   | clean
  mcp-bridge    | apcore-mcp-typescript   | TypeScript | 0.8.1   | clean
  integration   | django-apcore           | Python     | 0.2.0   | clean
  integration   | flask-apcore            | Python     | 0.3.0   | clean
  integration   | nestjs-apcore           | TypeScript | 0.1.0   | clean
  integration   | tiptap-apcore           | TypeScript | 0.1.0   | clean
  shared-lib    | apcore-discovery-python | Python     | —       | clean
```

#### 0.7 Store Ecosystem Context

Track resolved values for subsequent steps:
- `config` — final merged configuration object
- `ecosystem_root` — absolute path
- `repos[]` — discovered repositories with metadata
- `protocol_path` — path to apcore protocol repo
- `repos_by_type{}` — repos grouped by type (core-sdk, mcp-bridge, a2a-bridge, toolkit, integration, etc.)
- `core_sdks[]` — shortcut for repos_by_type["core-sdk"]
- `mcp_bridges[]` — shortcut for repos_by_type["mcp-bridge"]
- `integrations[]` — shortcut for repos_by_type["integration"]
