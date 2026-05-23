External audit request. We need to clear Codex Ratchet sim-contract metadata debt without fake passes. Review the proposed repair tool and dry-run summary.

Tool: scripts/contract_metadata_safe_repair.py
Principle: only add module-level contract metadata. C1 classification repaired only when source already contains one classification signal: a single emitted result literal or explicit docstring phrase like classified as classical_baseline. C2/C3 missing metadata repaired from imports as conservative supportive roles. C4 divergence_log added only when classical_baseline is already present or safely inferred. No scientific logic/result code edited.

Dry-run summary:
{
  "mode": "dry_run",
  "checked": 10497,
  "actionable": 1298,
  "blocked": 10,
  "action_counts": {
    "classification": 1061,
    "divergence_log": 231,
    "tool_manifest": 147,
    "tool_depth": 89
  },
  "blocked_counts": {
    "C1_classification_missing_needs_review": 10
  }
}

Representative actionable plans:
[
  {
    "sim": "system_v4/probes/sim_a1_homotopy_motivic_filtration.py",
    "rules": [
      "C1_classification_missing"
    ],
    "actions": [
      {
        "kind": "classification",
        "value": "classical_baseline",
        "reason": "explicit_docstring_classification"
      }
    ],
    "blocked": []
  },
  {
    "sim": "system_v4/probes/sim_ade_series_cartan_det_survey.py",
    "rules": [
      "C1_classification_missing"
    ],
    "actions": [
      {
        "kind": "classification",
        "value": "classical_baseline",
        "reason": "single_emitted_result_literal"
      }
    ],
    "blocked": []
  },
  {
    "sim": "system_v4/probes/sim_affine_ade_extended_dynkin_det0.py",
    "rules": [
      "C1_classification_missing"
    ],
    "actions": [
      {
        "kind": "classification",
        "value": "classical_baseline",
        "reason": "single_emitted_result_literal"
      }
    ],
    "blocked": []
  },
  {
    "sim": "system_v4/probes/sim_arrow_of_time_l1_l3_asymmetry.py",
    "rules": [
      "C4_divergence_log_missing"
    ],
    "actions": [
      {
        "kind": "divergence_log",
        "value": "Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.",
        "reason": "classical_baseline_requires_nonempty_divergence_log"
      }
    ],
    "blocked": []
  },
  {
    "sim": "system_v4/probes/sim_assoc_bundle_associated_bundle_coupling_to_g_tower.py",
    "rules": [
      "C4_divergence_log_missing"
    ],
    "actions": [
      {
        "kind": "divergence_log",
        "value": "Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.",
        "reason": "classical_baseline_requires_nonempty_divergence_log"
      }
    ],
    "blocked": []
  },
  {
    "sim": "system_v4/probes/sim_assoc_bundle_fiber_pairwise_coupling.py",
    "rules": [
      "C1_classification_missing"
    ],
    "actions": [
      {
        "kind": "classification",
        "value": "canonical",
        "reason": "single_emitted_result_literal"
      }
    ],
    "blocked": []
  },
  {
    "sim": "system_v4/probes/sim_assoc_bundle_torch_foundation.py",
    "rules": [
      "C1_classification_missing"
    ],
    "actions": [
      {
        "kind": "classification",
        "value": "canonical",
        "reason": "single_emitted_result_literal"
      }
    ],
    "blocked": []
  },
  {
    "sim": "system_v4/probes/sim_assoc_moment_index_chern_yang_mills_ricci_spin_frame_principal_kahler_symplectic_contact_12shell_coupling_canonical.py",
    "rules": [
      "C1_classification_missing"
    ],
    "actions": [
      {
        "kind": "classification",
        "value": "classical_baseline",
        "reason": "single_emitted_result_literal"
      }
    ],
    "blocked": []
  },
  {
    "sim": "system_v4/probes/sim_autograd_eigh.py",
    "rules": [
      "C1_classification_missing",
      "C2_manifest_missing"
    ],
    "actions": [
      {
        "kind": "classification",
        "value": "canonical",
        "reason": "single_emitted_result_literal"
      },
      {
        "kind": "tool_manifest",
        "value": {
          "numpy": {
            "tried": true,
            "used": true,
            "reason": "Conservative contract metadata repair: source imports this tool; role is marked supportive pending claim-specific review."
          },
          "pytorch": {
            "tried": true,
            "used": true,
            "reason": "Conservative contract metadata repair: source imports this tool; role is marked supportive pending claim-specific review."
          }
        },
        "reason": "import_based_supportive_manifest"
      }
    ],
    "blocked": []
  },
  {
    "sim": "system_v4/probes/sim_autograd_grad_Ic_axis0.py",
    "rules": [
      "C1_classification_missing"
    ],
    "actions": [
      {
        "kind": "classification",
        "value": "canonical",
        "reason": "single_emitted_result_literal"
      }
    ],
    "blocked": []
  },
  {
    "sim": "system_v4/probes/sim_autograd_implicit_diff.py",
    "rules": [
      "C1_classification_missing",
      "C2_manifest_missing"
    ],
    "actions": [
      {
        "kind": "classification",
        "value": "canonical",
        "reason": "single_emitted_result_literal"
      },
      {
        "kind": "tool_manifest",
        "value": {
          "numpy": {
            "tried": true,
            "used": true,
            "reason": "Conservative contract metadata repair: source imports this tool; role is marked supportive pending claim-specific review."
          },
          "pytorch": {
            "tried": true,
            "used": true,
            "reason": "Conservative contract metadata repair: source imports this tool; role is marked supportive pending claim-specific review."
          }
        },
        "reason": "import_based_supportive_manifest"
      }
    ],
    "blocked": []
  },
  {
    "sim": "system_v4/probes/sim_autograd_kraus_purity.py",
    "rules": [
      "C1_classification_missing",
      "C2_manifest_missing"
    ],
    "actions": [
      {
        "kind": "classification",
        "value": "canonical",
        "reason": "single_emitted_result_literal"
      },
      {
        "kind": "tool_manifest",
        "value": {
          "numpy": {
            "tried": true,
            "used": true,
            "reason": "Conservative contract metadata repair: source imports this tool; role is marked supportive pending claim-specific review."
          },
          "pytorch": {
            "tried": true,
            "used": true,
            "reason": "Conservative contract metadata repair: source imports this tool; role is marked supportive pending claim-specific review."
          }
        },
        "reason": "import_based_supportive_manifest"
      }
    ],
    "blocked": []
  },
  {
    "sim": "system_v4/probes/sim_autograd_matrix_exp.py",
    "rules": [
      "C1_classification_missing",
      "C2_manifest_missing"
    ],
    "actions": [
      {
        "kind": "classification",
        "value": "canonical",
        "reason": "single_emitted_result_literal"
      },
      {
        "kind": "tool_manifest",
        "value": {
          "numpy": {
            "tried": true,
            "used": true,
            "reason": "Conservative contract metadata repair: source imports this tool; role is marked supportive pending claim-specific review."
          },
          "pytorch": {
            "tried": true,
            "used": true,
            "reason": "Conservative contract metadata repair: source imports this tool; role is marked supportive pending claim-specific review."
          }
        },
        "reason": "import_based_supportive_manifest"
      }
    ],
    "blocked": []
  },
  {
    "sim": "system_v4/probes/sim_autograd_ntk.py",
    "rules": [
      "C1_classification_missing",
      "C2_manifest_missing"
    ],
    "actions": [
      {
        "kind": "classification",
        "value": "canonical",
        "reason": "single_emitted_result_literal"
      },
      {
        "kind": "tool_manifest",
        "value": {
          "numpy": {
            "tried": true,
            "used": true,
            "reason": "Conservative contract metadata repair: source imports this tool; role is marked supportive pending claim-specific review."
          },
          "pytorch": {
            "tried": true,
            "used": true,
            "reason": "Conservative contract metadata repair: source imports this tool; role is marked supportive pending claim-specific review."
          }
        },
        "reason": "import_based_supportive_manifest"
      }
    ],
    "blocked": []
  },
  {
    "sim": "system_v4/probes/sim_autograd_svd.py",
    "rules": [
      "C1_classification_missing",
      "C2_manifest_missing"
    ],
    "actions": [
      {
        "kind": "classification",
        "value": "canonical",
        "reason": "single_emitted_result_literal"
      },
      {
        "kind": "tool_manifest",
        "value": {
          "numpy": {
            "tried": true,
            "used": true,
            "reason": "Conservative contract metadata repair: source imports this tool; role is marked supportive pending claim-specific review."
          },
          "pytorch": {
            "tried": true,
            "used": true,
            "reason": "Conservative contract metadata repair: source imports this tool; role is marked supportive pending claim-specific review."
          }
        },
        "reason": "import_based_supportive_manifest"
      }
    ],
    "blocked": []
  },
  {
    "sim": "system_v4/probes/sim_autograd_vfe_descent.py",
    "rules": [
      "C1_classification_missing",
      "C2_manifest_missing"
    ],
    "actions": [
      {
        "kind": "classification",
        "value": "canonical",
        "reason": "single_emitted_result_literal"
      },
      {
        "kind": "tool_manifest",
        "value": {
          "numpy": {
            "tried": true,
            "used": true,
            "reason": "Conservative contract metadata repair: source imports this tool; role is marked supportive pending claim-specific review."
          },
          "pytorch": {
            "tried": true,
            "used": true,
            "reason": "Conservative contract metadata repair: source imports this tool; role is marked supportive pending claim-specific review."
          }
        },
        "reason": "import_based_supportive_manifest"
      }
    ],
    "blocked": []
  },
  {
    "sim": "system_v4/probes/sim_axis10_entanglement_structure_bridge.py",
    "rules": [
      "C1_classification_missing"
    ],
    "actions": [
      {
        "kind": "classification",
        "value": "classical_baseline",
        "reason": "single_emitted_result_literal"
      }
    ],
    "blocked": []
  },
  {
    "sim": "system_v4/probes/sim_axis11_measurement_backaction_bridge.py",
    "rules": [
      "C1_classification_missing"
    ],
    "actions": [
      {
        "kind": "classification",
        "value": "classical_baseline",
        "reason": "single_emitted_result_literal"
      }
    ],
    "blocked": []
  },
  {
    "sim": "system_v4/probes/sim_axis12_rg_flow_scale_dependence.py",
    "rules": [
      "C1_classification_missing"
    ],
    "actions": [
      {
        "kind": "classification",
        "value": "classical_baseline",
        "reason": "single_emitted_result_literal"
      }
    ],
    "blocked": []
  },
  {
    "sim": "system_v4/probes/sim_axis1_curvature_gtower_bridge.py",
    "rules": [
      "C1_classification_missing"
    ],
    "actions": [
      {
        "kind": "classification",
        "value": "classical_baseline",
        "reason": "single_emitted_result_literal"
      }
    ],
    "blocked": []
  }
]

