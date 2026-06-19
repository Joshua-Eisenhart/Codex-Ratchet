# Fresh audit verdict: geo_network_shell_coordinate_v0 v2

Audit date: 2026-06-10
Auditor mode: read-only inspection plus independent recomputation; only this `audit_verdict.md` was written.
Calibration bar: `system_v6/receipts/audit_bar_calibration_20260610.md`.

## Bottom line

VERDICT: ACCEPTED WITH NAMED CAVEAT.

The v2 packet is a genuine `scratch_diagnostic` packet for a named static network-level shell-coordinate family on committed n=3/n=4 lifted-rung exports. It fixes the v1 bare-Julia-leg defect: the Julia Manifolds and Z3 rows are claim-bearing, gated, and cross-checked by envelope validation plus independent recomputation.

It does not by itself close the whole n=3/n=4/n=5 lifted-rung G4 bookkeeping surface. The packet whitelists and computes n=3/n=4 only, and its envelope explicitly disallows `n5 trend`. G4 can be marked closed for "named coordinate family exists and is discriminated on n=3/n=4"; the lifted rungs still need either in-rung emission of this named coordinate row, or a committed n=5 coordinate packet/row that cites this packet's definition and computes n=5 values from n=5 per-site shell data.

Ceiling: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`; not canonical, not formal admission, not cross-run parity.

## Audit bar used

The calibrated bar keeps load-bearing capability and can-fail controls: `system_v6/receipts/audit_bar_calibration_20260610.md:5` says to keep "can-fail controls w/ failure semantics", "capability-probe gate for load_bearing", "route genuineness on claim paths", and "scratch ceilings".

For the Manifolds float row, I applied exactness-class stability rather than byte-stability: `system_v6/receipts/audit_bar_calibration_20260610.md:8` says diagnostic-float rows may move with route improvements when movement is reported, not failed. For solver evidence, `system_v6/receipts/audit_bar_calibration_20260610.md:11` allows one genuine derivation plus independent solver/cross-engine binding with an honest split label.

## Source quotes checked

- Packet pin and source scope: `geo_network_shell_coordinate_v0_julia.jl:23-27` names the packet as `G4-static-network-level-shell-coordinate`, names the candidate coordinates, and reads only committed `stage_lifted_spinor_shell_n3_v0` and `stage_lifted_spinor_shell_n4_v0` JAX result JSONs.
- Coordinate family: `geo_network_shell_coordinate_v0_julia.jl:74-79` emits `degree_weighted_shell_centroid_spread_v0`, `degree_squared_shell_centroid_v0`, `edge_gradient_shell_energy_v0`, and `unweighted_shell_mean_spread_alt_v0`.
- Manifolds call: `geo_network_shell_coordinate_v0_julia.jl:92-121` constructs `Manifolds.Sphere(2)` and `Manifolds.Torus(2)`, calls `Manifolds.mean(sphere, sphere_pts, weights)` and `Manifolds.mean(torus, torus_pts, weights)`, records `frechet_karcher_z_bar` vs `chart_space_weighted_z_bar`, and sets `fired` only when finite and, for unequal-degree rows, divergent by more than `1.0e-6`.
- Z3 binding: `geo_network_shell_coordinate_v0_julia.jl:153-175` binds each scaled raw z value and weight into Z3 integer variables before asserting equality. `geo_network_shell_coordinate_v0_julia.jl:178-212` records unweighted, weighted, erased-weight, and permuted statuses, and only fires when they match `sat/unsat/sat/unsat`.
- Control gate: `geo_network_shell_coordinate_v0_julia.jl:245-270` makes the degenerate alternative control depend on unweighted sameness, weighted separation, and the Z3 row firing.
- Tool depth and receipts: `geo_network_shell_coordinate_v0_julia.jl:337-355` marks `Graphs`, `Manifolds`, and `Z3` as load-bearing and records current-rerun capability receipts.
- Envelope gate: `geo_network_shell_coordinate_v0_envelope.py:272-292` requires all legs pass, source hashes fresh, input whitelist fresh, controls firing, cross-engine coordinate agreement, capability receipts, Manifolds row gate, Z3 SMT gate, and Z3/CVC5 crossover agreement.
- Ceiling: `geo_network_shell_coordinate_v0_envelope.py:304-310` allows only n=3/n=4 coordinate/control claims and disallows "canonical network coordinate", "formal admission", "promotion beyond scratch", "n5 trend", and "geo bracketing result".

## Q1 Candidate family honest

PASS.

The packet reports a family, not a crowned winner:

- `degree_weighted_shell_centroid_spread_v0`
- `degree_squared_shell_centroid_v0`
- `edge_gradient_shell_energy_v0`
- `unweighted_shell_mean_spread_alt_v0`
- Julia-only discriminating row: `frechet_karcher_shell_mean_degree_weighted_v0`
- Julia-only SMT row: `z3_smt_degenerate_conflation_v0`

The envelope result says the non-degenerate candidates after controls are `degree_weighted_shell_centroid_spread_v0` and `edge_gradient_shell_energy_v0`, while the unweighted alternative is retained but not crowned. The source and result rows keep the unweighted alternative visible as an alternative/control, which satisfies the anti-collapse requirement.

## Q2 Manifolds.jl load-bearing

PASS.

The source call is on a real manifold object:

- `sphere = Manifolds.Sphere(2)`
- `torus = Manifolds.Torus(2)`
- `sphere_mean = Manifolds.mean(sphere, sphere_pts, weights)`
- `torus_mean = Manifolds.mean(torus, torus_pts, weights)`

The Manifolds row gates the result. The row's `fired` condition is included in `all_controls_fired` through `source_coordinates`, and the envelope separately requires `julia_manifolds_rows_gate=true`.

Stored n=4 Manifolds row:

- chart-space weighted z: `0.05`
- Manifolds Frechet/Karcher z: `0.518398763214`
- stored divergence: `0.468398763214`
- `curvature_divergence_detected=true`

Independent recomputation from committed n=4 raw sites with a separate SciPy sphere-Frechet objective gave:

- independent sphere mean point: `[-0.854390389214, 0.035710113217, 0.518403173826]`
- independent Frechet z: `0.518403173826`
- independent chart-vs-manifold divergence: `0.468403173826`
- difference from stored Manifolds z: about `4.41e-6`

This is not byte-identical, but it independently verifies the row's substantive claim: the manifold mean is not the chart-space z mean, and the divergence is large relative to the `1.0e-6` firing threshold. Under the calibrated audit bar, this is a diagnostic-float movement report, not a fail.

## Q3 Z3 separation row derived

PASS.

Raw n=4 values recomputed from the committed export:

- site order: `q0,q1,q2,q3`
- z values: `[0.809016994375, 0.309016994375, -0.309016994375, -0.809016994375]`
- support degrees: `[3,2,3,2]`
- original degree-weighted mean: `(3*0.809016994375 + 2*0.309016994375 + 3*(-0.309016994375) + 2*(-0.809016994375)) / 10 = 0.05`
- after swapping q1/q2 z values: `(3*0.809016994375 + 2*(-0.309016994375) + 3*0.309016994375 + 2*(-0.809016994375)) / 10 = 0.111803398875`
- `0.111803398875 = sqrt(5)/20` within `1.06e-14` from the rounded committed data.
- unweighted mean before and after swap: `0.0`

Independent solver recomputation from raw scaled values:

| equality check | Z3 | CVC5 |
| --- | --- | --- |
| unweighted original == swapped | `sat` | `sat` |
| degree-weighted original == swapped | `unsat` | `unsat` |
| erased weights original == swapped | `sat` | `sat` |
| permuted paired weighted original == swapped | `unsat` | `unsat` |

This matches the stored Julia Z3 row and the envelope CVC5 crossover proof. The row is derived from bound raw values and weights, not just from already-rounded coordinate labels.

## Q4 Controls fire and can fail

PASS.

All four requested controls fire and are written as predicates that can fail:

- Collapsed shell: mutates every site z to one shell value; requires degree-weighted `sigma_z=0` and centroid equal to that shell.
- Permuted labels: reverses site labels and relabels support edges consistently; requires the network-coordinate dictionary to be invariant.
- Moved site: moves q0 by `-0.2` within bounds; requires the weighted z mean or edge-gradient energy to change.
- Degenerate alternative: swaps two unequal-degree n=4 site z values; requires unweighted conflation, weighted separation, and Z3 `sat/unsat/sat/unsat`.

Fresh recomputation confirmed n=4:

- collapsed shell gives centroid `0.309016994375` and spread `0.0`;
- label permutation preserves the coordinate dictionary;
- moved q0 changes weighted z from `0.05` to `-0.01` and edge energy from `0.95` to `0.7151145618`;
- unweighted swap conflates at `0.0`, while weighted swap separates `0.05` vs `0.111803398875`.

## Q5 Lineage and standard

PASS WITH PACKET-UNTRACKED NOTE.

The upstream n=3/n=4 inputs are committed files:

- `system_v6/sims/stage_lifted_spinor_shell_n3_v0/results/stage_lifted_spinor_shell_n3_v0_jax_results.json`
- `system_v6/sims/stage_lifted_spinor_shell_n4_v0/results/stage_lifted_spinor_shell_n4_v0_jax_results.json`

Recomputed hashes match packet receipts:

- n=3: `18dc57bd1f9f404daaa857e2e4d6cf5761b4cd49e4f410f00dd66a9e8935c273`
- n=4: `8ba4faf424e6f5a4a68d0220f3b3b658cc860ab643c7f3387ef8ea169282da3f`

The envelope `--validate-only` command returned:

```text
ok: true
errors: []
declared_mode: all_three_full_sims
require_pytorch: true
```

The packet has:

- `classification=scratch_diagnostic`
- `promotion_allowed=false`
- `formal_admission_allowed=false`
- `reads_peer_result=false` on Julia/JAX/PyTorch legs
- function-level `tool_calls`
- current-rerun `capability_receipts`
- no cross-run parity claim

Packet-untracked note: at audit time, `git status --short -- system_v6/sims/geo_network_shell_coordinate_v0` reported the packet directory as untracked. That does not invalidate the packet-local audit, but it means any durable closure claim needs the packet committed or otherwise admitted through the repo's evidence path.

## Q6 Closure

PARTIAL G4 CLOSURE.

This packet closes the specific missing-name/missing-discrimination defect for n=3/n=4: a named static network-level shell-coordinate family exists, is computed from committed per-site shell coordinates plus support graph edges, and is discriminated against a degenerate unweighted alternative. The family is honest because it reports multiple candidates and uses can-fail controls instead of crowning one coordinate too early.

This packet does not close all lifted-rung G4 bookkeeping for n=3/n=4/n=5 because n=5 is not read or computed here. The envelope's own disallowed claims include `n5 trend`, and the source whitelist contains only n=3 and n=4.

To close G4 across lifted rungs, the rungs need one of these concrete artifacts:

1. In-rung emission: each lifted rung result emits the named coordinate family rows, including `degree_weighted_shell_centroid_spread_v0`, `degree_squared_shell_centroid_v0`, `edge_gradient_shell_energy_v0`, `unweighted_shell_mean_spread_alt_v0`, source hash, and controls.
2. Citation plus computed row: each lifted rung cites this packet as the coordinate-definition authority and either includes its own computed values or points to a committed coordinate result packet covering that rung.

For n=5, a bare citation to this n=3/n=4 packet is enough to reuse the definition, but not enough to claim n=5 has a computed named network-level coordinate. A n=5 row or packet still has to compute the values and controls from the n=5 per-site shell export.

## Final classification

Accepted label: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

Accepted claims:

- named static network-level shell-coordinate family exists for committed n=3/n=4 exports;
- Manifolds.jl Frechet/Karcher row is genuinely load-bearing and gates a divergence row;
- Z3 separation row is genuinely derived from bound raw values and weights;
- CVC5 independently agrees with the weighted/separation solver result;
- controls fire and are fail-capable;
- no canonical/formal/cross-run/n5 trend claim is admitted.

Rejected or still-open claims:

- canonical network coordinate;
- formal admission;
- all-rung n=3/n=4/n=5 G4 closure without a n=5 coordinate row;
- cross-run parity;
- geo-bracketing or axis-level consequence.

## Builder-extension addendum: n5 coordinate rows

Addendum date: 2026-06-10.
Builder note, not fresh audit replacement: the fresh verdict above stands. The n5 rows have been added and rerun, but remain pending re-audit.

The extension computes the same named coordinate family on the committed n5 per-site shell export:

- Source: `system_v6/sims/stage_lifted_spinor_shell_n5_v0/results/stage_lifted_spinor_shell_n5_v0_jax_results.json`
- Source sha256: `f1f7aaeb2fd4376b5878ac71082891ccdaaf9535a498496b8793923968c8cbcb`
- Fields read: `rows.P2_support_object.sites`, `rows.P2_support_object.edges`, and `rows.P8_shell_leakage.aggregate_leakage`

Rows added:

- `n5.network_shell_coordinates.degree_weighted_shell_centroid_spread_v0`: `z_bar=0.0`, `sigma_z=0.626783170528`
- `n5.network_shell_coordinates.degree_squared_shell_centroid_v0`: `z_bar=0.0`
- `n5.network_shell_coordinates.edge_gradient_shell_energy_v0`: `edge_mean_delta_z_squared=0.752564170347`, `edge_count=7`
- `n5.network_shell_coordinates.unweighted_shell_mean_spread_alt_v0`: `z_bar=0.0`, `sigma_z=0.632455532033`
- `n5.julia_load_bearing_rows.frechet_karcher_shell_mean_degree_weighted_v0`: `frechet_karcher_z_bar=0.000207899144`, `chart_space_weighted_z_bar=0.0`, `abs_divergence=0.000207899144`, `fired=true`
- `n5.controls.degenerate_unweighted_conflation.z3_smt_row`: `sat/unsat/sat/unsat`, `weighted_original_z_bar=0.0`, `weighted_swapped_z_bar=0.071428571429`, `weighted_delta_abs=0.071428571429`

Controls at n5:

- `collapsed_shell`: fired
- `permuted_site_labels`: fired
- `moved_single_site`: fired
- `degenerate_unweighted_conflation`: fired, with Z3 and CVC5 both deriving weighted separation from bound n5 raw values and degree weights

Envelope change:

- The source whitelist now includes the n5 JAX result above.
- Allowed coordinate/control claims now cover per-rung n3/n4/n5 rows for this named coordinate family.
- Trend and scaling claims remain disallowed. The old `n5 trend` fence applied to the pre-extension state; this addendum only adds per-rung n5 coordinate rows.

Fresh reruns/checks:

- `julia system_v6/sims/geo_network_shell_coordinate_v0/geo_network_shell_coordinate_v0_julia.jl` -> `ok:true`
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_network_shell_coordinate_v0/geo_network_shell_coordinate_v0_jax.py` -> `ok:true`
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_network_shell_coordinate_v0/geo_network_shell_coordinate_v0_pytorch.py` -> `ok:true`
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_network_shell_coordinate_v0/geo_network_shell_coordinate_v0_envelope.py` -> `ok:true`
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_network_shell_coordinate_v0/geo_network_shell_coordinate_v0_envelope.py --validate-only` -> `ok:true`
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_network_shell_coordinate_v0/results/geo_network_shell_coordinate_v0_envelope_results.json` -> `ok:true`

