# ENUM_REGISTRY v1

Canonical enum definitions for this control-plane bundle.

**Single source of truth:** enum sets listed here MUST NOT be redefined elsewhere. Other documents may reference these enums and use their values, but must not restate the complete sets.

## direction
- `FORWARD`
- `BACKWARD`

## layer
- `A2`
- `A1`
- `A0`
- `B`
- `SIM`

## zip_type
FORWARD:
- `A2_TO_A1_PROPOSAL_ZIP`
- `A1_TO_A0_STRATEGY_ZIP`
- `A0_TO_B_EXPORT_BATCH_ZIP`

BACKWARD:
- `B_TO_A0_STATE_UPDATE_ZIP`
- `SIM_TO_A0_SIM_RESULT_ZIP`
- `A0_TO_A1_SAVE_ZIP`
- `A1_TO_A2_SAVE_ZIP`
- `A2_META_SAVE_ZIP`

## container_primitive
- `EXPORT_BLOCK vN`
- `SIM_EVIDENCE v1`
- `THREAD_S_SAVE_SNAPSHOT v2`
- `NONE`

## reject_tag (ZIP_PROTOCOL_v2)
- `MISSING_HEADER_FIELD`
- `ZIP_TYPE_DIRECTION_MISMATCH`
- `SEQUENCE_REGRESSION`
- `INVALID_HASH_FORMAT`
- `MANIFEST_HASH_MISMATCH`
- `HASHES_MISMATCH`
- `FORBIDDEN_FILE_PRESENT`
- `FORBIDDEN_CONTAINER_PRESENT`
- `MANIFEST_PATH_INVALID`
- `DUPLICATE_MANIFEST_PATH`
- `CONTAINER_BOUNDARY_INVALID`

## operator_id (A1 repair / generation)
- `OP_A1_GENERATED`
- `OP_BIND_SIM`
- `OP_REPAIR_DEF_FIELD`
- `OP_MUTATE_LEXEME`
- `OP_REORDER_DEPENDENCIES`
- `OP_NEG_SIM_EXPAND`
- `OP_INJECT_PROBE`

## promotion_state (A0 deterministic labels)
- `NOT_READY`
- `READY_FOR_TIGHTEN`
- `READY_FOR_CANON`
