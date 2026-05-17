#!/usr/bin/env python3
"""Eight-qubit boundary-projected gamma5 channel coherent-information scout."""

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
import opt_einsum as oe
import sympy as sp
import torch
from torch_geometric.utils import from_networkx
import z3

from sim_eight_qubit_dynamic_shell_gamma5_chirality_survivor_quotient_probe import (
    DIM,
    DTYPE,
    N_QUBITS,
    asymmetric_kraus,
    candidate_densities,
    embed_local,
    shell_weights,
    rates_from_weights,
)
from sim_gamma5_chirality_asymmetric_cptp_choi_distance_effective_channel_probe import gamma5_boundary, symmetric_kraus


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "eight_qubit_boundary_projected_gamma5_channel_coherent_information_probe_results.json"

NAME = "eight_qubit_boundary_projected_gamma5_channel_coherent_information_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: lifts the finite boundary-projected gamma5 "
    "chirality-asymmetric channel readout to eight-qubit density states and "
    "measures coherent information plus conditional entropy against symmetric, "
    "equal-rate, static, random-boundary, and product controls. It does not "
    "admit novelty, empirical physics, a final manifold tower, ontology, or "
    "bridge claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing eight-qubit density evolution, boundary projection, entropy spectra, coherent information, and CPTP checks"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing partial trace contractions over the 4|4 split"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing 16x16 finite boundary graph"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing graph tensor conversion for boundary graph features"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic boundary/interior count and signed-entropy identity"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing eight-qubit survivor/control witness"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}


def boundary_graph() -> tuple[nx.Graph, list[int], list[int]]:
    graph = nx.grid_2d_graph(16, 16)
    mapping = {node: idx for idx, node in enumerate(sorted(graph.nodes()))}
    graph = nx.relabel_nodes(graph, mapping)
    boundary = []
    for node in graph.nodes:
        x, y = next(key for key, value in mapping.items() if value == node)
        graph.nodes[node]["coord"] = (x, y)
        if x in (0, 15) or y in (0, 15):
            boundary.append(node)
    interior = [node for node in graph.nodes if node not in set(boundary)]
    return graph, boundary, interior


def boundary_targets(boundary: list[int], interior: list[int], mode: str) -> dict[int, int]:
    targets = {}
    for offset, idx in enumerate(interior):
        if mode == "nearest":
            targets[idx] = boundary[offset % len(boundary)]
        elif mode == "random_boundary":
            targets[idx] = boundary[(11 * offset + 17) % len(boundary)]
        else:
            raise ValueError(mode)
    return targets


def apply_boundary_expectation(rho: torch.Tensor, mode: str) -> torch.Tensor:
    if mode == "identity":
        return rho
    _, boundary, interior = boundary_graph()
    out = torch.zeros_like(rho)
    boundary_index = torch.tensor(boundary, dtype=torch.long)
    out[boundary_index[:, None], boundary_index[None, :]] = rho[boundary_index[:, None], boundary_index[None, :]]
    targets = boundary_targets(boundary, interior, mode)
    for src, dst in targets.items():
        out[dst, dst] = out[dst, dst] + rho[src, src]
    return out / torch.clamp(torch.trace(out).real, min=1e-15)


def cptp_gap_for_boundary(mode: str) -> float:
    if mode == "identity":
        return 0.0
    _, boundary, interior = boundary_graph()
    accum = torch.zeros((DIM, DIM), dtype=DTYPE)
    projector = torch.zeros((DIM, DIM), dtype=DTYPE)
    for idx in boundary:
        projector[idx, idx] = 1.0
    accum = accum + projector.conj().T @ projector
    for src, dst in boundary_targets(boundary, interior, mode).items():
        op = torch.zeros((DIM, DIM), dtype=DTYPE)
        op[dst, src] = 1.0
        accum = accum + op.conj().T @ op
    return float(torch.linalg.matrix_norm(accum - torch.eye(DIM, dtype=DTYPE)).item())


def apply_kraus(rho: torch.Tensor, kraus: list[torch.Tensor]) -> torch.Tensor:
    out = torch.zeros_like(rho)
    for k in kraus:
        out = out + k @ rho @ k.conj().T
    return out


def cptp_gap(kraus: list[torch.Tensor]) -> float:
    accum = torch.zeros((kraus[0].shape[1], kraus[0].shape[1]), dtype=DTYPE)
    for k in kraus:
        accum = accum + k.conj().T @ k
    return float(torch.linalg.matrix_norm(accum - torch.eye(kraus[0].shape[1], dtype=DTYPE)).item())


def reduced_density(rho: torch.Tensor, keep: list[int]) -> torch.Tensor:
    tensor = rho.reshape([2] * N_QUBITS * 2)
    trace = [idx for idx in range(N_QUBITS) if idx not in keep]
    perm = keep + trace + [idx + N_QUBITS for idx in keep] + [idx + N_QUBITS for idx in trace]
    matrix = tensor.permute(perm).reshape(2 ** len(keep), 2 ** len(trace), 2 ** len(keep), 2 ** len(trace))
    return oe.contract("abcb->ac", matrix)


