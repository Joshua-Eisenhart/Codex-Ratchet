#!/usr/bin/env python3
"""TopoNetX cycle incidence for Hopf/Weyl vertical and horizontal density readouts."""

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
from receipt_boundary import apply_default_receipt_boundary
from toponetx import CellComplex


NAME = "toponetx_hopf_weyl_vertical_horizontal_density_readout_cycle_incidence"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "builds CellComplex cycle/collapsed fixtures from Bloch-density readout path families and computes incidence/Hodge-Laplacian zero-mode proxies",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "samples Hopf/Weyl carrier paths, computes Bloch-density readouts, displacement controls, and Laplacian eigenspectrum proxies",
    },
}
TOOL_INTEGRATION_DEPTH = {"toponetx": "load_bearing", "numpy": "supportive"}


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


def build_cycle_or_collapsed_complex(points: np.ndarray, collapse_tol: float = 1e-8) -> tuple[CellComplex, str]:
    max_displacement = float(np.max(np.linalg.norm(points - points[0], axis=1)))
    complex_ = CellComplex()
    if max_displacement < collapse_tol:
        complex_.add_node(0)
        return complex_, "collapsed_point"
    for idx in range(points.shape[0]):
        complex_.add_cell([idx, (idx + 1) % points.shape[0]], rank=1)
    return complex_, "cycle_graph"


def zero_modes(matrix: np.ndarray, tol: float = 1e-8) -> int:
    if matrix.size == 0:
        return 0
    symmetric = (matrix + matrix.T) / 2.0
    return int(np.sum(np.abs(np.linalg.eigvalsh(symmetric)) < tol))


def complex_readout(points: np.ndarray) -> dict[str, object]:
    complex_, kind = build_cycle_or_collapsed_complex(points)
    incidence_shapes = {}
    laplacian_shapes = {}
    zero_mode_proxy = {}
    for rank in (0, 1):
        try:
            incidence_shapes[str(rank)] = list(complex_.incidence_matrix(rank).shape)
        except ValueError:
            incidence_shapes[str(rank)] = [0, 0]
        try:
            laplacian = complex_.hodge_laplacian_matrix(rank).toarray()
        except ValueError:
            laplacian_shapes[str(rank)] = [0, 0]
            zero_mode_proxy[str(rank)] = 0
        else:
            laplacian_shapes[str(rank)] = list(laplacian.shape)
            zero_mode_proxy[str(rank)] = zero_modes(laplacian)
    centered = points - points.mean(axis=0, keepdims=True)
    singular_values = np.linalg.svd(centered, compute_uv=False)
    return {
        "complex_kind": kind,
        "node_count": int(len(complex_.nodes)),
        "edge_count": int(len(complex_.edges)),
        "rank2_cell_count": int(len(complex_.cells)),
        "incidence_shapes": incidence_shapes,
        "laplacian_shapes": laplacian_shapes,
        "zero_mode_proxy": zero_mode_proxy,
        "max_pairwise_displacement": float(np.max(np.linalg.norm(points - points[0], axis=1))),
        "rank_proxy_singular_value_count": int(np.sum(singular_values > 1e-8)),
    }


def readout(theta: float, samples: int = 32) -> dict[str, object]:
    phi0 = math.pi / 5.0
    chi0 = math.pi / 7.0
    return {
        family: complex_readout(path_points(theta, phi0, chi0, 1, family, samples))
        for family in ("vertical_fiber", "raw_base", "horizontal_base", "wrong_sign_horizontal_base")
    }


def run_positive() -> dict[str, object]:
    rows = readout(math.pi / 3.0)
    return {
        "theta": math.pi / 3.0,
        "readouts": rows,
        "density_readout_cycle_incidence_pass": bool(
            rows["vertical_fiber"]["complex_kind"] == "collapsed_point"
            and rows["vertical_fiber"]["zero_mode_proxy"]["0"] == 1
            and rows["vertical_fiber"]["zero_mode_proxy"]["1"] == 0
            and rows["horizontal_base"]["complex_kind"] == "cycle_graph"
            and rows["horizontal_base"]["zero_mode_proxy"]["0"] == 1
            and rows["horizontal_base"]["zero_mode_proxy"]["1"] == 1
            and rows["raw_base"]["zero_mode_proxy"] == rows["horizontal_base"]["zero_mode_proxy"]
            and rows["wrong_sign_horizontal_base"]["zero_mode_proxy"] == rows["horizontal_base"]["zero_mode_proxy"]
        ),
    }


