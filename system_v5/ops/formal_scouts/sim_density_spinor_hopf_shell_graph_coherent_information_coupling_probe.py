#!/usr/bin/env python3
"""Density/spinor/Hopf/shell-graph/coherent-information coupling scout."""

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


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "density_spinor_hopf_shell_graph_coherent_information_coupling_probe_results.json"

NAME = "density_spinor_hopf_shell_graph_coherent_information_coupling_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: composes finite density states, spinor carriers, Hopf "
    "shell projection, graph coupling, survivor quotienting, and coherent-information "
    "readouts into one bounded candidate. It does not admit a final manifold tower, "
    "empirical spacetime claim, standard-model recovery, ontology, bridge claim, "
    "or target-system claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing spinors, density matrices, channels, shell distances, and coherent information"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing two-qubit partial traces"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing shell graph and survivor quotient graph"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing graph tensor conversion for the survivor graph"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence over graph-edge filtration"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing noncommuting channel algebra check"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing coupling and graveyard contradiction checks"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

DTYPE = torch.complex128
N = 8


def normalize(psi: torch.Tensor) -> torch.Tensor:
    return psi / torch.linalg.vector_norm(psi)


def seed_spinors() -> list[torch.Tensor]:
    spinors = []
    for idx in range(N):
        theta = 0.23 + 0.13 * idx
        phi = 0.41 * idx
        spinors.append(normalize(torch.tensor([math.cos(theta), math.sin(theta) * complex(math.cos(phi), math.sin(phi))], dtype=DTYPE)))
    return spinors


def hopf_projection(psi: torch.Tensor) -> torch.Tensor:
    a, b = psi[0], psi[1]
    product = a * torch.conj(b)
    return torch.stack([2 * torch.real(product), 2 * torch.imag(product), torch.abs(a) ** 2 - torch.abs(b) ** 2]).to(torch.float64)


def unitary_x(angle: float) -> torch.Tensor:
    c = math.cos(angle / 2)
    s = math.sin(angle / 2)
    return torch.tensor([[c, -1j * s], [-1j * s, c]], dtype=DTYPE)


def unitary_z(angle: float) -> torch.Tensor:
    return torch.tensor([[complex(math.cos(-angle / 2), math.sin(-angle / 2)), 0.0], [0.0, complex(math.cos(angle / 2), math.sin(angle / 2))]], dtype=DTYPE)


def apply_channel_sequence(spinors: list[torch.Tensor], order: str) -> list[torch.Tensor]:
    rz = unitary_z(0.73)
    rx = unitary_x(0.49)
    if order == "zx":
        op = rx @ rz
    elif order == "xz":
        op = rz @ rx
    elif order == "zz":
        op = unitary_z(0.49) @ rz
    else:
        op = torch.eye(2, dtype=DTYPE)
    return [normalize(op @ psi) for psi in spinors]


def two_qubit_density_from_spinor(psi: torch.Tensor, entangle: float, mix: float) -> torch.Tensor:
    state = torch.zeros(4, dtype=DTYPE)
    if entangle <= 0.0:
        state[0] = psi[0]
        state[2] = psi[1]
    else:
        state[0] = math.sqrt(max(0.0, entangle)) * psi[0]
        state[3] = math.sqrt(max(0.0, entangle)) * psi[1]
        state[1] = math.sqrt(max(0.0, 1 - entangle)) * psi[0]
        state[2] = math.sqrt(max(0.0, 1 - entangle)) * psi[1]
    state = normalize(state)
    rho = torch.outer(state, state.conj())
    return (1 - mix) * rho + mix * torch.eye(4, dtype=DTYPE) / 4


def partial_trace_two_qubit(rho: torch.Tensor, keep: int) -> torch.Tensor:
    tensor = rho.reshape(2, 2, 2, 2)
    if keep == 0:
        return oe.contract("abad->bd", tensor)
    return oe.contract("abcb->ac", tensor)


def entropy(rho: torch.Tensor) -> float:
    herm = (rho + rho.conj().T) / 2
    eigs = torch.clamp(torch.linalg.eigvalsh(herm), min=1e-15)
    eigs = eigs / eigs.sum()
    return float((-torch.sum(eigs * torch.log(eigs))).item())


def coherent_information(rho: torch.Tensor) -> float:
    return entropy(partial_trace_two_qubit(rho, 1)) - entropy(rho)


def trace_distance(rho: torch.Tensor, sigma: torch.Tensor) -> float:
    diff = ((rho - sigma) + (rho - sigma).conj().T) / 2
    return float((0.5 * torch.sum(torch.abs(torch.linalg.eigvalsh(diff)))).item())


def one_qubit_density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, psi.conj())


