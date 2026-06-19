# GCM 3Q Freeze: Carve SHA Drift Diagnosis
**Date:** 2026-06-13
**Task:** Diagnose and fix (or flag) the integrity failure in `gcm_3q_freeze_and_cuts_v0` where the validator reports "3Q registry drift against source rebuild".

---

## Diagnosis: Two-Layer Problem

### Layer 1 — Carve results.json metadata drift (CONFIRMED MATH-UNCHANGED)

The upstream file `gcm_constraint_carve_3q_v1/results/gcm_constraint_carve_3q_v1_results.json` differs from the version committed at `5544ad21c`.

| | SHA256 |
|---|---|
| Committed version (at `5544ad21c`) | `05b11d6e81dea29be8142088a193a6d73f11d4bc3db49eb461bdf302a3204d02` |
| Current working-tree version | `f903c80331d6486e0a996969d9d6e1c2b31625b4197fe120b3fe4036500996f7` |

The file is `modified` in git (unstaged). The carve's own validator passes (exit 0) against the current working-tree version.

**Byte-diff between committed and current carve results.json** — only five top-level keys differ; all are provenance/metadata:

| Key | Nature |
|---|---|
| `generated_at` | Run timestamp changed (`2026-06-13T01:23:41Z` -> `2026-06-13T07:14:13Z`) |
| `ledger_lock_refreshed` | `qubit_ladder_climb_ledger_20260612.md` got a new git commit (`1778ad021` -> `2ce176d3d`) after the freeze was built |
| `result_sha256` | Derived from `generated_at` — changes when timestamp changes |
| `source_locks["build_card"]` | `git_last_commit` changed from `None` to `5544ad21c` (git indexed the file after initial run) |
| `source_locks["climb_ledger_correction"]` | Same ledger commit drift as `ledger_lock_refreshed` |

All math-bearing keys are **identical** between the two versions:
- `survivors` (all 545 rows)
- `state_artifacts` (all density matrices)
- `constraint_matrix` (full 552x3)
- `quotient` (9 classes)
- `survivor_count`, `survivor_family_counts`
- `ghz_w_matrix_finding`, `monogamy_ckw_recomputed_from_stored_rho`
- `kill_counts_by_constraint`, `kill_ledger`, `killed_rows`

**Verdict: math unchanged, metadata-only drift.**

### Layer 2 — Cascade: hardcoded 3Q registry body SHA in many files (OUT OF SCOPE TO FIX HERE)

The freeze `build_3q_registry` function embeds `sha256_file(THREE_Q_CARVE_RESULT)` into the `pinned` dict that seeds `gcm_3q_object_id`. When the carve file byte-changed (metadata only), the rebuild produces:

| | Value |
|---|---|
| Old 3Q registry body SHA (from committed carve) | `623785e4ec0f41bd8cd040c44ceefbc5f1bd3c14d3257487a82afc0a89439fb0` |
| New 3Q registry body SHA (from current carve) | `f556c365fecb9a6b723cad43fa8908f4f249085f360adf498cb4e28163fb37f8` |
| Old 3Q object ID | `gcm3qobj_492a4d00823507fd9ae8a1b3e4d0acb5` |
| New 3Q object ID | `gcm3qobj_66e9df6cdb1e0715ffdad6895065785b` |

The hardcoded `EXPECTED_3Q_REGISTRY_BODY_SHA256 = "623785e4..."` in `scripts/gcm_substrate_check.py` line 16 is what blocks the substrate positive check after a rebuild against the current carve.

**Files that hardcode the old 3Q registry body SHA `623785e4` (non-results files only):**

