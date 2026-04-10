---
name: release
description: >
  Coordinated multi-repo release pipeline for the apcore ecosystem. Handles version
  bumps across all version files, CHANGELOG generation from git history, cross-repo
  dependency updates, test verification, and staged commits. Only pushes after
  explicit user approval.
instructions: >
  NEVER push without explicit user approval. NEVER use git add -A or git add .
  — always stage specific files. All changes are committed locally first and
  presented for review. If push fails, do NOT force-push.
---

# Apcore Skills — Release

## ⚡ Execution Entry Point (READ THIS FIRST)

**When this skill is loaded, you MUST immediately begin executing the Workflow below — do not wait, do not summarize, do not ask "what should I do now". Skills are operational manuals, not reference documents.** Read the first executable step, perform it, then the next, etc., until the workflow completes or you reach an `AskUserQuestion` checkpoint. **Never push without explicit user approval — this is enforced by the workflow's user-confirmation checkpoints, not optional.**

If the harness shows you `Successfully loaded skill · N tools allowed`, that message means **the SKILL.md content was injected into your context** — it does NOT mean the skill has run. Skills do not "run" autonomously; you run them by executing the Detailed Steps below.

If you find yourself about to say "the skill didn't produce output", "skill 仍未输出", "falling back to manual release", "回退到手动 release", or anything similar, **STOP**. You have misunderstood how skills work. Go directly to the first executable step and start.

The first user-visible action of this skill should be either (a) the output of the first step, or (b) an `AskUserQuestion` if the first step needs disambiguation. Never an apology, never a fallback, never silence.

---

Execute a coordinated release across multiple apcore ecosystem repositories.

## Iron Law

**NEVER PUSH WITHOUT EXPLICIT USER APPROVAL. All changes are committed locally and presented for review before any push.**

## Anti-Rationalization Table

| Thought | Reality |
|---------|---------|
| "I'll just bump the version number" | Version exists in 2-3 files per repo. Miss one and imports break. |
| "CHANGELOG can be updated later" | CHANGELOG is part of the release artifact. Generate it now from git log. |
| "Tests passed last time, skip them" | Test every repo after version bump. Dependency changes can break things. |
| "I'll push one repo at a time" | Coordinate all repos first, push together after approval. |

## When to Use

- Releasing a new version of core SDKs (both Python and TypeScript together)
- Releasing a new version of MCP bridges (both together)
- Releasing an integration update
- Coordinated ecosystem-wide release

## Command Format

```
/apcore-skills:release <version> [--scope core|mcp|integrations|all] [--dry-run]
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `<version>` | Yes | — | Target version (e.g., `0.9.0`, `1.0.0`) |
| `--scope` | No | **cwd** | Which repos to release. **If omitted, defaults to the current working directory's repo only.** Use `--scope core\|mcp\|all` for group release. |
| `--dry-run` | No | off | Show what would change without making changes |

## Workflow

```
Step 0 (ecosystem) → 1 (parse & validate) → 2 (pre-flight) → 3 (version bump) → 4 (changelog) → 5 (deps update) → 6 (test) → 7 (commit) → 8 (summary) → [9 (push)]
```

## Context Management

Steps 3, 4, and 6 use parallel sub-agents (one per repo) for speed. The main context orchestrates phases and collects results.

## Detailed Steps

### Step 0: Ecosystem Discovery

@../shared/ecosystem.md

---

### Step 1: Parse Arguments and Validate

Parse `$ARGUMENTS`:

1. Extract `<version>` — required. Validate format: `X.Y.Z` (semver without `v` prefix)
2. Extract `--scope` — determine which repos to release
3. Extract `--dry-run` — simulation mode

#### 1.1 CWD-based Default Scope

**If `--scope` is NOT specified:**
1. Detect CWD repo name (basename of CWD)
2. Look up in discovered ecosystem:
   - If it's a known apcore repo → release **only this repo**
   - If CWD is a `protocol`/`docs-site` repo → error: "Documentation repos cannot be released directly. Specify --scope core|mcp|all."
   - If CWD is not an apcore repo → use `AskUserQuestion` to ask: "CWD is not an apcore repo. Which repo do you want to release?" with options from `repos[]` names + "All repos (group release)"
3. Display: "Release scope: {repo-name} (from CWD). Use --scope core|mcp|all for group release."

**If `--scope` IS specified:** use explicit scope.

#### 1.2 Scope → Repos

| Scope | Repos |
|---|---|
| (cwd default) | Only the CWD repo |
| `core` | All core SDKs |
| `mcp` | All MCP bridges |
| `integrations` | Use `AskUserQuestion` to select which integrations |
| `all` | All repos (use `AskUserQuestion` to confirm version per group) |

For `all` scope, versions may differ per group:
- Use `AskUserQuestion`: "Version for core SDKs?" / "Version for MCP bridges?" / "Version per integration?"

Display release plan:
```
Release Plan:
  Core SDKs:     {repos} → v{version}
  MCP Bridges:   {repos} → v{mcp-version}
  Integrations:  {repos} → v{int-version}
  Mode:          {release | dry-run}
