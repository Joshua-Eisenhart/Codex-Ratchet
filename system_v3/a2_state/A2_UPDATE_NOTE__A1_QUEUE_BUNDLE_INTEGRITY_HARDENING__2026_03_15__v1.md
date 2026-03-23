# A2_UPDATE_NOTE__A1_QUEUE_BUNDLE_INTEGRITY_HARDENING__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the patch that turns the A1 queue packet into a stronger integrity boundary by requiring ready bundle companions to cohere, not merely exist

## Scope

Primary runtime/integrity files:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/a1_queue_ready_integrity.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/validate_a1_queue_status_packet.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/a1_queue_surface_models.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/audit_a1_queue_surfaces_pydantic.py`

Focused regressions:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_status_packet.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_queue_status_surfaces.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_refresh_active_current_a1_queue_state.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_surface_pydantic_stack.py`

## Problem

The next highest-priority review finding after validator unification was:
- queue-ready surfaces proved only that referenced files existed
- they did not prove the referenced packet, bundle result, send-text companion, and launch spine belonged to the same dispatch/bundle set

That made the queue packet too weak as a trust boundary.
Hand-edited or stale queue packets could stitch together mismatched staged artifacts and still validate.

## What changed

### 1) New shared ready-artifact coherence validator

New helper:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/a1_queue_ready_integrity.py`

It validates one ready queue packet against its referenced staged artifacts.

For the ready packet it now checks:
- referenced worker packet exists and is itself valid
- queue packet fields match the ready packet:
  - `dispatch_id`
  - `target_a1_role`
  - `required_a1_boot`
  - `bounded_scope`
  - `stop_rule`
  - `go_on_count`
  - `go_on_budget`
  - `queue_status`
  - validation provenance fields
  - `source_a2_artifacts`
  - `a1_reload_artifacts`
- `family_slice_json` is actually present in the ready packet fuel list

For bundle mode it now also checks:
- bundle result points back to the same ready packet and remains `READY`
- send-text companion points back to the same ready packet and matches dispatch/role/scope/budget/source lists
- launch spine points to the same ready packet, gate-result path, companion path, and handoff path
- launch spine dispatch/role/scope/budget/source lists match the ready packet
- launch spine packet/companion hashes match the actual files
- spine `send_text_sha256` matches the companion `send_text_sha256`

### 2) Plain validator and local Pydantic model now share the same integrity law

Both:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/validate_a1_queue_status_packet.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/a1_queue_surface_models.py`

now call the same ready-artifact coherence helper.

So the queue trust boundary is stronger in both paths:
- plain validator path
- local spec-graph / Pydantic path

### 3) Local queue audit now exposes that integrity was verified

`audit_a1_queue_surfaces_pydantic.py` now reports:
- `ready_artifact_integrity_verified`

for ready queue packets that survive the local model audit.

## Meaning

This patch does not yet make the queue packet a fully cryptographic owner surface.
But it materially improves the live controller-facing boundary:
- mismatched staged companions are now rejected
- queue validation now proves the ready bundle artifacts belong together
- the plain validator and local Pydantic path no longer diverge on this integrity check

## Focused verification

Compile:
- `python3 -m py_compile system_v3/tools/a1_queue_ready_integrity.py system_v3/tools/validate_a1_queue_status_packet.py system_v3/tools/a1_queue_surface_models.py system_v3/tools/audit_a1_queue_surfaces_pydantic.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_status_packet.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_surface_pydantic_stack.py`

Focused queue/controller tests:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_status_packet.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_queue_status_surfaces.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_refresh_active_current_a1_queue_state.py`
- result:
  - `Ran 14 tests ... OK`

Local spec-graph queue tests:
- `'.venv_spec_graph/bin/python' -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_queue_surface_pydantic_stack.py`
- result:
  - `Ran 7 tests ... OK`

## Next seam

Best next move is still in the real system core:
- bring the hand-written family-slice schema into tighter alignment with the live model/runtime
- then continue shrinking remaining family-slice planner defaults that still behave like hidden universal law
