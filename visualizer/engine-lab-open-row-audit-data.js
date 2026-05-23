window.ENGINE_LAB_OPEN_ROW_AUDIT_DATA = {
  "name": "engine_lab_open_row_audit",
  "summary": {
    "audit_complete": true,
    "matrix_all_pass": false,
    "coverage_status": "complete",
    "matrix_status": "complete_with_open_rows",
    "available_rows": 81,
    "missing_rows": 0,
    "nonpassing_row_count": 11,
    "audited_nonpassing_rows": 11,
    "missing_audit_rows": 0,
    "unclassified_open_rows": 0,
    "audit_class_counts": {
      "open_lab_failure": 5,
      "readout_split": 1,
      "repair_gap": 4,
      "topology_sidecar_or_graveyard": 1
    },
    "repair_gap_rows": 4,
    "repair_gap_rows_with_passing_successor": 2,
    "repair_gap_rows_with_consolidated_recheck": 2,
    "repair_gap_rows_closed_by_consolidated_recheck": 2,
    "repair_gap_rows_still_open_after_consolidated_recheck": 0,
    "qit_or_axis_promotion_allowed": false,
    "scope_note": "Controller audit over engine-lab rows with summary.all_pass=false. It separates coverage completion from open scientific failures, repair targets, and topology/readout sidecars."
  },
  "rows": [
    {
      "row_id": "carnot_entropy_family_array",
      "engine_family": "carnot",
      "audit_class": "readout_split",
      "next_allowed_action": "use_as_negative_readout_evidence_or_rewrite_hypothesis",
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
      "target_qit_row_id": null,
      "passing_successor_count": 1,
      "successor_rows": [
        {
          "row_id": "carnot_entropy_family_open_split",
          "exists": true,
          "classification": "audit",
          "all_pass": true,
          "scope_note": "Open-carrier successor for the Carnot entropy-family readout split. The source row compared exact QIT anchors and open stochastic/topology rows; this recheck asks only whether open carriers disagree across performance, closure, return, and bath-entropy readouts. It does not claim QIT, GStack, axis, or engine admission."
        }
      ],
      "consolidated_admission_status": "not_run",
      "consolidated_admission_receipt": null
    },
    {
      "row_id": "carnot_forward_asymmetric",
      "engine_family": "carnot",
      "audit_class": "open_lab_failure",
      "next_allowed_action": "repair_open_row_or_convert_to_negative_graveyard_variant",
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
      "target_qit_row_id": null,
      "passing_successor_count": 1,
      "successor_rows": [
        {
          "row_id": "carnot_forward_cold_leg_dominance_successor",
          "exists": true,
          "classification": "exploratory",
          "all_pass": true,
          "scope_note": "Bounded successor for the forward Carnot asymmetric isotherm row. The source row falsified the hot-heavy closure prior; this receipt records the surviving cold-leg closure dominance as a corrected local variant without QIT, GStack, axis, or runtime promotion."
        }
      ],
      "consolidated_admission_status": "not_run",
      "consolidated_admission_receipt": null
    },
    {
      "row_id": "carnot_reverse_asymmetric",
      "engine_family": "carnot",
      "audit_class": "open_lab_failure",
      "next_allowed_action": "repair_open_row_or_convert_to_negative_graveyard_variant",
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
      "target_qit_row_id": null,
      "passing_successor_count": 1,
      "successor_rows": [
        {
          "row_id": "carnot_reverse_balanced_return_successor",
          "exists": true,
          "classification": "exploratory",
          "all_pass": true,
          "scope_note": "Bounded successor for the reverse Carnot asymmetric row. The source row falsifies reverse asymmetric closure, near-Carnot COP, and simple leg dominance; this receipt preserves the surviving balanced near-zero return closure signal without QIT, GStack, axis, or runtime promotion."
        }
      ],
      "consolidated_admission_status": "not_run",
      "consolidated_admission_receipt": null
    },
    {
      "row_id": "qit_szilard_record_translation_lane",
      "engine_family": "szilard",
      "audit_class": "repair_gap",
      "next_allowed_action": "use_passing_successor_as_repair_evidence_keep_original_as_negative",
      "promotion_blocker": "strict translation gaps remain above row-local bounds",
      "failed_check_count": 1,
      "failed_checks": [
        {
          "section": "boundary",
          "check": "translation_gaps_are_bounded_for_clean_admission"
        }
      ],
      "target_qit_row_id": null,
      "passing_successor_count": 6,
      "successor_rows": [
        {
          "row_id": "qit_szilard_record_repair_translation_lane",
          "exists": true,
          "classification": "canonical",
          "all_pass": true,
          "scope_note": "Promoted repair translation lane for the improved open Szilard record/reset sweep. It shows that measurement and survival can be brought close to the strict row while reset swing remains weak."
        },
        {
          "row_id": "qit_szilard_record_hard_reset_translation_lane",
          "exists": true,
          "classification": "canonical",
          "all_pass": true,
          "scope_note": "Hard-reset translation lane for the open Szilard record carrier. Reset is materially stronger now; ordering remains the main gap."
        },
        {
          "row_id": "qit_szilard_record_ordering_translation_lane",
          "exists": true,
          "classification": "canonical",
          "all_pass": true,
          "scope_note": "Ordering-focused translation lane for the open Szilard hard-reset carrier. It shows that stronger feedback asymmetry improves the open ordering signal materially."
        },
        {
          "row_id": "qit_szilard_record_ordering_refinement_translation_lane",
          "exists": true,
          "classification": "canonical",
          "all_pass": true,
          "scope_note": "Refined ordering-focused translation lane for the open Szilard hard-reset carrier. It checks whether local feedback-duration and barrier-depth tuning materially shrink the remaining ordering gap to the strict record/reset companion."
        },
        {
          "row_id": "szilard_record_ordering_refinement_reset_swing_sweep",
          "exists": true,
          "classification": "exploratory",
          "all_pass": false,
          "scope_note": "Row-local reset-swing sensitivity recheck for the Szilard record ordering refinement. It emits the original reset_swing_gap observable instead of substituting residual reset entropy."
        },
        {
          "row_id": "measurement_record_reset_parameter_sweep",
          "exists": true,
          "classification": "exploratory",
          "all_pass": true,
          "scope_note": "Bounded successor probe for the Szilard record reset-swing blocker. It widens reset tilt, reset duration, and reset barrier around the existing ordering-refinement carrier, keeps the original reset_swing_gap observable, and does not claim QIT, GStack, axis, or engine admission."
        },
        {
          "row_id": "szilard_record_ordering_refinement_measurement_accuracy_recheck",
          "exists": true,
          "classification": "exploratory",
          "all_pass": true,
          "scope_note": "Exact-observable recheck for the Szilard record translation blocker. It runs the ordering-refinement carrier and emits measurement_accuracy_gap, which the successor translation lane previously left unretested."
        }
      ],
      "consolidated_admission_status": "closed",
      "consolidated_admission_receipt": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/engine_lab_repair_gap_consolidated_admission_results.json"
    },
    {
      "row_id": "qit_szilard_reverse_recovery_companion",
      "engine_family": "szilard",
      "audit_class": "repair_gap",
      "next_allowed_action": "tighten_exact_translation_metrics_before_admission",
      "promotion_blocker": "strict translation gaps remain above row-local bounds",
      "failed_check_count": 1,
      "failed_checks": [
        {
          "section": "boundary",
          "check": "shared_bidirectional_protocol_import"
        }
      ],
      "target_qit_row_id": null,
      "passing_successor_count": 0,
      "successor_rows": [],
      "consolidated_admission_status": "not_run",
      "consolidated_admission_receipt": null
    },
    {
      "row_id": "qit_szilard_substep_refinement_translation_lane",
      "engine_family": "szilard",
      "audit_class": "repair_gap",
      "next_allowed_action": "use_passing_successor_as_repair_evidence_keep_original_as_negative",
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
      "target_qit_row_id": null,
      "passing_successor_count": 3,
      "successor_rows": [
        {
          "row_id": "qit_szilard_substep_translation_lane",
          "exists": true,
          "classification": "canonical",
          "all_pass": true,
          "scope_note": "Promoted QIT-aligned Szilard substep translation lane. It compares the open stochastic substep row against the strict finite two-qubit companion and keeps measurement, ordering, and reset gaps explicit."
        },
        {
          "row_id": "qit_szilard_substep_balanced_translation_lane",
          "exists": true,
          "classification": "canonical",
          "all_pass": true,
          "scope_note": "Balanced translation lane for the stochastic Szilard substep carrier. It favors low-noise settings with stronger reset alignment."
        },
        {
          "row_id": "qit_szilard_substep_ordering_push_translation_lane",
          "exists": true,
          "classification": "canonical",
          "all_pass": true,
          "scope_note": "Ordering-push translation lane for the stochastic Szilard substep carrier."
        }
      ],
      "consolidated_admission_status": "closed",
      "consolidated_admission_receipt": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/engine_lab_repair_gap_consolidated_admission_results.json"
    },
    {
      "row_id": "szilard_ordering_sensitivity",
      "engine_family": "szilard",
      "audit_class": "open_lab_failure",
      "next_allowed_action": "repair_open_row_or_convert_to_negative_graveyard_variant",
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
      "target_qit_row_id": null,
      "passing_successor_count": 1,
      "successor_rows": [
        {
          "row_id": "szilard_ordering_nonmonotone_noise_successor",
          "exists": true,
          "classification": "exploratory",
          "all_pass": true,
          "scope_note": "Bounded successor for the Szilard ordering-sensitivity row. The source row falsified low-noise monotonicity and clean high-noise failure; this receipt preserves the surviving local ordering signal with stronger feedback and nonmonotone noise response, without QIT, GStack, axis, or engine admission."
        }
      ],
      "consolidated_admission_status": "not_run",
      "consolidated_admission_receipt": null
    },
    {
      "row_id": "szilard_record_ordering_refinement_reset_swing_sweep",
      "engine_family": "szilard",
      "audit_class": "repair_gap",
      "next_allowed_action": "tighten_exact_translation_metrics_before_admission",
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
      "target_qit_row_id": null,
      "passing_successor_count": 0,
      "successor_rows": [],
      "consolidated_admission_status": "not_run",
      "consolidated_admission_receipt": null
    },
    {
      "row_id": "szilard_record_reset_repair_sweep",
      "engine_family": "szilard",
      "audit_class": "open_lab_failure",
      "next_allowed_action": "repair_open_row_or_convert_to_negative_graveyard_variant",
      "promotion_blocker": "open stochastic row does not satisfy its own pass conditions",
      "failed_check_count": 1,
      "failed_checks": [
        {
          "section": "positive",
          "check": "stronger_reset_grid_increases_open_reset_swing"
        }
      ],
      "target_qit_row_id": null,
      "passing_successor_count": 1,
      "successor_rows": [
        {
          "row_id": "szilard_record_lifetime_repair_successor",
          "exists": true,
          "classification": "exploratory",
          "all_pass": true,
          "scope_note": "Bounded successor for the Szilard record/reset repair sweep. The source row improves repair score, ordering, measurement information, and record survival, while reset swing remains blocked on this carrier and is routed to the separate reset-axis recheck. This receipt does not claim QIT, GStack, axis, or engine admission."
        }
      ],
      "consolidated_admission_status": "not_run",
      "consolidated_admission_receipt": null
    },
    {
      "row_id": "szilard_substep_refinement_sweep",
      "engine_family": "szilard",
      "audit_class": "open_lab_failure",
      "next_allowed_action": "repair_open_row_or_convert_to_negative_graveyard_variant",
      "promotion_blocker": "open stochastic row does not satisfy its own pass conditions",
      "failed_check_count": 1,
      "failed_checks": [
        {
          "section": "positive",
          "check": "measurement_information_stays_high"
        }
      ],
      "target_qit_row_id": null,
      "passing_successor_count": 1,
      "successor_rows": [
        {
          "row_id": "szilard_substep_ordering_reset_successor",
          "exists": true,
          "classification": "exploratory",
          "all_pass": true,
          "scope_note": "Bounded successor for the Szilard substep refinement sweep. It preserves the surviving ordering-margin and reset-signal improvements while keeping measurement mutual information as an explicit bottleneck. No QIT, GStack, axis, or engine admission is claimed."
        }
      ],
      "consolidated_admission_status": "not_run",
      "consolidated_admission_receipt": null
    },
    {
      "row_id": "szilard_topology_entropy_array",
      "engine_family": "szilard",
      "audit_class": "topology_sidecar_or_graveyard",
      "next_allowed_action": "keep_as_topology_variant_until_reexpressed_on_strict_carrier",
      "promotion_blocker": "topology geometry is informative but not yet strict QIT carrier evidence",
      "failed_check_count": 1,
      "failed_checks": [
        {
          "section": "negative",
          "check": "at_least_one_topology_remains_weak_for_ordering"
        }
      ],
      "target_qit_row_id": null,
      "passing_successor_count": 1,
      "successor_rows": [
        {
          "row_id": "szilard_topology_positive_diversity_successor",
          "exists": true,
          "classification": "exploratory",
          "all_pass": true,
          "scope_note": "Bounded successor for the Szilard topology entropy sidecar. The source row showed positive ordering across tested topologies, asymmetric topology as the best local ordering carrier, and nonlogical entropy diversity; the weak-topology claim is kept as killed. No QIT, GStack, axis, or engine admission is claimed."
        }
      ],
      "consolidated_admission_status": "not_run",
      "consolidated_admission_receipt": null
    }
  ]
};
