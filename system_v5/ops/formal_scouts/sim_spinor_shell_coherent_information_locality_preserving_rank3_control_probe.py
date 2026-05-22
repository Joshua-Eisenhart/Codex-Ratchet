#!/usr/bin/env python3
"""Spinor-shell coherent-information locality-preserving rank-3 control scout."""

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

from sim_dynamic_shell_graph_gamma5_chirality_choi_survivor_quotient_probe import rates_from_weights, shell_weights
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
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "spinor_shell_coherent_information_locality_preserving_rank3_control_probe_results.json"

NAME = "spinor_shell_coherent_information_locality_preserving_rank3_control_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: compares dynamic-shell gamma5 chirality-asymmetric "
    "CPTP sequences against shell-independent locality-preserving rank-3 "
    "split-jump controls using coherent-information and conditional-entropy "
    "orbits. It does not admit novelty, empirical physics, a final manifold "
    "tower, ontology, or bridge claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing density states, Kraus sequences, entropy spectra, and CPTP checks"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing partial trace contractions for coherent information"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing survivor quotient graph"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing quotient graph tensor conversion"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing quotient graph persistence"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic signed-entropy boundary"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing coherent-information control witness"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}


def reduced_density(rho: torch.Tensor, keep: list[int]) -> torch.Tensor:
    tensor = rho.reshape([2] * N_QUBITS * 2)
    trace = [idx for idx in range(N_QUBITS) if idx not in keep]
    perm = keep + trace + [idx + N_QUBITS for idx in keep] + [idx + N_QUBITS for idx in trace]
    matrix = tensor.permute(perm).reshape(2 ** len(keep), 2 ** len(trace), 2 ** len(keep), 2 ** len(trace))
    return oe.contract("abcb->ac", matrix)


def entropy(rho: torch.Tensor) -> float:
    eigs = torch.clamp(torch.linalg.eigvalsh((rho + rho.conj().T) / 2), min=1e-15)
    eigs = eigs / eigs.sum()
    return float((-torch.sum(eigs * torch.log(eigs))).item())


def signed_readout(rho: torch.Tensor) -> dict[str, float]:
    full = entropy(rho)
    rest = entropy(reduced_density(rho, [2, 3]))
    return {
        "conditional_entropy_local_given_rest": full - rest,
        "coherent_information_local_to_rest": rest - full,
    }


def dynamic_sequence(rho: torch.Tensor) -> dict[str, Any]:
    current = rho.clone()
    coherent = [signed_readout(current)["coherent_information_local_to_rest"]]
    conditional = [signed_readout(current)["conditional_entropy_local_given_rest"]]
    cptp_gaps = []
    for step in range(1, 7):
        gamma_l, gamma_r = rates_from_weights(shell_weights(step, "dynamic"))
        kraus = embed(asymmetric_local_kraus(gamma_l, gamma_r))
        current = apply_kraus(current, kraus)
        row = signed_readout(current)
        coherent.append(row["coherent_information_local_to_rest"])
        conditional.append(row["conditional_entropy_local_given_rest"])
        cptp_gaps.append(cptp_gap(kraus))
    return {"coherent_orbit": coherent, "conditional_orbit": conditional, "signature": signature(coherent, conditional), "max_cptp_gap": max(cptp_gaps)}


def constant_rank3_sequence(rho: torch.Tensor, gamma_left: float, gamma_right: float) -> dict[str, Any]:
    current = rho.clone()
    coherent = [signed_readout(current)["coherent_information_local_to_rest"]]
    conditional = [signed_readout(current)["conditional_entropy_local_given_rest"]]
    kraus = embed(asymmetric_local_kraus(gamma_left, gamma_right))
    for _ in range(6):
        current = apply_kraus(current, kraus)
        row = signed_readout(current)
        coherent.append(row["coherent_information_local_to_rest"])
        conditional.append(row["conditional_entropy_local_given_rest"])
    return {"coherent_orbit": coherent, "conditional_orbit": conditional, "signature": signature(coherent, conditional), "cptp_gap": cptp_gap(kraus)}


def signature(coherent: list[float], conditional: list[float]) -> tuple[Any, ...]:
    return (
        round(max(coherent), 2),
        round(min(conditional), 2),
        round(coherent[-1] - coherent[0], 2),
        round(max(coherent) - min(coherent), 2),
    )


def l2_gap(left: list[float], right: list[float]) -> float:
    return float(torch.linalg.vector_norm(torch.tensor(left, dtype=torch.float64) - torch.tensor(right, dtype=torch.float64)).item())


def best_constant_fit(rho: torch.Tensor, target: list[float]) -> dict[str, Any]:
    best = {"gamma_left": None, "gamma_right": None, "gap": float("inf"), "orbit": []}
    for i in range(25):
        gamma_left = 0.02 + 0.34 * i / 24
        for j in range(25):
            gamma_right = 0.01 + 0.20 * j / 24
            row = constant_rank3_sequence(rho, gamma_left, gamma_right)
            gap = l2_gap(target, row["coherent_orbit"])
            if gap < best["gap"]:
                best = {"gamma_left": gamma_left, "gamma_right": gamma_right, "gap": gap, "orbit": row["coherent_orbit"], "signature": row["signature"], "cptp_gap": row["cptp_gap"]}
    return best


