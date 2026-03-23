# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_qit_autoratchet_0001__v1`
Date: 2026-03-09

## Cluster 1: Small Autoratchet Edge Run
- archive meaning:
  - this object preserves a direct small autoratchet run that includes both queue state and a restored sequence ledger
- bound evidence:
  - `sequence_state.json` exists
  - `a1_inbox/` contains live unconsumed packets
  - no wrapper bundle or README is present
- retained interpretation:
  - useful as an archive example of a run captured mid-queue rather than after full inbox drain

## Cluster 2: Accepted Step Hidden By Zeroed Summary
- archive meaning:
  - the run preserves one accepted first step even though its headline counters were flattened to zero
- bound evidence:
  - `events.jsonl` step-result row records `accepted 7`
  - `state.json` keeps `accepted_batch_count 1` and `canonical_ledger_len 1`
  - `summary.json` and `soak_report.md` both say `accepted_total 0`
- retained interpretation:
  - this archive object should be read as post-success failure-masked, not as a true zero-accept run

## Cluster 3: Sequence-Gap Queue Failure
- archive meaning:
  - the run’s dominant failure mode is queued packet continuation breaking on sequence expectations
- bound evidence:
  - four repeated `a1_packet_zip_invalid::SEQUENCE_GAP` rows
  - active inbox still contains packets `000002` through `000005`
  - consumed lane contains only `000001`
- retained interpretation:
  - good historical evidence for autoratchet queue discipline failure rather than semantic rejection failure

## Cluster 4: Parked Semantic Burden Without Parked Packets
- archive meaning:
  - semantic burden remains even when packet-level park/reject counters are zero
- bound evidence:
  - both retained sims are marked `PARKED`
  - `evidence_pending` contains one canonical item
  - `kill_log_len 2` with token `NEG_INFINITE_SET`
  - `park_set_len 0` and `reject_log_len 0`
- retained interpretation:
  - archive preserves an important demotion pattern: parked semantic outcomes can exist without any packet-park surface

## Cluster 5: Same-Name Strategy Packet Divergence
- archive meaning:
  - consumed input residue and embedded transport residue are not interchangeable even when filenames match
- bound evidence:
  - consumed `000001_A1_TO_A0_STRATEGY_ZIP.zip` hash `2a91f3ec...`
  - embedded `000001_A1_TO_A0_STRATEGY_ZIP.zip` hash `69133caf...`
- retained interpretation:
  - this is a strong packet-lineage contradiction worth preserving for later audit and demotion history

