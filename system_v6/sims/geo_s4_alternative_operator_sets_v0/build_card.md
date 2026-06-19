# geo_s4_alternative_operator_sets_v0 Build Card

Ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.
Builder output only. No `audit_verdict.md`; no promotion or admission claim.

Question: under the same committed S4 battery, plus explicit per-channel normalized Choi positivity, are any tested alternative four-operator sets indistinguishable from the committed `D_z,D_x,R_x,R_z` pattern?

Parents:
- `system_v6/sims/geo_s4_operator_stage_v0/results/geo_s4_operator_stage_v0_envelope_results.json`
- `system_v6/sims/geo_s3_s4_mode_sweep_v0/results/geo_s3_s4_mode_sweep_v0_envelope_results.json`
- `system_v6/sims/terrain_exact_mirror_finder_v0/results/terrain_exact_mirror_finder_v0_envelope_results.json`
- `system_v6/receipts/stack_uniqueness_map_20260611.md`

Run:

```bash
SIM_PY=/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
$SIM_PY system_v6/sims/geo_s4_alternative_operator_sets_v0/geo_s4_alternative_operator_sets_v0.py
$SIM_PY system_v6/sims/geo_s4_alternative_operator_sets_v0/validate_geo_s4_alternative_operator_sets_v0.py
$SIM_PY scripts/validate_three_engine_sim_result.py system_v6/sims/geo_s4_alternative_operator_sets_v0/results/geo_s4_alternative_operator_sets_v0_envelope_results.json --require-source-backed
```

Expected builder result: committed anchor reproduces parent byte-exact; alternatives A-D all die under the declared row order; no co-survivor is named among tested alternatives; null model and non-CPTP controls fire.
