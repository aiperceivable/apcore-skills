#!/usr/bin/env python3
"""apcore-skills ecosystem discovery — deterministic fast path for Step 0.

Implements the rules in skills/shared/ecosystem.md (§0.1-0.7) as code so that
each skill invocation does not have to re-derive repo layout, versions, and git
status by reading files in the LLM context.

Output: a single JSON object on stdout with keys:
  ecosystem_root, repos[], repos_by_type{}, version_groups{}, cwd_repo,
  core_sdks[], mcp_bridges[], integrations[]

The markdown tables in ecosystem.md remain the authoritative specification and
the fallback when Python is unavailable or this script errors. Keep the two in
sync; `--selftest` guards the drift-prone parts (name->type classification and
version-string parsing).

Stdlib only. No third-party dependencies.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# tomllib is stdlib on 3.11+; we degrade to regex parsing when it is absent.
try:  # pragma: no cover - availability depends on interpreter version
    import tomllib  # type: ignore
except Exception:  # pragma: no cover
    tomllib = None  # type: ignore


# --- Classification tables (mirror ecosystem.md §0.2) -----------------------

KNOWN_LANGS = {
    "python": "Python",
    "typescript": "TypeScript",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "ts": "TypeScript",
    "node": "JavaScript",
    "rust": "Rust",
    "go": "Go",
    "golang": "Go",
    "java": "Java",
    "kotlin": "Kotlin",
    "php": "PHP",
    "ruby": "Ruby",
    "csharp": "C#",
    "cs": "C#",
    "dotnet": "C#",
    "swift": "Swift",
    "elixir": "Elixir",
}

EXCLUDE_PREFIXES = ("aphub", "apflow", "apdev")
EXCLUDE_NAMES = {"aipartnerup-website"}
EXPLICIT_DOCS_SITES = {"apcore-zh", "aipartnerup-docs"}
TOOLING_NAMES = {"apcore-studio"}

SCOPE_GROUP = {
    "core-sdk": "core",
    "mcp-bridge": "mcp",
    "a2a-bridge": "a2a",
    "toolkit": "toolkit",
    "integration": "integrations",
    "protocol": "docs",
    "docs-site": "docs",
    "shared-lib": "shared",
    "tooling": "tooling",
}


def classify(name: str):
    """Return (repo_type, lang_hint) for a directory name, or None if not apcore.

    Priority follows ecosystem.md §0.2: specific patterns before the
    apcore-{type}-{lang} wildcard. `lang_hint` may be None (resolved later from
    the build config). docs-site for bare `apcore-mcp` is detected at scan time
    via the mkdocs heuristic, not here.
    """
    if name in EXCLUDE_NAMES or name.startswith(EXCLUDE_PREFIXES):
        return None
    if name == "apcore":
        return ("protocol", None)
    if name in EXPLICIT_DOCS_SITES:
        return ("docs-site", None)
    if name in TOOLING_NAMES:
        return ("tooling", None)

    m = re.fullmatch(r"apcore-discovery-([a-z0-9]+)", name)
    if m and m.group(1) in KNOWN_LANGS:
        return ("shared-lib", m.group(1))

    m = re.fullmatch(r"apcore-mcp-([a-z0-9]+)", name)
    if m and m.group(1) in KNOWN_LANGS:
        return ("mcp-bridge", m.group(1))

    m = re.fullmatch(r"apcore-a2a-([a-z0-9]+)", name)
    if m and m.group(1) in KNOWN_LANGS:
        return ("a2a-bridge", m.group(1))

    m = re.fullmatch(r"apcore-([a-z0-9]+)", name)
    if m and m.group(1) in KNOWN_LANGS:
        return ("core-sdk", m.group(1))

    m = re.fullmatch(r"apcore-([a-z0-9]+)-([a-z0-9]+)", name)
    if m and m.group(2) in KNOWN_LANGS:
        return (m.group(1), m.group(2))  # type = first segment (wildcard)

    m = re.fullmatch(r"([a-z0-9]+)-apcore", name)
    if m:
        return ("integration", None)

    return None


# --- Version parsing (mirror ecosystem.md §0.5) -----------------------------
# Each parser takes file *text* and returns a version string or None, so that
# --selftest can exercise them without touching the filesystem.

def parse_pyproject_version(text: str):
    if tomllib is not None:
        try:
            data = tomllib.loads(text)
            v = data.get("project", {}).get("version")
            if v:
                return v
            v = data.get("tool", {}).get("poetry", {}).get("version")
            if v:
                return v
        except Exception:
            pass
    m = re.search(r"(?m)^\s*version\s*=\s*[\"']([^\"']+)[\"']", text)
    return m.group(1) if m else None


def parse_cargo_version(text: str):
    if tomllib is not None:
        try:
            data = tomllib.loads(text)
            v = data.get("package", {}).get("version")
            if v:
                return v
        except Exception:
            pass
    # Fallback: first `version = "..."` after a [package] header.
    section = re.split(r"(?m)^\s*\[package\]\s*$", text, maxsplit=1)
    scope = section[1] if len(section) > 1 else text
    m = re.search(r"(?m)^\s*version\s*=\s*[\"']([^\"']+)[\"']", scope)
    return m.group(1) if m else None


def parse_json_version(text: str):
    try:
        return json.loads(text).get("version")
    except Exception:
        m = re.search(r"\"version\"\s*:\s*\"([^\"]+)\"", text)
        return m.group(1) if m else None


def parse_pom_version(text: str):
    # The project version is conventionally the first <version> appearing before
    # the <dependencies> block (avoids picking up a dependency's version).
    head = re.split(r"<dependencies>", text, maxsplit=1)[0]
    m = re.search(r"<version>\s*([^<\s]+)\s*</version>", head)
    if m:
        return m.group(1)
    m = re.search(r"<version>\s*([^<\s]+)\s*</version>", text)
    return m.group(1) if m else None


def parse_gradle_version(text: str):
    m = re.search(r"(?m)^\s*version\s*=?\s*['\"]([^'\"]+)['\"]", text)
    return m.group(1) if m else None


def parse_mix_version(text: str):
    m = re.search(r"version:\s*\"([^\"]+)\"", text)
    return m.group(1) if m else None


def parse_csproj_version(text: str):
    m = re.search(r"<Version>\s*([^<\s]+)\s*</Version>", text)
    return m.group(1) if m else None


def parse_dunder_version(text: str):
    m = re.search(r"(?m)^\s*__version__\s*=\s*[\"']([^\"']+)[\"']", text)
    return m.group(1) if m else None


def parse_ts_version(text: str):
    m = re.search(r"export\s+const\s+VERSION\s*=\s*[\"']([^\"']+)[\"']", text)
    return m.group(1) if m else None


def _semver_key(tag: str):
    nums = re.findall(r"\d+", tag)
    return tuple(int(n) for n in nums[:3]) + (0,) * (3 - len(nums[:3]))


def latest_git_tag(path: Path):
    try:
        out = subprocess.run(
            ["git", "-C", str(path), "tag", "-l", "v*"],
            capture_output=True, text=True, timeout=15,
        )
        tags = [t.strip() for t in out.stdout.splitlines() if t.strip()]
        if not tags:
            return None
        return max(tags, key=_semver_key)
    except Exception:
        return None


# --- Build-config detection -------------------------------------------------

# (kind, filename) in detection priority order.
BUILD_FILES = [
    ("cargo", "Cargo.toml"),
    ("go_mod", "go.mod"),
    ("pyproject", "pyproject.toml"),
    ("package_json", "package.json"),
    ("pom", "pom.xml"),
    ("gradle_kts", "build.gradle.kts"),
    ("gradle", "build.gradle"),
    ("composer", "composer.json"),
    ("mix", "mix.exs"),
    ("swift", "Package.swift"),
]

KIND_LANG = {
    "cargo": "Rust",
    "go_mod": "Go",
    "pyproject": "Python",
    "pom": "Java",
    "gradle": "Java",
    "gradle_kts": "Java",
    "composer": "PHP",
    "mix": "Elixir",
    "swift": "Swift",
    "csproj": "C#",
}


def detect_build_file(entry: Path):
    for kind, fname in BUILD_FILES:
        if (entry / fname).exists():
            return kind, entry / fname
    if (entry / "setup.py").exists():
        return "pyproject", entry / "setup.py"
    csproj = list(entry.glob("*.csproj"))
    if csproj:
        return "csproj", csproj[0]
    return None


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def detect_language(entry: Path, kind: str, lang_hint):
    if kind == "package_json":
        return "TypeScript" if (entry / "tsconfig.json").exists() else "JavaScript"
    if kind in KIND_LANG:
        return KIND_LANG[kind]
    if lang_hint and lang_hint in KNOWN_LANGS:
        return KNOWN_LANGS[lang_hint]
    return None


def get_version(entry: Path, kind: str, bf_path: Path):
    text = _read(bf_path)
    if kind == "pyproject":
        v = parse_pyproject_version(text)
        if v and not str(v).startswith("{"):  # guard against dynamic markers
            return v
        # Fallback: __version__ in src/*/__init__.py or _version.py
        for cand in list(entry.glob("src/*/__init__.py")) + \
                list(entry.glob("src/*/_version.py")) + \
                list(entry.glob("*/__init__.py")):
            v = parse_dunder_version(_read(cand))
            if v:
                return v
        return None
    if kind == "cargo":
        return parse_cargo_version(text)
    if kind in ("package_json", "composer"):
        v = parse_json_version(text)
        if v:
            return v
        if kind == "package_json":
            for cand in entry.glob("src/*/index.ts"):
                v = parse_ts_version(_read(cand))
                if v:
                    return v
        return None
    if kind == "pom":
        return parse_pom_version(text)
    if kind in ("gradle", "gradle_kts"):
        return parse_gradle_version(text)
    if kind == "mix":
        return parse_mix_version(text)
    if kind == "csproj":
        return parse_csproj_version(text)
    if kind in ("go_mod", "swift"):
        return latest_git_tag(entry)
    return None


def get_package_name(kind: str, bf_path: Path):
    text = _read(bf_path)
    try:
        if kind == "pyproject":
            if tomllib is not None:
                data = tomllib.loads(text)
                return (data.get("project", {}).get("name")
                        or data.get("tool", {}).get("poetry", {}).get("name"))
            m = re.search(r"(?m)^\s*name\s*=\s*[\"']([^\"']+)[\"']", text)
            return m.group(1) if m else None
        if kind == "cargo":
            m = re.search(r"(?m)^\s*name\s*=\s*[\"']([^\"']+)[\"']", text)
            return m.group(1) if m else None
        if kind in ("package_json", "composer"):
            return json.loads(text).get("name")
        if kind == "go_mod":
            m = re.search(r"(?m)^\s*module\s+(\S+)", text)
            return m.group(1).rsplit("/", 1)[-1] if m else None
        if kind == "pom":
            head = re.split(r"<dependencies>", text, maxsplit=1)[0]
            m = re.search(r"<artifactId>\s*([^<\s]+)\s*</artifactId>", head)
            return m.group(1) if m else None
    except Exception:
        return None
    return None


def git_status(path: Path):
    try:
        out = subprocess.run(
            ["git", "-C", str(path), "status", "--porcelain"],
            capture_output=True, text=True, timeout=15,
        )
        if out.returncode != 0:
            return "unknown"
        return "clean" if out.stdout.strip() == "" else "dirty"
    except Exception:
        return "unknown"


# --- Ecosystem root detection (ecosystem.md §0.1) ---------------------------

def read_config_root(start: Path):
    cfg = start / ".apcore-skills.json"
    if cfg.exists():
        try:
            data = json.loads(_read(cfg))
            root = data.get("ecosystem_root")
            if root:
                return Path(root).expanduser().resolve()
        except Exception:
            pass
    return None


def find_ecosystem_root(start: Path):
    cfg_root = read_config_root(start)
    if cfg_root:
        return cfg_root
    cur = start.resolve()
    while True:
        if (cur / "apcore" / "PROTOCOL_SPEC.md").exists():
            return cur
        if cur.parent == cur:
            return None
        cur = cur.parent


# --- Main discovery ---------------------------------------------------------

def discover(root: Path):
    repos = []
    for entry in sorted(p for p in root.iterdir() if p.is_dir()):
        name = entry.name
        cls = classify(name)
        has_mkdocs = (entry / "mkdocs.yml").exists()
        has_src = (entry / "src").is_dir()
        if cls is None:
            if has_mkdocs and not has_src:
                cls = ("docs-site", None)
            else:
                continue
        rtype, lang_hint = cls

        # protocol and docs-site repos are intentionally build-config-less
        # (spec/doc authorities), so they are "present" rather than placeholder.
        if rtype in ("protocol", "docs-site"):
            repos.append({
                "name": name, "path": str(entry), "type": rtype,
                "language": None, "version": None, "package_name": None,
                "git_status": git_status(entry), "status": rtype,
            })
            continue

        bf = detect_build_file(entry)
        if bf is None:
            repos.append({
                "name": name, "path": str(entry), "type": rtype,
                "language": KNOWN_LANGS.get(lang_hint) if lang_hint else None,
                "version": None, "package_name": None,
                "git_status": git_status(entry), "status": "placeholder",
            })
            continue

        kind, bf_path = bf
        repos.append({
            "name": name, "path": str(entry), "type": rtype,
            "language": detect_language(entry, kind, lang_hint),
            "version": get_version(entry, kind, bf_path),
            "package_name": get_package_name(kind, bf_path),
            "git_status": git_status(entry), "status": "ok",
        })

    repos_by_type: dict[str, list[str]] = {}
    for r in repos:
        repos_by_type.setdefault(r["type"], []).append(r["name"])

    version_groups: dict[str, list[str]] = {}
    for r in repos:
        grp = SCOPE_GROUP.get(r["type"])
        if grp is None:  # wildcard apcore-{type}-{lang}
            grp = r["type"]
        if r["type"] in ("core-sdk", "mcp-bridge", "a2a-bridge") or \
                r["type"] not in SCOPE_GROUP:
            version_groups.setdefault(grp, []).append(r["name"])

    return repos, repos_by_type, version_groups


def detect_cwd_repo(repos, cwd: Path):
    base = cwd.name
    for r in repos:
        if r["name"] == base:
            grp = SCOPE_GROUP.get(r["type"], r["type"])
            return {"name": r["name"], "type": r["type"],
                    "language": r["language"], "scope_group": grp}
    return None


def build_output(root: Path, cwd: Path):
    repos, repos_by_type, version_groups = discover(root)
    return {
        "ecosystem_root": str(root),
        "repos": repos,
        "repos_by_type": repos_by_type,
        "version_groups": version_groups,
        "cwd_repo": detect_cwd_repo(repos, cwd),
        "core_sdks": repos_by_type.get("core-sdk", []),
        "mcp_bridges": repos_by_type.get("mcp-bridge", []),
        "integrations": repos_by_type.get("integration", []),
    }


# --- Self-test --------------------------------------------------------------

def selftest():
    cases = {
        "apcore": ("protocol", None),
        "apcore-python": ("core-sdk", "python"),
        "apcore-typescript": ("core-sdk", "typescript"),
        "apcore-rust": ("core-sdk", "rust"),
        "apcore-mcp-python": ("mcp-bridge", "python"),
        "apcore-mcp-typescript": ("mcp-bridge", "typescript"),
        "apcore-a2a-go": ("a2a-bridge", "go"),
        "apcore-toolkit-rust": ("toolkit", "rust"),
        "apcore-discovery-python": ("shared-lib", "python"),
        "django-apcore": ("integration", None),
        "nestjs-apcore": ("integration", None),
        "apcore-zh": ("docs-site", None),
        "aipartnerup-docs": ("docs-site", None),
        "apcore-studio": ("tooling", None),
        "aphub-server": None,
        "aipartnerup-website": None,
        "totally-unrelated": None,
    }
    for name, expected in cases.items():
        got = classify(name)
        assert got == expected, f"classify({name!r}) = {got!r}, expected {expected!r}"

    assert parse_pyproject_version('[project]\nname="x"\nversion = "1.2.3"\n') == "1.2.3"
    assert parse_cargo_version('[package]\nname = "x"\nversion = "0.4.0"\n') == "0.4.0"
    assert parse_json_version('{"name":"x","version":"2.0.1"}') == "2.0.1"
    assert parse_pom_version(
        "<project><version>3.1.0</version><dependencies>"
        "<version>9.9.9</version></dependencies></project>") == "3.1.0"
    assert parse_gradle_version("version = '1.0.0'") == "1.0.0"
    assert parse_gradle_version('version "1.0.1"') == "1.0.1"
    assert parse_mix_version('  version: "0.9.0",') == "0.9.0"
    assert parse_csproj_version("<Version>5.5.5</Version>") == "5.5.5"
    assert parse_dunder_version('__version__ = "7.7.7"') == "7.7.7"
    assert parse_ts_version('export const VERSION = "1.1.1"') == "1.1.1"
    print("discover.py selftest: OK")


def main(argv=None):
    ap = argparse.ArgumentParser(description="apcore-skills ecosystem discovery")
    ap.add_argument("--root", help="ecosystem root (skips upward search)")
    ap.add_argument("--cwd", help="working dir for cwd_repo detection (default: $PWD)")
    ap.add_argument("--selftest", action="store_true", help="run unit checks and exit")
    args = ap.parse_args(argv)

    if args.selftest:
        selftest()
        return 0

    cwd = Path(args.cwd).expanduser() if args.cwd else Path(os.getcwd())
    if args.root:
        root = Path(args.root).expanduser().resolve()
    else:
        root = find_ecosystem_root(cwd)

    if root is None or not root.is_dir():
        json.dump({"error": "ecosystem_root_not_found",
                   "hint": "pass --root or create .apcore-skills.json; "
                           "fall back to AskUserQuestion per ecosystem.md §0.1"},
                  sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 2

    json.dump(build_output(root, cwd), sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
