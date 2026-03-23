# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_A2MID_archive_signal_0005_runtime_alignment_auditnull_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Why this parent was selected
- the previous child explicitly handed off into `RUN_SIGNAL_0005`
- the parent is the next live archive descendant and preserves the same signal-plus-audit structure as `RUN_SIGNAL_0004` with one high-yield change:
  - runtime-facing counts are now internally aligned
- the parent also keeps two unresolved seams that are still reduction-worthy:
  - replay determinism with divergent replay final hash
  - `SIGNAL_AUDIT.json` nullability drift beside nonzero math-kill metadata

## Why reduction is useful
- it preserves the run as a repaired hybrid signal-plus-audit archive object instead of letting runtime-count alignment masquerade as promotion closure
- it preserves the aligned sixty-pass lattice separately from the still-fail-closed semantic burden
- it preserves stronger snapshot binding separately from the event endpoint and replay-final hash
- it preserves root-only sequence retention
- it preserves renamed consumed-lane drift and the signal-audit null seam without letting either collapse into clean identity or clean audit closure

## Why the comparison anchors were sufficient
- `BATCH_A2MID_archive_signal_0004_summary_replay_audit_fences__v1` preserves the nearest sibling before the runtime-alignment repair and shows what changed
- `BATCH_A2MID_archive_signal_0003_negative_residue_hashdrift_fences__v1` preserves the same fail-closed promotion and stronger-snapshot-than-event closure spine below the audit-heavy repair
- `BATCH_A2MID_archive_run_signal_0005_bundle_controller_fences__v1` preserves the richer bundle-side sibling so this raw-parent child can stay below bundle richness rather than re-deriving it

## What stays out of scope
- no mutation of active A2 state surfaces
- no reopening of sibling runs beyond later explicit selection
- no claim that aligned runtime-facing counts imply semantic closure
- no claim that replay determinism resolves replay-final-hash divergence
- no claim that `SIGNAL_AUDIT.json` null fields can be silently backfilled from nearby counts
- no claim that the raw parent inherits the bundle sibling's retained local evidence bodies
