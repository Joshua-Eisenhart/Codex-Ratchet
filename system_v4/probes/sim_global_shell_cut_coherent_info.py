#!/usr/bin/env python3
"""
PURE LEGO: Global Shell-Cut Coherent Information
================================================
Standalone pre-final-canon sim for shell-indexed coherent-information forms.

This probe compares:
1. local shell coherent information I_c(r)
2. uniform shell averages
3. weighted shell sums phi_w = sum_r w_r I_c(r)

The goal is bounded taxonomy and falsification:
- when weighting sharpens discrimination beyond local/uniform summaries
- when weighting is only shell bookkeeping
- when weighting cannot manufacture signal from uniformly weak shells

Boot context:
- new docs/06_entropy_sweep_protocol.md
- new docs/10_cross_domain_equivalence_map.md
- new docs/09_research_inventory_and_foundations.md
"""

import json
import os
from typing import Dict, List

import numpy as np


TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed for this bounded pure-math shell sim"},
    "pyg": {"tried": False, "used": False, "reason": "not needed for this bounded pure-math shell sim"},
    "z3": {"tried": False, "used": False, "reason": "not needed for this bounded pure-math shell sim"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed for this bounded pure-math shell sim"},
    "sympy": {"tried": False, "used": False, "reason": "not needed for this bounded pure-math shell sim"},
    "clifford": {"tried": False, "used": False, "reason": "not needed for this bounded pure-math shell sim"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed for this bounded pure-math shell sim"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed for this bounded pure-math shell sim"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed for this bounded pure-math shell sim"},
    "xgi": {"tried": False, "used": False, "reason": "not needed for this bounded pure-math shell sim"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed for this bounded pure-math shell sim"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed for this bounded pure-math shell sim"},
}

EPS = 1e-12


def bell_projector() -> np.ndarray:
    psi = np.array([1.0, 0.0, 0.0, 1.0], dtype=np.complex128) / np.sqrt(2.0)
    return np.outer(psi, psi.conj())


def werner_like_state(p: float) -> np.ndarray:
    ident = np.eye(4, dtype=np.complex128) / 4.0
    return p * bell_projector() + (1.0 - p) * ident


def partial_trace_b(rho_ab: np.ndarray) -> np.ndarray:
    reshaped = rho_ab.reshape(2, 2, 2, 2)
    return np.einsum("abcb->ac", reshaped)


def von_neumann_entropy(rho: np.ndarray) -> float:
    evals = np.linalg.eigvalsh(0.5 * (rho + rho.conj().T)).real
    evals = np.clip(evals, EPS, 1.0)
    return float(-np.sum(evals * np.log2(evals)))


def coherent_information(rho_ab: np.ndarray) -> float:
    rho_b = partial_trace_b(rho_ab)
    return float(von_neumann_entropy(rho_b) - von_neumann_entropy(rho_ab))


def normalize_weights(weights: List[float]) -> np.ndarray:
    weights_np = np.asarray(weights, dtype=np.float64)
    return weights_np / weights_np.sum()


def shell_profile_ic(ps: List[float]) -> List[float]:
    return [coherent_information(werner_like_state(p)) for p in ps]


def weighted_shell_sum(values: List[float], weights: List[float]) -> float:
    return float(np.dot(normalize_weights(weights), np.asarray(values, dtype=np.float64)))


def summarize_candidate_behavior() -> Dict[str, str]:
    return {
        "local_shell_ic": "local cut-state signed quantity per shell",
        "uniform_shell_average": "placement-blind shell summary",
        "weighted_shell_sum": "global shell-cut candidate that can sharpen shell placement differences",
        "caveat": "weighting is not doctrine by itself; constant-profile and weak-shell counterfeits must collapse",
    }


def run_positive_tests() -> Dict[str, dict]:
    increasing_weights = [1.0, 2.0, 3.0, 4.0]
    uniform_weights = [1.0, 1.0, 1.0, 1.0]

    front_loaded = [0.9, 0.7, 0.3, 0.1]
    back_loaded = list(reversed(front_loaded))
    front_ic = shell_profile_ic(front_loaded)
    back_ic = shell_profile_ic(back_loaded)

    monotone_strong = [0.2, 0.5, 0.8, 1.0]
    monotone_ic = shell_profile_ic(monotone_strong)

    return {
        "weighting_sharpens_shell_placement_with_same_uniform_average": {
            "front_uniform": weighted_shell_sum(front_ic, uniform_weights),
            "back_uniform": weighted_shell_sum(back_ic, uniform_weights),
            "front_weighted": weighted_shell_sum(front_ic, increasing_weights),
            "back_weighted": weighted_shell_sum(back_ic, increasing_weights),
            "uniform_equal": abs(weighted_shell_sum(front_ic, uniform_weights) - weighted_shell_sum(back_ic, uniform_weights)) < 1e-12,
            "weighted_distinguishes": abs(weighted_shell_sum(front_ic, increasing_weights) - weighted_shell_sum(back_ic, increasing_weights)) > 1e-4,
            "pass": abs(weighted_shell_sum(front_ic, uniform_weights) - weighted_shell_sum(back_ic, uniform_weights)) < 1e-12
                    and abs(weighted_shell_sum(front_ic, increasing_weights) - weighted_shell_sum(back_ic, increasing_weights)) > 1e-4,
        },
        "weighted_sum_matches_manual_normalized_definition": {
            "shell_ic": front_ic,
            "weighted_value": weighted_shell_sum(front_ic, increasing_weights),
            "manual_value": float(np.dot(np.array([0.1, 0.2, 0.3, 0.4]), np.asarray(front_ic))),
            "equal": abs(weighted_shell_sum(front_ic, increasing_weights) - float(np.dot(np.array([0.1, 0.2, 0.3, 0.4]), np.asarray(front_ic)))) < 1e-12,
            "pass": abs(weighted_shell_sum(front_ic, increasing_weights) - float(np.dot(np.array([0.1, 0.2, 0.3, 0.4]), np.asarray(front_ic)))) < 1e-12,
        },
        "uniform_weights_are_shell_permutation_blind": {
            "profile_a_uniform": weighted_shell_sum(front_ic, uniform_weights),
            "profile_b_uniform": weighted_shell_sum(back_ic, uniform_weights),
            "equal": abs(weighted_shell_sum(front_ic, uniform_weights) - weighted_shell_sum(back_ic, uniform_weights)) < 1e-12,
            "pass": abs(weighted_shell_sum(front_ic, uniform_weights) - weighted_shell_sum(back_ic, uniform_weights)) < 1e-12,
        },
        "weighted_global_prefers_late_strong_shells": {
            "uniform_mean": weighted_shell_sum(monotone_ic, uniform_weights),
            "weighted_sum": weighted_shell_sum(monotone_ic, increasing_weights),
            "weighted_larger": weighted_shell_sum(monotone_ic, increasing_weights) > weighted_shell_sum(monotone_ic, uniform_weights),
            "pass": weighted_shell_sum(monotone_ic, increasing_weights) > weighted_shell_sum(monotone_ic, uniform_weights),
        },
        "global_weighting_tracks_positive_shell_tail_better_than_first_shell_only": {
            "first_shell_ic": monotone_ic[0],
            "last_shell_ic": monotone_ic[-1],
            "weighted_sum": weighted_shell_sum(monotone_ic, increasing_weights),
            "weighted_between_extremes": monotone_ic[0] < weighted_shell_sum(monotone_ic, increasing_weights) < monotone_ic[-1],
            "pass": monotone_ic[0] < weighted_shell_sum(monotone_ic, increasing_weights) < monotone_ic[-1],
        },
    }


def run_negative_tests() -> Dict[str, dict]:
    increasing_weights = [1.0, 2.0, 3.0, 4.0]
    scaled_weights = [10.0, 20.0, 30.0, 40.0]

    constant_profile = [0.7, 0.7, 0.7, 0.7]
    weak_profile = [0.1, 0.2, 0.2, 0.1]

    constant_ic = shell_profile_ic(constant_profile)
    weak_ic = shell_profile_ic(weak_profile)

    return {
        "constant_shell_profile_adds_no_weighting_signal": {
            "uniform_mean": weighted_shell_sum(constant_ic, [1, 1, 1, 1]),
            "weighted_sum": weighted_shell_sum(constant_ic, increasing_weights),
            "equal": abs(weighted_shell_sum(constant_ic, [1, 1, 1, 1]) - weighted_shell_sum(constant_ic, increasing_weights)) < 1e-12,
            "pass": abs(weighted_shell_sum(constant_ic, [1, 1, 1, 1]) - weighted_shell_sum(constant_ic, increasing_weights)) < 1e-12,
        },
        "weighting_cannot_manufacture_positive_signal_from_uniformly_weak_shells": {
            "shell_ic": weak_ic,
            "uniform_mean": weighted_shell_sum(weak_ic, [1, 1, 1, 1]),
            "weighted_sum": weighted_shell_sum(weak_ic, increasing_weights),
            "all_nonpositive": all(value <= 0.0 for value in weak_ic),
            "weighted_nonpositive": weighted_shell_sum(weak_ic, increasing_weights) <= 0.0,
            "pass": all(value <= 0.0 for value in weak_ic) and weighted_shell_sum(weak_ic, increasing_weights) <= 0.0,
        },
        "normalized_weighting_is_scale_invariant_not_extra_signal": {
            "weighted_sum": weighted_shell_sum(weak_ic, increasing_weights),
            "scaled_weighted_sum": weighted_shell_sum(weak_ic, scaled_weights),
            "equal": abs(weighted_shell_sum(weak_ic, increasing_weights) - weighted_shell_sum(weak_ic, scaled_weights)) < 1e-12,
            "pass": abs(weighted_shell_sum(weak_ic, increasing_weights) - weighted_shell_sum(weak_ic, scaled_weights)) < 1e-12,
        },
        "single_local_shell_cannot_recover_global_placement_discrimination": {
            "front_first_shell": shell_profile_ic([0.9])[0],
            "back_first_shell": shell_profile_ic([0.1])[0],
            "front_weighted": weighted_shell_sum(shell_profile_ic([0.9, 0.7, 0.3, 0.1]), increasing_weights),
            "back_weighted": weighted_shell_sum(shell_profile_ic([0.1, 0.3, 0.7, 0.9]), increasing_weights),
            "global_and_local_differ": abs(
                (shell_profile_ic([0.9])[0] - shell_profile_ic([0.1])[0])
                - (
                    weighted_shell_sum(shell_profile_ic([0.9, 0.7, 0.3, 0.1]), increasing_weights)
                    - weighted_shell_sum(shell_profile_ic([0.1, 0.3, 0.7, 0.9]), increasing_weights)
                )
            ) > 1e-4,
            "pass": abs(
                (shell_profile_ic([0.9])[0] - shell_profile_ic([0.1])[0])
                - (
                    weighted_shell_sum(shell_profile_ic([0.9, 0.7, 0.3, 0.1]), increasing_weights)
                    - weighted_shell_sum(shell_profile_ic([0.1, 0.3, 0.7, 0.9]), increasing_weights)
                )
            ) > 1e-4,
        },
    }


def run_boundary_tests() -> Dict[str, dict]:
    weights = [1.0, 2.0, 3.0, 4.0]
    profile = [0.2, 0.5, 0.8, 1.0]
    profile_ic = shell_profile_ic(profile)

    return {
        "single_shell_reduces_to_local_coherent_information": {
            "local_ic": shell_profile_ic([0.8])[0],
            "weighted_single_shell": weighted_shell_sum(shell_profile_ic([0.8]), [5.0]),
            "equal": abs(shell_profile_ic([0.8])[0] - weighted_shell_sum(shell_profile_ic([0.8]), [5.0])) < 1e-12,
            "pass": abs(shell_profile_ic([0.8])[0] - weighted_shell_sum(shell_profile_ic([0.8]), [5.0])) < 1e-12,
        },
        "one_hot_weight_selects_target_shell": {
            "target_shell_ic": profile_ic[2],
            "one_hot_value": weighted_shell_sum(profile_ic, [0.0, 0.0, 1.0, 0.0]),
            "equal": abs(profile_ic[2] - weighted_shell_sum(profile_ic, [0.0, 0.0, 1.0, 0.0])) < 1e-12,
            "pass": abs(profile_ic[2] - weighted_shell_sum(profile_ic, [0.0, 0.0, 1.0, 0.0])) < 1e-12,
        },
        "uniform_weights_reduce_to_arithmetic_mean": {
            "uniform_value": weighted_shell_sum(profile_ic, [1.0, 1.0, 1.0, 1.0]),
            "mean_value": float(np.mean(profile_ic)),
            "equal": abs(weighted_shell_sum(profile_ic, [1.0, 1.0, 1.0, 1.0]) - float(np.mean(profile_ic))) < 1e-12,
            "pass": abs(weighted_shell_sum(profile_ic, [1.0, 1.0, 1.0, 1.0]) - float(np.mean(profile_ic))) < 1e-12,
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

    pos_counts = count_section(positive)
    neg_counts = count_section(negative)
    bnd_counts = count_section(boundary)
    total_fail = pos_counts["failed"] + neg_counts["failed"] + bnd_counts["failed"]

    results = {
        "name": "PURE LEGO: Global Shell-Cut Coherent Information",
        "probe": "global_shell_cut_coherent_info",
        "purpose": (
            "Compare local coherent information against weighted shell sums on simple shell-indexed bipartite families"
        ),
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "taxonomy_summary": summarize_candidate_behavior(),
        "classification": "classical_baseline",
        "caveat": (
            "Pre-final-canon only. Weighting may sharpen shell placement effects, but it is not promoted here beyond candidate status."
        ),
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
    out_path = os.path.join(out_dir, "global_shell_cut_coherent_info_results.json")
    with open(out_path, "w") as handle:
        json.dump(results, handle, indent=2)

    print(f"Results written to {out_path}")
    print(json.dumps(results["summary"], indent=2))


if __name__ == "__main__":
    main()
