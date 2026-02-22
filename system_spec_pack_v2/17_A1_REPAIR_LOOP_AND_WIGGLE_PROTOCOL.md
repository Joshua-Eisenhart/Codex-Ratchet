# A1 Repair Loop + Wiggle Protocol (v1)
Status: DRAFT / NONCANON
Date: 2026-02-20

Goal: define explicit A1 behavior when B rejects/parks candidates, while preserving non-deterministic exploration.

==================================================
1) Input Surfaces
==================================================

A1 reads:
- B canonical state (`state.json`)
- graveyard records (id, reason, raw_lines)
- A2 fuel queue (`fuel_queue.json`)
- rosetta overlays (noncanon)
- latest run provenance events

A1 writes:
- `A1_STRATEGY_v1` declaration only

A1 never writes directly to B state.

==================================================
2) Wiggle Envelope
==================================================

A1 is allowed to:
- explore alternative phrasings and compositions
- propose multiple nearby candidates per target
- include plausible wrong alternatives intentionally (graveyard fuel)

A1 is not allowed to:
- emit raw B artifacts directly
- bypass overlay bans / forbidden terms
- invent unsupported SPEC_KIND values

==================================================
3) Repair Loop (per cycle)
==================================================

Step 1: classify failures from recent graveyard/park set:
- schema failures
- undefined term failures
- derived-only failures
- dependency failures
- probe pressure parks
- sim evidence gaps

Step 2: choose repair operators:
- `OP_REORDER_DEPS`: move prerequisite terms earlier
- `OP_SPLIT_COMPOUND`: split large term into smaller atoms
- `OP_REBIND_TERM`: adjust bind target if invalid
- `OP_SIM_ADD`: add missing positive/negative sim references
- `OP_ALT_REWRITE`: rewrite alternatives to be plausible but still test failure surface
- `OP_CANON_PERMIT_ADD`: add permit/evidence path for term state transitions

Step 3: generate updated strategy with explicit deltas:
- each target should include `repair_from` refs to failed ids where applicable

Step 4: hand strategy to A0 for deterministic compilation.

==================================================
4) Failure-to-Operator Mapping (explicit)
==================================================

- `MISSING_DEPENDENCY` -> `OP_REORDER_DEPS`, `OP_SPLIT_COMPOUND`
- `UNDEFINED_TERM_USE` -> `OP_SPLIT_COMPOUND`, `OP_REORDER_DEPS`
- `DERIVED_ONLY_PRIMITIVE_USE` -> `OP_CANON_PERMIT_ADD`, `OP_REBIND_TERM`
- `PROBE_PRESSURE` -> reduce batch size or include probe coverage
- `SCHEMA_FAIL` -> normalize strategy fields and id formats
- `SIM_FAIL` / persistent pending -> `OP_SIM_ADD` or downgrade from "ratcheted meaningful" target

==================================================
5) Repair Attempt Budget
==================================================

Per target, configurable limits:
- max local mutation depth: 3
- max retries before park in A1 view: 5
- max speculative variants per cycle: bounded by `budget.max_items`

If budget is exceeded:
- keep unresolved targets in A2 fuel queue with explicit reason tags

==================================================
6) Explicitness Rules
==================================================

- Every proposed target must state dependencies explicitly.
- Every alternative must include an explicit expected failure mode.
- Every "ratcheted meaningful" claim must include evidence references (positive + negative + graveyard alt id).

==================================================
7) Do Not Do (A1)
==================================================

- Do NOT repeat identical failed candidates without structural mutation.
- Do NOT optimize for admission count alone.
- Do NOT submit targets with missing sim path for required evidence policy.
- Do NOT treat parked items as accepted progress.

