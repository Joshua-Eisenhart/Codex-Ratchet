# geo_s3_s4_mode_sweep_v0 build card

Status: builder packet only. No `audit_verdict.md` is emitted.

Ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

Scope:
- Extend the committed `geo_s2_s5_mode_sweep_v0` closed-caveat machinery to S3 density/observable and S4 operator stages.
- Read committed `geo_s3_density_observable_v0` and `geo_s4_operator_stage_v0` read-only and hash-bind them in `parent_lineage`.
- Execute only `RESTRICTED` and `QUOTIENTED` modes. `RATCHETED` remains out of scope.
- Use the honest mode label `julia_canon_plus_jax_diagnostic`; PyTorch is omitted because no graph/network/autograd claim path is scoped.

Computed rows:
- S3 RESTRICTED: fixed-purity shell `|r|=1/2`, finite grid narrowing `27 -> 6` with `21` excluded, Born range narrowed to `[1/4, 3/4]`, trace-distance/fidelity changes, and CPTP contraction on shell inputs.
- S3 QUOTIENTED: further z-axis probe coarsening over the native density quotient; equivalence classes are computed, z-observables descend, x/y observables do not.
- S4 RESTRICTED: each of `D_z`, `D_x`, `R_x`, and `R_z` is tested on the fixed-purity shell; rotations preserve, dephasings leak generic transverse shell points.
- S4 QUOTIENTED: each operator is tested for well-definedness on the z-probe quotient; `D_z`, `D_x`, and `R_z` descend, `R_x` is excluded there.
- ORDER ROWS: two explicit pipelines per stage. S3 gap is `0`; S4 gap is `2`.

Controls:
- Nothing-excluded controls are byte-exact for parent S3/S4 rows.
- Everything-excluded controls are honest empty rows.
- Per-operator controls can fail and do fail for generic dephasing shell preservation.
- z3/cvc5 both bind raw S3 finite-grid counts and include an erased-exclusion flip.
- Julia Symbolics/Z3 mirrors the z-probe descent and same-class controls.

Validation commands:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_s3_s4_mode_sweep_v0/geo_s3_s4_mode_sweep_v0.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_s3_s4_mode_sweep_v0/validate_geo_s3_s4_mode_sweep_v0.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --strict-source-backed system_v6/sims/geo_s3_s4_mode_sweep_v0/results/geo_s3_s4_mode_sweep_v0_envelope_results.json
```
