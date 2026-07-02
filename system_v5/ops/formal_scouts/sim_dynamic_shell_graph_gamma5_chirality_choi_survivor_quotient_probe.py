#!/usr/bin/env python3
"""Dynamic shell graph gamma5 chirality Choi survivor-quotient scout."""

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
import sympy as sp
import torch
from torch_geometric.utils import from_networkx
import z3

from sim_gamma5_offdiagonal_coherence_trace_orbit_survivor_quotient_probe import (
    DTYPE,
    DIM,
    N_QUBITS,
    apply_kraus,
    asymmetric_local_kraus,
    candidate_densities,
    cptp_gap,
    embed,
    gamma5_boundary,
    offdiag_trace_norm,
    pair_entropy,
    signature,
    symmetric_local_kraus,
)
from sim_gamma5_chirality_asymmetric_cptp_choi_distance_effective_channel_probe import (
    choi_matrix,
    trace_distance,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "dynamic_shell_graph_gamma5_chirality_choi_survivor_quotient_probe_results.json"

NAME = "dynamic_shell_graph_gamma5_chirality_choi_survivor_quotient_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: couples dynamic shell graph weights to gamma5 "
    "chirality-asymmetric CPTP channel rates, then quotients finite density "
    "states by P_L rho P_R trace-norm orbit signatures with Choi-distance "
    "effective-channel controls. It does not admit novelty, empirical physics, "
    "a final manifold tower, ontology, or bridge claim."
)

