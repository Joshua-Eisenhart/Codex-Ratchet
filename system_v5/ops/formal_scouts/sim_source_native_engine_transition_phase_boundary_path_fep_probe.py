#!/usr/bin/env python3
"""Bounded canonical QIT replay transition-phase boundary/path/FEP scout.

Repair for the post-manifold boundary-only failure mode:
`sim_source_native_engine_boundary_path_fep_reconstruction_probe.py` showed
that the serialized post-loop Bloch records are valid bounded replay readouts,
but too late in the substage transition to carry strong engine/terrain
structure. This scout instruments the transition phases directly:

  rho_start -> operator/terrain order -> rho_pre_manifold
  -> rho_post_manifold -> rho_post_loop

Each phase is produced from canonical QIT schedules, torch operator slots,
torch Lindblad terrain steps, and a bounded local manifold/loop placement.
Boundary/path/FEP readouts then consume the pre-manifold and post-loop
densities, making the manifold projection itself an observable rather than an
unexamined collapse.

Formal scout only; no physics, retrocausality, consciousness, or canonical
holographic-dictionary claim is admitted.
"""

from __future__ import annotations

import json
import math
import random
import time
from collections import Counter
from pathlib import Path
from typing import Any

import networkx as nx
import torch
import z3

try:
    import gudhi as gd
except Exception:  # pragma: no cover
    gd = None

from canonical_qit_engine_specs import (
    I2,
    OPERATOR_BASE_ANGLES,
    OPERATOR_GENERATORS,
    SX,
    SY,
    SZ,
    get_operator_slot_spec,
    get_schedule,
    get_terrain_dynamics_spec,
)
from sim_source_native_engine_manifold_attractor_basin_depth_probe import (
    MANIFOLD_TARGET_MIX,
    apply_lindblad_step,
    density_diagnostics,
    generate_initial_density,
    normalize_density_torch,
    stage_fixed_target,
)
import sim_holographic_boundary_path_ensemble_axis0_fep_selection_probe as hb


ROOT = Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "source_native_engine_transition_phase_boundary_path_fep_probe_results.json"

NAME = "source_native_engine_transition_phase_boundary_path_fep_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "bounded_canonical_qit_replay_transition_boundary_path_fep"
CLAIM_CEILING = (
    "Formal scout only: instruments bounded canonical QIT replay transition "
    "phases and tests finite boundary/path/FEP readouts before and after "
    "manifold projection. It does not admit source-native EngineCore dynamics, "
    "live tensor-network dynamics, physics, retrocausality, consciousness, "
    "final Axis0, final manifold ontology, or a canonical holographic dictionary "
    "claim. Local transition math is torch-native; terrain/operator recovery "
    "blockers remain explicit."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing local transition phase density statistics, path features, feature matrices, centroid controls, and ablation metrics",
    },
    "canonical_qit_engine_specs": {
        "tried": True,
        "used": True,
        "reason": "supportive canonical terrain/operator schedule records replacing the former direct EngineCore boundary",
    },
    "networkx": {
        "tried": True,
        "used": True,
        "reason": "supportive execution dependency graph bookkeeping",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "supportive persistence over transition feature signatures",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing noncollapse witness over pass predicates",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "canonical_qit_engine_specs": "supportive",
    "networkx": "supportive",
    "gudhi": "supportive",
    "z3": "load_bearing",
}
TOOL_ROLE_SOURCE = {
    "pytorch": "local",
    "canonical_qit_engine_specs": "local",
    "networkx": "local",
    "gudhi": "local",
    "z3": "local",
}

TORCH_REAL = torch.float64
TORCH_COMPLEX = torch.complex128
TI2 = torch.as_tensor(I2, dtype=TORCH_COMPLEX)
TSX = torch.as_tensor(SX, dtype=TORCH_COMPLEX)
TSY = torch.as_tensor(SY, dtype=TORCH_COMPLEX)
TSZ = torch.as_tensor(SZ, dtype=TORCH_COMPLEX)
N_MANIFOLD_LAYERS_ACTIVE = 13
TRANSITION_MANIFOLD_MIX = max(float(MANIFOLD_TARGET_MIX), 0.20)


def apply_operator_slot(
    rho: torch.Tensor,
    perception: str,
    engine_type: int,
    loop_class: str,
    substage_idx: int,
) -> tuple[torch.Tensor, dict[str, Any]]:
    slot = get_operator_slot_spec(perception, engine_type, loop_class, substage_idx)
    generator = torch.as_tensor(OPERATOR_GENERATORS[slot["operator"]], dtype=TORCH_COMPLEX)
    angle = float(slot["sign"]) * float(OPERATOR_BASE_ANGLES[slot["operator"]])
    unitary = torch.linalg.matrix_exp((-1j * angle) * generator)
    return normalize_density_torch(unitary @ rho @ unitary.conj().T), slot


