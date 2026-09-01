#!/usr/bin/env python3
"""apcore-skills sync — lossless extraction cache.

Caches the OUTPUT of expensive sub-agent calls in `sync` Step 2 (per-repo public
API extraction) and Step 4C (per-module deep-chain analysis), keyed by a content
hash of exactly the local source files that sub-agent would read.

This is purely local and offline: the "key" is a sha256 over the current bytes
of the relevant files on disk (plus, for Step 4C, the spec text passed via
`--extra`). No network access, no git remote, no git required at all — `git` is
never invoked by this script.

Contract: if the hash matches a stored entry, the *input* the sub-agent would see
is guaranteed byte-identical to a prior run — this script only ever attests to
that. It does NOT re-run any orchestrator-side judgment (shape validation,
quality gates, anti-pattern guards) that decided the prior output was good
enough to trust; the caller is responsible for (a) re-validating the returned
`data`'s structural shape on every hit — cheap, local, no LLM call — and
(b) only ever `put`-ting output that already cleared its own quality gate, and
(c) folding any change to that gate's logic into `--extra` the same way a
prompt-template change is folded in. Only when the caller does all three is a
hit truly equivalent to a fresh run; see `shared/ecosystem.md` §0.6b.

Usage:
  # 1. Before spawning a Step 2 sub-agent for a repo:
  python3 extract_cache.py check --cache-dir <dir> --kind api --key <repo_name> \
      --repo-dir <path> --lang <language>
  # -> {"status": "hit", "hash": "...", "data": "<cached sub-agent output>"}
  # -> {"status": "miss", "hash": "..."}   (spawn the sub-agent; reuse this hash for `put`)

  # 2. After a Step 2 sub-agent returns, persist its output:
  python3 extract_cache.py put --cache-dir <dir> --kind api --key <repo_name> \
      --hash <hash-from-check> --data-file <path-to-file-with-subagent-output>

  # Step 4C (deep-chain) works the same way with explicit --paths instead of
  # --repo-dir/--lang, plus --extra for spec-contract / symbol-list text that
  # should also invalidate the cache when it changes:
  python3 extract_cache.py check --cache-dir <dir> --kind deepchain --key <module_name> \
      --paths <file1> <file2> ... --extra "<spec contract text>" --extra "<public symbols list>"
  python3 extract_cache.py put --cache-dir <dir> --kind deepchain --key <module_name> \
      --hash <hash-from-check> --data-file <path-to-file-with-subagent-json>

Stdlib only. No third-party dependencies. No git invocation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from types import SimpleNamespace

SCRIPT_VERSION = "1"

# --- language -> source extensions (mirrors discover.py's KNOWN_LANGS scope) -
LANG_EXTENSIONS = {
    "Python": [".py"],
    "TypeScript": [".ts", ".tsx"],
    "JavaScript": [".js", ".jsx"],
    "Rust": [".rs"],
    "Go": [".go"],
    "Java": [".java"],
    "Kotlin": [".kt"],
    "PHP": [".php"],
    "Ruby": [".rb"],
    "C#": [".cs"],
    "Swift": [".swift"],
    "Elixir": [".ex", ".exs"],
}

# Build-config files whose content also affects a Step 2 extraction summary
# (e.g. the VERSION line) even when no source file changed.
BUILD_FILES = [
    "pyproject.toml", "setup.py", "package.json", "Cargo.toml", "go.mod",
    "pom.xml", "build.gradle", "build.gradle.kts", "composer.json",
    "mix.exs", "Package.swift",
]

# Build-config files matched by SUFFIX rather than exact name, because the
# filename itself varies per project (e.g. `MyProject.csproj`).
BUILD_FILE_SUFFIXES = {".csproj"}

EXCLUDE_DIR_NAMES = {
    "node_modules", "dist", "build", "target", ".venv", "venv", "env",
    "__pycache__", ".git", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    "coverage", ".next", "out", "bin", "obj", ".tox", "vendor", ".cargo",
}


def _iter_repo_files(repo_dir: Path, lang: str | None):
    exts = set(LANG_EXTENSIONS.get(lang, [])) if lang else set()
    if not exts:
        # Unknown language hint: fall back to the union of all known
        # extensions so a miss on `lang` degrades to "hash everything
        # source-shaped" rather than silently hashing nothing (which would
        # make every run a false cache hit).
        for v in LANG_EXTENSIONS.values():
            exts.update(v)

    for p in sorted(repo_dir.rglob("*")):
        if not p.is_file():
            continue
        if any(part in EXCLUDE_DIR_NAMES for part in p.relative_to(repo_dir).parts[:-1]):
            continue
        if p.suffix in exts or p.name in BUILD_FILES or p.suffix in BUILD_FILE_SUFFIXES:
            yield p


def hash_repo_dir(repo_dir: Path, lang: str | None) -> str:
    h = hashlib.sha256()
    for p in _iter_repo_files(repo_dir, lang):
        rel = p.relative_to(repo_dir).as_posix()
        try:
            data = p.read_bytes()
        except OSError:
            continue
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(data)
        h.update(b"\0")
    return h.hexdigest()


def hash_paths(paths: list[str], extra: list[str]) -> str:
    h = hashlib.sha256()
    for raw in sorted(paths):
        p = Path(raw)
        rel = raw  # caller-supplied path is already the stable identity
        try:
            data = p.read_bytes()
        except OSError:
            data = b""  # missing file is a valid state to hash (symbol not implemented here)
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(data)
        h.update(b"\0")
    for e in extra:
        h.update(e.encode("utf-8"))
        h.update(b"\0")
    return h.hexdigest()


def _safe_key(key: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", key)


def _cache_path(cache_dir: Path, kind: str, key: str) -> Path:
    return cache_dir / kind / f"{_safe_key(key)}.json"


def cmd_check(args) -> int:
    cache_dir = Path(args.cache_dir).expanduser()
    if args.repo_dir:
        digest = hash_repo_dir(Path(args.repo_dir).expanduser(), args.lang)
        if args.extra:
            # Fold --extra (e.g. a prompt-template version tag) into a
            # repo-dir hash too, so an edit to the extraction prompt itself
            # invalidates every cached entry without touching any source file.
            h = hashlib.sha256(digest.encode("utf-8"))
            for e in args.extra:
                h.update(b"\0")
                h.update(e.encode("utf-8"))
            digest = h.hexdigest()
    else:
        digest = hash_paths(args.paths or [], args.extra or [])

    entry_path = _cache_path(cache_dir, args.kind, args.key)
    if entry_path.exists():
        try:
            entry = json.loads(entry_path.read_text(encoding="utf-8"))
        except Exception:
            entry = None
        if entry and entry.get("content_hash") == digest and entry.get("script_version") == SCRIPT_VERSION:
            json.dump({"status": "hit", "hash": digest, "cached_at": entry.get("cached_at"),
                       "data": entry.get("data")}, sys.stdout)
            sys.stdout.write("\n")
            return 0

    json.dump({"status": "miss", "hash": digest}, sys.stdout)
    sys.stdout.write("\n")
    return 0


def cmd_put(args) -> int:
    cache_dir = Path(args.cache_dir).expanduser()
    entry_path = _cache_path(cache_dir, args.kind, args.key)
    entry_path.parent.mkdir(parents=True, exist_ok=True)

    if args.data_file:
        data = Path(args.data_file).read_text(encoding="utf-8")
    else:
        data = sys.stdin.read()

    entry = {
        "script_version": SCRIPT_VERSION,
        "kind": args.kind,
        "key": args.key,
        "content_hash": args.hash,
        "cached_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "data": data,
    }
    entry_path.write_text(json.dumps(entry, indent=2), encoding="utf-8")
    json.dump({"status": "stored", "path": str(entry_path)}, sys.stdout)
    sys.stdout.write("\n")
    return 0


def cmd_clear(args) -> int:
    cache_dir = Path(args.cache_dir).expanduser()
    target = cache_dir / args.kind if args.kind else cache_dir
    n = 0
    if target.exists():
        for p in target.rglob("*.json"):
            p.unlink()
            n += 1
    json.dump({"status": "cleared", "removed": n}, sys.stdout)
    sys.stdout.write("\n")
    return 0


def selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        repo = root / "repo"
        (repo / "src" / "pkg").mkdir(parents=True)
        (repo / "src" / "pkg" / "a.py").write_text("def f(): pass\n")
        (repo / "node_modules" / "x").mkdir(parents=True)
        (repo / "node_modules" / "x" / "junk.py").write_text("SHOULD_BE_EXCLUDED\n")

        h1 = hash_repo_dir(repo, "Python")
        h2 = hash_repo_dir(repo, "Python")
        assert h1 == h2, "hash must be stable across repeated runs"

        (repo / "src" / "pkg" / "a.py").write_text("def f(): return 1\n")
        h3 = hash_repo_dir(repo, "Python")
        assert h3 != h1, "hash must change when a hashed file's content changes"

        (repo / "node_modules" / "x" / "junk.py").write_text("STILL_EXCLUDED\n")
        h4 = hash_repo_dir(repo, "Python")
        assert h4 == h3, "excluded directories must not affect the hash"

        csrepo = root / "csrepo"
        csrepo.mkdir()
        (csrepo / "MyProject.csproj").write_text("<Project><Version>1.0.0</Version></Project>\n")
        hc1 = hash_repo_dir(csrepo, "C#")
        (csrepo / "MyProject.csproj").write_text("<Project><Version>1.0.1</Version></Project>\n")
        hc2 = hash_repo_dir(csrepo, "C#")
        assert hc1 != hc2, "*.csproj files (variable filename) must participate in the hash"

        cache_dir = root / "cache"
        p1 = hash_paths([str(repo / "src" / "pkg" / "a.py")], ["contract-text-v1"])
        p2 = hash_paths([str(repo / "src" / "pkg" / "a.py")], ["contract-text-v2"])
        assert p1 != p2, "--extra must participate in the hash (spec-only changes must invalidate)"

        ns = SimpleNamespace(
            cache_dir=str(cache_dir), kind="api", key="demo-repo",
            repo_dir=str(repo), lang="Python", paths=None, extra=None,
        )
        assert cmd_check(ns) == 0

        ns2 = SimpleNamespace(
            cache_dir=str(cache_dir), kind="api", key="demo-repo",
            hash=hash_repo_dir(repo, "Python"), data_file=None,
        )
        import io
        old_stdin = sys.stdin
        sys.stdin = io.StringIO("REPO: demo-repo\nEXPORT_COUNT: 1\n")
        try:
            assert cmd_put(ns2) == 0
        finally:
            sys.stdin = old_stdin

        assert (cache_dir / "api" / "demo-repo.json").exists()

        ns3 = SimpleNamespace(
            cache_dir=str(cache_dir), kind="api", key="demo-repo",
            repo_dir=str(repo), lang="Python", paths=None, extra=None,
        )
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            assert cmd_check(ns3) == 0
            hit = json.loads(sys.stdout.getvalue())
        finally:
            sys.stdout = old_stdout
        assert hit["status"] == "hit", "put followed by check on unchanged input must hit"
        assert hit["data"] == "REPO: demo-repo\nEXPORT_COUNT: 1\n", "hit must return the exact stored data"

        ns_bad_version = SimpleNamespace(
            cache_dir=str(cache_dir), kind="api", key="demo-repo",
            repo_dir=str(repo), lang="Python", paths=None, extra=None,
        )
        entry_path = cache_dir / "api" / "demo-repo.json"
        stale = json.loads(entry_path.read_text())
        stale["script_version"] = "0"
        entry_path.write_text(json.dumps(stale))
        sys.stdout = io.StringIO()
        try:
            assert cmd_check(ns_bad_version) == 0
            stale_result = json.loads(sys.stdout.getvalue())
        finally:
            sys.stdout = old_stdout
        assert stale_result["status"] == "miss", "a script_version mismatch must be treated as a miss"

        assert cmd_clear(SimpleNamespace(cache_dir=str(cache_dir), kind="api")) == 0
        assert not (cache_dir / "api" / "demo-repo.json").exists(), "clear --kind api must remove the api entry"

    print("extract_cache.py selftest: OK")


def main(argv=None):
    ap = argparse.ArgumentParser(description="apcore-skills sync — lossless extraction cache")
    ap.add_argument("--selftest", action="store_true", help="run unit checks and exit")
    sub = ap.add_subparsers(dest="cmd")

    p_check = sub.add_parser("check", help="compute content hash and check cache")
    p_check.add_argument("--cache-dir", required=True)
    p_check.add_argument("--kind", required=True, help="e.g. api | deepchain")
    p_check.add_argument("--key", required=True, help="cache entry key, e.g. repo name or module name")
    p_check.add_argument("--repo-dir", help="hash mode: whole-repo walk filtered by --lang (Step 2)")
    p_check.add_argument("--lang", help="language for --repo-dir extension filtering")
    p_check.add_argument("--paths", nargs="*", help="hash mode: explicit file list (Step 4C)")
    p_check.add_argument("--extra", action="append", help="extra text folded into the hash (e.g. spec contract text); repeatable")
    p_check.set_defaults(func=cmd_check)

    p_put = sub.add_parser("put", help="store sub-agent output under a content hash")
    p_put.add_argument("--cache-dir", required=True)
    p_put.add_argument("--kind", required=True)
    p_put.add_argument("--key", required=True)
    p_put.add_argument("--hash", required=True, help="the hash returned by a prior `check` call")
    p_put.add_argument("--data-file", help="file containing the sub-agent output (default: stdin)")
    p_put.set_defaults(func=cmd_put)

    p_clear = sub.add_parser("clear", help="drop cached entries (e.g. after a schema change)")
    p_clear.add_argument("--cache-dir", required=True)
    p_clear.add_argument("--kind", help="restrict to one kind (default: clear everything under cache-dir)")
    p_clear.set_defaults(func=cmd_clear)

    args = ap.parse_args(argv)

    if args.selftest:
        selftest()
        return 0

    if not args.cmd:
        ap.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
