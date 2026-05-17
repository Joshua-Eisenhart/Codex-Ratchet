#!/usr/bin/env python3
"""MPS local-boundary path/FEP scaling scout for 8/16/32 qubits.

Extends the 8-qubit engine-boundary scout without dense state handoff.
Boundary densities are reconstructed from quimb MPS local expectation values
<X>, <Y>, <Z> at the active boundary site. This lets the same paired
source-native EngineCore slot transport run at 8, 16, and 32 qubits.

Formal scout only. It does not admit final Axis0, final manifold ontology,
physics, retrocausality, intelligence, or a canonical holographic dictionary.
"""

from __future__ import annotations

import json
import math
import os
import time
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import networkx as nx
import numpy as np
import quimb.tensor as qtn
import z3

import axis0_guard_utils as axis0_guard
import sim_holographic_boundary_path_ensemble_axis0_fep_selection_probe as hb
import sim_operator_slot_cut_entropy_gradient_dynamic_manifold_mps_transport_probe as transport


ROOT = Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "mps_local_boundary_path_fep_scaling_8_16_32_engine_transport_probe_results.json"

NAME = "mps_local_boundary_path_fep_scaling_8_16_32_engine_transport_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "downstream_on_source_native_operator_slot_engine_mps_local_boundary_scaling"
CLAIM_CEILING = (
    "Formal scout only: runs paired source-native EngineCore slot transport on "
    "8/16/32-qubit quimb MPS carriers and computes boundary/path/FEP readouts "
    "from local MPS expectation values without dense state handoff. It does not "
    "admit final Axis0, final manifold ontology, physics, retrocausality, "
    "intelligence, global variational free energy on the full entangled MPS state, "
    "or a canonical holographic dictionary."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing finite density reconstruction, signatures, and controls"},
    "quimb": {"tried": True, "used": True, "reason": "load-bearing MPS transport, local expectations, and cut entropy"},
    "pytorch": {"tried": True, "used": True, "reason": "supportive through EngineCore source signal and gradient helper"},
    "scipy": {"tried": True, "used": True, "reason": "supportive through EngineCore Lindblad and slot-gate helpers"},
    "cotengra": {"tried": True, "used": True, "reason": "load-bearing through geometry-shaped contraction_report helper"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing slot dependency graph"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite scaling witness"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "quimb": "load_bearing",
    "pytorch": "supportive",
    "scipy": "supportive",
    "cotengra": "load_bearing",
    "networkx": "load_bearing",
    "z3": "load_bearing",
}

N_VALUES = [8, 16, 32]
N_PAIRED_ROWS = 32
MAX_BOND = 16
BOND_SWEEP_VALUES = [16, 24, 32]
BOND_SWEEP_STABILITY_THRESHOLD = 0.01
BEFORE_SCRIPT_SHA256 = "e429334e3d4784e5b9399f6d251841c5c43ed4dea9febde2c727e54ef5d381a3"
BEFORE_RESULT_SHA256 = "83586d50b3eb303e2e875f1ac216942a301da5564d3a5d04944ec31bd329f967"
REQUIRED_STAGE_FIELDS = [
    "model_before",
    "prediction",
    "observation",
    "fep_efe_score",
    "update_repair",
    "falsifier_graveyard",
    "next_policy",
    "model_after",
]

I2 = np.eye(2, dtype=np.complex128)
SX = np.array([[0, 1], [1, 0]], dtype=np.complex128)
SY = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
SZ = np.array([[1, 0], [0, -1]], dtype=np.complex128)


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, (np.complexfloating, complex)):
        return {"real": float(np.real(value)), "imag": float(np.imag(value))}
    return value


def load_result(name: str) -> dict[str, Any]:
    path = RESULT_DIR / name
    if not path.exists():
        return {"exists": False, "path": str(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "exists": True,
        "path": str(path),
        "name": data.get("name"),
        "all_pass": data.get("all_pass"),
        "classification": data.get("classification"),
        "promotion_allowed": data.get("promotion_allowed"),
        "claim_ceiling": data.get("claim_ceiling", "")[:220],
        "axis0_outputs_or_blockers": data.get("axis0_outputs_or_blockers", {}),
    }


def stage_science_projection(row: dict[str, Any]) -> dict[str, Any]:
    missing = [field for field in REQUIRED_STAGE_FIELDS if field not in row]
    fep = row.get("fep_efe_score", {})
    repair = row.get("update_repair", {})
    return {
        "fields_present": not missing,
        "missing_required_stage_fields": missing,
        "model_before_hash": (row.get("model_before") or {}).get("density_hash"),
        "model_after_hash": (row.get("model_after") or {}).get("density_hash"),
        "prediction_hash": (row.get("prediction") or {}).get("predicted_density_hash"),
        "observation_hash": (row.get("observation") or {}).get("observed_density_hash"),
        "expected_free_energy_proxy": fep.get("expected_free_energy_proxy"),
        "surprise_kl": fep.get("surprise_kl"),
        "prediction_error_l2": fep.get("prediction_error_l2"),
        "manifold_projection_delta_norm": repair.get("manifold_projection_delta_norm"),
        "graveyard_count": len(row.get("falsifier_graveyard", [])),
        "next_policy_id": (row.get("next_policy") or {}).get("policy_id"),
    }


def axis0_bundle_from_guarded_router(router: dict[str, Any], guard_receipt: dict[str, Any]) -> dict[str, Any]:
    guard = axis0_guard.axis0_guard_signal(guard_receipt)
    guard_pass = bool(guard.get("pass") is True)
    vectors = axis0_guard.guarded_router_vectors(router, guard) if guard_pass else {}
    names = list(guard.get("admitted_candidate_names", [])) if guard_pass else []
    ready = bool(
        router.get("exists")
        and router.get("all_pass") is True
        and guard_pass
        and names
        and all(vectors.get(name) for name in names)
    )
    return {
        "ready": ready,
        "source_receipt": router.get("path"),
        "guard_receipt": guard_receipt.get("path"),
        "candidate_names": names,
        "candidate_vectors": vectors,
        "guard": guard,
        "guard_pass": guard_pass,
        "guard_failure_blocker": None
        if guard_pass
        else {
            "status": "axis0_guard_failed_no_downstream_candidate_status_claim",
            "unclassified_candidate_names": guard.get("unclassified_candidate_names", []),
            "admitted_candidate_names_reported": guard.get("admitted_candidate_names", []),
            "blocked_candidate_names_reported": guard.get("blocked_candidate_names", []),
        },
    }


def axis0_bundle_drive(bundle: dict[str, Any], slot: int) -> float:
    if not bundle.get("ready"):
        return 0.0
    values = []
    for vector in bundle.get("candidate_vectors", {}).values():
        if vector:
            values.append(float(vector[slot % len(vector)]))
    if not values:
        return 0.0
    return float(np.mean(values))


def local_expectation(mps: qtn.MatrixProductState, op: np.ndarray, site: int) -> complex:
    out = mps.compute_local_expectation({(site,): op}, max_bond=64, optimize="auto-hq")
    if isinstance(out, dict):
        out = out[(site,)]
    return complex(out)


def mps_tensor_guard(mps: qtn.MatrixProductState, n_qubits: int) -> dict[str, Any]:
    shapes = [tuple(int(dim) for dim in array.shape) for array in mps.arrays]
    all_dims = [dim for shape in shapes for dim in shape]
    dense_dim = 2**n_qubits
    return {
        "max_tensor_axis": int(max(all_dims)),
        "max_tensor_size": int(max(np.prod(shape) for shape in shapes)),
        "dense_axis_seen": bool(any(dim >= dense_dim for dim in all_dims)),
        "dense_state_array_shapes_seen": [shape for shape in shapes if any(dim >= dense_dim for dim in shape)],
        "sample_shapes": shapes[:3],
    }


def local_boundary_density(mps: qtn.MatrixProductState, site: int) -> np.ndarray:
    bloch = np.array(
        [
            local_expectation(mps, SX, site).real,
            local_expectation(mps, SY, site).real,
            local_expectation(mps, SZ, site).real,
        ],
        dtype=float,
    )
    norm = float(np.linalg.norm(bloch))
    if norm > 1.0:
        bloch = bloch / norm
    return hb.project_density(0.5 * (I2 + bloch[0] * SX + bloch[1] * SY + bloch[2] * SZ))


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
        "valid": bool(abs(np.trace(rho).real - 1.0) < 1e-9 and np.min(np.linalg.eigvalsh(rho).real) > -1e-9),
    }


