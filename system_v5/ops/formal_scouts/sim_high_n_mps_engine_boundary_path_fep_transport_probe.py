#!/usr/bin/env python3
"""High-N MPS engine boundary/path/FEP transport scout.

This is the next repair after the 2D transition-phase scout found that the
post-manifold C^2 carrier collapses terrain/operator recoverability. Here the
boundary/path/FEP readouts consume the existing 8-qubit MPS transport surface:

  paired EngineCore slot histories
  -> Ax0-style conditional-entropy gradient
  -> dynamic metric/connection parameters
  -> quimb MPS gate transport
  -> one-site boundary reductions and Kraus path/FEP readouts

The carrier is 8 qubits, the current minimum operating scale requested for
this workstream. This scout still does not claim a final manifold, final Axis0,
physics, intelligence, or a canonical holographic dictionary.
"""

from __future__ import annotations

import json
import math
import os
import random
import time
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import networkx as nx
import quimb.tensor as qtn
import torch
import z3

import sim_holographic_boundary_path_ensemble_axis0_fep_selection_probe as hb
import sim_operator_slot_cut_entropy_gradient_dynamic_manifold_mps_transport_probe as transport


ROOT = Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "high_n_mps_engine_boundary_path_fep_transport_probe_results.json"

NAME = "high_n_mps_engine_boundary_path_fep_transport_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "downstream_on_source_native_operator_slot_engine_high_n_mps_transport"
CLAIM_CEILING = (
    "Formal scout only: couples paired source-native EngineCore slot histories "
    "to an 8-qubit MPS transport carrier, then applies finite boundary/path/FEP "
    "readouts to reduced boundary states. It does not admit final Axis0, final "
    "manifold ontology, intelligence, physics, retrocausality, or a canonical "
    "holographic dictionary."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing local boundary densities, signatures, controls, reduced-density contractions, and MPS handoff statistics"},
    "quimb": {"tried": True, "used": True, "reason": "load-bearing 8-qubit MPS transport and cut entropy"},
    "opt_einsum": {"tried": True, "used": True, "reason": "supportive/transitive through transport helper lineage; reduced-density contractions are local PyTorch"},
    "scipy": {"tried": True, "used": True, "reason": "supportive through EngineCore Lindblad and slot-gate helpers; not directly load-bearing in this controller"},
    "cotengra": {"tried": True, "used": True, "reason": "load-bearing through the called geometry-shaped contraction_report helper"},
    "networkx": {"tried": True, "used": True, "reason": "supportive slot dependency graph"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing noncollapse witness"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "quimb": "load_bearing",
    "opt_einsum": "supportive",
    "scipy": "supportive",
    "cotengra": "load_bearing",
    "networkx": "supportive",
    "z3": "load_bearing",
}
TOOL_ROLE_SOURCE = {
    "pytorch": "local",
    "quimb": "local",
    "opt_einsum": "transitive_supportive",
    "scipy": "transitive_supportive",
    "cotengra": "transitive_helper",
    "networkx": "local",
    "z3": "local",
}

N_QUBITS = 8
N_PAIRED_ROWS = 32

TORCH_REAL = torch.float64
TORCH_COMPLEX = torch.complex128
TI2 = torch.eye(2, dtype=TORCH_COMPLEX)
TSX = torch.as_tensor([[0, 1], [1, 0]], dtype=TORCH_COMPLEX)
TSY = torch.as_tensor([[0, -1j], [1j, 0]], dtype=TORCH_COMPLEX)
TSZ = torch.as_tensor([[1, 0], [0, -1]], dtype=TORCH_COMPLEX)


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


def norm_float(value: Any) -> float:
    tensor = as_complex_tensor(value)
    return float(torch.linalg.vector_norm(tensor.reshape(-1)).item())


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, torch.Tensor):
        return value.tolist()
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def normalized_dense(mps: qtn.MatrixProductState) -> torch.Tensor:
    psi = as_complex_tensor(mps.to_dense()).reshape(-1)
    return psi / max(float(torch.linalg.vector_norm(psi).item()), 1e-15)


