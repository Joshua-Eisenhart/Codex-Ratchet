# Independent audit verdict - ecd06_prediction_first_inference_v0

Audit mode: read-only cross-backend audit with independent recomputation from source; live repo write scope was this file only.
Freshness tier: TIER-3 by `audit_standards_codex_v1`, because the prompt supplied builder claims and verdict pressure. Central numeric rows below were recomputed from source in this audit.
Auditor: independent cross-backend auditor.

## Bottom Line

VERDICT: BY_CONSTRUCTION / SURVIVAL CLAIM REJECTED AS STATED.

The packet mechanically computes the reported QIT-vs-implemented-baseline margin correctly, and the adjusted-error normalization is applied identically to the implemented QIT and baseline candidates. But the implemented fair baseline class is too weak for the advertised claim against "the strongest classical baseline": it does not include a per-cell/per-state one-step conditional transition table. The reported fair winner is `global_empirical_one_step_mean`, an order-blind mean-field predictor, with adjusted error `1.573328909229`.

Auditor recompute of the missing source-plus-generator empirical transition table gives adjusted error `0.0` in-sample on the committed edge table. That is stronger than the QIT best `qit_prediction_first_render_gain_1.00` at adjusted error `0.35108241978`. Because the result depends on excluding this stronger classical table while still calling the comparison "strongest classical," the v0 survival does not survive audit.

Accepted ceiling: current artifacts show only a narrowed, no-state/identity-excluded baseline-class diagnostic: QIT beats the implemented global/generator aggregate baselines under the pinned metric. They do not establish `SURVIVES_v0` against a strongest-form classical one-step predictor. `promotion_allowed=false`; `formal_admission_allowed=false`; no QIT-engine, holodeck, FEP, Axis-0, bridge, manifold, physics, canonical, or stable 3-cell claim.

Registry row language:

`ECD.06 prediction-first inference: BY_CONSTRUCTION / NOT ADJUDICATED AS SURVIVAL. Current packet beats only the implemented no-state aggregate baseline class on the committed render_layer_readout_v1 edge table under the pinned adjusted typed-error metric. Survival against strongest-form classical one-step predictors is open and requires v1 fair-baseline widening.`

## Baseline Strength

Implemented baseline candidates in `ecd06_prediction_first_inference_v0_common.py:386-441`:

| policy | fair eligible | adjusted error | audit note |
|---|---:|---:|---|
| `mandatory_persistence_identity_inclusive_diagnostic` | false | `0.654843995788` | source-coordinate baseline, excluded from fair winner |
| `global_empirical_one_step_mean` | true | `1.573328909229` | reported fair winner; mean-field/order-blind |
| `empirical_one_step_frequency_table_by_generator_leave_one_out` | true | `1.654019431039` | generator-only LOO aggregate |
| `searched_policy_class_generator_family_mean` | true | `1.573328909229` | collapses to the same global/family mean here |

Missing from the fair class: a per-cell/per-state empirical one-step conditional table. Recomputed auditor baselines from `build_rows()` over all 198 committed edges:

| auditor recompute | adjusted error | note |
|---|---:|---|
| `src_generator_mean_in_sample` | `0.0` | exact source-plus-generator transition table; kills survival as a strongest-baseline claim |
| `src_mean_in_sample` | `0.788257079197` | source-conditioned aggregate, still stronger than reported fair baseline but weaker than QIT |
| `src_mean_LOO` | `0.965570504825` | source-conditioned LOO aggregate |
| `src_generator_family_mean_in_sample` | `0.134934989265` | source-plus-family table; also beats QIT |
| `src_generator_family_mean_LOO` | `1.331689620421` | stronger than reported fair baseline, still weaker than QIT |

The zero-error source-plus-generator row is not mysterious: the row table has 33 source cells and 6 generators, yielding one committed edge per `(src, generator)` pair. A classical transition table that learns that row family predicts the realized next coordinate exactly.

This table conditions on source identity and therefore violates the packet's current no-identity fair-candidate rule. That exclusion is acceptable only if the claim is explicitly narrowed to "identity/state-excluded aggregate baselines." It is not acceptable for a headline "strongest classical baseline" survival, especially under the ECD supplement's two-sided doctrine after the prior v0 deaths.

## Training And Observation Budget

QIT side uses row-local source and committed render vector for every row: `source + gain * (render - source)`, searched over gains `0.50`, `0.75`, `1.00`, `1.25` (`ecd06_prediction_first_inference_v0_common.py:360-383`).

The implemented fair baseline side receives only global, generator, or generator-family aggregate information, while source-conditioned predictors are excluded from the fair winner. That is not a same-budget comparison against the strongest classical one-step learner over the same committed trajectories.

The v1 repair must make the budget explicit:

- if cell/source identity is banned, rename the claim to a no-state/no-identity aggregate-baseline diagnostic and do not call it strongest classical;
- if the claim remains strongest-form classical, include at minimum `classical_transition_table_by_source_and_generator` as a named baseline;
- include both an in-sample full-table diagnostic and a predeclared holdout/leave-family variant where the training budget is comparable and not self-target leakage;
- report whether each stronger table is excluded by G.2a, eligible for the survival comparison, or only a diagnostic death check.

## Adjusted-Error Normalization

I recomputed the builder numbers from source and found no ECD.05-style asymmetric normalization bug in the implemented comparison.

