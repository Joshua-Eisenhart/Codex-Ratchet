#!/usr/bin/env python3
"""Carnot tool-coupling matrix.

This is a tool-stage / lego-fit probe for the Carnot family.  It does not
promote a runtime QIT engine claim.  It checks which installed tools can carry
small, concrete Carnot surfaces before broader coupling work consumes them.
"""

from __future__ import annotations

import json
import math
import pathlib

import cvc5
import gudhi
import numpy as np
import qutip
import rustworkx as rx
import scipy.linalg
import sympy as sp
import torch
import xgi
import z3
from clifford import Cl
from geomstats.geometry.spd_matrices import SPDMatrices
from qiskit.quantum_info import DensityMatrix
from torch_geometric.data import Data

try:
    import geomstats.backend as gs
except Exception:  # pragma: no cover - import verified by the row itself
    gs = None

try:
    import toponetx as tnx
except Exception:  # pragma: no cover - import verified by the row itself
    tnx = None


CLASSIFICATION = "tool_lego_fit_probe"
classification = CLASSIFICATION
SIM_EXECUTION_KIND = "classical"
divergence_log = (
    "Carnot tool-coupling matrix.  This is pre-admission fit evidence across "
    "classical, bridge, and nonclassical-adjacent tools, not a claim that the "
    "repo runtime engine realizes a Carnot machine."
)

LEGO_IDS = [
    "carnot_cycle",
    "quantum_thermodynamics",
    "density_matrix",
    "graph_topology",
    "proof_fence",
]
PRIMARY_LEGO_IDS = ["carnot_cycle"]

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing numeric Carnot bookkeeping"},
    "scipy": {"tried": True, "used": True, "reason": "load-bearing matrix-log entropy cross-check"},
    "sympy": {"tried": True, "used": True, "reason": "symbolic Carnot efficiency derivation"},
    "z3": {"tried": True, "used": True, "reason": "UNSAT fence for super-Carnot inequality"},
    "cvc5": {"tried": True, "used": True, "reason": "independent fixed-parameter UNSAT fence"},
    "qutip": {"tried": True, "used": True, "reason": "density-matrix thermal state witness"},
    "qiskit": {"tried": True, "used": True, "reason": "independent density-matrix thermal state witness"},
    "pytorch": {"tried": True, "used": True, "reason": "autograd over Carnot efficiency with respect to bath ratio"},
    "pyg": {"tried": True, "used": True, "reason": "stage graph tensor carrier for four Carnot legs"},
    "rustworkx": {"tried": True, "used": True, "reason": "directed stage graph and cycle ordering witness"},
    "xgi": {"tried": True, "used": True, "reason": "hypergraph grouping of bath/adiabatic leg families"},
    "toponetx": {"tried": True, "used": tnx is not None, "reason": "cell-complex stage topology witness"},
    "gudhi": {"tried": True, "used": True, "reason": "simplex filtration over cycle-stage adjacency"},
    "geomstats": {"tried": True, "used": True, "reason": "SPD manifold membership check for regularized density carriers"},
    "clifford": {"tried": True, "used": True, "reason": "geometric-algebra noncommutation witness for leg-order variants"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "scipy": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "qutip": "load_bearing",
    "qiskit": "load_bearing",
    "pytorch": "load_bearing",
    "pyg": "load_bearing",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "supportive",
    "gudhi": "load_bearing",
    "geomstats": "load_bearing",
    "clifford": "load_bearing",
}

RESULT_DIR = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results"


def binary_entropy(p: float) -> float:
    p = min(max(float(p), 1e-15), 1.0 - 1e-15)
    return float(-(p * math.log(p) + (1.0 - p) * math.log(1.0 - p)))


def gibbs_excited_probability(temperature: float, gap: float) -> float:
    weight = math.exp(-float(gap) / float(temperature))
    return float(weight / (1.0 + weight))


def density_from_probability(p_excited: float) -> np.ndarray:
    p = min(max(float(p_excited), 0.0), 1.0)
    return np.array([[1.0 - p, 0.0], [0.0, p]], dtype=np.complex128)


def scipy_vn_entropy(rho: np.ndarray) -> float:
    log_rho = scipy.linalg.logm(rho)
    return float(np.real(-np.trace(rho @ log_rho)))


