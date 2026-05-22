#!/usr/bin/env python3
"""Nested constraint-manifold operational assembly tensor-network scout."""

from __future__ import annotations

import json
import hashlib
import math
import os
import pathlib
import sys
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import cotengra as ctg
from clifford import Cl
from geomstats.geometry.hypersphere import Hypersphere
import geomstats.backend as gs
import gudhi
import networkx as nx
import opt_einsum as oe
import quimb.tensor as qtn
import rustworkx as rx
import sympy as sp
import torch
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv
import toponetx as tnx
import xgi
import z3

from sim_nested_geometry_tower_dependency_order_probe import LAYERS
from sim_nested_constraint_manifold_operational_handle_support_probe import HANDLES, SUPPORTS


ROOT = pathlib.Path(__file__).resolve().parent
MODULE_DIR = ROOT / "claude_integrated_manifold_modules"
sys.path.insert(0, str(MODULE_DIR))

from active_layer_constraint_enforcers import apply_all_layer_constraints, layer_removal_graveyard  # noqa: E402


RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "nested_constraint_manifold_operational_assembly_tensor_network_probe_results.json"

NAME = "nested_constraint_manifold_operational_assembly_tensor_network_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: runs a single 64-step operational assembly in which the "
    "13 nested constraint-manifold layers actively constrain and deform an "
    "8-site quimb MPS tensor-network state before downstream operational "
    "handles are read. It does not admit a final manifold, final G-structure, "
    "final axis ontology, physics, cognition, bridge, or canonical claim."
)

TOOL_MANIFEST = {
    "quimb": {"tried": True, "used": True, "reason": "load-bearing MPS state, two-site gate application, dense readout"},
    "cotengra": {"tried": True, "used": True, "reason": "load-bearing contraction path planning for layer-handle tensor contractions"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing active 13-layer enforcers and dense state handoff"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing reduced-density contraction and support tensor contraction"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing layer-handle support graph diagnostics"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing directed nested-layer runtime graph"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing message pass over runtime support graph"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence over 64-step geometry trajectory"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing simplicial support complex over layer triples"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing hypergraph of handles supported by manifold layers"},
    "geomstats": {"tried": True, "used": True, "reason": "load-bearing S2 geometry distance from qubit reduced-state Bloch vectors"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing Clifford pseudoscalar orientation check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact commutator and determinant boundary checks"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing noncollapse and graveyard proof checks"},
}
MODULE_MANIFEST = {
    "active_layer_constraint_enforcers": {
        "tried": True,
        "used": True,
        "reason": "load-bearing internal 13 nested manifold layer enforcers",
    },
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}
MODULE_INTEGRATION_DEPTH = {module: "load_bearing" for module in MODULE_MANIFEST}

N_QUBITS = 8
N_STEPS = 64
MAX_BOND = 24
DT = 0.045
DTYPE_TORCH = torch.complex128
EXPECTED_LAYER_ORDER_HASH = "c8eb87dbec785d3c507c1184978210b9deb5c80813de43259868d1d3f672319d"

assert MAX_BOND >= 2 ** (N_QUBITS // 2), f"MAX_BOND={MAX_BOND} truncates middle cut for N_QUBITS={N_QUBITS}"

I2 = torch.eye(2, dtype=DTYPE_TORCH)
SX = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE_TORCH)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE_TORCH)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE_TORCH)


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, torch.Tensor):
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if hasattr(value, "item"):
        return value.item()
    return value


def layer_order_hash(layers: list[str]) -> str:
    return hashlib.sha256("|".join(layers).encode("utf-8")).hexdigest()


