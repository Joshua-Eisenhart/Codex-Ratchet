#!/usr/bin/env python3
"""Geomstats S2 distance readout for Hopf fiber and base loops."""

from __future__ import annotations

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import json
import math
from pathlib import Path

import numpy as np
from geomstats.geometry.hypersphere import Hypersphere
from receipt_boundary import apply_default_receipt_boundary


NAME = "geomstats_hopf_projected_fiber_base_sphere_distance"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": "computes intrinsic S2 metric distances between Bloch readouts projected from declared Hopf-coordinate paths",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "samples Hopf path coordinates and computes Bloch projection arrays",
    },
}
TOOL_INTEGRATION_DEPTH = {"geomstats": "load_bearing", "numpy": "supportive"}

S2 = Hypersphere(dim=2)


def bloch(theta: float, phi: float) -> np.ndarray:
    return np.array(
        [
            math.sin(theta) * math.cos(phi),
            math.sin(theta) * math.sin(phi),
            math.cos(theta),
        ],
        dtype=float,
    )


def intrinsic_path_metrics(points: list[np.ndarray]) -> dict[str, float | list[float]]:
    step_distances = [
        float(S2.metric.dist(points[idx], points[idx + 1]))
        for idx in range(len(points) - 1)
    ]
    displacements = [float(S2.metric.dist(points[0], point)) for point in points]
    return {
        "intrinsic_path_length": float(sum(step_distances)),
        "intrinsic_displacement_from_start": float(max(displacements)),
        "start_point": [float(value) for value in points[0]],
        "end_point": [float(value) for value in points[-1]],
    }


def sample_inner_loop(theta: float, phi: float, samples: int) -> list[np.ndarray]:
    return [bloch(theta, phi) for _ in np.linspace(0.0, 2.0 * math.pi, samples)]


def sample_outer_loop(theta: float, samples: int) -> list[np.ndarray]:
    return [bloch(theta, phi) for phi in np.linspace(0.0, 2.0 * math.pi, samples)]


def survives(inner: dict[str, object], outer: dict[str, object]) -> bool:
    return bool(
        inner["intrinsic_displacement_from_start"] < 1e-9
        and inner["intrinsic_path_length"] < 1e-9
        and outer["intrinsic_displacement_from_start"] > 1.0
        and outer["intrinsic_path_length"] > 5.0
    )


def run_positive() -> dict[str, object]:
    samples = 129
    theta = math.pi / 3.0
    inner = intrinsic_path_metrics(sample_inner_loop(theta=theta, phi=math.pi / 5.0, samples=samples))
    outer = intrinsic_path_metrics(sample_outer_loop(theta=theta, samples=samples))
    return {
        "samples": samples,
        "theta": theta,
        "inner_loop": inner,
        "outer_loop": outer,
        "survives_geomstats_sphere_distance": survives(inner, outer),
    }


def run_graveyards() -> dict[str, object]:
    samples = 129
    theta = math.pi / 3.0
    inner = intrinsic_path_metrics(sample_inner_loop(theta=theta, phi=math.pi / 5.0, samples=samples))
    outer = intrinsic_path_metrics(sample_outer_loop(theta=theta, samples=samples))
    pole_outer = intrinsic_path_metrics(sample_outer_loop(theta=0.0, samples=samples))
    ambient_outer_chord = float(np.linalg.norm(np.asarray(outer["start_point"]) - np.asarray(outer["end_point"])))
    return {
        "both_paths_inner_collapses_distinction": {
            "candidate_passed": survives(inner, inner),
            "expected": False,
            "passed": survives(inner, inner) is False,
        },
        "both_paths_outer_collapses_distinction": {
            "candidate_passed": survives(outer, outer),
            "expected": False,
            "passed": survives(outer, outer) is False,
        },
        "outer_loop_at_pole_degenerates": {
            "intrinsic_displacement_from_start": pole_outer["intrinsic_displacement_from_start"],
            "expected_collapse": True,
            "passed": bool(pole_outer["intrinsic_displacement_from_start"] < 1e-9),
        },
        "ambient_start_end_chord_hides_closed_outer_path": {
            "ambient_start_end_chord": ambient_outer_chord,
            "intrinsic_path_length": outer["intrinsic_path_length"],
            "chord_collapses_closed_path": bool(ambient_outer_chord < 1e-9),
            "passed": bool(ambient_outer_chord < 1e-9 and outer["intrinsic_path_length"] > 5.0),
        },
    }


