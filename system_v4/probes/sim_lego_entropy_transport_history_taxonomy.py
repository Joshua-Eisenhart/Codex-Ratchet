#!/usr/bin/env python3
"""
PURE LEGO: Pre-Bridge Entropy Transport/History Taxonomy
=======================================================
Bounded pure-math taxonomy sim for four pre-bridge candidate families:

1. shell-weighted entropy
2. history-window entropy
3. transport-weighted entropy
4. operator-order-sensitive path entropy

The goal is separation and falsification, not bridge doctrine:
- what is invariant under permutation or relabeling
- what is genuinely order-sensitive
- what collapses under identity transport
- what is bookkeeping rather than geometry

Boot context:
- system_v5/new docs/06_entropy_sweep_protocol.md
- system_v5/new docs/10_cross_domain_equivalence_map.md
- system_v5/new docs/09_research_inventory_and_foundations.md
"""

import json
import os
from typing import Callable, Dict, List

import numpy as np
classification = "classical_baseline"  # auto-backfill


TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed for this bounded taxonomy sim"},
    "pyg": {"tried": False, "used": False, "reason": "not needed for this bounded taxonomy sim"},
    "z3": {"tried": False, "used": False, "reason": "not needed for this bounded taxonomy sim"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed for this bounded taxonomy sim"},
    "sympy": {"tried": False, "used": False, "reason": "not needed for this bounded taxonomy sim"},
    "clifford": {"tried": False, "used": False, "reason": "not needed for this bounded taxonomy sim"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed for this bounded taxonomy sim"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed for this bounded taxonomy sim"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed for this bounded taxonomy sim"},
    "xgi": {"tried": False, "used": False, "reason": "not needed for this bounded taxonomy sim"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed for this bounded taxonomy sim"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed for this bounded taxonomy sim"},
}

EPS = 1e-10


def dm_from_ket(vec: np.ndarray) -> np.ndarray:
    vec = np.asarray(vec, dtype=np.complex128).reshape(-1, 1)
    return vec @ vec.conj().T


def normalize_density(rho: np.ndarray) -> np.ndarray:
    rho = np.asarray(rho, dtype=np.complex128)
    rho = 0.5 * (rho + rho.conj().T)
    return rho / np.trace(rho).real


def von_neumann_entropy(rho: np.ndarray) -> float:
    evals = np.linalg.eigvalsh(normalize_density(rho))
    evals = np.clip(evals.real, EPS, 1.0)
    return float(-np.sum(evals * np.log2(evals)))


def diagonal_shannon_entropy(rho: np.ndarray) -> float:
    probs = np.clip(np.real(np.diag(normalize_density(rho))), EPS, 1.0)
    probs = probs / probs.sum()
    return float(-np.sum(probs * np.log2(probs)))


def trace_distance(rho: np.ndarray, sigma: np.ndarray) -> float:
    diff = normalize_density(rho) - normalize_density(sigma)
    evals = np.linalg.eigvalsh(0.5 * (diff + diff.conj().T))
    return float(0.5 * np.sum(np.abs(evals)))


def shell_weighted_entropy(trajectory: List[np.ndarray], weights: List[float]) -> float:
    weights = np.asarray(weights, dtype=np.float64)
    weights = weights / weights.sum()
    entropies = np.array([von_neumann_entropy(rho) for rho in trajectory], dtype=np.float64)
    return float(np.dot(weights, entropies))


def history_window_entropy(trajectory: List[np.ndarray], window: int) -> float:
    vals = []
    for idx in range(len(trajectory) - window + 1):
        avg_state = sum(trajectory[idx: idx + window]) / window
        vals.append(von_neumann_entropy(avg_state))
    return float(np.mean(vals))


def transport_weighted_entropy(trajectory: List[np.ndarray]) -> float:
    total = 0.0
    for left, right in zip(trajectory[:-1], trajectory[1:]):
        dist = trace_distance(left, right)
        local_entropy = 0.5 * (von_neumann_entropy(left) + von_neumann_entropy(right))
        total += dist * local_entropy
    return float(total)


def ordered_path_entropy(rho0: np.ndarray, operators: List[Callable[[np.ndarray], np.ndarray]]) -> float:
    trajectory = [normalize_density(rho0)]
    current = trajectory[0]
    for op in operators:
        current = normalize_density(op(current))
        trajectory.append(current)
    weights = np.arange(1, len(trajectory) + 1, dtype=np.float64)
    return shell_weighted_entropy(trajectory, weights.tolist())


def apply_sequence(rho0: np.ndarray, operators: List[Callable[[np.ndarray], np.ndarray]]) -> List[np.ndarray]:
    out = [normalize_density(rho0)]
    current = out[0]
    for op in operators:
        current = normalize_density(op(current))
        out.append(current)
    return out


def x_rotation(theta: float) -> Callable[[np.ndarray], np.ndarray]:
    sx = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
    ident = np.eye(2, dtype=np.complex128)
    unitary = np.cos(theta / 2.0) * ident - 1j * np.sin(theta / 2.0) * sx
    return lambda rho: unitary @ rho @ unitary.conj().T


def z_rotation(theta: float) -> Callable[[np.ndarray], np.ndarray]:
    sz = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
    ident = np.eye(2, dtype=np.complex128)
    unitary = np.cos(theta / 2.0) * ident - 1j * np.sin(theta / 2.0) * sz
    return lambda rho: unitary @ rho @ unitary.conj().T


def z_dephasing(p: float) -> Callable[[np.ndarray], np.ndarray]:
    sz = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)

    def channel(rho: np.ndarray) -> np.ndarray:
        return (1.0 - p) * rho + p * (sz @ rho @ sz)

    return channel


