# Safe Delete Surface v1
Status: ACTIVE
Date: 2026-02-24

## Purpose
List non-destructive cleanup targets that are safe to delete without changing canonical runtime logic.

## Safety Posture
- append-first beats rewrite-first
- archive/demotion beats immediate deletion
- no cleanup step should be justified only by size, neatness, or pressure to look lean
- if active-path dependence is unclear, do not delete

## Safe Now (No Replay Impact)
- Any file under `archive/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/`
- `*.DS_Store` files anywhere outside `.git/`
- Any ad hoc ZIP copies in `archive/` cache tiers

## Safe With One Guardrail
- Completed run folders under `system_v3/runs/<RUN_ID>/`
Guardrail: keep at least one representative run per active campaign before deleting others.

## Keep (Do Not Delete)
- `system_v3/runtime/bootpack_b_kernel_v1/`
- `system_v3/specs/`
- `system_v3/control_plane_bundle_work/`
- `system_v3/runs/_CURRENT_STATE/`
- `system_v3/runs/_CURRENT_RUN.txt`
- `system_v3/a2_state/`

## Delete Workflow (Safe Mode)
1. Move candidate files into `archive/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/` first.
2. Re-run guards:
   - `python3 system_v3/tools/sprawl_guard.py`
   - `python3 system_v3/tools/archive_guard.py`
3. Run a bounded without-it check on the intended active path when feasible.
4. If guards pass and no needed artifacts are missing, delete from cache tier.

## Archive Demotion Workflow (Preferred Before Delete)
1. If the target is a historical run family, prefer external archive demotion over local deletion.
2. If family-level doctrine still cites raw local run paths, replace those citations with:
   - run-anchor surfaces
   - regeneration-witness surfaces
3. Move the run family into external archive heat-dump storage with a demotion manifest.
4. Rewrite the corresponding anchor/witness surfaces to the archive location in the same bounded step.
5. Only after demotion and proof of local nondependence should any true deletion be considered.

## Do Not Use This Surface For
- broad doc rewrites
- random repo cleanup
- deleting unclear system surfaces before they are classified
- treating archive placement as proof of dispensability
