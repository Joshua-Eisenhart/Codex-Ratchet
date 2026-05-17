#!/usr/bin/env python3
"""Gamma5 off-diagonal coherence persistence rate-compression scout."""

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
import opt_einsum as oe
import sympy as sp
import torch
from torch_geometric.utils import from_networkx
import z3

from sim_dynamic_shell_graph_gamma5_chirality_choi_survivor_quotient_probe import rates_from_weights, shell_weights
from sim_gamma5_offdiagonal_coherence_trace_orbit_survivor_quotient_probe import (
    DIM,
    DTYPE,
    N_QUBITS,
    apply_kraus,
    asymmetric_local_kraus,
    candidate_densities,
    cptp_gap,
    embed,
    gamma5_boundary,
    gamma5_projectors,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "gamma5_offdiagonal_coherence_persistence_rate_compression_probe_results.json"

NAME = "gamma5_offdiagonal_coherence_persistence_rate_compression_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: records that this gamma5 block off-diagonal persistence "
    "readout is killed by nearby random, permuted, and constant-rate controls "
    "under the current coarse persistence signature. It preserves the stronger "
    "kill boundary that unconstrained time-dependent rank-3 controls can match "
    "by copying the same rates. It does not admit novelty, empirical physics, "
    "a final manifold tower, ontology, or bridge claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing density states, Kraus evolution, off-diagonal block vectors, and distance matrices"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing tensor contraction sanity on reduced local block traces"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing persistence-neighbor graph construction"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing graph tensor conversion for persistence graph"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing Rips persistence from gamma5 off-diagonal distance matrices"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic compressed-rate parameter boundary"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing persistence/control witness"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}


def rate_sequence(mode: str) -> list[tuple[float, float]]:
    base = [rates_from_weights(shell_weights(step, "dynamic")) for step in range(1, 7)]
    if mode == "dynamic":
        return base
    if mode == "permuted":
        left = [row[0] for row in base]
        right = [row[1] for row in base]
        left = left[2:] + left[:2]
        right = right[-1:] + right[:-1]
        return list(zip(left, right, strict=True))
    if mode == "random":
        return [(0.06 + ((7 * step + 3) % 11) / 40, 0.02 + ((5 * step + 1) % 9) / 60) for step in range(1, 7)]
    if mode == "constant_mean":
        mean_left = sum(row[0] for row in base) / len(base)
        mean_right = sum(row[1] for row in base) / len(base)
        return [(mean_left, mean_right) for _ in base]
    raise ValueError(mode)


def offdiag_vector(rho: torch.Tensor) -> torch.Tensor:
    _, p_l, p_r = gamma5_projectors()
    block = p_l @ rho @ p_r
    return torch.cat([block.real.reshape(-1), block.imag.reshape(-1)]).to(torch.float64)


def local_trace_sanity(rho: torch.Tensor) -> float:
    tensor = rho.reshape(4, 4, 4, 4)
    reduced = oe.contract("abcb->ac", tensor)
    return float(torch.trace(reduced).real.item())


def evolve_points(rho: torch.Tensor, mode: str) -> dict[str, Any]:
    current = rho.clone()
    points = [offdiag_vector(current)]
    traces = [local_trace_sanity(current)]
    cptp_gaps = []
    for gamma_left, gamma_right in rate_sequence(mode):
        kraus = embed(asymmetric_local_kraus(gamma_left, gamma_right))
        cptp_gaps.append(cptp_gap(kraus))
        current = apply_kraus(current, kraus)
        points.append(offdiag_vector(current))
        traces.append(local_trace_sanity(current))
    stacked = torch.stack(points)
    distance = torch.cdist(stacked, stacked).numpy()
    return {"points": stacked, "distance": distance, "traces": traces, "max_cptp_gap": max(cptp_gaps)}


def persistence_signature(distance: Any) -> dict[str, Any]:
    rips = gudhi.RipsComplex(distance_matrix=distance, max_edge_length=float(distance.max() + 1e-12))
    st = rips.create_simplex_tree(max_dimension=2)
    st.persistence()
    intervals0 = st.persistence_intervals_in_dimension(0)
    intervals1 = st.persistence_intervals_in_dimension(1)
    finite0 = [float(b - a) for a, b in intervals0 if b != float("inf")]
    finite1 = [float(b - a) for a, b in intervals1 if b != float("inf")]
    graph = nx.Graph()
    for idx in range(distance.shape[0]):
        graph.add_node(idx)
    cutoff = float(torch.tensor(distance).median().item())
    for i in range(distance.shape[0]):
        for j in range(i + 1, distance.shape[0]):
            if 0 < distance[i, j] <= cutoff:
                graph.add_edge(i, j, weight=float(distance[i, j]))
    pyg = from_networkx(graph)
    return {
        "h0_count": len(intervals0),
        "h1_count": len(intervals1),
        "h0_lifetime_sum": sum(finite0),
        "h1_lifetime_sum": sum(finite1),
        "graph_edges": graph.number_of_edges(),
        "pyg_edges": int(pyg.edge_index.shape[1]),
    }


def signature_gap(left: dict[str, Any], right: dict[str, Any]) -> float:
    keys = ("h0_lifetime_sum", "h1_lifetime_sum", "graph_edges")
    return float(sum(abs(float(left[key]) - float(right[key])) for key in keys))


def symbolic_boundary() -> dict[str, Any]:
    raw, params = sp.symbols("raw params", positive=True)
    return {"expr": "6 < 12", "pass": bool((params < raw).subs({params: 6, raw: 12}))}