def main() -> int:
    positive = run_positive()
    graveyards = run_graveyards()
    all_pass = bool(
        positive["survives_geomstats_sphere_distance"]
        and all(row["passed"] for row in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "Geomstats S2 distance readout baseline for declared projected Hopf-coordinate paths only; no full "
            "S3 bundle, physical fiber/base loop independence, QIT, GStack, axis, bridge, nonclassical, "
            "target-system, or full geometric-constraint-manifold admission"
        ),
        "next_lego_target": "declared_fiber_base_coordinate_readout_baseline",
        "promotion_condition": (
            "May only support later manifold/path planning after independent carrier and operator-evolution receipts "
            "reproduce the same distinction with physical graveyards."
        ),
        "demotion_condition": (
            "Demote if geomstats intrinsic S2 distances vary on the fiber projected path, fail to detect the outer "
            "projected path away from degeneracy, or if same-path/pole/ambient-chord graveyards do not collapse."
        ),
        "blocked_until": "blocked from target-system claims until fuller carrier/topology and physical-evolution fixtures exist",
        "out_of_scope": [
            "No full Hopf bundle implementation.",
            "No Lindblad evolution, Hamiltonian dynamics, or target-system admission.",
            "No QIT, GStack, axis, bridge, or nonclassical admission.",
            "No claim that flux is represented.",
        ],
        "divergence_log": (
            "This is a geomstats intrinsic-distance baseline on a projected S2 readout. It does not simulate the "
            "full carrier bundle, physical loop dynamics, or target geometric constraint manifold."
        ),
        "operation_sequence": [
            "project declared Hopf-style carrier coordinates to S2 Bloch readout points",
            "sample an inner projected loop as a constant S2 point",
            "sample an outer projected loop as a latitude circle on S2",
            "compute geomstats intrinsic S2 step distances and path lengths",
            "run same-path, pole-degenerate, and ambient-chord graveyards",
        ],
        "carrier_topology": "projected S2 Bloch readout of Hopf-style carrier coordinates; no full S3 bundle object",
        "observable": "geomstats intrinsic S2 path length and displacement from start",
        "pass_fail_predicate": (
            "inner projected loop has zero intrinsic path length while outer projected loop has nonzero intrinsic path "
            "length away from the pole, and adjacent graveyards collapse"
        ),
        "graveyards": [
            "both paths forced to fiber loop collapse distinction",
            "both paths forced to base loop collapse distinction",
            "base loop at pole degenerates",
            "ambient start-end chord hides closed outer path",
        ],
        "baselines": [
            "sampled NumPy Hopf path metric fixture",
            "symbolic SymPy Hopf density derivative fixture",
            "QuTiP/Qiskit/PyTorch density readout fixtures",
        ],
        "alternative_formulations": [
            "full S3/S2 bundle fixture",
            "operator-evolution manifold path fixture",
            "cell-complex approximation to projected loop transport",
        ],
        "exact_tool_function_needs": {
            "geomstats": ["Hypersphere(dim=2).metric.dist"],
            "numpy": ["array", "linspace", "linalg.norm"],
        },
        "lego_or_coupling_target": "declared_fiber_base_coordinate_readout_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyards_detail": graveyards,
        "promotion_allowed": False,
        "pass": all_pass,
    }
    results = apply_default_receipt_boundary(results, source_name=f"sim_{NAME}")
    out_path = RESULTS_DIR / f"{NAME}_results.json"
    out_path.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"PASS={results['pass']}  name={NAME}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
