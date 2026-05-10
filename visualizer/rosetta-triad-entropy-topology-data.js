window.ROSETTA_TRIAD_ENTROPY_TOPOLOGY_DATA = {
  "name": "rosetta_triad_entropy_topology_sweep",
  "summary": {
    "all_pass": true,
    "engine_count": 3,
    "entropy_family_count": 9,
    "topology_row_count": 3,
    "graveyard_row_count": 4,
    "topology_signature_collapse_blocked": true,
    "visual_payload": "visualizer/rosetta-triad-entropy-topology-data.js",
    "scope_note": "Rosetta triad entropy/topology sweep over Carnot, Szilard, and I Ching-64. It applies shared entropy families and graph/topology signatures to the three existing receipts. It is comparison evidence only, not QIT admission."
  },
  "entropy_rows": [
    {
      "engine": "carnot",
      "support_size": 4,
      "distribution": [
        0.16288976568198069,
        0.33711023431801934,
        0.33711023431801934,
        0.16288976568198069
      ],
      "entropy_family": {
        "shannon": 1.3242965742546695,
        "renyi_0_5": 1.3544582981863065,
        "renyi_2": 1.2717065699203571,
        "renyi_inf_proxy": 1.0873452973156428,
        "tsallis_0_5": 1.93683196333755,
        "tsallis_2": 0.7196472283082391,
        "min_entropy": 1.0873452973156428,
        "max_entropy": 1.3862943611198906,
        "purity": 0.2803527716917609
      },
      "density_entropy_checks": {
        "scipy_vn": 1.3242965742546655,
        "qutip_vn": 1.3242965742546693,
        "torch_shannon": 1.3242965742546695,
        "qiskit_trace": 1.0,
        "qutip_trace": 1.0,
        "pass": true
      },
      "family_pass": true
    },
    {
      "engine": "szilard",
      "support_size": 4,
      "distribution": [
        0.33333333333317305,
        0.33333333333317305,
        0.33333333333317305,
        4.808983469620628e-13
      ],
      "entropy_family": {
        "shannon": 1.098612288681702,
        "renyi_0_5": 1.098613089415741,
        "renyi_2": 1.0986122886690712,
        "renyi_inf_proxy": 1.0986122886685905,
        "tsallis_0_5": 1.4641030020736139,
        "tsallis_2": 0.6666666666669872,
        "min_entropy": 1.0986122886685905,
        "max_entropy": 1.3862943611198906,
        "purity": 0.3333333333330128
      },
      "density_entropy_checks": {
        "scipy_vn": 1.0986122886816982,
        "qutip_vn": 1.098612288681702,
        "torch_shannon": 1.098612288681702,
        "qiskit_trace": 1.0,
        "qutip_trace": 1.0,
        "pass": true
      },
      "family_pass": true
    },
    {
      "engine": "iching_64",
      "support_size": 64,
      "distribution": [
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625,
        0.015625
      ],
      "entropy_family": {
        "shannon": 4.1588830833596715,
        "renyi_0_5": 4.1588830833596715,
        "renyi_2": 4.1588830833596715,
        "renyi_inf_proxy": 4.1588830833596715,
        "tsallis_0_5": 14.0,
        "tsallis_2": 0.984375,
        "min_entropy": 4.1588830833596715,
        "max_entropy": 4.1588830833596715,
        "purity": 0.015625
      },
      "density_entropy_checks": {
        "scipy_vn": 4.158883083359607,
        "qutip_vn": 4.158883083359677,
        "torch_shannon": 4.1588830833596715,
        "qiskit_trace": 1.0,
        "qutip_trace": 1.0,
        "pass": true
      },
      "family_pass": true
    }
  ],
  "topology_rows": [
    {
      "engine": "carnot",
      "nodes": 4,
      "edges": 4,
      "beta0_laplacian": 1,
      "beta1_cycle_rank": 1,
      "euler_characteristic": 0,
      "laplacian_zero_eigenvalues": 1,
      "laplacian_spectral_gap": 2.0,
      "pyg_nodes": 4,
      "pyg_edges": 4,
      "xgi_edges": 4,
      "gudhi_simplices": 8,
      "toponetx_shape": [
        4,
        4,
        0
      ],
      "topology_pass": true
    },
    {
      "engine": "szilard",
      "nodes": 4,
      "edges": 3,
      "beta0_laplacian": 1,
      "beta1_cycle_rank": 0,
      "euler_characteristic": 1,
      "laplacian_zero_eigenvalues": 1,
      "laplacian_spectral_gap": 0.585786437626905,
      "pyg_nodes": 4,
      "pyg_edges": 3,
      "xgi_edges": 4,
      "gudhi_simplices": 7,
      "toponetx_shape": [
        4,
        3,
        0
      ],
      "topology_pass": true
    },
    {
      "engine": "iching_64",
      "nodes": 64,
      "edges": 64,
      "beta0_laplacian": 1,
      "beta1_cycle_rank": 1,
      "euler_characteristic": 0,
      "laplacian_zero_eigenvalues": 1,
      "laplacian_spectral_gap": 0.00963054665560548,
      "pyg_nodes": 64,
      "pyg_edges": 64,
      "xgi_edges": 64,
      "gudhi_simplices": 128,
      "toponetx_shape": [
        64,
        64,
        0
      ],
      "topology_pass": true
    }
  ],
  "stress_tests": {
    "all_entropy_families_pass": {
      "pass": true,
      "failed": []
    },
    "all_topology_rows_pass": {
      "pass": true,
      "failed": []
    },
    "z3_blocks_topology_signature_collapse": {
      "claim": "all three topology signatures are identical in node count and cycle rank",
      "signatures": {
        "carnot": {
          "nodes": 4,
          "beta1": 1
        },
        "szilard": {
          "nodes": 4,
          "beta1": 0
        },
        "iching_64": {
          "nodes": 64,
          "beta1": 1
        }
      },
      "result": "unsat",
      "pass": true
    },
    "cvc5_blocks_topology_signature_collapse": {
      "claim": "all three topology signatures are identical in node count and cycle rank",
      "signatures": {
        "carnot": {
          "nodes": 4,
          "beta1": 1
        },
        "szilard": {
          "nodes": 4,
          "beta1": 0
        },
        "iching_64": {
          "nodes": 64,
          "beta1": 1
        }
      },
      "result": "unsat",
      "pass": true
    }
  },
  "graveyard_rows": [
    {
      "variant": "one_entropy_language_fits_all",
      "status": "rejected",
      "reason": "The same formulas run everywhere, but each engine uses a different source distribution and readout.",
      "evidence": {
        "carnot": 4,
        "szilard": 4,
        "iching_64": 64
      }
    },
    {
      "variant": "all_three_have_same_topology_signature",
      "status": "killed",
      "reason": "Carnot is a 4-cycle, Szilard is a 4-path, and I Ching is a 64-cycle.",
      "evidence": {
        "z3": "unsat",
        "cvc5": "unsat"
      }
    },
    {
      "variant": "cycle_rank_alone_identifies_engine",
      "status": "rejected",
      "reason": "Carnot and I Ching both have cycle-rank 1 but different cardinality and operator language.",
      "evidence": {
        "carnot": {
          "nodes": 4,
          "beta1": 1
        },
        "szilard": {
          "nodes": 4,
          "beta1": 0
        },
        "iching_64": {
          "nodes": 64,
          "beta1": 1
        }
      }
    },
    {
      "variant": "density_entropy_witness_implies_qit_runtime",
      "status": "blocked",
      "reason": "Density witnesses validate distributions only; they do not provide GStack, operator stack, or QIT admission.",
      "evidence": {
        "carnot": true,
        "szilard": true,
        "iching_64": true
      }
    }
  ]
};
