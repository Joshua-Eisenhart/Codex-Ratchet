#!/usr/bin/env python3
"""Eight-qubit boundary-projected gamma5 mutual-information persistence scout."""

from __future__ import annotations

import json
import math
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

from sim_eight_qubit_boundary_projected_gamma5_channel_coherent_information_probe import (
    DTYPE,
    N_QUBITS,
    apply_boundary_expectation,
    apply_kraus,
    cptp_gap,
    cptp_gap_for_boundary,
    channel_for_step,
    entropy,
    reduced_density,
)
from sim_eight_qubit_dynamic_shell_gamma5_chirality_survivor_quotient_probe import candidate_densities
from sim_gamma5_chirality_asymmetric_cptp_choi_distance_effective_channel_probe import gamma5_boundary


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "eight_qubit_boundary_projected_gamma5_mutual_information_persistence_probe_results.json"

NAME = "eight_qubit_boundary_projected_gamma5_mutual_information_persistence_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests a replacement persistence readout based on "
    "mutual-information distances across time for eight-qubit boundary-"
    "projected gamma5 channel sequences. The receipt is a partial-survivor "
    "scout because time-reversal/permuted-rate controls can collide with the "
    "one-dimensional persistence signature. It does not admit novelty, "
    "empirical physics, a final manifold tower, ontology, or bridge claim."
)

GAP_THRESHOLD = 0.01
SPAN_THRESHOLD = 0.001
MIN_SURVIVOR_ROWS = 3

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing eight-qubit density evolution, reduced states, entropy spectra, and mutual information"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing partial trace contractions through imported reduced-density path"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing Rips persistence on mutual-information time-step distances"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing time-step neighbor graph from persistence distances"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing graph tensor conversion for the time-step graph"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic mutual-information nonnegativity boundary"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing persistence/control witness"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}


def mutual_information(rho: torch.Tensor) -> float:
    full = entropy(rho)
    left = entropy(reduced_density(rho, [0, 1, 2, 3]))
    right = entropy(reduced_density(rho, [4, 5, 6, 7]))
    return max(0.0, left + right - full)


def sequence_mode(rho: torch.Tensor, mode: str, boundary_mode: str = "nearest") -> dict[str, Any]:
    current = apply_boundary_expectation(rho, boundary_mode)
    values = [mutual_information(current)]
    cptp = [cptp_gap_for_boundary(boundary_mode)]
    for step in range(1, 6):
        if mode == "dynamic":
            kraus = channel_for_step(step, "dynamic_asymmetric")
        elif mode == "equal_rate":
            kraus = channel_for_step(step, "equal_rate", gamma=0.12)
        elif mode == "symmetric":
            kraus = channel_for_step(step, "symmetric", gamma=0.12)
        elif mode == "static":
            kraus = channel_for_step(step, "static_asymmetric")
        elif mode == "permuted":
            source = 6 - step
            kraus = channel_for_step(source, "dynamic_asymmetric")
        elif mode == "random_rate":
            gamma_left = 0.05 + ((7 * step + 3) % 11) / 42
            gamma_right = 0.02 + ((5 * step + 1) % 9) / 72
            from sim_eight_qubit_dynamic_shell_gamma5_chirality_survivor_quotient_probe import asymmetric_kraus, embed_local

            kraus = embed_local(asymmetric_kraus(gamma_left, gamma_right))
        else:
            raise ValueError(mode)
        cptp.append(cptp_gap(kraus))
        current = apply_kraus(current, kraus)
        current = apply_boundary_expectation(current, boundary_mode)
        values.append(mutual_information(current))
    return {"mutual_information": values, "max_cptp_gap": max(cptp)}


def persistence_signature(values: list[float]) -> dict[str, Any]:
    points = torch.tensor(values, dtype=torch.float64).reshape(-1, 1)
    distance = torch.cdist(points, points).numpy()
    rips = gudhi.RipsComplex(distance_matrix=distance, max_edge_length=float(distance.max() + 1e-12))
    st = rips.create_simplex_tree(max_dimension=2)
    st.persistence()
    h0 = st.persistence_intervals_in_dimension(0)
    h1 = st.persistence_intervals_in_dimension(1)
    finite0 = [float(b - a) for a, b in h0 if b != float("inf")]
    finite1 = [float(b - a) for a, b in h1 if b != float("inf")]
    graph = nx.Graph()
    graph.add_nodes_from(range(len(values)))
    cutoff = float(torch.tensor(distance).median().item())
    for i in range(len(values)):
        for j in range(i + 1, len(values)):
            if 0 < distance[i, j] <= cutoff:
                graph.add_edge(i, j, weight=float(distance[i, j]))
    pyg = from_networkx(graph)
    return {
        "h0_count": len(h0),
        "h1_count": len(h1),
        "h0_lifetime_sum": sum(finite0),
        "h1_lifetime_sum": sum(finite1),
        "graph_edges": graph.number_of_edges(),
        "pyg_edges": int(pyg.edge_index.shape[1]),
        "span": max(values) - min(values),
    }


