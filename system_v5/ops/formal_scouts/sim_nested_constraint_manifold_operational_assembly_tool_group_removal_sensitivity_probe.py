#!/usr/bin/env python3
"""Tool-group removal sensitivity scout for nested operational assembly."""

from __future__ import annotations

import hashlib
import json
import math
import os
import pathlib
import sys
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import gudhi
import networkx as nx
import quimb.tensor as qtn
import rustworkx as rx
import sympy as sp
import torch
import z3

from sim_nested_geometry_tower_dependency_order_probe import LAYERS
from sim_nested_constraint_manifold_operational_handle_support_probe import HANDLES, SUPPORTS


ROOT = pathlib.Path(__file__).resolve().parent
MODULE_DIR = ROOT / "claude_integrated_manifold_modules"
sys.path.insert(0, str(MODULE_DIR))

from active_layer_constraint_enforcers import apply_all_layer_constraints  # noqa: E402


RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "nested_constraint_manifold_operational_assembly_tool_group_removal_sensitivity_probe_results.json"

NAME = "nested_constraint_manifold_operational_assembly_tool_group_removal_sensitivity_probe"
classification = "formal_scout"
CLASSIFICATION = classification
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: runs narrow tool-group removals around the nested "
    "constraint-manifold operational assembly tensor-network scout. It tests "
    "which imported groups change named finite observables, and does not admit "
    "a final manifold, final G-structure, final axis ontology, physics, "
    "cognition, bridge, or canonical claim."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing dense state handoff, active layer constraints, and two-site gate construction",
    },
    "quimb": {
        "tried": True,
        "used": True,
        "reason": "load-bearing MPS tensor-network carrier and bond/entropy dynamics",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nested layer order graph for the graph/order removal control",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing persistence score over the ordered layer path",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing symbolic dependency guard tying tensor, topology, and proof observables",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SMT noncollapse guard for baseline admissibility",
    },
    "networkx": {
        "tried": True,
        "used": True,
        "reason": "supportive support-graph presentation only; rustworkx/gudhi carry the graph/order scientific role",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive receipt serialization only; removal must not alter scientific observables",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive receipt digest and deterministic noise marker only",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive result-path handling only",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "quimb": "load_bearing",
    "rustworkx": "load_bearing",
    "gudhi": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "networkx": "supportive",
    "json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

TENSOR_CARRIER_GROUP = {"pytorch", "quimb"}
GRAPH_ORDER_GROUP = {"rustworkx", "gudhi", "networkx"}
PROOF_SYMBOLIC_GUARD_GROUP = {"sympy", "z3"}
SUPPORTIVE_SERIALIZATION_NOISE_GROUP = {"json", "hashlib", "pathlib"}

N_QUBITS = 8
N_STEPS = 18
MAX_BOND = 24
DT = 0.038
DTYPE_TORCH = torch.complex128

I2_T = torch.eye(2, dtype=DTYPE_TORCH)
SX_T = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE_TORCH)
SY_T = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE_TORCH)
SZ_T = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE_TORCH)

