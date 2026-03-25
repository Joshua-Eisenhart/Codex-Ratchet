# CONTROLLER_REENTRY_SHORTLIST__v1
Status: PROPOSED / NONCANONICAL / CONTROLLER REENTRY SHORTLIST
Date: 2026-03-09
Role: small controller-side routing packet after broad-parent reduction backlog exhaustion

## 1) Live Gate
- latest live shell-only recheck at this pass:
  - zero current zero-file `BATCH*` shells
- latest live queue read at this pass:
  - no unreduced non-`A2MID` `A2_2_CANDIDATE` broad-parent packet remains
- controller consequence:
  - next work must come from revisit-side routing rather than another broad-parent reduction

## 2) Stale Selection Correction
- stable anchor signal that still holds:
  - `BATCH_refinedfuel_nonsims_residual_inventory_closure_audit__v1`
  - still nominates `Constraints. Entropy` as the strongest refined-fuel revisit anchor after coverage closure
- older bounded-selection signal that is now stale:
  - `BATCH_A2MID_reentry_gap_selection_audit__v1`
  - had selected `BATCH_a2feed_thread_b_bootpack_engine_pattern__v1` as the next unresolved compact parent
- live repo correction:
  - `BATCH_a2feed_thread_b_bootpack_engine_pattern__v1` is now direct-child closed by:
    - `BATCH_A2MID_a2feed_thread_b_provenance_admission_fences__v1`
- corrected read:
  - `Constraints. Entropy` remains the highest-value revisit anchor and comparison lane
  - no live clean compact non-archive revisit parent remains for immediate fresh controller reduction
  - the remaining open revisit set now splits into:
    - duplicate-family quarantine
    - archive-side revisit packets

## 3) Priority A: Revisit Anchor Pair
- primary anchor:
  - `BATCH_refinedfuel_constraints_entropy_term_conflict__v1`
  - direct child already present:
    - `BATCH_A2MID_constraints_entropy_chain_fences__v1`
- paired companion:
  - `BATCH_refinedfuel_constraints_term_conflict__v1`
  - direct child already present:
    - `BATCH_A2MID_constraints_foundation_governance_fences__v1`
- why this pair stays first in revisit routing:
  - it is the highest-density refined-fuel contradiction cluster still marked `REVISIT_REQUIRED`
  - the residual-inventory closure audit explicitly nominates `Constraints. Entropy`
  - the existing children already isolate reusable fence packets for scalar, path, recurrence, topology, bundle, governance, and inevitability drift
- controller use:
  - use this pair as anchor/context for legacy precursor translation
  - do not reopen either parent as if it still lacked a direct child reduction

## 4) Priority B: Duplicate-Family Quarantine
- quarantine-side parent:
  - `BATCH_a2feed_grok_unified_phuysics_source_map__v1`
- why it is not a clean next reduction target:
  - it points at the same `6599`-line source path and same SHA as the corrected sibling:
    - `BATCH_a2feed_grok_unified_physics_source_map__v1`
  - the corrected sibling already has a direct child:
    - `BATCH_A2MID_grok_unified_admission_conflicts__v1`
  - the typo variant is therefore duplicate-family revisit residue rather than the next bounded controller packet
- controller use:
  - keep the typo variant in quarantine-side family reconciliation
  - do not reduce it separately as if it were a fresh unresolved doctrine parent
  - use `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/CONTROLLER_DUPLICATE_FAMILY_QUARANTINE__v1.md` as the small duplicate-family routing surface

## 5) Priority C: Archive-Side Revisit Cluster
- archive-side unresolved cluster:
  - `BATCH_archive_surface_deep_archive_run_signal_0003__v1`
  - `BATCH_archive_surface_deep_archive_run_signal_0004__v1`
  - `BATCH_archive_surface_deep_archive_run_signal_0005__v1`
  - `BATCH_archive_surface_deep_archive_run_signal_0005_bundle__v1`
  - `BATCH_archive_surface_deep_archive_test_a1_packet_empty__v1`
  - `BATCH_archive_surface_deep_archive_test_a1_packet_zip__v1`
  - `BATCH_archive_surface_deep_archive_test_det_a__v1`
  - `BATCH_archive_surface_deep_archive_test_det_b__v1`
  - `BATCH_archive_surface_deep_archive_test_real_a1_001__v1`
  - `BATCH_archive_surface_deep_archive_test_real_a1_002__v1`
- why this cluster stays separate from active intake-side reduction:
  - these are archive-root historical run or test packets rather than active intake doctrine parents
  - they are better treated as archive-side revisit work than as the next controller-facing live intake reduction
