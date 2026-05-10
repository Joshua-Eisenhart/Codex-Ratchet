window.PRIME_QIT_SIDECAR_DATA = {
  "name": "prime_qit_sidecar_probe",
  "summary": {
    "all_pass": true,
    "fixed_states_match_primes": true,
    "noncommuting_order_detected": true,
    "order_variants_keep_prime_fixed_states": true,
    "baseline_exact_match_count": 0,
    "prime_count": 25,
    "composite_count": 71,
    "claim_ceiling": "sidecar_probe_candidate_prior_only",
    "visual_payload": "visualizer/prime-qit-sidecar-data.js",
    "scope_note": "Finite-N prime/composite survivor probe.  The channel is built from divisibility transitions, prime labels are used only for evaluation, and the result is evidence fuel only: no RH, PNT, zeta, QIT, GStack, axis, or nonclassical admission claim.",
    "recommendation": "retool",
    "recommendation_reason": "bounded diagnostic passes fixed-state and noncommuting-order checks, but remains sidecar evidence and needs stronger baselines before promotion",
    "logm_skipped_channels": {
      "sidecar": false,
      "orders": {
        "ascending": false,
        "descending": false,
        "shuffled": false
      },
      "baselines": {
        "shuffled_absorbers": false,
        "random_survivor_map": false,
        "identity_channel": false
      }
    },
    "logm_skipped_count": 0
  },
  "parameters": {
    "N": 97,
    "seed": 1729,
    "index_range": [
      2,
      97
    ],
    "max_logm_dim": 96
  },
  "sidecar_evaluation": {
    "fixed_state_count": 25,
    "prime_count": 25,
    "true_positive": 25,
    "false_positive": 0,
    "false_negative": 0,
    "precision": 1.0,
    "recall": 1.0,
    "exact_fixed_state_match": true,
    "fixed_state_sample": [
      2,
      3,
      5,
      7,
      11,
      13,
      17,
      19,
      23,
      29,
      31,
      37,
      41,
      43,
      47,
      53,
      59,
      61,
      67,
      71,
      73,
      79,
      83,
      89
    ],
    "spectral": {
      "unit_eigenvalue_count": 25,
      "spectral_gap_proxy": 1.0,
      "logm_frobenius_proxy": 246.9462129081255,
      "logm_error": null,
      "logm_skipped": false,
      "max_logm_dim": 96,
      "rank": 25
    }
  },
  "noncommuting_sieve_order_test": {
    "nonzero_commutator_count": 22,
    "max_commutator_frobenius": 5.656854249492381,
    "order_distribution_l1": {
      "ascending_vs_descending": 0.3958333333333337,
      "ascending_vs_shuffled": 0.1875000000000001,
      "descending_vs_shuffled": 0.2291666666666669
    },
    "orders": {
      "ascending": {
        "fixed_state_count": 25,
        "precision": 1.0,
        "recall": 1.0,
        "exact_fixed_state_match": true,
        "survivor_distribution": {
          "2": 0.5000000000000003,
          "3": 0.16666666666666663,
          "5": 0.07291666666666666,
          "7": 0.041666666666666664,
          "11": 0.010416666666666666,
          "13": 0.010416666666666666,
          "17": 0.010416666666666666,
          "19": 0.010416666666666666,
          "23": 0.010416666666666666,
          "29": 0.010416666666666666,
          "31": 0.010416666666666666,
          "37": 0.010416666666666666,
          "41": 0.010416666666666666,
          "43": 0.010416666666666666,
          "47": 0.010416666666666666,
          "53": 0.010416666666666666,
          "59": 0.010416666666666666,
          "61": 0.010416666666666666,
          "67": 0.010416666666666666,
          "71": 0.010416666666666666,
          "73": 0.010416666666666666,
          "79": 0.010416666666666666,
          "83": 0.010416666666666666,
          "89": 0.010416666666666666,
          "97": 0.010416666666666666
        }
      },
      "descending": {
        "fixed_state_count": 25,
        "precision": 1.0,
        "recall": 1.0,
        "exact_fixed_state_match": true,
        "survivor_distribution": {
          "2": 0.3020833333333333,
          "3": 0.25,
          "5": 0.11458333333333333,
          "7": 0.11458333333333331,
          "11": 0.010416666666666666,
          "13": 0.010416666666666666,
          "17": 0.010416666666666666,
          "19": 0.010416666666666666,
          "23": 0.010416666666666666,
          "29": 0.010416666666666666,
          "31": 0.010416666666666666,
          "37": 0.010416666666666666,
          "41": 0.010416666666666666,
          "43": 0.010416666666666666,
          "47": 0.010416666666666666,
          "53": 0.010416666666666666,
          "59": 0.010416666666666666,
          "61": 0.010416666666666666,
          "67": 0.010416666666666666,
          "71": 0.010416666666666666,
          "73": 0.010416666666666666,
          "79": 0.010416666666666666,
          "83": 0.010416666666666666,
          "89": 0.010416666666666666,
          "97": 0.010416666666666666
        }
      },
      "shuffled": {
        "fixed_state_count": 25,
        "precision": 1.0,
        "recall": 1.0,
        "exact_fixed_state_match": true,
        "survivor_distribution": {
          "2": 0.41666666666666685,
          "3": 0.24999999999999994,
          "5": 0.06249999999999999,
          "7": 0.05208333333333333,
          "11": 0.010416666666666666,
          "13": 0.010416666666666666,
          "17": 0.010416666666666666,
          "19": 0.010416666666666666,
          "23": 0.010416666666666666,
          "29": 0.010416666666666666,
          "31": 0.010416666666666666,
          "37": 0.010416666666666666,
          "41": 0.010416666666666666,
          "43": 0.010416666666666666,
          "47": 0.010416666666666666,
          "53": 0.010416666666666666,
          "59": 0.010416666666666666,
          "61": 0.010416666666666666,
          "67": 0.010416666666666666,
          "71": 0.010416666666666666,
          "73": 0.010416666666666666,
          "79": 0.010416666666666666,
          "83": 0.010416666666666666,
          "89": 0.010416666666666666,
          "97": 0.010416666666666666
        }
      }
    }
  },
  "prime_gap_statistics": {
    "count": 24,
    "mean_gap": 3.9583333333333335,
    "max_gap": 8.0,
    "mean_spacing_ratio": 0.5615942028985507,
    "poisson_ratio_reference": 0.3863,
    "gue_ratio_reference": 0.5996
  },
  "baselines": {
    "shuffled_absorbers": {
      "fixed_state_count": 25,
      "precision": 0.32,
      "recall": 0.32,
      "exact_fixed_state_match": false,
      "spectral": {
        "unit_eigenvalue_count": 25,
        "spectral_gap_proxy": 1.0,
        "logm_frobenius_proxy": 246.94621290812552,
        "logm_error": null,
        "logm_skipped": false,
        "max_logm_dim": 96,
        "rank": 25
      }
    },
    "random_survivor_map": {
      "fixed_state_count": 0,
      "precision": 0.0,
      "recall": 0.0,
      "exact_fixed_state_match": false,
      "spectral": {
        "unit_eigenvalue_count": 3,
        "spectral_gap_proxy": 1.0,
        "logm_frobenius_proxy": null,
        "logm_error": "array must not contain infs or NaNs",
        "logm_skipped": false,
        "max_logm_dim": 96,
        "rank": 63
      }
    },
    "identity_channel": {
      "fixed_state_count": 96,
      "precision": 0.2604166666666667,
      "recall": 1.0,
      "exact_fixed_state_match": false,
      "spectral": {
        "unit_eigenvalue_count": 96,
        "spectral_gap_proxy": 1.0,
        "logm_frobenius_proxy": 9.797959776920493e-09,
        "logm_error": null,
        "logm_skipped": false,
        "max_logm_dim": 96,
        "rank": 96
      }
    }
  }
};