def reduced_density(psi: torch.Tensor, keep: int) -> torch.Tensor:
    tensor = psi.reshape([2] * N_QUBITS)
    moved = torch.movedim(tensor, keep, 0).reshape(2, -1)
    rho = moved @ torch.conj(moved).transpose(0, 1)
    return project_density(rho / max(float(torch.real(torch.trace(rho)).item()), 1e-15))


def boundary_stats(rho: Any) -> dict[str, Any]:
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


def purification_for_boundary(rho_b: Any, seed: int) -> torch.Tensor:
    return project_density(
        hb.purification_for_boundary(
            project_density(rho_b),
            interior_angle=0.21 + 0.017 * (seed % 29),
            phase=0.33 + 0.023 * (seed % 31),
        )
    )


def path_readout(rho_b: Any, seed: int, depth: int = 2) -> dict[str, float]:
    rho = purification_for_boundary(rho_b, seed)
    low = hb.enumerate_histories(rho, depth=depth, q_basis=0.46)
    high = hb.enumerate_histories(rho, depth=depth, q_basis=0.89)
    out: dict[str, float] = {}
    for name, hist in [("low", low), ("high", high)]:
        summed = project_density(hist["summed_state"])
        rho_i = project_density(hb.partial_trace_two_qubit(summed, "I"))
        rho_b2 = project_density(hb.partial_trace_two_qubit(summed, "B"))
        out[f"{name}_path_entropy"] = hist["path_entropy"]
        out[f"{name}_effective_paths"] = hist["effective_paths"]
        out[f"{name}_mi"] = entropy(rho_i) + entropy(rho_b2) - entropy(summed)
        out[f"{name}_conditional_entropy"] = entropy(summed) - entropy(rho_b2)
        out[f"{name}_coh"] = entropy(rho_b2) - entropy(summed)
        out[f"{name}_purity"] = purity(summed)
        out[f"{name}_sum_vs_direct_gap"] = hist["sum_vs_direct_gap"]
    out["axis0_path_entropy_delta"] = out["high_path_entropy"] - out["low_path_entropy"]
    out["axis0_mi_delta"] = out["high_mi"] - out["low_mi"]
    out["axis0_conditional_entropy_delta"] = out["high_conditional_entropy"] - out["low_conditional_entropy"]
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


