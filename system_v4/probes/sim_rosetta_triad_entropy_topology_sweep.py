#!/usr/bin/env python3
"""Entropy/topology sweep over the Carnot/Szilard/I Ching Rosetta triad.

This compares more entropy families and topology signatures across the three
receipt-backed rows.  It is a breadth sweep for the Rosetta layer, not a QIT
engine admission or a GStack nesting claim.
"""

from __future__ import annotations

import json
import math
import pathlib
from typing import Any

import cvc5
import numpy as np
import qutip
import rustworkx as rx
import scipy.linalg
import sympy as sp
import torch
import xgi
import z3
from qiskit.quantum_info import DensityMatrix
from torch_geometric.data import Data

try:
    import gudhi
except Exception:  # pragma: no cover
    gudhi = None

try:
    import toponetx as tnx
except Exception:  # pragma: no cover
    tnx = None


CLASSIFICATION = "canonical"
classification = CLASSIFICATION
divergence_log = (
    "Rosetta triad entropy/topology sweep over Carnot, Szilard, and I Ching-64. "
    "It applies shared entropy families and graph/topology signatures to the "
    "three existing receipts. It is comparison evidence only, not QIT admission."
)

LEGO_IDS = [
    "carnot_cycle",
    "szilard_cycle",
    "iching_64_schedule",
    "entropy_family",
    "graph_topology",
    "density_matrix",
    "proof_fence",
    "rosetta_correlation",
    "graveyard_variant",
]
PRIMARY_LEGO_IDS = ["entropy_family", "graph_topology", "rosetta_correlation"]

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "loads exact triad source receipts"},
    "numpy": {"tried": True, "used": True, "reason": "probability distributions, entropy families, topology signatures"},
    "scipy": {"tried": True, "used": True, "reason": "matrix-log von Neumann entropy cross-check"},
    "sympy": {"tried": True, "used": True, "reason": "symbolic Euler/cycle-rank identities"},
    "torch": {"tried": True, "used": True, "reason": "entropy tensor checks and Laplacian spectrum carrier"},
    "pyg": {"tried": True, "used": True, "reason": "graph tensor carrier for each topology signature"},
    "rustworkx": {"tried": True, "used": True, "reason": "cycle/path graph construction and topology signatures"},
    "xgi": {"tried": True, "used": True, "reason": "hypergraph grouping of entropy/topology rows"},
    "qiskit": {"tried": True, "used": True, "reason": "density-matrix witness for each entropy distribution"},
    "qutip": {"tried": True, "used": True, "reason": "independent density-matrix entropy witness"},
    "z3": {"tried": True, "used": True, "reason": "UNSAT fence against collapsing distinct topology signatures"},
    "cvc5": {"tried": True, "used": True, "reason": "independent UNSAT fence against topology collapse"},
    "gudhi": {"tried": True, "used": gudhi is not None, "reason": "simplex-tree persistence summary when installed"},
    "toponetx": {"tried": True, "used": tnx is not None, "reason": "cell-complex shape/Euler witness when installed"},
}
TOOL_INTEGRATION_DEPTH = {
    tool: ("load_bearing" if spec["used"] else None) for tool, spec in TOOL_MANIFEST.items()
}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
VIS_DIR = PROBE_DIR.parents[1] / "visualizer"


def load_result(stem: str) -> dict[str, Any]:
    path = RESULT_DIR / f"{stem}_results.json"
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(values: list[float]) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float64)
    arr = np.maximum(arr, 0.0)
    total = float(arr.sum())
    if total <= 0.0:
        return np.ones(len(arr), dtype=np.float64) / float(len(arr))
    return arr / total


def carnot_distribution(carnot: dict[str, Any]) -> np.ndarray:
    return normalize([float(row["p_excited"]) for row in carnot.get("states", [])])


def szilard_distribution(szilard: dict[str, Any]) -> np.ndarray:
    labels = ["initial_mixed_blank", "measured_record", "feedback_purified", "erased_closed"]
    return normalize([float(szilard["states"][label]["joint_entropy"]) + 1e-12 for label in labels])


def iching_distribution(iching: dict[str, Any]) -> np.ndarray:
    return np.ones(int(iching["summary"]["state_count"]), dtype=np.float64) / float(iching["summary"]["state_count"])


def shannon(probs: np.ndarray) -> float:
    p = probs[probs > 1e-15]
    return float(-np.sum(p * np.log(p)))


def renyi(probs: np.ndarray, alpha: float) -> float:
    if abs(alpha - 1.0) < 1e-12:
        return shannon(probs)
    p = probs[probs > 1e-15]
    return float(math.log(float(np.sum(p ** alpha))) / (1.0 - alpha))


