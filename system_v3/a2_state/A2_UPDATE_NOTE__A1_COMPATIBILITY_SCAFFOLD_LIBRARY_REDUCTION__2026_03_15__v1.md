# A2_UPDATE_NOTE__A1_COMPATIBILITY_SCAFFOLD_LIBRARY_REDUCTION__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the reset step where legacy A1 compatibility profiles stop expanding into whole hardcoded campaign tables and are reduced to explicit scaffold-sized term libraries

## Scope

Primary runtime files:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/autoratchet.py`

Focused regressions:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_autoratchet_family_slice.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_autoratchet_controller_result.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_wiggle_control_cycle.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py`

## Why this reset step was needed

Earlier reset work already made family-slice mode the expected path and forced explicit legacy override for goal-profile mode.

But compatibility mode still carried too much real policy because the fallback profile names still mapped to large hardcoded goal tables such as:
- `REFINED_FUEL_GOALS`
- `EXTENDED_GOALS`
- `ENTROPY_BRIDGE_GOALS`
- `ENTROPY_BOOKKEEPING_BRIDGE_GOALS`

That meant the code could still act as if a legacy profile name implied a whole doctrine-sized campaign surface.

## Source-grounded reduction rule

The new compatibility read is:
- legacy profile mode = scaffold-only
- family-slice mode = the place where real bounded family meaning should live

This reduction is grounded by the A1 family docs:
- first substrate scaffold is the five-term substrate family with `probe_operator` as active head and `partial_trace` in floor support:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_FIRST_SUBSTRATE_FAMILY_CAMPAIGN__v1.md`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_CARTRIDGE_REVIEW__PROBE_OPERATOR__v1.md`
- entropy executable entrypoint is narrower than the broader bridge proposal surface and keeps `correlation_polarity` as current executable head while `entropy_production_rate` remains passenger-side:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_ENTROPY_EXECUTABLE_ENTRYPOINT__v1.md`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_FIRST_ENTROPY_BRIDGE_CAMPAIGN__v1.md`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_TARGET_FAMILY_MODEL__v1.md`

## What changed

### 1) Planner compatibility path now uses reduced scaffold term libraries

`a1_adaptive_ratchet_planner.py` now defines:
- `COMPATIBILITY_SCAFFOLD_TERMS_BY_PROFILE`
- `_compatibility_scaffold_terms_for_profile(...)`

and `legacy` goal-profile mode now resolves through those reduced term lists rather than the old large goal tuples.

Important reductions:
- `refined_fuel` no longer implies the whole historical refined-fuel ladder
- `refined_fuel` compatibility now resolves to a small substrate scaffold
- `entropy_bridge` compatibility now resolves to a narrow executable scaffold centered on `correlation_polarity`
- `entropy_bookkeeping_bridge` compatibility keeps `correlation_polarity` plus `density_entropy` instead of promoting `entropy_production_rate` as a head

### 2) Autoratchet semantic-gate expectations were reduced to the same scaffold scale

`autoratchet.py` now derives both:
- compatibility goal terms
- compatibility required probe terms

from the same reduced scaffold library.

That removes the old mismatch where legacy compatibility mode could still require wide probe surfaces like:
- `qit_master_conjunction`
- broad entropy bridge witness terms

even after controller/runtime reset work had already demoted profile mode to compatibility-only.

## Meaning

This does **not** make the planner fully doctrine-aligned.

It does make the legacy surface much smaller and more honest:
- compatibility profile names no longer secretly stand in for a whole sprawling campaign
- family-slice mode is now more clearly the only route for real family-scale planning

## Verification

Compile:
- `python3 -m py_compile system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tools/autoratchet.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_autoratchet_family_slice.py`

Focused tests:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_a1_adaptive_ratchet_planner.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_autoratchet_family_slice.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_autoratchet_controller_result.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_autoratchet_cycle_audit.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_a1_wiggle_control_cycle.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_run_real_loop.py`
- result:
  - `Ran 35 tests ... OK`

## Remaining drift

One important planner drift still remains after this step:
- family-slice terms still inherit some old known-term track identities when the same term appears in multiple historical goal families

That means family-slice control has improved, but some track labeling still reflects old table history.

## Next seam

Best next move:
- reduce or remove old known-goal track inheritance for family-slice-controlled planning
- make family-slice-controlled track/branch metadata derive from the slice itself rather than whichever historical tuple first defined the term
