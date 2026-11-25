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
sync; `--selftest` covers monorepo layout, CWD selection, and version parsing.

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
from tempfile import TemporaryDirectory

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

EXPLICIT_DOCS_SITES = {"apcore-zh", "aipartnerup-docs"}
TOOLING_NAMES = {"apcore-studio"}
SURFACE_TYPES = {
    "mcp": "mcp-bridge",
    "a2a": "a2a-bridge",
    "cli": "cli",
    "toolkit": "toolkit",
}

SCOPE_GROUP = {
    "core-sdk": "core",
    "mcp-bridge": "mcp",
    "a2a-bridge": "a2a",
    "cli": "cli",
    "toolkit": "toolkit",
    "integration": "integrations",
    "protocol": "docs",
    "docs-site": "docs",
    "shared-lib": "shared",
    "tooling": "tooling",
}
VERSION_GROUP_TYPES = {"core-sdk", "mcp-bridge", "a2a-bridge", "cli"}


def classify(name: str):
    """Classify independently maintained sibling repos, per ecosystem.md §0.2."""
    if name in EXPLICIT_DOCS_SITES:
        return ("docs-site", None)
    if name in TOOLING_NAMES:
        return ("tooling", None)

    m = re.fullmatch(r"apcore-discovery-([a-z0-9]+)", name)
    if m and m.group(1) in KNOWN_LANGS:
        return ("shared-lib", m.group(1))

    if re.fullmatch(r"[a-z0-9]+-apcore", name):
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


def latest_git_tag(path: Path, prefix: str):
    try:
        out = subprocess.run(
            ["git", "-C", str(path), "tag", "-l", f"{prefix}*"],
            capture_output=True, text=True, timeout=15,
        )
        versions = [
            tag[len(prefix):]
            for tag in out.stdout.splitlines()
            if tag.startswith(prefix) and re.fullmatch(r"\d+\.\d+\.\d+", tag[len(prefix):])
        ]
        return max(versions, key=_semver_key, default=None)
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


def get_version(entry: Path, kind: str, bf_path: Path, tag_prefix: str | None):
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
    if kind in ("go_mod", "swift") and tag_prefix:
        return latest_git_tag(entry, tag_prefix)
    return None


def read_release_tag_prefix(path: Path):
    text = _read(path / ".unirelease.toml")
    if tomllib is not None:
        try:
            prefix = tomllib.loads(text).get("tag_prefix")
        except tomllib.TOMLDecodeError:
            return None
        return prefix if isinstance(prefix, str) and prefix.strip() else None
    match = re.search(r"""(?m)^[ \t]*tag_prefix[ \t]*=[ \t]*(["'])([^"'\n]+)\1""", text)
    return match.group(2) if match else None


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


