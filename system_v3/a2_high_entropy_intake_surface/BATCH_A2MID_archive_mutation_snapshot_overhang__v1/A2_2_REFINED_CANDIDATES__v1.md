# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_archive_mutation_snapshot_overhang__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Candidate RC1: `ONE_STEP_MUTATION_SPINE_STAYS_THE_PRIMARY_EXECUTED_CORE`
- candidate read:
  - controller reads should preserve that `TEST_STATE_TRANSITION_MUTATION` has one executed strategy/export/snapshot spine with two retained SIM returns and no queued continuation packet
- why candidate:
  - this is the parent's strongest bounded execution core
- parent dependencies:
  - `summary.json`
  - `state.json`
  - `sequence_state.json`
  - `events.jsonl`
  - `zip_packets/`

## Candidate RC2: `SUMMARY_STATE_FINAL_HASH_OUTRANKS_THE_ONLY_EVENT_ENDPOINT`
- candidate read:
  - controller reads should preserve the summary/state-sidecar final hash `63995c34...` as the stronger retained closure over the only executed event endpoint `fcb5d2fe...`
- why candidate:
  - this is the parent's narrowest closure-layer authority fence
- parent dependencies:
  - `summary.json`
  - `state.json.sha256`
  - `events.jsonl`

## Candidate RC3: `ZERO_PACKET_PARKS_DO_NOT_CANCEL_TWO_PARKED_PROMOTION_STATES`
- candidate read:
  - controller reads should preserve that summary and soak report zero parked packets while final state still keeps two `PARKED` promotion states and two unresolved blockers
- why candidate:
  - this is the parent's clearest transport-cleanliness versus semantic-closure split
- parent dependencies:
  - `summary.json`
  - `soak_report.md`
  - `state.json`

## Candidate RC4: `SNAPSHOT_PENDING_EVIDENCE_CAN_SURVIVE_ABOVE_EMPTY_FINAL_EVIDENCE_PENDING`
- candidate read:
  - controller reads should preserve that the retained Thread-S snapshot still lists both retained specs under `EVIDENCE_PENDING` while final state keeps `evidence_pending` empty
- why candidate:
  - this is the parent's cleanest snapshot-versus-final-state bookkeeping seam
- parent dependencies:
  - `state.json`
  - `zip_packets/000001_B_TO_A0_STATE_UPDATE_ZIP.zip`

## Candidate RC5: `EXPORT_AND_SNAPSHOT_KILL_IF_RESIDUE_CAN_SURVIVE_ABOVE_EMPTY_FINAL_KILL_LOG`
- candidate read:
  - controller reads should preserve that export and snapshot both retain `KILL_IF ... NEG_NEG_BOUNDARY` lines for both specs while final state keeps `kill_log` empty and retained SIM evidence stays free of explicit kill-signal lines
- why candidate:
  - this is the parent's strongest pre-SIM kill-intent versus final-bookkeeping contradiction
- parent dependencies:
  - `zip_packets/000001_A0_TO_B_EXPORT_BATCH_ZIP.zip`
  - `zip_packets/000001_B_TO_A0_STATE_UPDATE_ZIP.zip`
  - `state.json`
  - `zip_packets/000001_SIM_TO_A0_SIM_RESULT_ZIP.zip`
  - `zip_packets/000002_SIM_TO_A0_SIM_RESULT_ZIP.zip`

## Candidate RC6: `DUPLICATE_2_FILES_EMPTY_SHELLS_AND_RUNTIME_PATH_LEAKAGE_STAY_RESIDUE_ONLY`
- candidate read:
  - controller reads should preserve the exact duplicate ` 2` file family, the empty residue directories, and the event rows that still point under `system_v3/runtime/...` as archive-side residue only, not as a newer execution lane or live-runtime authority
- why candidate:
  - this is the parent's distinctive packaging-and-relocation seam
- parent dependencies:
  - `{summary 2.json,state 2.json,state.json 2.sha256,sequence_state 2.json,events 2.jsonl,soak_report 2.md}`
  - `{a1_inbox,a1_strategies 2,outbox 2,reports 2,zip_packets 2}`
  - `events.jsonl`
  - `MANIFEST.json`

## Quarantined Q1: `SOLE_EVENT_ENDPOINT_AS_FULL_FINAL_CLOSURE`
- quarantine read:
  - do not let the only executed event endpoint retell the run as if there were no higher retained final snapshot/state layer
- why quarantined:
  - the parent explicitly preserves final closure at `63995c34...`, not at the event row endpoint `fcb5d2fe...`
- parent dependencies:
  - `summary.json`
  - `state.json.sha256`
  - `events.jsonl`

## Quarantined Q2: `ZERO_PARKED_PACKETS_AS_PROOF_OF_PROMOTION_CLOSURE`
- quarantine read:
  - do not let zero parked packets convert the run into a closed semantic-promotion success
- why quarantined:
  - the parent explicitly preserves two `PARKED` promotion states and two unresolved blockers
- parent dependencies:
  - `summary.json`
  - `soak_report.md`
  - `state.json`

## Quarantined Q3: `SNAPSHOT_EXPORT_RESIDUE_AS_ALREADY_CONSUMED_BY_FINAL_BOOKKEEPING`
- quarantine read:
  - do not collapse snapshot `EVIDENCE_PENDING` entries or export/snapshot `KILL_IF` lines into a story where final bookkeeping already absorbed them cleanly
- why quarantined:
  - the parent explicitly keeps `evidence_pending` and `kill_log` empty while those richer upper-layer residues still survive
- parent dependencies:
  - `zip_packets/000001_A0_TO_B_EXPORT_BATCH_ZIP.zip`
  - `zip_packets/000001_B_TO_A0_STATE_UPDATE_ZIP.zip`
  - `state.json`

## Quarantined Q4: `DUPLICATE_2_FILES_EMPTY_SHELLS_AND_RUNTIME_PATHS_AS_NEW_EXECUTION_OR_LIVE_AUTHORITY`
- quarantine read:
  - do not turn duplicate ` 2` files, empty residue directories, or runtime absolute paths into proof of a second execution branch or current live-runtime authority
- why quarantined:
  - the parent explicitly preserves them as packaging and relocation residue only
- parent dependencies:
  - `{summary 2.json,state 2.json,state.json 2.sha256,sequence_state 2.json,events 2.jsonl,soak_report 2.md}`
  - `{a1_inbox,a1_strategies 2,outbox 2,reports 2,zip_packets 2}`
  - `events.jsonl`