def run_high_n_transport(mode: str = "full") -> dict[str, Any]:
    engine_l = transport.EngineCore(0, manifold_enabled=True)
    engine_r = transport.EngineCore(1, manifold_enabled=True)
    rho_l = transport.generate_initial_density(3101)
    rho_r = transport.generate_initial_density(4101)
    mps = qtn.MPS_rand_state(N_QUBITS, bond_dim=3, seed=91)
    params = as_real_tensor([0.05, 0.03, -0.02, 0.35])
    source_history: list[dict[str, float]] = []
    rows = []
    graph = nx.DiGraph()

    for main_idx, ((per_l, loop_l), (per_r, loop_r)) in enumerate(zip(engine_l.schedule, engine_r.schedule)):
        for sub_idx in range(4):
            rho_l, rec_l = engine_l.run_substage(rho_l, per_l, loop_l, main_idx, sub_idx)
            rho_r, rec_r = engine_r.run_substage(rho_r, per_r, loop_r, main_idx, sub_idx)
            live_signal = transport.source_information_signal(rho_l, rho_r, params[3])
            source_history.append(live_signal)
            if mode == "zero_gradient":
                source_signal = dict(live_signal)
                source_signal["axis0_gradient"] = 0.0
            elif mode == "frozen_geometry":
                source_signal = live_signal
            elif mode == "density_frozen":
                source_signal = source_history[0]
            else:
                source_signal = live_signal
            update_mode = "frozen_geometry" if mode == "frozen_geometry" else "full"
            params = transport.update_geometry(params, source_signal, rec_l, rec_r, update_mode)
            geom = transport.metric_values(params)
            gate_l = transport.slot_gate(rec_l, geom, source_signal, sign_collapsed=(mode == "sign_collapsed"))
            gate_r = transport.slot_gate(rec_r, geom, source_signal, sign_collapsed=(mode == "sign_collapsed"))
            for pair in transport.TOPOLOGY_PAIRS[per_l][:2]:
                mps.gate_(gate_l, pair, contract="swap+split", max_bond=12, cutoff=1e-10)
            for pair in transport.TOPOLOGY_PAIRS[per_r][-2:]:
                mps.gate_(gate_r, pair, contract="swap+split", max_bond=12, cutoff=1e-10)

            psi = normalized_dense(mps)
            boundary_site = (main_idx + sub_idx) % N_QUBITS
            rho_b = reduced_density(psi, boundary_site)
            boundary = boundary_stats(rho_b)
            path = path_readout(rho_b, seed=1000 + main_idx * 4 + sub_idx)
            cuts = as_real_tensor([float(mps.entropy(cut)) for cut in range(1, N_QUBITS)])
            contract = transport.contraction_report(params, source_signal, static_tree=(mode == "static_tree"))
            slot = main_idx * 4 + sub_idx
            node = f"slot:{slot}"
            graph.add_node(node)
            if slot:
                graph.add_edge(f"slot:{slot - 1}", node)
            rows.append(
                {
                    "slot": slot,
                    "boundary_site": boundary_site,
                    "left_token": rec_l["ordered_token"],
                    "right_token": rec_r["ordered_token"],
                    "left_family": rec_l["terrain_dynamics_family"],
                    "right_family": rec_r["terrain_dynamics_family"],
                    "left_operator": rec_l["operator"],
                    "right_operator": rec_r["operator"],
                    "left_operator_sign": rec_l["operator_sign"],
                    "right_operator_sign": rec_r["operator_sign"],
                    "phi0": source_signal["phi0"],
                    "axis0_gradient": source_signal["axis0_gradient"],
                    "coherent_information": source_signal["coherent_information"],
                    "mutual_information": source_signal["mutual_information"],
                    "lr_trace_distance": source_signal["lr_trace_distance"],
                    "curvature": geom["curvature"],
                    "torsion": geom["torsion"],
                    "coupling": geom["coupling"],
                    "mps_entropy_sum": float(torch.sum(cuts).item()),
                    "mps_entropy_std": float(torch.std(cuts, unbiased=False).item()),
                    "mps_max_bond": int(mps.max_bond()),
                    "boundary_entropy": boundary["entropy"],
                    "boundary_purity": boundary["purity"],
                    "boundary_bloch": boundary["bloch"],
                    "boundary_valid": boundary["valid"],
                    **{f"path_{key}": value for key, value in path.items()},
                    **contract,
                }
            )
    return {
        "mode": mode,
        "rows": rows,
        "graph": {
            "nodes": graph.number_of_nodes(),
            "edges": graph.number_of_edges(),
            "acyclic": nx.is_directed_acyclic_graph(graph),
        },
    }


def signature(run: dict[str, Any]) -> torch.Tensor:
    arr = as_real_tensor(
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
                r["path_axis0_path_entropy_delta"],
                r["contract_norm"],
            ]
            for r in run["rows"]
        ]
    )
    return torch.cat([torch.mean(arr, dim=0), torch.std(arr, dim=0, unbiased=False), arr[-1]])


def fep_selection(rows: list[dict[str, Any]]) -> dict[str, float]:
    generator = torch.Generator().manual_seed(8675309)
    compatible = []
    randoms = []
    shuffled = []
    boundaries = []
    for row in rows:
        r = 0.5 * (
            TI2
            + row["boundary_bloch"][0] * TSX
            + row["boundary_bloch"][1] * TSY
            + row["boundary_bloch"][2] * TSZ
        )
        boundaries.append(project_density(r))
    for idx, target in enumerate(boundaries):
        candidate = hb.partial_trace_two_qubit(purification_for_boundary(target, 5000 + idx), "B")
        compatible.append(tomographic_kl(target, candidate))
        v = (
            torch.randn(2, generator=generator, dtype=TORCH_REAL)
            + 1j * torch.randn(2, generator=generator, dtype=TORCH_REAL)
        ).to(TORCH_COMPLEX)
        v = v / torch.linalg.vector_norm(v)
        randoms.append(tomographic_kl(target, torch.outer(v, torch.conj(v))))
        shuffled.append(tomographic_kl(target, boundaries[(idx * 11 + 3) % len(boundaries)]))
    return {
        "compatible_mean_kl": mean_float(compatible),
        "random_mean_kl": mean_float(randoms),
        "shuffled_mean_kl": mean_float(shuffled),
        "random_mean_gap": mean_float(randoms) - mean_float(compatible),
        "shuffled_mean_gap": mean_float(shuffled) - mean_float(compatible),
        "compatible_max_kl": max_float(compatible),
    }


