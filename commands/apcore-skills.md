---
description: "Apcore ecosystem dashboard — ONLY when user explicitly invokes /apcore-skills. Do NOT auto-trigger based on project name or directory."
argument-hint: "[sync|sdk|integration|audit|release|tester] [args...]"
allowed-tools: [Read, Glob, Grep, Write, Edit, Bash, AskUserQuestion, Agent, TaskCreate, TaskUpdate, TaskList, TaskGet]
---

You are the apcore-skills orchestrator. Your job is to route subcommands or display the ecosystem dashboard.

The user invoked: `/apcore-skills $ARGUMENTS`

## Step 1: Parse Arguments

Parse `$ARGUMENTS` into `subcommand` and remaining `args`:

| Input Pattern | subcommand | args |
|---|---|---|
| `sync` | `sync` | (remaining) |
| `sdk go` | `sdk` | `go` |
| `integration fastapi` | `integration` | `fastapi` |
| `audit` | `audit` | (remaining) |
| `release v0.9.0` | `release` | `v0.9.0` |
| `tester apcore-python` | `tester` | `apcore-python` |
| (empty) | `dashboard` | — |

## Step 2: Route

### Route A: `dashboard` (no arguments)

Run `discover.py` as described in `skills/shared/ecosystem.md` §0.1–0.2,
including the markdown fallback. Either the Core protocol marker or a recognized
Surface component can locate the ecosystem root. Use the returned target paths,
versions, Git statuses, and `version_groups` for the dashboard.

**Consistency health.** Use the canonical glob patterns from
`skills/shared/ecosystem.md` §0.6a.
   - Latest audit: newest mtime match of `{ecosystem_root}/audit-report-*.md` ∪ `{ecosystem_root}/release-audit-*.md`. Extract D9 Leanness, D10 Contract Parity, and D11 Deep-Chain Parity scores from the Health Score section.
   - Latest sync: newest match of `{ecosystem_root}/sync-report-*.md` ∪ `{ecosystem_root}/release-sync-*.md` — EXCLUDE `-phase-a-` / `-phase-b-` partials (prefer combined reports). Extract Phase A / Phase B FAIL counts, contract-tier divergences (A-C-*), and deep-chain tier divergences (A-D-*).
   - Latest tester: newest match of `{ecosystem_root}/tester-report-*.md` ∪ `{ecosystem_root}/release-tester-*.md` ∪ `{ecosystem_root}/sdk-bootstrap-tester-*.md`. Extract conformance pass rate and divergent case count.
   - If no reports exist for a given signal, show `"— no recent report; run /apcore-skills:{audit|sync|tester} --save to populate"`.

Example display with a subset of targets:

```
apcore-skills — Ecosystem Dashboard

Ecosystem root: {ecosystem_root}
Targets discovered: {count}

  Target ID           | Path relative to ecosystem root | Version   | Git status
  apcore              | apcore/                         | —         | {git_status}
  apcore-python       | apcore/python/                  | {version} | {git_status}
  apcore-mcp          | apcore-surfaces/mcp/             | —         | {git_status}
  apcore-mcp-rust     | apcore-surfaces/mcp/rust/        | {version} | {git_status}
  apcore-a2a-rust     | apcore-surfaces/a2a/rust/        | {version} | {git_status}
  apcore-cli-python   | apcore-surfaces/cli/python/      | {version} | {git_status}
  apcore-toolkit-rust | apcore-surfaces/toolkit/rust/    | {version} | {git_status}
  django-apcore       | django-apcore/                  | {version} | {git_status}

Version Sync Check:
  {version_group}: {target IDs and versions}  {status}

Consistency Health (from latest reports):
  Last audit:     {date} — {audit-report-path}
    Contract Parity (D10):    {score}/100  {▓▓▓▓▓▓░░░░}
    Deep-Chain Parity (D11):  {score}/100  {▓▓▓▓▓▓▓▓░░}
    Leanness (D9):            {score}/100  {▓▓▓▓▓▓▓░░░}
    CRITICAL findings:        {N}  (top: [{top-finding-id}] {one-line})
  Last sync:      {date} — {sync-report-path}
    Phase A FAIL:          {N}
    Phase B FAIL:          {N}
    Contract-tier divergences (A-C-*):    {N}
    Deep-chain-tier divergences (A-D-*):  {N} critical / {N} warning / {N} inconclusive
  Last tester:    {date} — {tester-report-path}
    Conformance cases:    {pass}/{total} PASS
    Cross-language divergences: {N}

  (If no reports found: "Run /apcore-skills:audit --save to populate this section.")

Commands:

  /apcore-skills:sync [repos...] [--skip-docs] [--fix] [--scope core|mcp|integrations|all] [--lang python,typescript,...] [--internal-check none|contract|skeleton|behavior] [--deep-chain on|off] [--modules mod1,mod2,...] [--save]
      Cross-language API + contract + documentation consistency check & fix

  /apcore-skills:sdk <language> [--type core|mcp|a2a|cli|toolkit] [--ref <existing-sdk>]
      Bootstrap new language SDK

  /apcore-skills:integration <framework> [--lang python|typescript|go] [--ref <existing-integration>]
      Bootstrap new framework integration

  /apcore-skills:audit [--repo <target-id> | --scope core|mcp|integrations|all] [--fix] [--deep-chain on|off] [--strict] [--save report.md]
      Deep cross-repo consistency audit

  /apcore-skills:tester [<repos...>] [--spec <feature>] [--mode generate|run|full] [--category unit|integration|boundary|protocol|contract|conformance|all] [--save report.md]
      Spec-driven test generation & cross-language behavioral verification

  /apcore-skills:release <version> [--scope core|mcp|integrations|all] [--dry-run]
      Coordinated multi-repo release
```

Use `AskUserQuestion` to ask what to do next.

### Route B: Subcommand dispatch

For recognized subcommands, read and execute the corresponding SKILL.md directly (do NOT call the Skill tool — that would cause a recursive loop):
- `sync` → read and execute `../skills/sync/SKILL.md`
- `sdk` → read and execute `../skills/sdk/SKILL.md`
- `integration` → read and execute `../skills/integration/SKILL.md`
- `audit` → read and execute `../skills/audit/SKILL.md`
- `release` → read and execute `../skills/release/SKILL.md`
- `tester` → read and execute `../skills/tester/SKILL.md`
