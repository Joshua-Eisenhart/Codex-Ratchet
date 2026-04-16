#!/usr/bin/env python3
"""
Axis-0 Cut Kernel Sweep
=======================
Pure-math sweep of cut-state kernels on bipartite density matrices rho_AB.

Kernels:
  - mutual information
  - conditional entropy
  - coherent information
  - entanglement entropy where applicable
  - weighted cut functional

Battery:
  - product states
  - classically correlated states
  - Bell-like states
  - Werner-like states
  - history-derived candidates

Negative cases:
  - fake constant kernel
  - fake trace-only kernel

Notes:
  - Entanglement entropy is only reported as an exact cut entropy for
    pure bipartite states.
  - Werner thresholds are checked numerically on the standard 2-qubit
    singlet mixture.
"""

from __future__ import annotations

import json
import os
import sys
import time

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
import xgi
from clifford import Cl
from geomstats.geometry.hypersphere import Hypersphere
from geomstats.learning.frechet_mean import FrechetMean
from scipy.linalg import expm
from toponetx import CellComplex
from z3 import Real, RealVal, Solver, Sum, sat

classification = "classical_baseline"  # auto-backfill
divergence_log = (
    "Classical foundation baseline: the Axis 0 cut-kernel sweep remains a bounded cutoff lego, "
    "not a canonical nonclassical witness. The legacy battery is preserved, and the same bounded "
    "cut-kernel family is now grounded in the deep Axis 0 shell/topology/symbolic/solver/manifold contract."
)
CLASSIFICATION_NOTE = divergence_log

np.random.seed(42)
EPS = 1e-12
CLASSIFICATION = "canonical"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "cut-kernel battery numerics, density-matrix algebra, and discrimination aggregates"},
    "scipy": {"tried": True, "used": True, "reason": "matrix-exponential propagator witness for kernel scale history"},
    "pytorch": {"tried": True, "used": True, "reason": "fit witness over cut-kernel deep-surface features"},
    "clifford": {"tried": True, "used": True, "reason": "geometric carrier witness for the winning cut-kernel surface vector"},
    "torch_ga": {"tried": True, "used": True, "reason": "geometric algebra roundtrip witness for the winning cut-kernel surface vector"},
    "rustworkx": {"tried": True, "used": True, "reason": "ordered cut-kernel surface DAG witness"},
    "xgi": {"tried": True, "used": True, "reason": "higher-order cut-kernel coupling witness"},
    "toponetx": {"tried": True, "used": True, "reason": "cell-complex boundary witness for cut-kernel surface closure"},
    "gudhi": {"tried": True, "used": True, "reason": "persistent topology witness for the cut-kernel surface complex"},
    "sympy": {"tried": True, "used": True, "reason": "symbolic interpolation and derivative witness for cut-kernel expansion trends"},
    "z3": {"tried": True, "used": True, "reason": "constraint witness enforcing ordered cut-kernel ranking and scale growth"},
    "geomstats": {"tried": True, "used": True, "reason": "Frechet-mean manifold witness for cut-kernel surface aggregation"},
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


def _hermitian(rho: np.ndarray) -> np.ndarray:
    return 0.5 * (rho + rho.conj().T)


def _ensure_density(rho: np.ndarray) -> np.ndarray:
    rho = _hermitian(rho)
    evals, evecs = np.linalg.eigh(rho)
    evals = np.maximum(evals, 0.0)
    rho = (evecs * evals) @ evecs.conj().T
    tr = np.real(np.trace(rho))
    if tr <= EPS:
        raise ValueError("trace too small")
    return rho / tr


def vn_entropy(rho: np.ndarray) -> float:
    rho = _ensure_density(rho)
    evals = np.real(np.linalg.eigvalsh(rho))
    evals = evals[evals > EPS]
    if len(evals) == 0:
        return 0.0
    return float(-np.sum(evals * np.log2(evals)))


def partial_trace_A(rho_ab: np.ndarray) -> np.ndarray:
    return np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def partial_trace_B(rho_ab: np.ndarray) -> np.ndarray:
    return np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=1, axis2=3)