Formula in source and build card:

`adjusted_error = mean(normalized trace_norm, direction_abs, orthogonal_residual) * (1 + 0.05 * unique_prediction_codes / row_count)`

The same `metric_scales(rows)` object is passed to `qit_side(rows, scales)` and `baseline_side(rows, scales)` in `build_prediction_first_object()` (`ecd06_prediction_first_inference_v0_common.py:584-589`). Recomputed scales:

```json
{
  "trace_norm": 0.3610521680605239,
  "direction_abs": 0.36105216806052404,
  "orthogonal_residual": 0.28931735613094767
}
```

Recomputed headline values:

```json
{
  "qit_best_policy_id": "qit_prediction_first_render_gain_1.00",
  "qit_best_adjusted_error": 0.35108241978,
  "reported_fair_baseline_policy_id": "global_empirical_one_step_mean",
  "reported_fair_baseline_adjusted_error": 1.573328909229,
  "reported_margin": -1.222246489449,
  "missing_transition_table_adjusted_error": 0.0
}
```

The normalization is not the death. The weak baseline class is.

## QIT Side

QIT side is searched, not single-config: four admissible gains are evaluated. The best is `gain_1.00`. This satisfies the two-sided doctrine on the QIT side for the packet's stated gain family, but the scope remains the pinned gain family only.

This search does not rescue the survival because the classical side lacks the stronger transition-table baseline.

## Scrambled Flip

I recomputed the scrambled-error regression from source. It flips to a baseline win:

```json
{
  "scrambled_qit_best_adjusted_error": 0.434440678208,
  "scrambled_baseline_best_fair_adjusted_error": 0.322635993741,
  "scrambled_margin": 0.111804684467,
  "scrambled_winner": "baseline"
}
```

This is a meaningful control for the implemented comparison. It does not answer the missing-baseline problem.

## Identity Leak And G.2a

No-identity leak as implemented passes its emitted standard fields:

```json
{
  "identity_leak_detected": false,
  "identity_inclusive_best_accuracy": 0.212121212121,
  "identity_leak_excluded_best_accuracy": 0.782828282828,
  "excluded_fields": ["src", "dst", "source_coord", "realized_coord", "row_id", "direct_prediction_code"]
}
```

But this control is aimed at recovering `v1_error_label`, not at adjudicating whether a classical next-state transition table is a fair strongest-form predictor. The exact table that kills the survival conditions on source identity plus generator; under the packet's current rule it is excluded, but under the survival headline it is the missing stronger classical baseline.

G.2a passes. The validator delegates audit-file handling through `builder_audit_boundary_errors(...)` (`validate_ecd06_prediction_first_inference_v0.py:15-17,111-113`), and the build card states the from-birth G.2a boundary (`build_card.md:51-53`). I found no builder-authored audit verdict.

## Other Scope Checks

- No stable 3-cell invariant is consumed: the result pins all 198 committed render v1 carrier edges and reports `uses_exact_3_cell_set_invariant=false`.
- Three-engine envelope strict green is builder-side/mechanical only. It verifies lane consistency and result shape, not strongest-baseline adequacy.
- Solver rows bind the reported adjusted-error winner relation, but only for the implemented baseline winner. They do not prove the missing baseline cannot win.

## Required v1 Repair Card

Build `ecd06_prediction_first_inference_v1` only after pinning the baseline class before execution:

1. Add named baseline `classical_transition_table_by_source_and_generator`.
2. Add source-conditioned aggregate variants: `source_mean`, `source_generator_family_mean`, and their leave-one-out or holdout versions.
3. State for each source-conditioned baseline whether it is fair-eligible, identity-excluded, or diagnostic-only under G.2a.
4. If source identity is excluded, make the claim text say "no-state identity-excluded aggregate baselines," not "strongest classical baseline."
5. If source identity is allowed for a strongest-form classical baseline, survival must beat the source-plus-generator transition table or die.
6. Keep the same adjusted-error normalization and scrambled flip, but report them after the widened baseline winner is chosen.

## Commands And Checks

Read-only checks run:

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
# imported ecd06_prediction_first_inference_v0_common;
# ran build_rows(), metric_scales(), build_prediction_first_object();
# recomputed implemented QIT/baseline values, scrambled regression, and auditor transition-table baselines
PY
```

```bash
rg --files system_v6/sims/ecd06_prediction_first_inference_v0 system_v6/receipts
rg -n "G\\.2a|two-sided|baseline|adjusted|identity|scrambled|conditional|per-state|SURVIVES|BY_CONSTRUCTION" system_v6/receipts system_v6/sims/ecd06_prediction_first_inference_v0
```

Not run live in-place: packet builders, full validator, and pytest as command-line scripts, because those commands rewrite repo result receipts and this audit authorization allowed live repo writes only to `audit_verdict.md`. The validator and tests were inspected; source-level recomputation was run without writing repo result files.

## Citation Rule

Cite this audit only as:

`ECD.06 v0 survival rejected as stated: BY_CONSTRUCTION / baseline-gap. The implemented metric arithmetic is reproducible and shared across sides, QIT beats the implemented no-state aggregate fair baselines, and scrambled control flips; however the fair baseline class omits the source-plus-generator empirical transition table, which has adjusted error 0.0 on the committed edge table. No promotion/admission; v1 must widen or explicitly narrow the baseline claim.`

