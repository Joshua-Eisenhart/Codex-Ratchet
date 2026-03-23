# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_A2MID_archive_qit_autoratchet_namespace_drift_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Preserved contradiction 1
- headline:
  - one completed step and one digest family versus eight retained passes and multi-digest history
- kept explicit:
  - `summary.json` says `steps_completed 1`
  - `summary.json` says each unique digest family count is `1`
  - `events.jsonl` preserves eight `step_result` rows
  - all retained rows still use step value `1`
  - retained result history preserves eight strategy digests, eight export content digests, and five export structural digests
- why it must survive:
  - the parent repeats the double-compression seam at larger scale, and it should not be flattened into one headline process story

## Preserved contradiction 2
- headline:
  - queue drain versus unresolved semantic state
- kept explicit:
  - no live strategy packets remain in `a1_inbox/`
  - all eight strategy packets survive in `a1_inbox/consumed/`
  - `unresolved_promotion_blocker_count 18`
  - all `18` sim promotion states are `PARKED`
  - final state still retains six kill signals, thirteen parked items, twenty-six reject rows, and four pending canonical evidence items
- why it must survive:
  - drain completion and semantic closure are separate layers in this run

## Preserved contradiction 3
- headline:
  - namespace drift versus single-family run framing
- kept explicit:
  - retained semantic ids split across `A_` and `Z_` prefixes
  - evidence keys mix `S000003_A_*` and `S000001_Z_*`
  - sim ids in retained result rows mix `A_SIM_*` and `Z_SIM_*`
  - the summary surface offers no explanation for the namespace split
- why it must survive:
  - the namespace split is the clean new contradiction packet in this parent and should not be normalized away

## Preserved contradiction 4
- headline:
  - same-name strategy family versus full byte divergence
- kept explicit:
  - filenames `000001` through `000008` appear in both consumed and embedded lanes
  - all eight aligned pairs diverge byte-for-byte
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
  - the `A_`/`Z_` namespace split as already resolved
  - same-name family continuity as packet identity continuity
  - state-hash and packet-family retention as full evidence closure
