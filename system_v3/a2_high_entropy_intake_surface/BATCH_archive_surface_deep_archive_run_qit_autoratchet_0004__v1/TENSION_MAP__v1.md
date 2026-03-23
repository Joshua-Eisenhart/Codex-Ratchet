# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_qit_autoratchet_0004__v1`
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

## Tension 3: Final-Window Totals Versus Larger Park/Reject Residue
- source anchors:
  - `summary.json`
  - `state.json`
  - `soak_report.md`
- bounded contradiction:
  - top-line counters end at `accepted_total 3`, `parked_total 2`, and `rejected_total 2`, while final state still retains thirteen parked items, twenty-six reject rows, six kill signals, and eighteen parked sim promotions
- intake handling:
  - keep the headline window and deeper residue separate; do not let either one erase the other

## Tension 4: Queue Drain Versus Unresolved Promotion Debt
- source anchors:
  - `a1_inbox/consumed/`
  - `summary.json`
  - `state.json`
- bounded contradiction:
  - all eight strategy packets were consumed and no live inbox backlog remains, yet `unresolved_promotion_blocker_count` is `18`, all sim promotion states are `PARKED`, and four canonical evidence items remain pending
- intake handling:
  - preserve as archive evidence that queue completion did not produce promotion closure

## Tension 5: Namespace Drift Versus Single-Family Run Framing
- source anchors:
  - `state.json`
  - `soak_report.md`
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

