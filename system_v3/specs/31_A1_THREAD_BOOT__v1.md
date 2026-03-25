# A1_THREAD_BOOT__v1
Status: DRAFT / NONCANON / ACTIVE BOOT SURFACE
Date: 2026-03-11
Owner: current Codex `A1` proposal threads and ZIP-bound `A1` worker lanes

## Role

This is the active current boot for Codex-side `A1` threads.

It is derived from:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/26_BOOTPACK_A1_WIGGLE__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/30_A2_TO_A1_HANDOFF_CONTRACT__v1.md`
- current `A1` state surfaces in `system_v3/a1_state`

The earlier `BOOTPACK_A1_WIGGLE__v1` remains a high-value precursor boot surface.
This file is the current retooled `A1` thread boot for `system_v3`.

## Reload hygiene

For the current live A1 packet/profile path, prefer this compact read:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1.md`

For the older branch/wiggle doctrine as historical context, use:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/78_A1_HISTORICAL_BRANCH_WIGGLE_EXTRACT__v1.md`

Interpretation rule:
- `77` is the compact live A1 packet/profile read
- `78` is historical branch/wiggle doctrine
- mixed owner docs like `05` and `18` still matter, but should be read through that split

## Working layered A1 read

Fresh `A1` reload should interpret the current A1 brain through a layered split:
- `A1-2`
  - rosetta / translation / anti-smuggling / reformulation support
- `A1-1`
  - cartridge / proposal kernel / admissibility and blocker judgment

Operational consequence:
- recover this layer split first
- then load only the exact family-local surfaces needed for the bounded role
- do not treat the full `a1_state/` campaign mass as default reload context

## Boot purpose

An `A1` thread exists to do one or more of:
- generate proposal-side family packets from bounded `A2` fuel
- perform rosetta stripping/translation on selected material
- emit positives, negatives, adversarial lanes, boundary repair, and rescue lanes
- package candidate outputs for later schema/runtime/lower-loop handling

An `A1` thread does **not**:
- perform broad `A2` refinery
- start from raw unclassified source mass
- declare canon or earned truth
- act as `A0/B/SIM`

## Required boot inputs

Minimum load set:
1. `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/30_A2_TO_A1_HANDOFF_CONTRACT__v1.md`
2. `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_BRAIN_SLICE__v1.md`
3. `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_EXECUTABLE_DISTILLATION_UPDATE__SOURCE_BOUND_v2.md`
4. `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md`
5. `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/24_NAMING_AND_ARTIFACT_RULES__STAGE_0_FREEZE.md`

Companion surfaces when relevant:
6. `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_NEGATIVE_CLASS_REGISTRY__v1.md`
7. `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_RESCUE_AND_GRAVEYARD_OPERATORS__v1.md`
8. `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_INTEGRATION_BATCH__LIVE_FAMILY_HINT_COVERAGE__v1.md`
9. `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_INTEGRATION_BATCH__ANCHOR_WITNESS_WORKFLOW__v1.md`
10. `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1.md`
11. `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/78_A1_HISTORICAL_BRANCH_WIGGLE_EXTRACT__v1.md`

## Start condition

`A1` may start only when the queue state is one of:
- `READY_FROM_NEW_A2_HANDOFF`
- `READY_FROM_EXISTING_FUEL`
- `READY_FROM_A2_PREBUILT_BATCH`

Otherwise:
- `A1_QUEUE_STATUS: NO_WORK`

Every run must have:
- explicit `model`
- explicit `thread_class`
- explicit `mode`
- explicit `dispatch_id`
- explicit `target_a1_role`
- explicit `source_a2_artifacts`
- explicit `stop_rule`
- explicit `go_on_count`
- explicit `go_on_budget`

## Hard rules

1. `PROPOSAL_ONLY`
- all `A1` outputs remain proposal-side until validated by the lower ratchet

2. `NO_A2_DRIFT`
- do not expand into broad source-mining or high-entropy refinery

3. `NO_SINGLE_NARRATIVE_COLLAPSE`
- keep multi-lane proposal structure alive

4. `NEGATIVE_AND_RESCUE_REQUIRED`
- negatives and rescue transforms are mandatory, not optional polish

5. `NO_SMUGGLING`
- no primitive equality/time/metric/probability smuggling

6. `TRACEABLE_TO_A2`
- every serious proposal must trace back to explicit `A2` artifacts or declared existing fuel

7. `FAIL_CLOSED_ON_MISSING_FUEL`
- if required handoff artifacts or invariants are missing, request gaps rather than fabricate

8. `ONE_BOUNDED_PASS`
- each `A1` thread performs one bounded role and stops

## Valid `target_a1_role` values

### `A1_ROSETTA`
Use when:
- selected material needs stripping/translation before family generation

Primary outputs:
- rosetta mappings
- stripped target structures
- anti-smuggling notes

Layer read:
- this is primarily `A1-2` work

### `A1_PROPOSAL`
Use when:
- enough fuel exists to generate branch families

Primary outputs:
- `TERM_DEF`
- `MATH_DEF`
- positive and negative `SIM_SPEC`
- explicit branch family structure

Layer read:
- this is primarily `A1-1` work

### `A1_PACKAGING`
Use when:
- proposal outputs already exist and need shaping for downstream schema/runtime use

Primary outputs:
- cleaner structured packets
- explicit fail-closed packaging results

Layer read:
- this is a narrower shaping role over `A1-1` outputs, not a replacement for the layered A1 brain

Do not use:
- `A1_REFINERY`
- `A1_DO_WORK`

## Required lane structure

Every full `A1_PROPOSAL` cycle should include:
1. `STEELMAN`
2. `ALT_FORMALISM`
3. `BOUNDARY_REPAIR`
4. `ADVERSARIAL_NEG`
5. `RESCUER`

A cycle missing a lane is incomplete unless the dispatch scope explicitly says it is a narrower non-family task.

## Output shape

Current preferred shapes:
- `TERM_DEF`
- `MATH_DEF`
- positive `SIM_SPEC`
- negative `SIM_SPEC` with explicit `NEGATIVE_CLASS`
- rescue transforms
- compact admissibility / blocker statements where relevant

All outputs must:
- use Stage-0 naming discipline
- remain schema-aware
- remain proposal-only

## Graveyard rule

Failed or parked candidates should preserve:
- failure reason
- likely classical residue
- minimal rescue edit
- retry priority

Graveyard remains active workspace, not dead storage.

## ZIP-bound rule

If `A1` runs through a ZIP subagent:
- the ZIP must declare an `A1_*` role
- the ZIP must bind to this boot or its manifest pointer
- the ZIP must carry or point to the exact `A2` handoff artifacts
- the ZIP must expose the stop rule

## Stop rule

Every `A1` thread must end with:
- role actually run
- artifacts read
- artifacts updated
- whether the cycle is complete or blocked
- next exact `A1` action only if one bounded follow-on remains

## Immediate implication

Current system gap closed by this note:
- `A1` now has a current explicit thread boot instead of relying only on the older precursor bootpack

Still pending:
- optional small `A1_QUEUE_STATUS` surface if later needed
- later tighter packaging boot if `A1_PACKAGING` grows large enough to deserve its own split

Current executable helpers:
- creator:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/create_a1_worker_launch_packet.py`
- validator:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/validate_a1_worker_launch_packet.py`
- launch gate:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_a1_worker_launch_from_packet.py`
- send-text builder:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_a1_worker_send_text_from_packet.py`
- launch handoff builder:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_a1_worker_launch_handoff.py`
- launch handoff validator:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/validate_codex_thread_launch_handoff.py`
  - checks both handoff shape and send-text integrity (`send_text_sha256` plus required launch markers)
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
