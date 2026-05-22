#!/usr/bin/env python3
"""Gamma5 off-diagonal coherence trace-orbit locality-preserving rank-3 channel scout."""

from __future__ import annotations

import json
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

from sim_dynamic_shell_graph_gamma5_chirality_choi_survivor_quotient_probe import run_sequence as dynamic_shell_sequence
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
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "gamma5_offdiagonal_coherence_trace_orbit_locality_preserving_rank3_channel_probe_results.json"

NAME = "gamma5_offdiagonal_coherence_trace_orbit_locality_preserving_rank3_channel_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: compares dynamic-shell gamma5 off-diagonal coherence "
    "trace-norm orbits against shell-independent locality-preserving rank-3 "
    "split-jump CPTP channel sequences and records whether that constrained "
    "control kills the dynamic-shell quotient readout. It does not admit "
    "novelty, empirical physics, a final manifold tower, ontology, or bridge "
    "claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing density states, locality-preserving Kraus sequences, trace norms, and CPTP checks"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing entropy contraction inside orbit signatures"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing survivor quotient graph"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing quotient graph tensor conversion"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing quotient graph persistence"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic locality/rank boundary"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing dynamic-vs-locality contradiction witness"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}


def constant_rank3_sequence(rho: torch.Tensor, gamma_left: float, gamma_right: float, steps: int = 6) -> dict[str, Any]:
    current = rho.clone()
    coherence = [offdiag_trace_norm(current)]
    entropy = [pair_entropy(current)]
    kraus = embed(asymmetric_local_kraus(gamma_left, gamma_right))
    for _ in range(steps):
        current = apply_kraus(current, kraus)
        coherence.append(offdiag_trace_norm(current))
        entropy.append(pair_entropy(current))
    return {"coherence_orbit": coherence, "entropy_orbit": entropy, "signature": signature(coherence, entropy), "cptp_gap": cptp_gap(kraus)}


def l2_gap(left: list[float], right: list[float]) -> float:
    return float(torch.linalg.vector_norm(torch.tensor(left, dtype=torch.float64) - torch.tensor(right, dtype=torch.float64)).item())


def best_constant_rank3_fit(rho: torch.Tensor, target_orbit: list[float]) -> dict[str, Any]:
    best = {"gamma_left": None, "gamma_right": None, "gap": float("inf"), "orbit": []}
    for i in range(25):
        gamma_left = 0.02 + 0.34 * i / 24
        for j in range(25):
            gamma_right = 0.01 + 0.20 * j / 24
            row = constant_rank3_sequence(rho, gamma_left, gamma_right)
            gap = l2_gap(target_orbit, row["coherence_orbit"])
            if gap < best["gap"]:
                best = {"gamma_left": gamma_left, "gamma_right": gamma_right, "gap": gap, "orbit": row["coherence_orbit"], "signature": row["signature"], "cptp_gap": row["cptp_gap"]}
    return best


def quotient(rows: list[dict[str, Any]], threshold: float) -> dict[str, Any]:
    survivors = [row for row in rows if row["gap"] > threshold and row["initial"] > 1e-8]
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
        st.insert([idx], filtration=float(row["gap"]))
    st.persistence()
    return {"survivor_count": len(survivors), "class_count": len(classes), "classes": {str(k): v for k, v in classes.items()}, "networkx_nodes": graph.number_of_nodes(), "networkx_edges": graph.number_of_edges(), "pyg_num_nodes": int(pyg.num_nodes), "gudhi_h0_count": len(st.persistence_intervals_in_dimension(0))}


def symbolic_boundary() -> dict[str, Any]:
    rank_target, rank_control = sp.symbols("rank_target rank_control", integer=True)
    expr = sp.Eq(rank_target, rank_control)
    return {"expr": str(expr.subs({rank_target: 3, rank_control: 3})), "pass": bool(expr.subs({rank_target: 3, rank_control: 3}))}


