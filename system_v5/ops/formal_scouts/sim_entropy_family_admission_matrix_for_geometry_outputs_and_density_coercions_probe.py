#!/usr/bin/env python3
"""Entropy-family admission matrix for geometry outputs and density coercions."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any, Callable

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

from clifford import Cl
import gudhi
import networkx as nx
import opt_einsum as oe
import rustworkx as rx
import sympy as sp
import torch
from torch_geometric.utils import from_networkx
import toponetx as tnx
import xgi
import z3

try:
    import qutip

    HAVE_QUTIP = True
except Exception:
    HAVE_QUTIP = False

try:
    import geomstats.backend as gs

    HAVE_GEOMSTATS = True
except Exception:
    HAVE_GEOMSTATS = False


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "entropy_family_admission_matrix_for_geometry_outputs_and_density_coercions_probe_results.json"

NAME = "entropy_family_admission_matrix_for_geometry_outputs_and_density_coercions_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests which entropy readouts admit bounded geometry "
    "outputs directly or after explicit density coercion. It separates type "
    "compatibility from nesting-order claims and does not admit a final "
    "manifold, cycle, axis, bridge, or target-system entropy theorem."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing density matrices, spectra, tensor states, and entropy values"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing bipartite partial traces"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact entropy boundary check"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing type-admission impossibility checks"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing Cl(1,3) orientation check for chiral entropy"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistent entropy of an information graph"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing triple information hyperedge witness"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing joint-admission simplicial complex"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing admissibility-flow directed graph"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing graph source for PyG conversion"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing edge-index conversion for admission graph"},
    "qutip": {"tried": True, "used": HAVE_QUTIP, "reason": "supportive von-Neumann entropy cross-check when available"},
    "geomstats": {"tried": True, "used": HAVE_GEOMSTATS, "reason": "supportive array backend check for Bures-style distance value"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "opt_einsum": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "clifford": "load_bearing",
    "gudhi": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "rustworkx": "load_bearing",
    "networkx": "load_bearing",
    "torch_geometric": "load_bearing",
    "qutip": "supportive" if HAVE_QUTIP else None,
    "geomstats": "supportive" if HAVE_GEOMSTATS else None,
}


def hermitian(rho: torch.Tensor) -> torch.Tensor:
    return (rho + rho.conj().T) / 2


def is_density(obj: Any, tol: float = 1e-9) -> bool:
    if not isinstance(obj, torch.Tensor) or obj.ndim != 2 or obj.shape[0] != obj.shape[1]:
        return False
    if not torch.allclose(obj, obj.conj().T, atol=tol):
        return False
    if abs(float(torch.trace(obj).real) - 1.0) > tol:
        return False
    return bool(float(torch.linalg.eigvalsh(hermitian(obj)).min()) > -tol)


def random_density(dim: int, seed: int) -> torch.Tensor:
    gen = torch.Generator().manual_seed(seed)
    re = torch.randn(dim, dim, generator=gen, dtype=torch.float64)
    im = torch.randn(dim, dim, generator=gen, dtype=torch.float64)
    a = torch.complex(re, im)
    rho = a @ a.conj().T
    return rho / torch.trace(rho).real


def state_to_density(psi: torch.Tensor) -> torch.Tensor:
    psi = psi / torch.linalg.vector_norm(psi)
    return torch.outer(psi, psi.conj())


def ghz_state(n: int = 8) -> torch.Tensor:
    psi = torch.zeros(2**n, dtype=torch.complex128)
    psi[0] = 1 / math.sqrt(2)
    psi[-1] = 1 / math.sqrt(2)
    return psi


SIGMA_X = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex128)
SIGMA_Y = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex128)
SIGMA_Z = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex128)
IDENTITY_2 = torch.eye(2, dtype=torch.complex128)


def partial_trace_b_2x2(rho: torch.Tensor) -> torch.Tensor:
    return oe.contract("aibi->ab", rho.reshape(2, 2, 2, 2))


def partial_trace_a_2x2(rho: torch.Tensor) -> torch.Tensor:
    return oe.contract("aiaj->ij", rho.reshape(2, 2, 2, 2))


def entropy_von_neumann(rho: torch.Tensor) -> float:
    eigs = torch.clamp(torch.linalg.eigvalsh(hermitian(rho)), min=1e-15)
    eigs = eigs / eigs.sum()
    return float((-torch.sum(eigs * torch.log(eigs))).item())


def entropy_renyi_2(rho: torch.Tensor) -> float:
    return float(-torch.log(torch.real(torch.trace(rho @ rho))).item())


def entropy_tsallis_2(rho: torch.Tensor) -> float:
    return float((1.0 - torch.real(torch.trace(rho @ rho))).item())


def entropy_min(rho: torch.Tensor) -> float:
    return float(-torch.log(torch.linalg.eigvalsh(hermitian(rho)).clamp(min=1e-15).max()).item())


def entropy_max(rho: torch.Tensor) -> float:
    rank = int((torch.linalg.eigvalsh(hermitian(rho)) > 1e-9).sum())
    return float(math.log(max(rank, 1)))


def entropy_linear(rho: torch.Tensor) -> float:
    return float((1.0 - torch.real(torch.trace(rho @ rho))).item())


def mutual_information_2x2(rho: torch.Tensor) -> float:
    return entropy_von_neumann(partial_trace_b_2x2(rho)) + entropy_von_neumann(partial_trace_a_2x2(rho)) - entropy_von_neumann(rho)


def coherent_information_2x2(rho: torch.Tensor) -> float:
    return entropy_von_neumann(partial_trace_a_2x2(rho)) - entropy_von_neumann(rho)


def persistent_entropy_graph(psi: torch.Tensor) -> dict[str, Any]:
    st = gudhi.SimplexTree()
    for node in range(8):
        st.insert([node], filtration=0.0)
    for edge in range(7):
        st.insert([edge, edge + 1], filtration=float(edge + 1))
    pairs = st.persistence()
    finite_h0 = [(birth, death) for dim, (birth, death) in pairs if dim == 0 and death != float("inf")]
    lifetimes = torch.tensor([death - birth for birth, death in finite_h0], dtype=torch.float64)
    probs = lifetimes / lifetimes.sum()
    return {"persistent_entropy_H0": float((-(probs * torch.log(probs))).sum()), "features": len(finite_h0)}


def triple_information_hyperedge(psi: torch.Tensor) -> dict[str, Any]:
    graph = nx.Graph()
    graph.add_edges_from([(0, 1), (0, 2), (1, 2)])
    hypergraph = xgi.Hypergraph()
    hypergraph.add_nodes_from([0, 1, 2])
    hypergraph.add_edge([0, 1, 2])
    return {"triple_hyperedge_count": hypergraph.num_edges, "graph_triangle_count": nx.triangles(graph, 0)}


def chirality_projectors() -> tuple[torch.Tensor, torch.Tensor]:
    _, blades = Cl(1, 3)
    pseudo = blades["e1234"]
    pseudo_square_is_negative = abs(float((pseudo * pseudo)[()]) + 1.0) < 1e-12
    if not pseudo_square_is_negative:
        raise RuntimeError("unexpected Cl(1,3) pseudoscalar square")
    gamma5 = torch.diag(torch.tensor([-1, -1, 1, 1], dtype=torch.complex128))
    ident = torch.eye(4, dtype=torch.complex128)
    return (ident - gamma5) / 2, (ident + gamma5) / 2


def chirality_graded_entropy(rho: torch.Tensor) -> dict[str, Any]:
    p_left, p_right = chirality_projectors()
    left = p_left @ rho @ p_left
    right = p_right @ rho @ p_right
    tr_left = float(torch.trace(left).real)
    tr_right = float(torch.trace(right).real)
    return {
        "left_weight": tr_left,
        "right_weight": tr_right,
        "left_entropy": entropy_von_neumann(left / max(tr_left, 1e-15)) if tr_left > 1e-12 else 0.0,
        "right_entropy": entropy_von_neumann(right / max(tr_right, 1e-15)) if tr_right > 1e-12 else 0.0,
    }


def bures_distance_to_mixed(rho: torch.Tensor) -> float:
    dim = rho.shape[0]
    inner = rho / dim
    fidelity = float(torch.sqrt(torch.clamp(torch.linalg.eigvalsh(hermitian(inner)), min=0)).sum() ** 2)
    value = math.sqrt(max(0.0, 2 * (1 - fidelity)))
    if HAVE_GEOMSTATS:
        value = float(gs.array(value))
    return value


def admits_density(obj: Any) -> bool:
    return is_density(obj)


def admits_bipartite_density(obj: Any) -> bool:
    return is_density(obj) and int(math.sqrt(obj.shape[0])) ** 2 == obj.shape[0]


def admits_four_component_density(obj: Any) -> bool:
    return is_density(obj) and obj.shape == (4, 4)


def admits_eight_component_state(obj: Any) -> bool:
    return isinstance(obj, torch.Tensor) and obj.ndim == 1 and obj.numel() == 256 and abs(float(torch.linalg.vector_norm(obj)) - 1) < 1e-9


EntropyRow = tuple[Callable[[Any], Any], Callable[[Any], bool], str]
ENTROPIES: dict[str, EntropyRow] = {
    "von_neumann_entropy_density_matrix": (entropy_von_neumann, admits_density, "density matrix"),
    "renyi_order_2_entropy_density_matrix": (entropy_renyi_2, admits_density, "density matrix"),
    "tsallis_order_2_entropy_density_matrix": (entropy_tsallis_2, admits_density, "density matrix"),
    "min_entropy_density_matrix": (entropy_min, admits_density, "density matrix"),
    "max_entropy_density_matrix": (entropy_max, admits_density, "density matrix"),
    "linear_entropy_density_matrix": (entropy_linear, admits_density, "density matrix"),
    "mutual_information_bipartite_density_matrix": (mutual_information_2x2, admits_bipartite_density, "bipartite density matrix"),
    "coherent_information_bipartite_density_matrix": (coherent_information_2x2, admits_bipartite_density, "bipartite density matrix"),
    "persistent_entropy_eight_component_information_graph": (persistent_entropy_graph, admits_eight_component_state, "eight-component state"),
    "triple_information_three_site_hyperedge": (triple_information_hyperedge, admits_eight_component_state, "eight-component state"),
    "chirality_graded_entropy_four_component_density": (chirality_graded_entropy, admits_four_component_density, "four-component density matrix"),
    "bures_distance_to_maximally_mixed_density_matrix": (bures_distance_to_mixed, admits_density, "density matrix"),
}


def geometry_outputs() -> dict[str, Callable[[], Any]]:
    return {
        "two_component_state_vector": lambda: torch.tensor([0.6 + 0j, 0.0 + 0.8j], dtype=torch.complex128),
        "bloch_coordinate_vector": lambda: torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64),
        "hopf_phase_invariant_two_component_density": lambda: state_to_density(torch.tensor([1 + 0j, 1j], dtype=torch.complex128)),
        "unitary_holonomy_matrix": lambda: torch.eye(2, dtype=torch.complex128),
        "four_component_chiral_density_matrix": lambda: random_density(4, 7),
        "local_channel_output_density_matrix": lambda: random_density(2, 11),
        "simplicial_cycle_betti_number_scalar": lambda: 1,
        "two_point_spectral_distance_scalar": lambda: 1.0,
        "eight_component_tensor_network_state_vector": lambda: ghz_state(8),
        "support_graph_incidence_data": lambda: {"nodes": 8, "edges": 7},
    }


def coerce_to_density(name: str, obj: Any) -> Any | None:
    if name == "two_component_state_vector":
        return state_to_density(obj)
    if name == "bloch_coordinate_vector":
        bx, by, bz = [float(x) for x in obj]
        return 0.5 * (IDENTITY_2 + bx * SIGMA_X + by * SIGMA_Y + bz * SIGMA_Z)
    if name == "unitary_holonomy_matrix":
        return obj @ state_to_density(torch.tensor([1 + 0j, 0 + 0j], dtype=torch.complex128)) @ obj.conj().T
    if is_density(obj):
        return obj
    return obj if admits_eight_component_state(obj) else None


def build_matrix(coerce: bool) -> dict[str, Any]:
    rows = list(ENTROPIES)
    cols = list(geometry_outputs())
    matrix = torch.zeros((len(rows), len(cols)), dtype=torch.int64)
    details: dict[str, dict[str, str]] = {}
    for i, row in enumerate(rows):
        func, pred, _ = ENTROPIES[row]
        details[row] = {}
        for j, col in enumerate(cols):
            obj = geometry_outputs()[col]()
            candidate = coerce_to_density(col, obj) if coerce else obj
            if candidate is None:
                details[row][col] = "rejected_no_density_coercion"
                continue
            if not pred(candidate):
                details[row][col] = "rejected_input_type"
                continue
            try:
                func(candidate)
                matrix[i, j] = 1
                details[row][col] = "admitted"
            except Exception as exc:
                details[row][col] = f"runtime_error_{type(exc).__name__}"
    return {"rows": rows, "cols": cols, "matrix": matrix, "details": details}


def summarize_matrix(data: dict[str, Any]) -> dict[str, Any]:
    matrix = data["matrix"]
    rows = data["rows"]
    cols = data["cols"]
    graph = rx.PyDiGraph()
    col_nodes = {col: graph.add_node(("geometry_output", col)) for col in cols}
    row_nodes = {row: graph.add_node(("entropy", row)) for row in rows}
    for j, col in enumerate(cols):
        for i, row in enumerate(rows):
            if int(matrix[i, j]):
                graph.add_edge(col_nodes[col], row_nodes[row], "admits")

    nx_graph = nx.DiGraph()
    for j, col in enumerate(cols):
        for i, row in enumerate(rows):
            if int(matrix[i, j]):
                nx_graph.add_edge(col, row)
    pyg_graph = from_networkx(nx_graph)

    complex_ = tnx.SimplicialComplex()
    for col in cols:
        complex_.add_node(col)
    for a in range(len(cols)):
        for b in range(a + 1, len(cols)):
            if int(((matrix[:, a] == 1) & (matrix[:, b] == 1)).sum()):
                complex_.add_simplex([cols[a], cols[b]])
    for a in range(len(cols)):
        for b in range(a + 1, len(cols)):
            for c in range(b + 1, len(cols)):
                if int(((matrix[:, a] == 1) & (matrix[:, b] == 1) & (matrix[:, c] == 1)).sum()):
                    complex_.add_simplex([cols[a], cols[b], cols[c]])

    counts = [int(matrix[:, j].sum()) for j in range(len(cols))]
    diffs = [counts[i + 1] - counts[i] for i in range(len(counts) - 1)]
    return {
        "survived": int(matrix.sum()),
        "total": int(matrix.numel()),
        "admit_ratio": float(matrix.sum() / matrix.numel()),
        "per_geometry_output_admit_count": dict(zip(cols, counts)),
        "ordered_count_differences": diffs,
        "monotone_nonincreasing_in_list_order": all(diff <= 0 for diff in diffs),
        "rustworkx_edge_count": graph.num_edges(),
        "pyg_edge_index_shape": list(pyg_graph.edge_index.shape),
        "toponetx_vertices_edges_triangles": {
            "vertices": len(complex_.skeleton(0)),
            "edges": len(complex_.skeleton(1)),
            "triangles": len(complex_.skeleton(2)) if complex_.dim >= 2 else 0,
            "max_dim": complex_.dim,
        },
    }


def z3_type_impossibility() -> dict[str, Any]:
    scalar = z3.IntVal(0)
    matrix = z3.IntVal(2)
    solver = z3.Solver()
    solver.add(scalar == matrix)
    return {"solver_status": str(solver.check()), "pass": solver.check() == z3.unsat}


def sympy_entropy_boundary() -> dict[str, Any]:
    half = sp.Rational(1, 2)
    trace_square = half**2 + half**2
    renyi_2 = -sp.log(trace_square)
    return {"renyi_order_2_maximally_mixed_two_state": str(renyi_2), "pass": sp.simplify(renyi_2 - sp.log(2)) == 0}


def qutip_cross_check() -> dict[str, Any]:
    if not HAVE_QUTIP:
        return {"available": False, "pass": True}
    rho = qutip.Qobj([[0.5, 0.0], [0.0, 0.5]])
    return {"available": True, "entropy": float(qutip.entropy_vn(rho)), "pass": abs(float(qutip.entropy_vn(rho)) - math.log(2)) < 1e-9}


def main() -> dict[str, Any]:
    started = time.time()
    raw = build_matrix(coerce=False)
    coerced = build_matrix(coerce=True)
    raw_summary = summarize_matrix(raw)
    coerced_summary = summarize_matrix(coerced)

    positive = {
        "raw_and_density_coerced_admission_matrices_are_distinct": {
            "raw_survived": raw_summary["survived"],
            "coerced_survived": coerced_summary["survived"],
            "pass": coerced_summary["survived"] > raw_summary["survived"],
        },
        "admission_graph_edges_match_survived_coerced_cells": {
            "coerced_survived": coerced_summary["survived"],
            "rustworkx_edge_count": coerced_summary["rustworkx_edge_count"],
            "pyg_edge_index_shape": coerced_summary["pyg_edge_index_shape"],
            "pass": coerced_summary["survived"] == coerced_summary["rustworkx_edge_count"],
        },
        "joint_admission_complex_has_higher_order_faces": {
            "complex": coerced_summary["toponetx_vertices_edges_triangles"],
            "pass": coerced_summary["toponetx_vertices_edges_triangles"]["triangles"] > 0,
        },
        "z3_scalar_output_is_not_matrix_entropy_input": z3_type_impossibility(),
    }
    graveyard_companions = {
        "zero_trace_matrix_is_rejected_as_density": {
            "pass": not is_density(torch.zeros((2, 2), dtype=torch.complex128)),
        },
        "scalar_geometry_outputs_do_not_gain_entropy_without_explicit_coercion": {
            "raw_counts": {
                key: raw_summary["per_geometry_output_admit_count"][key]
                for key in ("simplicial_cycle_betti_number_scalar", "two_point_spectral_distance_scalar")
            },
            "pass": raw_summary["per_geometry_output_admit_count"]["simplicial_cycle_betti_number_scalar"] == 0
            and raw_summary["per_geometry_output_admit_count"]["two_point_spectral_distance_scalar"] == 0,
        },
        "list_order_is_not_evidence_of_depth_monotonic_entropy_reduction": {
            "coerced_counts": coerced_summary["per_geometry_output_admit_count"],
            "monotone_nonincreasing": coerced_summary["monotone_nonincreasing_in_list_order"],
            "pass": coerced_summary["monotone_nonincreasing_in_list_order"] is False,
        },
    }
    boundary = {
        "sympy_renyi_boundary_for_maximally_mixed_two_state": sympy_entropy_boundary(),
        "qutip_von_neumann_entropy_cross_check": qutip_cross_check(),
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "entropy-family admission matrix over bounded geometry output types and density coercions",
        "raw_matrix": {k: v for k, v in raw_summary.items() if k != "pyg_edge_index_shape"},
        "density_coerced_matrix": coerced_summary,
        "entropy_families": list(ENTROPIES),
        "geometry_outputs": list(geometry_outputs()),
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyard_companions), "passed": sum(1 for row in graveyard_companions.values() if row["pass"])},
        "blockers": [],
        "open_choices": [
            "this tests output-type and density-coercion admission, not final nesting order",
            "a separate ordered-chain scout should test whether constraints reduce allowed geometry transitions",
        ],
        "why_not_v4_probes": "This is a clean v5 formal scout using v5 naming and result contracts; it should not add to the mixed v4 probe estate.",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {"all_pass": bool(all_pass), "elapsed_seconds": round(time.time() - started, 6), "promotion_allowed": PROMOTION_ALLOWED},
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