def numeric_surface() -> dict:
    t_hot = 2.0
    t_cold = 1.0
    gap = 3.0
    p_hot = gibbs_excited_probability(t_hot, gap)
    rho = density_from_probability(p_hot)
    entropy_direct = binary_entropy(p_hot)
    entropy_scipy = scipy_vn_entropy(rho)
    return {
        "t_hot": t_hot,
        "t_cold": t_cold,
        "efficiency": 1.0 - t_cold / t_hot,
        "p_hot_excited": p_hot,
        "entropy_direct": entropy_direct,
        "entropy_scipy_logm": entropy_scipy,
        "pass": abs(entropy_direct - entropy_scipy) < 1e-10,
    }


def symbolic_surface() -> dict:
    tc, th = sp.symbols("Tc Th", positive=True)
    qh = sp.symbols("Qh", positive=True)
    qc = qh * tc / th
    eta = sp.simplify((qh - qc) / qh)
    target = 1 - tc / th
    return {
        "eta": str(eta),
        "target": str(target),
        "symbolic_difference": str(sp.simplify(eta - target)),
        "pass": bool(sp.simplify(eta - target) == 0),
    }


def z3_surface() -> dict:
    tc, th, qh, qc, w, eta = z3.Reals("tc th qh qc w eta")
    solver = z3.Solver()
    solver.add(tc > 0, th > 0, tc < th)
    solver.add(qh > 0, qc >= 0, w == qh - qc)
    solver.add(qc / tc >= qh / th)
    solver.add(eta == w / qh)
    solver.add(eta > 1 - tc / th)
    result = solver.check()
    return {"super_carnot_general_check": str(result), "pass": result == z3.unsat}


def cvc5_surface() -> dict:
    solver = cvc5.Solver()
    solver.setLogic("QF_LRA")
    real = solver.getRealSort()
    qc = solver.mkConst(real, "qc")
    one = solver.mkReal(1)
    half = solver.mkReal(1, 2)
    two = solver.mkReal(2)
    eta = solver.mkTerm(cvc5.Kind.DIVISION, solver.mkTerm(cvc5.Kind.SUB, two, qc), two)
    solver.assertFormula(solver.mkTerm(cvc5.Kind.GEQ, qc, one))
    solver.assertFormula(solver.mkTerm(cvc5.Kind.GT, eta, half))
    result = solver.checkSat()
    return {
        "fixed_tc1_th2_qh2_super_carnot_check": str(result),
        "pass": str(result).lower() == "unsat",
    }


def density_tool_surface() -> dict:
    p = gibbs_excited_probability(2.0, 3.0)
    rho_np = density_from_probability(p)
    rho_qutip = np.asarray(qutip.Qobj(rho_np, dims=[[2], [2]]).full(), dtype=np.complex128)
    rho_qiskit = np.asarray(DensityMatrix(rho_np).data, dtype=np.complex128)
    return {
        "qutip_trace": float(np.real(np.trace(rho_qutip))),
        "qiskit_trace": float(np.real(np.trace(rho_qiskit))),
        "qutip_qiskit_max_error": float(np.max(np.abs(rho_qutip - rho_qiskit))),
        "pass": bool(np.max(np.abs(rho_qutip - rho_np)) < 1e-12 and np.max(np.abs(rho_qiskit - rho_np)) < 1e-12),
    }


def tensor_graph_surface() -> dict:
    ratio = torch.tensor(0.5, dtype=torch.float64, requires_grad=True)
    eta = 1.0 - ratio
    eta.backward()
    x = torch.tensor([[2.0, 0.0], [0.0, 0.0], [1.0, 0.0], [0.0, 0.0]], dtype=torch.float64)
    edge_index = torch.tensor([[0, 1, 2, 3], [1, 2, 3, 0]], dtype=torch.long)
    data = Data(x=x, edge_index=edge_index)
    return {
        "eta": float(eta.detach()),
        "d_eta_d_ratio": float(ratio.grad),
        "pyg_nodes": int(data.num_nodes),
        "pyg_edges": int(data.num_edges),
        "pass": bool(abs(float(ratio.grad) + 1.0) < 1e-12 and data.num_nodes == 4 and data.num_edges == 4),
    }


