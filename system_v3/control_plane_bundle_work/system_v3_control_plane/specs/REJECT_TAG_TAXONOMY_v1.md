# REJECT_TAG_TAXONOMY v1

Purpose: define the meaning and usage constraints of the ZIP validator reject tags used by `ZIP_PROTOCOL_v2`.

**Enum source:** the reject tag set is defined exclusively in `specs/ENUM_REGISTRY_v1.md` under `reject_tag (ZIP_PROTOCOL_v2)`. This document MUST NOT redefine the set; it defines semantics and coupling only.

## 1) Ownership and emission

- Reject tags are emitted by the ZIP_PROTOCOL_v2 validator only.
- No alias tags.
- No tag overloading beyond the definitions below.
- Other layers (A0/B/SIM) may have separate codes, but MUST NOT reuse ZIP reject tags with different meanings.

## 2) Outcome coupling

- All reject tags imply outcome `REJECT`.
- Outcome `PARK` is reserved for deterministic sequencing/replay defers under ZIP_PROTOCOL_v2 (no reject tag is emitted for PARK).

## 3) Tag semantics (definitions)

The following semantic definitions correspond to tags in `ENUM_REGISTRY_v1.md`:

- `MISSING_HEADER_FIELD`: any required header field missing OR required-format invalid per ZIP_PROTOCOL_v2 (including invalid `zip_protocol` value or invalid `compiler_version` policy value).
- `ZIP_TYPE_DIRECTION_MISMATCH`: invalid enum value for `zip_type/direction/source_layer/target_layer` OR mismatch between `zip_type` and its implied `(direction, source_layer, target_layer)` mapping.
- `SEQUENCE_REGRESSION`: `sequence <= last_accepted_sequence` for `(run_id, source_layer)`.
- `INVALID_HASH_FORMAT`: any sha256 value where required is not lowercase hex64.
- `MANIFEST_HASH_MISMATCH`: header `manifest_sha256` does not match canonical MANIFEST.json bytes.
- `HASHES_MISMATCH`: HASHES coverage mismatch / duplicate hash line / extra hash line / byte-hash mismatch / MANIFEST byte_size mismatch.
- `FORBIDDEN_FILE_PRESENT`: any file outside the allowlist OR manifest payload set mismatch (missing required payload file or containing an extra payload file).
- `FORBIDDEN_CONTAINER_PRESENT`: forbidden container delimiter detected by exact full-line match.
- `MANIFEST_PATH_INVALID`: invalid rel_path normalization (separator, absolute paths, `..`, backslash, etc.).
- `DUPLICATE_MANIFEST_PATH`: duplicate rel_path entries in MANIFEST.json.
- `CONTAINER_BOUNDARY_INVALID`: malformed container boundaries, nesting mismatch, or required block-count violation in container-bearing files.

## 4) Evolution rule

- The reject tag set is immutable under v1.
- Any new reject tag requires a protocol version bump and corresponding updates to `ENUM_REGISTRY_v1.md`.
