#!/usr/bin/env python3
"""rustworkx cycle graph for Hopf/Weyl vertical and horizontal density readouts."""

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
import rustworkx as rx
from receipt_boundary import apply_default_receipt_boundary


NAME = "rustworkx_hopf_weyl_vertical_horizontal_density_readout_cycle_graph"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "builds PyGraph cycle/collapsed fixtures from Bloch-density readout path families and computes connected-component and cycle-basis readouts",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "samples Hopf/Weyl carrier paths and computes Bloch-density readouts and displacement controls",
    },
}
TOOL_INTEGRATION_DEPTH = {"rustworkx": "load_bearing", "numpy": "supportive"}


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


def build_cycle_or_collapsed_graph(points: np.ndarray, collapse_tol: float = 1e-8) -> tuple[rx.PyGraph, str]:
    max_displacement = float(np.max(np.linalg.norm(points - points[0], axis=1)))
    graph = rx.PyGraph()
    if max_displacement < collapse_tol:
        graph.add_node("collapsed_density_readout")
        return graph, "collapsed_point"
    nodes = [graph.add_node(idx) for idx in range(points.shape[0])]
    for idx in range(points.shape[0]):
        graph.add_edge(nodes[idx], nodes[(idx + 1) % points.shape[0]], "path_edge")
    return graph, "cycle_graph"


def graph_readout(points: np.ndarray) -> dict[str, object]:
    graph, kind = build_cycle_or_collapsed_graph(points)
    cycles = rx.cycle_basis(graph)
    centered = points - points.mean(axis=0, keepdims=True)
    singular_values = np.linalg.svd(centered, compute_uv=False)
    return {
        "graph_kind": kind,
        "node_count": int(graph.num_nodes()),
        "edge_count": int(graph.num_edges()),
        "connected_component_count": int(rx.number_connected_components(graph)),
        "is_connected": bool(rx.is_connected(graph)),
        "cycle_basis_count": int(len(cycles)),
        "cycle_basis_lengths": [int(len(row)) for row in cycles],
        "max_pairwise_displacement": float(np.max(np.linalg.norm(points - points[0], axis=1))),
        "rank_proxy_singular_value_count": int(np.sum(singular_values > 1e-8)),
    }


def readout(theta: float, samples: int = 32) -> dict[str, object]:
    phi0 = math.pi / 5.0
    chi0 = math.pi / 7.0
    return {
        family: graph_readout(path_points(theta, phi0, chi0, 1, family, samples))
        for family in ("vertical_fiber", "raw_base", "horizontal_base", "wrong_sign_horizontal_base")
    }


def run_positive() -> dict[str, object]:
    rows = readout(math.pi / 3.0)
    return {
        "theta": math.pi / 3.0,
        "readouts": rows,
        "density_readout_cycle_graph_pass": bool(
            rows["vertical_fiber"]["graph_kind"] == "collapsed_point"
            and rows["vertical_fiber"]["cycle_basis_count"] == 0
            and rows["horizontal_base"]["graph_kind"] == "cycle_graph"
            and rows["horizontal_base"]["connected_component_count"] == 1
            and rows["horizontal_base"]["cycle_basis_count"] == 1
            and rows["raw_base"]["cycle_basis_count"] == rows["horizontal_base"]["cycle_basis_count"]
            and rows["wrong_sign_horizontal_base"]["cycle_basis_count"] == rows["horizontal_base"]["cycle_basis_count"]
        ),
    }


