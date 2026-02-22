# LAYER_ISOLATION_INVARIANT v1

Purpose: formalize layer-isolation constraints for the existing architecture.

This document is doctrine-only.
It does NOT modify kernel behavior.
It does NOT modify `ZIP_PROTOCOL_v2`.

## Invariants

- A2 influences lower layers only via `A2_TO_A1_PROPOSAL_ZIP`.
- A1 influences lower layers only via `A1_TO_A0_STRATEGY_ZIP`.
- A0 mutates canon only via `A0_TO_B_EXPORT_BATCH_ZIP`.
- B admits canon only via `EXPORT_BLOCK vN` in the allowed export path.
- No cross-layer implicit state is allowed.

## Integrity Clause

- Side channels, hidden state injection, and bypass routes are out of contract.
- This document introduces no new ZIP types, containers, enums, or mutation paths.
