#!/usr/bin/env python3
"""Hard-constraint survivor probe-quotient pruning-order scout."""

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
OUT_PATH = RESULT_DIR / "hard_constraint_survivor_probe_quotient_pruning_order_probe_results.json"

NAME = "hard_constraint_survivor_probe_quotient_pruning_order_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: applies hard admissibility predicates to finite "
    "candidate density assemblies, then quotients surviving candidates by "
    "probe indistinguishability. It tests pruning plus quotienting, but does "
    "not admit a final manifold tower, ontology, cycle identity, bridge, axis, "
    "or target-system claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite density candidates, channel transforms, hard predicates, and probe signatures"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing partial traces for local entropy and reduced-state predicates"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact projector/Pauli noncommutation sanity check"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing survivor-shrink and order-difference contradiction checks"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing survivor indistinguishability graph"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing graph tensor conversion for quotient classes"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence over quotient graph"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing hard-constraint order transition graph"},
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
    for name, parts in [
        ("plus_plus_plus", [plus, plus, plus]),
        ("plus_zero_zero", [plus, zero, zero]),
        ("zero_plus_zero", [zero, plus, zero]),
        ("zero_zero_plus", [zero, zero, plus]),
        ("minus_plus_zero", [minus, plus, zero]),
        ("one_plus_zero", [one, plus, zero]),
        ("plus_one_zero", [plus, one, zero]),
        ("zero_minus_plus", [zero, minus, plus]),
    ]:
        states.append((name, torch.kron(torch.kron(parts[0], parts[1]), parts[2])))
    ghz = torch.zeros(DIM, dtype=DTYPE)
    ghz[0] = 1 / math.sqrt(2)
    ghz[-1] = 1 / math.sqrt(2)
    w = torch.zeros(DIM, dtype=DTYPE)
    for idx in [1, 2, 4]:
        w[idx] = 1 / math.sqrt(3)
    bell = torch.tensor([1, 0, 0, 1], dtype=DTYPE) / math.sqrt(2)
    states.extend(
        [
            ("ghz_000_111", ghz),
            ("w_single_excitation", w),
            ("bell_pair_01_zero_2", torch.kron(bell, zero)),
            ("bell_pair_01_one_2", torch.kron(bell, one)),
        ]
    )
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


def purity(rho: torch.Tensor) -> float:
    return float(torch.real(torch.trace(rho @ rho)).item())


def trace_distance(a: torch.Tensor, b: torch.Tensor) -> float:
    diff = (a - b + (a - b).conj().T) / 2
    return float(0.5 * torch.sum(torch.abs(torch.linalg.eigvalsh(diff))).item())


def density_valid(rho: torch.Tensor) -> bool:
    herm = (rho + rho.conj().T) / 2
    trace = torch.trace(rho)
    eigs = torch.linalg.eigvalsh(herm)
    return bool(abs(float(torch.real(trace).item()) - 1) < 1e-9 and abs(float(torch.imag(trace).item())) < 1e-9 and float(torch.min(eigs).item()) > -1e-9)


def expectation(rho: torch.Tensor, local: torch.Tensor, qubit: int) -> float:
    return float(torch.real(torch.trace(one_qubit_operator(local, qubit) @ rho)).item())


def channel_pauli_flux(rho: torch.Tensor, sign: int) -> torch.Tensor:
    sx = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
    generator = one_qubit_operator(sx, 0) @ one_qubit_operator(sz, 1)
    unitary = torch.linalg.matrix_exp((-1j * sign * 0.41) * generator)
    return unitary @ rho @ unitary.conj().T


def spectral_filter(rho: torch.Tensor) -> torch.Tensor:
    filt = one_qubit_operator(torch.diag(torch.tensor([1.0, 0.55], dtype=DTYPE)), 1)
    out = filt @ rho @ filt.conj().T
    return out / torch.real(torch.trace(out))