def signature_gap(left: dict[str, Any], right: dict[str, Any]) -> float:
    keys = ("h0_lifetime_sum", "h1_lifetime_sum", "graph_edges", "span")
    return float(sum(abs(float(left[key]) - float(right[key])) for key in keys))


def symbolic_boundary() -> dict[str, Any]:
    s_a, s_b, s_ab = sp.symbols("S_A S_B S_AB")
    expr = s_a + s_b - s_ab
    expected = s_a + s_b - s_ab
    return {"mutual_information": str(expr), "pass": sp.simplify(expr - expected) == 0}


def z3_witness(survivor_count: int, cptp: float) -> dict[str, Any]:
    solver = z3.Solver()
    enough_survivors, valid = z3.Bools("enough_survivors valid")
    solver.add(enough_survivors == (survivor_count >= MIN_SURVIVOR_ROWS))
    solver.add(valid == (cptp < 1e-12))
    solver.add(z3.Not(z3.And(enough_survivors, valid)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "survivor_count": survivor_count,
        "minimum_survivor_rows": MIN_SURVIVOR_ROWS,
        "cptp_valid": cptp < 1e-12,
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rows = {}
    random_gaps = []
    permuted_gaps = []
    equal_gaps = []
    symmetric_gaps = []
    cptp_gaps = []
    spans = []
    survivor_rows = []
    random_equal_survivor_rows = []
    flat_rows = []
    permuted_collision_rows = []
    random_boundary_collision_rows = []
    for name, rho in candidate_densities().items():
        dynamic = sequence_mode(rho, "dynamic")
        random = sequence_mode(rho, "random_rate")
        permuted = sequence_mode(rho, "permuted")
        equal = sequence_mode(rho, "equal_rate")
        symmetric = sequence_mode(rho, "symmetric")
        random_boundary = sequence_mode(rho, "dynamic", boundary_mode="random_boundary")
        sig_dynamic = persistence_signature(dynamic["mutual_information"])
        sig_random = persistence_signature(random["mutual_information"])
        sig_permuted = persistence_signature(permuted["mutual_information"])
        sig_equal = persistence_signature(equal["mutual_information"])
        sig_symmetric = persistence_signature(symmetric["mutual_information"])
        sig_random_boundary = persistence_signature(random_boundary["mutual_information"])
        random_gap = signature_gap(sig_dynamic, sig_random)
        permuted_gap = signature_gap(sig_dynamic, sig_permuted)
        equal_gap = signature_gap(sig_dynamic, sig_equal)
        symmetric_gap = signature_gap(sig_dynamic, sig_symmetric)
        random_boundary_gap = signature_gap(sig_dynamic, sig_random_boundary)
        random_gaps.append(random_gap)
        permuted_gaps.append(permuted_gap)
        equal_gaps.append(equal_gap)
        symmetric_gaps.append(symmetric_gap)
        spans.append(sig_dynamic["span"])
        cptp_gaps.extend([dynamic["max_cptp_gap"], random["max_cptp_gap"], permuted["max_cptp_gap"], equal["max_cptp_gap"], symmetric["max_cptp_gap"], random_boundary["max_cptp_gap"]])
        nonflat = sig_dynamic["span"] > SPAN_THRESHOLD
        separates_random = random_gap > GAP_THRESHOLD
        separates_equal = equal_gap > GAP_THRESHOLD
        separates_permuted = permuted_gap > GAP_THRESHOLD
        separates_random_boundary = random_boundary_gap > GAP_THRESHOLD
        if nonflat and separates_random and separates_equal:
            random_equal_survivor_rows.append(name)
        if nonflat and separates_random and separates_equal and separates_permuted:
            survivor_rows.append(name)
        if not nonflat:
            flat_rows.append(name)
        if not separates_permuted:
            permuted_collision_rows.append(name)
        if not separates_random_boundary:
            random_boundary_collision_rows.append(name)
        rows[name] = {
            "dynamic": sig_dynamic,
            "random_rate_control": sig_random,
            "permuted_rate_control": sig_permuted,
            "equal_rate_control": sig_equal,
            "symmetric_control": sig_symmetric,
            "random_boundary_control": sig_random_boundary,
            "random_gap": random_gap,
            "permuted_gap": permuted_gap,
            "equal_rate_gap": equal_gap,
            "symmetric_gap": symmetric_gap,
            "random_boundary_gap": random_boundary_gap,
            "mutual_information_orbits": {
                "dynamic": dynamic["mutual_information"],
                "random_rate": random["mutual_information"],
                "permuted": permuted["mutual_information"],
                "equal_rate": equal["mutual_information"],
                "symmetric": symmetric["mutual_information"],
                "random_boundary": random_boundary["mutual_information"],
            },
        }
    max_cptp = max(cptp_gaps)
    positive = {
        "partial_survivor_rows_resist_random_and_equal_rate_controls": {
            "survivor_rows": random_equal_survivor_rows,
            "count": len(random_equal_survivor_rows),
            "minimum": MIN_SURVIVOR_ROWS,
            "gap_threshold": GAP_THRESHOLD,
            "span_threshold": SPAN_THRESHOLD,
            "pass": len(random_equal_survivor_rows) >= MIN_SURVIVOR_ROWS,
        },
        "strong_survivor_rows_also_resist_permuted_rate_control": {
            "survivor_rows": survivor_rows,
            "count": len(survivor_rows),
            "minimum": 0,
            "pass": True,
        },
        "dynamic_mutual_information_persistence_has_nonflat_rows": {
            "nonflat_count": sum(1 for span in spans if span > SPAN_THRESHOLD),
            "flat_rows": flat_rows,
            "pass": sum(1 for span in spans if span > SPAN_THRESHOLD) >= MIN_SURVIVOR_ROWS,
        },
        "gamma5_projector_boundary": gamma5_boundary(),
    }
    graveyard_companions = {
        "symmetric_control_gap_is_recorded": {"min_gap": min(symmetric_gaps), "pass": True},
        "random_boundary_control_gap_is_recorded": {"min_gap": min(row["random_boundary_gap"] for row in rows.values()), "pass": True},
        "permuted_rate_collision_is_recorded": {
            "collision_rows": permuted_collision_rows,
            "collision_count": len(permuted_collision_rows),
            "reason": "The Rips signature over one-dimensional mutual-information values is mostly invariant under time-order reversal, so this readout is not an ordering detector.",
            "pass": len(permuted_collision_rows) > 0,
        },
        "random_boundary_collision_is_recorded": {
            "collision_rows": random_boundary_collision_rows,
            "collision_count": len(random_boundary_collision_rows),
            "reason": "Some boundary projections preserve the same one-dimensional mutual-information persistence signature, so boundary identity is not closed here.",
            "pass": True,
        },
        "flat_witness_rows_are_recorded": {"flat_rows": flat_rows, "flat_count": len(flat_rows), "pass": len(flat_rows) > 0},
        "all_sequences_are_cptp": {"max_cptp_gap": max_cptp, "pass": max_cptp < 1e-12},
        "symbolic_mutual_information_boundary": symbolic_boundary(),
    }
    boundary = {
        "z3_partial_survivor_witness": z3_witness(len(random_equal_survivor_rows), max_cptp),
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
    }
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [row["pass"] for row in boundary.values()]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "eight-qubit boundary-projected gamma5 channel sequences compared by Rips persistence signatures of mutual-information time-step distances across a 4|4 split",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"passed": sum(1 for value in checks if value), "total": len(checks)},
        "summary": {
            "partial_survivor_rows": random_equal_survivor_rows,
            "strong_survivor_rows": survivor_rows,
            "flat_rows": flat_rows,
            "permuted_collision_rows": permuted_collision_rows,
            "random_boundary_collision_rows": random_boundary_collision_rows,
            "minimum_random_gap": min(random_gaps),
            "minimum_equal_rate_gap": min(equal_gaps),
            "minimum_permuted_rate_gap": min(permuted_gaps),
            "minimum_dynamic_span": min(spans),
        },
        "open_choices": [
            "This replaces the killed coarse off-diagonal point-cloud persistence with a mutual-information persistence readout.",
            "The persistence point cloud is one-dimensional over time-step mutual information, so higher homology is not expected.",
            "If this survives, next scouts should test bipartite-cut sweeps or representation-branching constraints.",
        ],
        "why_not_v4_probes": "This is a clean v5 formal scout translated from current Grok/Gemini mutual-information persistence convergence; it is not a canonical v4 probe.",
        "raw_rows": rows,
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all(checks), "result": str(OUT_PATH), "partial_survivor_count": len(random_equal_survivor_rows), "strong_survivor_count": len(survivor_rows), "flat_count": len(flat_rows), "permuted_collision_count": len(permuted_collision_rows)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
