# Independent Audit Verdict: gcm_4q_freeze_and_cuts_v0

generated_at: 2026-06-13T04:21:07Z
auditor: independent Codex audit
audit_mode: read-only audit, except this `audit_verdict.md`
freshness_tier: TIER-2 results-available with independent recomputation
verdict: PASS_WITH_CAVEAT
accepted_ceiling: scratch_diagnostic_4q_attachment_surface_with_cut_states

## Bottom Line

The cut-state caveat is resolved for the current working-tree packet. `cut_state_available=true` is genuinely backed by stored per-cut reduced density matrices, not summary scalars: the packet contains exactly `546 * 7 = 3822` survivor/cut rows, each with `rho_left` and `rho_right`, and the sampled matrices recompute exactly by partial trace from the upstream 4Q states.

The strict-green builder claim is not fully accepted. The 4Q packet validator is green and the helper bypass holes are closed, including the 4Q-specific `GCM4Q_REGISTRY_IDENTITY_MISMATCH` and `GCM4Q_LINEAGE_CONSUMPTION_MISSING` teeth. However, fresh no-write standalone validation of the older 1Q and 2Q packets fails after the helper edit because stored/generated artifacts are stale against the modified helper. That is not a mathematical break in the 4Q cut-state evidence, but it is a real strict-regression caveat.

## Verdict

Accepted:

- `gcm_4q_object_id = gcm4qobj_64fa5326aa89eae836e75e6c71fc8cdc`
- `registry_body_sha256 = bf92c850a2880e26011080c900879cf729f8394ffc2e5d00bf1f70ed786020de`
- `classification = scratch_diagnostic`
- `promotion_allowed = false`
- `formal_admission_allowed = false`
- `cut_state_available = true`
- `stored_matrix_pair_count = 3822`
- 4Q validator, checked by importing `validate_payload()` without writing repo result files: `ok=true`, `errors=[]`

Not accepted:

- no formal admission
- no canonical manifold claim
- no axis, bridge, physics, SLOCC, G2, or Spin(7) claim
- no "all 1Q/2Q/3Q/4Q standalone validators are strict green" claim until 1Q/2Q generated artifacts are refreshed or the drift is otherwise reconciled

## Stored Reduced Matrices

Evidence path:

- `system_v6/sims/gcm_4q_freeze_and_cuts_v0/results/gcm_4q_freeze_and_cuts_v0_results.json`
- `system_v6/sims/gcm_4q_freeze_and_cuts_v0/results/gcm_4q_freeze_and_cuts_v0_registry.json`
- upstream state source: `system_v6/sims/gcm_constraint_carve_4q_v0/results/gcm_constraint_carve_4q_v0_results.json`

Fresh no-write recomputation sampled raw 4Q survivor IDs `0, 1, 17, 273, 545` across all seven cuts:

- cuts checked: `35`
- matrices checked: `70`
- all sampled matrices hermitian within tolerance
- all sampled matrices trace 1 within tolerance
- all sampled matrices PSD within tolerance
- all sampled matrix dimensions match the cut:
  - `1|234`, `2|134`, `3|124`, `4|123`: left `2x2`, right `8x8`
  - `12|34`, `13|24`, `14|23`: left `4x4`, right `4x4`
- all sampled matrices match direct partial trace from stored upstream `rho_ABCD`
- all sampled `rho_left_id` / `rho_right_id` recompute from canonical matrix JSON
- all sampled matrix IDs change under cell mutation

Full count check:

```json
{
  "1|234": 546,
  "2|134": 546,
  "3|124": 546,
  "4|123": 546,
  "12|34": 546,
  "13|24": 546,
  "14|23": 546
}
```

Total: `3822` cut rows, each with a stored `rho_left` and `rho_right` pair.

## Helper Bypass Regression

Fresh helper checks were run without repo writes. Positives pass at all four rungs. Negative/bypass tests fail red.

Object-id-only / lineage-free:

- 1Q: `GCM_LINEAGE_CONSUMPTION_MISSING`
- 2Q: `GCM_LINEAGE_CONSUMPTION_MISSING`, `GCM2Q_LINEAGE_CONSUMPTION_MISSING`
- 3Q: `GCM_LINEAGE_CONSUMPTION_MISSING`, `GCM2Q_LINEAGE_CONSUMPTION_MISSING`, `GCM3Q_LINEAGE_CONSUMPTION_MISSING`
- 4Q: `GCM_LINEAGE_CONSUMPTION_MISSING`, `GCM2Q_LINEAGE_CONSUMPTION_MISSING`, `GCM3Q_LINEAGE_CONSUMPTION_MISSING`, `GCM4Q_LINEAGE_CONSUMPTION_MISSING`

Forged registry:

- 1Q: `GCM_REGISTRY_BODY_HASH_MISMATCH`, `GCM_REGISTRY_IDENTITY_MISMATCH`
- 2Q: `GCM_REGISTRY_BODY_HASH_MISMATCH`, `GCM2Q_REGISTRY_IDENTITY_MISMATCH`
- 3Q: `GCM_REGISTRY_BODY_HASH_MISMATCH`, `GCM3Q_REGISTRY_IDENTITY_MISMATCH`
- 4Q: `GCM_REGISTRY_BODY_HASH_MISMATCH`, `GCM4Q_REGISTRY_IDENTITY_MISMATCH`

Wrong-lineage / stale hash:

- 1Q: `GCM_LINEAGE_REGISTRY_BODY_SHA256_MISMATCH`
- 2Q: `GCM2Q_LINEAGE_REGISTRY_BODY_SHA256_MISMATCH`
- 3Q: `GCM3Q_LINEAGE_REGISTRY_BODY_SHA256_MISMATCH`
- 4Q: `GCM4Q_LINEAGE_REGISTRY_BODY_SHA256_MISMATCH`

Standalone validator regression caveat:

- 1Q fresh no-write `validate_payload(...)`: `ok=false`
  - `registry drift against rebuilt output`
  - `substrate_check_helper source hash drift`
- 2Q fresh no-write `validate_payload(...)`: `ok=false`
  - `packet drift against source rebuild`
- 3Q fresh no-write `validate_payload()`: `ok=true`
- 4Q fresh no-write `validate_payload()`: `ok=true`

Adjudication: 1Q/2Q drift is stale generated-artifact/source-lock churn caused by the helper edit, not a demonstrated bypass reopening. It still blocks the strict "all standalone rung validators green" claim.

## Registry And Lineage

Registry derivation passed.

- Stored registry equals fresh `build_4q_registry(...)`.
- The 4Q object ID recomputes from the pinned 1Q/2Q/3Q identities, 4Q carve result hash, counts, survivor family counts, and seven-cut lattice.
- Mutation tests changed the object ID when mutating:
  - 4Q carve hash
  - survivor count
  - seven-cut lattice
  - 3Q registry hash
- Cross-rung lineage is narrow and green:
  - 3Q input survivor count: `545`
  - 4Q product lifts: `545`
  - every 3Q survivor has one 4Q lift: `true`
  - `Tr_D(rho_ABCD)` reproduces 3Q states: `true`
  - max delta: `0.0`
  - the single 4Q entangled anchor is not claimed as a 3Q registry embedding

## Monogamy And Entropy

Entropy fields are present for every survivor/cut row:

- `S_rho_left`
- `S_rho_right`
- `S_rho_ABCD`
- `conditional_S_left_given_right`
- `conditional_S_right_given_left`
- `mutual_I_left_right`
- `coherent_I_c_left_to_right`
- `coherent_I_c_right_to_left`
- `negativity`
- `log_negativity`

The 4-party monogamy table is accepted only at its stated narrow ceiling:

- `computed_from_stored_rho_ABCD = true`
- `pure_survivor_count_checked = 2`
- `all_focus_qubits_satisfy_ckw = true`
- CKW margin range observed: `0.0` to `0.1875`
- `residual_4_tangle_claimed = false`

