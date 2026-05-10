window.PRIME_QIT_SIDECAR_GRAVEYARD_DATA = {
  "name": "prime_qit_sidecar_graveyard",
  "summary": {
    "all_pass": true,
    "variant_count": 6,
    "killed_or_control_count": 5,
    "reference_survives": true,
    "hardcoded_prime_control_killed": true,
    "random_control_killed": true,
    "order_variant_detected": true,
    "claim_ceiling": "sidecar_graveyard_control_only",
    "recommendation": "retool",
    "visual_payload": "visualizer/prime-qit-sidecar-graveyard-data.js",
    "scope_note": "Negative/control battery around prime_qit_sidecar_probe. It checks that prime-like survivor behavior is not accepted when primes are hardcoded, when survivors are random, when noncommuting order is erased, or when order sensitivity changes the composite-to-survivor distribution. No RH, PNT, zeta, QIT, GStack, axis, or nonclassical claim is promoted."
  },
  "variants": [
    {
      "name": "reference_divisibility_channel",
      "hardcoded_prime_use_in_construction": false,
      "fixed_state_count": 54,
      "prime_count": 54,
      "exact_fixed_state_match": true,
      "false_positive_sample": [],
      "false_negative_sample": [],
      "rank": 54,
      "unit_eigenvalue_count": 54,
      "graveyard_status": "survives_as_reference"
    },
    {
      "name": "forbidden_hardcoded_prime_lookup",
      "hardcoded_prime_use_in_construction": true,
      "fixed_state_count": 54,
      "prime_count": 54,
      "exact_fixed_state_match": true,
      "false_positive_sample": [],
      "false_negative_sample": [],
      "rank": 54,
      "unit_eigenvalue_count": 54,
      "graveyard_status": "killed_or_control"
    },
    {
      "name": "random_survivor_control",
      "hardcoded_prime_use_in_construction": false,
      "fixed_state_count": 54,
      "prime_count": 54,
      "exact_fixed_state_match": false,
      "false_positive_sample": [
        14,
        15,
        26,
        27,
        39,
        42,
        58,
        68,
        70,
        78,
        80,
        81
      ],
      "false_negative_sample": [
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
        37
      ],
      "rank": 54,
      "unit_eigenvalue_count": 54,
      "graveyard_status": "killed_or_control"
    },
    {
      "name": "commutative_projection_control",
      "hardcoded_prime_use_in_construction": false,
      "fixed_state_count": 54,
      "prime_count": 54,
      "exact_fixed_state_match": true,
      "false_positive_sample": [],
      "false_negative_sample": [],
      "rank": 54,
      "unit_eigenvalue_count": 54,
      "graveyard_status": "killed_or_control"
    },
    {
      "name": "ascending_ordered_divisor_control",
      "hardcoded_prime_use_in_construction": false,
      "fixed_state_count": 54,
      "prime_count": 54,
      "exact_fixed_state_match": true,
      "false_positive_sample": [],
      "false_negative_sample": [],
      "rank": 54,
      "unit_eigenvalue_count": 54,
      "graveyard_status": "killed_or_control"
    },
    {
      "name": "descending_ordered_divisor_control",
      "hardcoded_prime_use_in_construction": false,
      "fixed_state_count": 54,
      "prime_count": 54,
      "exact_fixed_state_match": true,
      "false_positive_sample": [],
      "false_negative_sample": [],
      "rank": 54,
      "unit_eigenvalue_count": 54,
      "graveyard_status": "killed_or_control"
    }
  ],
  "order_distribution_l1": {
    "reference_vs_ascending": 0.0,
    "ascending_vs_descending": 0.5254901960784313,
    "reference_vs_descending": 0.5254901960784313
  }
};