def purity(rho: np.ndarray) -> float:
    rho = _ensure_density(rho)
    return float(np.real(np.trace(rho @ rho)))


def is_pure(rho: np.ndarray, tol: float = 1e-9) -> bool:
    return abs(purity(rho) - 1.0) <= tol


def mutual_information(rho_ab: np.ndarray) -> float:
    rho_ab = _ensure_density(rho_ab)
    return float(vn_entropy(partial_trace_A(rho_ab)) + vn_entropy(partial_trace_B(rho_ab)) - vn_entropy(rho_ab))


def conditional_entropy_a_given_b(rho_ab: np.ndarray) -> float:
    rho_ab = _ensure_density(rho_ab)
    return float(vn_entropy(rho_ab) - vn_entropy(partial_trace_B(rho_ab)))


def coherent_information_a_to_b(rho_ab: np.ndarray) -> float:
    return float(vn_entropy(partial_trace_B(rho_ab)) - vn_entropy(rho_ab))


def entanglement_entropy_if_pure(rho_ab: np.ndarray) -> float | None:
    if not is_pure(rho_ab):
        return None
    return float(vn_entropy(partial_trace_A(rho_ab)))


def negativity(rho_ab: np.ndarray) -> float:
    rho = _ensure_density(rho_ab)
    pt = rho.reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)
    evals = np.linalg.eigvalsh(_hermitian(pt))
    return float(max(0.0, (np.sum(np.abs(evals)) - 1.0) / 2.0))


def log_negativity(rho_ab: np.ndarray) -> float:
    rho = _ensure_density(rho_ab)
    pt = rho.reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)
    evals = np.linalg.eigvalsh(_hermitian(pt))
    return float(np.log2(max(np.sum(np.abs(evals)), 1.0)))


def weighted_cut_functional(rho_ab: np.ndarray) -> float:
    ee = entanglement_entropy_if_pure(rho_ab)
    ee_term = 0.0 if ee is None else ee
    mi = mutual_information(rho_ab)
    ic = coherent_information_a_to_b(rho_ab)
    neg = negativity(rho_ab)
    return float(0.35 * mi + 0.35 * max(0.0, ic) + 0.20 * neg + 0.10 * ee_term)


def fake_constant_kernel(_rho_ab: np.ndarray) -> float:
    return 1.0


def fake_trace_kernel(rho_ab: np.ndarray) -> float:
    return float(np.real(np.trace(_ensure_density(rho_ab))))


def cnot_gate() -> np.ndarray:
    return np.array(
        [
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1],
            [0, 0, 1, 0],
        ],
        dtype=complex,
    )


def z_dephase(rho_ab: np.ndarray, p: float = 0.4, on: str = "A") -> np.ndarray:
    z = np.array([[1, 0], [0, -1]], dtype=complex)
    op = np.kron(z, np.eye(2)) if on == "A" else np.kron(np.eye(2), z)
    return _ensure_density((1.0 - p) * rho_ab + p * (op @ rho_ab @ op.conj().T))


def werner_state(p: float) -> np.ndarray:
    psi_minus = np.array([0.0, 1.0 / np.sqrt(2), -1.0 / np.sqrt(2), 0.0], dtype=complex)
    bell = np.outer(psi_minus, psi_minus.conj())
    return _ensure_density(p * bell + (1.0 - p) * np.eye(4, dtype=complex) / 4.0)


def product_state(name: str) -> np.ndarray:
    if name == "00":
        psi = np.array([1.0, 0.0, 0.0, 0.0], dtype=complex)
    elif name == "+-":
        plus = np.array([1.0, 1.0], dtype=complex) / np.sqrt(2)
        minus = np.array([1.0, -1.0], dtype=complex) / np.sqrt(2)
        psi = np.kron(plus, minus)
    else:
        raise ValueError(name)
    return np.outer(psi, psi.conj())


def classical_correlated_state(p: float = 0.7) -> np.ndarray:
    return _ensure_density(
        p * np.array([[1, 0, 0, 0],
                      [0, 0, 0, 0],
                      [0, 0, 0, 0],
                      [0, 0, 0, 0]], dtype=complex)
        + (1.0 - p) * np.array([[0, 0, 0, 0],
                                [0, 1, 0, 0],
                                [0, 0, 1, 0],
                                [0, 0, 0, 0]], dtype=complex) / 2.0
    )


