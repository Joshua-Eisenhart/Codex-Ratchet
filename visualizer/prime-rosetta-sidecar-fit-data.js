window.PRIME_ROSETTA_SIDECAR_FIT_DATA = {
  "name": "prime_rosetta_sidecar_fit",
  "summary": {
    "all_pass": true,
    "fit_count": 3,
    "all_fits_diagnostic_only": true,
    "max_fit": 0.5677268648857039,
    "min_fit": 0.55804360876269,
    "claim_ceiling": "sidecar_fit_diagnostic_only",
    "recommendation": "retool",
    "visual_payload": "visualizer/prime-rosetta-sidecar-fit-data.js",
    "scope_note": "Diagnostic Rosetta fit for the bounded prime sidecar. It compares finite survivor/order/control signatures against the current engine lego registry without admitting prime/Riemann, QIT, GStack, axes, bridge, or nonclassical claims."
  },
  "fits": [
    {
      "lego_id": "carnot",
      "cosine_fit": 0.5612107974092314,
      "scipy_cosine_fit": 0.5612107974092314,
      "fit_delta": 0.0,
      "allowed_next": false,
      "status": "diagnostic_sidecar_only",
      "reason": "Prime sidecar has no prime proof, QIT gate, GStack gate, or axis admission."
    },
    {
      "lego_id": "szilard",
      "cosine_fit": 0.55804360876269,
      "scipy_cosine_fit": 0.55804360876269,
      "fit_delta": 0.0,
      "allowed_next": false,
      "status": "diagnostic_sidecar_only",
      "reason": "Prime sidecar has no prime proof, QIT gate, GStack gate, or axis admission."
    },
    {
      "lego_id": "iching_64",
      "cosine_fit": 0.5677268648857039,
      "scipy_cosine_fit": 0.5677268648857039,
      "fit_delta": 0.0,
      "allowed_next": false,
      "status": "diagnostic_sidecar_only",
      "reason": "Prime sidecar has no prime proof, QIT gate, GStack gate, or axis admission."
    }
  ],
  "fit_graph": {
    "nodes": 4,
    "edges": 3,
    "weighted_edges": [
      {
        "left": "prime_sidecar",
        "right": "carnot",
        "weight": 0.5612107974092314
      },
      {
        "left": "prime_sidecar",
        "right": "szilard",
        "weight": 0.55804360876269
      },
      {
        "left": "prime_sidecar",
        "right": "iching_64",
        "weight": 0.5677268648857039
      }
    ]
  }
};
