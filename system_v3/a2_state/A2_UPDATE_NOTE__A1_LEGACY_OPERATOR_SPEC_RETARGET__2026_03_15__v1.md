# A2_UPDATE_NOTE__A1_LEGACY_OPERATOR_SPEC_RETARGET__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the spec-level cleanup where the two remaining legacy A1 operator-vocabulary surfaces stop reading like live runtime law

## Scope

Patched draft specs:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/18_A1_WIGGLE_EXECUTION_CONTRACT.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/05_A1_STRATEGY_AND_REPAIR_SPEC.md`

Grounding anchors:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/00_README.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/ENUM_REGISTRY_v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/A1_REPAIR_OPERATOR_MAPPING_v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/A1_STRATEGY_v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__A1_OPERATOR_DOCTRINE_SPLIT_AND_POLICY_SOURCE__2026_03_15__v1.md`

## Problem

After the operator-doctrine split audit, the repo still had two draft specs whose operator sections could be misread as live runtime law:
- `18_A1_WIGGLE_EXECUTION_CONTRACT.md`
- `05_A1_STRATEGY_AND_REPAIR_SPEC.md`

That was a reload hazard because the live runtime/control path is already grounded in the control-plane operator enum/mapping, not those older operator vocabularies.

## What changed

### 1) `18_A1_WIGGLE_EXECUTION_CONTRACT.md`

Added an explicit `Live Operator Law Note` near the top:
- says the document remains draft/noncanon branch-model doctrine
- says its operator/quota model is not the active runtime/control-plane operator law
- points readers to:
  - `ENUM_REGISTRY_v1.md`
  - `A1_REPAIR_OPERATOR_MAPPING_v1.md`
  - `A1_STRATEGY_v1.md`

Retargeted section labels:
- `Operator Set (Deterministic IDs)` -> `Legacy Operator Set (Historical Draft IDs)`
- `Operator Quota Table (Default)` -> `Legacy Operator Quota Table (Historical Draft)`
- `Stall Detection and Rebalance` -> `Legacy Stall Detection and Rebalance (Historical Draft)`

Meaning:
- the old branch/quota model is preserved for provenance
- it is no longer presented as current live operator doctrine

### 2) `05_A1_STRATEGY_AND_REPAIR_SPEC.md`

Added an explicit `Live Operator Law Note` near the top:
- points to the control-plane operator enum/mapping and strategy schema
- says the older repair operator vocabulary later in the draft is legacy/nonactive doctrine

Retargeted section labels:
- `Branch Scheduler` -> `Legacy Branch Scheduler`
- `Repair Loop` -> `Legacy Repair Loop Vocabulary`
- `Wiggle Model` -> `Legacy Wiggle Model`
- `Novelty Floor` -> `Legacy Novelty Floor`
- `Branch Lifecycle` -> `Legacy Branch Lifecycle`
- `Stall Behavior` -> `Legacy Stall Behavior`

Meaning:
- the mixed draft still keeps useful live packet-profile material
- but the old repair-loop operator subsection is no longer silently presented as current runtime law

## Result

The repo now says this more honestly:
- live runtime/control operator law comes from the control-plane bundle
- the remaining old operator vocabularies survive only as legacy draft doctrine

That reduces reload ambiguity without inventing a new operator model.

## Verification

Grounded grep checks:
- `rg -n "Live Operator Law Note|Legacy Operator Set|Legacy Operator Quota Table|Legacy Repair Loop Vocabulary|Legacy Branch Scheduler" system_v3/specs/18_A1_WIGGLE_EXECUTION_CONTRACT.md system_v3/specs/05_A1_STRATEGY_AND_REPAIR_SPEC.md`
- confirmed the new retarget markers are present

Legacy operator-name localization:
- `rg -n "OP_REORDER_DEPS|OP_REBIND|OP_ALT_REWRITE|OP_SIM_EXPAND|OP_PROBE_REBALANCE|OP_SPLIT_COMPOUND|OP_COMPOSE_COMPOUND|OP_ALT_FOR_FAILURE_MODE|OP_GRAVEYARD_RESCUE|OP_PROBE_BALANCE" system_v3`
- result:
  - legacy names remain in the two draft specs above
  - plus the derived A2 reset note that records the split

No runtime code changed in this step.

## Next seam

Best next move is narrower doctrinal cleanup:
- decide whether to further split `05_A1_STRATEGY_AND_REPAIR_SPEC.md` into:
  - still-useful live packet/profile material
  - clearly historical branch/repair vocabulary
- or leave it as a mixed draft now that the legacy sections are explicitly labeled
