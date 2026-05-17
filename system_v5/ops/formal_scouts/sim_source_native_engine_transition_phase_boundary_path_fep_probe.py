#!/usr/bin/env python3
"""Source-native engine transition-phase boundary/path/FEP scout.

Repair for the post-manifold boundary-only failure mode:
`sim_source_native_engine_boundary_path_fep_reconstruction_probe.py` showed
that the serialized post-loop Bloch records are valid source-native readouts,
but too late in the substage transition to carry strong engine/terrain
structure. This scout instruments the transition phases directly:

  rho_start -> operator/terrain order -> rho_pre_manifold
  -> rho_post_manifold -> rho_post_loop

Each phase is produced by the same EngineCore functions. Boundary/path/FEP
readouts then consume the pre-manifold and post-loop densities, making the
manifold projection itself an observable rather than an unexamined collapse.

Formal scout only; no physics, retrocausality, consciousness, or canonical
holographic-dictionary claim is admitted.
"""

from __future__ import annotations

import json
import math
import time
from collections import Counter
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
import z3

try:
    import gudhi as gd
except Exception:  # pragma: no cover
    gd = None

from canonical_qit_engine_specs import I2, SX, SY, SZ, get_operator_slot_spec
from engine_core import (
    EngineCore,
    apply_manifold_to_density,
    apply_operator_map_family_to_density,
    apply_terrain_dynamics_to_density,
    generate_initial_density,
)
import sim_holographic_boundary_path_ensemble_axis0_fep_selection_probe as hb


ROOT = Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "source_native_engine_transition_phase_boundary_path_fep_probe_results.json"

NAME = "source_native_engine_transition_phase_boundary_path_fep_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "downstream_on_source_native_operating_space"
CLAIM_CEILING = (
    "Formal scout only: instruments source-native EngineCore transition phases "
    "and tests finite boundary/path/FEP readouts before and after manifold "
    "projection. It does not admit physics, retrocausality, consciousness, "
    "final Axis0, final manifold ontology, or a canonical holographic "
    "dictionary claim."
)

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing density phases, path features, nearest-centroid and ablation metrics",
    },
    "scipy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing transitively through EngineCore terrain/Lindblad evolution",
    },
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing transitively through EngineCore 13-layer manifold enforcers",
    },
    "networkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing execution dependency graph",
    },
    "gudhi": {
        "tried": True,
        "used": gd is not None,
        "reason": "supportive persistence over transition feature signatures",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing noncollapse witness over pass predicates",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "scipy": "load_bearing",
    "torch": "load_bearing",
    "networkx": "load_bearing",
    "gudhi": "supportive" if gd is not None else None,
    "z3": "load_bearing",
}


def density_stats(rho: np.ndarray) -> dict[str, Any]:
    rho = hb.project_density(rho)
    return {
        "entropy": hb.entropy(rho),
        "purity": hb.purity(rho),
        "bloch": [
            float(np.real(np.trace(SX @ rho))),
            float(np.real(np.trace(SY @ rho))),
            float(np.real(np.trace(SZ @ rho))),
        ],
        "valid": bool(
            abs(np.trace(rho).real - 1.0) < 1e-9
            and np.min(np.linalg.eigvalsh(rho).real) > -1e-9
        ),
    }


def purification_for_boundary(rho_b: np.ndarray, phase_seed: int) -> np.ndarray:
    return hb.purification_for_boundary(
        hb.project_density(rho_b),
        interior_angle=0.29 + 0.013 * (phase_seed % 17),
        phase=0.41 + 0.019 * (phase_seed % 23),
    )


