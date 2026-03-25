# A2_UPDATE_NOTE__A1_ACTIVE_CURRENT_QUEUE_COMPANION_SURFACES__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the step where the new queue candidate registry and queue packet became active repo-held controller companion surfaces in `a2_state`, instead of existing only as draft outputs under `work/`

## Scope

New active machine-readable controller companions:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A1_QUEUE_CANDIDATE_REGISTRY__CURRENT__2026_03_15__v1.json`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A1_QUEUE_STATUS_PACKET__CURRENT__2026_03_15__v1.json`

Supporting helper path:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/create_a1_queue_candidate_registry.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/validate_a1_queue_candidate_registry.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/prepare_current_a1_queue_status_from_candidates.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/prepare_a1_queue_status_surfaces.py`

Patched active read surfaces:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A1_QUEUE_STATUS__CURRENT__2026_03_16__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_STATE_RECORD__CURRENT__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/32_A1_QUEUE_STATUS_SURFACE__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/07_A2_OPERATIONS_SPEC.md`

## Admission/class read

These new `a2_state` JSON companions should be read as:
- `DERIVED_A2`

Why:
- written by A2/controller-side tooling
- bounded control-memory companions
- machine-readable views over current queue state
- not source corpus
- not earned state
- not proposal truth

They do **not** outrank:
- the human-readable current queue note
- source-bearing A2 notes
- lower-loop evidence

They are controller support companions for:
- current queue candidate set
- current machine-readable queue answer

## What changed

### 1) Active current registry

The repo now has one active current candidate registry:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A1_QUEUE_CANDIDATE_REGISTRY__CURRENT__2026_03_15__v1.json`

Current read:
- `candidate_family_slice_jsons = []`
- `selected_family_slice_json = ""`

Meaning:
- no bounded family slices are currently admitted into the live A1 queue candidate set

### 2) Active current queue packet

The repo now has one active current machine-readable queue packet:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A1_QUEUE_STATUS_PACKET__CURRENT__2026_03_15__v1.json`

Current read:
- `A1_QUEUE_STATUS: NO_WORK`
- same reason as the active current note

### 3) Active human-readable surfaces now point to them

The existing current queue note and current controller state record now explicitly point to these machine-readable companions instead of leaving them hidden in draft space only.

## Verification

Active companions validate cleanly:
- `python3 system_v3/tools/validate_a1_queue_candidate_registry.py --registry-json '/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A1_QUEUE_CANDIDATE_REGISTRY__CURRENT__2026_03_15__v1.json'`
- `python3 system_v3/tools/validate_a1_queue_status_packet.py --packet-json '/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A1_QUEUE_STATUS_PACKET__CURRENT__2026_03_15__v1.json'`

Focused suite:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_candidate_registry.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_current_a1_queue_status_from_candidates.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_queue_status_surfaces.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_status_packet.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a2_controller_send_text_from_packet.py`

Result:
- `Ran 13 tests ... OK`

## Next seam

The next real controller decision is whether the active current registry should remain empty until manually curated, or whether one bounded promoted family-slice companion surface should be added under `a2_state` so the live queue path can become ready without depending on `work/audit_tmp` draft locations.
