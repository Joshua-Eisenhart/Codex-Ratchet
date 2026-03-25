# A2_CONTROLLER_LAUNCH_PACKET__v1
Status: DRAFT / NONCANON / ACTIVE CONTROL SURFACE
Date: 2026-03-12
Owner: current `A2` controller relaunches

## Purpose

This note defines the missing fail-closed launch packet for fresh `A2_CONTROLLER` threads.

It exists because:
- the current system has strong worker/result/continuation machinery
- the current system has weaker controller launch identity
- controller relaunches should not infer weighted priority from mixed long-form execution history alone

This packet is the top launch artifact for:
- controller identity
- controller launch weighting
- controller stop/dispatch discipline

Normative anchors:
- `RQ-145`
- `RQ-146`
- `RQ-147`

It does not replace:
- `A2` brain surfaces
- worker dispatch packets
- `A1` ready packets
- execution history

## Required governing surfaces

Every `A2_CONTROLLER` launch packet must bind to:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/27_MASTER_CONTROLLER_THREAD_PROCESS__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/40_PARALLEL_CODEX_THREAD_CONTROL__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/66_PARALLEL_CODEX_RUN_PLAYBOOK__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_STATE_RECORD__CURRENT__v1.md`

## Packet role

This packet is the fail-closed controller launch gate.

It should be read before the controller starts substantive work.

If required fields are missing, the launch is invalid and the thread should stop rather than improvise.

## Required fields

Every launch packet must include:

1. `MODEL`
- exact model label

2. `THREAD_CLASS`
- must be exactly:
  - `A2_CONTROLLER`

3. `MODE`
- must be exactly:
  - `CONTROLLER_ONLY`

4. `PRIMARY_CORPUS`
- exact primary owner corpus path

5. `STATE_RECORD`
- exact path to the current weighted controller-state record

6. `CURRENT_PRIMARY_LANE`
- one exact currently governing lane

7. `CURRENT_A1_QUEUE_STATUS`
- one exact current queue state

8. `GO_ON_COUNT`
- integer count since last fresh controller relaunch or manual reset

9. `GO_ON_BUDGET`
- integer maximum before forced re-anchor or stop

10. `STOP_RULE`
- one exact bounded stop law for the controller

11. `DISPATCH_RULE`
- one exact controller dispatch law

12. `INITIAL_BOUNDED_SCOPE`
- one exact bounded controller action the fresh launch is allowed to perform first

## Hard rules

1. `FAIL_CLOSED_ON_MISSING_FIELDS`
- if any required field is missing, the launch is invalid

2. `PRIMARY_CORPUS_LOCK`
- `PRIMARY_CORPUS` must be explicit
- the controller may not begin from a vague mixed-corpus impression

3. `STATE_RECORD_LOCK`
- `CURRENT_PRIMARY_LANE` and `CURRENT_A1_QUEUE_STATUS` must match the state record or explicitly declare a reweighting reason

4. `NO_CONTROLLER_REFINERY_DRIFT`
- controller may route, dispatch, refresh state, or answer queue status
- controller may not absorb long serial worker/refinery work as its normal continuation behavior

5. `GO_ON_BUDGET_LOCK`
- controller launch must state current count and budget
- if budget is exhausted, the next valid move is stop/reload or explicit manual re-anchor

6. `DISPATCH_FIRST_FOR_SUBSTANTIVE_WORK`
- if substantive processing is needed and a bounded worker packet can express it, dispatch the worker instead of doing the work inside the controller

7. `A1_QUEUE_LOCK`
- `A1` may not start from controller enthusiasm or residual context
- it may start only from a valid current ready packet path

## Packet template

```text
A2_CONTROLLER_LAUNCH_PACKET
MODEL: <exact model label>
THREAD_CLASS: A2_CONTROLLER
MODE: CONTROLLER_ONLY
PRIMARY_CORPUS: <exact owner corpus path>
STATE_RECORD: <exact current state record path>
CURRENT_PRIMARY_LANE: <one exact lane>
CURRENT_A1_QUEUE_STATUS: <one exact queue status>
GO_ON_COUNT: <integer>
GO_ON_BUDGET: <integer>
STOP_RULE: <one exact bounded controller stop law>
DISPATCH_RULE: <one exact controller dispatch law>
INITIAL_BOUNDED_SCOPE: <one exact bounded controller action>
```

## Current launch basis

Current expected state record:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_STATE_RECORD__CURRENT__v1.md`

Current primary owner corpus:
- `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel`

Current working interpretation:
- the internal refinedfuel `Constraints` / `Constraints. Entropy` lineage remains the primary internal lane
- the external entropy / Carnot / Szilard lane is secondary support unless explicitly reweighted
- `A1_QUEUE_STATUS` is currently `NO_WORK`