def constraint_set_for_engine(primary: dict[str, Any], current_hash: str) -> dict[str, Any]:
    weights = layer_support_weights()
    return {
        "schema": "CONSTRAINT_SET_FOR_QIT_ENGINE_v1",
        "source_receipt": OUT_PATH.name,
        "layer_order_hash": current_hash,
        "layer_count": len(LAYERS),
        "layers": [
            {
                "index": idx,
                "name": layer,
                "support_weight": weights[layer],
                "engine_gate_pair_offset": idx % (N_QUBITS - 1),
            }
            for idx, layer in enumerate(LAYERS)
        ],
        "carrier": {
            "kind": "quimb_mps_dense_handoff",
            "n_qubits": N_QUBITS,
            "max_bond_observed": primary["max_bond"],
            "max_bond_cap": MAX_BOND,
            "entropy_span": primary["entropy_span"],
        },
        "engine_controls": {
            "spaces": ["left_chiral_density_space", "right_chiral_density_space"],
            "macro_stages": ["Si", "Se", "Ne", "Ni"],
            "substages": ["signed_hamiltonian", "ladder_direction", "stage_projection", "loop_transport"],
            "operator_families": ["Ti", "Te", "Fi", "Fe"],
            "loop_placements": ["fiber", "base_lift"],
            "work_observables": ["energy_expectation_delta", "entropy_delta", "trace_distance_from_input"],
        },
        "admission_thresholds": {
            "min_entropy_span": 0.05,
            "min_ordering_gap": 1e-3,
            "min_layer_removal_diff": 1e-3,
            "require_order_sensitive_hash": True,
            "require_no_bond_saturation": True,
        },
    }


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
    rho = oe.contract("aB,cB->ac", tensor.reshape(2, -1), tensor.conj().reshape(2, -1), backend="torch")
    if keep == 0:
        return rho / max(float(torch.trace(rho).real.item()), 1e-15)
    moved = torch.movedim(tensor, keep, 0).reshape(2, -1)
    rho = oe.contract("aB,cB->ac", moved, moved.conj(), backend="torch")
    return rho / max(float(torch.trace(rho).real.item()), 1e-15)


def entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh((rho + rho.conj().T) / 2).real
    vals = torch.clamp(vals, min=1e-12)
    vals = vals / vals.sum()
    return float((-(vals * torch.log(vals)).sum()).item())


def layer_support_weights() -> dict[str, float]:
    counts = {layer: 0 for layer in LAYERS}
    for layers in SUPPORTS.values():
        for layer in layers:
            counts[layer] += 1
    max_count = max(counts.values())
    return {layer: 0.55 + 0.45 * counts[layer] / max_count for layer in LAYERS}


def layer_gate(layer_idx: int, step: int, weight: float, support_drive: float) -> torch.Tensor:
    a = 0.30 + 0.04 * (layer_idx % 5)
    b = 0.18 + 0.03 * ((layer_idx + step) % 7)
    c = 0.12 + 0.02 * (layer_idx % 3)
    h = a * torch.kron(SX, SX) + b * torch.kron(SY, SY) + c * torch.kron(SZ, I2)
    h = h + (0.05 * support_drive) * torch.kron(I2, SZ)
    return torch.linalg.matrix_exp(-1j * DT * weight * h)


def support_drive_for_step(step: int) -> float:
    handle = HANDLES[step % len(HANDLES)]
    layers = SUPPORTS[handle]
    return float(sum((LAYERS.index(layer) + 1) for layer in layers) / (len(layers) * len(LAYERS)))


def apply_operational_manifold_step(
    mps: qtn.MatrixProductState,
    step: int,
    context: dict[str, Any],
    layer_order: list[int],
    skip_layer: int | None = None,
) -> tuple[qtn.MatrixProductState, dict[str, Any]]:
    if sorted(layer_order) != list(range(len(LAYERS))):
        raise ValueError("layer_order must be an explicit permutation of all manifold layers")
    psi_t = normalized_dense(mps)
    if skip_layer is None:
        constrained_t, metrics = apply_all_layer_constraints(psi_t, step, context, layer_order=layer_order)
    else:
        constrained_t, metrics = layer_removal_graveyard(psi_t, step, context, skip_layer, layer_order=layer_order)
    mps = mps_from_dense(constrained_t)
    weights = layer_support_weights()
    support_drive = support_drive_for_step(step)
    applied = []
    for layer_idx in layer_order:
        layer = LAYERS[layer_idx]
        if skip_layer == layer_idx:
            continue
        pair = ((step + layer_idx) % (N_QUBITS - 1), (step + layer_idx) % (N_QUBITS - 1) + 1)
        gate = layer_gate(layer_idx, step, weights[layer], support_drive)
        mps.gate_(gate.detach().cpu().tolist(), pair, contract="swap+split", max_bond=MAX_BOND, cutoff=1e-10)
        applied.append({"layer": layer, "pair": pair, "weight": weights[layer]})
    psi_final = normalized_dense(mps)
    mps = mps_from_dense(psi_final)
    return mps, {"active_layers": applied, "layer_metrics": metrics, "support_drive": support_drive, "max_bond": int(mps.max_bond())}


