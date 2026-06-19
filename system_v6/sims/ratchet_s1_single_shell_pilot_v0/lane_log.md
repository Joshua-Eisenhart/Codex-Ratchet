# ratchet_s1_single_shell_pilot_v0 lane log

## 2026-06-11 builder-fix

- Re-emitted the envelope through the packet builder under `schema_version: three_engine_sim_result_v1`.
- Kept `mode` as a field and set `engine_contract.mode: RATCHETED`.
- Declared scoped `julia` and `jax` lanes, with `pytorch` omitted because this single-shell pilot has no graph/network/autograd claim path.
- Preserved the generated exact row subtrees; this was an envelope-shape repair, not a recompute of the math rows.
- Kept the packet validator result as supplementary output; the binding repo validator is `scripts/validate_three_engine_sim_result.py`.
