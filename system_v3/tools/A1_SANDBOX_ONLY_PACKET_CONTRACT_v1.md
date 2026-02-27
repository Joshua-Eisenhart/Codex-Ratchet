# A1 Sandbox-Only Packet Contract v1

This contract defines **sandbox-only** packets for A1 work.

## Invariants
- MUST NOT invoke A0/B/SIM.
- MUST NOT write to `system_v3/` except tool outputs under `work/`.
- MUST be sequential: one packet step at a time.
- MUST support multi-narrative generation (steelman + devils + rescuers) without schema drift.
- MUST be compact: avoid document explosion; store only structured deltas.

## Packet Types

### `A1_SANDBOX_TASK_ZIP_v1`
A single sandbox step. Contains a `REQUEST` and a `RESPONSE` artifact.

**Zip contents**
- `ZIP_HEADER.json`
- `MANIFEST.json`
- `A1_SANDBOX_TASK_REQUEST.json`
- `A1_SANDBOX_TASK_RESPONSE.json` (optional until completed)

**Request schema**: `A1_SANDBOX_TASK_REQUEST_v1`
- `run_id` (string)
- `sequence` (int)
- `task_kind` (enum):
  - `FUEL_INGEST`
  - `STEELMAN_BUILD`
  - `DEVILS_ADVOCATE_BUILD`
  - `BOUNDARY_TEST_BUILD`
  - `GRAVEYARD_SEED_PLAN`
  - `GRAVEYARD_RESCUE_PLAN`
  - `TERM_DEFINITION_DRAFT`
  - `SIM_DRAFT`
- `topic_terms` (list[string])
- `required_roles` (list[string])
- `inputs` (object):
  - `a1_brain_digest` (sha256 string)
  - `fuel_digest` (sha256 string)
  - `constraints` (list[string])

**Response schema**: `A1_SANDBOX_TASK_RESPONSE_v1`
- `run_id` (string)
- `sequence` (int)
- `role_outputs` (list[object]) where each object:
  - `role` (string)
  - `claims` (list[string])
  - `negative_classes` (list[string])
  - `proposed_terms` (list[string])
  - `term_definition_drafts` (list[object])
    - `term` (string)
    - `math_def` (string)  # professional, readable, explicit
    - `requires_terms` (list[string])
  - `sim_drafts` (list[object])
    - `sim_name` (string)
    - `sim_intent` (enum): `POSITIVE`|`NEGATIVE`
    - `probe_terms` (list[string])
    - `expected_kill_tokens` (list[string])
- `graveyard_seed_list` (list[string])  # concepts to dump to graveyard later (planning only)
- `brain_delta` (object):
  - `new_focus_terms` (list[string])
  - `new_open_questions` (list[string])

## Storage
Sandbox-only packets and state live under:
- `work/a1_sandbox_only/<run_id>/packets/`
- `work/a1_sandbox_only/<run_id>/brain/a1_brain.json`

Nothing in this contract is canonical to the ratchet until explicitly promoted into A1->A0 artifacts.
