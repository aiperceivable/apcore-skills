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

## Sub-agent Dispatch Policy

@../shared/subagent-policy.md

> **If you cannot see `<!-- SUBAGENT-POLICY-LOADED -->` above, this include did not expand** — some
> hosts do not support `@`-includes. Read `skills/shared/subagent-policy.md` directly before continuing; it is
> normative, not background reading. Proceeding without it silently drops the rules it
> carries.

**release-specific bindings:**

- **P2 ceiling: 2 x repos.** Use `--scope` to limit the group.
- **P1/P3 plan:** Compute the dispatch count from the selected targets. Run phases sequentially and apply P4's batch-of-3 limit to each phase.
- **P5:** a 429 aborts this run; persist finished units first, then report how to resume. This skill previously had **no** rate-limit handling.

## Iron Law

**NEVER PUSH WITHOUT EXPLICIT USER APPROVAL. All changes are committed locally and presented for review before any push.**

## Anti-Rationalization Table

| Thought | Reality |
|---------|---------|
| "I'll just bump the version number" | Version exists in 2-3 files per repo. Miss one and imports break. |
| "CHANGELOG can be updated later" | CHANGELOG is part of the release artifact. Generate it now from git log. |
| "Tests passed last time, skip them" | Test every repo after version bump. Dependency changes can break things. |
| "I'll push one repo at a time" | Coordinate all repos first, push together after approval. |
| "Audit / sync can run after the release" | NO. Shipping a version with a known critical L2 intent divergence means every user hits the bug. Step 2.5 runs audit + sync BEFORE version bump. Any CRITICAL blocks release unless user explicitly overrides (with logged rationale). |
| "Conventional commit prefixes tell me what's breaking" | NO. A Contract-level change (e.g., silent overwrite → raise DuplicateError) is breaking but often lands under `fix:` or `refactor:`. Step 2.5 surfaces the actual Contract deltas from the sync report; Step 4 uses that delta to classify CHANGELOG entries correctly, not just commit prefixes. |

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
Step 0 (ecosystem) → 1 (parse & validate) → 2 (pre-flight) → 2.5 (consistency gate) → 3 (version bump) → 4 (changelog) → 5 (deps update) → 6 (test) → 7 (commit) → 8 (summary) → [9 (push)]
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
1. Use Step 0's `cwd_repo` and resolve `cwd_repo.name` in `repos[]`.
2. A buildable target selects that package only. For a protocol or docs target,
   ask the user to choose a buildable package or request a group with `--scope`.
   If `cwd_repo` is null, ask which discovered buildable target to release.
3. Display: "Release scope: {repo-name} (from CWD). Use --scope core|mcp|integrations|all for group release."

**If `--scope` IS specified:** use explicit scope.

#### 1.2 Scope → Repos

| Scope | Repos |
|---|---|
| (cwd default) | Only the CWD repo |
| `core` | All core SDKs |
| `mcp` | All MCP bridges |
| `integrations` | Use `AskUserQuestion` to select which integrations |
| `all` | All buildable targets (use `AskUserQuestion` to confirm version per component and for independent targets) |

For each selected target record its `name`, package `path`, `git_root`, package
path relative to `git_root`, intended version, and `release_tag_prefix` from
Step 0. Form the tag as `<release_tag_prefix><version>`, for example
`core/python/v0.34.0` or `mcp/typescript/v0.24.0`. A missing monorepo prefix
requires a valid package-local `.unirelease.toml` before the release proceeds.
Group targets by `git_root` for Git operations. Keep the tag and version
alongside the target ID for all later steps.

Identify the dependency updates in Step 5 before pre-flight. Add their owning
checkouts to the plan with their affected paths, including checkouts whose
only change is a dependency constraint.

Display release plan:
```
Release Plan:
  Checkout | Target | Package path | Target version | Full tag
  Mode:          {release | dry-run}
```

---

### Step 2: Pre-flight Checks

For each `git_root`, confirm the branch and origin, check that its working tree
and index are clean, and record the starting commit. Changes in any package of
a shared checkout affect this check. Resolve dirty worktrees and unexpected
branches before creating a release commit.

For each selected package, verify the proposed version is greater than its
current version unless the user explicitly overrides the comparison. A package
with no prior release may set its first version. Validate the proposed tag with
`git check-ref-format` and check local and remote refs with that exact tag.
Two targets in the same checkout must have distinct tags. Report collisions
before modifying files. An existing remote tag requires a different version or a
separate recovery decision.

Find the latest reachable stable release tag with this package's prefix. Use
that package-specific tag for its changelog range. Preserve the ordinary `v`
prefix for independent packages that use it. A newly bootstrapped package may
have no previous tag.

Display the planned version change, tag, checkout branch and any pre-flight
issues for each target. Resolve scope or version changes before continuing.

---

### Step 2.5: Consistency Gate (MANDATORY — runs before any mutation)

Before bumping any version, run the ecosystem consistency skills and block the release if any CRITICAL finding exists. This prevents shipping known intent divergences, API mismatches, or contract parity gaps.

