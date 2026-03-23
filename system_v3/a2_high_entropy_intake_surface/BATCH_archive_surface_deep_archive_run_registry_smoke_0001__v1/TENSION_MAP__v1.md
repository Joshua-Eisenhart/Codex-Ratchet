# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_registry_smoke_0001__v1`
Date: 2026-03-09

## Tension 1: One Completed Step Versus Two Retained Accepted Passes
- source anchors:
  - `summary.json`
  - `events.jsonl`
  - `soak_report.md`
- bounded contradiction:
  - the summary says `steps_completed 1`, while the retained event and soak surfaces preserve two accepted result passes, both still labeled step `1`
- intake handling:
  - preserve as historical step compression rather than forcing the run into either "one pass" or "two steps"

## Tension 2: Accepted Total Seven Versus Two Accepted-Seven Passes
- source anchors:
  - `summary.json`
  - `events.jsonl`
  - `state.json`
- bounded contradiction:
  - the summary reports `accepted_total 7`, while the retained result rows each report `accepted 7` and state preserves `accepted_batch_count 2`
- intake handling:
  - preserve as a compressed headline window rather than inferring that the run only accepted seven items overall

## Tension 3: Zero Packet Parks/Rejections Versus Parked Semantic Outcomes
- source anchors:
  - `summary.json`
  - `state.json`
  - `soak_report.md`
- bounded contradiction:
  - packet-level surfaces report zero parks and zero rejects, while state marks all four retained sim outcomes as `PARKED` and keeps two pending canonical evidence items
- intake handling:
  - keep the distinction between transport cleanliness and semantic promotion state

## Tension 4: Unique Digest Counts Of One Versus Two-Digest Retained History
- source anchors:
  - `summary.json`
  - `events.jsonl`
- bounded contradiction:
  - the summary collapses strategy and export digest counts to `1`, while the retained result rows preserve `2` distinct strategy digests, `2` export content digests, and `2` export structural digests
- intake handling:
  - preserve both surfaces; the summary digest counts are historically informative precisely because they underreport retained diversity

## Tension 5: SIM Output References Versus Empty Evidence Paths
- source anchors:
  - `events.jsonl`
  - `soak_report.md`
- bounded contradiction:
  - retained result rows include four SIM outputs, but every `sim_outputs[].path` field is an empty string and the run root keeps no `sim/` directory
- intake handling:
  - preserve as archive evidence of SIM-result retention without usable evidence-body paths

## Tension 6: Same Filenames Versus Different Strategy Bytes Across Two Pairs
- source anchors:
  - `zip_packets/000001_A1_TO_A0_STRATEGY_ZIP.zip`
  - `zip_packets/000002_A1_TO_A0_STRATEGY_ZIP.zip`
  - `a1_inbox/consumed/000001_A1_TO_A0_STRATEGY_ZIP.zip`
  - `a1_inbox/consumed/000002_A1_TO_A0_STRATEGY_ZIP.zip`
- bounded contradiction:
  - both same-name consumed-versus-embedded strategy packet pairs preserve different bytes
- intake handling:
  - keep the family as packet-lineage warning; filename continuity does not imply payload continuity in this archive run