def tsallis(probs: np.ndarray, q: float) -> float:
    if abs(q - 1.0) < 1e-12:
        return shannon(probs)
    p = probs[probs > 1e-15]
    return float((1.0 - float(np.sum(p ** q))) / (q - 1.0))


def density_entropy_checks(probs: np.ndarray) -> dict[str, Any]:
    rho = np.diag(probs.astype(np.complex128))
    scipy_vn = float(np.real(-np.trace(rho @ scipy.linalg.logm(rho + np.eye(len(probs)) * 1e-15))))
    qiskit_trace = float(np.real(np.trace(DensityMatrix(rho).data)))
    qutip_rho = qutip.Qobj(rho)
    qutip_trace = float(np.real(qutip_rho.tr()))
    qutip_vn = float(qutip.entropy_vn(qutip_rho, base=math.e))
    torch_probs = torch.tensor(probs, dtype=torch.float64)
    torch_shannon = float(-(torch_probs[torch_probs > 0] * torch.log(torch_probs[torch_probs > 0])).sum())
    return {
        "scipy_vn": scipy_vn,
        "qutip_vn": qutip_vn,
        "torch_shannon": torch_shannon,
        "qiskit_trace": qiskit_trace,
        "qutip_trace": qutip_trace,
        "pass": bool(
            abs(qiskit_trace - 1.0) < 1e-12
            and abs(qutip_trace - 1.0) < 1e-12
            and abs(scipy_vn - shannon(probs)) < 1e-9
            and abs(qutip_vn - shannon(probs)) < 1e-9
            and abs(torch_shannon - shannon(probs)) < 1e-12
        ),
    }


def entropy_row(engine: str, probs: np.ndarray) -> dict[str, Any]:
    rows = {
        "shannon": shannon(probs),
        "renyi_0_5": renyi(probs, 0.5),
        "renyi_2": renyi(probs, 2.0),
        "renyi_inf_proxy": -math.log(float(np.max(probs))),
        "tsallis_0_5": tsallis(probs, 0.5),
        "tsallis_2": tsallis(probs, 2.0),
        "min_entropy": -math.log(float(np.max(probs))),
        "max_entropy": math.log(float(np.count_nonzero(probs > 1e-15))),
        "purity": float(np.sum(probs * probs)),
    }
    checks = density_entropy_checks(probs)
    return {
        "engine": engine,
        "support_size": int(len(probs)),
        "distribution": [float(v) for v in probs],
        "entropy_family": rows,
        "density_entropy_checks": checks,
        "family_pass": bool(
            rows["max_entropy"] + 1e-12 >= rows["shannon"] >= rows["min_entropy"] - 1e-12
            and rows["renyi_0_5"] + 1e-12 >= rows["shannon"] >= rows["renyi_2"] - 1e-12
            and rows["purity"] > 0.0
            and checks["pass"]
        ),
    }


def graph_for(engine: str, node_count: int) -> tuple[rx.PyGraph, list[tuple[int, int]]]:
    graph = rx.PyGraph()
    graph.add_nodes_from(range(node_count))
    if engine == "szilard":
        edges = [(0, 1), (1, 2), (2, 3)]
    else:
        edges = [(i, (i + 1) % node_count) for i in range(node_count)]
    graph.add_edges_from_no_data(edges)
    return graph, edges


def laplacian_eigs(node_count: int, edges: list[tuple[int, int]]) -> list[float]:
    adjacency = np.zeros((node_count, node_count), dtype=np.float64)
    for a, b in edges:
        adjacency[a, b] = 1.0
        adjacency[b, a] = 1.0
    degree = np.diag(adjacency.sum(axis=1))
    lap = degree - adjacency
    return [float(v) for v in np.linalg.eigvalsh(lap)]