def amplitude_damping(gamma: float) -> Callable[[np.ndarray], np.ndarray]:
    k0 = np.array([[1.0, 0.0], [0.0, np.sqrt(1.0 - gamma)]], dtype=np.complex128)
    k1 = np.array([[0.0, np.sqrt(gamma)], [0.0, 0.0]], dtype=np.complex128)

    def channel(rho: np.ndarray) -> np.ndarray:
        return k0 @ rho @ k0.conj().T + k1 @ rho @ k1.conj().T

    return channel


def identity_transport() -> Callable[[np.ndarray], np.ndarray]:
    return lambda rho: rho


def summarize_taxonomy(sample_trajectory: List[np.ndarray]) -> Dict[str, str]:
    uniform_shell = shell_weighted_entropy(sample_trajectory, [1.0] * len(sample_trajectory))
    relabeled_shell = shell_weighted_entropy(sample_trajectory, [1.0, 2.0, 3.0, 4.0][: len(sample_trajectory)])
    history_val = history_window_entropy(sample_trajectory, min(2, len(sample_trajectory)))
    transport_val = transport_weighted_entropy(sample_trajectory)
    return {
        "shell_weighted": (
            "shell-index bookkeeping candidate"
            if abs(uniform_shell - relabeled_shell) > 1e-6
            else "state-summary candidate"
        ),
        "history_window": (
            "order/grouping-sensitive candidate"
            if abs(history_val - uniform_shell) > 1e-6
            else "collapses to shell summary at this window"
        ),
        "transport_weighted": (
            "geometry/trajectory-sensitive candidate"
            if transport_val > 1e-8
            else "collapses under identity transport"
        ),
        "operator_order_sensitive": "final-state order-sensitive candidate, pre-bridge only",
    }


