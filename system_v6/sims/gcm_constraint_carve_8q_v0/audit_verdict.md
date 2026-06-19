# Audit Verdict - `gcm_constraint_carve_8q_v0`

Bottom line: `GENUINE_WITH_CAVEATS`.

This is a genuine LEAN, state-fingerprinted 8Q count fixture. The caveat is the intended lean ceiling: only the 13 sampled full `256x256` matrices are stored and recomputable as full-rho rows from stored sample data; the all-candidate surface is hashes plus the full C1/C2/C3 constraint matrix, not full matrices for all candidates.

Admissible ceiling: `scratch_diagnostic_lean_state_fingerprinted_8q_count_fixture`, carrier-and-pins-relative. No manifold/admission/bridge/axis/physics/SLOCC/eight-party-entanglement-classification claim is admitted.

Read-only audit note: I did not run the builder, validator script, or pytest directly because those paths write result/validator files. I used `write=False` recomputation, direct stored-payload validation, file-size checks, and helper preflight. No repo write was made except this verdict file.

## Falsifier 1 - LEAN STORAGE HONEST

PASS.

Evidence:
- `du -sh system_v6/sims/gcm_constraint_carve_8q_v0` reports `10M`.
- `find system_v6/sims/gcm_constraint_carve_8q_v0 -type f -size +50M -print` returned no files.
- Largest files:
  - sample matrix file: `9,030,018` bytes.
  - main result file: `1,848,733` bytes.
  - common source: `59,434` bytes.
- Stored validator payload reports `dir_size_bytes: 10952435`, `oversize_files_over_50mb: []`, `result_size_bytes: 1848733`, `sample_size_bytes: 9030018`, `ok: true`.
- Main packet flags:
  - `main_packet_stores_every_candidate_full_rho: false`
  - `main_packet_stores_hash_per_candidate: true`
  - `sample_file_stores_bounded_full_matrices: true`
  - `no_blob_regression: true`
- Main result has 559 `candidate_fingerprints`, 559 `constraint_matrix` rows, and 559 `kill_ledger` rows. The full `rho_ABCDEFGH` matrix payload appears in the bounded sample file, not in the all-candidate main packet surfaces.
- The sample file stores 13 full `256x256` matrices: GHZ8, W8, cluster, five survivor spotchecks, and five kill spotchecks.

5MB to 50MB wall judgment: justified. The main result remains under 2MB. The size jump comes from the bounded sample moving from 7Q `128x128` matrices to 8Q `256x256` matrices. The committed 7Q v1 lean packet is about `4.0M`, with a `2,252,052` byte sample file; 8Q is about `10M`, with a `9,030,018` byte sample file. That is the expected fourfold matrix-size jump for the same 13-row sample, not a return to the 7Q v0 1.1GB all-candidate full-rho blob.

## Falsifier 2 - SAMPLE GENUINELY RECOMPUTABLE

PASS.

Evidence from independent `write=False` recomputation:
- `GHZ8` candidate `549`: stored and recomputed content id, sha, exact matrix JSON, and constraints match; pass/fail is `C1=true, C2=false, C3=false`.
- `W8` candidate `550`: stored and recomputed content id, sha, exact matrix JSON, and constraints match; pass/fail is `C1=true, C2=true, C3=false`.
- `cluster_linear_8` candidate `551`: stored and recomputed content id, sha, exact matrix JSON, and constraints match; pass/fail is `C1=true, C2=false, C3=false`.
- Survivor spotcheck `7q_lift_0` candidate `0`: stored and recomputed content id, sha, exact matrix JSON, and constraints match; pass/fail is `C1=true, C2=true, C3=true`.
- Kill spotcheck `invalid_trace_anchor` candidate `555`: stored and recomputed content id, sha, exact matrix JSON, and constraints match; pass/fail is `C1=false, C2=true, C3=true`.
- Recomputed sample reports `spotcheck_recompute.all_match: true`.

Mutation sensitivity:
- In-memory mutation of GHZ8 sample cell `[0][0][0] += 0.25` changed the full-rho sha from `751e816cbe306b48d8ce8d3aaee90f0f9fede07ac5d42ed2c971871230e8a547` to `f63fb0c2606c652bec62167abed0ebe99a2845c132387573c54515bb2a53b201`.
- The mutated content id no longer matches the stored `rhoabcdefgh_751e816cbe306b48d8ce8d3a` id.
- Source recompute injection control is also red: forbidden `terrain`, `atlas`, and `Se` tokens are caught with `GCM8Q_SOURCE_RECOMPUTE_FORBIDDEN_TOKEN`.

## Falsifier 3 - COUNTS REAL

PASS.