def git_status(git_root: Path, path: Path):
    try:
        out = subprocess.run(
            ["git", "-C", str(git_root), "status", "--porcelain", "--",
             str(path.relative_to(git_root))],
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
        if (cur / "apcore" / "PROTOCOL_SPEC.md").is_file() or any(
            (cur / "apcore-surfaces" / component).is_dir() for component in SURFACE_TYPES
        ):
            return cur
        if cur.parent == cur:
            return None
        cur = cur.parent


# --- Main discovery ---------------------------------------------------------

def describe_target(name, path, rtype, *, git_root, spec_root=None, build_file=None,
                    lang_hint=None):
    conformance = spec_root / "conformance" if spec_root else None
    target = {
        "name": name, "path": str(path), "type": rtype,
        "language": KNOWN_LANGS.get(lang_hint), "version": None, "package_name": None,
        "git_status": git_status(git_root, path),
        "status": rtype if rtype in ("protocol", "docs-site") else "placeholder",
        "git_root": str(git_root),
        "release_tag_prefix": None,
        "spec_root": str(spec_root) if spec_root else None,
        "conformance_path": str(conformance) if conformance and conformance.is_dir() else None,
    }
    if build_file:
        kind, manifest = build_file
        tag_prefix = read_release_tag_prefix(path)
        if tag_prefix is None and path == git_root:
            tag_prefix = "v"
        target.update(
            language=target["language"] or detect_language(path, kind, lang_hint),
            version=get_version(path, kind, manifest, tag_prefix),
            package_name=get_package_name(kind, manifest),
            release_tag_prefix=tag_prefix,
            status="ok",
        )
    return target


def discover_monorepo_targets(root: Path):
    core = root / "apcore"
    surfaces = root / "apcore-surfaces"
    locations = [(core, core, "apcore", "core-sdk")]
    locations.extend(
        (surfaces / component, surfaces, f"apcore-{component}", rtype)
        for component, rtype in SURFACE_TYPES.items()
    )
    for component_path, git_root, name, rtype in locations:
        is_core = rtype == "core-sdk"
        has_spec = ((component_path / "PROTOCOL_SPEC.md").is_file() if is_core
                    else (component_path / "docs").is_dir())
        spec_root = component_path if has_spec else None
        if spec_root:
            yield describe_target(
                name, spec_root, "protocol" if is_core else "docs-site",
                git_root=git_root, spec_root=spec_root,
            )
        for lang in KNOWN_LANGS:
            path = component_path / lang
            if not path.is_dir():
                continue
            build_file = detect_build_file(path)
            if build_file:
                yield describe_target(
                    f"{name}-{lang}", path, rtype, git_root=git_root,
                    spec_root=spec_root, build_file=build_file, lang_hint=lang,
                )


def discover(root: Path):
    repos = list(discover_monorepo_targets(root))
    for entry in root.iterdir():
        if not entry.is_dir():
            continue
        cls = classify(entry.name)
        if cls is None:
            continue
        rtype, lang_hint = cls
        is_docs = rtype == "docs-site"
        repos.append(describe_target(
            entry.name, entry, rtype, git_root=entry,
            spec_root=entry if is_docs else None,
            build_file=None if is_docs else detect_build_file(entry),
            lang_hint=lang_hint,
        ))
    repos.sort(key=lambda repo: repo["name"])

    repos_by_type: dict[str, list[str]] = {}
    for r in repos:
        repos_by_type.setdefault(r["type"], []).append(r["name"])

    version_groups: dict[str, list[str]] = {}
    for r in repos:
        if r["type"] in VERSION_GROUP_TYPES:
            version_groups.setdefault(SCOPE_GROUP[r["type"]], []).append(r["name"])

    return repos, repos_by_type, version_groups


def detect_cwd_repo(repos, cwd: Path):
    cwd = cwd.resolve()
    by_path = {Path(r["path"]).resolve(): r for r in repos}
    for path in (cwd, *cwd.parents):
        if (r := by_path.get(path)) is not None:
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

def selftest_monorepos():
    with TemporaryDirectory() as temp:
        root = Path(temp).resolve()

        def write_file(path, content=""):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

        core = root / "apcore"
        surfaces = root / "apcore-surfaces"
        write_file(core / "PROTOCOL_SPEC.md")
        components = {
            "apcore": (core, core),
            **{
                f"apcore-{component}": (surfaces / component, surfaces)
                for component in ("mcp", "a2a", "cli", "toolkit")
            },
        }
        manifests = {
            "python": ("pyproject.toml", '[project]\nname="package"\nversion="2.1.0"\n'),
            "rust": ("Cargo.toml", '[package]\nname="package"\nversion="2.1.0"\n'),
            "typescript": ("package.json", '{"name":"package","version":"2.1.0"}'),
        }
        for name, (spec_root, _) in components.items():
            write_file(spec_root / "docs" / "index.md")
            write_file(spec_root / "conformance" / "case.json")
            if spec_root != core:
                write_file(root / name / "mkdocs.yml")
            for lang, (manifest, content) in manifests.items():
                write_file(spec_root / lang / manifest, content)
                write_file(root / f"{name}-{lang}" / manifest, content.replace("2.1.0", "1.0.0"))

        # An old language checkout without a monorepo peer is also ignored.
        write_file(root / "apcore-go" / "go.mod", "module example.org/apcore-go")
        write_file(root / "flask-apcore" / "pyproject.toml", manifests["python"][1])
        core_cwd = core / "python" / "src" / "apcore"
        mcp_cwd = surfaces / "mcp" / "typescript" / "src" / "server"
        for cwd in (core_cwd, mcp_cwd):
            cwd.mkdir(parents=True)
            assert find_ecosystem_root(cwd) == root, cwd

        output = build_output(root, core_cwd)
        repos = {r["name"]: r for r in output["repos"]}
        assert len(repos) == len(output["repos"]), "Duplicate discovery names"
        expected_names = {"flask-apcore", *components}
        expected_names.update(f"{name}-{lang}" for name in components for lang in manifests)
        assert repos.keys() == expected_names, sorted(repos)
        for name, (spec_root, git_root) in components.items():
            assert repos[name]["path"] == str(spec_root), name
            for lang in manifests:
                repo = repos[f"{name}-{lang}"]
                assert repo["path"] == str(spec_root / lang), repo
                assert repo["version"] == "2.1.0", repo
                assert repo["package_name"] == "package", repo
                assert repo["git_root"] == str(git_root), repo
                assert repo["spec_root"] == str(spec_root), repo
                assert repo["conformance_path"] == str(spec_root / "conformance"), repo

        assert output["cwd_repo"]["name"] == "apcore-python", output["cwd_repo"]
        mcp_target = detect_cwd_repo(output["repos"], mcp_cwd)
        assert mcp_target == {
            "name": "apcore-mcp-typescript", "type": "mcp-bridge",
            "language": "TypeScript", "scope_group": "mcp",
        }, mcp_target
        assert detect_cwd_repo(output["repos"], root / "apcore-mcp-typescript") is None
        assert detect_cwd_repo(output["repos"], core)["name"] == "apcore"
        assert detect_cwd_repo(output["repos"], surfaces / "mcp" / "docs")["name"] == "apcore-mcp"
        assert detect_cwd_repo(output["repos"], surfaces) is None
        assert detect_cwd_repo(output["repos"], root / "flask-apcore" / "src")["name"] == "flask-apcore"

        go = core / "go"
        write_file(go / "go.mod", "module example.org/apcore/go")
        write_file(go / ".unirelease.toml", 'tag_prefix = "go/v"\n')
        new_package = build_output(root, go)["cwd_repo"]
        assert new_package and new_package["name"] == "apcore-go", new_package

        git = [
            "git", "-C", str(core),
            "-c", "user.name=Discovery Test", "-c", "user.email=test@example.org",
            "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false",
            "-c", "core.hooksPath=/dev/null",
        ]
        subprocess.run([*git, "init", "-q"], check=True)
        subprocess.run([*git, "commit", "-qm", "fixture", "--allow-empty"], check=True)
        for tag in ("go/v2.1.0", "go/v3.0.0-beta", "core/rust/v4.0.0", "v5.0.0"):
            subprocess.run([*git, "tag", tag], check=True)
        repos_with_go = {r["name"]: r for r in discover(root)[0]}
        assert repos_with_go["apcore-go"]["release_tag_prefix"] == "go/v"
        assert repos_with_go["apcore-go"]["version"] == "2.1.0"
        assert repos_with_go["flask-apcore"]["release_tag_prefix"] == "v"

        (surfaces / "toolkit" / "rust" / "Cargo.toml").unlink()
        assert "apcore-toolkit-rust" not in {r["name"] for r in discover(root)[0]}
        (core / "PROTOCOL_SPEC.md").unlink()
        assert find_ecosystem_root(mcp_cwd) == root, "Discover without the Core protocol marker"


def selftest():
    cases = {
        "apcore-python": None,
        "apcore-mcp-python": None,
        "apcore-a2a-go": None,
        "apcore-toolkit-rust": None,
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
    selftest_monorepos()
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