```

---

### Step 2: Pre-flight Checks (Parallel Sub-agents — One per Repo)

Spawn one `Agent(subagent_type="general-purpose")` **per repo, all simultaneously**:

**Sub-agent prompt:**
```
Run pre-flight checks for release in {repo_path}.

1. Git status: run `git -C {repo_path} status --porcelain` — must be empty (clean)
   - If dirty: list modified files
2. Branch: run `git -C {repo_path} branch --show-current` — should be main or master
3. Current version: extract from build config (pyproject.toml or package.json)
4. Git tags: run `git -C {repo_path} tag --sort=-v:refname | head -5` — list recent tags

Error handling:
- If the repo path does not exist, return: REPO: {repo-name}, STATUS: NOT_FOUND
- If git is not initialized, return: REPO: {repo-name}, STATUS: NO_GIT

Return:
REPO: {repo-name}
GIT_STATUS: clean | dirty
DIRTY_FILES: {list if dirty, empty if clean}
BRANCH: {current branch name}
CURRENT_VERSION: {version}
RECENT_TAGS: {list}
```

Wait for all pre-flight sub-agents to complete. Aggregate results:

```
Pre-flight:
  apcore-python:      ✓ clean, main, 0.7.0 → 0.9.0
  apcore-typescript:   ✓ clean, main, 0.7.1 → 0.9.0
  apcore-mcp-python:   ✓ clean, main, 0.8.1 → 0.9.0
  apcore-mcp-typescript: ⚠ dirty (2 modified files)
```

For each repo with issues, use `AskUserQuestion` to resolve:
- Dirty repo: "Stash changes" / "Skip this repo" / "Abort"
- Wrong branch: "Continue on {branch}" / "Switch to main" / "Abort"
- Version not < target: "Force version update" / "Skip this repo" / "Abort"

---

### Step 3: Version Bump (Parallel Sub-agents — All Repos Simultaneously)

Spawn one `Agent(subagent_type="general-purpose")` **per repo, all simultaneously in a single round of parallel Agent calls**:

**Sub-agent prompt:**
```
Update all version references in {repo_path} from {old_version} to {new_version}.

Files to update (check each, update if exists):

For Python repos:
1. pyproject.toml → [project] version = "{new_version}"
2. src/{package}/__init__.py → __version__ = "{new_version}"
3. src/{package}/_version.py → __version__ = "{new_version}" (if exists)

For TypeScript repos:
1. package.json → "version": "{new_version}"
2. src/index.ts → VERSION constant (if exists)
3. package-lock.json → top-level "version" (if exists)

For Go repos:
1. Version constant in internal/version.go or cmd/version.go (if exists)
2. Go modules use git tags (v{new_version}) — note for Step 7 tagging

For Rust repos:
1. Cargo.toml → [package] version = "{new_version}"
2. Cargo.lock → update corresponding entry (if exists)

For Java repos (Maven):
1. pom.xml → <version>{new_version}</version>

For Java repos (Gradle):
1. build.gradle or build.gradle.kts → version = "{new_version}"
2. gradle.properties → version={new_version} (if exists)

For PHP repos:
1. composer.json → "version": "{new_version}"

For C# repos:
1. *.csproj → <Version>{new_version}</Version>

For Swift repos:
1. Package.swift → version constant (if exists)

For Elixir repos:
1. mix.exs → version: "{new_version}"

Additional (all repos):
- README.md → version badges or installation instructions mentioning version
- Any other file containing the old version string (search with grep)

{If dry-run:} Do NOT modify any files. Just report what would change.

Error handling:
- If a version file is missing, skip it and note in CHANGES as "{file} (NOT_FOUND)"
- If a file is unwritable, skip it and note in CHANGES as "{file} (WRITE_ERROR)"

