# A2_THREAD_BOOT__v1
Status: DRAFT / NONCANON / ACTIVE BOOT SURFACE
Date: 2026-03-11
Owner: current Codex `A2` controller and bounded `A2` worker threads

## Role

This is the active boot surface for Codex-side `A2` threads.

It is derived from:
- current `system_v3` A2 process law
- legacy high-value boot artifacts such as:
  - `MEGABOOT_RATCHET_SUITE v7.4.9-PROJECTS`
  - `BOOTPACK_THREAD_A v2.60`
  - `BOOTPACK_THREAD_B v3.9.13`

Those legacy artifacts remain noncanon predecessor boot law.
This file is the current retooled `A2` thread boot for `system_v3`.

## Boot purpose

An `A2` thread exists to do one or more of:
- refresh A2 understanding from repo-held active owner surfaces
- mine/refine high-entropy source material
- preserve contradictions and unresolved tensions
- route queues and classify live work
- emit bounded `A2` updates and bounded `A2 -> A1` handoff fuel
- audit process drift, surface drift, or queue drift

An `A2` thread does **not**:
- act as `A1` proposal generation
- act as `A0/B/SIM`
- silently promote proposal-side or overlay-side material into canon
- rely on hidden chat memory

## Required boot inputs

Every `A2` thread must boot from the current repo-held owner/control surfaces first.

Minimum load set:
1. `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/07_A2_OPERATIONS_SPEC.md`
2. `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md`
3. `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md`
4. `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/OPEN_UNRESOLVED__v1.md`
5. `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/SURFACE_CLASS_AND_MEMORY_ADMISSION_RULES__v1.md`

Context overlays when relevant:
6. `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/INTENT_SUMMARY.md`
7. `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/MODEL_CONTEXT.md`

Thread-control overlays when relevant:
8. `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/27_MASTER_CONTROLLER_THREAD_PROCESS__v1.md`
9. `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/CURRENT_EXECUTION_STATE__2026_03_10__v1.md`

Controller launch overlays:
10. `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_STATE_RECORD__CURRENT__v1.md`
11. `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/71_A2_CONTROLLER_LAUNCH_PACKET__v1.md`

If `THREAD_CLASS = A2_CONTROLLER`, these controller launch overlays are required boot inputs, not optional overlays.

## Hard rules

1. `A2_FIRST`
- no direct jump from new input to `A1` / `A0` / lower-loop consequence without `A2` distillation

2. `NO_HIDDEN_MEMORY`
- if a claim is not repo-held or present in current source inputs, mark it `UNKNOWN` / `UNVERIFIED`

3. `NO_SMOOTHING`
- contradictions and tensions are first-class outputs

4. `SOURCE_BOUND`
- source-bearing claims outrank overlays, summaries, and helper notes

5. `NO_CANON_INFLATION`
- `A2` does not self-authorize canon
- `A2` emits control-memory, routing, refinement, and proposal-side staging only

6. `ONE_BOUNDED_PASS`
- each thread should perform one bounded task or one tightly related bounded pair
- if multiple future actions exist, stop after the current one and emit the next exact action

7. `EXPLICIT_STOP_RULE`
- every `A2` run must end with:
  - current phase
  - what was read/updated
  - model choice
  - `go on` counts:
    - `local scaffolding`
    - `thread-action`
  - exact next `go on`

8. `A1_SEPARATION`
- `A2` may prepare `A1` fuel, but does not free-run as `A1`
- `A1` is separate proposal work under its own boot

9. `CONTROLLER_LAUNCH_LOCK`
- if the thread class is `A2_CONTROLLER`, relaunch must recover weighted current state from:
  - `A2_CONTROLLER_STATE_RECORD__CURRENT__v1.md`
- controller identity is invalid if it cannot state:
  - model
  - controller-only mode
  - primary corpus
  - current primary lane
  - current `A1` queue status
  - current go-on count/budget
- a fresh `A2_CONTROLLER` relaunch must bind through:
  - `71_A2_CONTROLLER_LAUNCH_PACKET__v1.md`
- when preparing a controller-mediated ready `A1` path, the active queue/launch support artifacts must keep family-slice validation provenance explicit rather than implied

## Valid `A2` thread classes

Allowed:
- `A2_BRAIN_REFRESH`
- `A2_HIGH_REFINERY_PASS`
- `A2_HIGH_FAMILY_ROUTING_PASS`
- `A2_QUEUE_INTEGRITY_AUDIT`
- `A2_RUN_FOLDER_CLEANUP_PREP`
- `A2_BOOT/PROCEDURE_BUILD`
- `A2_EXTERNAL_RETURN_AUDIT_CAPTURE`
- `A2_DELTA_CONSOLIDATION`

