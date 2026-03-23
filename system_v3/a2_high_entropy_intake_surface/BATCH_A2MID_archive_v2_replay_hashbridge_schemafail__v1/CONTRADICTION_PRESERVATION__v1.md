# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / BOUNDED A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_archive_v2_replay_hashbridge_schemafail__v1`
Date: 2026-03-09

## Preserved Contradictions
- contradiction 1:
  - summary and soak both count `3`
  - the event ledger retains only steps `1` and `2`, and step `3` survives only as a queued strategy packet
- contradiction 2:
  - step `1` ends on `8f4b8d3d...` while step `2` begins from `ac87f698...`
  - step `2` ends on `3f67cddc...` while summary and state bind to `b26e5e1d...`
- contradiction 3:
  - summary labels the run `replay`
  - summary also keeps `needs_real_llm true`, stops on operator exhaustion, and the inbox is empty despite queued continuation residue
- contradiction 4:
  - step 2 proposes both `S0002` lanes
  - final state keeps only `S_BIND_ALPHA_ALT_ALT_S0002`
- contradiction 5:
  - the first snapshot keeps pending evidence and both SIM packets emit `NEG_NEG_BOUNDARY`
  - final state keeps `evidence_pending` and `kill_log` empty
- contradiction 6:
  - the archive keeps local packet copies
  - event rows still point under `system_v3/runtime/...` and no `sequence_state.json` is retained

## Preservation Rule
- this batch keeps all contradictions above intact
- none of them are resolved into a clean three-step execution story, a self-sufficient replay story, or a clean bookkeeping story
