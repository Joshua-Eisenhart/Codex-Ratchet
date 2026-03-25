# A2_UPDATE_NOTE__A1_FAMILY_SLICE_PREFERRED_PREPARATION_ROUTING__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the routing change where the family-slice-driven packet/bundle path becomes a preferred preparation path in active A2 -> A1 workflow docs

## Scope

Patched routing surfaces:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/30_A2_TO_A1_HANDOFF_CONTRACT__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/THREAD_AND_AUTOMATION_PROCESS_FLOWS__2026_03_11__v1.md`

## What changed

`30_A2_TO_A1_HANDOFF_CONTRACT__v1.md` now:
- explicitly allows bounded `A2_TO_A1_FAMILY_SLICE_v1` objects in A2 -> A1 input classes
- names the preferred preparation path when a valid bounded family slice exists:
  - `34_A1_READY_PACKET__v1.md`
  - `build_a1_worker_launch_packet_from_family_slice.py`
  - `prepare_a1_launch_bundle_from_family_slice.py`

`THREAD_AND_AUTOMATION_PROCESS_FLOWS__2026_03_11__v1.md` now:
- prefers compiling the ready packet or full launch bundle directly from a valid bounded family slice
- treats plain `A1_READY_PACKET` emission as the fallback when no such slice exists

## Meaning

This is a policy/routing step, not a new runtime.

The repo now says more clearly:
- if a valid bounded family slice exists, use it as the preferred A1 launch-preparation substrate
- only fall back to more manually assembled ready-packet flow when that bounded structured object is not available

## Verification

Grounded checks:
- `rg -n "A2_TO_A1_FAMILY_SLICE_v1|Preferred preparation path when a valid bounded family slice exists" system_v3/specs/30_A2_TO_A1_HANDOFF_CONTRACT__v1.md`
- `rg -n "valid bounded family slice|A1_READY_PACKET" system_v3/a2_state/THREAD_AND_AUTOMATION_PROCESS_FLOWS__2026_03_11__v1.md`

## Next seam

The next likely seam is controller-state integration:
- where exactly the controller records that a valid bounded family slice exists
- and how `a1?` chooses between:
  - `NO_WORK`
  - packet-from-family-slice
  - bundle-from-family-slice
  - fallback manually assembled ready packet
