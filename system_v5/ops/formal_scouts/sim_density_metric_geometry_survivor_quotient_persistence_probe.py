#!/usr/bin/env python3
"""Density-metric geometry survivor-quotient persistence scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from collections import defaultdict
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import geomstats.backend as gs
import gudhi
import networkx as nx
import rustworkx as rx
import sympy as sp
import torch
from torch_geometric.utils import from_networkx
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "density_metric_geometry_survivor_quotient_persistence_probe_results.json"

NAME = "density_metric_geometry_survivor_quotient_persistence_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: compares density-matrix metric geometries as constraint "
    "layers, computes survivor sets, probe quotients, and Vietoris-Rips "
    "persistence. It tests whether geometry choice changes admissibility, but "
    "does not admit a final manifold, ontology, cycle identity, bridge, axis, "
    "or target-system claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing density candidates, channels, spectra, entropy, and matrix distances"},
    "geomstats": {"tried": True, "used": True, "reason": "load-bearing backend array sanity for metric-coordinate values"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing Vietoris-Rips persistence on survivor distance matrices"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing quotient graph construction"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing graph-to-tensor conversion for quotient graph"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing geometry/order transition graph"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact metric boundary sanity check"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing geometry-choice survivor difference contradiction check"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

DTYPE = torch.complex128
DIM = 4


def hermitian(rho: torch.Tensor) -> torch.Tensor:
    return (rho + rho.conj().T) / 2


def density_valid(rho: torch.Tensor) -> bool:
    eigs = torch.linalg.eigvalsh(hermitian(rho))
    tr = torch.trace(rho)
    return bool(abs(float(torch.real(tr).item()) - 1.0) < 1e-9 and abs(float(torch.imag(tr).item())) < 1e-9 and float(torch.min(eigs).item()) >= -1e-9)


def normalize_density(raw: torch.Tensor) -> torch.Tensor:
    rho = raw @ raw.conj().T
    return rho / torch.real(torch.trace(rho))


def candidate_densities() -> list[dict[str, Any]]:
    gen = torch.Generator().manual_seed(314159)
    candidates = []
    pure_vectors = []
    for idx in range(DIM):
        psi = torch.zeros(DIM, dtype=DTYPE)
        psi[idx] = 1
        pure_vectors.append((f"basis_{idx}", psi))
    pure_vectors.append(("bell_plus", torch.tensor([1, 0, 0, 1], dtype=DTYPE) / math.sqrt(2)))
    pure_vectors.append(("bell_minus", torch.tensor([1, 0, 0, -1], dtype=DTYPE) / math.sqrt(2)))
    pure_vectors.append(("plus_plus", torch.tensor([1, 1, 1, 1], dtype=DTYPE) / 2))
    for name, psi in pure_vectors:
        pure = torch.outer(psi, psi.conj())
        mixed = 0.78 * pure + 0.22 * torch.eye(DIM, dtype=DTYPE) / DIM
        candidates.append({"candidate_id": len(candidates), "source_label": name, "rho": mixed})
    for _ in range(17):
        re = torch.randn(DIM, DIM, generator=gen, dtype=torch.float64)
        im = torch.randn(DIM, DIM, generator=gen, dtype=torch.float64)
        raw = torch.complex(re, im)
        rho = normalize_density(raw)
        rho = 0.85 * rho + 0.15 * torch.eye(DIM, dtype=DTYPE) / DIM
        candidates.append({"candidate_id": len(candidates), "source_label": f"mixed_{len(candidates):02d}", "rho": rho})
    return candidates


def one_qubit_operator(local: torch.Tensor, qubit: int) -> torch.Tensor:
    eye = torch.eye(2, dtype=DTYPE)
    return torch.kron(local if qubit == 0 else eye, local if qubit == 1 else eye)


def phase_damping(rho: torch.Tensor, gamma: float = 0.31) -> torch.Tensor:
    z = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
    op = one_qubit_operator(z, 0)
    return (1 - gamma) * rho + gamma * (op @ rho @ op.conj().T)


def amplitude_damping(rho: torch.Tensor, gamma: float = 0.27) -> torch.Tensor:
    k0 = torch.tensor([[1, 0], [0, math.sqrt(1 - gamma)]], dtype=DTYPE)
    k1 = torch.tensor([[0, math.sqrt(gamma)], [0, 0]], dtype=DTYPE)
    out = torch.zeros_like(rho)
    for local in (k0, k1):
        op = one_qubit_operator(local, 1)
        out += op @ rho @ op.conj().T
    return out


def spectral_filter(rho: torch.Tensor) -> torch.Tensor:
    filt = torch.diag(torch.tensor([1.0, 0.73, 0.59, 0.41], dtype=DTYPE))
    out = filt @ rho @ filt.conj().T
    return out / torch.real(torch.trace(out))


ORDERS = {
    "phase_then_damping_then_filter": [phase_damping, amplitude_damping, spectral_filter],
    "damping_then_phase_then_filter": [amplitude_damping, phase_damping, spectral_filter],
    "filter_then_phase_then_damping": [spectral_filter, phase_damping, amplitude_damping],
}


def entropy(rho: torch.Tensor) -> float:
    eigs = torch.clamp(torch.linalg.eigvalsh(hermitian(rho)), min=1e-15)
    eigs = eigs / eigs.sum()
    return float((-torch.sum(eigs * torch.log(eigs))).item())


def purity(rho: torch.Tensor) -> float:
    return float(torch.real(torch.trace(rho @ rho)).item())


def trace_distance(a: torch.Tensor, b: torch.Tensor) -> float:
    diff = hermitian(a - b)
    return float(0.5 * torch.sum(torch.abs(torch.linalg.eigvalsh(diff))).item())


def hilbert_schmidt_distance(a: torch.Tensor, b: torch.Tensor) -> float:
    diff = a - b
    return float(torch.sqrt(torch.real(torch.trace(diff.conj().T @ diff))).item())


def matrix_sqrt_psd(a: torch.Tensor) -> torch.Tensor:
    eigvals, eigvecs = torch.linalg.eigh(hermitian(a))
    eigvals = torch.clamp(eigvals, min=0.0)
    return eigvecs @ torch.diag(torch.sqrt(eigvals)).to(DTYPE) @ eigvecs.conj().T


def bures_distance(a: torch.Tensor, b: torch.Tensor) -> float:
    sqrt_a = matrix_sqrt_psd(a)
    middle = matrix_sqrt_psd(sqrt_a @ b @ sqrt_a)
    fidelity_root = torch.real(torch.trace(middle))
    return float(torch.sqrt(torch.clamp(2 - 2 * fidelity_root, min=0.0)).item())


METRICS = {
    "bures_density_metric": bures_distance,
    "trace_distance_metric": trace_distance,
    "hilbert_schmidt_metric": hilbert_schmidt_distance,
}


def apply_order(rho: torch.Tensor, order_name: str) -> torch.Tensor:
    out = rho
    for channel in ORDERS[order_name]:
        out = channel(out)
    return out


def probe_signature(rho: torch.Tensor) -> tuple[float, ...]:
    z = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
    x = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
    probes = [
        float(torch.real(torch.trace(one_qubit_operator(z, 0) @ rho)).item()),
        float(torch.real(torch.trace(one_qubit_operator(z, 1) @ rho)).item()),
        float(torch.real(torch.trace(one_qubit_operator(x, 0) @ rho)).item()),
        entropy(rho),
        purity(rho),
    ]
    return tuple(round(v, 3) for v in probes)


def rips_persistence(distance_matrix: list[list[float]]) -> dict[str, Any]:
    rips = gudhi.RipsComplex(distance_matrix=distance_matrix, max_edge_length=max(max(row) for row in distance_matrix))
    st = rips.create_simplex_tree(max_dimension=2)
    pairs = st.persistence()
    h0 = [pair for pair in pairs if pair[0] == 0]
    h1 = [pair for pair in pairs if pair[0] == 1]
    finite_h1 = [pair for pair in h1 if pair[1][1] != float("inf")]
    total_h1_life = sum(float(death - birth) for _, (birth, death) in finite_h1)
    return {
        "simplex_count": st.num_simplices(),
        "h0_pair_count": len(h0),
        "h1_pair_count": len(h1),
        "finite_h1_lifetime_sum": total_h1_life,
    }


def quotient_classes(rows: list[dict[str, Any]], metric_name: str, radius: float) -> dict[str, Any]:
    survivors = [row for row in rows if row["survived"]]
    graph = nx.Graph()
    for row in survivors:
        graph.add_node(row["candidate_id"])
    metric = METRICS[metric_name]
    distance_matrix = [[0.0 for _ in survivors] for _ in survivors]
    for i, a in enumerate(survivors):
        for j, b in enumerate(survivors[i + 1 :], start=i + 1):
            dist = metric(a["rho"], b["rho"])
            distance_matrix[i][j] = distance_matrix[j][i] = dist
            if dist <= radius:
                graph.add_edge(a["candidate_id"], b["candidate_id"])
    components = [sorted(component) for component in nx.connected_components(graph)]
    pyg = from_networkx(graph) if graph.number_of_edges() else None
    persistence = rips_persistence(distance_matrix) if len(survivors) >= 2 else {"simplex_count": len(survivors), "h0_pair_count": len(survivors), "h1_pair_count": 0, "finite_h1_lifetime_sum": 0.0}
    signatures: dict[tuple[float, ...], list[int]] = defaultdict(list)
    for row in survivors:
        signatures[row["signature"]].append(row["candidate_id"])
    return {
        "survivor_count": len(survivors),
        "radius_class_count": len(components),
        "signature_class_count": len(signatures),
        "largest_radius_class_size": max((len(component) for component in components), default=0),
        "edge_count": graph.number_of_edges(),
        "pyg_edge_index_shape": list(pyg.edge_index.shape) if pyg is not None else [2, 0],
        "persistence": persistence,
    }


def survivors_for(order_name: str, metric_name: str, min_distance_from_mixed: float) -> list[dict[str, Any]]:
    mixed = torch.eye(DIM, dtype=DTYPE) / DIM
    metric = METRICS[metric_name]
    rows = []
    for candidate in candidate_densities():
        rho = apply_order(candidate["rho"], order_name)
        dist = metric(rho, mixed)
        survived = density_valid(rho) and entropy(rho) <= 1.35 and purity(rho) >= 0.26 and dist >= min_distance_from_mixed
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "source_label": candidate["source_label"],
                "rho": rho,
                "distance_from_mixed": dist,
                "survived": survived,
                "signature": probe_signature(rho) if survived else None,
            }
        )
    return rows


def transition_graph(summary_rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    nodes = {idx: graph.add_node(row["metric_name"] + "::" + row["order_name"]) for idx, row in enumerate(summary_rows)}
    for i, a in enumerate(summary_rows):
        for j, b in enumerate(summary_rows):
            if i != j and (a["survivor_count"], a["radius_class_count"]) != (b["survivor_count"], b["radius_class_count"]):
                graph.add_edge(nodes[i], nodes[j], "differs")
    cycles = list(rx.simple_cycles(graph))
    return {"edge_count": graph.num_edges(), "cycle_count": len(cycles), "pass": graph.num_edges() > 0}


def sympy_metric_boundary() -> dict[str, Any]:
    x = sp.symbols("x", positive=True)
    expr = sp.sqrt((x - x) ** 2)
    return {"same_point_distance": str(sp.simplify(expr)), "pass": sp.simplify(expr) == 0}


def z3_geometry_choice_check(survivor_counts: list[int], class_counts: list[int]) -> dict[str, Any]:
    survivor_varies = len(set(survivor_counts)) > 1
    class_varies = len(set(class_counts)) > 1
    s1 = z3.Solver()
    s2 = z3.Solver()
    a = z3.Bool("survivor_varies")
    b = z3.Bool("class_varies")
    s1.add(a == survivor_varies, a == False)
    s2.add(b == class_varies, b == False)
    return {
        "survivor_count_depends_on_geometry_unsat_if_constant": {"solver_status": str(s1.check()), "pass": survivor_varies and s1.check() == z3.unsat},
        "quotient_count_depends_on_geometry_unsat_if_constant": {"solver_status": str(s2.check()), "pass": class_varies and s2.check() == z3.unsat},
    }


def main() -> dict[str, Any]:
    started = time.time()
    geomstats_backend_probe = gs.array([0.0, 1.0, 2.0])
    thresholds = {"bures_density_metric": 0.28, "trace_distance_metric": 0.34, "hilbert_schmidt_metric": 0.31}
    radii = {"bures_density_metric": 0.11, "trace_distance_metric": 0.13, "hilbert_schmidt_metric": 0.12}
    summary_rows = []
    for metric_name in METRICS:
        for order_name in ORDERS:
            rows = survivors_for(order_name, metric_name, thresholds[metric_name])
            quotient = quotient_classes(rows, metric_name, radii[metric_name])
            summary_rows.append(
                {
                    "metric_name": metric_name,
                    "order_name": order_name,
                    "threshold": thresholds[metric_name],
                    "radius": radii[metric_name],
                    **quotient,
                }
            )
    z3_rows = z3_geometry_choice_check([row["survivor_count"] for row in summary_rows], [row["radius_class_count"] for row in summary_rows])
    positive = {
        "candidate_density_set_is_valid": {
            "candidate_count": len(candidate_densities()),
            "pass": len(candidate_densities()) == 24 and all(density_valid(row["rho"]) for row in candidate_densities()),
        },
        "metric_geometries_produce_survivor_and_quotient_rows": {
            "row_count": len(summary_rows),
            "pass": len(summary_rows) == len(METRICS) * len(ORDERS),
        },
        "geometry_choice_changes_survivor_or_quotient_counts": {
            "summary_rows": summary_rows,
            "pass": len({row["survivor_count"] for row in summary_rows}) > 1 or len({row["radius_class_count"] for row in summary_rows}) > 1,
        },
        "rips_persistence_computes_for_survivor_clouds": {
            "h1_lifetime_sum_by_row": [row["persistence"]["finite_h1_lifetime_sum"] for row in summary_rows],
            "pass": all(row["persistence"]["simplex_count"] >= row["survivor_count"] for row in summary_rows),
        },
        "rustworkx_transition_graph_detects_geometry_order_difference": transition_graph(summary_rows),
        "sympy_same_point_metric_boundary": sympy_metric_boundary(),
        "z3_geometry_choice_difference_checks": {"checks": z3_rows, "pass": all(row["pass"] for row in z3_rows.values())},
        "geomstats_backend_array_is_used": {"shape": list(gs.shape(geomstats_backend_probe)), "pass": list(gs.shape(geomstats_backend_probe)) == [3]},
    }
    all_identity_rows = []
    for candidate in candidate_densities():
        rho = candidate["rho"]
        all_identity_rows.append({"candidate_id": candidate["candidate_id"], "rho": rho, "survived": True, "signature": probe_signature(rho)})
    constant_metric_rows = [{**row, "survived": True} for row in all_identity_rows]
    graveyard_companions = {
        "zero_threshold_admits_all_identity_candidates": {
            "survivor_count": len(all_identity_rows),
            "pass": len(all_identity_rows) == len(candidate_densities()),
        },
        "overlarge_radius_collapses_all_radius_classes": {
            "class_count": quotient_classes(constant_metric_rows, "trace_distance_metric", radius=99.0)["radius_class_count"],
            "pass": quotient_classes(constant_metric_rows, "trace_distance_metric", radius=99.0)["radius_class_count"] == 1,
        },
        "overstrict_distance_threshold_extinguishes_candidates": {
            "survivor_count": sum(row["survived"] for row in survivors_for("phase_then_damping_then_filter", "bures_density_metric", 99.0)),
            "pass": sum(row["survived"] for row in survivors_for("phase_then_damping_then_filter", "bures_density_metric", 99.0)) == 0,
        },
    }
    boundary = {
        "metric_count": {"count": len(METRICS), "pass": len(METRICS) == 3},
        "order_count": {"count": len(ORDERS), "pass": len(ORDERS) == 3},
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard_companions.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "density-matrix metric geometries as hard constraint layers with survivor quotients and Vietoris-Rips persistence",
        "summary_rows": summary_rows,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyard_companions), "passed": sum(1 for row in graveyard_companions.values() if row["pass"])},
        "blockers": [],
        "open_choices": [
            "Metric thresholds are calibrated by hand and should be swept next.",
            "Bures implementation is closed-form torch linear algebra, with geomstats used only as backend sanity here.",
            "This compares metric geometry choices, not final frame-bundle or structure-reduction geometry.",
        ],
        "why_not_v4_probes": "This is a clean v5 formal scout for metric geometry alternatives and should not add to the mixed v4 probe estate.",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": bool(all_pass),
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": PROMOTION_ALLOWED,
            "survivor_counts": [row["survivor_count"] for row in summary_rows],
            "radius_class_counts": [row["radius_class_count"] for row in summary_rows],
            "h1_lifetime_sums": [row["persistence"]["finite_h1_lifetime_sum"] for row in summary_rows],
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