def run_graveyards() -> dict[str, object]:
    positive = run_positive()["readouts"]
    pole = readout(0.0)
    equator = readout(math.pi / 2.0)

    no_edge = CellComplex()
    for idx in range(32):
        no_edge.add_node(idx)
    no_edge_readout = {
        "node_count": int(len(no_edge.nodes)),
        "edge_count": int(len(no_edge.edges)),
        "zero_mode_proxy": {
            "0": zero_modes(no_edge.hodge_laplacian_matrix(0).toarray()),
            "1": 0,
        },
    }

    return {
        "vertical_fiber_density_readout_collapses_to_point_complex": {
            "complex_kind": positive["vertical_fiber"]["complex_kind"],
            "zero_mode_proxy": positive["vertical_fiber"]["zero_mode_proxy"],
            "passed": bool(
                positive["vertical_fiber"]["complex_kind"] == "collapsed_point"
                and positive["vertical_fiber"]["zero_mode_proxy"]["1"] == 0
            ),
        },
        "horizontal_base_density_readout_is_cycle_complex": {
            "complex_kind": positive["horizontal_base"]["complex_kind"],
            "zero_mode_proxy": positive["horizontal_base"]["zero_mode_proxy"],
            "passed": bool(
                positive["horizontal_base"]["complex_kind"] == "cycle_graph"
                and positive["horizontal_base"]["zero_mode_proxy"]["1"] == 1
            ),
        },
        "cell_incidence_does_not_distinguish_raw_from_horizontal_base": {
            "raw_base_zero_mode_proxy": positive["raw_base"]["zero_mode_proxy"],
            "horizontal_base_zero_mode_proxy": positive["horizontal_base"]["zero_mode_proxy"],
            "passed": bool(positive["raw_base"]["zero_mode_proxy"] == positive["horizontal_base"]["zero_mode_proxy"]),
        },
        "wrong_sign_cell_incidence_is_not_a_connection_sign_detector": {
            "horizontal_base_zero_mode_proxy": positive["horizontal_base"]["zero_mode_proxy"],
            "wrong_sign_zero_mode_proxy": positive["wrong_sign_horizontal_base"]["zero_mode_proxy"],
            "passed": bool(
                positive["wrong_sign_horizontal_base"]["zero_mode_proxy"]
                == positive["horizontal_base"]["zero_mode_proxy"]
            ),
        },
        "pole_horizontal_base_density_readout_collapses": {
            "complex_kind": pole["horizontal_base"]["complex_kind"],
            "zero_mode_proxy": pole["horizontal_base"]["zero_mode_proxy"],
            "passed": bool(
                pole["horizontal_base"]["complex_kind"] == "collapsed_point"
                and pole["horizontal_base"]["zero_mode_proxy"]["1"] == 0
            ),
        },
        "equator_raw_and_horizontal_cell_incidence_coincide": {
            "raw_base_zero_mode_proxy": equator["raw_base"]["zero_mode_proxy"],
            "horizontal_base_zero_mode_proxy": equator["horizontal_base"]["zero_mode_proxy"],
            "passed": bool(equator["raw_base"]["zero_mode_proxy"] == equator["horizontal_base"]["zero_mode_proxy"]),
        },
        "node_cloud_without_edges_is_not_cycle_complex": {
            "node_count": no_edge_readout["node_count"],
            "edge_count": no_edge_readout["edge_count"],
            "zero_mode_proxy": no_edge_readout["zero_mode_proxy"],
            "passed": bool(no_edge_readout["edge_count"] == 0 and no_edge_readout["zero_mode_proxy"]["1"] == 0),
        },
    }