Counts computed from the full C1/C2/C3 matrix:
- Candidate rows: `559`.
- Candidate construction: `549` 7Q survivor product lifts plus `10` 8Q anchors/controls.
- Survivors from `all(C1,C2,C3)`: `550`.
- Killed rows: `9`.
- Quotient classes: `9`.
- Quotient member total: `550`.
- Survivor family counts: `549` `7q_survivor_product_lift`, `1` `entangled_boundary_anchor`.
- Eight-partite entangled survivor count: `1`.
- Kill counts by constraint, allowing multi-fail rows: `C1=1`, `C2=5`, `C3=7`.

Class sanity:
- Eight quotient classes have `68` product-lift members each.
- Final class `Q8` has `6` members: `5` product lifts plus `1` entangled boundary anchor.

Ladder sanity:
- 7Q v1 is `558 -> 549 / 9`.
- 8Q v0 is `559 -> 550 / 9`.
- The +1 survivor is consistent with the added 8Q anchor/control set leaving one entangled boundary anchor alive, while all 549 7Q survivors lift through `rho_ABCDEFG tensor |0><0|_H`.

The stored `first_failed_constraint_display_only` field agrees as a crosscheck, but the audit count above used the actual C1/C2/C3 pass booleans, not the display label.

## Falsifier 4 - SUBSTRATE CONSUMED

PASS.

Evidence:
- `gcm_lineage` carries the 1Q object id `gcmobj_a40e54e13cec01466c9d675028b3574b`, 1Q registry hash `0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed`, 2Q object id `gcm2qobj_715e9424ea66468243108751fb59395f`, 2Q registry hash `57c8b47b0c60867f9d58969803e905fb905e27a2915641121583175e32c598ac`, 3Q object id `gcm3qobj_492a4d00823507fd9ae8a1b3e4d0acb5`, and 3Q registry hash `623785e4ec0f41bd8cd040c44ceefbc5f1bd3c14d3257487a82afc0a89439fb0`.
- Hardened substrate checks are green for 1Q, 2Q, 3Q, and 7Q. The 7Q source check reports `survivor_count: 549`, `quotient_class_count: 9`, sha `778596ff25cf80c8494d3cee8c67e69d4def1d350e64394ec713d887b2197ae5`.
- Lineage-free and stale-lineage negatives stay red for 1Q through 7Q with error codes.
- Cross-rung rows show all `549` 7Q survivors have one 8Q product lift, and `Tr_H(rho_ABCDEFGH)` reproduces the 7Q source state for `549` rows with `max_abs_delta_TrH_vs_7q_rho: 0.0`.
- 8Q feedstock is consumed by hash, not rebuilt: `geo_s1_scaling_stress_678q_exact_v0` pin `e4da6f5578731c0017ca6140646e893f84b296db78837413d88f0012f86721e8`, `stage_lifted_spinor_shell_n8_v0` pin `6330ff1ce5b81363666b35caafee6a451f825ebab8fef908d375635bf71b09b2`, and `Cl(16)` is named as feedstock/capability floor.

## Falsifier 5 - CEILING HONEST

PASS.

Evidence:
- Result fields: `classification: scratch_diagnostic`, `promotion_allowed: false`, `formal_admission_allowed: false`, `carrier_and_pins_relative: true`, `not_THE_manifold: true`.
- `claim_ceiling` is `scratch_diagnostic_lean_state_fingerprinted_8q_count_fixture`.
- `allowed_claims` are limited to the lean 8Q count fixture, all-candidate C1/C2/C3 rows, sampled full-rho spotchecks, and 7Q-to-8Q product embedding / `Tr_H` retraction fixture.
- `blocked_consumers` explicitly include formal admission, canonical manifold claim, geometry claim, axis or bridge claim, physics claim, SLOCC or eight-party entanglement classification, 8Q registry freeze claim, and reduced-cut-state artifact claim.
- CKW wording is narrow: sampled pure-row focus-qubit inequality only; `residual_8_tangle_claimed: false`, `higher_party_residual_allocation_claimed: false`, and no eight-party classification claim.

No overclaim found in the packet surface I checked.

## Checks Run

- File size scan with `du`, `find -size +50M`, and `stat`.
- Stored result/sample inspection with `jq`.
- `write=False` recomputation using `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`.
- Direct `validate_payload(..., require_helper_preflight=True)` on stored result and sample: `ok: true`, no errors.
- Helper preflight with `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/helper_process_audit.py --strict`: `all_pass: true`, `helper_process_count: 0`.
- In-memory mutation sensitivity check on the GHZ8 sample matrix.

## Overall

Overall verdict: `GENUINE_WITH_CAVEATS`.

The packet is admissible as a scratch diagnostic lean 8Q count fixture. It is not admissible as full all-candidate full-rho evidence, a manifold/admission artifact, an 8Q registry freeze, or any geometry/axis/bridge/physics/classification claim.
