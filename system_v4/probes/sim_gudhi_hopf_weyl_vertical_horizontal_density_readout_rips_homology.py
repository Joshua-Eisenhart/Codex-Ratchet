#!/usr/bin/env python3
"""GUDHI Rips homology for Hopf/Weyl vertical and horizontal density readouts."""

from __future__ import annotations

import json
import math
from pathlib import Path

import gudhi
import numpy as np
from receipt_boundary import apply_default_receipt_boundary


NAME = "gudhi_hopf_weyl_vertical_horizontal_density_readout_rips_homology"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "builds Vietoris-Rips complexes over Bloch-density readout point clouds and computes persistent homology intervals",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "samples Hopf/Weyl carrier paths and computes Bloch-density point clouds and distance controls",
    },
}
TOOL_INTEGRATION_DEPTH = {"gudhi": "load_bearing", "numpy": "supportive"}


def spinor(theta: float, phi: float, chi: float, sheet_orientation: int) -> np.ndarray:
    signed_phi = float(sheet_orientation) * phi
    return np.asarray(
        [
            math.cos(theta / 2.0) * np.exp(0.5j * (chi + signed_phi)),
            math.sin(theta / 2.0) * np.exp(0.5j * (chi - signed_phi)),
        ],
        dtype=np.complex128,
    )


def bloch_readout(state: np.ndarray) -> np.ndarray:
    a, b = state
    return np.asarray(
        [
            2.0 * np.real(np.conjugate(a) * b),
            2.0 * np.imag(np.conjugate(a) * b),
            abs(a) ** 2 - abs(b) ** 2,
        ],
        dtype=float,
    )


def path_points(
    theta: float,
    phi0: float,
    chi0: float,
    sheet_orientation: int,
    family: str,
    samples: int,
) -> np.ndarray:
    points = []
    for value in np.linspace(0.0, 2.0 * math.pi, samples, endpoint=False):
        if family == "vertical_fiber":
            phi = phi0
            chi = chi0 + float(value)
        elif family == "raw_base":
            phi = phi0 + float(value)
            chi = chi0
        elif family == "horizontal_base":
            phi = phi0 + float(value)
            chi = chi0 - float(sheet_orientation) * math.cos(theta) * float(value)
        elif family == "wrong_sign_horizontal_base":
            phi = phi0 + float(value)
            chi = chi0 + float(sheet_orientation) * math.cos(theta) * float(value)
        else:
            raise ValueError(f"unknown path family: {family}")
        points.append(bloch_readout(spinor(theta, phi, chi, sheet_orientation)))
    return np.asarray(points, dtype=float)


def persistence_summary(points: np.ndarray, max_edge_length: float = 2.0) -> dict[str, object]:
    rips = gudhi.RipsComplex(points=points.tolist(), max_edge_length=max_edge_length)
    tree = rips.create_simplex_tree(max_dimension=2)
    tree.compute_persistence()
    h0 = tree.persistence_intervals_in_dimension(0)
    h1 = tree.persistence_intervals_in_dimension(1)
    finite_h1 = [
        [float(birth), float(death), float(death - birth)]
        for birth, death in h1
        if np.isfinite(death)
    ]
    infinite_h1 = [[float(birth), "inf"] for birth, death in h1 if not np.isfinite(death)]
    persistent_h1 = [row for row in finite_h1 if row[2] > 0.2] + infinite_h1
    centered = points - points.mean(axis=0, keepdims=True)
    singular_values = np.linalg.svd(centered, compute_uv=False)
    return {
        "point_count": int(points.shape[0]),
        "simplex_count": int(tree.num_simplices()),
        "h0_interval_count": int(len(h0)),
        "h1_interval_count": int(len(h1)),
        "persistent_h1_count": int(len(persistent_h1)),
        "finite_h1_intervals": finite_h1,
        "infinite_h1_intervals": infinite_h1,
        "max_pairwise_displacement": float(np.max(np.linalg.norm(points - points[0], axis=1))),
        "rank_proxy_singular_values": [float(value) for value in singular_values],
        "rank_proxy_singular_value_count": int(np.sum(singular_values > 1e-8)),
    }


def run_positive() -> dict[str, object]:
    theta = math.pi / 3.0
    phi0 = math.pi / 5.0
    chi0 = math.pi / 7.0
    rows = {
        family: persistence_summary(path_points(theta, phi0, chi0, 1, family, samples=129))
        for family in ("vertical_fiber", "raw_base", "horizontal_base", "wrong_sign_horizontal_base")
    }
    return {
        "theta": theta,
        "phi0": phi0,
        "chi0": chi0,
        "readouts": rows,
        "density_readout_topology_pass": bool(
            rows["vertical_fiber"]["persistent_h1_count"] == 0
            and rows["vertical_fiber"]["rank_proxy_singular_value_count"] == 0
            and rows["raw_base"]["persistent_h1_count"] >= 1
            and rows["horizontal_base"]["persistent_h1_count"] >= 1
            and rows["wrong_sign_horizontal_base"]["persistent_h1_count"] >= 1
        ),
    }


