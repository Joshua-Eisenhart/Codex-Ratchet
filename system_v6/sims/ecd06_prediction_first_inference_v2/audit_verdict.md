# Independent audit verdict - ecd06_prediction_first_inference_v2

Audit mode: read-only audit with independent source recomputation; live repo write scope was this file only.
Freshness tier: TIER-3 by `audit_standards_codex_v1` because the prompt supplied builder claims and exact audit teeth. Central rows below were recomputed from source in this audit.
Auditor: independent cross-backend auditor.

## Bottom Line

VERDICT: `DIES_v2` accepted, with a generated-artifact freshness caveat.

The line closes on this carrier. ECD.06 v0 died as a baseline/regime gap, v1 died as a model-access gap, and v2 dies under equal information: prediction-first inference is not an engine capability on the committed render-layer v1 edge carrier under this pinned budget. Every apparent advantage traced to information asymmetry; when both sides get the same training and prediction inputs, the learned render/error/update loop structure subtracts overhead without benefit.

Headline source recompute:

```json
{
  "qit_best_policy_id": "qit_learned_loop_source_state_gain_0.50_correction_1.00",
  "qit_best_adjusted_error": 1.081028410929,
  "baseline_best_fair_policy_id": "persistence_source_state",
  "baseline_best_fair_adjusted_error": 0.608433222810,
  "qit_minus_baseline_adjusted_error_margin": 0.472595188119,
  "verdict": "DIES_v2"
}
```

Stronger audit tooth: the headline QIT row is train-selected. Even if I neutralize that selection asymmetry in QIT's favor and grant QIT the heldout-best learned-loop candidate, the best QIT eval row is `qit_learned_loop_generator_family_gain_0.50_correction_0.00` at `0.671719983517`, still worse than persistence by `0.063286760707`. So the death is not an artifact of choosing a bad learned-loop candidate.