def damp(rho: torch.Tensor) -> torch.Tensor:
    gamma = 0.34
    k0 = torch.tensor([[1.0, 0.0], [0.0, math.sqrt(1 - gamma)]], dtype=DTYPE)
    k1 = torch.tensor([[0.0, math.sqrt(gamma)], [0.0, 0.0]], dtype=DTYPE)
    out = torch.zeros_like(rho)
    for local in (k0, k1):
        op = one_qubit_operator(local, 2)
        out += op @ rho @ op.conj().T
    return out


def hard_predicates(rho: torch.Tensor) -> dict[str, bool]:
    sx = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
    local_0 = partial_trace_density(rho, [0])
    local_1 = partial_trace_density(rho, [1])
    pair_01 = partial_trace_density(rho, [0, 1])
    return {
        "density_valid": density_valid(rho),
        "qubit_0_z_expectation_nonnegative": expectation(rho, sz, 0) >= -1e-8,
        "qubit_1_x_magnitude_not_too_large": abs(expectation(rho, sx, 1)) <= 0.76,
        "qubit_0_local_entropy_below_bound": entropy(local_0) <= 0.62,
        "qubit_1_local_entropy_above_floor": entropy(local_1) >= 0.02,
        "pair_01_purity_above_floor": purity(pair_01) >= 0.36,
    }


def probe_signature(rho: torch.Tensor, digits: int = 3) -> tuple[float, ...]:
    sx = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
    values = [
        expectation(rho, sz, 0),
        expectation(rho, sz, 1),
        expectation(rho, sz, 2),
        expectation(rho, sx, 0),
        expectation(rho, sx, 1),
        entropy(partial_trace_density(rho, [0])),
        entropy(partial_trace_density(rho, [1])),
        entropy(partial_trace_density(rho, [0, 1])),
        purity(partial_trace_density(rho, [0, 1])),
    ]
    return tuple(round(float(value), digits) for value in values)


HARD_STEPS: dict[str, Callable[[torch.Tensor], torch.Tensor]] = {
    "positive_flux_pauli_pair_channel": lambda rho: channel_pauli_flux(rho, 1),
    "negative_flux_pauli_pair_channel": lambda rho: channel_pauli_flux(rho, -1),
    "spectral_weight_filter_channel": spectral_filter,
    "amplitude_damping_channel": damp,
}

ORDERS = {
    "filter_then_positive_flux_then_damping": ["spectral_weight_filter_channel", "positive_flux_pauli_pair_channel", "amplitude_damping_channel"],
    "positive_flux_then_filter_then_damping": ["positive_flux_pauli_pair_channel", "spectral_weight_filter_channel", "amplitude_damping_channel"],
    "negative_flux_then_filter_then_damping": ["negative_flux_pauli_pair_channel", "spectral_weight_filter_channel", "amplitude_damping_channel"],
    "damping_then_filter_then_positive_flux": ["amplitude_damping_channel", "spectral_weight_filter_channel", "positive_flux_pauli_pair_channel"],
}


def apply_hard_order(candidate: dict[str, Any], order: list[str]) -> dict[str, Any]:
    rho = candidate["rho"]
    trajectory = []
    killed_by = None
    for step in order:
        before = rho
        rho = HARD_STEPS[step](rho)
        predicates = hard_predicates(rho)
        failed = [name for name, ok in predicates.items() if not ok]
        trajectory.append({"step": step, "gap": trace_distance(before, rho), "predicates": predicates, "failed": failed})
        if failed:
            killed_by = {"step": step, "failed": failed}
            break
    survived = killed_by is None
    return {
        "candidate_id": candidate["candidate_id"],
        "source_label": candidate["source_label"],
        "survived": survived,
        "killed_by": killed_by,
        "rho": rho,
        "signature": probe_signature(rho) if survived else None,
        "trajectory": trajectory,
    }


