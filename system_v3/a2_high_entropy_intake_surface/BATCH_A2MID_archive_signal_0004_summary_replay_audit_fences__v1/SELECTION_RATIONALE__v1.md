# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_A2MID_archive_signal_0004_summary_replay_audit_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Why this parent was selected
- the previous child explicitly handed off into `RUN_SIGNAL_0004`
- the parent is the next live archive descendant and keeps the signal-run fail-closed promotion spine while adding two new high-yield seams:
  - summary compression over a larger retained transport surface
  - deterministic replay audit that still diverges from both run-final and event-final hashes

## Why reduction is useful
- it preserves the run as a hybrid signal-plus-audit archive object instead of letting it flatten into a plain direct signal run or a cleaner replay story
- it preserves the forty-step summary separately from the retained sixty-pass A1 lattice and the `640` versus `960` accepted-flow split
- it preserves packet cleanliness separately from the larger semantic debt in final state
- it preserves replay determinism separately from replay authority and replay closure
- it preserves root-only sequence retention and renamed strategy-lane discontinuity

## Why the comparison anchors were sufficient
- `BATCH_A2MID_archive_signal_0003_negative_residue_hashdrift_fences__v1` preserves the nearest direct sibling with the same fail-closed promotion and stronger-snapshot-than-event closure spine
- `BATCH_A2MID_archive_signal_0002_failclosed_promotion_hashdrift_fences__v1` preserves the larger direct signal sibling with the same renamed consumed-lane split
- `BATCH_A2MID_archive_run_foundation_packet_failure_evidence_fences__v1` preserves the broader archive failure and evidence baseline beneath which this run must still remain archive history

## What stays out of scope
- no mutation of active A2 state surfaces
- no reopening of sibling runs beyond the next bounded handoff
- no claim that forty-step summary counts are the full retained execution truth
- no claim that replay determinism or replay coverage resolves the replay-final-hash split
- no claim that root sequence retention proves inbox-local continuity
- no claim that runtime-like sim paths prove local evidence-body retention
