### Sub-agent Dispatch Policy (shared — READ BEFORE SPAWNING ANYTHING)

<!-- SUBAGENT-POLICY-LOADED -->


Normative for every skill in this plugin that spawns sub-agents: `sync`, `audit`,
`tester`, `release`, `integration`, `sdk`. These are hard limits, not guidance.

Cost in this plugin is dominated by sub-agent **count**, not by any single
sub-agent's depth. The ecosystem this plugin targets has ~23 repos; a rule of the
form "one per repo, all simultaneously" repeated across five phases is 115
sub-agents from one command.

---

#### P1. Announce the plan before the first spawn

Print the expected count and its arithmetic, then spawn:

```
Sub-agent plan: {step} = {n}  ({what each one covers})
                {step} = {n}
                Budget: {total} / {ceiling}
```

A run whose fan-out is never stated cannot be noticed going wrong until the quota
is gone.

#### P2. Global ceiling per invocation

| Skill | Ceiling | Rationale |
|---|---|---|
| `sync` | 40 | repos × modules; 4C dominates |
| `audit` | 12 | 6 parallel dimensions + D11 delegation |
| `tester` | 3 × repos | generation + execution + verification passes |
| `release` | 2 × repos | phases are sequential; only one phase in flight |
| `integration` | 4 | bootstrap is inherently small |
| `sdk` | 4 | bootstrap is inherently small |

On reaching the ceiling: **STOP spawning**, report what completed, and name the
flags that reduce the count. Never silently continue past it.

#### P3. Exactly one sub-agent per unit of work

One per repo, or one per module — whichever the step defines. **Splitting a unit
because it "looks too big" is forbidden.** Every split agent re-reads the unit's
shared context (barrel files, type definitions, config), so cost grows
superlinearly in the number of splits while the work covered stays the same.

Measured failure: a 3-repo extraction split by "cluster" became 20+ sub-agents and
exhausted a multi-hour quota without producing a single finding.

A unit too large for one pass is handled by **P7**, not by cloning the agent.

#### P4. Bounded concurrency

At most **3 sub-agents in flight** unless the step states otherwise. Dispatch in
batches; wait for a batch before starting the next. Unbounded parallel dispatch
starves the orchestrator's tool budget and multiplies the blast radius of P5.

#### P5. Rate limits: ABORT, never retry

| Failure | Action |
|---|---|
| Rate limit / HTTP 429 / "server is temporarily limiting requests" | **ABORT THE RUN.** Do NOT retry. Do NOT spawn queued sub-agents. Persist every completed unit (cache `put`, or write partial results to disk), then report: `"Rate limited after {N} of {total} sub-agents. Completed work is saved. Re-run to resume, or narrow scope with {flags}."` |
| Malformed / empty output | One retry with an explicit correction. Second failure → mark `failed`, surface as a finding. |
| Tool error / unreadable source | No retry. Mark `failed`, surface it. |

Retrying under a 429 is strictly negative expected value: the failed agent already
spent its input tokens, the retry spends them again, and the throttle makes a
second rejection *more* likely. A 429 retry cascade is the most expensive failure
mode in this plugin — it can exhaust a multi-hour quota and produce zero output.

**Cache first, abort second, never retry.**

#### P6. Ignore sub-agent notifications you did not spawn

Other sessions' agents can surface in the same transcript. Match every
completion/failure against your own spawn list by id. A name not on your list is
not yours: do not react to it, do not retry it, do not report it as your result.

#### P7. Large outputs go to a file, not into the reply

When a sub-agent's natural output exceeds a few KB, it **writes to a file and
returns a receipt** — a path, plus whatever small summary the caller must act on.
The caller reads slices of that file on demand.

This is what makes P3's one-agent-per-unit ceiling achievable. A step that both
demands complete coverage and caps the reply at a few KB is unsatisfiable on a
real repo, and an agent facing that contradiction will either under-report
(silently wrong) or subdivide (P3 violation). Remove the ceiling instead of making
the agent choose which rule to break.

