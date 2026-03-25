# A1_QUEUE_STATUS_SURFACE__v1
Status: DRAFT / NONCANON / ACTIVE CONTROL SURFACE
Date: 2026-03-11
Owner: current `A2` controller and any operator asking `a1?`

## Purpose

This note defines the minimal current output surface for `A1` queue status.

It exists so `a1?` is a concrete controller response rather than only an informal idea.

## Rule

When the controller is asked `a1?`, it must return exactly one bounded queue-status packet.

That packet must answer only:
- is there `A1` work right now?
- if yes, what exact bounded work?
- if no, why not?

## Allowed queue statuses

Current allowed values:
- `A1_QUEUE_STATUS: NO_WORK`
- `A1_QUEUE_STATUS: READY_FROM_NEW_A2_HANDOFF`
- `A1_QUEUE_STATUS: READY_FROM_EXISTING_FUEL`
- `A1_QUEUE_STATUS: READY_FROM_A2_PREBUILT_BATCH`
- `A1_QUEUE_STATUS: BLOCKED_MISSING_BOOT`
- `A1_QUEUE_STATUS: BLOCKED_MISSING_ARTIFACTS`

Do not use:
- `READY`
- `MAYBE`
- `SORT_OF_READY`
- freeform narrative status labels

## Required output shape

### Case 1: no work

Return:
- `A1_QUEUE_STATUS: NO_WORK`
- `reason: <one short line>`

### Case 2: blocked

Return:
- exact blocked status
- `reason: <one short line>`
- `missing:`
  - explicit missing item(s)

### Case 3: ready

Return:
- exact ready status
- `dispatch_id`
- `target_a1_role`
- `required_a1_boot`
- `a1_reload_artifacts` when live/historical A1 reload guidance is needed
- `source_a2_artifacts`
- `prompt_to_send`
- `stop_rule`
- `ready_send_text_companion_json` when the ready surface is an `A1_LAUNCH_BUNDLE`
- `ready_launch_spine_json` when the ready surface is an `A1_LAUNCH_BUNDLE`

## `prompt_to_send` rule

If the queue status is ready, the packet must include a self-contained bounded prompt.

That prompt must:
- match the declared `target_a1_role`
- assume the declared `A1` boot
- name the required artifacts
- include a stop condition

It must not require:
- hidden context
- “open some old thread”
- “read whatever seems relevant”

## `source_a2_artifacts` rule

Artifact list must be explicit and bounded.

Allowed artifact classes:
- `A2_UPDATE_NOTE`
- `A2_TO_A1_IMPACT_NOTE`
- `A2_A1_DELTA`
- bounded `A2_TO_A1_FAMILY_SLICE_v1` object
- contradiction map
- residue map
- queue/routing note
- ZIP-bound handoff packet

Do not list:
- raw high-entropy source mass without prior `A2` distillation
- ambient controller memory

## `a1_reload_artifacts` rule

Reload list is optional but preferred for active `A1` launches.

Use it for bounded repo-held A1 read surfaces that should accompany the boot, especially:
- live packet/profile read surfaces
- historical branch/wiggle doctrine surfaces when the task needs them

Do not use it for:
- raw repo sweeps
- open-ended “read more if needed”
- extra fuel that belongs in `source_a2_artifacts`

## `stop_rule` rule

Every ready packet must say when the `A1` run stops.

Minimum acceptable forms:
- one bounded proposal cycle
- one bounded rosetta translation pass
- one bounded packaging pass

## Active current companions

The current queue answer may also be carried in machine-readable companion surfaces under `system_v3/a2_state/`, for example:
- current queue packet:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A1_QUEUE_STATUS_PACKET__CURRENT__2026_03_15__v1.json`
- current candidate registry:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A1_QUEUE_CANDIDATE_REGISTRY__CURRENT__2026_03_15__v1.json`

Interpretation rule:
- the registry is the bounded candidate input set
- the queue packet is the machine-readable current answer
- the human-readable current note remains the active operator-facing summary
- staged family-slice companions may exist in `a2_state`, but they do not affect the live queue until they are explicitly admitted into the current candidate registry
- when the ready surface kind is `A1_LAUNCH_BUNDLE`, the current queue packet should also point at:
  - the staged send-text companion
  - the staged launch spine
  so the bundle path has both the direct send-text-derived companion and one compact machine-readable reload surface

## Optional local spec-object validation mode

The current queue helpers now support:
- `--family-slice-validation-mode auto`
- `--family-slice-validation-mode jsonschema`
- `--family-slice-validation-mode local_pydantic`
- `--spec-graph-python /home/ratchet/Desktop/Codex Ratchet/.venv_spec_graph/bin/python`

Current controller-facing default:
- `auto`

`auto` means:
- if the local spec-object stack exists at the provided `--spec-graph-python`, validate through `local_pydantic`
- otherwise fall back to the hand-written `jsonschema` path

Interpretation rule:
- `auto` is the preferred controller-facing compatibility mode
- `local_pydantic` remains an explicit bounded local-stack mode
- this does not by itself change the live queue packet format
- this does not make the repo's default runtime interpreter depend on the local venv

## Immediate implication

Current system gap closed by this note:
- `a1?` now has a current repo-held response format

This note does not itself start `A1`.
It only defines the queue-status packet the controller should emit.

## Current executable helpers

- queue-status builder:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_a1_queue_status_packet.py`
- queue-status validator:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/validate_a1_queue_status_packet.py`
- active current-queue refresh wrapper:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/refresh_active_current_a1_queue_state.py`
- current-note renderer:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/render_a1_queue_status_current_note_from_packet.py`
- queue-surfaces wrapper:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/prepare_a1_queue_status_surfaces.py`
- current-queue selector wrapper:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/prepare_current_a1_queue_status_from_candidates.py`
- candidate-registry creator:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/create_a1_queue_candidate_registry.py`
- candidate-registry validator:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/validate_a1_queue_candidate_registry.py`
- local spec-object queue-surface audit:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/audit_a1_queue_surfaces_pydantic.py`
- local spec-object queue-surface GraphML export:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/export_a1_queue_surfaces_graph.py`
- local spec-object queue-surface schema emit:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/emit_a1_queue_surface_pydantic_schemas.py`
- family-slice packet compiler:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_a1_worker_launch_packet_from_family_slice.py`
- family-slice bundle preparer:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/prepare_a1_launch_bundle_from_family_slice.py`