Stability note:

- Existing n3/n4 network coordinate rows stayed byte-stable against `HEAD` in Julia, JAX, and PyTorch result JSONs.
- Existing n3/n4 control fired statuses stayed stable.
- Existing n3/n4 Julia Manifolds diagnostic-float rows stayed exactness-class stable; this rerun showed no numeric movement for stored `frechet_karcher_z_bar` or `abs_divergence`.

## Focused re-audit addendum: n5 extension rows only

Addendum date: 2026-06-10.
Scope: read-only re-audit of the new n5 rows only. The committed v2 verdict above (`ACCEPTED WITH NAMED CAVEAT`) stands.

Result: n=5 G4 coordinate rows EARNED. They consume the committed n5 per-site export, reuse the named coordinate-family definitions, derive the n5 solver row from n5 raw values, fire the required controls, leave n3/n4 rows byte-stable, and keep trend/scaling claims disallowed.

Source lineage checked:

- Source quote: `geo_network_shell_coordinate_v0_julia.jl:23-28` says `inputs=committed stage_lifted_spinor_shell_n3_v0,n4_v0,n5_v0 results read-only` and maps `"n5"` to `stage_lifted_spinor_shell_n5_v0_jax_results.json`.
- Source quote: `geo_network_shell_coordinate_v0_jax.py:34-41` and `geo_network_shell_coordinate_v0_pytorch.py:29-36` use the same pin text and coordinate names for the n5 extension.
- Source quote: `geo_network_shell_coordinate_v0_envelope.py:30-36` whitelists n3, n4, and n5 source result paths and sets `DEGENERATE_DISCRIMINATOR_LABELS = ("n4", "n5")`.
- `git ls-files --error-unmatch system_v6/sims/stage_lifted_spinor_shell_n5_v0/results/stage_lifted_spinor_shell_n5_v0_jax_results.json` succeeded, and `git cat-file -e HEAD:<same path>` succeeded, so the n5 source export is committed in `HEAD`.
- Recomputed sha256 of the n5 source export: `f1f7aaeb2fd4376b5878ac71082891ccdaaf9535a498496b8793923968c8cbcb`, matching the cited `input_source_results.n5.sha256` in the Julia/JAX/PyTorch legs and envelope.