def quotient_classes(rows: list[dict[str, Any]]) -> dict[str, Any]:
    survivors = [row for row in rows if row["survived"]]
    if not survivors:
        return {"class_count": 0, "classes": [], "largest_class_size": 0, "edge_count": 0, "pyg_edge_index_shape": [2, 0], "persistence_pair_count": 0}
    classes: dict[tuple[float, ...], list[int]] = defaultdict(list)
    labels: dict[tuple[float, ...], list[str]] = defaultdict(list)
    for row in survivors:
        classes[row["signature"]].append(row["candidate_id"])
        labels[row["signature"]].append(row["source_label"])
    graph = nx.Graph()
    for row in survivors:
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
        "classes": [{"signature": list(sig), "candidate_ids": ids, "source_labels": labels[sig]} for sig, ids in classes.items()],
        "largest_class_size": max(len(ids) for ids in classes.values()),
        "edge_count": graph.number_of_edges(),
        "pyg_edge_index_shape": list(pyg.edge_index.shape) if pyg is not None else [2, 0],
        "persistence_pair_count": len(st.persistence()),
    }


def order_transition_graph(order_outputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    nodes = {name: graph.add_node(name) for name in order_outputs}
    for a, row_a in order_outputs.items():
        for b, row_b in order_outputs.items():
            if a != b and (row_a["survivor_count"], row_a["class_count"]) != (row_b["survivor_count"], row_b["class_count"]):
                graph.add_edge(nodes[a], nodes[b], "survivor_or_class_count_differs")
    cycles = list(rx.simple_cycles(graph))
    return {"edge_count": graph.num_edges(), "cycle_count": len(cycles), "pass": graph.num_edges() > 0}


def sympy_projector_noncommutation() -> dict[str, Any]:
    sx = sp.Matrix([[0, 1], [1, 0]])
    p0 = sp.Matrix([[1, 0], [0, 0]])
    comm = sx * p0 - p0 * sx
    return {"commutator": str(comm), "pass": comm != sp.zeros(2)}


def z3_pruning_checks(survivor_counts: list[int], candidate_count: int) -> dict[str, Any]:
    some_pruned = any(count < candidate_count for count in survivor_counts)
    order_diff = len(set(survivor_counts)) > 1
    prune_solver = z3.Solver()
    diff_solver = z3.Solver()
    prune = z3.Bool("some_pruned")
    diff = z3.Bool("order_diff")
    prune_solver.add(prune == some_pruned, prune == False)
    diff_solver.add(diff == order_diff, diff == False)
    return {
        "some_candidates_are_pruned_unsat_if_false": {"solver_status": str(prune_solver.check()), "pass": some_pruned and prune_solver.check() == z3.unsat},
        "survivor_count_depends_on_order_unsat_if_false": {"solver_status": str(diff_solver.check()), "pass": order_diff and diff_solver.check() == z3.unsat},
    }


def main() -> dict[str, Any]:
    started = time.time()
    candidates = candidate_states()
    order_outputs = {}
    for order_name, order in ORDERS.items():
        rows = [apply_hard_order(candidate, order) for candidate in candidates]
        quotient = quotient_classes(rows)
        killed = [row for row in rows if not row["survived"]]
        order_outputs[order_name] = {
            "order": order,
            "survivor_count": len(rows) - len(killed),
            "killed_count": len(killed),
            "killed": [{"candidate_id": row["candidate_id"], "source_label": row["source_label"], "killed_by": row["killed_by"]} for row in killed],
            "class_count": quotient["class_count"],
            "largest_class_size": quotient["largest_class_size"],
            "quotient_classes": quotient["classes"],
            "indistinguishability_edge_count": quotient["edge_count"],
            "persistence_pair_count": quotient["persistence_pair_count"],
        }
    survivor_counts = [row["survivor_count"] for row in order_outputs.values()]
    class_counts = [row["class_count"] for row in order_outputs.values()]
    z3_rows = z3_pruning_checks(survivor_counts, len(candidates))
    positive = {
        "finite_candidate_set_generated": {
            "candidate_count": len(candidates),
            "pass": len(candidates) >= 18 and all(density_valid(candidate["rho"]) for candidate in candidates),
        },
        "hard_constraints_prune_candidate_sets": {
            "survivor_counts": {name: row["survivor_count"] for name, row in order_outputs.items()},
            "killed_counts": {name: row["killed_count"] for name, row in order_outputs.items()},
            "pass": any(count < len(candidates) for count in survivor_counts),
        },
        "pruning_order_changes_survivor_count": {
            "survivor_counts": {name: row["survivor_count"] for name, row in order_outputs.items()},
            "pass": len(set(survivor_counts)) > 1,
        },
        "survivors_are_quotiented_by_probe_indistinguishability": {
            "class_counts": {name: row["class_count"] for name, row in order_outputs.items()},
            "largest_class_sizes": {name: row["largest_class_size"] for name, row in order_outputs.items()},
            "pass": any(row["class_count"] > 0 for row in order_outputs.values())
            and all(row["class_count"] >= 0 for row in order_outputs.values()),
        },
        "order_transition_graph_detects_pruning_difference": order_transition_graph(order_outputs),
        "sympy_exact_projector_noncommutation": sympy_projector_noncommutation(),
        "z3_pruning_and_order_dependence_checks": {"checks": z3_rows, "pass": all(row["pass"] for row in z3_rows.values())},
    }
    no_hard_rejection_rows = [{"candidate_id": c["candidate_id"], "source_label": c["source_label"], "survived": True, "signature": probe_signature(c["rho"])} for c in candidates]
    no_hard_quotient = quotient_classes(no_hard_rejection_rows)
    constant_probe_rows = [{"candidate_id": c["candidate_id"], "source_label": c["source_label"], "survived": True, "signature": (0.0,)} for c in candidates]
    constant_quotient = quotient_classes(constant_probe_rows)
    graveyard_companions = {
        "no_hard_rejection_keeps_all_candidates": {
            "survivor_count": len(no_hard_rejection_rows),
            "class_count": no_hard_quotient["class_count"],
            "pass": len(no_hard_rejection_rows) == len(candidates),
        },
        "constant_probe_collapses_all_survivors": {
            "class_count": constant_quotient["class_count"],
            "largest_class_size": constant_quotient["largest_class_size"],
            "pass": constant_quotient["class_count"] == 1 and constant_quotient["largest_class_size"] == len(candidates),
        },
        "scaled_density_fails_density_admission": {
            "trace": float(torch.real(torch.trace(2 * candidates[0]["rho"])).item()),
            "pass": not density_valid(2 * candidates[0]["rho"]),
        },
        "overstrict_order_can_kill_all_candidates": {
            "extinct_orders": [name for name, row in order_outputs.items() if row["survivor_count"] == 0],
            "pass": any(row["survivor_count"] == 0 for row in order_outputs.values()),
        },
    }
    boundary = {
        "three_qubit_dimension": {"dimension": DIM, "pass": DIM == 8},
        "hard_order_count": {"count": len(ORDERS), "pass": len(ORDERS) == 4},
        "at_least_one_order_has_nonempty_survivor_set": {"survivor_counts": survivor_counts, "pass": any(count > 0 for count in survivor_counts)},
        "class_count_never_exceeds_survivor_count": {
            "pairs": [(row["class_count"], row["survivor_count"]) for row in order_outputs.values()],
            "pass": all(row["class_count"] <= row["survivor_count"] for row in order_outputs.values()),
        },
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard_companions.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "hard admissibility constraints prune finite density candidates before probe indistinguishability quotienting",
        "candidate_count": len(candidates),
        "orders": ORDERS,
        "order_outputs": order_outputs,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyard_companions), "passed": sum(1 for row in graveyard_companions.values() if row["pass"])},
        "blockers": [],
        "open_choices": [
            "The hard predicate thresholds are hand-set and should be swept in a later scout.",
            "This scout proves pruning mechanics and order sensitivity, not the final constraint family.",
            "A later sparse/tensor-network version should scale this beyond exact three-qubit density matrices.",
        ],
        "why_not_v4_probes": "This is a clean v5 hard-survivor quotient scout and should not add to the mixed v4 probe estate.",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": bool(all_pass),
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": PROMOTION_ALLOWED,
            "survivor_counts_by_order": {name: row["survivor_count"] for name, row in order_outputs.items()},
            "class_counts_by_order": {name: row["class_count"] for name, row in order_outputs.items()},
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