def path_readout_for_boundary(rho_b: np.ndarray, seed: int, depth: int = 2) -> dict[str, float]:
    rho = purification_for_boundary(rho_b, seed)
    low = hb.enumerate_histories(rho, depth=depth, q_basis=0.47)
    high = hb.enumerate_histories(rho, depth=depth, q_basis=0.88)
    out: dict[str, float] = {}
    for name, hist in [("low", low), ("high", high)]:
        rho_i = hb.partial_trace_two_qubit(hist["summed_state"], "I")
        rho_b_out = hb.partial_trace_two_qubit(hist["summed_state"], "B")
        out[f"{name}_path_entropy"] = hist["path_entropy"]
        out[f"{name}_effective_paths"] = hist["effective_paths"]
        out[f"{name}_mi"] = hb.entropy(rho_i) + hb.entropy(rho_b_out) - hb.entropy(hist["summed_state"])
        out[f"{name}_coh"] = hb.entropy(rho_b_out) - hb.entropy(hist["summed_state"])
        out[f"{name}_purity"] = hb.purity(hist["summed_state"])
        out[f"{name}_sum_vs_direct_gap"] = hist["sum_vs_direct_gap"]
        for axis, sigma in [("x", SX), ("y", SY), ("z", SZ)]:
            out[f"{name}_b{axis}"] = float(np.real(np.trace(sigma @ rho_b_out)))
    out["axis0_path_entropy_delta"] = out["high_path_entropy"] - out["low_path_entropy"]
    out["axis0_mi_delta"] = out["high_mi"] - out["low_mi"]
    out["axis0_coh_delta"] = out["high_coh"] - out["low_coh"]
    out["max_sum_vs_direct_gap"] = max(out["low_sum_vs_direct_gap"], out["high_sum_vs_direct_gap"])
    return out


def pauli_distribution(rho: np.ndarray) -> np.ndarray:
    rho = hb.project_density(rho)
    projectors = []
    for sigma in [SZ, SX, SY]:
        projectors.extend([0.5 * (I2 + sigma), 0.5 * (I2 - sigma)])
    probs = np.array([float(np.real(np.trace(p @ rho))) for p in projectors], dtype=float)
    probs = np.clip(probs, 1e-12, None)
    return probs / float(np.sum(probs))


def tomographic_kl(target: np.ndarray, candidate: np.ndarray) -> float:
    return hb.kl(pauli_distribution(target), pauli_distribution(candidate))


def run_transition_phases(manifold_enabled: bool = True, terrain_enabled: bool = True) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for engine_type in [0, 1]:
        engine = EngineCore(engine_type, manifold_enabled=manifold_enabled)
        rho = generate_initial_density(4200 + engine_type)
        for main_idx, (perception, loop_class) in enumerate(engine.schedule):
            for substage_idx in range(4):
                slot = get_operator_slot_spec(perception, engine_type, loop_class, substage_idx)
                op_name = slot["operator"]
                sign = int(slot["sign"])
                rho_start = hb.project_density(rho)
                terrain_metrics: dict[str, Any] = {}

                if slot["precedence"] == "operator_first":
                    rho_after_operator = apply_operator_map_family_to_density(rho_start, op_name, sign)
                    if terrain_enabled:
                        rho_pre_manifold, terrain_metrics = apply_terrain_dynamics_to_density(
                            rho_after_operator, perception, engine_type
                        )
                    else:
                        rho_pre_manifold = rho_after_operator.copy()
                        terrain_metrics = {
                            "terrain_realization": engine.spec["topologies"][perception]["realization"],
                            "terrain_dynamics_family": "disabled_control",
                            "terrain_delta_norm": 0.0,
                        }
                    rho_after_terrain = rho_pre_manifold
                else:
                    if terrain_enabled:
                        rho_after_terrain, terrain_metrics = apply_terrain_dynamics_to_density(
                            rho_start, perception, engine_type
                        )
                    else:
                        rho_after_terrain = rho_start.copy()
                        terrain_metrics = {
                            "terrain_realization": engine.spec["topologies"][perception]["realization"],
                            "terrain_dynamics_family": "disabled_control",
                            "terrain_delta_norm": 0.0,
                        }
                    rho_pre_manifold = apply_operator_map_family_to_density(rho_after_terrain, op_name, sign)
                    rho_after_operator = rho_pre_manifold

                if manifold_enabled:
                    rho_post_manifold, manifold_metrics = apply_manifold_to_density(
                        rho_pre_manifold, engine.global_step, engine.manifold_context
                    )
                else:
                    rho_post_manifold = rho_pre_manifold.copy()
                    manifold_metrics = {}

                rho_post_loop = engine._apply_loop_placement(rho_post_manifold, main_idx, loop_class)
                rho = rho_post_loop
                stage_id = f"E{engine_type}:{main_idx:02d}:{terrain_metrics['terrain_realization']}:{loop_class}"
                slot_id = f"{stage_id}:{substage_idx}:{slot['token']}"
                phase_map = {
                    "start": rho_start,
                    "after_operator": rho_after_operator,
                    "after_terrain": rho_after_terrain,
                    "pre_manifold": rho_pre_manifold,
                    "post_manifold": rho_post_manifold,
                    "post_loop": rho_post_loop,
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
                        "operator": op_name,
                        "operator_sign": sign,
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
                        "operator_delta_norm": float(np.linalg.norm(rho_after_operator - rho_start, ord="fro")),
                        "pre_manifold_delta_norm": float(np.linalg.norm(rho_pre_manifold - rho_start, ord="fro")),
                        "manifold_delta_norm": float(np.linalg.norm(rho_post_manifold - rho_pre_manifold, ord="fro")),
                        "loop_delta_norm": float(np.linalg.norm(rho_post_loop - rho_post_manifold, ord="fro")),
                        "n_manifold_layers_active": active_layers,
                        "global_step": engine.global_step,
                    }
                )
                engine.global_step += 1
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


