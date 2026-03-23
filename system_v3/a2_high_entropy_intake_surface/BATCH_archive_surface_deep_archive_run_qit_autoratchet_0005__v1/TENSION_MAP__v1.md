# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_qit_autoratchet_0005__v1`
Date: 2026-03-09

## Tension 1: One Completed Step Versus Eight Retained Result Passes
- source anchors:
  - `summary.json`
  - `events.jsonl`
  - `soak_report.md`
- bounded contradiction:
  - the summary says `steps_completed 1`, while the retained event and soak surfaces preserve eight separate result passes, all labeled as step `1`
- intake handling:
  - preserve as historical step compression rather than forcing the run into either "one pass" or "eight steps"

## Tension 2: Unique Digest Counts Of One Versus Multi-Digest Retained History
- source anchors:
  - `summary.json`
  - `events.jsonl`
- bounded contradiction:
  - the summary collapses strategy and export digest counts to `1`, while the retained result rows preserve `8` distinct strategy digests, `8` export content digests, and `5` export structural digests
- intake handling:
  - preserve both surfaces; the summary digest counts are historically informative precisely because they underreport retained diversity

## Tension 3: Flat Final Totals Versus Expanded Semantic Load
- source anchors:
  - `summary.json`
  - `state.json`
  - `events.jsonl`
- bounded contradiction:
  - the headline remains `accepted_total 3`, `parked_total 2`, and `rejected_total 2`, while final state expands to `8` evidence-pending items, `8` term-registry entries, `12` sim results, and `8` kill signals
- intake handling:
  - keep the headline window and semantic expansion separate; do not let the flat summary erase the larger retained state

## Tension 4: Soak Failure Tag Simplicity Versus Mixed State Residue
- source anchors:
  - `soak_report.md`
  - `state.json`
- bounded contradiction:
  - soak reports only `SCHEMA_FAIL: 3` as the top failure tag, while final state preserves `NEAR_REDUNDANT`, `SCHEMA_FAIL`, and `PROBE_PRESSURE` across park and reject residue
- intake handling:
  - preserve both surfaces; the soak view is a narrow recent-failure window, not a complete residue taxonomy

## Tension 5: Namespace Drift Versus Single-Family Run Framing
- source anchors:
  - `state.json`
  - `events.jsonl`
- bounded contradiction:
  - retained semantic ids split across `A_` and `Z_` prefixes inside one run family, while the top-line summary presents the run as a single coherent state surface with no explanation for the prefix drift
- intake handling:
  - keep the namespace split explicit; do not normalize the ids into one family without source proof

## Tension 6: Same Filenames Versus Different Strategy Bytes Across Eight Pairs
- source anchors:
  - `zip_packets/000001_A1_TO_A0_STRATEGY_ZIP.zip` through `zip_packets/000008_A1_TO_A0_STRATEGY_ZIP.zip`
  - `a1_inbox/consumed/000001_A1_TO_A0_STRATEGY_ZIP.zip` through `a1_inbox/consumed/000008_A1_TO_A0_STRATEGY_ZIP.zip`
- bounded contradiction:
  - all eight same-name consumed-versus-embedded strategy packet pairs preserve different bytes
- intake handling:
  - keep the whole family as packet-lineage warning; filename continuity does not imply payload continuity in this archive run

