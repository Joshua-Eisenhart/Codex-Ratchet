# A2_UPDATE_NOTE__A1_FAMILY_SLICE_CONTRACT__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 CONTROL NOTE
Date: 2026-03-15
Role: propose the bounded A2-derived family-slice object that should replace ladder-scripted planner input for the active A1 path

## Scope

This note proposes one replacement input contract for the active A1 planner/orchestrator reset.

It is not a new owner-surface law yet.
It is a bounded controller-side proposal object for the first rewrite pass.

## Source basis

Primary handoff/doctrine surfaces:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/30_A2_TO_A1_HANDOFF_CONTRACT__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/31_A1_THREAD_BOOT__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_BRAIN_SLICE__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_EXECUTABLE_DISTILLATION_UPDATE__SOURCE_BOUND_v2.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_TARGET_FAMILY_MODEL__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_GRAVEYARD_FIRST_VALIDITY_PROFILE__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/A1_CONSOLIDATION_PREPACK_JOB__v1.md`

Reset plan anchor:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__A1_RUNTIME_FIRST_REWRITE_PLAN__2026_03_15__v1.md`

## Core claim

The active A1 planner should stop taking its main meaning from:
- fixed goal tuples
- fixed profile ladders
- hardcoded required-probe-term lists

and should instead take one bounded A2-derived input object of the form:

- `A2_TO_A1_FAMILY_SLICE_v1`

This object should be small enough to:
- survive controller reload
- be traced to explicit A2 surfaces
- define one bounded family campaign
- feed either:
  - scaffold/proof mode
  - graveyard-first validity mode

without forcing the planner to invent doctrine from code.

## Proposed object purpose

One `A2_TO_A1_FAMILY_SLICE_v1` object should answer:
- what family is in scope
- what mode this run is
- what lanes must exist
- what negatives and rescue obligations are mandatory
- what admissibility placement currently exists
- what SIM/evidence obligations apply
- what exact sources/contradictions from A2 justify the campaign
- what the planner is forbidden to do

## Proposed top-level fields

### 1) Identity and routing

- `schema`
  - `A2_TO_A1_FAMILY_SLICE_v1`
- `slice_id`
- `dispatch_id`
- `target_a1_role`
  - expected default: `A1_PROPOSAL`
- `run_mode`
  - `SCAFFOLD_PROOF`
  - `GRAVEYARD_VALIDITY`
- `bounded_scope`
- `stop_rule`

Purpose:
- keep the object aligned with the existing A2 -> A1 handoff contract

### 2) Provenance and source anchors

- `source_a2_artifacts[]`
- `source_refs[]`
- `contradiction_refs[]`
- `residue_cluster_refs[]`
- `family_hint_refs[]`
- `generated_from_update_note`

Purpose:
- enforce the rule that A1 starts from bounded A2 handoff, not ambient repo mass

### 3) Family identity

- `family_id`
- `family_label`
- `family_kind`
  - examples:
    - `SUBSTRATE_BASE`
    - `SUBSTRATE_ENRICHMENT`
    - `ENTROPY_BRIDGE`
    - `MANIFOLD_CANDIDATE`
    - `AXIS_CANDIDATE`
- `primary_target_terms[]`
- `companion_terms[]`
- `deferred_terms[]`

Purpose:
- define the actual concept family being ratcheted

### 4) Lane obligations

- `required_lanes[]`
  - expected members drawn from:
    - `STEELMAN`
    - `ALT_FORMALISM`
    - `BOUNDARY_REPAIR`
    - `ADVERSARIAL_NEG`
    - `RESCUER`
- `lane_minimums{}`
  - example:
    - `ADVERSARIAL_NEG.min_branches = 1`
    - `RESCUER.min_branches = 1`

Purpose:
- encode the A1 thread boot / brain-slice “full cycle” rule directly in the planner input

### 5) Branch-family obligations