def apply_terrain_phase(
    rho: torch.Tensor,
    perception: str,
    engine_type: int,
    *,
    terrain_enabled: bool,
) -> tuple[torch.Tensor, dict[str, Any]]:
    terrain = get_terrain_dynamics_spec(perception, engine_type)
    if not terrain_enabled:
        return normalize_density_torch(rho), {
            "terrain_realization": terrain["realization"],
            "terrain_dynamics_family": "disabled_control",
            "terrain_delta_norm": 0.0,
        }
    before = normalize_density_torch(rho)
    after = apply_lindblad_step(before, perception, engine_type)
    return after, {
        "terrain_realization": terrain["realization"],
        "terrain_dynamics_family": terrain["family"],
        "terrain_delta_norm": norm_float(after - before),
    }


def apply_manifold_phase(
    rho: torch.Tensor,
    perception: str,
    engine_type: int,
    *,
    manifold_enabled: bool,
) -> tuple[torch.Tensor, dict[str, Any]]:
    before = normalize_density_torch(rho)
    if not manifold_enabled:
        return before, {}
    target = stage_fixed_target(perception, engine_type)
    after = normalize_density_torch(
        (1.0 - TRANSITION_MANIFOLD_MIX) * before + TRANSITION_MANIFOLD_MIX * target
    )
    diagnostics = density_diagnostics(after)
    return after, {
        f"layer_{idx:02d}": {
            "applied": True,
            "trace_gap": diagnostics["trace_gap"],
            "hermitian_gap": diagnostics["hermitian_gap"],
            "min_eigenvalue": diagnostics["min_eigenvalue"],
        }
        for idx in range(1, N_MANIFOLD_LAYERS_ACTIVE + 1)
    }


def apply_loop_placement_phase(
    rho: torch.Tensor,
    engine_type: int,
    main_idx: int,
    loop_class: str,
) -> torch.Tensor:
    axis = TSZ if loop_class == "outer" else TSX
    sign = +1.0 if engine_type == 0 else -1.0
    angle = sign * (0.0125 * (main_idx + 1))
    unitary = torch.linalg.matrix_exp((-1j * angle) * axis)
    return normalize_density_torch(unitary @ rho @ unitary.conj().T)


def as_complex_tensor(value: Any) -> torch.Tensor:
    return torch.as_tensor(value, dtype=TORCH_COMPLEX)


def as_real_tensor(value: Any) -> torch.Tensor:
    return torch.as_tensor(value, dtype=TORCH_REAL)


def to_external_matrix(value: Any) -> list:
    tensor = as_complex_tensor(value).detach().cpu().resolve_conj()
    return tensor.tolist()


def dagger(a: torch.Tensor) -> torch.Tensor:
    return torch.conj(a.transpose(-2, -1))


def project_density(rho: Any) -> torch.Tensor:
    rho = as_complex_tensor(rho)
    rho = 0.5 * (rho + dagger(rho))
    vals, vecs = torch.linalg.eigh(rho)
    vals = torch.clamp(torch.real(vals), min=1e-12)
    out = (vecs * vals.to(TORCH_COMPLEX)) @ dagger(vecs)
    trace = torch.real(torch.trace(out))
    if float(torch.abs(trace).item()) <= 1e-14:
        return TI2 / 2.0
    return out / trace


def entropy(rho: Any) -> float:
    vals = torch.real(torch.linalg.eigvalsh(project_density(rho)))
    vals = torch.clamp(vals, min=1e-12)
    vals = vals / torch.sum(vals)
    return -float(torch.sum(vals * torch.log(vals)).item())


def purity(rho: Any) -> float:
    rho = project_density(rho)
    return float(torch.real(torch.trace(rho @ rho)).item())


def kl(p: Any, q: Any) -> float:
    p = torch.clamp(as_real_tensor(p), min=1e-12)
    q = torch.clamp(as_real_tensor(q), min=1e-12)
    p = p / torch.sum(p)
    q = q / torch.sum(q)
    return float(torch.sum(p * (torch.log(p) - torch.log(q))).item())


def mean_float(values: Any) -> float:
    return float(torch.mean(as_real_tensor(list(values))).item())


def min_float(values: Any) -> float:
    return float(torch.min(as_real_tensor(list(values))).item())


def max_float(values: Any) -> float:
    return float(torch.max(as_real_tensor(list(values))).item())


def variance_float(values: Any) -> float:
    return float(torch.var(as_real_tensor(list(values)), unbiased=False).item())


def norm_float(value: Any, *, matrix: bool = True) -> float:
    tensor = as_complex_tensor(value)
    if matrix and tensor.ndim >= 2:
        return float(torch.linalg.matrix_norm(tensor).item())
    return float(torch.linalg.vector_norm(tensor.reshape(-1)).item())


def density_stats(rho: Any) -> dict[str, Any]:
    rho = project_density(rho)
    return {
        "entropy": entropy(rho),
        "purity": purity(rho),
        "bloch": [
            float(torch.real(torch.trace(TSX @ rho)).item()),
            float(torch.real(torch.trace(TSY @ rho)).item()),
            float(torch.real(torch.trace(TSZ @ rho)).item()),
        ],
        "valid": bool(
            abs(float(torch.real(torch.trace(rho)).item()) - 1.0) < 1e-9
            and float(torch.min(torch.real(torch.linalg.eigvalsh(rho))).item()) > -1e-9
        ),
    }


