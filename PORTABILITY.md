# Host portability

This plugin is authored for Claude Code and installed for Codex as a skill tree
(`.codex/INSTALL.md`). Four constructs in the source are **host-specific**. None of them
fails loudly on its own, so each one is listed here with the behaviour to expect and the
fallback the documents already carry.

The inventory is held mechanically: `selfcheck.py`'s `host-constructs` check fails if a
construct appears in a file the manifest does not already list. The surface is allowed to
be non-zero; it is not allowed to grow silently.

---

## 1. `@../shared/*.md` includes — **load-bearing, fails silently**

**Claude Code:** the host expands the include, and the shared document's content is in
context.

**Elsewhere:** the line may be left as literal text. The skill then runs **without** the
shared document — and `subagent-policy.md` is where the sub-agent ceiling, the bounded
concurrency and the "a 429 aborts the run, never retry" rule live. Losing it silently is
how a run burns a multi-hour quota, which has happened.

**Fallback, already in the files:** every shared document begins with a marker comment
(`<!-- SUBAGENT-POLICY-LOADED -->`), and every include site is followed by an instruction
to read the file directly if the marker is not visible. An agent that follows the text
recovers on its own.

**If you port this:** make the include expand, or inline the shared documents at bundle
time. Do not rely on the reader noticing.

---

## 2. `$CLAUDE_PLUGIN_ROOT` — **breaks script invocation**

Used to locate `skills/shared/scripts/` from inside a skill.

**Elsewhere:** undefined, so the path resolves to `/skills/shared/scripts/...` and the
script is not found.

**Fallback, already in the files:** `api-extraction-protocol.md` states the rule — the
scripts live beside the shared docs under `shared/scripts/`, and a bundler rewrites the
path. Every consumer of a script also has a documented non-script fallback
(`discover.py` → manual discovery per `ecosystem.md` §0.1; `extract_cache.py` → treat
every entry as a miss; `extract-markers.sh` → the per-language grep patterns). **No step
blocks on a script being unavailable** — that is a deliberate property, not an accident.

**If you port this:** set the variable, or rewrite the paths at bundle time.

---

## 3. `Agent(subagent_type="general-purpose")` — **the parallelism model**

This plugin's cost and correctness both hinge on sub-agent dispatch: one per repo, one per
module, with a ceiling, bounded concurrency and an abort-on-429 rule.

**Elsewhere:** the spawning API differs. The *policy* is host-independent and stated in
prose (`shared/subagent-policy.md` P1–P10); only the call is not.

**If you port this:** map the call, and keep P1–P10. A host that cannot bound concurrency
or observe rate limits needs the ceilings lowered, not the policy dropped.

---

## 4. `AskUserQuestion` — **interactive checkpoints**

Used where scope is ambiguous (e.g. CWD is not inside a known repo).

**Elsewhere:** no equivalent. Every use is a checkpoint, never a data source, so a host
without it can print the question and stop, or take the documented default.

**If you port this:** substitute a prompt-and-halt. Do not silently guess the answer — the
question exists because guessing wrong sends a whole run at the wrong repos.

---

## What is *not* host-specific

Worth stating, because it is most of the value and it ports unchanged:

- Everything in `skills/shared/scripts/` is plain Python 3 / POSIX shell with no host
  dependency. `test.sh` runs anywhere.
- The extraction cache (`.apcore-skills-cache/`) is content-hashed files on disk.
- The report formats, finding-ID namespaces, severity mapping and the review-compatible
  output are plain markdown contracts.
- `selfcheck.py` holds the cross-file invariants on any host.