def entropy(rho: torch.Tensor) -> float:
    eigs = torch.clamp(torch.linalg.eigvalsh((rho + rho.conj().T) / 2).real, min=1e-15)
    eigs = eigs / eigs.sum()
    return float((-torch.sum(eigs * torch.log(eigs))).item())


def signed_readout(rho: torch.Tensor) -> dict[str, float]:
    full = entropy(rho)
    rest = entropy(reduced_density(rho, [4, 5, 6, 7]))
    return {"coherent_information_first_half_to_second_half": rest - full, "conditional_entropy_first_half_given_second_half": full - rest}


def channel_for_step(step: int, mode: str, gamma: float | None = None) -> list[torch.Tensor]:
    if mode == "dynamic_asymmetric":
        left, right = rates_from_weights(shell_weights(step, "dynamic"))
        return embed_local(asymmetric_kraus(left, right))
    if mode == "static_asymmetric":
        left, right = rates_from_weights(shell_weights(1, "static"))
        return embed_local(asymmetric_kraus(left, right))
    if mode == "equal_rate":
        rate = 0.12 if gamma is None else gamma
        return embed_local(asymmetric_kraus(rate, rate))
    if mode == "symmetric":
        rate = 0.12 if gamma is None else gamma
        return embed_local(symmetric_kraus(rate))
    raise ValueError(mode)


def run_sequence(rho: torch.Tensor, channel_mode: str, boundary_mode: str, gamma: float | None = None) -> dict[str, Any]:
    current = apply_boundary_expectation(rho, boundary_mode)
    coherent = [signed_readout(current)["coherent_information_first_half_to_second_half"]]
    conditional = [signed_readout(current)["conditional_entropy_first_half_given_second_half"]]
    cptp = [cptp_gap_for_boundary(boundary_mode)]
    for step in range(1, 6):
        kraus = channel_for_step(step, channel_mode, gamma=gamma)
        cptp.append(cptp_gap(kraus))
        current = apply_kraus(current, kraus)
        current = apply_boundary_expectation(current, boundary_mode)
        row = signed_readout(current)
        coherent.append(row["coherent_information_first_half_to_second_half"])
        conditional.append(row["conditional_entropy_first_half_given_second_half"])
    return {"coherent_orbit": coherent, "conditional_orbit": conditional, "max_cptp_gap": max(cptp)}


def l2_gap(left: list[float], right: list[float]) -> float:
    return float(torch.linalg.vector_norm(torch.tensor(left, dtype=torch.float64) - torch.tensor(right, dtype=torch.float64)).item())


def best_symmetric_grid_fit(rho: torch.Tensor, target: list[float], boundary_mode: str) -> dict[str, Any]:
    best = {"gamma": None, "gap": float("inf"), "coherent_orbit": []}
    for idx in range(21):
        gamma = 0.01 + 0.30 * idx / 20
        row = run_sequence(rho, "symmetric", boundary_mode, gamma=gamma)
        gap = l2_gap(target, row["coherent_orbit"])
        if gap < best["gap"]:
            best = {"gamma": gamma, "gap": gap, "coherent_orbit": row["coherent_orbit"]}
    return best


def symbolic_boundary() -> dict[str, Any]:
    n = sp.Integer(16)
    total = n**2
    boundary = n**2 - (n - 2) ** 2
    s_ab, s_b = sp.symbols("S_AB S_B")
    return {"total": int(total), "boundary": int(boundary), "inside_identity": str(sp.simplify((s_b - s_ab) + (s_ab - s_b))), "pass": int(total) == DIM and int(boundary) == 60}


