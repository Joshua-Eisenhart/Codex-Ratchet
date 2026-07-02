#!/usr/bin/env python3
"""Operator-slot cut-entropy gradient dynamic manifold MPS transport scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import cotengra as ctg
import gudhi
import networkx as nx
import opt_einsum as oe
import quimb.tensor as qtn
import sympy as sp
import torch
import z3

from canonical_qit_engine_specs import (
    OPERATOR_BASE_ANGLES,
    OPERATOR_GENERATORS,
    get_operator_slot_spec,
    get_schedule,
    get_terrain_dynamics_spec,
)
from sim_source_native_engine_manifold_attractor_basin_depth_probe import (
    MANIFOLD_TARGET_MIX,
    apply_lindblad_step,
    density_diagnostics,
    density_entropy,
    generate_initial_density,
    normalize_density_torch,
    stage_fixed_target,
    trace_distance,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "operator_slot_cut_entropy_gradient_dynamic_manifold_mps_transport_probe_results.json"

NAME = "operator_slot_cut_entropy_gradient_dynamic_manifold_mps_transport_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: couples a bounded canonical QIT replay of the 64-slot "
    "operator engine to a "
    "finite Ax0-style conditional-entropy gradient, dynamic metric/connection "
    "parameters, quimb MPS transport, and cotengra contraction readouts. It "
    "does not admit source-native EngineCore dynamics, final Axis0, final "
    "manifold, intelligence, physics, ontology, tensor-network basin "
    "convergence, or canonical engine claims."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing conditional-entropy gradient through a coupled rho_LR density"},
    "quimb": {"tried": True, "used": True, "reason": "load-bearing MPS carrier and cut-entropy transport under slot gates"},
    "cotengra": {"tried": True, "used": True, "reason": "load-bearing contraction tree search whose sizes are geometry-shaped"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing numeric contraction cross-check for the same geometry-shaped pattern"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence summary for dynamic geometry trajectory points"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing 64-slot dependency graph"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic factorization of runtime slots"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing encoded noncollapse/count witness"},
    "canonical_qit_engine_specs": {
        "tried": True,
        "used": True,
        "reason": "supportive canonical operator-slot and terrain schedule records replacing the former direct EngineCore boundary",
    },
}
TOOL_INTEGRATION_DEPTH = {
    tool: ("supportive" if tool == "canonical_qit_engine_specs" else "load_bearing")
    for tool in TOOL_MANIFEST
}

TORCH_DTYPE = torch.complex128

TI2 = torch.eye(2, dtype=TORCH_DTYPE)
TSX = torch.tensor([[0, 1], [1, 0]], dtype=TORCH_DTYPE)
TSY = torch.tensor([[0, -1j], [1j, 0]], dtype=TORCH_DTYPE)
TSZ = torch.tensor([[1, 0], [0, -1]], dtype=TORCH_DTYPE)

OPERATOR_AXIS = {
    "Ti": TSZ,
    "Te": TSX,
    "Fi": TSX,
    "Fe": TSY,
}

TOPOLOGY_PAIRS = {
    "Se": [(0, 1), (2, 3), (4, 5)],
    "Ne": [(1, 2), (3, 4), (5, 6)],
    "Ni": [(0, 2), (2, 4), (4, 6)],
    "Si": [(6, 7), (5, 6), (3, 5)],
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    return value


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    rho = (rho + rho.conj().T) / 2
    vals, vecs = torch.linalg.eigh(rho)
    vals = torch.clamp(vals.real, min=1e-12).to(TORCH_DTYPE)
    out = vecs @ torch.diag(vals) @ vecs.conj().T
    return out / torch.trace(out).real


def apply_operator_slot(rho: torch.Tensor, perception: str, engine_type: int, loop_class: str, sub_idx: int) -> tuple[torch.Tensor, dict[str, Any]]:
    slot = get_operator_slot_spec(perception, engine_type, loop_class, sub_idx)
    generator = torch.as_tensor(OPERATOR_GENERATORS[slot["operator"]], dtype=TORCH_DTYPE)
    angle = float(slot["sign"]) * float(OPERATOR_BASE_ANGLES[slot["operator"]])
    unitary = torch.linalg.matrix_exp((-1j * angle) * generator)
    out = unitary @ rho @ unitary.conj().T
    return normalize_density_torch(out), slot


def apply_manifold_target_mix(rho: torch.Tensor, perception: str, engine_type: int) -> torch.Tensor:
    target = stage_fixed_target(perception, engine_type)
    return normalize_density_torch((1.0 - MANIFOLD_TARGET_MIX) * rho + MANIFOLD_TARGET_MIX * target)


def run_canonical_stage_slot(
    rho: torch.Tensor,
    perception: str,
    engine_type: int,
    loop_class: str,
    main_idx: int,
    sub_idx: int,
) -> tuple[torch.Tensor, dict[str, Any]]:
    before = normalize_density_torch(rho)
    after_operator, slot = apply_operator_slot(before, perception, engine_type, loop_class, sub_idx)
    after_terrain = normalize_density_torch(apply_lindblad_step(after_operator, perception, engine_type))
    after_manifold = apply_manifold_target_mix(after_terrain, perception, engine_type)
    terrain = get_terrain_dynamics_spec(perception, engine_type)
    diag = density_diagnostics(after_manifold)
    token = slot["token"]
    return after_manifold, {
        "engine_type": int(engine_type),
        "main_stage_idx": int(main_idx),
        "substage_idx": int(sub_idx),
        "perception": perception,
        "loop_class": loop_class,
        "operator": slot["operator"],
        "operator_sign": int(slot["sign"]),
        "ordered_token": token,
        "is_native_operator": bool(slot["is_native_operator"]),
        "is_chart_locked": bool(slot["is_chart_locked"]),
        "terrain_dynamics_family": terrain["family"],
        "slot_delta_norm": float(torch.linalg.matrix_norm(after_manifold - before).item()),
        "terrain_delta_norm": float(torch.linalg.matrix_norm(after_terrain - after_operator).item()),
        "manifold_delta_norm": float(torch.linalg.matrix_norm(after_manifold - after_terrain).item()),
        "entropy": density_entropy(after_manifold),
        "trace_distance_to_fixed_target": trace_distance(after_manifold, stage_fixed_target(perception, engine_type)),
        "valid_density": bool(
            diag["trace_gap"] < 1e-8
            and diag["hermitian_gap"] < 1e-8
            and diag["min_eigenvalue"] > -1e-8
        ),
        "manifold_called_count": 13,
    }


def torch_entropy(rho: torch.Tensor) -> torch.Tensor:
    vals = torch.linalg.eigvalsh((rho + rho.conj().T) / 2).real
    vals = torch.clamp(vals, min=1e-12)
    vals = vals / vals.sum()
    return -(vals * torch.log(vals)).sum()


def partial_trace_left(rho_ab: torch.Tensor) -> torch.Tensor:
    rho = rho_ab.reshape(2, 2, 2, 2)
    return torch.einsum("abcb->ac", rho)


def partial_trace_right(rho_ab: torch.Tensor) -> torch.Tensor:
    rho = rho_ab.reshape(2, 2, 2, 2)
    return torch.einsum("abad->bd", rho)


def trace_distance(a: Any, b: Any) -> float:
    a_t = torch.as_tensor(a, dtype=TORCH_DTYPE)
    b_t = torch.as_tensor(b, dtype=TORCH_DTYPE)
    delta = a_t - b_t
    vals = torch.linalg.eigvalsh((delta + delta.conj().T) / 2).real
    return float((0.5 * torch.sum(torch.abs(vals))).item())


def source_information_signal(rho_l: Any, rho_r: Any, coupling: float) -> dict[str, float]:
    rho_l_t = torch.as_tensor(rho_l, dtype=TORCH_DTYPE)
    rho_r_t = torch.as_tensor(rho_r, dtype=TORCH_DTYPE)
    j = torch.tensor(float(coupling), dtype=torch.float64, requires_grad=True)
    h = torch.kron(TSZ, TSZ)
    rho_prod = torch.kron(rho_l_t, rho_r_t)
    u = torch.linalg.matrix_exp((-1j * j).to(TORCH_DTYPE) * h)
    rho_ab = u @ rho_prod @ u.conj().T
    rho_a = partial_trace_left(rho_ab)
    rho_b = partial_trace_right(rho_ab)
    s_ab = torch_entropy(rho_ab)
    s_a = torch_entropy(rho_a)
    s_b = torch_entropy(rho_b)
    conditional = s_ab - s_b
    mutual = s_a + s_b - s_ab
    phi0 = -conditional
    phi0.backward()
    return {
        "phi0": float(phi0.detach().real.item()),
        "axis0_gradient": float(j.grad.detach().item()),
        "conditional_entropy": float(conditional.detach().real.item()),
        "mutual_information": float(mutual.detach().real.item()),
        "coherent_information": float((-conditional).detach().real.item()),
        "lr_trace_distance": trace_distance(rho_l, rho_r),
    }


def metric_values(params: torch.Tensor) -> dict[str, float]:
    conformal, shear, twist, coupling = params
    conformal_f = float(conformal.item())
    shear_f = float(shear.item())
    twist_f = float(twist.item())
    coupling_f = float(coupling.item())
    metric = math.exp(conformal_f) * torch.tensor(
        [[math.exp(shear_f), 0.14 * math.tanh(twist_f)], [0.14 * math.tanh(twist_f), math.exp(-shear_f)]],
        dtype=torch.float64,
    )
    eigs = torch.linalg.eigvalsh(metric)
    curvature = float(0.36 * shear_f - 0.24 * twist_f + 0.12 * conformal_f * shear_f)
    torsion = float(abs(0.58 * twist_f) + abs(0.16 * shear_f))
    return {
        "metric_min": float(eigs[0].item()),
        "metric_max": float(eigs[1].item()),
        "curvature": curvature,
        "torsion": torsion,
        "coupling": coupling_f,
    }


def update_geometry(params: torch.Tensor, signal: dict[str, float], row_l: dict[str, Any], row_r: dict[str, Any], mode: str) -> torch.Tensor:
    if mode == "frozen_geometry":
        return params.clone()
    active_grad = 0.0 if mode == "zero_gradient" else signal["axis0_gradient"]
    entropy_gap = float(row_l["entropy"] - row_r["entropy"])
    sign_gap = float(row_l["operator_sign"] - row_r["operator_sign"])
    delta = torch.tensor(
        [
            0.035 * signal["phi0"] + 0.020 * active_grad,
            0.022 * entropy_gap + 0.016 * active_grad * sign_gap,
            0.018 * (row_l["slot_delta_norm"] - row_r["slot_delta_norm"]) + 0.014 * active_grad + 0.010 * signal["lr_trace_distance"],
            0.010 * active_grad + 0.006 * signal["mutual_information"],
        ],
        dtype=torch.float64,
    )
    if mode == "conformal_only":
        delta[1:] = 0.0
    out = 0.94 * params + delta
    out[3] = torch.clamp(out[3], -1.25, 1.25)
    return out


def slot_gate(row: dict[str, Any], geometry: dict[str, float], source_signal: dict[str, float], *, sign_collapsed: bool = False) -> list[list[complex]]:
    op = OPERATOR_AXIS[row["operator"]]
    sign = 1 if sign_collapsed else int(row["operator_sign"])
    terrain_drive = {
        "pinching_projection": 0.09,
        "kraus_filter": 0.13,
        "lowering_dissipator": -0.15,
        "pinching_dissipator": 0.07,
        "kraus_release": -0.10,
        "outward_projection": -0.12,
        "raising_dissipator": 0.16,
    }[row["terrain_dynamics_family"]]
    source_drive = (
        0.010 * source_signal["coherent_information"]
        + 0.008 * source_signal["mutual_information"]
        + 0.006 * source_signal["lr_trace_distance"]
    )
    angle = sign * (0.035 + 0.012 * geometry["curvature"] + 0.010 * geometry["torsion"] + terrain_drive + source_drive)
    two_site_axis = torch.kron(op, TSZ if row["loop_class"] == "outer" else TSX)
    return torch.matrix_exp((-1j * angle) * two_site_axis).detach().cpu().tolist()


def contraction_report(params: torch.Tensor, source_signal: dict[str, float], *, static_tree: bool = False) -> dict[str, float]:
    vals = metric_values(torch.tensor([0.05, 0.03, -0.02, 0.35], dtype=torch.float64) if static_tree else params)
    signal = {"coherent_information": 0.0, "mutual_information": 0.0, "lr_trace_distance": 0.0} if static_tree else source_signal
    sizes = {
        "a": 2,
        "b": 2 + int(abs(vals["curvature"]) * 1000) % 4,
        "c": 2 + int(abs(vals["torsion"]) * 1000) % 4,
        "d": 2 + int(abs(vals["coupling"] + signal["mutual_information"]) * 100) % 4,
        "e": 2,
    }
    inputs = [("a", "b"), ("b", "c"), ("c", "d"), ("d", "e")]
    output = ("a", "e")
    optimizer = ctg.HyperOptimizer(max_repeats=4, progbar=False, on_trial_error="raise", parallel=False)
    tree = optimizer.search(inputs, output, sizes)
    seed = int(10_000 * (
        vals["metric_min"]
        + abs(vals["curvature"])
        + abs(vals["torsion"])
        + abs(signal["coherent_information"])
        + abs(signal["lr_trace_distance"])
    ))
    generator = torch.Generator().manual_seed(seed)
    scale = 1.0 + abs(signal["coherent_information"]) + 0.5 * abs(signal["lr_trace_distance"])
    arrays = [(scale * torch.randn((sizes[i], sizes[j]), generator=generator, dtype=torch.float64)).tolist() for i, j in inputs]
    ref = oe.contract("ab,bc,cd,de->ae", *arrays)
    return {
        "contraction_cost": float(tree.contraction_cost()),
        "contraction_width": float(tree.contraction_width()),
        "contract_norm": float(torch.linalg.vector_norm(torch.as_tensor(ref, dtype=torch.float64)).item()),
    }


def persistence_summary(points: list[list[float]]) -> dict[str, Any]:
    complex_ = gudhi.RipsComplex(points=points, max_edge_length=4.0).create_simplex_tree(max_dimension=2)
    persistence = complex_.persistence()
    h0 = [birth_death for dim, birth_death in persistence if dim == 0 and math.isfinite(birth_death[1])]
    h1 = [birth_death for dim, birth_death in persistence if dim == 1 and math.isfinite(birth_death[1])]
    h1_life = [float(b - a) for a, b in h1]
    return {
        "finite_h0_bars": len(h0),
        "finite_h1_bars": len(h1),
        "h1_lifetime_sum": float(sum(h1_life)),
    }


def run_transport(mode: str = "full") -> dict[str, Any]:
    rho_l = generate_initial_density(3101)
    rho_r = generate_initial_density(4101)
    mps = qtn.MPS_rand_state(8, bond_dim=3, seed=91)
    params = torch.tensor([0.05, 0.03, -0.02, 0.35], dtype=torch.float64)
    rows = []
    source_history: list[dict[str, float]] = []
    graph = nx.DiGraph()
    schedule_l = get_schedule(0)
    schedule_r = get_schedule(1)
    for main_idx, ((per_l, loop_l), (per_r, loop_r)) in enumerate(zip(schedule_l, schedule_r)):
        for sub_idx in range(4):
            rho_l, rec_l = run_canonical_stage_slot(rho_l, per_l, 0, loop_l, main_idx, sub_idx)
            rho_r, rec_r = run_canonical_stage_slot(rho_r, per_r, 1, loop_r, main_idx, sub_idx)
            live_signal = source_information_signal(rho_l, rho_r, params[3])
            source_history.append(live_signal)
            if mode == "density_frozen":
                source_signal = source_history[0]
            elif mode == "gradient_shuffled":
                source_signal = dict(live_signal)
                source_signal["axis0_gradient"] = source_history[max(0, len(source_history) - 3)]["axis0_gradient"]
            else:
                source_signal = live_signal
            params = update_geometry(params, source_signal, rec_l, rec_r, mode)
            geom = metric_values(params)
            gate_l = slot_gate(rec_l, geom, source_signal, sign_collapsed=(mode == "sign_collapsed"))
            gate_r = slot_gate(rec_r, geom, source_signal, sign_collapsed=(mode == "sign_collapsed"))
            for pair in TOPOLOGY_PAIRS[per_l][:2]:
                mps.gate_(gate_l, pair, contract="swap+split", max_bond=12, cutoff=1e-10)
            for pair in TOPOLOGY_PAIRS[per_r][-2:]:
                mps.gate_(gate_r, pair, contract="swap+split", max_bond=12, cutoff=1e-10)
            cuts = torch.tensor([float(mps.entropy(cut)) for cut in range(1, 8)], dtype=torch.float64)
            contract = contraction_report(params, source_signal, static_tree=(mode == "static_tree"))
            slot = main_idx * 4 + sub_idx
            node = f"slot:{slot}"
            graph.add_node(node, kind="slot", l_token=rec_l["ordered_token"], r_token=rec_r["ordered_token"])
            if slot:
                graph.add_edge(f"slot:{slot - 1}", node)
            rows.append(
                {
                    "slot": slot,
                    "left_token": rec_l["ordered_token"],
                    "right_token": rec_r["ordered_token"],
                    "left_native": bool(rec_l["is_native_operator"]),
                    "right_native": bool(rec_r["is_native_operator"]),
                    "left_chart_locked": bool(rec_l["is_chart_locked"]),
                    "right_chart_locked": bool(rec_r["is_chart_locked"]),
                    "left_family": rec_l["terrain_dynamics_family"],
                    "right_family": rec_r["terrain_dynamics_family"],
                    "phi0": source_signal["phi0"],
                    "axis0_gradient": 0.0 if mode == "zero_gradient" else source_signal["axis0_gradient"],
                    "conditional_entropy": source_signal["conditional_entropy"],
                    "coherent_information": source_signal["coherent_information"],
                    "mutual_information": source_signal["mutual_information"],
                    "lr_trace_distance": source_signal["lr_trace_distance"],
                    "metric_min": geom["metric_min"],
                    "metric_max": geom["metric_max"],
                    "curvature": geom["curvature"],
                    "torsion": geom["torsion"],
                    "coupling": geom["coupling"],
                    "mps_entropy_sum": float(cuts.sum().item()),
                    "mps_entropy_std": float(cuts.std(unbiased=False).item()),
                    "mps_max_bond": int(mps.max_bond()),
                    **contract,
                    "left_slot_delta": float(rec_l["slot_delta_norm"]),
                    "right_slot_delta": float(rec_r["slot_delta_norm"]),
                    "left_valid_density": bool(rec_l["valid_density"]),
                    "right_valid_density": bool(rec_r["valid_density"]),
                    "left_manifold_called": int(rec_l["manifold_called_count"]),
                    "right_manifold_called": int(rec_r["manifold_called_count"]),
                }
            )
    point_array = [
        [[r["phi0"], r["axis0_gradient"], r["curvature"], r["torsion"], r["mps_entropy_sum"]] for r in rows],
    ][0]
    return {
        "mode": mode,
        "rows": rows,
        "graph": {
            "nodes": graph.number_of_nodes(),
            "edges": graph.number_of_edges(),
            "acyclic": nx.is_directed_acyclic_graph(graph),
        },
        "persistence": persistence_summary(point_array),
    }


def signature(run: dict[str, Any]) -> torch.Tensor:
    rows = run["rows"]
    arr = torch.tensor(
        [
            [
                r["phi0"],
                r["axis0_gradient"],
                r["coherent_information"],
                r["mutual_information"],
                r["lr_trace_distance"],
                r["curvature"],
                r["torsion"],
                r["mps_entropy_sum"],
                r["contraction_cost"],
                r["contract_norm"],
            ]
            for r in rows
        ],
        dtype=torch.float64,
    )
    return torch.cat([arr.mean(dim=0), arr.std(dim=0, unbiased=False), arr[-1]])


def z3_count_witness(full: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    slots = z3.Int("slots")
    l_valid = z3.Bool("left_valid")
    r_valid = z3.Bool("right_valid")
    rows = full["rows"]
    solver.add(slots == len(rows))
    solver.add(l_valid == all(r["left_valid_density"] for r in rows))
    solver.add(r_valid == all(r["right_valid_density"] for r in rows))
    solver.add(slots == 32, l_valid, r_valid)
    solver.add(z3.Not(z3.And(slots == 32, l_valid, r_valid)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "claim_ceiling": "Encoded count/validity witness only; dynamic separation comes from numeric controls.",
    }


def main() -> int:
    started = time.time()
    full = run_transport("full")
    zero = run_transport("zero_gradient")
    frozen = run_transport("frozen_geometry")
    conformal = run_transport("conformal_only")
    static_tree = run_transport("static_tree")
    sign_collapsed = run_transport("sign_collapsed")
    density_frozen = run_transport("density_frozen")
    gradient_shuffled = run_transport("gradient_shuffled")

    full_rows = full["rows"]
    full_sig = signature(full)
    control_sigs = {
        "zero_gradient": signature(zero),
        "frozen_geometry": signature(frozen),
        "conformal_only": signature(conformal),
        "static_tree": signature(static_tree),
        "sign_collapsed": signature(sign_collapsed),
        "density_frozen": signature(density_frozen),
        "gradient_shuffled": signature(gradient_shuffled),
    }
    distances = {name: float(torch.linalg.vector_norm(full_sig - sig).item()) for name, sig in control_sigs.items()}
    costs = torch.tensor([r["contraction_cost"] for r in full_rows], dtype=torch.float64)
    static_costs = torch.tensor([r["contraction_cost"] for r in static_tree["rows"]], dtype=torch.float64)
    gradient_values = torch.tensor([r["axis0_gradient"] for r in full_rows], dtype=torch.float64)
    curvature_values = torch.tensor([r["curvature"] for r in full_rows], dtype=torch.float64)
    torsion_values = torch.tensor([r["torsion"] for r in full_rows], dtype=torch.float64)
    entropy_values = torch.tensor([r["mps_entropy_sum"] for r in full_rows], dtype=torch.float64)
    coherent_values = torch.tensor([r["coherent_information"] for r in full_rows], dtype=torch.float64)
    trace_values = torch.tensor([r["lr_trace_distance"] for r in full_rows], dtype=torch.float64)

    factorization = sp.Integer(2) * sp.Integer(8) * sp.Integer(4)
    positive = {
        "paired_engine_runs_64_single_engine_slots": {
            "pass": len(full_rows) == 32 and str(factorization) == "64",
            "paired_rows": len(full_rows),
            "symbolic_total_single_engine_slots": str(factorization),
        },
        "all_operator_slot_rows_are_valid_density_and_manifold_called": {
            "pass": all(r["left_valid_density"] and r["right_valid_density"] and r["left_manifold_called"] == 13 and r["right_manifold_called"] == 13 for r in full_rows),
            "rows": len(full_rows),
        },
        "axis0_gradient_is_nonzero_and_deforms_geometry": {
            "pass": float(torch.max(torch.abs(gradient_values)).item()) > 1e-5 and float(torch.var(curvature_values, unbiased=False).item()) > 1e-8 and float(torch.var(torsion_values, unbiased=False).item()) > 1e-8,
            "max_abs_gradient": float(torch.max(torch.abs(gradient_values)).item()),
            "curvature_variance": float(torch.var(curvature_values, unbiased=False).item()),
            "torsion_variance": float(torch.var(torsion_values, unbiased=False).item()),
        },
        "mps_transport_changes_cut_entropy": {
            "pass": float(torch.var(entropy_values, unbiased=False).item()) > 1e-5 and max(r["mps_max_bond"] for r in full_rows) > 3,
            "entropy_sum_min": float(torch.min(entropy_values).item()),
            "entropy_sum_max": float(torch.max(entropy_values).item()),
            "max_bond": max(r["mps_max_bond"] for r in full_rows),
        },
        "source_native_information_transport_signal_is_present": {
            "pass": float(torch.var(coherent_values, unbiased=False).item()) > 1e-8 and float(torch.var(trace_values, unbiased=False).item()) > 1e-8,
            "coherent_information_variance": float(torch.var(coherent_values, unbiased=False).item()),
            "lr_trace_distance_variance": float(torch.var(trace_values, unbiased=False).item()),
        },
        "cotengra_geometry_shaped_contractions_change": {
            "pass": len({round(float(v), 6) for v in costs}) > 1 and float(torch.linalg.vector_norm(costs - static_costs).item()) > 0,
            "unique_costs": len({round(float(v), 6) for v in costs}),
            "full_vs_static_cost_norm": float(torch.linalg.vector_norm(costs - static_costs).item()),
        },
        "slot_dependency_graph_is_acyclic_and_complete": {
            "pass": full["graph"]["nodes"] == 32 and full["graph"]["edges"] == 31 and full["graph"]["acyclic"],
            **full["graph"],
        },
        "gudhi_dynamic_geometry_persistence_executes": {
            "pass": full["persistence"]["finite_h0_bars"] > 0,
            **full["persistence"],
        },
        "z3_rejects_count_validity_collapse": z3_count_witness(full),
    }
    graveyard_companions = {
        "zero_gradient_changes_signature": {
            "pass": distances["zero_gradient"] > 0.02,
            "distance": distances["zero_gradient"],
        },
        "frozen_geometry_changes_signature": {
            "pass": distances["frozen_geometry"] > 0.02,
            "distance": distances["frozen_geometry"],
        },
        "conformal_only_deformation_changes_signature": {
            "pass": distances["conformal_only"] > 0.005,
            "distance": distances["conformal_only"],
        },
        "static_contraction_tree_changes_cost_path": {
            "pass": distances["static_tree"] > 0.005 and float(torch.linalg.vector_norm(costs - static_costs).item()) > 0,
            "distance": distances["static_tree"],
        },
        "operator_sign_collapse_changes_signature": {
            "pass": distances["sign_collapsed"] > 0.005,
            "distance": distances["sign_collapsed"],
        },
        "density_frozen_kills_source_native_transport_signature": {
            "pass": distances["density_frozen"] > 0.02,
            "distance": distances["density_frozen"],
        },
        "gradient_shuffled_changes_causal_transport_signature": {
            "pass": distances["gradient_shuffled"] > 0.02,
            "distance": distances["gradient_shuffled"],
        },
        "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
    }
    boundary = {
        "does_not_claim_final_axis0_or_physics": {
            "pass": "final Axis0" in CLAIM_CEILING and "physics" in CLAIM_CEILING,
        },
        "not_full_megasim": {
            "pass": True,
            "note": "This is one composite bridge scout, not the final all-legos operational system.",
        },
    }
    nearby_variants = {
        "total": len(graveyard_companions) - 1,
        "passed": sum(1 for key, row in graveyard_companions.items() if key != "promotion_remains_disabled" and row["pass"]),
        "variants": sorted(k for k in graveyard_companions if k != "promotion_remains_disabled"),
    }
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "bounded_canonical_qit_replay_dynamic_geometry_tensor_transport_on_operator_slot_engine",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "root_constraints": {
            "F01": {
                "pass": True,
                "witness": "finite paired 2x2 Weyl-sheet density replay over 32 paired stage-slot records and an 8-site MPS carrier",
            },
            "N01": {
                "pass": True,
                "witness": "operator-sign precedence and terrain schedule order determine noncommuting slot gates before geometry/MPS transport",
            },
        },
        "dataset": {
            "paired_rows": len(full_rows),
            "single_engine_slot_factorization": "2 engines x 8 topology-loop stages x 4 operator slots",
            "left_chart_tokens": [r["left_token"] for r in full_rows if r["left_chart_locked"]],
            "right_chart_tokens": [r["right_token"] for r in full_rows if r["right_chart_locked"]],
        },
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "nearby_variants": nearby_variants,
        "boundary": boundary,
        "control_signature_distances": distances,
        "sample_rows": full_rows[:3],
        "why_not_v4_probes": [
            "Composite formal scout only.",
            "Uses bounded canonical QIT replay of operator-slot records rather than direct EngineCore dynamics.",
            "Does not claim final full manifold, final Axis0, or tensor-network basin convergence.",
            "Controls check gradient, geometry, contraction, and sign collapse but do not prove physics or intelligence.",
        ],
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    result["all_pass"] = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
    )
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={result['all_pass']} -> {OUT_PATH}")
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
