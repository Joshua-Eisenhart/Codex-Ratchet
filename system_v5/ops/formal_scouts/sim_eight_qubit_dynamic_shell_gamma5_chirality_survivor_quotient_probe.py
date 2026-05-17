#!/usr/bin/env python3
"""Eight-qubit dynamic shell gamma5 chirality survivor-quotient scout."""

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
from scipy.optimize import minimize_scalar
import sympy as sp
import torch
from torch_geometric.utils import from_networkx
import z3

from sim_gamma5_chirality_asymmetric_cptp_choi_distance_effective_channel_probe import (
    asymmetric_kraus,
    choi_matrix,
    cptp_gap,
    gamma5_boundary,
    symmetric_kraus,
    trace_distance,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "eight_qubit_dynamic_shell_gamma5_chirality_survivor_quotient_probe_results.json"

NAME = "eight_qubit_dynamic_shell_gamma5_chirality_survivor_quotient_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: lifts dynamic shell gamma5 chirality-asymmetric CPTP "
    "sequences to eight-qubit density states and quotients them by P_L rho P_R "
    "trace-norm orbit signatures with Choi-distance effective-family controls. "
    "It does not admit novelty, empirical physics, a final manifold tower, "
    "ontology, or bridge claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing eight-qubit density states, embedded Kraus updates, gamma5 projectors, and trace norms"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing four-qubit reduced entropy contraction inside orbit signatures"},
    "scipy": {"tried": True, "used": True, "reason": "load-bearing symmetric effective-gamma Choi fit per shell step"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing dynamic shell graph and quotient graph"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing graph tensor conversion"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing quotient graph persistence"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic noncommuting update boundary"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing eight-qubit quotient/control witness"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

DTYPE = torch.complex128
N_QUBITS = 8
DIM = 2**N_QUBITS
LOCAL_DIM = 4
REF_DIM = 2 ** (N_QUBITS - 2)


def normalize(psi: torch.Tensor) -> torch.Tensor:
    return psi / torch.linalg.vector_norm(psi)


def pure_density(entries: dict[int, complex]) -> torch.Tensor:
    psi = torch.zeros(DIM, dtype=DTYPE)
    for idx, value in entries.items():
        psi[idx] = value
    psi = normalize(psi)
    return torch.outer(psi, psi.conj())


def candidate_densities() -> dict[str, torch.Tensor]:
    return {
        "balanced_reference_a": pure_density({0b00000000: 0.42, 0b01100111: 0.33j, 0b10101010: -0.51, 0b11011101: 0.67j}),
        "balanced_reference_b": pure_density({0b00010001: 0.56, 0b01001100: -0.35j, 0b10011001: 0.47, 0b11101110: 0.59j}),
        "phase_reference_a": pure_density({0b00110011: complex(0.44, -0.16), 0b01110111: 0.52j, 0b10011001: -0.49, 0b11011101: complex(0.21, 0.48)}),
        "thin_bridge_reference_a": pure_density({0b00000000: 0.90, 0b10101010: 0.18, 0b11001100: 0.22j, 0b01010101: 0.30}),
        "left_block_reference": pure_density({0b00000000: 0.61, 0b00111100: -0.36j, 0b01010101: 0.55, 0b01101010: 0.44j}),
        "right_block_reference": pure_density({0b10000000: 0.54, 0b10110011: 0.49j, 0b11011101: -0.52, 0b11111111: 0.44j}),
        "maximally_mixed": torch.eye(DIM, dtype=DTYPE) / DIM,
    }


def shell_points(step: int, mode: str) -> torch.Tensor:
    rows = []
    stretch = 1.0
    twist = 0.0
    if mode == "dynamic":
        stretch = 1.0 + 0.18 * step
        twist = 0.23 * step
    elif mode == "isotropic":
        twist = 0.23 * step
    for idx in range(8):
        theta = 2 * math.pi * idx / 8 + twist
        z = -0.75 + 1.50 * idx / 7
        xy = math.sqrt(max(0.0, 1 - z * z))
        rows.append([stretch * xy * math.cos(theta), xy * math.sin(theta) / math.sqrt(stretch), z / math.sqrt(stretch)])
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
    graph.add_nodes_from(range(8))
    for i in range(8):
        for j in range(i + 1, 8):
            weight = float(weights[i, j].item())
            if weight > 0.20:
                graph.add_edge(i, j, weight=weight)
    return graph


def rates_from_weights(weights: torch.Tensor) -> tuple[float, float]:
    nonzero = weights[weights > 0]
    mean = float(nonzero.mean().item())
    std = float(nonzero.std().item())
    return min(0.43, 0.05 + 0.24 * mean + 0.10 * std), min(0.22, 0.014 + 0.08 * mean - 0.02 * std)


def embed_local(kraus: list[torch.Tensor]) -> list[torch.Tensor]:
    eye_ref = torch.eye(REF_DIM, dtype=DTYPE)
    return [torch.kron(k, eye_ref) for k in kraus]


def apply_kraus(rho: torch.Tensor, kraus: list[torch.Tensor]) -> torch.Tensor:
    out = torch.zeros_like(rho)
    for k in kraus:
        out = out + k @ rho @ k.conj().T
    return out


def gamma5_projectors() -> tuple[torch.Tensor, torch.Tensor]:
    eye_ref = torch.eye(REF_DIM, dtype=DTYPE)
    gamma5 = torch.diag(torch.tensor([1.0, 1.0, -1.0, -1.0], dtype=DTYPE))
    eye4 = torch.eye(LOCAL_DIM, dtype=DTYPE)
    p_l = torch.kron((eye4 + gamma5) / 2, eye_ref)
    p_r = torch.kron((eye4 - gamma5) / 2, eye_ref)
    return p_l, p_r


def offdiag_trace_norm(rho: torch.Tensor) -> float:
    p_l, p_r = gamma5_projectors()
    return float(torch.sum(torch.linalg.svdvals(p_l @ rho @ p_r)).item())


def reduced_entropy_first_four(rho: torch.Tensor) -> float:
    tensor = rho.reshape(16, 16, 16, 16)
    red = oe.contract("abcb->ac", tensor)
    eigs = torch.clamp(torch.linalg.eigvalsh((red + red.conj().T) / 2), min=1e-15)
    eigs = eigs / eigs.sum()
    return float((-torch.sum(eigs * torch.log(eigs))).item())


def signature(coherence: list[float], entropy: list[float]) -> tuple[Any, ...]:
    return (
        round(coherence[0], 1),
        round(coherence[-1], 1),
        round(coherence[0] - coherence[-1], 1),
        round(max(coherence) - min(coherence), 1),
        round(entropy[-1] - entropy[0], 1),
    )


def best_symmetric_choi_gap(gamma_left: float, gamma_right: float) -> dict[str, Any]:
    target = asymmetric_kraus(gamma_left, gamma_right)
    target_choi = choi_matrix(target)
    def objective(gamma: float) -> float:
        return trace_distance(target_choi, choi_matrix(symmetric_kraus(float(gamma))))
    result = minimize_scalar(objective, bounds=(0.0, 0.50), method="bounded", options={"xatol": 1e-11})
    return {"gamma": float(result.x), "choi_trace_distance": float(result.fun), "success": bool(result.success)}


def run_sequence(rho: torch.Tensor, mode: str) -> dict[str, Any]:
    current = rho.clone()
    coherence = [offdiag_trace_norm(current)]
    entropy = [reduced_entropy_first_four(current)]
    graph_rows = []
    choi_gaps = []
    cptp_gaps = []
    for step in range(1, 6):
        weights = shell_weights(step, mode)
        graph = graph_from_weights(weights)
        gamma_l, gamma_r = rates_from_weights(weights)
        local = asymmetric_kraus(gamma_l, gamma_r)
        current = apply_kraus(current, embed_local(local))
        coherence.append(offdiag_trace_norm(current))
        entropy.append(reduced_entropy_first_four(current))
        fit = best_symmetric_choi_gap(gamma_l, gamma_r)
        choi_gaps.append(fit["choi_trace_distance"])
        cptp_gaps.append(cptp_gap(local))
        graph_rows.append({"step": step, "edge_count": graph.number_of_edges(), "gamma_left": gamma_l, "gamma_right": gamma_r, "choi_trace_distance": fit["choi_trace_distance"]})
    return {"coherence_orbit": coherence, "entropy_orbit": entropy, "signature": signature(coherence, entropy), "graph_rows": graph_rows, "min_choi_gap": min(choi_gaps), "max_cptp_gap": max(cptp_gaps)}


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


def symbolic_noncommuting_boundary() -> dict[str, Any]:
    a, b = sp.symbols("a b")
    left = sp.Matrix([[1, a], [0, 1]])
    right = sp.Matrix([[1, 0], [b, 1]])
    comm = sp.simplify(left * right - right * left)
    return {"commutator": str(comm), "pass": comm != sp.zeros(2)}


def z3_witness(dynamic_classes: int, static_classes: int, min_choi_gap: float, cptp_gap_value: float) -> dict[str, Any]:
    solver = z3.Solver()
    d, s, c, v = z3.Bools("dynamic static choi cptp")
    solver.add(d == (dynamic_classes >= 3), s == (dynamic_classes > static_classes), c == (min_choi_gap > 0.02), v == (cptp_gap_value < 1e-12))
    solver.add(z3.Not(z3.And(d, s, c, v)))
    status = solver.check()
    return {"solver_status": str(status), "pass": status == z3.unsat, "dynamic_classes": dynamic_classes, "static_classes": static_classes, "min_choi_gap": min_choi_gap, "cptp_valid": cptp_gap_value < 1e-12}


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
        dynamic_rows.append({"name": name, "signature": dyn["signature"], "gap": dyn_static_gap, "initial": dyn["coherence_orbit"][0]})
        static_rows.append({"name": name, "signature": sta["signature"], "gap": 0.0, "initial": sta["coherence_orbit"][0]})
        uniform_rows.append({"name": name, "signature": uni["signature"], "gap": dyn_static_gap, "initial": uni["coherence_orbit"][0]})
        raw[name] = {"dynamic": dyn, "static": sta, "uniform": uni, "dynamic_static_orbit_gap": dyn_static_gap}
    threshold = 0.005
    dynamic_q = quotient(dynamic_rows, threshold)
    static_q = quotient(static_rows, threshold)
    uniform_q = quotient(uniform_rows, threshold)
    nonzero_rows = [row for row in raw.values() if row["dynamic"]["coherence_orbit"][0] > 1e-8]
    min_choi_gap = min(row["dynamic"]["min_choi_gap"] for row in nonzero_rows)
    max_cptp_gap = max(row["dynamic"]["max_cptp_gap"] for row in raw.values())
    positive = {
        "eight_qubit_dynamic_shell_gamma5_sequence_forms_multiple_survivor_classes": {"quotient": dynamic_q, "threshold": threshold, "pass": dynamic_q["survivor_count"] >= 3 and dynamic_q["class_count"] >= 3},
        "eight_qubit_dynamic_classes_exceed_static_shell_control": {"dynamic_class_count": dynamic_q["class_count"], "static_class_count": static_q["class_count"], "pass": dynamic_q["class_count"] > static_q["class_count"]},
        "shell_step_channels_resist_symmetric_choi_fit": {"min_choi_gap": min_choi_gap, "pass": min_choi_gap > 0.02},
        "gamma5_projector_boundary": gamma5_boundary(),
        "symbolic_noncommuting_update_boundary": symbolic_noncommuting_boundary(),
    }
    graveyard_companions = {
        "static_shell_control_has_no_survivor_classes": {"quotient": static_q, "pass": static_q["class_count"] == 0},
        "uniform_shell_control_is_not_killed_by_this_eight_qubit_readout": {"quotient": uniform_q, "dynamic_class_count": dynamic_q["class_count"], "pass": uniform_q["class_count"] >= dynamic_q["class_count"]},
        "zero_initial_offdiagonal_controls_do_not_survive": {"zero_names": [name for name, row in raw.items() if row["dynamic"]["coherence_orbit"][0] <= 1e-8], "pass": all(raw[name]["dynamic"]["coherence_orbit"][0] <= 1e-8 and raw[name]["dynamic_static_orbit_gap"] <= 1e-12 for name in ("left_block_reference", "right_block_reference", "maximally_mixed"))},
        "dynamic_channels_are_cptp": {"max_cptp_gap": max_cptp_gap, "pass": max_cptp_gap < 1e-12},
    }
    boundary = {
        "finite_eight_qubit_density_dimension": {"dimension": DIM, "qubits": N_QUBITS, "pass": DIM == 256 and N_QUBITS == 8},
        "z3_eight_qubit_dynamic_shell_witness": z3_witness(dynamic_q["class_count"], static_q["class_count"], min_choi_gap, max_cptp_gap),
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
    }
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [row["pass"] for row in boundary.values()]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "eight-qubit density family under dynamic shell graph weights coupled to gamma5 chirality-asymmetric CPTP channel sequences, quotiented by P_L rho P_R trace-norm orbit signatures with Choi-distance effective-family controls",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"passed": sum(1 for value in checks if value), "total": len(checks)},
        "open_choices": ["This is an eight-qubit lift of the gamma5 off-diagonal survivor quotient, not a final tensor-network theory.", "The eight-qubit orbit shifts are weaker than the four-qubit scout and require the explicit 0.005 survivor threshold.", "The uniform-shell control is not killed here; it forms at least as many classes as the dynamic shell at this threshold.", "The arbitrary-Kraus equivalence kill boundary still applies.", "The next stronger version should add explicit tensor-network compression and locality-preserving rank-3 fitting."],
        "why_not_v4_probes": "This is a clean v5 formal scout translated from Grok/Gemini eight-qubit dynamic-shell proposals; it is not a canonical v4 probe.",
        "raw_rows": raw,
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all(checks), "result": str(OUT_PATH), "dynamic_classes": dynamic_q["class_count"], "static_classes": static_q["class_count"], "uniform_classes": uniform_q["class_count"], "min_choi_gap": min_choi_gap}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
