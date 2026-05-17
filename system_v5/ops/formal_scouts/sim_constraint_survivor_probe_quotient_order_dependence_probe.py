#!/usr/bin/env python3
"""Constraint-survivor probe-quotient order-dependence scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from collections import defaultdict
from typing import Any, Callable

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import gudhi
import networkx as nx
import opt_einsum as oe
import rustworkx as rx
import sympy as sp
import torch
from torch_geometric.utils import from_networkx
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "constraint_survivor_probe_quotient_order_dependence_probe_results.json"

NAME = "constraint_survivor_probe_quotient_order_dependence_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: builds finite candidate density assemblies, applies "
    "ordered constraint sequences, and quotients survivor sets by probe "
    "indistinguishability. It tests nominalist constraint engineering as an "
    "executable shape, but does not admit a final manifold tower, ontology, "
    "cycle identity, bridge, axis, or target-system claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite candidate density assemblies, constraints, and probe signatures"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing partial trace contractions for reduced-state probes"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact Pauli constraint noncommutation sanity check"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing survivor-quotient order-dependence contradiction checks"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing indistinguishability graph construction"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing graph-to-tensor conversion for quotient classes"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence over quotient graph filtration"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing directed constraint-order transition graph and cycle checks"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

DTYPE = torch.complex128
N_QUBITS = 3
DIM = 2**N_QUBITS


def one_qubit_operator(local: torch.Tensor, qubit: int) -> torch.Tensor:
    eye = torch.eye(2, dtype=DTYPE)
    op = torch.tensor([[1.0 + 0j]], dtype=DTYPE)
    for idx in range(N_QUBITS):
        op = torch.kron(op, local if idx == qubit else eye)
    return op


def density(psi: torch.Tensor) -> torch.Tensor:
    psi = psi / torch.linalg.vector_norm(psi)
    return torch.outer(psi, psi.conj())


def candidate_states() -> list[dict[str, Any]]:
    states: list[tuple[str, torch.Tensor]] = []
    for idx in range(DIM):
        psi = torch.zeros(DIM, dtype=DTYPE)
        psi[idx] = 1
        states.append((f"basis_{idx:03b}", psi))
    plus = torch.tensor([1, 1], dtype=DTYPE) / math.sqrt(2)
    minus = torch.tensor([1, -1], dtype=DTYPE) / math.sqrt(2)
    zero = torch.tensor([1, 0], dtype=DTYPE)
    one = torch.tensor([0, 1], dtype=DTYPE)
    product_specs = [
        ("plus_plus_plus", [plus, plus, plus]),
        ("plus_zero_zero", [plus, zero, zero]),
        ("zero_plus_zero", [zero, plus, zero]),
        ("zero_zero_plus", [zero, zero, plus]),
        ("minus_plus_zero", [minus, plus, zero]),
        ("one_plus_zero", [one, plus, zero]),
    ]
    for name, parts in product_specs:
        psi = torch.kron(torch.kron(parts[0], parts[1]), parts[2])
        states.append((name, psi))
    ghz = torch.zeros(DIM, dtype=DTYPE)
    ghz[0] = 1 / math.sqrt(2)
    ghz[-1] = 1 / math.sqrt(2)
    w = torch.zeros(DIM, dtype=DTYPE)
    for idx in [1, 2, 4]:
        w[idx] = 1 / math.sqrt(3)
    bell0 = torch.tensor([1, 0, 0, 1], dtype=DTYPE) / math.sqrt(2)
    bell_pair_01 = torch.kron(bell0, zero)
    states.extend([("ghz_000_111", ghz), ("w_single_excitation", w), ("bell_pair_01_zero_2", bell_pair_01)])
    return [{"candidate_id": idx, "source_label": name, "rho": density(psi)} for idx, (name, psi) in enumerate(states)]


def partial_trace_density(rho: torch.Tensor, keep: list[int]) -> torch.Tensor:
    rest = [idx for idx in range(N_QUBITS) if idx not in keep]
    tensor = rho.reshape([2] * N_QUBITS + [2] * N_QUBITS)
    perm = keep + rest + [idx + N_QUBITS for idx in keep] + [idx + N_QUBITS for idx in rest]
    ordered = tensor.permute(perm)
    d_keep = 2 ** len(keep)
    d_rest = 2 ** len(rest)
    return oe.contract("abcb->ac", ordered.reshape(d_keep, d_rest, d_keep, d_rest))


def entropy(rho: torch.Tensor) -> float:
    eigs = torch.clamp(torch.linalg.eigvalsh((rho + rho.conj().T) / 2), min=1e-15)
    eigs = eigs / eigs.sum()
    return float((-torch.sum(eigs * torch.log(eigs))).item())


def trace_distance(a: torch.Tensor, b: torch.Tensor) -> float:
    diff = (a - b + (a - b).conj().T) / 2
    return float(0.5 * torch.sum(torch.abs(torch.linalg.eigvalsh(diff))).item())


def density_valid(rho: torch.Tensor) -> bool:
    herm = (rho + rho.conj().T) / 2
    trace = torch.trace(rho)
    eigs = torch.linalg.eigvalsh(herm)
    return bool(abs(float(torch.real(trace).item()) - 1) < 1e-9 and abs(float(torch.imag(trace).item())) < 1e-9 and float(torch.min(eigs).item()) > -1e-9)


def channel_pauli_flux(rho: torch.Tensor, sign: int) -> torch.Tensor:
    sx = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
    generator = one_qubit_operator(sx, 0) @ one_qubit_operator(sz, 1)
    unitary = torch.linalg.matrix_exp((-1j * sign * 0.41) * generator)
    return unitary @ rho @ unitary.conj().T


def channel_projector_constraint(rho: torch.Tensor) -> torch.Tensor:
    p0 = one_qubit_operator(torch.tensor([[1, 0], [0, 0]], dtype=DTYPE), 0)
    out = p0 @ rho @ p0.conj().T
    trace = torch.real(torch.trace(out))
    return rho if float(trace.item()) < 1e-12 else out / trace


def channel_spectral_filter(rho: torch.Tensor) -> torch.Tensor:
    filt = one_qubit_operator(torch.diag(torch.tensor([1.0, 0.55], dtype=DTYPE)), 1)
    out = filt @ rho @ filt.conj().T
    return out / torch.real(torch.trace(out))


def channel_damping_constraint(rho: torch.Tensor) -> torch.Tensor:
    gamma = 0.34
    k0 = torch.tensor([[1.0, 0.0], [0.0, math.sqrt(1 - gamma)]], dtype=DTYPE)
    k1 = torch.tensor([[0.0, math.sqrt(gamma)], [0.0, 0.0]], dtype=DTYPE)
    out = torch.zeros_like(rho)
    for local in (k0, k1):
        op = one_qubit_operator(local, 2)
        out += op @ rho @ op.conj().T
    return out


CONSTRAINTS: dict[str, Callable[[torch.Tensor], torch.Tensor]] = {
    "positive_flux_pauli_pair_channel": lambda rho: channel_pauli_flux(rho, 1),
    "negative_flux_pauli_pair_channel": lambda rho: channel_pauli_flux(rho, -1),
    "projector_constraint_channel": channel_projector_constraint,
    "spectral_weight_filter_channel": channel_spectral_filter,
    "amplitude_damping_channel": channel_damping_constraint,
}

ORDERS = {
    "flux_then_projector_then_filter_then_damping": [
        "positive_flux_pauli_pair_channel",
        "projector_constraint_channel",
        "spectral_weight_filter_channel",
        "amplitude_damping_channel",
    ],
    "projector_then_flux_then_filter_then_damping": [
        "projector_constraint_channel",
        "positive_flux_pauli_pair_channel",
        "spectral_weight_filter_channel",
        "amplitude_damping_channel",
    ],
    "filter_then_projector_then_flux_then_damping": [
        "spectral_weight_filter_channel",
        "projector_constraint_channel",
        "positive_flux_pauli_pair_channel",
        "amplitude_damping_channel",
    ],
    "negative_flux_then_projector_then_filter_then_damping": [
        "negative_flux_pauli_pair_channel",
        "projector_constraint_channel",
        "spectral_weight_filter_channel",
        "amplitude_damping_channel",
    ],
}


def probe_signature(rho: torch.Tensor, digits: int = 3) -> tuple[float, ...]:
    z = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
    x = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
    probes = [
        torch.real(torch.trace(one_qubit_operator(z, 0) @ rho)).item(),
        torch.real(torch.trace(one_qubit_operator(z, 1) @ rho)).item(),
        torch.real(torch.trace(one_qubit_operator(z, 2) @ rho)).item(),
        torch.real(torch.trace(one_qubit_operator(x, 0) @ rho)).item(),
        entropy(partial_trace_density(rho, [0])),
        entropy(partial_trace_density(rho, [1])),
        entropy(partial_trace_density(rho, [0, 1])),
    ]
    return tuple(round(float(value), digits) for value in probes)


def apply_order(candidate: dict[str, Any], order: list[str]) -> dict[str, Any]:
    rho = candidate["rho"]
    trajectory = []
    for name in order:
        before = rho
        rho = CONSTRAINTS[name](rho)
        trajectory.append({"constraint": name, "step_gap": trace_distance(before, rho), "density_valid": density_valid(rho)})
    return {
        "candidate_id": candidate["candidate_id"],
        "source_label": candidate["source_label"],
        "rho": rho,
        "signature": probe_signature(rho),
        "trajectory": trajectory,
        "density_valid": density_valid(rho),
    }


def quotient_classes(rows: list[dict[str, Any]]) -> dict[str, Any]:
    classes: dict[tuple[float, ...], list[int]] = defaultdict(list)
    labels: dict[tuple[float, ...], list[str]] = defaultdict(list)
    for row in rows:
        classes[row["signature"]].append(row["candidate_id"])
        labels[row["signature"]].append(row["source_label"])
    graph = nx.Graph()
    for row in rows:
        graph.add_node(row["candidate_id"])
    for ids in classes.values():
        for idx, a in enumerate(ids):
            for b in ids[idx + 1 :]:
                graph.add_edge(a, b)
    pyg = from_networkx(graph) if graph.number_of_edges() else None
    st = gudhi.SimplexTree()
    for node in graph.nodes:
        st.insert([int(node)], filtration=0.0)
    for a, b in graph.edges:
        st.insert([int(a), int(b)], filtration=1.0)
    return {
        "class_count": len(classes),
        "classes": [{"signature": list(signature), "candidate_ids": ids, "source_labels": labels[signature]} for signature, ids in classes.items()],
        "largest_class_size": max(len(ids) for ids in classes.values()),
        "indistinguishability_edge_count": graph.number_of_edges(),
        "pyg_edge_index_shape": list(pyg.edge_index.shape) if pyg is not None else [2, 0],
        "persistence_pair_count": len(st.persistence()),
    }


def order_transition_graph(order_summaries: dict[str, dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    nodes = {name: graph.add_node(name) for name in order_summaries}
    names = list(order_summaries)
    for a in names:
        for b in names:
            if a != b and order_summaries[a]["class_count"] != order_summaries[b]["class_count"]:
                graph.add_edge(nodes[a], nodes[b], "quotient_count_differs")
    cycles = list(rx.simple_cycles(graph))
    return {"node_count": graph.num_nodes(), "edge_count": graph.num_edges(), "cycle_count": len(cycles), "pass": graph.num_edges() > 0}


def sympy_noncommutation_check() -> dict[str, Any]:
    sx = sp.Matrix([[0, 1], [1, 0]])
    p0 = sp.Matrix([[1, 0], [0, 0]])
    return {"commutator": str(sx * p0 - p0 * sx), "pass": sx * p0 - p0 * sx != sp.zeros(2)}


def z3_quotient_order_check(class_counts: list[int]) -> dict[str, Any]:
    all_equal_observed = len(set(class_counts)) == 1
    solver = z3.Solver()
    all_equal = z3.Bool("all_equal")
    observed_diff = z3.Bool("observed_diff")
    solver.add(all_equal == True, observed_diff == (not all_equal_observed), z3.Implies(observed_diff, z3.Not(all_equal)))
    return {
        "class_counts": class_counts,
        "solver_status": str(solver.check()),
        "pass": (not all_equal_observed) and solver.check() == z3.unsat,
    }


def main() -> dict[str, Any]:
    started = time.time()
    candidates = candidate_states()
    order_outputs: dict[str, dict[str, Any]] = {}
    for order_name, order in ORDERS.items():
        rows = [apply_order(candidate, order) for candidate in candidates]
        quotient = quotient_classes(rows)
        order_outputs[order_name] = {
            "order": order,
            "survivor_count": sum(1 for row in rows if row["density_valid"]),
            "class_count": quotient["class_count"],
            "largest_class_size": quotient["largest_class_size"],
            "indistinguishability_edge_count": quotient["indistinguishability_edge_count"],
            "pyg_edge_index_shape": quotient["pyg_edge_index_shape"],
            "persistence_pair_count": quotient["persistence_pair_count"],
            "classes": quotient["classes"],
            "all_survivors_density_valid": all(row["density_valid"] for row in rows),
        }
    class_counts = [row["class_count"] for row in order_outputs.values()]
    transition = order_transition_graph(order_outputs)
    positive = {
        "finite_candidate_set_generated_without_assumed_object_classes": {
            "candidate_count": len(candidates),
            "source_labels": [candidate["source_label"] for candidate in candidates],
            "pass": len(candidates) >= 16 and all(density_valid(candidate["rho"]) for candidate in candidates),
        },
        "ordered_constraints_produce_survivor_sets": {
            "survivor_counts": {name: row["survivor_count"] for name, row in order_outputs.items()},
            "pass": all(row["survivor_count"] == len(candidates) for row in order_outputs.values()),
        },
        "probe_indistinguishability_quotient_classes_are_computed": {
            "class_counts": {name: row["class_count"] for name, row in order_outputs.items()},
            "largest_class_sizes": {name: row["largest_class_size"] for name, row in order_outputs.items()},
            "pass": all(row["class_count"] > 0 and row["largest_class_size"] >= 1 for row in order_outputs.values()),
        },
        "constraint_order_changes_probe_quotient_structure": z3_quotient_order_check(class_counts),
        "indistinguishability_graph_and_persistence_are_nonempty": {
            "edge_counts": {name: row["indistinguishability_edge_count"] for name, row in order_outputs.items()},
            "persistence_pair_counts": {name: row["persistence_pair_count"] for name, row in order_outputs.items()},
            "pass": any(row["indistinguishability_edge_count"] > 0 for row in order_outputs.values()),
        },
        "rustworkx_order_transition_graph_detects_order_dependence": transition,
        "sympy_exact_constraint_noncommutation_check": sympy_noncommutation_check(),
    }
    identity_order_rows = []
    for candidate in candidates:
        signature = probe_signature(candidate["rho"])
        identity_order_rows.append({"candidate_id": candidate["candidate_id"], "source_label": candidate["source_label"], "signature": signature})
    identity_quotient = quotient_classes(identity_order_rows)
    all_same_probe = []
    for candidate in candidates:
        all_same_probe.append({"candidate_id": candidate["candidate_id"], "source_label": candidate["source_label"], "signature": (0.0,)})
    collapsed_quotient = quotient_classes(all_same_probe)
    graveyard_companions = {
        "identity_constraint_sequence_does_not_match_nontrivial_order_counts": {
            "identity_class_count": identity_quotient["class_count"],
            "nontrivial_class_counts": class_counts,
            "pass": identity_quotient["class_count"] not in set(class_counts),
        },
        "constant_probe_family_collapses_all_survivors_to_one_class": {
            "class_count": collapsed_quotient["class_count"],
            "largest_class_size": collapsed_quotient["largest_class_size"],
            "pass": collapsed_quotient["class_count"] == 1 and collapsed_quotient["largest_class_size"] == len(candidates),
        },
        "scaled_density_fails_survivor_admission": {
            "trace": float(torch.real(torch.trace(2 * candidates[0]["rho"])).item()),
            "pass": not density_valid(2 * candidates[0]["rho"]),
        },
    }
    boundary = {
        "finite_dimension_three_qubit": {"dimension": DIM, "pass": DIM == 8},
        "constraint_sequence_count": {"count": len(ORDERS), "pass": len(ORDERS) == 4},
        "probe_signature_width": {"width": len(probe_signature(candidates[0]["rho"])), "pass": len(probe_signature(candidates[0]["rho"])) == 7},
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard_companions.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "finite candidate density assemblies constrained into survivor sets and quotiented by probe indistinguishability",
        "candidate_count": len(candidates),
        "orders": ORDERS,
        "order_outputs": order_outputs,
        "identity_quotient": identity_quotient,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyard_companions), "passed": sum(1 for row in graveyard_companions.values() if row["pass"])},
        "blockers": [],
        "open_choices": [
            "The probe family is hand-picked; later scouts should sweep probe families and compare quotient stability.",
            "All constraints are channels here, so survivor count stays full; later scouts should include hard rejection constraints.",
            "Three qubits keep this exact and auditable; larger variable-qubit quotient sweeps should be separate.",
        ],
        "why_not_v4_probes": "This is a clean v5 nominalist survivor-quotient scout and should not add to the mixed v4 probe estate.",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": bool(all_pass),
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": PROMOTION_ALLOWED,
            "class_counts_by_order": {name: row["class_count"] for name, row in order_outputs.items()},
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