def run_graveyards() -> dict[str, object]:
    theta = math.pi / 3.0
    phi0 = math.pi / 5.0
    chi0 = math.pi / 7.0
    positive = run_positive()["readouts"]
    pole = {
        family: persistence_summary(path_points(0.0, phi0, chi0, 1, family, samples=129))
        for family in ("vertical_fiber", "horizontal_base")
    }
    equator = {
        family: persistence_summary(path_points(math.pi / 2.0, phi0, chi0, 1, family, samples=129))
        for family in ("raw_base", "horizontal_base")
    }
    return {
        "vertical_fiber_density_readout_has_no_loop": {
            "persistent_h1_count": positive["vertical_fiber"]["persistent_h1_count"],
            "rank_proxy_singular_value_count": positive["vertical_fiber"]["rank_proxy_singular_value_count"],
            "passed": bool(
                positive["vertical_fiber"]["persistent_h1_count"] == 0
                and positive["vertical_fiber"]["rank_proxy_singular_value_count"] == 0
            ),
        },
        "horizontal_base_density_readout_has_loop": {
            "persistent_h1_count": positive["horizontal_base"]["persistent_h1_count"],
            "rank_proxy_singular_value_count": positive["horizontal_base"]["rank_proxy_singular_value_count"],
            "passed": bool(
                positive["horizontal_base"]["persistent_h1_count"] >= 1
                and positive["horizontal_base"]["rank_proxy_singular_value_count"] == 2
            ),
        },
        "density_topology_does_not_distinguish_raw_from_horizontal_base": {
            "raw_base_persistent_h1_count": positive["raw_base"]["persistent_h1_count"],
            "horizontal_base_persistent_h1_count": positive["horizontal_base"]["persistent_h1_count"],
            "raw_base_rank_proxy": positive["raw_base"]["rank_proxy_singular_value_count"],
            "horizontal_base_rank_proxy": positive["horizontal_base"]["rank_proxy_singular_value_count"],
            "passed": bool(
                positive["raw_base"]["persistent_h1_count"] == positive["horizontal_base"]["persistent_h1_count"]
                and positive["raw_base"]["rank_proxy_singular_value_count"]
                == positive["horizontal_base"]["rank_proxy_singular_value_count"]
            ),
        },
        "wrong_sign_density_topology_is_not_a_connection_sign_detector": {
            "horizontal_base_persistent_h1_count": positive["horizontal_base"]["persistent_h1_count"],
            "wrong_sign_persistent_h1_count": positive["wrong_sign_horizontal_base"]["persistent_h1_count"],
            "passed": bool(
                positive["horizontal_base"]["persistent_h1_count"]
                == positive["wrong_sign_horizontal_base"]["persistent_h1_count"]
            ),
        },
        "pole_horizontal_base_density_readout_collapses": {
            "persistent_h1_count": pole["horizontal_base"]["persistent_h1_count"],
            "rank_proxy_singular_value_count": pole["horizontal_base"]["rank_proxy_singular_value_count"],
            "passed": bool(
                pole["horizontal_base"]["persistent_h1_count"] == 0
                and pole["horizontal_base"]["rank_proxy_singular_value_count"] == 0
            ),
        },
        "equator_raw_and_horizontal_density_topology_coincide": {
            "raw_base_persistent_h1_count": equator["raw_base"]["persistent_h1_count"],
            "horizontal_base_persistent_h1_count": equator["horizontal_base"]["persistent_h1_count"],
            "passed": bool(
                equator["raw_base"]["persistent_h1_count"] == equator["horizontal_base"]["persistent_h1_count"]
                and equator["raw_base"]["rank_proxy_singular_value_count"]
                == equator["horizontal_base"]["rank_proxy_singular_value_count"]
            ),
        },
    }


