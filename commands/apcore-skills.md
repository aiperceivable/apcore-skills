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

Run the ecosystem discovery from the shared ecosystem module:

1. Detect ecosystem root (search for `apcore/PROTOCOL_SPEC.md` in parent/sibling directories)
2. Scan for all apcore repositories
3. Extract versions from build config files
4. Check git status for each repo
5. **Surface consistency health** — use the canonical glob patterns from `skills/shared/ecosystem.md` §0.6a (single source of truth for report paths):
   - Latest audit: newest mtime match of `{ecosystem_root}/audit-report-*.md` ∪ `{ecosystem_root}/release-audit-*.md`. Extract D9 Leanness, D10 Contract Parity, and D11 Deep-Chain Parity scores from the Health Score section.
   - Latest sync: newest match of `{ecosystem_root}/sync-report-*.md` ∪ `{ecosystem_root}/release-sync-*.md` — EXCLUDE `-phase-a-` / `-phase-b-` partials (prefer combined reports). Extract Phase A / Phase B FAIL counts, contract-tier divergences (A-C-*), and deep-chain tier divergences (A-D-*).
   - Latest tester: newest match of `{ecosystem_root}/tester-report-*.md` ∪ `{ecosystem_root}/release-tester-*.md` ∪ `{ecosystem_root}/sdk-bootstrap-tester-*.md`. Extract conformance pass rate and divergent case count.
   - If no reports exist for a given signal, show `"— no recent report; run /apcore-skills:{audit|sync|tester} --save to populate"`.

Display:

```
apcore-skills — Ecosystem Dashboard

Ecosystem root: /path/to/aipartnerup/
Repos discovered: {count}

  Type          | Repo                    | Lang       | Version | Status
  protocol      | apcore                  | —          | —       | clean
  core-sdk      | apcore-python           | Python     | 0.7.0   | clean
  core-sdk      | apcore-typescript       | TypeScript | 0.7.1   | 2 modified
  core-sdk      | apcore-rust             | Rust       | 0.1.0   | clean
  mcp-bridge    | apcore-mcp-python       | Python     | 0.8.1   | clean
  mcp-bridge    | apcore-mcp-typescript   | TypeScript | 0.8.1   | clean
  integration   | django-apcore           | Python     | 0.2.0   | clean
  integration   | flask-apcore            | Python     | 0.3.0   | clean
  integration   | nestjs-apcore           | TypeScript | 0.1.0   | clean
  integration   | tiptap-apcore           | TypeScript | 0.1.0   | clean

Version Sync Check:
  core group:  apcore-python=0.7.0, apcore-typescript=0.7.1, apcore-rust=0.1.0  ⚠ MISMATCH
  mcp group:   apcore-mcp-python=0.8.1, apcore-mcp-typescript=0.8.1  ✓ OK

Consistency Health (from latest reports):
  Last audit:     {date} — audit-report-{date}.md
    Contract Parity (D10):    {score}/100  {▓▓▓▓▓▓░░░░}
    Deep-Chain Parity (D11):  {score}/100  {▓▓▓▓▓▓▓▓░░}
    Leanness (D9):            {score}/100  {▓▓▓▓▓▓▓░░░}
    CRITICAL findings:        {N}  (top: [{top-finding-id}] {one-line})
  Last sync:      {date} — sync-report-{date}.md
    Phase A FAIL:          {N}
    Phase B FAIL:          {N}
    Contract-tier divergences (A-C-*):    {N}
    Deep-chain-tier divergences (A-D-*):  {N} critical / {N} warning / {N} inconclusive
  Last tester:    {date} — tester-{date}.md
    Conformance cases:    {pass}/{total} PASS
    Cross-language divergences: {N}

  (If no reports found: "Run /apcore-skills:audit --save to populate this section.")

Commands:

  /apcore-skills:sync [repos...] [--phase a|b|all] [--fix] [--scope core|mcp|all] [--lang python,typescript,...] [--internal-check none|contract|skeleton|behavior] [--deep-chain on|off] [--save]
      Cross-language API + contract + documentation consistency check & fix

  /apcore-skills:sdk <language> [--type core|mcp] [--ref <existing-sdk>]
      Bootstrap new language SDK

  /apcore-skills:integration <framework> [--lang python|typescript|go] [--ref <existing-integration>]
      Bootstrap new framework integration

  /apcore-skills:audit [--scope core|mcp|integrations|all] [--fix] [--no-deep-chain] [--save report.md]
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
