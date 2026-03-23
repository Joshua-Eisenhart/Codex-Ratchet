# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_A2MID_archive_registry_smoke_transport_semantic_gap_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Preserved contradiction 1
- headline:
  - one completed step versus two retained accepted passes
- kept explicit:
  - `summary.json` says `steps_completed 1`
  - `events.jsonl` preserves two retained result rows
  - both retained result rows still use step value `1`
  - `soak_report.md` preserves the same two accepted result passes
- why it must survive:
  - the run's strongest archive value is small-scale step compression, and that should not be flattened into one simple process story

## Preserved contradiction 2
- headline:
  - `accepted_total 7` versus two accepted-seven passes
- kept explicit:
  - `summary.json` says `accepted_total 7`
  - both retained result rows show `accepted 7`
  - `state.json` keeps `accepted_batch_count 2`
- why it must survive:
  - the parent compresses accepted history into one headline window while still retaining two accepted-seven passes underneath

## Preserved contradiction 3
- headline:
  - zero packet parks/rejections versus parked semantic outcomes
- kept explicit:
  - packet-facing surfaces end at:
    - `parked_total 0`
    - `rejected_total 0`
  - `state.json` still keeps:
    - two pending canonical evidence obligations
    - four kill signals
    - four sim promotion states, all `PARKED`
- why it must survive:
  - transport cleanliness is not semantic closure in this archive run

## Preserved contradiction 4
- headline:
  - unique digest counts of one versus retained two-digest history
- kept explicit:
  - `summary.json` reports each unique digest family count as `1`
  - `events.jsonl` still preserves:
    - `2` strategy digests
    - `2` export content digests
    - `2` export structural digests
- why it must survive:
  - the parent's digest counts are historically useful precisely because they underreport retained diversity

## Preserved contradiction 5
- headline:
  - retained SIM outputs versus empty evidence paths
- kept explicit:
  - retained result rows reference four SIM outputs
  - every retained `sim_outputs[].path` field is an empty string
  - the run root keeps no local `sim/` directory
- why it must survive:
  - SIM-result lineage survives more cleanly than evidence-body preservation here

## Preserved contradiction 6
- headline:
  - same filenames versus different strategy bytes
- kept explicit:
  - `000001_A1_TO_A0_STRATEGY_ZIP.zip` appears in both consumed and embedded lanes
  - `000002_A1_TO_A0_STRATEGY_ZIP.zip` appears in both consumed and embedded lanes
  - both same-name pairs differ byte-for-byte
- why it must survive:
  - filename continuity is weaker than payload continuity in this archive object

## Non-preserved overreads
- not preserved:
  - the one-step and `accepted_total 7` headline as full run truth
  - zero packet parks/rejects as proof of no semantic burden
  - digest counts of one as full retained history
  - SIM-output references and matching state hash as full evidence closure
  - same-name strategy continuity as packet identity continuity