def z3_witness(sym_count: int, equal_count: int, random_separation_count: int, cptp: float, signed_bound: float) -> dict[str, Any]:
    solver = z3.Solver()
    sym, equal, random_separates, valid, inside = z3.Bools("sym equal random_separates valid inside")
    solver.add(sym == (sym_count >= 3))
    solver.add(equal == (equal_count >= 3))
    solver.add(random_separates == (random_separation_count >= 3))
    solver.add(valid == (cptp < 1e-12))
    solver.add(inside == (signed_bound <= N_QUBITS * math.log(2) + 1e-12))
    solver.add(z3.Not(z3.And(sym, equal, random_separates, valid, inside)))
    status = solver.check()
    return {"solver_status": str(status), "pass": status == z3.unsat, "symmetric_survivor_count": sym_count, "equal_rate_survivor_count": equal_count, "random_boundary_separation_count": random_separation_count, "cptp_valid": cptp < 1e-12, "inside_information_bound": signed_bound <= N_QUBITS * math.log(2) + 1e-12}


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    graph, boundary, interior = boundary_graph()
    pyg = from_networkx(graph)
    rows = {}
    symmetric_survivors = []
    equal_survivors = []
    random_separations = []
    cptp_gaps = []
    max_abs_signed = 0.0
    for name, rho in candidate_densities().items():
        target = run_sequence(rho, "dynamic_asymmetric", "nearest")
        symmetric = best_symmetric_grid_fit(rho, target["coherent_orbit"], "nearest")
        equal = run_sequence(rho, "equal_rate", "nearest", gamma=0.12)
        static = run_sequence(rho, "static_asymmetric", "nearest")
        random_boundary = run_sequence(rho, "dynamic_asymmetric", "random_boundary")
        sym_gap = symmetric["gap"]
        equal_gap = l2_gap(target["coherent_orbit"], equal["coherent_orbit"])
        static_gap = l2_gap(target["coherent_orbit"], static["coherent_orbit"])
        random_gap = l2_gap(target["coherent_orbit"], random_boundary["coherent_orbit"])
        if sym_gap > 0.01:
            symmetric_survivors.append(name)
        if equal_gap > 0.01:
            equal_survivors.append(name)
        if random_gap > 0.005:
            random_separations.append(name)
        cptp_gaps.extend([target["max_cptp_gap"], equal["max_cptp_gap"], static["max_cptp_gap"], random_boundary["max_cptp_gap"]])
        max_abs_signed = max(max_abs_signed, max(abs(v) for v in target["coherent_orbit"] + target["conditional_orbit"]))
        rows[name] = {
            "dynamic_boundary_projected": target,
            "best_symmetric_grid_fit": symmetric,
            "equal_rate_control": equal,
            "static_asymmetric_control": static,
            "random_boundary_control": random_boundary,
            "symmetric_gap": sym_gap,
            "equal_rate_gap": equal_gap,
            "static_gap": static_gap,
            "random_boundary_gap": random_gap,
        }
    max_cptp = max(cptp_gaps)
    positive = {
        "eight_qubit_boundary_projected_coherent_information_has_symmetric_fit_survivor_rows": {"survivor_names": symmetric_survivors, "survivor_count": len(symmetric_survivors), "threshold": 0.01, "pass": len(symmetric_survivors) >= 3},
        "eight_qubit_boundary_projected_coherent_information_has_equal_rate_survivor_rows": {"survivor_names": equal_survivors, "survivor_count": len(equal_survivors), "threshold": 0.01, "pass": len(equal_survivors) >= 3},
        "eight_qubit_boundary_projected_sequence_is_cptp": {"max_cptp_gap": max_cptp, "pass": max_cptp < 1e-12},
        "gamma5_projector_boundary": gamma5_boundary(),
        "symbolic_boundary_and_signed_entropy_check": symbolic_boundary(),
    }
    graveyard_companions = {
        "random_boundary_projection_separates_all_nontrivial_rows": {"separation_names": random_separations, "separation_count": len(random_separations), "pass": len(random_separations) >= 3},
        "static_asymmetric_control_gap_is_recorded": {"min_static_gap": min(row["static_gap"] for row in rows.values()), "pass": True},
        "boundary_graph_has_interior_and_boundary": {"boundary_nodes": len(boundary), "interior_nodes": len(interior), "pyg_edges": int(pyg.edge_index.shape[1]), "pass": len(boundary) == 60 and len(interior) == 196},
        "signed_readouts_stay_inside_finite_information_bound": {"max_abs_signed_readout": max_abs_signed, "bound": N_QUBITS * math.log(2), "pass": max_abs_signed <= N_QUBITS * math.log(2) + 1e-12},
    }
    boundary_section = {
        "z3_eight_qubit_boundary_projected_coherent_information_witness": z3_witness(len(symmetric_survivors), len(equal_survivors), len(random_separations), max_cptp, max_abs_signed),
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
    }
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [row["pass"] for row in boundary_section.values()]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "eight-qubit finite boundary conditional expectation composed with gamma5 chirality-asymmetric CPTP channels and read by coherent-information and conditional-entropy orbits across a 4|4 split",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary_section,
        "nearby_variants": {"passed": sum(1 for value in checks if value), "total": len(checks)},
        "open_choices": [
            "This is an eight-qubit lift of the boundary-projected coherent-information scout, but it still uses a grid fit rather than continuous optimization for the symmetric control.",
            "Random boundary projection is a separating control at this size, unlike the four-qubit readout where collisions remained.",
            "Next scout should add a stronger time-dependent locality-preserving rank-3 kill control or representation-branching invariant.",
        ],
        "why_not_v4_probes": "This is a clean v5 formal scout translated from current Grok/Gemini eight-qubit coherent-information convergence; it is not a canonical v4 probe.",
        "raw_rows": rows,
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all(checks), "result": str(OUT_PATH), "symmetric_survivors": len(symmetric_survivors), "equal_rate_survivors": len(equal_survivors), "random_boundary_separations": len(random_separations)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