Definition reuse checked:

- Source quote: `geo_network_shell_coordinate_v0_julia.jl:63-80`, `geo_network_shell_coordinate_v0_jax.py:111-142`, and `geo_network_shell_coordinate_v0_pytorch.py:80-97` compute the same four named rows: `degree_weighted_shell_centroid_spread_v0`, `degree_squared_shell_centroid_v0`, `edge_gradient_shell_energy_v0`, and `unweighted_shell_mean_spread_alt_v0`.
- The stored n5 source values are `z=[0.866025403784, 0.5, 0.0, -0.5, -0.866025403784]`, degrees `[3,2,4,2,3]`, and `edge_count=7`.
- Hand recomputation from the committed per-site export: unweighted mean `(0.866025403784 + 0.5 + 0 - 0.5 - 0.866025403784)/5 = 0.0`; unweighted sigma `0.632455532033`, matching `n5.unweighted_shell_mean_spread_alt_v0`.
- Hand recomputation of one weighted value: `(3*0.866025403784 + 2*0.5 + 4*0 + 2*(-0.5) + 3*(-0.866025403784))/(3+2+4+2+3) = 0.0`, matching `n5.degree_weighted_shell_centroid_spread_v0.z_bar`. The same recomputation gives weighted sigma `0.626783170528`, matching the stored n5 row.
- Edge-energy recomputation from the n5 support edges gives `0.752564170347`, matching `n5.edge_gradient_shell_energy_v0.edge_mean_delta_z_squared`.