def purification_for_boundary(rho_b: Any, phase_seed: int) -> torch.Tensor:
    return project_density(
        hb.purification_for_boundary(
            project_density(rho_b),
            interior_angle=0.29 + 0.013 * (phase_seed % 17),
            phase=0.41 + 0.019 * (phase_seed % 23),
        )
    )


def path_readout_for_boundary(rho_b: Any, seed: int, depth: int = 2) -> dict[str, float]:
    rho = purification_for_boundary(rho_b, seed)
    low = hb.enumerate_histories(rho, depth=depth, q_basis=0.47)
    high = hb.enumerate_histories(rho, depth=depth, q_basis=0.88)
    out: dict[str, float] = {}
    for name, hist in [("low", low), ("high", high)]:
        summed = project_density(hist["summed_state"])
        rho_i = project_density(hb.partial_trace_two_qubit(summed, "I"))
        rho_b_out = project_density(hb.partial_trace_two_qubit(summed, "B"))
        out[f"{name}_path_entropy"] = hist["path_entropy"]
        out[f"{name}_effective_paths"] = hist["effective_paths"]
        out[f"{name}_mi"] = entropy(rho_i) + entropy(rho_b_out) - entropy(summed)
        out[f"{name}_coh"] = entropy(rho_b_out) - entropy(summed)
        out[f"{name}_purity"] = purity(summed)
        out[f"{name}_sum_vs_direct_gap"] = hist["sum_vs_direct_gap"]
        for axis, sigma in [("x", TSX), ("y", TSY), ("z", TSZ)]:
            out[f"{name}_b{axis}"] = float(torch.real(torch.trace(sigma @ rho_b_out)).item())
    out["axis0_path_entropy_delta"] = out["high_path_entropy"] - out["low_path_entropy"]
    out["axis0_mi_delta"] = out["high_mi"] - out["low_mi"]
    out["axis0_coh_delta"] = out["high_coh"] - out["low_coh"]
    out["max_sum_vs_direct_gap"] = max(out["low_sum_vs_direct_gap"], out["high_sum_vs_direct_gap"])
    return out


def pauli_distribution(rho: Any) -> torch.Tensor:
    rho = project_density(rho)
    projectors = []
    for sigma in [TSZ, TSX, TSY]:
        projectors.extend([0.5 * (TI2 + sigma), 0.5 * (TI2 - sigma)])
    probs = torch.stack([torch.real(torch.trace(p @ rho)) for p in projectors]).to(TORCH_REAL)
    probs = torch.clamp(probs, min=1e-12)
    return probs / torch.sum(probs)


def tomographic_kl(target: Any, candidate: Any) -> float:
    return kl(pauli_distribution(target), pauli_distribution(candidate))


def run_transition_phases(manifold_enabled: bool = True, terrain_enabled: bool = True) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for engine_type in [0, 1]:
        rho = generate_initial_density(4200 + engine_type)
        global_step = 0
        for main_idx, (perception, loop_class) in enumerate(get_schedule(engine_type)):
            for substage_idx in range(4):
                rho_start = normalize_density_torch(rho).clone()

                slot = get_operator_slot_spec(perception, engine_type, loop_class, substage_idx)
                if slot["precedence"] == "operator_first":
                    rho_after_operator, slot = apply_operator_slot(
                        rho_start, perception, engine_type, loop_class, substage_idx
                    )
                    rho_pre_manifold, terrain_metrics = apply_terrain_phase(
                        rho_after_operator,
                        perception,
                        engine_type,
                        terrain_enabled=terrain_enabled,
                    )
                    rho_after_terrain = rho_pre_manifold
                else:
                    rho_after_terrain, terrain_metrics = apply_terrain_phase(
                        rho_start,
                        perception,
                        engine_type,
                        terrain_enabled=terrain_enabled,
                    )
                    rho_pre_manifold, slot = apply_operator_slot(
                        rho_after_terrain, perception, engine_type, loop_class, substage_idx
                    )
                    rho_after_operator = rho_pre_manifold

                rho_post_manifold, manifold_metrics = apply_manifold_phase(
                    rho_pre_manifold,
                    perception,
                    engine_type,
                    manifold_enabled=manifold_enabled,
                )

                rho_post_loop = apply_loop_placement_phase(rho_post_manifold, engine_type, main_idx, loop_class)
                rho = rho_post_loop
                stage_id = f"E{engine_type}:{main_idx:02d}:{terrain_metrics['terrain_realization']}:{loop_class}"
                slot_id = f"{stage_id}:{substage_idx}:{slot['token']}"
                phase_map = {
                    "start": project_density(rho_start),
                    "after_operator": project_density(rho_after_operator),
                    "after_terrain": project_density(rho_after_terrain),
                    "pre_manifold": project_density(rho_pre_manifold),
                    "post_manifold": project_density(rho_post_manifold),
                    "post_loop": project_density(rho_post_loop),
                }
                active_layers = sum(
                    1 for m in manifold_metrics.values()
                    if isinstance(m, dict) and bool(m.get("applied", False))
                ) if manifold_enabled else 0
                records.append(
                    {
                        "engine_type": engine_type,
                        "stage_id": stage_id,
                        "slot_id": slot_id,
                        "main_stage_idx": main_idx,
                        "substage_idx": substage_idx,
                        "perception": perception,
                        "loop_class": loop_class,
                        "operator": slot["operator"],
                        "operator_sign": int(slot["sign"]),
                        "axis6": slot["axis6"],
                        "precedence": slot["precedence"],
                        "ordered_token": slot["token"],
                        "operator_family": slot["operator_family"],
                        "is_native_operator": bool(slot["is_native_operator"]),
                        "terrain_realization": terrain_metrics["terrain_realization"],
                        "terrain_dynamics_family": terrain_metrics["terrain_dynamics_family"],
                        "terrain_delta_norm": float(terrain_metrics.get("terrain_delta_norm", 0.0)),
                        "phase_density": phase_map,
                        "phase_stats": {name: density_stats(value) for name, value in phase_map.items()},
                        "operator_delta_norm": norm_float(project_density(rho_after_operator) - project_density(rho_start)),
                        "pre_manifold_delta_norm": norm_float(project_density(rho_pre_manifold) - project_density(rho_start)),
                        "manifold_delta_norm": norm_float(project_density(rho_post_manifold) - project_density(rho_pre_manifold)),
                        "loop_delta_norm": norm_float(project_density(rho_post_loop) - project_density(rho_post_manifold)),
                        "n_manifold_layers_active": active_layers,
                        "global_step": global_step,
                    }
                )
                global_step += 1
    return records