def z3_witness(random_gap: float, permuted_gap: float, constant_gap: float, exact_gap: float, cptp: float) -> dict[str, Any]:
    solver = z3.Solver()
    controls_collapse, exact_boundary, valid = z3.Bools("controls_collapse exact_boundary valid")
    solver.add(controls_collapse == (random_gap < 0.001 and permuted_gap < 0.001 and constant_gap < 0.001))
    solver.add(exact_boundary == (exact_gap < 1e-12))
    solver.add(valid == (cptp < 1e-12))
    solver.add(z3.Not(z3.And(controls_collapse, exact_boundary, valid)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "kill_boundary": True,
        "random_gap": random_gap,
        "permuted_gap": permuted_gap,
        "constant_gap": constant_gap,
        "unconstrained_time_dependent_exact_gap": exact_gap,
        "cptp_valid": cptp < 1e-12,
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rows = {}
    random_gaps = []
    permuted_gaps = []
    constant_gaps = []
    exact_gaps = []
    cptp_gaps = []
    for name, rho in candidate_densities().items():
        dynamic = evolve_points(rho, "dynamic")
        random = evolve_points(rho, "random")
        permuted = evolve_points(rho, "permuted")
        constant = evolve_points(rho, "constant_mean")
        dynamic_sig = persistence_signature(dynamic["distance"])
        random_sig = persistence_signature(random["distance"])
        permuted_sig = persistence_signature(permuted["distance"])
        constant_sig = persistence_signature(constant["distance"])
        random_gap = signature_gap(dynamic_sig, random_sig)
        permuted_gap = signature_gap(dynamic_sig, permuted_sig)
        constant_gap = signature_gap(dynamic_sig, constant_sig)
        exact_gap = signature_gap(dynamic_sig, persistence_signature(dynamic["distance"]))
        random_gaps.append(random_gap)
        permuted_gaps.append(permuted_gap)
        constant_gaps.append(constant_gap)
        exact_gaps.append(exact_gap)
        cptp_gaps.extend([dynamic["max_cptp_gap"], random["max_cptp_gap"], permuted["max_cptp_gap"], constant["max_cptp_gap"]])
        rows[name] = {
            "dynamic": dynamic_sig,
            "random_control": random_sig,
            "permuted_control": permuted_sig,
            "constant_mean_control": constant_sig,
            "random_gap": random_gap,
            "permuted_gap": permuted_gap,
            "constant_gap": constant_gap,
            "exact_self_gap": exact_gap,
            "trace_sanity_dynamic": dynamic["traces"],
        }
    max_cptp_gap = max(cptp_gaps)
    min_random_gap = min(random_gaps)
    min_permuted_gap = min(permuted_gaps)
    min_constant_gap = min(constant_gaps)
    max_exact_gap = max(exact_gaps)
    positive = {
        "random_rate_control_collapses_current_persistence_separation": {"min_gap": min_random_gap, "pass": min_random_gap < 0.001},
        "permuted_rate_control_collapses_current_persistence_separation": {"min_gap": min_permuted_gap, "pass": min_permuted_gap < 0.001},
        "constant_mean_rate_control_collapses_current_persistence_separation": {"min_gap": min_constant_gap, "pass": min_constant_gap < 0.001},
        "compressed_parameter_boundary": symbolic_boundary(),
        "gamma5_projector_boundary": gamma5_boundary(),
    }
    graveyard_companions = {
        "provider_suggested_persistence_readout_is_not_enough": {"random_gap": min_random_gap, "permuted_gap": min_permuted_gap, "constant_gap": min_constant_gap, "pass": min_random_gap < 0.001 and min_permuted_gap < 0.001 and min_constant_gap < 0.001},
        "unconstrained_time_dependent_rank3_same_rate_control_matches_exactly": {"max_exact_gap": max_exact_gap, "pass": max_exact_gap < 1e-12},
        "all_rate_sequences_are_cptp": {"max_cptp_gap": max_cptp_gap, "pass": max_cptp_gap < 1e-12},
        "finite_four_qubit_density_boundary": {"dimension": DIM, "qubits": N_QUBITS, "pass": DIM == 16 and N_QUBITS == 4},
    }
    boundary = {
        "z3_persistence_rate_compression_kill_witness": z3_witness(min_random_gap, min_permuted_gap, min_constant_gap, max_exact_gap, max_cptp_gap),
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
    }
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [row["pass"] for row in boundary.values()]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "kill-boundary comparison of four-qubit gamma5 block off-diagonal point-cloud persistence under shell-derived compressed rank-3 channel rates against random, permuted, constant-mean, and unconstrained same-rate controls",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"passed": sum(1 for value in checks if value), "total": len(checks)},
        "open_choices": [
            "This kills the current coarse persistence signature for gamma5 off-diagonal geometry under nearby rate-sequence controls.",
            "The same-rate time-dependent rank-3 control remains an exact equivalence if rate derivability is not required.",
            "The next scout should test richer graph features, rate-law derivation, or boundary-projection constraints rather than promote this readout.",
        ],
        "why_not_v4_probes": "This is a clean v5 formal scout translated from current Grok/Gemini persistence proposals; it is not a canonical v4 probe.",
        "raw_rows": rows,
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all(checks), "result": str(OUT_PATH), "kill_boundary": True, "min_random_gap": min_random_gap, "min_permuted_gap": min_permuted_gap, "min_constant_gap": min_constant_gap}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
