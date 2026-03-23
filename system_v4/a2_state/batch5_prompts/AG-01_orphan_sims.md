# AG-01: Integrate 4 Orphan NO_TOKENS SIMs

## Context
CODEX RATCHET ENGINE — 33 SIMs, 99 tokens, 94P/5K. Each SIM should emit EvidenceTokens (JSON to stdout with token_id, sim_spec_id, status, measured_value). The runner (run_all_sims.py) captures these.

## Task
4 SIMs run successfully but emit NO EvidenceTokens:
- `system_v4/probes/navier_stokes_complexity_sim.py`
- `system_v4/probes/dual_weyl_spinor_engine_sim.py`
- `system_v4/probes/rock_falsifier_sim.py`
- `system_v4/probes/scale_testing_sim.py`

Read each, understand what it tests. Add EvidenceToken emission using `foundations_sim.py` as pattern. Run: `python3 system_v4/probes/run_all_sims.py` to verify.
