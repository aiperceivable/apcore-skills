# apcore-skills

> Part of [aipartnerup/apcore-skills](https://github.com/aipartnerup/apcore-skills)

Apcore ecosystem management skill for Claude Code. Handles cross-language SDK synchronization, framework integration scaffolding, multi-repo audits, coordinated releases, and documentation alignment.

## Commands

| Command | Description |
|---------|-------------|
| `/apcore-skills` | Ecosystem dashboard — versions, coverage, health |
| `/apcore-skills:sync` | Cross-language API consistency check & fix |
| `/apcore-skills:sdk` | Bootstrap a new language SDK from reference |
| `/apcore-skills:integration` | Bootstrap a new framework integration |
| `/apcore-skills:audit` | Deep cross-repo consistency audit |
| `/apcore-skills:release` | Coordinated multi-repo release pipeline |
| `/apcore-skills:docs` | Documentation sync across repos |

## Ecosystem

The apcore ecosystem consists of:

**Core Protocol:**
- `apcore` — Protocol specification and documentation

**Core SDKs (must stay in sync):**
- `apcore-python` — Python SDK
- `apcore-typescript` — TypeScript SDK (npm: `apcore-js`)

**MCP Bridges (must stay in sync):**
- `apcore-mcp-python` — Python MCP server
- `apcore-mcp-typescript` — TypeScript MCP server (npm: `apcore-mcp`)

**Framework Integrations:**
- `django-apcore` — Django integration
- `flask-apcore` — Flask integration
- `nestjs-apcore` — NestJS integration
- `tiptap-apcore` — TipTap editor integration

**Shared Libraries:**
- `apcore-discovery-python` — Shared discovery utilities

## Prerequisites

1. All apcore ecosystem repos should be in a common parent directory (e.g., `~/WorkSpace/aipartnerup/`)
2. The `apcore/` protocol repo with `PROTOCOL_SPEC.md` is required for `sync` and `sdk` commands
3. No config file needed — ecosystem discovery is automatic based on directory naming conventions
4. Optional: `.apcore-skills.json` in the ecosystem root to customize discovery and version groups

## Integration with Other Skills

- **spec-forge** — Generate specifications for new features before implementing
- **code-forge** — Plan and implement features within individual repos
- **code-forge:port** — Port features from one language SDK to another
- **apcore-skills** — Ecosystem-level operations that span multiple repos