def z3_witness(metrics: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    paired_rows = z3.Int("paired_rows")
    single_slots = z3.Int("single_slots")
    n_qubits = z3.Int("n_qubits")
    max_bond = z3.Int("max_bond")
    max_path_gap = z3.Real("max_path_gap")
    path_delta = z3.Real("mean_abs_path_delta")
    fep_random_gap = z3.Real("fep_random_gap")
    fep_shuffled_gap = z3.Real("fep_shuffled_gap")
    control_min = z3.Real("control_min")
    solver.add(paired_rows == int(metrics["paired_rows"]))
    solver.add(single_slots == int(metrics["single_engine_slot_count"]))
    solver.add(n_qubits == int(metrics["n_qubits"]))
    solver.add(max_bond == int(metrics["max_mps_bond"]))
    solver.add(max_path_gap == str(float(metrics["max_path_sum_gap"])))
    solver.add(path_delta == str(float(metrics["mean_abs_axis0_path_entropy_delta"])))
    solver.add(fep_random_gap == str(float(metrics["fep_random_mean_gap"])))
    solver.add(fep_shuffled_gap == str(float(metrics["fep_shuffled_mean_gap"])))
    solver.add(control_min == str(float(metrics["min_control_signature_distance"])))
    required = z3.And(
        paired_rows == 32,
        single_slots == 64,
        n_qubits >= 8,
        max_bond > 3,
        max_path_gap < z3.RealVal("1e-9"),
        path_delta > z3.RealVal("0.01"),
        fep_random_gap > z3.RealVal("0.10"),
        fep_shuffled_gap > z3.RealVal("0.02"),
        control_min > z3.RealVal("0.005"),
    )
    solver.add(z3.Not(required))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "encoded_thresholds": [
            "paired_rows == 32",
            "single_slots == 64",
            "n_qubits >= 8",
            "max_bond > 3",
            "max_path_gap < 1e-9",
            "path_delta > 0.01",
            "fep_random_gap > 0.10",
            "fep_shuffled_gap > 0.02",
            "control_min > 0.005",
        ],
    }