Solver row checked:

- Source quote: `geo_network_shell_coordinate_v0_julia.jl:154-175` binds raw scaled z values and weights into Z3 variables before equality assertions; `geo_network_shell_coordinate_v0_envelope.py:215-253` separately rebuilds n4/n5 CVC5 and Z3 crossover proofs from Julia row raw `z_values` and `degrees`.
- The n5 row uses n5 raw values, not n3/n4 relabeling: site ids are `q0..q4`, z values are `[0.866025403784, 0.5, 0.0, -0.5, -0.866025403784]`, and degrees are `[3,2,4,2,3]`.
- Recomputed n5 swap of positions 2 and 3 keeps unweighted mean at `0.0`, but changes degree-weighted mean from `0.0` to `0.071428571429`, delta `0.071428571429`.
- Stored n5 Z3/CVC5 row reports `unweighted=sat`, `weighted=unsat`, `erased_weights=sat`, and `permuted_weighted=unsat`; this matches the n5 raw-value recomputation and differs numerically from the n4 row (`0.05` to `0.111803398875`, delta `0.061803398875`).

Controls and stability checked:

- Source quote: `geo_network_shell_coordinate_v0_julia.jl:217-243`, `geo_network_shell_coordinate_v0_jax.py:166-201`, and `geo_network_shell_coordinate_v0_pytorch.py:100-130` define the same four controls: `collapsed_shell`, `permuted_site_labels`, `moved_single_site`, and `degenerate_unweighted_conflation`.
- Current Julia/JAX/PyTorch result JSONs all report n5 `collapsed_shell=true`, `permuted_site_labels=true`, `moved_single_site=true`, and `degenerate_unweighted_conflation=true`.
- `geo_network_shell_coordinate_v0_envelope.py --validate-only` returned `ok: true`, `errors: []`, mode `all_three_full_sims`, and `require_pytorch: true`.
- Extracted `.rows.n3` and `.rows.n4` from current Julia, JAX, and PyTorch result JSONs diffed byte-stable against `HEAD` after `jq -S` normalization.