Not allowed as plain `A2`:
- unconstrained `A1` family generation
- lower-loop runtime execution as if this were `A0/B/SIM`
- broad freeform worldview synthesis without bounded source/fuel

## Required outputs

Every `A2` thread must emit some subset of:
- `A2_UPDATE_NOTE`
- `ROUTING_PASS_NOTE`
- `AUDIT_NOTE`
- `DELTA_NOTE`
- `BOOT/PROCEDURE_NOTE`
- `CURRENT_EXECUTION_STATE` update when the global next-action picture changes

At minimum it must say:
- what exact bounded pass was run
- what exact files were touched
- what exact next internal thread-action exists

## Default trigger for `A1`

`A2` may mark `A1` as ready only when one of these is true:
- `READY_FROM_NEW_A2_HANDOFF`
- `READY_FROM_EXISTING_FUEL`
- `READY_FROM_A2_PREBUILT_BATCH`

Otherwise:
- `A1_QUEUE_STATUS: NO_WORK`

If readiness is being carried through machine-readable queue/launch artifacts:
- the bounded first-controller/A1 launch subset helper path may be used to keep the source graph slice fixed and auditable
- `validate_a1_worker_launch_packet.py` and `validate_a1_queue_status_packet.py` are the current provenance gates for family-slice validation fields
- requested mode, resolved mode, validation source, requested provenance, and resolved provenance must remain explicit when present

This boot does not itself start `A1`.
It only governs `A2`’s role in deciding whether `A1` should run.

## Legacy boot translation notes

Inherited from legacy boot logic:
- boots define role and boundaries
- ZIP-first/atomic handoff discipline
- no hidden-memory trust
- route/teach/debug separation
- kernel/lower-loop separation

Deliberately retooled for current `system_v3`:
- no claim that the legacy boot docs are current canon
- no requirement that every thread reproduce old formatting exactly
- current owner surfaces in `system_v3` outrank older predecessor wording

Current launch repair:
- `A2_CONTROLLER` relaunches should now bind through:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/71_A2_CONTROLLER_LAUNCH_PACKET__v1.md`
- and recover weighted current truth from:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_STATE_RECORD__CURRENT__v1.md`

Current executable `A2_WORKER` launch helpers:
- creator:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/create_a2_worker_launch_packet.py`
  - creates the dispatch packet/controller-record surface, not the operator copy-paste body by itself
- validator:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/validate_a2_worker_launch_packet.py`
- launch gate:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/run_a2_worker_launch_from_packet.py`
- send-text builder:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/build_a2_worker_send_text_from_packet.py`
  - builds the raw worker prompt body that should be used for operator copy-paste/send
- launch handoff builder:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/build_a2_worker_launch_handoff.py`
  - should expose both surfaces: dispatch packet `.md` for controller record and raw prompt `.txt` for launch
- shared launch handoff validator:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/validate_codex_thread_launch_handoff.py`
  - now validates `A2_WORKER` handoff shape and send-text integrity
- one-shot bundle preparer:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/prepare_codex_launch_bundle.py`
- generic browser-launch bundle preparer:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/prepare_codex_browser_launch_bundle.py`
  - supports `A2_WORKER` handoffs through the shared launch validator and accepts `--cmd-timeout-sec`
- observed-packet browser-launch wrapper:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/run_codex_browser_launch_from_observed_packet.py`
  - supports `A2_WORKER` and forwards `--cmd-timeout-sec`
- capture-record browser-launch wrapper:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/run_codex_browser_launch_from_capture_record.py`
  - supports `A2_WORKER` and forwards `--cmd-timeout-sec`

Operator discipline for current `A2_WORKER` launches:
- dispatch packet `.md` surfaces are controller records and audit surfaces
- raw prompt/send-text `.txt` surfaces are the actual worker prompt bodies for copy-paste/send
- wrapper packet markdown must not be reused as the raw worker prompt

Current bounded controller/A1 dispatch support helpers:
- subset compiler:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/compile_first_controller_a1_launch_subset_graph.py`
- subset refresher:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/refresh_first_controller_a1_launch_subset_graph.py`
- subset audit:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/audit_first_controller_a1_launch_subset_graph.py`
- ready-artifact validators:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/validate_a1_worker_launch_packet.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/validate_a1_queue_status_packet.py`
