### Step 0: Ecosystem Discovery and Configuration

**Important:** Detect the ecosystem layout before any operation.

> **Fast path (preferred).** Run the bundled discovery script instead of reading
> build files in-context:
>
> ```
> python3 <scripts_dir>/discover.py [--root <ecosystem_root>]
> ```
>
> **Locating `<scripts_dir>`** — `discover.py` is bundled with apcore-skills
> beside this file under `shared/scripts/`, NOT in the user's project (the CWD is
> the ecosystem to *scan*, never where the script lives). Resolve per platform:
> - **Claude Code:** `$CLAUDE_PLUGIN_ROOT/skills/shared/scripts`.
> - **Codex / bundled:** `shared/scripts/` resolved relative to this skill (the
>   bundler rewrites this to the in-bundle path).
> - **Cannot resolve it, or no Python?** Skip to the markdown rules below — they
>   are the authoritative fallback. Never block on the script.
>
> Omit `--root` to auto-detect the ecosystem by searching upward from the real CWD
> (the user's location) — the intended behavior.
>
> It emits a JSON object with `ecosystem_root`, `repos[]` (each with `name`,
> `path`, `type`, `language`, `version`, `package_name`, `git_status`, `status`),
> `repos_by_type`, `version_groups`, `cwd_repo`, and the `core_sdks` /
> `mcp_bridges` / `integrations` shortcuts — exactly the values §0.2–0.7 define.
> Parse its stdout and proceed to Step 1.
>
> - If it prints `{"error": "ecosystem_root_not_found"}` (exit 2), fall back to
>   the `AskUserQuestion` flow in §0.1.
> - If Python is unavailable, the script errors, or output looks wrong, **execute
>   the markdown rules below directly** — they remain the authoritative spec and
>   the fallback. Keep script and tables in sync (`discover.py --selftest`).

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

#### 0.6a Canonical Report Save Paths

Every skill that produces a report and accepts `--save` MUST use these canonical default file names so the dashboard and downstream tools can discover the newest report by glob. The paths are relative to `ecosystem_root`. Explicit `--save <path>` arguments override these defaults.

| Skill | Invocation | Canonical default path |
|---|---|---|
| audit | `/apcore-skills:audit --save` (no arg) | `{ecosystem_root}/audit-report-{cwd_repo}-{YYYY-MM-DD}.md` (`{cwd_repo}` = the session's CWD repo/dir name from Step 0, so same-day runs from different repos don't overwrite each other; re-running the same scope on the same day overwrites idempotently) |
| audit (from release gate) | release Step 2.5.1 | `{ecosystem_root}/release-audit-{version}.md` |
| sync | `/apcore-skills:sync --save` (no arg) | `{ecosystem_root}/sync-report-{cwd_repo}-{YYYY-MM-DD}.md` (`{cwd_repo}` = the session's CWD repo/dir name from Step 0, so same-day runs from different repos don't overwrite each other; re-running the same scope on the same day overwrites idempotently) |
| sync Phase A only | `/apcore-skills:sync --phase a --save` | `{ecosystem_root}/sync-report-phase-a-{cwd_repo}-{YYYY-MM-DD}.md` |
| sync Phase B only | `/apcore-skills:sync --phase b --save` | `{ecosystem_root}/sync-report-phase-b-{cwd_repo}-{YYYY-MM-DD}.md` |
| sync (from release gate) | release Step 2.5.2 | `{ecosystem_root}/release-sync-{version}.md` |
| tester | `/apcore-skills:tester --save` (no arg) | `{ecosystem_root}/tester-report-{cwd_repo}-{YYYY-MM-DD}.md` (`{cwd_repo}` = the session's CWD repo/dir name from Step 0, so same-day runs from different repos don't overwrite each other; re-running the same scope on the same day overwrites idempotently) |
| tester (from release gate) | release Step 6 | `{ecosystem_root}/release-tester-{version}.md` |
| tester (from sdk gate) | sdk Step 9.5.2 | `{ecosystem_root}/sdk-bootstrap-tester-{target-repo-name}.md` |
| release overrides | release Step 2.5.3 BLOCK override | `{ecosystem_root}/release-overrides-{version}.md` |
| sdk gate sync | sdk Step 9.5.1 | `{ecosystem_root}/sdk-bootstrap-sync-{target-repo-name}.md` |
| sdk gate overrides | sdk Step 9.5.3 manual override | `{ecosystem_root}/sdk-gate-overrides.md` |

**Dashboard glob patterns** (cited from this table in `commands/apcore-skills.md`):
- Latest audit: newest mtime match of `{ecosystem_root}/audit-report-*.md` OR `{ecosystem_root}/release-audit-*.md`
- Latest sync: newest match of `{ecosystem_root}/sync-report-*.md` OR `{ecosystem_root}/release-sync-*.md` (ignore `-phase-a-` / `-phase-b-` partials — prefer combined report)
- Latest tester: newest match of `{ecosystem_root}/tester-report-*.md` OR `{ecosystem_root}/release-tester-*.md` OR `{ecosystem_root}/sdk-bootstrap-tester-*.md`

If `--save` is passed with an explicit path, use the explicit path verbatim (including relative paths from CWD). The dashboard glob will only find files under `ecosystem_root` matching the pattern — explicit paths are the operator's responsibility to track.

#### 0.6b Canonical Extraction Cache Path

Skills that spawn sub-agents to extract a deterministic summary from unchanged local source (sync's per-repo API extraction and per-module deep-chain analysis are the current consumers) MAY cache the sub-agent's output keyed by a content hash of the exact files it read, via `shared/scripts/extract_cache.py`. A cache hit is **lossless with respect to input** — the hash guarantees the input the sub-agent would see is byte-identical to a prior run, so re-deriving it would produce the same output. That guarantee only holds end-to-end if the consumer also (a) re-validates the cached output's structural shape on every hit — cheap, local, no LLM call — and (b) folds any write-time validation/quality-gate logic (not just the prompt template) into the version tag below, since a hit does not re-run LLM-judgment gates. A consumer that skips either of these is caching "probably fine," not "provably equivalent."

- **Cache root:** `{ecosystem_root}/.apcore-skills-cache/` — sibling to all discovered repos, never inside a single repo's own `.git`. Each consumer uses its own kind sub-directory, e.g. `.apcore-skills-cache/sync/api/`, `.apcore-skills-cache/sync/deepchain/`.
- **Purely local and offline.** The hash is computed from bytes already on disk (`hashlib.sha256` over sorted `(relpath, content)` pairs). No git invocation, no network access — a dirty working tree is hashed exactly as it sits.
- **Only cache output that already cleared the consumer's own quality gate.** If the consumer has a coverage/validation gate on a fresh sub-agent's output (e.g. sync's Step 2 extraction-coverage gate, Step 4C's shape check + anti-pattern guards), a `put` MUST happen only for output that passed cleanly — never persist a partial/failed/warned result, or it gets frozen indefinitely instead of getting a fresh independent attempt next run.
- **Schema-version tag.** Pass a short literal tag (e.g. `"sync-extract-v1"`) via `extract_cache.py check --extra <tag>` so that editing the sub-agent's prompt template — **or the orchestrator's own write-time validation/anti-pattern-guard logic** — invalidates every cached entry without needing to touch source files. Bump the tag whenever `references/extract-api-prompt.md` / `references/deep-chain-prompt.md` changes, or whenever a validation rule tightens, in a way that could change which outputs would now be accepted for the same input.
- **`.gitignore`.** If `ecosystem_root` itself is (or is inside) a git repo, add `.apcore-skills-cache/` to its `.gitignore` — the cache is a local performance artifact, not something to commit or share. Do this at the actual point a consumer first creates the directory (its first `put` of a run), not only as a documented convention here.
- See `sync` Step 2 and Step 4C for the concrete check/put call sequence, including the structural re-validation on hit and the coverage/quality gate on write.

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