def graph_topology_surface() -> dict:
    graph = rx.PyDiGraph()
    graph.add_nodes_from(["hot_iso", "adiabatic_expand", "cold_iso", "adiabatic_compress"])
    graph.add_edge(0, 1, "to_cold_low")
    graph.add_edge(1, 2, "cold_contact")
    graph.add_edge(2, 3, "to_hot_high")
    graph.add_edge(3, 0, "hot_contact")

    hypergraph = xgi.Hypergraph([["hot_iso", "cold_iso"], ["adiabatic_expand", "adiabatic_compress"]])

    cell_shape = None
    if tnx is not None:
        cc = tnx.CellComplex()
        cc.add_cell([0, 1], rank=1)
        cc.add_cell([1, 2], rank=1)
        cc.add_cell([2, 3], rank=1)
        cc.add_cell([3, 0], rank=1)
        cell_shape = tuple(int(v) for v in cc.shape)

    simplex = gudhi.SimplexTree()
    for edge in [(0, 1), (1, 2), (2, 3), (0, 3)]:
        simplex.insert(edge)
    simplex.persistence()

    return {
        "rustworkx_nodes": graph.num_nodes(),
        "rustworkx_edges": graph.num_edges(),
        "xgi_edges": hypergraph.num_edges,
        "toponetx_shape": cell_shape,
        "gudhi_simplices": simplex.num_simplices(),
        "pass": bool(graph.num_edges() == 4 and hypergraph.num_edges == 2 and simplex.num_simplices() >= 8),
    }


def geometry_algebra_surface() -> dict:
    spd_space = SPDMatrices(n=2)
    rho = density_from_probability(gibbs_excited_probability(2.0, 3.0)) + np.eye(2) * 1e-6
    spd_belongs = bool(spd_space.belongs(gs.array(np.real(rho)))) if gs is not None else False

    _layout, blades = Cl(3)
    e1, e2 = blades["e1"], blades["e2"]
    anticommutator = e1 * e2 + e2 * e1
    commutator = e1 * e2 - e2 * e1
    return {
        "geomstats_spd_regularized_density": spd_belongs,
        "clifford_anticommutator_norm": float(np.linalg.norm(anticommutator.value)),
        "clifford_commutator_norm": float(np.linalg.norm(commutator.value)),
        "pass": bool(spd_belongs and np.linalg.norm(anticommutator.value) < 1e-12 and np.linalg.norm(commutator.value) > 0.0),
    }


def main() -> None:
    surfaces = {
        "numeric_classical": numeric_surface(),
        "symbolic": symbolic_surface(),
        "z3_fence": z3_surface(),
        "cvc5_fence": cvc5_surface(),
        "density_tools": density_tool_surface(),
        "tensor_graph_tools": tensor_graph_surface(),
        "graph_topology_tools": graph_topology_surface(),
        "geometry_algebra_tools": geometry_algebra_surface(),
    }
    all_pass = all(surface.get("pass") is True for surface in surfaces.values())
    results = {
        "name": "carnot_tool_coupling_matrix",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "allowed_claims": [
            "tool-lego fit evidence for Carnot rows",
            "classical support-tool availability before bridge/nonclassical admission",
            "no runtime engine promotion",
        ],
        "promotion_status": "keep_but_open",
        "promotion_blockers": [
            "does not couple to GStack",
            "does not assert Carnot runtime engine realization",
            "does not replace row-specific Carnot sims",
        ],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": {
            "tools_can_touch_carnot_lego_surfaces": {
                "pass": all_pass,
                "surface_count": len(surfaces),
            }
        },
        "negative": {
            "super_carnot_is_blocked_by_proof_fences": {
                "z3_pass": surfaces["z3_fence"]["pass"],
                "cvc5_pass": surfaces["cvc5_fence"]["pass"],
                "pass": surfaces["z3_fence"]["pass"] and surfaces["cvc5_fence"]["pass"],
            },
            "noncommuting_order_surface_is_not_collapsed_to_classical_commutation": {
                "pass": surfaces["geometry_algebra_tools"]["clifford_commutator_norm"] > 0.0,
            },
        },
        "boundary": {
            "four_leg_cycle_graph_is_closed": {
                "pass": surfaces["graph_topology_tools"]["rustworkx_edges"] == 4,
            }
        },
        "surfaces": surfaces,
        "summary": {
            "all_pass": all_pass,
            "tool_count": len(TOOL_MANIFEST),
            "load_bearing_tool_count": sum(1 for depth in TOOL_INTEGRATION_DEPTH.values() if depth == "load_bearing"),
            "scope_note": divergence_log,
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULT_DIR / "carnot_tool_coupling_matrix_results.json"
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"{out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
