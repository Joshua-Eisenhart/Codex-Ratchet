
# Layer Boundaries

This document defines the **hard boundaries** between layers and which artifacts may cross each boundary.

## Boundary: A2 → A1
Allowed:
- `A2_TO_A1_PROPOSAL_ZIP` (FORWARD)
Forbidden:
- Any mutation container (`EXPORT_BLOCK vN`, `SIM_EVIDENCE v1`, `THREAD_S_SAVE_SNAPSHOT v2`)
- Any direct B-facing output

## Boundary: A1 → A0
Allowed:
- `A1_TO_A0_STRATEGY_ZIP` containing exactly one `A1_STRATEGY_v1.json`
Forbidden:
- Any mutation container
- Any raw container text intended for B/SIM

## Boundary: A0 → B
Allowed:
- `A0_TO_B_EXPORT_BATCH_ZIP` containing exactly one `EXPORT_BLOCK vN` block
Forbidden:
- Any alternate mutation pathway

## Boundary: B → A0
Allowed:
- `B_TO_A0_STATE_UPDATE_ZIP` containing exactly one `THREAD_S_SAVE_SNAPSHOT v2` block
Forbidden:
- Any `EXPORT_BLOCK` or `SIM_EVIDENCE`

## Boundary: SIM → A0
Allowed:
- `SIM_TO_A0_SIM_RESULT_ZIP` containing `SIM_EVIDENCE v1` blocks (1+)
Forbidden:
- Any `EXPORT_BLOCK` or snapshots

## Save ladder (BACKWARD)
Allowed:
- `A0_TO_A1_SAVE_ZIP` (informational summary only)
- `A1_TO_A2_SAVE_ZIP` (informational summary only)
- `A2_META_SAVE_ZIP` (informational meta-save only)
Forbidden:
- Any mutation container of any kind

## Transport-only doctrine
Transport law MUST NOT encode:
- policy logic
- confidence metrics
- classification stages
- TTL/latency management
- ABAC semantics
- probabilistic reasoning