def run_graveyards() -> dict[str, object]:
    positive = run_positive()["readouts"]
    pole = readout(0.0)
    equator = readout(math.pi / 2.0)
    path_no_closure = rx.PyGraph()
    nodes = [path_no_closure.add_node(idx) for idx in range(32)]
    for idx in range(31):
        path_no_closure.add_edge(nodes[idx], nodes[idx + 1], "path_edge")
    isolated_nodes = rx.PyGraph()
    for idx in range(32):
        isolated_nodes.add_node(idx)
    return {
        "vertical_fiber_density_readout_collapses_to_one_node_graph": {
            "graph_kind": positive["vertical_fiber"]["graph_kind"],
            "cycle_basis_count": positive["vertical_fiber"]["cycle_basis_count"],
            "passed": bool(
                positive["vertical_fiber"]["graph_kind"] == "collapsed_point"
                and positive["vertical_fiber"]["cycle_basis_count"] == 0
            ),
        },
        "horizontal_base_density_readout_has_one_cycle": {
            "graph_kind": positive["horizontal_base"]["graph_kind"],
            "cycle_basis_count": positive["horizontal_base"]["cycle_basis_count"],
            "passed": bool(
                positive["horizontal_base"]["graph_kind"] == "cycle_graph"
                and positive["horizontal_base"]["cycle_basis_count"] == 1
            ),
        },
        "cycle_graph_does_not_distinguish_raw_from_horizontal_base": {
            "raw_base_cycle_basis_count": positive["raw_base"]["cycle_basis_count"],
            "horizontal_base_cycle_basis_count": positive["horizontal_base"]["cycle_basis_count"],
            "passed": bool(positive["raw_base"]["cycle_basis_count"] == positive["horizontal_base"]["cycle_basis_count"]),
        },
        "wrong_sign_cycle_graph_is_not_a_connection_sign_detector": {
            "horizontal_base_cycle_basis_count": positive["horizontal_base"]["cycle_basis_count"],
            "wrong_sign_cycle_basis_count": positive["wrong_sign_horizontal_base"]["cycle_basis_count"],
            "passed": bool(
                positive["wrong_sign_horizontal_base"]["cycle_basis_count"]
                == positive["horizontal_base"]["cycle_basis_count"]
            ),
        },
        "pole_horizontal_base_density_readout_collapses": {
            "graph_kind": pole["horizontal_base"]["graph_kind"],
            "cycle_basis_count": pole["horizontal_base"]["cycle_basis_count"],
            "passed": bool(
                pole["horizontal_base"]["graph_kind"] == "collapsed_point"
                and pole["horizontal_base"]["cycle_basis_count"] == 0
            ),
        },
        "equator_raw_and_horizontal_cycle_graphs_coincide": {
            "raw_base_cycle_basis_count": equator["raw_base"]["cycle_basis_count"],
            "horizontal_base_cycle_basis_count": equator["horizontal_base"]["cycle_basis_count"],
            "passed": bool(equator["raw_base"]["cycle_basis_count"] == equator["horizontal_base"]["cycle_basis_count"]),
        },
        "open_path_has_no_cycle": {
            "node_count": int(path_no_closure.num_nodes()),
            "edge_count": int(path_no_closure.num_edges()),
            "cycle_basis_count": int(len(rx.cycle_basis(path_no_closure))),
            "passed": bool(len(rx.cycle_basis(path_no_closure)) == 0),
        },
        "isolated_nodes_are_not_one_connected_cycle": {
            "node_count": int(isolated_nodes.num_nodes()),
            "edge_count": int(isolated_nodes.num_edges()),
            "connected_component_count": int(rx.number_connected_components(isolated_nodes)),
            "cycle_basis_count": int(len(rx.cycle_basis(isolated_nodes))),
            "passed": bool(
                rx.number_connected_components(isolated_nodes) == isolated_nodes.num_nodes()
                and len(rx.cycle_basis(isolated_nodes)) == 0
            ),
        },
    }


