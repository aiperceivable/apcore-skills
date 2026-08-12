# sync — Step 4 checklist lookup tables

Reference tables for `apcore-skills:sync` Step 4.2 (Checklist Evaluation Rules).
Read this file when you reach 4.2; the evaluation rules themselves stay in
SKILL.md because they are execution logic, not lookup material.

> **Not in `shared/api-extraction.md` on purpose.** That file is `@`-included at
> the top of Step 4, so anything placed there loads unconditionally. These two
> tables are consulted only when you are actually rendering the checklist (§1) or
> evaluating a trait/interface contract (§2), so they live here and load on
> demand.

---

## §1 Master checklist table shape

The per-class checklist Step 4.1 builds and Step 4.2 evaluates. One row per
check item, one column per implementation repo, plus a `Status` column carrying
`PASS` / `FAIL` / `WARN`. Nest rows under the symbol they belong to.

```
┌────────────────────────┬──────────┬──────────┬──────────┬──────────┐
│ Check Item             │ Spec     │ Python   │ TypeScript│ Status   │
├────────────────────────┼──────────┼──────────┼──────────┼──────────┤
│ Registry               │          │          │          │          │
│  ├─ class exists       │ ✓        │ ✓        │ ✓        │ PASS     │
│  ├─ constructor params │          │          │          │          │
│  │  ├─ config: Config  │ required │ required │ required │ PASS     │
│  │  └─ discoverers     │ optional │ optional │ MISSING  │ FAIL     │
│  ├─ method: register   │          │          │          │          │
│  │  ├─ exists          │ ✓        │ ✓        │ ✓        │ PASS     │
│  │  ├─ name convention │ register │ register │ register │ PASS     │
│  │  ├─ params          │ (module) │ (module) │ (module) │ PASS     │
│  │  ├─ return type     │ None     │ None     │ void     │ PASS     │
│  │  └─ async           │ no       │ no       │ no       │ PASS     │
│  ├─ method: get_module │          │          │          │          │
│  │  ├─ exists          │ ✓        │ ✓        │ ✓        │ PASS     │
│  │  ├─ name convention │ get_mod  │ get_mod  │ getMod   │ PASS     │
│  │  ├─ params          │ (id)     │ (id)     │ (id)     │ PASS     │
│  │  └─ return type     │ Module?  │ Module?  │ Module?  │ PASS     │
│  ├─ method: scan_dir   │          │          │          │          │
│  │  ├─ exists          │ ✓        │ ✓        │ ✗        │ FAIL     │
│  │  ...                │          │          │          │          │
└────────────────────────┴──────────┴──────────┴──────────┴──────────┘
```

---

## §2 Trait / interface equivalence table

Used by Step 4.2 → *For each CLASS* → item 4 (Trait / Interface satisfaction).
For each trait contract the spec declares a class must satisfy, each
implementation must expose the equivalent using its language's idiomatic
mechanism.

| Spec contract | Python | TypeScript | Go | Rust | Java |
|---|---|---|---|---|---|
| `Display` (string repr) | `__str__` | `toString()` | `String() string` | `impl Display` | `toString()` |
| `Debug` (debug repr) | `__repr__` | `[util.inspect.custom]` | `GoString() string` | `impl Debug` | `toString()` (debug variant) |
| `Equality` | `__eq__` + `__hash__` | `equals()` + `hashCode()` (or value-equality lib) | `Equal(other) bool` | `impl PartialEq + Eq + Hash` | `equals()` + `hashCode()` |
| `Clone` | `__copy__` / `copy.copy` | `clone()` method | explicit copy func | `impl Clone` | `clone()` (Cloneable) |
| `Default construction` | classmethod `default()` | static `default()` | `NewX()` zero-value | `impl Default` | no-arg constructor |
| `Serialize` | `to_dict` / pydantic | `toJSON` / class-transformer | `MarshalJSON` | `impl Serialize` | Jackson annotations |
| `Iterator` | `__iter__` + `__next__` | `[Symbol.iterator]` | `Next() (T, bool)` channel | `impl Iterator` | `Iterator<T>` |
| `Context manager` | `__enter__` + `__exit__` | `Symbol.dispose` / `using` | `defer` + Close() | `impl Drop` | try-with-resources (`AutoCloseable`) |

**Fallback.** If the spec contract has no row above, use: *"implementation
exposes a method whose canonical-snake-case name matches the contract's spec
name"*.

**Severity.** A missing equivalent is `FAIL` with severity `critical`.
