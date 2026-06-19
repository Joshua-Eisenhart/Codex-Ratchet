# Independent audit verdict - ecd06_prediction_first_inference_v1

Audit mode: read-only audit with independent source recomputation; live repo write scope was this file only.
Freshness tier: TIER-3 by `audit_standards_codex_v1` because the prompt supplied builder claims, v0 death language, and the exact audit teeth. Central rows below were recomputed from source in this audit.
Auditor: independent cross-backend auditor.

## Bottom Line

VERDICT: BY_CONSTRUCTION / model-access-gap. The v1 `SURVIVES_v1` row does not survive as an engine-capability discriminator.

The headline arithmetic recomputes: primary regime gate passes with `66/198 = 0.333333333333` source+generator cells observed, heldout eval pair coverage `0.0`, collision rate `0.0`; QIT adjusted error is `0.344150808264`; the validator-selected widened baseline is the train-budget-limited source+generator table at `1.210737013737`; margin is `-0.866586205473`.

But the decisive tooth kills the survival: the QIT predictor consumes the heldout row's committed `render` vector at prediction time. That vector is the committed one-step image before quantization from the upstream render carrier. The widened baselines are trained from the pinned training budget and do not receive the same row-local committed render/model surface. A render-access classical control that predicts with the same row-local `render` vector ties QIT exactly at `0.344150808264`. So the positive row is "a predictor with the true committed render model beats budget-limited predictors without it," not an earned QIT prediction-first capability.

Accepted ceiling: `scratch_diagnostic` model-access-gap finding only; `promotion_allowed=false`; `formal_admission_allowed=false`; no QIT-engine, holodeck/FEP, physics, Axis-0, bridge, manifold, or canonical-by-process claim.

## Decisive Tooth: Model Access

FAIL. The ECD06 row builder imports `render_layer_readout_v1_common`, calls `anchor_object()`, obtains all `committed_edge_rows(...)`, and stores for each ECD06 row:

- `source`;
- `render`;
- `realized`;
- `committed_direction`;
- source/destination/generator metadata.

The upstream render source defines `render` as `edge["image_before_quantization"]` and labels it `committed_one_step_image_before_quantization`. That is not a learned training-budget estimate inside ECD06; it is committed carrier dynamics.

The later, active ECD06 partial-observability `qit_side()` predicts each heldout row as:

```text
source + gain * (render - source)
```

The winning QIT policy is `qit_prediction_first_render_gain_1.00`, so its prediction is exactly the row-local committed `render` vector. The baselines never get an equivalent row-local committed render feature or generator spec. Equal-access control:

```json
{
  "policy_id": "model_access_control_row_local_render_vector",
  "train_adjusted_error": 0.405641904221,
  "adjusted_error": 0.344150808264,
  "unique_prediction_codes": 127
}
```

That ties the QIT winner exactly. This is a model-access asymmetry, not a fair discriminator.

## Recomputed Headline Rows

Fresh recompute from `ecd06_prediction_first_inference_v1_common.py`:

```json
{
  "rows": 198,
  "train": 66,
  "eval": 132,
  "total_source_generator_cells": 198,
  "observed_source_generator_cells": 66,
  "transition_table_fill_fraction": 0.333333333333,
  "eval_pair_coverage_fraction": 0.0,
  "collision_pair_count": 0,
  "collision_rate": 0.0,
  "qit_best_adjusted_error": 0.344150808264,
  "baseline_selected_adjusted_error": 1.210737013737,
  "margin": -0.866586205473
}
```

The committed result JSON matches the source recompute on these fields, and `validate_payload(...)` returned `errors=[]` without writing repo receipts.

## Baseline Table

Full widened-baseline table, adjusted error on the heldout eval rows:

| Policy | Train adjusted error | Eval adjusted error |
|---|---:|---:|
| `persistence_source_state` | 0.862207446533 | 0.608433222810 |
| `global_empirical_one_step_mean` | 1.692746890979 | 1.630873038765 |
| `per_state_conditional_table_train_budget` | 0.692576593064 | 1.202705865674 |
| `source_generator_transition_table_v0_killer_included_train_budget` | 0.000000000000 | 1.210737013737 |
| `searched_policy_class_generator_mean` | 1.655980133072 | 1.693231057393 |
| `searched_policy_class_generator_family_mean` | 1.672226788116 | 1.693917271420 |
| `searched_policy_class_source_plus_generator_delta` | 0.915271198075 | 0.755326811849 |
| `searched_policy_class_table_delta_blend_0.25` | 0.688942352180 | 0.770106266328 |
| `searched_policy_class_table_delta_blend_0.50` | 0.459294901507 | 0.885428940688 |
| `searched_policy_class_table_delta_blend_0.75` | 0.229647450802 | 1.059361687136 |

