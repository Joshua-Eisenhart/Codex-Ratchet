# ZIP_PROTOCOL_v2

Revision: v2.3 (document hardening revision; protocol identifier remains `ZIP_PROTOCOL_v2`)

## 1) HEADER CONTRACT (ZIP_HEADER.json)

`ZIP_HEADER.json` is required in every ZIP.

Required fields (all required; no extras are used for validation):
- `zip_protocol`: MUST equal `"ZIP_PROTOCOL_v2"`.
- `zip_type`: value MUST be in `ENUM_REGISTRY_v1.md` (zip_type).
- `direction`: value MUST be in `ENUM_REGISTRY_v1.md` (direction).
- `source_layer`: value MUST be in `ENUM_REGISTRY_v1.md` (layer).
- `target_layer`: value MUST be in `ENUM_REGISTRY_v1.md` (layer).
- `run_id`: string; validated by regex `^[A-Za-z0-9._-]{1,128}$`.
- `sequence`: integer, `>= 1`.
- `created_utc`: string; RFC3339 UTC format `YYYY-MM-DDTHH:MM:SSZ`.
- `compiler_version`: string; always required.
- `manifest_sha256`: lowercase hex64.

`compiler_version` required value:
- If `source_layer == A0`: MUST be non-empty.
- If `source_layer != A0`: MUST be `""`.

Header invariants:
- `zip_type` implies exact `direction`, `source_layer`, and `target_layer` per Section 5. Any mismatch is invalid.
- Sequence is strictly monotone per `(run_id, source_layer)`:
  - `sequence <= last_accepted_sequence` is invalid.
  - `sequence > last_accepted_sequence + 1` is a sequence gap.
  - Gaps are structurally valid but must `PARK` until missing sequence numbers arrive and validate.
- `created_utc` is informational only and MUST NEVER be used as a compile, routing, admission, or replay decision input.

Invalid-header handling:
- Missing `zip_protocol`, invalid `zip_protocol`, missing `compiler_version`, or invalid `compiler_version` policy value => `MISSING_HEADER_FIELD`.
- Missing `run_id` or invalid `run_id` format => `MISSING_HEADER_FIELD`.
- Missing `created_utc` or invalid RFC3339 UTC format => `MISSING_HEADER_FIELD`.

## 2) MANIFEST CONTRACT (MANIFEST.json)

`MANIFEST.json` is required in every ZIP and is the canonical payload inventory.

Canonical JSON rules for `MANIFEST.json`:
- UTF-8 encoding.
- LF newlines only.
- Object keys sorted lexicographically.
- Stable separators: `,` and `:` with no extra spaces.
- No trailing spaces.
- Trailing newline required.

Manifest structure:
- Top-level value: array of entry objects.
- Array ordering: MUST be lexicographically sorted by `rel_path`.
- Each entry object fields:
  - `rel_path` (string)
  - `byte_size` (integer, `>= 0`)
  - `sha256` (lowercase hex64)

Manifest scope:
- Files only (directories forbidden).
- MUST list all payload files and MUST exclude:
  - `ZIP_HEADER.json`
  - `MANIFEST.json`
  - `HASHES.sha256`

Coverage rule:
- `set(MANIFEST.rel_path)` MUST equal the payload allowlist set for the selected `zip_type` in Section 5.
- Any mismatch (missing payload file in manifest, extra manifest entry, or payload allowlist divergence) is invalid.

