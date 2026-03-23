# PRO-03: Complexity Gap P-NP Scaling

## Context
CODEX RATCHET ENGINE — QIT framework. Density matrices (ρ) + 4 CPTP operators: Ti (projection), Te (Hamiltonian), Fi (filtering), Fe (Lindblad). Axioms: F01 (finite d), N01 (AB≠BA). LIVE: 99 tokens, 94P/5K. BANNED: "Win/Lose" use SG/EE.

## Required Reads
- `system_v4/probes/complexity_gap_sim.py`
- `system_v4/probes/proof_cost_sim.py` (Landauer costs)
- `system_v4/probes/p_vs_np_sim.py`

## Problem
1 KILL: S_SIM_BASIN_DEPTH_V1, reason NO_CORRELATION. The SIM tests whether P-NP gap scales with dimension d, but finds no correlation.

## Fix Direction
Use Landauer's principle. Each Ti projection costs kT·ln(2) entropy per bit erasure.
- "P" operations: Stay within basin → cost O(d)
- "NP" operations: Cross basin boundary → cost O(d·ln(d)) due to Lindblad depth
- The gap should grow logarithmically, not linearly

## Required Output
Save to `system_v4/probes/`:
- `complexity_gap_v2_sim.py`
- `COMPLEXITY_GAP_FIX_NOTES.md`
- Run it and include results
