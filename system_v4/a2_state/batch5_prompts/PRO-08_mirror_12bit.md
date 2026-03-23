# PRO-08: 12-Bit Mirror Mapping

## Context
CODEX RATCHET ENGINE — QIT framework. The engine uses a 6-bit control surface (bits 1-6) for operator selection at each stage.

## Task
NLM-15 flagged 12-Bit Mirror (bits 7-12) as "enormous inferential leap, never simulated." Bits 1-6 = control surface. Bits 7-12 should be the MIRROR — same algebraic structure, different thermodynamic domain, related via conjugation/reflection. BUILD: SIM that constructs 12-bit address space and tests whether bits 7-12 genuinely mirror bits 1-6 structure. Test: is the mirror forced by F01+N01 or is it another CHOSEN structure?

## Required Output
Save to `system_v4/probes/`:
- `mirror_12bit_sim.py`
- `MIRROR_12BIT_NOTES.md`
- Run it and include results