- `scripts/gcm_substrate_check.py:16` — the shared substrate check constant (load-bearing for ALL downstream validators)
- `system_v6/sims/gcm_4q_freeze_and_cuts_v0/gcm_4q_freeze_and_cuts_v0_common.py:56`
- `system_v6/sims/gcm_5q_freeze_and_cuts_v0/gcm_5q_freeze_and_cuts_v0_common.py:67`
- `system_v6/sims/gcm_constraint_carve_4q_v0/gcm_constraint_carve_4q_v0_common.py:49`
- `system_v6/sims/gcm_constraint_carve_5q_v0/gcm_constraint_carve_5q_v0_common.py:50`
- `system_v6/sims/gcm_constraint_carve_6q_v0/gcm_constraint_carve_6q_v0_common.py:50`
- `system_v6/sims/gcm_runtime_flux_3q_v0/gcm_runtime_flux_3q_v0_common.py:78`
- `system_v6/sims/gcm_runtime_flux_3q_v1/gcm_runtime_flux_3q_v1_common.py:83`
- `system_v6/sims/gcm_nested_geometry_delta_3q_v0/gcm_nested_geometry_delta_3q_v0_common.py:51`
- `system_v6/sims/gcm_nested_geometry_delta_4q_v0/gcm_nested_geometry_delta_4q_v0_common.py:52`
- `system_v6/sims/gcm_nesting_tower_le4q_v0/gcm_nesting_tower_le4q_v0_common.py:59`
- Several `results/*.json` files (non-authoritative — these are receipts of past runs)
- Several `build_card.md` files (documentation only)

**Critical finding: the 4Q freeze validator currently CRASHES** (not just fails) with `KeyError: 'gcm3qsurv_5197eacabb43ac19561c19c5'` when run against the current carve, because the 4Q packet's stored `gcm_3q_survivor_id` references the old 3Q registry's survivor IDs, which change when the 3Q object is re-pinned. Downstream validators (`gcm_runtime_flux_3q_v0`, `gcm_runtime_flux_3q_v1`, `gcm_nested_geometry_delta_3q_v0`) currently PASS because they have their own stored results that still match the old registry body SHA — they would all fail if the 3Q registry and substrate check constant were updated.

---

## What Was NOT Done (and Why)

The minimal-honest fix for the 3Q freeze alone (re-pin `EXPECTED_3Q_REGISTRY_BODY_SHA256` in `scripts/gcm_substrate_check.py`, rebuild the 3Q freeze packet) would:
1. Fix the 3Q freeze validator
2. Break the 4Q freeze validator (crash-level, not just fail)
3. Break `gcm_runtime_flux_3q_v0`, `gcm_runtime_flux_3q_v1`, `gcm_nested_geometry_delta_3q_v0` (they currently pass; re-pinning changes the registry body SHA they must cite)
4. Require rebuilding all downstream sims in order — this is a cascade touching files outside the write target

This is an owner decision: the correct fix requires a coordinated re-pin across the full 3Q-dependent chain, in order. It is NOT a silent metadata re-pin.

---

## Owner Decision Required

**The math is unchanged.** The drift is metadata-only. But the pinning architecture treats the full carve file byte-hash (including timestamps) as the identity anchor for the 3Q object. This means any re-run of the carve that touches `generated_at` or `source_locks` will cascade-invalidate all downstream sims.

**Two options for owner:**

1. **Restore the carve results.json to the committed version** (`git checkout -- system_v6/sims/gcm_constraint_carve_3q_v1/results/gcm_constraint_carve_3q_v1_results.json`) — this returns all validators to green without any re-pinning, because the freeze was built against the committed version. The carve's own validator still passes against the committed version.

2. **Accept the current carve results.json and cascade-repin** — update `scripts/gcm_substrate_check.py:16` to the new 3Q body SHA `f556c365...`, then rebuild and re-pin in order: 3Q freeze → 4Q freeze → 5Q freeze → runtime flux → nested geometry → nesting tower. Each requires a fresh sim run.

**Option 1 is the minimal-impact correct fix** given math is unchanged. Option 2 is valid if there is a reason to keep the current carve metadata (e.g., the ledger or build_card commit was intentionally refreshed).

---

## Evidence Files

- Committed carve (reference): `git show 5544ad21c:system_v6/sims/gcm_constraint_carve_3q_v1/results/gcm_constraint_carve_3q_v1_results.json`
- Current carve (live): `system_v6/sims/gcm_constraint_carve_3q_v1/results/gcm_constraint_carve_3q_v1_results.json`
- Freeze validator: `system_v6/sims/gcm_3q_freeze_and_cuts_v0/validate_gcm_3q_freeze_and_cuts_v0.py`
- Substrate check: `scripts/gcm_substrate_check.py`
