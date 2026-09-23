#!/usr/bin/env python3
"""Mechanical self-consistency checks for the apcore-skills plugin itself.

`audit-mechanical.py` checks the user's SDK repos. This checks THIS plugin, for the
class of defect that recurred five times while the plugin was being fixed:

    a normative document changed, and a consumer that depends on it did not.

Every check here is mechanical -- file reads, regex, hashing. No LLM judgment, so it
runs in CI and in `test.sh` for free. Each check exists because the failure it catches
actually happened, and was caught by a human reading files rather than by a tool:

  C1 include-resolves    -- an `@../shared/x.md` that points at nothing
  C2 flag-spelling       -- the same concept flagged differently per skill
                            (`--deep-chain on|off` vs `--no-deep-chain`)
  C3 flag-default-drift  -- prose asserting a default the flag table contradicts
  C4 namespace-registry  -- a finding-ID namespace emitted but never registered in
                            report-formats.md, so the report cannot render it
  C5 field-consumers     -- a field added to a sub-agent's output format that nothing
                            downstream reads (`errors_propagated` shipped inert)
  C6 tag-covers          -- a cached prompt template edited without bumping its
                            cache-version tag, so stale entries are served into a
                            schema that changed under them
  C7 host-constructs     -- a Claude-Code-specific construct spreading to a file the
                            portability inventory does not cover (an unexpanded
                            `@`-include drops its shared rules silently)

Usage:
    selfcheck.py --root <plugin-root>     # exit 0 = clean, 1 = findings
    selfcheck.py --selftest
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SCRIPT_VERSION = "1"

# ---------------------------------------------------------------- helpers


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return ""


def _skill_files(root: Path):
    """Every markdown file that is part of the plugin's normative surface."""
    out = []
    for pat in ("skills/*/SKILL.md", "skills/*/references/*.md", "skills/shared/*.md",
                "commands/*.md", "SKILL.md", "README.md"):
        out.extend(sorted(root.glob(pat)))
    # sdk-workspace holds captured experiment output, not plugin source
    return [p for p in out if "sdk-workspace" not in p.parts]


def _finding(check, severity, path, detail, fix):
    return {"check": check, "severity": severity, "file": str(path),
            "detail": detail, "fix": fix}


# ---------------------------------------------------------------- C1


def check_includes(root: Path):
    """Every `@../path.md` must resolve."""
    out = []
    for f in _skill_files(root):
        for m in re.finditer(r"@((?:\.\./)+[A-Za-z0-9_/.-]+\.md)", _read(f)):
            target = (f.parent / m.group(1)).resolve()
            if not target.is_file():
                out.append(_finding(
                    "include-resolves", "critical", f.relative_to(root),
                    f"`@{m.group(1)}` does not resolve to a file",
                    "fix the relative path, or create the missing shared doc"))
    return out


# ---------------------------------------------------------------- C2


def _flag_rows(text: str):
    """`| \\`--flag\\` | default | description |` rows out of a flag table."""
    rows = {}
    for m in re.finditer(r"^\|\s*`(--[a-z][a-z0-9-]*)`\s*\|\s*([^|]*)\|", text, re.M):
        flag, default = m.group(1), m.group(2).strip()
        rows.setdefault(flag, []).append(default)
    return rows


def check_flag_spelling(root: Path, spec: dict):
    """A concept must not be spelled as both `--x` and `--no-x` across skills."""
    out = []
    declared = {}
    for f in root.glob("skills/*/SKILL.md"):
        if "sdk-workspace" in f.parts:
            continue
        for flag in _flag_rows(_read(f)):
            declared.setdefault(flag, []).append(f.relative_to(root))

    allow = set(spec.get("conventional_negative_flags", []))
    for flag, where in sorted(declared.items()):
        if not flag.startswith("--no-") or flag in allow:
            continue
        positive = "--" + flag[len("--no-"):]
        if positive in declared:
            # both spellings exist -- fine ONLY if the --no- form is marked deprecated
            for f in where:
                body = _read(root / f)
                row = re.search(r"^\|\s*`" + re.escape(flag) + r"`\s*\|.*$", body, re.M)
                if row and "deprecat" not in row.group(0).lower():
                    out.append(_finding(
                        "flag-spelling", "warning", f,
                        f"`{flag}` and `{positive}` both declared; the negative form is "
                        f"not marked deprecated",
                        f"make `{positive}` canonical and mark `{flag}` a deprecated alias"))
        else:
            out.append(_finding(
                "flag-spelling", "warning", where[0],
                f"`{flag}` is a bare negative flag with no `{positive}` counterpart",
                f"prefer `{positive} on|off` so the switch can gain values later"))
    return out


