# A1_READY_PACKET__v1
Status: DRAFT / NONCANON / ACTIVE CONTROL TEMPLATE
Date: 2026-03-11
Owner: current `A2` controller when emitting a ready `A1` dispatch

## Purpose

This note defines the current minimal concrete `A1_READY_PACKET`.

It exists so `a1?` can emit:
- one exact ready packet
- one exact prompt to send
- one exact stop rule

instead of only returning abstract queue status labels.

## Use condition

This packet may be emitted only when queue state is one of:
- `A1_QUEUE_STATUS: READY_FROM_NEW_A2_HANDOFF`
- `A1_QUEUE_STATUS: READY_FROM_EXISTING_FUEL`
- `A1_QUEUE_STATUS: READY_FROM_A2_PREBUILT_BATCH`

Otherwise use:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/32_A1_QUEUE_STATUS_SURFACE__v1.md`

## Required fields

Every `A1_READY_PACKET` must include:
- `model`
- `thread_class`
- `mode`
- `dispatch_id`
- `queue_status`
- `target_a1_role`
- `required_a1_boot`
- `a1_reload_artifacts` when current live/historical A1 read surfaces must be carried with the packet
- `source_a2_artifacts`
- `bounded_scope`
- `prompt_to_send`
- `stop_rule`
- `go_on_count`
- `go_on_budget`

## Template

```text
model: <exact model label>
thread_class: A1_WORKER
mode: PROPOSAL_ONLY
A1_QUEUE_STATUS: <READY_FROM_NEW_A2_HANDOFF | READY_FROM_EXISTING_FUEL | READY_FROM_A2_PREBUILT_BATCH>
dispatch_id: <exact dispatch id>
target_a1_role: <A1_ROSETTA | A1_PROPOSAL | A1_PACKAGING>
required_a1_boot: /home/ratchet/Desktop/Codex Ratchet/system_v3/specs/31_A1_THREAD_BOOT__v1.md
a1_reload_artifacts:
- /home/ratchet/Desktop/Codex Ratchet/system_v3/specs/77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1.md
- /home/ratchet/Desktop/Codex Ratchet/system_v3/specs/78_A1_HISTORICAL_BRANCH_WIGGLE_EXTRACT__v1.md
source_a2_artifacts:
- <artifact path 1>
- <artifact path 2>
- <artifact path 3>
bounded_scope: <one bounded sentence>
prompt_to_send:
<self-contained bounded prompt>
stop_rule: <one bounded stop condition sentence>
go_on_count: <integer>
go_on_budget: <integer>
```

## `prompt_to_send` requirements

The prompt must:
- name the exact `target_a1_role`
- assume the current `A1` boot
- carry the declared `a1_reload_artifacts` when present
- name the exact artifact inputs
- forbid drift into `A2`
- forbid lower-loop claims
- end after one bounded pass

The prompt must not:
- refer to hidden thread memory
- refer to “whatever seems relevant”
- require opening old chat threads

## Minimal role-specific prompt skeletons

### `A1_ROSETTA`

```text
Use the current A1 boot:
- /home/ratchet/Desktop/Codex Ratchet/system_v3/specs/31_A1_THREAD_BOOT__v1.md

Run one bounded A1_ROSETTA pass only.

Use only these artifacts:
- <artifact path list>

Task:
- strip selected overlays/jargon into ratchet-safe candidate structure
- preserve disagreements
- emit one bounded rosetta output set

Rules:
- no A2 refinery
- no lower-loop claims
- proposal-side only
- stop after one bounded rosetta pass
```

### `A1_PROPOSAL`

```text
Use the current A1 boot:
- /home/ratchet/Desktop/Codex Ratchet/system_v3/specs/31_A1_THREAD_BOOT__v1.md

Run one bounded A1_PROPOSAL pass only.

Use only these artifacts:
- <artifact path list>

Task:
- generate one bounded proposal family from the supplied A2 fuel
- include negatives and rescue paths
- remain proposal-only

Rules:
- no A2 refinery
- no canon claims
- no lower-loop claims
- stop after one bounded proposal pass
```

### `A1_PACKAGING`

```text
Use the current A1 boot:
- /home/ratchet/Desktop/Codex Ratchet/system_v3/specs/31_A1_THREAD_BOOT__v1.md

Run one bounded A1_PACKAGING pass only.

Use only these artifacts:
- <artifact path list>

Task:
- package the supplied A1 proposal outputs into cleaner bounded packets
- do not generate new doctrine