This supports a stored-state focus-qubit CKW table for pure survivor rows only. It does not support residual 4-tangle, SLOCC family separation, GHZ/W/cluster classification, or any geometry/admission claim.

## Size And Composition

The size wall is handled correctly for this packet.

- result JSON size: `31,215,276` bytes
- registry JSON size: about `1.0M`
- result directory size: about `31M`
- survivor cut rows: `546`
- cut rows: `3822`
- `rho_left` arrays in survivor cut rows: `3822`
- `rho_right` arrays in survivor cut rows: `3822`
- full `rho_ABCD` arrays in survivor cut rows: `0`

The 31M payload is large because it stores reduced matrices for every survivor/cut pair, not because it embeds full 4Q joint states in every row.

## G.2a And Coordinates

G.2a is satisfied for the new 4Q packet shape:

- build card declares the boundary and `NO git add/commit`
- builder self-assessment does not claim audit authority
- `builder_gates.G_2a_idempotency_from_birth = true`
- `builder_gates.no_builder_audit_verdict = true` before this independent audit
- this verdict header declares independent/read-only audit status, preserving post-audit idempotency

Coordinates are accepted only as declared packet coordinates:

```json
{
  "layers": "4Q freeze/registry plus all bipartition cut-state attachments",
  "nesting": "1|234, 2|134, 3|124, 4|123, 12|34, 13|24, 14|23 cut lattice",
  "qubit_depth": "4Q"
}
```

They are not independent manifold chart coordinates.

## Unblock Statement

The `<=4Q tower`, `4Q geometry-delta`, and `4Q flux` lanes may now cite 4Q cut-state evidence from this packet, but only under this exact rule:

They may consume:

- the 4Q object ID and registry hash above;
- the all-seven bipartition lattice;
- stored `rho_left` and `rho_right` matrices for each survivor/cut;
- entropy-family rows derived from those stored reductions;
- the narrow pure-state focus-CKW monogamy table;
- cross-rung 3Q product-lift lineage and `Tr_D` projection rows.

They must say:

- `classification=scratch_diagnostic`
- `promotion_allowed=false`
- `formal_admission_allowed=false`
- `carrier_and_pins_relative=true`
- `not_THE_manifold=true`
- current evidence is working-tree local until committed

They must not consume this as:

- formal admission;
- canonical manifold evidence;
- bridge, axis, or physics evidence;
- SLOCC, GHZ/W/cluster separation evidence;
- G2/Spin(7)/triality/F4 evidence;
- proof that all lower-rung standalone validators are strict green.

## Commands And Checks

Fresh local commands/checks used for this verdict:

- `git status --short -- system_v6/sims/gcm_4q_freeze_and_cuts_v0 scripts/gcm_substrate_check.py`
  - observed: `scripts/gcm_substrate_check.py` modified; `system_v6/sims/gcm_4q_freeze_and_cuts_v0/` untracked
- `du -h system_v6/sims/gcm_4q_freeze_and_cuts_v0/results/* ...`
  - observed: `30M` result JSON, `1.0M` registry JSON, `31M` results directory
- no-write matrix recomputation through the sim-stack Python interpreter
  - observed: `35` cut checks, `70` matrix checks, all pass
- no-write helper bypass matrix through `gcm_substrate_check`
  - observed: positives green, object-id-only/forged/wrong-lineage negatives red
- no-write validator imports:
  - 1Q false with source-lock/generated drift
  - 2Q false with packet drift
  - 3Q true
  - 4Q true
- registry/object ID mutation probe
  - observed: object ID changes under pinned-field mutations

## Hygiene Notes

The target packet directory is untracked in this checkout, and `scripts/gcm_substrate_check.py` is already modified. No git add/commit was performed.

One explorer lane reported accidentally running the packet's full pytest file, whose final test invokes writer paths. I did not use that writer run as evidence. The controlling evidence above is from fresh no-write imports and recomputation after that report.