Blocked plans:
[
  {
    "sim": "system_v4/probes/sim_bipartite_phase_entropy_closure.py",
    "rules": [
      "C1_classification_missing"
    ],
    "actions": [],
    "blocked": [
      "C1_classification_missing_needs_review"
    ]
  },
  {
    "sim": "system_v4/probes/sim_constraint_shells_ablation_closure.py",
    "rules": [
      "C1_classification_missing"
    ],
    "actions": [],
    "blocked": [
      "C1_classification_missing_needs_review"
    ]
  },
  {
    "sim": "system_v4/probes/sim_gerbe_derived_stack_cohomology.py",
    "rules": [
      "C1_classification_missing"
    ],
    "actions": [],
    "blocked": [
      "C1_classification_missing_needs_review"
    ]
  },
  {
    "sim": "system_v4/probes/sim_integration_pymoo_gudhi_pareto_persistence.py",
    "rules": [
      "C1_classification_missing"
    ],
    "actions": [],
    "blocked": [
      "C1_classification_missing_needs_review"
    ]
  },
  {
    "sim": "system_v4/probes/sim_pent_all_five_frameworks.py",
    "rules": [
      "C1_classification_missing",
      "C2_manifest_missing",
      "C3_depth_missing"
    ],
    "actions": [
      {
        "kind": "tool_manifest",
        "value": {
          "z3": {
            "tried": true,
            "used": true,
            "reason": "Conservative contract metadata repair: source imports this tool; role is marked supportive pending claim-specific review."
          }
        },
        "reason": "import_based_supportive_manifest"
      },
      {
        "kind": "tool_depth",
        "value": {
          "z3": "supportive"
        },
        "reason": "supportive_depth_from_manifest_or_imports"
      }
    ],
    "blocked": [
      "C1_classification_missing_needs_review"
    ]
  },
  {
    "sim": "system_v4/probes/sim_quad_holodeck_igt_leviathan_fep.py",
    "rules": [
      "C1_classification_missing",
      "C2_manifest_missing",
      "C3_depth_missing"
    ],
    "actions": [
      {
        "kind": "tool_manifest",
        "value": {
          "z3": {
            "tried": true,
            "used": true,
            "reason": "Conservative contract metadata repair: source imports this tool; role is marked supportive pending claim-specific review."
          }
        },
        "reason": "import_based_supportive_manifest"
      },
      {
        "kind": "tool_depth",
        "value": {
          "z3": "supportive"
        },
        "reason": "supportive_depth_from_manifest_or_imports"
      }
    ],
    "blocked": [
      "C1_classification_missing_needs_review"
    ]
  },
  {
    "sim": "system_v4/probes/sim_quad_holodeck_igt_leviathan_sci_method.py",
    "rules": [
      "C1_classification_missing",
      "C2_manifest_missing",
      "C3_depth_missing"
    ],
    "actions": [
      {
        "kind": "tool_manifest",
        "value": {
          "z3": {
            "tried": true,
            "used": true,
            "reason": "Conservative contract metadata repair: source imports this tool; role is marked supportive pending claim-specific review."
          }
        },
        "reason": "import_based_supportive_manifest"
      },
      {
        "kind": "tool_depth",
        "value": {
          "z3": "supportive"
        },
        "reason": "supportive_depth_from_manifest_or_imports"
      }
    ],
    "blocked": [
      "C1_classification_missing_needs_review"
    ]
  },
  {
    "sim": "system_v4/probes/sim_quad_holodeck_igt_sci_method_fep.py",
    "rules": [
      "C1_classification_missing",
      "C2_manifest_missing",
      "C3_depth_missing"
    ],
    "actions": [
      {
        "kind": "tool_manifest",
        "value": {
          "z3": {
            "tried": true,
            "used": true,
            "reason": "Conservative contract metadata repair: source imports this tool; role is marked supportive pending claim-specific review."
          }
        },
        "reason": "import_based_supportive_manifest"
      },
      {
        "kind": "tool_depth",
        "value": {
          "z3": "supportive"
        },
        "reason": "supportive_depth_from_manifest_or_imports"
      }
    ],
    "blocked": [
      "C1_classification_missing_needs_review"
    ]
  },
  {
    "sim": "system_v4/probes/sim_quad_holodeck_leviathan_sci_method_fep.py",
    "rules": [
      "C1_classification_missing",
      "C2_manifest_missing",
      "C3_depth_missing"
    ],
    "actions": [
      {
        "kind": "tool_manifest",
        "value": {
          "z3": {
            "tried": true,
            "used": true,
            "reason": "Conservative contract metadata repair: source imports this tool; role is marked supportive pending claim-specific review."
          }
        },
        "reason": "import_based_supportive_manifest"
      },
      {
        "kind": "tool_depth",
        "value": {
          "z3": "supportive"
        },
        "reason": "supportive_depth_from_manifest_or_imports"
      }
    ],
    "blocked": [
      "C1_classification_missing_needs_review"
    ]
  },
  {
    "sim": "system_v4/probes/sim_quad_igt_leviathan_sci_method_fep.py",
    "rules": [
      "C1_classification_missing",
      "C2_manifest_missing",
      "C3_depth_missing"
    ],
    "actions": [
      {
        "kind": "tool_manifest",
        "value": {
          "z3": {
            "tried": true,
            "used": true,
            "reason": "Conservative contract metadata repair: source imports this tool; role is marked supportive pending claim-specific review."
          }
        },
        "reason": "import_based_supportive_manifest"
      },
      {
        "kind": "tool_depth",
        "value": {
          "z3": "supportive"
        },
        "reason": "supportive_depth_from_manifest_or_imports"
      }
    ],
    "blocked": [
      "C1_classification_missing_needs_review"
    ]
  }
]

Question: Is it safe to apply this repair script to the actionable 1298 files, then rerun contract lint? Identify any overclaim/fake-pass risk and any guard that must be added before applying. Keep concise.