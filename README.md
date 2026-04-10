# apcore-skills

> Part of [aipartnerup/apcore-skills](https://github.com/aipartnerup/apcore-skills)

Apcore ecosystem management skill for Claude Code. Handles cross-language SDK synchronization, framework integration scaffolding, multi-repo audits, spec-driven test generation, coordinated releases, and documentation alignment.

## Commands

| Command | Usage | Description |
|---------|-------|-------------|
| `/apcore-skills` | | Ecosystem dashboard — versions, git status, health, all commands |
| `/apcore-skills:sync` | `[repos...] [--phase a\|b\|all] [--fix] [--scope core\|mcp\|all] [--lang python,typescript,...] [--internal-check none\|skeleton\|behavior] [--save]` | Cross-language API + documentation consistency check & fix |
| `/apcore-skills:sdk` | `<language> [--type core\|mcp] [--ref <existing-sdk>]` | Bootstrap a new language SDK from reference |
| `/apcore-skills:integration` | `<framework> [--lang python\|typescript\|go] [--ref <existing-integration>]` | Bootstrap a new framework integration |
| `/apcore-skills:audit` | `[--scope core\|mcp\|integrations\|all] [--fix] [--save report.md]` | Deep cross-repo consistency audit |
| `/apcore-skills:tester` | `[<repos...>] [--spec <feature>] [--mode generate\|run\|full] [--category unit\|integration\|boundary\|protocol\|all] [--save report.md]` | Spec-driven test generation & cross-language behavioral verification |
| `/apcore-skills:release` | `<version> [--scope core\|mcp\|integrations\|all] [--dry-run]` | Coordinated multi-repo release pipeline |

## Ecosystem

The apcore ecosystem consists of:

**Core Protocol:**
- `apcore` — Protocol specification and documentation

**Core SDKs (must stay in sync):**
- `apcore-python` — Python SDK
- `apcore-typescript` — TypeScript SDK (npm: `apcore-js`)
- `apcore-rust` — Rust SDK

**MCP Bridges (must stay in sync):**
- `apcore-mcp-python` — Python MCP server
- `apcore-mcp-typescript` — TypeScript MCP server (npm: `apcore-mcp`)
- `apcore-mcp-rust` — Rust MCP server

**A2A Bridges:**
- `apcore-a2a-python` — Python A2A bridge
- `apcore-a2a-typescript` — TypeScript A2A bridge

**Toolkit:**
- `apcore-toolkit-python` — Python toolkit
- `apcore-toolkit-typescript` — TypeScript toolkit

**CLI:**
- `apcore-cli` — Command-line interface

**Framework Integrations:**
- `django-apcore` — Django integration
- `flask-apcore` — Flask integration
- `nestjs-apcore` — NestJS integration
- `tiptap-apcore` — TipTap editor integration

**Shared Libraries:**
- `apcore-discovery-python` — Shared discovery utilities

## Prerequisites

1. All apcore ecosystem repos should be in a common parent directory (e.g., `~/WorkSpace/aipartnerup/`)
2. The `apcore/` protocol repo with `PROTOCOL_SPEC.md` is required for `sync`, `sdk`, and `tester` (core-sdk target) commands
3. Spec repos per project type: `apcore-mcp/` (MCP bridges), `apcore-a2a/` (A2A bridges), `apcore-cli/` (CLI), `apcore-toolkit/` (toolkit)
4. No config file needed — ecosystem discovery is automatic based on directory naming conventions
5. Optional: `.apcore-skills.json` in the ecosystem root to customize discovery and version groups
6. **[code-forge](https://github.com/tercel/code-forge)** skill required for `sdk` and `integration` commands (generates `.code-forge.json` and uses `code-forge:port`, `code-forge:plan`, `code-forge:impl`)

## Integration with Other Skills

- **spec-forge** — Generate specifications for new features before implementing
- **code-forge:plan / code-forge:impl** — Plan and implement features within individual repos
- **code-forge:port** — Port features from one language SDK to another
- **code-forge:tdd / code-forge:fix** — Fix failures surfaced by `tester` via TDD red-green cycle
- **code-forge:verify** — Verify test results before claiming fixes are complete
- **apcore-skills** — Ecosystem-level operations that span multiple repos
