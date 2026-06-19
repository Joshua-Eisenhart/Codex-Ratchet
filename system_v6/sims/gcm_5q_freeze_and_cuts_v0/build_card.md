# gcm_5q_freeze_and_cuts_v0 Build Card

## Scope

Build the 5Q freeze/registry plus lean cut-state attachment surface for the `<=5Q` tower prerequisite.

Input source:
- `system_v6/sims/gcm_4q_freeze_and_cuts_v0/`
- `system_v6/sims/gcm_constraint_carve_5q_v0/`

Target:
- freeze `gcm_5q_object_id` over pinned 1Q/2Q/3Q/4Q lineage, the committed 5Q carve result, survivor/class/region counts, survivor families, the 15-cut lattice, and the lean cut-state policy;
- enumerate all 5Q unordered bipartition cuts;
- set `cut_state_available=true` using a recomputable hash-per-(survivor,cut) reduced-state map plus sample full reduced matrices.

## Expected Counts

- candidate count: `556`
- survivor count: `547`
- killed count: `9`
- quotient class count: `9`
- candidate region count: `9`
- product-lift survivor count: `546`
- five-partite entangled survivor count: `1`
- cut count: `15`
- full density carrier: `Cl(10)` / `C^32`; density matrix entries are `1024`

## Lean Storage Rule

Do not store full reduced matrices for all survivors x all cuts.

Store:
- hashes and metrics for every survivor/cut `rho_left` and `rho_right`;
- sample full reduced matrices for GHZ5, W5, cluster, survivor, and killed/control rows;
- enough source locks and IDs to recompute any missing full matrix from the pinned 5Q carve source.

The honest ceiling is `scratch_diagnostic` and carrier/pins-relative. This is not manifold admission, not formal admission, and not an all-survivor full-matrix blob.

## Required Verification

Run with the sim-stack interpreter:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/gcm_5q_freeze_and_cuts_v0/gcm_5q_freeze_and_cuts_v0_common.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/gcm_5q_freeze_and_cuts_v0/validate_gcm_5q_freeze_and_cuts_v0.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/gcm_substrate_check.py system_v6/sims/gcm_5q_freeze_and_cuts_v0/results/gcm_5q_freeze_and_cuts_v0_results.json --registry system_v6/sims/gcm_4q_freeze_and_cuts_v0/results/gcm_4q_freeze_and_cuts_v0_registry.json
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest system_v6/sims/gcm_5q_freeze_and_cuts_v0/tests/test_gcm_5q_freeze_and_cuts_v0.py
```

```bash
find system_v6/sims/gcm_5q_freeze_and_cuts_v0 -type f -size +50M -print
```

## Git Boundary

NO git add/commit in this build slice.