Trend/scaling ceiling checked:

- Source quote: `geo_network_shell_coordinate_v0_envelope.py:315-320` allows only computed n3/n4/n5 coordinate/control claims and explicitly disallows `"trend claim"` and `"scaling claim"`.
- Search over the packet source, result JSONs, and this verdict found no promoted ladder-trend, monotonic, scaling, or cross-rung consequence language. The only live per-rung wording is bookkeeping for computed n3/n4/n5 rows, not a trend claim.

Q6 condition: completed for the audit's own G4 bookkeeping condition only: named family + discriminated + per-rung rows n3/n4/n5. Ceiling remains `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`; not canonical, not formal, not a trend/scaling claim, not geo-bracketing or axis-level evidence.

## Builder-extension addendum: n6/n7 coordinate rows

Addendum date: 2026-06-10.
Builder note, not fresh audit replacement: the fresh verdict and focused n5 re-audit above stand. The n6/n7 rows have been added and rerun, but remain pending re-audit.

The extension computes the same named coordinate family on the committed n6 and n7 per-site shell exports:

- n6 source: `system_v6/sims/stage_lifted_spinor_shell_n6_v0/results/stage_lifted_spinor_shell_n6_v0_jax_results.json`
- n6 source sha256: `881e1b9b1255cd408e08094aa679790417706937e81a619fe1b283dc17d54571`
- n7 source: `system_v6/sims/stage_lifted_spinor_shell_n7_v0/results/stage_lifted_spinor_shell_n7_v0_jax_results.json`
- n7 source sha256: `1a24dbf38f4f7cc366de261767bd74f43a8ef7fdd59acc5897f037e660b988fc`
- Fields read: `rows.P2_support_object.sites`, `rows.P2_support_object.edges`, and `rows.P8_shell_leakage.aggregate_leakage`

Rows added:

- `n6.network_shell_coordinates.degree_weighted_shell_centroid_spread_v0`: `z_bar=0.0`, `sigma_z=0.645497224368`
- `n6.network_shell_coordinates.degree_squared_shell_centroid_v0`: `z_bar=0.0`
- `n6.network_shell_coordinates.edge_gradient_shell_energy_v0`: `edge_mean_delta_z_squared=0.910048599846`, `edge_count=12`
- `n6.network_shell_coordinates.unweighted_shell_mean_spread_alt_v0`: `z_bar=0.0`, `sigma_z=0.645497224368`
- `n6.julia_load_bearing_rows.frechet_karcher_shell_mean_degree_weighted_v0`: `frechet_karcher_z_bar=0.000046834698`, `chart_space_weighted_z_bar=0.0`, `abs_divergence=0.000046834698`, `fired=true`
- `n7.network_shell_coordinates.degree_weighted_shell_centroid_spread_v0`: `z_bar=0.0`, `sigma_z=0.654653670708`
- `n7.network_shell_coordinates.degree_squared_shell_centroid_v0`: `z_bar=0.0`
- `n7.network_shell_coordinates.edge_gradient_shell_energy_v0`: `edge_mean_delta_z_squared=0.821671016952`, `edge_count=14`
- `n7.network_shell_coordinates.unweighted_shell_mean_spread_alt_v0`: `z_bar=0.0`, `sigma_z=0.654653670708`
- `n7.julia_load_bearing_rows.frechet_karcher_shell_mean_degree_weighted_v0`: `frechet_karcher_z_bar=0.000015554599`, `chart_space_weighted_z_bar=0.0`, `abs_divergence=0.000015554599`, `fired=true`

