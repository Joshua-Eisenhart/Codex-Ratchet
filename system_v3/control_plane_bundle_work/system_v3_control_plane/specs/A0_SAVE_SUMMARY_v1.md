# A0_SAVE_SUMMARY v1

Defines the canonical informational summary object carried in:
- `A0_TO_A1_SAVE_ZIP` as `A0_SAVE_SUMMARY.json`

This object is informational only and is not a mutation container.

## Required fields

- `schema`: MUST equal `"A0_SAVE_SUMMARY_v1"`
- `run_id`: string
- `last_sequence`: integer
- `state_hash`: lowercase hex64
- `survivor_ledger_digest`: lowercase hex64
- `graveyard_digest`: lowercase hex64
- `sim_summary_digest`: lowercase hex64

## Optional fields

- `notes`: string

## Rules

- All required fields MUST exist.
- No implicit defaults are allowed.
- Hash fields MUST be lowercase hex64.
- `run_id` must match the ZIP header run_id.
- `last_sequence` must match the ZIP header sequence.

## Usage

- A1 uses this summary as deterministic context input when producing `A1_STRATEGY_v1`.
- A2 may consume it indirectly through `A1_TO_A2_SAVE_ZIP` summaries.

## Prohibitions

- No `EXPORT_BLOCK` content.
- No `SIM_EVIDENCE` content.
- No snapshot containers.
