window.ROSETTA_TRIAD_MODES_DATA = {
  "name": "rosetta_triad_modes",
  "summary": {
    "all_pass": true,
    "engine_count": 3,
    "mode_count": 3,
    "mode_row_count": 9,
    "shared_structure_row_count": 6,
    "graveyard_row_count": 5,
    "all_modes_pass": true,
    "identity_collapse_blocked": true,
    "visual_payload": "visualizer/rosetta-triad-modes-data.js",
    "scope_note": "Triadic Rosetta mode layer over Carnot, Szilard, and I Ching-64 rows. It compares the three through classical, bridge, and nonclassical-adjacent mode surfaces, then stress-tests identity-collapse and promotion mistakes. It is not QIT-engine admission, not I Ching proof, and not an axis claim."
  },
  "mode_matrix": [
    {
      "engine": "carnot",
      "mode": "classical",
      "pass": true,
      "claim": "finite state/operator bookkeeping with an entropy readout",
      "geometry": "four-state thermodynamic cycle",
      "entropy_readout": "reservoir entropy plus heat/work efficiency",
      "state_count": 4,
      "operator_count": 4,
      "axis_count": 7,
      "boundary": "classical agreement is surface grammar, not identity"
    },
    {
      "engine": "carnot",
      "mode": "bridge",
      "pass": true,
      "claim": "axis slots, graph/order, and proof fences connect language layers",
      "geometry": "four-state thermodynamic cycle",
      "entropy_readout": "reservoir entropy plus heat/work efficiency",
      "state_count": 4,
      "operator_count": 4,
      "axis_count": 7,
      "boundary": "bridge rows are comparison scaffolds, not promotion gates"
    },
    {
      "engine": "carnot",
      "mode": "nonclassical_adjacent",
      "pass": true,
      "claim": "density carriers or graph tensors give a nonclassical-compatible representation",
      "geometry": "four-state thermodynamic cycle",
      "entropy_readout": "reservoir entropy plus heat/work efficiency",
      "state_count": 4,
      "operator_count": 4,
      "axis_count": 7,
      "boundary": "density/tool witnesses are not a final QIT engine runtime"
    },
    {
      "engine": "szilard",
      "mode": "classical",
      "pass": true,
      "claim": "finite state/operator bookkeeping with an entropy readout",
      "geometry": "finite two-qubit system-memory protocol path",
      "entropy_readout": "record entropy, mutual information, erasure cost",
      "state_count": 4,
      "operator_count": 3,
      "axis_count": 7,
      "boundary": "classical agreement is surface grammar, not identity"
    },
    {
      "engine": "szilard",
      "mode": "bridge",
      "pass": true,
      "claim": "axis slots, graph/order, and proof fences connect language layers",
      "geometry": "finite two-qubit system-memory protocol path",
      "entropy_readout": "record entropy, mutual information, erasure cost",
      "state_count": 4,
      "operator_count": 3,
      "axis_count": 7,
      "boundary": "bridge rows are comparison scaffolds, not promotion gates"
    },
    {
      "engine": "szilard",
      "mode": "nonclassical_adjacent",
      "pass": true,
      "claim": "density carriers or graph tensors give a nonclassical-compatible representation",
      "geometry": "finite two-qubit system-memory protocol path",
      "entropy_readout": "record entropy, mutual information, erasure cost",
      "state_count": 4,
      "operator_count": 3,
      "axis_count": 7,
      "boundary": "density/tool witnesses are not a final QIT engine runtime"
    },
    {
      "engine": "iching_64",
      "mode": "classical",
      "pass": true,
      "claim": "finite state/operator bookkeeping with an entropy readout",
      "geometry": "six-bit hypercube Gray-cycle symbolic schedule",
      "entropy_readout": "uniform state entropy plus parity polarity",
      "state_count": 64,
      "operator_count": 64,
      "axis_count": 7,
      "boundary": "classical agreement is surface grammar, not identity"
    },
    {
      "engine": "iching_64",
      "mode": "bridge",
      "pass": true,
      "claim": "axis slots, graph/order, and proof fences connect language layers",
      "geometry": "six-bit hypercube Gray-cycle symbolic schedule",
      "entropy_readout": "uniform state entropy plus parity polarity",
      "state_count": 64,
      "operator_count": 64,
      "axis_count": 7,
      "boundary": "bridge rows are comparison scaffolds, not promotion gates"
    },
    {
      "engine": "iching_64",
      "mode": "nonclassical_adjacent",
      "pass": true,
      "claim": "density carriers or graph tensors give a nonclassical-compatible representation",
      "geometry": "six-bit hypercube Gray-cycle symbolic schedule",
      "entropy_readout": "uniform state entropy plus parity polarity",
      "state_count": 64,
      "operator_count": 64,
      "axis_count": 7,
      "boundary": "density/tool witnesses are not a final QIT engine runtime"
    }
  ],
  "shared_structure_rows": [
    {
      "slot": "finite_carrier",
      "status": "shared_with_different_cardinality",
      "evidence": {
        "carnot": 4,
        "szilard": 4,
        "iching_64": 64
      },
      "boundary": "same finite-carrier grammar, not same state space"
    },
    {
      "slot": "ordered_local_operator",
      "status": "shared_with_different_operator_language",
      "evidence": {
        "carnot": 4,
        "szilard": 3,
        "iching_64": 64
      },
      "boundary": "thermal legs, information operations, and line flips do not collapse"
    },
    {
      "slot": "dual_orientation",
      "status": "shared",
      "evidence": {
        "carnot": 2,
        "szilard": 2,
        "iching_64": 2
      },
      "boundary": "two-direction grammar is a comparison invariant only"
    },
    {
      "slot": "axis_schedule",
      "status": "shared_candidate_slots",
      "evidence": {
        "carnot": 7,
        "szilard": 7,
        "iching_64": 7
      },
      "boundary": "Ax0-Ax6 labels remain local candidate slots, not admitted axes"
    },
    {
      "slot": "entropy_gradient",
      "status": "shared_shape_different_readout",
      "evidence": {
        "carnot": "reservoir entropy plus heat/work efficiency",
        "szilard": "record entropy, mutual information, erasure cost",
        "iching_64": "uniform state entropy plus parity polarity"
      },
      "boundary": "reservoir entropy, record entropy, and parity entropy stay distinct"
    },
    {
      "slot": "nonclassical_adjacent_carrier",
      "status": "shared_tool_surface",
      "evidence": {
        "carnot": true,
        "szilard": true,
        "iching_64": true
      },
      "boundary": "qutip/qiskit/PyG witnesses do not equal QIT engine admission"
    }
  ],
  "stress_tests": {
    "all_source_rows_pass": {
      "pass": true,
      "source_pass": {
        "carnot": true,
        "szilard": true,
        "iching_64": true
      }
    },
    "all_modes_have_receipts": {
      "pass": true,
      "failed": []
    },
    "all_axis_slots_present_but_not_promoted": {
      "pass": true,
      "axis_counts": {
        "carnot": 7,
        "szilard": 7,
        "iching_64": 7
      },
      "boundary": "axis slots are candidate comparison slots only"
    },
    "z3_blocks_identity_collapse": {
      "fixed_counts": {
        "carnot": 4,
        "szilard": 4,
        "iching_64": 64
      },
      "claim": "all three rows are the same state space",
      "result": "unsat",
      "pass": true
    },
    "cvc5_blocks_identity_collapse": {
      "fixed_counts": {
        "carnot": 4,
        "szilard": 4,
        "iching_64": 64
      },
      "claim": "all three rows are the same state space",
      "result": "unsat",
      "pass": true
    },
    "graph_tensor_density_witness": {
      "nodes": 9,
      "edges": 12,
      "pyg_nodes": 9,
      "pyg_edges": 12,
      "density_dimension": 3,
      "state_count_distribution": {
        "carnot": 4,
        "szilard": 4,
        "iching_64": 64
      },
      "state_count_entropy": 0.4258484492385814,
      "qutip_trace": 1.0,
      "qiskit_trace": 1.0,
      "pass": true
    }
  },
  "graveyard_rows": [
    {
      "variant": "collapse_all_three_to_one_state_space",
      "status": "killed",
      "reason": "Carnot/Szilard four-state receipts and I Ching 64-state receipt cannot satisfy one shared state-count identity.",
      "evidence": {
        "z3": "unsat",
        "cvc5": "unsat"
      }
    },
    {
      "variant": "erase_dual_orientation",
      "status": "killed",
      "reason": "Each row has two orientation families; deleting that axis loses the engine grammar under comparison.",
      "evidence": {
        "carnot": 2,
        "szilard": 2,
        "iching_64": 2
      }
    },
    {
      "variant": "promote_symbolic_iching_to_qit_admission",
      "status": "blocked",
      "reason": "The I Ching row is symbolic and nonclassical-adjacent only; no GStack or QIT runtime receipt exists.",
      "evidence": "symbolic 64-state schedule, not QIT math or I Ching proof"
    },
    {
      "variant": "collapse_operator_languages",
      "status": "rejected",
      "reason": "Thermal legs, information operations, and line flips share ordered-local-operator grammar but remain different operators.",
      "evidence": {
        "carnot": 4,
        "szilard": 3,
        "iching_64": 64
      }
    },
    {
      "variant": "read_nonclassical_tools_as_engine_runtime",
      "status": "blocked",
      "reason": "Density and graph witnesses show compatible carriers, not a final QIT engine or admitted axis stack.",
      "evidence": {
        "carnot": true,
        "szilard": true,
        "iching_64": true
      }
    }
  ]
};
