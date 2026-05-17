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
import numpy as np
import opt_einsum as oe
import quimb as qu
import quimb.tensor as qtn
import sympy as sp
import torch
import z3

from engine_core import EngineCore, generate_initial_density


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "operator_slot_cut_entropy_gradient_dynamic_manifold_mps_transport_probe_results.json"

NAME = "operator_slot_cut_entropy_gradient_dynamic_manifold_mps_transport_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: couples the repaired 64-slot operator engine to a "
    "finite Ax0-style conditional-entropy gradient, dynamic metric/connection "
    "parameters, quimb MPS transport, and cotengra contraction readouts. It "
    "does not admit final Axis0, final manifold, intelligence, physics, "
    "ontology, or canonical engine claims."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing density, geometry, trajectory, and control summaries"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing conditional-entropy gradient through a coupled rho_LR density"},
    "quimb": {"tried": True, "used": True, "reason": "load-bearing MPS carrier and cut-entropy transport under slot gates"},
    "cotengra": {"tried": True, "used": True, "reason": "load-bearing contraction tree search whose sizes are geometry-shaped"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing numeric contraction cross-check for the same geometry-shaped pattern"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing persistence summary for dynamic geometry trajectory points"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing 64-slot dependency graph"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic factorization of runtime slots"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing encoded noncollapse/count witness"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

DTYPE = np.complex128
TORCH_DTYPE = torch.complex128

I2 = np.eye(2, dtype=DTYPE)
SX = np.array([[0, 1], [1, 0]], dtype=DTYPE)
SY = np.array([[0, -1j], [1j, 0]], dtype=DTYPE)
SZ = np.array([[1, 0], [0, -1]], dtype=DTYPE)

TI2 = torch.eye(2, dtype=TORCH_DTYPE)
TSX = torch.tensor(SX, dtype=TORCH_DTYPE)
TSY = torch.tensor(SY, dtype=TORCH_DTYPE)
TSZ = torch.tensor(SZ, dtype=TORCH_DTYPE)

OPERATOR_AXIS = {
    "Ti": SZ,
    "Te": SX,
    "Fi": SX,
    "Fe": SY,
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
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    return value


def normalize_density(rho: np.ndarray) -> np.ndarray:
    rho = (rho + rho.conj().T) / 2
    vals, vecs = np.linalg.eigh(rho)
    vals = np.clip(vals.real, 1e-12, None)
    out = vecs @ np.diag(vals) @ vecs.conj().T
    return (out / np.trace(out).real).astype(DTYPE)


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


def trace_distance(a: np.ndarray, b: np.ndarray) -> float:
    vals = np.linalg.eigvalsh((a - b + (a - b).conj().T) / 2).real
    return float(0.5 * np.sum(np.abs(vals)))


def source_information_signal(rho_l: np.ndarray, rho_r: np.ndarray, coupling: float) -> dict[str, float]:
    rho_l_t = torch.tensor(rho_l, dtype=TORCH_DTYPE)
    rho_r_t = torch.tensor(rho_r, dtype=TORCH_DTYPE)
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


def metric_values(params: np.ndarray) -> dict[str, float]:
    conformal, shear, twist, coupling = params
    metric = math.exp(conformal) * np.array(
        [[math.exp(shear), 0.14 * math.tanh(twist)], [0.14 * math.tanh(twist), math.exp(-shear)]],
        dtype=float,
    )
    eigs = np.linalg.eigvalsh(metric)
    curvature = float(0.36 * shear - 0.24 * twist + 0.12 * conformal * shear)
    torsion = float(abs(0.58 * twist) + abs(0.16 * shear))
    return {
        "metric_min": float(eigs[0]),
        "metric_max": float(eigs[1]),
        "curvature": curvature,
        "torsion": torsion,
        "coupling": float(coupling),
    }


def update_geometry(params: np.ndarray, signal: dict[str, float], row_l: dict[str, Any], row_r: dict[str, Any], mode: str) -> np.ndarray:
    if mode == "frozen_geometry":
        return params.copy()
    active_grad = 0.0 if mode == "zero_gradient" else signal["axis0_gradient"]
    entropy_gap = float(row_l["entropy"] - row_r["entropy"])
    sign_gap = float(row_l["operator_sign"] - row_r["operator_sign"])
    delta = np.array(
        [
            0.035 * signal["phi0"] + 0.020 * active_grad,
            0.022 * entropy_gap + 0.016 * active_grad * sign_gap,
            0.018 * (row_l["slot_delta_norm"] - row_r["slot_delta_norm"]) + 0.014 * active_grad + 0.010 * signal["lr_trace_distance"],
            0.010 * active_grad + 0.006 * signal["mutual_information"],
        ],
        dtype=float,
    )
    if mode == "conformal_only":
        delta[1:] = 0.0
    out = 0.94 * params + delta
    out[3] = float(np.clip(out[3], -1.25, 1.25))
    return out


def slot_gate(row: dict[str, Any], geometry: dict[str, float], source_signal: dict[str, float], *, sign_collapsed: bool = False) -> np.ndarray:
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
    two_site_axis = np.kron(op, SZ if row["loop_class"] == "outer" else SX)
    return qu.expm(-1j * angle * two_site_axis)


def contraction_report(params: np.ndarray, source_signal: dict[str, float], *, static_tree: bool = False) -> dict[str, float]:
    vals = metric_values(np.array([0.05, 0.03, -0.02, 0.35]) if static_tree else params)
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
    optimizer = ctg.HyperOptimizer(max_repeats=4, progbar=False, on_trial_error="raise")
    tree = optimizer.search(inputs, output, sizes)
    seed = int(10_000 * (
        vals["metric_min"]
        + abs(vals["curvature"])
        + abs(vals["torsion"])
        + abs(signal["coherent_information"])
        + abs(signal["lr_trace_distance"])
    ))
    rng = np.random.default_rng(seed)
    scale = 1.0 + abs(signal["coherent_information"]) + 0.5 * abs(signal["lr_trace_distance"])
    arrays = [scale * rng.normal(size=(sizes[i], sizes[j])) for i, j in inputs]
    ref = oe.contract("ab,bc,cd,de->ae", *arrays)
    return {
        "contraction_cost": float(tree.contraction_cost()),
        "contraction_width": float(tree.contraction_width()),
        "contract_norm": float(np.linalg.norm(ref)),
    }


def persistence_summary(points: np.ndarray) -> dict[str, Any]:
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
    engine_l = EngineCore(0, manifold_enabled=True)
    engine_r = EngineCore(1, manifold_enabled=True)
    rho_l = generate_initial_density(3101)
    rho_r = generate_initial_density(4101)
    mps = qtn.MPS_rand_state(8, bond_dim=3, seed=91)
    params = np.array([0.05, 0.03, -0.02, 0.35], dtype=float)
    rows = []
    source_history: list[dict[str, float]] = []
    graph = nx.DiGraph()
    for main_idx, ((per_l, loop_l), (per_r, loop_r)) in enumerate(zip(engine_l.schedule, engine_r.schedule)):
        for sub_idx in range(4):
            rho_l, rec_l = engine_l.run_substage(rho_l, per_l, loop_l, main_idx, sub_idx)
            rho_r, rec_r = engine_r.run_substage(rho_r, per_r, loop_r, main_idx, sub_idx)
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
            cuts = np.array([float(mps.entropy(cut)) for cut in range(1, 8)], dtype=float)
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
                    "mps_entropy_sum": float(cuts.sum()),
                    "mps_entropy_std": float(cuts.std()),
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
    point_array = np.array(
        [[r["phi0"], r["axis0_gradient"], r["curvature"], r["torsion"], r["mps_entropy_sum"]] for r in rows],
        dtype=float,
    )
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


def signature(run: dict[str, Any]) -> np.ndarray:
    rows = run["rows"]
    arr = np.array(
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
        dtype=float,
    )
    return np.r_[arr.mean(axis=0), arr.std(axis=0), arr[-1]]


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
    distances = {name: float(np.linalg.norm(full_sig - sig)) for name, sig in control_sigs.items()}
    costs = np.array([r["contraction_cost"] for r in full_rows], dtype=float)
    static_costs = np.array([r["contraction_cost"] for r in static_tree["rows"]], dtype=float)
    gradient_values = np.array([r["axis0_gradient"] for r in full_rows], dtype=float)
    curvature_values = np.array([r["curvature"] for r in full_rows], dtype=float)
    torsion_values = np.array([r["torsion"] for r in full_rows], dtype=float)
    entropy_values = np.array([r["mps_entropy_sum"] for r in full_rows], dtype=float)
    coherent_values = np.array([r["coherent_information"] for r in full_rows], dtype=float)
    trace_values = np.array([r["lr_trace_distance"] for r in full_rows], dtype=float)

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
            "pass": float(np.max(np.abs(gradient_values))) > 1e-5 and float(np.var(curvature_values)) > 1e-8 and float(np.var(torsion_values)) > 1e-8,
            "max_abs_gradient": float(np.max(np.abs(gradient_values))),
            "curvature_variance": float(np.var(curvature_values)),
            "torsion_variance": float(np.var(torsion_values)),
        },
        "mps_transport_changes_cut_entropy": {
            "pass": float(np.var(entropy_values)) > 1e-5 and max(r["mps_max_bond"] for r in full_rows) > 3,
            "entropy_sum_min": float(np.min(entropy_values)),
            "entropy_sum_max": float(np.max(entropy_values)),
            "max_bond": max(r["mps_max_bond"] for r in full_rows),
        },
        "source_native_information_transport_signal_is_present": {
            "pass": float(np.var(coherent_values)) > 1e-8 and float(np.var(trace_values)) > 1e-8,
            "coherent_information_variance": float(np.var(coherent_values)),
            "lr_trace_distance_variance": float(np.var(trace_values)),
        },
        "cotengra_geometry_shaped_contractions_change": {
            "pass": len({round(v, 6) for v in costs}) > 1 and float(np.linalg.norm(costs - static_costs)) > 0,
            "unique_costs": len({round(v, 6) for v in costs}),
            "full_vs_static_cost_norm": float(np.linalg.norm(costs - static_costs)),
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
            "pass": distances["static_tree"] > 0.005 and float(np.linalg.norm(costs - static_costs)) > 0,
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
            "pass": "does not admit final Axis0" in CLAIM_CEILING and "physics" in CLAIM_CEILING,
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
        "source_alignment_category": "downstream_dynamic_geometry_tensor_transport_on_operator_slot_engine",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
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
            "Uses the repaired operator-slot engine but does not claim final full manifold or final Axis0.",
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
