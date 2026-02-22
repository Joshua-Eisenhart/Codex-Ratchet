
# A2_PERCEPTION_FRAME v1

This specification defines the structured perception object used by A2 for meta-reasoning.
It is intended to be deterministically derivable from artifact history (ZIPs + summaries).

A2_PERCEPTION_FRAME is **non-kernel** and must never be treated as canonical mutation.

## 1. Container / file form
A2 perception is carried inside `A2_PROPOSAL.json` (in `A2_TO_A1_PROPOSAL_ZIP`) as a JSON object under key `perception_frame`.

## 2. Required top-level fields
- `schema`: MUST equal `"A2_PERCEPTION_FRAME_v1"`
- `run_id`: string
- `a0_state_hash`: lowercase hex64 or `""`
- `last_sequence_seen`: integer (max sequence observed by A2 for this run_id)
- `summaries`: object (see below)
- `reject_histogram`: object (see below)
- `sim_outcomes`: object (see below)
- `graveyard_summary`: object (see below)

## 3. summaries object (required)
- `a0_save_zip_sha256`: lowercase hex64 or `""`
- `a1_save_zip_sha256`: lowercase hex64 or `""`
- `state_update_zip_sha256`: lowercase hex64 or `""`
- `sim_result_zip_sha256`: lowercase hex64 or `""`

## 4. reject_histogram object (required)
A mapping: reject_tag → integer count.
Reject tags SHOULD be those defined in `ZIP_PROTOCOL_v2` plus any deterministic kernel/compiler tags A0 exposes (non-ZIP tags may be namespaced by layer).

Example:
- `FORBIDDEN_FILE_PRESENT`: 2
- `HASHES_MISMATCH`: 1
- `A0.SCHEMA_FAIL`: 1

## 5. sim_outcomes object (required)
Deterministic aggregation over recent SIM_EVIDENCE blocks.

Required fields:
- `sim_pass_count`: integer
- `sim_fail_count`: integer
- `kill_signal_count`: integer
- `evidence_signal_count`: integer
- `last_kill_targets`: array of strings (sorted, deduped)

No probabilities; counts only.

## 6. graveyard_summary object (required)
Deterministic aggregation over graveyard state as exposed by A0 save summary.

Required fields:
- `graveyard_item_count`: integer
- `graveyard_by_kind`: object mapping spec_kind → integer

## 7. Use
A2 uses the perception frame to produce advisory outputs:
- candidate repair hypotheses
- constraint tightening suggestions
- SIM expansion suggestions
- coverage gap notes

All outputs must pass through A1 strategy packaging and A0 compilation before reaching B.