**Dry-run handling.** When `--dry-run` is active, the gate runs identically (same audit, same sync, same decision rule) but:
- Reports are written to OS tempfiles (e.g., via `mktemp` to `/tmp/apcore-release-gate-{version}-XXXX.md`), NOT to the canonical `{ecosystem_root}/release-{audit|sync|tester}-*.md` paths — dry-run must not pollute the dashboard's "latest report" glob.
- Every gate line in the user-visible output is prefixed with `[DRY-RUN]`.
- BLOCK / WARN / PASS decisions are still computed and displayed — dry-run's purpose includes surfacing gate failures.
- No `release-overrides-*.md` is ever written on dry-run (override is not relevant when nothing is being mutated).
- After dry-run completes (PASS, WARN, or BLOCK), report the gate decision and stop — subsequent steps (3–9) are dry-run simulated per each step's own dry-run semantics.

#### 2.5.1 Run Audit

Use the `ecosystem_root` resolved in release Step 0. Set the report path to
`{ecosystem_root}/release-audit-{version}.md` or the dry-run temp path.

- An explicit group release calls `/apcore-skills:audit --scope {scope} --save {report-path}`.
- A single-package release without a scope flag calls
  `/apcore-skills:audit --repo {selected-target-id} --save {report-path}`,
  using the ID in the release plan. Verify that the report's `Primary target`
  matches that ID before consuming any scores or findings. A missing or
  mismatched target requires rerunning the audit with the correct ID.

Wait for audit to complete. Parse the saved report for:
- **CRITICAL count** across dimensions D1–D11
- **Contract Parity score** (D10) — from the Health Score section
- **Deep-Chain Parity score** (D11) — from the Health Score section
- **D11 critical count** (chain-level divergences are never acceptable at release time — see scoring.md release gate rule 3)
- **Leanness score** (D9) — from the Health Score section

#### 2.5.2 Run Sync (only when scope has ≥2 peer repos)

Skip if no component has multiple selected language packages. Invoke `sync`
with the selected package IDs for those components as positional arguments.
Pass `--save {ecosystem_root}/release-sync-{version}.md` or the dry-run temp path.

Wait for sync to complete. Parse the saved report for:
- CRITICAL findings in Phase A (spec ↔ impl) and Phase B (docs)
- Contract tier (Step 4B) divergences — A-C-* namespace
- **Deep-chain tier (Step 4C) divergences — A-D-* namespace — `critical`, `warning`, and `inconclusive` counts are all release-relevant**

#### 2.5.3 Aggregate Gate Decision

```
Release Consistency Gate — v{version}

Audit report: release-audit-{version}.md
  D10 Contract Parity score: {score}/100
  D11 Deep-Chain Parity score: {score}/100
  D11 critical findings: {N}  ← ANY critical blocks release per scoring.md rule 3
  D9 Leanness score: {score}/100
  CRITICAL findings (D1–D11): {N}

Sync report: release-sync-{version}.md
  Phase A: {N} critical
  Phase B: {N} critical
  Contract tier divergences (A-C-*): {N}
  Deep-chain tier divergences (A-D-*): {N} critical / {N} warning / {N} inconclusive
```

**Decision rule:** defined canonically in `shared/scoring.md` §Release Gate Thresholds. Apply the 5-rule first-match precedence from that file verbatim (note: rule 3 is a hard block on any D11 critical regardless of score). If `shared/scoring.md` thresholds change, the release gate behavior changes — do not duplicate the numbers here.

**When BLOCKED** (normal run), display the top 5 findings by severity (cite the finding IDs from the saved reports) and use `AskUserQuestion`:
- "Run /code-forge:fix --review on the audit + sync reports" — delegates fix-up; after fixes complete, user re-invokes `/apcore-skills:release`
- "Abort release" — stop; no mutations have been made yet
- "Override and continue (requires rationale)" — `AskUserQuestion` follow-up: "Provide rationale for shipping with known critical findings" (free-form text); append the rationale to `{ecosystem_root}/release-overrides-{version}.md` with timestamp, user identity (run `git -C {primary_release_repo} config user.email` where `primary_release_repo` is the first repo in the release scope; fall back to `whoami` + hostname if that is empty), and the list of unfixed finding IDs. Only then continue to Step 3.

**When BLOCKED (dry-run),** display the findings with `[DRY-RUN]` prefix and stop. No override option is offered (nothing to override — no mutation is pending). User fixes and re-runs.

**When WARN (medium D10 score)**, display summary and ask `AskUserQuestion`: "Continue release?" → continue | "Run fix first" | "Abort".

