# A2_UPDATE_NOTE__RUN_REAL_LOOP_OPERATOR_DOC_RETARGET__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 CONTROL NOTE
Date: 2026-03-15
Role: preserve the canonical operator-doc retarget for strict vs recovery real-loop entrypoints

## Scope

This note is bounded to the documented operator surface for the real-loop helper.

Patched owner surface:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/22_RUN_SURFACE_TEMPLATE_AND_SCAFFOLDER_CONTRACT.md`

## What changed

The run-surface spec now distinguishes:
- strict/default entrypoint:
  - `system_v3/tools/run_real_loop.py`
- explicit recovery entrypoint:
  - `system_v3/tools/run_real_loop_recovery_cycle.py`

It now also states that:
- default strict mode fails closed on missing canonical runtime artifacts
- recovery should use the dedicated recovery entrypoint
- `run_real_loop.py --allow-reconstructed-artifacts` is now a lower-level compatibility path, not the preferred operator surface

## Meaning

This closes an operator-discoverability gap created by the recent reset work.

Before this patch:
- code and A2 notes knew about the recovery entrypoint
- the main run-surface spec did not

After this patch:
- the canonical live helper spec reflects the new split

## Verification

No runtime logic changed in this step.
This was a doc retarget only, on top of the already-verified recovery entrypoint and test coverage.

## Next seam

Best next move:
- audit any remaining helper docs or bridges that still narrate recovery mainly as a flag on `run_real_loop.py`
- then decide whether the compatibility flag should eventually be deprecated from the strict runner
