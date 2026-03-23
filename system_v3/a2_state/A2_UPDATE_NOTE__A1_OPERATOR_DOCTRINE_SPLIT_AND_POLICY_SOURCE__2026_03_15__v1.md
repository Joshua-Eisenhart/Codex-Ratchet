# A2_UPDATE_NOTE__A1_OPERATOR_DOCTRINE_SPLIT_AND_POLICY_SOURCE__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the grounded operator-doctrine split audit and the small follow-through patch that makes the live operator-policy source visible in planner/audit/controller surfaces

## Scope

Audit anchors:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/18_A1_WIGGLE_EXECUTION_CONTRACT.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/05_A1_STRATEGY_AND_REPAIR_SPEC.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/00_README.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/ENUM_REGISTRY_v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/A1_REPAIR_OPERATOR_MAPPING_v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/A1_STRATEGY_v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/a0_compiler.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/a1_request_to_codex_prompt.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/run_a1_autoratchet_cycle_audit.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/build_a1_autoratchet_controller_result.py`

Focused regressions:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_autoratchet_controller_result.py`

## Problem

The repo is still speaking two different operator languages.

Live runtime/control surfaces use the control-plane operator enum and repair mapping:
- `OP_BIND_SIM`
- `OP_REPAIR_DEF_FIELD`
- `OP_MUTATE_LEXEME`
- `OP_REORDER_DEPENDENCIES`
- `OP_NEG_SIM_EXPAND`
- `OP_INJECT_PROBE`

But two older draft specs still define a different A1 wiggle/repair operator law:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/18_A1_WIGGLE_EXECUTION_CONTRACT.md`
  - `OP_SPLIT_COMPOUND`
  - `OP_COMPOSE_COMPOUND`
  - `OP_ALT_FOR_FAILURE_MODE`
  - `OP_GRAVEYARD_RESCUE`
  - `OP_PROBE_BALANCE`
  - plus a cycle quota table
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/05_A1_STRATEGY_AND_REPAIR_SPEC.md`
  - `OP_REORDER_DEPS`
  - `OP_SPLIT_COMPOUND`
  - `OP_REBIND`
  - `OP_ALT_REWRITE`
  - `OP_SIM_EXPAND`
  - `OP_PROBE_REBALANCE`

That split is now small enough to state precisely:
- the live path does **not** implement the legacy wiggle operator sets
- the legacy operator names are localized to the two draft/noncanon specs above

## Grounded read

### 1) Active live operator doctrine

The active runtime/control path is grounded in the control-plane bundle:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/00_README.md`
  - says the bundle is the frozen single source-of-truth spec suite and disagreements should be treated as bugs
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/ENUM_REGISTRY_v1.md`
  - says enum sets listed there must not be redefined elsewhere
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/A1_REPAIR_OPERATOR_MAPPING_v1.md`
  - says `operator_id` values are defined exclusively in `ENUM_REGISTRY_v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/A1_STRATEGY_v1.md`
  - requires proposal `operator_id` to be in that control-plane repair enum

The live code agrees with that bundle:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/a0_compiler.py`
  - only implements repair/application functions for the control-plane operator family
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`
  - emits `OP_BIND_SIM`, `OP_REPAIR_DEF_FIELD`, `OP_MUTATE_LEXEME`, `OP_REORDER_DEPENDENCIES`, `OP_NEG_SIM_EXPAND`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/a1_request_to_codex_prompt.py`
  - narrates the live family/operator map:
    - `BASELINE -> OP_BIND_SIM`
    - `BOUNDARY_SWEEP -> OP_REPAIR_DEF_FIELD`
    - `PERTURBATION -> OP_MUTATE_LEXEME`
    - `COMPOSITION_STRESS -> OP_REORDER_DEPENDENCIES`
    - `ADVERSARIAL_NEG -> OP_NEG_SIM_EXPAND`

### 2) Legacy / nonactive operator doctrine

`18_A1_WIGGLE_EXECUTION_CONTRACT.md` is explicitly `DRAFT / NONCANON`, and its operator/quota system is not the active runtime law.

`05_A1_STRATEGY_AND_REPAIR_SPEC.md` is mixed:
- its live packet-profile sections still describe current A1 packet reality reasonably well
- but its `Repair Loop` and `Branch Scheduler` operator sections preserve an older operator vocabulary that the live runtime does not use

So the right reading is not:
- “throw out 05 entirely”

It is:
- keep using 05 as a mixed draft/spec memory surface
- treat the older repair operator subsection there as legacy drift until rewritten or demoted

## Repo-localized mismatch

A repo-wide grep for the old operator names now localizes them to:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/18_A1_WIGGLE_EXECUTION_CONTRACT.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/05_A1_STRATEGY_AND_REPAIR_SPEC.md`

That is useful because it means the live runtime itself is no longer half-using both languages.
The remaining split is mostly doctrinal/documentary.

## Small follow-through patch

After the audit, the live planner/audit/controller path now exposes the active operator-policy source explicitly instead of making controllers infer it from emitted operator ids.

### Planner self-audit

`/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`

Family-slice strategy self-audit now includes:
- `operator_policy_sources = ["ENUM_REGISTRY_v1", "A1_REPAIR_OPERATOR_MAPPING_v1"]`

### Cycle audit

`/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/run_a1_autoratchet_cycle_audit.py`

Family-slice audit now checks:
- `AUTORATCHET_FAMILY_SLICE_OPERATOR_POLICY_SOURCES_VISIBLE`
- `AUTORATCHET_FAMILY_SLICE_OPERATOR_POLICY_SOURCES_CANONICAL`

and preserves:
- `operator_policy_sources`

in the audit report.

### Controller result

`/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/build_a1_autoratchet_controller_result.py`

Controller result now carries:
- `operator_policy_sources`

so controller reads no longer have to guess which operator doctrine the run actually used.

## Meaning

This patch does **not** make family slices own operator policy.

It only does the safer thing:
- preserve the operator-doctrine split honestly
- mark the live path as using the control-plane operator law
- make that visible in planner/audit/controller surfaces

So the system is now better prepared for the next decision without pretending it has already been made.

## Verification

Focused validation:
- `python3 -m py_compile system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py system_v3/tools/run_a1_autoratchet_cycle_audit.py system_v3/tools/build_a1_autoratchet_controller_result.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_autoratchet_controller_result.py`
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_autoratchet_controller_result.py`
- result:
  - `Ran 30 tests ... OK`

Repo sweep for legacy operator names:
- `python3` not needed; `rg` localized them to:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/18_A1_WIGGLE_EXECUTION_CONTRACT.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/05_A1_STRATEGY_AND_REPAIR_SPEC.md`

## Next seam

Best next move is still doctrinal cleanup, not new operator invention:
- demote or retarget the legacy operator sections in `18_A1_WIGGLE_EXECUTION_CONTRACT.md`
- isolate the still-useful live packet/profile parts of `05_A1_STRATEGY_AND_REPAIR_SPEC.md` from its legacy repair-loop subsection
- only after that decide whether bounded family slices should own operator policy, or whether operator policy stays fixed in the live control-plane law