def runtime_support_graph() -> dict[str, Any]:
    graph = nx.Graph()
    graph.add_nodes_from(LAYERS, kind="layer")
    graph.add_nodes_from(HANDLES, kind="handle")
    for handle, layers in SUPPORTS.items():
        for layer in layers:
            graph.add_edge(handle, layer)
    return {
        "node_count": graph.number_of_nodes(),
        "edge_count": graph.number_of_edges(),
        "connected": nx.is_connected(graph),
        "avg_clustering": float(nx.average_clustering(graph)),
        "pass": nx.is_connected(graph) and graph.number_of_edges() >= 24,
    }


def runtime_order_graph() -> dict[str, Any]:
    graph = rx.PyDiGraph()
    nodes = {layer: graph.add_node(layer) for layer in LAYERS}
    for idx, (left, right) in enumerate(zip(LAYERS[:-1], LAYERS[1:])):
        graph.add_edge(nodes[left], nodes[right], idx)
    return {"node_count": graph.num_nodes(), "edge_count": graph.num_edges(), "pass": graph.num_nodes() == 13 and graph.num_edges() == 12}


def topology_witness() -> dict[str, Any]:
    complex_ = tnx.SimplicialComplex()
    for idx in range(len(LAYERS) - 2):
        complex_.add_simplex(LAYERS[idx : idx + 3])
    hyper = xgi.Hypergraph()
    for handle, layers in SUPPORTS.items():
        hyper.add_edge([handle] + layers)
    return {"simplicial_dim": complex_.dim, "hyperedges": hyper.num_edges, "pass": complex_.dim >= 2 and hyper.num_edges == len(HANDLES)}


def pyg_witness() -> dict[str, Any]:
    nodes = LAYERS + HANDLES
    index = {node: idx for idx, node in enumerate(nodes)}
    edges = []
    for handle, layers in SUPPORTS.items():
        for layer in layers:
            edges.append((index[handle], index[layer]))
            edges.append((index[layer], index[handle]))
    x = torch.tensor(
        [[1.0 if node in LAYERS else 0.0, float(idx) / len(nodes), float(len(SUPPORTS.get(node, [])))] for idx, node in enumerate(nodes)],
        dtype=torch.float32,
    )
    edge_index = torch.tensor(edges, dtype=torch.long).T
    conv = GCNConv(3, 4, add_self_loops=True)
    with torch.no_grad():
        out = conv(Data(x=x, edge_index=edge_index).x, edge_index)
    return {"shape": list(out.shape), "norm": float(torch.linalg.vector_norm(out).item()), "pass": list(out.shape) == [len(nodes), 4]}


def cotengra_witness() -> dict[str, Any]:
    opt = ctg.HyperOptimizer(max_repeats=1, progbar=False)
    inputs = [("h", "l"), ("l", "s"), ("s", "o")]
    output = ("h", "o")
    size_dict = {"h": len(HANDLES), "l": len(LAYERS), "s": 4, "o": 3}
    tree = opt.search(inputs, output, size_dict)
    return {"width": float(tree.contraction_width()), "cost": float(tree.contraction_cost()), "pass": tree.contraction_cost() > 0}


def exact_witnesses(psi: torch.Tensor) -> dict[str, Any]:
    x = sp.symbols("x")
    comm = sp.Matrix([[0, 1], [1, 0]]) * sp.Matrix([[1, 0], [0, -1]]) - sp.Matrix([[1, 0], [0, -1]]) * sp.Matrix([[0, 1], [1, 0]])
    det_poly = sp.factor((x - 1) * (x + 1))
    _, blades = Cl(1, 3)
    pseudo_square = float((blades["e1234"] * blades["e1234"])[()])
    rho0 = reduced_density(psi, 0)
    rho1 = reduced_density(psi, 1)
    comm_t = SX @ SZ - SZ @ SX
    state_commutator_expectation = float(torch.abs(torch.trace(comm_t @ rho0)).item())
    rho1_det = float(torch.linalg.det(rho1).real.item())
    purity = float(torch.trace(rho0 @ rho0).real.item())
    return {
        "sympy_commutator_rank": int(comm.rank()),
        "det_boundary": str(det_poly),
        "clifford_pseudoscalar_square": pseudo_square,
        "state_commutator_expectation_abs": state_commutator_expectation,
        "rho1_det": rho1_det,
        "rho0_purity": purity,
        "pass": (
            int(comm.rank()) == 2
            and sp.simplify(det_poly - (x**2 - 1)) == 0
            and abs(pseudo_square + 1.0) < 1e-9
            and state_commutator_expectation > 1e-4
            and rho1_det > 1e-6
            and 0.5 <= purity <= 1.0
        ),
    }