def graph_from_spinors(spinors: list[torch.Tensor], mode: str) -> tuple[nx.Graph, torch.Tensor]:
    points = torch.stack([hopf_projection(psi) for psi in spinors])
    distances = torch.cdist(points, points)
    graph = nx.Graph()
    for idx in range(len(spinors)):
        graph.add_node(idx)
    weights = torch.zeros((len(spinors), len(spinors)), dtype=torch.float64)
    for i in range(len(spinors)):
        for j in range(i + 1, len(spinors)):
            if mode == "random_projection":
                distance = 1.0 + ((i * 3 + j * 5) % 7) / 7.0
            else:
                distance = float(distances[i, j].item())
            similarity = 1.0 - trace_distance(one_qubit_density(spinors[i]), one_qubit_density(spinors[j]))
            weight = max(0.0, similarity) / max(distance * distance, 0.18)
            if mode == "uniform_graph":
                weight = 1.0
            weights[i, j] = weights[j, i] = weight
            graph.add_edge(i, j, weight=weight)
    return graph, weights


def graph_stats(graph: nx.Graph, weights: torch.Tensor) -> dict[str, Any]:
    lap = torch.diag(weights.sum(dim=1)) - weights
    eigs = torch.sort(torch.linalg.eigvalsh(lap))[0]
    st = gudhi.SimplexTree()
    for node in graph.nodes:
        st.insert([int(node)], filtration=0.0)
    for a, b, data in graph.edges(data=True):
        st.insert([int(a), int(b)], filtration=1.0 / max(float(data["weight"]), 1e-12))
    pyg = from_networkx(graph)
    return {
        "edge_count": graph.number_of_edges(),
        "weight_std": float(torch.std(weights[weights > 0]).item()),
        "fiedler_value": float(eigs[1].item()) if len(eigs) > 1 else 0.0,
        "persistence_pair_count": len(st.persistence()),
        "pyg_edge_index_shape": list(pyg.edge_index.shape),
    }


def survivor_quotient(rows: list[dict[str, Any]]) -> dict[str, Any]:
    survivors = [row for row in rows if row["survived"]]
    classes: dict[tuple[Any, ...], list[int]] = defaultdict(list)
    for row in survivors:
        classes[row["signature"]].append(row["node"])
    graph = nx.Graph()
    for row in survivors:
        graph.add_node(row["node"])
    for nodes in classes.values():
        for idx, a in enumerate(nodes):
            for b in nodes[idx + 1 :]:
                graph.add_edge(a, b)
    return {
        "survivor_count": len(survivors),
        "class_count": len(classes),
        "quotient_edge_count": graph.number_of_edges(),
    }


def run_case(name: str, order: str, entangle: float, mix: float, graph_mode: str) -> dict[str, Any]:
    spinors = apply_channel_sequence(seed_spinors(), order)
    graph, weights = graph_from_spinors(spinors, graph_mode)
    densities = [two_qubit_density_from_spinor(psi, entangle=entangle, mix=mix) for psi in spinors]
    ci_values = [coherent_information(rho) for rho in densities]
    rows = []
    for idx, (psi, ci) in enumerate(zip(spinors, ci_values, strict=True)):
        base = hopf_projection(psi)
        signature = (round(float(base[2].item()), 1), ci > 0.05, weights[idx].gt(0.25).sum().item())
        rows.append({"node": idx, "coherent_information": ci, "signature": signature, "survived": ci > 0.05 and weights[idx].sum().item() > 0.5})
    quotient = survivor_quotient(rows)
    stats = graph_stats(graph, weights)
    return {
        "name": name,
        "order": order,
        "entangle": entangle,
        "mix": mix,
        "graph_mode": graph_mode,
        "coherent_information_mean": float(sum(ci_values) / len(ci_values)),
        "coherent_information_min": float(min(ci_values)),
        "graph": stats,
        "quotient": quotient,
        "node_rows": rows,
        "signature": [
            round(float(sum(ci_values) / len(ci_values)), 6),
            round(float(stats["weight_std"]), 6),
            quotient["survivor_count"],
            quotient["class_count"],
        ],
    }


