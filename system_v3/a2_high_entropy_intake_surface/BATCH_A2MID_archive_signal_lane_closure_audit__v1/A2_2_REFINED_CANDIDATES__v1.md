# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_archive_signal_lane_closure_audit__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Candidate RC1) `RUN_SIGNAL_LANE_0002_TO_0005_PLUS_BUNDLE_IS_DIRECT_CHILD_CLOSED`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the deep-archive `RUN_SIGNAL` lane is now direct-child closed across:
  - raw `0002`
  - raw `0003`
  - raw `0004`
  - raw `0005`
  - `0005_bundle`

Why this survives reduction:
- it preserves the main closure fact now needed for routing
- it blocks default reopening of already-childed signal parents

Source lineage:
- child manifests:
  - `BATCH_A2MID_archive_signal_0002_failclosed_promotion_hashdrift_fences__v1`
  - `BATCH_A2MID_archive_signal_0003_negative_residue_hashdrift_fences__v1`
  - `BATCH_A2MID_archive_signal_0004_summary_replay_audit_fences__v1`
  - `BATCH_A2MID_archive_signal_0005_runtime_alignment_auditnull_fences__v1`
  - `BATCH_A2MID_archive_run_signal_0005_bundle_controller_fences__v1`
- ledger anchor:
  - `BATCH_INDEX__v1.md`

Preserved limits:
- this batch does not claim the whole deep-archive run corpus is closed
- it preserves only the `RUN_SIGNAL` lane closure fact

## Candidate RC2) `SIGNAL_REENTRY_IS_NO_LONGER_THE_STRONGEST_DEEP_ARCHIVE_GAP`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- after that closure, another signal-family reduction is no longer the strongest unresolved next step

Why this survives reduction:
- it prevents stale lane momentum from overruling the live ledger
- it keeps the next move bounded to a genuinely unresolved family

Source lineage:
- parent consequences:
  - `BATCH_A2MID_archive_signal_0005_runtime_alignment_auditnull_fences__v1`
  - `BATCH_A2MID_archive_run_signal_0005_bundle_controller_fences__v1`
- ledger anchor:
  - `BATCH_INDEX__v1.md`

Preserved limits:
- this batch does not deny future signal-lane revisit value
- it preserves only the rule that signal is not the strongest next gap now

## Candidate RC3) `NEXT_UNRESOLVED_POOL_NOW_SITS_IN_COMPACT_TEST_FAMILIES`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest remaining deep-archive run/test pool now sits in compact test families rather than the closed signal lane

Why this survives reduction:
- it narrows the residual set after signal closure
- it prevents aimless descent into already-covered run families

Source lineage:
- comparison anchors:
  - `BATCH_archive_surface_deep_archive_test_a1_packet_empty__v1`
  - `BATCH_archive_surface_deep_archive_test_a1_packet_zip__v1`
  - `BATCH_archive_surface_deep_archive_test_real_a1_001__v1`
  - `BATCH_archive_surface_deep_archive_test_real_a1_002__v1`
  - `BATCH_archive_surface_deep_archive_test_resume_001__v1`
- ledger anchor:
  - `BATCH_INDEX__v1.md`

Preserved limits:
- this batch does not rank every remaining test family equally
- it preserves only the narrowed residual pool

## Candidate RC4) `TEST_A1_PACKET_ZIP_IS_THE_STRONGEST_NEXT_UNRESOLVED_TARGET`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest next bounded deep-archive target is `TEST_A1_PACKET_ZIP` because:
  - it remains unchilded
  - it already has a close sibling child in `TEST_A1_PACKET_EMPTY`
  - it preserves a compact one-step packet-loop contradiction packet
  - it localizes same-name packet identity drift, zeroed sequence residue, and summary collapse in one bounded surface

Why this survives reduction:
- it gives the lane a real next target after signal closure
- it uses sibling support instead of reopening a broad corpus blindly

Source lineage:
- target parent:
  - `BATCH_archive_surface_deep_archive_test_a1_packet_zip__v1`
- comparison anchors:
  - `BATCH_A2MID_archive_test_packet_empty_handoff_fences__v1`
  - `BATCH_A2MID_archive_signal_0005_runtime_alignment_auditnull_fences__v1`
  - `BATCH_A2MID_archive_run_signal_0005_bundle_controller_fences__v1`

Preserved limits:
- this batch does not claim `TEST_A1_PACKET_ZIP` is globally the most important remaining archive target
- it preserves only the rule that `TEST_A1_PACKET_ZIP` is the strongest next bounded target now

