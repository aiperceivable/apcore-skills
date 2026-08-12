#!/usr/bin/env python3
"""apcore-skills mechanical audit dimensions — deterministic fast path.

Implements the purely mechanical audit dimensions from
`skills/audit/references/dimension-prompts.md` as code, so audit Step 2 does not
have to spawn one LLM sub-agent per dimension for checks that have no judgment
component:

    D2 — Naming Conventions
    D3 — Version Sync
    D6 — Dependencies   (mechanical subset; see `not_covered` in the output)
    D7 — Configuration  (integrations only)
    D8 — Project Structure

The semantic dimensions stay LLM-driven by design and are NOT implemented here:
D1 (API surface normalization & comparison), D4 (documentation), D5 (test
execution), D9 (bloat/reachability), D10 (contract parity), D11 (deep chain).
See `shared/scripts/README.md` — do not extend this script into them.

**Suppression Gate.** The gate in dimension-prompts.md exists to catch LLM
failure modes: speculation, security theater on internal flows, padded findings,
and claims about greps that were never run. A deterministic checker cannot fail
gate 1/3/5/6 — it reports exactly what it matched, cites file:line by
construction, and never pads. Gate 2 (trust boundary) does not apply: none of
these dimensions emit security findings. Gate 4 (severity calibration) is
encoded as fixed severity per rule below. The gate text is therefore NOT
inherited by this fast path.

Output: a single JSON object on stdout:
  {script, version, ecosystem_root, repos_scanned[], dimensions{D2,D3,D6,D7,D8}}
Each dimension carries {dimension, finding_count, findings[], checked[],
not_covered[]}. `not_covered` is load-bearing: it tells the orchestrator which
rules from the markdown this run did NOT evaluate, so coverage is never silently
reduced.

The markdown in dimension-prompts.md remains the authoritative specification and
the fallback when Python is unavailable or this script errors.

Stdlib only. No third-party dependencies.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import discover  # reuse classification + every version-string parser
except Exception:  # pragma: no cover - surfaced as JSON error by main()
    discover = None

SCRIPT_VERSION = "1"

# --------------------------------------------------------------------------
# Naming predicates (D2)
# --------------------------------------------------------------------------

RE_SNAKE = re.compile(r"^_*[a-z][a-z0-9_]*$")
RE_PASCAL = re.compile(r"^[A-Z][A-Za-z0-9]*$")
RE_CAMEL = re.compile(r"^_*[a-z][A-Za-z0-9]*$")
RE_KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
RE_UPPER_SNAKE = re.compile(r"^[A-Z][A-Z0-9_]*$")


def is_snake(s):
    return bool(RE_SNAKE.match(s))


def is_pascal(s):
    return bool(RE_PASCAL.match(s))


def is_camel(s):
    return bool(RE_CAMEL.match(s))


def is_kebab(s):
    return bool(RE_KEBAB.match(s))


def is_upper_snake(s):
    return bool(RE_UPPER_SNAKE.match(s))


# --------------------------------------------------------------------------
# Source scanning helpers
# --------------------------------------------------------------------------

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
    "target", ".mypy_cache", ".pytest_cache", ".tox", "vendor", ".next",
}

PY_CLASS = re.compile(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)")
PY_DEF = re.compile(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)")
PY_ENUM_BASE = re.compile(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)")
PY_ENUM_MEMBER = re.compile(r"^\s{4}([A-Za-z_][A-Za-z0-9_]*)\s*=")

TS_CLASS = re.compile(r"^\s*(?:export\s+)?(?:abstract\s+)?class\s+([A-Za-z_$][\w$]*)")
TS_FUNC = re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)")
TS_ENUM = re.compile(r"^\s*(?:export\s+)?(?:const\s+)?enum\s+([A-Za-z_$][\w$]*)")
TS_ENUM_MEMBER = re.compile(r"^\s+([A-Za-z_$][\w$]*)\s*[=,]")


def walk_sources(root: Path, suffixes):
    """Yield source files under root, skipping vendor/build dirs."""
    if not root.is_dir():
        return
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix not in suffixes:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def read_lines(path: Path):
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []


def rel(path: Path, repo_path: Path):
    try:
        return str(path.relative_to(repo_path))
    except ValueError:
        return str(path)


def finding(severity, repo, detail, location, fix, evidence=None):
    f = {"severity": severity, "repo": repo, "detail": detail,
         "location": location, "fix": fix}
    if evidence:
        f["evidence"] = evidence
    return f


def dim(name, findings, checked, not_covered):
    return {"dimension": name, "finding_count": len(findings),
            "findings": findings, "checked": checked,
            "not_covered": not_covered}


# --------------------------------------------------------------------------
# D2 — Naming Conventions
# --------------------------------------------------------------------------

def check_d2(repos):
    findings = []
    for r in repos:
        repo_path = Path(r["path"])
        name = r["name"]
        src = repo_path / "src"
        lang = (r.get("language") or "").lower()

        if not src.is_dir():
            continue

        if lang == "python":
            for f in walk_sources(src, {".py"}):
                stem = f.stem
                if stem != "__init__" and not is_snake(stem):
                    findings.append(finding(
                        "warning", name,
                        f"Python source file '{f.name}' is not snake_case",
                        rel(f, repo_path),
                        f"Rename to {re.sub(r'(?<!^)(?=[A-Z])', '_', stem).lower()}.py",
                    ))
                for i, line in enumerate(read_lines(f), 1):
                    m = PY_CLASS.match(line)
                    if m:
                        cls = m.group(1)
                        if not is_pascal(cls):
                            findings.append(finding(
                                "warning", name,
                                f"Class '{cls}' is not PascalCase",
                                f"{rel(f, repo_path)}:{i}",
                                "Rename the class to PascalCase",
                                evidence=f"{rel(f, repo_path)}:{i}: {line.strip()}",
                            ))
                        base = PY_ENUM_BASE.match(line)
                        if base and "Enum" in base.group(2):
                            findings.extend(_py_enum_members(
                                f, i, read_lines(f), repo_path, name, cls))
                        continue
                    m = PY_DEF.match(line)
                    if m:
                        fn = m.group(1)
                        if fn.startswith("__") and fn.endswith("__"):
                            continue
                        if not is_snake(fn):
                            findings.append(finding(
                                "warning", name,
                                f"Function '{fn}' is not snake_case",
                                f"{rel(f, repo_path)}:{i}",
                                "Rename the function to snake_case",
                                evidence=f"{rel(f, repo_path)}:{i}: {line.strip()}",
                            ))

        elif lang in ("typescript", "javascript"):
            for f in walk_sources(src, {".ts", ".tsx", ".js"}):
                stem = f.stem.replace(".d", "")
                if stem not in ("index",) and not is_kebab(stem):
                    findings.append(finding(
                        "warning", name,
                        f"TypeScript source file '{f.name}' is not kebab-case",
                        rel(f, repo_path),
                        "Rename the file to kebab-case",
                    ))
                lines = read_lines(f)
                for i, line in enumerate(lines, 1):
                    m = TS_CLASS.match(line)
                    if m and not is_pascal(m.group(1)):
                        findings.append(finding(
                            "warning", name,
                            f"Class '{m.group(1)}' is not PascalCase",
                            f"{rel(f, repo_path)}:{i}",
                            "Rename the class to PascalCase",
                            evidence=f"{rel(f, repo_path)}:{i}: {line.strip()}",
                        ))
                    m = TS_FUNC.match(line)
                    if m and not is_camel(m.group(1)):
                        findings.append(finding(
                            "warning", name,
                            f"Function '{m.group(1)}' is not camelCase",
                            f"{rel(f, repo_path)}:{i}",
                            "Rename the function to camelCase",
                            evidence=f"{rel(f, repo_path)}:{i}: {line.strip()}",
                        ))
                    m = TS_ENUM.match(line)
                    if m:
                        if not is_pascal(m.group(1)):
                            findings.append(finding(
                                "warning", name,
                                f"Enum '{m.group(1)}' is not PascalCase",
                                f"{rel(f, repo_path)}:{i}",
                                "Rename the enum to PascalCase",
                                evidence=f"{rel(f, repo_path)}:{i}: {line.strip()}",
                            ))
                        findings.extend(_ts_enum_members(
                            f, i, lines, repo_path, name, m.group(1)))

        # Error class naming (language-agnostic on the class name itself).
        findings.extend(_error_class_names(repo_path, name, lang))

        # Package name convention.
        findings.extend(_package_name(r, repo_path, name, lang))

    return dim(
        "D2 — Naming Conventions", findings,
        checked=[
            "source filename casing (py: snake_case, ts: kebab-case)",
            "class PascalCase, function casing per language",
            "enum name PascalCase, enum members UPPER_SNAKE",
            "error class names end with 'Error'",
            "package name convention (snake_case / kebab-case)",
        ],
        not_covered=[
            "import/export *aliases* in the main module file — requires resolving "
            "re-export chains; left to D1 (API surface, LLM)",
        ],
    )


def _py_enum_members(f, class_line, lines, repo_path, name, cls):
    out = []
    for j in range(class_line, min(class_line + 200, len(lines))):
        line = lines[j]
        if line.strip() and not line.startswith((" ", "\t")):
            break
        m = PY_ENUM_MEMBER.match(line)
        if m and not is_upper_snake(m.group(1)):
            out.append(finding(
                "warning", name,
                f"Enum member '{cls}.{m.group(1)}' is not UPPER_SNAKE",
                f"{rel(f, repo_path)}:{j + 1}",
                "Rename the enum member to UPPER_SNAKE",
                evidence=f"{rel(f, repo_path)}:{j + 1}: {line.strip()}",
            ))
    return out


def _ts_enum_members(f, enum_line, lines, repo_path, name, enum_name):
    out = []
    for j in range(enum_line, min(enum_line + 200, len(lines))):
        line = lines[j]
        if "}" in line:
            break
        m = TS_ENUM_MEMBER.match(line)
        if m and not is_upper_snake(m.group(1)):
            out.append(finding(
                "warning", name,
                f"Enum member '{enum_name}.{m.group(1)}' is not UPPER_SNAKE",
                f"{rel(f, repo_path)}:{j + 1}",
                "Rename the enum member to UPPER_SNAKE",
                evidence=f"{rel(f, repo_path)}:{j + 1}: {line.strip()}",
            ))
    return out


EXC_BASE = re.compile(
    r"^\s*(?:export\s+)?(?:abstract\s+)?class\s+([A-Za-z_$][\w$]*)"
    r"\s*(?:\(([^)]*)\)|extends\s+([A-Za-z_$][\w$.]*))"
)


def _error_class_names(repo_path: Path, name, lang):
    """Flag classes that derive from an exception base but lack an Error suffix."""
    out = []
    suffixes = {".py"} if lang == "python" else {".ts", ".tsx", ".js"}
    for f in walk_sources(repo_path / "src", suffixes):
        for i, line in enumerate(read_lines(f), 1):
            m = EXC_BASE.match(line)
            if not m:
                continue
            cls = m.group(1)
            base = (m.group(2) or m.group(3) or "")
            if not re.search(r"Error|Exception", base):
                continue
            if not cls.endswith("Error"):
                out.append(finding(
                    "warning", name,
                    f"Error class '{cls}' does not end with 'Error' "
                    f"(derives from {base.strip()})",
                    f"{rel(f, repo_path)}:{i}",
                    f"Rename '{cls}' to '{cls}Error'",
                    evidence=f"{rel(f, repo_path)}:{i}: {line.strip()}",
                ))
    return out


def _package_name(r, repo_path: Path, name, lang):
    out = []
    pkg = r.get("package_name")
    if not pkg:
        return out
    bare = pkg.split("/")[-1] if pkg.startswith("@") else pkg
    if lang == "python" and not is_snake(bare.replace("-", "_")):
        out.append(finding(
            "warning", name,
            f"Python package name '{pkg}' is not snake_case-compatible",
            "pyproject.toml", "Rename the distribution/package to snake_case",
        ))
    if lang in ("typescript", "javascript") and not is_kebab(bare):
        out.append(finding(
            "warning", name,
            f"npm package name '{pkg}' is not kebab-case",
            "package.json", "Rename the package to kebab-case",
        ))
    return out


# --------------------------------------------------------------------------
# D3 — Version Sync
# --------------------------------------------------------------------------

def major_minor(v):
    if not v:
        return None
    m = re.match(r"^v?(\d+)\.(\d+)", str(v))
    return f"{m.group(1)}.{m.group(2)}" if m else None


def check_d3(repos, version_groups):
    findings = []
    by_name = {r["name"]: r for r in repos}

    # 1+2. Group members must agree on major.minor.
    for group, members in sorted((version_groups or {}).items()):
        pairs = [(n, by_name[n].get("version")) for n in members if n in by_name]
        known = [(n, v) for n, v in pairs if v]
        mms = {major_minor(v) for _, v in known}
        mms.discard(None)
        if len(mms) > 1:
            detail = ", ".join(f"{n}={v}" for n, v in sorted(known))
            findings.append(finding(
                "critical", group,
                f"Version group '{group}' disagrees on major.minor: {detail}",
                "build config of each listed repo",
                f"Align all '{group}' repos to a single major.minor",
                evidence=detail,
            ))
        for n, v in pairs:
            if not v:
                findings.append(finding(
                    "warning", n,
                    f"No version could be parsed for '{n}' (group '{group}')",
                    "build config",
                    "Add an explicit version to the build config",
                ))

    # 3. Intra-repo consistency: build config vs in-source version constant.
    for r in repos:
        repo_path = Path(r["path"])
        declared = r.get("version")
        if not declared:
            continue
        for src_file, parser, label in _insource_version_candidates(repo_path, r):
            text = _read(src_file)
            if text is None:
                continue
            found = parser(text)
            if found and found != declared:
                findings.append(finding(
                    "critical", r["name"],
                    f"Version mismatch inside repo: build config={declared}, "
                    f"{label}={found}",
                    rel(src_file, repo_path),
                    f"Set {label} to {declared} (or bump both together)",
                    evidence=f"{rel(src_file, repo_path)}: {label} = {found}",
                ))

    return dim(
        "D3 — Version Sync", findings,
        checked=[
            "core-sdk group major.minor agreement",
            "mcp-bridge group major.minor agreement",
            "build config version vs in-source __version__ / VERSION",
            "unparseable version detection",
        ],
        not_covered=[
            "integration -> core SDK dependency compatibility ranges "
            "(needs semver range semantics; see D6 dependency findings)",
        ],
    )


def _read(path: Path):
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _insource_version_candidates(repo_path: Path, r):
    """(file, parser, label) triples for in-source version constants."""
    assert discover is not None  # guaranteed: run() returns early on import failure
    out = []
    lang = (r.get("language") or "").lower()
    if lang == "python":
        for cand in sorted(repo_path.glob("src/*/__init__.py")) + \
                sorted(repo_path.glob("src/*/_version.py")):
            out.append((cand, discover.parse_dunder_version, "__version__"))
    elif lang in ("typescript", "javascript"):
        for cand in (repo_path / "src" / "index.ts", repo_path / "src" / "index.js"):
            if cand.exists():
                out.append((cand, discover.parse_ts_version, "VERSION"))
    return out


# --------------------------------------------------------------------------
# D6 — Dependencies (mechanical subset)
# --------------------------------------------------------------------------

DEV_TOOLING = {
    "python": {"linter": ("ruff", "flake8", "pylint"),
               "type_checker": ("mypy", "pyright"),
               "test_framework": ("pytest",)},
    "typescript": {"linter": ("eslint", "biome", "oxlint"),
                   "type_checker": ("typescript",),
                   "test_framework": ("vitest", "jest", "mocha")},
    "javascript": {"linter": ("eslint", "biome", "oxlint"),
                   "type_checker": ("typescript",),
                   "test_framework": ("vitest", "jest", "mocha")},
}

RE_DEP_PY = re.compile(r"^\s*[\"']?([A-Za-z0-9._-]+)\s*(?:[><=~!^]=?\s*([0-9][^\"',\]]*))?")
RE_DEP_JSON = re.compile(r"\"([^\"]+)\"\s*:\s*\"([^\"]+)\"")


def _deps_python(repo_path: Path):
    """Return (runtime{name:spec}, dev_tool_names_seen)."""
    text = _read(repo_path / "pyproject.toml")
    runtime, seen = {}, set()
    if not text:
        return runtime, seen
    block = re.search(r"(?ms)^dependencies\s*=\s*\[(.*?)\]", text)
    if block:
        # Split on the quoted entries, not on newlines: `deps = ["a>=1", "b>=2"]`
        # is legal TOML on a single line and a line-wise scan would see only "a".
        for raw in re.findall(r"[\"']([^\"']+)[\"']", block.group(1)):
            m = RE_DEP_PY.match(raw.strip())
            if m and m.group(1):
                runtime[m.group(1).lower()] = (m.group(2) or "").strip()
    for name in re.findall(r"[\"']([A-Za-z0-9._-]+)[\"']", text):
        seen.add(name.lower())
    return runtime, seen


def _deps_node(repo_path: Path):
    text = _read(repo_path / "package.json")
    runtime, seen = {}, set()
    if not text:
        return runtime, seen
    try:
        data = json.loads(text)
    except ValueError:
        return runtime, seen
    for k, v in (data.get("dependencies") or {}).items():
        runtime[k.lower()] = v
    for section in ("dependencies", "devDependencies", "peerDependencies"):
        for k in (data.get(section) or {}):
            seen.add(k.lower())
    return runtime, seen


def check_d6(repos):
    findings = []
    runtime_by_repo = {}

    for r in repos:
        repo_path = Path(r["path"])
        name = r["name"]
        lang = (r.get("language") or "").lower()
        if lang == "python":
            runtime, seen = _deps_python(repo_path)
            cfg = "pyproject.toml"
        elif lang in ("typescript", "javascript"):
            runtime, seen = _deps_node(repo_path)
            cfg = "package.json"
        else:
            continue

        if not (repo_path / cfg).exists():
            findings.append(finding(
                "warning", name, f"No build config found for {name}",
                cfg, f"Add a {cfg}",
            ))
            continue

        runtime_by_repo[name] = (lang, runtime)
        tooling = DEV_TOOLING.get(lang, {})
        for role, candidates in sorted(tooling.items()):
            if not any(c in seen for c in candidates):
                findings.append(finding(
                    "warning", name,
                    f"No {role.replace('_', ' ')} declared "
                    f"(expected one of: {', '.join(candidates)})",
                    cfg,
                    f"Add a {role.replace('_', ' ')} to dev dependencies",
                ))

    # Duplicate dependency at conflicting versions across repos. Keyed by
    # (language, dep): a PyPI `httpx` and an npm `httpx` are unrelated packages,
    # so comparing their version specs would emit a nonsense finding.
    versions = {}
    for repo, (lang, deps) in runtime_by_repo.items():
        for dep, spec in deps.items():
            if spec:
                versions.setdefault((lang, dep), {}).setdefault(spec, []).append(repo)
    for (lang, dep), specs in sorted(versions.items()):
        if len(specs) > 1:
            detail = "; ".join(
                f"{spec} in {', '.join(sorted(rs))}" for spec, rs in sorted(specs.items()))
            findings.append(finding(
                "warning", "ecosystem",
                f"Dependency '{dep}' ({lang}) pinned at conflicting versions "
                f"across repos: {detail}",
                "build configs", f"Align '{dep}' to one version range",
                evidence=detail,
            ))

    return dim(
        "D6 — Dependencies", findings,
        checked=[
            "build config presence",
            "dev tooling present (linter / type checker / test framework)",
            "same dependency at conflicting versions across repos",
        ],
        not_covered=[
            "schema-validation lib version *expectations* (needs the spec's "
            "canonical version table)",
            "MCP SDK compatibility semantics",
            "known-vulnerability patterns — belongs to a real advisory DB, not "
            "a static rule; run a dedicated audit tool instead",
        ],
    )


# --------------------------------------------------------------------------
# D7 — Configuration (integrations only)
# --------------------------------------------------------------------------

CANONICAL_SETTINGS = {
    "APCORE_ENABLED": "True",
    "APCORE_DEBUG": "False",
    "APCORE_SCANNERS": '["auto"]',
    "APCORE_INCLUDE_PATHS": "[]",
    "APCORE_EXCLUDE_PATHS": "[]",
    "APCORE_MODULE_PREFIX": '""',
    "APCORE_AUTH_ENABLED": "False",
    "APCORE_AUTH_STRATEGY": '"bearer"',
    "APCORE_TRANSPORT": '"stdio"',
    "APCORE_HOST": '"0.0.0.0"',
    "APCORE_PORT": "8808",
}

RE_SETTING = re.compile(r"\b(APCORE_[A-Z0-9_]+)\b\s*[:=]\s*([^\n,;]+)")


def normalize_default(raw):
    """Normalize a default across languages so True/true and '' quoting agree."""
    if raw is None:
        return None
    s = raw.strip().rstrip(",;").strip()
    s = re.sub(r"^[A-Za-z_][\w.]*\s*\(\s*", "", s)  # strip Field( / env( wrapper
    s = s.rstrip(")").strip()
    s = re.sub(r":\s*[A-Za-z_][\w\[\]<>., |]*\s*=\s*", "", s)
    low = s.lower()
    if low in ("true", "false"):
        return low.capitalize()
    if low in ("none", "null", "undefined"):
        return "None"
    s = s.replace("'", '"')
    s = re.sub(r"\s+", "", s)
    return s


def check_d7(repos):
    findings = []
    matrix = {}
    integrations = [r for r in repos if r.get("type") == "integration"]

    for r in integrations:
        repo_path = Path(r["path"])
        name = r["name"]
        cfg_files = [p for p in walk_sources(repo_path / "src", {".py", ".ts"})
                     if p.stem == "config"]
        if not cfg_files:
            findings.append(finding(
                "warning", name, f"Config file not found for {name}",
                "src/*/config.{py,ts}", "Add a config module declaring APCORE_* settings",
            ))
            continue

        found = {}
        for cfg in cfg_files:
            for i, line in enumerate(read_lines(cfg), 1):
                for m in RE_SETTING.finditer(line):
                    found.setdefault(m.group(1), (normalize_default(m.group(2)),
                                                  f"{rel(cfg, repo_path)}:{i}"))

        for setting, (value, loc) in sorted(found.items()):
            matrix.setdefault(setting, {})[name] = value

        # Missing canonical settings.
        for setting in sorted(CANONICAL_SETTINGS):
            if setting not in found:
                findings.append(finding(
                    "warning", name,
                    f"Required canonical setting {setting} is missing",
                    rel(cfg_files[0], repo_path),
                    f"Declare {setting} with default "
                    f"{CANONICAL_SETTINGS[setting]}",
                ))

        # Default mismatch against canonical -> CRITICAL per the markdown.
        for setting, expected in sorted(CANONICAL_SETTINGS.items()):
            if setting not in found:
                continue
            actual, loc = found[setting]
            if actual is not None and actual != normalize_default(expected):
                findings.append(finding(
                    "critical", name,
                    f"{setting} default is {actual}, canonical is "
                    f"{normalize_default(expected)}",
                    loc, f"Change the default to {normalize_default(expected)}",
                    evidence=f"{loc}: {setting} = {actual}",
                ))

        # Unauthorized bare APCORE_* setting -> CRITICAL per the markdown.
        framework_token = name.replace("apcore-", "").replace("-apcore", "")
        framework_token = re.sub(r"[^A-Za-z0-9]", "", framework_token).upper()
        for setting, (_, loc) in sorted(found.items()):
            if setting in CANONICAL_SETTINGS:
                continue
            tail = setting[len("APCORE_"):]
            if framework_token and tail.startswith(framework_token + "_"):
                findings.append(finding(
                    "warning", name,
                    f"Framework-specific setting {setting} — verify it is "
                    f"documented under a Framework-specific settings heading",
                    loc, "Document it in docs/features/config.md",
                ))
            else:
                findings.append(finding(
                    "critical", name,
                    f"Unauthorized canonical setting {setting} — not in the "
                    f"canonical list",
                    loc,
                    f"Use APCORE_{framework_token or 'FRAMEWORK'}_* for "
                    f"framework-specific settings, or propose an addition to "
                    f"shared/conventions.md",
                    evidence=f"{loc}: {setting}",
                ))

    config_matrix = []
    for setting in sorted(matrix):
        row = {"setting": setting}
        row.update(matrix[setting])
        row["consistent"] = len(set(matrix[setting].values())) <= 1
        config_matrix.append(row)

    d = dim(
        "D7 — Configuration", findings,
        checked=[
            "canonical setting presence",
            "canonical default match (critical on mismatch)",
            "unauthorized bare APCORE_* settings",
            "cross-integration value consistency (CONFIG_MATRIX)",
        ],
        not_covered=[
            "type declarations per setting — extraction is language-specific "
            "and regex-based here; the matrix carries values only",
            "whether a framework-specific setting is *actually* documented "
            "(needs a docs read; emitted as warning to verify)",
        ],
    )
    d["config_matrix"] = [r for r in config_matrix if not r["consistent"]]
    d["config_matrix_consistent_count"] = sum(
        1 for r in config_matrix if r["consistent"])
    return d


# --------------------------------------------------------------------------
# D8 — Project Structure
# --------------------------------------------------------------------------

EXPECTED_SUBDIRS = {
    "core-sdk": ["middleware", "registry", "schema", "observability", "utils"],
    "mcp-bridge": ["server", "auth", "adapters", "converters"],
    "integration": ["scanners", "output"],
}
REQUIRED_FILES = ["README.md", "CHANGELOG.md", "LICENSE", ".gitignore"]
BUILD_FILES = ["pyproject.toml", "package.json", "Cargo.toml", "go.mod",
               "pom.xml", "build.gradle", "build.gradle.kts", "mix.exs",
               "composer.json", "Package.swift"]


def check_d8(repos):
    findings = []
    for r in repos:
        repo_path = Path(r["path"])
        name = r["name"]
        rtype = r.get("type")

        if not repo_path.is_dir() or not any(repo_path.iterdir()):
            findings.append(finding(
                "info", name, f"Repo {name} is empty or placeholder",
                str(repo_path), "Populate the repo or remove it from the ecosystem",
            ))
            continue

        src = repo_path / "src"
        if not src.is_dir():
            findings.append(finding(
                "warning", name, "No src/ directory",
                "src/", "Create src/ per the project structure convention",
            ))
        else:
            expected = EXPECTED_SUBDIRS.get(rtype, [])
            present = {p.name for p in src.rglob("*") if p.is_dir()}
            for sub in expected:
                if sub not in present:
                    findings.append(finding(
                        "warning", name,
                        f"Expected {rtype} subdirectory '{sub}/' not found under src/",
                        f"src/**/{sub}/",
                        f"Create src/**/{sub}/ or document the deviation",
                    ))

        if not (repo_path / "tests").is_dir():
            findings.append(finding(
                "warning", name, "No tests/ directory",
                "tests/", "Create tests/",
            ))
        for fname in REQUIRED_FILES:
            if not (repo_path / fname).exists():
                findings.append(finding(
                    "warning", name, f"Missing {fname}",
                    fname, f"Add {fname}",
                ))
        if not any((repo_path / b).exists() for b in BUILD_FILES):
            findings.append(finding(
                "critical", name, "No build config found",
                str(repo_path), f"Add one of: {', '.join(BUILD_FILES[:4])}",
            ))

    return dim(
        "D8 — Project Structure", findings,
        checked=[
            "src/ presence and per-type expected subdirectories",
            "tests/ presence",
            "README.md / CHANGELOG.md / LICENSE / .gitignore presence",
            "build config presence",
        ],
        not_covered=[
            "integration 'cli' entry point — declared in build config under "
            "language-specific keys; left to D1/D4",
        ],
    )


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------

DIMENSIONS = {"D2": check_d2, "D3": check_d3, "D6": check_d6,
              "D7": check_d7, "D8": check_d8}


def run(root=None, only=None, repo_filter=None):
    if discover is None:
        return {"error": "discover_import_failed",
                "detail": "could not import discover.py from the same directory"}
    if root:
        eco_root = Path(root).expanduser().resolve()
    else:
        eco_root = discover.find_ecosystem_root(Path(os.getcwd()))
    if eco_root is None or not eco_root.is_dir():
        return {"error": "ecosystem_root_not_found",
                "hint": "pass --root or create .apcore-skills.json; "
                        "fall back to AskUserQuestion per ecosystem.md §0.1"}
    repos, _repos_by_type, version_groups = discover.discover(eco_root)
    if repo_filter:
        wanted = {n.strip() for n in repo_filter.split(",") if n.strip()}
        repos = [r for r in repos if r["name"] in wanted]

    selected = [d.strip().upper() for d in only.split(",")] if only else list(DIMENSIONS)
    unknown = [d for d in selected if d not in DIMENSIONS]
    if unknown:
        return {"error": "unknown_dimension", "detail": ", ".join(unknown),
                "supported": list(DIMENSIONS)}

    out = {}
    for key in selected:
        fn = DIMENSIONS[key]
        out[key] = fn(repos, version_groups) if key == "D3" else fn(repos)

    return {
        "script": "audit-mechanical.py",
        "version": SCRIPT_VERSION,
        "ecosystem_root": str(eco_root),
        "repos_scanned": [r["name"] for r in repos],
        "dimensions": out,
    }


# --------------------------------------------------------------------------
# Selftest — guards the drift-prone predicates and normalizers
# --------------------------------------------------------------------------

def selftest():
    assert is_snake("scan_module") and is_snake("_private") and is_snake("x")
    assert not is_snake("scanModule") and not is_snake("ScanModule")
    assert is_pascal("APCore") and is_pascal("Registry")
    assert not is_pascal("registry") and not is_pascal("my_class")
    assert is_camel("scanModule") and is_camel("call")
    assert not is_camel("ScanModule") and not is_camel("scan_module")
    assert is_kebab("mcp-bridge") and is_kebab("registry")
    assert not is_kebab("mcpBridge") and not is_kebab("mcp_bridge")
    assert is_upper_snake("AUTO") and is_upper_snake("MAX_RETRY_COUNT")
    assert not is_upper_snake("Auto") and not is_upper_snake("maxRetry")

    assert major_minor("1.2.3") == "1.2"
    assert major_minor("v0.14.0-rc1") == "0.14"
    assert major_minor("not-a-version") is None
    assert major_minor(None) is None

    # Cross-language default normalization must collapse to one form.
    assert normalize_default("True") == normalize_default("true") == "True"
    assert normalize_default("False") == normalize_default("false") == "False"
    assert normalize_default("'bearer'") == normalize_default('"bearer"') == '"bearer"'
    assert normalize_default('["auto"]') == normalize_default("['auto']") == '["auto"]'
    assert normalize_default("[ ]") == "[]"
    assert normalize_default("8808") == "8808"
    assert normalize_default("None") == normalize_default("null") == "None"
    assert normalize_default("Field(default=True)").endswith("True")

    # Every canonical default must survive normalization idempotently.
    for k, v in CANONICAL_SETTINGS.items():
        n = normalize_default(v)
        assert normalize_default(n) == n, f"{k} normalization not idempotent"

    # Regex anchors used for structural claims.
    assert PY_CLASS.match("class Registry:").group(1) == "Registry"
    assert PY_DEF.match("    def scan_module(self):").group(1) == "scan_module"
    assert TS_CLASS.match("export class Registry {").group(1) == "Registry"
    assert TS_FUNC.match("export async function call() {").group(1) == "call"
    assert TS_ENUM.match("export enum Transport {").group(1) == "Transport"
    m = EXC_BASE.match("class ScanFailure(APCoreError):")
    assert m.group(1) == "ScanFailure" and "Error" in m.group(2)
    m = EXC_BASE.match("export class ScanFailure extends APCoreError {")
    assert m.group(1) == "ScanFailure" and "Error" in m.group(3)

    assert RE_SETTING.search("APCORE_PORT = 8808").group(1) == "APCORE_PORT"
    assert RE_SETTING.search("APCORE_HOST: str = '0.0.0.0'").group(1) == "APCORE_HOST"

    # Regression: a single-line TOML dependency array must yield EVERY entry.
    # A line-wise scan previously returned only the first, silently under-
    # reporting D6 cross-repo version conflicts.
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = Path(td)
        (p / "pyproject.toml").write_text(
            '[project]\nname = "x"\nversion = "1.0.0"\n'
            'dependencies = ["pydantic>=2.0", "httpx>=0.27", "rich"]\n',
            encoding="utf-8")
        rt, seen = _deps_python(p)
        assert set(rt) == {"pydantic", "httpx", "rich"}, rt
        assert rt["httpx"] == "0.27" and rt["rich"] == "", rt
        # Multi-line form must parse identically.
        (p / "pyproject.toml").write_text(
            '[project]\ndependencies = [\n  "pydantic>=2.0",\n  "httpx>=0.27",\n]\n',
            encoding="utf-8")
        rt2, _ = _deps_python(p)
        assert set(rt2) == {"pydantic", "httpx"}, rt2

    # Dimension coverage must match what the markdown delegates to this script.
    assert set(DIMENSIONS) == {"D2", "D3", "D6", "D7", "D8"}, \
        "fast path must not silently gain or lose a dimension"

    print("audit-mechanical.py selftest: OK")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="apcore-skills mechanical audit dimensions (D2/D3/D6/D7/D8)")
    ap.add_argument("--root", help="ecosystem root (skips upward search)")
    ap.add_argument("--repos", help="comma-separated repo names to limit the scan")
    ap.add_argument("--only", help="comma-separated dimensions, e.g. D3,D8")
    ap.add_argument("--selftest", action="store_true", help="run internal checks")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()

    try:
        result = run(root=args.root, only=args.only, repo_filter=args.repos)
    except Exception as exc:  # never crash the caller; let it fall back
        result = {"error": "unhandled_exception", "detail": f"{type(exc).__name__}: {exc}"}

    print(json.dumps(result, indent=2, ensure_ascii=False))
    if "error" in result:
        return 2 if result["error"] == "ecosystem_root_not_found" else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