Path rules:
- `/` separators only.
- `\` forbidden.
- Absolute paths forbidden.
- `..` segments forbidden.
- Case-sensitive matching.

Additional manifest checks:
- Duplicate `rel_path` entries are invalid.
- `byte_size` MUST equal actual file byte length.

`manifest_sha256` definition:
- `ZIP_HEADER.json.manifest_sha256` MUST equal SHA-256 of canonical `MANIFEST.json` bytes.

## 3) HASHES FILE CONTRACT (HASHES.sha256)

`HASHES.sha256` is REQUIRED for all `zip_type` values.

Line format:
- `<sha256><two spaces><rel_path>`
- `<sha256>` must be lowercase hex64.
- `<rel_path>` must be exact, case-sensitive.

Ordering and newline rules:
- Lines sorted lexicographically by `rel_path`.
- LF newlines only.
- Trailing newline required.

Coverage:
- MUST include exactly one line for each of:
  - `ZIP_HEADER.json`
  - `MANIFEST.json`
  - every payload file listed in `MANIFEST.json`
- MUST NOT include `HASHES.sha256`.

Cycle rule:
- `HASHES.sha256` depends on `ZIP_HEADER.json` bytes.
- `ZIP_HEADER.json` does not depend on `HASHES.sha256`.
- No cycle exists.

Validation:
- Every required file has exactly one hash line.
- No extra hash lines.
- Each hash must match exact file bytes.

## 4) DETERMINISTIC CANONICALIZATION RULES

Determinism scope:
- Validation determinism is defined over extracted file bytes plus canonicalization, not ZIP container bytes.

ZIP metadata handling:
- Validators MUST ignore ZIP metadata (timestamps, extra fields, archive entry metadata).

Producer ordering rule:
- Producers MUST write ZIP entries in lexicographic order by `rel_path`.
- Validators do not use ZIP entry order as a decision input.

JSON canonicalization (all JSON files in ZIP):
- UTF-8.
- LF only.
- Sorted keys.
- Stable separators.
- No trailing spaces.
- Trailing newline required.

Text canonicalization (all non-JSON text files in ZIP):
- UTF-8.
- LF only.
- No trailing spaces per line.
- Trailing newline required.

Hashing:
- SHA-256 only.
- Lowercase hex only.

Transport-only and no-reroute clauses:
- This protocol defines transport structure only.
- It does not encode policy logic, confidence metrics, classification stages, TTL management, ABAC semantics, or probabilistic reasoning.
- ZIP validation failure MUST NOT trigger alternate routing, auto-correction, or downgrade.

## Replay Integrity Rule (normative)

For a given `run_id`:

1. ZIPs MUST be processed strictly in increasing `sequence` order.
2. A ZIP with `sequence > last_accepted + 1` MUST result in `PARK` (sequence-gap only).
3. Backward ZIPs (`direction == BACKWARD`) MUST NOT be applied unless all prior FORWARD ZIPs for the same `run_id` up to that sequence have been validated or deterministically parked.
4. Replaying the same ordered ZIP chain over the same initial state and `compiler_version` MUST produce identical:
   - final state hash
   - emitted artifact digests
   - decision outcomes

Cross-run mixing is forbidden.

## No-Implicit-Defaults Rule (normative)

If a required field defined in this specification is absent, it MUST NOT be defaulted silently.
Absence of a required field is invalid and MUST result in `REJECT` (or admission failure where applicable).

## Determinism Domain Clarification (normative)

Determinism is defined over canonicalized extracted file bytes under this protocol’s canonicalization rules.
ZIP container metadata (timestamps, entry attributes, entry order) is ignored.

## State Transition Digest (reference)

A0 MAY compute and record deterministic replay digests per `specs/STATE_TRANSITION_DIGEST_v1.md`.
This does not introduce new container primitives and does not change B admission rules.

## 5) ZIP_TYPE ENUMERATION + ALLOWLIST/FORBIDLIST TABLE (core table)

`zip_type` enum (exact; no additions):
- `A2_TO_A1_PROPOSAL_ZIP`
- `A1_TO_A0_STRATEGY_ZIP`
- `A0_TO_B_EXPORT_BATCH_ZIP`
- `B_TO_A0_STATE_UPDATE_ZIP`
- `SIM_TO_A0_SIM_RESULT_ZIP`
- `A0_TO_A1_SAVE_ZIP`
- `A1_TO_A2_SAVE_ZIP`
- `A2_META_SAVE_ZIP`

This enum must remain identical to `ENUM_REGISTRY_v1.md`.

Sharding policy:
- No sharding allowed in ZIP payload filenames.
- Exact filenames only.

Container detection rule:
- Container detection MUST use exact full-line delimiter matches after trimming line edges.
- No substring matching is permitted.
- Delimiters are strict:
  - `BEGIN SIM_EVIDENCE v1`
  - `END SIM_EVIDENCE v1`
  - `BEGIN THREAD_S_SAVE_SNAPSHOT v2`
  - `END THREAD_S_SAVE_SNAPSHOT v2`
  - `BEGIN EXPORT_BLOCK vN` and `END EXPORT_BLOCK vN` where `N` is digits and begin/end versions must match.

| zip_type | direction | source_layer | target_layer | allowed filenames (exact) | cardinality by filename | allowed container types by file | forbidden container types |
|---|---|---|---|---|---|---|---|
| `A2_TO_A1_PROPOSAL_ZIP` | `FORWARD` | `A2` | `A1` | `ZIP_HEADER.json`, `MANIFEST.json`, `HASHES.sha256`, `A2_PROPOSAL.json` | all exactly 1 | `A2_PROPOSAL.json`: `NONE` | `EXPORT_BLOCK vN`, `SIM_EVIDENCE v1`, `THREAD_S_SAVE_SNAPSHOT v2` |
| `A1_TO_A0_STRATEGY_ZIP` | `FORWARD` | `A1` | `A0` | `ZIP_HEADER.json`, `MANIFEST.json`, `HASHES.sha256`, `A1_STRATEGY_v1.json` | all exactly 1 | `A1_STRATEGY_v1.json`: `NONE` | `EXPORT_BLOCK vN`, `SIM_EVIDENCE v1`, `THREAD_S_SAVE_SNAPSHOT v2` |
| `A0_TO_B_EXPORT_BATCH_ZIP` | `FORWARD` | `A0` | `B` | `ZIP_HEADER.json`, `MANIFEST.json`, `HASHES.sha256`, `EXPORT_BLOCK.txt` | all exactly 1 | `EXPORT_BLOCK.txt`: `EXPORT_BLOCK vN` exactly 1 block | `SIM_EVIDENCE v1`, `THREAD_S_SAVE_SNAPSHOT v2` |
| `B_TO_A0_STATE_UPDATE_ZIP` | `BACKWARD` | `B` | `A0` | `ZIP_HEADER.json`, `MANIFEST.json`, `HASHES.sha256`, `THREAD_S_SAVE_SNAPSHOT_v2.txt` | all exactly 1 | `THREAD_S_SAVE_SNAPSHOT_v2.txt`: `THREAD_S_SAVE_SNAPSHOT v2` exactly 1 block | `EXPORT_BLOCK vN`, `SIM_EVIDENCE v1` |
| `SIM_TO_A0_SIM_RESULT_ZIP` | `BACKWARD` | `SIM` | `A0` | `ZIP_HEADER.json`, `MANIFEST.json`, `HASHES.sha256`, `SIM_EVIDENCE.txt` | all exactly 1 | `SIM_EVIDENCE.txt`: `SIM_EVIDENCE v1` one or more blocks | `EXPORT_BLOCK vN`, `THREAD_S_SAVE_SNAPSHOT v2` |
| `A0_TO_A1_SAVE_ZIP` | `BACKWARD` | `A0` | `A1` | `ZIP_HEADER.json`, `MANIFEST.json`, `HASHES.sha256`, `A0_SAVE_SUMMARY.json` | all exactly 1 | `A0_SAVE_SUMMARY.json`: `NONE` | `EXPORT_BLOCK vN`, `SIM_EVIDENCE v1`, `THREAD_S_SAVE_SNAPSHOT v2` |
| `A1_TO_A2_SAVE_ZIP` | `BACKWARD` | `A1` | `A2` | `ZIP_HEADER.json`, `MANIFEST.json`, `HASHES.sha256`, `A1_SAVE_SUMMARY.json` | all exactly 1 | `A1_SAVE_SUMMARY.json`: `NONE` | `EXPORT_BLOCK vN`, `SIM_EVIDENCE v1`, `THREAD_S_SAVE_SNAPSHOT v2` |
| `A2_META_SAVE_ZIP` | `BACKWARD` | `A2` | `A2` | `ZIP_HEADER.json`, `MANIFEST.json`, `HASHES.sha256`, `A2_META_SAVE_SUMMARY.json` | all exactly 1 | `A2_META_SAVE_SUMMARY.json`: `NONE` | `EXPORT_BLOCK vN`, `SIM_EVIDENCE v1`, `THREAD_S_SAVE_SNAPSHOT v2` |

Hard invariants:
- SAVE zip types (`A0_TO_A1_SAVE_ZIP`, `A1_TO_A2_SAVE_ZIP`, `A2_META_SAVE_ZIP`) MUST NOT contain:
  - `EXPORT_BLOCK vN`
  - `SIM_EVIDENCE v1`
  - `THREAD_S_SAVE_SNAPSHOT v2`
- `EXPORT_BLOCK vN` is allowed only in `A0_TO_B_EXPORT_BATCH_ZIP`, exactly one block.
- `SIM_EVIDENCE v1` is allowed only in `SIM_TO_A0_SIM_RESULT_ZIP`, one or more blocks.
- `THREAD_S_SAVE_SNAPSHOT v2` is allowed only in `B_TO_A0_STATE_UPDATE_ZIP`, exactly one block.
- Any file outside the allowlist for the selected `zip_type` is invalid.

## 6) LAYER DETERMINISM INVARIANT

A0-DET-01:  
Given identical (ZIP bytes, canonical state snapshot bytes, compiler_version),  
A0 must produce identical outputs.

Replay integrity rule (v2.3 revision):
- For a given `run_id`, ZIPs MUST be processed in strictly increasing `sequence` order.
- A ZIP with `sequence > last_accepted + 1` MUST result in `PARK`.
- A `BACKWARD` ZIP MUST NOT be accepted unless all prior `FORWARD` ZIPs for the same `run_id` up to the same sequence are already in terminal status (`OK` or `PARK`).
- Replaying the same ordered sequence of ZIPs over the same initial state MUST produce identical resulting state hashes and identical emitted artifacts.
- Cross-run mixing of ZIPs is forbidden.

Validation determinism note:
- ZIP validation determinism is defined over extracted file bytes plus canonicalization and hash checks in this protocol.
- `ZIP bytes` in `A0-DET-01` means canonical producer bytes under Section 4 canonicalization rules.

## 7) VALIDATION OUTCOMES + REJECT TAGS

Outcomes:
- `OK`: structurally valid and accepted.
- `PARK`: structurally valid but deferred due to sequencing/replay preconditions.
- `REJECT`: contract violation.

PARK scope:
- Sequence-gap defer: `sequence > last_accepted + 1` for `(run_id, source_layer)`.
- Replay-prerequisite defer: `direction == BACKWARD` and required prior `FORWARD` ZIP coverage for the same `run_id` is incomplete.
- All other contract violations are `REJECT`.

No-implicit-defaults rule:
- If a required field is missing in any protocol artifact, the artifact is invalid.
- Validators and routers MUST NOT assume default values unless explicitly defined in this spec.

Reject tags (minimal set; deterministic mapping):
- `MISSING_HEADER_FIELD`:
  - missing required header field, invalid `zip_protocol`, invalid `run_id`, invalid `created_utc`, or invalid `compiler_version` policy value.
- `ZIP_TYPE_DIRECTION_MISMATCH`:
  - unknown `zip_type`, unknown/invalid `direction`, unknown/invalid `source_layer`, unknown/invalid `target_layer`, or `zip_type` mapping mismatch against `direction/source_layer/target_layer`.
- `SEQUENCE_REGRESSION`:
  - `sequence <= last_accepted` for `(run_id, source_layer)`.
- `INVALID_HASH_FORMAT`:
  - any hash not lowercase hex64 where required.
- `MANIFEST_HASH_MISMATCH`:
  - header `manifest_sha256` does not match canonical `MANIFEST.json` bytes.
- `HASHES_MISMATCH`:
  - hash line coverage mismatch, duplicate hash line, byte hash mismatch, or `byte_size` mismatch against actual bytes.
- `FORBIDDEN_FILE_PRESENT`:
  - any non-allowlisted file present, or manifest payload coverage mismatch against zip_type payload allowlist set.
- `FORBIDDEN_CONTAINER_PRESENT`:
  - forbidden container type found by exact full-line delimiter matching.
- `MANIFEST_PATH_INVALID`:
  - invalid `rel_path` normalization/path rules.
- `DUPLICATE_MANIFEST_PATH`:
  - duplicate `rel_path` in `MANIFEST.json`.
- `CONTAINER_BOUNDARY_INVALID`:
  - malformed strict container begin/end boundaries or block count violations for required container-bearing files.
