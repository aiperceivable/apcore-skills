### Step 0: Ecosystem Discovery and Configuration

<!-- ECOSYSTEM-LOADED -->


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
> `path`, `type`, `language`, `version`, `package_name`, `git_status`, `status`,
> `git_root`, `spec_root`, `conformance_path`, and `release_tag_prefix`),
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

The ecosystem root is the parent directory of the `apcore/` and
`apcore-surfaces/` checkouts. Resolve it in this order:

1. Use the explicit `--root <ecosystem_root>` value when running the script with that option.
2. Read `ecosystem_root` from `.apcore-skills.json` in the current directory if configured.
3. Starting at the current directory, walk upward to the nearest directory that contains
   `apcore/PROTOCOL_SPEC.md` or an `apcore-surfaces/` checkout with an `mcp/`, `a2a/`,
   `cli/`, or `toolkit/` component directory. Either checkout is enough to find the root.
4. If the root is still unknown, use `AskUserQuestion` to ask for its path.

#### 0.2 Discover Repositories

Scan the two monorepos for Core SDK and Surface targets. In the table, `<lang>` is
a recognized language directory (see `KNOWN_LANGS` in `discover.py`). The current
packages use `python`, `rust`, and `typescript`. An SDK scaffold becomes a
discovery target as soon as its language directory contains a build file.

| Path relative to ecosystem root | Type | Target name |
|---|---|---|
| `apcore/` with `PROTOCOL_SPEC.md` | `protocol` | `apcore` |
| `apcore/<lang>/` | `core-sdk` | `apcore-<lang>` |
| `apcore-surfaces/<component>/` with `docs/` | `docs-site` | `apcore-<component>` |
| `apcore-surfaces/mcp/<lang>/` | `mcp-bridge` | `apcore-mcp-<lang>` |
| `apcore-surfaces/a2a/<lang>/` | `a2a-bridge` | `apcore-a2a-<lang>` |
| `apcore-surfaces/cli/<lang>/` | `cli` | `apcore-cli-<lang>` |
| `apcore-surfaces/toolkit/<lang>/` | `toolkit` | `apcore-toolkit-<lang>` |

`<component>` is one of `mcp`, `a2a`, `cli`, or `toolkit`. Discover a language
package when its directory contains a supported build file. Ignore the former
standalone Core SDK and Surface checkouts, including their documentation
checkouts, even if the corresponding monorepo target is absent. The
`apcore-surfaces/` root groups its components.

Also scan for independently maintained sibling projects:

| Directory pattern | Type | Examples |
|---|---|---|
| `{framework}-apcore/` | `integration` | `django-apcore`, `flask-apcore`, `nestjs-apcore` |
| `apcore-discovery-<lang>/` | `shared-lib` | `apcore-discovery-python` |
| `apcore-zh/`, `aipartnerup-docs/` | `docs-site` | Localization and organization docs |
| `apcore-studio/` | `tooling` | Tooling project |

Supported build files include `pyproject.toml`, `setup.py`, `package.json`,
`go.mod`, `Cargo.toml`, `pom.xml`, `build.gradle`, `build.gradle.kts`,
`composer.json`, `mix.exs`, `Package.swift`, and `*.csproj`. Keep a recognized
sibling project without a build file as a `placeholder`. Protocol and docs
targets are present by layout and have no package version.

Store targets in `repos[]` sorted by `name`. Use `name` as a stable ID for target
selection, references, and reports. Resolve that ID via `repos[]` for every
filesystem operation.