# ---------------------------------------------------------------- C3


def check_flag_default_drift(root: Path):
    """Prose claiming a default must agree with that flag's own table row."""
    out = []
    for f in root.glob("skills/**/*.md"):
        if "sdk-workspace" in f.parts:
            continue
        text = _read(f)
        rows = _flag_rows(text)
        if not rows:
            continue
        for flag, defaults in rows.items():
            decl = defaults[0].strip().strip("*`").lower()
            if decl not in ("on", "off"):
                continue
            opposite = "off" if decl == "on" else "on"
            bare = flag.lstrip("-")
            # "default is on" / "DEFAULT ON" / "on by default" near the flag's concept
            for m in re.finditer(
                    r"(?i)(default(?:s)?\s+(?:is\s+)?" + opposite + r"\b"
                    r"|DEFAULT\s+" + opposite.upper() + r"\b"
                    r"|\b" + opposite + r"\s+by\s+default)", text):
                line = text[:m.start()].count("\n") + 1
                ctx = text[max(0, m.start() - 200):m.start() + 80]
                if bare not in ctx and flag not in ctx:
                    continue
                out.append(_finding(
                    "flag-default-drift", "critical", f.relative_to(root),
                    f"line {line}: prose says {flag} defaults {opposite!r}, "
                    f"but its table row declares {decl!r}",
                    "update the prose, or the table -- one of them is stale"))
    return out


# ---------------------------------------------------------------- C4


def check_namespace_registry(root: Path):
    """Every `[X-...]` finding-ID namespace emitted must be registered."""
    out = []
    registry_files = list(root.glob("skills/*/references/report-formats.md"))
    registry = "\n".join(_read(p) for p in registry_files)
    if not registry:
        return out
    emitted = set()
    for f in root.glob("skills/*/SKILL.md"):
        if "sdk-workspace" in f.parts:
            continue
        for m in re.finditer(r"\[([A-Z]+(?:-[A-Z]+)*)-\{seq\}\]", _read(f)):
            emitted.add(m.group(1))
    for ns in sorted(emitted):
        if not re.search(r"\b" + re.escape(ns) + r"-\{seq\}", registry):
            out.append(_finding(
                "namespace-registry", "warning",
                "skills/sync/references/report-formats.md",
                f"finding-ID namespace `{ns}-` is emitted but never registered",
                f"add a `{ns}-{{seq}}` row to the Finding ID namespaces list so the "
                f"report can render and explain it"))
    return out


# ---------------------------------------------------------------- C5


def check_field_consumers(root: Path, spec: dict):
    """A field in a sub-agent output format must be read by something downstream."""
    out = []
    for producer_rel, entry in sorted(spec.get("field_consumers", {}).items()):
        producer = root / producer_rel
        ptext = _read(producer)
        if not ptext:
            continue
        consumers = [root / c for c in entry["consumers"]]
        ctext = "\n".join(_read(c) for c in consumers)
        for field in entry["fields"]:
            if field not in ptext:
                out.append(_finding(
                    "field-consumers", "warning", producer_rel,
                    f"declared field `{field}` is no longer in this output format",
                    "remove it from selfcheck.json, or restore it"))
                continue
            if field not in ctext:
                out.append(_finding(
                    "field-consumers", "critical", producer_rel,
                    f"`{field}` is emitted by this output format but read by none of: "
                    + ", ".join(entry["consumers"]),
                    "wire the field into its consumers, or it ships inert"))
    return out


