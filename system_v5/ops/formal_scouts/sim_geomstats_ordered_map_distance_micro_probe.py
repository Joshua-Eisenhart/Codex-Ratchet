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

SIM_ID = "geomstats_ordered_map_distance_micro_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: uses geomstats with the PyTorch backend to measure "
    "ordered noncommuting map distances on S^2. This is bounded tool evidence "
    "for order sensitivity and does not admit canonical, manifold, axis, "
    "bridge, engine, or final basin claims."
)
ROOT_CONSTRAINTS_IN_FORCE = ["F01_FINITE_CARRIER_PROBE_OPERATOR_PATH_SET", "N01_NONCOMMUTING_OR_ORDER_SENSITIVE_ACTION"]
FINITE_MAP = (
    "GeomstatsS2OrderDistance : finite S2 point plus two ordered rotations -> "
    "geomstats geodesic distance, membership checks, and wrong-structure controls"
)
DOMAIN = {
    "manifold": "geomstats Hypersphere(dim=2) with PyTorch backend",
    "carrier": "one finite torch float64 point on S2",
    "ordered_actions": ["Rz o Rx", "Rx o Rz"],
    "controls": [
        "identity distance",
        "same-axis commuting rotations",
        "off-sphere point rejected by belongs",
        "geomstats projection returns rejected point to S2",
        "flat chord distance is not used as the geodesic claim",
    ],
}
CODOMAIN_OR_OUTPUT = {
    "ordered_geodesic_gap": "finite geomstats S2 metric distance between ordered endpoints",
    "membership_flags": "geomstats belongs readouts for endpoints and controls",
    "control_gaps": "finite checks showing the claim fails or changes under wrong structures",
}

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
    rx_a = rotation_x(torch.tensor(0.31, dtype=torch.float64))
    rx_b = rotation_x(torch.tensor(0.89, dtype=torch.float64))
    same_axis_ab = rx_b @ (rx_a @ point)
    same_axis_ba = rx_a @ (rx_b @ point)
    same_axis_distance = metric.dist(same_axis_ab, same_axis_ba)
    off_sphere = 1.7 * point
    projected = sphere.projection(off_sphere)
    projected_membership = sphere.belongs(projected)
    off_sphere_membership = sphere.belongs(off_sphere)
    projected_move_distance = metric.dist(point, projected)
    flat_chord = torch.linalg.norm(after_xz - after_zx)
    membership_xz = sphere.belongs(after_xz)
    membership_zx = sphere.belongs(after_zx)
    gap = float(ordered_distance.item())
    identity_gap = float(identity_distance.item())
    same_axis_gap = float(same_axis_distance.item())
    projected_gap = float(projected_move_distance.item())
    flat_chord_gap = float(abs(float(flat_chord.item()) - gap))

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
        "geomstats_projection_recovers_off_sphere_control": {
            "pass": (not bool(off_sphere_membership.item())) and bool(projected_membership.item()),
            "off_sphere_belongs": bool(off_sphere_membership.item()),
            "projected_belongs": bool(projected_membership.item()),
            "claim": "geomstats distinguishes an invalid ambient point from its projected S2 point.",
        },
    }
    graveyard_companions = {
        "identity_distance_zero_control": {
            "pass": identity_gap < 1.0e-12,
            "distance": identity_gap,
            "claim": "geomstats reports zero distance for the identical point control.",
        },
        "same_axis_rotations_commute_control": {
            "pass": same_axis_gap < 1.0e-12,
            "distance": same_axis_gap,
            "claim": "when the ordered actions commute, the order-sensitive distance disappears.",
        },
        "flat_chord_distance_not_used_as_geodesic_claim": {
            "pass": flat_chord_gap > 1.0e-4,
            "flat_chord": float(flat_chord.item()),
            "geomstats_geodesic": gap,
            "difference": flat_chord_gap,
            "claim": "the receipt relies on geomstats geodesic distance, not a flat ambient norm.",
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
    nearby_variants = {
        "total": len(graveyard_companions),
        "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
    }

    receipt = {
        "sim_id": SIM_ID,
        "name": "geomstats_ordered_map_distance_micro_probe",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "SIM_EXECUTION_KIND": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "root_constraints_in_force": ROOT_CONSTRAINTS_IN_FORCE,
        "finite_map": FINITE_MAP,
        "domain": DOMAIN,
        "codomain_or_output": CODOMAIN_OR_OUTPUT,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
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
            "same_axis_distance": same_axis_gap,
            "off_sphere_point": [float(v.item()) for v in off_sphere],
            "projected_point": [float(v.item()) for v in projected],
            "projected_move_distance": projected_gap,
            "flat_chord_distance": float(flat_chord.item()),
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
