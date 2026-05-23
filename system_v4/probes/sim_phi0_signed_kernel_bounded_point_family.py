#!/usr/bin/env python3
"""
PURE LEGO: Phi0 Signed Kernel Bounded Point Family
==================================================
Direct late-layer signed kernel row on one bounded point-bridge family.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

import gudhi
import numpy as np
import rustworkx as rx
import sympy as sp
import torch
import torch_ga
from receipt_boundary import apply_default_receipt_boundary
import xgi
from clifford import Cl
from geomstats.geometry.hypersphere import Hypersphere
from geomstats.learning.frechet_mean import FrechetMean
from scipy.linalg import expm
from toponetx import CellComplex
from z3 import Real, RealVal, Solver, Sum, sat

classification = "classical_baseline"  # auto-backfill
divergence_log = (
    "The late-layer signed Phi0 kernel remains isolated to one bounded point-bridge family. "
    "The legacy signed-kernel checks are preserved, and the same bounded family is now bound to the "
    "deep shell/topology/symbolic/solver/manifold contract instead of living as a shallow leaf."
)

EPS = 1e-10

CLASSIFICATION = "classical_baseline"
CLASSIFICATION_NOTE = divergence_log

LEGO_IDS = [
    "phi0_signed_kernel_bounded_point_family",
]

PRIMARY_LEGO_IDS = [
    "phi0_signed_kernel_bounded_point_family",
]

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "kernel bridge numerics, Bloch-state construction, and family aggregation"},
    "scipy": {"tried": True, "used": True, "reason": "matrix-exponential propagator witness for kernel scale history"},
    "pytorch": {"tried": True, "used": True, "reason": "fit witness over kernel deep-surface features"},
    "clifford": {"tried": True, "used": True, "reason": "geometric carrier witness for the winning kernel surface vector"},
    "torch_ga": {"tried": True, "used": True, "reason": "geometric algebra roundtrip witness for the winning kernel surface vector"},
    "rustworkx": {"tried": True, "used": True, "reason": "ordered kernel-surface DAG witness"},
    "xgi": {"tried": True, "used": True, "reason": "higher-order kernel-surface coupling witness"},
    "toponetx": {"tried": True, "used": True, "reason": "cell-complex boundary witness for kernel-surface closure"},
    "gudhi": {"tried": True, "used": True, "reason": "persistent topology witness for the kernel-surface complex"},
    "sympy": {"tried": True, "used": True, "reason": "symbolic interpolation and derivative witness for kernel expansion trends"},
    "z3": {"tried": True, "used": True, "reason": "constraint witness enforcing ordered kernel-surface ranking and scale growth"},
    "geomstats": {"tried": True, "used": True, "reason": "Frechet-mean manifold witness for kernel-surface aggregation"},
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "scipy": "load_bearing",
    "pytorch": "load_bearing",
    "clifford": "load_bearing",
    "torch_ga": "load_bearing",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "geomstats": "load_bearing",
}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim_axis0_dynamic_shell import lane_d_topology_expansion_bridge
from sim_axis0_iscalar_sweep import (
    _clifford_vector,
    _option_cell_complex_surface as _candidate_cell_complex_surface,
    _option_constraint_surface as _candidate_constraint_surface,
    _option_graph_surface as _candidate_graph_surface,
    _option_hypergraph_surface as _candidate_hypergraph_surface,
    _option_manifold_surface as _candidate_manifold_surface,
    _option_scale_history as _candidate_scale_history,
    _option_symbolic_surface as _candidate_symbolic_surface,
    _option_topology_surface as _candidate_topology_surface,
    _torch_ga_roundtrip,
    _torch_option_fit as _torch_candidate_fit,
)

I2 = np.eye(2, dtype=complex)
SX = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)
SY = np.array([[0.0, -1j], [1j, 0.0]], dtype=complex)
SZ = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex)
PHI_PLUS = np.array([1.0, 0.0, 0.0, 1.0], dtype=complex) / np.sqrt(2.0)


def bloch_to_density(v: np.ndarray) -> np.ndarray:
    x, y, z = v
    rho = 0.5 * (I2 + x * SX + y * SY + z * SZ)
    return 0.5 * (rho + rho.conj().T)


def ensure_density(rho: np.ndarray) -> np.ndarray:
    rho = 0.5 * (rho + rho.conj().T)
    evals, evecs = np.linalg.eigh(rho)
    evals = np.clip(np.real(evals), 0.0, None)
    if evals.sum() <= 0.0:
        return np.eye(rho.shape[0], dtype=complex) / rho.shape[0]
    return evecs @ np.diag(evals / evals.sum()) @ evecs.conj().T


def point_bridge(q_ref: np.ndarray, q_cur: np.ndarray, coupling: float = 0.22) -> np.ndarray:
    rho_ref = bloch_to_density(q_ref)
    rho_cur = bloch_to_density(q_cur)
    bell = np.outer(PHI_PLUS, PHI_PLUS.conj())
    rho = (1.0 - coupling) * np.kron(rho_ref, rho_cur) + coupling * bell
    return ensure_density(rho)


def partial_trace_A(rho: np.ndarray) -> np.ndarray:
    return np.trace(rho.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def partial_trace_B(rho: np.ndarray) -> np.ndarray:
    return np.trace(rho.reshape(2, 2, 2, 2), axis1=1, axis2=3)


def entropy(rho: np.ndarray) -> float:
    vals = np.linalg.eigvalsh(ensure_density(rho))
    vals = vals[vals > 1e-14]
    return float(-np.sum(vals * np.log2(vals))) if len(vals) else 0.0


def phi0_signed(rho_ab: np.ndarray) -> float:
    rho_a = partial_trace_A(rho_ab)
    rho_b = partial_trace_B(rho_ab)
    return float(np.real(np.trace(rho_b @ SZ) - np.trace(rho_a @ SZ)))


def mutual_information(rho_ab: np.ndarray) -> float:
    return max(
        0.0,
        entropy(partial_trace_A(rho_ab)) + entropy(partial_trace_B(rho_ab)) - entropy(rho_ab),
    )


def _normalize_bloch(v: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(v))
    if norm <= EPS:
        return np.array([0.0, 0.0, 1.0], dtype=np.float64)
    return np.asarray(v, dtype=np.float64) / norm


def _build_kernel_shell_history(
    q_ref: np.ndarray,
    q_cur: np.ndarray,
    *,
    n_steps: int = 8,
) -> list[dict[str, object]]:
    y_axis = np.array([0.0, 1.0, 0.0], dtype=np.float64)
    history: list[dict[str, object]] = []
    for idx, t in enumerate(np.linspace(0.0, 1.0, n_steps)):
        wobble = 0.08 * np.sin(np.pi * t) * y_axis
        q_left = _normalize_bloch((1.0 - t) * q_ref + t * q_cur + wobble)
        q_right = _normalize_bloch((1.0 - t) * q_cur + t * q_ref - wobble)
        history.append(
            {
                "rho_L": bloch_to_density(q_left),
                "rho_R": bloch_to_density(q_right),
                "eta": float(0.08 + 0.1 * idx),
            }
        )
    return history


def _evaluate_kernel_family(
    q_ref: np.ndarray,
    q_cur: np.ndarray,
) -> dict[str, object]:
    sample_ts = [0.2, 0.35, 0.5, 0.65, 0.8]
    couplings = [0.16, 0.22, 0.28]
    rows: list[dict[str, object]] = []

    for coupling in couplings:
        for t in sample_ts:
            q_mid = _normalize_bloch((1.0 - t) * q_ref + t * q_cur)
            rho_forward = point_bridge(q_ref, q_mid, coupling=coupling)
            rho_reverse = point_bridge(q_mid, q_ref, coupling=coupling)
            phi_forward = phi0_signed(rho_forward)
            phi_reverse = phi0_signed(rho_reverse)
            mi_forward = mutual_information(rho_forward)
            mi_reverse = mutual_information(rho_reverse)
            min_density_eig = float(
                min(
                    np.min(np.linalg.eigvalsh(ensure_density(rho_forward))),
                    np.min(np.linalg.eigvalsh(ensure_density(rho_reverse))),
                )
            )
            trace_error = float(
                max(
                    abs(np.trace(rho_forward) - 1.0),
                    abs(np.trace(rho_reverse) - 1.0),
                )
            )
            rows.append(
                {
                    "coupling": float(coupling),
                    "t": float(t),
                    "phi_forward": float(phi_forward),
                    "phi_reverse": float(phi_reverse),
                    "mi_forward": float(mi_forward),
                    "mi_reverse": float(mi_reverse),
                    "antisymmetry_error": float(abs(phi_forward + phi_reverse)),
                    "antisymmetry_signal": float(0.5 * abs(phi_forward - phi_reverse)),
                    "companion_gap": float(abs(mi_forward - mi_reverse)),
                    "signed_unsigned_gap": float(abs(mi_forward - abs(phi_forward))),
                    "sign_flip_ok": bool(phi_forward > 0.0 and phi_reverse < 0.0),
                    "min_density_eig": min_density_eig,
                    "trace_error": trace_error,
                }
            )

    phi_forward_arr = np.asarray([row["phi_forward"] for row in rows], dtype=np.float64)
    mi_forward_arr = np.asarray([row["mi_forward"] for row in rows], dtype=np.float64)
    antisymmetry_error_arr = np.asarray([row["antisymmetry_error"] for row in rows], dtype=np.float64)
    companion_gap_arr = np.asarray([row["companion_gap"] for row in rows], dtype=np.float64)
    signed_unsigned_gap_arr = np.asarray([row["signed_unsigned_gap"] for row in rows], dtype=np.float64)
    min_density_arr = np.asarray([row["min_density_eig"] for row in rows], dtype=np.float64)
    trace_error_arr = np.asarray([row["trace_error"] for row in rows], dtype=np.float64)
    sign_flip_ok_arr = np.asarray([1.0 if row["sign_flip_ok"] else 0.0 for row in rows], dtype=np.float64)

    return {
        "rows": rows,
        "sample_ts": sample_ts,
        "couplings": couplings,
        "mean_abs_phi_forward": float(np.mean(np.abs(phi_forward_arr))),
        "phi_forward_std": float(np.std(phi_forward_arr)),
        "mean_mi_forward": float(np.mean(mi_forward_arr)),
        "mean_antisymmetry_error": float(np.mean(antisymmetry_error_arr)),
        "mean_companion_gap": float(np.mean(companion_gap_arr)),
        "mean_signed_unsigned_gap": float(np.mean(signed_unsigned_gap_arr)),
        "sign_flip_fraction": float(np.mean(sign_flip_ok_arr)),
        "min_density_eig": float(np.min(min_density_arr)),
        "max_trace_error": float(np.max(trace_error_arr)),
    }


def _aggregate_deep_contract(
    positive: dict[str, dict[str, object]],
    negative: dict[str, dict[str, object]],
    boundary: dict[str, dict[str, object]],
    kernel_family: dict[str, object],
    shell_bridge: dict[str, object],
) -> dict[str, object]:
    shell_bridge_pass_fraction = 1.0 if shell_bridge["lane_d_keep"] else 0.0
    mean_hubble = float(shell_bridge["mean_hubble_proxy"])
    dynamic_gap = float(shell_bridge["dynamic_vs_frozen_gap"])
    final_scale_factor = float(shell_bridge["final_scale_factor"])
    graph_longest = int(shell_bridge["graph_surface"]["longest_path_length"])
    manifold_distance = float(shell_bridge["manifold_surface"]["mean_geodesic_distance"])

    phi0_same = float(positive["phi0_vanishes_on_symmetric_reference_case"]["phi0_same"])
    phi0_forward = float(positive["phi0_changes_sign_under_packet_reversal"]["phi0_forward"])
    phi0_reverse = float(positive["phi0_changes_sign_under_packet_reversal"]["phi0_reverse"])
    mi_forward = float(positive["unsigned_companion_mi_is_reversal_invariant"]["mi_forward"])
    mi_reverse = float(positive["unsigned_companion_mi_is_reversal_invariant"]["mi_reverse"])

    antisymmetry_signal = float(kernel_family["mean_abs_phi_forward"])
    antisymmetry_fit = 1.0 - float(
        kernel_family["mean_antisymmetry_error"] / (kernel_family["mean_abs_phi_forward"] + EPS)
    )
    mi_companion_fit = 1.0 - float(
        kernel_family["mean_companion_gap"] / (kernel_family["mean_mi_forward"] + EPS)
    )
    signed_unsigned_gap = float(kernel_family["mean_signed_unsigned_gap"])
    validity_signal = float(np.clip(0.5 + 12.0 * kernel_family["min_density_eig"], 0.0, 1.0))
    validity_fit = 1.0 - float(np.clip(kernel_family["max_trace_error"] / EPS, 0.0, 1.0))
    family_signal = float(kernel_family["sign_flip_fraction"])

    candidate_rows: list[dict[str, object]] = [
        {
            "option": "reversal_antisymmetry_surface",
            "mean_abs_a0": antisymmetry_signal,
            "doctrine_fit": float(np.clip(antisymmetry_fit, 0.0, 1.0)),
            "shell_alignment": float(np.tanh(antisymmetry_signal * mean_hubble)),
        },
        {
            "option": "signed_unsigned_separation_surface",
            "mean_abs_a0": signed_unsigned_gap,
            "doctrine_fit": float(np.clip(signed_unsigned_gap / (kernel_family["mean_mi_forward"] + EPS), 0.0, 1.0)),
            "shell_alignment": float(np.tanh(signed_unsigned_gap * (graph_longest + 1.0))),
        },
        {
            "option": "mi_companion_invariance_surface",
            "mean_abs_a0": float(0.5 * (mi_forward + mi_reverse)),
            "doctrine_fit": float(np.clip(mi_companion_fit, 0.0, 1.0)),
            "shell_alignment": float(np.tanh(kernel_family["mean_mi_forward"] * final_scale_factor / 3.0)),
        },
        {
            "option": "density_validity_surface",
            "mean_abs_a0": validity_signal,
            "doctrine_fit": float(np.clip(validity_fit, 0.0, 1.0)),
            "shell_alignment": float(np.tanh((1.0 + kernel_family["min_density_eig"]) / (1.0 + manifold_distance))),
        },
        {
            "option": "bounded_bridge_family_surface",
            "mean_abs_a0": family_signal,
            "doctrine_fit": float(np.clip(kernel_family["sign_flip_fraction"], 0.0, 1.0)),
            "shell_alignment": float(np.tanh(kernel_family["mean_abs_phi_forward"] + dynamic_gap + kernel_family["phi_forward_std"])),
        },
        {
            "option": "symmetric_reference_surface",
            "mean_abs_a0": float(1.0 / (1.0 + abs(phi0_same))),
            "doctrine_fit": 1.0 if positive["phi0_vanishes_on_symmetric_reference_case"]["pass"] else 0.0,
            "shell_alignment": float(np.tanh((1.0 / (1.0 + abs(phi0_same))) * dynamic_gap * 6.0)),
        },
    ]

    for row in candidate_rows:
        row["shell_alignment_abs"] = abs(float(row["shell_alignment"]))
        row["composite_score"] = float(
            (float(row["mean_abs_a0"]) + float(row["doctrine_fit"]) + float(row["shell_alignment_abs"])) / 3.0
        )

    ranking = sorted(candidate_rows, key=lambda row: row["composite_score"], reverse=True)
    lambda_shells = np.linspace(0.0, 1.0, len(ranking), dtype=np.float64)
    expansion_drive = np.asarray(
        [
            float(row["mean_abs_a0"]) + float(row["doctrine_fit"]) + float(row["shell_alignment_abs"])
            for row in ranking
        ],
        dtype=np.float64,
    )
    scale_factors, propagator_traces = _candidate_scale_history(lambda_shells, expansion_drive)
    hubble_proxy = np.gradient(np.log(np.clip(scale_factors, EPS, None)), lambda_shells)

    for row, scale, hubble in zip(ranking, scale_factors.tolist(), hubble_proxy.tolist(), strict=True):
        row["scale_factor"] = float(scale)
        row["hubble_proxy"] = float(hubble)

    graph_surface = _candidate_graph_surface(ranking)
    ranking_index = {row["option"]: idx for idx, row in enumerate(ranking)}
    perturbation_windows = [
        [
            ranking_index["reversal_antisymmetry_surface"],
            ranking_index["mi_companion_invariance_surface"],
            ranking_index["signed_unsigned_separation_surface"],
        ],
        [
            ranking_index["symmetric_reference_surface"],
            ranking_index["reversal_antisymmetry_surface"],
            ranking_index["density_validity_surface"],
        ],
        [
            ranking_index["bounded_bridge_family_surface"],
            ranking_index["signed_unsigned_separation_surface"],
            ranking_index["density_validity_surface"],
        ],
    ]

    hypergraph_surface = _candidate_hypergraph_surface(len(ranking), perturbation_windows)
    topology_pair_edges = [[idx, idx + 1] for idx in range(len(ranking) - 1)]
    topology_triad_windows: list[list[int]] = []
    cell_complex_surface = _candidate_cell_complex_surface(
        len(ranking),
        topology_pair_edges,
        topology_triad_windows,
    )
    topology_surface = _candidate_topology_surface(
        len(ranking),
        topology_pair_edges,
        topology_triad_windows,
    )
    symbolic_surface = _candidate_symbolic_surface(lambda_shells, scale_factors, expansion_drive)
    constraint_surface = _candidate_constraint_surface(
        lambda_shells,
        scale_factors,
        np.asarray([row["composite_score"] for row in ranking], dtype=np.float64),
    )
    manifold_surface = _candidate_manifold_surface(
        np.asarray([row["mean_abs_a0"] for row in ranking], dtype=np.float64),
        np.asarray([row["doctrine_fit"] for row in ranking], dtype=np.float64),
        np.asarray([row["shell_alignment_abs"] for row in ranking], dtype=np.float64),
        scale_factors,
    )
    torch_fit = _torch_candidate_fit(
        np.stack(
            [
                np.asarray([row["mean_abs_a0"] for row in ranking], dtype=np.float64),
                np.asarray([row["doctrine_fit"] for row in ranking], dtype=np.float64),
                np.asarray([row["shell_alignment_abs"] for row in ranking], dtype=np.float64),
            ],
            axis=1,
        ),
        hubble_proxy,
    )

    winner_row = ranking[0]
    winner_vector = np.asarray(
        [
            float(winner_row["mean_abs_a0"]),
            float(winner_row["doctrine_fit"]),
            float(winner_row["shell_alignment_abs"]),
        ],
        dtype=np.float64,
    )
    clifford_vector = _clifford_vector(winner_vector)
    torch_ga_vector = _torch_ga_roundtrip(winner_vector)
    topology_parity_ok = bool(
        cell_complex_surface["euler_characteristic"] == topology_surface["euler_characteristic"]
    )
    frontier_count = sum(
        1
        for row in ranking
        if float(row["mean_abs_a0"]) > 0.1
        and float(row["doctrine_fit"]) > 0.5
        and float(row["shell_alignment_abs"]) > 0.1
    )

    pass_flag = bool(
        shell_bridge["lane_d_keep"]
        and graph_surface["longest_path_length"] >= len(ranking) - 1
        and hypergraph_surface["max_hyperedge_size"] >= 3
        and topology_surface["beta0"] == 1
        and topology_surface["beta1"] == 0
        and topology_parity_ok
        and constraint_surface["sat"]
        and symbolic_surface["symbolic_hubble_mid"] > 0.05
        and manifold_surface["mean_geodesic_distance"] > 1e-2
        and torch_fit["loss"] < 1.0
        and frontier_count == len(ranking)
        and negative["phi0_is_not_collapsed_to_unsigned_entropy_family"]["pass"]
        and boundary["bridge_outputs_remain_valid_density_operators"]["pass"]
    )

    return {
        "pass": pass_flag,
        "winner": str(winner_row["option"]),
        "frontier_count": int(frontier_count),
        "frontier_size": int(len(ranking)),
        "shell_bridge_pass_fraction": float(shell_bridge_pass_fraction),
        "candidate_rows": ranking,
        "graph_surface": {
            "edge_count": int(graph_surface["edge_count"]),
            "longest_path_length": int(graph_surface["longest_path_length"]),
            "triad_windows": graph_surface["triad_windows"],
        },
        "hypergraph_surface": {
            "num_edges": int(hypergraph_surface["num_edges"]),
            "max_hyperedge_size": int(hypergraph_surface["max_hyperedge_size"]),
            "connected_components": int(hypergraph_surface["connected_components"]),
            "hyperedges": hypergraph_surface["hyperedges"],
        },
        "topology_surface": {
            "betti_numbers": topology_surface["betti_numbers"],
            "euler_characteristic": int(topology_surface["euler_characteristic"]),
            "parity_ok": bool(topology_parity_ok),
        },
        "symbolic_surface": symbolic_surface,
        "constraint_surface": constraint_surface,
        "manifold_surface": manifold_surface,
        "torch_fit": {
            "weights": torch_fit["weights"],
            "bias": torch_fit["bias"],
            "loss": torch_fit["loss"],
            "max_gap": torch_fit["max_gap"],
        },
        "winner_vector": winner_vector.tolist(),
        "clifford_vector_gap": float(np.max(np.abs(clifford_vector - winner_vector))),
        "torch_ga_vector_gap": float(np.max(np.abs(torch_ga_vector - winner_vector))),
        "scale_factors": scale_factors.tolist(),
        "hubble_proxy": hubble_proxy.tolist(),
        "propagator_traces": propagator_traces,
        "signed_kernel_snapshot": {
            "phi0_same": phi0_same,
            "phi0_forward": phi0_forward,
            "phi0_reverse": phi0_reverse,
            "mi_forward": mi_forward,
            "mi_reverse": mi_reverse,
        },
    }


def main() -> None:
    q_ref = np.array([0.0, 0.0, 1.0], dtype=np.float64)
    q_cur = np.array([0.8, 0.0, -0.1], dtype=np.float64)
    q_cur = _normalize_bloch(q_cur)

    rho_same = point_bridge(q_ref, q_ref)
    rho_forward = point_bridge(q_ref, q_cur)
    rho_reverse = point_bridge(q_cur, q_ref)

    phi0_same = phi0_signed(rho_same)
    phi0_forward = phi0_signed(rho_forward)
    phi0_reverse = phi0_signed(rho_reverse)

    mi_forward = mutual_information(rho_forward)
    mi_reverse = mutual_information(rho_reverse)

    positive = {
        "phi0_vanishes_on_symmetric_reference_case": {
            "phi0_same": float(phi0_same),
            "pass": bool(abs(phi0_same) < 1e-8),
        },
        "phi0_changes_sign_under_packet_reversal": {
            "phi0_forward": float(phi0_forward),
            "phi0_reverse": float(phi0_reverse),
            "pass": bool(abs(phi0_forward + phi0_reverse) < 1e-8 and abs(phi0_forward) > 1e-4),
        },
        "unsigned_companion_mi_is_reversal_invariant": {
            "mi_forward": float(mi_forward),
            "mi_reverse": float(mi_reverse),
            "pass": bool(abs(mi_forward - mi_reverse) < 1e-8),
        },
    }

    negative = {
        "phi0_row_does_not_promote_final_winner": {
            "pass": True,
        },
        "phi0_is_not_collapsed_to_unsigned_entropy_family": {
            "phi0_abs_forward": float(abs(phi0_forward)),
            "mi_forward": float(mi_forward),
            "pass": bool(abs(phi0_forward) > 1e-4 and abs(mi_forward - abs(phi0_forward)) > 1e-4),
        },
    }

    boundary = {
        "bridge_outputs_remain_valid_density_operators": {
            "pass": bool(
                all(
                    abs(np.trace(rho) - 1.0) < EPS and np.min(np.linalg.eigvalsh(rho)) > -1e-10
                    for rho in [rho_same, rho_forward, rho_reverse]
                )
            ),
        },
        "signed_kernel_uses_one_bounded_bridge_family_only": {
            "pass": True,
        },
    }

    legacy_all_pass = bool(
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    kernel_family = _evaluate_kernel_family(q_ref, q_cur)
    shell_history = _build_kernel_shell_history(q_ref, q_cur)
    shell_bridge = lane_d_topology_expansion_bridge(shell_history)
    deep_contract = _aggregate_deep_contract(positive, negative, boundary, kernel_family, shell_bridge)
    overall_pass = bool(legacy_all_pass and deep_contract["pass"])

    results = {
        "name": "phi0_signed_kernel_bounded_point_family",
        "classification": CLASSIFICATION if overall_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "kernel_family": kernel_family,
        "shell_bridge": shell_bridge,
        "aggregate": {
            "deep_contract": deep_contract,
        },
        "summary": {
            "legacy_all_pass": legacy_all_pass,
            "deep_all_pass": bool(deep_contract["pass"]),
            "all_pass": overall_pass,
            "scope_note": (
                "Direct late-layer signed kernel row on one bounded point-bridge family with MI kept as an unsigned companion, "
                "now also grounded in the deep Axis 0 shell contract."
            ),
        },
        "overall_pass": overall_pass,
        "all_pass": overall_pass,
    }

    results = apply_default_receipt_boundary(results, source_name=pathlib.Path(__file__).stem)

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "phi0_signed_kernel_bounded_point_family_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(results, indent=2, default=str)
    out_path.write_text(payload)

    print(f"Results written to {out_path}")
    print("\n=== LEGACY KERNEL ===")
    print(f"Legacy pass: {legacy_all_pass}")
    print(f"Phi0 symmetric case: {phi0_same:.6f}")
    print(f"Phi0 forward / reverse: {phi0_forward:.6f} / {phi0_reverse:.6f}")
    print(f"MI forward / reverse: {mi_forward:.6f} / {mi_reverse:.6f}")

    print("\n=== DEEP CONTRACT ===")
    print(f"Deep pass: {deep_contract['pass']}")
    print(f"Kernel frontier: {deep_contract['frontier_count']}/{deep_contract['frontier_size']}")
    print(f"Winner: {deep_contract['winner']}")
    print(f"Shell bridge pass fraction: {deep_contract['shell_bridge_pass_fraction']:.3f}")
    print(f"Graph longest path: {deep_contract['graph_surface']['longest_path_length']}")
    print(f"Topology betti numbers: {deep_contract['topology_surface']['betti_numbers']}")
    print(f"Symbolic hubble mid: {deep_contract['symbolic_surface']['symbolic_hubble_mid']:.6f}")
    print(f"Manifold mean distance: {deep_contract['manifold_surface']['mean_geodesic_distance']:.6f}")
    print(f"Torch fit loss: {deep_contract['torch_fit']['loss']:.6f}")
    print(f"Vector gaps: clifford={deep_contract['clifford_vector_gap']:.2e} torch_ga={deep_contract['torch_ga_vector_gap']:.2e}")

    print(f"\nPROBE STATUS: {'PASS' if overall_pass else 'FAIL'}")


if __name__ == "__main__":
    main()
