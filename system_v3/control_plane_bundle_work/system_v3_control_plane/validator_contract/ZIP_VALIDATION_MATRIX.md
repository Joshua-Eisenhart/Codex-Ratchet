
# ZIP_VALIDATION_MATRIX

This matrix defines deterministic validation outcomes and reject tags for ZIP_PROTOCOL_v2.

## Outcomes
- `OK`: ZIP is valid and accepted.
- `PARK`: ZIP is structurally valid but deferred due to sequencing/replay preconditions.
- `REJECT`: ZIP is invalid under protocol.

## PARK conditions
- `sequence > last_accepted_sequence + 1` for `(run_id, source_layer)` → PARK
- `direction == BACKWARD` and required prior FORWARD ZIP coverage for same `run_id` is incomplete → PARK

All other failures are REJECT.

## Reject tags (ZIP_PROTOCOL_v2)
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

## Condition → Tag mapping (minimal)

### Header
- Missing required header field OR invalid `run_id` OR invalid `created_utc` OR invalid `zip_protocol` OR invalid `compiler_version` → `MISSING_HEADER_FIELD`
- `zip_type` invalid OR `direction/source_layer/target_layer` invalid OR mismatch with zip_type implied mapping → `ZIP_TYPE_DIRECTION_MISMATCH`
- `sequence <= last_accepted_sequence` → `SEQUENCE_REGRESSION`

### Hash format / integrity
- Any sha256 not lowercase hex64 where required → `INVALID_HASH_FORMAT`
- `manifest_sha256` mismatch → `MANIFEST_HASH_MISMATCH`
- HASHES coverage mismatch / duplicate / extra / byte-hash mismatch / manifest byte_size mismatch → `HASHES_MISMATCH`

### Allowlist / forbidlist
- Any extra file not in zip_type allowlist OR missing required payload file → `FORBIDDEN_FILE_PRESENT`
- Forbidden container detected (exact delimiter match only) → `FORBIDDEN_CONTAINER_PRESENT`
- Container boundary mismatch / nesting mismatch / wrong block count in container-bearing files → `CONTAINER_BOUNDARY_INVALID`

### Manifest path
- Invalid rel_path normalization → `MANIFEST_PATH_INVALID`
- Duplicate rel_path entries → `DUPLICATE_MANIFEST_PATH`