**Findings captured by the gate are passed forward** to Step 4 (CHANGELOG) — any critical finding marked "contract tier divergence" indicates a Contract-level semantic change that SHOULD appear in CHANGELOG's `### Breaking` section regardless of commit prefix. Step 4 reads the sync report to enrich classification.

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
2. Go modules derive their version from the package tag resolved in Step 1.2

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
2. Run `git -C {git_root} log --oneline {last_tag}..HEAD -- {package_relative_path}` with the tag found in Step 2. Without a prior package tag, use `git -C {git_root} log -50 --oneline -- {package_relative_path}`.
3. Categorize commits into:
   - **Added** — new features (feat:)
   - **Changed** — modifications to existing features (refactor:, perf:)
   - **Fixed** — bug fixes (fix:)
   - **Breaking** — breaking changes (feat!:, fix!:, or BREAKING CHANGE in body)
   - **Documentation** — doc changes (docs:)
   - **Other** — everything else (chore:, ci:, test:)

   **Augment classification from Step 2.5 gate findings.** Read the sync report if Step 2.5.2 produced one. For every finding in sync Phase A (signature change) or sync Step 4B (Contract tier — inputs/errors/side-effects/return/properties divergence from prior version), cross-reference the commit that introduced it (via `git log -S`). Any such commit MUST land in the `### Breaking` section even if its prefix was `fix:` or `refactor:`. Emit a note under the entry: `Breaking (contract): {finding summary} — was classified as {prefix} in commit history`.

   Also include any A-001 / A-C-{seq} / B-001 finding IDs referenced in the commits. The finding ID + a one-line description goes into the CHANGELOG entry so downstream consumers can trace.
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

For integrations in the pre-flighted dependency plan that depend on Core SDKs
or MCP bridges being released, spawn one `Agent(subagent_type="general-purpose")`
per integration. Match each dependency to the released package's language and
target version.

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
Run the full test suite for {repo_path} and report results. Include any
dependency-only integration changed in Step 5.

Detect the language from the build config file and use the appropriate test command:
- Python (pyproject.toml): cd {repo_path} && python -m pytest --tb=short -q 2>&1
- TypeScript (package.json): use the test command from this package or its checkout CI (pnpm for monorepo packages).
- Go (go.mod): cd {repo_path} && go test ./... 2>&1
- Rust (Cargo.toml): use the test command and features from this package or its checkout CI.
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

For selected packages with `conformance_path`, call
`/apcore-skills:tester {selected-package-ids} --category conformance --mode run --save {ecosystem_root}/release-tester-{version}.md`.
Pass the IDs as separate positional arguments. Tester runs their native
fixture-driven tests against each package's shared suite. A failing assertion,
behavioral divergence, or unavailable suite for a selected package blocks its
release. Treat a missing Core or Surface fixture path as an unavailable suite.
Report unverified per-case evidence separately.

Display results:
```
Test verification:
  Unit tests by target:
    {target-id}: {passed}/{total} passed, {failed} failed, {skipped} skipped
  Shared conformance by component:
    {component} / {target-id}: {passed}/{total} passed, {failed} failed, {unverified} unverified
  Cross-language divergent cases: {N}
```

If unit tests or the conformance verification fail:
- Display failure / divergence details
- Use `AskUserQuestion`: "How to proceed?"
  - "Fix and retry" — investigate failures (route conformance divergences to `/code-forge:fix --review` consuming the tester report)
  - "Skip this target" — for a unit-test failure, restore this run's edits using the pre-flight baseline, remove the failed target from the plan, and recompute dependency updates and verification before committing. Resolve shared-suite failures before proceeding.
  - "Abort release" — use the release file lists and the Step 2 baseline to revert only this run's edits, including any dependency changes. Preserve unrelated changes and remove only files created by the run.

---

### Step 7: Commit by Checkout

Make one local release commit per changed `git_root`. Combine and deduplicate
exact repository-relative paths from the version, changelog, and dependency
updates. Include a dependency-only checkout if the changes are part of this
release. Check the staged diff against this list and commit only those paths.
Record the new commit SHA and associate it with the plan's package tags for
that checkout.

```bash
git -C "$git_root" add -- "${release_paths[@]}"
git -C "$git_root" diff --cached --stat
git -C "$git_root" commit -m "release: $release_summary" -- "${release_paths[@]}"
```

---

### Step 8: Release Summary and Approval

Show each checkout's branch, release commit, changed files, packages, full tags,
and verification results. Ask for explicit approval to push all eligible
checkouts or a selected subset of checkouts. A shared checkout's branch push
includes its complete release commit. To narrow this to a subset of its
packages, revise the plan and commit before asking for push approval.

---

### Step 9: Push and Tag (only with explicit approval)

For each approved checkout, confirm the release branch still points at the
reviewed commit. Create each planned tag on that commit. On retry, reuse a local
tag only when it points to the reviewed release commit. Refuse to replace a tag
at another commit.

Push the approved branch and all of its planned tag refs together. Construct
`release_refs` from the full branch ref and exactly the planned tags. For
example, a Core release can use `refs/heads/main`,
`refs/tags/core/python/v0.34.0` and `refs/tags/core/rust/v0.34.0`.

```bash
git -C "$git_root" push --atomic origin "${release_refs[@]}"
```

If the remote rejects the atomic push or the connection drops, inspect the
exact branch and tag refs before retrying. Preserve the reviewed refs for retry
and report what reached the remote. Stop for that checkout on tag conflicts,
branch changes, or lack of atomic support. Never force-push. Report the exact
pushed tags and any pending checkouts. Resolve any subsequent registry commands
from each package's `path`.
