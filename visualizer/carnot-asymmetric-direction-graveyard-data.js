window.CARNOT_ASYMMETRIC_DIRECTION_GRAVEYARD_DATA = {
  "name": "carnot_asymmetric_direction_graveyard",
  "summary": {
    "all_pass": true,
    "variant_count": 10,
    "killed_count": 7,
    "survived_count": 3,
    "source_rows_closed": false,
    "qit_or_axis_promotion_allowed": false,
    "scope_note": "Controller graveyard for Carnot asymmetric isotherm sweeps. It records which forward/reverse leg-dominance hypotheses failed and which bounded negative variants survived."
  },
  "rows": [
    {
      "variant_id": "forward_asymmetric_closure_advantage",
      "source_row": "carnot_forward_asymmetric",
      "source_receipt": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/carnot_asymmetric_isotherm_sweep_results.json",
      "expected": "some asymmetric forward setting improves closure over the balanced baseline",
      "observed": "best asymmetric closure beats the best balanced closure",
      "metrics": {
        "best_closure_variance_mismatch_abs": 0.00044977673628832093,
        "best_balanced_variance_mismatch_abs": 0.0021393088120044146
      },
      "verdict": "survived",
      "next_allowed_action": "use as forward finite-time closure variant evidence only"
    },
    {
      "variant_id": "forward_high_budget_near_carnot_efficiency",
      "source_row": "carnot_forward_asymmetric",
      "source_receipt": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/carnot_asymmetric_isotherm_sweep_results.json",
      "expected": "some high-budget forward setting approaches Carnot efficiency within 0.05",
      "observed": "best high-budget efficiency distance is below the row-local bound",
      "metrics": {
        "best_efficiency_distance_to_carnot": 0.013511707719928767,
        "bound": 0.05
      },
      "verdict": "survived",
      "next_allowed_action": "use as forward finite-time efficiency variant evidence only"
    },
    {
      "variant_id": "forward_hot_heavy_closure_dominance",
      "source_row": "carnot_forward_asymmetric",
      "source_receipt": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/carnot_asymmetric_isotherm_sweep_results.json",
      "expected": "hot-heavy isotherm budgets close the forward stochastic cycle better on average",
      "observed": "cold-heavy closure mismatch mean is lower than hot-heavy mean",
      "metrics": {
        "hot_heavy_mean_variance_mismatch": 0.04489199700634758,
        "cold_heavy_mean_variance_mismatch": 0.009774097049211802
      },
      "verdict": "killed",
      "next_allowed_action": "treat cold-leg budget dominance as a forward closure variant, not as QIT admission"
    },
    {
      "variant_id": "forward_cold_leg_budget_insufficient",
      "source_row": "carnot_forward_asymmetric",
      "source_receipt": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/carnot_asymmetric_isotherm_sweep_results.json",
      "expected": "cold-leg budget alone is insufficient for best forward closure",
      "observed": "best cold-heavy closure beats best hot-heavy closure",
      "metrics": {
        "best_cold_heavy_variance_mismatch_abs": 0.00044977673628832093,
        "best_hot_heavy_variance_mismatch_abs": 0.005883953332590286
      },
      "verdict": "killed",
      "next_allowed_action": "keep as negative evidence against the original forward leg-order prior"
    },
    {
      "variant_id": "reverse_asymmetric_closure_advantage",
      "source_row": "carnot_reverse_asymmetric",
      "source_receipt": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/carnot_reverse_asymmetric_sweep_results.json",
      "expected": "some reverse asymmetric setting improves closure over balanced baseline",
      "observed": "best closure setting is balanced and equals the best balanced mismatch",
      "metrics": {
        "best_closure_variance_mismatch_abs": 0.0044596912592960725,
        "best_balanced_variance_mismatch_abs": 0.0044596912592960725
      },
      "verdict": "killed",
      "next_allowed_action": "prefer balanced reverse closure unless a new reverse carrier changes the evidence"
    },
    {
      "variant_id": "reverse_high_budget_near_carnot_cop",
      "source_row": "carnot_reverse_asymmetric",
      "source_receipt": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/carnot_reverse_asymmetric_sweep_results.json",
      "expected": "high-budget reverse setting reaches COP within 0.05 of Carnot",
      "observed": "best COP distance remains above the row-local threshold",
      "metrics": {
        "best_cop_distance_to_carnot": 0.09570592873213313,
        "bound": 0.05
      },
      "verdict": "killed",
      "next_allowed_action": "keep reverse COP as open finite-time sidecar evidence"
    },
    {
      "variant_id": "reverse_cold_heavy_closure_dominance",
      "source_row": "carnot_reverse_asymmetric",
      "source_receipt": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/carnot_reverse_asymmetric_sweep_results.json",
      "expected": "cold-heavy budgets beat hot-heavy budgets on reverse closure average",
      "observed": "hot-heavy mean mismatch is lower than cold-heavy mean mismatch",
      "metrics": {
        "cold_heavy_mean_variance_mismatch": 0.022799850197799315,
        "hot_heavy_mean_variance_mismatch": 0.02131833828759856
      },
      "verdict": "killed",
      "next_allowed_action": "treat reverse hot-heavy tendency as a variant signal, not a closure proof"
    },
    {
      "variant_id": "reverse_best_row_nonzero_return_error",
      "source_row": "carnot_reverse_asymmetric",
      "source_receipt": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/carnot_reverse_asymmetric_sweep_results.json",
      "expected": "even best reverse row still has nonzero return error above 1e-3",
      "observed": "best reverse closure row has near-zero cycle_delta_u",
      "metrics": {
        "cycle_delta_u": -8.09542095921989e-05,
        "bound": 0.001
      },
      "verdict": "killed",
      "next_allowed_action": "separate return-error closure from COP and leg-dominance failures"
    },
    {
      "variant_id": "reverse_best_row_near_zero_return_error",
      "source_row": "carnot_reverse_asymmetric",
      "source_receipt": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/carnot_reverse_asymmetric_sweep_results.json",
      "expected": "the reverse row can approach return-error closure even while COP and asymmetry claims fail",
      "observed": "best reverse closure row has cycle_delta_u within 1e-3",
      "metrics": {
        "cycle_delta_u": -8.09542095921989e-05,
        "bound": 0.001
      },
      "verdict": "survived",
      "next_allowed_action": "use as return-closure side evidence, not as reverse COP or QIT admission"
    },
    {
      "variant_id": "reverse_hot_leg_budget_insufficient",
      "source_row": "carnot_reverse_asymmetric",
      "source_receipt": "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results/carnot_reverse_asymmetric_sweep_results.json",
      "expected": "hot-leg budget alone is insufficient to optimize reverse closure",
      "observed": "best hot-heavy closure beats best cold-heavy closure",
      "metrics": {
        "best_hot_heavy_variance_mismatch_abs": 0.0068756012626213225,
        "best_cold_heavy_variance_mismatch_abs": 0.008507886240086027
      },
      "verdict": "killed",
      "next_allowed_action": "keep as negative evidence against a symmetric forward/reverse leg-order prior"
    }
  ]
};
