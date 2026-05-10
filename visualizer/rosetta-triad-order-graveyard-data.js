window.ROSETTA_TRIAD_ORDER_GRAVEYARD_DATA = {
  "name": "rosetta_triad_order_graveyard",
  "summary": {
    "all_pass": true,
    "variant_count": 13,
    "survivor_count": 6,
    "killed_count": 7,
    "expected_status_match": true,
    "order_graphs_pass": true,
    "proof_fences_pass": true,
    "visual_payload": "visualizer/rosetta-triad-order-graveyard-data.js",
    "scope_note": "Triadic order-variant graveyard over Carnot, Szilard, and I Ching-64. It tests canonical and reverse orders as survivors, and nearby scrambled, collapsed, or wrong-precedence variants as killed candidates. This is negative Rosetta evidence, not QIT admission."
  },
  "variant_rows": [
    {
      "engine": "carnot",
      "variant": "canonical_forward",
      "order": [
        "isothermal",
        "adiabatic",
        "isothermal",
        "adiabatic"
      ],
      "expected": "survives",
      "survives_order_gate": true,
      "status": "survives",
      "reason": "Carnot accepts only the canonical heat-engine order or its honest reverse refrigerator traversal.",
      "graph": {
        "nodes": 4,
        "edges": 3,
        "pyg_nodes": 4,
        "pyg_edges": 3,
        "pass": true
      }
    },
    {
      "engine": "carnot",
      "variant": "honest_reverse",
      "order": [
        "adiabatic",
        "isothermal",
        "adiabatic",
        "isothermal"
      ],
      "expected": "survives",
      "survives_order_gate": true,
      "status": "survives",
      "reason": "Carnot accepts only the canonical heat-engine order or its honest reverse refrigerator traversal.",
      "graph": {
        "nodes": 4,
        "edges": 3,
        "pyg_nodes": 4,
        "pyg_edges": 3,
        "pass": true
      }
    },
    {
      "engine": "carnot",
      "variant": "swap_middle_legs",
      "order": [
        "isothermal",
        "isothermal",
        "adiabatic",
        "adiabatic"
      ],
      "expected": "killed",
      "survives_order_gate": false,
      "status": "killed",
      "reason": "Carnot accepts only the canonical heat-engine order or its honest reverse refrigerator traversal.",
      "graph": {
        "nodes": 4,
        "edges": 3,
        "pyg_nodes": 4,
        "pyg_edges": 3,
        "pass": true
      }
    },
    {
      "engine": "carnot",
      "variant": "collapsed_single_leg",
      "order": [
        "isothermal",
        "isothermal",
        "isothermal",
        "isothermal"
      ],
      "expected": "killed",
      "survives_order_gate": false,
      "status": "killed",
      "reason": "Carnot accepts only the canonical heat-engine order or its honest reverse refrigerator traversal.",
      "graph": {
        "nodes": 4,
        "edges": 3,
        "pyg_nodes": 4,
        "pyg_edges": 3,
        "pass": true
      }
    },
    {
      "engine": "szilard",
      "variant": "canonical_measure_feedback_erase",
      "order": [
        "measurement",
        "feedback",
        "erasure"
      ],
      "expected": "survives",
      "survives_order_gate": true,
      "status": "survives",
      "reason": "Szilard requires measurement-feedback-erasure precedence or the exact reverse bookkeeping traversal.",
      "graph": {
        "nodes": 3,
        "edges": 2,
        "pyg_nodes": 3,
        "pyg_edges": 2,
        "pass": true
      }
    },
    {
      "engine": "szilard",
      "variant": "honest_reverse_recovery",
      "order": [
        "erasure_reverse",
        "feedback_reverse",
        "measurement_reverse"
      ],
      "expected": "survives",
      "survives_order_gate": true,
      "status": "survives",
      "reason": "Szilard requires measurement-feedback-erasure precedence or the exact reverse bookkeeping traversal.",
      "graph": {
        "nodes": 3,
        "edges": 2,
        "pyg_nodes": 3,
        "pyg_edges": 2,
        "pass": true
      }
    },
    {
      "engine": "szilard",
      "variant": "feedback_before_measurement",
      "order": [
        "feedback",
        "measurement",
        "erasure"
      ],
      "expected": "killed",
      "survives_order_gate": false,
      "status": "killed",
      "reason": "Szilard requires measurement-feedback-erasure precedence or the exact reverse bookkeeping traversal.",
      "graph": {
        "nodes": 3,
        "edges": 2,
        "pyg_nodes": 3,
        "pyg_edges": 2,
        "pass": true
      }
    },
    {
      "engine": "szilard",
      "variant": "missing_erasure",
      "order": [
        "measurement",
        "feedback"
      ],
      "expected": "killed",
      "survives_order_gate": false,
      "status": "killed",
      "reason": "Szilard requires measurement-feedback-erasure precedence or the exact reverse bookkeeping traversal.",
      "graph": {
        "nodes": 2,
        "edges": 1,
        "pyg_nodes": 2,
        "pyg_edges": 1,
        "pass": true
      }
    },
    {
      "engine": "iching_64",
      "variant": "canonical_gray_cycle",
      "expected": "survives",
      "unique_states": 64,
      "min_hamming_step": 1,
      "max_hamming_step": 1,
      "survives_order_gate": true,
      "status": "survives",
      "reason": "I Ching-64 symbolic row requires a one-line-at-a-time Hamiltonian cycle through all 64 states.",
      "graph": {
        "nodes": 64,
        "edges": 63,
        "pyg_nodes": 64,
        "pyg_edges": 63,
        "pass": true
      }
    },
    {
      "engine": "iching_64",
      "variant": "honest_reverse_gray_cycle",
      "expected": "survives",
      "unique_states": 64,
      "min_hamming_step": 1,
      "max_hamming_step": 1,
      "survives_order_gate": true,
      "status": "survives",
      "reason": "I Ching-64 symbolic row requires a one-line-at-a-time Hamiltonian cycle through all 64 states.",
      "graph": {
        "nodes": 64,
        "edges": 63,
        "pyg_nodes": 64,
        "pyg_edges": 63,
        "pass": true
      }
    },
    {
      "engine": "iching_64",
      "variant": "binary_count_order",
      "expected": "killed",
      "unique_states": 64,
      "min_hamming_step": 1,
      "max_hamming_step": 6,
      "survives_order_gate": false,
      "status": "killed",
      "reason": "I Ching-64 symbolic row requires a one-line-at-a-time Hamiltonian cycle through all 64 states.",
      "graph": {
        "nodes": 64,
        "edges": 63,
        "pyg_nodes": 64,
        "pyg_edges": 63,
        "pass": true
      }
    },
    {
      "engine": "iching_64",
      "variant": "collapsed_single_state",
      "expected": "killed",
      "unique_states": 1,
      "min_hamming_step": 0,
      "max_hamming_step": 0,
      "survives_order_gate": false,
      "status": "killed",
      "reason": "I Ching-64 symbolic row requires a one-line-at-a-time Hamiltonian cycle through all 64 states.",
      "graph": {
        "nodes": 64,
        "edges": 63,
        "pyg_nodes": 64,
        "pyg_edges": 63,
        "pass": true
      }
    },
    {
      "engine": "iching_64",
      "variant": "seeded_random_order",
      "expected": "killed",
      "unique_states": 64,
      "min_hamming_step": 1,
      "max_hamming_step": 5,
      "survives_order_gate": false,
      "status": "killed",
      "reason": "I Ching-64 symbolic row requires a one-line-at-a-time Hamiltonian cycle through all 64 states.",
      "graph": {
        "nodes": 64,
        "edges": 63,
        "pyg_nodes": 64,
        "pyg_edges": 63,
        "pass": true
      }
    }
  ],
  "proof_fences": {
    "z3_wrong_szilard_precedence_unsat": {
      "claim": "feedback can precede measurement while preserving canonical Szilard precedence",
      "result": "unsat",
      "pass": true
    },
    "cvc5_wrong_szilard_precedence_unsat": {
      "claim": "feedback can precede measurement while preserving canonical Szilard precedence",
      "result": "unsat",
      "pass": true
    }
  },
  "order_exhaustion": {
    "szilard_permutation_count": 6,
    "valid_orders": [
      [
        "measurement",
        "feedback",
        "erasure"
      ],
      [
        "erasure",
        "feedback",
        "measurement"
      ]
    ],
    "killed_orders": [
      [
        "measurement",
        "erasure",
        "feedback"
      ],
      [
        "feedback",
        "measurement",
        "erasure"
      ],
      [
        "feedback",
        "erasure",
        "measurement"
      ],
      [
        "erasure",
        "measurement",
        "feedback"
      ]
    ],
    "pass": true
  }
};
