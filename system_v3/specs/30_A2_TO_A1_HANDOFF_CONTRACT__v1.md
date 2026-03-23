# A2_TO_A1_HANDOFF_CONTRACT__v1
Status: DRAFT / NONCANON / ACTIVE PROCEDURE SURFACE
Date: 2026-03-11
Owner: current Codex `A2` controller, `A1` proposal threads, and ZIP-bound A1 worker lanes

## Purpose

This note defines the exact handoff boundary between `A2` and `A1`.

Rule:
- `A2` prepares, distills, routes, and dispatches
- `A1` proposes from bounded fuel
- `A1` does not self-start from raw source mass or ambient thread memory

This contract is the current missing coordination surface between:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/26_BOOTPACK_A1_WIGGLE__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/29_ZIP_BOOT_BINDING_RULES__v1.md`

## Core split

### `A2`
Allowed to:
- read and refine source-bearing material
- preserve contradictions
- classify residues, negatives, and rescue opportunities
- build bounded handoff packets
- mark `A1` queue status

Not allowed to:
- free-run as `A1`
- claim proposal work has already happened
- silently hand raw high-entropy source mass directly to `A1`

### `A1`
Allowed to:
- generate proposal-side family packets
- perform rosetta stripping/translation on selected material
- emit positives, negatives, adversarials, repairs, and rescue candidates
- package structured proposal outputs for later `A0`/schema/runtime handling

Not allowed to:
- re-run broad `A2` refinery
- self-authorize canon
- treat overlays or loose summaries as sufficient fuel if required handoff fields are missing

## Valid `A1` start conditions

`A1` may start only under one of these queue states:
- `READY_FROM_NEW_A2_HANDOFF`
- `READY_FROM_EXISTING_FUEL`
- `READY_FROM_A2_PREBUILT_BATCH`

Otherwise:
- `A1_QUEUE_STATUS: NO_WORK`

## Minimum handoff packet

Every valid `A2 -> A1` handoff must declare:
- `dispatch_id`
- `handoff_status`
- `target_a1_role`
- `required_a1_boot`
- `source_a2_artifacts`
- `bounded_scope`
- `required_output_shape`
- `stop_rule`

Minimum required content:
1. one explicit `A2_UPDATE_NOTE` or equivalent current A2 distillation surface
2. one explicit contradiction/residue/readout surface if relevant
3. one explicit target scope for `A1`
4. one explicit stop boundary

## Allowed `target_a1_role` values

Current valid roles:
- `A1_ROSETTA`
- `A1_PROPOSAL`
- `A1_PACKAGING`

Do not use:
- ambiguous mixed roles like `A1_REFINERY`
- generic `A1_DO_WORK`

## Required `A1` boot binding

Every handoff must name the `A1` boot surface it expects.

Current required boot:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/31_A1_THREAD_BOOT__v1.md`

Current required working context:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a1_state/A1_BRAIN_SLICE__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1.md`

Precursor boot still relevant:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/26_BOOTPACK_A1_WIGGLE__v1.md`

Historical branch/wiggle context when needed:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/78_A1_HISTORICAL_BRANCH_WIGGLE_EXTRACT__v1.md`

## Required `A1` input classes

`A2` may hand `A1`:
- explicit update notes
- explicit impact notes
- explicit delta packets
- bounded `A2_TO_A1_FAMILY_SLICE_v1` objects
- explicit contradiction maps
- explicit residue clusters
- explicit rosetta mappings
- explicit queue/routing notes
- ZIP job packets already bound to an `A1` role and boot

`A2` may not hand `A1`:
- raw unclassified external-source dumps
- ambient controller memory
- “read the repo and figure it out” instructions

## `a1?` controller response contract

When asked `a1?`, the controller must return exactly one of:

### Case 1
- `A1_QUEUE_STATUS: NO_WORK`
- one short reason

### Case 2
- `A1_QUEUE_STATUS: READY_FROM_NEW_A2_HANDOFF`
- one exact bounded prompt
- explicit artifact list
- explicit required boot
- explicit stop rule

### Case 3
- `A1_QUEUE_STATUS: READY_FROM_EXISTING_FUEL`
- one exact bounded prompt
- explicit artifact list
- explicit required boot
- explicit stop rule

### Case 4
- `A1_QUEUE_STATUS: READY_FROM_A2_PREBUILT_BATCH`
- one exact bounded prompt
- explicit artifact list
- explicit required boot
- explicit stop rule

Current response surface:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/32_A1_QUEUE_STATUS_SURFACE__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/build_a1_queue_status_packet.py`

Preferred preparation path when a valid bounded family slice exists:
- ready-packet surface:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/34_A1_READY_PACKET__v1.md`
- family-slice packet compiler:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/build_a1_worker_launch_packet_from_family_slice.py`
- family-slice bundle preparer:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/prepare_a1_launch_bundle_from_family_slice.py`

Current validation-policy interpretation for that path:
- default validation mode is `auto`
- `auto` means:
  - use the local spec-object stack when `--spec-graph-python` exists
  - otherwise fall back to the hand-written JSON schema path

## ZIP-bound handoff rule

If `A1` is being run through ZIP subagents:
- the ZIP must declare `ROLE = A1_*`
- the ZIP must bind to the same boot and stop rule named in the handoff
- the ZIP must carry or point to the exact A2 handoff artifacts

## Stop rule

An `A2 -> A1` handoff is complete only when:
- the handoff role is explicit
- the `A1` boot is explicit
- the artifact list is explicit
- the stop rule is explicit

If any of those are missing:
- do not dispatch
- return `BLOCKED_MISSING_ARTIFACTS` or `BLOCKED_MISSING_BOOT`

## Immediate implication

Current system gap closed by this note:
- `A2` now has a current repo-held rule for how it may dispatch `A1`

Still pending:
- explicit current `A1_THREAD_BOOT`
- a small queue-status surface or controller packet format if later needed
