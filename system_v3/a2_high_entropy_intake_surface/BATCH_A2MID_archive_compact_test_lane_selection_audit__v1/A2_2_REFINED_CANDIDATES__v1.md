# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_archive_compact_test_lane_selection_audit__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Candidate RC1) `EARLIER_COMPACT_TEST_FAMILIES_THROUGH_V2_PACKET_REQ_ARE_DIRECT_CHILD_CLOSED`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the earlier compact deep-archive test families are now direct-child closed:
  - packet microfamily
  - deterministic pair
  - `REAL_A1` pair
  - resume stub
  - state-transition family
  - `V2_ZIPV2_PACKET_E2E_001`
  - `V2_ZIPV2_PACKET_REQ_001`

Why this survives reduction:
- it preserves the closure facts needed to stop stale duplicate routing
- it blocks reopening already-childed families by default

Source lineage:
- child manifests:
  - `BATCH_A2MID_archive_test_packet_empty_handoff_fences__v1`
  - `BATCH_A2MID_archive_test_packet_zip_identity_residue__v1`
  - `BATCH_A2MID_archive_test_det_a_controller_fences__v1`
  - `BATCH_A2MID_archive_test_det_b_controller_fences__v1`
  - `BATCH_A2MID_archive_test_real_a1_001_controller_fences__v1`
  - `BATCH_A2MID_archive_test_real_a1_002_controller_fences__v1`
  - `BATCH_A2MID_archive_test_resume_stub_leakage__v1`
  - `BATCH_A2MID_archive_test_state_transition_chain_a_controller_fences__v1`
  - `BATCH_A2MID_archive_chain_b_shell_drift__v1`
  - `BATCH_A2MID_archive_mutation_snapshot_overhang__v1`
  - `BATCH_A2MID_archive_v2_packet_e2e_save_request_divergence__v1`
  - `BATCH_A2MID_archive_v2_packet_req_bootstrap_scaffold__v1`
- ledger anchor:
  - `BATCH_INDEX__v1.md`

Preserved limits:
- this batch does not claim the whole deep-archive run surface is closed
- it preserves only the local compact-test family closure facts

## Candidate RC2) `NEXT_UNRESOLVED_COMPACT_TEST_POOL_NOW_IS_ONLY_V2_ZIPV2_REPLAY_001`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- after closure of the earlier compact test families, the remaining compact test pool in this local lane is now only:
  - `V2_ZIPV2_REPLAY_001`

Why this survives reduction:
- it narrows the residual test set to the sole remaining parent in the compact lane slice
- it prevents further routing drift into already-covered families

Source lineage:
- comparison anchor:
  - `BATCH_archive_surface_deep_archive_v2_zipv2_replay_001__v1`
- ledger anchor:
  - `BATCH_INDEX__v1.md`

Preserved limits:
- this batch does not claim `REPLAY_001` is the only unresolved deep-archive parent globally
- it preserves only the narrowed residual pool for the compact test lane

## Candidate RC3) `V2_ZIPV2_REPLAY_001_IS_THE_STRONGEST_NEXT_UNRESOLVED_TARGET`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the strongest next bounded compact-test target is `V2_ZIPV2_REPLAY_001` because:
  - it remains unchilded
  - it is now the sole remaining unresolved parent in this lane
  - it preserves the strongest remaining contradiction packet here:
    - summary and soak count `3` while events retain only `2`
    - queued third strategy packet is the only trace of step `3`
    - hidden hash bridges across executed and final layers
    - replay authorship coexisting with real-LLM demand
    - step-2 `SCHEMA_FAIL` with partial `S0002` landing
    - packet-facing evidence and kill residue richer than final bookkeeping

Why this survives reduction:
- it gives the lane a real next target after closure of the earlier compact test families
- it preserves the strongest remaining unresolved contradiction packet in this bounded slice

Source lineage:
- target parent:
  - `BATCH_archive_surface_deep_archive_v2_zipv2_replay_001__v1`
- comparison anchors:
  - `BATCH_A2MID_archive_v2_packet_e2e_save_request_divergence__v1`
  - `BATCH_A2MID_archive_v2_packet_req_bootstrap_scaffold__v1`

Preserved limits:
- this batch does not claim `REPLAY_001` is the most important remaining deep-archive target in all respects
- it preserves only the rule that `REPLAY_001` is the strongest next bounded compact-test target now

## Candidate RC4) `REPLAY_001_NOW_OUTRANKS_PACKET_REQ_AND_PACKET_E2E_ONLY_BECAUSE_THEY_ARE_ALREADY_CHILDED`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- `REPLAY_001` now outranks `PACKET_REQ_001` and `PACKET_E2E_001` only because:
  - both earlier `v2_zipv2` siblings already have direct children
  - no unresolved sibling remains to outrank it inside this lane

Why this survives reduction:
- it preserves the live-ledger reason for `REPLAY_001` selection
- it blocks stale rerouting back onto already-childed `v2_zipv2` siblings