def main() -> int:
    positive = run_positive()
    graveyards = run_graveyards()
    all_pass = bool(positive["density_readout_topology_pass"] and all(row["passed"] for row in graveyards.values()))
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "GUDHI Vietoris-Rips persistent homology baseline for Bloch-density readout point clouds from declared "
            "Hopf/Weyl vertical fiber and horizontal base-lift paths only; this shows density topology sees loop "
            "presence versus fiber collapse, but it does not distinguish raw base from horizontal base or connection "
            "sign; no full nested Hopf-torus geometric-constraint manifold, no physical evolution, no flux, no QIT, "
            "no GStack, no axis, no bridge, no nonclassical admission, and no target-system admission"
        ),
        "next_lego_target": "hopf_weyl_carrier_loop_geometry_baseline",
        "promotion_condition": (
            "May only support later geometry planning after full carrier, connection, topology, solver, density-object, "
            "and physical operator-evolution receipts reproduce compatible vertical/horizontal separation with adjacent controls."
        ),
        "demotion_condition": (
            "Demote if vertical fiber density readout has persistent H1, if horizontal/base density readouts have no loop, "
            "or if pole/equator/raw-horizontal/wrong-sign controls do not collapse or coincide as predicted."
        ),
        "blocked_until": "blocked from target-system claims until full carrier/topology and physical-evolution receipts exist",
        "out_of_scope": [
            "No full nested Hopf-torus manifold or geometric-constraint manifold.",
            "No flux representation or Pauli-boundary shortcut.",
            "No Lindblad, Hamiltonian, thermodynamic, or information-cycle mechanics.",
            "No distinction between raw base and horizontal base by density topology alone.",
            "No QIT, GStack, axis, bridge, nonclassical, or target-system admission.",
        ],
        "divergence_log": (
            "This GUDHI packet is deliberately weaker than the metric and density-object transport packets: it detects "
            "fiber-collapse versus density-loop topology but records raw-base/horizontal-base and connection-sign "
            "indistinguishability as graveyard limits."
        ),
        "operation_sequence": [
            "construct two-component Hopf/Weyl spinor samples from theta, phi, and chi",
            "project each carrier sample to a three-coordinate Bloch-density readout",
            "sample vertical fiber, raw base, horizontal base lift, and wrong-sign horizontal base paths",
            "build GUDHI Vietoris-Rips complexes over each density readout point cloud",
            "compute H0 and H1 persistence intervals and rank-proxy coordinate span diagnostics",
            "run fiber-collapse, horizontal-loop, pole-collapse, equator-coincidence, raw-horizontal, and wrong-sign graveyards",
        ],
        "carrier_topology": "sampled two-component Hopf/Weyl carrier projected to Bloch-density point clouds; no full nested-torus manifold",
        "observable": "Vietoris-Rips H0/H1 persistence intervals, persistent-H1 counts, pairwise displacement, and coordinate-rank proxies",
        "pass_fail_predicate": (
            "vertical fiber density readout has no persistent H1 and collapses in coordinate span, horizontal/raw/wrong-sign "
            "base density readouts have persistent H1, and adjacent controls collapse or become indistinguishable as predicted"
        ),
        "graveyards": [
            "vertical fiber density readout has no loop",
            "horizontal base density readout has loop",
            "density topology does not distinguish raw from horizontal base",
            "wrong-sign density topology is not a connection-sign detector",
            "pole horizontal base density readout collapses",
            "equator raw and horizontal density topology coincide",
        ],
        "baselines": [
            "SymPy Hopf/Weyl fiber-horizontal-base loop independence identities",
            "Geomstats Hopf/Weyl fiber-horizontal-base loop distance baseline",
            "Clifford Hopf/Weyl fiber-horizontal-base tangent inner-product baseline",
            "QuTiP/Qiskit Hopf/Weyl vertical-horizontal density transport baselines",
            "z3/cvc5 Hopf/Weyl vertical-horizontal metric predicate controls",
        ],
        "alternative_formulations": [
            "GUDHI AlphaComplex over S2/Bloch readout point clouds",
            "TopoNetX cycle-cell fixture for density readout loops",
            "Geomstats path-neighborhood distance sweep around fiber and horizontal base paths",
            "physical Hamiltonian generator evolution over vertical and horizontal path families",
        ],
        "exact_tool_function_needs": {
            "gudhi": [
                "RipsComplex",
                "RipsComplex.create_simplex_tree",
                "SimplexTree.compute_persistence",
                "SimplexTree.persistence_intervals_in_dimension",
            ],
            "numpy": ["linspace", "exp", "asarray", "linalg.norm", "linalg.svd", "isfinite"],
        },
        "lego_or_coupling_target": "hopf_weyl_carrier_loop_geometry_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyards_detail": graveyards,
        "promotion_allowed": False,
        "pass": all_pass,
    }
    results = apply_default_receipt_boundary(results, source_name=f"sim_{NAME}")
    out_path = RESULTS_DIR / f"{NAME}_results.json"
    out_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"PASS={results['pass']}  name={NAME}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