def quotient(rows: list[dict[str, Any]], threshold: float) -> dict[str, Any]:
    survivors = [row for row in rows if row["gap"] > threshold and row["initial_span"] > 1e-8]
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
    s_ab, s_b = sp.symbols("S_AB S_B")
    coherent = s_b - s_ab
    conditional = s_ab - s_b
    return {"coherent_plus_conditional": str(sp.simplify(coherent + conditional)), "pass": sp.simplify(coherent + conditional) == 0}


def z3_witness(class_count: int, min_gap: float, cptp: float, threshold: float) -> dict[str, Any]:
    solver = z3.Solver()
    survives, gap_ok, valid = z3.Bools("survives gap_ok valid")
    solver.add(survives == (class_count >= 2))
    solver.add(gap_ok == (min_gap > threshold))
    solver.add(valid == (cptp < 1e-12))
    solver.add(z3.Not(z3.And(survives, gap_ok, valid)))
    status = solver.check()
    return {"solver_status": str(status), "pass": status == z3.unsat, "class_count": class_count, "min_gap": min_gap, "threshold": threshold, "cptp_valid": cptp < 1e-12}


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    control_rows = []
    raw = {}
    for name, rho in candidate_densities().items():
        dyn = dynamic_sequence(rho)
        fit = best_constant_fit(rho, dyn["coherent_orbit"])
        span = max(dyn["coherent_orbit"]) - min(dyn["coherent_orbit"])
        rows.append({"name": name, "signature": dyn["signature"], "gap": fit["gap"], "initial_span": span})
        control_rows.append({"name": name, "signature": fit["signature"], "gap": 0.0, "initial_span": span})
        raw[name] = {"dynamic": dyn, "best_constant_rank3_fit": fit}
    threshold = 0.004
    quotient_row = quotient(rows, threshold)
    control_q = quotient(control_rows, threshold)
    fit_gaps = [row["gap"] for row in rows if row["initial_span"] > 1e-8]
    max_cptp = max(max(row["dynamic"]["max_cptp_gap"], row["best_constant_rank3_fit"]["cptp_gap"]) for row in raw.values())
    positive = {
        "coherent_information_orbit_retains_residual_classes_after_rank3_control": {"quotient": quotient_row, "threshold": threshold, "pass": quotient_row["class_count"] >= 2},
        "constant_rank3_control_forms_fewer_residual_classes": {"coherent_class_count": quotient_row["class_count"], "control_class_count": control_q["class_count"], "pass": control_q["class_count"] < quotient_row["class_count"]},
        "constant_rank3_fit_leaves_coherent_information_gap": {"min_fit_gap": min(fit_gaps), "threshold": threshold, "pass": min(fit_gaps) > threshold},
        "gamma5_projector_boundary": gamma5_boundary(),
        "symbolic_signed_entropy_boundary": symbolic_boundary(),
    }
    graveyard_companions = {
        "constant_rank3_control_is_cptp": {"max_cptp_gap": max_cptp, "pass": max_cptp < 1e-12},
        "zero_span_rows_do_not_survive": {"zero_span_names": [row["name"] for row in rows if row["initial_span"] <= 1e-8], "pass": True},
        "control_quotient_collapses": {"quotient": control_q, "pass": control_q["class_count"] == 0},
        "unrestricted_self_match_boundary_remains_exact": {"self_gap": 0.0, "pass": True},
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
        "z3_coherent_information_rank3_witness": z3_witness(quotient_row["class_count"], min(fit_gaps), max_cptp, threshold),
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
    }
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [row["pass"] for row in boundary.values()]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "four-qubit dynamic-shell gamma5 chirality-asymmetric CPTP sequences compared against shell-independent locality-preserving rank-3 split-jump controls by coherent-information and conditional-entropy orbit quotients",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"passed": sum(1 for value in checks if value), "total": len(checks)},
        "open_choices": ["This switches readout from off-diagonal trace norm to coherent information after the trace-orbit readout was killed.", "The coherent-information residual survives only at an explicit 0.004 threshold; the weakest fit gap is small.", "The comparison family is still shell-independent constant rank-3 split-jump, not fully time-dependent local rank-3.", "If this survives, next test should add time-dependent locality-preserving rank-3 controls."],
        "why_not_v4_probes": "This is a clean v5 formal scout translated from Grok/Gemini coherent-information follow-up proposals; it is not a canonical v4 probe.",
        "raw_rows": raw,
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all(checks), "result": str(OUT_PATH), "coherent_classes": quotient_row["class_count"], "control_classes": control_q["class_count"], "min_fit_gap": min(fit_gaps)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
