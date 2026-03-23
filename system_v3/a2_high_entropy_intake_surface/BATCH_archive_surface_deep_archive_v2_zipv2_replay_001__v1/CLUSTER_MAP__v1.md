# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_v2_zipv2_replay_001__v1`
Date: 2026-03-09

## Cluster 1: Two Executed Replay Steps Plus One Queued Third Strategy
- archive meaning:
  - the run preserves a two-step executed replay spine and a third-step continuation only as a retained strategy packet
- bound evidence:
  - `events.jsonl` contains only steps `1` and `2`
  - `soak_report.md` and `summary.json` both count `3` cycles/completed steps
  - `zip_packets/000003_A1_TO_A0_STRATEGY_ZIP.zip` exists
  - `a1_inbox/` is empty
- retained interpretation:
  - useful historical example of summary/soak counting a queued continuation beyond the executed event spine

## Cluster 2: Hidden Hash Bridges Across The Executed Spine
- archive meaning:
  - the run preserves two distinct state bridges that are not visible as continuous event endpoints
- bound evidence:
  - step `1` ends on `8f4b8d3d...`, while step `2` begins from `ac87f698...`
  - step `2` ends on `3f67cddc...`, while summary/state bind to `b26e5e1d...`
  - third strategy input hash is `b26e5e1d...`
- retained interpretation:
  - useful archive evidence of replay-side normalization between executed rows and retained final continuation state

## Cluster 3: Replay Label With Real-LLM Demand
- archive meaning:
  - the run is replay-authored but still flags real-LLM need and operator exhaustion
- bound evidence:
  - `a1_source replay`
  - `needs_real_llm true`
  - `stop_reason A2_OPERATOR_SET_EXHAUSTED`
  - escalation reason `OPERATOR_SET_EXHAUSTED:SCHEMA_FAIL`
- retained interpretation:
  - useful contradiction surface showing replay authorship did not remove higher-level continuation demand

## Cluster 4: Step-2 Schema Failure Advances Only The Alternative Lane
- archive meaning:
  - the second executed step proposes both `S0002` lanes, but final state keeps only the alternative advancement
- bound evidence:
  - second strategy/export advance `S_BIND_ALPHA_S0002` and `S_BIND_ALPHA_ALT_ALT_S0002`
  - second step rejects once with `SCHEMA_FAIL`
  - final state keeps `S_BIND_ALPHA_ALT_ALT_S0002` but not `S_BIND_ALPHA_S0002`
  - second snapshot survivor ledger includes `S_BIND_ALPHA_ALT_ALT_S0002` only
- retained interpretation:
  - useful archive example of asymmetric survivor carryover after schema failure

## Cluster 5: SIM And Snapshot Residue Outrun Final Bookkeeping
- archive meaning:
  - packet-facing surfaces keep richer evidence and kill-condition residue than final state
- bound evidence:
  - first snapshot keeps `EVIDENCE_PENDING` for both `S0001` specs
  - both SIM packets emit `KILL_SIGNAL NEG_NEG_BOUNDARY`
  - final state keeps `evidence_pending` empty and `kill_log` empty
- retained interpretation:
  - useful archive seam between packet-facing residue and later state normalization

## Cluster 6: Empty Inbox With Retained Third Strategy Packet
- archive meaning:
  - the run root keeps no inbox residue even though continuation survives in packet form
- bound evidence:
  - `a1_inbox/` is empty
  - `zip_packets/000003_A1_TO_A0_STRATEGY_ZIP.zip` exists
  - no `A0_TO_A1_SAVE_ZIP` is retained
- retained interpretation:
  - useful archive sign that queued continuation packets were not always mirrored into inbox residue

## Cluster 7: Runtime-Local Event Paths And Missing Sequence Ledger
- archive meaning:
  - the archive retains local packet copies but event rows still point outward to the old runtime tree
- bound evidence:
  - `events.jsonl` packet and sim paths point under `system_v3/runtime/...`
  - archive-local copies exist under `zip_packets/`
  - top-level `sequence_state.json` is absent
- retained interpretation:
  - useful relocation-era archive signature for replay objects
