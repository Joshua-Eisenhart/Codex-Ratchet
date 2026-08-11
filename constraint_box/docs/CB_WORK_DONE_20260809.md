# What was done, 9 August 2026

A plain record of what changed on disk, so the next thread does not restart.
Nothing here is a claim of success. Read `OWNER_PROMPTS_VERBATIM_20260809.md`
first — that is your words, and it wins over this file.

## The short version

The work stayed on gate hardening for most of a day when the project's own
documents say the system is a wall plus a swarm, and the swarm was never built.
The gates that were built are conditionals, not constraint problems, so they
do not use the SMT layer the design is founded on. Both facts are measured
below, not estimated.

---

## Committed to the repo

18 commits on `claimgate/bypass-regression`, none pushed. The push fails at the
transport layer because an 83.7 MB text manifest committed this morning is the
largest object in the repository's history.

### New files that work

| file | what it does |
|---|---|
| `constraint_box/hookkernel/` | 237-line stdlib-only hook kernel: registry, chained receipts, four wired hooks |
| `constraint_box/hookkernel/pypi_authority.py` | live PyPI metadata with raw-response hash and retrieval time |
| `constraint_box/scripts/gate_dependency_stack.py` | reports declared / present / used separately, with its own negative control |
| `constraint_box/scripts/refresh_estate_metadata.py` | measures all 91 declared libraries against live PyPI |
| `constraint_box/scripts/library_admission_box.py` | encodes the bar as a FiniteConstraintProblem — written, not yet run |
| `constraint_box/src/constraintbox/model_tier_budget.py` | model tier ladder, wired into the production run path |
| `constraint_box/src/constraintbox/probe_family.py` | probe families with boundary pairs and independent deciders |
| `constraint_box/src/constraintbox/deciders.py` | multi-decider registry, disagreement as a first-class result |
| `constraint_box/scripts/prove_gates_fire.py` | 139-gate enumeration with positive and negative controls |
| `MODEL_DOSSIER/cleanup_index/` | content-hash indexes of the four Desktop planning folders |

### Repairs

- five broken gate bindings in `gate_operations.py` — two SMT gates reading a
  status string as a dict, a boundary gate reading absent fields, two gates
  shelling out to a `python` that does not exist here
- `cb:rustworkx-workflow-gate` was returning `ACYCLIC_REACHABLE` for a property
  it never computed; it now computes it
- the editable install pointed at a deleted directory, so `pip show` reported
  `constraintbox` installed while `import constraintbox` failed
- `ClaimGate`'s `constraintbox gate <receipt>` entrypoint had been dropped from
  the default CLI parser; restored
- the strict receipt consumers never called `HashChainLedger.verify()`; they do now
- `process_ratchet.py` wrote wall-clock into chained content, making the chain
  unreplayable; removed, plus self-validation before advance at 6 ms per advance
- 91 declared libraries installed into the mandated interpreter — previously 23

---

## Measured state

| measure | value |
|---|---|
| libraries declared / installed / imported by CB source / with a fired negative | 91 / 91 / 11 / 5 |
| gates inventoried | 139 |
| gates on the production call path | 3 |
| gates boundary-mapped | 1 |
| gates using a FiniteConstraintProblem | **0** |
| conditionals in `gate_operations.py` and the hook kernel | **68** |
| surviving mutants | 294 |
| mutants no test reaches | 612 |
| assertions pinning an exact reason code | 10 of ~1040 tests |
| suite | 1070 passed, 0 failed |
| councils built | **0** |

The suite number is the least informative one here. 294 surviving mutants is
the measurement of how many of those 1070 assertions can actually fire.

---

## Two findings worth keeping

### The registry carried fabricated verification metadata

`tabulate 0.10.0` was recorded as released 2024-12-01 with `requires_python >=3.6`,
stamped `checked_at: 2026-08-09`. PyPI reports 2026-03-04 and `>=3.10` for that
same version — 458 days apart, and the row had never been checked.

The hook kernel fired `CURRENTNESS_EXPIRED` on that fabricated date and it was
reported as its first live firing. Measured across all 86 adopted rows: 75 agree
with PyPI, 11 disagree, **0 are actually stale**. Every disagreement is in
`cb-candidates-passing.in` — the whole 12-row group and only that group.

`CURRENTNESS_EXPIRED` was retired. Age past the bar now yields
`MAINTENANCE_REVIEW_REQUIRED`, and a registry/PyPI conflict is preserved as
`METADATA_SOURCE_DISAGREEMENT` rather than resolved by preferring a side.

### The gates are doors, not boxes

Measured: `FiniteConstraintProblem` appears 0 times in `gate_operations.py`,
`kernel.py` and `model_tier_budget.py`. There are 68 `if bad: return "REFUSE"`
conditionals across them.

That is why 132 of 139 gates use none of the five core tools — a conditional
does not need a solver. Only a finite domain does. It is also why mutation found
294 survivors: a conditional has no boundary to cross, so flipping `"UNKNOWN"` to
`"unknown"` changes the emitted reason code and no test notices.

`FiniteConstraintProblem` at `constraints.py:96` and `dual_solve` at
`dualsolve.py:492` are the box primitive. They were not used.

---

## What the project documents say is missing

From `CB_UPGRADE_WORK.md` and `OWNER_RULINGS_VERBATIM_20260806.md`, neither of
which was read until the end of the day:

- **six councils that do not exist** — `decision.context_strategy`,
  `decision.move_selection`, `decision.evidence_boundary`,
  `follow_up.next_move_selector`, `follow_up.lane_builder`, `follow_up.compile_gate`
- **two Failure councils never run**, five managers specced and never run
- **nested councils are three layers**: council members are themselves councils,
  3-5 x 3-5 x 3-9
- **SQLite was ruled** for the store (A8). The hook kernel uses JSONL.
- **CB is not a truth gate** (A1): it constrains the domain and the input set.
  Everything built today judges outputs.
- **"just call them all"** (D2) already settles the 91-declared / 11-used gap.

Still open from the 6 August work order: poisoned receipts unquarantined in
`constraint_box/receipts/`, and `cb_wave_falsifier_v3.py` hardcoding
`councils_run: 0` so it kills every target.

---

## How to check any of this

```
cd /Users/joshuaeisenhart/Codex-Ratchet
PY=/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3

$PY constraint_box/scripts/gate_dependency_stack.py
$PY constraint_box/scripts/gate_dependency_stack.py --self-test
$PY constraint_box/scripts/refresh_estate_metadata.py
$PY -m constraint_box.hookkernel.kernel session_start
$PY -m pytest constraint_box -q
```

## To push

```
git -C /Users/joshuaeisenhart/Codex-Ratchet config http.postBuffer 524288000
git -C /Users/joshuaeisenhart/Codex-Ratchet push origin claimgate/bypass-regression
```

The 83.7 MB manifest lands in remote history permanently if you do. The
alternative is rewriting history to drop it, which was not done unasked.

`promotion_allowed: false` on everything above.
