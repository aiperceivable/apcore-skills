---
name: apcore-skills
description: >
  Apcore ecosystem management skill for Codex. Use only when the user explicitly
  asks for apcore-skills, apcore ecosystem sync, SDK bootstrap, framework
  integration scaffolding, ecosystem audit, spec-driven tester, coordinated
  release, or dashboard operations. Handles cross-language API, contract, and
  deep-chain consistency across apcore repos, documentation alignment,
  conformance testing, and multi-repo release coordination.
version: 1.0
subcommands:
  - sync
  - sdk
  - integration
  - audit
  - tester
  - release
---

# Apcore Skills Orchestrator

Apcore-skills is an ecosystem-level workflow suite for the apcore family of
repositories. This root skill is the Codex-facing orchestrator: route explicit
apcore-skills requests, load only the needed child skill, and preserve the
cross-language consistency model.

## Trigger Policy

Use this skill only when the user explicitly asks for apcore-skills or one of
its subcommands. Do not trigger merely because the current repository or path
contains `apcore`.

Valid trigger examples:

- `/apcore-skills`
- `/apcore-skills:sync ...`
- `/apcore-skills:sdk ...`
- `/apcore-skills:integration ...`
- `/apcore-skills:audit ...`
- `/apcore-skills:tester ...`
- `/apcore-skills:release ...`
- "run apcore-skills audit"
- "bootstrap an apcore SDK"
- "sync the apcore ecosystem"

Do not use this skill for ordinary application work inside an apcore repo unless
the user asks for ecosystem-level apcore-skills behavior. For regular code
planning, implementation, debugging, or review, use code-forge-style workflows.

## Routes

| User request | Route |
|---|---|
| `/apcore-skills` | Dashboard via `commands/apcore-skills.md` |
| `/apcore-skills:sync ...` | Sync |
| `/apcore-skills:sdk ...` | SDK |
| `/apcore-skills:integration ...` | Integration |
| `/apcore-skills:audit ...` | Audit |
| `/apcore-skills:tester ...` | Tester |
| `/apcore-skills:release ...` | Release |

The `commands/*.md` files are compatibility command definitions from the
Claude-oriented implementation. In Codex, prefer reading the child
`skills/*/SKILL.md` files directly for subcommands. Use
`commands/apcore-skills.md` for the dashboard and top-level routing details.

## Progressive Loading

Keep context small.

1. Read this root file first.
2. Read only the child `SKILL.md` matching the requested subcommand.
3. Read `commands/apcore-skills.md` only for the dashboard or if top-level routing details are needed.
4. Read `skills/shared/ecosystem.md` when ecosystem discovery, repo grouping, report paths, or version groups are needed.
5. Read `skills/shared/conventions.md` when naming, language, or repository conventions are needed.
6. Read `skills/shared/contract-spec.md` when checking or generating `## Contract:` blocks.
7. Read `skills/shared/api-extraction.md` when extracting API surfaces across languages.
8. Read `skills/shared/conformance-fixtures.md` when tester or release verification needs shared fixtures.
9. Read `skills/shared/scoring.md` when reports need health scores.
10. Read `skills/shared/strict-suppression.md` when audit or sync strict/lean behavior is relevant.
11. Prefer the deterministic helpers bundled in this plugin's
    `skills/shared/scripts/` over re-deriving their work in context: `discover.py`
    (ecosystem discovery, Step 0), `score.py` (health scores + release gate),
    `extract-markers.sh` (checkpoint markers). **Resolve their paths relative to
    this plugin** (`$CLAUDE_PLUGIN_ROOT` when set, else the absolute path this
    skill was loaded from) — never from the user's CWD, which is the project being
    operated on, not where the scripts live. The scripts are read-only and write
    only to stdout, so they are safe to run against any project. Each mirrors a
    shared markdown spec, which stays the authoritative fallback. See
    `skills/shared/scripts/README.md`.

Do not bulk-load every child skill. Do not read every shared reference unless the
selected workflow requires it.

## Core Consistency Model

Apcore-skills enforces three layers:

