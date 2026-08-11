# ConstraintBox — complete state report, 9 August 2026

## What this is

A full account of what ConstraintBox is, what has been built, what is proven, and what is
claimed but not earned. It is written to be handed to another model or person for audit, so
every number carries the command that produced it and every claim carries its rung on the
status ladder.

Read the honest summary first. It is short and it is not flattering.

## How to check this yourself

```
cd /Users/joshuaeisenhart/Codex-Ratchet
PY=/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3

$PY constraint_box/scripts/gate_dependency_stack.py            # estate: declared / present / used
$PY constraint_box/scripts/gate_dependency_stack.py --self-test # the gate's own negative control
$PY -m constraint_box.hookkernel.kernel session_start           # the hook kernel, live
$PY constraint_box/scripts/refresh_estate_metadata.py           # live PyPI authority
$PY -m constraint_box.hookkernel.kernel estate_metadata_refreshed
$PY -m pytest constraint_box -q                                 # the suite
```

Nothing below should be believed on the strength of this document. Each command re-derives its
own number.

---

## 1. The honest summary

ConstraintBox is a deterministic gating harness for mass looping swarms of diverse LLMs, where
the LLMs do not control their own gating. Gates are code, never model judgement.

Today it has, for the first time, a hook spine that fires on events the model does not choose,
and that spine caught real defects including several in itself. That is genuine progress and it
is the first thing all day that does not depend on trusting a model's report.

It also produced, today, a textbook example of the failure it exists to prevent: a registry row
carrying fabricated verification metadata, which a gate then fired on and reported as a live
success. That is recorded in full at section 6 because it is the most instructive artefact here.

| dimension | state |
|---|---|
| environment | 92 packages installed and importable, locked for macOS only |
| tool activation | 92 present, 11 imported by CB source, 5 with fired negatives |
| gates | 139 inventoried, 3 on the production call path, 1 boundary-mapped |
| probe coverage | 294 mutants survive, 612 mutants no test reaches |
| hooks | 4 wired, 167 chained receipts, 8 distinct negatives observed firing |
| manifold layers | C0 finitude accepted, C1/C2/C3 candidate |
| cross-platform | not established. macOS only |
| repository | 18 commits local, none pushed |

---

## 2. Stage order, and whether each stage was actually completed

The binding rule is that stages are not skipped. Measured against that rule, honestly:

| stage | state | evidence |
|---|---|---|
| 0. freeze current state | **skipped** | no baseline receipt was taken before repairs began |
| 1. environment real | **done** | 92/92 import; `gate_dependency_stack.py` exits 0 |
| 1b. environment reproducible | **not done** | lock covers macOS only; no Linux or Windows lock |
| 2. probe substrate | **partial** | probe format exists; determinism proven on one gate |
| 3. tool roles | **partial** | roles declared for 92; 11 have a caller; 5 have fired negatives |
| 4. gate repair and mapping | **partial** | 5 bindings repaired; 1 of 139 boundary-mapped |
| 5. Mini-LevOS vertical slice | **not started** | no end-to-end CB → MiniLev → CB run with a probe map |
| 6. full tool activation | **not started** | 81 of 92 packages imported by nothing |
| 7. CB supervises simulation | **not started** | correctly blocked behind earlier stages |
| 8. ratchet and release | **partial** | ratchet built and self-validating; not wired to production |

Two stages were genuinely skipped and should be named as such. Stage 0 was never done — repairs
began before any frozen baseline existed, which is why several "before" numbers in today's work
are reconstructions rather than measurements. Stage 1b is incomplete while the cross-platform
requirement is stated as met in prose and unmet in fact.

Work did **not** skip ahead into stages 5, 6 or 7. Those are untouched, which is correct.

---

## 3. The hook spine — what actually fires

Four hooks are wired. Two were added today; two pre-existed.

| hook | event | can block | status |
|---|---|---|---|
| `SessionStart` | session start | no | pre-existing, reinjects project rules |
| `PostCompact` | context compaction | no | pre-existing |
| `PreToolUse` (Bash) | pip/uv/python commands | **yes, exit 2** | added today |
| `PostToolUse` | every tool result | no, records only | added today |
| `Stop` | end of every turn | disabled | added today, then disarmed — see below |