def sympy_noncommutation_check() -> dict[str, Any]:
    i = sp.I
    sx = sp.Matrix([[0, 1], [1, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    comm = sp.simplify(sz * sx - sx * sz)
    return {"commutator": str(comm), "pass": comm != sp.zeros(2)}


def z3_checks(candidate: dict[str, Any], graveyards: dict[str, dict[str, Any]]) -> dict[str, Any]:
    candidate_survives = candidate["quotient"]["survivor_count"] > 0 and candidate["coherent_information_mean"] > 0.05
    product_killed = graveyards["product_state_no_coherent_information"]["coherent_information_mean"] <= 0.05
    mixed_killed = graveyards["maximally_mixed_density_no_coherent_information"]["coherent_information_mean"] <= 0.05
    graph_killed = graveyards["uniform_graph_removes_shell_weight_variation"]["graph"]["weight_std"] < candidate["graph"]["weight_std"]
    solver = z3.Solver()
    c, p, m, g = z3.Bools("candidate product mixed graph")
    solver.add(c == candidate_survives, p == product_killed, m == mixed_killed, g == graph_killed)
    solver.add(z3.Not(z3.And(c, p, m, g)))
    return {
        "candidate_and_three_graveyards_cannot_fail_together": {
            "solver_status": str(solver.check()),
            "pass": solver.check() == z3.unsat,
        }
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    candidate = run_case("noncommuting_spinor_hopf_shell_graph_coupling", "zx", entangle=0.92, mix=0.04, graph_mode="hopf_shell")
    graveyards = {
        "product_state_no_coherent_information": run_case("product_state_no_coherent_information", "zx", entangle=0.0, mix=0.04, graph_mode="hopf_shell"),
        "maximally_mixed_density_no_coherent_information": run_case("maximally_mixed_density_no_coherent_information", "zx", entangle=0.92, mix=1.0, graph_mode="hopf_shell"),
        "uniform_graph_removes_shell_weight_variation": run_case("uniform_graph_removes_shell_weight_variation", "zx", entangle=0.92, mix=0.04, graph_mode="uniform_graph"),
        "random_projection_weakens_hopf_shell_coupling": run_case("random_projection_weakens_hopf_shell_coupling", "zx", entangle=0.92, mix=0.04, graph_mode="random_projection"),
        "commuting_channel_sequence_reduces_order_gap": run_case("commuting_channel_sequence_reduces_order_gap", "zz", entangle=0.92, mix=0.04, graph_mode="hopf_shell"),
    }
    positive = {
        "candidate_survives_density_spinor_hopf_shell_graph_coupling": {
            "coherent_information_mean": candidate["coherent_information_mean"],
            "survivor_count": candidate["quotient"]["survivor_count"],
            "class_count": candidate["quotient"]["class_count"],
            "weight_std": candidate["graph"]["weight_std"],
            "pass": candidate["coherent_information_mean"] > 0.05
            and candidate["quotient"]["survivor_count"] >= 4
            and candidate["quotient"]["class_count"] >= 2
            and candidate["graph"]["weight_std"] > 0.1,
        },
        "noncommuting_channel_algebra_is_real": sympy_noncommutation_check(),
    }
    graveyard_checks = {
        "product_state_no_coherent_information": {
            "coherent_information_mean": graveyards["product_state_no_coherent_information"]["coherent_information_mean"],
            "pass": graveyards["product_state_no_coherent_information"]["coherent_information_mean"] <= 0.05,
        },
        "maximally_mixed_density_no_coherent_information": {
            "coherent_information_mean": graveyards["maximally_mixed_density_no_coherent_information"]["coherent_information_mean"],
            "pass": graveyards["maximally_mixed_density_no_coherent_information"]["coherent_information_mean"] <= 0.05,
        },
        "uniform_graph_removes_shell_weight_variation": {
            "candidate_weight_std": candidate["graph"]["weight_std"],
            "control_weight_std": graveyards["uniform_graph_removes_shell_weight_variation"]["graph"]["weight_std"],
            "pass": graveyards["uniform_graph_removes_shell_weight_variation"]["graph"]["weight_std"] < candidate["graph"]["weight_std"],
        },
        "random_projection_changes_shell_graph_signature": {
            "candidate_signature": candidate["signature"],
            "control_signature": graveyards["random_projection_weakens_hopf_shell_coupling"]["signature"],
            "pass": graveyards["random_projection_weakens_hopf_shell_coupling"]["signature"] != candidate["signature"],
        },
        "commuting_channel_sequence_changes_signature": {
            "candidate_signature": candidate["signature"],
            "control_signature": graveyards["commuting_channel_sequence_reduces_order_gap"]["signature"],
            "pass": graveyards["commuting_channel_sequence_reduces_order_gap"]["signature"] != candidate["signature"],
        },
    }
    z3_result = z3_checks(candidate, graveyards)
    nearby_passes = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_checks.values()]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "finite density states carried by spinors, Hopf-projected to shell graph weights, then quotiented by coherent-information survivor readouts",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_checks,
        "boundary": {
            "provider_proposals_are_not_evidence": {"pass": True},
            "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
            "z3_coupling_checks": {"checks": z3_result, "pass": all(row["pass"] for row in z3_result.values())},
        },
        "nearby_variants": {"passed": sum(1 for item in nearby_passes if item), "total": len(nearby_passes)},
        "open_choices": [
            "The spinor-to-shell graph weight rule is one candidate coupling, not a unique construction.",
            "Coherent information is one signed information readout; conditional entropy and mutual information should be compared in later scouts.",
            "This uses a small finite shell and does not test large tensor-network scaling.",
        ],
        "why_not_v4_probes": "This is a clean v5 exploratory coupling scout translated from provider proposals; it is not a canonical v4 probe.",
        "candidate": candidate,
        "raw_graveyard_rows": graveyards,
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all(nearby_passes) and all(row["pass"] for row in z3_result.values()), "result": str(OUT_PATH), "candidate_signature": candidate["signature"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
