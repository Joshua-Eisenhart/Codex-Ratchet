# Independent audit verdict -- manifold_dynamic_chart_v0

Auditor: independent fresh Codex cross-backend audit.
Audit mode: read-only packet audit except this verdict file.
Freshness tier: TIER-3 annotation-verify, because the pre-existing verdict file was visible during the audit. The lethal rows below were recomputed independently from source/result before accepting any verdict language.
Write scope: `system_v6/sims/manifold_dynamic_chart_v0/audit_verdict.md` only.
Verdict vocabulary: calibrated 2026-06-10 bar.

## Bottom Line

Verdict: `GENUINE-WITH-CAVEATS` as protocol machinery, but `NO-STABLE-DISTINCTION-YET` as a dynamic per-cell/Axis-0 readout.

The packet genuinely builds a dynamic Family A chart: `rho_c(t)` rows exist, local vN entropy is state-derived, entropy shells are recomputed and move, `j/k` rows are computed from graph continuations, controls are present, and the three engine lanes agree. It does not earn an actual Axis-0 readout. The lead tooth fires: the bridge response class is nearly constant, `32/33` `SPREAD` and `1/33` `DAMP`, while the region-level classifier returns `DAMP` for all three entropy regions.

Claim ceiling remains:

```text
scratch_diagnostic_dynamic_chart_v0_first_measurement_attempt_only
promotion_allowed=false
formal_admission_allowed=false
axis0_admission=not_admitted_first_honest_attempt
```

## Tooth 1 -- Near-Constancy

This is the decisive caveat.

Fresh recompute:

- Bridge per-cell actual classes: `SPREAD=32`, `DAMP=1`.
- Bridge majority baseline: `0.969696969697`.
- Old static sign accuracy: `0.454545454545`.
- Region classifier classes: `DAMP=3`, `SPREAD=0`, `NEUTRAL=0`.
- Small committed kick changes `32/33` initial states at `t=0`, and the state-Hamming fraction remains `0.969696969697` through `t=4`.

Reachability check:

- Per-cell bridge classes technically reach both values under the current pins, but `DAMP` is a single-cell exception.
- Region-level spread-vs-damp does not reach both values under the current pins: every entropy region is `DAMP`/`SCRAMBLING`.

Verdict: the packet must be cited as "protocol works; this perturbation family/window/classifier did not separate cells stably." Any future prose that treats the `32/33` vs `1/33` bridge class as a real per-cell dynamic readout overclaims the result.

## Tooth 2 -- State-Derived Verification

Pass with a narrow ceiling.

Source trace:

- Density matrices are built from the current Bloch cell coordinate and entropy is computed with `torch.linalg.eigvalsh`; source: `manifold_dynamic_chart_v0_common.py:263-282`.
- State rows store `entropy_source="computed_from_rho_eigenvalues"`; source: `manifold_dynamic_chart_v0_common.py:301-321`.
- Directed gradients are computed as `S_vN(rho_dst(t))-S_vN(rho_src(t))`; source: `manifold_dynamic_chart_v0_common.py:401-421`.
- Entropy shells use live per-time min/max entropy thirds and recompute memberships/boundaries at each `t`; source: `manifold_dynamic_chart_v0_common.py:438-483`.

Fresh recompute:

- Entropy recomputed from stored eigenvalues: max absolute drift `1.05e-12`, bad rows `0/165`.
- Density validity from stored rho/eigen rows: trace bad `0`, PSD bad `0`, Hermitian bad `0`.
- Entropy source labels: `165/165` are `computed_from_rho_eigenvalues`.
- Shell recompute mismatches: `0`.
- Boundary counts recomputed from shell memberships: `[48, 52, 52, 54, 62]`.

The old static `phi` enters only through the bridge row; the result manifest also declares `discrete_axis0_field_v0` supportive and not the entropy source.

## Tooth 3 -- Dynamics Nontriviality

Pass as finite chart dynamics, not as a stable response measurement.

The baseline trajectory has `T=4`, `165` state rows, and transition changed-cell counts `[30, 28, 4, 2]`, totaling `64` changed cell-steps. The motion is far above numerical noise because it is discrete cell movement under committed generators, not a float threshold artifact.

The perturbation bite is also real but too coarse for the readout: the small kick changes `32/33` initial states immediately. That explains the near-constant response and should become a v1 design target rather than a promoted v0 finding.

## Tooth 4 -- Bridge Row

The old static anchor is not rescued. The bridge row reports:

```text
old_phi_accuracy=0.454545454545
majority_baseline=0.969696969697
predicts_above_chance=false
outcome=fails_above_chance
```

But the bridge falsification is weak in the specific way the owner warned about: against a `32/33` majority class, almost any nonconstant predictor scores badly. The correct citation is local and negative: "old `phi` did not predict this v0 near-constant response class." It is not a strong falsification against a meaningful dynamic Axis-0 classifier, because v0 has not produced one yet.