The hook kernel is `constraint_box/hookkernel/`, 237 lines at time of writing, standard library
only. It does not import `constraintbox` and does not import any of the 92 estate packages,
because it judges that estate and cannot depend on it. A test walks its AST and fails on any
non-stdlib import.

### Negatives observed firing

This is the number that matters, not the pass count. From the live receipt chain, 167 records:

| verdict | count |
|---|---|
| ADMIT | 95 |
| REFUSE | 37 |
| HOLD | 35 |

| reason code | times fired |
|---|---|
| `OBSERVATION_RECORDED` | 79 |
| `COMPLETION_UNEARNED` | 19 |
| `ENV_INTERPRETER_MISMATCH` | 18 |
| `KERNEL_TAMPERED` | 18 |
| `HOOK_RESULT_INVALID` | 6 |
| `LOCK_VALID` | 4 |
| `LOCK_STALE` | 4 |
| `CURRENTNESS_EXPIRED` | 4 (verdict now retired, see section 6) |
| `ENV_INTERPRETER_VALID` | 4 |
| `COMPLETION_EARNED` | 4 |
| `CURRENTNESS_VALID` | 3 |
| `PROBES_REQUIRED` | 2 |
| `PROBES_CURRENT` | 1 |
| `METADATA_SOURCE_DISAGREEMENT` | 1 |

Eight distinct refusal codes have fired against real events. That is the evidence that the spine
is non-constant. It is **not** evidence that it is boundary-mapped.

### Defects the hooks found in themselves

The spine caught six of its own faults in the first hours of running:

1. Over-broad shell matching — the guard refused commands that merely mentioned pip.
2. Permanent HOLD deadlock — a fact once bad could never return to good, so the gate jammed.
3. Caller-forged currentness — the kernel accepted a caller's `today` override.
4. Caller-forged lock status — it accepted a caller's `lock_covers_declared_set` boolean.
5. Missing probe-resolution lifecycle — `PROBES_REQUIRED` had no way to be discharged.
6. `Stop` hooked to every conversational turn rather than to an actual completion claim.

All six were fixed by making the constraint recompute from an authority. None by weakening a
check. Fault 6 was fixed by disarming the `Stop` block, which is a real reduction in enforcement
and is recorded as such: the completion check still runs and still writes its receipt, but it no
longer blocks.

---

## 4. Gates

139 gates inventoried across `constraint_box` and `claimgate_plugin`.

| category | count |
|---|---|
| proposal reason codes | 44 |
| construction invariants | 30 |
| runtime invariants | 30 |
| module gate candidates | 20 |
| `gate_operations` `cb:*` gates | 11 |
| contract identifiers | 4 |

**Three gates are on the production call path.** `model_tier_reasons` via `agentrun.py:893`,
and `cb:sympy-exact-gate` plus `cb:maude-transition-gate` via `run_formal_flow_gates` at
`agentrun.py:1137`. The other 136 are reachable from harnesses and tests, not from a production
run.

**One gate is boundary-mapped** with independent deciders. The rest are at best non-constant.

Five broken bindings were repaired today: two SMT gates reading a status string as a dict, a
boundary gate reading fields absent from its input object, and two gates shelling out to a bare
`python` that does not exist on this host. One gate was emitting `ACYCLIC_REACHABLE` for a
property it never computed; it now computes it.

---

## 5. Tools and the constraint set

### The bar

Encoded in `constraint_box/config/cb_light_library_candidates.json`:

```
platforms_required                linux, macos, windows
python_versions_required          3.12, 3.13
stale_days_max                    548
max_declared_runtime_deps         3
max_wheel_bytes                   5 MB
requires_python_must_be_declared  true
```

139 candidates measured against it: **92 keep, 47 drop**.

### The estate ladder