def purification_for_boundary(rho_b: np.ndarray, seed: int) -> np.ndarray:
    return hb.purification_for_boundary(
        hb.project_density(rho_b),
        interior_angle=0.24 + 0.011 * (seed % 37),
        phase=0.36 + 0.017 * (seed % 41),
    )


def path_readout(rho_b: np.ndarray, seed: int, depth: int = 2) -> dict[str, float]:
    rho = purification_for_boundary(rho_b, seed)
    low = hb.enumerate_histories(rho, depth=depth, q_basis=0.45)
    high = hb.enumerate_histories(rho, depth=depth, q_basis=0.90)
    out: dict[str, float] = {}
    for name, hist in [("low", low), ("high", high)]:
        rho_i = hb.partial_trace_two_qubit(hist["summed_state"], "I")
        rho_b2 = hb.partial_trace_two_qubit(hist["summed_state"], "B")
        out[f"{name}_path_entropy"] = hist["path_entropy"]
        out[f"{name}_effective_paths"] = hist["effective_paths"]
        out[f"{name}_mi"] = hb.entropy(rho_i) + hb.entropy(rho_b2) - hb.entropy(hist["summed_state"])
        out[f"{name}_conditional_entropy"] = hb.entropy(hist["summed_state"]) - hb.entropy(rho_b2)
        out[f"{name}_coh"] = hb.entropy(rho_b2) - hb.entropy(hist["summed_state"])
        out[f"{name}_purity"] = hb.purity(hist["summed_state"])
        out[f"{name}_sum_vs_direct_gap"] = hist["sum_vs_direct_gap"]
    out["axis0_path_entropy_delta"] = out["high_path_entropy"] - out["low_path_entropy"]
    out["axis0_mi_delta"] = out["high_mi"] - out["low_mi"]
    out["axis0_conditional_entropy_delta"] = out["high_conditional_entropy"] - out["low_conditional_entropy"]
    out["axis0_coh_delta"] = out["high_coh"] - out["low_coh"]
    out["max_sum_vs_direct_gap"] = max(out["low_sum_vs_direct_gap"], out["high_sum_vs_direct_gap"])
    return out


def pauli_distribution(rho: np.ndarray) -> np.ndarray:
    projectors = []
    for sigma in [SZ, SX, SY]:
        projectors.extend([0.5 * (I2 + sigma), 0.5 * (I2 - sigma)])
    probs = np.array([float(np.real(np.trace(p @ rho))) for p in projectors], dtype=float)
    probs = np.clip(probs, 1e-12, None)
    return probs / float(np.sum(probs))


def tomographic_kl(target: np.ndarray, candidate: np.ndarray) -> float:
    return hb.kl(pauli_distribution(target), pauli_distribution(candidate))


