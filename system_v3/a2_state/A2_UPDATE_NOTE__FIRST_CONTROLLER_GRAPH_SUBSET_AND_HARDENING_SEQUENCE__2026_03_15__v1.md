# A2_UPDATE_NOTE__FIRST_CONTROLLER_GRAPH_SUBSET_AND_HARDENING_SEQUENCE__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 CONTROL NOTE
Date: 2026-03-15
Role: preserve the recommended next-step hardening order and the first bounded graph subset for the local spec-object/controller path

## Scope

This note captures the current controller-thread recommendation after:
- the family-slice object path became live
- queue/controller/launch surfaces were partially objectified
- review found remaining validator split, provenance, and queue-integrity seams

This is a `DERIVED_A2` routing note.
It does not promote new doctrine or reclassify owner surfaces.

## Immediate sequencing

The next work should not jump straight to a big graph or graph DB.

The recommended order is:

1. unify the family-slice validator law
2. stamp validation provenance into emitted artifacts
3. harden queue/bundle integrity
4. refresh generated schema artifacts automatically
5. only then build the first bounded controller graph subset

## Why this order

Current risk is not lack of graph machinery.
Current risk is that the new object layer is still not one trustworthy contract boundary.

Known open seams:
- manual JSON schema vs live Pydantic/runtime drift
- `auto` validator path changing by machine
- queue packet only proving staged artifacts exist, not that they cohere
- generated Pydantic schema artifacts drifting behind live models

So the graph step should come after substrate hardening, not before.

## Immediate hardening targets

### 1) Validator unification

Bring these into the same law:
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1.schema.json`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/a2_to_a1_family_slice_models.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`

Goal:
- one family slice should not pass prep and fail later because validators disagree

### 2) Validation provenance stamping

Emitted artifacts should record:
- requested validation mode
- resolved validation mode
- validator source
- schema/model version reference if relevant

At minimum on:
- A1 worker launch packet
- family-slice launch bundle result
- A1 queue status packet
- active current queue refresh result

### 3) Queue/bundle integrity hardening

Queue-ready surfaces should prove that the staged references cohere:
- `ready_packet_json`
- `ready_bundle_result_json`
- `ready_send_text_companion_json`
- `ready_launch_spine_json`

Checks should prove shared identity such as:
- dispatch id
- packet hash
- send-text hash
- launch packet path

### 4) Generated schema refresh

The checked-in emitted schema artifacts should be either:
- auto-refreshed by a bounded tool path
- or clearly marked stale/generated-nonowner and removed from “current” reload guidance

## First bounded graph subset

After the hardening above, the first graph should stay small and controller-facing.

Recommended initial node set:
- `family_slice`
- `queue_candidate_registry`
- `queue_status_packet`
- `a1_worker_launch_packet`
- `a1_worker_send_text_companion`
- `a1_worker_launch_handoff`
- `a1_worker_launch_spine`
- `a2_controller_launch_packet`
- `a2_controller_launch_handoff`
- `a2_controller_launch_spine`

Recommended initial edge set:
- `compiled_into`
- `selected_into`
- `emits`
- `requires_reload_artifact`
- `derived_from`
- `validated_by`
- `handoff_for`
- `supersedes`
- `current_pointer_to`

## Why this subset first

This slice is the best first graph target because it is:
- already partially objectified
- controller-facing
- small enough to reason about
- directly tied to fresh-thread reload and dispatch
- where current integrity/provenance problems are already visible

This is a much better first graph than:
- whole-system markdown graph
- all specs at once
- graph DB migration

## What not to do yet

Do not jump yet to:
- a full repo-wide graph compiler
- a graph-native database
- invariant/TLA/counterexample runtime
- hostile validator-agent society

Those may still be good later.
But they should sit on top of a hardened object/provenance substrate.

## Suggested bounded external-thread jobs

If external Codex worker threads are used, the best bounded jobs now are:

1. `validator_unification_and_provenance_patch`
- unify family-slice validation law
- stamp validation provenance into emitted packet/bundle/queue artifacts

2. `queue_integrity_hardening`
- make queue-ready bundle references prove shared identity rather than mere file existence

3. `first_controller_graph_subset`
- build one small graph compiler over the controller/A1 launch surfaces above
- emit one compiled reload/dispatch slice from that graph

## Reload use

On reload, this note should be read after:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__THREAD_RELOAD_SPINE_AND_RUN_BLOAT_AUDIT__2026_03_15__v1.md`

Use it to decide:
- whether to keep hardening the object substrate
- or whether the first bounded graph subset is ready to begin