Controls at n6/n7:

- `collapsed_shell`: fired
- `permuted_site_labels`: fired
- `moved_single_site`: fired
- `degenerate_unweighted_conflation`: fired as an equal-degree boundary row, not as an unequal-degree Z3 separation row

Boundary note:

- The committed n6 and n7 support graphs are degree-regular under this packet's existing `support_graph_degree` rule: n6 weights are `[4,4,4,4,4,4]`; n7 weights are `[4,4,4,4,4,4,4]`.
- Therefore degree-weighted and unweighted means intentionally coincide for n6/n7. A rung-local Z3 weighted-vs-unweighted separation would be false for these raw degree values.
- The envelope keeps `DEGENERATE_DISCRIMINATOR_LABELS=("n4","n5")` and adds `EQUAL_DEGREE_BOUNDARY_LABELS=("n3","n6","n7")`. This preserves the named coordinate family without inventing a new directed-degree coordinate or widening the claim.

Envelope change:

- The source whitelist now includes the n6 and n7 JAX results above.
- Allowed coordinate/control claims now cover per-rung n3/n4/n5/n6/n7 rows for this named coordinate family.
- Trend and scaling claims remain disallowed.

Fresh reruns/checks:

- `julia system_v6/sims/geo_network_shell_coordinate_v0/geo_network_shell_coordinate_v0_julia.jl` -> `ok:true`
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_network_shell_coordinate_v0/geo_network_shell_coordinate_v0_jax.py` -> `ok:true`
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_network_shell_coordinate_v0/geo_network_shell_coordinate_v0_pytorch.py` -> `ok:true`
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_network_shell_coordinate_v0/geo_network_shell_coordinate_v0_envelope.py` -> `ok:true`
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_network_shell_coordinate_v0/geo_network_shell_coordinate_v0_envelope.py --validate-only` -> `ok:true`
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_network_shell_coordinate_v0/results/geo_network_shell_coordinate_v0_envelope_results.json` -> `ok:true`

Stability note:

- Existing n3/n4/n5 row objects stayed byte-equivalent to `HEAD` in Julia, JAX, and PyTorch result JSONs.
- `stage_lifted_spinor_shell_n8_v0` was not edited, staged, or committed by this extension.

## Focused re-audit addendum: n6/n7 extension rows only

Addendum date: 2026-06-10.
Scope: read-only re-audit of the new n6/n7 rows only. Prior verdicts above stand.

Result: n6/n7 G4 rows EARNED as equal-degree boundary rows. They do not earn a new weighted-vs-unweighted separation witness; they earn the narrower claim that the named coordinate family is computed from committed n6/n7 exports and that these rungs are honestly recorded as degree-regular boundary cases while the Z3/CVC5 separation discriminator remains on n4/n5.

Degree regularity checked from committed exports:

- `git show HEAD:system_v6/sims/stage_lifted_spinor_shell_n6_v0/results/stage_lifted_spinor_shell_n6_v0_jax_results.json` recomputed sha256 `881e1b9b1255cd408e08094aa679790417706937e81a619fe1b283dc17d54571`, node count `6`, edge count `12`, degree sequence `[4,4,4,4,4,4]`.
- `git show HEAD:system_v6/sims/stage_lifted_spinor_shell_n7_v0/results/stage_lifted_spinor_shell_n7_v0_jax_results.json` recomputed sha256 `1a24dbf38f4f7cc366de261767bd74f43a8ef7fdd59acc5897f037e660b988fc`, node count `7`, edge count `14`, degree sequence `[4,4,4,4,4,4,4]`.
- The arithmetic check is exact for the graph sizes: `12*2/6=4` and `14*2/7=4`.

Impossibility argument stated:

- For weights `w_i=d` constant on all sites, the degree-weighted mean is `sum_i d*z_i / sum_i d = d*sum_i z_i / (n*d) = sum_i z_i/n`, exactly the unweighted mean.
- The same collapse holds for degree-squared weights because `w_i=d^2` is also constant.
- Therefore a rung-local weighted-vs-unweighted separation is structurally impossible for n6/n7 under this packet's `support_graph_degree` rule. Recording `degenerate_witness_applicable=false`, `fired=true`, and `packet_discriminator_source="n4"` is an honest boundary, not a dodge.

Coordinate values still computed from real exports:

- n6 recomputation from the committed export gives weighted `z_bar=0.0`, weighted `sigma_z=0.645497224368`, unweighted `z_bar=0.0`, unweighted `sigma_z=0.645497224368`, and edge energy `0.910048599846`; these match the stored Julia n6 row.
- n7 recomputation from the committed export gives weighted `z_bar=0.0`, weighted `sigma_z=0.654653670708`, unweighted `z_bar=0.0`, unweighted `sigma_z=0.654653670708`, and edge energy `0.821671016952`; these match the stored Julia n7 row.
- The Julia Manifolds rows are present and nonzero as real computed rows: n6 `frechet_karcher_z_bar=0.000046834698`, `chart_space_weighted_z_bar=0.0`, `abs_divergence=0.000046834698`; n7 `frechet_karcher_z_bar=0.000015554599`, `chart_space_weighted_z_bar=0.0`, `abs_divergence=0.000015554599`.

Stability and gates checked:

- Extracted `.rows.n3`, `.rows.n4`, and `.rows.n5` from current Julia, JAX, and PyTorch result JSONs diffed byte-stable against `HEAD` after `jq -S` normalization.
- `geo_network_shell_coordinate_v0_envelope.py --validate-only` returned `ok: true`, `errors: []`, mode `all_three_full_sims`, and `require_pytorch: true`; its read-only source list includes n3/n4/n5/n6/n7.
- The envelope keeps `DEGENERATE_DISCRIMINATOR_LABELS=("n4","n5")` and `EQUAL_DEGREE_BOUNDARY_LABELS=("n3","n6","n7")`.
- Search over the packet source and result JSONs found no promoted trend, scaling, monotonic, or cross-rung consequence claim. The envelope explicitly lists `"trend claim"` and `"scaling claim"` under `disallowed_claims`.

Full G4 status across n3..n7: EARNED for per-rung named coordinate-family bookkeeping at `scratch_diagnostic` ceiling; n3/n6/n7 are equal-degree boundary rows, n4/n5 are the unequal-degree separation discriminator rows. Ceiling remains `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`; not canonical, not formal admission, not trend/scaling evidence, and not geo-bracketing or axis-level evidence.

Conclusion: n6/n7 G4 rows EARNED (as boundary rows).

## Builder-extension addendum: n8 coordinate row

Addendum date: 2026-06-11.
Builder note, not fresh audit replacement: the prior verdicts and addenda above stand. The n8 row has been added and rerun, but remains pending re-audit.

The extension computes the same named coordinate family on the committed n8 per-site shell export:

- n8 source: `system_v6/sims/stage_lifted_spinor_shell_n8_v0/results/stage_lifted_spinor_shell_n8_v0_jax_results.json`
- n8 source sha256: `f7ded95c7fb77973cfb93d8ee329d43e4ec70ffa21c0966b03f3b4cec2fe4c1d`
- Fields read: `rows.P2_support_object.sites`, `rows.P2_support_object.edges`, and `rows.P8_shell_leakage.aggregate_leakage`

Rows added:

- `n8.network_shell_coordinates.degree_weighted_shell_centroid_spread_v0`: `z_bar=0.0`, `sigma_z=0.661437827766`
- `n8.network_shell_coordinates.degree_squared_shell_centroid_v0`: `z_bar=0.0`
- `n8.network_shell_coordinates.edge_gradient_shell_energy_v0`: `edge_mean_delta_z_squared=0.742674300518`, `edge_count=16`
- `n8.network_shell_coordinates.unweighted_shell_mean_spread_alt_v0`: `z_bar=0.0`, `sigma_z=0.661437827766`
- `n8.julia_load_bearing_rows.frechet_karcher_shell_mean_degree_weighted_v0`: `frechet_karcher_z_bar=0.000008777222`, `chart_space_weighted_z_bar=0.0`, `abs_divergence=0.000008777222`, `fired=true`

Controls at n8:

- `collapsed_shell`: fired
- `permuted_site_labels`: fired
- `moved_single_site`: fired
- `degenerate_unweighted_conflation`: fired as an equal-degree boundary row, not as an unequal-degree Z3 separation row

Boundary note:

- The committed n8 support graph is degree-regular under this packet's existing `support_graph_degree` rule: 8 nodes, 16 undirected edges, degree sequence `[4,4,4,4,4,4,4,4]`.
- Therefore degree-weighted and unweighted means intentionally coincide for n8. A rung-local weighted-vs-unweighted separation would be false for these raw degree values.
- The envelope keeps `DEGENERATE_DISCRIMINATOR_LABELS=("n4","n5")` and extends `EQUAL_DEGREE_BOUNDARY_LABELS=("n3","n6","n7","n8")`. This preserves the named coordinate family without inventing a directed-degree coordinate or widening the claim.

Envelope change:

- The source whitelist now includes the n8 JAX result above.
- Allowed coordinate/control claims now cover per-rung n3/n4/n5/n6/n7/n8 rows for this named coordinate family.
- Trend and scaling claims remain disallowed.

Fresh reruns/checks:

- `julia system_v6/sims/geo_network_shell_coordinate_v0/geo_network_shell_coordinate_v0_julia.jl` -> `ok:true`
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_network_shell_coordinate_v0/geo_network_shell_coordinate_v0_jax.py` -> `ok:true`
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_network_shell_coordinate_v0/geo_network_shell_coordinate_v0_pytorch.py` -> `ok:true`
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_network_shell_coordinate_v0/geo_network_shell_coordinate_v0_envelope.py` -> `ok:true`
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_network_shell_coordinate_v0/geo_network_shell_coordinate_v0_envelope.py --validate-only` -> `ok:true`
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_network_shell_coordinate_v0/results/geo_network_shell_coordinate_v0_envelope_results.json` -> `ok:true`