Source for the bridge definition: `manifold_dynamic_chart_v0_common.py:709-743`. Result values: `results/manifold_dynamic_chart_v0_envelope_results.json:27165-27405`.

## Tooth 5 -- Controls

Pass, with one interpretation caveat.

Computed controls:

- Identity dynamics: ran, all cells static, classifier refused as `refuse_degenerate_static`.
- Scrambled adjacency: ran, trajectory signature changed.
- Dropped-half perturbation: ran, changed `16` initial states, peak Hamming fraction `0.484848484848`.
- Over-boundary perturbation: refused as boundary control, not injected as a fake entropy state.
- No-identity-leak: classifier feature fields exclude `cell_id`, `state_id`, `start_cell`, and `current_cell`.

Caveat: the no-identity-leak control is a field-exclusion check for a rule classifier, not a learned predictor recovery test. That is acceptable for this v0 ceiling, but it must not be cited as a full independence result.

Source: `manifold_dynamic_chart_v0_common.py:821-882`; result: `results/manifold_dynamic_chart_v0_envelope_results.json:416-449`.

## Tooth 6 -- G.2a And Three-Engine Roles

Pass for envelope hygiene.

The local validator result is green: `results/manifold_dynamic_chart_v0_validator_results.json:1-4`. The non-writing strict source-backed validator was rerun during this audit and returned `ok=true` for:

```text
scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/manifold_dynamic_chart_v0/results/manifold_dynamic_chart_v0_envelope_results.json
```

Engine roles are honest at this ceiling:

- Julia uses `Graphs` for the finite transition graph.
- JAX uses `networkx` and `sympy` for graph/count checks.
- PyTorch uses `torch.func` and `sympy`; the common path uses `torch.linalg.eigvalsh` for vN entropy.
- All lanes report `reads_peer_result=false` and `result_all_pass=true`.

This is cross-backend agreement on the chart trajectory and entropy arrays, not a stronger cross-run parity theorem.

## Tooth 7 -- What V0 Earned

Earned:

- `GENUINE` protocol machinery for a first dynamic chart packet.
- State-derived local vN entropy field on evolving chart states.
- Moving entropy shells.
- Computed `j/k` continuation rows.
- Controls where static/identity behavior can fail or be refused.
- A local negative bridge row for the old static `phi` under this v0 classifier.

Did not earn:

- Axis-0 admission.
- A real per-cell allostasis/homeostasis readout.
- A meaningful bridge falsification of the old anchor against a nondegenerate classifier.
- Final substrate choice among chart, spinor-network surface, and QCA/local update.
- Bridge, physics, manifold, or formal admission evidence.

## V1 Contract

The next admissible packet should vary the parts that made v0 nearly constant:

1. Perturbation strength: include smaller/localized kicks so the initial bite is not `32/33` by construction.
2. Perturbation family: compare generator kick, local neighbor kick, order perturbation, and over-boundary refusal with matched metrics.
3. Window length: test whether divergence damps, spreads, or reconverges after `T=4`.
4. Classification functional: replace final-cell-changed with a predeclared functional over entropy spread, shell motion, `j/k` multiplicity, and reconvergence.
5. Reachability gate: require both spread and damp to be reachable in more than a one-cell exception before any per-cell readout is cited.
6. `j/k` can-fail gate: include a variant where `j<k` or explicitly report that the current chart keeps all six continuations admissible.

## Citation Rule

Allowed citation:

```text
manifold_dynamic_chart_v0 is a GENUINE-WITH-CAVEATS scratch diagnostic: it builds the first state-derived dynamic Family A chart protocol, but the v0 response readout is near-constant (`32/33` bridge SPREAD; `3/3` regions DAMP), so Axis-0 remains unbuilt and the measurement question stays open.
```

Required caveat when citing the bridge:

```text
The old static phi bridge failed locally (`0.4545` vs `0.9697` majority), but because the dynamic class is near-constant this is not strong evidence against a meaningful nondegenerate dynamic classifier.
```

Do not cite this packet as `Axis-0 readout`, `homeostasis/allostasis measurement`, `bridge admission`, `canonical`, `formal`, or `final substrate` evidence.

## Evidence Pointers

- Binding owner correction: `system_v6/receipts/owner_correction_axis0_not_built_20260612.md` at `0313d47bc`.
- Dynamic upgrade design: `system_v6/receipts/dynamic_manifold_upgrade_design_20260612.md` at `4fc7c2f3b`.
- Static-shallowness rule 5: `system_v6/receipts/static_shallowness_audit_20260612.md` at `b4ee8f030`.
- Packet source: `system_v6/sims/manifold_dynamic_chart_v0/manifold_dynamic_chart_v0_common.py`.
- Envelope result: `system_v6/sims/manifold_dynamic_chart_v0/results/manifold_dynamic_chart_v0_envelope_results.json`.
- Validator result: `system_v6/sims/manifold_dynamic_chart_v0/results/manifold_dynamic_chart_v0_validator_results.json`.
