# card — attractors_basin_native_schedule_v0

Date: 2026-07-10. Lane: make Attractors.jl load-bearing on one source-native finite schedule.
Directive source: external review immediate item 1 (dispatcher instruction, session
r0-three-engine-probes; advisory receipt lineage:
`system_v7/control/model_lane_receipts/engine_four_count_external_review_20260710/external_review_receipt.json`,
authority advisory_only).

Claim ceiling: `scratch_diagnostic`, `promotion_allowed = false`. Pure math, structural
indices only, seeded (rng seed 0), deterministic, standalone.

## Source contract (cited, copied read-only)

- `system_v7/constraint_core/engines/targets.json` (sha256
  `1d74d038881b528e67e7ac21d9feef09e26c942ebc0e8f3bbcbca1e78ebbe69e`) — the 16-stage
  cross-substrate contract: 8 terrain GKSL generators t0..t7, each paired with its 2
  native operators (Ti/Fi or Te/Fe), composed terrain-first ("down"). Model constants:
  G=0.35, KAP=1.0, Q=1-exp(-1), TH=pi/4, T_FLOW=1.0.
- `system_v7/constraint_core/engines/oracle_targets.py` (sha256
  `e97247034d7da3a2ebbd27bda01d348e76da6c7cd605144219a3f297524dcdfb`) — defines the
  generators (`gen`), operators (`op`), flow, and the native down-order stage list.
  Local copies in `source_copies/`; the engines directory itself is not written.

## Obligation

Measure basins of attraction for the native 16-stage schedule as a real 3D Bloch-vector
flow. Each stage = (terrain GKSL flow for T_FLOW, then native operator), native order
t0..t7 with each terrain's two native operators in the contract order. One full pass of
the 16 stages defines a stroboscopic map on the Bloch ball; Attractors.jl measures its
attractors and basins.

Controls (same instrument, same grid, same seed):

1. reversed schedule (stage order reversed);
2. grouped same-basis schedule (stages regrouped so same-basis operator blocks are
   adjacent);
3. commuting control pair (a same-basis dissipative+unitary pair, the pair type
   excluded by the P9 admissibility result — order gap 0);
4. one-axis control (single terrain generator + its unitary only, one axis).

Negative instrument check (required): a deliberately trivial flow with a single global
attractor — the instrument must report exactly one attractor with basin fraction 1.
Positive instrument check (added for honesty): a known multistable map (independent of
the contract) where the instrument must report >= 2 basins with nontrivial fractions —
otherwise "one basin everywhere" could be an instrument failure, not a finding.

## Load-bearing requirement

Basin fractions must come from Attractors.jl API calls
(`AttractorsViaRecurrences` / `basins_of_attraction` or equivalent), not hand-rolled
loops. Julia project: `~/.julia/environments/codex-ratchet-attractors-v1.12`
(Attractors v1.37.0, IntervalArithmetic, StaticArrays).

## Pre-registered honesty note

Every stage map here is an affine contraction on the Bloch ball (GKSL flow + CPTP
operator, both affine in the Bloch vector). Composition of affine maps is affine; a
strict affine contraction admits exactly one fixed point, hence one attractor and a
trivial basin (fraction 1). The expected honest outcome is therefore: native and all
controls report one attractor each, distinguished by attractor LOCATION, not basin
fractions. If that holds, the schedule-specificity claim at the basin-structure level
dies, and the record says so; specificity, if any, lives in the fixed-point geometry.
This is pre-registered so a trivial result cannot be dressed up afterward.

## Deliverables

- `attractors_native_schedule.jl` — standalone script, seeded, deterministic, prints
  headline invariants, writes versioned results JSON (never overwrites).
- `results_v1.json` (+ `results_v1_rerun.json` for the determinism check).
- Receipt: basin fractions per schedule, attractor locations, boundary sensitivity
  (perturbed initial conditions near any basin boundary; if single-basin, perturbation
  convergence check instead), control comparison, instrument checks pass/fail.
