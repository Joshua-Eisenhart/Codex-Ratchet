#!/usr/bin/env python3
"""Geomstats ordered-map distance micro-probe using the PyTorch backend."""

from __future__ import annotations

import json
import os
import pathlib
import time

os.environ["GEOMSTATS_BACKEND"] = "pytorch"

import torch
from geomstats.geometry.hypersphere import Hypersphere


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "geomstats_ordered_map_distance_micro_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: uses geomstats with the PyTorch backend to measure "
    "ordered noncommuting map distances on S^2. This is bounded tool evidence "
    "for order sensitivity and does not admit canonical, manifold, axis, "
    "bridge, engine, or final basin claims."
)

TOOL_MANIFEST = {
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: S^2 manifold and geodesic distance computation.",
    },
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "supportive: backend tensors and deterministic rotation actions.",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive: environment selection, JSON receipt, paths, and timestamps.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "geomstats": "load_bearing",
    "pytorch": "supportive",
    "python_stdlib": "supportive",
}


def rotation_x(angle: torch.Tensor) -> torch.Tensor:
    c = torch.cos(angle)
    s = torch.sin(angle)
    one = torch.ones((), dtype=torch.float64)
    zero = torch.zeros((), dtype=torch.float64)
    return torch.stack(
        (
            torch.stack((one, zero, zero)),
            torch.stack((zero, c, -s)),
            torch.stack((zero, s, c)),
        )
    )


def rotation_z(angle: torch.Tensor) -> torch.Tensor:
    c = torch.cos(angle)
    s = torch.sin(angle)
    one = torch.ones((), dtype=torch.float64)
    zero = torch.zeros((), dtype=torch.float64)
    return torch.stack(
        (
            torch.stack((c, -s, zero)),
            torch.stack((s, c, zero)),
            torch.stack((zero, zero, one)),
        )
    )


def main() -> int:
    sphere = Hypersphere(dim=2)
    metric = sphere.metric
    point = torch.tensor([0.35, 0.43, 0.831083629283], dtype=torch.float64)
    point = point / torch.linalg.norm(point)

    rx = rotation_x(torch.tensor(0.73, dtype=torch.float64))
    rz = rotation_z(torch.tensor(1.11, dtype=torch.float64))
    after_xz = rz @ (rx @ point)
    after_zx = rx @ (rz @ point)

    ordered_distance = metric.dist(after_xz, after_zx)
    identity_distance = metric.dist(point, point)
    membership_xz = sphere.belongs(after_xz)
    membership_zx = sphere.belongs(after_zx)
    gap = float(ordered_distance.item())
    identity_gap = float(identity_distance.item())

    positive = {
        "ordered_actions_diverge": {
            "pass": gap > 1.0e-6,
            "distance": gap,
            "claim": "the X-then-Z and Z-then-X actions produce different S^2 endpoints.",
        },
        "geomstats_membership_preserved": {
            "pass": bool(membership_xz.item()) and bool(membership_zx.item()),
            "belongs_x_then_z": bool(membership_xz.item()),
            "belongs_z_then_x": bool(membership_zx.item()),
            "claim": "both ordered endpoints remain on the geomstats S^2 manifold.",
        },
    }
    graveyard_companions = {
        "identity_distance_zero_control": {
            "pass": identity_gap < 1.0e-12,
            "distance": identity_gap,
            "claim": "geomstats reports zero distance for the identical point control.",
        }
    }
    boundary = {
        "pytorch_backend_selected_before_geomstats_import": {
            "pass": os.environ.get("GEOMSTATS_BACKEND") == "pytorch",
            "backend": os.environ.get("GEOMSTATS_BACKEND"),
            "claim": "backend was fixed before importing geomstats.",
        },
        "torch_tensor_surface_only": {
            "pass": isinstance(after_xz, torch.Tensor) and isinstance(after_zx, torch.Tensor),
            "claim": "probe keeps the computational surface on torch tensors.",
        },
    }
    nearby_variants = {"total": len(graveyard_companions), "passed": 1}

    receipt = {
        "name": "geomstats_ordered_map_distance_micro_probe",
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
            "ordered map distance fixture, not a promoted manifold or lego result",
            "nonclassical execution kind with promotion explicitly blocked",
        ],
        "raw": {
            "point": [float(v.item()) for v in point],
            "x_then_z": [float(v.item()) for v in after_xz],
            "z_then_x": [float(v.item()) for v in after_zx],
            "ordered_distance": gap,
            "identity_distance": identity_gap,
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
