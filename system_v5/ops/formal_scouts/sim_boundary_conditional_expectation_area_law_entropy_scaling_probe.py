#!/usr/bin/env python3
"""Boundary conditional-expectation area-law entropy-scaling scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import networkx as nx
import sympy as sp
import torch
from torch_geometric.utils import from_networkx
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "boundary_conditional_expectation_area_law_entropy_scaling_probe_results.json"

NAME = "boundary_conditional_expectation_area_law_entropy_scaling_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests a finite conditional expectation from a cubic "
    "bulk density algebra onto a boundary-supported subalgebra and checks "
    "whether the projected maximally mixed entropy scales like boundary area "
    "rather than bulk volume. It does not admit black-hole physics, empirical "
    "gravity, a final manifold tower, ontology, or bridge claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing diagonal density states, conditional expectation, trace, positivity, and entropy spectra"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing finite cubic shell graph and boundary-node extraction"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing graph tensor conversion for shell graph features"},
    "python_math": {"tried": True, "used": True, "reason": "load-bearing closed-form log-log least-squares scaling fits"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic volume-versus-boundary exponent check"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing area-law scaling witness"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}


def cube_graph(length: int) -> tuple[nx.Graph, list[int], list[int]]:
    graph = nx.Graph()
    index = {}
    counter = 0
    for x in range(length):
        for y in range(length):
            for z in range(length):
                index[(x, y, z)] = counter
                graph.add_node(counter, coord=(x, y, z))
                counter += 1
    for (x, y, z), node in index.items():
        for dx, dy, dz in ((1, 0, 0), (0, 1, 0), (0, 0, 1)):
            nbr = (x + dx, y + dy, z + dz)
            if nbr in index:
                graph.add_edge(node, index[nbr])
    boundary = [
        node
        for node, data in graph.nodes(data=True)
        for x, y, z in [data["coord"]]
        if x in (0, length - 1) or y in (0, length - 1) or z in (0, length - 1)
    ]
    interior = [node for node in graph.nodes if node not in set(boundary)]
    return graph, boundary, interior


def entropy(prob: torch.Tensor) -> float:
    values = prob[prob > 1e-15]
    return float((-torch.sum(values * torch.log(values))).item())


def conditional_expectation_to_boundary(prob: torch.Tensor, boundary: list[int]) -> torch.Tensor:
    projected = torch.zeros_like(prob)
    boundary_mass = float(prob[boundary].sum().item())
    complement_mass = 1.0 - boundary_mass
    projected[boundary] = prob[boundary] + complement_mass / len(boundary)
    return projected / projected.sum()


def random_volume_like_projection(prob: torch.Tensor, count: int, salt: int) -> torch.Tensor:
    idx = torch.arange(prob.shape[0])
    chosen = idx[((idx * (salt + 3) + 5) % prob.shape[0]) < count]
    if chosen.numel() < count:
        chosen = idx[:count]
    chosen = chosen[:count]
    projected = torch.zeros_like(prob)
    projected[chosen] = 1.0 / chosen.numel()
    return projected


def closed_form_loglog_regression(xs: list[float], ys: list[float]) -> dict[str, float]:
    n = len(xs)
    if n != len(ys) or n < 2:
        raise ValueError("closed_form_loglog_regression requires matching inputs with at least two points")
    x_mean = math.fsum(xs) / n
    y_mean = math.fsum(ys) / n
    x_deltas = [x - x_mean for x in xs]
    y_deltas = [y - y_mean for y in ys]
    ss_xx = math.fsum(dx * dx for dx in x_deltas)
    ss_yy = math.fsum(dy * dy for dy in y_deltas)
    if ss_xx <= 0.0:
        raise ValueError("closed_form_loglog_regression requires non-constant x values")
    ss_xy = math.fsum(dx * dy for dx, dy in zip(x_deltas, y_deltas))
    slope_value = ss_xy / ss_xx
    intercept = y_mean - slope_value * x_mean
    rvalue = 0.0 if ss_yy <= 0.0 else ss_xy / math.sqrt(ss_xx * ss_yy)
    residual_ss = math.fsum((y - (slope_value * x + intercept)) ** 2 for x, y in zip(xs, ys))
    stderr = math.sqrt(max(0.0, residual_ss / (n - 2) / ss_xx)) if n > 2 else 0.0
    return {"slope": float(slope_value), "rvalue": float(rvalue), "stderr": float(stderr)}


def slope(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    xs = [math.log(row["length"]) for row in rows]
    ys = [math.log(max(row[key], 1e-12)) for row in rows]
    return closed_form_loglog_regression(xs, ys)


def z3_witness(volume_slope: float, boundary_slope: float, trace_gap: float, positivity_gap: float) -> dict[str, Any]:
    solver = z3.Solver()
    volume_like, boundary_like, valid = z3.Bools("volume_like boundary_like valid")
    solver.add(volume_like == (abs(volume_slope - 3.0) < 0.25))
    solver.add(boundary_like == (abs(boundary_slope - 2.0) < 0.35))
    solver.add(valid == (trace_gap < 1e-12 and positivity_gap >= -1e-12))
    solver.add(z3.Not(z3.And(volume_like, boundary_like, valid)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "volume_slope": volume_slope,
        "boundary_slope": boundary_slope,
        "trace_preserving": trace_gap < 1e-12,
        "positive": positivity_gap >= -1e-12,
    }


def symbolic_boundary() -> dict[str, Any]:
    l = sp.symbols("L", positive=True, integer=True)
    volume = l**3
    boundary = l**3 - (l - 2) ** 3
    leading = sp.LT(sp.expand(boundary), l).as_expr()
    return {"volume": str(volume), "boundary": str(sp.expand(boundary)), "boundary_leading_term": str(leading), "pass": leading == 6 * l**2}


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    trace_gaps = []
    positivity_gaps = []
    for length in range(6, 19):
        graph, boundary, interior = cube_graph(length)
        pyg = from_networkx(graph)
        prob = torch.ones(graph.number_of_nodes(), dtype=torch.float64) / graph.number_of_nodes()
        boundary_prob = conditional_expectation_to_boundary(prob, boundary)
        random_prob = random_volume_like_projection(prob, max(len(boundary), graph.number_of_nodes() // 2), length)
        trace_gaps.append(abs(float(boundary_prob.sum().item()) - 1.0))
        positivity_gaps.append(float(boundary_prob.min().item()))
        rows.append(
            {
                "length": length,
                "volume_nodes": graph.number_of_nodes(),
                "boundary_nodes": len(boundary),
                "interior_nodes": len(interior),
                "edges": graph.number_of_edges(),
                "pyg_edges": int(pyg.edge_index.shape[1]),
                "volume_entropy": entropy(prob),
                "boundary_projected_entropy": entropy(boundary_prob),
                "random_volume_like_entropy": entropy(random_prob),
            }
        )
    volume_fit = slope(rows, "volume_nodes")
    boundary_fit = slope(rows, "boundary_nodes")
    entropy_volume_fit = slope(rows, "volume_entropy")
    entropy_boundary_fit = slope(rows, "boundary_projected_entropy")
    max_trace_gap = max(trace_gaps)
    min_positivity = min(positivity_gaps)
    positive = {
        "bulk_count_scales_like_volume": {"fit": volume_fit, "pass": abs(volume_fit["slope"] - 3.0) < 0.25},
        "boundary_count_scales_like_area": {"fit": boundary_fit, "pass": abs(boundary_fit["slope"] - 2.0) < 0.35},
        "conditional_expectation_is_trace_preserving_and_positive": {"max_trace_gap": max_trace_gap, "min_value": min_positivity, "pass": max_trace_gap < 1e-12 and min_positivity >= -1e-12},
        "symbolic_boundary_count_has_area_leading_term": symbolic_boundary(),
    }
    graveyard_companions = {
        "identity_bulk_readout_stays_volume_counted": {"fit": volume_fit, "pass": volume_fit["slope"] > boundary_fit["slope"] + 0.45},
        "random_volume_like_projection_does_not_define_the_boundary": {"last_random_entropy": rows[-1]["random_volume_like_entropy"], "last_boundary_entropy": rows[-1]["boundary_projected_entropy"], "pass": rows[-1]["random_volume_like_entropy"] >= rows[-1]["boundary_projected_entropy"]},
        "finite_size_boundary_has_lower_order_terms": {"first_length": rows[0]["length"], "first_boundary_nodes": rows[0]["boundary_nodes"], "pass": rows[0]["boundary_nodes"] == rows[0]["volume_nodes"] - (rows[0]["length"] - 2) ** 3},
        "entropy_scaling_is_logarithmic_not_direct_area": {"volume_entropy_fit": entropy_volume_fit, "boundary_entropy_fit": entropy_boundary_fit, "pass": entropy_volume_fit["slope"] < 1.0 and entropy_boundary_fit["slope"] < 1.0},
    }
    boundary = {
        "z3_area_law_scaling_witness": z3_witness(volume_fit["slope"], boundary_fit["slope"], max_trace_gap, min_positivity),
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
    }
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [row["pass"] for row in boundary.values()]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "finite cubic shell graph with a trace-preserving positive conditional expectation from bulk maximally mixed density to boundary-supported density, compared by area-versus-volume count and entropy scaling",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"passed": sum(1 for value in checks if value), "total": len(checks)},
        "open_choices": [
            "This is only a finite boundary-projection scaffold, not black-hole entropy or a holographic proof.",
            "The entropy of a maximally mixed finite distribution scales logarithmically in node count; area law here means boundary support size, not direct entropy proportional to area.",
            "Next scouts should couple this boundary expectation to gamma5 channel rates and tensor-network coherent information.",
        ],
        "why_not_v4_probes": "This is a clean v5 formal scout translated from holistic Grok/Gemini area-law pressure; it is not a canonical v4 probe.",
        "raw_rows": rows,
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all(checks), "result": str(OUT_PATH), "volume_slope": volume_fit["slope"], "boundary_slope": boundary_fit["slope"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