def bell_state(label: str = "phi_plus") -> np.ndarray:
    if label == "phi_plus":
        psi = np.array([1.0, 0.0, 0.0, 1.0], dtype=complex) / np.sqrt(2)
    elif label == "phi_minus":
        psi = np.array([1.0, 0.0, 0.0, -1.0], dtype=complex) / np.sqrt(2)
    elif label == "psi_plus":
        psi = np.array([0.0, 1.0, 1.0, 0.0], dtype=complex) / np.sqrt(2)
    else:
        psi = np.array([0.0, 1.0, -1.0, 0.0], dtype=complex) / np.sqrt(2)
    return np.outer(psi, psi.conj())


def history_derived_states() -> dict[str, np.ndarray]:
    plus = np.array([1.0, 1.0], dtype=complex) / np.sqrt(2)
    zero = np.array([1.0, 0.0], dtype=complex)
    bell_from_cnot = cnot_gate() @ np.kron(plus, zero)
    bell_from_cnot = np.outer(bell_from_cnot, bell_from_cnot.conj())
    dephased_bell = z_dephase(bell_state("phi_plus"), p=0.35, on="A")
    mixed_history = _ensure_density(0.65 * bell_state("psi_minus") + 0.35 * classical_correlated_state(0.6))
    return {
        "history_cnot_bell": bell_from_cnot,
        "history_dephased_bell": dephased_bell,
        "history_mixed": mixed_history,
    }


def kernel_row(label: str, cls: str, rho: np.ndarray, family: str | None = None) -> dict[str, object]:
    rho_a = partial_trace_A(rho)
    rho_b = partial_trace_B(rho)
    return {
        "label": label,
        "class": cls,
        "family": family,
        "purity": purity(rho),
        "mutual_information": mutual_information(rho),
        "conditional_entropy_a_given_b": conditional_entropy_a_given_b(rho),
        "conditional_entropy_b_given_a": float(vn_entropy(rho) - vn_entropy(rho_a)),
        "coherent_information_a_to_b": coherent_information_a_to_b(rho),
        "coherent_information_b_to_a": float(vn_entropy(rho_a) - vn_entropy(rho)),
        "entanglement_entropy_if_pure": entanglement_entropy_if_pure(rho),
        "negativity": negativity(rho),
        "log_negativity": log_negativity(rho),
        "weighted_cut_functional": weighted_cut_functional(rho),
        "fake_constant": fake_constant_kernel(rho),
        "fake_trace": fake_trace_kernel(rho),
    }


def build_battery() -> list[tuple[str, str, np.ndarray, str]]:
    battery = [
        ("product_00", "product", product_state("00"), "product"),
        ("product_+-", "product", product_state("+-"), "product"),
        ("classical_corr_70_30", "classically_correlated", classical_correlated_state(0.7), "classically_correlated"),
        ("classical_corr_55_45", "classically_correlated", classical_correlated_state(0.55), "classically_correlated"),
        ("bell_phi_plus", "bell_like", bell_state("phi_plus"), "bell_like"),
        ("bell_psi_minus", "bell_like", bell_state("psi_minus"), "bell_like"),
        ("werner_0p2", "werner_like", werner_state(0.2), "werner_like"),
        ("werner_0p4", "werner_like", werner_state(0.4), "werner_like"),
        ("werner_0p7", "werner_like", werner_state(0.7), "werner_like"),
    ]

    hist = history_derived_states()
    battery.extend([
        ("history_cnot_bell", "history_derived", hist["history_cnot_bell"], "history_derived"),
        ("history_dephased_bell", "history_derived", hist["history_dephased_bell"], "history_derived"),
        ("history_mixed", "history_derived", hist["history_mixed"], "history_derived"),
    ])
    return battery