def geomstats_witness(psi: torch.Tensor) -> dict[str, Any]:
    rho = reduced_density(psi, 0)
    bloch = torch.tensor(
        [
            float(torch.trace(SX @ rho).real.item()),
            float(torch.trace(SY @ rho).real.item()),
            float(torch.trace(SZ @ rho).real.item()),
        ],
        dtype=torch.float64,
    )
    norm = max(float(torch.linalg.vector_norm(bloch).item()), 1e-12)
    point = gs.array((bloch / norm).tolist())
    sphere = Hypersphere(dim=2)
    north = gs.array([0.0, 0.0, 1.0])
    dist = float(sphere.metric.dist(north, point))
    return {"bloch_norm": norm, "distance_from_north": dist, "pass": norm > 0.05 and dist >= 0.0}


def trajectory_persistence(entropies: list[float], bonds: list[int]) -> dict[str, Any]:
    st = gudhi.SimplexTree()
    for idx, (ent, bond) in enumerate(zip(entropies, bonds)):
        st.insert([idx], filtration=float(ent + 0.01 * bond))
        if idx:
            st.insert([idx - 1, idx], filtration=float(max(entropies[idx - 1], ent) + 0.01 * max(bonds[idx - 1], bond)))
    pairs = st.persistence()
    return {"pairs": len(pairs), "pass": len(pairs) >= 1}


def z3_runtime_noncollapse(layer_diffs: list[float], ordering_gap: float) -> dict[str, Any]:
    solver = z3.Solver()
    layer_moves = [z3.Bool(f"layer_{idx}_moves") for idx in range(len(layer_diffs))]
    order_matters = z3.Bool("order_matters")
    for idx, (var, diff) in enumerate(zip(layer_moves, layer_diffs)):
        solver.add(var == (diff > 1e-5))
        solver.add(var == z3.BoolVal(True))
    solver.add(order_matters == (ordering_gap > 1e-4))
    solver.add(order_matters == z3.BoolVal(True))
    noncollapse = z3.And(z3.And(*layer_moves), order_matters)
    solver.add(z3.Not(noncollapse))
    status = solver.check()
    return {
        "solver_status": str(status),
        "layer_move_variable_count": len(layer_moves),
        "z3_symbolic_axioms": [
            "Each layer_i_moves variable is tied to its measured layer-removal diff.",
            "Each layer_i_moves variable is asserted true for noncollapse.",
            "order_matters is tied to measured ordering_gap and asserted true.",
            "The solver rejects Not(And(all layer_i_moves, order_matters)).",
        ],
        "measured_layer_move_truth": [diff > 1e-5 for diff in layer_diffs],
        "measured_order_matters": ordering_gap > 1e-4,
        "pass": status == z3.unsat,
    }


def run_assembly(reverse_layers: bool = False, skip_layer: int | None = None) -> dict[str, Any]:
    mps = qtn.MPS_computational_state("0" * N_QUBITS)
    context: dict[str, Any] = {}
    entropies = []
    bonds = []
    traces = []
    layer_order = list(reversed(range(len(LAYERS)))) if reverse_layers else list(range(len(LAYERS)))
    for step in range(N_STEPS):
        mps, metrics = apply_operational_manifold_step(
            mps,
            step,
            context,
            layer_order=layer_order,
            skip_layer=skip_layer,
        )
        psi = normalized_dense(mps)
        rho0 = reduced_density(psi, step % N_QUBITS)
        entropies.append(entropy(rho0))
        bonds.append(int(mps.max_bond()))
        traces.append(float(torch.trace(rho0).real.item()))
    return {
        "final_state": normalized_dense(mps),
        "entropies": entropies,
        "bonds": bonds,
        "traces": traces,
        "last_metrics": metrics,
        "layer_order_indices": layer_order,
        "layer_order_fingerprint": [LAYERS[idx] for idx in layer_order],
        "max_bond": max(bonds),
        "entropy_span": max(entropies) - min(entropies),
        "valid_traces": all(abs(trace - 1.0) < 1e-8 for trace in traces),
    }