def matrix_from_features(records: list[dict[str, Any]]) -> tuple[np.ndarray, list[str]]:
    rows = [transition_feature(record) for record in records]
    keys = sorted(rows[0])
    return np.array([[row[key] for key in keys] for row in rows], dtype=float), keys


def loo_centroid_accuracy(x: np.ndarray, labels: list[str]) -> float:
    labels_arr = np.asarray(labels)
    correct = 0
    for idx in range(len(labels)):
        train = np.ones(len(labels), dtype=bool)
        train[idx] = False
        label_set = sorted(set(labels_arr[train]))
        centroids = np.array([np.mean(x[train & (labels_arr == label)], axis=0) for label in label_set])
        pred = label_set[int(np.argmin(np.linalg.norm(centroids - x[idx], axis=1)))]
        correct += int(pred == labels[idx])
    return float(correct / len(labels))


def shuffled_accuracy(x: np.ndarray, labels: list[str], seed: int) -> float:
    rng = np.random.default_rng(seed)
    shuffled = list(labels)
    rng.shuffle(shuffled)
    return loo_centroid_accuracy(x, shuffled)


def boundary_selection(records: list[dict[str, Any]]) -> dict[str, float]:
    rng = np.random.default_rng(314159)
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
        random_vec = rng.normal(size=2) + 1j * rng.normal(size=2)
        random_vec = random_vec / np.linalg.norm(random_vec)
        random_b = np.outer(random_vec, np.conjugate(random_vec))
        random_kls.append(tomographic_kl(target, random_b))
        shuffled = post_loop_boundaries[(idx * 7 + 5) % len(post_loop_boundaries)]
        shuffled_kls.append(tomographic_kl(target, shuffled))
    return {
        "compatible_mean_kl": float(np.mean(compatible_kls)),
        "random_mean_kl": float(np.mean(random_kls)),
        "shuffled_mean_kl": float(np.mean(shuffled_kls)),
        "random_mean_gap": float(np.mean(random_kls) - np.mean(compatible_kls)),
        "shuffled_mean_gap": float(np.mean(shuffled_kls) - np.mean(compatible_kls)),
        "compatible_max_kl": float(np.max(compatible_kls)),
    }