Return:
REPO: {repo-name}
OLD_VERSION: {old}
NEW_VERSION: {new}
FILES_MODIFIED: {count}
CHANGES:
- {file}: {what changed}
```

After all sub-agents complete, display results:
```
Version bump:
  apcore-python:       0.7.0 → 0.9.0 (3 files)
  apcore-typescript:    0.7.1 → 0.9.0 (2 files)
```

---

### Step 4: CHANGELOG Generation (Parallel Sub-agents — All Repos Simultaneously)

Spawn one `Agent(subagent_type="general-purpose")` **per repo, all simultaneously**:

**Sub-agent prompt:**
```
Generate a CHANGELOG entry for {repo_path} version {new_version}.

1. Read the current CHANGELOG.md
2. Run: git -C {repo_path} log --oneline {last_tag}..HEAD
   (If no tags exist, use the last 50 commits)
3. Categorize commits into:
   - **Added** — new features (feat:)
   - **Changed** — modifications to existing features (refactor:, perf:)
   - **Fixed** — bug fixes (fix:)
   - **Breaking** — breaking changes (feat!:, fix!:, or BREAKING CHANGE in body)
   - **Documentation** — doc changes (docs:)
   - **Other** — everything else (chore:, ci:, test:)
4. Write the new entry at the top of CHANGELOG.md, after any existing header:

## [{new_version}] - {YYYY-MM-DD}

### Added
- Description from commit message

### Changed
- ...

### Fixed
- ...

{If dry-run:} Do NOT modify CHANGELOG.md. Just return the generated entry.

Error handling:
- If CHANGELOG.md does not exist, create a new one with standard header and the version entry
- If git log fails or returns no commits, generate minimal entry: "Initial release"
- If fewer than 50 commits exist, use all available commits
- If no tags exist and no git history, generate an empty-categories entry

Return in this exact format:
REPO: {repo-name}
CHANGELOG_ENTRY:
## [{new_version}] - {YYYY-MM-DD}
### Added
- {entries}
### Changed
- {entries}
### Fixed
- {entries}

COMMIT_COUNT: {N commits analyzed}
FILES_MODIFIED: {0 if dry-run, 1 if CHANGELOG.md was updated}
CHANGES:
- CHANGELOG.md: {created | prepended version {new_version} entry}
```

Display preview of each CHANGELOG entry for user review.

---

### Step 5: Cross-Repo Dependency Updates (Parallel Sub-agents — One per Integration)

**Skip condition:** If `--scope integrations` (only integration repos in this release, no core SDKs or MCP bridges), skip this step entirely and note: "Dependency versions unchanged — core SDKs/MCP bridges not part of this release."

For integration repos that depend on core SDKs or MCP bridges being released, spawn one `Agent(subagent_type="general-purpose")` **per integration repo, all simultaneously**:

**Sub-agent prompt:**
```
Update apcore dependency versions in {repo_path}.

The core SDK version has been bumped to {new_version}.

1. Read the build config (pyproject.toml or package.json)
2. Find all references to apcore packages in dependencies:
   - Python: [project] dependencies, [project.optional-dependencies]
   - TypeScript: dependencies, peerDependencies, devDependencies
3. Update version constraints:
   - apcore>={old} → apcore>={new_version}
   - apcore-mcp>={old} → apcore-mcp>={new_version}
   - (and any other apcore-* packages)

{If dry-run:} Do NOT modify any files. Just report what would change.

Error handling:
- If build config is missing, return: REPO: {repo-name}, STATUS: NO_BUILD_CONFIG
- If no apcore dependencies found, return: REPO: {repo-name}, UPDATES: [] (empty — no apcore deps)

Return:
REPO: {repo-name}
UPDATES:
- package: {name}, old: {constraint}, new: {constraint}, file: {path}
```

Wait for all sub-agents to complete. Display:
```
Dependency updates:
  django-apcore:  apcore>=0.7.0 → apcore>={new_version}
  flask-apcore:   apcore>=0.7.0 → apcore>={new_version}
```

---

### Step 6: Test Verification (Parallel Sub-agents — All Repos Simultaneously)

Spawn one `Agent(subagent_type="general-purpose")` **per repo, all simultaneously**:

**Sub-agent prompt:**
```
Run the full test suite for {repo_path} and report results.

