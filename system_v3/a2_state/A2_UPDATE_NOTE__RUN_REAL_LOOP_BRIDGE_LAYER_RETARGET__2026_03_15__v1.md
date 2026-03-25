# A2_UPDATE_NOTE__RUN_REAL_LOOP_BRIDGE_LAYER_RETARGET__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 CONTROL NOTE
Date: 2026-03-15
Role: preserve the bridge-layer retarget after splitting strict and recovery real-loop entrypoints

## Scope

This note is bounded to the lightweight work-bridge layer only.

Patched surfaces:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_real_loop_bridge_from_work.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_real_loop_recovery_bridge_from_work.py`

## What changed

### 1) Existing work bridge clarified

`run_real_loop_bridge_from_work.py` now explicitly documents that it is the legacy bridge for:
- strict/default real-loop entrypoint

and points to:
- `system_v3/tools/run_real_loop.py`
- `system_v3/tools/run_real_loop_recovery_cycle.py`

### 2) Recovery bridge added

New bridge:
- `run_real_loop_recovery_bridge_from_work.py`

This provides a matching work-bridge surface for the explicit recovery entrypoint:
- `system_v3/tools/run_real_loop_recovery_cycle.py`

## Verification

Compile:
- `python3 -m py_compile system_v3/tools/run_real_loop_bridge_from_work.py system_v3/tools/run_real_loop_recovery_bridge_from_work.py`

## Meaning

This closes the remaining live bridge-layer asymmetry:
- strict mode had a work bridge
- recovery mode did not

Now both operator paths have matching bridge surfaces.

## Next seam

Best next move:
- decide whether `run_real_loop.py --allow-reconstructed-artifacts` should remain as a compatibility path long term
- or whether recovery should eventually be routed only through the dedicated recovery entrypoint and bridge