## Candidate RC5) `PACKET_ZIP_OUTRANKS_REAL_A1_002_AND_BROADER_STATE_TRANSITION_REENTRY`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- `TEST_A1_PACKET_ZIP` outranks:
  - `TEST_REAL_A1_002`
  - `TEST_RESUME_001`
  - the broader state-transition family
- because it combines:
  - an existing sibling child
  - a compact one-step contradiction packet
  - location-dependent same-name packet divergence
  - summary collapse against deeper retained residue

Why this survives reduction:
- it records why the next target is not chosen only by novelty or raw scope
- it keeps the next step attached to contradiction density and sibling leverage

Source lineage:
- comparison anchors:
  - `BATCH_archive_surface_deep_archive_test_a1_packet_zip__v1`
  - `BATCH_archive_surface_deep_archive_test_real_a1_002__v1`
  - `BATCH_archive_surface_deep_archive_test_resume_001__v1`
  - `BATCH_archive_surface_deep_archive_test_state_transition_chain_a__v1`
  - `BATCH_archive_surface_deep_archive_test_state_transition_chain_b__v1`
  - `BATCH_archive_surface_deep_archive_test_state_transition_mutation__v1`

Preserved limits:
- this batch does not erase future value in the deferred families
- it preserves only the priority rule for the current step

## Candidate RC6) `LEDGER_STATE_OVERRIDES_STALE_FOLDER_ORDER_OR_NEXT_NUMBER_MOMENTUM`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- target selection must follow:
  - current ledger state
  - current child coverage
  - current unresolved family density
- not stale queue text, lexical name order, or next-number run momentum

Why this survives reduction:
- it is the main process rule required to keep the lane bounded
- it blocks automatic continuation from closed signal numbering into unrelated families

Source lineage:
- ledger anchor:
  - `BATCH_INDEX__v1.md`

Preserved limits:
- this batch does not rewrite selection globally
- it preserves only the routing rule for the current closure state

## Quarantined Residue Q1) `REOPEN_SIGNAL_0002_TO_0005_BY_DEFAULT`
Status:
- `QUARANTINED`

Preserved residue:
- acting as if another signal-family re-entry is still the strongest next move

Why it stays quarantined:
- that lane is now direct-child closed through raw `0005` plus `0005_bundle`

Source lineage:
- signal child manifests
- `BATCH_INDEX__v1.md`

## Quarantined Residue Q2) `TREAT_RAW_0005_OR_0005_BUNDLE_AS_GLOBAL_DEEP_ARCHIVE_CLOSURE`
Status:
- `QUARANTINED`

Preserved residue:
- treating the richest signal-side repaired surfaces as if they close the whole deep-archive run/test pool

Why it stays quarantined:
- unresolved compact test families still remain

Source lineage:
- `BATCH_A2MID_archive_signal_0005_runtime_alignment_auditnull_fences__v1`
- `BATCH_A2MID_archive_run_signal_0005_bundle_controller_fences__v1`

## Quarantined Residue Q3) `PICK_NEXT_TARGET_BY_LEXICAL_OR_NUMERIC_MOMENTUM`
Status:
- `QUARANTINED`

Preserved residue:
- continuing only because another run number appears next in lexical or numeric order

Why it stays quarantined:
- the signal lane is closed and the live ledger points elsewhere

Source lineage:
- `BATCH_INDEX__v1.md`

## Quarantined Residue Q4) `TREAT_PACKET_EMPTY_CHILD_AS_IF_IT_ALREADY_CLOSED_PACKET_ZIP`
Status:
- `QUARANTINED`

Preserved residue:
- treating the existing packet-empty child as if it already resolved the packet-zip sibling

Why it stays quarantined:
- sibling closeness does not erase an unchilded packet-zip contradiction packet

Source lineage:
- `BATCH_archive_surface_deep_archive_test_a1_packet_empty__v1`
- `BATCH_A2MID_archive_test_packet_empty_handoff_fences__v1`
- `BATCH_archive_surface_deep_archive_test_a1_packet_zip__v1`

## Quarantined Residue Q5) `CLOSURE_AUDIT_AS_ACTIVE_A2_CONTROL_MEMORY`
Status:
- `QUARANTINED`

Preserved residue:
- treating this routing audit as active A2 control law

Why it stays quarantined:
- it is only a bounded A2-mid selection surface

Source lineage:
- `A2_MID_REFINEMENT_PROCESS__v1.md`
- `BATCH_INDEX__v1.md`
