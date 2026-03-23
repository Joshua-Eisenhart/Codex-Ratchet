# PRO-07: Type-2 Divergent Engine

## Context
CODEX RATCHET ENGINE — QIT framework. Type-1 (FeTi outer, γ-dominant, convergent) + Type-2 (TeFi outer, ω-dominant, divergent). 720° spinor.

## Required Reads
- `system_v4/probes/type2_engine_sim.py`

## Task
Type-2 is ω-dominant (underdamped, divergent). It explores phase space. NLM-16 says Type-2 should be intentionally underdamped (γ<2ω). Current SIM is basic. Build full parameterized Type-2 with: phase space exploration metrics, comparison to Type-1 convergence rate, verify spinor 720° property.

## Required Output
Save to `system_v4/probes/`:
- `type2_engine_v2_sim.py`
- `TYPE2_ENGINE_NOTES.md`
- Run it and include results
