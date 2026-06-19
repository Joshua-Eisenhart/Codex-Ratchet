# Build Card - ecd06_prediction_first_inference_v2

Build in `system_v6/sims/ecd06_prediction_first_inference_v2/`. No git add or commit.

## Bottom Line

Build the ECD.06 v2 equal-information test. The question is now well posed: does a prediction-error-correction loop structure beat equally informed one-shot predictors on this carrier?

Either outcome is the result. If the loop loses or ties, the registry row is a clean death: the loop structure adds nothing under equal information on this carrier.

Ceiling: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`.

## Read-First Authority

- `system_v6/sims/ecd06_prediction_first_inference_v1/audit_verdict.md` at `0a7949d35`: v1 killed because QIT consumed the held-out row's committed render vector, and a classical render-access equalizer tied QIT at `0.344150808264`.
- `system_v6/receipts/ecd_registry_supplement_1_20260612.md`, Addendum 3: ECD.06 v2 must enforce the EQUAL-INFORMATION contract.
- `system_v6/sims/ecd06_prediction_first_inference_v1/ecd06_prediction_first_inference_v1_common.py`: reuse the honest regime gate by hash.
- `system_v6/receipts/audit_standards_codex_v1.md`: G.2a binds from birth.

## Binding Contract

1. Equal information:
   - both sides receive the same pinned training inputs;
   - both sides receive the same held-out prediction inputs;
   - neither side may read held-out `render`, committed generator/render specs, held-out targets, `dst`, row-id target lookup, or direct prediction codes before prediction.
2. QIT loop structure only:
   - keep render/error/update as an architecture;
   - fit the render proposal and residual correction from the same training budget the baselines get;
   - prediction uses only `src`, `source`, generator label, and generator family.
3. Baseline class:
   - persistence;
   - global empirical mean;
   - per-state conditional table;
   - source+generator transition table, including the v0 killer;
   - searched learned policies from v1.
   - verdict compares QIT against the strongest heldout-scored fixed baseline in this class; the v1 train-selected table row remains reported separately.
4. Witness gates before discriminator rows:
   - v1 regime gate: `regime_pin_passed_table_not_exactly_learnable`;
   - v2 information-parity gate: `information_parity_passed`.
5. Controls:
   - v1 render-access regression: grant forbidden held-out render access back and reproduce the `0.344150808264` equalizer tie;
   - full-observability regression: source+generator table wins at adjusted error `0.0`;
   - scrambled-error margin movement;
   - dropped-half budgets for both sides;
   - no identity leak.

## Files

- `ecd06_prediction_first_inference_v2_common.py`: regime gate, equal-information gate, learned QIT loop, baselines, controls, and result object.
- `ecd06_prediction_first_inference_v2_boundary.py`: packet-local G.2a, regime, and parity boundary helper.
- `ecd06_prediction_first_inference_v2.py`: base result writer.
- `ecd06_prediction_first_inference_v2_jax.py`: JAX/tool lane.
- `ecd06_prediction_first_inference_v2_pytorch.py`: PyTorch/tool lane.
- `ecd06_prediction_first_inference_v2_julia.jl`: Julia strict-carrier lane.
- `ecd06_prediction_first_inference_v2_envelope.py`: three-engine envelope builder.
- `validate_ecd06_prediction_first_inference_v2.py`: packet validator.
- `tests/test_ecd06_prediction_first_inference_v2.py`: regression tests.

## Standard Gates

- G.2a from birth: validator and boundary helper call `builder_audit_boundary_errors(...)`; builder output may not contain a builder-authored audit verdict.
- Three-engine where scoped: `all_three_full_sims` envelope with Julia/JAX/PyTorch lanes, still capped at `scratch_diagnostic`.
- Same adjusted-error normalization as v1: mean normalized `trace_norm`, `direction_abs`, and `orthogonal_residual`, plus the same diversity penalty.

## Commands

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd06_prediction_first_inference_v2/ecd06_prediction_first_inference_v2.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd06_prediction_first_inference_v2/ecd06_prediction_first_inference_v2_jax.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd06_prediction_first_inference_v2/ecd06_prediction_first_inference_v2_pytorch.py
```

```bash
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/ecd06_prediction_first_inference_v2/ecd06_prediction_first_inference_v2_julia.jl
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd06_prediction_first_inference_v2/ecd06_prediction_first_inference_v2_envelope.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd06_prediction_first_inference_v2/validate_ecd06_prediction_first_inference_v2.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest system_v6/sims/ecd06_prediction_first_inference_v2/tests/test_ecd06_prediction_first_inference_v2.py
```
