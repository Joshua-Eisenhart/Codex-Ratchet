# Fresh Audit: geo_s1_negative_models_v0

Audit date: 2026-06-10

VERDICT: GENUINE-WITH-CAVEATS for the Stage-1 negative-model suite.

The packet is an executable three-engine scratch diagnostic. The strict validator passes, the selectivity matrix is complete, each negative fails only its predicted receipt family, the no-conjugate map has the intended "looks right on S^2 but fails phase-orbit invariance" behavior, the naive grid factor is exactly 2 from computed integer counts, the positive S1 control passes, and the SMT polarity checks bind raw scaled values or computed integer counts.

The caveat is specific: the classical-bit absence receipts are computed local receipts, but they are not produced through the same geometry function path as the positive S1 control. That does not break the negative suite, but it blocks a clean anti-fixture-isolation claim for N4.

Ceiling remains: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. All three negatives are `negative_model=true`. No negative in this packet is a claim candidate or promotion artifact.

## Evidence Boundary

Sources read:

- `system_v6/sims/geo_s1_negative_models_v0/build_card.md`
- `system_v6/sims/geo_s1_negative_models_v0/geo_s1_negative_models_v0_jax.py`
- `system_v6/sims/geo_s1_negative_models_v0/geo_s1_negative_models_v0_pytorch.py`
- `system_v6/sims/geo_s1_negative_models_v0/geo_s1_negative_models_v0_julia.jl`
- `system_v6/sims/geo_s1_negative_models_v0/geo_s1_negative_models_v0_envelope.py`
- `system_v6/sims/geo_s1_negative_models_v0/results/geo_s1_negative_models_v0_jax_results.json`
- `system_v6/sims/geo_s1_negative_models_v0/results/geo_s1_negative_models_v0_pytorch_results.json`
- `system_v6/sims/geo_s1_negative_models_v0/results/geo_s1_negative_models_v0_julia_results.json`
- `system_v6/sims/geo_s1_negative_models_v0/results/geo_s1_negative_models_v0_envelope_results.json`
- R3 comparison pattern: `system_v6/sims/axis_independence_discriminators_036/audit_verdict.md`

Fresh commands/checks:

- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_s1_negative_models_v0/results/geo_s1_negative_models_v0_envelope_results.json` returned `ok:true`.
- Source import recomputed `no_conjugate_receipt()`, `grid_receipt()`, `classical_bit_receipt()`, `positive_control_receipt()`, `build_selectivity(...)`, and the z3/cvc5 proof helper calls without calling `main()` or rewriting result JSON.
- `git status --short -- system_v6/sims/geo_s1_negative_models_v0` reports the packet directory as untracked in this checkout.

## Manual Recompute Packet

Source-import recompute values:

| Check | Recomputed value |
|---|---|
| Selectivity complete | `true` |
| Selectivity pass | `true` |
| Negative 1 observed failures | `phase_invariance`, `fiber_phase_orbit` |
| Negative 2 observed failures | `grid_distinct_count`, `grid_area_ratio`, `grid_volume_ratio` |
| Negative 3 observed failures | `phase_quotient_nonempty`, `reconstructed_dimension_3`, `double_cover_rotation_nontrivial`, `fibration_link_exists` |
| No-conjugate S^2 max norm deviation | `1.1102230246251565e-15` |
| No-conjugate phase-orbit spread | `2.0000000000000004` |
| True-Hopf control spread | `5.772734324011309e-16` |
| Naive grid count | `4096` |
| Actual distinct spinor count | `2048` |
| Naive/distinct ratio | `2.0` |
| Pair identification max deviation | `4.62985963945236e-16` |
| Classical state-space dimension | `1` |
| Classical phase parameter count | `0` |
| Classical linking available | `0` |
| Positive control pass | `true` |
| Positive corrected-grid ratio | `1.0` |
| z3 spread-is-zero on negative 1 | `unsat` |
| cvc5 spread-is-zero on negative 1 | `unsat` |
| z3 spread-is-zero on true Hopf control | `sat` |
| cvc5 spread-is-zero on true Hopf control | `sat` |
| z3 ratio-not-2 on negative 2 | `unsat` |
| cvc5 ratio-not-2 on negative 2 | `unsat` |

## N1. Selectivity Matrix

Decision: PASS.

Quoted source:

```python
observed = {row: [key for key, value in cols.items() if value["status"] == "fail"] for row, cols in matrix.items()}
...
"selectivity_pass": all(observed[row] == predicted[row] for row in predicted),
```

Cites: `geo_s1_negative_models_v0_jax.py:393-401`; envelope gate at `geo_s1_negative_models_v0_envelope.py:154-160`.

The recomputed observed failures exactly match the predicted failures. Negative 1 fails only phase/fiber orbit receipts, negative 2 fails only grid/area/volume receipts, and negative 3 fails only phase quotient, dimension, double-cover, and fibration-link receipts. No negative fails everything, so this is not suite conflation.

## N2. No-Conjugate Map

Decision: PASS.

Quoted source:

```python
fake_norm = jnp.sum(hopf_no_conjugate(psi) ** 2, axis=1)
...
fake_spread = max_pairwise_distance(fake_images)
```

Cites: map definition at `geo_s1_negative_models_v0_jax.py:111-118`; receipt computation at `geo_s1_negative_models_v0_jax.py:165-203`.

The "looks right" receipt is real: max unit-sphere deviation recomputed as `1.1102230246251565e-15`, within `TOL=1.0e-8`. The phase-orbit spread is computed from images of phased spinors, not asserted: recompute gives `2.0000000000000004`, while the true-Hopf control spread is `5.772734324011309e-16`.

## N3. Naive Grid Factor

Decision: PASS.

Quoted source:

```python
naive, distinct = grid_distinct_count(n, eta)
expected_distinct = n * n // 2
```

Cites: distinct-count loop at `geo_s1_negative_models_v0_jax.py:154-162`; grid receipt at `geo_s1_negative_models_v0_jax.py:206-259`; proof binding at `geo_s1_negative_models_v0_jax.py:427-450`.

The factor 2 is from computed integer counts: `4096 / 2048 = 2.0`. The pair identification receipt also recomputed cleanly, with max paired-spinor deviation `4.62985963945236e-16`.

## N4. Classical-Bit Absences

Decision: PASS FOR RECEIPTS, CAVEAT FOR SAME-PATH CLAIM.

Quoted source:

```python
ps = jnp.linspace(0.0, 1.0, 257)
diag_expectation = ps
commutator = jnp.zeros((2, 2))
```

Cites: classical-bit receipt at `geo_s1_negative_models_v0_jax.py:262-304`; positive control at `geo_s1_negative_models_v0_jax.py:307-329`; shared main assembly at `geo_s1_negative_models_v0_jax.py:404-410`.

The absences are emitted as concrete receipt values: dimension `1`, phase parameter count `0`, double-cover absence magnitude `2.0`, and linking available `0`. The issue is path shape. `classical_bit_receipt()` is a separate fixture-style function using direct simplex/probe constants, while `positive_control_receipt()` uses the spinor/Hopf/grid path. They are assembled by the same `main()` and judged by the same selectivity function, but the classical absence receipts are not computed through the same geometry path as the positive control. That is the anti-fixture-isolation caveat.

## N5. Positive S1 Control

Decision: PASS.

Quoted source:

```python
true_images = hopf_true(jnp.exp(1j * alphas[:, None]) * base[None, :])
naive, distinct = grid_distinct_count(n, math.pi / 5.0)
```

Cites: `geo_s1_negative_models_v0_jax.py:307-329`; envelope gate at `geo_s1_negative_models_v0_envelope.py:162-166`.

The positive control passes in the same packet assembly: phase spread `5.772734324011309e-16`, corrected-grid ratio `1.0`, state-space dimension `3`, fibration linking number `1`, and `pass=true`.

## N6. Raw-Value SMT Flips

Decision: PASS.

Quoted source:

```python
spread_scaled = int(round(neg1["phase_invariance_receipt"]["orbit_spread_max_image_distance"] * SCALE))
...
naive_count = int(neg2["distinct_point_count_receipt"]["naive_claimed_count"])
actual_distinct = int(neg2["distinct_point_count_receipt"]["actual_distinct_spinor_count"])
```

Cites: raw values bound at `geo_s1_negative_models_v0_jax.py:411-438`; proof pass logic at `geo_s1_negative_models_v0_jax.py:440-450`; envelope raw-value binding at `geo_s1_negative_models_v0_envelope.py:226-260`.

The SMT checks bind the raw scaled no-conjugate spread and computed integer grid counts. Recompute gives `spread_scaled=2000000`, true-Hopf control `0`, and ratio row `[4096, 2048]`. z3 and cvc5 both return `unsat` for spread zero and ratio-not-2 on the negative rows, while the true-Hopf zero-spread controls return `sat`.

## Named Gaps

1. The N4 classical-bit path should be hardened if this suite is later used as anti-fixture evidence. The classical negative should be run through a common suite adapter that invokes the same receipt interface as the positive control, not a separate constant-heavy function.
2. The PyTorch and Julia legs are independent enough for envelope agreement, but the JAX leg is the richest audit surface for selectivity detail. Future reviewers should keep source-level JAX review as the primary check unless the other legs gain full matrix detail.
3. This packet should not be used to support a positive S1 geometry claim. It only shows that three named bad models fail in their predicted ways under this suite.

## Final Boundary

Keep: executable three-engine scratch diagnostic; negative selectivity evidence; no-conjugate phase failure; naive-grid factor-2 failure; positive-control sanity check; raw-value SMT polarity.

Audit further: shared-path hardening for the classical-bit negative.

Demote: any claim that this proves S1 admission, bridge support, axis evidence, or formal geometry closure.

Broken/blocked: none found for the stated scratch-diagnostic packet.

Next build: common negative-suite adapter with one receipt interface for classical negatives and positive controls, while preserving the current selectivity matrix.

## Post-Hardening Re-Audit Addendum — 2026-06-10

Scope: focused read-only re-audit of the prior §Named Gaps after hardening. I did not rebuild or harden this packet; I inspected source/result state and reran the validators.

Validator reruns:

- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed system_v6/sims/geo_s1_negative_models_v0/results/geo_s1_negative_models_v0_envelope_results.json` returned `{"ok": true}`.
- Extra strict check also returned `{"ok": true}` with `--require-pytorch --strict-source-backed`.

