# DETERMINISTIC_REPLAY_RUNNER_OUTLINE v1

## Script target
`runtime/bootpack_b_kernel_v1/tools/replay_runner.py`

## Inputs
- ordered ZIP path list (explicit ordering; no filesystem enumeration reliance)
- initial canonical state snapshot bytes
- compiler_version
- last_sequence table initialization (per run_id/source_layer)

## Replay integrity (must enforce)
- Strict sequence processing per `specs/ZIP_PROTOCOL_v2.md` (Replay Integrity Rule).
- Gap → PARK only.
- Backward ZIP application must respect forward-validation gating.

## Deterministic replay algorithm (outline)

1) Initialize `state = initial_state`.
2) For each ZIP in the given order:
   a) Validate ZIP (ZIP_PROTOCOL_v2).
      - If REJECT: stop; record reject tag; no state mutation.
      - If PARK: record PARK; do not apply; continue.
      - If OK: proceed.
   b) Route ZIP by zip_type to deterministic handler.
   c) Apply resulting deterministic state transition (if any).
3) Emit final state hash.

## Verification outputs
Compute deterministic digests for:
- final state hash
- emitted artifact digests (if any)
- decision trace digest

Replay same ordered ZIP chain twice:
- any mismatch is a determinism violation.

## STATE_TRANSITION_DIGEST verification (if recorded)
If A0 records `state_transition_digest` for mutation cycles, replay must recompute and verify it per:
- `specs/STATE_TRANSITION_DIGEST_v1.md`

## Hard rules
- ignore ZIP metadata (timestamps, entry attrs, entry order)
- canonicalize extracted file bytes before hashing/verifying
- never depend on wall-clock
- never depend on filesystem enumeration order