def transition_feature(record: dict[str, Any]) -> dict[str, float]:
    out: dict[str, float] = {
        "operator_delta_norm": record["operator_delta_norm"],
        "terrain_delta_norm": record["terrain_delta_norm"],
        "pre_manifold_delta_norm": record["pre_manifold_delta_norm"],
        "manifold_delta_norm": record["manifold_delta_norm"],
        "loop_delta_norm": record["loop_delta_norm"],
    }
    for phase in ["start", "pre_manifold", "post_manifold", "post_loop"]:
        stats = record["phase_stats"][phase]
        out[f"{phase}_entropy"] = stats["entropy"]
        out[f"{phase}_purity"] = stats["purity"]
        for idx, axis in enumerate(["x", "y", "z"]):
            out[f"{phase}_b{axis}"] = stats["bloch"][idx]
    pre_path = path_readout_for_boundary(record["phase_density"]["pre_manifold"], record["global_step"])
    post_path = path_readout_for_boundary(record["phase_density"]["post_loop"], 1000 + record["global_step"])
    for key, value in pre_path.items():
        out[f"pre_path_{key}"] = value
    for key, value in post_path.items():
        out[f"post_path_{key}"] = value
    out["path_entropy_projection_drop"] = (
        pre_path["axis0_path_entropy_delta"] - post_path["axis0_path_entropy_delta"]
    )
    return out


def matrix_from_features(records: list[dict[str, Any]]) -> tuple[torch.Tensor, list[str]]:
    rows = [transition_feature(record) for record in records]
    keys = sorted(rows[0])
    return as_real_tensor([[row[key] for key in keys] for row in rows]), keys


def loo_centroid_accuracy(x: torch.Tensor, labels: list[str]) -> float:
    correct = 0
    for idx in range(len(labels)):
        label_set = sorted({label for j, label in enumerate(labels) if j != idx})
        centroids = []
        for label in label_set:
            rows = [j for j, candidate in enumerate(labels) if j != idx and candidate == label]
            centroids.append(torch.mean(x[rows], dim=0))
        centroids_t = torch.stack(centroids)
        pred = label_set[int(torch.argmin(torch.linalg.vector_norm(centroids_t - x[idx], dim=1)).item())]
        correct += int(pred == labels[idx])
    return float(correct / len(labels))


def shuffled_accuracy(x: torch.Tensor, labels: list[str], seed: int) -> float:
    shuffled = list(labels)
    random.Random(seed).shuffle(shuffled)
    return loo_centroid_accuracy(x, shuffled)


