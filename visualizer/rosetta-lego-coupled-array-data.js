window.ROSETTA_LEGO_COUPLED_ARRAY_DATA = {
  "name": "rosetta_lego_coupled_array",
  "summary": {
    "all_pass": true,
    "engine_count": 3,
    "coupled_pair_count": 3,
    "weighted_edge_count": 3,
    "qit_promotion_blocked": true,
    "visual_payload": "visualizer/rosetta-lego-coupled-array-data.js",
    "scope_note": "Bounded coupled Rosetta lego-array sim over current Carnot, Szilard, and I Ching-64 survivor legos. It tests whether registry-approved pairwise couplings assemble into a larger functional comparison graph without QIT, GStack, or axis promotion."
  },
  "coupling_graph": {
    "engines": [
      "carnot",
      "iching_64",
      "szilard"
    ],
    "nodes": 3,
    "edges": 3,
    "pyg_nodes": 3,
    "pyg_edges": 3,
    "xgi_edges": 5,
    "weighted_edges": [
      {
        "left": "carnot",
        "right": "szilard",
        "score": 1.0
      },
      {
        "left": "carnot",
        "right": "iching_64",
        "score": 0.9423076923076923
      },
      {
        "left": "szilard",
        "right": "iching_64",
        "score": 0.9423076923076923
      }
    ],
    "pass": true
  },
  "coupling_density": {
    "probabilities": [
      0.3466666666666667,
      0.32666666666666666,
      0.32666666666666666
    ],
    "shannon_entropy": 1.098214876889085,
    "scipy_vn_entropy": 1.0982148768890818,
    "qiskit_trace": 1.0,
    "qutip_trace": 1.0,
    "torch_gradient_positive": true,
    "sympy_normalization_identity": "1",
    "pass": true
  },
  "proof_fences": {
    "z3_blocks_qit_promotion": {
      "claim": "registry-approved Rosetta couplings imply QIT runtime promotion",
      "result": "unsat",
      "pass": true
    },
    "cvc5_blocks_qit_promotion": {
      "claim": "registry-approved Rosetta couplings imply QIT runtime promotion",
      "result": "unsat",
      "pass": true
    }
  }
};
