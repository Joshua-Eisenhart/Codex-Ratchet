# FULL_CYCLE_SIMULATION v2.5

This document defines one canonical end-to-end simulation trace against the control-plane specs (v2.5 hardening revision).

## Scope
- Directional ZIP transport (ZIP_PROTOCOL_v2)
- A2 → A1 → A0 → B forward path
- B/SIM → A0 backward path
- Save ladder to A2
- Replay determinism check + Replay Integrity Rule
- Optional STATE_TRANSITION_DIGEST verification

## Initial state
- `run_id = RUN_001`
- `state_hash = S0`
- last_sequence per `(run_id, source_layer)` initialized to 0

## Step 1: A2 proposal (FORWARD)
ZIP:
- `zip_type = A2_TO_A1_PROPOSAL_ZIP`
- `sequence = 1`
- payload: `A2_PROPOSAL.json` (no mutation containers)
Expected:
- ZIP validation outcome: OK

## Step 2: A1 strategy (FORWARD)
ZIP:
- `zip_type = A1_TO_A0_STRATEGY_ZIP`
- `sequence = 1`
- payload: `A1_STRATEGY_v1.json`
Expected:
- ZIP validation outcome: OK
- A0 admission:
  - self-hash verified (recursion-safe rule)
  - structural distinctness enforced (STRUCTURAL_DIGEST)
  - forbidden keys absent
  - if admission fails: stop; no B-facing artifacts

## Step 3: A0 export batch (FORWARD)
ZIP:
- `zip_type = A0_TO_B_EXPORT_BATCH_ZIP`
- `sequence = 1`
- payload: `EXPORT_BLOCK.txt` containing exactly one `EXPORT_BLOCK vN`
Expected:
- ZIP validation outcome: OK

## Step 4: B state update (BACKWARD)
ZIP:
- `zip_type = B_TO_A0_STATE_UPDATE_ZIP`
- `sequence = 1`
- payload: exactly one `THREAD_S_SAVE_SNAPSHOT v2`
Expected:
- ZIP validation outcome: OK
- expected state transition: `S0 → S1`
- optional: compute snapshot_hash for STATE_TRANSITION_DIGEST input

## Step 5: SIM evidence (BACKWARD)
ZIP:
- `zip_type = SIM_TO_A0_SIM_RESULT_ZIP`
- `sequence = 1`
- payload: one or more `SIM_EVIDENCE v1` blocks
Expected:
- ZIP validation outcome: OK

## Step 6: A0 save ladder (BACKWARD)
ZIP:
- `zip_type = A0_TO_A1_SAVE_ZIP`
- `sequence = 1`
- payload: `A0_SAVE_SUMMARY.json` (informational only)
Expected:
- ZIP validation outcome: OK

## Step 7: A1 save to A2 (BACKWARD)
ZIP:
- `zip_type = A1_TO_A2_SAVE_ZIP`
- `sequence = 1`
Expected:
- ZIP validation outcome: OK

## Step 8: A2 meta save (BACKWARD)
ZIP:
- `zip_type = A2_META_SAVE_ZIP`
- `sequence = 1`
Expected:
- ZIP validation outcome: OK

## Replay Integrity Rule check
Replay the ordered ZIP chain twice over identical initial state and compiler_version.
Expected:
- identical final state hash (S1)
- identical emitted artifact digests
- identical decision outcomes

## Optional STATE_TRANSITION_DIGEST check
If A0 records:
- previous_state_hash = S0
- export_block_hash
- snapshot_hash
- compiler_version

Then verify:
- state_transition_digest matches `specs/STATE_TRANSITION_DIGEST_v1.md`
and is identical under replay.