# ---------------------------------------------------------------- C6


def check_tag_covers(root: Path, spec: dict):
    """A cache tag must be bumped when the prompt it covers changes."""
    out = []
    for tag, entry in sorted(spec.get("tag_covers", {}).items()):
        for rel, recorded in entry["files"].items():
            p = root / rel
            body = _read(p)
            if not body:
                out.append(_finding(
                    "tag-covers", "warning", rel,
                    f"tag `{tag}` covers this file, but it is missing",
                    "update selfcheck.json"))
                continue
            actual = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
            if actual != recorded:
                out.append(_finding(
                    "tag-covers", "critical", rel,
                    f"changed since cache tag `{tag}` was recorded "
                    f"(recorded {recorded}, now {actual})",
                    f"if the change alters what a correct extraction contains, bump the "
                    f"tag past `{tag}` and record the new hash; if it is cosmetic, just "
                    f"record the new hash"))
    return out


# ---------------------------------------------------------------- C7


def check_host_constructs(root: Path, spec: dict):
    """Host-specific constructs may exist, but the inventory must stay declared.

    None of these fails loudly on a host that lacks it -- an unexpanded `@`-include
    just drops the shared rules it carried. PORTABILITY.md documents each one and its
    fallback; this check fails when a construct shows up in a file that inventory does
    not list, so the surface cannot grow without someone deciding it should.
    """
    out = []
    inv = spec.get("host_constructs")
    if not inv:
        return out
    for name, entry in sorted(inv.items()):
        pattern = re.compile(entry["pattern"])
        declared = set(entry["files"])
        found = set()
        for f in _skill_files(root):
            if pattern.search(_read(f)):
                found.add(str(f.relative_to(root)))
        for extra in sorted(found - declared):
            out.append(_finding(
                "host-constructs", "warning", extra,
                f"uses host-specific construct `{name}`, which PORTABILITY.md's "
                f"inventory does not list for this file",
                f"add it to selfcheck.json host_constructs[{name}].files after "
                f"confirming PORTABILITY.md still describes the right fallback, or "
                f"use a host-neutral form"))
        for gone in sorted(declared - found):
            out.append(_finding(
                "host-constructs", "warning", gone,
                f"declared as using `{name}` but no longer does",
                "drop it from selfcheck.json -- a stale inventory understates portability"))
    return out


# ---------------------------------------------------------------- driver


