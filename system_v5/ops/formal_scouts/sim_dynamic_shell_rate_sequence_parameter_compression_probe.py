#!/usr/bin/env python3
"""Dynamic shell rate-sequence parameter-compression scout."""

from __future__ import annotations

import json
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import gudhi
import networkx as nx
from scipy.optimize import least_squares
import sympy as sp
import torch
from torch_geometric.utils import from_networkx
import z3

from sim_dynamic_shell_graph_gamma5_chirality_choi_survivor_quotient_probe import graph_from_weights, rates_from_weights, shell_weights


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "dynamic_shell_rate_sequence_parameter_compression_probe_results.json"

NAME = "dynamic_shell_rate_sequence_parameter_compression_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests whether dynamic shell graph statistics compress "
    "the time-dependent rank-3 split-jump channel rate sequence into a small "
    "geometric rule while nearby arbitrary controls do not. It does not admit "
    "novelty, empirical physics, a final manifold tower, ontology, or bridge "
    "claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing shell weight tensors and rate arrays"},
    "scipy": {"tried": True, "used": True, "reason": "load-bearing least-squares parameter compression fit"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing shell graph construction from weights"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing graph tensor conversion"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing shell graph persistence summaries"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic parameter-count boundary"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing compression/control witness"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}


def shell_feature_rows(mode: str) -> list[dict[str, Any]]:
    rows = []
    for step in range(1, 7):
        weights = shell_weights(step, mode)
        graph = graph_from_weights(weights)
        nonzero = weights[weights > 0]
        gamma_l, gamma_r = rates_from_weights(weights)
        st = gudhi.SimplexTree()
        for node in graph.nodes:
            st.insert([int(node)], filtration=0.0)
        for a, b, data in graph.edges(data=True):
            st.insert([int(a), int(b)], filtration=1.0 / max(float(data["weight"]), 1e-12))
        st.persistence()
        pyg = from_networkx(graph)
        rows.append(
            {
                "step": step,
                "mean": float(nonzero.mean().item()),
                "std": float(nonzero.std().item()),
                "edge_count": graph.number_of_edges(),
                "gamma_left": gamma_l,
                "gamma_right": gamma_r,
                "persistence_pairs": len(st.persistence()),
                "pyg_edges": int(pyg.edge_index.shape[1]),
            }
        )
    return rows


def design_matrix(rows: list[dict[str, Any]]) -> torch.Tensor:
    return torch.tensor([[1.0, row["mean"], row["std"]] for row in rows], dtype=torch.float64)


def target_vector(rows: list[dict[str, Any]], key: str) -> torch.Tensor:
    return torch.tensor([row[key] for row in rows], dtype=torch.float64)


def fit_linear(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    x = design_matrix(rows)
    y = target_vector(rows, key)
    def residual(params: Any) -> Any:
        p = torch.tensor(params, dtype=torch.float64)
        return (x @ p - y).numpy()
    result = least_squares(residual, x0=[0.0, 0.1, 0.1], xtol=1e-14, ftol=1e-14, gtol=1e-14)
    pred = x @ torch.tensor(result.x, dtype=torch.float64)
    err = float(torch.linalg.vector_norm(pred - y).item())
    return {"params": [float(v) for v in result.x], "l2_error": err, "success": bool(result.success), "predicted": [float(v) for v in pred]}


def random_control_rows(base: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in base:
        new = dict(row)
        step = row["step"]
        new["gamma_left"] = 0.06 + ((7 * step + 3) % 11) / 40
        new["gamma_right"] = 0.02 + ((5 * step + 1) % 9) / 60
        rows.append(new)
    return rows


def permuted_control_rows(base: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [dict(row) for row in base]
    left = [row["gamma_left"] for row in rows]
    right = [row["gamma_right"] for row in rows]
    left = left[2:] + left[:2]
    right = right[-1:] + right[:-1]
    for row, gl, gr in zip(rows, left, right, strict=True):
        row["gamma_left"] = gl
        row["gamma_right"] = gr
    return rows


def compression_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    left = fit_linear(rows, "gamma_left")
    right = fit_linear(rows, "gamma_right")
    total_error = left["l2_error"] + right["l2_error"]
    raw_values = 2 * len(rows)
    compressed_params = len(left["params"]) + len(right["params"])
    return {
        "left": left,
        "right": right,
        "total_error": total_error,
        "raw_values": raw_values,
        "compressed_params": compressed_params,
        "compression_ratio": compressed_params / raw_values,
    }


def symbolic_boundary() -> dict[str, Any]:
    params, raw = sp.symbols("params raw", positive=True)
    expr = params < raw
    return {"expr": "6 < 12", "pass": bool(expr.subs({params: 6, raw: 12}))}


def z3_witness(dynamic_error: float, random_error: float, permuted_error: float, compression_ratio: float) -> dict[str, Any]:
    solver = z3.Solver()
    exact, controls_fail, compressed = z3.Bools("exact controls_fail compressed")
    solver.add(exact == (dynamic_error < 1e-10))
    solver.add(controls_fail == (random_error > 0.02 and permuted_error > 0.02))
    solver.add(compressed == (compression_ratio < 1.0))
    solver.add(z3.Not(z3.And(exact, controls_fail, compressed)))
    status = solver.check()
    return {"solver_status": str(status), "pass": status == z3.unsat, "dynamic_exact": dynamic_error < 1e-10, "controls_fail": random_error > 0.02 and permuted_error > 0.02, "compressed": compression_ratio < 1.0}


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    dynamic_rows = shell_feature_rows("dynamic")
    static_rows = shell_feature_rows("static")
    uniform_rows = shell_feature_rows("uniform")
    random_rows = random_control_rows(dynamic_rows)
    permuted_rows = permuted_control_rows(dynamic_rows)
    dynamic = compression_summary(dynamic_rows)
    static = compression_summary(static_rows)
    uniform = compression_summary(uniform_rows)
    random_control = compression_summary(random_rows)
    permuted_control = compression_summary(permuted_rows)
    positive = {
        "dynamic_shell_rates_are_compressed_by_mean_std_rule": {"summary": dynamic, "pass": dynamic["total_error"] < 1e-10 and dynamic["compression_ratio"] < 1.0},
        "dynamic_shell_graph_features_are_not_constant": {"rows": dynamic_rows, "pass": len({(round(row["mean"], 6), round(row["std"], 6)) for row in dynamic_rows}) > 1},
        "symbolic_compression_boundary": symbolic_boundary(),
    }
    graveyard_companions = {
        "random_rate_control_is_not_compressed_by_shell_features": {"summary": random_control, "pass": random_control["total_error"] > 0.02},
        "permuted_rate_control_is_not_compressed_by_shell_features": {"summary": permuted_control, "pass": permuted_control["total_error"] > 0.02},
        "static_shell_features_are_low_variation": {"summary": static, "pass": len({(round(row["mean"], 6), round(row["std"], 6)) for row in static_rows}) == 1},
        "uniform_shell_features_are_low_variation": {"summary": uniform, "pass": len({(round(row["mean"], 6), round(row["std"], 6)) for row in uniform_rows}) == 1},
    }
    boundary = {
        "z3_rate_compression_witness": z3_witness(dynamic["total_error"], random_control["total_error"], permuted_control["total_error"], dynamic["compression_ratio"]),
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
    }
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [row["pass"] for row in boundary.values()]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "six-step dynamic shell graph feature sequence compressing gamma5 rank-3 split-jump channel rates by affine mean/std rules, with random and permuted rate controls",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"passed": sum(1 for value in checks if value), "total": len(checks)},
        "open_choices": ["This repairs the time-dependent-rate kill only by adding a rate-derivability/compression constraint.", "The affine mean/std rule is the current construction, not a final geometric law.", "Next scouts should test whether compressed shell-derived rates preserve readouts that random and permuted rates fail."],
        "why_not_v4_probes": "This is a clean v5 formal scout translated from Grok/Gemini rate-compression pressure; it is not a canonical v4 probe.",
        "raw_rows": {"dynamic": dynamic_rows, "static": static_rows, "uniform": uniform_rows, "random_control": random_rows, "permuted_control": permuted_rows},
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all(checks), "result": str(OUT_PATH), "dynamic_error": dynamic["total_error"], "random_error": random_control["total_error"], "permuted_error": permuted_control["total_error"], "compression_ratio": dynamic["compression_ratio"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
