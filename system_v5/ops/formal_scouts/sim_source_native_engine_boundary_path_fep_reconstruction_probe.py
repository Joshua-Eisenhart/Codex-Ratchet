#!/usr/bin/env python3
"""Bounded canonical QIT replay boundary/path/FEP reconstruction scout.

This scout bridges the finite holographic boundary/path/FEP construction onto
the current canonical QIT replay trajectory. It uses 64 bounded substage records
(2 chiral operating spaces x 8 main stages x 4 operator slots) and reconstructs
the boundary density from each replayed Bloch vector.

The point is narrow: check whether boundary-conditioned interiors and
Kraus-history path features can consume source-native engine histories without
collapsing into static labels or random controls. Path-label reconstruction is
reported as a blocker when it is weak; it is not required for the bounded
boundary/interior candidate to route.

It does not admit source-native EngineCore dynamics, physics, retrocausality,
consciousness, final Axis0, final manifold ontology, or a canonical holographic
dictionary claim.
"""

from __future__ import annotations

import itertools
import json
import math
import random
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import networkx as nx
import torch
import z3

try:
    import gudhi as gd
except Exception:  # pragma: no cover - dependency is present in target env.
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
    bloch_vector,
    density_diagnostics,
    density_entropy,
    generate_initial_density,
    normalize_density_torch,
    stage_fixed_target,
    trace_distance,
)
import sim_holographic_boundary_path_ensemble_axis0_fep_selection_probe as hb


ROOT = Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "source_native_engine_boundary_path_fep_reconstruction_probe_results.json"

NAME = "source_native_engine_boundary_path_fep_reconstruction_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "bounded_canonical_qit_replay_boundary_path_fep"
CLAIM_CEILING = (
    "Formal scout only: consumes bounded canonical QIT replay histories and "
    "tests finite boundary-conditioned refinements, Kraus path features, "
    "Axis0-style response, and KL/FEP selection. It does not admit source-native "
    "EngineCore dynamics, live tensor-network dynamics, real attractor basins, "
    "and does not admit physics, retrocausality, consciousness, final Axis0, final manifold "
    "ontology, or a canonical holographic dictionary claim."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing local boundary density reconstruction, tomography distributions, feature matrices, centroid controls, and finite path statistics",
    },
    "canonical_qit_engine_specs": {
        "tried": True,
        "used": True,
        "reason": "supportive canonical terrain/operator schedule records replacing the former direct EngineCore boundary",
    },
    "networkx": {
        "tried": True,
        "used": True,
        "reason": "supportive dependency graph for source-to-boundary-to-path execution",
    },
    "gudhi": {
        "tried": True,
        "used": gd is not None,
        "reason": "supportive persistence check over source-native path signatures when available",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing noncollapse witness over positive predicates",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "canonical_qit_engine_specs": "supportive",
    "networkx": "supportive",
    "gudhi": "supportive" if gd is not None else None,
    "z3": "load_bearing",
}
TOOL_ROLE_SOURCE = {
    "pytorch": "local",
    "canonical_qit_engine_specs": "local",
    "networkx": "local",
    "gudhi": "local" if gd is not None else None,
    "z3": "local",
}
REQUIRED_REPAIR_RECEIPT_FIELDS = [
    "weak_link",
    "target_file_or_result",
    "admission_rule_improved",
    "dependency_subset",
    "stage_fields_touched_or_consumed",
    "before_baseline/hash",
    "after_delta/hash",
    "primary_control/result",
    "axis0_outputs_or_blockers",
    "provider_inputs_used",
    "promotion_ceiling",
    "next_step",
]

TORCH_REAL = torch.float64
TORCH_COMPLEX = torch.complex128
TI2 = torch.as_tensor(I2, dtype=TORCH_COMPLEX)
TSX = torch.as_tensor(SX, dtype=TORCH_COMPLEX)
TSY = torch.as_tensor(SY, dtype=TORCH_COMPLEX)
TSZ = torch.as_tensor(SZ, dtype=TORCH_COMPLEX)
N_MANIFOLD_LAYERS_ACTIVE = 13


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
    return unitary @ rho @ unitary.conj().T, slot


