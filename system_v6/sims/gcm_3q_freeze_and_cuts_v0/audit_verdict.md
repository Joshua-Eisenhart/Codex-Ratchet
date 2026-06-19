---
audit_mode: independent fresh read-only audit verdict; only authorized repo write is this file
freshness_tier: TIER-3 annotation-verify for binding prior 2Q freeze audit pattern and 3Q carve v1 audit context; target packet recomputed independently
auditor: Codex controller-local audit
audit_date: 2026-06-13
standards_codex: system_v6/receipts/audit_standards_codex_v1.md
binding_inputs: standards codex including G.2a; 2Q freeze audit bypass-hole lessons; 3Q carve v1 survivor source; nesting law cut lattice A|BC, B|AC, C|AB
write_scope: system_v6/sims/gcm_3q_freeze_and_cuts_v0/audit_verdict.md only
---

Bottom line: VERDICT = PASS / RUNTIME-QIT-FLUX GATE UNBLOCKED, with ceiling.

The audited packet is genuine for `gcm_3q_freeze_and_cuts_v0`: it freezes the
content-derived 3Q registry object `gcm3qobj_492a4d00823507fd9ae8a1b3e4d0acb5`,
stores all three bipartition cut reductions, stores the requested entropy family
per cut, and closes the helper bypass holes across 1Q, 2Q, and 3Q.

Claim ceiling: `scratch_diagnostic_3q_attachment_surface_runtime_flux_blocked`.
This audit unblocks the next runtime/QIT-flux build, but it does not promote this
packet to flux computation, formal admission, canonical manifold, bridge, or axis
claim.

Runtime-flux gate statement: with this audited, the runtime/QIT-flux family for
3Q `J_ent` / `J_cut` may consume the stored `rho_left` and `rho_right` reductions
for `A|BC`, `B|AC`, and `C|AB`, plus the per-cut entropy set:
`S_rho_left`, `S_rho_right`, `S_rho_ABC`, conditional entropies, mutual
information, coherent informations, negativity, and log-negativity. The fence is
explicit: geometric-flux is the 1Q/2Q story; this gate is for the runtime/QIT-flux
family the owner means.

## What I Checked

I did not run packet commands that rewrite result files. Instead, I imported the
packet and validator modules and ran read-only recomputation in memory, using temp
files only for forged-registry negatives.

Commands/checks run:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY' ... read-only audit recomputation ... PY
```

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY' ... validate_payload() ... PY
```

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/gcm_substrate_check.py system_v6/sims/gcm_3q_freeze_and_cuts_v0/results/gcm_3q_freeze_and_cuts_v0_results.json --registry system_v6/sims/gcm_3q_freeze_and_cuts_v0/results/gcm_3q_freeze_and_cuts_v0_registry.json
```

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/helper_process_audit.py --strict
```

Read-only validator result: `ok=true`, `error_count=0`.
Direct 3Q substrate helper result: `ok=true`, no error codes.
Helper-process strict audit: `all_pass=true`, helper process count `0`.

## Helper Extension

All bypass tests I ran were red as desired:

| Test | Result | Key error code(s) |
|---|---:|---|
| 1Q object-id-only | fail | `GCM_LINEAGE_REGISTRY_BODY_SHA256_MISSING`, `GCM_LINEAGE_CONSUMPTION_MISSING` |
| 1Q self-consistent forged registry | fail | `GCM_REGISTRY_IDENTITY_MISMATCH`, `GCM_LINEAGE_REGISTRY_BODY_SHA256_MISMATCH` |
| 2Q object-id-only | fail | `GCM2Q_LINEAGE_REGISTRY_BODY_SHA256_MISMATCH`, `GCM2Q_LINEAGE_CONSUMPTION_MISSING` |
| 2Q self-consistent forged registry | fail | `GCM2Q_REGISTRY_IDENTITY_MISMATCH`, `GCM2Q_LINEAGE_REGISTRY_BODY_SHA256_MISMATCH` |
| 3Q object-id-only | fail | `GCM3Q_LINEAGE_REGISTRY_BODY_SHA256_MISMATCH`, `GCM3Q_LINEAGE_CONSUMPTION_MISSING` |
| 3Q self-consistent forged registry | fail | `GCM3Q_REGISTRY_IDENTITY_MISMATCH`, `GCM3Q_LINEAGE_REGISTRY_BODY_SHA256_MISMATCH` |
| 3Q object citation with only 1Q/2Q lineage | fail | `GCM3Q_LINEAGE_CONSUMPTION_MISSING` |

