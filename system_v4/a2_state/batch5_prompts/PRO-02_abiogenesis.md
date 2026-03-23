# PRO-02: Abiogenesis Dual-Loop Fix

## Context
CODEX RATCHET ENGINE — QIT framework. Density matrices (ρ) + 4 CPTP operators: Ti (projection), Te (Hamiltonian), Fi (filtering), Fe (Lindblad). 8-stage engine. LIVE: 99 tokens, 94P/5K. BANNED: "Win/Lose" use SG/EE.

## Required Reads
- `system_v4/probes/abiogenesis_sim.py`
- `system_v4/probes/foundations_sim.py` (operator implementations)
- `system_v4/skills/intent-compiler/dna.yaml` (axioms + operators)

## Problem
1 KILL: S_SIM_ABIOGENESIS_V1, reason NO_SPONTANEOUS_LIFE. Starts from I/d (maximally mixed), applies random CPTP perturbations, structure never emerges.

## Fix Direction
The dual-loop mechanism is the key:
- Random SINGLE operators → thermal death (correct! this should NOT produce life)
- But the DUAL LOOP (alternating Ti→Fe→Te→Fi ratchet cycle) should SOMETIMES find the attractor
- The ratchet provides directed structure that random ops cannot

Test BOTH:
1. Random single operators → must NEVER produce structure (confirm current behavior)
2. Dual-loop operator cycle → should SOMETIMES produce structure (the fix)

## Required Output
Save to `system_v4/probes/`:
- `abiogenesis_v2_sim.py`
- `ABIOGENESIS_FIX_NOTES.md`
- Run it and include results
