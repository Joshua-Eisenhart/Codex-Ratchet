#!/usr/bin/env python3
"""
Shared Axis 0 lambda cross-lane semantics core.

This keeps the live bridge logic in one place so the standalone witness and
the lambda cosmology lane answer to the same contract.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

import cirq
import cvc5
import numpy as np
import pennylane as qml
import qutip
import sympy as sp
import torch
from cvc5 import Kind
from e3nn import o3
from torch_geometric.data import Data
from torch_geometric.nn import MessagePassing

from axis0_result_loader import load_axis0_result
from axis0_bridge_owner_packet_surface import load_bridge_owner_packet_surface
from axis0_constraint_types import build_distinguishability_constraint
from axis0_xi_law_fingerprint import (
    carrier_law_fingerprint,
    carrier_matches_law,
    entropy_law_fingerprint,
    pre_entropy_law_fingerprint,
    strict_law_fingerprint,
)
from sim_axis0_axis6_coupling_seam import (
    _aggregate_deep_contract as _seam_aggregate_deep_contract,
    _build_seam_shell_history,
    semantic_row_surface as _seam_semantic_row_surface,
    run_boundary_tests as _run_seam_boundary_tests,
    run_negative_tests as _run_seam_negative_tests,
    run_positive_tests as _run_seam_positive_tests,
)
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
from sim_axis0_pyg_proxy import (
    Axis0ProxyModel,
    _aggregate_deep_contract as _pyg_aggregate_deep_contract,
    _build_pyg_shell_history,
    build_pyg_chain_graph,
    semantic_row_surface as _pyg_semantic_row_surface,
    run_axis0_summary_test as _run_pyg_axis0_summary_test,
    run_boundary_tests as _run_pyg_boundary_tests,
    run_negative_tests as _run_pyg_negative_tests,
    run_positive_tests as _run_pyg_positive_tests,
    sweep_gradient_profile,
    verify_chain_admissibility_z3 as _verify_pyg_chain_admissibility_z3,
    verify_ic_formula_sympy as _verify_pyg_ic_formula_sympy,
)
from sim_axis0_through_shells import (
    _aggregate_deep_contract as _through_aggregate_deep_contract,
    _build_shell_projection_history,
    build_shell_order,
    semantic_row_surface as _through_semantic_row_surface,
    run_boundary_tests as _run_through_boundary_tests,
    run_negative_tests as _run_through_negative_tests,
    run_positive_tests as _run_through_positive_tests,
)
from sim_integration_quantum_open_entangle_correlator_mega_stack import (
    _bell_prep,
    _cirq_prep,
    _open_system_reference,
    _pennylane_prep,
    _qutip_evolution,
    _rho,
)

EPS = 1e-12
PAIRWISE_COSINE_THRESHOLD = 0.96
PAIRWISE_GAP_THRESHOLD = 0.40
MANIFOLD_DISTANCE_THRESHOLD = 1e-3
STRUCTURE_PATH_WEIGHT = 0.08
STRUCTURE_PYG_WEIGHT = 0.08

DEFAULT_THETA = 1.127
DEFAULT_PHI = -0.713
DEFAULT_GAMMA = 0.68
DEFAULT_T = 0.91
DEFAULT_RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"


def _persisted_result_paths(root: Path) -> dict[str, list[Path]]:
    return {
        "lambda_cosmology": [root / "sim_axis0_lambda_expansion_cosmology_stack_results.json"],
        "axis6_seam": [root / "sim_axis0_axis6_coupling_seam_results.json"],
        "through_shells": [
            root / "sim_axis0_through_shells_results.json",
            root / "axis0_through_shells_results.json",
        ],
        "pyg_proxy": [
            root / "sim_axis0_pyg_proxy_results.json",
            root / "axis0_pyg_proxy_results.json",
        ],
    }


def _refresh_persisted_result_artifact(lane: str) -> None:
    script_map = {
        "lambda_cosmology": "sim_axis0_lambda_expansion_cosmology_stack.py",
        "axis6_seam": "sim_axis0_axis6_coupling_seam.py",
        "through_shells": "sim_axis0_through_shells.py",
        "pyg_proxy": "sim_axis0_pyg_proxy.py",
    }
    script_name = script_map.get(lane)
    if script_name is None:
        raise KeyError(f"Unknown persisted semantic lane: {lane}")
    script_path = Path(__file__).resolve().parent / script_name
    proc = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(script_path.parent),
    )
    if proc.returncode != 0:
        detail = (proc.stdout + "\n" + proc.stderr).strip()
        raise RuntimeError(
            f"Refresh for persisted semantic lane {lane} failed with code {proc.returncode}\n{detail}"
        )


def ensure_persisted_semantic_rows(results_dir: str | Path | None = None) -> list[str]:
    root = Path(results_dir) if results_dir is not None else DEFAULT_RESULTS_DIR
    refreshed: list[str] = []
    paths = _persisted_result_paths(root)
    allow_refresh = root.resolve() == DEFAULT_RESULTS_DIR.resolve()
    for lane, candidates in paths.items():
        if any(path.exists() for path in candidates):
            continue
        if not allow_refresh:
            rendered = ", ".join(str(path) for path in candidates)
            raise FileNotFoundError(f"Persisted semantic row artifact missing: {rendered}")
        _refresh_persisted_result_artifact(lane)
        if not any(path.exists() for path in candidates):
            rendered = ", ".join(str(path) for path in candidates)
            raise FileNotFoundError(
                f"Persisted semantic row artifact still missing after refresh: {rendered}"
            )
        refreshed.append(lane)
    return refreshed


def _load_cosmology_case_fn():
    from sim_axis0_lambda_expansion_cosmology_stack import _cosmology_case

    return _cosmology_case


def _load_xi_packet_surface(results_dir: str | Path | None = None) -> dict[str, object]:
    root = Path(results_dir) if results_dir is not None else DEFAULT_RESULTS_DIR
    strict_result = load_axis0_result(root, "axis0_xi_strict_bakeoff_results.json")
    carrier_validation = json.loads((root / "carrier_selection_packet_validation.json").read_text())
    pre_entropy_validation = json.loads((root / "pre_entropy_packet_validation.json").read_text())
    entropy_validation = json.loads((root / "entropy_readout_packet_validation.json").read_text())
    stack_validation = json.loads((root / "axis0_stack_packet_validation.json").read_text())

    strict_fp = strict_law_fingerprint(strict_result)
    carrier_fp = carrier_validation.get(
        "xi_hist_carrier_semantics",
        carrier_law_fingerprint(carrier_validation),
    )
    pre_entropy_fp = pre_entropy_validation.get(
        "xi_hist_law_fingerprint",
        pre_entropy_law_fingerprint(pre_entropy_validation),
    )
    entropy_fp = entropy_validation.get(
        "xi_hist_law_fingerprint",
        entropy_law_fingerprint(entropy_validation),
    )
    stack_gate = next(
        item
        for item in stack_validation["gates"]
        if item["name"] == "S8_xi_hist_law_is_semantically_consistent_across_stack"
    )
    pass_flag = bool(
        stack_gate["pass"]
        and strict_fp == pre_entropy_fp
        and strict_fp == entropy_fp
        and carrier_matches_law(carrier_fp, strict_fp)
    )
    return {
        "pass": pass_flag,
        "stack_gate_pass": bool(stack_gate["pass"]),
        "strict_vs_pre_entropy_match": bool(strict_fp == pre_entropy_fp),
        "strict_vs_entropy_readout_match": bool(strict_fp == entropy_fp),
        "carrier_matches_strict_law": bool(carrier_matches_law(carrier_fp, strict_fp)),
        "strict_xi_law": strict_fp,
        "carrier_xi_semantics": carrier_fp,
    }


def _diag_density(prob: float) -> np.ndarray:
    p = float(np.clip(prob, 1e-6, 1.0 - 1e-6))
    return np.array([[p, 0.0], [0.0, 1.0 - p]], dtype=np.complex128)


def source_bridge_surface(theta: float, phi: float, gamma: float, t: float) -> dict[str, object]:
    prep_ref = _bell_prep(theta, phi)
    prep_cirq = _cirq_prep(theta, phi)
    prep_pl = np.asarray(qml.math.asarray(_pennylane_prep(theta, phi)), dtype=np.complex128)
    prep_rho_ref = _rho(prep_ref)
    ref_rho_t = _open_system_reference(prep_rho_ref, gamma, t)
    qutip_rho_t = _qutip_evolution(prep_rho_ref, gamma, [0.0, t])[-1]
    prep_surface = {
        "numpy_vs_cirq": float(np.linalg.norm(_rho(prep_ref) - _rho(prep_cirq))),
        "numpy_vs_pennylane": float(np.linalg.norm(_rho(prep_ref) - _rho(prep_pl))),
        "cirq_cnot_trace": float(np.real(np.trace(cirq.unitary(cirq.CNOT)))),
        "pennylane_state_norm": float(np.linalg.norm(prep_pl)),
    }
    open_surface = {
        "numpy_vs_qutip": float(np.linalg.norm(ref_rho_t - qutip_rho_t)),
        "reference_trace_gap": float(abs(np.trace(ref_rho_t) - 1.0)),
    }
    return {
        "pass": bool(
            prep_surface["numpy_vs_cirq"] < 1e-6
            and prep_surface["numpy_vs_pennylane"] < 1e-6
            and open_surface["numpy_vs_qutip"] < 1e-6
            and open_surface["reference_trace_gap"] < 1e-9
        ),
        "prep_surface": prep_surface,
        "open_system_surface": open_surface,
    }


def _structure_proxy(
    graph_longest_path_length: int,
    manifold_distance: float,
    pyg_mean_aggregate_norm: float,
) -> float:
    return float(
        float(manifold_distance)
        + STRUCTURE_PATH_WEIGHT * float(np.tanh(float(graph_longest_path_length)))
        + STRUCTURE_PYG_WEIGHT * float(np.tanh(float(pyg_mean_aggregate_norm)))
    )


def semantic_row(
    lane: str,
    symbolic_hubble_mid: float,
    constraint_pass: bool,
    cvc5_pass: bool,
    graph_longest_path_length: int,
    manifold_distance: float,
    pyg_mean_aggregate_norm: float,
    bridge_owner_pass: bool | None = None,
    bridge_owner_gate_fraction: float | None = None,
    distinguishability_pass: bool | None = None,
    distinguishability_gate_fraction: float | None = None,
    distinguishability_surface: dict[str, object] | None = None,
    constraint_family_profile: dict[str, object] | None = None,
) -> dict[str, object]:
    doctrine_components = [float(constraint_pass), float(cvc5_pass)]
    if bridge_owner_pass is not None:
        doctrine_components.append(float(bridge_owner_pass))
    if bridge_owner_gate_fraction is not None:
        doctrine_components.append(float(bridge_owner_gate_fraction))
    if distinguishability_pass is not None:
        doctrine_components.append(float(distinguishability_pass))
    if distinguishability_gate_fraction is not None:
        doctrine_components.append(float(distinguishability_gate_fraction))
    doctrine_score = float(np.mean(doctrine_components))
    semantic_vector = np.array(
        [
            float(symbolic_hubble_mid),
            doctrine_score,
            _structure_proxy(
                graph_longest_path_length,
                manifold_distance,
                pyg_mean_aggregate_norm,
            ),
        ],
        dtype=np.float64,
    )
    return {
        "lane": lane,
        "semantic_vector": semantic_vector.tolist(),
        "symbolic_hubble_mid": float(symbolic_hubble_mid),
        "constraint_pass": bool(constraint_pass),
        "cvc5_pass": bool(cvc5_pass),
        "bridge_owner_pass": None if bridge_owner_pass is None else bool(bridge_owner_pass),
        "bridge_owner_gate_fraction": (
            None if bridge_owner_gate_fraction is None else float(bridge_owner_gate_fraction)
        ),
        "distinguishability_pass": (
            None if distinguishability_pass is None else bool(distinguishability_pass)
        ),
        "distinguishability_gate_fraction": (
            None
            if distinguishability_gate_fraction is None
            else float(distinguishability_gate_fraction)
        ),
        "distinguishability_surface": distinguishability_surface,
        "constraint_family_profile": constraint_family_profile,
        "graph_longest_path_length": int(graph_longest_path_length),
        "manifold_distance": float(manifold_distance),
        "pyg_mean_aggregate_norm": float(pyg_mean_aggregate_norm),
    }


def build_positive_lane_payload(
    cosmology_metrics: dict[str, object] | None = None,
) -> dict[str, object]:
    cosmology = (
        cosmology_metrics
        if cosmology_metrics is not None
        else _load_cosmology_case_fn()(
            theta=DEFAULT_THETA,
            phi=DEFAULT_PHI,
            gamma=DEFAULT_GAMMA,
            t=DEFAULT_T,
        )
    )

    seam_positive = _run_seam_positive_tests()
    seam_negative = _run_seam_negative_tests()
    seam_boundary = _run_seam_boundary_tests()
    seam_shell_bridge = lane_d_topology_expansion_bridge(_build_seam_shell_history())
    seam_deep = _seam_aggregate_deep_contract(seam_positive, seam_negative, seam_boundary, seam_shell_bridge)

    through_positive = _run_through_positive_tests()
    through_negative = _run_through_negative_tests()
    through_boundary = _run_through_boundary_tests()
    ordered_shells, _ = build_shell_order()
    through_shell_bridge = lane_d_topology_expansion_bridge(_build_shell_projection_history(ordered_shells))
    through_deep = _through_aggregate_deep_contract(
        through_positive,
        through_negative,
        through_boundary,
        through_shell_bridge,
    )

    np.random.seed(42)
    torch.manual_seed(42)
    pyg_model = Axis0ProxyModel()
    pyg_sweep = sweep_gradient_profile(pyg_model)
    pyg_positive = _run_pyg_positive_tests(pyg_model, pyg_sweep)
    pyg_negative = _run_pyg_negative_tests(pyg_model)
    pyg_boundary = _run_pyg_boundary_tests(pyg_model)
    pyg_axis0 = _run_pyg_axis0_summary_test(pyg_sweep)
    pyg_z3 = _verify_pyg_chain_admissibility_z3()
    pyg_sympy = _verify_pyg_ic_formula_sympy()
    pyg_graph = build_pyg_chain_graph()
    pyg_shell_bridge = lane_d_topology_expansion_bridge(_build_pyg_shell_history(pyg_sweep))
    pyg_deep = _pyg_aggregate_deep_contract(
        pyg_positive,
        pyg_negative,
        pyg_boundary,
        pyg_axis0,
        pyg_z3,
        pyg_sympy,
        pyg_sweep,
        pyg_graph,
        pyg_shell_bridge,
    )

    rows = [
        semantic_row(**dict(cosmology["semantic_row_surface"])),
        semantic_row(**_seam_semantic_row_surface(seam_deep)),
        semantic_row(**_through_semantic_row_surface(through_deep)),
        semantic_row(**_pyg_semantic_row_surface(pyg_deep)),
    ]

    return {
        "cosmology": cosmology,
        "seam": {
            "positive": seam_positive,
            "negative": seam_negative,
            "boundary": seam_boundary,
            "shell_bridge": seam_shell_bridge,
            "deep_contract": seam_deep,
        },
        "through_shells": {
            "positive": through_positive,
            "negative": through_negative,
            "boundary": through_boundary,
            "shell_bridge": through_shell_bridge,
            "deep_contract": through_deep,
        },
        "pyg_proxy": {
            "positive": pyg_positive,
            "negative": pyg_negative,
            "boundary": pyg_boundary,
            "axis0_summary": pyg_axis0,
            "z3_surface": pyg_z3,
            "sympy_surface": pyg_sympy,
            "shell_bridge": pyg_shell_bridge,
            "deep_contract": pyg_deep,
        },
        "rows": rows,
    }


def _semantic_shell_history(candidate_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    history: list[dict[str, object]] = []
    for idx, row in enumerate(candidate_rows):
        vector = np.asarray(row["semantic_vector"], dtype=np.float64)
        expansion = float(vector[0])
        doctrine = float(vector[1])
        structure = float(vector[2])
        p_left = float(np.clip(0.56 + 0.18 * np.tanh(expansion) + 0.08 * doctrine - 0.04 * structure, 0.05, 0.99))
        p_right = float(np.clip(0.60 + 0.12 * np.tanh(expansion) + 0.06 * structure - 0.03 * doctrine, 0.05, 0.99))
        history.append(
            {
                "rho_L": _diag_density(p_left),
                "rho_R": _diag_density(p_right),
                "eta": float(0.2 + 0.15 * idx),
                "semantic_vector": vector.tolist(),
            }
        )
    return history


def _pairwise_alignment_surface(candidate_rows: list[dict[str, object]]) -> dict[str, object]:
    semantic_matrix = np.asarray([row["semantic_vector"] for row in candidate_rows], dtype=np.float64)
    pairwise_rows: list[dict[str, object]] = []
    min_cosine = 1.0
    max_gap = 0.0
    for idx in range(len(candidate_rows)):
        for jdx in range(idx + 1, len(candidate_rows)):
            lhs = semantic_matrix[idx]
            rhs = semantic_matrix[jdx]
            cosine = float(np.dot(lhs, rhs) / max(np.linalg.norm(lhs) * np.linalg.norm(rhs), EPS))
            gap = float(np.max(np.abs(lhs - rhs)))
            pairwise_rows.append(
                {
                    "lhs": candidate_rows[idx]["lane"],
                    "rhs": candidate_rows[jdx]["lane"],
                    "cosine_similarity": cosine,
                    "max_component_gap": gap,
                }
            )
            min_cosine = min(min_cosine, cosine)
            max_gap = max(max_gap, gap)
    consensus_vector = np.mean(semantic_matrix, axis=0) if len(semantic_matrix) else np.zeros(3, dtype=np.float64)
    distinguishability_alignment = _pairwise_distinguishability_alignment_surface(candidate_rows)
    return {
        "rows": pairwise_rows,
        "min_cosine_similarity": float(min_cosine if pairwise_rows else 1.0),
        "max_component_gap": float(max_gap),
        "consensus_vector": consensus_vector.tolist(),
        "distinguishability_alignment": distinguishability_alignment,
    }


def _pairwise_distinguishability_alignment_surface(
    candidate_rows: list[dict[str, object]],
) -> dict[str, object]:
    gate_names = (
        "observational",
        "admissible",
        "stable",
        "entropy_conditioned",
        "topology_conditioned",
    )
    pairwise_rows: list[dict[str, object]] = []
    min_gate_agreement = 1.0
    max_gate_disagreement = 0.0
    min_surface_cosine = 1.0
    min_signal_cosine = 1.0
    min_signal_overlap = 0

    def _surface_vector(row: dict[str, object]) -> np.ndarray:
        surface = row.get("distinguishability_surface") or {}
        gates = surface.get("gates") or {}
        return np.asarray(
            [
                1.0 if bool(gates.get(name, False)) else 0.0
                for name in gate_names
            ]
            + [
                float(row.get("distinguishability_gate_fraction", 0.0)),
            ],
            dtype=np.float64,
        )

    def _signal_map(row: dict[str, object]) -> dict[str, float]:
        surface = row.get("distinguishability_surface") or {}
        raw = surface.get("signals") or {}
        return {str(key): float(value) for key, value in raw.items()}

    def _constraint_profile(row: dict[str, object]) -> dict[str, float]:
        surface = row.get("distinguishability_surface") or {}
        raw = surface.get("constraint_profile") or {}
        if raw:
            return {str(key): float(value) for key, value in raw.items()}
        raw_signals = surface.get("signals") or {}
        return {
            "observational": float(raw_signals.get("observational_signal", 0.0)),
            "admissible": float(raw_signals.get("admissibility_signal", 0.0)),
            "stable": float(raw_signals.get("stability_signal", 0.0)),
            "entropy_conditioned": float(raw_signals.get("entropy_signal", 0.0)),
            "topology_conditioned": float(raw_signals.get("topology_signal", 0.0)),
        }

    for idx in range(len(candidate_rows)):
        for jdx in range(idx + 1, len(candidate_rows)):
            lhs = _surface_vector(candidate_rows[idx])
            rhs = _surface_vector(candidate_rows[jdx])
            lhs_profile = _constraint_profile(candidate_rows[idx])
            rhs_profile = _constraint_profile(candidate_rows[jdx])
            lhs_signals = _signal_map(candidate_rows[idx])
            rhs_signals = _signal_map(candidate_rows[jdx])
            profile_keys = (
                "observational",
                "admissible",
                "stable",
                "entropy_conditioned",
                "topology_conditioned",
            )
            lhs_profile_vector = np.asarray(
                [lhs_profile.get(key, 0.0) for key in profile_keys],
                dtype=np.float64,
            )
            rhs_profile_vector = np.asarray(
                [rhs_profile.get(key, 0.0) for key in profile_keys],
                dtype=np.float64,
            )
            lhs_profile_vector = np.tanh(lhs_profile_vector)
            rhs_profile_vector = np.tanh(rhs_profile_vector)
            profile_cosine = float(
                np.dot(lhs_profile_vector, rhs_profile_vector)
                / max(np.linalg.norm(lhs_profile_vector) * np.linalg.norm(rhs_profile_vector), EPS)
            )
            shared_signal_keys = sorted(set(lhs_signals).intersection(rhs_signals))
            if shared_signal_keys:
                lhs_signal_vector = np.asarray(
                    [lhs_signals[key] for key in shared_signal_keys],
                    dtype=np.float64,
                )
                rhs_signal_vector = np.asarray(
                    [rhs_signals[key] for key in shared_signal_keys],
                    dtype=np.float64,
                )
                lhs_signal_vector = np.tanh(lhs_signal_vector)
                rhs_signal_vector = np.tanh(rhs_signal_vector)
                signal_cosine = float(
                    np.dot(lhs_signal_vector, rhs_signal_vector)
                    / max(np.linalg.norm(lhs_signal_vector) * np.linalg.norm(rhs_signal_vector), EPS)
                )
            else:
                signal_cosine = 1.0
            gate_agreement = float(np.mean(np.isclose(lhs[:-1], rhs[:-1]).astype(np.float64)))
            max_gate_diff = float(np.max(np.abs(lhs[:-1] - rhs[:-1])))
            cosine = float(np.dot(lhs, rhs) / max(np.linalg.norm(lhs) * np.linalg.norm(rhs), EPS))
            pairwise_rows.append(
                {
                    "lhs": candidate_rows[idx]["lane"],
                    "rhs": candidate_rows[jdx]["lane"],
                    "gate_agreement": gate_agreement,
                    "max_gate_disagreement": max_gate_diff,
                    "surface_cosine_similarity": cosine,
                    "constraint_profile_cosine_similarity": profile_cosine,
                    "signal_keys": shared_signal_keys,
                    "signal_cosine_similarity": signal_cosine,
                }
            )
            min_gate_agreement = min(min_gate_agreement, gate_agreement)
            max_gate_disagreement = max(max_gate_disagreement, max_gate_diff)
            min_surface_cosine = min(min_surface_cosine, cosine)
            min_signal_cosine = min(min_signal_cosine, signal_cosine)
            min_signal_overlap = min_signal_overlap if min_signal_overlap else len(shared_signal_keys)
            if min_signal_overlap:
                min_signal_overlap = min(min_signal_overlap, len(shared_signal_keys))
            else:
                min_signal_overlap = len(shared_signal_keys)

    return {
        "rows": pairwise_rows,
        "min_gate_agreement": float(min_gate_agreement if pairwise_rows else 1.0),
        "max_gate_disagreement": float(max_gate_disagreement),
        "min_surface_cosine_similarity": float(min_surface_cosine if pairwise_rows else 1.0),
        "min_constraint_profile_cosine_similarity": float(
            min(
                (
                    float(row["constraint_profile_cosine_similarity"])
                    for row in pairwise_rows
                ),
                default=1.0,
            )
        ),
        "min_signal_cosine_similarity": float(min_signal_cosine if pairwise_rows else 1.0),
        "min_shared_signal_count": int(min_signal_overlap if pairwise_rows else 0),
    }


def _crosslane_pyg_surface(candidate_rows: list[dict[str, object]]) -> dict[str, object]:
    features = np.asarray(
        [
            [
                float(row["mean_abs_a0"]),
                float(row["doctrine_fit"]),
                float(row["shell_alignment_abs"]),
            ]
            for row in candidate_rows
        ],
        dtype=np.float64,
    )
    if len(features) < 2:
        return {
            "pass": False,
            "num_nodes": int(len(features)),
            "num_edges": 0,
            "mean_aggregate_norm": 0.0,
            "max_aggregate_norm": 0.0,
            "edge_weight_mean": 0.0,
        }

    edge_pairs: list[list[int]] = []
    edge_weights: list[float] = []
    for idx in range(len(features) - 1):
        weight = float(
            0.5
            * (
                float(candidate_rows[idx]["composite_score"])
                + float(candidate_rows[idx + 1]["composite_score"])
            )
        )
        edge_pairs.extend([[idx, idx + 1], [idx + 1, idx]])
        edge_weights.extend([weight, weight])

    x = torch.tensor(features, dtype=torch.float64)
    edge_index = torch.tensor(edge_pairs, dtype=torch.long).t().contiguous()
    edge_attr = torch.tensor(edge_weights, dtype=torch.float64)
    data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr)

    class CrosslaneMessagePassing(MessagePassing):
        def __init__(self) -> None:
            super().__init__(aggr="add")

        def forward(self, x, edge_index, edge_attr):
            return self.propagate(edge_index, x=x, edge_attr=edge_attr)

        def message(self, x_j, edge_attr):
            return edge_attr.view(-1, 1) * x_j

    mp_layer = CrosslaneMessagePassing()
    aggregated = mp_layer(data.x, data.edge_index, data.edge_attr)
    norms = torch.linalg.norm(aggregated, dim=1)
    return {
        "pass": bool(
            int(data.num_nodes) == len(candidate_rows)
            and int(data.num_edges) >= 2 * (len(candidate_rows) - 1)
            and float(norms.mean().item()) > 1e-3
        ),
        "num_nodes": int(data.num_nodes),
        "num_edges": int(data.num_edges),
        "mean_aggregate_norm": float(norms.mean().item()),
        "max_aggregate_norm": float(norms.max().item()),
        "edge_weight_mean": float(edge_attr.mean().item()),
    }


def _crosslane_cvc5_surface(candidate_rows: list[dict[str, object]]) -> dict[str, object]:
    ranking_scores = [float(row["composite_score"]) for row in candidate_rows]
    if len(ranking_scores) < 2:
        return {
            "pass": False,
            "actual_sat": False,
            "contradiction_unsat": False,
            "winner_gap": 0.0,
        }

    solver = cvc5.Solver()
    solver.setLogic("QF_LRA")
    score_vars = [
        solver.mkConst(solver.getRealSort(), f"score_{idx}")
        for idx in range(len(ranking_scores))
    ]
    for score_var, value in zip(score_vars, ranking_scores, strict=True):
        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL, score_var, solver.mkReal(f"{value:.12f}"))
        )
    for idx in range(len(score_vars) - 1):
        solver.assertFormula(solver.mkTerm(Kind.GEQ, score_vars[idx], score_vars[idx + 1]))
    actual_sat = solver.checkSat().isSat()

    contradiction = cvc5.Solver()
    contradiction.setLogic("QF_LRA")
    contradiction_vars = [
        contradiction.mkConst(contradiction.getRealSort(), f"cscore_{idx}")
        for idx in range(len(ranking_scores))
    ]
    for score_var, value in zip(contradiction_vars, ranking_scores, strict=True):
        contradiction.assertFormula(
            contradiction.mkTerm(Kind.EQUAL, score_var, contradiction.mkReal(f"{value:.12f}"))
        )
    for idx in range(len(contradiction_vars) - 1):
        contradiction.assertFormula(
            contradiction.mkTerm(Kind.GEQ, contradiction_vars[idx], contradiction_vars[idx + 1])
        )
    contradiction.assertFormula(
        contradiction.mkTerm(Kind.LT, contradiction_vars[0], contradiction_vars[-1])
    )
    contradiction_unsat = not contradiction.checkSat().isSat()
    return {
        "pass": bool(actual_sat and contradiction_unsat),
        "actual_sat": bool(actual_sat),
        "contradiction_unsat": bool(contradiction_unsat),
        "winner_gap": float(ranking_scores[0] - ranking_scores[-1]),
    }


def _crosslane_e3nn_surface(consensus_vector: np.ndarray) -> dict[str, object]:
    base_vector = np.asarray(consensus_vector, dtype=np.float64)
    base_vector = np.where(np.abs(base_vector) < 1e-6, 1e-6, base_vector)
    vector = torch.tensor(base_vector[None, :], dtype=torch.float64)
    reflected = vector.clone()
    reflected[:, 0] *= -1.0

    y0 = o3.spherical_harmonics(0, vector, normalize=True, normalization="component")
    y0_reflected = o3.spherical_harmonics(0, reflected, normalize=True, normalization="component")
    y1 = o3.spherical_harmonics(1, vector, normalize=True, normalization="component")
    y1_reflected = o3.spherical_harmonics(1, reflected, normalize=True, normalization="component")

    l0_gap = float(torch.max(torch.abs(y0 - y0_reflected)).item())
    l1_norm_gap = float(
        torch.max(torch.abs(torch.linalg.norm(y1, dim=1) - torch.linalg.norm(y1_reflected, dim=1))).item()
    )
    x_parity_gap = float(torch.abs(y1[0, 0] + y1_reflected[0, 0]).item())
    yz_invariance_gap = float(torch.max(torch.abs(y1[0, 1:] - y1_reflected[0, 1:])).item())
    return {
        "pass": bool(
            l0_gap < 1e-6
            and l1_norm_gap < 1e-6
            and x_parity_gap < 1e-6
            and yz_invariance_gap < 1e-6
        ),
        "l0_gap": l0_gap,
        "l1_norm_gap": l1_norm_gap,
        "x_parity_gap": x_parity_gap,
        "yz_invariance_gap": yz_invariance_gap,
    }


def crosslane_bridge(candidate_rows: list[dict[str, object]], source_surface: dict[str, object]) -> dict[str, object]:
    rows = [dict(row) for row in candidate_rows]
    alignment_surface = _pairwise_alignment_surface(rows)
    distinguishability_alignment = alignment_surface["distinguishability_alignment"]
    flat_frontier = bool(alignment_surface["max_component_gap"] <= 1e-12)

    max_mean_abs = max(abs(float(row["semantic_vector"][0])) for row in rows)
    max_structure = max(abs(float(row["semantic_vector"][2])) for row in rows)
    for row in rows:
        vector = np.asarray(row["semantic_vector"], dtype=np.float64)
        mean_abs_a0 = float(abs(vector[0]))
        doctrine_fit = float(vector[1])
        shell_alignment_abs = float(abs(vector[2]))
        row["option"] = row["lane"]
        row["mean_abs_a0"] = mean_abs_a0
        row["mean_signed_a0"] = float(vector[0])
        row["doctrine_fit"] = doctrine_fit
        row["sign_consistency"] = doctrine_fit
        row["shell_alignment"] = float(vector[2])
        row["shell_alignment_abs"] = shell_alignment_abs
        row["signal_score"] = float(mean_abs_a0 / max(max_mean_abs, EPS))
        structure_score = float(shell_alignment_abs / max(max_structure, EPS))
        row["composite_score"] = float(0.40 * doctrine_fit + 0.35 * row["signal_score"] + 0.25 * structure_score)
        row["mean_signal"] = float(vector[0] + vector[2])

    ranked_rows = sorted(rows, key=lambda row: float(row["composite_score"]), reverse=True)
    lambda_shells = np.linspace(0.0, 1.0, len(ranked_rows), dtype=np.float64)
    if flat_frontier:
        expansion_drive = np.zeros(len(ranked_rows), dtype=np.float64)
        scale_factors = np.ones(len(ranked_rows), dtype=np.float64)
        propagator_traces = [2.0 for _ in range(max(0, len(ranked_rows) - 1))]
        hubble_proxy = np.zeros(len(ranked_rows), dtype=np.float64)
    else:
        expansion_drive = np.asarray(
            [
                float(row["mean_abs_a0"]) + float(row["doctrine_fit"]) + float(row["shell_alignment_abs"])
                for row in ranked_rows
            ],
            dtype=np.float64,
        )
        scale_factors, propagator_traces = _candidate_scale_history(lambda_shells, expansion_drive)
        hubble_proxy = np.gradient(np.log(np.clip(scale_factors, EPS, None)), lambda_shells)
    for row, scale, hubble in zip(ranked_rows, scale_factors.tolist(), hubble_proxy.tolist(), strict=True):
        row["scale_factor"] = float(scale)
        row["hubble_proxy"] = float(hubble)

    if flat_frontier:
        semantic_history = [
            {
                "rho_L": _diag_density(0.5),
                "rho_R": _diag_density(0.5),
                "eta": float(0.2 + 0.15 * idx),
                "semantic_vector": np.asarray(row["semantic_vector"], dtype=np.float64).tolist(),
            }
            for idx, row in enumerate(ranked_rows)
        ]
    else:
        semantic_history = _semantic_shell_history(ranked_rows)
    shell_bridge = lane_d_topology_expansion_bridge(semantic_history)
    if flat_frontier:
        graph_surface = {
            "node_count": int(len(ranked_rows)),
            "edge_count": 0,
            "pair_edges": [],
            "triad_windows": [],
            "topological_order": [int(idx) for idx in range(len(ranked_rows))],
            "longest_path_length": 0,
            "acyclic": True,
            "edge_signal_sum": 0.0,
        }
        config_windows: list[list[int]] = []
    else:
        graph_surface = _candidate_graph_surface(ranked_rows)
        config_windows = []
        if len(ranked_rows) >= 3:
            config_windows.append([0, 1, 2])
        if len(ranked_rows) >= 4:
            config_windows.append([1, 2, 3])
    hypergraph_surface = _candidate_hypergraph_surface(len(ranked_rows), config_windows)

    combined_pair_edges = sorted(
        {
            tuple(edge)
            for edge in graph_surface["pair_edges"] + hypergraph_surface["pair_edges"]
        }
    )
    combined_triad_windows = sorted(
        {
            tuple(window)
            for window in graph_surface["triad_windows"] + hypergraph_surface["triad_windows"]
        }
    )
    closed_pair_edges = set(combined_pair_edges)
    for window in combined_triad_windows:
        for idx in range(len(window)):
            for jdx in range(idx + 1, len(window)):
                closed_pair_edges.add(tuple(sorted((int(window[idx]), int(window[jdx])))))

    cell_complex_surface = _candidate_cell_complex_surface(
        len(ranked_rows),
        [list(edge) for edge in sorted(closed_pair_edges)],
        [list(window) for window in combined_triad_windows],
    )
    topology_surface = _candidate_topology_surface(
        len(ranked_rows),
        [list(edge) for edge in sorted(closed_pair_edges)],
        [list(window) for window in combined_triad_windows],
    )
    if flat_frontier:
        symbolic_surface = {
            "scale_factor_polynomial": str(sp.Integer(1)),
            "expansion_drive_polynomial": str(sp.Integer(0)),
            "scale_poly_degree": 0,
            "drive_poly_degree": 0,
            "mid_lambda": float(lambda_shells[len(lambda_shells) // 2]) if len(lambda_shells) else 0.0,
            "symbolic_hubble_mid": 0.0,
            "symbolic_acceleration_mid": 0.0,
            "symbolic_drive_mid": 0.0,
        }
    else:
        symbolic_surface = _candidate_symbolic_surface(lambda_shells, scale_factors, expansion_drive)
    constraint_surface = _candidate_constraint_surface(
        lambda_shells,
        scale_factors,
        np.asarray([float(row["composite_score"]) for row in ranked_rows], dtype=np.float64),
    )
    manifold_surface = _candidate_manifold_surface(
        np.asarray([float(row["mean_abs_a0"]) for row in ranked_rows], dtype=np.float64),
        np.asarray([float(row["doctrine_fit"]) for row in ranked_rows], dtype=np.float64),
        np.asarray([float(row["shell_alignment_abs"]) for row in ranked_rows], dtype=np.float64),
        scale_factors,
    )
    torch_fit = _torch_candidate_fit(
        np.stack(
            [
                np.asarray([float(row["mean_abs_a0"]) for row in ranked_rows], dtype=np.float64),
                np.asarray([float(row["doctrine_fit"]) for row in ranked_rows], dtype=np.float64),
                np.asarray([float(row["shell_alignment_abs"]) for row in ranked_rows], dtype=np.float64),
            ],
            axis=1,
        ),
        hubble_proxy,
    )
    if flat_frontier:
        pyg_surface = {
            "pass": True,
            "num_nodes": int(len(ranked_rows)),
            "num_edges": 0,
            "mean_aggregate_norm": 0.0,
            "max_aggregate_norm": 0.0,
            "edge_weight_mean": 0.0,
        }
    else:
        pyg_surface = _crosslane_pyg_surface(ranked_rows)
    cvc5_surface = _crosslane_cvc5_surface(ranked_rows)
    consensus_vector = np.asarray(alignment_surface["consensus_vector"], dtype=np.float64)
    e3nn_surface = _crosslane_e3nn_surface(consensus_vector)
    clifford_vector = _clifford_vector(consensus_vector)
    torch_ga_vector = _torch_ga_roundtrip(consensus_vector)
    topology_parity_ok = bool(
        cell_complex_surface["euler_characteristic"] == topology_surface["euler_characteristic"]
    )

    pass_flag = bool(
        source_surface["pass"]
        and alignment_surface["min_cosine_similarity"] >= PAIRWISE_COSINE_THRESHOLD
        and alignment_surface["max_component_gap"] <= PAIRWISE_GAP_THRESHOLD
        and distinguishability_alignment["min_gate_agreement"] >= 0.8
        and distinguishability_alignment["min_surface_cosine_similarity"] >= 0.94
        and distinguishability_alignment["min_constraint_profile_cosine_similarity"] >= 0.9
        and distinguishability_alignment["min_signal_cosine_similarity"] >= 0.9
        and shell_bridge["lane_d_keep"]
        and graph_surface["longest_path_length"] >= max(1, len(ranked_rows) - 2)
        and hypergraph_surface["max_hyperedge_size"] >= 3
        and topology_surface["beta0"] == 1
        and topology_surface["beta1"] <= max(1, len(ranked_rows) // 3)
        and topology_parity_ok
        and constraint_surface["sat"]
        and cvc5_surface["pass"]
        and symbolic_surface["symbolic_hubble_mid"] > 0.05
        and manifold_surface["mean_geodesic_distance"] > MANIFOLD_DISTANCE_THRESHOLD
        and torch_fit["loss"] < 1.0
        and pyg_surface["pass"]
        and e3nn_surface["pass"]
    )

    return {
        "pass": pass_flag,
        "source_surface": source_surface,
        "alignment_surface": alignment_surface,
        "ranked_rows": ranked_rows,
        "shell_bridge": shell_bridge,
        "graph_surface": graph_surface,
        "hypergraph_surface": hypergraph_surface,
        "cell_complex_surface": cell_complex_surface,
        "topology_surface": {
            **topology_surface,
            "parity_ok": topology_parity_ok,
        },
        "symbolic_surface": symbolic_surface,
        "constraint_surface": constraint_surface,
        "cvc5_surface": cvc5_surface,
        "manifold_surface": manifold_surface,
        "pyg_surface": pyg_surface,
        "e3nn_surface": e3nn_surface,
        "torch_fit": torch_fit,
        "consensus_vector": consensus_vector.tolist(),
        "clifford_vector_gap": float(np.max(np.abs(clifford_vector - consensus_vector))),
        "torch_ga_vector_gap": float(np.max(np.abs(torch_ga_vector - consensus_vector))),
        "scale_factors": scale_factors.tolist(),
        "hubble_proxy": hubble_proxy.tolist(),
        "propagator_traces": propagator_traces,
    }


def run_positive_tests(
    cosmology_metrics: dict[str, object] | None = None,
) -> dict[str, object]:
    payload = build_positive_lane_payload(cosmology_metrics)
    source_surface = source_bridge_surface(
        theta=DEFAULT_THETA,
        phi=DEFAULT_PHI,
        gamma=DEFAULT_GAMMA,
        t=DEFAULT_T,
    )
    bridge = crosslane_bridge(payload["rows"], source_surface)
    xi_packet_surface = _load_xi_packet_surface()
    bridge_owner_surface = load_bridge_owner_packet_surface()
    return {
        "pass": bool(bridge["pass"] and xi_packet_surface["pass"] and bridge_owner_surface["pass"]),
        "crosslane_bridge": bridge,
        "xi_packet_surface": xi_packet_surface,
        "bridge_owner_surface": bridge_owner_surface,
        "lane_rows": payload["rows"],
    }


def run_negative_tests(
    cosmology_metrics: dict[str, object] | None = None,
) -> dict[str, object]:
    payload = build_positive_lane_payload(cosmology_metrics)
    source_surface = source_bridge_surface(
        theta=DEFAULT_THETA,
        phi=DEFAULT_PHI,
        gamma=DEFAULT_GAMMA,
        t=DEFAULT_T,
    )

    reflected_rows = [dict(row) for row in payload["rows"]]
    reflected_rows[0]["semantic_vector"] = [
        -float(reflected_rows[0]["semantic_vector"][0]),
        float(reflected_rows[0]["semantic_vector"][1]),
        float(reflected_rows[0]["semantic_vector"][2]),
    ]
    reflected_bridge = crosslane_bridge(reflected_rows, source_surface)

    ablated_rows = [dict(row) for row in payload["rows"]]
    ablated_rows[1]["semantic_vector"] = [
        float(ablated_rows[1]["semantic_vector"][0]),
        0.0,
        float(ablated_rows[1]["semantic_vector"][2]),
    ]
    ablated_bridge = crosslane_bridge(ablated_rows, source_surface)

    return {
        "pass": bool(
            not reflected_bridge["pass"]
            and reflected_bridge["alignment_surface"]["min_cosine_similarity"] < 0.75
            and not ablated_bridge["pass"]
            and ablated_bridge["alignment_surface"]["min_cosine_similarity"] < PAIRWISE_COSINE_THRESHOLD
        ),
        "reflected_cosmology_breaks_alignment": {
            "pass": bool(
                not reflected_bridge["pass"]
                and reflected_bridge["alignment_surface"]["min_cosine_similarity"] < 0.75
            ),
            "min_cosine_similarity": reflected_bridge["alignment_surface"]["min_cosine_similarity"],
            "max_component_gap": reflected_bridge["alignment_surface"]["max_component_gap"],
        },
        "constraint_ablation_breaks_bridge": {
            "pass": bool(
                not ablated_bridge["pass"]
                and ablated_bridge["alignment_surface"]["min_cosine_similarity"] < PAIRWISE_COSINE_THRESHOLD
            ),
            "min_cosine_similarity": ablated_bridge["alignment_surface"]["min_cosine_similarity"],
            "max_component_gap": ablated_bridge["alignment_surface"]["max_component_gap"],
        },
    }


def run_boundary_tests() -> dict[str, object]:
    source_surface = source_bridge_surface(theta=0.0, phi=0.0, gamma=0.0, t=0.0)
    boundary_rows = [
        {
            "lane": lane,
            "semantic_vector": [0.0, 1.0, 0.0],
        }
        for lane in ["lambda_cosmology", "axis6_seam", "through_shells", "pyg_proxy"]
    ]
    bridge = crosslane_bridge(boundary_rows, source_surface)
    boundary_ok = bool(
        source_surface["pass"]
        and bridge["alignment_surface"]["min_cosine_similarity"] > 1.0 - 1e-9
        and bridge["alignment_surface"]["max_component_gap"] < 1e-9
        and bridge["graph_surface"]["edge_count"] == 0
        and bridge["pyg_surface"]["num_edges"] == 0
        and bridge["topology_surface"]["beta0"] == len(boundary_rows)
        and bridge["topology_surface"]["beta1"] == 0
        and abs(bridge["symbolic_surface"]["symbolic_hubble_mid"]) < 1e-9
        and bridge["constraint_surface"]["sat"]
        and bridge["cvc5_surface"]["pass"]
        and bridge["manifold_surface"]["mean_geodesic_distance"] < 1e-12
        and bridge["e3nn_surface"]["pass"]
    )
    return {
        "pass": boundary_ok,
        "crosslane_boundary": {
            "pass": boundary_ok,
            "alignment_surface": bridge["alignment_surface"],
            "graph_surface": bridge["graph_surface"],
            "pyg_surface": bridge["pyg_surface"],
            "topology_surface": bridge["topology_surface"],
            "symbolic_surface": bridge["symbolic_surface"],
            "constraint_surface": bridge["constraint_surface"],
            "cvc5_surface": bridge["cvc5_surface"],
            "manifold_surface": bridge["manifold_surface"],
            "e3nn_surface": bridge["e3nn_surface"],
        },
    }


def load_persisted_semantic_rows(results_dir: str | Path | None = None) -> dict[str, dict[str, object]]:
    root = Path(results_dir) if results_dir is not None else DEFAULT_RESULTS_DIR
    paths = _persisted_result_paths(root)
    loaded: dict[str, dict[str, object]] = {}
    for lane, candidates in paths.items():
        path = next((candidate for candidate in candidates if candidate.exists()), None)
        if path is None:
            rendered = ", ".join(str(candidate) for candidate in candidates)
            raise FileNotFoundError(f"Persisted semantic row artifact missing at load time: {rendered}")
        data = json.loads(path.read_text())
        if lane == "lambda_cosmology":
            row = dict(data["positive"]["axis0_lambda_expansion"]["semantic_row_surface"])
        else:
            row = dict(data["aggregate"]["deep_contract"]["semantic_row_surface"])
        loaded[lane] = row
    return loaded


def run_positive_tests_from_results(results_dir: str | Path | None = None) -> dict[str, object]:
    refreshed_lanes = ensure_persisted_semantic_rows(results_dir)
    persisted_rows = load_persisted_semantic_rows(results_dir)
    rows = [
        semantic_row(**persisted_rows["lambda_cosmology"]),
        semantic_row(**persisted_rows["axis6_seam"]),
        semantic_row(**persisted_rows["through_shells"]),
        semantic_row(**persisted_rows["pyg_proxy"]),
    ]
    source_surface = source_bridge_surface(
        theta=DEFAULT_THETA,
        phi=DEFAULT_PHI,
        gamma=DEFAULT_GAMMA,
        t=DEFAULT_T,
    )
    bridge = crosslane_bridge(rows, source_surface)
    xi_packet_surface = _load_xi_packet_surface(results_dir)
    bridge_owner_surface = load_bridge_owner_packet_surface(results_dir)
    return {
        "pass": bool(bridge["pass"] and xi_packet_surface["pass"] and bridge_owner_surface["pass"]),
        "crosslane_bridge": bridge,
        "xi_packet_surface": xi_packet_surface,
        "bridge_owner_surface": bridge_owner_surface,
        "lane_rows": rows,
        "row_source": "persisted_results",
        "refreshed_missing_artifacts": refreshed_lanes,
    }