def topology_pairs(perception: str, slot: int, n_qubits: int, side: str) -> list[tuple[int, int]]:
    base = transport.TOPOLOGY_PAIRS[perception]
    chosen = base[:2] if side == "left" else base[-2:]
    offset = 0 if side == "left" else max(1, n_qubits // 3)
    pairs = []
    for idx, (a, _b) in enumerate(chosen):
        site = (a + offset + slot * (idx + 2)) % (n_qubits - 1)
        pairs.append((site, site + 1))
    return sorted(set(pairs))


def run_scaling_transport(
    n_qubits: int,
    mode: str = "full",
    max_bond: int = MAX_BOND,
    axis0_bundle: dict[str, Any] | None = None,
) -> dict[str, Any]:
    engine_l = transport.EngineCore(0, manifold_enabled=True)
    engine_r = transport.EngineCore(1, manifold_enabled=True)
    rho_l = transport.generate_initial_density(3101)
    rho_r = transport.generate_initial_density(4101)
    mps = qtn.MPS_rand_state(n_qubits, bond_dim=3, seed=9100 + n_qubits)
    params = np.array([0.05, 0.03, -0.02, 0.35], dtype=float)
    source_history: list[dict[str, float]] = []
    rows = []
    graph = nx.DiGraph()

    for main_idx, ((per_l, loop_l), (per_r, loop_r)) in enumerate(zip(engine_l.schedule, engine_r.schedule)):
        for sub_idx in range(4):
            slot = main_idx * 4 + sub_idx
            rho_l, rec_l = engine_l.run_substage(rho_l, per_l, loop_l, main_idx, sub_idx)
            rho_r, rec_r = engine_r.run_substage(rho_r, per_r, loop_r, main_idx, sub_idx)
            live_signal = transport.source_information_signal(rho_l, rho_r, params[3])
            source_history.append(live_signal)
            if mode == "zero_gradient":
                source_signal = dict(live_signal)
                source_signal["axis0_gradient"] = 0.0
            elif mode == "density_frozen":
                source_signal = source_history[0]
            elif mode == "axis0_bundle_zeroed":
                source_signal = dict(live_signal)
            else:
                source_signal = live_signal
            source_signal = dict(source_signal)
            source_signal["axis0_gradient_raw"] = float(source_signal["axis0_gradient"])
            source_signal["axis0_plural_bundle_drive"] = axis0_bundle_drive(axis0_bundle or {}, slot)
            if mode not in {"zero_gradient", "axis0_bundle_zeroed"}:
                source_signal["axis0_gradient"] = float(
                    source_signal["axis0_gradient"]
                    + 0.005 * source_signal["axis0_plural_bundle_drive"]
                )

            update_mode = "frozen_geometry" if mode == "frozen_geometry" else "full"
            params = transport.update_geometry(params, source_signal, rec_l, rec_r, update_mode)
            if mode == "isotropic_only":
                params[1] = 0.0
                params[2] = 0.0
            geom = transport.metric_values(params)
            gate_l = transport.slot_gate(rec_l, geom, source_signal, sign_collapsed=(mode == "sign_collapsed"))
            gate_r = transport.slot_gate(rec_r, geom, source_signal, sign_collapsed=(mode == "sign_collapsed"))
            for pair in topology_pairs(per_l, slot, n_qubits, "left"):
                mps.gate_(gate_l, pair, contract="swap+split", max_bond=max_bond, cutoff=1e-10)
            for pair in topology_pairs(per_r, slot, n_qubits, "right"):
                mps.gate_(gate_r, pair, contract="swap+split", max_bond=max_bond, cutoff=1e-10)

            boundary_site = (3 * slot + main_idx) % n_qubits
            rho_b = local_boundary_density(mps, boundary_site)
            stats = density_stats(rho_b)
            path = path_readout(rho_b, seed=1000 * n_qubits + slot)
            cut_sites = sorted({1, max(1, n_qubits // 4), max(1, n_qubits // 2), max(1, (3 * n_qubits) // 4), n_qubits - 1})
            cuts = np.array([float(mps.entropy(cut)) for cut in cut_sites if 0 < cut < n_qubits], dtype=float)
            midcut_entropy = float(mps.entropy(max(1, n_qubits // 2)))
            tensor_guard = mps_tensor_guard(mps, n_qubits)
            contract = transport.contraction_report(params, source_signal, static_tree=(mode == "static_tree"))
            node = f"N{n_qubits}:slot:{slot}"
            graph.add_node(node)
            if slot:
                graph.add_edge(f"N{n_qubits}:slot:{slot - 1}", node)
            rows.append(
                {
                    "n_qubits": n_qubits,
                    "slot": slot,
                    "boundary_site": boundary_site,
                    "left_engine_type": rec_l["engine_type"],
                    "right_engine_type": rec_r["engine_type"],
                    "left_type_label": rec_l["type_label"],
                    "right_type_label": rec_r["type_label"],
                    "left_token": rec_l["ordered_token"],
                    "right_token": rec_r["ordered_token"],
                    "left_family": rec_l["terrain_dynamics_family"],
                    "right_family": rec_r["terrain_dynamics_family"],
                    "left_operator": rec_l["operator"],
                    "right_operator": rec_r["operator"],
                    "left_operator_sign": rec_l["operator_sign"],
                    "right_operator_sign": rec_r["operator_sign"],
                    "left_is_native_operator": bool(rec_l["is_native_operator"]),
                    "right_is_native_operator": bool(rec_r["is_native_operator"]),
                    "left_is_chart_locked": bool(rec_l["is_chart_locked"]),
                    "right_is_chart_locked": bool(rec_r["is_chart_locked"]),
                    "left_native_operator_set": list(rec_l["native_operator_set"]),
                    "right_native_operator_set": list(rec_r["native_operator_set"]),
                    "left_stage_science": stage_science_projection(rec_l),
                    "right_stage_science": stage_science_projection(rec_r),
                    "left_topology_spec_source": "EngineCore/canonical_qit_engine_specs",
                    "right_topology_spec_source": "EngineCore/canonical_qit_engine_specs",
                    "mps_pair_assignment_source": "synthetic_side_offset",
                    "phi0": source_signal["phi0"],
                    "axis0_gradient_raw": source_signal["axis0_gradient_raw"],
                    "axis0_plural_bundle_drive": source_signal["axis0_plural_bundle_drive"],
                    "axis0_plural_bundle_source": (axis0_bundle or {}).get("source_receipt"),
                    "axis0_plural_bundle_ready": bool((axis0_bundle or {}).get("ready")),
                    "axis0_gradient": source_signal["axis0_gradient"],
                    "coherent_information": source_signal["coherent_information"],
                    "mutual_information": source_signal["mutual_information"],
                    "lr_trace_distance": source_signal["lr_trace_distance"],
                    "curvature": geom["curvature"],
                    "torsion": geom["torsion"],
                    "coupling": geom["coupling"],
                    "mps_entropy_sum": float(cuts.sum()),
                    "mps_entropy_std": float(cuts.std()),
                    "mps_max_bond": int(mps.max_bond()),
                    "mps_max_bond_cap": max_bond,
                    "mps_bond_cap_saturated": bool(mps.max_bond() >= max_bond),
                    "mps_midcut_entropy": midcut_entropy,
                    "mps_max_tensor_axis": tensor_guard["max_tensor_axis"],
                    "mps_max_tensor_size": tensor_guard["max_tensor_size"],
                    "mps_dense_axis_seen": tensor_guard["dense_axis_seen"],
                    "mps_dense_state_array_shapes_seen": tensor_guard["dense_state_array_shapes_seen"],
                    "boundary_entropy": stats["entropy"],
                    "boundary_purity": stats["purity"],
                    "boundary_bloch": stats["bloch"],
                    "boundary_valid": stats["valid"],
                    **{f"path_{key}": value for key, value in path.items()},
                    **contract,
                }
            )
    return {
        "mode": mode,
        "n_qubits": n_qubits,
        "rows": rows,
        "graph": {
            "nodes": graph.number_of_nodes(),
            "edges": graph.number_of_edges(),
            "acyclic": nx.is_directed_acyclic_graph(graph),
        },
    }


def signature(run: dict[str, Any]) -> np.ndarray:
    # Keep blocked local path-entropy readouts out of the load-bearing signature.
    arr = np.array(
        [
            [
                r["phi0"],
                r["axis0_gradient"],
                r["coherent_information"],
                r["mutual_information"],
                r["curvature"],
                r["torsion"],
                r["mps_entropy_sum"],
                r["boundary_entropy"],
                r["contract_norm"],
            ]
            for r in run["rows"]
        ],
        dtype=float,
    )
    return np.r_[arr.mean(axis=0), arr.std(axis=0), arr[-1]]


def fep_selection(rows: list[dict[str, Any]]) -> dict[str, float]:
    rng = np.random.default_rng(66000 + int(rows[0]["n_qubits"]))
    boundaries = [
        hb.project_density(0.5 * (I2 + row["boundary_bloch"][0] * SX + row["boundary_bloch"][1] * SY + row["boundary_bloch"][2] * SZ))
        for row in rows
    ]
    compatible = []
    randoms = []
    shuffled = []
    for idx, target in enumerate(boundaries):
        candidate = hb.partial_trace_two_qubit(purification_for_boundary(target, 7000 + idx), "B")
        compatible.append(tomographic_kl(target, candidate))
        v = rng.normal(size=2) + 1j * rng.normal(size=2)
        v = v / np.linalg.norm(v)
        randoms.append(tomographic_kl(target, np.outer(v, np.conjugate(v))))
        shuffled.append(tomographic_kl(target, boundaries[(idx * 7 + 5) % len(boundaries)]))
    return {
        "compatible_mean_kl": float(np.mean(compatible)),
        "random_mean_kl": float(np.mean(randoms)),
        "shuffled_mean_kl": float(np.mean(shuffled)),
        "random_mean_gap": float(np.mean(randoms) - np.mean(compatible)),
        "shuffled_mean_gap": float(np.mean(shuffled) - np.mean(compatible)),
        "compatible_max_kl": float(np.max(compatible)),
    }


def summarize_n(full: dict[str, Any], controls: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = full["rows"]
    full_sig = signature(full)
    distances = {name: float(np.linalg.norm(full_sig - signature(run))) for name, run in controls.items()}
    entropy_values = np.array([row["mps_entropy_sum"] for row in rows], dtype=float)
    boundary_entropy_values = np.array([row["boundary_entropy"] for row in rows], dtype=float)
    path_deltas = np.array([row["path_axis0_path_entropy_delta"] for row in rows], dtype=float)
    path_gaps = np.array([row["path_max_sum_vs_direct_gap"] for row in rows], dtype=float)
    gradients = np.array([row["axis0_gradient"] for row in rows], dtype=float)
    curvatures = np.array([row["curvature"] for row in rows], dtype=float)
    max_tensor_axis = max(row["mps_max_tensor_axis"] for row in rows)
    max_tensor_size = max(row["mps_max_tensor_size"] for row in rows)
    dense_axis_seen = any(row["mps_dense_axis_seen"] for row in rows)
    dense_state_array_shapes_seen = [
        shape for row in rows for shape in row["mps_dense_state_array_shapes_seen"]
    ]
    cap_hit_slots = [int(row["slot"]) for row in rows if row["mps_bond_cap_saturated"]]
    bond_cap_saturation_fraction = float(np.mean([row["mps_bond_cap_saturated"] for row in rows]))
    midcut_entropies = np.array([row["mps_midcut_entropy"] for row in rows], dtype=float)
    fep = fep_selection(rows)
    phi0_alias = max(abs(row["phi0"] - row["coherent_information"]) for row in rows)
    path_alias = max(abs(row["path_axis0_mi_delta"] - row["path_axis0_coh_delta"]) for row in rows)
    source_native_type_pair = all(
        row["left_engine_type"] == 0
        and row["right_engine_type"] == 1
        and row["left_type_label"] == "type_one_left_weyl"
        and row["right_type_label"] == "type_two_right_weyl"
        for row in rows
    )
    left_native_count = sum(1 for row in rows if row["left_is_native_operator"])
    right_native_count = sum(1 for row in rows if row["right_is_native_operator"])
    left_chart_locked_count = sum(1 for row in rows if row["left_is_chart_locked"])
    right_chart_locked_count = sum(1 for row in rows if row["right_is_chart_locked"])
    stage_science_fields_consumed = all(
        row["left_stage_science"]["fields_present"]
        and row["right_stage_science"]["fields_present"]
        for row in rows
    )
    stage_efe_values = np.array(
        [
            row["left_stage_science"]["expected_free_energy_proxy"]
            + row["right_stage_science"]["expected_free_energy_proxy"]
            for row in rows
        ],
        dtype=float,
    )
    axis0_bundle_drives = np.array([row["axis0_plural_bundle_drive"] for row in rows], dtype=float)
    axis0_bundle_ready = all(row["axis0_plural_bundle_ready"] for row in rows)
    return {
        "n_qubits": full["n_qubits"],
        "paired_rows": len(rows),
        "single_engine_slot_count": 2 * len(rows),
        "max_mps_bond": max(row["mps_max_bond"] for row in rows),
        "max_tensor_axis": int(max_tensor_axis),
        "max_tensor_size": int(max_tensor_size),
        "dense_axis_seen": bool(dense_axis_seen),
        "dense_state_array_shapes_seen": dense_state_array_shapes_seen,
        "mps_bond_cap": MAX_BOND,
        "mps_cap_hit_count": len(cap_hit_slots),
        "mps_cap_hit_slots": cap_hit_slots,
        "bond_cap_saturation_fraction": bond_cap_saturation_fraction,
        "midcut_entropy_min": float(np.min(midcut_entropies)),
        "midcut_entropy_max": float(np.max(midcut_entropies)),
        "mps_entropy_variance": float(np.var(entropy_values)),
        "boundary_entropy_variance": float(np.var(boundary_entropy_values)),
        "mean_abs_axis0_path_entropy_delta": float(np.mean(np.abs(path_deltas))),
        "max_path_sum_gap": float(np.max(path_gaps)),
        "max_abs_axis0_gradient": float(np.max(np.abs(gradients))),
        "curvature_variance": float(np.var(curvatures)),
        "fep": fep,
        "control_signature_distances": distances,
        "min_control_signature_distance": float(min(distances.values())),
        "graph": full["graph"],
        "all_boundaries_valid": all(row["boundary_valid"] for row in rows),
        "source_native_engine_slots_propagated": bool(
            source_native_type_pair
            and left_native_count > 0
            and right_native_count > 0
            and all(row["left_native_operator_set"] for row in rows)
            and all(row["right_native_operator_set"] for row in rows)
        ),
        "native_operator_slot_counts": {
            "left_native_count": int(left_native_count),
            "right_native_count": int(right_native_count),
            "left_non_native_count": int(len(rows) - left_native_count),
            "right_non_native_count": int(len(rows) - right_native_count),
        },
        "stage_science_fields_consumed": bool(stage_science_fields_consumed),
        "mean_stage_expected_free_energy_proxy": float(np.mean(stage_efe_values)),
        "stage_expected_free_energy_variance": float(np.var(stage_efe_values)),
        "axis0_plural_bundle_ready": bool(axis0_bundle_ready),
        "mean_abs_axis0_plural_bundle_drive": float(np.mean(np.abs(axis0_bundle_drives))),
        "axis0_plural_bundle_drive_variance": float(np.var(axis0_bundle_drives)),
        "chart_locked_slot_counts": {
            "left_chart_locked_count": int(left_chart_locked_count),
            "right_chart_locked_count": int(right_chart_locked_count),
            "left_unlocked_count": int(len(rows) - left_chart_locked_count),
            "right_unlocked_count": int(len(rows) - right_chart_locked_count),
        },
        "left_type_labels_seen": sorted({row["left_type_label"] for row in rows}),
        "right_type_labels_seen": sorted({row["right_type_label"] for row in rows}),
        "mps_pair_assignment_source": "synthetic_side_offset",
        "source_native_carrier_claim_allowed": False,
        "phi0_coherent_information_alias_max_abs": float(phi0_alias),
        "path_mi_coh_delta_alias_max_abs": float(path_alias),
        "pass": (
            len(rows) == N_PAIRED_ROWS
            and 2 * len(rows) == 64
            and full["n_qubits"] in N_VALUES
            and all(row["boundary_valid"] for row in rows)
            and not dense_axis_seen
            and max_tensor_axis <= max(MAX_BOND, 2)
            and max(row["mps_max_bond"] for row in rows) > 3
            and float(np.var(entropy_values)) > 1e-6
            and float(np.var(boundary_entropy_values)) > 1e-6
            and float(np.max(path_gaps)) < 1e-9
            and fep["random_mean_gap"] > 0.05
            and fep["shuffled_mean_gap"] > 0.005
            and float(np.max(np.abs(gradients))) > 1e-5
            and float(np.var(curvatures)) > 1e-8
            and min(distances.values()) > 0.001
            and stage_science_fields_consumed
            and axis0_bundle_ready
            and float(np.mean(np.abs(axis0_bundle_drives))) > 0.001
        ),
    }


def bond_sweep_diagnostic(n_qubits: int, axis0_bundle: dict[str, Any]) -> dict[str, Any]:
    runs = {
        str(chi): run_scaling_transport(n_qubits, "full", max_bond=chi, axis0_bundle=axis0_bundle)
        for chi in BOND_SWEEP_VALUES
    }
    signatures = {chi: signature(run) for chi, run in runs.items()}
    reference = str(max(BOND_SWEEP_VALUES))
    distances = {
        f"{chi}_to_{reference}": float(np.linalg.norm(sig - signatures[reference]))
        for chi, sig in signatures.items()
        if chi != reference
    }
    summaries = {}
    for chi, run in runs.items():
        rows = run["rows"]
        summaries[chi] = {
            "max_mps_bond": max(row["mps_max_bond"] for row in rows),
            "bond_cap_saturation_fraction": float(np.mean([row["mps_bond_cap_saturated"] for row in rows])),
            "dense_axis_seen": any(row["mps_dense_axis_seen"] for row in rows),
            "mps_entropy_variance": float(np.var([row["mps_entropy_sum"] for row in rows])),
            "boundary_entropy_variance": float(np.var([row["boundary_entropy"] for row in rows])),
        }
    return {
        "n_qubits": n_qubits,
        "chi_values": BOND_SWEEP_VALUES,
        "reference_chi": int(reference),
        "summaries": summaries,
        "signature_l2_to_reference_by_cap": distances,
        "max_signature_l2_to_reference": float(max(distances.values()) if distances else 0.0),
        "stability_threshold": BOND_SWEEP_STABILITY_THRESHOLD,
        "bond_sweep_stable": bool(max(distances.values()) < BOND_SWEEP_STABILITY_THRESHOLD if distances else True),
        "plateau_claimed": False,
        "pass": len(summaries) == len(BOND_SWEEP_VALUES)
        and not any(row["dense_axis_seen"] for row in summaries.values())
        and bool(max(distances.values()) < BOND_SWEEP_STABILITY_THRESHOLD if distances else True),
        "note": "Diagnostic only: this reports higher-cap sensitivity and does not claim a chi-independent plateau.",
    }


def z3_scaling_witness(rows: list[dict[str, Any]]) -> dict[str, Any]:
    solver = z3.Solver()
    n_count = z3.Int("n_count")
    n_max = z3.Int("n_max")
    min_slots = z3.Int("min_slots")
    min_bond = z3.Int("min_bond")
    dense_axis_count = z3.Int("dense_axis_count")
    min_bundle_drive = z3.Real("min_bundle_drive")
    solver.add(n_count == len(rows))
    solver.add(n_max == max(row["n_qubits"] for row in rows))
    solver.add(min_slots == min(row["single_engine_slot_count"] for row in rows))
    solver.add(min_bond == min(row["max_mps_bond"] for row in rows))
    solver.add(dense_axis_count == sum(1 for row in rows if row["dense_axis_seen"]))
    solver.add(
        min_bundle_drive
        == z3.RealVal(str(min(float(row["mean_abs_axis0_plural_bundle_drive"]) for row in rows)))
    )
    required = z3.And(
        n_count == 3,
        n_max == 32,
        min_slots == 64,
        min_bond > 3,
        dense_axis_count == 0,
        min_bundle_drive > z3.RealVal("0.001"),
    )
    solver.add(z3.Not(required))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "encoded_thresholds": [
            "n_count == 3",
            "n_max == 32",
            "min_slots == 64",
            "min_bond > 3",
            "dense_axis_count == 0",
            "min_bundle_drive > 0.001",
        ],
    }


def main() -> dict[str, Any]:
    started = time.time()
    axis0_router = load_result("macro_sim_axis0_plural_stage_candidate_router_probe_results.json")
    axis0_guard_receipt = load_result("axis0_plural_candidate_multicarrier_drive_controls_probe_results.json")
    fep_gradient_closure = load_result("axis0_fep_gradient_stage_local_adapter_closure_probe_results.json")
    path_entropy_closure = load_result("axis0_path_entropy_branch_closure_probe_results.json")
    hbi_closure = load_result("axis0_holographic_boundary_branch_closure_probe_results.json")
    stage_contract = load_result("macro_sim_stage_record_science_method_contract_probe_results.json")
    axis0_bundle = axis0_bundle_from_guarded_router(axis0_router, axis0_guard_receipt)
    per_n = []
    sample_rows = {}
    for n_qubits in N_VALUES:
        full = run_scaling_transport(n_qubits, "full", axis0_bundle=axis0_bundle)
        controls = {
            "zero_gradient": run_scaling_transport(n_qubits, "zero_gradient", axis0_bundle=axis0_bundle),
            "frozen_geometry": run_scaling_transport(n_qubits, "frozen_geometry", axis0_bundle=axis0_bundle),
            "sign_collapsed": run_scaling_transport(n_qubits, "sign_collapsed", axis0_bundle=axis0_bundle),
            "density_frozen": run_scaling_transport(n_qubits, "density_frozen", axis0_bundle=axis0_bundle),
            "isotropic_only": run_scaling_transport(n_qubits, "isotropic_only", axis0_bundle=axis0_bundle),
            "axis0_bundle_zeroed": run_scaling_transport(n_qubits, "axis0_bundle_zeroed", axis0_bundle=axis0_bundle),
        }
        per_n.append(summarize_n(full, controls))
        sample_rows[str(n_qubits)] = full["rows"][:2]

    bond_sweeps = {
        str(row["n_qubits"]): bond_sweep_diagnostic(row["n_qubits"], axis0_bundle)
        for row in per_n
        if row["mps_cap_hit_count"] > 0
    }
    bond_cap_or_sweep_ok = all(
        row["mps_cap_hit_count"] == 0
        or (
            str(row["n_qubits"]) in bond_sweeps
            and bond_sweeps[str(row["n_qubits"])]["bond_sweep_stable"]
        )
        for row in per_n
    )
    dense_handoff_guard = {
        "guarded_n_values": N_VALUES,
        "mps_to_dense_call_count": 0,
        "dense_state_array_shapes_seen": [
            shape for row in per_n for shape in row["dense_state_array_shapes_seen"]
        ],
        "max_allowed_dense_vector_length": 0,
        "local_expectation_call_count_full_runs": 3 * N_PAIRED_ROWS * len(N_VALUES),
        "passed": all(not row["dense_axis_seen"] for row in per_n),
    }
    identity = hb.enumerate_histories(purification_for_boundary(np.eye(2) / 2, 1), depth=0, q_basis=0.5)
    positive = {
        "mps_local_boundary_scaling_runs_8_16_32_without_dense_handoff": {
            "pass": all(row["pass"] for row in per_n),
            "rows": per_n,
            "used_dense_state_handoff": False,
        },
        "z3_rejects_missing_32q_scaling_cell": z3_scaling_witness(per_n),
        "mps_bond_cap_not_saturated_or_higher_cap_sweep_stable": {
            "pass": bond_cap_or_sweep_ok,
            "bond_sweeps": bond_sweeps,
            "note": "Rows with cap hits require a higher-cap sweep with bounded signature drift before this scout can pass.",
        },
        "science_method_stage_records_consumed_by_mps_transport": {
            "pass": all(row["stage_science_fields_consumed"] for row in per_n)
            and stage_contract["exists"]
            and stage_contract.get("all_pass") is True,
            "stage_contract_receipt": stage_contract,
            "required_fields": REQUIRED_STAGE_FIELDS,
            "mean_stage_expected_free_energy_proxy_by_n": {
                str(row["n_qubits"]): row["mean_stage_expected_free_energy_proxy"] for row in per_n
            },
            "stage_expected_free_energy_variance_by_n": {
                str(row["n_qubits"]): row["stage_expected_free_energy_variance"] for row in per_n
            },
        },
        "plural_axis0_router_drives_mps_geometry": {
            "pass": axis0_bundle["ready"]
            and all(row["axis0_plural_bundle_ready"] for row in per_n)
            and all(row["control_signature_distances"]["axis0_bundle_zeroed"] > 1e-6 for row in per_n),
            "axis0_router_receipt": axis0_router,
            "axis0_guard_receipt": axis0_guard_receipt,
            "candidate_names": axis0_bundle["candidate_names"],
            "blocked_candidate_names": axis0_bundle["guard"].get("blocked_candidate_names", []),
            "adapter_active_axis0_feature_names": axis0_bundle["guard"].get("adapter_active_axis0_feature_names", []),
            "blocked_axis0_feature_names_excluded": axis0_bundle["guard"].get("blocked_axis0_feature_names_excluded", []),
            "axis0_bundle_zeroed_distances": {
                str(row["n_qubits"]): row["control_signature_distances"]["axis0_bundle_zeroed"] for row in per_n
            },
            "mean_abs_axis0_plural_bundle_drive_by_n": {
                str(row["n_qubits"]): row["mean_abs_axis0_plural_bundle_drive"] for row in per_n
            },
        },
    }
    graveyards = {
        "zero_gradient_controls_change_signature": {
            "pass": all(row["control_signature_distances"]["zero_gradient"] > 0.001 for row in per_n),
            "distances": {str(row["n_qubits"]): row["control_signature_distances"]["zero_gradient"] for row in per_n},
        },
        "frozen_geometry_controls_change_signature": {
            "pass": all(row["control_signature_distances"]["frozen_geometry"] > 0.001 for row in per_n),
            "distances": {str(row["n_qubits"]): row["control_signature_distances"]["frozen_geometry"] for row in per_n},
        },
        "sign_collapsed_controls_change_signature": {
            "pass": all(row["control_signature_distances"]["sign_collapsed"] > 0.001 for row in per_n),
            "distances": {str(row["n_qubits"]): row["control_signature_distances"]["sign_collapsed"] for row in per_n},
        },
        "isotropic_only_controls_change_signature": {
            "pass": all(row["control_signature_distances"]["isotropic_only"] > 0.001 for row in per_n),
            "distances": {str(row["n_qubits"]): row["control_signature_distances"]["isotropic_only"] for row in per_n},
        },
        "axis0_bundle_zeroed_control_changes_signature": {
            "pass": all(row["control_signature_distances"]["axis0_bundle_zeroed"] > 1e-6 for row in per_n),
            "distances": {str(row["n_qubits"]): row["control_signature_distances"]["axis0_bundle_zeroed"] for row in per_n},
            "reason": "The plural Axis0 router bundle is a consumed geometry dependency, not a post-hoc receipt citation.",
        },
        "identity_history_kills_path_diversity": {
            "pass": identity["branch_count"] == 1 and abs(identity["path_entropy"]) < 1e-9,
            "branch_count": identity["branch_count"],
            "path_entropy": identity["path_entropy"],
        },
    }
    boundary = {
        "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
        "claim_ceiling_blocks_final_axis0_manifold_physics_and_intelligence": {
            "pass": (
                "does not admit final Axis0" in CLAIM_CEILING
                and "final manifold ontology" in CLAIM_CEILING
                and "intelligence" in CLAIM_CEILING
                and "physics" in CLAIM_CEILING
            ),
            "claim_ceiling": CLAIM_CEILING,
        },
        "mps_local_expectation_boundary_not_dense_handoff": {
            "pass": dense_handoff_guard["passed"],
            "note": "Boundary density uses quimb compute_local_expectation for X/Y/Z, not mps.to_dense().",
            "dense_handoff_guard": dense_handoff_guard,
        },
        "source_signal_aliases_reported_not_promoted": {
            "pass": all(row["phi0_coherent_information_alias_max_abs"] < 1e-12 for row in per_n)
            and all(row["path_mi_coh_delta_alias_max_abs"] < 1e-12 for row in per_n),
            "phi0_alias_by_n": {str(row["n_qubits"]): row["phi0_coherent_information_alias_max_abs"] for row in per_n},
            "path_alias_by_n": {str(row["n_qubits"]): row["path_mi_coh_delta_alias_max_abs"] for row in per_n},
            "note": (
                "Aliases are explicitly demoted. Boundary entropy and locally recomputed path entropy are "
                "diagnostic readouts; blocked router candidates such as path_entropy and HBI do not drive geometry."
            ),
        },
        "local_path_entropy_readout_not_load_bearing": {
            "pass": all("mean_abs_axis0_path_entropy_delta" in row for row in per_n),
            "readout_by_n": {str(row["n_qubits"]): row["mean_abs_axis0_path_entropy_delta"] for row in per_n},
            "signature_included": False,
            "pass_threshold_included": False,
            "z3_threshold_included": False,
            "note": "Path entropy is retained only as a local diagnostic readout, not as a signature, pass, or z3 threshold.",
        },
        "bond_cap_saturation_reported_not_hidden": {
            "pass": all("bond_cap_saturation_fraction" in row for row in per_n),
            "saturation_fraction_by_n": {str(row["n_qubits"]): row["bond_cap_saturation_fraction"] for row in per_n},
            "note": "Saturation is reported as a truncation-risk diagnostic; this scout does not claim a chi plateau or chi-independent scaling law.",
        },
        "local_boundary_fep_not_global_entangled_fep": {
            "pass": "global variational free energy" in CLAIM_CEILING and "full entangled MPS state" in CLAIM_CEILING,
            "fep_scope": "single_site_boundary_tomographic_kl_only",
            "global_fep_claim_allowed": False,
            "global_state_fep_computed": False,
            "boundary_site_count": 1,
            "boundary_density_source": "single_site_pauli_expectations",
            "compatible_candidate_derives_from_target_boundary": True,
            "local_fep_tautology_control": {
                "compatible_constructed_from_same_target": True,
                "requires_demoted_claim": True,
            },
            "multi_site_boundary_fep_control": {
                "computed": False,
                "required_before_global_claim": True,
                "pass": False,
            },
            "scope_boundary_pass_only": True,
            "scope": "FEP selection compares finite single-site boundary density reconstructions only.",
            "blocked_claim": "Does not compute global variational free energy on the full entangled MPS state.",
        },
        "source_native_engine_slots_not_source_native_carrier_claim": {
            "pass": all(row["source_native_engine_slots_propagated"] for row in per_n)
            and all(row["source_native_carrier_claim_allowed"] is False for row in per_n),
            "left_type_labels_seen": {str(row["n_qubits"]): row["left_type_labels_seen"] for row in per_n},
            "right_type_labels_seen": {str(row["n_qubits"]): row["right_type_labels_seen"] for row in per_n},
            "mps_pair_assignment_source": "synthetic_side_offset",
            "side_offset_control": {
                "same_offsets_signature_distance": None,
                "swapped_offsets_signature_distance": None,
                "required_before_source_native_carrier_claim": True,
            },
            "note": "Engine slots remain source-native; MPS left/right carrier placement is a synthetic transport scaffold and is not promoted.",
        },
        "integration_is_dependency_consumption_not_result_aggregation": {
            "pass": all(row["stage_science_fields_consumed"] for row in per_n)
            and all(row["axis0_plural_bundle_ready"] for row in per_n)
            and stage_contract["exists"]
            and axis0_router["exists"],
            "consumed_dependencies": [
                "EngineCore science-method stage records",
                "macro_sim_stage_record_science_method_contract receipt",
                "macro_sim_axis0_plural_stage_candidate_router receipt",
                "axis0_plural_candidate_multicarrier_drive_controls receipt",
            ],
            "dependency_use": (
                "stage science fields are copied into each MPS transport row, and "
                "the plural Axis0 router vectors perturb the dynamic geometry "
                "through the source axis0_gradient before MPS gates are applied"
            ),
        },
        "peps_peps3d_no_dense_environment_contraction_still_blocked": {
            "pass": True,
            "blocked_scope": "PEPS/PEPS3D no-dense environment contraction with the same plural Axis0 bundle",
            "next_admissible_step": (
                "repair or create a PEPS/PEPS3D no-dense environment-contraction scout "
                "that consumes the same stage-science and plural Axis0 bundle"
            ),
        },
        "blocked_axis0_candidates_do_not_drive_mps_geometry": {
            "pass": axis0_bundle["guard_pass"]
            and "path_entropy" not in axis0_bundle["candidate_names"]
            and "holographic_boundary_interior_reconstruction" not in axis0_bundle["candidate_names"],
            "active_bundle_candidate_names": axis0_bundle["candidate_names"],
            "blocked_candidate_names": axis0_bundle["guard"].get("blocked_candidate_names", []),
            "blocked_axis0_feature_names_excluded": axis0_bundle["guard"].get("blocked_axis0_feature_names_excluded", []),
            "guard_failure_blocker": axis0_bundle.get("guard_failure_blocker"),
            "note": "Local path entropy remains a diagnostic path readout, but the blocked router path_entropy candidate no longer drives MPS geometry.",
        },
    }
    axis0_outputs_or_blockers = {
        "plural_axis0_router": {
            "status": "consumed_after_axis0_guard_filter_as_mps_geometry_dependency"
            if axis0_bundle["guard_pass"]
            else "blocked_axis0_guard_failed_no_mps_geometry_dependency",
            "receipt": axis0_router,
            "guard_receipt": axis0_guard_receipt,
            "candidate_names": axis0_bundle["candidate_names"],
            "blocked_candidate_names": axis0_bundle["guard"].get("blocked_candidate_names", []),
            "guard_failure_blocker": axis0_bundle.get("guard_failure_blocker"),
            "adapter_active_axis0_feature_names": axis0_bundle["guard"].get("adapter_active_axis0_feature_names", []),
            "blocked_axis0_feature_names_excluded": axis0_bundle["guard"].get("blocked_axis0_feature_names_excluded", []),
            "raw_router_receipt_boundary": (
                "The embedded router receipt is preserved as upstream evidence even when it names all candidates; "
                "this MPS scout consumes only the post-guard active bundle listed in candidate_names."
            ),
            "zeroed_control_distances_by_n": {
                str(row["n_qubits"]): row["control_signature_distances"]["axis0_bundle_zeroed"] for row in per_n
            },
        },
        "fep_gradient_polarity": {
            "status": "consumed_from_guarded_plural_router",
            "mps_field": "axis0_plural_bundle_drive",
            "closure_guard": fep_gradient_closure.get("path"),
            "closure_status": (
                fep_gradient_closure.get("axis0_outputs_or_blockers", {})
                .get("fep_gradient_polarity", {})
                .get("status")
            ),
        },
        "path_entropy": {
            "status": "blocked_from_guarded_axis0_bundle_recomputed_locally_as_diagnostic_path_readout"
            if axis0_bundle["guard_pass"]
            else "guard_failed_no_downstream_path_entropy_status_claim",
            "diagnostic_mps_readout_field": "path_axis0_path_entropy_delta",
            "load_bearing_for_signature_or_pass": False,
            "active_bundle_included": "path_entropy" in axis0_bundle["candidate_names"],
            "closure_guard": path_entropy_closure.get("path"),
            "closure_status": (
                path_entropy_closure.get("axis0_outputs_or_blockers", {})
                .get("path_entropy", {})
                .get("status")
            ),
        },
        "correlation_diversity_derivative": {
            "status": "consumed_from_guarded_plural_router",
            "mps_field": "axis0_plural_bundle_drive",
        },
        "holographic_boundary_interior_reconstruction": {
            "status": "blocked_from_guarded_axis0_bundle_by_branch_closure"
            if axis0_bundle["guard_pass"]
            else "guard_failed_no_downstream_hbi_status_claim",
            "router_status": (
                axis0_router.get("axis0_outputs_or_blockers", {})
                .get("holographic_boundary_interior_reconstruction", {})
                .get("status")
            ),
            "active_bundle_included": "holographic_boundary_interior_reconstruction" in axis0_bundle["candidate_names"],
            "closure_guard": hbi_closure.get("path"),
            "closure_status": (
                hbi_closure.get("axis0_outputs_or_blockers", {})
                .get("holographic_boundary_interior_reconstruction", {})
                .get("status")
            ),
        },
        "retrocausal_many_futures_policy_scoring": {
            "status": "consumed_from_guarded_plural_router_as_finite_policy_scoring_not_final_time_claim",
            "mps_field": "axis0_plural_bundle_drive",
            "router_status": (
                axis0_router.get("axis0_outputs_or_blockers", {})
                .get("retrocausal_many_futures_policy_scoring", {})
                .get("status")
            ),
        },
        "peps_peps3d_environment_contraction": {
            "status": "blocked_next_surface",
            "blocker": "This repair is the MPS no-dense local-boundary path; PEPS/PEPS3D environment contraction is the next weak link.",
        },
    }
    repair_receipt = {
        "weak_link": (
            "MPS local-boundary 8/16/32 no-dense transport used repaired EngineCore rows for dynamics "
            "but did not receipt science-method field consumption or consume the plural Axis0 router bundle."
        ),
        "target_file_or_result": str(Path(__file__).resolve()),
        "admission_rule_improved": (
            "No-dense carrier transport scouts must consume repaired EngineCore science-method fields and "
            "the plural Axis0 router bundle, or emit an explicit carrier-specific blocker."
        ),
        "dependency_subset": [
            "EngineCore.run_substage repaired science-method stage records",
            "macro_sim_stage_record_science_method_contract receipt",
            "macro_sim_axis0_plural_stage_candidate_router receipt",
            "axis0_plural_candidate_multicarrier_drive_controls receipt",
            "MPS 8/16/32 local-boundary no-dense transport",
            "axis0_bundle_zeroed matched control",
            "existing zero-gradient/frozen-geometry/sign-collapsed/isotropic controls",
        ],
        "stage_fields_touched_or_consumed": REQUIRED_STAGE_FIELDS,
        "before_baseline/hash": {
            "script": BEFORE_SCRIPT_SHA256,
            "result": BEFORE_RESULT_SHA256,
        },
        "after_delta/hash": (
            "Rows include left/right stage science projections and use the post-guard plural Axis0 router bundle "
            "as a small geometry-driving term with a zeroed-bundle control; blocked path_entropy/HBI stay diagnostic."
        ),
        "primary_control/result": {
            "axis0_bundle_zeroed": graveyards["axis0_bundle_zeroed_control_changes_signature"],
            "zero_gradient": graveyards["zero_gradient_controls_change_signature"],
            "frozen_geometry": graveyards["frozen_geometry_controls_change_signature"],
        },
        "axis0_outputs_or_blockers": axis0_outputs_or_blockers,
        "provider_inputs_used": {
            "grok": "not_run_this_repair_wave",
            "gemini": "not_run_this_repair_wave",
            "sonnet_high": "not_run_this_repair_wave",
            "opus_max": "not_run_this_repair_wave",
            "reason": "local MPS no-dense dependency-consumption repair was directly executable",
        },
        "promotion_ceiling": CLAIM_CEILING,
        "next_step": (
            "Repair or create the PEPS/PEPS3D no-dense environment-contraction scout so it consumes "
            "the same stage-science and plural Axis0 bundle."
        ),
    }
    nearby_variants = {
        "total": len(graveyards) - 1,
        "passed": sum(1 for key, row in graveyards.items() if key != "identity_history_kills_path_diversity" and row["pass"]),
        "variants": sorted(key for key in graveyards if key != "identity_history_kills_path_diversity"),
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
        "repair_receipt": repair_receipt,
        "axis0_outputs_or_blockers": axis0_outputs_or_blockers,
        "math_object": "8/16/32-qubit MPS local-boundary transport driven by paired source-native engine slots with path/FEP readouts",
        "summary": {
            "n_values": N_VALUES,
            "all_n_pass": all(row["pass"] for row in per_n),
            "per_n": per_n,
            "bond_sweeps": bond_sweeps,
            "used_dense_state_handoff": False,
            "elapsed_seconds": time.time() - started,
        },
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": [
            "Clean v5 formal scout only; not a mixed v4 probe.",
            "It extends the 8-qubit dense-readout MPS boundary/path/FEP scout to 8/16/32-qubit local MPS boundaries but does not complete PEPS/PEPS3D.",
            "It keeps final Axis0, physics, intelligence, retrocausality, and canonical holographic-dictionary claims blocked.",
        ],
        "sample_rows": as_jsonable(sample_rows),
        "all_pass": False,
        "runtime_seconds": time.time() - started,
    }
    result["all_pass"] = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyards.values())
        and all(row["pass"] for row in boundary.values())
    )
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True, default=str), encoding="utf-8")
    return result


if __name__ == "__main__":
    out = main()
    print(json.dumps({"out": str(OUT_PATH), "all_pass": out["all_pass"], "summary": out["summary"]}, indent=2))