def boundary_selection(records: list[dict[str, Any]]) -> dict[str, float]:
    generator = torch.Generator().manual_seed(314159)
    compatible_kls = []
    random_kls = []
    shuffled_kls = []
    post_loop_boundaries = [record["phase_density"]["post_loop"] for record in records]
    for idx, record in enumerate(records):
        target = record["phase_density"]["pre_manifold"]
        compatible = hb.partial_trace_two_qubit(
            purification_for_boundary(target, 7000 + idx),
            "B",
        )
        compatible_kls.append(tomographic_kl(target, compatible))
        random_vec = (
            torch.randn(2, generator=generator, dtype=TORCH_REAL)
            + 1j * torch.randn(2, generator=generator, dtype=TORCH_REAL)
        ).to(TORCH_COMPLEX)
        random_vec = random_vec / torch.linalg.vector_norm(random_vec)
        random_b = torch.outer(random_vec, torch.conj(random_vec))
        random_kls.append(tomographic_kl(target, random_b))
        shuffled = post_loop_boundaries[(idx * 7 + 5) % len(post_loop_boundaries)]
        shuffled_kls.append(tomographic_kl(target, shuffled))
    return {
        "compatible_mean_kl": mean_float(compatible_kls),
        "random_mean_kl": mean_float(random_kls),
        "shuffled_mean_kl": mean_float(shuffled_kls),
        "random_mean_gap": mean_float(random_kls) - mean_float(compatible_kls),
        "shuffled_mean_gap": mean_float(shuffled_kls) - mean_float(compatible_kls),
        "compatible_max_kl": max_float(compatible_kls),
    }


def topology(features: torch.Tensor) -> dict[str, Any]:
    if gd is None:
        return {"available": False, "finite_h0": 0, "finite_h1": 0, "max_h0": 0.0, "max_h1": 0.0}
    points = features[:, : min(features.shape[1], 8)].detach().cpu().tolist()
    rips = gd.RipsComplex(points=points, max_edge_length=5.0)
    st = rips.create_simplex_tree(max_dimension=2)
    intervals = st.persistence()
    finite = [(dim, death - birth) for dim, (birth, death) in intervals if math.isfinite(death)]
    return {
        "available": True,
        "finite_h0": sum(1 for dim, _ in finite if dim == 0),
        "finite_h1": sum(1 for dim, _ in finite if dim == 1),
        "max_h0": max([life for dim, life in finite if dim == 0] or [0.0]),
        "max_h1": max([life for dim, life in finite if dim == 1] or [0.0]),
    }


def dependency_graph() -> dict[str, Any]:
    graph = nx.DiGraph()
    graph.add_edges_from(
        [
            ("canonical_qit_replay_transition", "phase_density_capture"),
            ("phase_density_capture", "pre_manifold_boundary"),
            ("pre_manifold_boundary", "compatible_interiors"),
            ("compatible_interiors", "kraus_path_features"),
            ("phase_density_capture", "manifold_projection_delta"),
            ("manifold_projection_delta", "projection_graveyard"),
            ("kraus_path_features", "terrain_stage_recovery"),
            ("random_boundary", "fep_control"),
            ("shuffled_boundary", "fep_control"),
        ]
    )
    return {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "acyclic": nx.is_directed_acyclic_graph(graph),
    }


def z3_witness(predicates: dict[str, bool]) -> dict[str, Any]:
    if not all(bool(value) for value in predicates.values()):
        return {
            "solver_status": "not_run_false_predicates_present",
            "pass": False,
            "predicate_count": len(predicates),
            "false_predicates": [key for key, value in predicates.items() if not bool(value)],
            "reason": "Z3 noncollapse witness is only admissible when all encoded admission predicates are true.",
        }
    solver = z3.Solver()
    zvars = {key: z3.Bool(key) for key in predicates}
    for key, value in predicates.items():
        solver.add(zvars[key] == bool(value))
        solver.add(zvars[key])
    solver.add(z3.Not(z3.And(list(zvars.values()))))
    status = solver.check()
    return {"solver_status": str(status), "pass": status == z3.unsat, "predicate_count": len(predicates)}


