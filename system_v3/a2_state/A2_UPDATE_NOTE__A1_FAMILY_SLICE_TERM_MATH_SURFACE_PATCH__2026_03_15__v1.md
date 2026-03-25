# A2_UPDATE_NOTE__A1_FAMILY_SLICE_TERM_MATH_SURFACE_PATCH__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the reset step where family-slice-controlled planning can now carry term-level math-surface definitions instead of always inheriting the universal minimal planner templates

## Scope

Contract/work surfaces:
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1.schema.json`
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json`

Primary runtime/audit files:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_a1_autoratchet_cycle_audit.py`

Focused regressions:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`
- plus the standing focused family-slice/controller suite

## Problem

Even after:
- family-slice path outranked goal-profile path
- compatibility profiles were reduced to scaffold libraries
- family-slice tracks and negative obligations were made slice-owned

the planner still carried one more universal legacy seam:
- `MINIMAL_SUBSTRATE_MATH_SURFACES`

Family-slice-controlled planning still reused those universal term templates directly, which meant the active path did not yet fully own its own term-surface definitions.

## What changed

### 1) The family-slice contract now allows explicit term-level math surfaces

The draft schema now includes optional:
- `term_math_surfaces`

Each term entry carries:
- `objects`
- `operations`
- `invariants`
- `domain`
- `codomain`

The sample substrate family slice now includes explicit `term_math_surfaces` for:
- `finite_dimensional_hilbert_space`
- `density_matrix`
- `probe_operator`
- `cptp_channel`
- `partial_trace`

### 2) Planner now prefers family-slice math surfaces over universal templates

`a1_adaptive_ratchet_planner.py` now adds:
- `_family_slice_math_surface_for_term(...)`

Behavior:
- if `family_slice.term_math_surfaces[term]` exists and is complete, planner uses it first
- only if no slice-owned surface is present does planner fall back to the older `MINIMAL_SUBSTRATE_MATH_SURFACES`

So the active family-slice path can now define its own math-surface payloads instead of silently inheriting the universal planner defaults.

### 3) Strategy self-audit and cycle audit now expose this surface ownership

Planner `self_audit` now includes:
- `family_slice_math_surface_terms`

Cycle audit now checks:
- `AUTORATCHET_FAMILY_SLICE_MATH_SURFACES_VISIBLE`

So controller-facing auditing can now tell whether a family slice declared term-surface ownership and whether that declaration remained visible through emitted strategy metadata.

## Meaning

This is not the full end of hardcoded planner surface inheritance.

But it is a real reset improvement:
- family slices can now own term-local math surfaces
- the planner prefers slice-owned definitions
- the audit path can see that ownership

That makes the active family-slice path less like “legacy planner with better routing” and more like a genuinely slice-driven planning mode.

## Verification

Focused tests:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_autoratchet_family_slice.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_autoratchet_controller_result.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_wiggle_control_cycle.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py`
- result:
  - `Ran 40 tests ... OK`

Schema/sample validation:
- `jsonschema.validate(...)` passed for:
  - `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1.schema.json`
  - `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json`

## Next seam

Best next move:
- inspect the remaining universal planner laws that still apply inside family-slice mode
- especially:
  - target-class naming
  - tier defaults
  - broad negative-branch expansion logic in graveyard-first mode
