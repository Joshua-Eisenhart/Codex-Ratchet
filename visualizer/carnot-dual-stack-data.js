window.CARNOT_DUAL_STACK_DATA = {
  "name": "two_bath_heat_work_reversible_cycle_pair",
  "summary": {
    "all_pass": true,
    "forward_efficiency": 0.5000000000000001,
    "forward_carnot_bound": 0.5,
    "reverse_cop": 0.9999999999999999,
    "reverse_cop_carnot": 1.0,
    "q_hot_absorbed": 0.3755915097737852,
    "q_cold_rejected": 0.1877957548868926,
    "q_cold_absorbed_reverse": 0.1877957548868926,
    "tool_count": 16,
    "load_bearing_tool_count": 13,
    "visual_payload": "visualizer/carnot-dual-stack-data.js",
    "scope_note": "Two-bath heat/work reversible cycle-pair row: same finite qubit working substance, two opposite cycle directions. It supports cycle visualization and tool coupling; it does not promote a final QIT runtime or admitted-axis claim."
  },
  "loops": {
    "inductive_heating_loop": {
      "loop_id": "inductive_heating_loop",
      "role": "forward_work_producing_cycle",
      "step_labels": [
        "B_hot_low_gap",
        "C_cold_low_gap",
        "D_cold_high_gap",
        "A_hot_high_gap_return"
      ],
      "heat_from_hot_bath_into_system": 0.3755915097737852,
      "heat_from_cold_bath_into_system": -0.1877957548868926,
      "work_by_system": 0.18779575488689262,
      "work_input": 0.0,
      "working_substance_delta_entropy": 0.0,
      "cold_reservoir_entropy_delta": 0.1877957548868926,
      "hot_reservoir_entropy_delta": -0.1877957548868926,
      "total_reservoir_entropy_delta": 0.0,
      "stage_trace": [
        {
          "kind": "isothermal",
          "before": "A_hot_high_gap",
          "after": "B_hot_low_gap",
          "delta_entropy": 0.1877957548868926,
          "heat_into_system": 0.3755915097737852,
          "work_by_system": 0.5453274123947087
        },
        {
          "kind": "adiabatic",
          "before": "B_hot_low_gap",
          "after": "C_cold_low_gap",
          "delta_entropy": 0.0,
          "heat_into_system": 0.0,
          "work_by_system": 0.18877033439907273
        },
        {
          "kind": "isothermal",
          "before": "C_cold_low_gap",
          "after": "D_cold_high_gap",
          "delta_entropy": -0.1877957548868926,
          "heat_into_system": -0.1877957548868926,
          "work_by_system": -0.27266370619735436
        },
        {
          "kind": "adiabatic",
          "before": "D_cold_high_gap",
          "after": "A_hot_high_gap_return",
          "delta_entropy": 0.0,
          "heat_into_system": 0.0,
          "work_by_system": -0.27363828570953447
        }
      ]
    },
    "deductive_cooling_loop": {
      "loop_id": "deductive_cooling_loop",
      "role": "reverse_refrigerator",
      "step_labels": [
        "D_cold_high_gap",
        "C_cold_low_gap",
        "B_hot_low_gap",
        "A_hot_high_gap"
      ],
      "heat_from_hot_bath_into_system": -0.3755915097737852,
      "heat_from_cold_bath_into_system": 0.1877957548868926,
      "work_by_system": -0.18779575488689262,
      "work_input": 0.18779575488689262,
      "working_substance_delta_entropy": 0.0,
      "cold_reservoir_entropy_delta": -0.1877957548868926,
      "hot_reservoir_entropy_delta": 0.1877957548868926,
      "total_reservoir_entropy_delta": 0.0,
      "stage_trace": [
        {
          "kind": "adiabatic_reverse",
          "before": "A_hot_high_gap_return",
          "after": "D_cold_high_gap",
          "delta_entropy": -0.0,
          "heat_into_system": -0.0,
          "work_by_system": 0.27363828570953447
        },
        {
          "kind": "isothermal_reverse",
          "before": "D_cold_high_gap",
          "after": "C_cold_low_gap",
          "delta_entropy": 0.1877957548868926,
          "heat_into_system": 0.1877957548868926,
          "work_by_system": 0.27266370619735436
        },
        {
          "kind": "adiabatic_reverse",
          "before": "C_cold_low_gap",
          "after": "B_hot_low_gap",
          "delta_entropy": -0.0,
          "heat_into_system": -0.0,
          "work_by_system": -0.18877033439907273
        },
        {
          "kind": "isothermal_reverse",
          "before": "B_hot_low_gap",
          "after": "A_hot_high_gap",
          "delta_entropy": -0.1877957548868926,
          "heat_into_system": -0.3755915097737852,
          "work_by_system": -0.5453274123947087
        }
      ]
    }
  },
  "states": [
    {
      "label": "A_hot_high_gap",
      "temperature": 2.0,
      "gap": 3.0,
      "p_excited": 0.18242552380635632,
      "entropy": 0.47505156369228685,
      "internal_energy": 0.5472765714190689,
      "free_energy": -0.40282655596550476
    },
    {
      "label": "B_hot_low_gap",
      "temperature": 2.0,
      "gap": 1.0,
      "p_excited": 0.37754066879814546,
      "entropy": 0.6628473185791794,
      "internal_energy": 0.37754066879814546,
      "free_energy": -0.9481539683602134
    },
    {
      "label": "C_cold_low_gap",
      "temperature": 1.0,
      "gap": 0.5,
      "p_excited": 0.37754066879814546,
      "entropy": 0.6628473185791794,
      "internal_energy": 0.18877033439907273,
      "free_energy": -0.4740769841801067
    },
    {
      "label": "D_cold_high_gap",
      "temperature": 1.0,
      "gap": 1.5,
      "p_excited": 0.18242552380635632,
      "entropy": 0.47505156369228685,
      "internal_energy": 0.27363828570953447,
      "free_energy": -0.20141327798275238
    }
  ],
  "cycle_step_invariant_map": {
    "boundary": "local_cycle_invariant_map_not_admitted_axis_promotion",
    "invariants": {
      "entropy_transfer_polarity": {
        "local_name": "entropy_gradient_polarity",
        "degree_of_freedom": "sign and magnitude of reservoir entropy transfer",
        "observable": "cold_reservoir_entropy_delta",
        "inductive_value": 0.1877957548868926,
        "deductive_value": -0.1877957548868926,
        "correlation_hint": "closest to thermodynamic entropy-drive intuition, not a QIT cut kernel"
      },
      "bath_contact_branch": {
        "local_name": "bath_branch",
        "degree_of_freedom": "hot-contact versus cold-contact branch",
        "observable": "isothermal leg bath label",
        "values": [
          "hot_isotherm",
          "cold_isotherm"
        ],
        "correlation_hint": "terrain/topology split analogue"
      },
      "temperature_gap_frame": {
        "local_name": "working_frame",
        "degree_of_freedom": "temperature-scaled gap frame",
        "observable": "gap / temperature invariant along adiabats",
        "hot_high_ratio": 1.5,
        "cold_high_ratio": 1.5,
        "hot_low_ratio": 0.5,
        "cold_low_ratio": 0.5,
        "correlation_hint": "frame-change analogue; adiabats preserve occupation probability"
      },
      "cycle_traversal_family": {
        "local_name": "loop_family",
        "degree_of_freedom": "work-producing versus work-consuming traversal family",
        "observable": "work sign and cold entropy sign",
        "values": {
          "inductive_heating": {
            "work_by_system": 0.18779575488689262,
            "cold_entropy_delta": 0.1877957548868926
          },
          "deductive_cooling": {
            "work_by_system": -0.18779575488689262,
            "cold_entropy_delta": -0.1877957548868926
          }
        },
        "correlation_hint": "work-cycle-family split analogue"
      },
      "step_sequence_parity": {
        "local_name": "leg_order_class",
        "degree_of_freedom": "isothermal/adiabatic composition order",
        "observable": "I-A-I-A versus reversed A-I-A-I",
        "inductive_order": [
          "isothermal",
          "adiabatic",
          "isothermal",
          "adiabatic"
        ],
        "deductive_order": [
          "adiabatic_reverse",
          "isothermal_reverse",
          "adiabatic_reverse",
          "isothermal_reverse"
        ],
        "correlation_hint": "loop-order family analogue"
      },
      "heat_work_operator_family": {
        "local_name": "operator_mode",
        "degree_of_freedom": "heat-exchange leg versus work-only leg",
        "observable": "nonzero heat_into_system versus zero heat_into_system",
        "values": [
          "thermal_contact",
          "adiabatic_work"
        ],
        "correlation_hint": "operator-family split analogue"
      },
      "stage_precedence_orientation": {
        "local_name": "precedence_orientation",
        "degree_of_freedom": "which leg precedes which under traversal direction",
        "observable": "directed cycle order",
        "inductive_order": [
          "B_hot_low_gap",
          "C_cold_low_gap",
          "D_cold_high_gap",
          "A_hot_high_gap_return"
        ],
        "deductive_order": [
          "D_cold_high_gap",
          "C_cold_low_gap",
          "B_hot_low_gap",
          "A_hot_high_gap"
        ],
        "correlation_hint": "composition/precedence analogue"
      }
    },
    "degrees_of_freedom": [
      "temperature_ratio",
      "gap_ratio",
      "cycle_direction",
      "bath_contact_branch",
      "leg_order",
      "heat_work_mode",
      "stage_precedence",
      "entropy_gradient_sign"
    ]
  },
  "tool_summary": {
    "tool_count": 16,
    "load_bearing_tool_count": 13
  },
  "boundaries": {
    "super_carnot_blocked_by_z3": {
      "result": "unsat",
      "pass": true
    },
    "super_carnot_blocked_by_cvc5_fixed_case": {
      "result": "unsat",
      "pass": true
    },
    "dual_stack_is_not_two_different_cycles": {
      "shared_state_count": 4,
      "pass": true
    }
  }
};