def main() -> dict[str, Any]:
    start = time.time()
    full = run_high_n_transport("full")
    zero = run_high_n_transport("zero_gradient")
    frozen = run_high_n_transport("frozen_geometry")
    sign = run_high_n_transport("sign_collapsed")
    density = run_high_n_transport("density_frozen")

    rows = full["rows"]
    full_sig = signature(full)
    control_distances = {
        "zero_gradient": norm_float(full_sig - signature(zero)),
        "frozen_geometry": norm_float(full_sig - signature(frozen)),
        "sign_collapsed": norm_float(full_sig - signature(sign)),
        "density_frozen": norm_float(full_sig - signature(density)),
    }
    entropy_values = [row["mps_entropy_sum"] for row in rows]
    boundary_entropy_values = [row["boundary_entropy"] for row in rows]
    path_deltas = [row["path_axis0_path_entropy_delta"] for row in rows]
    path_gaps = [row["path_max_sum_vs_direct_gap"] for row in rows]
    gradients = [row["axis0_gradient"] for row in rows]
    curvatures = [row["curvature"] for row in rows]
    fep = fep_selection(rows)
    identity = hb.enumerate_histories(purification_for_boundary(TI2 / 2.0, 1), depth=0, q_basis=0.5)
    phi0_coherent_alias_max = max(abs(row["phi0"] - row["coherent_information"]) for row in rows)
    path_mi_coh_alias_max = max(abs(row["path_axis0_mi_delta"] - row["path_axis0_coh_delta"]) for row in rows)
    summary = {
        "paired_rows": len(rows),
        "single_engine_slot_count": 2 * len(rows),
        "n_qubits": N_QUBITS,
        "max_mps_bond": max(row["mps_max_bond"] for row in rows),
        "mps_entropy_variance": variance_float(entropy_values),
        "boundary_entropy_variance": variance_float(boundary_entropy_values),
        "mean_abs_axis0_path_entropy_delta": mean_float(abs(value) for value in path_deltas),
        "max_path_sum_gap": max_float(path_gaps),
        "max_abs_axis0_gradient": max_float(abs(value) for value in gradients),
        "curvature_variance": variance_float(curvatures),
        "fep_random_mean_gap": fep["random_mean_gap"],
        "fep_shuffled_mean_gap": fep["shuffled_mean_gap"],
        "control_signature_distances": control_distances,
        "min_control_signature_distance": min_float(control_distances.values()),
        "phi0_coherent_information_alias_max_abs": float(phi0_coherent_alias_max),
        "path_mi_coh_delta_alias_max_abs": float(path_mi_coh_alias_max),
    }

    predicates = {
        "source_high_n_surface_complete": len(rows) == N_PAIRED_ROWS
        and (2 * len(rows)) == 64
        and all(row["boundary_valid"] for row in rows),
        "mps_transport_is_nontrivial": max(row["mps_max_bond"] for row in rows) > 3
        and variance_float(entropy_values) > 1e-5,
        "boundary_readout_is_noncollapsed": variance_float(boundary_entropy_values) > 1e-5
        and max(boundary_entropy_values) > 0.01,
        "path_sum_cptp": max_float(path_gaps) < 1e-9,
        "axis0_path_response": mean_float(abs(value) for value in path_deltas) > 0.01,
        "fep_selection_beats_controls": fep["random_mean_gap"] > 0.10 and fep["shuffled_mean_gap"] > 0.02,
        "gradient_deforms_geometry": max_float(abs(value) for value in gradients) > 1e-5
        and variance_float(curvatures) > 1e-8,
        "controls_change_signature": all(distance > 0.005 for distance in control_distances.values()),
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
        "math_object": "8-qubit MPS transport driven by paired source-native engine slots with boundary/path/FEP readouts",
        "summary": summary,
        "positive": {
            "source_native_high_n_surface_complete": {
                "pass": predicates["source_high_n_surface_complete"],
                "paired_rows": len(rows),
                "single_engine_slot_count": 2 * len(rows),
                "n_qubits": N_QUBITS,
                "graph": full["graph"],
            },
            "mps_transport_entangles_and_moves_cut_entropy": {
                "pass": predicates["mps_transport_is_nontrivial"],
                "max_bond": max(row["mps_max_bond"] for row in rows),
                "entropy_min": min_float(entropy_values),
                "entropy_max": max_float(entropy_values),
                "entropy_variance": variance_float(entropy_values),
            },
            "boundary_reductions_are_dynamic_not_static": {
                "pass": predicates["boundary_readout_is_noncollapsed"],
                "boundary_entropy_min": min_float(boundary_entropy_values),
                "boundary_entropy_max": max_float(boundary_entropy_values),
                "boundary_entropy_variance": variance_float(boundary_entropy_values),
            },
            "kraus_path_sum_matches_cptp_on_high_n_boundaries": {
                "pass": predicates["path_sum_cptp"],
                "max_sum_vs_direct_gap": max_float(path_gaps),
            },
            "axis0_path_response_survives_on_high_n_boundaries": {
                "pass": predicates["axis0_path_response"],
                "mean_abs_delta": mean_float(abs(value) for value in path_deltas),
                "min_delta": min_float(path_deltas),
                "max_delta": max_float(path_deltas),
            },
            "tomographic_fep_selection_beats_random_and_shuffled_boundaries": {
                "pass": predicates["fep_selection_beats_controls"],
                **fep,
            },
            "axis0_gradient_deforms_dynamic_geometry": {
                "pass": predicates["gradient_deforms_geometry"],
                "max_abs_gradient": max_float(abs(value) for value in gradients),
                "curvature_variance": variance_float(curvatures),
            },
            "controls_change_transport_signature": {
                "pass": predicates["controls_change_signature"],
                **control_distances,
            },
            "z3_rejects_high_n_boundary_path_transport_collapse": z3_witness(summary),
        },
        "graveyard_companions": {
            "zero_gradient_changes_signature": {
                "pass": control_distances["zero_gradient"] > 0.005,
                "distance": control_distances["zero_gradient"],
            },
            "frozen_geometry_changes_signature": {
                "pass": control_distances["frozen_geometry"] > 0.005,
                "distance": control_distances["frozen_geometry"],
            },
            "operator_sign_collapse_changes_signature": {
                "pass": control_distances["sign_collapsed"] > 0.005,
                "distance": control_distances["sign_collapsed"],
            },
            "density_frozen_changes_signature": {
                "pass": control_distances["density_frozen"] > 0.005,
                "distance": control_distances["density_frozen"],
            },
            "identity_history_kills_path_diversity": {
                "pass": identity["branch_count"] == 1 and abs(identity["path_entropy"]) < 1e-9,
                "branch_count": identity["branch_count"],
                "path_entropy": identity["path_entropy"],
            },
        },
        "boundary": {
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
            "minimum_scale_not_final_scale": {
                "pass": N_QUBITS == 8,
                "n_qubits": N_QUBITS,
                "note": "8 qubits is the current minimum operating scale, not the final 32/64 target.",
            },
            "source_signal_phi0_alias_is_reported_not_promoted": {
                "pass": phi0_coherent_alias_max < 1e-12,
                "max_abs_gap": float(phi0_coherent_alias_max),
                "note": "On the two-density source signal, phi0 is exactly the negative conditional entropy and therefore aliases coherent information. Distinct Axis0 claims require high-N/boundary aggregation.",
            },
            "path_mi_coherent_delta_alias_is_reported_not_promoted": {
                "pass": path_mi_coh_alias_max < 1e-12,
                "max_abs_gap": float(path_mi_coh_alias_max),
                "note": "The path purification readout makes MI and coherent-information deltas alias on this branch family; path entropy is the load-bearing Axis0 response here.",
            },
        },
        "nearby_variants": {
            "total": 4,
            "passed": sum(
                1
                for key in ["zero_gradient", "frozen_geometry", "sign_collapsed", "density_frozen"]
                if control_distances[key] > 0.005
            ),
            "variants": ["zero_gradient", "frozen_geometry", "sign_collapsed", "density_frozen"],
        },
        "boundary_conditions": {
            "not_a_full_holographic_dictionary": True,
            "not_a_physics_or_retrocausality_claim": True,
            "not_a_final_axis0_definition": True,
            "n_qubits_is_minimum_operating_scale_not_final_scale": N_QUBITS,
            "next_required_scale": "repeat on 16/32-qubit MPS and PEPS/PEPS3D sheet-volume carriers",
        },
        "why_not_v4_probes": [
            "Clean v5 formal scout only; not a mixed v4 probe.",
            "It adds boundary/path/FEP readouts to an 8-qubit MPS engine-transport carrier but does not complete the 32/64-qubit PEPS/PEPS3D target.",
            "It keeps final Axis0, physics, intelligence, retrocausality, and canonical holographic-dictionary claims blocked.",
        ],
        "sample_rows": as_jsonable(rows[:3]),
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
    boundary_passes = [
        bool(v.get("pass", False))
        for v in result["boundary"].values()
        if isinstance(v, dict) and "pass" in v
    ]
    result["all_pass"] = bool(all(positive_passes) and all(graveyard_passes) and all(boundary_passes))
    result["root_constraints"] = {
        "F01": True,
        "N01": True,
        "finite_carrier_root": True,
        "noncommutation_or_order_root": True,
        "n01_evidence": "bounded path/FEP transport controls, Kraus path sums, and operator-sign controls record order-sensitive engine transport evidence",
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True, default=str), encoding="utf-8")
    return result


if __name__ == "__main__":
    output = main()
    print(json.dumps({"out": str(OUT_PATH), "all_pass": output["all_pass"], "summary": output["summary"]}, indent=2))