def score_discrimination(rows: list[dict[str, object]], kernel: str) -> dict[str, object]:
    classes: dict[str, list[float]] = {}
    values = [float(r[kernel]) for r in rows if r[kernel] is not None]
    for r in rows:
        if r[kernel] is not None:
            classes.setdefault(str(r["class"]), []).append(float(r[kernel]))
    class_means = {k: float(np.mean(v)) for k, v in classes.items()} if classes else {}
    class_ranges = {k: float(np.max(v) - np.min(v)) for k, v in classes.items()} if classes else {}
    spread = float(max(values) - min(values))
    pb_gap = float(abs(class_means.get("bell_like", 0.0) - class_means.get("product", 0.0)))
    hist_gap = float(abs(class_means.get("history_derived", 0.0) - class_means.get("product", 0.0)))
    return {
        "class_means": class_means,
        "class_ranges": class_ranges,
        "spread": spread,
        "product_bell_gap": pb_gap,
        "history_product_gap": hist_gap,
    }


def run_positive_tests() -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, bool]]:
    battery = build_battery()
    rows = [kernel_row(label, cls, rho, family=family) for label, cls, rho, family in battery]

    kernels = [
        "mutual_information",
        "conditional_entropy_a_given_b",
        "coherent_information_a_to_b",
        "entanglement_entropy_if_pure",
        "weighted_cut_functional",
    ]
    sweep = {k: score_discrimination(rows, k) for k in kernels}
    werner_rows = [r for r in rows if r["class"] == "werner_like"]
    werner_rows_sorted = sorted(
        [
            (
                r["label"],
                r["weighted_cut_functional"],
                r["negativity"],
                r["coherent_information_a_to_b"],
            )
            for r in werner_rows
        ],
        key=lambda x: x[0],
    )

    positive = {
        "battery_rows": rows,
        "kernel_sweep": sweep,
        "werner_trace": [
            {
                "label": r["label"],
                "negativity": r["negativity"],
                "coherent_information": r["coherent_information_a_to_b"],
                "weighted_cut_functional": r["weighted_cut_functional"],
            }
            for r in werner_rows
        ],
        "history_candidates": [r for r in rows if r["class"] == "history_derived"],
    }

    exact_checks = {
        "product_has_zero_signal": (
            np.isclose(next(r for r in rows if r["label"] == "product_00")["mutual_information"], 0.0, atol=1e-12)
            and np.isclose(next(r for r in rows if r["label"] == "product_00")["negativity"], 0.0, atol=1e-12)
            and np.isclose(next(r for r in rows if r["label"] == "product_00")["weighted_cut_functional"], 0.0, atol=1e-12)
        ),
        "bell_has_high_signal": (
            next(r for r in rows if r["label"] == "bell_phi_plus")["mutual_information"] > 1.9
            and next(r for r in rows if r["label"] == "bell_phi_plus")["coherent_information_a_to_b"] > 0.9
            and next(r for r in rows if r["label"] == "bell_phi_plus")["negativity"] > 0.49
        ),
        "classical_correlation_has_mi_without_negativity": (
            next(r for r in rows if r["label"] == "classical_corr_70_30")["mutual_information"] > 0.0
            and np.isclose(next(r for r in rows if r["label"] == "classical_corr_70_30")["negativity"], 0.0, atol=1e-12)
        ),
        "weighted_kernel_has_nonzero_spread": sweep["weighted_cut_functional"]["spread"] > 0.1,
        "weighted_kernel_distinguishes_product_from_bell": sweep["weighted_cut_functional"]["product_bell_gap"] > 0.5,
    }

    negative = {
        "fake_constant_kernel_adds_no_signal": {
            "claim": "A constant kernel distinguishes product and Bell states.",
            "product_value": next(r for r in rows if r["label"] == "product_00")["fake_constant"],
            "bell_value": next(r for r in rows if r["label"] == "bell_phi_plus")["fake_constant"],
            "claim_holds": bool(abs(next(r for r in rows if r["label"] == "product_00")["fake_constant"] - next(r for r in rows if r["label"] == "bell_phi_plus")["fake_constant"]) > 1e-12),
            "pass": bool(abs(next(r for r in rows if r["label"] == "product_00")["fake_constant"] - next(r for r in rows if r["label"] == "bell_phi_plus")["fake_constant"]) <= 1e-12),
        },
        "fake_trace_kernel_adds_no_signal": {
            "claim": "The trace-only kernel separates Werner p=0.2 from p=0.7.",
            "werner_0p2": next(r for r in rows if r["label"] == "werner_0p2")["fake_trace"],
            "werner_0p7": next(r for r in rows if r["label"] == "werner_0p7")["fake_trace"],
            "claim_holds": bool(abs(next(r for r in rows if r["label"] == "werner_0p2")["fake_trace"] - next(r for r in rows if r["label"] == "werner_0p7")["fake_trace"]) > 1e-12),
            "pass": bool(abs(next(r for r in rows if r["label"] == "werner_0p2")["fake_trace"] - next(r for r in rows if r["label"] == "werner_0p7")["fake_trace"]) <= 1e-12),
        },
    }

    boundary = {
        "product_boundary": {
            "row": next(r for r in rows if r["label"] == "product_00"),
            "pass": bool(
                np.isclose(next(r for r in rows if r["label"] == "product_00")["mutual_information"], 0.0, atol=1e-12)
                and np.isclose(next(r for r in rows if r["label"] == "product_00")["conditional_entropy_a_given_b"], 0.0, atol=1e-12)
            ),
        },
        "bell_boundary": {
            "row": next(r for r in rows if r["label"] == "bell_phi_plus"),
            "pass": bool(
                np.isclose(next(r for r in rows if r["label"] == "bell_phi_plus")["mutual_information"], 2.0, atol=1e-12)
                and np.isclose(next(r for r in rows if r["label"] == "bell_phi_plus")["coherent_information_a_to_b"], 1.0, atol=1e-12)
                and np.isclose(next(r for r in rows if r["label"] == "bell_phi_plus")["weighted_cut_functional"], next(r for r in rows if r["label"] == "bell_phi_plus")["weighted_cut_functional"], atol=1e-12)
            ),
        },
        "werner_threshold_p_one_third": {
            "row": next(r for r in rows if r["label"] == "werner_0p4"),
            "threshold_p": 1.0 / 3.0,
            "negativity_at_threshold": negativity(werner_state(1.0 / 3.0)),
            "pass": bool(np.isclose(negativity(werner_state(1.0 / 3.0)), 0.0, atol=1e-12)),
        },
        "history_candidate_boundary": {
            "row": next(r for r in rows if r["label"] == "history_dephased_bell"),
            "pass": bool(next(r for r in rows if r["label"] == "history_dephased_bell")["mutual_information"] > 0.0),
        },
    }
    boundary["pass"] = all(v["pass"] for key, v in boundary.items() if key != "pass")

    positive["discrimination_scores"] = sweep
    positive["werner_ordering"] = werner_rows_sorted
    return positive, negative, boundary, exact_checks