Stability note:

- Existing n3/n4/n5/n6/n7 row objects stayed byte-equivalent to `HEAD` in Julia, JAX, and PyTorch result JSONs after `jq -S` normalization.
- `stage_lifted_spinor_shell_n8_v0` was read only; it was not edited, staged, or committed by this extension.

Full G4 status across n3..n8: EARNED for per-rung named coordinate-family bookkeeping at `scratch_diagnostic` ceiling; n3/n6/n7/n8 are equal-degree boundary rows, n4/n5 are the unequal-degree separation discriminator rows. Ceiling remains `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`; not canonical, not formal admission, not trend/scaling evidence, and not geo-bracketing or axis-level evidence.

## Focused re-audit addendum: n8 extension row only

Addendum date: 2026-06-11.
Scope: read-only re-audit of the new n8 rows only. All prior verdicts and addenda above stand.

Hash/source binding checked:

- Recomputed `HEAD` sha256 for `system_v6/sims/stage_lifted_spinor_shell_n8_v0/results/stage_lifted_spinor_shell_n8_v0_jax_results.json`: `f7ded95c7fb77973cfb93d8ee329d43e4ec70ffa21c0966b03f3b4cec2fe4c1d`, matching the packet n8 source receipt.
- The envelope validate-only gate returned `ok:true`, `errors:[]`, `declared_mode:"all_three_full_sims"`, `require_pytorch:true`, and read-only source list including n3/n4/n5/n6/n7/n8.
- `validate_three_engine_sim_result.py --require-pytorch --strict-source-backed ...geo_network_shell_coordinate_v0_envelope_results.json` returned `{"ok": true}` with exit 0.

