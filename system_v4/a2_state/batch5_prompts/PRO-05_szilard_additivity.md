# PRO-05: Szilard 64-Stage Additivity Fix

## Context
CODEX RATCHET ENGINE — QIT framework. Density matrices (ρ) + 4 CPTP operators. 8-stage engine, Type-1 (FeTi outer) + Type-2 (TeFi outer) = 64 total microstates. LIVE: 99 tokens, 94P/5K.

## Required Reads
- `system_v4/probes/szilard_64stage_sim.py`
- `system_v4/probes/full_8stage_engine_sim.py`

## Problem
1 KILL: S_SIM_DUAL_SZILARD_V1, reason ADDITIVE. Entropy changes across 64-stage dual-stacked cycle are not additive. The Szilard engine is Engine A output = Engine B input. Fe dissipation between A→B is not conservative, or partial trace at handoff loses entropy. Related to γ calibration — both about the same γ ratio issue.

## Required Output
Save to `system_v4/probes/`:
- `szilard_64stage_v2_sim.py`
- `SZILARD_FIX_NOTES.md`
- Run it and include results