- best bounded starts inside the archive cluster if one archive-side packet is wanted:
  - richest self-contained bundle now already direct-child reduced:
    - `BATCH_archive_surface_deep_archive_run_signal_0005_bundle__v1`
    - child packet:
      - `BATCH_A2MID_archive_run_signal_0005_bundle_controller_fences__v1`
  - smaller relatively coherent test packet now already direct-child reduced:
    - `BATCH_archive_surface_deep_archive_test_det_a__v1`
    - child packet:
      - `BATCH_A2MID_archive_test_det_a_controller_fences__v1`
  - adjacent comparison sibling now also direct-child reduced:
    - `BATCH_archive_surface_deep_archive_test_det_b__v1`
    - child packet:
      - `BATCH_A2MID_archive_test_det_b_controller_fences__v1`
  - next adjacent real-a1-named packet now also direct-child reduced:
    - `BATCH_archive_surface_deep_archive_test_real_a1_001__v1`
    - child packet:
      - `BATCH_A2MID_archive_test_real_a1_001_controller_fences__v1`
  - next adjacent real-a1-named sibling now also direct-child reduced:
    - `BATCH_archive_surface_deep_archive_test_real_a1_002__v1`
    - child packet:
      - `BATCH_A2MID_archive_test_real_a1_002_controller_fences__v1`
  - next adjacent resume-stub packet now also direct-child reduced:
    - `BATCH_archive_surface_deep_archive_test_resume_001__v1`
    - child packet:
      - `BATCH_A2MID_archive_test_resume_001_controller_fences__v1`
  - next adjacent state-transition packet now also direct-child reduced:
    - `BATCH_archive_surface_deep_archive_test_state_transition_chain_a__v1`
    - child packet:
      - `BATCH_A2MID_archive_test_state_transition_chain_a_controller_fences__v1`
  - next adjacent state-transition sibling was already direct-child reduced:
    - `BATCH_archive_surface_deep_archive_test_state_transition_chain_b__v1`
    - child packet:
      - `BATCH_A2MID_archive_chain_b_shell_drift__v1`
  - next adjacent mutation packet was already direct-child reduced:
    - `BATCH_archive_surface_deep_archive_test_state_transition_mutation__v1`
    - child packet:
      - `BATCH_A2MID_archive_mutation_snapshot_overhang__v1`
  - next adjacent ZIPv2 packet-loop sibling was already direct-child reduced:
    - `BATCH_archive_surface_deep_archive_v2_zipv2_packet_e2e_001__v1`
    - child packet:
      - `BATCH_A2MID_archive_v2_packet_e2e_save_request_divergence__v1`
  - next adjacent request-only ZIPv2 sibling now has duplicate child coverage:
    - `BATCH_archive_surface_deep_archive_v2_zipv2_packet_req_001__v1`
    - preferred live child handle:
      - `BATCH_A2MID_archive_v2_packet_req_bootstrap_scaffold__v1`
    - overlapping later duplicate-child residue:
      - `BATCH_A2MID_archive_v2_packet_req_request_only_handoff__v1`
  - next adjacent replay-side ZIPv2 sibling is now also direct-child reduced:
    - `BATCH_archive_surface_deep_archive_v2_zipv2_replay_001__v1`
    - child packet:
      - `BATCH_A2MID_archive_v2_replay_hashbridge_schemafail__v1`
  - next adjacent compact sibling after the now-covered ZIPv2 strip:
    - `BATCH_archive_surface_heat_dumps_root_family_split__v1`
- keep deferred behind the three priorities above:
  - `BATCH_a2feed_leviathan_family_source_map__v1`
  - `BATCH_a2feed_gpt_thread_a1_trigram_source_map__v1`
  - `BATCH_upgrade_docs_megaboot_ratchet_suite_source_map__v1`
  - `BATCH_archive_surface_batch01_core_constraint_ladder_axis_foundation__v1`

## 6) Controller Rule
- if the need is:
  - reconcile legacy refined-fuel precursor language against later fail-closed contracts
  - start with the `Constraints. Entropy` pair as anchor/context
- if the need is:
  - clean live intake duplication before new reduction
  - quarantine `BATCH_a2feed_grok_unified_phuysics_source_map__v1` against the corrected sibling and existing child packet
- if the need is:
  - produce one more bounded historical packet from the remaining unresolved set
  - continue inside the archive-side cluster with `BATCH_archive_surface_heat_dumps_root_family_split__v1`
- in all cases:
  - keep ledger state above stale queue text
  - keep existing child coverage visible
  - do not treat this shortlist as active A2 mutation authority
