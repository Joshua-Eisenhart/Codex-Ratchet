window.ENGINE_LAB_SUCCESSOR_COVERAGE_DATA = {
  "name": "engine_lab_successor_coverage_audit",
  "generated_at": "2026-05-10T08:03:31.074807+00:00",
  "summary": {
    "all_pass": true,
    "queue_row_count": 10,
    "active_uncovered_row_count": 0,
    "covered_by_successor_count": 7,
    "covered_by_consolidated_closed_count": 2,
    "covered_by_superseded_count": 1,
    "source_rows_preserved_negative": true,
    "qit_or_axis_promotion_allowed": false,
    "schema_error_count": 0,
    "scope_note": "Controller audit proving the current engine-lab open-row queue has no active uncovered rows. It accepts only successor-covered, consolidated-closed, or superseded lanes, preserves source negatives, and does not admit QIT, GStack, axis, or runtime-engine claims."
  },
  "source_receipts": {
    "cycle_protocol_receipt_status_matrix": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/cycle_protocol_receipt_status_matrix_results.json",
    "engine_lab_open_row_audit": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/engine_lab_open_row_audit_results.json",
    "engine_lab_next_work_queue": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/engine_lab_next_work_queue_results.json"
  },
  "source_receipt_mtimes": {
    "cycle_protocol_receipt_status_matrix_results.json": 1778400210.9422123,
    "engine_lab_open_row_audit_results.json": 1778400211.073278,
    "engine_lab_next_work_queue_results.json": 1778398582.870418
  },
  "positive": {
    "queue_reports_no_active_uncovered_rows": {
      "active_uncovered_row_count": 0,
      "pass": true
    },
    "all_queue_rows_are_covered_by_allowed_lane_types": {
      "covered_count": 10,
      "row_count": 10,
      "pass": true
    },
    "open_row_audit_is_complete": {
      "audit_complete": true,
      "missing_audit_rows": 0,
      "unclassified_open_rows": 0,
      "pass": true
    }
  },
  "negative": {
    "source_rows_remain_negative_or_nonpassing": {
      "source_negative_count": 10,
      "row_count": 10,
      "pass": true
    },
    "matrix_still_not_promoted_to_full_pass": {
      "matrix_all_pass": false,
      "matrix_status": "complete_with_open_rows",
      "pass": true
    },
    "successor_coverage_is_not_qit_axis_or_gstack_admission": {
      "qit_or_axis_promotion_allowed": false,
      "pass": true
    }
  },
  "boundary": {
    "coverage_rows_match_queue_rows": {
      "coverage_row_count": 10,
      "queue_row_count": 10,
      "pass": true
    },
    "uncovered_rows_are_listed_explicitly": {
      "uncovered_row_count": 0,
      "uncovered_rows": [],
      "pass": true
    }
  },
  "rows": [
    {
      "row_id": "carnot_entropy_family_array",
      "audit_class": "readout_split",
      "recommended_lane": "successor_receipt_available_keep_source_as_negative_readout_split",
      "covered": true,
      "passing_successor_count": 1,
      "consolidated_admission_status": "not_run",
      "graveyard_covered": true,
      "source_all_pass": false,
      "source_negative_preserved": true,
      "qit_or_axis_promotion_allowed": false,
      "schema_error": null
    },
    {
      "row_id": "carnot_forward_asymmetric",
      "audit_class": "open_lab_failure",
      "recommended_lane": "successor_receipt_available_keep_source_as_negative_open_failure",
      "covered": true,
      "passing_successor_count": 1,
      "consolidated_admission_status": "not_run",
      "graveyard_covered": true,
      "source_all_pass": false,
      "source_negative_preserved": true,
      "qit_or_axis_promotion_allowed": false,
      "schema_error": null
    },
    {
      "row_id": "carnot_reverse_asymmetric",
      "audit_class": "open_lab_failure",
      "recommended_lane": "successor_receipt_available_keep_source_as_negative_open_failure",
      "covered": true,
      "passing_successor_count": 1,
      "consolidated_admission_status": "not_run",
      "graveyard_covered": true,
      "source_all_pass": false,
      "source_negative_preserved": true,
      "qit_or_axis_promotion_allowed": false,
      "schema_error": null
    },
    {
      "row_id": "qit_szilard_record_translation_lane",
      "audit_class": "repair_gap",
      "recommended_lane": "closed_by_consolidated_successor_keep_source_negative",
      "covered": true,
      "passing_successor_count": 6,
      "consolidated_admission_status": "closed",
      "graveyard_covered": false,
      "source_all_pass": false,
      "source_negative_preserved": true,
      "qit_or_axis_promotion_allowed": false,
      "schema_error": null
    },
    {
      "row_id": "qit_szilard_substep_refinement_translation_lane",
      "audit_class": "repair_gap",
      "recommended_lane": "closed_by_consolidated_successor_keep_source_negative",
      "covered": true,
      "passing_successor_count": 3,
      "consolidated_admission_status": "closed",
      "graveyard_covered": false,
      "source_all_pass": false,
      "source_negative_preserved": true,
      "qit_or_axis_promotion_allowed": false,
      "schema_error": null
    },
    {
      "row_id": "szilard_ordering_sensitivity",
      "audit_class": "open_lab_failure",
      "recommended_lane": "successor_receipt_available_keep_source_as_negative_open_failure",
      "covered": true,
      "passing_successor_count": 1,
      "consolidated_admission_status": "not_run",
      "graveyard_covered": true,
      "source_all_pass": false,
      "source_negative_preserved": true,
      "qit_or_axis_promotion_allowed": false,
      "schema_error": null
    },
    {
      "row_id": "szilard_record_reset_repair_sweep",
      "audit_class": "open_lab_failure",
      "recommended_lane": "successor_receipt_available_keep_source_as_negative_open_failure",
      "covered": true,
      "passing_successor_count": 1,
      "consolidated_admission_status": "not_run",
      "graveyard_covered": true,
      "source_all_pass": false,
      "source_negative_preserved": true,
      "qit_or_axis_promotion_allowed": false,
      "schema_error": null
    },
    {
      "row_id": "szilard_substep_refinement_sweep",
      "audit_class": "open_lab_failure",
      "recommended_lane": "successor_receipt_available_keep_source_as_negative_open_failure",
      "covered": true,
      "passing_successor_count": 1,
      "consolidated_admission_status": "not_run",
      "graveyard_covered": true,
      "source_all_pass": false,
      "source_negative_preserved": true,
      "qit_or_axis_promotion_allowed": false,
      "schema_error": null
    },
    {
      "row_id": "szilard_topology_entropy_array",
      "audit_class": "topology_sidecar_or_graveyard",
      "recommended_lane": "successor_receipt_available_keep_source_as_negative_topology_sidecar",
      "covered": true,
      "passing_successor_count": 1,
      "consolidated_admission_status": "not_run",
      "graveyard_covered": true,
      "source_all_pass": false,
      "source_negative_preserved": true,
      "qit_or_axis_promotion_allowed": false,
      "schema_error": null
    },
    {
      "row_id": "szilard_record_ordering_refinement_reset_swing_sweep",
      "audit_class": "repair_gap",
      "recommended_lane": "superseded_by_reset_axis_widened_recheck_keep_as_negative",
      "covered": true,
      "passing_successor_count": 0,
      "consolidated_admission_status": "not_run",
      "graveyard_covered": false,
      "source_all_pass": false,
      "source_negative_preserved": true,
      "qit_or_axis_promotion_allowed": false,
      "schema_error": null
    }
  ],
  "uncovered_rows": []
};