def run(root: Path):
    spec_path = root / "skills/shared/scripts/selfcheck.json"
    spec = json.loads(_read(spec_path)) if spec_path.is_file() else {}
    findings = []
    findings += check_includes(root)
    findings += check_flag_spelling(root, spec)
    findings += check_flag_default_drift(root)
    findings += check_namespace_registry(root)
    findings += check_field_consumers(root, spec)
    findings += check_tag_covers(root, spec)
    findings += check_host_constructs(root, spec)
    return findings


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="plugin root")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        selftest()
        return 0

    root = Path(args.root).expanduser().resolve()
    findings = run(root)

    if args.json:
        json.dump({"script_version": SCRIPT_VERSION, "findings": findings},
                  sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        if not findings:
            print("selfcheck: clean")
        else:
            by = {}
            for f in findings:
                by.setdefault(f["check"], []).append(f)
            for check, items in sorted(by.items()):
                print(f"\n== {check} ({len(items)}) ==")
                for f in items:
                    print(f"  [{f['severity']}] {f['file']}")
                    print(f"      {f['detail']}")
                    print(f"      fix: {f['fix']}")
            crit = sum(1 for f in findings if f["severity"] == "critical")
            print(f"\nselfcheck: {len(findings)} finding(s), {crit} critical")
    return 1 if any(f["severity"] == "critical" for f in findings) else 0


# ---------------------------------------------------------------- selftest


def selftest():
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "skills/alpha/references").mkdir(parents=True)
        (root / "skills/shared/scripts").mkdir(parents=True)

        # C1: one resolving include, one dangling
        (root / "skills/shared/real.md").write_text("shared\n", encoding="utf-8")
        (root / "skills/alpha/SKILL.md").write_text(
            "# Alpha\n"
            "@../shared/real.md\n"
            "@../shared/ghost.md\n"
            "| `--deep-chain` | `off` | description |\n"
            "| `--no-deep-chain` | — | not marked |\n"
            "Deep-chain is DEFAULT ON here.\n"
            "emit `[A-ZZ-{seq}] something`\n",
            encoding="utf-8")
        (root / "skills/alpha/references/report-formats.md").write_text(
            "Finding ID namespaces:\n  A-{seq} base\n", encoding="utf-8")

        f = run(root)
        kinds = {x["check"] for x in f}
        assert "include-resolves" in kinds, "C1 must flag the dangling include"
        assert any("ghost.md" in x["detail"] for x in f if x["check"] == "include-resolves")
        assert not any("real.md" in x["detail"] for x in f), "resolving include must not flag"
        assert "flag-spelling" in kinds, "C2 must flag an undeprecated --no- twin"
        assert "flag-default-drift" in kinds, "C3 must flag prose contradicting the table"
        assert "namespace-registry" in kinds, "C4 must flag an unregistered namespace"

        # C2 must go quiet once the negative form is marked deprecated
        p = root / "skills/alpha/SKILL.md"
        p.write_text(_read(p).replace("| `--no-deep-chain` | — | not marked |",
                                      "| `--no-deep-chain` | — | Deprecated alias. |"),
                     encoding="utf-8")
        assert not any(x["check"] == "flag-spelling" for x in run(root)), \
            "a deprecated-marked alias is legal and must not be flagged"

        # C3 must go quiet once the prose agrees
        p.write_text(_read(p).replace("Deep-chain is DEFAULT ON here.",
                                      "Deep-chain is DEFAULT OFF here."),
                     encoding="utf-8")
        assert not any(x["check"] == "flag-default-drift" for x in run(root)), \
            "prose agreeing with the table must not be flagged"

        # C5 + C6
        prod = root / "skills/alpha/references/prompt.md"
        prod.write_text("output:\n  errors_raised: []\n  errors_propagated: []\n",
                        encoding="utf-8")
        cons = root / "skills/alpha/consumer.md"
        cons.write_text("compare errors_raised only\n", encoding="utf-8")
        spec = {
            "field_consumers": {
                "skills/alpha/references/prompt.md": {
                    "fields": ["errors_raised", "errors_propagated"],
                    "consumers": ["skills/alpha/consumer.md"],
                }
            },
            "tag_covers": {
                "demo-v1": {"files": {"skills/alpha/references/prompt.md": "0" * 16}}
            },
        }
        (root / "skills/shared/scripts/selfcheck.json").write_text(
            json.dumps(spec), encoding="utf-8")

        f = run(root)
        fc = [x for x in f if x["check"] == "field-consumers"]
        assert len(fc) == 1 and "errors_propagated" in fc[0]["detail"], \
            "C5 must flag exactly the field no consumer reads"
        assert any(x["check"] == "tag-covers" for x in f), \
            "C6 must flag a covered file whose hash moved"

        # C5 quiet once the consumer reads it; C6 quiet once the hash is recorded
        cons.write_text("compare errors_raised and errors_propagated\n", encoding="utf-8")
        h = hashlib.sha256(_read(prod).encode("utf-8")).hexdigest()[:16]
        spec["tag_covers"]["demo-v1"]["files"]["skills/alpha/references/prompt.md"] = h
        (root / "skills/shared/scripts/selfcheck.json").write_text(
            json.dumps(spec), encoding="utf-8")
        f = run(root)
        assert not any(x["check"] in ("field-consumers", "tag-covers") for x in f), \
            "C5/C6 must go quiet once wired and recorded"

    print("selfcheck.py selftest: OK")


if __name__ == "__main__":
    sys.exit(main())