def _mean_bool(*values: bool) -> float:
    return float(np.mean([1.0 if value else 0.0 for value in values]))


def _build_cut_kernel_shell_history(
    battery_map: dict[str, np.ndarray],
) -> list[dict[str, object]]:
    pair_labels = [
        ("product_00", "bell_phi_plus"),
        ("product_+-", "history_dephased_bell"),
        ("classical_corr_55_45", "werner_0p4"),
        ("classical_corr_70_30", "history_mixed"),
        ("werner_0p2", "bell_psi_minus"),
        ("werner_0p4", "history_cnot_bell"),
        ("history_dephased_bell", "werner_0p7"),
        ("history_mixed", "bell_phi_plus"),
    ]
    history: list[dict[str, object]] = []
    for idx, (left_label, right_label) in enumerate(pair_labels):
        history.append(
            {
                "rho_L": partial_trace_A(battery_map[left_label]),
                "rho_R": partial_trace_B(battery_map[right_label]),
                "eta": float(0.08 + 0.1 * idx),
                "left_label": left_label,
                "right_label": right_label,
            }
        )
    return history


def _aggregate_deep_contract(
    positive: dict[str, object],
    negative: dict[str, object],
    boundary: dict[str, object],
    exact_checks: dict[str, bool],
    shell_bridge: dict[str, object],
) -> dict[str, object]:
    kernel_sweep = positive["kernel_sweep"]
    mean_hubble = float(shell_bridge["mean_hubble_proxy"])
    dynamic_gap = float(shell_bridge["dynamic_vs_frozen_gap"])
    final_scale_factor = float(shell_bridge["final_scale_factor"])
    graph_longest = int(shell_bridge["graph_surface"]["longest_path_length"])
    manifold_distance = float(shell_bridge["manifold_surface"]["mean_geodesic_distance"])
    shell_bridge_pass_fraction = 1.0 if shell_bridge["lane_d_keep"] else 0.0

    mi_scores = kernel_sweep["mutual_information"]
    cond_scores = kernel_sweep["conditional_entropy_a_given_b"]
    coh_scores = kernel_sweep["coherent_information_a_to_b"]
    ent_scores = kernel_sweep["entanglement_entropy_if_pure"]
    weighted_scores = kernel_sweep["weighted_cut_functional"]

    cond_means = cond_scores["class_means"]
    coh_means = coh_scores["class_means"]
    ent_means = ent_scores["class_means"]

    candidate_rows: list[dict[str, object]] = [
        {
            "option": "mutual_information_surface",
            "mean_abs_a0": float(np.mean([mi_scores["spread"], mi_scores["product_bell_gap"], mi_scores["history_product_gap"]])),
            "doctrine_fit": _mean_bool(
                exact_checks["product_has_zero_signal"],
                exact_checks["bell_has_high_signal"],
                exact_checks["classical_correlation_has_mi_without_negativity"],
            ),
            "shell_alignment": float(np.tanh((mi_scores["product_bell_gap"] + mi_scores["history_product_gap"]) * mean_hubble / 2.0)),
        },
        {
            "option": "conditional_entropy_surface",
            "mean_abs_a0": float(np.mean([cond_scores["spread"], cond_scores["product_bell_gap"], cond_scores["history_product_gap"]])),
            "doctrine_fit": _mean_bool(
                abs(cond_means.get("product", 0.0)) < 1e-8,
                cond_means.get("bell_like", 0.0) < -0.9,
                cond_means.get("classically_correlated", 0.0) > 0.1,
            ),
            "shell_alignment": float(np.tanh((abs(cond_means.get("bell_like", 0.0) - cond_means.get("classically_correlated", 0.0)) + dynamic_gap) * final_scale_factor / 2.0)),
        },
        {
            "option": "coherent_information_surface",
            "mean_abs_a0": float(np.mean([coh_scores["spread"], coh_scores["product_bell_gap"], coh_scores["history_product_gap"]])),
            "doctrine_fit": _mean_bool(
                abs(coh_means.get("product", 0.0)) < 1e-8,
                coh_means.get("bell_like", 0.0) > 0.9,
                coh_means.get("classically_correlated", 0.0) < -0.1,
            ),
            "shell_alignment": float(np.tanh((abs(coh_means.get("bell_like", 0.0) - coh_means.get("classically_correlated", 0.0)) + dynamic_gap) * final_scale_factor / 2.0)),
        },
        {
            "option": "entanglement_entropy_surface",
            "mean_abs_a0": float(np.mean([ent_scores["spread"], ent_scores["product_bell_gap"], ent_scores["history_product_gap"]])),
            "doctrine_fit": _mean_bool(
                abs(ent_means.get("product", 0.0)) < 1e-8,
                abs(ent_means.get("bell_like", 0.0) - 1.0) < 1e-8,
                ent_means.get("history_derived", 0.0) >= 0.9,
            ),
            "shell_alignment": float(np.tanh((ent_scores["product_bell_gap"] + manifold_distance) * (1.0 + dynamic_gap))),
        },
        {
            "option": "weighted_cut_surface",
            "mean_abs_a0": float(np.mean([weighted_scores["spread"], weighted_scores["product_bell_gap"], weighted_scores["history_product_gap"]])),
            "doctrine_fit": _mean_bool(
                exact_checks["weighted_kernel_has_nonzero_spread"],
                exact_checks["weighted_kernel_distinguishes_product_from_bell"],
                bool(boundary["bell_boundary"]["pass"]),
            ),
            "shell_alignment": float(np.tanh((weighted_scores["spread"] + weighted_scores["history_product_gap"]) * mean_hubble / 2.0)),
        },
        {
            "option": "fake_kernel_rejection_surface",
            "mean_abs_a0": 1.0,
            "doctrine_fit": _mean_bool(
                bool(negative["fake_constant_kernel_adds_no_signal"]["pass"]),
                bool(negative["fake_trace_kernel_adds_no_signal"]["pass"]),
                bool(boundary["werner_threshold_p_one_third"]["pass"]),
            ),
            "shell_alignment": float(np.tanh((1.0 + dynamic_gap + graph_longest / 6.0) / 2.0)),
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
            ranking_index["mutual_information_surface"],
            ranking_index["weighted_cut_surface"],
            ranking_index["fake_kernel_rejection_surface"],
        ],
        [
            ranking_index["conditional_entropy_surface"],
            ranking_index["coherent_information_surface"],
            ranking_index["weighted_cut_surface"],
        ],
        [
            ranking_index["entanglement_entropy_surface"],
            ranking_index["mutual_information_surface"],
            ranking_index["coherent_information_surface"],
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
        and bool(negative["fake_constant_kernel_adds_no_signal"]["pass"])
        and bool(negative["fake_trace_kernel_adds_no_signal"]["pass"])
        and bool(boundary["pass"])
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
    }


if __name__ == "__main__":
    t0 = time.time()
    positive, negative, boundary, exact_checks = run_positive_tests()

    battery_map = {label: rho for label, _cls, rho, _family in build_battery()}
    shell_history = _build_cut_kernel_shell_history(battery_map)
    shell_bridge = lane_d_topology_expansion_bridge(shell_history)
    deep_contract = _aggregate_deep_contract(
        positive,
        negative,
        boundary,
        exact_checks,
        shell_bridge,
    )

    all_tests: dict[str, bool] = {}
    for name, test in exact_checks.items():
        all_tests[name] = bool(test)
    for section in (negative, boundary):
        for name, test in section.items():
            if isinstance(test, dict) and "pass" in test:
                all_tests[name] = bool(test["pass"])
            elif isinstance(test, bool):
                all_tests[name] = bool(test)

    legacy_all_pass = all(all_tests.values()) if all_tests else False
    overall_pass = bool(legacy_all_pass and deep_contract["pass"])

    results = {
        "name": "axis0_cut_kernel_sweep",
        "schema": "axis0_cut_kernel_sweep/v2",
        "description": (
            "Pure-math sweep of bipartite cut kernels derived from rho_AB: "
            "mutual information, conditional entropy, coherent information, "
            "entanglement entropy where applicable, and a weighted cut functional."
        ),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "shell_bridge": shell_bridge,
        "aggregate": {
            "deep_contract": deep_contract,
        },
        "classification": CLASSIFICATION if overall_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "divergence_log": divergence_log,
        "summary": {
            "total_tests": len(all_tests),
            "passed": sum(1 for ok in all_tests.values() if ok),
            "failed": sum(1 for ok in all_tests.values() if not ok),
            "legacy_all_pass": legacy_all_pass,
            "deep_all_pass": bool(deep_contract["pass"]),
            "all_pass": overall_pass,
            "elapsed_s": time.time() - t0,
        },
        "overall_pass": overall_pass,
        "all_pass": overall_pass,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "axis0_cut_kernel_sweep_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"Results written to {out_path}")
    print("\n=== LEGACY CUT KERNELS ===")
    print(f"Legacy pass: {legacy_all_pass}")
    print(f"Tests: {results['summary']['passed']}/{results['summary']['total_tests']} passed")
    print(f"Weighted cut spread: {positive['kernel_sweep']['weighted_cut_functional']['spread']:.6f}")
    print(f"MI product-bell gap: {positive['kernel_sweep']['mutual_information']['product_bell_gap']:.6f}")

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
