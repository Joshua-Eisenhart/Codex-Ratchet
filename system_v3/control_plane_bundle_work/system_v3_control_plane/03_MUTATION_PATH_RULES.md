
# Mutation Path Rules

## Single allowed mutation path
Mutation to canonical state is permitted only via:

1) A1 emits: `A1_TO_A0_STRATEGY_ZIP`
2) A0 compiles deterministically into: `A0_TO_B_EXPORT_BATCH_ZIP`
3) B admits changes from the single `EXPORT_BLOCK vN` inside the ZIP

No other path may mutate canon.

## Hard prohibitions
- A2 MUST NOT emit mutation containers.
- A1 MUST NOT emit mutation containers.
- A0 MUST NOT invent new structure; it only compiles accepted strategy inputs.
- SAVE ZIPs MUST NOT contain mutation containers.
- ZIP validation failure MUST NOT trigger alternate routing, auto-correction, or downgrade.

## Evidence is not mutation
- `SIM_EVIDENCE v1` is evidence-only and must not be treated as a direct mutation mechanism.
- State snapshots (`THREAD_S_SAVE_SNAPSHOT v2`) represent B-produced state only; A0 is a deterministic custodian.

## Fail-closed
If an artifact cannot be validated deterministically, it must be rejected or parked per `ZIP_PROTOCOL_v2`.