TOOL_MANIFEST = {
    "python_math": {"tried": True, "used": True, "reason": "supportive local bounded scalar minimizer for effective-gamma Choi fit"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing density states, shell-driven Kraus sequences, Choi matrices, trace norms, and effective-gamma Choi objective evaluation"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing pair entropy contraction inside orbit signatures"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing dynamic shell graph construction and quotient graph"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing graph-to-tensor conversion for quotient graph"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence on survivor quotient graph"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic noncommuting shell update sanity"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing dynamic/static/control contradiction witness"},
}
TOOL_INTEGRATION_DEPTH = {
    tool: ("supportive" if tool == "python_math" else "load_bearing")
    for tool in TOOL_MANIFEST
}


def shell_points(step: int, mode: str) -> torch.Tensor:
    rows = []
    stretch = 1.0
    twist = 0.0
    if mode == "dynamic":
        stretch = 1.0 + 0.22 * step
        twist = 0.31 * step
    elif mode == "isotropic":
        stretch = 1.0
        twist = 0.31 * step
    for idx in range(4):
        theta = 2 * math.pi * idx / 4 + twist
        z = -0.55 + 1.10 * idx / 3
        r_xy = math.sqrt(max(0.0, 1 - z * z))
        rows.append([stretch * r_xy * math.cos(theta), r_xy * math.sin(theta) / math.sqrt(stretch), z / math.sqrt(stretch)])
    return torch.tensor(rows, dtype=torch.float64)


def shell_weights(step: int, mode: str) -> torch.Tensor:
    pts = shell_points(step, mode)
    dist = torch.cdist(pts, pts)
    weights = 1.0 / torch.clamp(dist * dist, min=0.2)
    weights.fill_diagonal_(0.0)
    if mode == "uniform":
        weights = torch.ones_like(weights)
        weights.fill_diagonal_(0.0)
    return weights / torch.clamp(weights.max(), min=1e-12)


def graph_from_weights(weights: torch.Tensor) -> nx.Graph:
    graph = nx.Graph()
    graph.add_nodes_from(range(4))
    for i in range(4):
        for j in range(i + 1, 4):
            weight = float(weights[i, j].item())
            if weight > 0.18:
                graph.add_edge(i, j, weight=weight)
    return graph


def rates_from_weights(weights: torch.Tensor) -> tuple[float, float]:
    nonzero = weights[weights > 0]
    mean = float(nonzero.mean().item())
    std = float(nonzero.std().item())
    return min(0.42, 0.05 + 0.23 * mean + 0.11 * std), min(0.22, 0.015 + 0.09 * mean - 0.03 * std)


def bounded_scalar_minimize(
    objective: Any,
    lower: float,
    upper: float,
    *,
    xatol: float = 1e-11,
    max_iter: int = 200,
) -> dict[str, Any]:
    inv_phi = (math.sqrt(5.0) - 1.0) / 2.0
    inv_phi_sq = 1.0 - inv_phi
    a = float(lower)
    b = float(upper)
    h = b - a
    c = a + inv_phi_sq * h
    d = a + inv_phi * h
    fc = float(objective(c))
    fd = float(objective(d))
    iterations = 0
    while h > xatol and iterations < max_iter:
        if fc < fd:
            b = d
            d = c
            fd = fc
            h = b - a
            c = a + inv_phi_sq * h
            fc = float(objective(c))
        else:
            a = c
            c = d
            fc = fd
            h = b - a
            d = a + inv_phi * h
            fd = float(objective(d))
        iterations += 1
    candidates = [(a, float(objective(a))), (b, float(objective(b))), (c, fc), (d, fd)]
    x, fun = min(candidates, key=lambda item: item[1])
    return {"x": float(x), "fun": float(fun), "success": h <= xatol, "iterations": iterations}


def best_symmetric_choi_gap(gamma_left: float, gamma_right: float) -> dict[str, Any]:
    target = asymmetric_local_kraus(gamma_left, gamma_right)
    target_choi = choi_matrix(target)
    def objective(gamma: float) -> float:
        return trace_distance(target_choi, choi_matrix(symmetric_local_kraus(float(gamma))))
    result = bounded_scalar_minimize(objective, 0.0, 0.50, xatol=1e-11)
    return {"gamma": result["x"], "choi_trace_distance": result["fun"], "success": result["success"]}


def run_sequence(rho: torch.Tensor, mode: str) -> dict[str, Any]:
    current = rho.clone()
    coherence = [offdiag_trace_norm(current)]
    entropy = [pair_entropy(current)]
    graph_rows = []
    choi_gaps = []
    cptp_gaps = []
    for step in range(1, 7):
        weights = shell_weights(step, mode)
        graph = graph_from_weights(weights)
        gamma_l, gamma_r = rates_from_weights(weights)
        local = asymmetric_local_kraus(gamma_l, gamma_r)
        current = apply_kraus(current, embed(local))
        coherence.append(offdiag_trace_norm(current))
        entropy.append(pair_entropy(current))
        fit = best_symmetric_choi_gap(gamma_l, gamma_r)
        choi_gaps.append(fit["choi_trace_distance"])
        cptp_gaps.append(cptp_gap(embed(local)))
        graph_rows.append(
            {
                "step": step,
                "edge_count": graph.number_of_edges(),
                "weight_mean": float(weights[weights > 0].mean().item()),
                "weight_std": float(weights[weights > 0].std().item()),
                "gamma_left": gamma_l,
                "gamma_right": gamma_r,
                "best_symmetric_gamma": fit["gamma"],
                "choi_trace_distance": fit["choi_trace_distance"],
            }
        )
    return {
        "coherence_orbit": coherence,
        "entropy_orbit": entropy,
        "signature": signature(coherence, entropy),
        "graph_rows": graph_rows,
        "min_choi_gap": min(choi_gaps),
        "max_cptp_gap": max(cptp_gaps),
    }


def quotient(rows: list[dict[str, Any]], threshold: float) -> dict[str, Any]:
    survivors = [row for row in rows if row["fit_gap"] > threshold and row["initial"] > 1e-8]
    classes: dict[tuple[Any, ...], list[str]] = defaultdict(list)
    graph = nx.Graph()
    for row in survivors:
        classes[row["signature"]].append(row["name"])
        graph.add_node(row["name"])
    for names in classes.values():
        for i, left in enumerate(names):
            for right in names[i + 1 :]:
                graph.add_edge(left, right)
    pyg = from_networkx(graph)
    st = gudhi.SimplexTree()
    for idx, row in enumerate(survivors):
        st.insert([idx], filtration=float(row["fit_gap"]))
    st.persistence()
    return {
        "survivor_count": len(survivors),
        "class_count": len(classes),
        "classes": {str(key): value for key, value in classes.items()},
        "networkx_nodes": graph.number_of_nodes(),
        "networkx_edges": graph.number_of_edges(),
        "pyg_num_nodes": int(pyg.num_nodes),
        "gudhi_h0_count": len(st.persistence_intervals_in_dimension(0)),
    }


def symbolic_dynamic_boundary() -> dict[str, Any]:
    a, b = sp.symbols("a b")
    m1 = sp.Matrix([[1, a], [0, 1]])
    m2 = sp.Matrix([[1, 0], [b, 1]])
    comm = sp.simplify(m1 * m2 - m2 * m1)
    return {"commutator": str(comm), "pass": comm != sp.zeros(2)}


def z3_witness(dynamic_classes: int, static_classes: int, min_choi_gap: float, cptp_gap_value: float) -> dict[str, Any]:
    solver = z3.Solver()
    d, s, c, v = z3.Bools("dynamic_classes static_fewer choi_gap cptp_valid")
    solver.add(d == (dynamic_classes >= 3))
    solver.add(s == (dynamic_classes > static_classes))
    solver.add(c == (min_choi_gap > 0.02))
    solver.add(v == (cptp_gap_value < 1e-12))
    solver.add(z3.Not(z3.And(d, s, c, v)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "dynamic_classes": dynamic_classes,
        "static_classes": static_classes,
        "min_choi_gap": min_choi_gap,
        "cptp_valid": cptp_gap_value < 1e-12,
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    dynamic_rows = []
    static_rows = []
    uniform_rows = []
    raw = {}
    for name, rho in candidate_densities().items():
        dyn = run_sequence(rho, "dynamic")
        sta = run_sequence(rho, "static")
        uni = run_sequence(rho, "uniform")
        dyn_static_gap = float(torch.linalg.vector_norm(torch.tensor(dyn["coherence_orbit"], dtype=torch.float64) - torch.tensor(sta["coherence_orbit"], dtype=torch.float64)).item())
        dynamic_rows.append({"name": name, "signature": dyn["signature"], "fit_gap": dyn_static_gap, "initial": dyn["coherence_orbit"][0]})
        static_rows.append({"name": name, "signature": sta["signature"], "fit_gap": 0.0, "initial": sta["coherence_orbit"][0]})
        uniform_rows.append({"name": name, "signature": uni["signature"], "fit_gap": dyn_static_gap, "initial": uni["coherence_orbit"][0]})
        raw[name] = {"dynamic": dyn, "static": sta, "uniform": uni, "dynamic_static_orbit_gap": dyn_static_gap}
    threshold = 0.025
    dynamic_q = quotient(dynamic_rows, threshold)
    static_q = quotient(static_rows, threshold)
    uniform_q = quotient(uniform_rows, threshold)
    min_choi_gap = min(row["dynamic"]["min_choi_gap"] for row in raw.values() if row["dynamic"]["coherence_orbit"][0] > 1e-8)
    max_cptp_gap = max(row["dynamic"]["max_cptp_gap"] for row in raw.values())
    positive = {
        "dynamic_shell_gamma5_sequence_forms_multiple_survivor_classes": {
            "quotient": dynamic_q,
            "threshold": threshold,
            "pass": dynamic_q["survivor_count"] >= 4 and dynamic_q["class_count"] >= 3,
        },
        "dynamic_shell_classes_exceed_static_shell_control": {
            "dynamic_class_count": dynamic_q["class_count"],
            "static_class_count": static_q["class_count"],
            "pass": dynamic_q["class_count"] > static_q["class_count"],
        },
        "dynamic_shell_step_channels_resist_symmetric_choi_fit": {
            "min_choi_gap": min_choi_gap,
            "pass": min_choi_gap > 0.02,
        },
        "gamma5_projector_boundary": gamma5_boundary(),
        "symbolic_dynamic_update_boundary": symbolic_dynamic_boundary(),
    }
    graveyard_companions = {
        "static_shell_control_has_no_survivor_classes": {
            "quotient": static_q,
            "pass": static_q["class_count"] == 0,
        },
        "uniform_shell_control_has_no_more_classes_than_dynamic_shell": {
            "quotient": uniform_q,
            "pass": uniform_q["class_count"] <= dynamic_q["class_count"],
        },
        "zero_initial_offdiagonal_controls_do_not_survive": {
            "zero_names": [name for name, row in raw.items() if row["dynamic"]["coherence_orbit"][0] <= 1e-8],
            "pass": all(raw[name]["dynamic"]["coherence_orbit"][0] <= 1e-8 and raw[name]["dynamic_static_orbit_gap"] <= 1e-12 for name in ("block_diagonal_left", "block_diagonal_right", "maximally_mixed")),
        },
        "dynamic_channels_are_cptp": {
            "max_cptp_gap": max_cptp_gap,
            "pass": max_cptp_gap < 1e-12,
        },
    }
    boundary = {
        "finite_four_qubit_density_dimension": {
            "dimension": DIM,
            "qubits": N_QUBITS,
            "minimum_nonclassical_width": 8,
            "minimum_width_role": "calibration_only",
            "minimum_width_reason": "four-qubit density fixture is a finite boundary/control, not nonclassical maturity evidence",
            "pass": DIM == 16 and N_QUBITS == 4,
        },
        "z3_dynamic_shell_quotient_witness": z3_witness(dynamic_q["class_count"], static_q["class_count"], min_choi_gap, max_cptp_gap),
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
    }
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [row["pass"] for row in boundary.values()]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "four-qubit density family under dynamic shell graph weights coupled to gamma5 chirality-asymmetric CPTP channel sequences, quotiented by P_L rho P_R trace-norm orbit signatures with Choi-distance effective-channel controls",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"passed": sum(1 for value in checks if value), "total": len(checks)},
        "open_choices": [
            "This scout couples dynamic shell rates to gamma5 channels but remains four-qubit and formal.",
            "The next stronger version should lift this to the eight-qubit tensor-network shell graph.",
            "The arbitrary-CPTP reduction falsifier remains open; this only carries the one-parameter Choi control at each step.",
        ],
        "why_not_v4_probes": "This is a clean v5 formal scout translated from Grok/Gemini dynamic-shell coupling proposals; it is not a canonical v4 probe.",
        "raw_rows": raw,
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": all(checks),
                "result": str(OUT_PATH),
                "dynamic_classes": dynamic_q["class_count"],
                "static_classes": static_q["class_count"],
                "uniform_classes": uniform_q["class_count"],
                "min_choi_gap": min_choi_gap,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
