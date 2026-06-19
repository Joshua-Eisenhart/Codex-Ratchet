# Build Card — ecd06_prediction_first_inference_v1

## Bottom Line

Build the ECD.06 v1 regime repair after the v0 baseline-gap rejection. The v1 packet must first prove the pinned partial-observability budget makes the source+generator transition table not exactly learnable. Only then may it compare the render/error/update prediction loop against the widened baseline class.

Ceiling: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`.

## Read-First Authority

- `system_v6/sims/ecd06_prediction_first_inference_v0/audit_verdict.md` at `d0609c9bf`: v0 rejected because the source+generator transition table has adjusted error `0.0` under full observability.
- `system_v6/receipts/ecd_registry_supplement_1_20260612.md`, Addendum 2: v1 must widen baselines and narrow the regime.
- `system_v6/sims/render_layer_readout_v1/*` at `ce1a91b28`: render v1 machinery is diagnostic input only.

## Binding Contract

1. Widen the baseline class:
   - persistence;
   - global empirical mean;
   - per-state conditional table;
   - source+generator transition table, including the v0 killer;
   - searched budget-learned policy class.
2. Narrow the regime:
   - primary pin: `primary_hash_balanced_train66_eval132`, a deterministic 66-row training budget over the 198 source+generator cells;
   - sensitivity variant: canonical dropped-half budgets, `99/99` each direction;
   - the source+generator table must report fill fraction, heldout coverage, and collision rate before any discriminator rows.
3. Witness gate:
   - if the table is exactly learnable, emit `regime_pin_failed_table_learnable` and stop;
   - discriminator rows are valid only after `regime_pin_passed_table_not_exactly_learnable`.
4. Controls:
   - full-observability v0 regression: source+generator table wins at adjusted error `0.0`;
   - scrambled-error margin movement;
   - dropped-half data-budget sensitivity on both sides;
   - no target identity leak.

## Files

- `ecd06_prediction_first_inference_v1_common.py`: core budget gate, widened baselines, controls, and result object.
- `ecd06_prediction_first_inference_v1_boundary.py`: packet-local G.2a and regime boundary helper.
- `ecd06_prediction_first_inference_v1.py`: base result writer.
- `ecd06_prediction_first_inference_v1_jax.py`: JAX/tool lane.
- `ecd06_prediction_first_inference_v1_pytorch.py`: PyTorch/tool lane.
- `ecd06_prediction_first_inference_v1_julia.jl`: Julia strict-carrier lane.
- `ecd06_prediction_first_inference_v1_envelope.py`: three-engine envelope builder.
- `validate_ecd06_prediction_first_inference_v1.py`: packet validator.
- `tests/test_ecd06_prediction_first_inference_v1.py`: regression tests.

## Standard Gates

- G.2a from birth: validator and boundary helper call `builder_audit_boundary_errors(...)`; builder output may not contain a builder-authored audit verdict.
- Three-engine where scoped: `all_three_full_sims` envelope with Julia/JAX/PyTorch lanes, still capped at `scratch_diagnostic`.
- Same adjusted-error normalization as v0: mean normalized `trace_norm`, `direction_abs`, and `orthogonal_residual`, plus the same diversity penalty.

## Commands

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd06_prediction_first_inference_v1/ecd06_prediction_first_inference_v1.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd06_prediction_first_inference_v1/ecd06_prediction_first_inference_v1_jax.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd06_prediction_first_inference_v1/ecd06_prediction_first_inference_v1_pytorch.py
```

```bash
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/ecd06_prediction_first_inference_v1/ecd06_prediction_first_inference_v1_julia.jl
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd06_prediction_first_inference_v1/ecd06_prediction_first_inference_v1_envelope.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd06_prediction_first_inference_v1/validate_ecd06_prediction_first_inference_v1.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest system_v6/sims/ecd06_prediction_first_inference_v1/tests/test_ecd06_prediction_first_inference_v1.py
```
