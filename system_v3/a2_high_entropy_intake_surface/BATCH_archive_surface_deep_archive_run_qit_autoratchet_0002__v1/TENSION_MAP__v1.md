# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_qit_autoratchet_0002__v1`
Date: 2026-03-09

## Tension 1: One Completed Step Versus Five Retained Step Results
- source anchors:
  - `summary.json`
  - `events.jsonl`
  - `soak_report.md`
- bounded contradiction:
  - the summary says `steps_completed 1`, while the event ledger and soak window preserve five separate result passes, all labeled as step `1`
- intake handling:
  - preserve as historical step-compression rather than forcing the run into either "one pass" or "five steps"

## Tension 2: Narrow Headline Counters Versus Larger Final-State Burden
- source anchors:
  - `summary.json`
  - `state.json`
  - `soak_report.md`
- bounded contradiction:
  - top-line counters end at `accepted_total 4`, `parked_total 1`, and `rejected_total 10`, while final state still retains four kill signals, three parked semidefinite sims, thirty-three reject rows, and thirteen parked sim promotions
- intake handling:
  - keep the headline window and the deeper residue separate; do not treat either one as a complete substitute for the other

## Tension 3: Queue Drain Versus Unresolved Promotion State
- source anchors:
  - `a1_inbox/consumed/`
  - `summary.json`
  - `state.json`
- bounded contradiction:
  - all five strategy packets were consumed and no live inbox backlog remains, yet `unresolved_promotion_blocker_count` is `13` and every retained sim promotion state is still `PARKED`
- intake handling:
  - preserve as archive evidence that queue completion did not resolve semantic promotion or evidence debt

## Tension 4: Matching A1 Sequence Max Versus Non-Identical Sequence Ledgers
- source anchors:
  - root `sequence_state.json`
  - `a1_inbox/sequence_state.json`
- bounded contradiction:
  - both ledgers preserve the same terminal A1 max of `5`, but the retained JSON surfaces are structurally different and therefore not interchangeable
- intake handling:
  - keep both ledgers as separate historical surfaces rather than collapsing the inbox-local view into the full run ledger

## Tension 5: Same Filenames Versus Different Strategy Bytes Across The Entire Family
- source anchors:
  - `zip_packets/000001_A1_TO_A0_STRATEGY_ZIP.zip` through `zip_packets/000005_A1_TO_A0_STRATEGY_ZIP.zip`
  - `a1_inbox/consumed/000001_A1_TO_A0_STRATEGY_ZIP.zip` through `a1_inbox/consumed/000005_A1_TO_A0_STRATEGY_ZIP.zip`
- bounded contradiction:
  - all five same-name consumed-versus-embedded strategy packet pairs preserve different bytes
- intake handling:
  - preserve the full family as a packet-lineage warning; filename continuity does not imply payload continuity in this archive run

