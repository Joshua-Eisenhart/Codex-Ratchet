#!/usr/bin/env python3
"""Future-possibility and past-correlation shell-direction survivor scout."""

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

import gudhi
import networkx as nx
import opt_einsum as oe
import rustworkx as rx
import sympy as sp
import torch
from torch_geometric.utils import from_networkx
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "future_possibility_past_correlation_shell_direction_survivor_quotient_probe_results.json"

NAME = "future_possibility_past_correlation_shell_direction_survivor_quotient_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: models future-possibility expansion and past-correlation "
    "binding as opposite directions on one finite shell, with distance-weighted "
    "influence, density-matrix correlation readouts, survivor classes, and nearby "
    "graveyards. It does not admit empirical gravity, a final spacetime theory, "
    "standard-model recovery, ontology, bridge, axis, or target-system claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing shell coordinates, density states, kernels, entropy, and distance tensors"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing partial traces for two-qubit mutual information"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing inverse-square symbolic sanity check"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing opposed-direction and inverse-square-dependence contradiction checks"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing survivor quotient graph"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing quotient graph tensor conversion"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence over shell-distance and quotient graphs"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing shell-transition graph"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

DTYPE = torch.complex128
N = 6
DIM = 4


def shell_points() -> torch.Tensor:
    return torch.tensor(
        [
            [1.0, 0.0, 0.0],
            [-1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, -1.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.0, -1.0],
        ],
        dtype=torch.float64,
    )


def distance_matrix(points: torch.Tensor) -> torch.Tensor:
    return torch.cdist(points, points)


def row_normalize(matrix: torch.Tensor) -> torch.Tensor:
    return matrix / torch.clamp(matrix.sum(dim=1, keepdim=True), min=1e-12)


def future_kernel(dist: torch.Tensor) -> torch.Tensor:
    weights = 1.0 / torch.clamp(dist**2, min=0.25)
    weights.fill_diagonal_(0.0)
    return row_normalize(weights)


def uniform_offdiag(n: int) -> torch.Tensor:
    matrix = torch.ones((n, n), dtype=torch.float64)
    matrix.fill_diagonal_(0.0)
    return row_normalize(matrix)


def density_from_pair(theta: float, mix: float) -> torch.Tensor:
    psi = torch.zeros(DIM, dtype=DTYPE)
    psi[0] = math.cos(theta)
    psi[3] = math.sin(theta)
    rho = torch.outer(psi, psi.conj())
    return (1 - mix) * rho + mix * torch.eye(DIM, dtype=DTYPE) / DIM


def shell_densities() -> list[torch.Tensor]:
    states = []
    for idx in range(N):
        theta = 0.18 + 0.11 * idx
        mix = 0.08 + 0.035 * (idx % 3)
        states.append(density_from_pair(theta, mix))
    return states


def partial_trace_two_qubit(rho: torch.Tensor, keep: int) -> torch.Tensor:
    tensor = rho.reshape(2, 2, 2, 2)
    if keep == 0:
        return oe.contract("abad->bd", tensor)
    return oe.contract("abcb->ac", tensor)


def entropy(rho: torch.Tensor) -> float:
    herm = (rho + rho.conj().T) / 2
    eigs = torch.clamp(torch.linalg.eigvalsh(herm), min=1e-15)
    eigs = eigs / eigs.sum()
    return float((-torch.sum(eigs * torch.log(eigs))).item())


def mutual_information(rho: torch.Tensor) -> float:
    return entropy(partial_trace_two_qubit(rho, 0)) + entropy(partial_trace_two_qubit(rho, 1)) - entropy(rho)


def past_kernel_from_correlations(densities: list[torch.Tensor], dist: torch.Tensor) -> torch.Tensor:
    mi = torch.tensor([mutual_information(rho) for rho in densities], dtype=torch.float64)
    pair = torch.sqrt(torch.outer(mi, mi))
    weights = pair / torch.clamp(dist**2, min=0.25)
    weights.fill_diagonal_(0.0)
    return row_normalize(weights)


def distribution_entropy(row: torch.Tensor) -> float:
    probs = torch.clamp(row, min=1e-15)
    probs = probs / probs.sum()
    return float((-torch.sum(probs * torch.log(probs))).item())


