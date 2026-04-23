# PRO-10: Alignment Formal SIM

## Context
CODEX RATCHET ENGINE — QIT framework. 8-stage dual-loop engine.

## Required Reads
- `system_v4/probes/alignment_sim.py` (currently 2 PASS, basic)

## Task
Upgrade SUGGESTIVE→STRUCTURAL requires: "Mathematical Solvency Operator proving E(ρ*)=ρ* under shocks." Build:
1. Define solvency S(ρ) = ability to maintain structure under perturbation
2. Apply random environmental shocks
3. Show aligned system (dual-loop) maintains E(ρ*)≈ρ*
4. Show misaligned (single-loop) degrades

## Required Output
Save to `system_v4/probes/`:
- `alignment_formal_sim.py`
- `ALIGNMENT_FORMAL_NOTES.md`
- Run it and include results