**A receipt must never contain anything that scales with the input.** Measured:
a `FILE_MAP` section is 7.5–11 KB for a 285–398 symbol SDK, against a 2 KB reply
budget — it belongs in the file, cited by line range.

#### P8. Never pipe a large payload through stdout

A cached or generated payload read back via a shell command lands in the caller's
context in full. Write it to a file and print only metadata.

Measured: `extract_cache.py check` without `--out-file` printed 941 KB across
three repos, making a cache **hit** ~1200× more expensive than a miss. Any
`check`-like call whose payload can exceed a few KB must have a file-output mode,
and callers must use it.

---

#### P9. Reuse the extraction cache — never re-derive what another skill already extracted

`sync` Step 2 writes a complete public-API extraction per repo to:

    {ecosystem_root}/.apcore-skills-cache/sync/api/{repo_name}.extraction.md

It is **ecosystem-wide, not sync-private.** Every skill that needs a repo's public
surface, per-symbol signatures, per-method behavioral contracts, or a symbol→file map
reads it instead of re-deriving. Measured on this ecosystem it holds 1,019 symbols and
1,568 contract blocks across three SDKs, and cost ~1.07 M sub-agent tokens to produce.

Known consumers and what each takes:

| Consumer | Reads | Instead of |
|---|---|---|
| `sync` Step 4 | signatures, contracts (sliced per module) | — (owner) |
| `audit` D10 | the `contract:` blocks | re-extracting contracts from source |
| `audit` D9 check 1 | the `FILE_MAP:` section | re-enumerating the export surface |
| `tester` | the symbol list + signatures, to know what to generate cases for | re-reading each repo's exports |
| `release` | the export surface, for API-change detection between versions | re-scanning each repo |

**Rules for any consumer:**

1. **Check before scanning.** File present → read it in slices. Absent → fall back to
   scanning and say so in your output (`SOURCE: derived-from-source`), because a
   from-source pass and a cached pass are not guaranteed identical in depth.
2. **Read the coverage block.** Every file carries `EXTRACTION_VERIFICATION`. If the
   extraction was partial, your result is partial too — report that rather than
   silently comparing a subset.
3. **Never write to another skill's cache.** Only the owning skill (`sync` for
   `api/`) populates it. A consumer that repairs or extends an entry makes the
   content hash lie about what produced it.
4. **The cache records where a symbol is defined, never who calls it.** Caller
   analysis, reachability, and call graphs remain the consumer's own work.

#### P10. Index a large corpus; never load it

Spec corpora are the main-context twin of P7's sub-agent problem, and no sub-agent can
absorb them for you. Measured on `apcore/`: `PROTOCOL_SPEC.md` is 713 KB and
`docs/features/*.md` is 870 KB — ~1.6 MB, ~400 k tokens — of which only the 140
`## Contract:` blocks (250 KB, 29%) are normative for symbol-level comparison. The
other 71% is Overview / Requirements / Usage / Testing prose no checklist compares.

    grep -n '^## Contract: ' {doc_repo}/docs/features/*.md    # a few KB

Index with grep, slice by line range when you evaluate that symbol, discard before the
next. Applies to `sync` Step 3.1, `audit` D4 check 7 and D10 Step 1, and any future
step that reads a spec corpus.

---

#### Threshold design rule (why these failures recur)

Every failure above is one shape: **a fixed small limit applied to something that
grows with the repo.** Before writing any threshold, ask what it does on a repo
100× larger than the one in front of you.

A threshold whose failure mode is unbounded recurring cost — re-extraction on
every run, a permanent cache miss, a retry cascade — must be one a correct input
can actually clear. Gate on completeness ratios that a correct repo reaches
(symbol-defining file coverage == 100%), never on absolute sizes or on raw
percentages a healthy repo legitimately misses.
