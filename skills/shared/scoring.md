### Health Score Formulas

Canonical formulas for ecosystem health metrics. Referenced by audit (Step 3 Health Score), release (Step 2.5 consistency gate thresholds), and the `/apcore-skills` dashboard. Single source of truth — do not duplicate per-skill.

All scores are integers in `[0, 100]`. Start at 100 and subtract per finding; floor at 0.

#### Leanness Score (D9 — Bloat & Redundancy)

```
leanness = max(0, 100 - 5·critical - 2·warning - 0.5·info)
```

Where the counts are from D9 findings. A leanness score below **70** indicates the repo needs a dedicated cleanup pass before the next release.

#### Contract Parity Score (D10 — Intent Parity)

```
contract_parity = max(0, 100 - 8·critical - 3·warning - 0.5·info)
```

Counts are from D10 findings (both intra-language parity findings and integration consumer-contract findings). The per-critical penalty is higher than leanness because intent divergence is a more severe bug class — users will hit inconsistent behavior across SDKs. A contract parity score below **80** means at least one implementation is silently doing something different from its peers — must be fixed before release.

#### Release Gate Thresholds

Release Step 2.5 uses Contract Parity for the gate decision (explicit precedence — first match wins):

1. If `audit_critical > 0` OR `sync_critical > 0` → **BLOCK**
2. Else if `contract_parity < 70` → **BLOCK**
3. Else if `contract_parity < 90` → **WARN**
4. Else → **PASS**

#### Dashboard Display

`/apcore-skills` dashboard renders each score as `{score}/100` with a 10-cell progress bar (`▓` filled, `░` empty) where each cell represents 10 points. Example for score 72:

```
  Contract Parity (D10): 72/100  ▓▓▓▓▓▓▓░░░
```

#### Aggregate Ecosystem Health (for dashboard rollup — optional)

When multiple repos are audited in the same scope, compute group-level scores as the **minimum** across repos (weakest link), not the mean — a single divergent repo is a release blocker regardless of how many peers are clean:

```
group_leanness = min(per_repo_leanness_scores)
group_contract_parity = min(per_repo_contract_parity_scores)
```

The dashboard displays both per-repo and group-min scores for the latest audit.

#### Change Control

Any change to a formula or threshold in this file is a breaking change to release/audit behavior. It MUST:
1. Bump the minor version of apcore-skills itself
2. Appear in README's "Breaking Changes" section
3. Be called out in audit's Step 3 Health Score output (add a footnote "Scoring v{X.Y} per shared/scoring.md")
