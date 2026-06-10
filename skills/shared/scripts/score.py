#!/usr/bin/env python3
"""apcore-skills health scoring and release-gate — deterministic fast path.

Implements the canonical formulas and gate precedence in
skills/shared/scoring.md. Computing these in code (instead of in the LLM
context) removes arithmetic-error risk and the "do not re-implement the
formula" drift the scoring doc itself warns about.

Reads a JSON object on stdin, writes a JSON object on stdout.

Single-repo input:
  {
    "d9":  {"critical": 1, "warning": 8, "info": 5},
    "d10": {"critical": 3, "warning": 4, "info": 2},
    "d11": {"critical": 5, "warning": 2, "info": 0, "inconclusive": 3},
    "gate": {"audit_critical": 0, "sync_critical": 0}   // optional
  }

Multi-repo input (group-min rollup, ecosystem.md / scoring.md "weakest link"):
  { "repos": { "apcore-python": {<d9/d10/d11>}, "apcore-typescript": {...} },
    "gate": {"audit_critical": 0, "sync_critical": 0} }

Rounding policy (single source of truth, also noted in scoring.md):
  - DISPLAY scores are rounded half-up to an integer in [0, 100].
  - Release-gate threshold comparisons use the EXACT (unrounded) value, so a
    score of 89.5 is treated as < 90 (WARN) and never rounded up across a gate
    boundary.

Stdlib only.
"""
from __future__ import annotations

import json
import math
import sys


def _f(counts, key):
    return float((counts or {}).get(key, 0) or 0)


def leanness_raw(c):
    return max(0.0, 100 - 5 * _f(c, "critical") - 2 * _f(c, "warning") - 0.5 * _f(c, "info"))


def contract_parity_raw(c):
    return max(0.0, 100 - 8 * _f(c, "critical") - 3 * _f(c, "warning") - 0.5 * _f(c, "info"))


def deep_chain_parity_raw(c):
    return max(0.0, 100
               - 10 * _f(c, "critical")
               - 3 * _f(c, "warning")
               - 2 * _f(c, "inconclusive")
               - 0.5 * _f(c, "info"))


def display(raw):
    """Round half-up to an integer in [0, 100]."""
    return max(0, min(100, int(math.floor(raw + 0.5))))


def bar(score_int):
    filled = max(0, min(10, score_int // 10))
    return "▓" * filled + "░" * (10 - filled)


def gate_decision(contract_raw, deep_chain_raw, audit_critical, sync_critical,
                  deep_chain_has_critical):
    """Release gate per scoring.md — explicit precedence, first match wins."""
    if audit_critical > 0 or sync_critical > 0:
        return "BLOCK", "audit_or_sync_critical>0"
    if contract_raw < 70 or deep_chain_raw < 70:
        return "BLOCK", "parity<70"
    if deep_chain_has_critical:
        return "BLOCK", "deep_chain_critical_present"
    if contract_raw < 90 or deep_chain_raw < 90:
        return "WARN", "parity<90"
    return "PASS", "all_thresholds_met"


def score_single(obj):
    lean_raw = leanness_raw(obj.get("d9"))
    cp_raw = contract_parity_raw(obj.get("d10"))
    dcp_raw = deep_chain_parity_raw(obj.get("d11"))
    return {
        "raw": {"leanness": lean_raw, "contract_parity": cp_raw,
                "deep_chain_parity": dcp_raw},
        "leanness": display(lean_raw),
        "contract_parity": display(cp_raw),
        "deep_chain_parity": display(dcp_raw),
        "deep_chain_has_critical": _f(obj.get("d11"), "critical") > 0,
    }


def compute(obj):
    gate_in = obj.get("gate") or {}
    audit_c = int(gate_in.get("audit_critical", 0) or 0)
    sync_c = int(gate_in.get("sync_critical", 0) or 0)

    if "repos" in obj:
        per_repo = {name: score_single(counts)
                    for name, counts in obj["repos"].items()}
        # Group min = weakest link (scoring.md §Aggregate).
        def gmin(field):
            raws = [v["raw"][field] for v in per_repo.values()]
            return min(raws) if raws else 100.0
        g_lean = gmin("leanness")
        g_cp = gmin("contract_parity")
        g_dcp = gmin("deep_chain_parity")
        any_dc_crit = any(v["deep_chain_has_critical"] for v in per_repo.values())
        decision, reason = gate_decision(g_cp, g_dcp, audit_c, sync_c, any_dc_crit)
        return {
            "per_repo": {name: {
                "leanness": v["leanness"],
                "contract_parity": v["contract_parity"],
                "deep_chain_parity": v["deep_chain_parity"],
            } for name, v in per_repo.items()},
            "group": {
                "leanness": display(g_lean),
                "contract_parity": display(g_cp),
                "deep_chain_parity": display(g_dcp),
            },
            "bars": {
                "leanness": bar(display(g_lean)),
                "contract_parity": bar(display(g_cp)),
                "deep_chain_parity": bar(display(g_dcp)),
            },
            "gate": decision,
            "gate_reason": reason,
        }

    s = score_single(obj)
    decision, reason = gate_decision(
        s["raw"]["contract_parity"], s["raw"]["deep_chain_parity"],
        audit_c, sync_c, s["deep_chain_has_critical"])
    return {
        "leanness": s["leanness"],
        "contract_parity": s["contract_parity"],
        "deep_chain_parity": s["deep_chain_parity"],
        "bars": {
            "leanness": bar(s["leanness"]),
            "contract_parity": bar(s["contract_parity"]),
            "deep_chain_parity": bar(s["deep_chain_parity"]),
        },
        "gate": decision,
        "gate_reason": reason,
    }


def selftest():
    # Formula spot checks.
    assert display(leanness_raw({"critical": 1, "warning": 8, "info": 5})) == 77, \
        display(leanness_raw({"critical": 1, "warning": 8, "info": 5}))
    assert display(contract_parity_raw({"critical": 3, "warning": 4, "info": 2})) == 63
    assert display(deep_chain_parity_raw(
        {"critical": 5, "warning": 2, "info": 0, "inconclusive": 3})) == 38
    assert display(leanness_raw({"critical": 100})) == 0  # floor at 0
    assert bar(72) == "▓" * 7 + "░" * 3

    # Gate precedence.
    assert gate_decision(95, 95, 1, 0, False)[0] == "BLOCK"   # rule 1
    assert gate_decision(63, 95, 0, 0, False)[0] == "BLOCK"   # rule 2
    assert gate_decision(95, 95, 0, 0, True)[0] == "BLOCK"    # rule 3
    assert gate_decision(70, 95, 0, 0, False)[0] == "WARN"    # rule 4 (70 not < 70)
    assert gate_decision(95, 95, 0, 0, False)[0] == "PASS"    # rule 5
    # Unrounded boundary: 89.5 must be treated as < 90.
    assert gate_decision(89.5, 95, 0, 0, False)[0] == "WARN"

    # End-to-end multi-repo group-min.
    out = compute({"repos": {
        "a": {"d10": {"critical": 0}, "d11": {"critical": 0}},
        "b": {"d10": {"critical": 1}, "d11": {"critical": 0}},
    }})
    assert out["group"]["contract_parity"] == 92, out["group"]
    assert out["gate"] == "PASS", out
    print("score.py selftest: OK")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--selftest" in argv:
        selftest()
        return 0
    try:
        obj = json.load(sys.stdin)
    except Exception as e:
        json.dump({"error": "invalid_json_input", "detail": str(e)}, sys.stdout)
        sys.stdout.write("\n")
        return 2
    json.dump(compute(obj), sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