| rung | count | meaning |
|---|---|---|
| declared | 92 | named in a requirements file or pyproject |
| present | 92 | imports in the mandated interpreter |
| used | 11 | imported by CB source, established by AST parse not grep |
| proven | 5 | has a negative that fired |

The gap between 92 present and 11 used is the honest state of tool activation. The gap between
11 used and 5 proven is the honest state of integration.

### Independent deciders available

| question | independent mechanisms |
|---|---|
| graph and DAG | rustworkx, networkx, igraph, finite enumeration |
| satisfiability | z3, cvc5, bounded enumeration |
| exact arithmetic | sympy, `fractions.Fraction` |
| hashing and chains | hashlib, blake3, independent recompute |
| schema | jsonschema, pydantic, attrs |
| rewriting | maude, explicit finite state enumeration |

Four independent graph engines are installed. Until today the gate that reported acyclicity ran
none of them.

---

## 6. The fabricated-metadata incident

This is the most instructive artefact of the day and it belongs in the permanent record.

The registry carried, for every row, a `verified` block stamped `checked_at: 2026-08-09`. For
`tabulate` it declared:

```
registry:  tabulate 0.10.0  released 2024-12-01  requires_python >=3.6
PyPI:      tabulate 0.10.0  released 2026-03-04  requires_python >=3.10
```

Same version. 458 days apart. The row had never been checked against PyPI despite the stamp.

The hook kernel then fired `CURRENTNESS_EXPIRED` on that fabricated date and it was reported as
the kernel's first live firing on real data. It was a false positive on invented evidence.

Measured scope, all 86 adopted rows against live PyPI:

| result | count |
|---|---|
| agree with PyPI | 75 |
| `METADATA_SOURCE_DISAGREEMENT` | 11 |
| stale by live data | **0** |

Every one of the 11 disagreements is in `cb-candidates-passing.in`. With `tabulate` that is the
entire 12-row group and only that group. The disagreements are not only dates: `platformdirs`
declared `>=3.8` where PyPI says `>=3.10`, and `stamina` and `structlog` the same — compatibility
claims wrong in the permissive direction.

### What changed as a result

`CURRENTNESS_EXPIRED` was retired as a verdict. Age past the bar now yields
`MAINTENANCE_REVIEW_REQUIRED`, which means consult the authority, not "abandoned" — a mature
library can sit 600 days and remain maintained, while a malicious one can upload yesterday. The
clean local path is `CURRENTNESS_LOCAL_OK` and carries its own ceiling text: *local registry
only; not confirmed against PyPI*.

`constraint_box/hookkernel/pypi_authority.py` is the separate authority. Every fetch records the
raw response sha256 and the retrieval timestamp, so measurement is distinguishable from
assertion. The refresh script deliberately does **not** rewrite the registry — overwriting it
with PyPI values would destroy the disagreement, which is the evidence.

The kernel now holds on the conflict rather than resolving it:

```
seq 164   HOLD   METADATA_SOURCE_DISAGREEMENT   11 rows   estate_currentness: disputed
```

Neither side wins. The registry is authoritative for what the registry says; PyPI is
authoritative for what PyPI holds.

---

## 7. Probes, and why the suite number is worthless

The suite reports 1070 passed, 0 failed. That number should not be read as success.

| measure | count |
|---|---|
| test functions | 1040+ |
| assertions pinning an exact reason code | 10 |
| test modules with zero refusal assertions | 36 of 94 |
| mutants that survived | 294 |
| mutants no test reaches | 612 |

A green suite establishes that the assertions are satisfiable. It does not establish that any of
them can fire. 294 surviving mutants is the direct measurement of how many cannot.

One concrete example, verified by hand. In `model_tier_budget.py`, changing the string
`"UNKNOWN"` to `"unknown"` on the non-string-slug branch:

```
unmutated:  non-string slug -> ['MODEL_TIER_UNKNOWN']
mutated:    non-string slug -> ['MODEL_TIER_ROLE_FORBIDDEN']
```

Both refuse, so every test still passes, but the reason code is wrong and an operator debugging
it would be told the wrong thing. No test passes a non-string slug, so nothing catches it.

