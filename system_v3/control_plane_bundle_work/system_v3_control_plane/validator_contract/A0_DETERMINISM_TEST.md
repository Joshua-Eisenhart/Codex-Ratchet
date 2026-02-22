# A0_DETERMINISM_TEST

This document defines deterministic conformance tests for the A0 hinge.

## A0-DET-01 (normative)

Given identical:
- canonicalized extracted file bytes of the input ZIPs (per `specs/ZIP_PROTOCOL_v2.md`),
- canonical state snapshot bytes,
- compiler_version,

A0 MUST produce identical outputs.

ZIP container metadata MUST NOT affect results.

## Test inputs (common)

- fixed initial canonical snapshot bytes (S0)
- fixed compiler_version string
- fixed ordered ZIP chain (or single ZIP) with known digests
- fixed last_sequence table for `(run_id, source_layer)`

## Test cases (deterministic)

### T1 — Compile determinism (identical inputs)
Inputs:
- identical `A1_TO_A0_STRATEGY_ZIP` extracted file bytes
- identical state snapshot bytes
- identical compiler_version

Expected:
- identical `A0_TO_B_EXPORT_BATCH_ZIP` extracted file bytes
- identical `EXPORT_BLOCK` canonical bytes and hash
- identical decision traces

### T2 — ZIP metadata variance
Inputs:
- two ZIP archives with identical extracted file bytes but different ZIP metadata (timestamps/order)
- identical state snapshot bytes
- identical compiler_version

Expected:
- identical A0 outputs (as in T1)

### T3 — Path normalization violations are deterministic
Inputs:
- ZIP with MANIFEST rel_path containing `..` or backslashes

Expected:
- ZIP validator deterministically REJECT with `MANIFEST_PATH_INVALID`
- A0 emits no outputs

### T4 — A1 strategy self-hash mismatch
Inputs:
- A1_STRATEGY_v1.json where `self_audit.strategy_sha256` does not match recomputed value under recursion-safe rule

Expected:
- A0 deterministically rejects strategy admission (A0-level failure)
- no B-facing artifacts emitted

### T5 — Structural digest mismatch / structural duplication
Inputs:
- A1 strategy where alternatives are not structurally distinct from targets under `STRUCTURAL_DIGEST_v1`

Expected:
- A0 deterministically rejects strategy admission (A0-level failure)
- no B-facing artifacts emitted

### T6 — Sequence gap handling is deterministic
Inputs:
- a valid ZIP with `sequence > last_accepted + 1` for `(run_id, source_layer)`

Expected:
- ZIP validator outcome = `PARK`
- no state mutation
- repeating the same ZIP yields deterministic `PARK` until missing sequences arrive

### T7 — STATE_TRANSITION_DIGEST verification
Inputs:
- a full cycle that produces `previous_state_hash`, `export_block_hash`, `snapshot_hash`
- a recorded `state_transition_digest` (if A0 records it)

Expected:
- recomputed digest per `specs/STATE_TRANSITION_DIGEST_v1.md` matches exactly
- mismatch must deterministically fail verification (A0-level failure)

## Reporting (required)

Each test execution MUST emit:
- input ZIP digest(s)
- state_hash_before, state_hash_after (where applicable)
- decision outcomes
- emitted artifact digests (where applicable)
- (optional) state_transition_digest