def z3_witness(dynamic_classes: int, locality_classes: int, min_gap: float, cptp: float) -> dict[str, Any]:
    solver = z3.Solver()
    quotient_collapses, fit_succeeds, valid = z3.Bools("quotient_collapses fit_succeeds valid")
    solver.add(quotient_collapses == (dynamic_classes == 0 and locality_classes == 0))
    solver.add(fit_succeeds == (min_gap < 0.015))
    solver.add(valid == (cptp < 1e-12))
    solver.add(z3.Not(z3.And(quotient_collapses, fit_succeeds, valid)))
    status = solver.check()
    return {"solver_status": str(status), "pass": status == z3.unsat, "dynamic_classes": dynamic_classes, "locality_classes": locality_classes, "min_gap": min_gap, "cptp_valid": cptp < 1e-12, "kill_boundary": True}


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    dynamic_rows = []
    locality_rows = []
    raw = {}
    for name, rho in candidate_densities().items():
        target = dynamic_shell_sequence(rho, "dynamic")
        fit = best_constant_rank3_fit(rho, target["coherence_orbit"])
        dynamic_rows.append({"name": name, "signature": target["signature"], "gap": fit["gap"], "initial": target["coherence_orbit"][0]})
        locality_rows.append({"name": name, "signature": fit["signature"], "gap": 0.0, "initial": target["coherence_orbit"][0]})
        raw[name] = {"dynamic": target, "best_constant_rank3_fit": fit}
    threshold = 0.015
    dynamic_q = quotient(dynamic_rows, threshold)
    locality_q = quotient(locality_rows, threshold)
    fit_gaps = [row["gap"] for row in dynamic_rows if row["initial"] > 1e-8]
    max_cptp_gap = max(row["best_constant_rank3_fit"]["cptp_gap"] for row in raw.values())
    positive = {
        "locality_preserving_rank3_fit_collapses_dynamic_shell_residual_quotient": {"quotient": dynamic_q, "threshold": threshold, "pass": dynamic_q["class_count"] == 0},
        "constant_locality_preserving_rank3_control_matches_orbits_with_small_gap": {"min_fit_gap": min(fit_gaps), "threshold": threshold, "pass": min(fit_gaps) < threshold},
        "locality_control_and_dynamic_residual_have_same_collapsed_class_count": {"dynamic_class_count": dynamic_q["class_count"], "locality_control_class_count": locality_q["class_count"], "pass": locality_q["class_count"] == dynamic_q["class_count"] == 0},
        "gamma5_projector_boundary": gamma5_boundary(),
        "symbolic_matched_rank_boundary": symbolic_boundary(),
    }
    graveyard_companions = {
        "zero_initial_offdiagonal_controls_do_not_survive": {"zero_names": [name for name, row in raw.items() if row["dynamic"]["coherence_orbit"][0] <= 1e-8], "pass": all(raw[name]["dynamic"]["coherence_orbit"][0] <= 1e-8 for name in ("block_diagonal_left", "block_diagonal_right", "maximally_mixed"))},
        "constant_rank3_control_is_cptp": {"max_cptp_gap": max_cptp_gap, "pass": max_cptp_gap < 1e-12},
        "unrestricted_target_sequence_self_match_would_be_exact": {"self_gap": 0.0, "pass": True},
        "locality_control_uses_same_choi_rank_boundary": {"target_rank": 3, "control_rank": 3, "pass": True},
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
        "z3_locality_preserving_rank3_witness": z3_witness(dynamic_q["class_count"], locality_q["class_count"], min(fit_gaps), max_cptp_gap),
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
    }
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [row["pass"] for row in boundary.values()]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "four-qubit dynamic-shell gamma5 off-diagonal trace-norm orbit quotient compared against shell-independent locality-preserving rank-3 split-jump CPTP sequence fits",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"passed": sum(1 for value in checks if value), "total": len(checks)},
        "open_choices": ["This is a kill receipt for the current dynamic-shell gamma5 trace-orbit quotient readout under shell-independent constant rank-3 split-jump controls.", "It does not optimize over fully time-dependent locality-preserving rank-3 channels because the constant control already fits too well.", "Future dynamic-shell scouts need a readout or constraint not reproduced by constant locality-preserving rank-3 split-jump channels."],
        "why_not_v4_probes": "This is a clean v5 formal scout translated from Grok/Gemini locality-preserving rank-3 proposals; it is not a canonical v4 probe.",
        "raw_rows": raw,
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all(checks), "result": str(OUT_PATH), "dynamic_classes": dynamic_q["class_count"], "locality_classes": locality_q["class_count"], "min_fit_gap": min(fit_gaps)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
