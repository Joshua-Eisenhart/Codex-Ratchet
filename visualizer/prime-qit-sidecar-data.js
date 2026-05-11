window.PRIME_QIT_SIDECAR_DATA = {
  "name": "prime_qit_sidecar_probe",
  "summary": {
    "all_pass": true,
    "fixed_states_match_primes": true,
    "noncommuting_order_detected": true,
    "order_variants_keep_prime_fixed_states": true,
    "baseline_exact_match_count": 0,
    "prime_count": 18,
    "composite_count": 45,
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
    "N": 64,
    "seed": 1729,
    "index_range": [
      2,
      64
    ],
    "max_logm_dim": 96
  },
  "sidecar_evaluation": {
    "fixed_state_count": 18,
    "prime_count": 18,
    "true_positive": 18,
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
      61
    ],
    "spectral": {
      "unit_eigenvalue_count": 18,
      "spectral_gap_proxy": 1.0,
      "logm_frobenius_proxy": 196.59816181046207,
      "logm_error": null,
      "logm_skipped": false,
      "max_logm_dim": 96,
      "rank": 18
    }
  },
  "noncommuting_sieve_order_test": {
    "nonzero_commutator_count": 16,
    "max_commutator_frobenius": 4.47213595499958,
    "order_distribution_l1": {
      "ascending_vs_descending": 0.4126984126984127,
      "ascending_vs_shuffled": 0.031746031746031744,
      "descending_vs_shuffled": 0.4126984126984127
    },
    "orders": {
      "ascending": {
        "fixed_state_count": 18,
        "precision": 1.0,
        "recall": 1.0,
        "exact_fixed_state_match": true,
        "survivor_distribution": {
          "2": 0.5079365079365079,
          "3": 0.1746031746031746,
          "5": 0.06349206349206349,
          "7": 0.031746031746031744,
          "11": 0.015873015873015872,
          "13": 0.015873015873015872,
          "17": 0.015873015873015872,
          "19": 0.015873015873015872,
          "23": 0.015873015873015872,
          "29": 0.015873015873015872,
          "31": 0.015873015873015872,
          "37": 0.015873015873015872,
          "41": 0.015873015873015872,
          "43": 0.015873015873015872,
          "47": 0.015873015873015872,
          "53": 0.015873015873015872,
          "59": 0.015873015873015872,
          "61": 0.015873015873015872
        }
      },
      "descending": {
        "fixed_state_count": 18,
        "precision": 1.0,
        "recall": 1.0,
        "exact_fixed_state_match": true,
        "survivor_distribution": {
          "2": 0.30158730158730157,
          "3": 0.2222222222222222,
          "5": 0.12698412698412698,
          "7": 0.12698412698412698,
          "11": 0.015873015873015872,
          "13": 0.015873015873015872,
          "17": 0.015873015873015872,
          "19": 0.015873015873015872,
          "23": 0.015873015873015872,
          "29": 0.015873015873015872,
          "31": 0.015873015873015872,
          "37": 0.015873015873015872,
          "41": 0.015873015873015872,
          "43": 0.015873015873015872,
          "47": 0.015873015873015872,
          "53": 0.015873015873015872,
          "59": 0.015873015873015872,
          "61": 0.015873015873015872
        }
      },
      "shuffled": {
        "fixed_state_count": 18,
        "precision": 1.0,
        "recall": 1.0,
        "exact_fixed_state_match": true,
        "survivor_distribution": {
          "2": 0.5079365079365079,
          "3": 0.1746031746031746,
          "5": 0.047619047619047616,
          "7": 0.047619047619047616,
          "11": 0.015873015873015872,
          "13": 0.015873015873015872,
          "17": 0.015873015873015872,
          "19": 0.015873015873015872,
          "23": 0.015873015873015872,
          "29": 0.015873015873015872,
          "31": 0.015873015873015872,
          "37": 0.015873015873015872,
          "41": 0.015873015873015872,
          "43": 0.015873015873015872,
          "47": 0.015873015873015872,
          "53": 0.015873015873015872,
          "59": 0.015873015873015872,
          "61": 0.015873015873015872
        }
      }
    }
  },
  "prime_gap_statistics": {
    "count": 17,
    "mean_gap": 3.4705882352941178,
    "max_gap": 6.0,
    "mean_spacing_ratio": 0.5625,
    "poisson_ratio_reference": 0.3863,
    "gue_ratio_reference": 0.5996
  },
  "baselines": {
    "shuffled_absorbers": {
      "fixed_state_count": 18,
      "precision": 0.3888888888888889,
      "recall": 0.3888888888888889,
      "exact_fixed_state_match": false,
      "spectral": {
        "unit_eigenvalue_count": 18,
        "spectral_gap_proxy": 1.0,
        "logm_frobenius_proxy": 196.59816181046207,
        "logm_error": null,
        "logm_skipped": false,
        "max_logm_dim": 96,
        "rank": 18
      }
    },
    "random_survivor_map": {
      "fixed_state_count": 0,
      "precision": 0.0,
      "recall": 0.0,
      "exact_fixed_state_match": false,
      "spectral": {
        "unit_eigenvalue_count": 15,
        "spectral_gap_proxy": 1.0,
        "logm_frobenius_proxy": null,
        "logm_error": "array must not contain infs or NaNs",
        "logm_skipped": false,
        "max_logm_dim": 96,
        "rank": 43
      }
    },
    "identity_channel": {
      "fixed_state_count": 63,
      "precision": 0.2857142857142857,
      "recall": 1.0,
      "exact_fixed_state_match": false,
      "spectral": {
        "unit_eigenvalue_count": 63,
        "spectral_gap_proxy": 1.0,
        "logm_frobenius_proxy": 7.93725458595648e-09,
        "logm_error": null,
        "logm_skipped": false,
        "max_logm_dim": 96,
        "rank": 63
      }
    }
  }
};