n8 degree regularity and boundary disposition checked:

```text
node_count=8
edge_count=16
degree_sequence=[4,4,4,4,4,4,4,4]
```

Because every support-graph degree is 4, degree-weighted and unweighted means are algebraically identical for this row. The stored `degenerate_unweighted_conflation` row says `degenerate_witness_applicable=false`, `fired=true`, `packet_discriminator_source="n4"`, with reason: all support-graph degrees are equal, so degree weighting intentionally collapses to the unweighted alternative. That is the correct boundary disposition; it does not manufacture a weighted/unweighted separation.

Coordinate-family values checked from the committed per-site z values:

```text
z=[0.939692620786,0.766044443119,0.5,0.173648177667,-0.173648177667,-0.5,-0.766044443119,-0.939692620786]
weighted z_bar=0.000000000000
weighted sigma_z=0.661437827766
stored degree_weighted_shell_centroid_spread_v0={z_bar:0.0, sigma_z:0.661437827766, weight_rule:"support_graph_degree"}
stored unweighted_shell_mean_spread_alt_v0={z_bar:0.0, sigma_z:0.661437827766}
```

The n8 controls are present and fired: `collapsed_shell`, `permuted_site_labels`, `moved_single_site`, and `degenerate_unweighted_conflation` as the equal-degree boundary row.

Byte-stability checked:

```text
Julia rows n3/n4/n5/n6/n7: MATCH_HEAD
JAX rows n3/n4/n5/n6/n7: MATCH_HEAD
PyTorch rows n3/n4/n5/n6/n7: MATCH_HEAD
Envelope network_coordinate_rows n3/n4/n5/n6/n7: MATCH_HEAD
```

Conclusion: n8 extension rows EARNED; full G4 status across n3..n8 is EARNED for per-rung named coordinate-family bookkeeping, with n3/n6/n7/n8 as equal-degree boundary rows and n4/n5 as unequal-degree discriminator rows; ceiling remains `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`, not canonical, not formal admission, not cross-run parity, and not geo-bracketing or axis-level evidence.
