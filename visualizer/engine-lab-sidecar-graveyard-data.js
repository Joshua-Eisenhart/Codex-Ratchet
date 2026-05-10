window.ENGINE_LAB_SIDECAR_GRAVEYARD_DATA = {
  "name": "engine_lab_sidecar_graveyard",
  "summary": {
    "all_pass": true,
    "variant_count": 6,
    "killed_count": 2,
    "survived_count": 4,
    "source_row_graveyarded_count": 0,
    "source_rows_closed": false,
    "source_sidecars_tool_integrated": false,
    "qit_or_axis_promotion_allowed": false,
    "scope_note": "Controller claim-level graveyard for engine-lab readout and topology sidecars. It separates killed readout/topology assumptions from surviving sidecar signals without graveyarding source rows or promoting QIT, GStack, axis, or runtime-engine claims."
  },
  "rows": [
    {
      "variant_id": "carnot_exact_rows_minimize_performance_distance",
      "source_row": "carnot_entropy_family_array",
      "source_receipt": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/carnot_entropy_family_array_results.json",
      "expected": "exact rows minimize performance distance relative to open rows",
      "observed": "exact performance distance is lower than the best open-row distance",
      "metrics": {
        "best_exact_distance": 1.1102230246251565e-16,
        "best_open_distance": 0.013511707719928767,
        "pass": true
      },
      "verdict": "survived",
      "next_allowed_action": "use as readout reference evidence only; do not graveyard source rows"
    },
    {
      "variant_id": "carnot_open_rows_approach_exact_performance",
      "source_row": "carnot_entropy_family_array",
      "source_receipt": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/carnot_entropy_family_array_results.json",
      "expected": "some open Carnot rows approach exact rows in performance",
      "observed": "best open performance distance is below the row-local threshold",
      "metrics": {
        "best_open_distance": 0.013511707719928767,
        "pass": true
      },
      "verdict": "survived",
      "next_allowed_action": "use as open performance proximity evidence, not closure or source-row admission"
    },
    {
      "variant_id": "carnot_performance_closure_split",
      "source_row": "carnot_entropy_family_array",
      "source_receipt": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/carnot_entropy_family_array_results.json",
      "expected": "best performance row differs from best closure row",
      "observed": "exact rows are best for both performance and closure in forward and reverse modes",
      "metrics": {
        "forward": {
          "best_performance_row": "exact_qit_forward",
          "best_closure_row": "exact_qit_forward",
          "pass": false
        },
        "reverse": {
          "best_performance_row": "exact_qit_reverse",
          "best_closure_row": "exact_qit_reverse",
          "pass": false
        }
      },
      "verdict": "killed",
      "next_allowed_action": "graveyard this negative-check claim only; keep all source rows open"
    },
    {
      "variant_id": "szilard_topology_positive_ordering",
      "source_row": "szilard_topology_entropy_array",
      "source_receipt": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/szilard_topology_entropy_array_results.json",
      "expected": "some topology has positive ordering margin",
      "observed": "asymmetric double well has the best positive margin",
      "metrics": {
        "best_topology": "asymmetric_double_well",
        "best_margin": 0.0195816888383884,
        "pass": true
      },
      "verdict": "survived",
      "next_allowed_action": "use asymmetric topology as local sidecar candidate only; do not graveyard source rows"
    },
    {
      "variant_id": "szilard_topology_changes_nonlogical_entropy",
      "source_row": "szilard_topology_entropy_array",
      "source_receipt": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/szilard_topology_entropy_array_results.json",
      "expected": "topology changes nonlogical entropy proxy",
      "observed": "spread entropy range is nonzero across topologies",
      "metrics": {
        "spread_entropy_range": 0.378558175664806,
        "pass": true
      },
      "verdict": "survived",
      "next_allowed_action": "use as topology/readout diversity evidence only; source row remains open"
    },
    {
      "variant_id": "szilard_weak_topology_exists",
      "source_row": "szilard_topology_entropy_array",
      "source_receipt": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/szilard_topology_entropy_array_results.json",
      "expected": "at least one topology remains weak for ordering",
      "observed": "worst margin is still positive rather than weak under the row-local negative test",
      "metrics": {
        "worst_margin": 0.006548442730138215,
        "pass": false
      },
      "verdict": "killed",
      "next_allowed_action": "graveyard this weak-topology claim only; do not remove wide topology"
    }
  ]
};