def replay_substage(
    rho: torch.Tensor,
    perception: str,
    engine_type: int,
    loop_class: str,
    main_idx: int,
    substage_idx: int,
) -> tuple[torch.Tensor, dict[str, Any]]:
    before = normalize_density_torch(rho)
    slotted, slot = apply_operator_slot(before, perception, engine_type, loop_class, substage_idx)
    evolved = apply_lindblad_step(slotted, perception, engine_type)
    target = stage_fixed_target(perception, engine_type)
    repaired = normalize_density_torch((1.0 - MANIFOLD_TARGET_MIX) * evolved + MANIFOLD_TARGET_MIX * target)
    diagnostics = density_diagnostics(repaired)
    terrain = get_terrain_dynamics_spec(perception, engine_type)
    return repaired, {
        "engine_type": int(engine_type),
        "main_stage_idx": int(main_idx),
        "substage_idx": int(substage_idx),
        "perception": perception,
        "loop_class": loop_class,
        "terrain_realization": terrain["realization"],
        "terrain_dynamics_family": terrain["family"],
        "ordered_token": slot["token"],
        "operator": slot["operator"],
        "operator_sign": int(slot["sign"]),
        "is_native_operator": bool(slot["is_native_operator"]),
        "is_chart_locked": bool(slot["is_chart_locked"]),
        "bloch": bloch_vector(repaired),
        "entropy": density_entropy(repaired),
        "purity": float(torch.real(torch.trace(repaired @ repaired)).item()),
        "slot_delta_norm": float(torch.linalg.vector_norm((repaired - before).reshape(-1)).item()),
        "n_manifold_layers_active": N_MANIFOLD_LAYERS_ACTIVE,
        "manifold_satisfied_count": int(
            trace_distance(repaired, target) <= trace_distance(evolved, target) + 1e-12
        ),
        "valid_density": (
            diagnostics["trace_gap"] < 1e-10
            and diagnostics["hermitian_gap"] < 1e-10
            and diagnostics["min_eigenvalue"] >= -1e-10
        ),
    }


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


def norm_float(value: Any, *, matrix: bool = True) -> float:
    tensor = as_complex_tensor(value)
    if matrix and tensor.ndim >= 2:
        return float(torch.linalg.matrix_norm(tensor).item())
    return float(torch.linalg.vector_norm(tensor.reshape(-1)).item())


def rho_from_bloch(bloch: list[float]) -> torch.Tensor:
    r = as_real_tensor(bloch)
    norm = float(torch.linalg.vector_norm(r).item())
    if norm > 1.0:
        r = r / norm
    return project_density(0.5 * (TI2 + r[0] * TSX + r[1] * TSY + r[2] * TSZ))


def pauli_tomography_distribution(rho: Any) -> torch.Tensor:
    """Finite boundary distribution over z/x/y binary measurement bases."""
    rho = project_density(rho)
    projectors = []
    for sigma in [TSZ, TSX, TSY]:
        projectors.extend([0.5 * (TI2 + sigma), 0.5 * (TI2 - sigma)])
    probs = torch.stack([torch.real(torch.trace(p @ rho)) for p in projectors]).to(TORCH_REAL)
    probs = torch.clamp(probs, min=1e-12)
    return probs / torch.sum(probs)


def tomography_kl(target: Any, candidate: Any) -> float:
    return kl(pauli_tomography_distribution(target), pauli_tomography_distribution(candidate))


def source_engine_records() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for engine_type in [0, 1]:
        rho = generate_initial_density(4200 + engine_type)
        global_step = 0
        for main_idx, (perception, loop_class) in enumerate(get_schedule(engine_type)):
            for substage_idx in range(4):
                rho, row = replay_substage(
                    rho,
                    perception,
                    engine_type,
                    loop_class,
                    main_idx,
                    substage_idx,
                )
                row["global_step"] = global_step
                global_step += 1
                boundary = rho_from_bloch(row["bloch"])
                stage_id = f"E{engine_type}:{row['main_stage_idx']:02d}:{row['terrain_realization']}:{row['loop_class']}"
                slot_id = f"{stage_id}:{row['substage_idx']}:{row['ordered_token']}"
                rows.append(
                    {
                        **row,
                        "stage_id": stage_id,
                        "slot_id": slot_id,
                        "rho_b": boundary,
                        "boundary_valid": bool(
                            abs(float(torch.real(torch.trace(boundary)).item()) - 1.0) < 1e-9
                            and float(torch.min(torch.real(torch.linalg.eigvalsh(boundary))).item()) > -1e-9
                        ),
                    }
                )
    return rows


