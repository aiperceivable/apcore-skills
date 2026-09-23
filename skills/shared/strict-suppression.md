# Strict-Mode Suppression (shared rules — audit & sync)

<!-- STRICT-SUPPRESSION-LOADED -->


This document defines the **lean vs strict** finding-suppression policy shared by `apcore-skills:audit` and `apcore-skills:sync`. Both skills consume this rule set from their noise-control pipeline (audit Step 2.5.6, sync Step 9.0.3) so that the lean/strict semantics never drift between the two commands.

## Purpose

Cross-language SDK audits produce a long tail of low-signal findings — language-idiom differences, defensive-depth divergences, style nits — that are *real* in the sense that "the code differs" but provide no actionable bug-fix signal. Without suppression, every audit/sync round re-surfaces them and the operator never reaches "zero warnings". Lean mode is the default and hides this tail. Strict mode (`--strict`) restores it for release audits.

**Design principle.** This is not a "won't fix" filter — those findings are still useful for periodic release reviews. It is a **default-vs-opt-in** split: most users most of the time want the minimal actionable set; specific moments (release audit, API-surface harmonization) want the full set.

## Inputs

Both calling skills compute a single boolean:

- `STRICT_MODE = true`  when `$ARGUMENTS` contains `--strict`
- `STRICT_MODE = false` otherwise (lean is the default)

## Suppression rule — a finding is "strict-only" when ANY of the following match

### (a) Language-idiom downgrade trace

The finding's `detail` (audit) or `description` (sync review-compat) field contains the literal marker:

```
[severity-calibration: downgraded from critical — X]
```

where X is exactly one of:
- `defensive-depth`
- `error-class-name-only`
- `async-no-work`
- `embedding-hygiene`
- `constructor-name-idiom`
- `type-wrapping`

These categories represent "the stricter SDK is fussy, no user-observable bug". They are emitted at `warning` severity per the standard severity-calibration rules (see `audit/references/dimension-prompts.md` D10 §Severity calibration) but provide no actionable signal in lean mode.

**Do NOT match:**
- `stub-field` — real dead-code signal, kept in lean mode
- `no observable trigger` — means the finding was downgraded for *lack of evidence*; surfacing as warning is correct
- A free-form sentence that mentions one of the keywords without the bracketed marker — match only on the exact bracketed trace, not on prose

### (b) Style-only naming findings

All of:
- The finding's category is in `{naming, naming_convention, language_idiom, style}` — audit D2 dimension, or sync Phase A 4.1–4.3 naming output
- `severity == "warning"` (critical naming findings — public symbol violates a documented naming contract with caller-observable impact — are never suppressed)
- The `fix` / `suggestion` field's primary action is one of:
  - Add a language-specific lint suppression (`#[allow(clippy::...)]`, `// eslint-disable`, `# noqa`, etc.)
  - Rename for language idiom only (e.g. `APCoreMCP` → `ApcoreMcp`, `Url` → `URL`)
  - Convert acronym casing
  - Detect by matching the suggestion against: `allow\(clippy::`, `eslint-disable`, `# noqa`, `rename to .*[A-Z][a-z]`, `idiomatic`, `consecutive-capital`, `upper_case_acronyms`, `acronym`

**Do NOT match:** Naming findings whose suggestion targets a public-API rename that crosses a language boundary (those carry caller-observable impact and stay at `warning` even in lean mode). When in doubt, keep the finding — false-negative suppression is worse than false-positive surfacing.

### (c) `[verify-spec-first]` tag

The finding's `detail` / `description` contains the literal marker `[verify-spec-first]`. Sub-agents emit this when their recommendation depends on which spec version is authoritative and the audit/sync cannot independently resolve it. See `audit/references/dimension-prompts.md` §verify-spec-first convention for the emission rules.

This is distinct from `inconclusive` severity:
- `inconclusive` = "I cannot tell whether this is a bug" (low confidence)
- `[verify-spec-first]` = "this IS a divergence, but the direction of the fix needs spec verification" (high confidence + ambiguous resolution)

## Suppression action

- If `STRICT_MODE == true` → emit the finding as-is, no suppression. Continue to the next noise-control sub-step.
- If `STRICT_MODE == false` → drop the finding from the active findings list. Increment `n_strict_suppressed`. Track the suppressed finding's id + match-reason in a separate `strict_only[]` collection so the report can show a one-line aggregate hint.

## Hard guarantees (NEVER suppress, regardless of strict-only match)

The following finding classes always surface, even if they happen to also match one of the rules above. These take precedence over the suppression rule when in conflict.

- Any finding with `severity == "critical"` or `severity == "blocker"`.
- Any dead-code finding — audit D9 with `category` in `{dead_export, unused_internal, duplicate, parallel_impl, reachability, scope_creep, stub_noop, unused_config, unused_dep}`, or the sync equivalent. Suppressing dead code defeats the primary purpose of the bloat dimension. (Note: `loc_growth` is intentionally NOT in this list — it is a trend metric, not a bug signal, and may legitimately be suppressed.)
- Any spec-violation finding — audit D10 / sync 4B where `spec_says != "(not declared)"`. This is a contract violation, not idiom.
- Any chain-level structural divergence — audit D11 / sync 4C with `type` in `{missing-validation, missing-registration, semantic-divergence}`. These are real cross-language bugs.
- Any API surface gap — audit D1 / sync 4.1 with `category == "missing_symbol"`.
- Any security-gated surface (per the severity-calibration "Step 2 — Security-gate exception") — findings touching `Sandbox.*`, `AuditLogger.*`, `AuthProvider.*`, `*ApprovalHandler.*`. The severity-calibration framework already keeps these at `critical`; the suppression must respect that.

Apply the suppression pass LAST in the noise-control pipeline (after info consolidation, deduplication, etc.) so that hard-guarantee findings cannot be accidentally dropped by an earlier sub-step.

## Report surface

Both calling skills surface lean/strict state in two places:

**1. Report header — Mode line:**
```
Mode: {"strict (all findings)" if STRICT_MODE else "lean (style/idiom/verify-spec suppressed — pass --strict for all)"}
```

**2. Noise-Control line — strict-suppressed count column:**
```
Noise-Control: ... · {n_strict_suppressed} strict-only ({"hidden — pass --strict to see" if !STRICT_MODE else "shown"})
```

**3. SUMMARY footer hint** (only when `n_strict_suppressed > 0` AND `STRICT_MODE == false`):
```
ℹ {n_strict_suppressed} additional findings hidden in lean mode (language-idiom, style, spec-verify). Re-run with --strict to see them.
```

Do NOT enumerate the suppressed findings inline in lean-mode reports. The full list is only recoverable via a `--strict` re-run. This is the entire suppression mechanism — there is no other escape hatch.

## What this rule set deliberately does NOT do

- **Per-finding whitelist files** — no `.audit-ignore`. The intent is to filter by *category* (declared via severity-calibration markers at emission time), not by per-finding hash. A whitelist would let real regressions silently pass; category-based suppression preserves the auditing function while reducing noise.
- **Severity downgrade** — the matched findings retain their original severity in strict mode. Suppression is binary (visible / hidden), not graduated.
- **Sub-agent re-prompting** — the sub-agents emit the same findings regardless of mode. Suppression happens in the orchestrator after collection. This keeps the sub-agent prompts simple and the suppression policy version-controllable in one file.
