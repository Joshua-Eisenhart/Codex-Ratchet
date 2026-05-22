window.SZILARD_DUAL_STACK_DATA = {
  "name": "measure_feedback_erasure_recovery_cycle_pair",
  "summary": {
    "all_pass": true,
    "information_gain": 0.6931471805599453,
    "system_free_energy_gain": 0.6931471805599453,
    "erasure_cost": 0.6931471805599453,
    "net_after_erasure": 0.0,
    "tool_count": 16,
    "load_bearing_tool_count": 11,
    "visual_payload": "visualizer/szilard-dual-stack-data.js",
    "scope_note": "Measurement/feedback/erasure recovery cycle-pair row on a finite two-qubit carrier. It models measurement/feedback/erasure and the reverse recovery bookkeeping as opposite information-cycle traversals without claiming a universal demon."
  },
  "loops": {
    "inductive_heating_loop": {
      "loop_id": "inductive_heating_loop",
      "role": "measurement_feedback_erasure",
      "record_entropy_delta": 0.0,
      "system_entropy_delta": -0.6931471805599453,
      "information_delta": 0.0,
      "free_energy_gain": 0.6931471805599453,
      "erasure_cost": 0.6931471805599453,
      "net_after_erasure": 0.0,
      "stage_trace": [
        {
          "kind": "measurement",
          "before": "initial_mixed_blank",
          "after": "measured_record",
          "record_entropy_delta": 0.6931471805599453,
          "system_entropy_delta": 0.0,
          "information_delta": 0.6931471805599453,
          "free_energy_gain": 0.0,
          "erasure_cost": 0.0
        },
        {
          "kind": "feedback",
          "before": "measured_record",
          "after": "feedback_purified",
          "record_entropy_delta": 0.0,
          "system_entropy_delta": -0.6931471805599453,
          "information_delta": -0.6931471805599453,
          "free_energy_gain": 0.6931471805599453,
          "erasure_cost": 0.0
        },
        {
          "kind": "erasure",
          "before": "feedback_purified",
          "after": "erased_closed",
          "record_entropy_delta": -0.6931471805599453,
          "system_entropy_delta": 0.0,
          "information_delta": 0.0,
          "free_energy_gain": 0.0,
          "erasure_cost": 0.6931471805599453
        }
      ]
    },
    "deductive_cooling_loop": {
      "loop_id": "deductive_cooling_loop",
      "role": "reverse_recovery_bookkeeping",
      "record_entropy_delta": 0.0,
      "system_entropy_delta": 0.6931471805599453,
      "information_delta": 0.0,
      "free_energy_gain": -0.6931471805599453,
      "erasure_cost": -0.6931471805599453,
      "net_after_erasure": 0.0,
      "stage_trace": [
        {
          "kind": "erasure_reverse",
          "before": "erased_closed",
          "after": "feedback_purified",
          "record_entropy_delta": 0.6931471805599453,
          "system_entropy_delta": -0.0,
          "information_delta": -0.0,
          "free_energy_gain": -0.0,
          "erasure_cost": -0.6931471805599453
        },
        {
          "kind": "feedback_reverse",
          "before": "feedback_purified",
          "after": "measured_record",
          "record_entropy_delta": -0.0,
          "system_entropy_delta": 0.6931471805599453,
          "information_delta": 0.6931471805599453,
          "free_energy_gain": -0.6931471805599453,
          "erasure_cost": -0.0
        },
        {
          "kind": "measurement_reverse",
          "before": "measured_record",
          "after": "initial_mixed_blank",
          "record_entropy_delta": -0.6931471805599453,
          "system_entropy_delta": -0.0,
          "information_delta": -0.6931471805599453,
          "free_energy_gain": -0.0,
          "erasure_cost": -0.0
        }
      ]
    }
  },
  "states": {
    "initial_mixed_blank": {
      "label": "initial_mixed_blank",
      "joint_entropy": 0.6931471805599453,
      "joint_entropy_scipy": 0.6931471805599433,
      "system_entropy": 0.6931471805599453,
      "memory_entropy": -0.0,
      "mutual_information": 0.0,
      "trace": 1.0
    },
    "measured_record": {
      "label": "measured_record",
      "joint_entropy": 0.6931471805599453,
      "joint_entropy_scipy": 0.6931471805599433,
      "system_entropy": 0.6931471805599453,
      "memory_entropy": 0.6931471805599453,
      "mutual_information": 0.6931471805599453,
      "trace": 1.0
    },
    "feedback_purified": {
      "label": "feedback_purified",
      "joint_entropy": 0.6931471805599453,
      "joint_entropy_scipy": 0.6931471805599433,
      "system_entropy": -0.0,
      "memory_entropy": 0.6931471805599453,
      "mutual_information": 0.0,
      "trace": 1.0
    },
    "erased_closed": {
      "label": "erased_closed",
      "joint_entropy": -0.0,
      "joint_entropy_scipy": -1.110223024625156e-15,
      "system_entropy": -0.0,
      "memory_entropy": -0.0,
      "mutual_information": 0.0,
      "trace": 1.0
    }
  },
  "cycle_step_invariant_map": {
    "boundary": "local_cycle_invariant_map_not_admitted_axis_promotion",
    "invariants": {
      "entropy_transfer_polarity": {
        "local_name": "information_entropy_polarity",
        "degree_of_freedom": "record/correlation entropy created versus erased",
        "observable": "record_entropy_delta and mutual_information",
        "inductive_value": 0.0,
        "deductive_value": 0.0
      },
      "record_branch_partition": {
        "local_name": "record_branch",
        "degree_of_freedom": "system side versus memory side",
        "observable": "partial traces rho_system and rho_memory"
      },
      "system_memory_control_frame": {
        "local_name": "control_frame",
        "degree_of_freedom": "unmeasured, measured, feedback-conditioned, erased frame",
        "observable": "protocol state label"
      },
      "cycle_traversal_family": {
        "local_name": "loop_family",
        "degree_of_freedom": "demon/work-extraction versus recovery/reset traversal",
        "observable": "free_energy_gain and erasure_cost signs"
      },
      "step_sequence_parity": {
        "local_name": "protocol_order_class",
        "degree_of_freedom": "measurement-feedback-erasure ordering",
        "observable": "directed protocol DAG"
      },
      "measurement_feedback_reset_operator_family": {
        "local_name": "operator_mode",
        "degree_of_freedom": "correlate, conditionally flip, reset",
        "observable": "CNOT, controlled-X, reset CPTP map"
      },
      "stage_precedence_orientation": {
        "local_name": "precedence_orientation",
        "degree_of_freedom": "which operation can legally precede another",
        "observable": "measurement before feedback before erasure"
      }
    },
    "degrees_of_freedom": [
      "system_state",
      "memory_state",
      "record_correlation",
      "feedback_order",
      "erasure_cost",
      "cycle_direction",
      "protocol_precedence"
    ]
  },
  "boundaries": {
    "landauer_free_erasure_blocked_by_z3": {
      "result": "unsat",
      "pass": true
    },
    "landauer_free_erasure_blocked_by_cvc5": {
      "result": "unsat",
      "pass": true
    },
    "not_a_universal_demon_claim": {
      "pass": true,
      "scope_note": "Measurement/feedback/erasure recovery cycle-pair row on a finite two-qubit carrier. It models measurement/feedback/erasure and the reverse recovery bookkeeping as opposite information-cycle traversals without claiming a universal demon."
    }
  }
};
