# AGW3-01 Orbit Failure Anatomy
**Model:** Claude Sonnet
**Return:** returns/AGW3-01_orbit_failure_anatomy__return.md

## Read
- system_v4/probes/a2_state/sim_results/axis0_orbit_phase_alignment_results.json
- system_v4/docs/AXIS0_ATTRACTOR_BASIN_NOTE.md
- system_v4/probes/sim_axis0_orbit_phase_alignment.py

## Context
32-step orbit probe found 31 total failures across 6 configs. Failures concentrate in inner half. Clifford shows Fi failing 4x in inner half despite Fi algebraic lemma proving lr_asym invariance.

## Task
From the JSON "failures" array, extract every record. Report: config, step, op_name, orbit_half, d_ga0, d_ct_mi, lr_asym. Then:
1. Failure count per operator (Ti/Fe/Te/Fi) across all configs
2. Failure count inner vs outer half
3. lr_asym distribution at failing steps (min/max/mean)
4. Sign disagreement pattern: which direction disagrees at each failure?
5. Is there a single shared feature across all 31 failures?

## Anti-smoothing
Report actual numbers. If no shared feature exists, say so.

## Required sections
Failure distribution by operator | Failure distribution by orbit half | lr_asym at failing steps | Sign disagreement pattern | Shared failure feature
