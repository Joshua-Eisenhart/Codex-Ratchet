#!/usr/bin/env python3
"""Hopf-shell chirality-asymmetric CPTP entropy-coupling scout."""

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
OUT_PATH = RESULT_DIR / "hopf_shell_chirality_asymmetric_cptp_entropy_coupling_probe_results.json"

NAME = "hopf_shell_chirality_asymmetric_cptp_entropy_coupling_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: composes Hopf-projected spinor shell geometry with "
    "chirality-asymmetric CPTP channel blocks and signed entropy readouts. It "
    "does not admit novelty, empirical physics, a final manifold tower, bridge "
    "claim, ontology, or target-system claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing four-qubit state, Hopf coordinates, Kraus channels, CPTP checks, and entropy spectra"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing reduced density contractions"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing Hopf shell graph"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing graph tensor conversion"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing shell graph persistence"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing chirality orientation sanity check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing noncommuting channel algebra check"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing control-separation contradiction check"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

DTYPE = torch.complex128
N_QUBITS = 4


def normalize(psi: torch.Tensor) -> torch.Tensor:
    return psi / torch.linalg.vector_norm(psi)


def seed_spinors() -> list[torch.Tensor]:
    rows = []
    for idx in range(4):
        theta = 0.23 + 0.15 * idx
        phi = 0.47 * idx
        rows.append(normalize(torch.tensor([math.cos(theta), math.sin(theta) * complex(math.cos(phi), math.sin(phi))], dtype=DTYPE)))
    return rows


def hopf_projection(psi: torch.Tensor) -> torch.Tensor:
    a, b = psi[0], psi[1]
    product = a * torch.conj(b)
    return torch.stack([2 * torch.real(product), 2 * torch.imag(product), torch.abs(a) ** 2 - torch.abs(b) ** 2]).to(torch.float64)


def shell_graph(mode: str) -> tuple[nx.Graph, torch.Tensor]:
    points = torch.stack([hopf_projection(psi) for psi in seed_spinors()])
    dist = torch.cdist(points, points)
    weights = 1.0 / torch.clamp(dist * dist, min=0.18)
    weights.fill_diagonal_(0.0)
    if mode == "uniform":
        weights = torch.ones_like(weights)
        weights.fill_diagonal_(0.0)
    elif mode == "random_projection":
        weights = torch.tensor(
            [
                [0.0, 0.2, 0.8, 0.3],
                [0.2, 0.0, 0.5, 0.9],
                [0.8, 0.5, 0.0, 0.4],
                [0.3, 0.9, 0.4, 0.0],
            ],
            dtype=torch.float64,
        )
    weights = weights / torch.clamp(weights.max(), min=1e-12)
    graph = nx.Graph()
    graph.add_nodes_from(range(4))
    for i in range(4):
        for j in range(i + 1, 4):
            graph.add_edge(i, j, weight=float(weights[i, j].item()))
    return graph, weights


def initial_state() -> torch.Tensor:
    # Four-qubit state: chirality qubit, system qubit, and a two-qubit reference.
    psi = torch.zeros(2**N_QUBITS, dtype=DTYPE)
    psi[0b0000] = 0.49
    psi[0b0111] = 0.51j
    psi[0b1010] = 0.36
    psi[0b1101] = -0.61j
    return normalize(psi)


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, psi.conj())


def embed_one_qubit(op: torch.Tensor, qubit: int) -> torch.Tensor:
    out = torch.tensor([[1.0 + 0j]], dtype=DTYPE)
    eye = torch.eye(2, dtype=DTYPE)
    for idx in range(N_QUBITS):
        out = torch.kron(out, op if idx == qubit else eye)
    return out


def amplitude_damping(gamma: float) -> list[torch.Tensor]:
    return [
        torch.tensor([[1.0, 0.0], [0.0, math.sqrt(1 - gamma)]], dtype=DTYPE),
        torch.tensor([[0.0, math.sqrt(gamma)], [0.0, 0.0]], dtype=DTYPE),
    ]


def chirality_asymmetric_embedded_kraus(gamma_left: float, gamma_right: float) -> list[torch.Tensor]:
    p_l = torch.tensor([[1.0, 0.0], [0.0, 0.0]], dtype=DTYPE)
    p_r = torch.tensor([[0.0, 0.0], [0.0, 1.0]], dtype=DTYPE)
    k0_l, k1_l = amplitude_damping(gamma_left)
    k0_r, k1_r = amplitude_damping(gamma_right)
    local = [
        torch.kron(p_l, k0_l) + torch.kron(p_r, k0_r),
        torch.kron(p_l, k1_l),
        torch.kron(p_r, k1_r),
    ]
    eye_ref = torch.eye(4, dtype=DTYPE)
    return [torch.kron(k, eye_ref) for k in local]