def run_positive_tests() -> Dict[str, dict]:
    psi_plus = np.array([1.0, 1.0], dtype=np.complex128) / np.sqrt(2.0)
    rho0 = dm_from_ket(psi_plus)

    noncomm_ops = [x_rotation(np.pi / 3.0), z_dephasing(0.35), x_rotation(-np.pi / 5.0)]
    commuting_ops = [z_rotation(np.pi / 4.0), z_dephasing(0.35), z_rotation(-np.pi / 7.0)]

    trajectory = apply_sequence(rho0, noncomm_ops)
    permuted = [trajectory[0], trajectory[2], trajectory[1], trajectory[3]]
    constant_traj = [trajectory[0], trajectory[0], trajectory[0], trajectory[0]]

    shell_uniform = shell_weighted_entropy(trajectory, [1, 1, 1, 1])
    shell_uniform_permuted = shell_weighted_entropy(permuted, [1, 1, 1, 1])
    shell_reindexed = shell_weighted_entropy(permuted, [1, 2, 3, 4])

    history_base = history_window_entropy(trajectory, 2)
    history_permuted = history_window_entropy(permuted, 2)
    transport_base = transport_weighted_entropy(trajectory)
    transport_constant = transport_weighted_entropy(constant_traj)

    noncomm_forward = von_neumann_entropy(
        apply_sequence(rho0, [amplitude_damping(0.35), x_rotation(np.pi / 3.0), amplitude_damping(0.2)])[-1]
    )
    noncomm_reverse = von_neumann_entropy(
        apply_sequence(rho0, [amplitude_damping(0.2), x_rotation(np.pi / 3.0), amplitude_damping(0.35)])[-1]
    )
    commuting_forward = von_neumann_entropy(
        apply_sequence(rho0, [z_rotation(np.pi / 4.0), z_dephasing(0.35)])[-1]
    )
    commuting_reverse = von_neumann_entropy(
        apply_sequence(rho0, [z_dephasing(0.35), z_rotation(np.pi / 4.0)])[-1]
    )

    return {
        "shell_uniform_invariant_under_state_permutation": {
            "shell_uniform": shell_uniform,
            "shell_uniform_permuted": shell_uniform_permuted,
            "equal": abs(shell_uniform - shell_uniform_permuted) < 1e-10,
            "pass": abs(shell_uniform - shell_uniform_permuted) < 1e-10,
        },
        "history_window_detects_temporal_reordering": {
            "history_base": history_base,
            "history_permuted": history_permuted,
            "different": abs(history_base - history_permuted) > 1e-4,
            "pass": abs(history_base - history_permuted) > 1e-4,
        },
        "transport_collapses_under_identity_transport": {
            "transport_base": transport_base,
            "transport_constant": transport_constant,
            "constant_zero": abs(transport_constant) < 1e-12,
            "base_positive": transport_base > 1e-4,
            "pass": abs(transport_constant) < 1e-12 and transport_base > 1e-4,
        },
        "operator_order_detects_noncommuting_sequence": {
            "forward": noncomm_forward,
            "reverse": noncomm_reverse,
            "different": abs(noncomm_forward - noncomm_reverse) > 1e-4,
            "pass": abs(noncomm_forward - noncomm_reverse) > 1e-4,
        },
        "operator_order_is_stable_for_commuting_control": {
            "forward": commuting_forward,
            "reverse": commuting_reverse,
            "equal": abs(commuting_forward - commuting_reverse) < 1e-10,
            "pass": abs(commuting_forward - commuting_reverse) < 1e-10,
        },
        "shell_reindexing_is_bookkeeping_not_transport": {
            "shell_uniform_permuted": shell_uniform_permuted,
            "shell_reindexed": shell_reindexed,
            "transport_permuted": transport_weighted_entropy(permuted),
            "reindex_changes_shell": abs(shell_uniform_permuted - shell_reindexed) > 1e-6,
            "pass": abs(shell_uniform_permuted - shell_reindexed) > 1e-6,
        },
    }


def run_negative_tests() -> Dict[str, dict]:
    psi_plus = np.array([1.0, 1.0], dtype=np.complex128) / np.sqrt(2.0)
    rho0 = dm_from_ket(psi_plus)
    rotated = x_rotation(np.pi / 3.0)(rho0)
    constant_traj = [rho0, rho0, rho0, rho0]
    two_state = [rho0, rotated, rho0, rotated]

    rho_basis = dm_from_ket(np.array([1.0, 0.0], dtype=np.complex128))
    diag_shannon_z = diagonal_shannon_entropy(rho_basis)
    diag_shannon_x = diagonal_shannon_entropy(x_rotation(np.pi / 3.0)(rho_basis))
    vn_z = von_neumann_entropy(rho_basis)
    vn_x = von_neumann_entropy(x_rotation(np.pi / 3.0)(rho_basis))

    return {
        "counterfeit_transport_from_repetition_fails": {
            "transport_constant": transport_weighted_entropy(constant_traj),
            "fake_signal_absent": abs(transport_weighted_entropy(constant_traj)) < 1e-12,
            "pass": abs(transport_weighted_entropy(constant_traj)) < 1e-12,
        },
        "history_window_one_step_collapses_to_shell_mean": {
            "history_w1": history_window_entropy(two_state, 1),
            "shell_uniform": shell_weighted_entropy(two_state, [1, 1, 1, 1]),
            "equal": abs(history_window_entropy(two_state, 1) - shell_weighted_entropy(two_state, [1, 1, 1, 1])) < 1e-10,
            "pass": abs(history_window_entropy(two_state, 1) - shell_weighted_entropy(two_state, [1, 1, 1, 1])) < 1e-10,
        },
        "commuting_order_cannot_fake_operator_signal": {
            "forward": von_neumann_entropy(apply_sequence(rho0, [z_rotation(np.pi / 6.0), z_dephasing(0.2)])[-1]),
            "reverse": von_neumann_entropy(apply_sequence(rho0, [z_dephasing(0.2), z_rotation(np.pi / 6.0)])[-1]),
            "equal": abs(
                von_neumann_entropy(apply_sequence(rho0, [z_rotation(np.pi / 6.0), z_dephasing(0.2)])[-1])
                - von_neumann_entropy(apply_sequence(rho0, [z_dephasing(0.2), z_rotation(np.pi / 6.0)])[-1])
            ) < 1e-10,
            "pass": abs(
                von_neumann_entropy(apply_sequence(rho0, [z_rotation(np.pi / 6.0), z_dephasing(0.2)])[-1])
                - von_neumann_entropy(apply_sequence(rho0, [z_dephasing(0.2), z_rotation(np.pi / 6.0)])[-1])
            ) < 1e-10,
        },
        "diagonal_shannon_is_basis_dependent_counterfeit": {
            "diag_shannon_before": diag_shannon_z,
            "diag_shannon_after_basis_change": diag_shannon_x,
            "von_neumann_before": vn_z,
            "von_neumann_after_basis_change": vn_x,
            "shannon_changes": abs(diag_shannon_z - diag_shannon_x) > 1e-4,
            "vn_invariant": abs(vn_z - vn_x) < 1e-10,
            "pass": abs(diag_shannon_z - diag_shannon_x) > 1e-4 and abs(vn_z - vn_x) < 1e-10,
        },
    }