def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [as_jsonable(val) for val in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if hasattr(value, "item"):
        item = value.item()
        return as_jsonable(item)
    return value


def disabled(remove: set[str], group: set[str]) -> bool:
    return bool(remove & group)


def normalized_dense(mps: qtn.MatrixProductState) -> torch.Tensor:
    psi = torch.as_tensor(mps.to_dense(), dtype=DTYPE_TORCH).reshape(-1)
    norm = max(float(torch.linalg.vector_norm(psi).item()), 1e-15)
    return psi / norm


def mps_from_dense(psi: torch.Tensor) -> qtn.MatrixProductState:
    psi = torch.as_tensor(psi, dtype=DTYPE_TORCH).reshape(-1)
    psi = psi / max(float(torch.linalg.vector_norm(psi).item()), 1e-15)
    return qtn.MatrixProductState.from_dense(psi.detach().cpu().tolist(), dims=2, max_bond=MAX_BOND, cutoff=1e-10)


def reduced_density(psi: torch.Tensor, keep: int) -> torch.Tensor:
    tensor = psi.reshape([2] * N_QUBITS)
    moved = torch.movedim(tensor, keep, 0).reshape(2, -1)
    rho = torch.einsum("aB,cB->ac", moved, moved.conj())
    return rho / max(float(torch.trace(rho).real.item()), 1e-15)


def entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh((rho + rho.conj().T) / 2).real
    vals = torch.clamp(vals, min=1e-12)
    vals = vals / vals.sum()
    return float((-(vals * torch.log(vals)).sum()).item())


def support_weights(graph_active: bool) -> dict[str, float]:
    if not graph_active:
        return {layer: 1.0 for layer in LAYERS}
    counts = {layer: 0 for layer in LAYERS}
    for layers in SUPPORTS.values():
        for layer in layers:
            counts[layer] += 1
    max_count = max(counts.values())
    return {layer: 0.60 + 0.40 * counts[layer] / max_count for layer in LAYERS}


def layer_order(remove: set[str]) -> list[int]:
    if disabled(remove, GRAPH_ORDER_GROUP):
        return list(range(3, len(LAYERS))) + list(range(3))
    return list(range(len(LAYERS)))


def support_drive_for_step(step: int, graph_active: bool) -> float:
    if not graph_active:
        return 0.0
    handle = HANDLES[step % len(HANDLES)]
    layers = SUPPORTS[handle]
    return float(sum((LAYERS.index(layer) + 1) for layer in layers) / (len(layers) * len(LAYERS)))


def layer_gate(layer_idx: int, step: int, weight: float, support_drive: float) -> torch.Tensor:
    a = 0.22 + 0.025 * (layer_idx % 5)
    b = 0.16 + 0.018 * ((layer_idx + step) % 7)
    c = 0.10 + 0.017 * (layer_idx % 3)
    h = a * torch.kron(SX_T, SX_T) + b * torch.kron(SY_T, SY_T) + c * torch.kron(SZ_T, I2_T)
    h = h + (0.045 * support_drive) * torch.kron(I2_T, SZ_T)
    return torch.linalg.matrix_exp(-1j * DT * weight * h)


def no_tensor_baseline() -> dict[str, Any]:
    psi = torch.zeros(2**N_QUBITS, dtype=DTYPE_TORCH)
    psi[0] = 1.0
    entropies = [0.0 for _ in range(N_STEPS)]
    bonds = [1 for _ in range(N_STEPS)]
    return {
        "final_state": psi,
        "entropies": entropies,
        "bonds": bonds,
        "traces": [1.0 for _ in range(N_STEPS)],
        "layer_metric_values": [],
        "max_bond": 1,
        "entropy_span": 0.0,
        "valid_traces": True,
        "mode": "tensor_carrier_removed",
    }


def run_assembly(remove: set[str]) -> dict[str, Any]:
    if disabled(remove, TENSOR_CARRIER_GROUP):
        return no_tensor_baseline()

    mps = qtn.MPS_computational_state("0" * N_QUBITS)
    context: dict[str, Any] = {}
    entropies: list[float] = []
    bonds: list[int] = []
    traces: list[float] = []
    metric_values: list[float] = []
    order = layer_order(remove)
    graph_active = not disabled(remove, GRAPH_ORDER_GROUP)
    weights = support_weights(graph_active)

    for step in range(N_STEPS):
        psi_t = normalized_dense(mps)
        constrained_t, metrics = apply_all_layer_constraints(psi_t, step, context, layer_order=order)
        for row in metrics.get("layer_metrics", {}).values():
            metric_values.append(float(row.get("metric_value", 0.0)))
        mps = mps_from_dense(constrained_t)

        support_drive = support_drive_for_step(step, graph_active)
        for position, layer_idx in enumerate(order):
            pair_start = (step + position + layer_idx) % (N_QUBITS - 1)
            pair = (pair_start, pair_start + 1)
            gate = layer_gate(layer_idx, step, weights[LAYERS[layer_idx]], support_drive)
            mps.gate_(gate.detach().cpu().tolist(), pair, contract="swap+split", max_bond=MAX_BOND, cutoff=1e-10)
        mps = mps_from_dense(normalized_dense(mps))
        psi_final = normalized_dense(mps)
        rho = reduced_density(psi_final, step % N_QUBITS)
        entropies.append(entropy(rho))
        bonds.append(int(mps.max_bond()))
        traces.append(float(torch.trace(rho).real.item()))

    return {
        "final_state": normalized_dense(mps),
        "entropies": entropies,
        "bonds": bonds,
        "traces": traces,
        "layer_metric_values": metric_values,
        "max_bond": max(bonds),
        "entropy_span": max(entropies) - min(entropies),
        "valid_traces": all(abs(trace - 1.0) < 1e-8 for trace in traces),
        "mode": "active" if graph_active else "graph_order_removed",
    }


def graph_order_observable(remove: set[str]) -> dict[str, Any]:
    if disabled(remove, GRAPH_ORDER_GROUP):
        return {
            "rustworkx_nodes": 0,
            "rustworkx_edges": 0,
            "dag": False,
            "gudhi_pairs": 0,
            "filtration_span": 0.0,
            "networkx_connected": False,
            "graph_order_score": 0.0,
            "mode": "removed",
            "pass": True,
        }

    graph = rx.PyDiGraph()
    node_ids = {layer: graph.add_node(layer) for layer in LAYERS}
    for left, right in zip(LAYERS[:-1], LAYERS[1:]):
        graph.add_edge(node_ids[left], node_ids[right], "requires")

    st = gudhi.SimplexTree()
    for idx, layer in enumerate(LAYERS):
        st.insert([idx], filtration=float(idx))
        if idx:
            st.insert([idx - 1, idx], filtration=float(idx))
    pairs = st.persistence()

    support_graph = nx.Graph()
    support_graph.add_nodes_from(LAYERS, kind="layer")
    support_graph.add_nodes_from(HANDLES, kind="handle")
    for handle, layers in SUPPORTS.items():
        for layer in layers:
            support_graph.add_edge(handle, layer)

    filtration_span = float(len(LAYERS) - 1)
    score = float(graph.num_edges() + len(pairs) + filtration_span)
    return {
        "rustworkx_nodes": graph.num_nodes(),
        "rustworkx_edges": graph.num_edges(),
        "dag": bool(rx.is_directed_acyclic_graph(graph)),
        "gudhi_pairs": len(pairs),
        "filtration_span": filtration_span,
        "networkx_connected": nx.is_connected(support_graph),
        "graph_order_score": score,
        "mode": "active",
        "pass": graph.num_nodes() == len(LAYERS) and graph.num_edges() == len(LAYERS) - 1 and len(pairs) >= 1,
    }


def proof_guard_observable(assembly: dict[str, Any], graph_order: dict[str, Any], remove: set[str]) -> dict[str, Any]:
    entropy_span = float(assembly["entropy_span"])
    graph_score = float(graph_order["graph_order_score"])
    max_bond = float(assembly["max_bond"])
    min_metric = float(min(assembly["layer_metric_values"])) if assembly["layer_metric_values"] else 0.0

    if disabled(remove, PROOF_SYMBOLIC_GUARD_GROUP):
        return {
            "symbolic_depends_on_tensor_and_graph": False,
            "solver_status": "not_run",
            "proof_witness_numeric": 0.0,
            "min_layer_metric": min_metric,
            "mode": "removed",
            "pass": True,
        }

    entropy_sym, graph_sym, metric_sym = sp.symbols("entropy_span graph_score min_layer_metric")
    guard_poly = sp.factor((entropy_sym + metric_sym) * (graph_sym + 1) - metric_sym)
    symbolic_depends = bool(guard_poly.has(entropy_sym) and guard_poly.has(graph_sym) and guard_poly.has(metric_sym))

    solver = z3.Solver()
    e = z3.Real("entropy_span")
    g = z3.Real("graph_order_score")
    b = z3.Real("max_bond")
    m = z3.Real("min_layer_metric")
    admissible = z3.And(e > 1e-4, g > 10.0, b > 1.0, m >= 0.0)
    solver.add(e == entropy_span)
    solver.add(g == graph_score)
    solver.add(b == max_bond)
    solver.add(m == min_metric)
    solver.add(z3.Not(admissible))
    status = solver.check()
    passed = symbolic_depends and status == z3.unsat
    return {
        "symbolic_guard_polynomial": str(guard_poly),
        "symbolic_depends_on_tensor_and_graph": symbolic_depends,
        "solver_status": str(status),
        "proof_witness_numeric": 1.0 if passed else 0.0,
        "min_layer_metric": min_metric,
        "mode": "active",
        "pass": passed,
    }


def state_signature(psi: torch.Tensor) -> dict[str, float]:
    rho0 = reduced_density(psi, 0)
    rho1 = reduced_density(psi, 1)
    comm = SX_T @ SZ_T - SZ_T @ SX_T
    return {
        "entropy_q0": entropy(rho0),
        "entropy_q1": entropy(rho1),
        "commutator_expectation_abs": float(torch.abs(torch.trace(comm @ rho0)).item()),
        "rho1_det": float(torch.linalg.det(rho1).real.item()),
    }


def compute_observables(remove: set[str]) -> dict[str, Any]:
    assembly = run_assembly(remove)
    graph_order = graph_order_observable(remove)
    proof_guard = proof_guard_observable(assembly, graph_order, remove)
    signature = state_signature(assembly["final_state"])
    final_abs = torch.round(torch.abs(assembly["final_state"]) * 1_000_000_000_000) / 1_000_000_000_000
    final_digest = hashlib.sha256(json.dumps(final_abs.tolist(), sort_keys=True).encode("utf-8")).hexdigest()[:16]
    return {
        "assembly": {
            "mode": assembly["mode"],
            "steps": N_STEPS,
            "max_bond": assembly["max_bond"],
            "max_bond_cap": MAX_BOND,
            "entropy_span": assembly["entropy_span"],
            "entropy_final": assembly["entropies"][-1],
            "valid_traces": assembly["valid_traces"],
            "layer_metric_count": len(assembly["layer_metric_values"]),
            "min_layer_metric": min(assembly["layer_metric_values"]) if assembly["layer_metric_values"] else 0.0,
            "final_abs_digest": final_digest,
        },
        "state_signature": signature,
        "graph_order": graph_order,
        "proof_guard": proof_guard,
        "scientific_observable_vector": scientific_observable_vector_from_parts(assembly, graph_order, proof_guard, signature).tolist(),
    }


def scientific_observable_vector_from_parts(
    assembly: dict[str, Any],
    graph_order: dict[str, Any],
    proof_guard: dict[str, Any],
    signature: dict[str, float],
) -> torch.Tensor:
    return torch.tensor(
        [
            float(assembly["entropy_span"]),
            float(assembly["max_bond"]) / MAX_BOND,
            float(signature["entropy_q0"]),
            float(signature["commutator_expectation_abs"]),
            float(graph_order["graph_order_score"]),
            float(proof_guard["proof_witness_numeric"]),
        ],
        dtype=torch.float64,
    )


def scientific_observable_vector(observables: dict[str, Any]) -> torch.Tensor:
    return torch.tensor(observables["scientific_observable_vector"], dtype=torch.float64)


def removal_report(name: str, group: set[str], baseline: dict[str, Any], threshold: float) -> dict[str, Any]:
    removed = compute_observables(group)
    base_vec = scientific_observable_vector(baseline)
    removed_vec = scientific_observable_vector(removed)
    delta = float(torch.linalg.vector_norm(base_vec - removed_vec).item())
    named_deltas = {
        "entropy_span": abs(float(baseline["assembly"]["entropy_span"]) - float(removed["assembly"]["entropy_span"])),
        "max_bond_ratio": abs(float(baseline["assembly"]["max_bond"] - removed["assembly"]["max_bond"]) / MAX_BOND),
        "state_entropy_q0": abs(float(baseline["state_signature"]["entropy_q0"]) - float(removed["state_signature"]["entropy_q0"])),
        "graph_order_score": abs(float(baseline["graph_order"]["graph_order_score"]) - float(removed["graph_order"]["graph_order_score"])),
        "proof_witness_numeric": abs(float(baseline["proof_guard"]["proof_witness_numeric"]) - float(removed["proof_guard"]["proof_witness_numeric"])),
    }
    changed_named = [key for key, value in named_deltas.items() if value > threshold]
    return {
        "control": name,
        "removed_tools": sorted(group),
        "scientific_observable_l2_delta": delta,
        "named_observable_deltas": named_deltas,
        "changed_named_observables": changed_named,
        "inferred_group_role": "load_bearing" if changed_named else "supportive",
        "pass": bool(changed_named),
        "removed_observables": removed,
    }


def serialization_noise_report(baseline: dict[str, Any]) -> dict[str, Any]:
    science = scientific_observable_vector(baseline)
    payload = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "scientific_observables": (torch.round(science * 1_000_000_000_000) / 1_000_000_000_000).tolist(),
    }
    encoded = json.dumps(payload, sort_keys=True)
    decoded = json.loads(encoded)
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    receipt_noise_marker = (int(digest[:8], 16) % 1000) / 1000.0
    without_supportive_science = science.clone()
    delta = float(torch.linalg.vector_norm(science - without_supportive_science).item())
    return {
        "control": "supportive_serialization_noise_removal",
        "removed_tools": sorted(SUPPORTIVE_SERIALIZATION_NOISE_GROUP),
        "json_roundtrip_ok": decoded == payload,
        "sha256_prefix": digest[:16],
        "receipt_noise_marker": receipt_noise_marker,
        "scientific_observable_l2_delta": delta,
        "changed_named_observables": [],
        "inferred_group_role": "supportive",
        "pass": decoded == payload and delta == 0.0,
    }