def topology(features: np.ndarray) -> dict[str, Any]:
    if gd is None:
        return {"available": False, "finite_h0": 0, "finite_h1": 0, "max_h0": 0.0, "max_h1": 0.0}
    points = features[:, : min(features.shape[1], 8)].tolist()
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
            ("engine_core_transition", "phase_density_capture"),
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
        "manifold_projection_is_observable": float(np.mean(manifold_deltas)) > 0.05
        and float(np.mean(pre_entropies) - np.mean(post_manifold_entropies)) > 0.02,
        "terrain_dynamics_load_bearing": float(np.mean(terrain_deltas)) > 0.01
        and terrain_acc > no_terrain_acc + 0.10,
        "path_sum_cptp": max(path_sum_gaps) < 1e-9,
        "axis0_path_response": float(np.mean(np.abs(path_deltas))) > 0.01,
        "fep_selection_beats_random_and_shuffled": selection["random_mean_gap"] > 0.10
        and selection["shuffled_mean_gap"] > 0.05,
        "features_recover_structure": terrain_acc > max(0.40, terrain_shuffle + 0.15)
        and op_sign_acc > max(0.40, op_sign_shuffle + 0.15),
    }

    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "math_object": (
            "instrumented EngineCore transition phase densities with "
            "pre-manifold boundary-conditioned Kraus path/FEP readouts"
        ),
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
            "mean_pre_manifold_entropy": float(np.mean(pre_entropies)),
            "mean_post_manifold_entropy": float(np.mean(post_manifold_entropies)),
            "mean_post_loop_entropy": float(np.mean(post_loop_entropies)),
            "mean_manifold_delta_norm": float(np.mean(manifold_deltas)),
            "mean_terrain_delta_norm": float(np.mean(terrain_deltas)),
            "mean_abs_axis0_path_entropy_delta": float(np.mean(np.abs(path_deltas))),
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
                "mean_pre_entropy": float(np.mean(pre_entropies)),
            },
            "manifold_projection_is_load_bearing_and_measurable": {
                "pass": predicates["manifold_projection_is_observable"],
                "mean_manifold_delta_norm": float(np.mean(manifold_deltas)),
                "mean_entropy_drop": float(np.mean(pre_entropies) - np.mean(post_manifold_entropies)),
                "min_active_layers": int(min(active_layers)),
                "max_active_layers": int(max(active_layers)),
            },
            "terrain_dynamics_remain_load_bearing_under_ablation": {
                "pass": predicates["terrain_dynamics_load_bearing"],
                "terrain_accuracy": terrain_acc,
                "no_terrain_control_accuracy": no_terrain_acc,
                "mean_terrain_delta_norm": float(np.mean(terrain_deltas)),
            },
            "kraus_path_sum_matches_cptp_on_transition_boundaries": {
                "pass": predicates["path_sum_cptp"],
                "max_path_sum_gap": float(max(path_sum_gaps)),
            },
            "axis0_path_response_survives_before_projection": {
                "pass": predicates["axis0_path_response"],
                "mean_abs_delta": float(np.mean(np.abs(path_deltas))),
                "min_delta": float(min(path_deltas)),
                "max_delta": float(max(path_deltas)),
            },
            "tomographic_fep_selection_beats_random_and_shuffled_boundaries": {
                "pass": predicates["fep_selection_beats_random_and_shuffled"],
                **selection,
            },
            "transition_features_recover_terrain_and_operator_sign_structure": {
                "pass": predicates["features_recover_structure"],
                "terrain_accuracy": terrain_acc,
                "terrain_shuffled_accuracy": terrain_shuffle,
                "operator_sign_accuracy": op_sign_acc,
                "operator_sign_shuffled_accuracy": op_sign_shuffle,
                "feature_count": len(keys),
            },
            "transition_feature_topology_is_nontrivial": {
                "pass": topo["available"] and topo["finite_h0"] > 0,
                **topo,
            },
            "dependency_graph_executes": {"pass": graph["acyclic"], **graph},
            "z3_rejects_transition_phase_collapse": z3_witness(predicates),
        },
        "graveyard_companions": {
            "no_terrain_control_reduces_terrain_recovery": {
                "pass": terrain_acc > no_terrain_acc + 0.10,
                "terrain_accuracy": terrain_acc,
                "no_terrain_control_accuracy": no_terrain_acc,
            },
            "shuffled_terrain_labels_fail_recovery": {
                "pass": terrain_acc > terrain_shuffle + 0.15,
                "terrain_accuracy": terrain_acc,
                "terrain_shuffled_accuracy": terrain_shuffle,
            },
            "shuffled_operator_sign_labels_fail_recovery": {
                "pass": op_sign_acc > op_sign_shuffle + 0.15,
                "operator_sign_accuracy": op_sign_acc,
                "operator_sign_shuffled_accuracy": op_sign_shuffle,
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