Named-gap closure check:

1. The classical-bit negative is now routed through the common suite adapter. Source defines `common_suite_adapter(...)`; `classical_bit_receipt()` returns `common_suite_adapter("negative_3_classical_bit_n01_negative_carrier", True, receipts, metadata)`, and `positive_control_receipt()` returns the same adapter id with the same receipt-key interface. Result records `adapter_id: s1_common_negative_positive_receipt_interface_v1` and `same_interface_as_positive_control: true` for both the classical-bit negative and the positive control.
2. The JAX-primary note is present. Envelope `audit_surface_note` says: `JAX leg = primary selectivity surface; Julia and PyTorch legs are envelope-level independent magnitude mirrors.`
3. The no-positive-claim fence is present under the packet's field name `negative_suite_scope`, not a literal `usage_fence` key. It says: `shows three named bad models fail as predicted; supports NO positive S1 claim`. The top-level claim also says this is `not a claim candidate`.

Byte-stable fields checked:

- Selectivity matrix remains complete and passing: `complete=true`, `selectivity_pass=true`.
- Observed failures still equal predicted failures:
  - `negative_1_no_conjugate_map`: `phase_invariance`, `fiber_phase_orbit`.
  - `negative_2_naive_grid_double_cover_ignored`: `grid_distinct_count`, `grid_area_ratio`, `grid_volume_ratio`.
  - `negative_3_classical_bit_n01_negative_carrier`: `phase_quotient_nonempty`, `reconstructed_dimension_3`, `double_cover_rotation_nontrivial`, `fibration_link_exists`.
- Factor-2 count row is stable: naive `4096`, actual distinct `2048`, overcount factor `2.0`.
- Orbit spread is stable across JAX/Julia/PyTorch shared scalars: `2.0000000000000004`; corrected true-Hopf control spread remains scaled `0`.
- Positive control remains stable: phase spread `5.772734324011309e-16`, corrected-grid ratio `1.0`, state-space dimension `3`, fibration linking number `1`, `pass=true`.
- Solver polarity remains stable: z3/cvc5 `negative_1_assert_spread_zero=unsat`, true-Hopf spread-zero control `sat`, `negative_2_assert_ratio_not_2=unsat`, corrected ratio-not-1 control `unsat`; Julia Z3 remains `unsat`.

Current ceiling: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`, `negative_model=true`. This is a negative-model fence only: it supports no positive S1 geometry, bridge, axis, formal-geometry, or promotion claim. Prior §Named Gaps are historically preserved above, but no stale open-gap surface remains for the three named hardening items checked here.

Final line: sustained.