Detect the language from the build config file and use the appropriate test command:
- Python (pyproject.toml): cd {repo_path} && python -m pytest --tb=short -q 2>&1
- TypeScript (package.json): cd {repo_path} && npx vitest run 2>&1
- Go (go.mod): cd {repo_path} && go test ./... 2>&1
- Rust (Cargo.toml): cd {repo_path} && cargo test 2>&1
- Java/Maven (pom.xml): cd {repo_path} && mvn test -q 2>&1
- Java/Gradle (build.gradle): cd {repo_path} && gradle test 2>&1
- C# (*.csproj): cd {repo_path} && dotnet test 2>&1
- Swift (Package.swift): cd {repo_path} && swift test 2>&1
- PHP (composer.json): cd {repo_path} && vendor/bin/phpunit 2>&1
- Elixir (mix.exs): cd {repo_path} && mix test 2>&1

Return:
REPO: {repo-name}
TEST_RESULT: pass | fail
TOTAL: {N}
PASSED: {N}
FAILED: {N}
ERRORS: {N}
FAILURE_DETAILS: {first 3 failure messages if any}

Error handling:
- If test runner not found (pytest/vitest not installed), return: TEST_RESULT: skipped, REASON: "{runner} not available"
- If dependencies not installed (ImportError, ModuleNotFoundError), return: TEST_RESULT: skipped, REASON: "dependencies not installed"
- Do NOT fail the entire release if test runner is unavailable — report and let user decide
```

Display results:
```
Test verification:
  apcore-python:       ✓ 393/393 passing
  apcore-typescript:    ✓ 287/287 passing
  apcore-mcp-python:   ✓ 156/156 passing
  django-apcore:       ✓ 644/644 passing
```

If any repo fails:
- Display failure details
- Use `AskUserQuestion`: "How to proceed?"
  - "Fix and retry" — investigate failures
  - "Skip this repo" — exclude from release
  - "Abort release" — stop everything, revert version bumps:
    For each repo already bumped in Step 3/4: `git -C {repo_path} checkout -- {list of modified files}`
    (Safe because Step 7 commit has not yet run — only uncommitted changes are discarded)

---

### Step 7: Commit Changes

For each repo with changes:

1. Stage only the files modified by version bump and CHANGELOG generation — use `git add` with explicit file paths (e.g., `git add pyproject.toml src/apcore/__init__.py CHANGELOG.md`)
2. **NEVER use `git add -A` or `git add .`** — this risks staging untracked files, `.env`, build artifacts, or other sensitive content
3. Commit with release message:

```bash
cd {repo_path} && git add {list of modified files} && git commit -m "release: v{new_version}"
```

Display:
```
Commits created:
  apcore-python:       release: v0.9.0 (3 files)
  apcore-typescript:    release: v0.9.0 (2 files)
  apcore-mcp-python:   release: v0.9.0 (3 files)
```

---

### Step 8: Release Summary and Approval

```
apcore-skills release — Summary

Version: {version}
Repos released: {count}

  Repo                    | Version       | Files | Tests  | Commit
  apcore-python           | 0.7.0 → 0.9.0 |   3   | 393 ✓  | abc1234
  apcore-typescript        | 0.7.1 → 0.9.0 |   2   | 287 ✓  | def5678
  apcore-mcp-python       | 0.8.1 → 0.9.0 |   3   | 156 ✓  | ghi9012
  apcore-mcp-typescript    | 0.8.1 → 0.9.0 |   2   | 112 ✓  | jkl3456

CHANGELOG entries generated: {count}
Dependency updates: {count}

All changes committed locally. Nothing has been pushed.
```

Use `AskUserQuestion`:
- "Review changes first" — show `git diff HEAD~1` for each repo
- "Push all repos" → Step 9
- "Push selected repos" → Step 9 with selection
- "Done (keep local commits, don't push)" — stop here

---

### Step 9: Push and Tag (only with explicit approval)

For each approved repo:

```bash
cd {repo_path} && git push origin {branch} && git tag v{new_version} && git push origin v{new_version}
```

**Error handling:** If push fails for any repo:
- Display the error message (auth failure, rejected push, network error)
- Use `AskUserQuestion`: "Push failed for {repo}."
  - "Retry" — attempt push again
  - "Skip this repo" — continue with remaining repos
  - "Abort remaining pushes" — stop, display which repos were pushed and which were not
- If rejected due to remote changes: warn user to `git pull --rebase` first, do NOT force-push

Display:
```
Push complete:
  apcore-python:       pushed + tagged v0.9.0
  apcore-typescript:    pushed + tagged v0.9.0

Next steps:
  Create GitHub releases (if desired)
  Publish packages:
    cd apcore-python && python -m build && twine upload dist/*
    cd apcore-typescript && npm publish
  Update documentation site
  Announce release
```