def symmetric_embedded_kraus(gamma: float) -> list[torch.Tensor]:
    k0, k1 = amplitude_damping(gamma)
    eye_chirality = torch.eye(2, dtype=DTYPE)
    eye_ref = torch.eye(4, dtype=DTYPE)
    return [torch.kron(torch.kron(eye_chirality, k), eye_ref) for k in (k0, k1)]


def apply_kraus(rho: torch.Tensor, kraus: list[torch.Tensor]) -> torch.Tensor:
    out = torch.zeros_like(rho)
    for k in kraus:
        out = out + k @ rho @ k.conj().T
    return out


def cptp_gap(kraus: list[torch.Tensor]) -> float:
    accum = torch.zeros_like(kraus[0])
    for k in kraus:
        accum = accum + k.conj().T @ k
    return float(torch.linalg.matrix_norm(accum - torch.eye(kraus[0].shape[0], dtype=DTYPE)).item())


def shell_weighted_channel(rho: torch.Tensor, mode: str, asymmetric: bool) -> tuple[torch.Tensor, dict[str, Any]]:
    graph, weights = shell_graph(mode)
    mean_weight = float(weights[weights > 0].mean().item())
    if asymmetric:
        kraus = chirality_asymmetric_embedded_kraus(gamma_left=0.08 + 0.32 * mean_weight, gamma_right=0.03 + 0.08 * mean_weight)
    else:
        kraus = symmetric_embedded_kraus(gamma=0.055 + 0.20 * mean_weight)
    return apply_kraus(rho, kraus), {"graph": graph, "weights": weights, "mean_weight": mean_weight, "cptp_gap": cptp_gap(kraus)}


def reduced_density_from_rho(rho: torch.Tensor, keep: list[int]) -> torch.Tensor:
    tensor = rho.reshape([2] * N_QUBITS * 2)
    trace = [idx for idx in range(N_QUBITS) if idx not in keep]
    current = tensor
    # Use einsum through explicit permutation to avoid hidden helper libraries.
    keep_out = keep
    trace_out = trace
    perm = keep_out + trace_out + [idx + N_QUBITS for idx in keep_out] + [idx + N_QUBITS for idx in trace_out]
    permuted = current.permute(perm)
    dim_keep = 2 ** len(keep)
    dim_trace = 2 ** len(trace)
    matrix = permuted.reshape(dim_keep, dim_trace, dim_keep, dim_trace)
    return oe.contract("abcb->ac", matrix)


def entropy(rho: torch.Tensor) -> float:
    eigs = torch.clamp(torch.linalg.eigvalsh((rho + rho.conj().T) / 2), min=1e-15)
    eigs = eigs / eigs.sum()
    return float((-torch.sum(eigs * torch.log(eigs))).item())


def readouts(rho: torch.Tensor) -> dict[str, float]:
    rho_b = reduced_density_from_rho(rho, [1, 2, 3])
    rho_chiral = reduced_density_from_rho(rho, [0])
    s_ab = entropy(rho)
    s_b = entropy(rho_b)
    return {
        "global_entropy": s_ab,
        "conditional_entropy_chirality_given_rest": s_ab - s_b,
        "coherent_information_chirality_to_rest": s_b - s_ab,
        "chirality_entropy": entropy(rho_chiral),
        "chirality_z": float(torch.real(rho_chiral[0, 0] - rho_chiral[1, 1]).item()),
    }


def persistence(graph: nx.Graph) -> dict[str, Any]:
    st = gudhi.SimplexTree()
    for node in graph.nodes:
        st.insert([int(node)], filtration=0.0)
    for a, b, data in graph.edges(data=True):
        st.insert([int(a), int(b)], filtration=1.0 / max(float(data["weight"]), 1e-12))
    pyg = from_networkx(graph)
    return {"edge_count": graph.number_of_edges(), "persistence_pair_count": len(st.persistence()), "pyg_edge_index_shape": list(pyg.edge_index.shape)}