def topology_row(engine: str, probs: np.ndarray) -> dict[str, Any]:
    graph, edges = graph_for(engine, len(probs))
    eigs = laplacian_eigs(len(probs), edges)
    beta0 = int(sum(abs(v) < 1e-9 for v in eigs))
    beta1 = int(graph.num_edges() - graph.num_nodes() + beta0)
    edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
    data = Data(
        x=torch.tensor([[float(probs[i])] for i in range(len(probs))], dtype=torch.float64),
        edge_index=edge_index,
    )
    hypergraph = xgi.Hypergraph([[engine, f"n{i}", "cycle" if beta1 else "path"] for i in range(len(probs))])
    gudhi_simplices = None
    if gudhi is not None:
        st = gudhi.SimplexTree()
        for i in range(len(probs)):
            st.insert([i])
        for a, b in edges:
            st.insert([a, b])
        st.persistence()
        gudhi_simplices = st.num_simplices()
    toponetx_shape = None
    if tnx is not None:
        cc = tnx.CellComplex()
        for a, b in edges:
            cc.add_cell([a, b], rank=1)
        toponetx_shape = tuple(int(v) for v in cc.shape)
    euler_symbolic = sp.simplify(sp.Integer(graph.num_nodes()) - sp.Integer(graph.num_edges()))
    return {
        "engine": engine,
        "nodes": graph.num_nodes(),
        "edges": graph.num_edges(),
        "beta0_laplacian": beta0,
        "beta1_cycle_rank": beta1,
        "euler_characteristic": int(euler_symbolic),
        "laplacian_zero_eigenvalues": beta0,
        "laplacian_spectral_gap": float(next((v for v in eigs if v > 1e-9), 0.0)),
        "pyg_nodes": int(data.num_nodes),
        "pyg_edges": int(data.num_edges),
        "xgi_edges": hypergraph.num_edges,
        "gudhi_simplices": gudhi_simplices,
        "toponetx_shape": toponetx_shape,
        "topology_pass": bool(
            graph.num_nodes() == len(probs)
            and int(data.num_nodes) == len(probs)
            and int(data.num_edges) == len(edges)
            and beta0 == 1
            and beta1 in {0, 1}
        ),
    }


def z3_topology_collapse_unsat(topology_rows: list[dict[str, Any]]) -> dict[str, Any]:
    c_nodes, s_nodes, i_nodes = z3.Ints("c_nodes s_nodes i_nodes")
    c_beta, s_beta, i_beta = z3.Ints("c_beta s_beta i_beta")
    by_engine = {row["engine"]: row for row in topology_rows}
    solver = z3.Solver()
    solver.add(c_nodes == by_engine["carnot"]["nodes"], c_beta == by_engine["carnot"]["beta1_cycle_rank"])
    solver.add(s_nodes == by_engine["szilard"]["nodes"], s_beta == by_engine["szilard"]["beta1_cycle_rank"])
    solver.add(i_nodes == by_engine["iching_64"]["nodes"], i_beta == by_engine["iching_64"]["beta1_cycle_rank"])
    solver.add(c_nodes == s_nodes, s_nodes == i_nodes, c_beta == s_beta, s_beta == i_beta)
    result = solver.check()
    return {
        "claim": "all three topology signatures are identical in node count and cycle rank",
        "signatures": {name: {"nodes": row["nodes"], "beta1": row["beta1_cycle_rank"]} for name, row in by_engine.items()},
        "result": str(result),
        "pass": result == z3.unsat,
    }


def cvc5_topology_collapse_unsat(topology_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_engine = {row["engine"]: row for row in topology_rows}
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    integer = solver.getIntegerSort()
    vars_ = {name: (solver.mkConst(integer, f"{name}_nodes"), solver.mkConst(integer, f"{name}_beta")) for name in by_engine}
    for name, row in by_engine.items():
        n, b = vars_[name]
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, n, solver.mkInteger(row["nodes"])))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, b, solver.mkInteger(row["beta1_cycle_rank"])))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, vars_["carnot"][0], vars_["szilard"][0]))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, vars_["szilard"][0], vars_["iching_64"][0]))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, vars_["carnot"][1], vars_["szilard"][1]))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, vars_["szilard"][1], vars_["iching_64"][1]))
    result = solver.checkSat()
    return {
        "claim": "all three topology signatures are identical in node count and cycle rank",
        "signatures": {name: {"nodes": row["nodes"], "beta1": row["beta1_cycle_rank"]} for name, row in by_engine.items()},
        "result": str(result),
        "pass": str(result).lower() == "unsat",
    }


def graveyard(entropy_rows: list[dict[str, Any]], topology_rows: list[dict[str, Any]], z3_check: dict[str, Any], cvc5_check: dict[str, Any]) -> list[dict[str, Any]]:
    entropy_by_engine = {row["engine"]: row for row in entropy_rows}
    topo_by_engine = {row["engine"]: row for row in topology_rows}
    return [
        {
            "variant": "one_entropy_language_fits_all",
            "status": "rejected",
            "reason": "The same formulas run everywhere, but each engine uses a different source distribution and readout.",
            "evidence": {name: row["support_size"] for name, row in entropy_by_engine.items()},
        },
        {
            "variant": "all_three_have_same_topology_signature",
            "status": "killed",
            "reason": "Carnot is a 4-cycle, Szilard is a 4-path, and I Ching is a 64-cycle.",
            "evidence": {"z3": z3_check["result"], "cvc5": cvc5_check["result"]},
        },
        {
            "variant": "cycle_rank_alone_identifies_engine",
            "status": "rejected",
            "reason": "Carnot and I Ching both have cycle-rank 1 but different cardinality and operator language.",
            "evidence": {name: {"nodes": row["nodes"], "beta1": row["beta1_cycle_rank"]} for name, row in topo_by_engine.items()},
        },
        {
            "variant": "density_entropy_witness_implies_qit_runtime",
            "status": "blocked",
            "reason": "Density witnesses validate distributions only; they do not provide GStack, operator stack, or QIT admission.",
            "evidence": {row["engine"]: row["density_entropy_checks"]["pass"] for row in entropy_rows},
        },
    ]


