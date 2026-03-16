---
description: "Apcore ecosystem dashboard — ONLY when user explicitly invokes /apcore-skills. Do NOT auto-trigger based on project name or directory."
argument-hint: "[sync|sdk|integration|audit|release|tester] [args...]"
allowed-tools: [Read, Glob, Grep, Write, Edit, Bash, AskUserQuestion, Task, TaskCreate, TaskUpdate, TaskList, TaskGet]
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

Commands:

  /apcore-skills:sync [repos...] [--phase a|b|all] [--fix] [--scope core|mcp|all] [--save]
      Cross-language API + documentation consistency check & fix

  /apcore-skills:sdk <language> [--type core|mcp] [--ref <existing-sdk>]
      Bootstrap new language SDK

  /apcore-skills:integration <framework> [--lang python|typescript|go] [--ref <existing-integration>]
      Bootstrap new framework integration

  /apcore-skills:audit [--scope core|mcp|integrations|all] [--fix] [--save report.md]
      Deep cross-repo consistency audit

  /apcore-skills:tester [<repos...>] [--spec <feature>] [--mode generate|run|full] [--category unit|integration|boundary|protocol|all] [--save report.md]
      Spec-driven test generation & cross-language behavioral verification

  /apcore-skills:release <version> [--scope core|mcp|integrations|all] [--dry-run]
      Coordinated multi-repo release
```

Use `AskUserQuestion` to ask what to do next.

### Route B: Subcommand dispatch

For recognized subcommands, invoke the corresponding skill:
- `sync` → invoke `apcore-skills:sync` skill
- `sdk` → invoke `apcore-skills:sdk` skill
- `integration` → invoke `apcore-skills:integration` skill
- `audit` → invoke `apcore-skills:audit` skill
- `release` → invoke `apcore-skills:release` skill
- `tester` → invoke `apcore-skills:tester` skill