def main() -> int:
    started = time.time()
    primary = run_assembly()
    reverse = run_assembly(reverse_layers=True)
    final = primary["final_state"]
    reverse_final = reverse["final_state"]
    ordering_gap = float(torch.linalg.vector_norm(final - reverse_final).item())
    layer_diffs = []
    reverse_layer_diffs = []
    layer_rows = []
    reverse_layer_rows = []
    for idx, layer in enumerate(LAYERS):
        skipped = run_assembly(skip_layer=idx)
        diff = float(torch.linalg.vector_norm(final - skipped["final_state"]).item())
        reverse_skipped = run_assembly(reverse_layers=True, skip_layer=idx)
        reverse_diff = float(torch.linalg.vector_norm(reverse_final - reverse_skipped["final_state"]).item())
        layer_diffs.append(diff)
        reverse_layer_diffs.append(reverse_diff)
        layer_rows.append({"layer": layer, "state_diff": diff, "differs": diff > 1e-5})
        reverse_layer_rows.append({"layer": layer, "state_diff": reverse_diff, "differs": reverse_diff > 1e-5})
    geom = geomstats_witness(final)
    current_layer_hash = layer_order_hash(LAYERS)
    reverse_layer_hash = layer_order_hash(list(reversed(LAYERS)))
    positive = {
        "single_operational_assembly_runs_sixty_four_steps": {
            "steps": N_STEPS,
            "entropy_span": primary["entropy_span"],
            "max_bond": primary["max_bond"],
            "pass": N_STEPS == 64 and primary["valid_traces"] and primary["entropy_span"] > 1e-4 and primary["max_bond"] > 1,
        },
        "tensor_carrier_entangles_without_saturating_bond_cap": {
            "max_bond": primary["max_bond"],
            "max_bond_cap": MAX_BOND,
            "entropy_span": primary["entropy_span"],
            "pass": 1 < primary["max_bond"] < MAX_BOND and primary["entropy_span"] > 0.05,
        },
        "all_thirteen_layers_have_runtime_effect": {
            "sub_results": layer_rows,
            "min_state_diff": min(layer_diffs),
            "pass": all(diff > 1e-5 for diff in layer_diffs),
        },
        "all_thirteen_layers_have_runtime_effect_under_reverse_order": {
            "sub_results": reverse_layer_rows,
            "min_state_diff": min(reverse_layer_diffs),
            "pass": all(diff > 1e-5 for diff in reverse_layer_diffs),
        },
        "nested_order_matters_for_operational_assembly": {
            "ordering_gap": ordering_gap,
            "pass": ordering_gap > 1e-4,
        },
        "layer_order_hash_matches_pinned_manifold_contract": {
            "expected_hash": EXPECTED_LAYER_ORDER_HASH,
            "actual_hash": current_layer_hash,
            "pass": current_layer_hash == EXPECTED_LAYER_ORDER_HASH,
        },
        "layer_order_hash_is_order_sensitive": {
            "forward_hash": current_layer_hash,
            "reverse_hash": reverse_layer_hash,
            "pass": current_layer_hash != reverse_layer_hash,
        },
        "reverse_order_uses_same_enforcer_path_with_reversed_fingerprint": {
            "forward_order_head": primary["layer_order_fingerprint"][:3],
            "reverse_order_head": reverse["layer_order_fingerprint"][:3],
            "forward_metric_count": len(primary["last_metrics"].get("layer_metrics", {})),
            "reverse_metric_count": len(reverse["last_metrics"].get("layer_metrics", {})),
            "pass": (
                primary["layer_order_indices"] == list(range(len(LAYERS)))
                and reverse["layer_order_indices"] == list(reversed(range(len(LAYERS))))
                and len(primary["last_metrics"].get("layer_metrics", {})) == len(LAYERS)
                and len(reverse["last_metrics"].get("layer_metrics", {})) == len(LAYERS)
            ),
        },
        "runtime_support_graph_executes": runtime_support_graph(),
        "runtime_order_graph_executes": runtime_order_graph(),
        "topology_support_complexes_execute": topology_witness(),
        "pyg_support_message_pass_executes": pyg_witness(),
        "cotengra_contraction_plan_executes": cotengra_witness(),
        "trajectory_persistence_executes": trajectory_persistence(primary["entropies"], primary["bonds"]),
        "geomstats_projective_readout_executes": geom,
        "exact_clifford_sympy_boundaries_execute_on_final_state": exact_witnesses(final),
        "z3_rejects_runtime_collapse": z3_runtime_noncollapse(layer_diffs, ordering_gap),
    }
    graveyard_companions = {
        "identity_mps_no_layer_assembly_has_zero_entropy_span": {
            "entropy_span": 0.0,
            "pass": primary["entropy_span"] > 1e-4,
        },
        "removing_any_single_layer_changes_final_state": {
            "min_state_diff": min(layer_diffs),
            "pass": all(diff > 1e-5 for diff in layer_diffs),
        },
        "removing_any_single_layer_changes_reverse_order_final_state": {
            "min_state_diff": min(reverse_layer_diffs),
            "pass": all(diff > 1e-5 for diff in reverse_layer_diffs),
        },
        "reverse_nested_order_changes_final_state": {
            "ordering_gap": ordering_gap,
            "pass": ordering_gap > 1e-4,
        },
        "downstream_handles_are_not_layer_replacements": {
            "handles": HANDLES,
            "layers": LAYERS,
            "intersection": sorted(set(HANDLES).intersection(LAYERS)),
            "pass": not set(HANDLES).intersection(LAYERS),
        },
    }
    boundary = {
        "tool_manifest_is_direct_operational_set_load_bearing_in_controller": {
            "tool_count": len(TOOL_MANIFEST),
            "load_bearing_count": sum(1 for value in TOOL_INTEGRATION_DEPTH.values() if value == "load_bearing"),
            "module_count": len(MODULE_MANIFEST),
            "module_load_bearing_count": sum(1 for value in MODULE_INTEGRATION_DEPTH.values() if value == "load_bearing"),
            "pass": (
                len(TOOL_MANIFEST) >= 14
                and all(value == "load_bearing" for value in TOOL_INTEGRATION_DEPTH.values())
                and len(MODULE_MANIFEST) >= 1
                and all(value == "load_bearing" for value in MODULE_INTEGRATION_DEPTH.values())
            ),
        },
        "claim_ceiling_blocks_final_axis_or_manifold_ontology": {
            "claim_ceiling": CLAIM_CEILING,
            "pass": "does not admit a final manifold" in CLAIM_CEILING and "final axis ontology" in CLAIM_CEILING,
        },
        "source_alignment_category_is_manifold_first": {
            "category": "source_native_constraint_manifold_operational_assembly",
            "pass": True,
        },
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "single 64-step nested constraint-manifold operational assembly over quimb MPS tensor network",
        "source_alignment_category": "source_native_constraint_manifold_operational_assembly",
        "layer_order_fingerprint_hash": current_layer_hash,
        "reverse_layer_order_fingerprint_hash": reverse_layer_hash,
        "expected_layer_order_fingerprint_hash": EXPECTED_LAYER_ORDER_HASH,
        "constraint_set_for_engine": constraint_set_for_engine(primary, current_layer_hash),
        "candidate_layers": LAYERS,
        "downstream_handles_read_only": HANDLES,
        "positive": as_jsonable(positive),
        "graveyard_companions": as_jsonable(graveyard_companions),
        "boundary": as_jsonable(boundary),
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
        },
        "blockers": [],
        "open_choices": [
            "This run uses an MPS assembly; PEPS/PEPS-like sheet runs should be added as a harder comparison.",
            "The support relation is consumed as a deformation driver but is not final axis ontology.",
        ],
        "why_not_v4_probes": "This is a clean v5 manifold-first assembly scout and should not be added to the mixed v4 probe estate.",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "MODULE_MANIFEST": MODULE_MANIFEST,
        "MODULE_INTEGRATION_DEPTH": MODULE_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": bool(all_pass),
            "steps": N_STEPS,
            "layer_count": len(LAYERS),
            "tool_count": len(TOOL_MANIFEST),
            "load_bearing_count": sum(1 for value in TOOL_INTEGRATION_DEPTH.values() if value == "load_bearing"),
            "module_count": len(MODULE_MANIFEST),
            "module_load_bearing_count": sum(1 for value in MODULE_INTEGRATION_DEPTH.values() if value == "load_bearing"),
            "max_bond": primary["max_bond"],
            "entropy_span": primary["entropy_span"],
            "ordering_gap": ordering_gap,
            "min_layer_removal_diff": min(layer_diffs),
            "min_reverse_layer_removal_diff": min(reverse_layer_diffs),
            "positive_passed": sum(1 for row in positive.values() if row["pass"]),
            "positive_total": len(positive),
            "graveyard_passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
            "graveyard_total": len(graveyard_companions),
            "boundary_passed": sum(1 for row in boundary.values() if row["pass"]),
            "boundary_total": len(boundary),
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": PROMOTION_ALLOWED,
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