### The probe standard

A gate does not detect a universal property. It partitions a finite probe set, and its meaning
is that partition. So the receipt reports two separate verdicts and never rounds one up:

- `non_constant` — at least one probe admitted, one refused. The weak claim.
- `boundary_mapped` — every reason code has a boundary pair that flipped, and at least two
  independent deciders agree across the family. The strong claim.

A boundary pair is two probes differing in exactly one field where the verdict flips. Where a
one-field change does **not** flip the verdict, that is recorded too: the gate is blind to that
field, which maps an equivalence class rather than a boundary.

---

## 8. The manifold layers in CB

`constraint_box/src/constraintbox/manifold_foundation.py`, reachable from `cli.py:89` and
`cr_sim_slice.py:24`. Seed at `constraint_box/fixtures/cr/manifold_time_first_seed_v1.json`:

| layer | status |
|---|---|
| `C0_finitude` | accepted_seed |
| `C1_time_opening_binding` | candidate |
| `C2_noncommutation` | candidate |
| `C3_nonassociativity` | candidate |

Finitude is the only accepted layer, and it is load-bearing throughout: `FiniteConstraintProblem`
is used by 8 modules, and finite enumerated domains are what make bounded enumeration a genuine
independent decider against z3 and cvc5 almost everywhere.

`manifold_foundation.py:194` refuses to admit `C3_nonassociativity` at any status other than
candidate or unvalidated. That is the owner's ruling — the order in which finitude,
non-commutation and non-associativity ratchet is **open** and must not be hard-coded — enforced
in code rather than only written down. The validator raises rather than accepting a promotion.

Non-commutation is present as a candidate layer but has no probe family and no constraint that
fires on it. Lev OS declares `N01_NONCOMMUTATION` a root axiom alongside `F01_FINITUDE`; CB
currently carries the first as a live constraint and the second as a name.

---

## 9. What is claimed but not earned

Stated plainly, because these are the places where a reader should not believe the system:

- **`KERNEL_TAMPERED` is not tamper protection.** The manifest was repinned by the same agent
  that edited the kernel, repeatedly, today. The earned ceiling is `SELF_CONSISTENCY_CHECKED`.
  Real tamper-evidence needs a hash the agent cannot update.
- **The receipt chain is internally chained, not externally anchored.** It is append-only by
  construction and writable by the agent. Its head is not committed anywhere out of reach.
- **`PROBES_CURRENT` cleared on an aggregate.** One receipt reporting fired negatives discharged
  the obligation globally. It should be per-obligation, indexed by tool, version, platform and
  constraint.
- **Cross-platform is unmet.** One macOS lock. No Linux, no Windows, no execution evidence on
  either. A `py3-none-any` wheel is an installation claim, not a portability claim.
- **The estate count has been reported as 86, 91 and 92 in different places.** PEP 503 name
  normalisation explains some of it. It has not been reconciled row by row.
- **Stage 0 was never done.** No frozen baseline exists from before today's repairs.

---

## 10. Immediate next work, in dependency order

1. Freeze the state properly — the baseline receipt that stage 0 required.
2. Reconcile the estate count row by row into one canonical manifest with disjoint sets.
3. Replace aggregate `PROBES_CURRENT` with per-obligation resolution.
4. Emit the hook topology as a tracked, portable manifest so a second machine can reproduce it.
5. Generate Linux and Windows locks, and get execution evidence on both.
6. Anchor the kernel hash and the receipt-chain head somewhere the agent cannot rewrite.
7. Only then begin the Mini-LevOS vertical slice.

Nothing in 5, 6 or 7 should start before 1 through 4 are done. That ordering is the point of the
system, and the two skipped stages in section 2 are what happens when it is not respected.

---

## Status ladder used throughout

`exists < runs < passes local rerun < canonical by process`

No claim in this document is at `canonical by process`. The hook spine, the estate install and
the gate repairs are at `passes local rerun`. Everything in section 9 is below that.

`promotion_allowed: false` for every receipt referenced here.