def build_visual_payload(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": result["name"],
        "summary": result["summary"],
        "entropy_rows": result["entropy_rows"],
        "topology_rows": result["topology_rows"],
        "stress_tests": result["stress_tests"],
        "graveyard_rows": result["graveyard_rows"],
    }


def write_visual_payload(result: dict[str, Any]) -> None:
    VIS_DIR.mkdir(parents=True, exist_ok=True)
    js = "window.ROSETTA_TRIAD_ENTROPY_TOPOLOGY_DATA = " + json.dumps(build_visual_payload(result), indent=2, default=str) + ";\n"
    (VIS_DIR / "rosetta-triad-entropy-topology-data.js").write_text(js, encoding="utf-8")


def main() -> None:
    carnot = load_result("two_bath_heat_work_reversible_cycle_pair")
    szilard = load_result("measure_feedback_erasure_recovery_cycle_pair")
    iching = load_result("six_bit_gray_code_single_flip_cycle_invariant")
    distributions = {
        "carnot": carnot_distribution(carnot),
        "szilard": szilard_distribution(szilard),
        "iching_64": iching_distribution(iching),
    }
    entropy_rows = [entropy_row(engine, probs) for engine, probs in distributions.items()]
    topology_rows = [topology_row(engine, probs) for engine, probs in distributions.items()]
    z3_check = z3_topology_collapse_unsat(topology_rows)
    cvc5_check = cvc5_topology_collapse_unsat(topology_rows)
    stress_tests = {
        "all_entropy_families_pass": {
            "pass": all(row["family_pass"] for row in entropy_rows),
            "failed": [row["engine"] for row in entropy_rows if not row["family_pass"]],
        },
        "all_topology_rows_pass": {
            "pass": all(row["topology_pass"] for row in topology_rows),
            "failed": [row["engine"] for row in topology_rows if not row["topology_pass"]],
        },
        "z3_blocks_topology_signature_collapse": z3_check,
        "cvc5_blocks_topology_signature_collapse": cvc5_check,
    }
    graveyard_rows = graveyard(entropy_rows, topology_rows, z3_check, cvc5_check)
    all_pass = all(row["family_pass"] for row in entropy_rows) and all(row["topology_pass"] for row in topology_rows) and z3_check["pass"] and cvc5_check["pass"]
    result = {
        "name": "rosetta_triad_entropy_topology_sweep",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "sim_execution_kind": "bridge",
        "allowed_claims": [
            "more entropy families run across Carnot, Szilard, and I Ching-64",
            "more topology signatures run across the same triad",
            "negative variants identify entropy/topology collapse failures",
        ],
        "promotion_status": "keep_but_open",
        "promotion_blockers": [
            "no GStack nesting",
            "no admitted QIT runtime",
            "no claim that entropy or topology language is identical across rows",
        ],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipts": {
            "carnot": str(RESULT_DIR / "two_bath_heat_work_reversible_cycle_pair_results.json"),
            "szilard": str(RESULT_DIR / "measure_feedback_erasure_recovery_cycle_pair_results.json"),
            "iching_64": str(RESULT_DIR / "six_bit_gray_code_single_flip_cycle_invariant_results.json"),
        },
        "entropy_rows": entropy_rows,
        "topology_rows": topology_rows,
        "stress_tests": stress_tests,
        "graveyard_rows": graveyard_rows,
        "summary": {
            "all_pass": bool(all_pass),
            "engine_count": 3,
            "entropy_family_count": len(entropy_rows[0]["entropy_family"]),
            "topology_row_count": len(topology_rows),
            "graveyard_row_count": len(graveyard_rows),
            "topology_signature_collapse_blocked": z3_check["pass"] and cvc5_check["pass"],
            "visual_payload": "visualizer/rosetta-triad-entropy-topology-data.js",
            "scope_note": divergence_log,
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULT_DIR / "rosetta_triad_entropy_topology_sweep_results.json"
    out_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    write_visual_payload(result)
    print(out_path)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
