
# SIM_EVIDENCE v1

This specification defines the canonical deterministic evidence container emitted by SIM and transported via:
- `SIM_TO_A0_SIM_RESULT_ZIP` (see `ZIP_PROTOCOL_v2.md`)

## Container boundaries (strict)
A `SIM_EVIDENCE v1` block MUST be delimited by exact full-line matches:

- `BEGIN SIM_EVIDENCE v1`
- `END SIM_EVIDENCE v1`

No text may appear outside the block when a file is specified to contain only SIM_EVIDENCE blocks.

## Required fields (exactly once each)
Inside each block:

- `SIM_ID: <ID>`
- `CODE_HASH_SHA256: <hex64>`
- `INPUT_HASH_SHA256: <hex64>`
- `OUTPUT_HASH_SHA256: <hex64>`
- `RUN_MANIFEST_SHA256: <hex64>`

`<hex64>` MUST be lowercase hex (64 chars).

## Optional / repeatable lines
The following lines MAY appear zero or more times:

- `METRIC: <key>=<value>`
- `EVIDENCE_SIGNAL <SIM_ID> CORR <TOKEN>`
- `KILL_SIGNAL <TARGET_ID> CORR <TOKEN>`

## Prohibitions
Inside the SIM_EVIDENCE block:
- No comments.
- No JSON.
- No extra container types.

## Binding intent
SIM_EVIDENCE provides deterministic binding to:
- simulation code identity (`CODE_HASH_SHA256`)
- input snapshot identity (`INPUT_HASH_SHA256`)
- output identity (`OUTPUT_HASH_SHA256`)
- runtime manifest (`RUN_MANIFEST_SHA256`)

## Compatibility
ZIP transport validation treats SIM_EVIDENCE containers structurally (BEGIN/END + delimiter correctness).
Semantic correctness (e.g. whether hashes correspond to actual executed code) is verified by the SIM runner and/or A0.