Source lineage:
- child manifests:
  - `BATCH_A2MID_archive_v2_packet_e2e_save_request_divergence__v1`
  - `BATCH_A2MID_archive_v2_packet_req_bootstrap_scaffold__v1`
- ledger anchor:
  - `BATCH_INDEX__v1.md`

Preserved limits:
- this batch does not retroactively demote the earlier sibling reductions
- it preserves only the reason `REPLAY_001` is now the next move

## Candidate RC5) `SOLE_REMAINING_PARENT_STATUS_SHRINKS_ROUTING_AMBIGUITY`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- once the lane is reduced to one unresolved raw parent, routing ambiguity shrinks sharply:
  - selection is no longer between siblings
  - selection is between following the live ledger or drifting back into stale momentum

Why this survives reduction:
- it preserves the bounded routing condition now governing the lane
- it records why the next step is less interpretive than the earlier corrections

Source lineage:
- target parent:
  - `BATCH_archive_surface_deep_archive_v2_zipv2_replay_001__v1`
- ledger anchor:
  - `BATCH_INDEX__v1.md`

Preserved limits:
- this batch does not claim routing ambiguity is globally gone
- it preserves only the local selection condition in this slice

## Candidate RC6) `LEDGER_STATE_OVERRIDES_STALE_PACKET_ZIP_REAL_A1_STATE_TRANSITION_AND_PACKET_E2E_QUEUE_TEXT`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- target selection must follow:
  - current ledger state
  - current child coverage
  - current residual-family boundaries
- not stale queue text first pointing at already-childed packet, `REAL_A1`, state-transition, or `PACKET_E2E` parents

Why this survives reduction:
- it is the main process rule required to keep the lane bounded
- it blocks duplicate packet, `REAL_A1`, state-transition, or earlier `v2_zipv2` reduction

Source lineage:
- parent audit:
  - `BATCH_A2MID_archive_signal_lane_closure_audit__v1`
- ledger anchor:
  - `BATCH_INDEX__v1.md`

Preserved limits:
- this batch does not rewrite routing globally
- it preserves only the routing rule for the current compact-test closure state

## Quarantined Residue Q1) `DUPLICATE_EARLIER_COMPACT_TEST_REDUCTION`
Status:
- `QUARANTINED`

Preserved residue:
- acting as if earlier compact-test parents still need a first A2-mid child

Why it stays quarantined:
- those earlier compact-test parents already have direct children

Source lineage:
- child manifests listed in `RC1`
- `BATCH_INDEX__v1.md`

## Quarantined Residue Q2) `TREAT_EARLIER_MICROFAMILY_CLOSURE_AS_TOTAL_DEEP_ARCHIVE_TEST_CLOSURE`
Status:
- `QUARANTINED`

Preserved residue:
- treating closure of the earlier compact test families as if no compact archive test family remained unresolved

Why it stays quarantined:
- `REPLAY_001` still remains unchilded in this lane

Source lineage:
- child manifests listed in `RC1`
- `BATCH_INDEX__v1.md`

## Quarantined Residue Q3) `REOPEN_ALREADY_CHILDED_STATE_TRANSITION_OR_V2_PACKET_BOOTSTRAP_PARENTS`
Status:
- `QUARANTINED`

Preserved residue:
- reopening state-transition, `PACKET_E2E_001`, or `PACKET_REQ_001` parents as if they were still unresolved

Why it stays quarantined:
- those parents already have direct children in the live ledger

Source lineage:
- `BATCH_A2MID_archive_test_state_transition_chain_a_controller_fences__v1`
- `BATCH_A2MID_archive_chain_b_shell_drift__v1`
- `BATCH_A2MID_archive_mutation_snapshot_overhang__v1`
- `BATCH_A2MID_archive_v2_packet_e2e_save_request_divergence__v1`
- `BATCH_A2MID_archive_v2_packet_req_bootstrap_scaffold__v1`
- `BATCH_INDEX__v1.md`

## Quarantined Residue Q4) `TREAT_REPLAY_001_AS_OPTIONAL_WHEN_IT_IS_THE_ONLY_REMAINING_PARENT`
Status:
- `QUARANTINED`

Preserved residue:
- acting as if `REPLAY_001` were just one optional sibling choice inside this lane

Why it stays quarantined:
- it is the sole remaining unresolved compact-test parent in the current slice

Source lineage:
- `BATCH_archive_surface_deep_archive_v2_zipv2_replay_001__v1`
- `BATCH_INDEX__v1.md`

## Quarantined Residue Q5) `TREAT_THIS_ROUTING_AUDIT_AS_ACTIVE_A2_CONTROL_MEMORY`
Status:
- `QUARANTINED`

Preserved residue:
- treating this compact-test routing audit as active A2 control law

Why it stays quarantined:
- it is only a bounded A2-mid selection surface

Source lineage:
- `A2_MID_REFINEMENT_PROCESS__v1.md`
- `BATCH_INDEX__v1.md`