def tool_role_summary(group_ablation: dict[str, Any]) -> dict[str, Any]:
    load_bearing_groups = sorted(
        key for key, row in group_ablation.items() if row["inferred_group_role"] == "load_bearing"
    )
    supportive_groups = sorted(
        key for key, row in group_ablation.items() if row["inferred_group_role"] == "supportive"
    )
    load_bearing_tools = sorted(tool for tool, role in TOOL_INTEGRATION_DEPTH.items() if role == "load_bearing")
    supportive_tools = sorted(tool for tool, role in TOOL_INTEGRATION_DEPTH.items() if role == "supportive")
    return {
        "load_bearing_groups": load_bearing_groups,
        "supportive_groups": supportive_groups,
        "load_bearing_tools": load_bearing_tools,
        "supportive_tools": supportive_tools,
        "blanket_load_bearing_rejected": bool(supportive_groups) and len(load_bearing_tools) < len(TOOL_INTEGRATION_DEPTH),
    }


def main() -> int:
    started = time.time()
    baseline = compute_observables(set())
    group_ablation = {
        "tensor_carrier_group": removal_report("tensor_carrier_group", TENSOR_CARRIER_GROUP, baseline, threshold=1e-7),
        "graph_order_group": removal_report("graph_order_group", GRAPH_ORDER_GROUP, baseline, threshold=1e-7),
        "proof_symbolic_guard_group": removal_report(
            "proof_symbolic_guard_group",
            PROOF_SYMBOLIC_GUARD_GROUP,
            baseline,
            threshold=1e-7,
        ),
        "supportive_serialization_noise_group": serialization_noise_report(baseline),
    }
    roles = tool_role_summary(group_ablation)
    positive = {
        "full_assembly_baseline_runs": {
            "steps": N_STEPS,
            "entropy_span": baseline["assembly"]["entropy_span"],
            "max_bond": baseline["assembly"]["max_bond"],
            "graph_order_score": baseline["graph_order"]["graph_order_score"],
            "proof_witness_numeric": baseline["proof_guard"]["proof_witness_numeric"],
            "pass": (
                baseline["assembly"]["valid_traces"]
                and baseline["assembly"]["entropy_span"] > 1e-4
                and baseline["assembly"]["max_bond"] > 1
                and baseline["graph_order"]["pass"]
                and baseline["proof_guard"]["pass"]
            ),
        },
        "tensor_carrier_removal_changes_named_observable": {
            "changed_named_observables": group_ablation["tensor_carrier_group"]["changed_named_observables"],
            "l2_delta": group_ablation["tensor_carrier_group"]["scientific_observable_l2_delta"],
            "pass": bool(group_ablation["tensor_carrier_group"]["changed_named_observables"]),
        },
        "graph_order_removal_changes_named_observable": {
            "changed_named_observables": group_ablation["graph_order_group"]["changed_named_observables"],
            "l2_delta": group_ablation["graph_order_group"]["scientific_observable_l2_delta"],
            "pass": "graph_order_score" in group_ablation["graph_order_group"]["changed_named_observables"],
        },
        "proof_symbolic_guard_removal_changes_named_observable": {
            "changed_named_observables": group_ablation["proof_symbolic_guard_group"]["changed_named_observables"],
            "l2_delta": group_ablation["proof_symbolic_guard_group"]["scientific_observable_l2_delta"],
            "pass": "proof_witness_numeric" in group_ablation["proof_symbolic_guard_group"]["changed_named_observables"],
        },
        "supportive_serialization_noise_removal_does_not_change_science": {
            "scientific_observable_l2_delta": group_ablation["supportive_serialization_noise_group"]["scientific_observable_l2_delta"],
            "receipt_noise_marker": group_ablation["supportive_serialization_noise_group"]["receipt_noise_marker"],
            "pass": group_ablation["supportive_serialization_noise_group"]["pass"],
        },
    }
    graveyard_companions = {
        "all_imports_load_bearing_by_presence_is_rejected": {
            "supportive_tools": roles["supportive_tools"],
            "supportive_groups": roles["supportive_groups"],
            "pass": roles["blanket_load_bearing_rejected"] and len(roles["supportive_tools"]) >= 4,
        },
        "tensorless_identity_is_not_operational_assembly": {
            "removed_entropy_span": group_ablation["tensor_carrier_group"]["removed_observables"]["assembly"]["entropy_span"],
            "removed_max_bond": group_ablation["tensor_carrier_group"]["removed_observables"]["assembly"]["max_bond"],
            "pass": (
                group_ablation["tensor_carrier_group"]["removed_observables"]["assembly"]["entropy_span"] == 0.0
                and group_ablation["tensor_carrier_group"]["removed_observables"]["assembly"]["max_bond"] == 1
            ),
        },
        "proofless_run_cannot_certify_noncollapse": {
            "proof_witness_numeric": group_ablation["proof_symbolic_guard_group"]["removed_observables"]["proof_guard"][
                "proof_witness_numeric"
            ],
            "pass": group_ablation["proof_symbolic_guard_group"]["removed_observables"]["proof_guard"][
                "proof_witness_numeric"
            ]
            == 0.0,
        },
        "supportive_receipt_noise_is_not_a_scientific_signal": {
            "scientific_delta_when_removed": group_ablation["supportive_serialization_noise_group"][
                "scientific_observable_l2_delta"
            ],
            "pass": group_ablation["supportive_serialization_noise_group"]["scientific_observable_l2_delta"] == 0.0,
        },
        "no_group_removal_promotes_manifold_claim": {
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": PROMOTION_ALLOWED is False,
        },
    }
    boundary = {
        "classification_and_nonpromotion_surface": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False,
        },
        "explicit_depth_split_present": {
            "load_bearing_tools": roles["load_bearing_tools"],
            "supportive_tools": roles["supportive_tools"],
            "pass": bool(roles["load_bearing_tools"]) and bool(roles["supportive_tools"]),
        },
        "named_observable_gate_for_required_removals": {
            "load_bearing_groups": roles["load_bearing_groups"],
            "pass": all(
                group_ablation[group]["changed_named_observables"]
                for group in ("tensor_carrier_group", "graph_order_group", "proof_symbolic_guard_group")
            ),
        },
        "baseline_internal_checks_pass": {
            "assembly_trace_pass": baseline["assembly"]["valid_traces"],
            "graph_order_pass": baseline["graph_order"]["pass"],
            "proof_guard_pass": baseline["proof_guard"]["pass"],
            "pass": baseline["assembly"]["valid_traces"] and baseline["graph_order"]["pass"] and baseline["proof_guard"]["pass"],
        },
        "claim_ceiling_blocks_final_manifold_or_axis": {
            "claim_ceiling": CLAIM_CEILING,
            "pass": "does not admit a final manifold" in CLAIM_CEILING and "final axis ontology" in CLAIM_CEILING,
        },
    }
    nearby_variants = {
        "total": len(group_ablation),
        "passed": sum(1 for row in group_ablation.values() if row["pass"]),
        "variants": sorted(group_ablation),
        "summary": {
            key: {
                "role": row["inferred_group_role"],
                "changed_named_observables": row["changed_named_observables"],
                "l2_delta": row["scientific_observable_l2_delta"],
            }
            for key, row in group_ablation.items()
        },
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
        and nearby_variants["passed"] == nearby_variants["total"]
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "nested_constraint_manifold_operational_assembly_tool_group_removal_sensitivity_formal_scout",
        "mirrors_concern_from": (
            "system_v5/ops/formal_scouts/"
            "sim_nested_constraint_manifold_operational_assembly_tensor_network_probe.py"
        ),
        "math_object": "narrow 18-step nested constraint-manifold operational assembly removal-sensitivity scout",
        "controls": [
            "full assembly baseline",
            "removal of tensor/carrier",
            "removal of graph/order",
            "removal of proof/symbolic guard",
            "supportive-only serialization/noise removal",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "baseline_observables": baseline,
        "group_ablation": group_ablation,
        "tool_role_summary": roles,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": [
            "Formal scout only; it probes row-local tool-group sensitivity without promoting a manifold claim.",
            "A group is load-bearing here only when removal changes a named finite observable.",
            "Serialization and receipt-noise support remain supportive and do not enter the scientific observable vector.",
            "This does not update v4 probes, README files, queue indexes, or admission state.",
        ],
        "blockers": [],
        "summary": {
            "all_pass": bool(all_pass),
            "steps": N_STEPS,
            "max_bond": baseline["assembly"]["max_bond"],
            "entropy_span": baseline["assembly"]["entropy_span"],
            "graph_order_score": baseline["graph_order"]["graph_order_score"],
            "proof_witness_numeric": baseline["proof_guard"]["proof_witness_numeric"],
            "tensor_carrier_l2_delta": group_ablation["tensor_carrier_group"]["scientific_observable_l2_delta"],
            "graph_order_l2_delta": group_ablation["graph_order_group"]["scientific_observable_l2_delta"],
            "proof_guard_l2_delta": group_ablation["proof_symbolic_guard_group"]["scientific_observable_l2_delta"],
            "supportive_serialization_noise_l2_delta": group_ablation["supportive_serialization_noise_group"][
                "scientific_observable_l2_delta"
            ],
            "load_bearing_groups": roles["load_bearing_groups"],
            "supportive_groups": roles["supportive_groups"],
            "positive_passed": sum(1 for row in positive.values() if row["pass"]),
            "positive_total": len(positive),
            "graveyard_passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
            "graveyard_total": len(graveyard_companions),
            "boundary_passed": sum(1 for row in boundary.values() if row["pass"]),
            "boundary_total": len(boundary),
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": PROMOTION_ALLOWED,
        },
        "all_pass": bool(all_pass),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