def main() -> int:
    positive = run_positive()
    graveyards = run_graveyards()
    all_pass = bool(positive["density_readout_cycle_incidence_pass"] and all(row["passed"] for row in graveyards.values()))
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "TopoNetX CellComplex incidence baseline for Bloch-density readout cycle fixtures from declared Hopf/Weyl "
            "vertical fiber and horizontal base-lift paths only; this represents fiber collapse versus density-loop "
            "readout but does not distinguish raw base from horizontal base or connection sign; no full nested Hopf-torus "
            "geometric-constraint manifold, no physical evolution, no flux, no QIT, no GStack, no axis, no bridge, "
            "no nonclassical admission, and no target-system admission"
        ),
        "next_lego_target": "hopf_weyl_carrier_loop_geometry_baseline",
        "promotion_condition": (
            "May only support later geometry planning after full carrier, connection, topology, solver, density-object, "
            "and physical operator-evolution receipts reproduce compatible vertical/horizontal separation with adjacent controls."
        ),
        "demotion_condition": (
            "Demote if vertical fiber density readout does not collapse, if horizontal/base readouts do not form one-cycle "
            "incidence fixtures, or if pole/equator/raw-horizontal/wrong-sign controls do not collapse or coincide as predicted."
        ),
        "blocked_until": "blocked from target-system claims until full carrier/topology and physical-evolution receipts exist",
        "out_of_scope": [
            "No full nested Hopf-torus manifold or geometric-constraint manifold.",
            "No flux representation or Pauli-boundary shortcut.",
            "No Lindblad, Hamiltonian, thermodynamic, or information-cycle mechanics.",
            "No distinction between raw base and horizontal base by cell incidence alone.",
            "No QIT, GStack, axis, bridge, nonclassical, or target-system admission.",
        ],
        "divergence_log": (
            "This TopoNetX packet is a cell-incidence formulation of the density-readout topology limit. It detects "
            "collapsed-fiber versus one-cycle readouts and records raw-base/horizontal-base and connection-sign "
            "indistinguishability as controls."
        ),
        "operation_sequence": [
            "construct two-component Hopf/Weyl spinor samples from theta, phi, and chi",
            "project each carrier sample to a three-coordinate Bloch-density readout",
            "sample vertical fiber, raw base, horizontal base lift, and wrong-sign horizontal base paths",
            "collapse near-constant density readout paths to one-node CellComplex fixtures",
            "encode non-collapsed density readout paths as TopoNetX one-cycle CellComplex fixtures",
            "compute incidence matrix shapes and Hodge-Laplacian zero-mode proxies",
            "run fiber-collapse, horizontal-cycle, pole-collapse, equator-coincidence, raw-horizontal, wrong-sign, and no-edge graveyards",
        ],
        "carrier_topology": "sampled two-component Hopf/Weyl carrier projected to Bloch-density readout paths and then to finite CellComplex fixtures",
        "observable": "TopoNetX CellComplex node/edge counts, incidence matrix shapes, Hodge-Laplacian zero-mode proxies, and density-readout displacement",
        "pass_fail_predicate": (
            "vertical fiber density readout collapses to a point fixture, horizontal/raw/wrong-sign base density readouts "
            "form one-cycle fixtures, and adjacent controls collapse or become indistinguishable as predicted"
        ),
        "graveyards": [
            "vertical fiber density readout collapses to point complex",
            "horizontal base density readout is cycle complex",
            "cell incidence does not distinguish raw from horizontal base",
            "wrong-sign cell incidence is not a connection-sign detector",
            "pole horizontal base density readout collapses",
            "equator raw and horizontal cell incidence coincide",
            "node cloud without edges is not cycle complex",
        ],
        "baselines": [
            "GUDHI Hopf/Weyl vertical-horizontal density readout Rips homology baseline",
            "QuTiP/Qiskit Hopf/Weyl vertical-horizontal density transport baselines",
            "SymPy/Geomstats/Clifford Hopf/Weyl vertical-horizontal metric baselines",
            "z3/cvc5 Hopf/Weyl vertical-horizontal metric predicate controls",
        ],
        "alternative_formulations": [
            "TopoNetX SimplicialComplex path-cycle fixture",
            "GUDHI SimplexTree explicit cycle/collapsed fixture",
            "NetworkX cycle graph and connected-component baseline",
            "physical Hamiltonian generator evolution over vertical and horizontal path families",
        ],
        "exact_tool_function_needs": {
            "toponetx": [
                "CellComplex",
                "CellComplex.add_node",
                "CellComplex.add_cell",
                "CellComplex.incidence_matrix",
                "CellComplex.hodge_laplacian_matrix",
            ],
            "numpy": ["linspace", "exp", "asarray", "linalg.norm", "linalg.eigvalsh", "linalg.svd"],
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