Rules:
- no A2 refinery
- no new proposal-family expansion
- no lower-loop claims
- stop after one bounded packaging pass
```

## Immediate implication

Current system gap closed by this note:
- `a1?` can now emit an actually sendable bounded packet

Still not implied:
- that `A1` should always run
- that every ready packet must be used immediately

Current executable helpers:
- queue-status builder:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_a1_queue_status_packet.py`
- family-slice compiler:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_a1_worker_launch_packet_from_family_slice.py`
- family-slice bundle preparer:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/prepare_a1_launch_bundle_from_family_slice.py`

Current validation-policy interpretation for these family-slice prep helpers:
- default validation mode is `auto`
- `auto` means:
  - use `local_pydantic` when the local stack is available through `--spec-graph-python`
  - otherwise fall back to `jsonschema`
- explicit `local_pydantic` is still allowed when the controller wants to force the local spec-object path
- when bundle prep is chosen, the derived ready queue surface should carry:
  - the staged send-text companion path as `ready_send_text_companion_json`
  - the staged launch spine path as `ready_launch_spine_json`
- creator:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/create_a1_worker_launch_packet.py`
- validator:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/validate_a1_worker_launch_packet.py`
- local spec-object packet audit:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/audit_a1_worker_launch_packet_pydantic.py`
- local spec-object packet GraphML export:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/export_a1_worker_launch_packet_graph.py`
- local spec-object packet schema emit:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/emit_a1_worker_launch_packet_pydantic_schema.py`
- launch gate:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_a1_worker_launch_from_packet.py`
- local spec-object gate-result audit:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/audit_a1_worker_launch_gate_result_pydantic.py`
- local spec-object gate-result GraphML export:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/export_a1_worker_launch_gate_result_graph.py`
- local spec-object gate-result schema emit:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/emit_a1_worker_launch_gate_result_pydantic_schema.py`
- send-text builder:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_a1_worker_send_text_from_packet.py`
- send-text companion builder:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_a1_worker_send_text_companion.py`
- local spec-object send-text companion audit:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/audit_a1_worker_send_text_companion_pydantic.py`
- local spec-object send-text companion GraphML export:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/export_a1_worker_send_text_companion_graph.py`
- local spec-object send-text companion schema emit:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/emit_a1_worker_send_text_companion_pydantic_schema.py`
- launch handoff builder:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_a1_worker_launch_handoff.py`
- launch handoff validator:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/validate_codex_thread_launch_handoff.py`
  - checks both handoff shape and send-text integrity (`send_text_sha256` plus required launch markers)
- local spec-object handoff audit:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/audit_a1_worker_launch_handoff_pydantic.py`
- local spec-object handoff GraphML export:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/export_a1_worker_launch_handoff_graph.py`
- local spec-object handoff schema emit:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/emit_a1_worker_launch_handoff_pydantic_schema.py`
- compact staged launch-spine builder:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_a1_worker_launch_spine.py`
- compact staged launch-spine audit:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/audit_a1_worker_launch_spine_pydantic.py`
- compact staged launch-spine GraphML export:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/export_a1_worker_launch_spine_graph.py`
- compact staged launch-spine schema emit:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/emit_a1_worker_launch_spine_pydantic_schema.py`
- one-shot bundle preparer:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/prepare_codex_launch_bundle.py`
- Playwright launch plan builder:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_codex_thread_launch_playwright_plan.py`
- Playwright launch executor:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/execute_codex_thread_launch_playwright_plan.py`
  - blocks if the expected visible verification text is not present in the snapshot before any send
- launch-target creator:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/create_codex_thread_launch_target.py`
- launch-target validator:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/validate_codex_thread_launch_target.py`
- launch-surface capture-record creator:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/create_codex_thread_launch_surface_capture_record.py`
- launch-surface capture-record validator:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/validate_codex_thread_launch_surface_capture_record.py`
- observed launch-packet creator:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/create_codex_thread_launch_observed_packet.py`
- observed launch-packet validator:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/validate_codex_thread_launch_observed_packet.py`
- launch-target from capture-record creator:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/create_codex_thread_launch_target_from_capture_record.py`
- one-shot browser-launch bundle preparer:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/prepare_codex_browser_launch_bundle.py`
- one-shot browser-launch bundle preparer from observed surface:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/prepare_codex_browser_launch_bundle_from_observed_surface.py`
- packet-driven browser-launch wrapper from staged capture record:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_codex_browser_launch_from_capture_record.py`
- packet-driven browser-launch wrapper from staged observed packet:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_codex_browser_launch_from_observed_packet.py`