Nuance: the packet's binding selection rule picks the minimum training adjusted error, so the v0-killer table is selected and then scores `1.210737013737` on eval. If choosing adversarially by heldout eval error, persistence is the best listed baseline at `0.608433222810`. Neither listed baseline beats QIT's `0.344150808264`, but that does not rescue the row because the render-access equalizer ties QIT.

The source+generator table's heldout fallback is real: eval pair coverage is `0.0`, so it has no exact pair hits. Its eval fallback counts are `state_backoff=120`, `generator_backoff=12`, `global_backoff=0`.

## QIT Table

QIT gain search:

| Policy | Train adjusted error | Eval adjusted error |
|---|---:|---:|
| `qit_prediction_first_render_gain_0.50` | 0.633964357992 | 0.480428262046 |
| `qit_prediction_first_render_gain_0.75` | 0.515259053795 | 0.409040392211 |
| `qit_prediction_first_render_gain_1.00` | 0.405641904221 | 0.344150808264 |
| `qit_prediction_first_render_gain_1.25` | 0.535226930633 | 0.459880655984 |

This search is internally consistent. The issue is not arithmetic drift; it is that every heldout QIT prediction is allowed to read the row-local `render` field.

## Controls

PASS for arithmetic and regression intent:

- Full-observability v0 regression: source+generator table adjusted error `0.0`; v0 kill preserved.
- Scrambled-error control: margin moves from `-0.866586205473` to `0.065676200831`.
- Dropped-half budget sensitivity: both directions still report QIT-lower-error rows, with margins `-1.367802038763` and `-1.200304769287`.
- G.2a builder/audit boundary: source wires `builder_audit_boundary_errors(...)`; pre-verdict `validate_payload(...)` returned `errors=[]`.

Partial / caveated:

- No direct target identity leak found: direct eval target lookup is forbidden, and the packet excludes heldout label-table entries, destination, realized coordinate, row-id target lookup, and direct prediction code.
- Standards field gap: the v1 no-identity-leak row emits `identity_leak_detected=false` and an exclusion rule, but not `identity_leak_excluded_best_accuracy`. This is not the decisive kill, but future packets should emit the full audit-standards field set.
- Three-engine caveat: the envelope says `all_three_full_sims`, but the Julia lane is a structural/package guard, not an independent recomputation of the Python prediction table. The kill above is source-semantic and does not depend on this caveat.

## Registry Language

Use this registry row:

`ECD.06 prediction-first inference v1: BY_CONSTRUCTION/model-access-gap. Under the primary partial-observability pin, QIT render-gain prediction scores adjusted error 0.344150808264 against budget-limited widened baselines (validator-selected source+generator table 1.210737013737; adversarial heldout-best listed baseline persistence 0.608433222810). But QIT consumes row-local committed render vectors from the true one-step render carrier at heldout prediction time; a baseline granted the same render access ties QIT at 0.344150808264. Not an engine capability result; scratch_diagnostic only; promotion_allowed=false.`

v2 contract:

`Both sides get the same information. Either grant classical baselines the committed generator/render spec and compare strongest-form predictors under that access, or require the QIT prediction machinery to learn from the same pinned training/observed structure without row-local committed render access on heldout rows.`

## Checks Run

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
# Imported ecd06_prediction_first_inference_v1_common; recomputed rows, primary budget gate,
# qit_side, baseline_side, winner, controls, baseline fallback counts, and render-access equalizer.
PY
```

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
# Loaded committed result JSON; rebuilt source object; compared headline fields;
# ran validate_ecd06_prediction_first_inference_v1.validate_payload(payload), result errors=[].
PY
```

Not run live in-place: builder scripts, envelope writer, validator main, and pytest, because those commands can rewrite repo result/cache receipts and the audit authorization allowed live repo writes only to this verdict file.