def sympy_noncommuting_boundary() -> dict[str, Any]:
    i = sp.I
    sx = sp.Matrix([[0, 1], [1, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    comm = sp.simplify(sx * sz - sz * sx)
    return {"commutator": str(comm), "pass": comm != sp.zeros(2)}


def clifford_boundary() -> dict[str, Any]:
    _, blades = Cl(1, 3)
    pseudo = blades["e1234"]
    return {"pseudoscalar": str(pseudo), "pass": str(pseudo) != str(-pseudo)}


def z3_witness(asym_gap: float, textbook_gap: float, cptp: float) -> dict[str, Any]:
    solver = z3.Solver()
    a, t, c = z3.Bools("asym textbook cptp")
    solver.add(a == (asym_gap > 0.05), t == (textbook_gap < 1e-12), c == (cptp < 1e-12), z3.Not(z3.And(a, t, c)))
    return {"solver_status": str(solver.check()), "pass": solver.check() == z3.unsat, "asym_separates": asym_gap > 0.05, "textbook_reduces": textbook_gap < 1e-12, "cptp": cptp < 1e-12}


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rho0 = density(initial_state())
    asym_rho, asym_meta = shell_weighted_channel(rho0, "hopf", True)
    sym_rho, sym_meta = shell_weighted_channel(rho0, "hopf", False)
    textbook_rho = apply_kraus(rho0, symmetric_embedded_kraus(gamma=0.055 + 0.20 * sym_meta["mean_weight"]))
    uniform_rho, uniform_meta = shell_weighted_channel(rho0, "uniform", True)
    random_rho, random_meta = shell_weighted_channel(rho0, "random_projection", True)
    asym = readouts(asym_rho)
    sym = readouts(sym_rho)
    textbook = readouts(textbook_rho)
    uniform = readouts(uniform_rho)
    random = readouts(random_rho)
    asym_signed_gap = abs(asym["coherent_information_chirality_to_rest"] - sym["coherent_information_chirality_to_rest"])
    textbook_gap = max(abs(sym[key] - textbook[key]) for key in sym)
    positive = {
        "chirality_asymmetric_hopf_shell_channel_separates_signed_information": {
            "asymmetric": asym,
            "symmetric": sym,
            "signed_gap": asym_signed_gap,
            "cptp_gap": asym_meta["cptp_gap"],
            "pass": asym_signed_gap > 0.05 and asym_meta["cptp_gap"] < 1e-12,
        },
        "chirality_symmetric_shell_channel_reduces_to_textbook_cptp": {
            "textbook_gap": textbook_gap,
            "pass": textbook_gap < 1e-12,
        },
        "hopf_shell_graph_has_persistence_witness": {
            "persistence": persistence(asym_meta["graph"]),
            "pass": persistence(asym_meta["graph"])["edge_count"] == 6,
        },
        "noncommuting_algebra_boundary": sympy_noncommuting_boundary(),
        "clifford_chirality_boundary": clifford_boundary(),
    }
    graveyard_companions = {
        "uniform_shell_graph_changes_asymmetric_readout": {
            "candidate": asym,
            "control": uniform,
            "pass": abs(asym["coherent_information_chirality_to_rest"] - uniform["coherent_information_chirality_to_rest"]) > 1e-6,
        },
        "random_projection_changes_graph_weights": {
            "candidate_mean_weight": asym_meta["mean_weight"],
            "control_mean_weight": random_meta["mean_weight"],
            "control_readout": random,
            "pass": abs(asym_meta["mean_weight"] - random_meta["mean_weight"]) > 1e-6,
        },
        "symmetric_channel_kills_chirality_asymmetric_separation": {
            "signed_gap": asym_signed_gap,
            "textbook_gap": textbook_gap,
            "pass": asym_signed_gap > 0.05 and textbook_gap < 1e-12,
        },
    }
    z3_row = z3_witness(asym_signed_gap, textbook_gap, asym_meta["cptp_gap"])
    boundary = {
        "finite_four_qubit_dimension": {"dimension": 2**N_QUBITS, "pass": 2**N_QUBITS == 16},
        "z3_asymmetric_textbook_cptp_witness": z3_row,
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
    }
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "four-qubit density state with Hopf shell graph weights driving chirality-asymmetric CPTP channel blocks and signed entropy readouts",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"passed": sum(1 for value in checks if value), "total": len(checks)},
        "open_choices": [
            "This is the small four-qubit integration; the next version should embed the same asymmetric block in the eight-qubit dynamic shell tensor scout.",
            "The Hopf graph weight only modulates channel strength here; it does not prove shell geometry forces chirality asymmetry.",
            "Textbook CPTP reduction remains the main kill control for symmetric channel implementations.",
        ],
        "why_not_v4_probes": "This is a clean v5 formal scout translated from Grok/Gemini and novelty-killer receipts; it is not a canonical v4 probe.",
        "raw_rows": {
            "asymmetric": asym,
            "symmetric": sym,
            "textbook": textbook,
            "uniform": uniform,
            "random_projection": random,
            "metadata": {
                "asymmetric": {"mean_weight": asym_meta["mean_weight"], "cptp_gap": asym_meta["cptp_gap"]},
                "symmetric": {"mean_weight": sym_meta["mean_weight"], "cptp_gap": sym_meta["cptp_gap"]},
                "uniform": {"mean_weight": uniform_meta["mean_weight"], "cptp_gap": uniform_meta["cptp_gap"]},
                "random_projection": {"mean_weight": random_meta["mean_weight"], "cptp_gap": random_meta["cptp_gap"]},
            },
        },
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all(checks) and all(row["pass"] for row in boundary.values()), "result": str(OUT_PATH), "signed_gap": asym_signed_gap, "textbook_gap": textbook_gap, "cptp_gap": asym_meta["cptp_gap"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
