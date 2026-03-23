# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_v2_zipv2_packet_e2e_001__v1`
Date: 2026-03-09

## Cluster 1: One Executed ZIPv2 Cycle Plus External A1 Save-Request
- archive meaning:
  - this run preserves one fully executed packet cycle and then stops by emitting an external save-request rather than a second executed strategy result
- bound evidence:
  - `summary.json` and `soak_report.md` both keep `steps/cycle 2`
  - `events.jsonl` step `1` is the only executed step-result row
  - `events.jsonl` step `2` is `a1_strategy_request_emitted`
  - `zip_packets/` keeps one strategy, one export, one Thread-S snapshot, one SIM result, and one `A0_TO_A1_SAVE_ZIP`
- retained interpretation:
  - useful historical example of a compact ZIPv2 loop transitioning directly into handoff state

## Cluster 2: Final Retained State Appears Through Request Emission Rather Than Executed Result
- archive meaning:
  - the final retained state is visible only through the save-request row, not through a second executed step-result row
- bound evidence:
  - step `1` ends on `3aede158...`
  - summary and `state.json.sha256` bind to `5b0f04fe...`
  - step `2` request row carries `state_hash 5b0f04fe...`
- retained interpretation:
  - useful archive seam between executed event endpoints and later retained handoff state

## Cluster 3: Clean Packet Counters With Open Promotion And No Canonical Ledger
- archive meaning:
  - packet transport is clean while semantic closure remains unresolved and canonical ledger retention is absent
- bound evidence:
  - summary and soak report keep `parked_total 0` and `rejected_total 0`
  - state keeps one `PARKED` promotion status and one unresolved blocker
  - state also keeps `accepted_batch_count 1` with `canonical_ledger_len 0`
- retained interpretation:
  - useful historical split between transport success, promotion status, and canonical bookkeeping

## Cluster 4: Same-Name Strategy Packet Divergence
- archive meaning:
  - the archive keeps two non-equivalent versions of `000001_A1_TO_A0_STRATEGY_ZIP.zip`
- bound evidence:
  - retained packet sha256 is `18b3943e...`
  - consumed packet sha256 is `2f205f54...`
  - retained packet carries target plus alternative lanes, typed fields, and populated self-audit
  - consumed packet collapses to one generic target, no alternatives, and all-zero input state
- retained interpretation:
  - useful archive contradiction showing that same-name packet identity did not guarantee semantic identity

## Cluster 5: Snapshot And SIM Residue Outrun Final State Bookkeeping
- archive meaning:
  - packet-facing surfaces keep richer evidence and kill-condition residue than the final state
- bound evidence:
  - `THREAD_S_SAVE_SNAPSHOT_v2.txt` keeps `EVIDENCE_PENDING` for `S_BIND_ALPHA_S0001`
  - `SIM_EVIDENCE.txt` keeps `EVIDENCE_SIGNAL E_BIND_ALPHA` and `KILL_SIGNAL NEG_NEG_BOUNDARY`
  - final `state.json` keeps `evidence_pending` empty and `kill_log` empty
- retained interpretation:
  - useful archive seam between Thread-S/SIM residue and later machine-state normalization

## Cluster 6: Runtime-Local Event Paths And Missing Sequence Ledger
- archive meaning:
  - the archived run still points outward to the old runtime tree and does not preserve `sequence_state.json`
- bound evidence:
  - `events.jsonl` references packet and sim paths under `system_v3/runtime/...`
  - archive-local copies of the same packet family are present under `zip_packets/`
  - top-level `sequence_state.json` is absent
- retained interpretation:
  - useful relocation-era archive signature showing path leakage and missing local sequence counters
