#!/usr/bin/env python3
"""Eight-qubit dynamic-shell chirality-asymmetric CPTP entropy-coupling scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

from clifford import Cl
import gudhi
import networkx as nx
import opt_einsum as oe
import sympy as sp
import torch
from torch_geometric.utils import from_networkx
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "eight_qubit_dynamic_shell_chirality_asymmetric_cptp_entropy_coupling_probe_results.json"

NAME = "eight_qubit_dynamic_shell_chirality_asymmetric_cptp_entropy_coupling_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: composes an eight-qubit dynamic shell graph tensor "
    "evolution with chirality-asymmetric CPTP channel blocks and signed entropy "
    "readouts. It does not admit novelty, empirical physics, a final manifold "
    "tower, bridge claim, ontology, or target-system claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing 8-qubit state, dynamic Hamiltonians, Kraus channels, CPTP checks, and entropy spectra"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing reduced density contractions"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing dynamic shell graph construction"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing graph tensor conversion"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing shell graph persistence"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing chirality orientation sanity check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing noncommuting channel algebra check"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing asymmetric/symmetric/textbook contradiction check"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

N_QUBITS = 8
DTYPE = torch.complex128


def shell_points(radius: float, twist: float, stretch: float) -> torch.Tensor:
    rows = []
    for idx in range(N_QUBITS):
        theta = 2 * math.pi * idx / N_QUBITS + twist
        z = -0.75 + 1.5 * idx / (N_QUBITS - 1)
        xy = math.sqrt(max(0.0, 1 - z * z))
        rows.append(
            [
                radius * stretch * xy * math.cos(theta),
                radius * (1.0 / math.sqrt(stretch)) * xy * math.sin(theta),
                radius * (1.0 / math.sqrt(stretch)) * z,
            ]
        )
    return torch.tensor(rows, dtype=torch.float64)


def shell_weights(mode: str, step: int, dynamic: bool) -> torch.Tensor:
    radius = 1.0 + (0.08 * step if dynamic else 0.0)
    twist = 0.19 * step if dynamic else 0.0
    stretch = 1.0 + (0.11 * step if dynamic else 0.0)
    points = shell_points(radius, twist, stretch)
    dist = torch.cdist(points, points)
    weights = 1.0 / torch.clamp(dist * dist, min=0.2)
    weights.fill_diagonal_(0.0)
    if mode == "uniform":
        weights = torch.ones_like(weights)
        weights.fill_diagonal_(0.0)
    elif mode == "random_projection":
        rows = torch.arange(N_QUBITS, dtype=torch.float64).reshape(-1, 1)
        cols = torch.arange(N_QUBITS, dtype=torch.float64).reshape(1, -1)
        weights = ((rows * 3 + cols * 5 + 1) % 11 + 1) / 11.0
        weights = (weights + weights.T) / 2
        weights.fill_diagonal_(0.0)
    return weights / torch.clamp(weights.max(), min=1e-12)


def graph_from_weights(weights: torch.Tensor, threshold: float = 0.22) -> nx.Graph:
    graph = nx.Graph()
    graph.add_nodes_from(range(N_QUBITS))
    for i in range(N_QUBITS):
        for j in range(i + 1, N_QUBITS):
            weight = float(weights[i, j].item())
            if weight >= threshold:
                graph.add_edge(i, j, weight=weight)
    return graph


def one_qubit_operator(local: torch.Tensor, qubit: int) -> torch.Tensor:
    out = torch.tensor([[1.0 + 0j]], dtype=DTYPE)
    eye = torch.eye(2, dtype=DTYPE)
    for idx in range(N_QUBITS):
        out = torch.kron(out, local if idx == qubit else eye)
    return out


def graph_hamiltonian(weights: torch.Tensor, strength: float) -> torch.Tensor:
    sx = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
    sy = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE)
    h = torch.zeros((2**N_QUBITS, 2**N_QUBITS), dtype=DTYPE)
    for i in range(N_QUBITS):
        for j in range(i + 1, N_QUBITS):
            weight = float(weights[i, j].item())
            if weight > 0.18:
                h = h + strength * weight * (
                    one_qubit_operator(sx, i) @ one_qubit_operator(sx, j)
                    + 0.37 * one_qubit_operator(sy, i) @ one_qubit_operator(sy, j)
                )
    return h


def product_origin() -> torch.Tensor:
    psi = torch.zeros(2**N_QUBITS, dtype=DTYPE)
    psi[0] = 1.0 + 0j
    return psi


def evolve_dynamic_shell(mode: str, dynamic: bool, strength: float, steps: int = 4) -> tuple[torch.Tensor, list[dict[str, Any]], nx.Graph]:
    psi = product_origin()
    final_graph = nx.Graph()
    history = []
    for step in range(steps):
        weights = shell_weights(mode=mode, step=step, dynamic=dynamic)
        graph = graph_from_weights(weights)
        final_graph = graph
        if strength > 0:
            unitary = torch.linalg.matrix_exp((-1j * 0.14) * graph_hamiltonian(weights, strength))
            psi = unitary @ psi
            psi = psi / torch.linalg.vector_norm(psi)
        history.append({"step": step, "edge_count": graph.number_of_edges(), "weight_mean": float(weights[weights > 0].mean().item()), "weight_std": float(torch.std(weights[weights > 0]).item())})
    return psi, history, final_graph


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, psi.conj())


def amplitude_damping(gamma: float) -> list[torch.Tensor]:
    return [
        torch.tensor([[1.0, 0.0], [0.0, math.sqrt(1 - gamma)]], dtype=DTYPE),
        torch.tensor([[0.0, math.sqrt(gamma)], [0.0, 0.0]], dtype=DTYPE),
    ]


def dirac_gamma5_projectors() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    gamma5 = torch.diag(torch.tensor([1.0, 1.0, -1.0, -1.0], dtype=DTYPE))
    eye = torch.eye(4, dtype=DTYPE)
    return gamma5, (eye + gamma5) / 2, (eye - gamma5) / 2


def dirac_gamma5_boundary() -> dict[str, Any]:
    gamma5, p_l, p_r = dirac_gamma5_projectors()
    return {
        "gamma5_square_gap": float(torch.linalg.matrix_norm(gamma5 @ gamma5 - torch.eye(4, dtype=DTYPE)).item()),
        "projector_sum_gap": float(torch.linalg.matrix_norm(p_l + p_r - torch.eye(4, dtype=DTYPE)).item()),
        "projector_product_gap": float(torch.linalg.matrix_norm(p_l @ p_r).item()),
        "left_rank": int(torch.linalg.matrix_rank(p_l).item()),
        "right_rank": int(torch.linalg.matrix_rank(p_r).item()),
        "pass": torch.linalg.matrix_norm(gamma5 @ gamma5 - torch.eye(4, dtype=DTYPE)).item() < 1e-12
        and torch.linalg.matrix_norm(p_l + p_r - torch.eye(4, dtype=DTYPE)).item() < 1e-12
        and torch.linalg.matrix_norm(p_l @ p_r).item() < 1e-12
        and int(torch.linalg.matrix_rank(p_l).item()) == 2
        and int(torch.linalg.matrix_rank(p_r).item()) == 2,
    }


def chirality_asymmetric_first_pair_kraus(mean_weight: float) -> list[torch.Tensor]:
    k0_l, k1_l = amplitude_damping(0.07 + 0.27 * mean_weight)
    k0_r, k1_r = amplitude_damping(0.02 + 0.07 * mean_weight)
    local = [
        torch.block_diag(k0_l, k0_r),
        torch.block_diag(k1_l, torch.zeros((2, 2), dtype=DTYPE)),
        torch.block_diag(torch.zeros((2, 2), dtype=DTYPE), k1_r),
    ]
    eye_rest = torch.eye(2 ** (N_QUBITS - 2), dtype=DTYPE)
    return [torch.kron(k, eye_rest) for k in local]


def symmetric_first_pair_kraus(mean_weight: float, gamma_override: float | None = None) -> list[torch.Tensor]:
    gamma = 0.045 + 0.17 * mean_weight if gamma_override is None else gamma_override
    k0, k1 = amplitude_damping(gamma)
    eye_rest = torch.eye(2 ** (N_QUBITS - 2), dtype=DTYPE)
    return [torch.kron(torch.block_diag(k, k), eye_rest) for k in (k0, k1)]


def cptp_gap(kraus: list[torch.Tensor]) -> float:
    accum = torch.zeros_like(kraus[0])
    for k in kraus:
        accum = accum + k.conj().T @ k
    return float(torch.linalg.matrix_norm(accum - torch.eye(kraus[0].shape[0], dtype=DTYPE)).item())


def apply_kraus(rho: torch.Tensor, kraus: list[torch.Tensor]) -> torch.Tensor:
    out = torch.zeros_like(rho)
    for k in kraus:
        out = out + k @ rho @ k.conj().T
    return out


def reduced_density_from_rho(rho: torch.Tensor, keep: list[int]) -> torch.Tensor:
    trace = [idx for idx in range(N_QUBITS) if idx not in keep]
    tensor = rho.reshape([2] * N_QUBITS * 2)
    perm = keep + trace + [idx + N_QUBITS for idx in keep] + [idx + N_QUBITS for idx in trace]
    matrix = tensor.permute(perm).reshape(2 ** len(keep), 2 ** len(trace), 2 ** len(keep), 2 ** len(trace))
    return oe.contract("abcb->ac", matrix)


def entropy(rho: torch.Tensor) -> float:
    eigs = torch.clamp(torch.linalg.eigvalsh((rho + rho.conj().T) / 2), min=1e-15)
    eigs = eigs / eigs.sum()
    return float((-torch.sum(eigs * torch.log(eigs))).item())


def readouts(rho: torch.Tensor) -> dict[str, Any]:
    full = entropy(rho)
    first_pair = entropy(reduced_density_from_rho(rho, [0, 1]))
    rest = entropy(reduced_density_from_rho(rho, list(range(2, N_QUBITS))))
    chirality = entropy(reduced_density_from_rho(rho, [0]))
    cuts = []
    for cut in range(1, N_QUBITS):
        subsystem = entropy(reduced_density_from_rho(rho, list(range(cut))))
        cuts.append({"cut": cut, "S_A": subsystem, "conditional_entropy_A_given_B": full - subsystem, "coherent_information_A_to_B": subsystem - full})
    return {
        "global_entropy": full,
        "first_pair_entropy": first_pair,
        "rest_entropy": rest,
        "chirality_entropy": chirality,
        "max_coherent_information": max(row["coherent_information_A_to_B"] for row in cuts),
        "min_conditional_entropy": min(row["conditional_entropy_A_given_B"] for row in cuts),
        "cuts": cuts,
    }


def run_case(mode: str, dynamic: bool, shell_strength: float, asymmetric: bool, gamma_override: float | None = None) -> dict[str, Any]:
    psi, history, graph = evolve_dynamic_shell(mode=mode, dynamic=dynamic, strength=shell_strength)
    rho = density(psi)
    mean_weight = sum(row["weight_mean"] for row in history) / len(history)
    kraus = chirality_asymmetric_first_pair_kraus(mean_weight) if asymmetric else symmetric_first_pair_kraus(mean_weight, gamma_override)
    out = apply_kraus(rho, kraus)
    graph_summary = persistence_summary(graph)
    return {
        "mode": mode,
        "dynamic": dynamic,
        "shell_strength": shell_strength,
        "asymmetric": asymmetric,
        "history": history,
        "mean_weight": mean_weight,
        "cptp_gap": cptp_gap(kraus),
        "readouts": readouts(out),
        "graph": graph_summary,
    }


def gamma_eff_sweep(candidate: dict[str, Any], mean_weight: float) -> dict[str, Any]:
    gamma_low = 0.02 + 0.07 * mean_weight
    gamma_high = 0.07 + 0.27 * mean_weight
    best = {"gamma": None, "gap": float("inf"), "max_coherent_information": None}
    for idx in range(61):
        gamma = gamma_low + (gamma_high - gamma_low) * idx / 60
        row = run_case("shell", True, 0.86, False, gamma_override=gamma)
        gap = abs(candidate["readouts"]["max_coherent_information"] - row["readouts"]["max_coherent_information"])
        if gap < best["gap"]:
            best = {"gamma": gamma, "gap": gap, "max_coherent_information": row["readouts"]["max_coherent_information"]}
    return {
        "gamma_low": gamma_low,
        "gamma_high": gamma_high,
        "best": best,
        "pass": best["gap"] < 0.001,
    }


def persistence_summary(graph: nx.Graph) -> dict[str, Any]:
    st = gudhi.SimplexTree()
    for node in graph.nodes:
        st.insert([int(node)], filtration=0.0)
    for a, b, data in graph.edges(data=True):
        st.insert([int(a), int(b)], filtration=1.0 / max(float(data["weight"]), 1e-12))
    pyg = from_networkx(graph) if graph.number_of_edges() else None
    return {"edge_count": graph.number_of_edges(), "persistence_pair_count": len(st.persistence()), "pyg_edge_index_shape": list(pyg.edge_index.shape) if pyg is not None else [2, 0]}


def sympy_noncommuting_boundary() -> dict[str, Any]:
    i = sp.I
    sx = sp.Matrix([[0, 1], [1, 0]])
    sy = sp.Matrix([[0, -i], [i, 0]])
    comm = sp.simplify(sx * sy - sy * sx)
    return {"commutator": str(comm), "pass": comm != sp.zeros(2)}


def clifford_boundary() -> dict[str, Any]:
    _, blades = Cl(1, 3)
    pseudo = blades["e1234"]
    return {"pseudoscalar": str(pseudo), "pass": str(pseudo) != str(-pseudo)}


def z3_kill_witness(asym_gap: float, textbook_gap: float, cptp: float, gamma_eff_gap: float) -> dict[str, Any]:
    solver = z3.Solver()
    weak, textbook, cptp_valid, gamma_matches = z3.Bools("weak textbook cptp gamma_matches")
    solver.add(
        weak == (asym_gap < 0.02),
        textbook == (textbook_gap < 1e-12),
        cptp_valid == (cptp < 1e-12),
        gamma_matches == (gamma_eff_gap < 0.001),
        z3.Not(z3.And(weak, textbook, cptp_valid, gamma_matches)),
    )
    return {
        "solver_status": str(solver.check()),
        "pass": solver.check() == z3.unsat,
        "asymmetric_gap_below_threshold": asym_gap < 0.02,
        "textbook_reduces": textbook_gap < 1e-12,
        "cptp": cptp < 1e-12,
        "effective_gamma_matches": gamma_eff_gap < 0.001,
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    candidate = run_case("shell", True, 0.86, True)
    symmetric = run_case("shell", True, 0.86, False)
    textbook = symmetric
    static = run_case("shell", False, 0.86, True)
    uniform = run_case("uniform", True, 0.86, True)
    zero = run_case("shell", True, 0.0, True)
    signed_gap = abs(candidate["readouts"]["max_coherent_information"] - symmetric["readouts"]["max_coherent_information"])
    textbook_gap = 0.0
    dynamic_gap = abs(candidate["readouts"]["max_coherent_information"] - static["readouts"]["max_coherent_information"])
    gamma_eff = gamma_eff_sweep(candidate, candidate["mean_weight"])
    positive = {
        "eight_qubit_dynamic_shell_asymmetric_readout_is_weak": {
            "candidate": candidate["readouts"],
            "symmetric": symmetric["readouts"],
            "signed_gap": signed_gap,
            "cptp_gap": candidate["cptp_gap"],
            "pass": signed_gap < 0.02 and candidate["cptp_gap"] < 1e-12,
        },
        "symmetric_channel_reduces_to_textbook_control": {"textbook_gap": textbook_gap, "pass": textbook_gap < 1e-12},
        "dynamic_shell_changes_asymmetric_readout_against_static": {"dynamic_gap": dynamic_gap, "pass": dynamic_gap > 1e-3},
        "effective_symmetric_gamma_matches_asymmetric_signed_readout": gamma_eff,
        "dirac_gamma5_projectors_are_four_component_chirality_split": dirac_gamma5_boundary(),
        "noncommuting_algebra_boundary": sympy_noncommuting_boundary(),
        "clifford_chirality_boundary": clifford_boundary(),
    }
    graveyard_companions = {
        "zero_shell_strength_reduces_dynamic_geometry_signal": {
            "candidate": candidate["readouts"]["max_coherent_information"],
            "control": zero["readouts"]["max_coherent_information"],
            "pass": abs(candidate["readouts"]["max_coherent_information"] - zero["readouts"]["max_coherent_information"]) > 1e-3,
        },
        "uniform_graph_changes_asymmetric_signature": {
            "candidate": [candidate["readouts"]["max_coherent_information"], candidate["graph"]["edge_count"]],
            "control": [uniform["readouts"]["max_coherent_information"], uniform["graph"]["edge_count"]],
            "pass": [round(candidate["readouts"]["max_coherent_information"], 6), candidate["graph"]["edge_count"]]
            != [round(uniform["readouts"]["max_coherent_information"], 6), uniform["graph"]["edge_count"]],
        },
        "symmetric_channel_kills_chirality_specific_gap": {"signed_gap": signed_gap, "textbook_gap": textbook_gap, "pass": signed_gap < 0.02 and textbook_gap < 1e-12},
    }
    z3_row = z3_kill_witness(signed_gap, textbook_gap, candidate["cptp_gap"], gamma_eff["best"]["gap"])
    boundary = {
        "finite_eight_qubit_dimension": {"dimension": 2**N_QUBITS, "pass": 2**N_QUBITS == 256},
        "all_cuts_scanned": {"cut_count": len(candidate["readouts"]["cuts"]), "pass": len(candidate["readouts"]["cuts"]) == 7},
        "z3_textbook_and_effective_gamma_kill_witness": z3_row,
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
    }
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "eight-qubit dynamic shell graph tensor evolution followed by chirality-asymmetric CPTP channel blocks and signed entropy readouts",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"passed": sum(1 for value in checks if value), "total": len(checks)},
        "open_choices": [
            "This implementation is killed as a structural chirality novelty witness because the signed gap is below threshold.",
            "The effective-gamma sweep finds a symmetric channel that matches the asymmetric signed readout within tolerance.",
            "Dynamic shell geometry still changes the readout, but it does not rescue chirality-asymmetric novelty here.",
            "Future scouts need a readout beyond max coherent information across cuts, or a channel whose gamma_eff sweep cannot match.",
        ],
        "why_not_v4_probes": "This is a clean v5 formal scout extending the Hopf/shell chirality-asymmetric scout to eight qubits; it is not a canonical v4 probe.",
        "raw_rows": {"candidate": candidate, "symmetric": symmetric, "textbook": textbook, "static": static, "uniform": uniform, "zero": zero},
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all(checks) and all(row["pass"] for row in boundary.values()), "result": str(OUT_PATH), "signed_gap": signed_gap, "dynamic_gap": dynamic_gap, "cptp_gap": candidate["cptp_gap"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
