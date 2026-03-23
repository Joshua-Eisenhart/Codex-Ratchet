# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_A2MID_archive_qit_autoratchet_double_compression_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Preserved contradiction 1
- headline:
  - one completed step and one digest family versus six retained passes and multi-digest history
- kept explicit:
  - `summary.json` says `steps_completed 1`
  - `summary.json` says each unique digest family count is `1`
  - `events.jsonl` preserves six `step_result` rows
  - all retained rows still use step value `1`
  - retained result history preserves six strategy digests, six export content digests, and five export structural digests
- why it must survive:
  - the parent's strongest contradiction is double compression, and it should not be flattened into one headline process story

## Preserved contradiction 2
- headline:
  - queue drain versus unresolved semantic state
- kept explicit:
  - no live strategy packets remain in `a1_inbox/`
  - all six strategy packets survive in `a1_inbox/consumed/`
  - `unresolved_promotion_blocker_count 14`
  - all `14` sim promotion states are `PARKED`
  - final state still retains six kill signals, nine parked items, eighteen reject rows, and four pending canonical evidence items
- why it must survive:
  - drain completion and semantic closure are separate layers in this run

## Preserved contradiction 3
- headline:
  - dual-ledger alignment versus noninterchangeable surfaces
- kept explicit:
  - root and inbox ledgers both preserve terminal A1 max `6`
  - JSON shapes differ
  - retained scopes differ
- why it must survive:
  - alignment on one scalar does not collapse two historical ledgers into one surface

## Preserved contradiction 4
- headline:
  - same-name strategy family versus full byte divergence
- kept explicit:
  - filenames `000001` through `000006` appear in both consumed and embedded lanes
  - all six aligned pairs diverge byte-for-byte
- why it must survive:
  - filename continuity is weaker than payload continuity across the whole retained family

## Preserved contradiction 5
- headline:
  - strong integrity versus missing evidence bodies
- kept explicit:
  - `state.json` hash matches `summary.json` final state hash
  - archive surfaces still reference retained sim result paths and evidence obligations
  - no local `sim/` subtree is retained
- why it must survive:
  - structural integrity and packet retention outlive evidence-body preservation in this archive object

## Non-preserved overreads
- not preserved:
  - the one-step and one-digest headline as full process truth
  - queue drain as readiness or closure
  - root and inbox sequence ledgers as interchangeable copies
  - same-name family continuity as packet identity continuity
  - state-hash and packet-family retention as full evidence closure