## Current relaunch packet example

```text
A2_CONTROLLER_LAUNCH_PACKET
MODEL: GPT-5.4 Medium
THREAD_CLASS: A2_CONTROLLER
MODE: CONTROLLER_ONLY
PRIMARY_CORPUS: /home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel
STATE_RECORD: /home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_STATE_RECORD__CURRENT__v1.md
CURRENT_PRIMARY_LANE: internal refinedfuel Constraints / Constraints. Entropy revisit lineage
CURRENT_A1_QUEUE_STATUS: A1_QUEUE_STATUS: NO_WORK
GO_ON_COUNT: 0
GO_ON_BUDGET: 2
STOP_RULE: stop after one bounded controller action unless one exact worker dispatch is issued
DISPATCH_RULE: substantive processing belongs in a bounded worker packet whenever a worker expression already exists
INITIAL_BOUNDED_SCOPE: refresh weighted current state and choose exactly one next bounded controller action
```

## Current executable helpers

Current machine-readable launch path:
- creator:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/create_a2_controller_launch_packet.py`
- validator:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/validate_a2_controller_launch_packet.py`
- local spec-object audit:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/audit_a2_controller_launch_packet_pydantic.py`
- local spec-object GraphML export:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/export_a2_controller_launch_packet_graph.py`
- local spec-object schema emit:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/emit_a2_controller_launch_packet_pydantic_schema.py`
- launch gate:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_a2_controller_launch_from_packet.py`
- local spec-object gate-result audit:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/audit_a2_controller_launch_gate_result_pydantic.py`
- local spec-object gate-result GraphML export:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/export_a2_controller_launch_gate_result_graph.py`
- local spec-object gate-result schema emit:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/emit_a2_controller_launch_gate_result_pydantic_schema.py`
- send-text builder:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_a2_controller_send_text_from_packet.py`
- send-text companion builder:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_a2_controller_send_text_companion.py`
- local spec-object send-text companion audit:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/audit_a2_controller_send_text_companion_pydantic.py`
- local spec-object send-text companion GraphML export:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/export_a2_controller_send_text_companion_graph.py`
- local spec-object send-text companion schema emit:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/emit_a2_controller_send_text_companion_pydantic_schema.py`
- launch handoff builder:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_a2_controller_launch_handoff.py`
- launch handoff validator:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/validate_codex_thread_launch_handoff.py`
  - checks both handoff shape and send-text integrity (`send_text_sha256` plus required launch markers)
- local spec-object handoff audit:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/audit_a2_controller_launch_handoff_pydantic.py`
- local spec-object handoff GraphML export:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/export_a2_controller_launch_handoff_graph.py`
- local spec-object handoff schema emit:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/emit_a2_controller_launch_handoff_pydantic_schema.py`
- compact controller launch-spine companion builder:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_a2_controller_launch_spine.py`
- compact controller launch-spine audit:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/audit_a2_controller_launch_spine_pydantic.py`
- compact controller launch-spine GraphML export:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/export_a2_controller_launch_spine_graph.py`
- compact controller launch-spine schema emit:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/emit_a2_controller_launch_spine_pydantic_schema.py`
- active current controller launch-spine refresh helper:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/refresh_active_current_a2_controller_launch_spine.py`
- current A1 queue-status helper for the bounded `a1?` action:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/refresh_active_current_a1_queue_state.py`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_a1_queue_status_packet.py`
  - these now default to controller-facing compatibility mode:
    - `--family-slice-validation-mode auto`
  - `auto` means:
    - use `local_pydantic` when the local stack exists at `--spec-graph-python`
    - otherwise fall back to `jsonschema`
  - explicit local-stack path still exists via:
    - `--family-slice-validation-mode local_pydantic`
    - `--spec-graph-python /home/ratchet/Desktop/Codex Ratchet/.venv_spec_graph/bin/python`
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

Current launch-gate result statuses:
- `LAUNCH_READY`
- `STOP_RELOAD_REQUIRED`
- `FAIL_CLOSED`

## Allowed first controller actions

After valid launch, the first controller action should be exactly one of:
- weighted state refresh only
- one bounded worker dispatch
- one bounded `a1?` queue answer
- stop and relaunch if weighting is stale

Not allowed as the first controller action:
- broad local refinery work
- long serial continuation on a secondary support lane
- stale `A1` launch
- multi-step freeform planning without one exact bounded action

## Immediate implication

This packet is now the missing top launch seam.

Use it to:
- keep controller identity explicit
- keep primary-corpus weighting explicit
- keep `A1` queue state explicit
- stop controller drift into worker behavior
