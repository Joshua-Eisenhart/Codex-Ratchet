# Audit Verdict: gcm_5q_freeze_and_cuts_v0

Bottom line: GENUINE.

The 5Q freeze/cut-states packet passes the requested falsifiers under the declared ceiling:
`scratch_diagnostic_5q_freeze_cut_attachment_surface_carrier_pins_relative`.

COMMIT_READY: yes.

Audit timestamp: 2026-06-13T06:18:47Z

## Scope

- Audited packet: `system_v6/sims/gcm_5q_freeze_and_cuts_v0/`
- Interpreter: `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`
- Direct repo mutation boundary: no git add/commit; write-producing validator/build/test reruns were verified in `/tmp/gcm5q_audit.ZjH30X/Codex-Ratchet`.
- Direct repo checks were read-only except this verdict file.

## Falsifiers

### 1. Validator and substrate helper

PASS.

Evidence:

- `/tmp` rerun of `gcm_5q_freeze_and_cuts_v0_common.py`: `ok: true`, cut count `15`, hash pair count `8205`, sample cut pair count `120`, object id `gcm5qobj_590b8a0be12324a14bb4ac530486a19e`.
- `/tmp` rerun of `validate_gcm_5q_freeze_and_cuts_v0.py`: `ok: true`, `errors: []`.
- Direct repo read-only substrate helper:
  `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/gcm_substrate_check.py system_v6/sims/gcm_5q_freeze_and_cuts_v0/results/gcm_5q_freeze_and_cuts_v0_results.json --registry system_v6/sims/gcm_4q_freeze_and_cuts_v0/results/gcm_4q_freeze_and_cuts_v0_registry.json`
  returned `ok: true`, `errors: []`, `error_codes: []`, registry body sha256 `bf92c850a2880e26011080c900879cf729f8394ffc2e5d00bf1f70ed786020de`.
- `/tmp` pytest rerun: `5 passed in 31.28s`.

### 2. Lean storage honest

PASS.

Evidence:

- `find system_v6/sims/gcm_5q_freeze_and_cuts_v0 -type f -size +50M -print` returned no files.
- Filesystem size check found largest packet file `results/gcm_5q_freeze_and_cuts_v0_results.json` at about 13 MB; full packet about 14 MB.
- Packet `lean_storage_policy.full_all_survivor_cut_matrices_stored` is `False`.
- Full-matrix leak scan over survivor hash rows found `0` hash-row cuts containing `rho_left` or `rho_right`.
- Stored sample matrix rows are capped at 8 labels x 15 cuts = 120 sample cut pairs, not all 547 survivors x 15 cuts.

### 3. Sample reduced matrices recompute from source and are mutation-sensitive

PASS.

Evidence:

- Source recompute against `gcm_constraint_carve_5q_v0` state artifacts checked `120` sample cut pairs with `mismatches: []` and `sample_recompute_pass: true`.
- Mutation control on sample `GHZ5`, cut `q0|q1234`, changed `rho_left` hash from expected `13b73c7af1c47042268a5a20f0ff465ee33adee6785b93bd572b4ca8c1ac017a` to mutated `e093de3a89c1a734327d03172516d1fb44bb8603498636429fdfe41faf7e243e`; `mutation_detected: true`.
- Additional non-sample survivor hash recompute probes matched source for:
  `4q_lift_0 / q0|q1234`, `4q_lift_273 / q03|q124`, and `locally_rotated_generalized_GHZ5_anchor / q34|q012`.

### 4. Survivor/class/region counts and cut-state map are real

PASS.

Evidence:

- 5Q carve source count matrix covers `556` candidates: `547` survivors and `9` killed rows.
- C1/C2/C3 failure combinations from the source matrix:
  `()` = 547 survivors, `('C2', 'C3')` = 4, `('C3',)` = 3, `('C1',)` = 1, `('C2',)` = 1.
- Source quotient classes are exactly `9`: `Q0` through `Q8`, with member counts `[68, 68, 68, 68, 68, 68, 68, 68, 3]`.
- Packet/registry counts agree: candidate count `556`, survivor count `547`, killed count `9`, class count `9`, region count `9`, product-lift survivors `546`, five-partite entangled survivor count `1`.
- Cut-state map completeness scan found `547` unique survivor ids, each with all `15` cuts, for `8205` unique survivor/cut pairs. Empty hashes: `0`.
- `cut_state_available=true` is backed by the complete per-survivor/per-cut hash map plus source recomputation functions, not just a flag.

### 5. Genuine substrate consumption by lineage against frozen registry

PASS.

Evidence:

- Direct substrate helper against the frozen 4Q registry returned `ok: true`.
- Packet controls include positive 4Q substrate check `ok: true`.
- Negative controls reject lineage removal and stale 4Q lineage:
  lineage-free rejected with `GCM_LINEAGE_CONSUMPTION_MISSING`, `GCM2Q_LINEAGE_CONSUMPTION_MISSING`, `GCM3Q_LINEAGE_CONSUMPTION_MISSING`, `GCM4Q_LINEAGE_CONSUMPTION_MISSING`;
  stale 4Q lineage rejected with `GCM4Q_LINEAGE_REGISTRY_BODY_SHA256_MISMATCH`.
- Lineage cites the pinned object ids:
  `gcmobj_a40e54e13cec01466c9d675028b3574b`,
  `gcm2qobj_715e9424ea66468243108751fb59395f`,
  `gcm3qobj_492a4d00823507fd9ae8a1b3e4d0acb5`,
  `gcm4qobj_64fa5326aa89eae836e75e6c71fc8cdc`.

### 6. Ceiling honest

PASS.

Evidence:

- `classification`: `scratch_diagnostic`
- `claim_ceiling`: `scratch_diagnostic_5q_freeze_cut_attachment_surface_carrier_pins_relative`
- `carrier_and_pins_relative`: `true`
- `not_THE_manifold`: `true`
- `promotion_allowed`: `false`
- `formal_admission_allowed`: `false`
- Blocked consumers include `formal_admission`, `canonical_manifold_claim`, `axis_or_bridge_claim`, `physics_claim`, `full_all_survivor_reduced_matrix_blob_claim`, and `SLOCC_or_five_party_entanglement_classification_claim`.

## Overall

Overall verdict: GENUINE.

Ceiling: scratch diagnostic only; carrier/pins-relative 5Q freeze plus lean recomputable cut-state attachment surface. This is not manifold admission, not formal admission, not a physics claim, and not a full all-survivor reduced-matrix blob.

COMMIT_READY: yes.
