window.SZILARD_OPEN_ROW_CONSOLIDATION_DATA = {
  "name": "szilard_open_row_consolidation",
  "summary": {
    "all_pass": true,
    "source_row_count": 4,
    "source_negative_count": 4,
    "passing_successor_count": 4,
    "fresh_source_count": 4,
    "fresh_successor_count": 4,
    "accepted_constraint_count": 4,
    "blocked_promotion_edges": [
      "topology_to_qit_or_gstack"
    ],
    "source_rows_closed": false,
    "qit_or_axis_promotion_allowed": false,
    "gstack_promotion_allowed": false,
    "bridge_promotion_allowed": false,
    "nonclassical_admission_allowed": false,
    "visual_payload": "visualizer/szilard-open-row-consolidation-data.js",
    "scope_note": "Controller consolidation for four open Szilard rows. It preserves the source rows as negative/open evidence, accepts only successor or graveyard constraints with passing receipts, and does not promote QIT, GStack, axis, bridge, nonclassical, or runtime-engine claims."
  },
  "coupling_constraints": {
    "ordering_to_substep": {
      "allowed": true,
      "constraint": "carry nonmonotone noise/feedback response into substep ordering and reset-signal repair"
    },
    "substep_to_record_reset": {
      "allowed": true,
      "constraint": "do not collapse measurement-information bottleneck into record-survival or reset-swing claims"
    },
    "record_reset_to_topology": {
      "allowed": true,
      "constraint": "topology diversity can host surviving ordering carriers but cannot close reset-axis or admission gaps"
    },
    "topology_to_qit_or_gstack": {
      "allowed": false,
      "constraint": "no QIT, GStack, axis, bridge, nonclassical, or runtime-engine promotion follows from this lane"
    }
  },
  "rows": [
    {
      "row_id": "szilard_ordering_sensitivity",
      "source_script": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_szilard_ordering_sensitivity_sweep.py",
      "source_receipt": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/szilard_ordering_sensitivity_sweep_results.json",
      "source_all_pass": false,
      "source_receipt_fresh": true,
      "successor_script": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_szilard_ordering_nonmonotone_noise_successor.py",
      "successor_receipt": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/szilard_ordering_nonmonotone_noise_successor_results.json",
      "successor_name": "szilard_ordering_nonmonotone_noise_successor",
      "successor_all_pass": true,
      "successor_receipt_fresh": true,
      "source_preserved_negative": true,
      "successor_blocks_promotion": true,
      "survived": "local ordering signal; stronger feedback; high-noise survival as tuning clue",
      "failed_or_killed": "low-noise monotonicity and clean high-noise failure prior",
      "coupling_constraint": "ordering can couple only as nonmonotone noise/feedback evidence, not as strict monotone axis",
      "accepted": true
    },
    {
      "row_id": "szilard_substep_refinement_sweep",
      "source_script": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_szilard_substep_refinement_sweep.py",
      "source_receipt": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/szilard_substep_refinement_sweep_results.json",
      "source_all_pass": false,
      "source_receipt_fresh": true,
      "successor_script": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_szilard_substep_ordering_reset_successor.py",
      "successor_receipt": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/szilard_substep_ordering_reset_successor_results.json",
      "successor_name": "szilard_substep_ordering_reset_successor",
      "successor_all_pass": true,
      "successor_receipt_fresh": true,
      "source_preserved_negative": true,
      "successor_blocks_promotion": true,
      "survived": "ordering-margin and reset-signal refinement",
      "failed_or_killed": "measurement mutual-information high-threshold claim",
      "coupling_constraint": "substep coupling must carry measurement-information bottleneck explicitly",
      "accepted": true
    },
    {
      "row_id": "szilard_record_reset_repair_sweep",
      "source_script": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_szilard_record_reset_repair_sweep.py",
      "source_receipt": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/szilard_record_reset_repair_sweep_results.json",
      "source_all_pass": false,
      "source_receipt_fresh": true,
      "successor_script": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_szilard_record_lifetime_repair_successor.py",
      "successor_receipt": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/szilard_record_lifetime_repair_successor_results.json",
      "successor_name": "szilard_record_lifetime_repair_successor",
      "successor_all_pass": true,
      "successor_receipt_fresh": true,
      "source_preserved_negative": true,
      "successor_blocks_promotion": true,
      "survived": "repair score, record lifetime, low-noise ordering, separate reset-axis reroute",
      "failed_or_killed": "reset swing on this carrier as a direct strict target",
      "coupling_constraint": "record/reset coupling must split lifetime survival from reset-axis repair",
      "accepted": true
    },
    {
      "row_id": "szilard_topology_entropy_array",
      "source_script": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_szilard_topology_entropy_array.py",
      "source_receipt": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/szilard_topology_entropy_array_results.json",
      "source_all_pass": false,
      "source_receipt_fresh": true,
      "successor_script": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/sim_szilard_topology_positive_diversity_successor.py",
      "successor_receipt": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/szilard_topology_positive_diversity_successor_results.json",
      "successor_name": "szilard_topology_positive_diversity_successor",
      "successor_all_pass": true,
      "successor_receipt_fresh": true,
      "source_preserved_negative": true,
      "successor_blocks_promotion": true,
      "survived": "positive ordering margins across tested topology family; asymmetric carrier is best local topology",
      "failed_or_killed": "weak-topology claim",
      "coupling_constraint": "topology can couple as positive diversity evidence, not as GStack or nonclassical admission",
      "accepted": true
    }
  ]
};
