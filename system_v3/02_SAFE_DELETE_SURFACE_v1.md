# Safe Delete Surface v1
Status: ACTIVE
Date: 2026-02-24

## Purpose
List non-destructive cleanup targets that are safe to delete without changing canonical runtime logic.

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
3. If guards pass and no needed artifacts are missing, delete from cache tier.
