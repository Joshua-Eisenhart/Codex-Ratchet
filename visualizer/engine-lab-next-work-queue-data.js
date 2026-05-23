window.ENGINE_LAB_NEXT_WORK_QUEUE_DATA = {
  "name": "engine_lab_next_work_queue",
  "summary": {
    "queue_complete": true,
    "open_row_count": 10,
    "active_uncovered_row_count": 0,
    "repair_gap_count": 3,
    "open_lab_failure_count": 5,
    "graveyard_covered_open_row_count": 7,
    "top_row_id": "carnot_entropy_family_array",
    "top_active_row_id": null,
    "qit_or_axis_promotion_allowed": false,
    "scope_note": "Controller queue derived from engine-lab open-row audit and repair-priority receipts. It does not claim row closure; it names bounded next sim moves."
  },
  "rows": [
    {
      "row_id": "carnot_entropy_family_array",
      "audit_class": "readout_split",
      "engine_family": "carnot",
      "level": "entropy_family_array",
      "next_allowed_action": "use_as_negative_readout_evidence_or_rewrite_hypothesis",
      "recommended_lane": "successor_receipt_available_keep_source_as_negative_readout_split",
      "graveyard_covered": true,
      "graveyard_variant_count": 3,
      "graveyard_killed_count": 1,
      "graveyard_survived_count": 2,
      "graveyard_receipts": [
        "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/engine_lab_sidecar_graveyard_results.json"
      ],
      "promotion_blocker": "readout families do not currently agree on the claimed ordering",
      "failed_check_count": 2,
      "failed_checks": [
        {
          "section": "negative",
          "check": "best_engine_performance_row_is_not_the_best_closure_row"
        },
        {
          "section": "negative",
          "check": "best_refrigerator_performance_row_is_not_the_best_closure_row"
        }
      ],
      "passing_successor_count": 1,
      "consolidated_admission_status": "not_run",
      "translation_closeness_score": null,
      "priority_bucket": null,
      "qit_or_axis_promotion_allowed": false
    },
    {
      "row_id": "carnot_forward_asymmetric",
      "audit_class": "open_lab_failure",
      "engine_family": "carnot",
      "level": "topology_budget_array",
      "next_allowed_action": "repair_open_row_or_convert_to_negative_graveyard_variant",
      "recommended_lane": "successor_receipt_available_keep_source_as_negative_open_failure",
      "graveyard_covered": true,
      "graveyard_variant_count": 4,
      "graveyard_killed_count": 2,
      "graveyard_survived_count": 2,
      "graveyard_receipts": [
        "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/carnot_asymmetric_direction_graveyard_results.json"
      ],
      "promotion_blocker": "open stochastic row does not satisfy its own pass conditions",
      "failed_check_count": 2,
      "failed_checks": [
        {
          "section": "positive",
          "check": "hot_heavy_budget_beats_cold_heavy_budget_on_average_for_closure"
        },
        {
          "section": "negative",
          "check": "cold_leg_budget_alone_is_not_sufficient_to_close_the_cycle"
        }
      ],
      "passing_successor_count": 1,
      "consolidated_admission_status": "not_run",
      "translation_closeness_score": null,
      "priority_bucket": null,
      "qit_or_axis_promotion_allowed": false
    },
    {
      "row_id": "carnot_reverse_asymmetric",
      "audit_class": "open_lab_failure",
      "engine_family": "carnot",
      "level": "topology_budget_array",
      "next_allowed_action": "repair_open_row_or_convert_to_negative_graveyard_variant",
      "recommended_lane": "successor_receipt_available_keep_source_as_negative_open_failure",
      "graveyard_covered": true,
      "graveyard_variant_count": 6,
      "graveyard_killed_count": 5,
      "graveyard_survived_count": 1,
      "graveyard_receipts": [
        "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/carnot_asymmetric_direction_graveyard_results.json"
      ],
      "promotion_blocker": "open stochastic row does not satisfy its own pass conditions",
      "failed_check_count": 5,
      "failed_checks": [
        {
          "section": "positive",
          "check": "some_asymmetric_setting_improves_reverse_closure_over_balanced_baseline"
        },
        {
          "section": "positive",
          "check": "some_high_budget_setting_moves_close_to_carnot_cop"
        },
        {
          "section": "positive",
          "check": "cold_heavy_budget_beats_hot_heavy_budget_on_average_for_reverse_closure"
        },
        {
          "section": "negative",
          "check": "even_the_best_reverse_row_still_has_nonzero_cycle_return_error"
        },
        {
          "section": "negative",
          "check": "hot_leg_budget_alone_is_not_sufficient_to_optimize_reverse_closure"
        }
      ],
      "passing_successor_count": 1,
      "consolidated_admission_status": "not_run",
      "translation_closeness_score": null,
      "priority_bucket": null,
      "qit_or_axis_promotion_allowed": false
    },
    {
      "row_id": "qit_szilard_record_translation_lane",
      "audit_class": "repair_gap",
      "engine_family": "szilard",
      "level": "qit_translation_lane",
      "next_allowed_action": "use_passing_successor_as_repair_evidence_keep_original_as_negative",
      "recommended_lane": "closed_by_consolidated_successor_keep_source_negative",
      "graveyard_covered": false,
      "graveyard_variant_count": 0,
      "graveyard_killed_count": 0,
      "graveyard_survived_count": 0,
      "graveyard_receipts": [],
      "promotion_blocker": "strict translation gaps remain above row-local bounds",
      "failed_check_count": 1,
      "failed_checks": [
        {
          "section": "boundary",
          "check": "translation_gaps_are_bounded_for_clean_admission"
        }
      ],
      "passing_successor_count": 6,
      "consolidated_admission_status": "closed",
      "translation_closeness_score": null,
      "priority_bucket": null,
      "qit_or_axis_promotion_allowed": false
    },
    {
      "row_id": "qit_szilard_substep_refinement_translation_lane",
      "audit_class": "repair_gap",
      "engine_family": "szilard",
      "level": "qit_translation_lane",
      "next_allowed_action": "use_passing_successor_as_repair_evidence_keep_original_as_negative",
      "recommended_lane": "closed_by_consolidated_successor_keep_source_negative",
      "graveyard_covered": false,
      "graveyard_variant_count": 0,
      "graveyard_killed_count": 0,
      "graveyard_survived_count": 0,
      "graveyard_receipts": [],
      "promotion_blocker": "strict translation gaps remain above row-local bounds",
      "failed_check_count": 3,
      "failed_checks": [
        {
          "section": "positive",
          "check": "ordering_gap_is_below_0_45"
        },
        {
          "section": "positive",
          "check": "measurement_information_gap_stays_below_0_08"
        },
        {
          "section": "positive",
          "check": "reset_signal_gap_is_below_0_35"
        }
      ],
      "passing_successor_count": 3,
      "consolidated_admission_status": "closed",
      "translation_closeness_score": null,
      "priority_bucket": null,
      "qit_or_axis_promotion_allowed": false
    },
    {
      "row_id": "szilard_ordering_sensitivity",
      "audit_class": "open_lab_failure",
      "engine_family": "szilard",
      "level": "parameter_array",
      "next_allowed_action": "repair_open_row_or_convert_to_negative_graveyard_variant",
      "recommended_lane": "successor_receipt_available_keep_source_as_negative_open_failure",
      "graveyard_covered": true,
      "graveyard_variant_count": 3,
      "graveyard_killed_count": 2,
      "graveyard_survived_count": 1,
      "graveyard_receipts": [
        "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/szilard_open_failure_graveyard_results.json"
      ],
      "promotion_blocker": "open stochastic row does not satisfy its own pass conditions",
      "failed_check_count": 2,
      "failed_checks": [
        {
          "section": "positive",
          "check": "lower_measurement_noise_improves_ordering_margin_on_average"
        },
        {
          "section": "negative",
          "check": "high_noise_settings_do_not_give_clean_ordering_separation"
        }
      ],
      "passing_successor_count": 1,
      "consolidated_admission_status": "not_run",
      "translation_closeness_score": null,
      "priority_bucket": null,
      "qit_or_axis_promotion_allowed": false
    },
    {
      "row_id": "szilard_record_reset_repair_sweep",
      "audit_class": "open_lab_failure",
      "engine_family": "szilard",
      "level": "record_reset_array",
      "next_allowed_action": "repair_open_row_or_convert_to_negative_graveyard_variant",
      "recommended_lane": "successor_receipt_available_keep_source_as_negative_open_failure",
      "graveyard_covered": true,
      "graveyard_variant_count": 3,
      "graveyard_killed_count": 1,
      "graveyard_survived_count": 2,
      "graveyard_receipts": [
        "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/szilard_open_failure_graveyard_results.json"
      ],
      "promotion_blocker": "open stochastic row does not satisfy its own pass conditions",
      "failed_check_count": 1,
      "failed_checks": [
        {
          "section": "positive",
          "check": "stronger_reset_grid_increases_open_reset_swing"
        }
      ],
      "passing_successor_count": 1,
      "consolidated_admission_status": "not_run",
      "translation_closeness_score": null,
      "priority_bucket": null,
      "qit_or_axis_promotion_allowed": false
    },
    {
      "row_id": "szilard_substep_refinement_sweep",
      "audit_class": "open_lab_failure",
      "engine_family": "szilard",
      "level": "stochastic_submechanics",
      "next_allowed_action": "repair_open_row_or_convert_to_negative_graveyard_variant",
      "recommended_lane": "successor_receipt_available_keep_source_as_negative_open_failure",
      "graveyard_covered": true,
      "graveyard_variant_count": 3,
      "graveyard_killed_count": 1,
      "graveyard_survived_count": 2,
      "graveyard_receipts": [
        "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/szilard_open_failure_graveyard_results.json"
      ],
      "promotion_blocker": "open stochastic row does not satisfy its own pass conditions",
      "failed_check_count": 1,
      "failed_checks": [
        {
          "section": "positive",
          "check": "measurement_information_stays_high"
        }
      ],
      "passing_successor_count": 1,
      "consolidated_admission_status": "not_run",
      "translation_closeness_score": null,
      "priority_bucket": null,
      "qit_or_axis_promotion_allowed": false
    },
    {
      "row_id": "szilard_topology_entropy_array",
      "audit_class": "topology_sidecar_or_graveyard",
      "engine_family": "szilard",
      "level": "topology_entropy_array",
      "next_allowed_action": "keep_as_topology_variant_until_reexpressed_on_strict_carrier",
      "recommended_lane": "successor_receipt_available_keep_source_as_negative_topology_sidecar",
      "graveyard_covered": true,
      "graveyard_variant_count": 3,
      "graveyard_killed_count": 1,
      "graveyard_survived_count": 2,
      "graveyard_receipts": [
        "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/engine_lab_sidecar_graveyard_results.json"
      ],
      "promotion_blocker": "topology geometry is informative but not yet strict QIT carrier evidence",
      "failed_check_count": 1,
      "failed_checks": [
        {
          "section": "negative",
          "check": "at_least_one_topology_remains_weak_for_ordering"
        }
      ],
      "passing_successor_count": 1,
      "consolidated_admission_status": "not_run",
      "translation_closeness_score": null,
      "priority_bucket": null,
      "qit_or_axis_promotion_allowed": false
    },
    {
      "row_id": "szilard_record_ordering_refinement_reset_swing_sweep",
      "audit_class": "repair_gap",
      "engine_family": "szilard",
      "level": "record_reset_array",
      "next_allowed_action": "tighten_exact_translation_metrics_before_admission",
      "recommended_lane": "superseded_by_reset_parameter_recheck_keep_as_negative",
      "graveyard_covered": false,
      "graveyard_variant_count": 0,
      "graveyard_killed_count": 0,
      "graveyard_survived_count": 0,
      "graveyard_receipts": [],
      "promotion_blocker": "strict translation gaps remain above row-local bounds",
      "failed_check_count": 2,
      "failed_checks": [
        {
          "section": "positive",
          "check": "reset_swing_gap_under_original_bound"
        },
        {
          "section": "positive",
          "check": "residual_reset_entropy_gap_under_original_bound"
        }
      ],
      "passing_successor_count": 0,
      "consolidated_admission_status": "not_run",
      "translation_closeness_score": null,
      "priority_bucket": null,
      "qit_or_axis_promotion_allowed": false
    }
  ]
};