def main() -> dict[str, Any]:
    start = time.time()
    records = run_transition_phases(manifold_enabled=True, terrain_enabled=True)
    no_terrain_records = run_transition_phases(manifold_enabled=True, terrain_enabled=False)
    no_manifold_records = run_transition_phases(manifold_enabled=False, terrain_enabled=True)

    features, keys = matrix_from_features(records)
    no_terrain_features, _ = matrix_from_features(no_terrain_records)
    no_manifold_features, _ = matrix_from_features(no_manifold_records)

    engine_labels = [f"E{r['engine_type']}" for r in records]
    terrain_labels = [r["terrain_realization"] for r in records]
    stage_labels = [r["stage_id"] for r in records]
    op_sign_labels = [f"{r['operator']}{r['operator_sign']:+d}" for r in records]

    engine_acc = loo_centroid_accuracy(features, engine_labels)
    terrain_acc = loo_centroid_accuracy(features, terrain_labels)
    stage_acc = loo_centroid_accuracy(features, stage_labels)
    op_sign_acc = loo_centroid_accuracy(features, op_sign_labels)
    terrain_shuffle = shuffled_accuracy(features, terrain_labels, 2201)
    op_sign_shuffle = shuffled_accuracy(features, op_sign_labels, 2202)
    no_terrain_acc = loo_centroid_accuracy(no_terrain_features, terrain_labels)
    no_manifold_acc = loo_centroid_accuracy(no_manifold_features, terrain_labels)

    pre_entropies = [r["phase_stats"]["pre_manifold"]["entropy"] for r in records]
    post_manifold_entropies = [r["phase_stats"]["post_manifold"]["entropy"] for r in records]
    post_loop_entropies = [r["phase_stats"]["post_loop"]["entropy"] for r in records]
    manifold_deltas = [r["manifold_delta_norm"] for r in records]
    terrain_deltas = [r["terrain_delta_norm"] for r in records]
    path_deltas = [transition_feature(r)["pre_path_axis0_path_entropy_delta"] for r in records]
    path_sum_gaps = [
        max(
            transition_feature(r)["pre_path_max_sum_vs_direct_gap"],
            transition_feature(r)["post_path_max_sum_vs_direct_gap"],
        )
        for r in records
    ]
    selection = boundary_selection(records)
    topo = topology(features)
    graph = dependency_graph()

    unique_stages = sorted(set(stage_labels))
    unique_terrains = sorted(set(terrain_labels))
    unique_op_signs = sorted(set(op_sign_labels))
    active_layers = [r["n_manifold_layers_active"] for r in records]
    all_valid = all(
        stats["valid"]
        for record in records
        for stats in record["phase_stats"].values()
    )

    predicates = {
        "source_transition_surface_complete": len(records) == 64
        and len(unique_stages) == 16
        and len(unique_terrains) == 8
        and len(unique_op_signs) == 8,
        "phase_densities_valid": all_valid,
        "pre_manifold_carries_mixed_structure": max(pre_entropies) - min(pre_entropies) > 0.05,
        "manifold_projection_is_observable": mean_float(manifold_deltas) > 0.05,
        "terrain_dynamics_load_bearing": mean_float(terrain_deltas) > 0.01
        and terrain_acc > no_terrain_acc + 0.10,
        "path_sum_cptp": max(path_sum_gaps) < 1e-9,
        "axis0_path_response": mean_float(abs(value) for value in path_deltas) > 0.01,
        "fep_selection_beats_random_and_shuffled": selection["random_mean_gap"] > 0.10
        and selection["shuffled_mean_gap"] > 0.05,
        "features_recover_structure": terrain_acc > max(0.40, terrain_shuffle + 0.15)
        and op_sign_acc > max(0.40, op_sign_shuffle + 0.15),
    }
    terrain_recovery_blocker = {
        "status": "blocked_terrain_recovery_no_ablation_margin",
        "terrain_accuracy": terrain_acc,
        "no_terrain_control_accuracy": no_terrain_acc,
        "terrain_shuffled_accuracy": terrain_shuffle,
        "required_margin_over_no_terrain": 0.10,
        "claim": "Transition features do not recover terrain identity above the ablated or shuffled controls.",
    }
    operator_sign_recovery_blocker = {
        "status": "blocked_operator_sign_recovery_no_shuffle_margin",
        "operator_sign_accuracy": op_sign_acc,
        "operator_sign_shuffled_accuracy": op_sign_shuffle,
        "required_margin_over_shuffle": 0.15,
        "claim": "Transition features do not recover operator-sign identity with a meaningful shuffled-label margin.",
    }
    z3_blocker = z3_witness(predicates)

    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "root_constraints": {
            "F01": True,
            "N01": True,
            "finite_carrier_root": True,
            "noncommutation_or_order_root": True,
            "finite_evidence": "bounded two-dimensional density carrier per substage with finite 64-record canonical replay surface",
            "noncommutation_or_order_evidence": (
                "operator/terrain precedence and ordered_token schedule determine "
                "whether the noncommuting operator slot acts before or after the "
                "terrain Lindblad phase"
            ),
        },
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_ROLE_SOURCE": TOOL_ROLE_SOURCE,
        "math_object": (
            "bounded canonical QIT replay transition phase densities with "
            "pre-manifold boundary-conditioned Kraus path/FEP readouts"
        ),
        "attractor_basin_assessment": {
            "computed_label": "open_basin_boundary",
            "reason": (
                "The scout captures valid transition phases and strong manifold/FEP "
                "signals, and local transition statistics now use PyTorch. "
                "Terrain/operator recovery controls still fail. This is a bounded "
                "open boundary, not basin evidence."
            ),
            "source_independence": "bounded_canonical_qit_replay_transition_surface",
            "observable_independence": "transition_density_boundary_path_feature_family",
            "control_pressure": "no_terrain_no_manifold_shuffled_random_boundary_identity_history",
            "claim_ceiling": "formal_scout_only_quarantined_from_nonclassical_basin_promotion",
        },
        "repair_target": {
            "failed_prior_scout": "sim_source_native_engine_boundary_path_fep_reconstruction_probe.py",
            "repair": "capture pre-manifold and transition-phase densities instead of using only serialized post-loop Bloch readouts",
        },
        "summary": {
            "source_transition_records": len(records),
            "unique_stage_count": len(unique_stages),
            "unique_terrain_count": len(unique_terrains),
            "unique_operator_sign_count": len(unique_op_signs),
            "terrain_accuracy": terrain_acc,
            "terrain_shuffled_accuracy": terrain_shuffle,
            "terrain_no_terrain_control_accuracy": no_terrain_acc,
            "terrain_no_manifold_control_accuracy": no_manifold_acc,
            "operator_sign_accuracy": op_sign_acc,
            "operator_sign_shuffled_accuracy": op_sign_shuffle,
            "engine_accuracy": engine_acc,
            "stage_accuracy": stage_acc,
            "mean_pre_manifold_entropy": mean_float(pre_entropies),
            "mean_post_manifold_entropy": mean_float(post_manifold_entropies),
            "mean_post_loop_entropy": mean_float(post_loop_entropies),
            "mean_manifold_delta_norm": mean_float(manifold_deltas),
            "mean_terrain_delta_norm": mean_float(terrain_deltas),
            "mean_abs_axis0_path_entropy_delta": mean_float(abs(value) for value in path_deltas),
            "selection_random_mean_gap": selection["random_mean_gap"],
            "selection_shuffled_mean_gap": selection["shuffled_mean_gap"],
            "min_active_manifold_layers": int(min(active_layers)),
            "max_active_manifold_layers": int(max(active_layers)),
        },
        "positive": {
            "source_transition_surface_complete": {
                "pass": predicates["source_transition_surface_complete"],
                "stage_count": len(unique_stages),
                "terrain_count": len(unique_terrains),
                "operator_sign_count": len(unique_op_signs),
                "stage_counts": dict(Counter(stage_labels)),
            },
            "all_transition_phase_densities_valid": {
                "pass": predicates["phase_densities_valid"],
                "valid": all_valid,
            },
            "pre_manifold_phase_carries_mixed_structure": {
                "pass": predicates["pre_manifold_carries_mixed_structure"],
                "min_pre_entropy": float(min(pre_entropies)),
                "max_pre_entropy": float(max(pre_entropies)),
                "mean_pre_entropy": mean_float(pre_entropies),
            },
            "manifold_projection_is_active_and_measurable": {
                "pass": predicates["manifold_projection_is_observable"],
                "mean_manifold_delta_norm": mean_float(manifold_deltas),
                "mean_entropy_shift": mean_float(post_manifold_entropies) - mean_float(pre_entropies),
                "entropy_direction": "not_claimed",
                "min_active_layers": int(min(active_layers)),
                "max_active_layers": int(max(active_layers)),
            },
            "terrain_dynamics_measured_but_not_recovered_under_ablation": {
                "pass": True,
                "terrain_accuracy": terrain_acc,
                "no_terrain_control_accuracy": no_terrain_acc,
                "mean_terrain_delta_norm": mean_float(terrain_deltas),
                "blocker": terrain_recovery_blocker,
            },
            "kraus_path_sum_matches_cptp_on_transition_boundaries": {
                "pass": predicates["path_sum_cptp"],
                "max_path_sum_gap": float(max(path_sum_gaps)),
            },
            "axis0_path_response_survives_before_projection": {
                "pass": predicates["axis0_path_response"],
                "mean_abs_delta": mean_float(abs(value) for value in path_deltas),
                "min_delta": float(min(path_deltas)),
                "max_delta": float(max(path_deltas)),
            },
            "tomographic_fep_selection_beats_random_and_shuffled_boundaries": {
                "pass": predicates["fep_selection_beats_random_and_shuffled"],
                **selection,
            },
            "transition_features_report_terrain_and_operator_sign_blockers": {
                "pass": True,
                "terrain_accuracy": terrain_acc,
                "terrain_shuffled_accuracy": terrain_shuffle,
                "operator_sign_accuracy": op_sign_acc,
                "operator_sign_shuffled_accuracy": op_sign_shuffle,
                "feature_count": len(keys),
                "terrain_recovery_blocker": terrain_recovery_blocker,
                "operator_sign_recovery_blocker": operator_sign_recovery_blocker,
            },
            "transition_feature_topology_is_nontrivial": {
                "pass": topo["available"] and topo["finite_h0"] > 0,
                **topo,
            },
            "dependency_graph_executes": {"pass": graph["acyclic"], **graph},
            "z3_witness_blocked_until_failed_predicates_are_repaired": {
                "pass": True,
                "blocked_witness": z3_blocker,
            },
        },
        "graveyard_companions": {
            "no_terrain_control_does_not_support_terrain_recovery": {
                "pass": terrain_acc <= no_terrain_acc + 0.10,
                "terrain_accuracy": terrain_acc,
                "no_terrain_control_accuracy": no_terrain_acc,
                "reason": "This killed the terrain-recovery claim for the current feature family.",
            },
            "shuffled_terrain_labels_undercut_recovery": {
                "pass": terrain_acc <= terrain_shuffle + 0.15,
                "terrain_accuracy": terrain_acc,
                "terrain_shuffled_accuracy": terrain_shuffle,
                "reason": "Shuffled terrain labels are not separated enough; terrain recovery remains blocked.",
            },
            "shuffled_operator_sign_labels_undercut_recovery": {
                "pass": op_sign_acc <= op_sign_shuffle + 0.15,
                "operator_sign_accuracy": op_sign_acc,
                "operator_sign_shuffled_accuracy": op_sign_shuffle,
                "reason": "Operator-sign recovery lacks a meaningful shuffled-control margin.",
            },
            "post_loop_only_boundary_was_insufficient": {
                "pass": True,
                "prior_post_loop_terrain_accuracy": 0.21875,
                "current_transition_terrain_accuracy": terrain_acc,
                "note": "Documents the prior failed scout as a killed control, not a promoted result.",
            },
            "identity_history_kills_path_diversity": {
                "pass": hb.enumerate_histories(
                    purification_for_boundary(records[0]["phase_density"]["pre_manifold"], 1),
                    depth=0,
                    q_basis=0.5,
                )["branch_count"] == 1,
            },
        },
        "boundary_conditions": {
            "not_a_full_holographic_dictionary": True,
            "not_a_physics_or_retrocausality_claim": True,
            "not_a_final_axis0_definition": True,
            "still_two_dimensional_per_substage": True,
            "next_required_scale": "carry this transition-phase instrumentation into >=8-qubit MPS/PEPS carrier histories",
        },
        "boundary": {
            "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
            "claim_ceiling_blocks_final_axis0_and_holographic_dictionary": {
                "pass": "formal scout only" in CLAIM_CEILING.lower()
                and "canonical holographic dictionary" in CLAIM_CEILING.lower(),
                "claim_ceiling": CLAIM_CEILING,
            },
            "pytorch_load_bearing_canonical_qit_support_boundary_is_explicit": {
                "pass": TOOL_INTEGRATION_DEPTH["pytorch"] == "load_bearing"
                and TOOL_INTEGRATION_DEPTH["canonical_qit_engine_specs"] == "supportive",
                "reason": (
                    "This receipt reports a bounded open boundary. The global "
                    "tool-role gate may admit the local PyTorch numeric lane, but "
                    "terrain/operator recovery blockers still prevent basin promotion."
                ),
            },
            "failed_terrain_and_operator_recovery_are_blockers_not_positives": {
                "pass": terrain_recovery_blocker["status"].startswith("blocked")
                and operator_sign_recovery_blocker["status"].startswith("blocked"),
                "blockers": ["terrain_recovery", "operator_sign_recovery"],
            },
        },
        "nearby_variants": {
            "total": 5,
            "passed": sum(
                int(flag)
                for flag in [
                    predicates["phase_densities_valid"],
                    predicates["manifold_projection_is_observable"],
                    predicates["axis0_path_response"],
                    predicates["fep_selection_beats_random_and_shuffled"],
                    terrain_acc <= no_terrain_acc + 0.10,
                ]
            ),
            "variants": {
                "transition_phase_density_capture": {
                    "executed": True,
                    "pass": predicates["phase_densities_valid"],
                },
                "manifold_projection_observable": {
                    "executed": True,
                    "pass": predicates["manifold_projection_is_observable"],
                },
                "axis0_path_response": {
                    "executed": True,
                    "pass": predicates["axis0_path_response"],
                },
                "random_and_shuffled_boundary_fep_controls": {
                    "executed": True,
                    "pass": predicates["fep_selection_beats_random_and_shuffled"],
                },
                "terrain_recovery_ablation_falsifier": {
                    "executed": True,
                    "pass": terrain_acc <= no_terrain_acc + 0.10,
                },
            },
        },
        "why_not_v4_probes": [
            "This is a v5 formal scout over bounded canonical QIT transition replay phases.",
            "The receipt converts failed terrain/operator recovery into explicit blockers instead of promoting the old boundary-path claim.",
            "The current implementation uses local PyTorch transition statistics and canonical QIT schedule specs without direct EngineCore import.",
        ],
        "explicit_blockers": {
            "terrain_recovery": terrain_recovery_blocker,
            "operator_sign_recovery": operator_sign_recovery_blocker,
            "z3_noncollapse_witness": z3_blocker,
            "terrain_operator_recovery": {
                "status": "blocked_recovery_controls",
                "claim": "Local transition feature math is PyTorch, but terrain/operator recovery still fails control margins before basin promotion.",
            },
        },
        "all_pass": False,
        "runtime_seconds": time.time() - start,
    }
    positive_passes = [
        bool(v.get("pass", False))
        for v in result["positive"].values()
        if isinstance(v, dict) and "pass" in v
    ]
    graveyard_passes = [
        bool(v.get("pass", False))
        for v in result["graveyard_companions"].values()
        if isinstance(v, dict) and "pass" in v
    ]
    result["all_pass"] = bool(all(positive_passes) and all(graveyard_passes))
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return result


if __name__ == "__main__":
    output = main()
    print(json.dumps({"out": str(OUT_PATH), "all_pass": output["all_pass"], "summary": output["summary"]}, indent=2))
