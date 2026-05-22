#!/usr/bin/env python3
"""e3nn noncommuting irrep action micro-probe."""

from __future__ import annotations

import json
import pathlib
import time

import torch
from e3nn import o3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "e3nn_noncommuting_irrep_action_micro_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: uses e3nn finite l=1 irrep rotation matrices to show "
    "two ordered SO(3) actions differ on a typed feature. This is bounded "
    "irrep-action evidence only; it does not admit canonical, manifold, axis, "
    "bridge, engine, or final basin claims."
)

TOOL_MANIFEST = {
    "e3nn": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: constructs finite l=1 irrep actions with o3.Irrep.D_from_angles.",
    },
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "supportive: tensor arithmetic and norm checks for the irrep feature.",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive: JSON receipt, path handling, and timestamps.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "e3nn": "load_bearing",
    "pytorch": "supportive",
    "python_stdlib": "supportive",
}


def irrep_rotation(alpha: float, beta: float, gamma: float) -> torch.Tensor:
    irrep = o3.Irrep("1e")
    return irrep.D_from_angles(
        torch.tensor(alpha, dtype=torch.float64),
        torch.tensor(beta, dtype=torch.float64),
        torch.tensor(gamma, dtype=torch.float64),
    )


def main() -> int:
    action_a = irrep_rotation(0.0, 0.62, 0.0)
    action_b = irrep_rotation(1.07, 0.0, 0.0)
    feature = torch.tensor([0.41, -0.27, 0.871033868], dtype=torch.float64)
    feature = feature / torch.linalg.norm(feature)

    after_ab = action_b @ (action_a @ feature)
    after_ba = action_a @ (action_b @ feature)
    commutator_feature = (action_b @ action_a - action_a @ action_b) @ feature
    ordered_gap = float(torch.linalg.norm(after_ab - after_ba).item())
    commutator_gap = float(torch.linalg.norm(commutator_feature).item())
    norm_ab = float(torch.linalg.norm(after_ab).item())
    norm_ba = float(torch.linalg.norm(after_ba).item())

    identity = torch.eye(3, dtype=torch.float64)
    identity_gap = float(torch.linalg.norm((identity @ feature) - feature).item())

    positive = {
        "ordered_irrep_actions_diverge": {
            "pass": ordered_gap > 1.0e-6,
            "ordered_gap": ordered_gap,
            "claim": "finite l=1 irrep actions A then B and B then A differ on the same typed feature.",
        },
        "commutator_action_nonzero": {
            "pass": commutator_gap > 1.0e-6,
            "commutator_gap": commutator_gap,
            "claim": "the matrix commutator has nonzero action on the probe feature.",
        },
        "irrep_action_preserves_feature_norm": {
            "pass": abs(norm_ab - 1.0) < 1.0e-10 and abs(norm_ba - 1.0) < 1.0e-10,
            "norm_after_ab": norm_ab,
            "norm_after_ba": norm_ba,
            "claim": "both ordered e3nn irrep actions preserve the l=1 feature norm.",
        },
    }
    graveyard_companions = {
        "identity_action_zero_gap_control": {
            "pass": identity_gap < 1.0e-12,
            "identity_gap": identity_gap,
            "claim": "identity action leaves the same feature unchanged.",
        }
    }
    boundary = {
        "finite_l1_irrep_only": {
            "pass": True,
            "claim": "evidence is bounded to one finite l=1 e3nn irrep action fixture.",
        },
        "torch_tensor_surface_only": {
            "pass": isinstance(after_ab, torch.Tensor) and isinstance(after_ba, torch.Tensor),
            "claim": "probe keeps the computational surface on torch tensors.",
        },
    }
    nearby_variants = {"total": len(graveyard_companions), "passed": 1}

    receipt = {
        "name": "e3nn_noncommuting_irrep_action_micro_probe",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "classification": CLASSIFICATION,
        "SIM_EXECUTION_KIND": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": [
            "new v5 formal scout receipt only",
            "finite irrep action fixture, not a promoted equivariant model or lego result",
            "nonclassical execution kind with promotion explicitly blocked",
        ],
        "raw": {
            "feature": [float(v.item()) for v in feature],
            "after_ab": [float(v.item()) for v in after_ab],
            "after_ba": [float(v.item()) for v in after_ba],
            "ordered_gap": ordered_gap,
            "commutator_gap": commutator_gap,
        },
        "blockers": [],
        "all_pass": all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values()),
    }

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {OUT_PATH}")
    print(f"all_pass={receipt['all_pass']}")
    return 0 if receipt["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
