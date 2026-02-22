
# ZIP Templates

This directory provides **scaffolding** for building ZIPs that conform to `specs/ZIP_PROTOCOL_v2.md`.

## Important
- ZIP validation is allowlist-only per `zip_type`.
- When producing a ZIP from a template, include **only** the allowlisted files.
- Hashes in templates are placeholders; producers must recompute:
  - `manifest_sha256`
  - all payload SHA-256 digests
  - `HASHES.sha256` entries

## Template folders (one per zip_type)

FORWARD:
- `A2_TO_A1_PROPOSAL_ZIP_TEMPLATE/`
- `A1_TO_A0_STRATEGY_ZIP_TEMPLATE/`
- `A0_TO_B_EXPORT_BATCH_ZIP_TEMPLATE/`

BACKWARD:
- `B_TO_A0_STATE_UPDATE_ZIP_TEMPLATE/`
- `SIM_TO_A0_SIM_RESULT_ZIP_TEMPLATE/`
- `A0_TO_A1_SAVE_ZIP_TEMPLATE/`
- `A1_TO_A2_SAVE_ZIP_TEMPLATE/`
- `A2_META_SAVE_ZIP_TEMPLATE/`

## Exact filenames per zip_type
See Section 5 table in `specs/ZIP_PROTOCOL_v2.md`.