| Field | Meaning |
|---|---|
| `path` | Absolute working directory for this package or documentation target |
| `git_root` | Absolute owning checkout directory. Core targets share `apcore/`, and Surface targets share `apcore-surfaces/`. |
| `spec_root` | Absolute directory containing the specification for the target, or `null`. For Core this is `apcore/`, and for a Surface it is `apcore-surfaces/<component>/`. |
| `conformance_path` | Absolute path to `<spec_root>/conformance/` when present, or `null` |
| `release_tag_prefix` | The package's `.unirelease.toml` `tag_prefix`, e.g. `core/python/v`. An independent buildable target defaults to `v` if unset. A monorepo package without a configured prefix returns `null`. |
| `type`, `status` | Target type and one of `ok`, `placeholder`, `protocol`, or `docs-site` |
| `language`, `version`, `package_name` | Language from the monorepo directory or sibling build config. Read the package name and version from the target's own build config. |
| `git_status` | `clean`, `dirty`, or `unknown`. Run Git from `git_root` with a pathspec for `path` so sibling packages' changes do not mark a language package dirty. |

#### 0.3 The `--scope` vocabulary (shared — every skill uses these exact values)

`--scope` takes one of **`core` | `mcp` | `integrations` | `all`** in every skill that
accepts it. The values are the `scope_group` names assigned in 0.3.1 below, so the flag
and the discovery output speak the same language.

| Value | Repos | Notes for skills that behave differently |
|---|---|---|
| `core` | the `protocol` repo + every `core-sdk` repo | — |
| `mcp` | the `docs-site` repo for MCP + every `mcp-bridge` repo | — |
| `integrations` | every `integration` repo | Integration repos have no protocol spec, so any spec-vs-implementation phase is N/A for them; skills that have one run only their documentation pass (e.g. `sync` Step 1.2). This is a property of the repo type, not of the flag. |
| `all` | every discovered repo | |

**Default when omitted: the current working directory's repo only** (0.3.1). Skills MUST
NOT invent extra values, drop a value from the list, or give one a different meaning. A
skill that genuinely cannot act on a value reports why — it does not treat it as an
unknown flag.

Further `scope_group` names exist in discovery output (`a2a`, `cli`, `toolkit`, `shared`,
`tooling`, and `docs`). Select those targets by CWD or by target ID using the
skill's selector, such as `audit --repo <target-id>` or a positional ID in
`sync`. The `--scope` values remain the four listed above.

#### 0.3.1 Detect CWD Repo

Determine `cwd_repo` using the resolved absolute paths. Start at CWD and walk up
its parents until a directory equals a discovered target's `path`. The first
match is the most specific target, so `apcore/python/src/apcore/` selects
`apcore-python`, and `apcore-surfaces/mcp/typescript/src/` selects
`apcore-mcp-typescript`. A component's documentation directory selects the
component's docs target. The ecosystem directory, the `apcore-surfaces/`
container, and former standalone SDK checkouts have no matching target.

For a match, store `cwd_repo = { name, type, language, scope_group }`:
   - `core-sdk` → `scope_group = "core"`
   - `mcp-bridge` → `scope_group = "mcp"`
   - `a2a-bridge` → `scope_group = "a2a"`
   - `cli` → `scope_group = "cli"`
   - `toolkit` → `scope_group = "toolkit"`
   - `integration` → `scope_group = "integrations"`
   - `protocol` / `docs-site` → `scope_group = "docs"`
   - `shared-lib` → `scope_group = "shared"`
   - `tooling` → `scope_group = "tooling"`

Set `cwd_repo = null` when no target matches.

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
   - `version_groups.mcp` = auto-populated from all discovered `mcp-bridge` repos (e.g., `["apcore-mcp-python", "apcore-mcp-rust", "apcore-mcp-typescript"]`)
   - `version_groups.a2a` and `version_groups.cli` are auto-populated from discovered A2A and CLI packages, respectively
   - Toolkit has no automatic `version_groups` entry. Audit D3 checks each Toolkit package's manifest and in-source version when available. Cross-language Toolkit API and conformance checks still use the shared component root.

2. **User global config** (`~/.apcore-skills.json`, if exists) → deep-merge

3. **Project config** (`<ecosystem_root>/.apcore-skills.json`, if exists) → deep-merge

