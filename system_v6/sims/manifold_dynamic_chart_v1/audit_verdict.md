# Independent audit verdict -- manifold_dynamic_chart_v1

Auditor: independent Codex cross-backend audit.
Audit mode: read-only packet audit except this audit_verdict.md file.
Freshness: fresh source recomputation and structural-null check, with builder claim text visible in the audit request and binding v0/panel-10 receipts read as required context.
Standards: system_v6/receipts/audit_standards_codex_v1.md; v0 audit at eb51339c0; panel 10 at 3ff556c10.

## Bottom line

VERDICT: ACCEPTED-PARTIAL, NOT STRUCTURAL-NULL, NOT ADMITTED.

manifold_dynamic_chart_v1 earned an honest partial result: the sweep ran, the criterion was real, no grid corner quietly satisfied the full rule, and the best partial row genuinely beat the majority baseline while passing the candidate negative controls. It did not earn cross-family stability, and the committed 33-cell carrier is not vertex-transitive under generator-label-preserving automorphisms. Therefore the panel-10 honest-null condition does not fire: the partial/null is not an impossibility-in-principle result on this carrier.

Claim ceiling remains:

```text
scratch_diagnostic_axis0_experiment_v1_no_admission
```

No Axis-0 admission, bridge admission, physics claim, canonical manifold promotion, or final substrate decision is earned by this packet.

## Citation rule

Safe citation:

```text
manifold_dynamic_chart_v1 is an honest scratch diagnostic Axis-0 experiment v1: no grid row earned the full criterion; the best partial row was amplitude_kicks/weak/shell_boundary/T=12/recovery_return_time, which beat majority and passed candidate negative controls but failed cross-family stability. A fresh structural-null check found the committed generator-labeled 33-cell carrier is not vertex-transitive, with singleton label-preserving orbits, so the null is not a symmetry-impossibility result. Claim ceiling: scratch_diagnostic_axis0_experiment_v1_no_admission.
```

Required caveats when citing:

- If citing the best partial row, also say it failed stability across two or more perturbation families.
- If citing the null/partial, also say the carrier was not vertex-transitive, so separation was not ruled out in principle by symmetry.
- Do not cite this as Axis-0 admission, substrate closure, bridge evidence, physics evidence, or canonical manifold evidence.

## Tooth 1 -- Best partial and criterion logic

Fresh recomputation from `manifold_dynamic_chart_v1_common.py` produced 576 sweep rows:

- 324 ran rows with `FAILS_CRITERION`.
- 252 refused rows with `REFUSED_DEAD_FAMILY_OR_TARGET`.
- 0 earned rows.

The recomputed first/best partial corner is:

```text
family: amplitude_kicks
strength: weak
target: shell_boundary
window_T: 12
classifier: recovery_return_time
classes: BOUNDARY=9, RETURN=24
majority baseline: 24/33 = 0.727272727273
best non-identity feature: z_sign
feature accuracy: 28/33 = 0.848484848485
negative_controls_fail_candidate: true
stable_family_count: 1
stable_family_ids: [amplitude_kicks]
failure_reasons: [not_stable_across_2_or_more_perturbation_families]
criterion_verdict: FAILS_CRITERION
```

The exact best-partial separation pattern was:

```text
BOUNDARY: [4, 11, 12, 14, 15, 19, 23, 26, 27]
RETURN: [0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 13, 16, 17, 18, 20, 21, 22, 24, 25, 28, 29, 30, 31, 32]
```

The failed stability row is the required same-corner comparison across perturbation families at `(weak, shell_boundary, T=12, recovery_return_time)`. Only `amplitude_kicks` carried the same stable feature; the group did not reach two families. The other family rows were not qualifying cross-family support:

- `dephasing_kicks`: did not beat majority; failed majority and stability.
- `generator_biased_kicks`: beat majority but negative controls passed a candidate; failed stability and controls.
- `unitary_kicks`: beat majority but negative controls passed a candidate; failed stability and controls.

Three spot checks agreed with the criterion logic:

- `unitary_kicks/weak/shell_boundary/T=12/recovery_return_time`: beat majority but failed stability and controls; correctly `FAILS_CRITERION`.
- `dephasing_kicks/weak/single_cell/T=4/v0_divergence`: refused as dead/no-bite; correctly `REFUSED_DEAD_FAMILY_OR_TARGET`.
- `generator_biased_kicks/medium/neighborhood/T=16/baseline_growth_rate_sign`: ran but did not beat majority and did not stabilize; correctly `FAILS_CRITERION`.

I found no corner that quietly passes the full criterion.

## Tooth 2 -- Panel-10 adjudication

Panel 10 pre-registered three expectations before v1 results were read:

- entropy/purity-touching kicks should separate if separation is possible;
- unitary-kick rows should reproduce near-constancy/coarse behavior;
- window length should matter.

Adjudication:

- Direction-consistent: `amplitude_kicks` produced the best partial separation. That is the expected direction for entropy/purity-touching perturbations.
- Not complete: the amplitude result failed cross-family stability, so it is informative but not earned separation.
- Unitary rows remained non-decisive/coarse. They produced near-constant or broad one-sided class distributions and failed the full criterion through stability/control gates.
- Window length mattered: the recomputed grid showed changed distribution diversity and negative-control behavior between T=4 and T=8/12/16, but no T window created a fully stable cross-family result.

Panel 10 is therefore partially confirmed as a diagnostic guide, not as an admission result.

