# SIM Promotion + Master Sim Gates (v1)
Status: DRAFT / NONCANON
Date: 2026-02-20

Goal: define deterministic promotion gates from lower-tier sims to higher-tier sims, including a strict gate for a single whole-system sim.

==================================================
1) Promotion Event Model
==================================================

Promotion is explicit and logged:
- `PROMOTE_REQUEST(sim_id, from_tier, to_tier)`
- `PROMOTE_PASS` or `PROMOTE_FAIL`
- reason tags are mandatory on fail

No implicit promotion is allowed.

==================================================
2) Promotion Gates (all required)
==================================================

`G1_DEPENDENCY_COVERAGE`
- all declared lower-tier dependencies exist
- all dependencies have valid evidence tokens

`G2_NEGATIVE_COVERAGE`
- target class has at least one negative sim with evidence
- negative sim includes explicit `failure_mode_id` and expected outcome class

`G3_GRAVEYARD_COVERAGE`
- target class has plausible failed alternatives in graveyard
- failed alternatives must contain replayable raw artifacts

`G4_REPRODUCIBILITY`
- rerun with same inputs/code produces same evidence hash set

`G5_NO_BYPASS`
- no policy bypass tag present
- no manual "force promote" allowed

`G6_STRESS_COVERAGE`
- required stress families are present for target class (`BASELINE`, `BOUNDARY_SWEEP`, `PERTURBATION`, `ADVERSARIAL_NEG`, `COMPOSITION_STRESS`)
- stress evidence is deterministic and replayable
- promotion is blocked if stress coverage is missing or non-replayable

==================================================
3) Failure / Demotion Rules
==================================================

If a promoted sim later fails reproducibility or dependencies drift:
- set status `DEMOTED`
- invalidate upward promotions that depended on the failing sim
- create repair target entries for A1 planning

==================================================
4) Whole-System Sim Gate
==================================================

Master sim id: `SIM_MASTER_T6` (or deterministic alias)

Admission requirements:
- all tiers `T0`..`T5` covered
- all promotion gates `G1`..`G6` pass
- at least one whole-system negative sim exists (`SIM_MASTER_T6_NEG`)
- whole-system alternatives exist in graveyard

`SIM_MASTER_T6` cannot be treated as valid if any lower-tier coverage regresses.

==================================================
5) Reporting Requirements
==================================================

Each run must emit:
- tier coverage table
- promotion pass/fail counts by tier
- master sim status (`NOT_READY|PARKED|ACTIVE|DEMOTED`)
- unresolved promotion blockers

==================================================
6) Forbidden Moves
==================================================

- Do not promote from `Tn` to `Tn+1` without `G1`..`G6`.
- Do not treat negative sims as optional for tier closure.
- Do not claim whole-system validity without a whole-system negative sim.
- Do not close graveyard coverage with trivial invalid junk.