#### 0.5 Version Extraction Rules

| File | Version Location |
|---|---|
| `pyproject.toml` | `[project] version = "X.Y.Z"` |
| `package.json` | `"version": "X.Y.Z"` |
| `Cargo.toml` | `[package] version = "X.Y.Z"` |
| `go.mod` | Highest stable version from Git tags matching the target's `release_tag_prefix` |
| `pom.xml` | `<version>X.Y.Z</version>` |
| `build.gradle` | `version = 'X.Y.Z'` or `version 'X.Y.Z'` |
| `build.gradle.kts` | `version = "X.Y.Z"` |
| `mix.exs` | `version: "X.Y.Z"` in `project/0` |
| `Package.swift` | Highest stable version from Git tags matching the target's `release_tag_prefix` |
| `*.csproj` | `<Version>X.Y.Z</Version>` |
| `composer.json` | `"version": "X.Y.Z"` |
| `__init__.py` / `_version.py` | `__version__ = "X.Y.Z"` |
| `src/*/index.ts` | `export const VERSION = "X.Y.Z"` |

For Python projects, also check `src/*/__init__.py` for `__version__`.

#### 0.6 Display Discovery Summary

For each discovered target, show its ID, path relative to the ecosystem root,
type, language, version, and Git status.

```
apcore-skills — Ecosystem Dashboard

Ecosystem root: {ecosystem_root}
Targets discovered: {count}

  Target ID          | Relative path            | Type       | Language | Version   | Git status
  apcore             | apcore/                  | protocol   | —        | —         | {git_status}
  apcore-python      | apcore/python/           | core-sdk   | Python   | {version} | {git_status}
  apcore-mcp-rust    | apcore-surfaces/mcp/rust/ | mcp-bridge | Rust     | {version} | {git_status}
```

#### 0.6a Canonical Report Save Paths

Every skill that produces a report and accepts `--save` MUST use these canonical default file names so the dashboard and downstream tools can discover the newest report by glob. The paths are relative to `ecosystem_root`. Explicit `--save <path>` arguments override these defaults.

| Skill | Invocation | Canonical default path |
|---|---|---|
| audit | `/apcore-skills:audit --save` (no path) | `{ecosystem_root}/audit-report-{target}-{YYYY-MM-DD}.md` (`{target}` is the primary target ID for target-based audits, or the session's CWD repo/dir name for group audits) |
| audit (from release gate) | release Step 2.5.1 | `{ecosystem_root}/release-audit-{version}.md` |
| sync | `/apcore-skills:sync --save` (no arg) | `{ecosystem_root}/sync-report-{cwd_repo}-{YYYY-MM-DD}.md` (`{cwd_repo}` = the session's CWD repo/dir name from Step 0, so same-day runs from different repos don't overwrite each other; re-running the same scope on the same day overwrites idempotently) |
| sync Phase A only | `/apcore-skills:sync --skip-docs --save` | `{ecosystem_root}/sync-report-phase-a-{cwd_repo}-{YYYY-MM-DD}.md` |
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
- **Schema-version tag.** Pass a short literal tag (e.g. `"sync-extract-v2"`) via `extract_cache.py check --extra <tag>` so that editing the sub-agent's prompt template — **or the orchestrator's own write-time validation/anti-pattern-guard logic** — invalidates every cached entry without needing to touch source files. Bump the tag whenever `references/extract-api-prompt.md` / `references/deep-chain-prompt.md` changes, or whenever a validation rule tightens, in a way that could change which outputs would now be accepted for the same input.
- **Always `check --out-file <path>`.** On a hit the payload is written there and stdout carries only `{status, hash, data_file, bytes}`. Without it the whole payload prints to stdout and lands in the caller's context — measured at 941 KB across three repos, which makes a cache **hit** ~1200× more expensive than a miss and inverts the point of caching. See `shared/subagent-policy.md` P8.
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