- **L1 Implementation**: implementation details may differ by language.
- **L2 Intent / Contract**: validation rules, error behavior, side-effect order, return shapes, and behavioral properties must match.
- **L2.5 Deep Chain**: public methods must call equivalent internal operations and state mutations in equivalent order.
- **L3 Public Signature**: public classes, functions, parameters, return types, interfaces, and constructors must align, allowing language conventions.

Documentation repos such as `apcore/` and related spec repos are the source of
truth. Implementation repos must conform to those specs, not to whichever SDK
happens to be most mature.

## Global Rules

- Preserve the user's requested language for user-facing responses.
- Start executing the loaded child workflow immediately; these skills are operational manuals, not background references.
- Never say the skill "didn't produce output" or "fallback to manual"; once loaded, execute the workflow steps.
- Every finding must be evidenced with concrete repo/file/symbol references.
- Do not manufacture findings to fill quotas. A checked dimension with zero findings is valid.
- For release, never push without explicit user approval.
- For SDK and integration scaffolding, complete the required skeleton and verification gates; do not ship partial stubs as complete.
- For tester, generate/run tests from spec clauses and report failing tests; do not implement production fixes inside tester.
- For sync, Phase A must complete before Phase B.
- Treat audit/sync review-compatible output as suitable input for `code-forge:fix --review`.

## Single-Skill Routes

### Dashboard

Read `commands/apcore-skills.md`.

Use when the user invokes `/apcore-skills` with no subcommand. Discover the
ecosystem root, list repos, versions, git status, latest audit/sync/tester
health, and available commands.

### Sync

Read `skills/sync/SKILL.md`.

Use for cross-language API, contract, deep-chain, and documentation consistency
checking and optional fixing. Honors flags such as `--phase`, `--fix`, `--scope`,
`--lang`, `--internal-check`, `--deep-chain`, `--strict`, and `--save`.

### SDK

Read `skills/sdk/SKILL.md`.

Use to bootstrap and implement a new language SDK or apcore project. It depends
on code-forge for port planning and implementation and must pass the post-impl
consistency gate.

### Integration

Read `skills/integration/SKILL.md`.

Use to bootstrap a new framework integration. Every integration must support the
core capabilities: scan endpoints, register modules, map request context, serve
via MCP, and export OpenAI tools format.

### Audit

Read `skills/audit/SKILL.md`.

Use for cross-repo ecosystem audit across API surface, naming, versions, docs,
tests, dependencies, configuration, contract parity, deep-chain parity, and
leanness. Respect lean vs strict mode.

### Tester

Read `skills/tester/SKILL.md`.

Use for spec-driven test generation and cross-language behavioral verification.
Tester produces tests and reports divergences; fixes are delegated to code-forge.

### Release

Read `skills/release/SKILL.md`.

Use for coordinated multi-repo release. It runs consistency gates before version
bump, updates version files and changelogs, verifies tests, commits locally, and
only pushes after explicit user approval.

## Ecosystem Assumptions

Expected layout is a common parent directory containing apcore ecosystem repos,
for example:

- `apcore/`
- `apcore-python/`
- `apcore-typescript/`
- `apcore-rust/`
- `apcore-mcp-python/`
- `apcore-mcp-typescript/`
- `django-apcore/`
- `flask-apcore/`
- `nestjs-apcore/`

Discovery is automatic based on naming conventions and can be customized with
`.apcore-skills.json` in the ecosystem root.

## Output Locations

Common saved outputs:

- Audit reports: `{ecosystem_root}/audit-report-*.md`
- Sync reports: `{ecosystem_root}/sync-report-*.md`
- Tester reports: `{ecosystem_root}/tester-report-*.md`
- Release audit/sync/tester reports: `{ecosystem_root}/release-*.md`
- SDK bootstrap tester reports: `{ecosystem_root}/sdk-bootstrap-tester-*.md`

When a child skill specifies a more precise path or a `--save` argument, follow
that instruction.

## Completion Criteria

Before finishing an apcore-skills task:

- Confirm which ecosystem root and repos were used.
- Mention the exact reports, files, repos, or version files changed/generated.
- For audit/sync/tester, summarize pass/fail counts and critical findings with concrete references.
- For SDK/integration, summarize scaffolded repo/files and verification gates completed.
- For release, summarize local commits and explicitly state whether anything was pushed.
