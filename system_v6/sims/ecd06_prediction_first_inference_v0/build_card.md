# BUILD CARD - ecd06_prediction_first_inference_v0

Build in `system_v6/sims/ecd06_prediction_first_inference_v0/`. No git add or commit.

## Authority Read First

- `system_v6/receipts/engine_capability_differentiators_20260612.md`, row `ECD.06`, commit hint `7c3f4b48d`.
- `system_v6/receipts/ecd_registry_supplement_1_20260612.md`, commit hint `cba57dbab`, including the two-sided fair-baseline contract and the ECD.05 addendum.
- `system_v6/sims/render_layer_readout_v1/` and `system_v6/sims/render_layer_readout_v1/audit_verdict.md`, commit hint `ce1a91b28`.
- `system_v6/receipts/owner_doctrine_holodeck_render_layer_20260612.md`, updated table: ECD.06 may consume only the two-sided own-readout-family diagnostic from `render_layer_readout_v1`; it must not consume the exact 3-cell set as invariant.
- `system_v6/receipts/audit_standards_codex_v1.md`, including G.2a and the no-identity-leak standard.

## Claim

`ecd06_prediction_first_inference_v0` asks whether the committed render/error/update machinery from `render_layer_readout_v1` achieves lower typed prediction error over committed-dynamics edge trajectories than the strongest fair classical predictor under the same alphabet/observation budget.

Ceiling: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`; no holodeck, FEP, physics, manifold, bridge, Axis-0, or QIT-engine admission.

## Pinned Object

- Carrier: the committed `render_layer_readout_v1` carrier rebuilt through its source path, not by reading its result JSON as the target.
- Trajectory family: all committed carrier edges from the v1 machinery; no exact 3-cell set is used.
- Prediction target: next realized committed carrier coordinate.
- QIT prediction-first side: searched over admissible render gains on the committed source-to-render vector: `0.50`, `0.75`, `1.00`, `1.25`.
- Baseline side: searched classical predictors using no cell identity, coordinate tuple, direct output fingerprint, or equivalent row identifier in fair contenders. Mandatory persistence is reported as an identity-inclusive diagnostic baseline and excluded from the fair winner by the no-identity-leak standard.

## Typed Error And Normalization

For each row and predictor:

- `trace_norm`: `norm(realized - predicted)`.
- `direction_abs`: `abs(dot(realized - predicted, unit(committed_render - source)))`.
- `orthogonal_residual`: the component of prediction error orthogonal to the committed render direction.

The aggregate score is the mean of those three typed components, normalized by packet-local positive scales, plus a diversity penalty:

`adjusted_error = typed_mean_error * (1 + 0.05 * unique_prediction_codes / row_count)`

This penalizes trivially injective readouts on either side while preserving the raw typed error table. The discriminator is the adjusted QIT best minus adjusted fair-classical best. Either outcome is valid.

## Required Controls

- Order-blind collapse.
- Scrambled-error regression using the v1 packet's control family style.
- Dropped-half sensitivity for both sides.
- No identity leak:
  - Definition: a claimed independence or contender row passes the no-identity-leak standard only if the claimed value is not recoverable with majority accuracy `1.0` from cell identity, coordinate tuple, direct output fingerprint, or any equivalent row identifier.
  - Predictors must not condition on cell identity, coordinate tuple, direct output fingerprint, or equivalent row identifier.
  - Required fields: `identity_leak_detected`, `identity_leak_excluded_best_accuracy`, `identity_leak_exclusion_rule`.

## G.2a Boundary

G.2a is binding from birth. The validator and tests must delegate audit-file handling to `scripts/builder_audit_boundary.py`; they must not hard-require permanent absence of `audit_verdict.md`.

## Expected Commands

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd06_prediction_first_inference_v0/ecd06_prediction_first_inference_v0.py
```

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd06_prediction_first_inference_v0/ecd06_prediction_first_inference_v0_jax.py
```

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd06_prediction_first_inference_v0/ecd06_prediction_first_inference_v0_pytorch.py
```

```bash
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/ecd06_prediction_first_inference_v0/ecd06_prediction_first_inference_v0_julia.jl
```

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd06_prediction_first_inference_v0/ecd06_prediction_first_inference_v0_envelope.py
```

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/ecd06_prediction_first_inference_v0/validate_ecd06_prediction_first_inference_v0.py
```

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/ecd06_prediction_first_inference_v0/tests
```