## Tooth 3 -- Structural-null check

I ran a fresh generator-label-preserving automorphism check on the committed 33-cell carrier. The automorphism condition used was:

```text
p(F_g(v)) = F_g(p(v)) for every state v and every named generator g
```

The invariant refinement was decisive:

```text
state_count: 33
generators: [Se_Funnel_L, Ni_Pit_L, Ni_Source_R, Ne_Spiral_R, D_z, R_x]
round 1 classes: 12
round 2 classes: 33
round 3 classes: 33 stable
label-preserving orbit structure: 33 singleton orbits
vertex_transitive: false
```

Because the generator-labeled invariant partition refines to singletons, every label-preserving automorphism orbit is singleton. The graph is not vertex-transitive. The best-partial `BOUNDARY`/`RETURN` split is therefore a union of singleton orbits only in the trivial sense; symmetry neither forces nor explains the observed split.

Consequence: the panel-10 honest-null criterion does not conclude structural impossibility. v1 cannot be called complete-with-answer on the basis that the carrier forbids separation. The v2-or-conclude decision remains an owner/substrate decision, not a symmetry-null decision.

## Tooth 4 -- Gates and controls

The packet-level gates and controls checked out:

- v0 regression reproduced exactly: `SPREAD=32`, `DAMP=1`.
- Density validity, entropy source, full grid, classifier, window, shell, and j/k gates passed.
- Perturbation bite was reported per family, including refused/dead rows instead of hidden skips.
- Candidate controls fired as required for the best partial row: identity dynamics, scrambled adjacency, label permutation, and dropped-half controls did not beat their majority baselines for that row.
- Dead families/targets were represented as refused rows, not promoted rows.

The family bite summary was nontrivial overall:

- `amplitude_kicks`: max changed initial states 10; refused rows 48.
- `dephasing_kicks`: max changed initial states 3; refused rows 96.
- `generator_biased_kicks`: max changed initial states 22; refused rows 48.
- `unitary_kicks`: max changed initial states 27; refused rows 60.

## Tooth 5 -- Identity leak, G.2a, and hash hygiene

The packet correctly reports identity leak risk in the standards-codex sense: identity-inclusive fields can trivially leak cell identity. The candidate logic excludes identity-like fields (`cell_id`, `state_id`, start/current cell, coordinates, and coordinate-scaled variants). The best partial uses `z_sign`, has feature cardinality 3, and is not identity-like.

The identity-excluded best coarse predictor can still reach 32/33 accuracy elsewhere, so it must not be promoted as a discovered identity-free manifold law. It is only a bounded diagnostic ceiling.

G.2a/builder-audit boundary is satisfied by this file: the builder packet did not write an audit verdict, and this verdict declares independent read-only audit status in its header.

The duplicate PID hygiene note did not reveal committed-result incoherence. The result envelope, trajectory sidecar, and direct file hash agreed on:

```text
manifold_dynamic_chart_v1_trajectory_artifact.json
sha256: 4cfe06e0c076840d10f3a2183392101afcce22fa0010d16d8e67609249b8f88e
sha_verified: true
```

Cross-backend internal hashes were coherent:

```text
cells_by_t_sha256: 8b624e5a... identical across JAX, Julia, and PyTorch
entropy_by_t_sha256: 8af30b3c... identical across JAX, Julia, and PyTorch
trajectory_signature_agreement: true
entropy_signature_agreement: true
```

I found no evidence that the committed result JSON represents a mixed-writer or hash-incoherent state.

## Verification commands

Fresh checks run in this audit:

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
# imported manifold_dynamic_chart_v1_common.py and recomputed build_sweep_rows()
PY
```

Result: 576 rows recomputed; 0 earned; best partial and spot checks matched the claims above.

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -u - <<'PY'
# computed generator-label-preserving automorphism invariant refinement
PY
```

Result: not vertex-transitive; 33 singleton label-preserving orbits.

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
# imported validate_manifold_dynamic_chart_v1.validate_payload without writing validator output
PY
```

Result: `ok: true`, no validator errors.

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/manifold_dynamic_chart_v1/results/manifold_dynamic_chart_v1_envelope_results.json
```

Result: `ok: true`.

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/manifold_dynamic_chart_v1/tests
```

Result: `5 passed`.

```bash
shasum -a 256 system_v6/sims/manifold_dynamic_chart_v1/results/manifold_dynamic_chart_v1_trajectory_artifact.json
cat system_v6/sims/manifold_dynamic_chart_v1/results/manifold_dynamic_chart_v1_trajectory_artifact.sha256
```

Result: file hash, sidecar hash, and envelope hash agreed.

## What v1 earned

v1 earned:

- honest execution of the expanded grid;
- correct criterion enforcement;
- exact v0 regression reproduction;
- an informative amplitude-kick partial;
- panel-10 directional support for entropy/purity-touching perturbations;
- a negative answer to the structural-null/vertex-transitivity hypothesis;
- coherent cross-backend and hash hygiene for the committed result packet.

v1 did not earn:

- a full separating row;
- stability across two or more perturbation families;
- an impossibility-in-principle null;
- substrate closure;
- Axis-0, bridge, physics, or manifold admission.

Decision implication: if the owner wants to continue, v2 remains live and should target the failed stability/control axis rather than treating the carrier as symmetry-forbidden. If the owner wants to stop, the honest stop reason is "expanded chart-grid diagnostic produced only a bounded partial," not "the carrier is vertex-transitive and separation is impossible."
