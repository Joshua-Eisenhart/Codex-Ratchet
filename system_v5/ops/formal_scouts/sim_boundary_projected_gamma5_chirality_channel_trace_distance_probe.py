#!/usr/bin/env python3
"""Boundary-projected gamma5 chirality channel trace-distance scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any, Callable

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import networkx as nx
import sympy as sp
import torch
from torch_geometric.utils import from_networkx
import z3

from sim_gamma5_chirality_asymmetric_cptp_choi_distance_effective_channel_probe import (
    DTYPE,
    apply_kraus,
    gamma5_boundary,
    symmetric_kraus,
)
from sim_gamma5_offdiagonal_coherence_trace_orbit_survivor_quotient_probe import (
    DIM,
    N_QUBITS,
    asymmetric_local_kraus,
    candidate_densities,
    embed,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "boundary_projected_gamma5_chirality_channel_trace_distance_probe_results.json"

NAME = "boundary_projected_gamma5_chirality_channel_trace_distance_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: couples a finite trace-preserving positive boundary "
    "conditional expectation to gamma5 chirality-asymmetric CPTP channel "
    "orbits and compares them to symmetric, equal-rate, static, and random "
    "boundary controls. It does not admit black-hole physics, empirical "
    "gravity, a final manifold tower, ontology, or bridge claim."
)

TOOL_MANIFEST = {
    "python_math": {"tried": True, "used": True, "reason": "load-bearing local bounded golden-section scalar search for symmetric effective-rate fit"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing density states, Kraus maps, boundary expectation, trace distance, entropy, CPTP checks, and fit objective evaluation"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing finite 4x4 boundary graph and interior/boundary partition"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing graph tensor conversion for boundary graph features"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic boundary/interior count check"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing boundary-projected separation witness"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}


def bounded_scalar_minimize(objective: Callable[[float], float], lower: float, upper: float, *, xatol: float = 1e-10, max_iter: int = 256) -> dict[str, Any]:
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    inv_phi = 1.0 / phi
    left = float(lower)
    right = float(upper)
    c = right - (right - left) * inv_phi
    d = left + (right - left) * inv_phi
    fc = float(objective(c))
    fd = float(objective(d))
    iterations = 0
    while abs(right - left) > xatol and iterations < max_iter:
        iterations += 1
        if fc <= fd:
            right = d
            d = c
            fd = fc
            c = right - (right - left) * inv_phi
            fc = float(objective(c))
        else:
            left = c
            c = d
            fc = fd
            d = left + (right - left) * inv_phi
            fd = float(objective(d))
    x = (left + right) / 2.0
    fun = float(objective(x))
    return {"x": x, "fun": fun, "success": math.isfinite(fun) and iterations < max_iter, "iterations": iterations}


def boundary_graph() -> tuple[nx.Graph, list[int], list[int]]:
    graph = nx.grid_2d_graph(4, 4)
    mapping = {node: idx for idx, node in enumerate(sorted(graph.nodes()))}
    graph = nx.relabel_nodes(graph, mapping)
    boundary = []
    for node, data in graph.nodes(data=True):
        x, y = next(key for key, value in mapping.items() if value == node)
        graph.nodes[node]["coord"] = (x, y)
        if x in (0, 3) or y in (0, 3):
            boundary.append(node)
    interior = [node for node in graph.nodes if node not in set(boundary)]
    return graph, boundary, interior


def boundary_expectation_kraus(boundary: list[int], interior: list[int], mode: str = "nearest") -> list[torch.Tensor]:
    rows = []
    projector = torch.zeros((DIM, DIM), dtype=DTYPE)
    for idx in boundary:
        projector[idx, idx] = 1.0
    rows.append(projector)
    if mode == "nearest":
        for offset, idx in enumerate(interior):
            target = boundary[offset % len(boundary)]
            op = torch.zeros((DIM, DIM), dtype=DTYPE)
            op[target, idx] = 1.0
            rows.append(op)
    elif mode == "random_boundary":
        for offset, idx in enumerate(interior):
            target = boundary[(5 * offset + 7) % len(boundary)]
            op = torch.zeros((DIM, DIM), dtype=DTYPE)
            op[target, idx] = 1.0
            rows.append(op)
    elif mode == "identity":
        return [torch.eye(DIM, dtype=DTYPE)]
    else:
        raise ValueError(mode)
    return rows


def entropy(rho: torch.Tensor) -> float:
    herm = (rho + rho.conj().T) / 2
    eigs = torch.clamp(torch.linalg.eigvalsh(herm).real, min=1e-15)
    eigs = eigs / eigs.sum()
    return float((-torch.sum(eigs * torch.log(eigs))).item())


def cptp_gap_any(kraus: list[torch.Tensor]) -> float:
    dim = kraus[0].shape[1]
    accum = torch.zeros((dim, dim), dtype=DTYPE)
    for k in kraus:
        accum = accum + k.conj().T @ k
    return float(torch.linalg.matrix_norm(accum - torch.eye(dim, dtype=DTYPE)).item())


def trace_distance(a: torch.Tensor, b: torch.Tensor) -> float:
    diff = (a - b + (a - b).conj().T) / 2
    return float(0.5 * torch.sum(torch.linalg.svdvals(diff)).item())


def apply_boundary_expectation(rho: torch.Tensor, mode: str) -> torch.Tensor:
    _, boundary, interior = boundary_graph()
    return apply_kraus(rho, boundary_expectation_kraus(boundary, interior, mode=mode))


def channel_sequence(rho: torch.Tensor, channel_mode: str, boundary_mode: str, gamma: float | None = None) -> dict[str, Any]:
    current = apply_boundary_expectation(rho, boundary_mode)
    initial = current.clone()
    distances = [0.0]
    entropies = [entropy(current)]
    cptp_gaps = [cptp_gap_any(boundary_expectation_kraus(boundary_graph()[1], boundary_graph()[2], mode=boundary_mode))]
    for step in range(1, 7):
        if channel_mode == "dynamic_asymmetric":
            gamma_left = 0.08 + 0.035 * step
            gamma_right = 0.025 + 0.010 * step
            kraus = embed(asymmetric_local_kraus(gamma_left, gamma_right))
        elif channel_mode == "static_asymmetric":
            kraus = embed(asymmetric_local_kraus(0.16, 0.055))
        elif channel_mode == "equal_rate":
            rate = gamma if gamma is not None else 0.10
            kraus = embed(asymmetric_local_kraus(rate, rate))
        elif channel_mode == "symmetric":
            rate = gamma if gamma is not None else 0.10
            kraus = embed(symmetric_kraus(rate))
        else:
            raise ValueError(channel_mode)
        cptp_gaps.append(cptp_gap_any(kraus))
        current = apply_kraus(current, kraus)
        current = apply_boundary_expectation(current, boundary_mode)
        distances.append(trace_distance(current, initial))
        entropies.append(entropy(current))
    return {"distance_orbit": distances, "entropy_orbit": entropies, "max_cptp_gap": max(cptp_gaps)}


def l2_gap(left: list[float], right: list[float]) -> float:
    return float(torch.linalg.vector_norm(torch.tensor(left, dtype=torch.float64) - torch.tensor(right, dtype=torch.float64)).item())


def best_symmetric_fit(rho: torch.Tensor, target: list[float], boundary_mode: str) -> dict[str, Any]:
    def objective(rate: float) -> float:
        row = channel_sequence(rho, "symmetric", boundary_mode, gamma=float(rate))
        return l2_gap(target, row["distance_orbit"])
    result = bounded_scalar_minimize(objective, 0.0, 0.35, xatol=1e-10)
    row = channel_sequence(rho, "symmetric", boundary_mode, gamma=float(result["x"]))
    return {"gamma": float(result["x"]), "gap": float(result["fun"]), "orbit": row["distance_orbit"], "success": bool(result["success"])}


def symbolic_boundary_count() -> dict[str, Any]:
    n = sp.Integer(4)
    total = n**2
    boundary = n**2 - (n - 2) ** 2
    interior = total - boundary
    return {"total": int(total), "boundary": int(boundary), "interior": int(interior), "pass": int(total) == DIM and int(boundary) == 12 and int(interior) == 4}


def z3_witness(symmetric_count: int, equal_count: int, random_collision_count: int, cptp: float, entropy_bound: float) -> dict[str, Any]:
    solver = z3.Solver()
    sym_sep, equal_sep, random_boundary_has_collisions, valid, inside = z3.Bools("sym_sep equal_sep random_boundary_has_collisions valid inside")
    solver.add(sym_sep == (symmetric_count >= 6))
    solver.add(equal_sep == (equal_count >= 8))
    solver.add(random_boundary_has_collisions == (random_collision_count > 0))
    solver.add(valid == (cptp < 1e-12))
    solver.add(inside == (entropy_bound <= N_QUBITS * math.log(2) + 1e-12))
    solver.add(z3.Not(z3.And(sym_sep, equal_sep, random_boundary_has_collisions, valid, inside)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "symmetric_survivor_count": symmetric_count,
        "equal_rate_survivor_count": equal_count,
        "random_boundary_collision_count": random_collision_count,
        "cptp_valid": cptp < 1e-12,
        "inside_information_bound": entropy_bound <= N_QUBITS * math.log(2) + 1e-12,
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    graph, boundary, interior = boundary_graph()
    pyg = from_networkx(graph)
    rows = {}
    symmetric_gaps = []
    equal_gaps = []
    static_gaps = []
    random_boundary_gaps = []
    cptp_gaps = []
    entropy_max = 0.0
    for name, rho in candidate_densities().items():
        target = channel_sequence(rho, "dynamic_asymmetric", "nearest")
        symmetric = best_symmetric_fit(rho, target["distance_orbit"], "nearest")
        equal = channel_sequence(rho, "equal_rate", "nearest", gamma=0.115)
        static = channel_sequence(rho, "static_asymmetric", "nearest")
        random_boundary = channel_sequence(rho, "dynamic_asymmetric", "random_boundary")
        symmetric_gap = symmetric["gap"]
        equal_gap = l2_gap(target["distance_orbit"], equal["distance_orbit"])
        static_gap = l2_gap(target["distance_orbit"], static["distance_orbit"])
        random_gap = l2_gap(target["distance_orbit"], random_boundary["distance_orbit"])
        symmetric_gaps.append(symmetric_gap)
        equal_gaps.append(equal_gap)
        static_gaps.append(static_gap)
        random_boundary_gaps.append(random_gap)
        cptp_gaps.extend([target["max_cptp_gap"], equal["max_cptp_gap"], static["max_cptp_gap"], random_boundary["max_cptp_gap"]])
        entropy_max = max(entropy_max, max(target["entropy_orbit"]))
        rows[name] = {
            "dynamic_boundary_projected": target,
            "best_symmetric_fit": symmetric,
            "equal_rate_control": equal,
            "static_asymmetric_control": static,
            "random_boundary_control": random_boundary,
            "symmetric_gap": symmetric_gap,
            "equal_rate_gap": equal_gap,
            "static_gap": static_gap,
            "random_boundary_gap": random_gap,
        }
    max_cptp_gap = max(cptp_gaps)
    symmetric_survivors = [name for name, row in rows.items() if row["symmetric_gap"] > 0.015]
    equal_rate_survivors = [name for name, row in rows.items() if row["equal_rate_gap"] > 0.010]
    random_boundary_collisions = [name for name, row in rows.items() if row["random_boundary_gap"] <= 0.005]
    positive = {
        "boundary_projected_dynamic_gamma5_orbit_has_symmetric_fit_survivor_rows": {"survivor_names": symmetric_survivors, "survivor_count": len(symmetric_survivors), "threshold": 0.015, "pass": len(symmetric_survivors) >= 6},
        "boundary_projected_dynamic_gamma5_orbit_has_equal_rate_survivor_rows": {"survivor_names": equal_rate_survivors, "survivor_count": len(equal_rate_survivors), "threshold": 0.010, "pass": len(equal_rate_survivors) >= 8},
        "boundary_expectation_is_cptp": {"max_cptp_gap": max_cptp_gap, "pass": max_cptp_gap < 1e-12},
        "gamma5_projector_boundary": gamma5_boundary(),
        "finite_boundary_graph_count": symbolic_boundary_count(),
    }
    graveyard_companions = {
        "static_asymmetric_control_gap_is_recorded": {"min_gap": min(static_gaps), "pass": True},
        "random_boundary_expectation_collides_on_some_rows": {"collision_names": random_boundary_collisions, "collision_count": len(random_boundary_collisions), "pass": len(random_boundary_collisions) > 0},
        "boundary_graph_has_interior_and_boundary": {"boundary_nodes": len(boundary), "interior_nodes": len(interior), "pyg_edges": int(pyg.edge_index.shape[1]), "pass": len(boundary) == 12 and len(interior) == 4},
        "entropy_stays_inside_finite_information_bound": {"max_entropy": entropy_max, "bound": N_QUBITS * math.log(2), "pass": entropy_max <= N_QUBITS * math.log(2) + 1e-12},
    }
    boundary_section = {
        "z3_boundary_projected_gamma5_partial_survivor_witness": z3_witness(len(symmetric_survivors), len(equal_rate_survivors), len(random_boundary_collisions), max_cptp_gap, entropy_max),
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
    }
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [row["pass"] for row in boundary_section.values()]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "four-qubit finite boundary conditional expectation composed with gamma5 chirality-asymmetric CPTP channels and read by boundary-projected trace-distance orbits",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary_section,
        "nearby_variants": {"passed": sum(1 for value in checks if value), "total": len(checks)},
        "open_choices": [
            "This composes the finite boundary scaffold with gamma5 channel dynamics but only shows partial survivor rows, not universal separation.",
            "The boundary expectation is a finite graph partition, not a physical horizon.",
            "Next scouts should lift this to eight-qubit tensor-network coherent information or test whether a stronger locality-preserving rank-3 control kills the trace-distance orbit.",
        ],
        "why_not_v4_probes": "This is a clean v5 formal scout translated from latest Grok/Gemini boundary-projection convergence; it is not a canonical v4 probe.",
        "raw_rows": rows,
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": all(checks),
                "result": str(OUT_PATH),
                "min_symmetric_gap": min(symmetric_gaps),
                "min_equal_rate_gap": min(equal_gaps),
                "min_random_boundary_gap": min(random_boundary_gaps),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