- `primary_branch_requirement`
- `alternative_branch_requirement`
- `negative_branch_requirement`
- `rescue_branch_requirement`
- `expected_failure_modes[]`
- `lineage_requirements[]`

Purpose:
- encode the target-family model directly
- prevent flat one-branch planning

### 6) Graveyard / rescue policy

- `graveyard_policy`
  - `ACTIVE_WORKSPACE`
- `graveyard_fill_policy`
  - example:
    - `fuel_full_load`
    - `anchor_replay`
- `rescue_start_conditions`
  - `min_graveyard_count`
  - `min_kill_diversity`
  - `min_canonical_count`
- `graveyard_library_terms[]`
- `rescue_lineage_required`

Purpose:
- distinguish scaffold from graveyard-first validity mode
- encode when rescue is allowed to begin

### 7) Negative-class obligations

- `required_negative_classes[]`
- `negative_emphasis_classes[]`
- `blocked_smuggles[]`
  - expected defaults include:
    - `PRIMITIVE_EQUALS`
    - `CLASSICAL_TIME`
    - `PRIMITIVE_PROBABILITY`
    - `EUCLIDEAN_METRIC`

Purpose:
- keep the negative surface explicit and family-local

### 8) Admissibility placement

- `admissibility`
  - `executable_head`
  - `active_companion_floor`
  - `late_passengers`
  - `witness_only_terms`
  - `residue_terms`
  - `landing_blockers`
  - `witness_floor`
  - `current_readiness_status`

### 8.1) Family-aware admissibility hints

- `family_admissibility_hints`
  - `strategy_head_terms[]`
  - `forbid_strategy_head_terms[]`
  - `late_passenger_terms[]`
  - `witness_only_terms[]`
  - `residue_only_terms[]`
  - `landing_blocker_overrides{}`

Purpose:
- reuse the family/local role placement doctrine already present in A1 surfaces
- keep selector and planner from inventing role placement from scratch

### 9) SIM/evidence obligations

- `sim_hooks`
  - `required_sim_families[]`
  - `required_probe_terms[]`
  - `expected_tier_floor`
  - `promotion_contract_refs[]`
- `evidence_obligations`
  - `structural_ladder_required = true`
  - `sim_ladder_required = true`

Purpose:
- encode the coupled structural/evidence ladder from the distillation inputs

### 10) Planner guardrails

- `forbid_direct_repo_reload = true`
- `forbid_goal_ladder_substitution = true`
- `forbid_unlisted_head_promotion = true`
- `forbid_rescue_during_fill`
- `forbid_family_collapse`
- `forbid_missing_context_fabrication = true`

Purpose:
- make the reset explicit at the input-contract level

## Minimum viable payload

The smallest valid slice should still include:

1. identity/routing
2. source anchors
3. one family identity block
4. required lanes
5. required negative classes
6. graveyard/rescue policy
7. admissibility placement
8. SIM/evidence hooks
9. planner guardrails

If any of those are missing:
- planner should fail closed
- or return `REQUEST_A2_CONTEXT_GAP`

## Best immediate use

This object should first replace:
- the active planner input assumptions
- not the lower loop

First adoption path:
1. A2 emits one bounded family slice for one lane
2. planner consumes that slice instead of a profile tuple
3. `autoratchet.py` becomes a thin orchestrator over that slice
4. prepack/selector continue to normalize toward one strict pre-A0 surface

## First recommended family-slice targets

The first slices should be explicit and narrow:

### Slice A
- first substrate family scaffold proof

### Slice B
- first substrate family graveyard-validity run

### Slice C
- first entropy bridge family slice

Purpose:
- prove the new contract on one substrate family and one entropy family before broad rollout

## Hold

- Do not treat this note as final schema law yet.
- Do not rewrite owner surfaces from it alone.
- Do not widen it into a full graph/object universe before the first planner reset proves the shape is workable.

## Reload use

On reload, this note should answer:
- what exact object should replace ladder-scripted A1 planner input
- what fields are required
- why those fields come from doctrine rather than new vibes
