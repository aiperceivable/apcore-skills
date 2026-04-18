### Health Score Formulas

Canonical formulas for ecosystem health metrics. Referenced by audit (Step 3 Health Score), release (Step 2.5 consistency gate thresholds), and the `/apcore-skills` dashboard. Single source of truth — do not duplicate per-skill.

All scores are integers in `[0, 100]`. Start at 100 and subtract per finding; floor at 0.

#### Leanness Score (D9 — Bloat & Redundancy)

```
leanness = max(0, 100 - 5·critical - 2·warning - 0.5·info)
```

Where the counts are from D9 findings. A leanness score below **70** indicates the repo needs a dedicated cleanup pass before the next release.

#### Contract Parity Score (D10 — Intent Parity, SHAPE-LEVEL)

```
contract_parity = max(0, 100 - 8·critical - 3·warning - 0.5·info)
```

Counts are from D10 findings (both intra-language parity findings and integration consumer-contract findings). The per-critical penalty is higher than leanness because intent divergence is a more severe bug class — users will hit inconsistent behavior across SDKs. A contract parity score below **80** means at least one implementation is silently doing something different from its peers — must be fixed before release.

#### Deep-Chain Parity Score (D11 — Intent Parity, CHAIN-LEVEL)

```
deep_chain_parity = max(0, 100 - 10·critical - 3·warning - 2·inconclusive - 0.5·info)
```

Counts are from D11 findings (cross-language call-graph divergences from sync Step 4C). The per-critical penalty is the highest in this file (10 points) because chain-level divergences are by definition bugs that shape-level checks missed — tolerating them silently breaks the "cross-language intent parity" guarantee that the ecosystem promises. `inconclusive` findings carry a 2-point penalty to discourage skills from flagging everything as inconclusive to dodge real critical findings.

A deep-chain parity score below **80** means at least one implementation's source diverges from peers in ways that require human review.

#### Release Gate Thresholds

Release Step 2.5 uses Contract Parity AND Deep-Chain Parity for the gate decision (explicit precedence — first match wins):

1. If `audit_critical > 0` OR `sync_critical > 0` → **BLOCK**
2. Else if `contract_parity < 70` OR `deep_chain_parity < 70` → **BLOCK**
3. Else if `deep_chain_parity` has any `critical` finding (regardless of score) → **BLOCK** — deep-chain critical is never acceptable at release time, since it means a language is behaving differently from peers in source code
4. Else if `contract_parity < 90` OR `deep_chain_parity < 90` → **WARN**
5. Else → **PASS**

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
group_deep_chain_parity = min(per_repo_deep_chain_parity_scores)
```

The dashboard displays both per-repo and group-min scores for the latest audit.

#### Change Control

Any change to a formula or threshold in this file is a breaking change to release/audit behavior. It MUST:
1. Bump the minor version of apcore-skills itself
2. Appear in README's "Breaking Changes" section
3. Be called out in audit's Step 3 Health Score output (add a footnote "Scoring v{X.Y} per shared/scoring.md")
