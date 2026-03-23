# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_v2_zipv2_replay_001__v1`
Date: 2026-03-09

## Tension 1: Summary/Soak Count Three Cycles While Events Retain Two Steps
- source anchors:
  - `summary.json`
  - `soak_report.md`
  - `events.jsonl`
  - `zip_packets/000003_A1_TO_A0_STRATEGY_ZIP.zip`
- bounded contradiction:
  - summary and soak report both count `3`, while the event ledger retains only steps `1` and `2`; the only trace of step `3` is the queued third strategy packet
- intake handling:
  - preserve executed events and queued continuation separately rather than flattening them into one notion of completed work

## Tension 2: Hidden Hash Bridges Across Executed And Final State
- source anchors:
  - `events.jsonl`
  - `summary.json`
  - `state.json.sha256`
  - `000003_A1_TO_A0_STRATEGY_ZIP.zip`
- bounded contradiction:
  - step `1` ends on `8f4b8d3d...` while step `2` begins from `ac87f698...`, and step `2` ends on `3f67cddc...` while summary/state bind to `b26e5e1d...`; the third strategy packet uses `b26e5e1d...` as its input state
- intake handling:
  - preserve both hidden bridges explicitly as replay-side normalization residue

## Tension 3: Replay Authorship Versus Real-LLM Demand
- source anchors:
  - `summary.json`
  - empty `a1_inbox/`
- bounded contradiction:
  - summary says `a1_source replay`, yet also marks `needs_real_llm true` and stops on operator exhaustion with no retained inbox continuation
- intake handling:
  - preserve replay labeling and real-LLM demand together rather than resolving one against the other

## Tension 4: Step-2 `SCHEMA_FAIL` Versus Partial Alternative-Lane Advancement
- source anchors:
  - `events.jsonl`
  - `000002_A1_TO_A0_STRATEGY_ZIP.zip`
  - `000002_A0_TO_B_EXPORT_BATCH_ZIP.zip`
  - `000002_B_TO_A0_STATE_UPDATE_ZIP.zip`
  - `state.json`
- bounded contradiction:
  - second-step strategy/export propose both `S0002` lanes, but final state and second snapshot keep only `S_BIND_ALPHA_ALT_ALT_S0002` after a recorded `SCHEMA_FAIL`
- intake handling:
  - preserve asymmetric advancement instead of smoothing it into full failure or full success

## Tension 5: SIM Kill Signals And Snapshot Pending Evidence Versus Empty Final Logs
- source anchors:
  - `000001_B_TO_A0_STATE_UPDATE_ZIP.zip`
  - both retained SIM packets
  - `state.json`
- bounded contradiction:
  - first snapshot keeps `EVIDENCE_PENDING` for both `S0001` specs and both SIM packets emit `NEG_NEG_BOUNDARY`, while final state keeps `evidence_pending` and `kill_log` empty
- intake handling:
  - preserve packet-facing residue without forcing it into final bookkeeping

## Tension 6: Empty Inbox Versus Retained Queued Third Strategy
- source anchors:
  - `a1_inbox/`
  - `zip_packets/000003_A1_TO_A0_STRATEGY_ZIP.zip`
- bounded contradiction:
  - the run keeps no inbox residue even though a third strategy packet is retained locally
- intake handling:
  - preserve the gap between packet retention and inbox retention as archive packaging behavior

## Tension 7: Archive-Local Packet Copies Versus Runtime-Local Event Paths
- source anchors:
  - `events.jsonl`
  - archive-local `zip_packets/`
- bounded contradiction:
  - the archive retains local packet copies, but event rows still point to `system_v3/runtime/...` packet and sim paths
- intake handling:
  - preserve path leakage as relocation residue instead of rewriting it away