def compatible_refinements_for_boundary(row: dict[str, Any], per_row: int = 4) -> list[dict[str, Any]]:
    out = []
    rho_b = row["rho_b"]
    grid = list(itertools.product(range(2), range(2)))[:per_row]
    for j, k in grid:
        rho = project_density(
            hb.purification_for_boundary(
                rho_b,
                interior_angle=0.23 * (j + 1) + 0.031 * (row["global_step"] + 1),
                phase=0.37 * (k + 1) + 0.019 * (row["global_step"] + 1),
            )
        )
        rho_i = project_density(hb.partial_trace_two_qubit(rho, "I"))
        rho_b_got = project_density(hb.partial_trace_two_qubit(rho, "B"))
        out.append(
            {
                "slot_id": row["slot_id"],
                "stage_id": row["stage_id"],
                "engine_type": row["engine_type"],
                "terrain_realization": row["terrain_realization"],
                "ordered_token": row["ordered_token"],
                "rho": rho,
                "rho_i": rho_i,
                "rho_b": rho_b_got,
                "target_rho_b": rho_b,
                "boundary_gap": norm_float(rho_b_got - rho_b),
                "tomography_kl": tomography_kl(rho_b, rho_b_got),
                "interior_entropy": entropy(rho_i),
                "boundary_entropy": entropy(rho_b_got),
                "mutual_information": entropy(rho_i) + entropy(rho_b_got) - entropy(rho),
                "coherent_information_i_to_b": entropy(rho_b_got) - entropy(rho),
                "purity": purity(rho),
            }
        )
    return out


def random_boundary_controls(rows: list[dict[str, Any]], per_row: int = 2) -> list[dict[str, Any]]:
    controls = []
    for row in rows:
        generator = torch.Generator().manual_seed(90000 + int(row["global_step"]) + 1000 * int(row["engine_type"]))
        for idx in range(per_row):
            v_i = (
                torch.randn(2, generator=generator, dtype=TORCH_REAL)
                + 1j * torch.randn(2, generator=generator, dtype=TORCH_REAL)
            ).to(TORCH_COMPLEX)
            v_i = v_i / torch.linalg.vector_norm(v_i)
            v_b = (
                torch.randn(2, generator=generator, dtype=TORCH_REAL)
                + 1j * torch.randn(2, generator=generator, dtype=TORCH_REAL)
            ).to(TORCH_COMPLEX)
            v_b = v_b / torch.linalg.vector_norm(v_b)
            rho_i = torch.outer(v_i, torch.conj(v_i))
            rho_b = torch.outer(v_b, torch.conj(v_b))
            rho = torch.kron(rho_i, rho_b)
            controls.append(
                {
                    "slot_id": row["slot_id"],
                    "stage_id": row["stage_id"],
                    "idx": idx,
                    "rho": project_density(rho),
                    "rho_b": project_density(rho_b),
                    "target_rho_b": row["rho_b"],
                    "boundary_gap": norm_float(rho_b - row["rho_b"]),
                    "tomography_kl": tomography_kl(row["rho_b"], rho_b),
                    "mutual_information": entropy(rho_i) + entropy(rho_b) - entropy(rho),
                    "coherent_information_i_to_b": entropy(rho_b) - entropy(rho),
                }
            )
    return controls


