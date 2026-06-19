# Independent Audit Verdict - gcm_constraint_carve_7q_v1

Bottom line: `ACCEPTED_AS_LEAN_SCRATCH_DIAGNOSTIC_WITH_LIMITS`.

The v1 packet fixes the 7Q scale-wall failure: the package is lean, the full
C1/C2/C3 pass-fail matrix exists for all 558 candidates, and the bounded sample
matrices are genuine enough to audit the stored hash/fingerprint discipline and
sample C-row computation. The claim ceiling is only
`scratch_diagnostic_lean_state_fingerprinted_7q_count_fixture`.

It is not formal admission, not canonical, not THE manifold, not a geometry,
axis, bridge, physics, SLOCC, seven-party-entanglement-classification, 7Q
registry-freeze, or reduced-cut-state artifact.

## Verdict

Pass, with the lean-model caveat made load-bearing:

- Main result: hash-per-candidate plus full C1/C2/C3 rows for all candidates.
- Sample result: 13 full 128x128 rho matrices only.
- Auditable full-state recomputation: sample only.
- Non-sample candidates: auditable as fingerprints, full C rows, counts, and
  lineage/hash discipline, not as locally recomputed full rho states.

This is the intended scale-wall tradeoff. Do not cite it as if every candidate's
full 128x128 matrix is stored or locally recomputed by the audit.

## Checks Run

Fresh read-only checks:

```text
find system_v6/sims/gcm_constraint_carve_7q_v1 -type f -size +50M -print
```

Result: no paths.

```text
du/file-size scan over system_v6/sims/gcm_constraint_carve_7q_v1
```

Result: total file-size sum `4112689` bytes. Largest files are
`results/gcm_constraint_carve_7q_v1_sample_matrices.json` at about 2.1M and
`results/gcm_constraint_carve_7q_v1_results.json` at about 1.7M.

```text
validate_payload(packet, sample, require_helper_preflight=True)
```

Result: `error_count=0`.

```text
make helper-process-audit-strict
```

Result: `all_pass=true`, `helper_process_count=0`.

The builder and validator entrypoints were not rerun because they write result
files. The audit was read-only except for this verdict file.

## Lean Storage Integrity

Pass.

- Candidate count: `558`.
- Candidate fingerprints: `558`.
- Constraint matrix rows: `558`.
- Kill ledger rows: `558`.
- Survivor count: `549`.
- Killed count: `9`.
- Quotient class count: `9`.
- Survivor family counts: `548` `6q_survivor_product_lift`, `1`
  `entangled_boundary_anchor`.
- Kill counts by constraint: `C1=1`, `C2=5`, `C3=7`.

The audit recomputed the sample rho content hashes from the stored JSON content
using the packet's canonical JSON hash discipline. Sample hashes match the
sample rows and the main candidate fingerprint rows. A local mutation flip in
the copied sample rho content changed the hash, so the content ids are
mutation-sensitive rather than label-only.

The main packet does not store every full rho. It stores hash-only rows in
`candidate_fingerprints`, and the validator rejects forbidden full state-artifact
blob surfaces in the main packet.

## Matrix And Sample

Pass.

The full matrix is not first-failed-only. Every row has C1, C2, and C3, and
`all_failed_constraints` matches the full set of failed constraints for the row.
The display-only `first_failed_constraint_display_only` field is not used as the
audit truth source.

The sample is representative under the declared lean contract:

- Named anchors: `GHZ7`, `W7`, `cluster_linear_7`.
- Survivor spotchecks: candidate ids `0,1,2,3,4`.
- Kill spotchecks: candidate ids `551,552,554,555,556`.
- Total full sampled matrices: `13`.

For sampled rows, the audit independently parsed the stored 128x128 complex
matrices and checked shape, Hermiticity, trace, PSD/density status, hash match,
mutation-hash sensitivity, and C1/C2/C3 recomputation. The invalid trace control
at candidate `554` correctly stays C1-red with trace `1.2`.

Named sample C rows match the packet:

- `GHZ7`: C1 pass, C2 fail, C3 fail.
- `W7`: C1 pass, C2 pass, C3 fail.
- `cluster_linear_7`: C1 pass, C2 fail, C3 fail.

## Regressions And Controls

Mostly pass, with one explicit gap.

- 6Q regression: present by count/hash lineage. The 6Q source reports
  `survivor_count=548`, `quotient_class_count=9`; 7Q product lifts preserve all
  548 via `rho_ABCDEF tensor |0><0|_G`.
- 5Q regression: present by count/ceiling row:
  `survivor_count=547`, `quotient_class_count=9`.
- 4Q regression: gap. The row says `direct_rerun_by_this_packet=false` and both
  survivor/class counts are null. Do not cite this packet as having checked the
  4Q regression.
- Empty-C, cliff-overconstrained, erasure-bite, probe-scramble, and
  source-recompute-injection-red controls are present and green.
- Terrain-blind guard is clean. The injection-red control catches `terrain`,
  `atlas`, and `Se`.

## 7Q Feedstock

Pass as consumed feedstock, not as rebuilt proof.

- `geo_s1_scaling_stress_678q_exact_v0` is consumed by hash and pin. Its 7Q rows
  carry `clifford_floor=Cl(14)` and passing Cl(14) support rows.
- `stage_lifted_spinor_shell_n7_v0` is consumed by hash and pin for support,
  density quotient, entropy, and order-gap feedstock.
- The standalone `cl14_capability_probe` path and hash are recorded, but the
  packet caveat says it is capability/supporting feedstock only and this packet
  does not rebuild Cl(14).

The correct citation is "Cl(14) feedstock consumed by hash/pin", not "Cl(14)
reproved here".

## Scale And Boundary

Pass.

The scale-wall finding at commit `da1188311` says the old v0 pattern produced a
1.1G result JSON by storing every 128x128 rho. This v1 packet does not recur that
blob pattern: no file is over 50MB, total file-size sum is `4112689` bytes, and
the main result stores hashes rather than every full rho.

G.2a boundary is wired:

- `no_builder_audit_verdict=true`.
- `no_builder_audit_verdict_envelope_gate=true`.
- `builder_gates.boundary_helper_fully_used=true`.
- This audit file begins with an independent audit header, satisfying the
  post-audit boundary helper.

The packet directory is currently untracked in git. That is not a content
failure for this local audit, but it is another reason not to cite it as a
committed or admitted artifact.

## Citation Rule

Allowed citation:

> `gcm_constraint_carve_7q_v1` is a lean, state-fingerprinted, scratch-diagnostic
> 7Q count fixture: 558 candidates, full C1/C2/C3 rows for all candidates, 549
> survivors, 9 quotient classes, sampled full-rho recomputation, 6Q-to-7Q product
> embedding, and hash/pin-consumed 7Q feedstock. Full-state recomputation is
> sample-limited by design.

Forbidden citation:

> Do not cite it as formal admission, canonical manifold evidence, THE manifold,
> geometry/axis/bridge/physics evidence, SLOCC or seven-party entanglement
> classification, a 7Q registry freeze, a reduced-cut-state artifact, a rebuild
> of Cl(14), a rerun of 4Q regression, or an audit of every candidate's full
> 128x128 rho matrix.