def main() -> int:
    positive = run_positive()
    graveyards = run_graveyards()
    all_pass = bool(positive["density_readout_cycle_graph_pass"] and all(row["passed"] for row in graveyards.values()))
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "rustworkx PyGraph baseline for Bloch-density readout cycle fixtures from declared Hopf/Weyl vertical "
            "fiber and horizontal base-lift paths only; this represents fiber collapse versus density-loop readout "
            "but does not distinguish raw base from horizontal base or connection sign; no full nested Hopf-torus "
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
            "graphs, or if pole/equator/raw-horizontal/wrong-sign/open-path/isolated-node controls do not collapse or coincide."
        ),
        "blocked_until": "blocked from target-system claims until full carrier/topology and physical-evolution receipts exist",
        "out_of_scope": [
            "No full nested Hopf-torus manifold or geometric-constraint manifold.",
            "No flux representation or Pauli-boundary shortcut.",
            "No Lindblad, Hamiltonian, thermodynamic, or information-cycle mechanics.",
            "No distinction between raw base and horizontal base by graph cycle structure alone.",
            "No QIT, GStack, axis, bridge, nonclassical, or target-system admission.",
        ],
        "divergence_log": (
            "This rustworkx packet is a graph-cycle formulation of the density-readout topology limit. It detects "
            "collapsed-fiber versus one-cycle readouts and records raw-base/horizontal-base and connection-sign "
            "indistinguishability as controls."
        ),
        "operation_sequence": [
            "construct two-component Hopf/Weyl spinor samples from theta, phi, and chi",
            "project each carrier sample to a three-coordinate Bloch-density readout",
            "sample vertical fiber, raw base, horizontal base lift, and wrong-sign horizontal base paths",
            "collapse near-constant density readout paths to one-node rustworkx PyGraph fixtures",
            "encode non-collapsed density readout paths as rustworkx one-cycle PyGraph fixtures",
            "compute connected-component counts, connectivity, and cycle-basis readouts",
            "run fiber-collapse, horizontal-cycle, pole-collapse, equator-coincidence, raw-horizontal, wrong-sign, open-path, and isolated-node graveyards",
        ],
        "carrier_topology": "sampled two-component Hopf/Weyl carrier projected to Bloch-density readout paths and then to finite graph fixtures",
        "observable": "rustworkx PyGraph node/edge counts, connected-component counts, connectivity, cycle-basis counts, and density-readout displacement",
        "pass_fail_predicate": (
            "vertical fiber density readout collapses to a point graph, horizontal/raw/wrong-sign base density readouts "
            "form one-cycle graphs, and adjacent controls collapse or become indistinguishable as predicted"
        ),
        "graveyards": [
            "vertical fiber density readout collapses to one-node graph",
            "horizontal base density readout has one cycle",
            "cycle graph does not distinguish raw from horizontal base",
            "wrong-sign cycle graph is not a connection-sign detector",
            "pole horizontal base density readout collapses",
            "equator raw and horizontal cycle graphs coincide",
            "open path has no cycle",
            "isolated nodes are not one connected cycle",
        ],
        "baselines": [
            "TopoNetX Hopf/Weyl vertical-horizontal density readout cycle incidence baseline",
            "GUDHI Hopf/Weyl vertical-horizontal density readout Rips homology baseline",
            "QuTiP/Qiskit Hopf/Weyl vertical-horizontal density transport baselines",
            "SymPy/Geomstats/Clifford Hopf/Weyl vertical-horizontal metric baselines",
            "z3/cvc5 Hopf/Weyl vertical-horizontal metric predicate controls",
        ],
        "alternative_formulations": [
            "NetworkX cycle graph and connected-component baseline",
            "TopoNetX SimplicialComplex path-cycle fixture",
            "GUDHI SimplexTree explicit cycle/collapsed fixture",
            "physical Hamiltonian generator evolution over vertical and horizontal path families",
        ],
        "exact_tool_function_needs": {
            "rustworkx": [
                "PyGraph",
                "PyGraph.add_node",
                "PyGraph.add_edge",
                "number_connected_components",
                "is_connected",
                "cycle_basis",
            ],
            "numpy": ["linspace", "exp", "asarray", "linalg.norm", "linalg.svd"],
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