Accepted ceiling: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`; no QIT-engine, holodeck/FEP, physics, Axis-0, bridge, manifold, or canonical-by-process claim.

## Artifact Freshness Caveat

The live committed/generated result JSON is stale against the current `ecd_registry_supplement_1_20260612.md` source hash:

```json
{
  "stored_supplement_hash": "106ff7947e2950e46a4fe887f2ea684ad22d0adad6f93763a29719d5074acb9d",
  "actual_supplement_hash": "3de0cefd2f467c471b29fba51fdfcfe039ec552fa49bd5d30c08d0103cc4ca2b",
  "validate_payload_on_committed_result": ["ecd_supplement_1 source hash drift"]
}
```

I did not refresh live result JSONs because the authorized write scope was only this audit verdict. A source-current in-memory rebuild validates with `errors=[]`, and a scratch-copy full command rerun under `/tmp/ecd06v2_audit_8oYQGv` passed base, JAX, PyTorch, Julia, envelope, validator, and `5 passed` pytest. Therefore the mathematical death is accepted, but strict-green artifact citation should either cite the scratch rerun in this audit or refresh the generated JSONs in a separate builder lane.

## Learned Loop Honesty

PASS. The v2 QIT side no longer predicts from heldout `render`. The learned-loop model fits:

- a render proposal as `source + gain * learned_delta`;
- `learned_delta` from training `realized - source` means keyed by `generator`, `generator_family`, or `source_state`;
- a residual correction from the same training rows;
- one correction update with rates `0.00`, `0.50`, or `1.00`.

The prediction function uses `src`, source coordinate, generator label/family, and learned training-budget tables. AST/source inspection of `_fit_qit_loop_model`, `qit_side`, and `baseline_side` found no prediction-time use of `render`, `dst`, `row_id`, direct prediction codes, committed generator specs, or heldout realized targets.

The `1.081028410929` headline learned-loop error is plausible, not a strawman. The carrier has slow state churn: `106/198` rows have zero source-to-realized movement, mean movement is `0.322106470486`, and heldout mean movement is `0.300425191603`. Persistence is naturally strong on these dynamics. The train-selected source-state loop overfits an allowed but weak grouping; generator/family loop variants do better, but still do not beat persistence.

## Parity Gate

PASS for both directions. The information-parity manifest gives both sides identical training inputs:

`budget_membership`, `src`, `source_coord`, `generator_label`, `generator_family`, `training_realized_target`

and identical prediction inputs:

`src`, `source_coord`, `generator_label`, `generator_family`.

Both sides forbid heldout render coordinates, heldout realized targets before prediction, `dst`, row-id target lookup, direct prediction code, committed generator matrix/spec, and upstream render-function output. I also checked the reverse asymmetry: persistence gets source state/source coordinate, but the QIT side is also allowed source-state keyed learned deltas; no baseline-only predictor input is present.

## Recomputed Rows And Controls

Primary budget: `66` train rows, `132` eval rows, `198` total source+generator cells, `66` train cells, `0` covered heldout eval pairs. The v0 full-observability regression still wins exactly with source+generator table adjusted error `0.0`, proving the deterministic table killer remains intact when the regime is fully observable.

Baseline table highlights:

| Policy | Train adjusted error | Eval adjusted error |
|---|---:|---:|
| `persistence_source_state` | 0.862207446533 | 0.608433222810 |
| `source_generator_transition_table_v0_killer_included_train_budget` | 0.000000000000 | 1.210737013737 |
| `searched_policy_class_source_plus_generator_delta` | 0.915271198075 | 0.755326811849 |
| `searched_policy_class_table_delta_blend_0.25` | 0.688942352180 | 0.770106266328 |

QIT best-by-eval cross-check:

| Policy | Train adjusted error | Eval adjusted error |
|---|---:|---:|
| `qit_learned_loop_generator_family_gain_0.50_correction_0.00` | 0.909463374323 | 0.671719983517 |
| `qit_learned_loop_generator_gain_0.50_correction_0.00` | 0.899372716440 | 0.691715653625 |
| `qit_learned_loop_source_state_gain_0.50_correction_1.00` | 0.692576593064 | 1.081028410929 |

Controls:

- v1 render-access regression equalizer reproduced the forbidden-access tie at `0.344150808264` for both QIT and classical equalizer.
- Full-observability table regression passed at `0.0`.
- Dropped-half controls both die: margins `0.047780215333` and `0.046662338598`.
- Scrambled-error control moved the margin from `0.472595188119` to `0.078731692081`.
- z3 and cvc5 finite scaled winner checks both returned `unsat` for contradiction of the baseline-wins relation.

## No Identity Leak And G.2a

No identity leak found in the predictor code path. The result excludes heldout render, committed generator/render specs, `dst`, realized coordinate, row-id target lookup, direct prediction code, and heldout label-table entries. The winning baseline is persistence from allowed source-state/source-coordinate information, not row identity lookup.

Standards caveat: the no-identity-leak row is an exclusion/code-path pass, not a measured identity-inclusive vs identity-excluded recovery sweep with `identity_leak_excluded_best_accuracy`. That does not rescue the QIT row or weaken the death, but registry citations should not overstate it as a full independent identity-leak classifier audit.

G.2a passes by source and scratch rerun: validator and boundary delegate to `builder_audit_boundary_errors(...)`, and this verdict header declares an independent read-only audit. No builder-authored audit verdict was present before this write.

## Reopen Conditions

No reopen condition remains for this carrier, this primary budget, and this equal-information contract.

Legitimate reopen lanes are scope changes, not objections to this death:

- a different carrier with faster churn or stochastic dynamics where residual error-correction has real temporal signal;
- a pre-registered recurrent/stateful learned-loop class that still obeys equal information;
- a metric that penalizes persistence or trivial source-state projection, declared before scoring;
- a different partial-observability budget where the same two-sided search and parity gates are pinned before evaluation.

## Registry Row Language

`ECD.06 prediction-first inference v2: DIES under equal information on the committed render-layer v1 edge carrier. Under the primary hash-balanced 66-train/132-heldout budget, the pinned train-selected learned render/error/update loop scores adjusted error 1.081028410929, while the best fair baseline, persistence_source_state, scores 0.608433222810 (margin +0.472595188119 against QIT). Even granting QIT heldout-best selection over its learned-loop candidates, its best row is 0.671719983517, still worse than persistence by +0.063286760707. The v1 forbidden render-access equalizer tie reproduces at 0.344150808264, full observability restores the source+generator table to 0.0, dropped-half controls both die, and no forbidden render/generator/target access appears in the v2 predictor path. Scratch diagnostic only; promotion_allowed=false; formal_admission_allowed=false; refresh generated result source locks before citing live strict-green artifacts.`

## Checks Run

Live checkout, read-only/in-memory:

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
# Loaded committed result, rebuilt build_prediction_first_object() in memory,
# compared headline fields, ran validate_payload(payload) and validate_payload(rebuilt).
# Committed payload error: ecd_supplement_1 source hash drift.
# Rebuilt payload errors: [].
PY
```

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
# Recomputed primary budget, QIT side, baseline side, movement/churn stats,
# QIT heldout-best countercheck, controls, z3/cvc5 rows, and AST prediction-input surface.
PY
```

Scratch copy under `/tmp/ecd06v2_audit_8oYQGv`:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 ecd06_prediction_first_inference_v2.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 ecd06_prediction_first_inference_v2_jax.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 ecd06_prediction_first_inference_v2_pytorch.py
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/tmp/ecd06v2_audit_8oYQGv/system_v5/julia_carrier ecd06_prediction_first_inference_v2_julia.jl
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 ecd06_prediction_first_inference_v2_envelope.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 validate_ecd06_prediction_first_inference_v2.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest tests/test_ecd06_prediction_first_inference_v2.py
```

Scratch results: base/JAX/PyTorch/Julia/envelope printed `all_pass: true`; validator printed `ok: true`, `errors: []`; pytest reported `5 passed in 18.19s`.

No `git add`, `git commit`, or live result refresh was run.
