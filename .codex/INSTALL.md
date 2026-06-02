# Installing apcore-skills for Codex

## Prerequisites

- Codex installed and configured
- Git installed
- Apcore ecosystem repositories cloned in a common parent directory

## Installation

1. Clone the repository:

```bash
git clone https://github.com/aipartnerup/apcore-skills.git
cd apcore-skills
```

2. Create the skills directory if it does not exist:

```bash
mkdir -p ~/.agents/skills
```

3. Symlink this repository to the Codex skills directory:

```bash
ln -s "$(pwd)" ~/.agents/skills/apcore-skills
```

If you are running this from the parent directory instead of the repository root,
use:

```bash
ln -s "$(pwd)/apcore-skills" ~/.agents/skills/apcore-skills
```

4. Verify the installation:

```bash
test -f ~/.agents/skills/apcore-skills/SKILL.md
ls ~/.agents/skills/apcore-skills/commands/
ls ~/.agents/skills/apcore-skills/skills/
# commands/ should include: apcore-skills.md  audit.md  integration.md
#                           release.md  sdk.md  sync.md  tester.md
# skills/ should include: audit  integration  release  sdk  sync  tester
```

## Usage

Once installed, the following commands are available in Codex:

- `/apcore-skills` - Ecosystem dashboard
- `/apcore-skills:sync ...` - Cross-language API, contract, deep-chain, and documentation consistency
- `/apcore-skills:sdk <language> [--type core|mcp] [--ref repo]` - Bootstrap a new SDK
- `/apcore-skills:integration <framework> [--lang python|typescript|go]` - Bootstrap framework integration
- `/apcore-skills:audit [--scope core|mcp|integrations|all]` - Deep ecosystem audit
- `/apcore-skills:tester ...` - Spec-driven test generation and behavioral verification
- `/apcore-skills:release <version> [--scope core|mcp|integrations|all]` - Coordinated release

## Notes

This repository is installed as a Codex skill tree via `~/.agents/skills`. It is
not currently packaged as a Codex plugin with `.codex-plugin/plugin.json` because
the repository contains `skills/shared/` as shared reference files rather than an
invokable skill directory. Packaging as a Codex plugin would require either
moving shared references out of `skills/` or otherwise adapting the layout to the
plugin validator.

The root Codex skill is intentionally conservative: it should trigger only for
explicit apcore-skills requests, not just because the current directory contains
an apcore repository.

## Uninstall

```bash
rm ~/.agents/skills/apcore-skills
```