def run_boundary_tests() -> Dict[str, dict]:
    psi_plus = np.array([1.0, 1.0], dtype=np.complex128) / np.sqrt(2.0)
    rho0 = dm_from_ket(psi_plus)
    rho1 = z_dephasing(0.5)(rho0)
    short_traj = [rho0, rho1]
    long_traj = apply_sequence(rho0, [x_rotation(np.pi / 4.0), z_dephasing(0.25), x_rotation(-np.pi / 6.0)])

    history_full = history_window_entropy(long_traj, len(long_traj))
    global_avg = von_neumann_entropy(sum(long_traj) / len(long_traj))

    return {
        "two_state_minimal_history_transport": {
            "history_w2": history_window_entropy(short_traj, 2),
            "entropy_global_average": von_neumann_entropy((rho0 + rho1) / 2.0),
            "transport": transport_weighted_entropy(short_traj),
            "history_matches_average": abs(history_window_entropy(short_traj, 2) - von_neumann_entropy((rho0 + rho1) / 2.0)) < 1e-10,
            "pass": abs(history_window_entropy(short_traj, 2) - von_neumann_entropy((rho0 + rho1) / 2.0)) < 1e-10,
        },
        "full_window_history_equals_global_average_entropy": {
            "history_full_window": history_full,
            "global_average_entropy": global_avg,
            "equal": abs(history_full - global_avg) < 1e-10,
            "pass": abs(history_full - global_avg) < 1e-10,
        },
        "identity_operator_insertion_keeps_transport_zero": {
            "transport_identity_only": transport_weighted_entropy(apply_sequence(rho0, [identity_transport(), identity_transport()])),
            "zero": abs(transport_weighted_entropy(apply_sequence(rho0, [identity_transport(), identity_transport()]))) < 1e-12,
            "pass": abs(transport_weighted_entropy(apply_sequence(rho0, [identity_transport(), identity_transport()]))) < 1e-12,
        },
    }


def count_section(section: Dict[str, dict]) -> Dict[str, int]:
    total = sum(1 for value in section.values() if isinstance(value, dict) and "pass" in value)
    passed = sum(1 for value in section.values() if isinstance(value, dict) and value.get("pass") is True)
    return {"passed": passed, "failed": total - passed, "total": total}


def main() -> None:
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    sample_traj = apply_sequence(
        dm_from_ket(np.array([1.0, 1.0], dtype=np.complex128) / np.sqrt(2.0)),
        [x_rotation(np.pi / 3.0), z_dephasing(0.35), x_rotation(-np.pi / 5.0)],
    )

    pos_counts = count_section(positive)
    neg_counts = count_section(negative)
    bnd_counts = count_section(boundary)
    total_fail = pos_counts["failed"] + neg_counts["failed"] + bnd_counts["failed"]

    results = {
        "name": "PURE LEGO: Pre-Bridge Entropy Transport/History Taxonomy",
        "probe": "entropy_transport_history_taxonomy",
        "purpose": (
            "Separate shell-weighted, history-window, transport-weighted, "
            "and operator-order-sensitive entropy-like functionals on simple trajectories"
        ),
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "taxonomy_summary": summarize_taxonomy(sample_traj),
        "caveat": (
            "Pre-bridge candidate taxonomy only. No shell/transport/history family "
            "here is promoted to final doctrine."
        ),
        "classification": "classical_baseline",
        "summary": {
            "positive_pass": pos_counts["passed"],
            "positive_fail": pos_counts["failed"],
            "negative_pass": neg_counts["passed"],
            "negative_fail": neg_counts["failed"],
            "boundary_pass": bnd_counts["passed"],
            "boundary_fail": bnd_counts["failed"],
            "total_fail": total_fail,
            "all_pass": total_fail == 0,
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entropy_transport_history_taxonomy_results.json")
    with open(out_path, "w") as handle:
        json.dump(results, handle, indent=2)

    print(f"Results written to {out_path}")
    print(json.dumps(results["summary"], indent=2))


if __name__ == "__main__":
    main()