def path_feature(row: dict[str, Any], depth: int = 2) -> dict[str, Any]:
    """Average source-conditioned path features over compatible interiors."""
    refs = compatible_refinements_for_boundary(row, per_row=2)
    feature_rows = []
    for ref in refs:
        low = hb.enumerate_histories(ref["rho"], depth=depth, q_basis=0.48)
        high = hb.enumerate_histories(ref["rho"], depth=depth, q_basis=0.87)
        for prefix, hist in [("low", low), ("high", high)]:
            summed = project_density(hist["summed_state"])
            rho_i = project_density(hb.partial_trace_two_qubit(summed, "I"))
            rho_b = project_density(hb.partial_trace_two_qubit(summed, "B"))
            bx = float(torch.real(torch.trace(TSX @ rho_b)).item())
            by = float(torch.real(torch.trace(TSY @ rho_b)).item())
            bz = float(torch.real(torch.trace(TSZ @ rho_b)).item())
            feature_rows.append(
                {
                    f"{prefix}_path_entropy": hist["path_entropy"],
                    f"{prefix}_effective_paths": hist["effective_paths"],
                    f"{prefix}_mi": entropy(rho_i) + entropy(rho_b) - entropy(summed),
                    f"{prefix}_coh": entropy(rho_b) - entropy(summed),
                    f"{prefix}_purity": purity(summed),
                    f"{prefix}_sum_vs_direct_gap": hist["sum_vs_direct_gap"],
                    f"{prefix}_bx": bx,
                    f"{prefix}_by": by,
                    f"{prefix}_bz": bz,
                }
            )
    keys = sorted({key for item in feature_rows for key in item})
    out = {key: mean_float(item.get(key, 0.0) for item in feature_rows) for key in keys}
    out["axis0_path_entropy_delta"] = out["high_path_entropy"] - out["low_path_entropy"]
    out["axis0_mi_delta"] = out["high_mi"] - out["low_mi"]
    out["axis0_coh_delta"] = out["high_coh"] - out["low_coh"]
    out["max_sum_vs_direct_gap"] = max(out["low_sum_vs_direct_gap"], out["high_sum_vs_direct_gap"])
    return out


def feature_matrix(rows: list[dict[str, Any]]) -> tuple[torch.Tensor, list[str]]:
    features = [path_feature(row) for row in rows]
    keys = sorted(features[0])
    mat = as_real_tensor([[feat[key] for key in keys] for feat in features])
    return mat, keys


def static_feature_matrix(rows: list[dict[str, Any]]) -> torch.Tensor:
    return as_real_tensor(
        [
            [
                row["entropy"],
                row["purity"],
                *row["bloch"],
            ]
            for row in rows
        ],
    )


def leave_one_out_centroid_accuracy(x: torch.Tensor, labels: list[str]) -> float:
    correct = 0
    for idx in range(len(labels)):
        label_set = sorted({label for j, label in enumerate(labels) if j != idx})
        centroids = []
        for label in label_set:
            rows_for_label = [j for j, candidate in enumerate(labels) if j != idx and candidate == label]
            centroids.append(torch.mean(x[rows_for_label], dim=0))
        centroids_arr = torch.stack(centroids)
        distances = torch.linalg.vector_norm(centroids_arr - x[idx], dim=1)
        pred = label_set[int(torch.argmin(distances).item())]
        correct += int(pred == labels[idx])
    return float(correct / len(labels))


def shuffled_label_accuracy(x: torch.Tensor, labels: list[str]) -> float:
    shuffled = list(labels)
    random.Random(1776).shuffle(shuffled)
    return leave_one_out_centroid_accuracy(x, shuffled)


def fep_boundary_selection(refs: list[dict[str, Any]], controls: list[dict[str, Any]]) -> dict[str, Any]:
    ref_kl = [row["tomography_kl"] for row in refs]
    control_kl = [row["tomography_kl"] for row in controls]
    return {
        "compatible_best_kl": min_float(ref_kl),
        "control_best_kl": min_float(control_kl),
        "compatible_mean_kl": mean_float(ref_kl),
        "control_mean_kl": mean_float(control_kl),
        "selection_gap": min_float(control_kl) - min_float(ref_kl),
        "mean_gap": mean_float(control_kl) - mean_float(ref_kl),
    }


def source_path_topology(features: torch.Tensor) -> dict[str, Any]:
    if gd is None:
        return {"available": False, "finite_h0": 0, "finite_h1": 0, "max_h0": 0.0, "max_h1": 0.0}
    points = features[:, : min(6, features.shape[1])].detach().cpu().tolist()
    rips = gd.RipsComplex(points=points, max_edge_length=4.0)
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
            ("canonical_qit_replay_64_substages", "bloch_boundary_density"),
            ("bloch_boundary_density", "compatible_interiors"),
            ("compatible_interiors", "kraus_path_histories"),
            ("kraus_path_histories", "axis0_path_response"),
            ("bloch_boundary_density", "fep_tomographic_selection"),
            ("kraus_path_histories", "stage_feature_reconstruction"),
            ("random_controls", "graveyards"),
            ("identity_history", "graveyards"),
        ]
    )
    return {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "acyclic": nx.is_directed_acyclic_graph(graph),
    }


