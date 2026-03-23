# A2_UPDATE_NOTE__A1_FAMILY_SLICE_TARGET_CLASS_AND_GRAVEYARD_NEG_PATCH__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the reset step where family-slice mode now owns target-class naming and graveyard-first negative expansion instead of inheriting those universal planner laws

## Scope

Primary runtime/audit files:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/run_a1_autoratchet_cycle_audit.py`

Focused regressions:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`
- plus the standing focused family-slice/controller suite

## Problem

After the earlier reset steps:
- family-slice mode owned routing
- family-slice mode owned tracks
- family-slice mode owned negative obligations
- family-slice mode could own term-level math surfaces

but two more planner laws were still too universal:

1. target-class naming still came from planner-global track law  
2. graveyard-first negative expansion still carried a hidden planner fallback shape

That meant family-slice mode was better than before, but still not fully defining its own branch identity and negative-pressure spread.

## What changed

### 1) Family-slice target classes now derive from family identity

`a1_adaptive_ratchet_planner.py` now adds:
- `_family_slice_target_class_prefix(...)`
- `_family_slice_target_class(...)`

When `family_slice` is present:
- target class no longer defaults to `TC_<track>`
- target class now derives from the slice family identity

Current shape:
- `TC_FAMILY_<family_id_or_kind>_<term>`

So family-slice-controlled planning now carries family-local target-class naming instead of silently inheriting older track-driven target classes.

### 2) Graveyard-first negative expansion now uses the slice-owned negative class set

`a1_adaptive_ratchet_planner.py` now adds:
- `_graveyard_negative_classes_for_mode(...)`

Behavior:
- if a family slice is present, graveyard-first expansion uses the slice’s ordered negative classes
- planner-global broad fallback classes are only used when no family slice is present

That means graveyard-validity family runs no longer quietly widen through a hidden universal planner list first.

### 3) Planner self-audit now exposes both surfaces

Planner `self_audit` now includes:
- `family_slice_target_class_prefix`
- `strategy_target_class`
- `graveyard_negative_classes_used`

### 4) Cycle audit now verifies both surfaces

`run_a1_autoratchet_cycle_audit.py` now checks:
- `AUTORATCHET_FAMILY_SLICE_TARGET_CLASS_VISIBLE`
- `AUTORATCHET_FAMILY_SLICE_GRAVEYARD_NEGATIVE_CLASSES_VISIBLE`

The graveyard-negative check is only strict for:
- `family_slice.run_mode == GRAVEYARD_VALIDITY`

So scaffold runs are not over-constrained by a graveyard-validity-specific audit rule.

## Meaning

This is another real reduction of planner-global doctrine leakage.

After this patch:
- family-slice mode owns target-class naming
- graveyard-validity family runs use slice-owned negative expansion
- controller-visible auditing can see both

That still does not mean the whole planner is now fully slice-defined.
But it removes two more universal control laws from the active family-slice path.

## Verification

Focused tests:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_autoratchet_family_slice.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_autoratchet_controller_result.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_wiggle_control_cycle.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py`
- result:
  - `Ran 43 tests ... OK`

## Next seam

Best next move:
- inspect the remaining family-slice inheritance inside planner-global defaults
- especially:
  - sim tier derivation
  - probe-term derivation
  - operator-id defaults on emitted structural/negative branches
