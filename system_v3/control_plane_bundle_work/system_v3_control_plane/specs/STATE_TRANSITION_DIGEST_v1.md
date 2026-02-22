# STATE_TRANSITION_DIGEST v1

Defines deterministic transition hashing at the A0 boundary for replay verification.

This is not a container primitive and does not modify B admission rules.
It is a deterministic digest computed from existing artifacts/hashes.

## Definition (normative)

For any accepted mutation cycle, define:

`state_transition_digest = sha256(previous_state_hash + export_block_hash + snapshot_hash + compiler_version)`

Where each component is a lowercase hex64 string, concatenated in the exact order shown with no separators.

- `previous_state_hash`: state hash prior to applying the mutation.
- `export_block_hash`: sha256 of the canonical bytes of the `EXPORT_BLOCK vN` container that was admitted by B (as carried in `A0_TO_B_EXPORT_BATCH_ZIP`).
- `snapshot_hash`: sha256 of the canonical bytes of the `THREAD_S_SAVE_SNAPSHOT v2` container emitted by B (as carried in `B_TO_A0_STATE_UPDATE_ZIP`).
- `compiler_version`: the exact `ZIP_HEADER.compiler_version` string used by A0 when compiling the export.

## Invariants

- Deterministic: identical inputs MUST produce identical digest.
- Replay-stable: replaying the same ZIP chain over the same initial state MUST produce identical state_transition_digest sequence.
- Independent of ZIP metadata: ZIP container timestamps/ordering must not affect digest.