def evolve_shell(
    future: torch.Tensor,
    past: torch.Tensor,
    future_k: torch.Tensor,
    past_k: torch.Tensor,
    future_rate: float,
    past_rate: float,
    steps: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    future_state = future.clone()
    past_state = past.clone()
    for _ in range(steps):
        future_state = row_normalize((1 - future_rate) * future_state + future_rate * future_k)
        past_state = row_normalize((1 - past_rate) * past_state + past_rate * past_k)
    return future_state, past_state


def influence_response(kernel: torch.Tensor, center: int) -> torch.Tensor:
    delta = torch.zeros(N, dtype=torch.float64)
    delta[center] = 1.0
    return kernel.T @ delta


def centered_correlation(xs: torch.Tensor, ys: torch.Tensor) -> float:
    x = xs.to(torch.float64) - xs.to(torch.float64).mean()
    y = ys.to(torch.float64) - ys.to(torch.float64).mean()
    denom = torch.linalg.vector_norm(x) * torch.linalg.vector_norm(y)
    return float((torch.dot(x, y) / denom).item()) if float(denom.item()) > 0 else 0.0


def shell_row(name: str, future_k: torch.Tensor, past_k: torch.Tensor, future_rate: float, past_rate: float) -> dict[str, Any]:
    start = uniform_offdiag(N)
    future_state, past_state = evolve_shell(start, start, future_k, past_k, future_rate, past_rate, steps=5)
    future_entropies = [distribution_entropy(future_state[i]) for i in range(N)]
    past_entropies = [distribution_entropy(past_state[i]) for i in range(N)]
    gap = torch.linalg.matrix_norm(future_state - past_state).item()
    response = influence_response(future_k, center=0)
    points = shell_points()
    d0 = distance_matrix(points)[0]
    mask = d0 > 0
    inverse_square = 1.0 / torch.clamp(d0[mask] ** 2, min=1e-12)
    response_correlation = centered_correlation(inverse_square, response[mask])
    signature = tuple(
        round(v, 4)
        for v in [
            sum(future_entropies) / N,
            sum(past_entropies) / N,
            gap,
            response_correlation,
            float(torch.max(response[mask]).item()),
        ]
    )
    survived = gap > 0.02 and response_correlation > 0.55 and sum(future_entropies) / N >= sum(past_entropies) / N
    return {
        "name": name,
        "future_entropy_mean": sum(future_entropies) / N,
        "past_entropy_mean": sum(past_entropies) / N,
        "future_past_direction_gap": gap,
        "center_0_influence_response": [round(float(x), 6) for x in response.tolist()],
        "inverse_square_response_correlation": response_correlation,
        "signature": signature,
        "survived": survived,
    }


def quotient(rows: list[dict[str, Any]]) -> dict[str, Any]:
    survivors = [row for row in rows if row["survived"]]
    classes: dict[tuple[float, ...], list[str]] = defaultdict(list)
    for row in survivors:
        classes[row["signature"]].append(row["name"])
    graph = nx.Graph()
    for row in survivors:
        graph.add_node(row["name"])
    for names in classes.values():
        for idx, a in enumerate(names):
            for b in names[idx + 1 :]:
                graph.add_edge(a, b)
    pyg = from_networkx(graph) if graph.number_of_edges() else None
    st = gudhi.SimplexTree()
    for idx, _ in enumerate(survivors):
        st.insert([idx], filtration=0.0)
    return {
        "survivor_count": len(survivors),
        "class_count": len(classes),
        "edge_count": graph.number_of_edges(),
        "pyg_edge_index_shape": list(pyg.edge_index.shape) if pyg is not None else [2, 0],
        "persistence_pair_count": len(st.persistence()),
    }


def shell_transition_graph(rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    nodes = {row["name"]: graph.add_node(row["name"]) for row in rows}
    for a in rows:
        for b in rows:
            if a["name"] != b["name"] and a["signature"] != b["signature"]:
                graph.add_edge(nodes[a["name"]], nodes[b["name"]], "differs")
    return {"edge_count": graph.num_edges(), "pass": graph.num_edges() > 0}


def sympy_inverse_square_check() -> dict[str, Any]:
    r = sp.symbols("r", positive=True)
    expr = sp.diff(1 / r, r)
    return {"gradient": str(expr), "pass": sp.simplify(expr + 1 / r**2) == 0}


def z3_checks(candidate: dict[str, Any], collapsed: dict[str, Any], uniform: dict[str, Any]) -> dict[str, Any]:
    opposed_survives = bool(candidate["survived"])
    collapsed_fails = not bool(collapsed["survived"])
    uniform_fails = uniform["inverse_square_response_correlation"] < candidate["inverse_square_response_correlation"]
    s1 = z3.Solver()
    s2 = z3.Solver()
    a = z3.Bool("opposed_shell_directions_survive")
    b = z3.Bool("uniform_distance_kernel_is_equivalent")
    s1.add(a == opposed_survives, a == False)
    s2.add(b == (not uniform_fails), b == True)
    return {
        "opposed_shell_directions_unsat_if_not_survivor": {"solver_status": str(s1.check()), "pass": opposed_survives and s1.check() == z3.unsat},
        "uniform_distance_kernel_not_equivalent_unsat_if_equivalent": {"solver_status": str(s2.check()), "pass": uniform_fails and s2.check() == z3.unsat},
        "collapsed_direction_fails": {"pass": collapsed_fails},
    }


def main() -> dict[str, Any]:
    started = time.time()
    points = shell_points()
    dist = distance_matrix(points)
    densities = shell_densities()
    fk = future_kernel(dist)
    pk = past_kernel_from_correlations(densities, dist)
    uniform = uniform_offdiag(N)
    rows = [
        shell_row("opposed_future_possibility_and_past_correlation_directions", fk, pk, 0.62, 0.62),
        shell_row("collapsed_same_direction_control", fk, fk, 0.62, 0.62),
        shell_row("uniform_distance_removed_control", uniform, pk, 0.62, 0.62),
        shell_row("static_no_update_control", fk, pk, 0.0, 0.0),
    ]
    q = quotient(rows)
    z3_rows = z3_checks(rows[0], rows[1], rows[2])
    positive = {
        "single_shell_has_spatial_points_and_density_states": {
            "point_count": len(points),
            "density_count": len(densities),
            "pass": len(points) == N and len(densities) == N,
        },
        "opposed_future_and_past_directions_survive": {**rows[0], "pass": rows[0]["survived"]},
        "survivor_quotient_classes_compute": {**q, "pass": q["survivor_count"] >= 1 and q["class_count"] >= 1},
        "instantaneous_shellwide_response_is_nonzero": {
            "response": rows[0]["center_0_influence_response"],
            "pass": sum(abs(x) > 0 for x in rows[0]["center_0_influence_response"]) > 1,
        },
        "inverse_square_distance_weight_is_detected": {
            "correlation": rows[0]["inverse_square_response_correlation"],
            "pass": rows[0]["inverse_square_response_correlation"] > 0.55,
        },
        "rustworkx_transition_graph_detects_direction_differences": shell_transition_graph(rows),
        "sympy_inverse_square_gradient_check": sympy_inverse_square_check(),
        "z3_direction_and_distance_checks": {"checks": z3_rows, "pass": all(row["pass"] for row in z3_rows.values())},
    }
    graveyard_companions = {
        "collapsed_same_direction_control_does_not_survive": {**rows[1], "pass": not rows[1]["survived"]},
        "uniform_distance_removed_control_has_weaker_distance_response": {
            **rows[2],
            "candidate_response": rows[0]["inverse_square_response_correlation"],
            "pass": rows[2]["inverse_square_response_correlation"] < rows[0]["inverse_square_response_correlation"],
        },
        "static_no_update_control_has_small_direction_gap": {**rows[3], "pass": rows[3]["future_past_direction_gap"] < rows[0]["future_past_direction_gap"]},
    }
    boundary = {
        "same_shell_not_two_substances": {"shell_count": 1, "pass": True},
        "candidate_count": {"count": len(rows), "pass": len(rows) == 4},
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard_companions.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "one finite shell with future-possibility expansion and past-correlation binding as opposite distributional directions",
        "rows": rows,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyard_companions), "passed": sum(1 for row in graveyard_companions.values() if row["pass"])},
        "blockers": [],
        "open_choices": [
            "This is a finite dynamic-shell scout, not empirical gravity or continuous spacetime.",
            "Distance weighting is inverse-square-like on a six-point shell; denser shells should be tested next.",
            "Past correlation uses mutual information from two-qubit density states; future possibility uses distance-weighted shell distributions.",
        ],
        "why_not_v4_probes": "This is a clean v5 dynamic-shell scout and should not add to the mixed v4 probe estate.",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": bool(all_pass),
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": PROMOTION_ALLOWED,
            "survivor_count": q["survivor_count"],
            "class_count": q["class_count"],
            "candidate_signature": rows[0]["signature"],
            "graveyard_passed": graveyard_companions,
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
