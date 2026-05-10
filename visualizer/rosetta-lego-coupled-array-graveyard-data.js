window.ROSETTA_LEGO_COUPLED_ARRAY_GRAVEYARD_DATA = {
  "name": "rosetta_lego_coupled_array_graveyard",
  "summary": {
    "all_pass": true,
    "variant_count": 5,
    "killed_or_blocked_count": 5,
    "proof_fences_pass": true,
    "visual_payload": "visualizer/rosetta-lego-coupled-array-graveyard-data.js",
    "scope_note": "Negative battery around rosetta_lego_coupled_array. It mutates mode coverage, entropy overlap, topology connectivity, operator mapping, and promotion status to check that the coupled array is not just trite assembly."
  },
  "variant_rows": [
    {
      "variant": "drop_one_coupling_edge",
      "mutation": "remove carnot-iching edge from the full triad graph",
      "status": "killed",
      "reason": "Coupled array requires all three pairwise Rosetta couplings; a two-edge chain is connected but no longer full pairwise coupling.",
      "evidence": {
        "edges": 2,
        "connected": true,
        "pyg_edges": 2
      },
      "survives": false
    },
    {
      "variant": "drop_two_coupling_edges",
      "mutation": "leave only one pairwise edge",
      "status": "killed",
      "reason": "A one-edge graph disconnects one engine and cannot be a triadic coupled array.",
      "evidence": {
        "edges": 1,
        "connected": false,
        "pyg_edges": 1
      },
      "survives": false
    },
    {
      "variant": "zero_entropy_overlap",
      "mutation": "set one coupling score to zero",
      "status": "killed",
      "reason": "Density weights require positive overlap on every allowed pair.",
      "evidence": {
        "score_sum_before": 2.8846153846153846,
        "min_mutated_score": 0.0
      },
      "survives": false
    },
    {
      "variant": "operator_language_identity_collapse",
      "mutation": "treat thermal legs, information operations, and line flips as one operator",
      "status": "rejected",
      "reason": "Registry permits shared ordered-operator grammar, not operator identity.",
      "evidence": {
        "claim_ceiling": "candidate_rosetta_surface_only"
      },
      "survives": false
    },
    {
      "variant": "promote_to_qit_runtime",
      "mutation": "reinterpret registry-approved coupling as QIT runtime",
      "status": "blocked",
      "reason": "The coupled array proof fences explicitly block promotion without GStack and runtime receipts.",
      "evidence": {
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
      },
      "survives": false
    }
  ],
  "proof_fences": {
    "z3_disconnected_full_coupling_unsat": {
      "claim": "a disconnected graph is still the full triadic coupled array",
      "result": "unsat",
      "pass": true
    },
    "cvc5_disconnected_full_coupling_unsat": {
      "claim": "a disconnected graph is still the full triadic coupled array",
      "result": "unsat",
      "pass": true
    }
  }
};
