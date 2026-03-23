# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_A2MID_archive_qit_autoratchet_queue_drain_step_compression_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Preserved contradiction 1
- headline:
  - one completed step versus five retained passes
- kept explicit:
  - `summary.json` says `steps_completed 1`
  - `events.jsonl` preserves five `step_result` rows
  - all retained rows still use step value `1`
  - `soak_report.md` keeps last-event texture across packets `000001` through `000005`
- why it must survive:
  - the parent's strongest contradiction is structural compression, and it should not be flattened into a single step story

## Preserved contradiction 2
- headline:
  - queue drain versus unresolved semantic state
- kept explicit:
  - no live strategy packets remain in `a1_inbox/`
  - all five strategy packets survive in `a1_inbox/consumed/`
  - `unresolved_promotion_blocker_count 13`
  - all `13` sim promotion states are `PARKED`
  - final state still retains kill, park, reject, and evidence-pending burden
- why it must survive:
  - drain completion and semantic closure are separate layers in this run

## Preserved contradiction 3
- headline:
  - partial sequence-ledger alignment versus noninterchangeable surfaces
- kept explicit:
  - root and inbox ledgers both preserve terminal A1 max `5`
  - JSON shapes differ
  - retained scopes differ
- why it must survive:
  - alignment on one scalar does not collapse two historical ledgers into one surface

## Preserved contradiction 4
- headline:
  - same-name strategy family versus full byte divergence
- kept explicit:
  - filenames `000001` through `000005` appear in both consumed and embedded lanes
  - all five aligned pairs diverge byte-for-byte
- why it must survive:
  - filename continuity is weaker than payload continuity across the whole retained family

## Preserved contradiction 5
- headline:
  - strong integrity versus missing evidence bodies
- kept explicit:
  - `state.json` hash matches `summary.json` final state hash
  - archive surfaces still reference `sim/sim_evidence_*`
  - no local `sim/` subtree is retained
- why it must survive:
  - structural integrity and packet retention outlive evidence-body preservation in this archive object

## Non-preserved overreads
- not preserved:
  - the one-step headline as full process truth
  - queue drain as readiness or closure
  - root and inbox sequence ledgers as interchangeable copies
  - same-name family continuity as packet identity continuity
  - state-hash and packet-family retention as full evidence closure