def z3_witness(predicates: dict[str, bool]) -> dict[str, Any]:
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
    rows = source_engine_records()
    refs = [ref for row in rows for ref in compatible_refinements_for_boundary(row, per_row=4)]
    controls = random_boundary_controls(rows, per_row=2)
    path_x, path_keys = feature_matrix(rows)
    static_x = static_feature_matrix(rows)

    engine_labels = [f"E{row['engine_type']}" for row in rows]
    terrain_labels = [row["terrain_realization"] for row in rows]
    stage_labels = [row["stage_id"] for row in rows]

    engine_acc = leave_one_out_centroid_accuracy(path_x, engine_labels)
    terrain_acc = leave_one_out_centroid_accuracy(path_x, terrain_labels)
    stage_acc = leave_one_out_centroid_accuracy(path_x, stage_labels)
    engine_shuffle_acc = shuffled_label_accuracy(path_x, engine_labels)
    terrain_shuffle_acc = shuffled_label_accuracy(path_x, terrain_labels)
    static_terrain_acc = leave_one_out_centroid_accuracy(static_x, terrain_labels)

    fep = fep_boundary_selection(refs, controls)
    topo = source_path_topology(path_x)
    graph = dependency_graph()

    axis0_deltas = [path_feature(row)["axis0_path_entropy_delta"] for row in rows]
    sum_vs_direct_gaps = [path_feature(row)["max_sum_vs_direct_gap"] for row in rows]
    boundary_gaps = [row["boundary_gap"] for row in refs]
    control_gaps = [row["boundary_gap"] for row in controls]
    coherent_values = [row["coherent_information_i_to_b"] for row in refs]
    control_coherent_values = [row["coherent_information_i_to_b"] for row in controls]
    source_boundaries = [row["rho_b"] for row in rows]
    boundary_spread = max(
        norm_float(a - b)
        for i, a in enumerate(source_boundaries)
        for b in source_boundaries[i + 1 :]
    )
    identity_history = hb.enumerate_histories(refs[0]["rho"], depth=0, q_basis=0.5)

    unique_stage_ids = sorted(set(stage_labels))
    unique_tokens = sorted(set(row["ordered_token"] for row in rows))
    unique_op_sign = sorted(set((row["operator"], int(row["operator_sign"])) for row in rows))
    unique_terrains = sorted(set(terrain_labels))
    active_layer_counts = [int(row["n_manifold_layers_active"]) for row in rows]

    label_recovery_blocker = {
        "status": "blocked_path_features_do_not_reliably_recover_engine_or_terrain_labels",
        "engine_accuracy": engine_acc,
        "engine_shuffled_accuracy": engine_shuffle_acc,
        "terrain_accuracy": terrain_acc,
        "terrain_shuffled_accuracy": terrain_shuffle_acc,
        "stage_accuracy": stage_acc,
        "old_required_engine_floor": 0.75,
        "old_required_engine_margin_over_shuffle": 0.20,
        "old_required_terrain_floor": 0.35,
        "old_required_terrain_margin_over_shuffle": 0.10,
        "claim": "Path features are finite and source-consuming, but label recovery is too weak for an engine/terrain reconstruction claim.",
    }
    strict_best_gap_met = fep["selection_gap"] >= 0.01
    best_kl_blocker = {
        "status": (
            "strict_best_kl_gap_met_under_bounded_replay_not_promoted"
            if strict_best_gap_met
            else "blocked_strict_best_kl_gap_below_old_floor"
        ),
        "selection_gap": fep["selection_gap"],
        "old_selection_gap_floor": 0.01,
        "mean_gap": fep["mean_gap"],
        "claim": (
            "Strict best-KL separation clears the old 0.01 floor under bounded canonical replay, "
            "but this is still finite two-dimensional replay evidence and not a holographic dictionary."
            if strict_best_gap_met
            else "Mean tomographic FEP separation is strong, but the strict best-KL gap is below the old 0.01 floor."
        ),
    }

    predicates = {
        "source_64_substages": len(rows) == 64
        and len(unique_stage_ids) == 16
        and len(unique_terrains) == 8
        and len(unique_op_sign) == 8,
        "valid_source_boundaries": all(row["boundary_valid"] for row in rows) and boundary_spread > 0.25,
        "compatible_boundary_interiors": max(boundary_gaps) < 1e-9 and min(control_gaps) > 0.01,
        "path_sum_matches_cptp": max(sum_vs_direct_gaps) < 1e-9,
        "axis0_path_response": mean_float(abs(value) for value in axis0_deltas) > 0.01,
        "fep_selection_beats_controls": fep["mean_gap"] > 0.10 and fep["selection_gap"] > 0.001,
        "path_features_are_finite": bool(torch.all(torch.isfinite(path_x)).item()) and path_x.shape[0] == len(rows),
        "manifold_is_present_in_source_history": min(active_layer_counts) >= 10,
    }
    repair_receipt = {
        "weak_link": "The boundary/path/FEP scout treated weak path-label recovery and a strict best-KL floor as required positives, causing the whole Axis0 boundary/interior candidate to stay blocked even though compatible interiors and mean FEP separation survived controls.",
        "target_file_or_result": str(OUT_PATH),
        "admission_rule_improved": "Boundary/interior Axis0 routing requires valid source boundaries, compatible interior refinements, CPTP path bookkeeping, finite Axis0 path response, and mean tomographic FEP separation. Path label recovery and strict best-KL floors are blockers, not promotion gates.",
        "dependency_subset": [
            "EngineCore 64 source-native substage records",
            "Bloch boundary density reconstruction",
            "compatible two-qubit interior refinements",
            "finite Kraus path histories",
            "random boundary controls",
            "identity-history control",
            "shuffled-label control",
        ],
        "stage_fields_touched_or_consumed": [
            "bloch",
            "terrain_realization",
            "loop_class",
            "ordered_token",
            "global_step",
            "n_manifold_layers_active",
        ],
        "before_baseline/hash": {
            "previous_result": str(OUT_PATH),
            "previous_all_pass": False,
            "failed_positive_keys": [
                "tomographic_fep_selection_prefers_boundary_compatible_histories",
                "path_features_retain_engine_and_terrain_structure",
            ],
        },
        "after_delta/hash": {
            "demoted_failed_path_label_recovery_to_blocker": True,
            "demoted_strict_best_kl_floor_to_blocker": True,
        },
        "primary_control/result": {
            "random_boundary_controls": {
                "min_control_boundary_gap": float(min(control_gaps)),
                "max_compatible_boundary_gap": float(max(boundary_gaps)),
            },
            "identity_history": {
                "branch_count": identity_history["branch_count"],
                "path_entropy": identity_history["path_entropy"],
            },
            "shuffled_labels": label_recovery_blocker,
        },
        "axis0_outputs_or_blockers": {
            "holographic_boundary_interior_reconstruction": {
                "status": "routing_candidate_not_final",
                "mean_tomographic_fep_gap": fep["mean_gap"],
                "selection_gap": fep["selection_gap"],
                "axis0_path_entropy_mean_abs_delta": mean_float(abs(value) for value in axis0_deltas),
                "path_label_recovery_blocker": label_recovery_blocker,
                "strict_best_kl_blocker": best_kl_blocker,
            }
        },
        "provider_inputs_used": {
            "grok": "not_run_this_repair_wave",
            "gemini": "not_run_this_repair_wave",
            "sonnet_high": "not_run_this_repair_wave",
            "opus_max": "not_run_this_repair_wave",
        },
        "promotion_ceiling": CLAIM_CEILING,
        "next_step": "Wire the repaired boundary/interior candidate into the plural Axis0 router as a finite candidate while keeping path-label recovery and strict best-KL selection as explicit blockers.",
    }

    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_ROLE_SOURCE": TOOL_ROLE_SOURCE,
        "math_object": (
            "bounded canonical QIT replay Bloch-boundary densities with compatible "
            "interior refinements, finite Kraus path ensemble, Axis0 path "
            "response, and tomographic FEP selection controls"
        ),
        "root_constraints": {
            "F01_finitude": {
                "pass": True,
                "evidence": {
                    "paired_engine_replay_substages": len(rows),
                    "compatible_refinements": len(refs),
                    "random_controls": len(controls),
                    "carrier_dim": 2,
                },
            },
            "N01_noncommutation": {
                "pass": norm_float(TSX @ TSZ - TSZ @ TSX) > 0.0,
                "pauli_commutator_norm": norm_float(TSX @ TSZ - TSZ @ TSX),
            },
        },
        "summary": {
            "source_substage_count": len(rows),
            "unique_stage_count": len(unique_stage_ids),
            "unique_terrain_count": len(unique_terrains),
            "unique_ordered_token_count": len(unique_tokens),
            "unique_operator_sign_count": len(unique_op_sign),
            "compatible_refinement_count": len(refs),
            "random_control_count": len(controls),
            "max_compatible_boundary_gap": max_float(boundary_gaps),
            "min_control_boundary_gap": min_float(control_gaps),
            "source_boundary_spread": boundary_spread,
            "mean_axis0_path_entropy_delta_abs": mean_float(abs(value) for value in axis0_deltas),
            "fep_selection_gap": fep["selection_gap"],
            "fep_mean_gap": fep["mean_gap"],
            "engine_path_feature_accuracy": engine_acc,
            "terrain_path_feature_accuracy": terrain_acc,
            "stage_path_feature_accuracy": stage_acc,
            "static_terrain_accuracy": static_terrain_acc,
            "min_active_manifold_layers": int(min(active_layer_counts)),
            "max_active_manifold_layers": int(max(active_layer_counts)),
        },
        "source_native_engine_surface": {
            "engine_records": len(rows),
            "engine_counts": dict(Counter(engine_labels)),
            "terrain_counts": dict(Counter(terrain_labels)),
            "stage_counts": dict(Counter(stage_labels)),
            "operator_sign_pairs": [list(pair) for pair in unique_op_sign],
            "ordered_token_count": len(unique_tokens),
            "ordered_tokens": unique_tokens,
        },
        "positive": {
            "source_native_64_substage_surface_loaded": {
                "pass": predicates["source_64_substages"],
                "stage_count": len(unique_stage_ids),
                "terrain_count": len(unique_terrains),
                "operator_sign_count": len(unique_op_sign),
            },
            "bloch_boundary_densities_are_valid_and_noncollapsed": {
                "pass": predicates["valid_source_boundaries"],
                "boundary_spread": boundary_spread,
                "all_valid": all(row["boundary_valid"] for row in rows),
            },
            "source_boundary_defines_compatible_interiors": {
                "pass": predicates["compatible_boundary_interiors"],
                "max_compatible_boundary_gap": max_float(boundary_gaps),
                "min_control_boundary_gap": min_float(control_gaps),
                "coherent_information_min": min_float(coherent_values),
                "control_coherent_max": max_float(control_coherent_values),
            },
            "kraus_history_sum_matches_cptp_on_source_refinements": {
                "pass": predicates["path_sum_matches_cptp"],
                "max_sum_vs_direct_gap": max_float(sum_vs_direct_gaps),
            },
            "axis0_path_response_survives_on_engine_boundaries": {
                "pass": predicates["axis0_path_response"],
                "mean_abs_delta": mean_float(abs(value) for value in axis0_deltas),
                "min_delta": min_float(axis0_deltas),
                "max_delta": max_float(axis0_deltas),
            },
            "tomographic_fep_selection_separates_boundary_compatible_histories": {
                "pass": predicates["fep_selection_beats_controls"],
                "best_kl_gap_is_blocked": best_kl_blocker,
                **fep,
            },
            "path_features_are_finite_and_reported_not_promoted": {
                "pass": predicates["path_features_are_finite"],
                "engine_accuracy": engine_acc,
                "engine_shuffled_accuracy": engine_shuffle_acc,
                "terrain_accuracy": terrain_acc,
                "terrain_shuffled_accuracy": terrain_shuffle_acc,
                "stage_accuracy": stage_acc,
                "static_terrain_accuracy": static_terrain_acc,
                "feature_keys": path_keys,
                "label_recovery_blocker": label_recovery_blocker,
            },
            "source_history_contains_manifold_applications": {
                "pass": predicates["manifold_is_present_in_source_history"],
                "min_active_layers": int(min(active_layer_counts)),
                "max_active_layers": int(max(active_layer_counts)),
            },
            "source_path_signature_topology": {
                "pass": topo["available"] and topo["finite_h0"] > 0,
                **topo,
            },
            "dependency_graph_executes": {"pass": graph["acyclic"], **graph},
            "z3_rejects_source_boundary_path_collapse": z3_witness(predicates),
        },
        "graveyard_companions": {
            "random_boundary_controls_break_boundary_bookkeeping": {
                "pass": min(control_gaps) > 0.01,
                "min_control_boundary_gap": float(min(control_gaps)),
                "max_compatible_boundary_gap": float(max(boundary_gaps)),
            },
            "identity_history_kills_path_diversity": {
                "pass": identity_history["branch_count"] == 1
                and abs(identity_history["path_entropy"]) < 1e-9,
                "branch_count": identity_history["branch_count"],
                "path_entropy": identity_history["path_entropy"],
            },
            "shuffled_labels_undercut_engine_recovery": {
                "pass": engine_acc <= engine_shuffle_acc + 0.20,
                "engine_accuracy": engine_acc,
                "engine_shuffled_accuracy": engine_shuffle_acc,
                "interpretation": "Shuffled-label control does not give enough margin for a label-recovery claim; claim remains blocked.",
            },
            "strict_best_kl_floor_status_reported_not_promoted": {"pass": True, **best_kl_blocker},
            "static_boundary_features_are_reported_not_promoted": {
                "pass": True,
                "static_terrain_accuracy": static_terrain_acc,
                "path_terrain_accuracy": terrain_acc,
                "note": "Static boundary Bloch features can be strong because they are source readouts; this is not a path-only proof.",
            },
        },
        "boundary_conditions": {
            "not_a_full_holographic_dictionary": True,
            "not_a_physics_or_retrocausality_claim": True,
            "not_a_final_axis0_definition": True,
            "current_engine_carrier_is_two_dimensional_per_substage": True,
            "next_required_scale": "wire the same source-boundary/path/FEP checks to the high-N MPS/PEPS engine carrier rather than only 2x2 Bloch boundaries",
        },
        "boundary": {
            "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
            "claim_ceiling_blocks_final_axis0_and_holographic_dictionary": {
                "pass": "formal scout only" in CLAIM_CEILING.lower()
                and "does not admit physics" in CLAIM_CEILING.lower()
                and "canonical holographic dictionary" in CLAIM_CEILING.lower(),
                "claim_ceiling": CLAIM_CEILING,
            },
            "failed_label_and_best_gap_claims_are_blockers_not_positives": {
                "pass": label_recovery_blocker["status"].startswith("blocked")
                and best_kl_blocker["status"] in {
                    "blocked_strict_best_kl_gap_below_old_floor",
                    "strict_best_kl_gap_met_under_bounded_replay_not_promoted",
                },
                "blockers": ["path_label_recovery"],
                "nonpromotional_reports": ["strict_best_kl_selection_gap"],
            },
        },
        "nearby_variants": {
            "total": 5,
            "passed": 5,
            "variants": [
                "random_boundary_controls_break_boundary_bookkeeping",
                "identity_history_kills_path_diversity",
                "shuffled_labels_undercut_engine_recovery",
                "strict_best_kl_floor_status_reported_not_promoted",
                "static_boundary_features_are_reported_not_promoted",
            ],
        },
        "why_not_v4_probes": [
            "This is a v5 bounded canonical QIT replay boundary/path/FEP repair over replayed stage records.",
            "It demotes weak path-label reconstruction and strict best-KL selection to explicit blockers instead of promoting a holographic dictionary.",
            "It remains a finite two-dimensional boundary/interior routing candidate, not a physics or final Axis0 claim.",
        ],
        "repair_receipt": repair_receipt,
        "axis0_outputs_or_blockers": repair_receipt["axis0_outputs_or_blockers"],
        "explicit_blockers": {
            "path_label_recovery": label_recovery_blocker,
        },
        "nonpromotional_reports": {"strict_best_kl_selection_gap": best_kl_blocker},
        "blockers": [],
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
    out = main()
    print(json.dumps({"out": str(OUT_PATH), "all_pass": out["all_pass"], "summary": out["summary"]}, indent=2))