This closes the two prior 1Q bypasses, the two prior 2Q bypasses, and the new 3Q
lineage/identity bypass. The 2Q audit's two helper holes are not still open in
the current helper.

## Cuts And CKW

I recomputed the three reduced-state pairs for four survivors from stored
`rho_ABC`: raw 3Q survivors `0`, `1`, `2`, and the tripartite anchor `544`.

For all four sampled survivors and all three cuts:

- `rho_left` max delta against stored rows: `0.0`.
- `rho_right` max delta against stored rows: `0.0`.
- entropy-family max delta against stored rows: `0.0`.

For the tripartite anchor, recomputed negativity is nonzero on all three cuts:

| Cut | Mutual information | Negativity |
|---|---:|---:|
| `A|BC` | `0.392933956929392` | `0.216506350945969` |
| `B|AC` | `0.392933956929096` | `0.216506350945969` |
| `C|AB` | `0.392933956929096` | `0.216506350945969` |

CKW recomputation from stored `rho_ABC` matches the stored table. Margins:

| Cut | Recomputed CKW margin | Delta from `3/16` |
|---|---:|---:|
| `A|BC` | `0.1875` | `0.0` |
| `B|AC` | `0.187499999999995` | `0.0` after packet rounding |
| `C|AB` | `0.187499999999995` | `0.0` after packet rounding |

The `1.87499999999995e-1` form on `B|AC` and `C|AB` is floating-point residue;
the audited value is `3/16`.

## Registry And Lineage

Stored registry equals a fresh in-memory rebuild from:

- `system_v6/sims/gcm_constraint_carve_3q_v1/results/gcm_constraint_carve_3q_v1_results.json`
- `system_v6/sims/gcm_2q_freeze_and_cut_v0/results/gcm_2q_freeze_and_cut_v0_registry.json`

Registry body hash:
`623785e4ec0f41bd8cd040c44ceefbc5f1bd3c14d3257487a82afc0a89439fb0`.

Mutation sensitivity passes. Changing the 3Q carve survivor count in memory
changed the object id from
`gcm3qobj_492a4d00823507fd9ae8a1b3e4d0acb5` to
`gcm3qobj_8c34ee241a8dc2bd93dd2429bc63027f`, and changed the registry body hash.

The split is consistent with 3Q carve v1:

- `545` total 3Q survivors in carve and freeze packet.
- `544` product-lift survivors.
- `1` tripartite entangled anchor.
- `544` unique 2Q sources, each with one 3Q product lift.
- `Tr_C(rho_ABC)` reproduces the 2Q local-pin product with max delta `0.0`.
- Full `rho_AB` is reproduced for `528` product rows; the `16` correlated 2Q
  rows are correctly fenced as not claimed.

## G.2a And Coordinates

G.2a passes for this packet shape:

- Builder gates say `G_2a_idempotency_from_birth=true`,
  `no_builder_audit_verdict=true`, and `no_builder_audit_verdict_envelope_gate=true`.
- `scripts/builder_audit_boundary.py` accepts the current audit boundary.
- The packet used the idempotent boundary helper from birth instead of a hard
  permanent absence check.
- This file declares independent fresh read-only audit status in the header.

Coordinates are correct and bounded:

```json
{
  "layers": "3Q freeze/registry plus all bipartition cut attachments",
  "nesting": "A|BC, B|AC, C|AB cut lattice",
  "qubit_depth": "3Q"
}
```

## Citation Rule

Future citations to this gate must cite all of:

- this audit verdict;
- `system_v6/sims/gcm_3q_freeze_and_cuts_v0/results/gcm_3q_freeze_and_cuts_v0_results.json`;
- `system_v6/sims/gcm_3q_freeze_and_cuts_v0/results/gcm_3q_freeze_and_cuts_v0_registry.json`;
- `system_v6/sims/gcm_constraint_carve_3q_v1/results/gcm_constraint_carve_3q_v1_results.json`;
- `scripts/gcm_substrate_check.py`.

Do not cite only the object id. Do not cite this as runtime flux already built.
The admissible downstream citation is: "3Q runtime/QIT-flux input surface audited;
stored cuts and entropy set may be consumed for `J_ent` / `J_cut` build."
