#!/usr/bin/env python3
"""
PURE LEGO: 2-Qubit vs 3-Qubit Bridge Kernel Advantage
=====================================================
Bounded pure-math comparison of when a 3-qubit lift provides real extra
discrimination beyond matched 2-qubit bridge-built kernels.

Compared objects:
  - 2-qubit product, classical-correlated, Bell, Werner-like families
  - matched 3-qubit ancilla lifts
  - genuine 3-qubit GHZ and mixed bridge-style families

Advantage is treated narrowly:
  - matched-cut preservation is not itself an advantage
  - extra discrimination comes from multi-cut coverage, localization
    patterns, or tripartite companion structure
"""

import json
import os
from typing import Dict, List

import numpy as np

EPS = 1e-12

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "pure-math numpy baseline"},
    "pyg": {"tried": False, "used": False, "reason": "not needed for this bounded comparison sim"},
    "z3": {"tried": False, "used": False, "reason": "not needed for this bounded comparison sim"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed for this bounded comparison sim"},
    "sympy": {"tried": False, "used": False, "reason": "not needed for this bounded comparison sim"},
    "clifford": {"tried": False, "used": False, "reason": "not needed for this bounded comparison sim"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed for this bounded comparison sim"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed for this bounded comparison sim"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed for this bounded comparison sim"},
    "xgi": {"tried": False, "used": False, "reason": "not needed for this bounded comparison sim"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed for this bounded comparison sim"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed for this bounded comparison sim"},
}


def normalize_rho(rho: np.ndarray) -> np.ndarray:
    rho = 0.5 * (rho + rho.conj().T)
    tr = np.trace(rho)
    if abs(tr) < EPS:
        raise ValueError("trace too small")
    return rho / tr


def pure_density(psi: np.ndarray) -> np.ndarray:
    psi = np.asarray(psi, dtype=np.complex128)
    return normalize_rho(np.outer(psi, psi.conj()))


def vn_entropy(rho: np.ndarray) -> float:
    evals = np.linalg.eigvalsh(normalize_rho(rho)).real
    evals = np.clip(evals, 0.0, None)
    nz = evals[evals > EPS]
    if len(nz) == 0:
        return 0.0
    return float(-np.sum(nz * np.log2(nz)))


def partial_trace_2q_A(rho_ab: np.ndarray) -> np.ndarray:
    return np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def partial_trace_2q_B(rho_ab: np.ndarray) -> np.ndarray:
    return np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=1, axis2=3)


def partial_transpose_2q(rho_ab: np.ndarray) -> np.ndarray:
    return rho_ab.reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)


def kernel_report_2q(rho_ab: np.ndarray) -> Dict[str, float]:
    rho_a = partial_trace_2q_A(rho_ab)
    rho_b = partial_trace_2q_B(rho_ab)
    pt = partial_transpose_2q(normalize_rho(rho_ab))
    evals = np.linalg.eigvalsh(0.5 * (pt + pt.conj().T))
    return {
        "mutual_information": vn_entropy(rho_a) + vn_entropy(rho_b) - vn_entropy(rho_ab),
        "conditional_entropy_a_given_b": vn_entropy(rho_ab) - vn_entropy(rho_b),
        "coherent_information_to_b": vn_entropy(rho_b) - vn_entropy(rho_ab),
        "negativity": float(max(0.0, (np.sum(np.abs(evals)) - 1.0) / 2.0)),
    }


def basis3(bits: str) -> np.ndarray:
    vec = np.zeros(8, dtype=np.complex128)
    vec[int(bits, 2)] = 1.0
    return vec


def reduced_density_3q(rho: np.ndarray, keep: List[int]) -> np.ndarray:
    bra = ["a", "b", "c"]
    ket = ["d", "e", "f"]
    for idx in range(3):
        if idx not in keep:
            ket[idx] = bra[idx]
    subs_in = "".join(bra + ket)
    subs_out = "".join([bra[idx] for idx in keep] + [ket[idx] for idx in keep])
    reduced = np.einsum(f"{subs_in}->{subs_out}", rho.reshape(2, 2, 2, 2, 2, 2))
    dim = 2 ** len(keep)
    return normalize_rho(reduced.reshape(dim, dim))


def partial_transpose_3q(rho: np.ndarray, subsystem: int) -> np.ndarray:
    tensor = rho.reshape(2, 2, 2, 2, 2, 2)
    if subsystem == 0:
        pt = tensor.transpose(3, 1, 2, 0, 4, 5)
    elif subsystem == 1:
        pt = tensor.transpose(0, 4, 2, 3, 1, 5)
    else:
        pt = tensor.transpose(0, 1, 5, 3, 4, 2)
    return normalize_rho(pt.reshape(8, 8))


def kernel_report_3q(rho: np.ndarray) -> Dict[str, dict]:
    partitions = {
        "A|BC": {"a": [0], "b": [1, 2], "pt_sys": 0},
        "B|AC": {"a": [1], "b": [0, 2], "pt_sys": 1},
        "C|AB": {"a": [2], "b": [0, 1], "pt_sys": 2},
    }
    out: Dict[str, dict] = {}
    for label, spec in partitions.items():
        rho_a = reduced_density_3q(rho, spec["a"])
        rho_b = reduced_density_3q(rho, spec["b"])
        pt = partial_transpose_3q(rho, spec["pt_sys"])
        evals = np.linalg.eigvalsh(pt)
        out[label] = {
            "mutual_information": vn_entropy(rho_a) + vn_entropy(rho_b) - vn_entropy(rho),
            "conditional_entropy_a_given_b": vn_entropy(rho) - vn_entropy(rho_b),
            "coherent_information_to_b": vn_entropy(rho_b) - vn_entropy(rho),
            "negativity": float(max(0.0, (np.sum(np.abs(evals)) - 1.0) / 2.0)),
        }
    s_a = vn_entropy(reduced_density_3q(rho, [0]))
    s_b = vn_entropy(reduced_density_3q(rho, [1]))
    s_c = vn_entropy(reduced_density_3q(rho, [2]))
    s_ab = vn_entropy(reduced_density_3q(rho, [0, 1]))
    s_ac = vn_entropy(reduced_density_3q(rho, [0, 2]))
    s_bc = vn_entropy(reduced_density_3q(rho, [1, 2]))
    s_abc = vn_entropy(rho)
    out["tripartite_mutual_information"] = s_a + s_b + s_c - s_ab - s_ac - s_bc + s_abc
    return out


def active_signed_cut_count(report_3q: Dict[str, dict]) -> int:
    return sum(1 for key in ["A|BC", "B|AC", "C|AB"] if report_3q[key]["coherent_information_to_b"] > 1e-9 or report_3q[key]["negativity"] > 1e-9)


def matched_cut_delta(report_2q: Dict[str, float], report_3q: Dict[str, dict], cut: str) -> Dict[str, float]:
    return {
        "mi_delta": abs(report_2q["mutual_information"] - report_3q[cut]["mutual_information"]),
        "cond_delta": abs(report_2q["conditional_entropy_a_given_b"] - report_3q[cut]["conditional_entropy_a_given_b"]),
        "ic_delta": abs(report_2q["coherent_information_to_b"] - report_3q[cut]["coherent_information_to_b"]),
        "neg_delta": abs(report_2q["negativity"] - report_3q[cut]["negativity"]),
    }


def bell_2q() -> np.ndarray:
    zero = np.array([1.0, 0.0], dtype=np.complex128)
    one = np.array([0.0, 1.0], dtype=np.complex128)
    psi = (np.kron(zero, zero) + np.kron(one, one)) / np.sqrt(2.0)
    return pure_density(psi)


def product_2q() -> np.ndarray:
    zero = np.array([1.0, 0.0], dtype=np.complex128)
    return pure_density(np.kron(zero, zero))


def classical_2q() -> np.ndarray:
    zero = np.array([1.0, 0.0], dtype=np.complex128)
    one = np.array([0.0, 1.0], dtype=np.complex128)
    return normalize_rho(0.7 * pure_density(np.kron(zero, zero)) + 0.3 * pure_density(np.kron(one, one)))


def werner_2q(p: float = 0.55) -> np.ndarray:
    return normalize_rho(p * bell_2q() + (1.0 - p) * np.eye(4, dtype=np.complex128) / 4.0)


def lift_2q_to_3q(rho_ab: np.ndarray) -> np.ndarray:
    anc = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=np.complex128)
    return np.kron(rho_ab, anc)


def ghz_3q() -> np.ndarray:
    psi = (basis3("000") + basis3("111")) / np.sqrt(2.0)
    return pure_density(psi)


def bridge_mixture_3q() -> np.ndarray:
    return normalize_rho(0.55 * ghz_3q() + 0.45 * np.eye(8, dtype=np.complex128) / 8.0)


def run_positive_tests() -> Dict[str, dict]:
    bell2 = kernel_report_2q(bell_2q())
    bell3 = kernel_report_3q(lift_2q_to_3q(bell_2q()))
    wer2 = kernel_report_2q(werner_2q())
    ghz3 = kernel_report_3q(ghz_3q())
    bridge3 = kernel_report_3q(bridge_mixture_3q())

    bell_delta = matched_cut_delta(bell2, bell3, "A|BC")
    wer_delta = matched_cut_delta(wer2, kernel_report_3q(lift_2q_to_3q(werner_2q())), "A|BC")

    return {
        "matched_cut_is_preserved_under_bell_ancilla_lift": {
            **bell_delta,
            "preserved": max(bell_delta.values()) < 1e-12,
            "pass": max(bell_delta.values()) < 1e-12,
        },
        "ghz_has_true_multi_cut_coverage_advantage_over_2q_bell": {
            "ghz_active_cuts": active_signed_cut_count(ghz3),
            "2q_max_active_cuts": 1,
            "advantage": active_signed_cut_count(ghz3) > 1,
            "pass": active_signed_cut_count(ghz3) > 1,
        },
        "bell_lift_adds_localization_pattern_unavailable_in_2q": {
            "A|BC_neg": bell3["A|BC"]["negativity"],
            "B|AC_neg": bell3["B|AC"]["negativity"],
            "C|AB_neg": bell3["C|AB"]["negativity"],
            "localized_pattern": bell3["A|BC"]["negativity"] > 0.4 and bell3["B|AC"]["negativity"] > 0.4 and bell3["C|AB"]["negativity"] < 1e-12,
            "pass": bell3["A|BC"]["negativity"] > 0.4 and bell3["B|AC"]["negativity"] > 0.4 and bell3["C|AB"]["negativity"] < 1e-12,
        },
        "bridge_mixture_exposes_tripartite_companion_absent_in_2q_werner": {
            "werner_matched_cut_delta_max": max(wer_delta.values()),
            "bridge_tripartite_mi": bridge3["tripartite_mutual_information"],
            "nonzero_tripartite_companion": abs(bridge3["tripartite_mutual_information"]) > 1e-4,
            "pass": max(wer_delta.values()) < 1e-12 and abs(bridge3["tripartite_mutual_information"]) > 1e-4,
        },
        "3q_bridge_can_add_partition_coverage_even_when_signed_cut_is_not_positive": {
            "bridge_active_cuts": active_signed_cut_count(bridge3),
            "bridge_first_cut_negativity": bridge3["A|BC"]["negativity"],
            "bridge_first_cut_ic": bridge3["A|BC"]["coherent_information_to_b"],
            "extra_structure": active_signed_cut_count(bridge3) == 3 and bridge3["A|BC"]["coherent_information_to_b"] < 0.0 and bridge3["A|BC"]["negativity"] > 0.0,
            "pass": active_signed_cut_count(bridge3) == 3 and bridge3["A|BC"]["coherent_information_to_b"] < 0.0 and bridge3["A|BC"]["negativity"] > 0.0,
        },
    }


def run_negative_tests() -> Dict[str, dict]:
    prod2 = kernel_report_2q(product_2q())
    prod3 = kernel_report_3q(lift_2q_to_3q(product_2q()))
    class2 = kernel_report_2q(classical_2q())
    class3 = kernel_report_3q(lift_2q_to_3q(classical_2q()))
    bell2 = kernel_report_2q(bell_2q())
    bell3 = kernel_report_3q(lift_2q_to_3q(bell_2q()))
    wer2 = kernel_report_2q(werner_2q())
    wer3 = kernel_report_3q(lift_2q_to_3q(werner_2q()))

    prod_delta = matched_cut_delta(prod2, prod3, "A|BC")
    class_delta = matched_cut_delta(class2, class3, "A|BC")
    bell_delta = matched_cut_delta(bell2, bell3, "A|BC")
    wer_delta = matched_cut_delta(wer2, wer3, "A|BC")

    return {
        "product_ancilla_lift_adds_complexity_but_no_signal": {
            **prod_delta,
            "tripartite_mi": prod3["tripartite_mutual_information"],
            "no_signal": max(prod_delta.values()) < 1e-12 and abs(prod3["tripartite_mutual_information"]) < 1e-12 and active_signed_cut_count(prod3) == 0,
            "pass": max(prod_delta.values()) < 1e-12 and abs(prod3["tripartite_mutual_information"]) < 1e-12 and active_signed_cut_count(prod3) == 0,
        },
        "classical_ancilla_lift_adds_no_signed_or_tripartite_gain": {
            **class_delta,
            "tripartite_mi": class3["tripartite_mutual_information"],
            "matched_mi_preserved_no_extra_signed_signal": class3["A|BC"]["mutual_information"] > 0.1 and class3["A|BC"]["coherent_information_to_b"] <= 1e-12 and abs(class3["tripartite_mutual_information"]) < 1e-12,
            "pass": max(class_delta.values()) < 1e-12 and class3["A|BC"]["mutual_information"] > 0.1 and class3["A|BC"]["coherent_information_to_b"] <= 1e-12 and abs(class3["tripartite_mutual_information"]) < 1e-12,
        },
        "bell_lift_does_not_improve_the_matched_cut_itself": {
            **bell_delta,
            "matched_cut_only_no_advantage": max(bell_delta.values()) < 1e-12,
            "pass": max(bell_delta.values()) < 1e-12,
        },
        "werner_lift_does_not_create_tripartite_signal_by_adding_ancilla_only": {
            **wer_delta,
            "tripartite_mi": wer3["tripartite_mutual_information"],
            "no_tripartite_signal": max(wer_delta.values()) < 1e-12 and abs(wer3["tripartite_mutual_information"]) < 1e-12,
            "pass": max(wer_delta.values()) < 1e-12 and abs(wer3["tripartite_mutual_information"]) < 1e-12,
        },
    }


def run_boundary_tests() -> Dict[str, dict]:
    bell2 = kernel_report_2q(bell_2q())
    bell3 = kernel_report_3q(lift_2q_to_3q(bell_2q()))
    ghz3 = kernel_report_3q(ghz_3q())

    return {
        "matched_cut_choice_matters_for_lifted_bell": {
            "A|BC_ic": bell3["A|BC"]["coherent_information_to_b"],
            "C|AB_ic": bell3["C|AB"]["coherent_information_to_b"],
            "matched_vs_unmatched_different": abs(bell3["A|BC"]["coherent_information_to_b"] - bell3["C|AB"]["coherent_information_to_b"]) > 1e-6,
            "pass": abs(bell3["A|BC"]["coherent_information_to_b"] - bell3["C|AB"]["coherent_information_to_b"]) > 1e-6,
        },
        "2q_bell_and_ghz_share_local_cut_strength_but_not_coverage": {
            "2q_bell_ic": bell2["coherent_information_to_b"],
            "ghz_A|BC_ic": ghz3["A|BC"]["coherent_information_to_b"],
            "ghz_active_cuts": active_signed_cut_count(ghz3),
            "same_local_strength_extra_coverage": abs(bell2["coherent_information_to_b"] - ghz3["A|BC"]["coherent_information_to_b"]) < 1e-12 and active_signed_cut_count(ghz3) == 3,
            "pass": abs(bell2["coherent_information_to_b"] - ghz3["A|BC"]["coherent_information_to_b"]) < 1e-12 and active_signed_cut_count(ghz3) == 3,
        },
        "ancilla_lift_preserves_base_kernels_before_any_advantage_metric": {
            "bell_matched_delta_max": max(matched_cut_delta(bell2, bell3, 'A|BC').values()),
            "preserved": max(matched_cut_delta(bell2, bell3, 'A|BC').values()) < 1e-12,
            "pass": max(matched_cut_delta(bell2, bell3, 'A|BC').values()) < 1e-12,
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

    pos = count_section(positive)
    neg = count_section(negative)
    bnd = count_section(boundary)
    total_fail = pos["failed"] + neg["failed"] + bnd["failed"]

    results = {
        "name": "PURE LEGO: 2-Qubit vs 3-Qubit Bridge Kernel Advantage",
        "probe": "bridge_2q_vs_3q_kernel_advantage",
        "purpose": "Compare when a 3-qubit lift provides real extra discrimination beyond matched 2-qubit bridge kernels",
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "classical_baseline",
        "caveat": "Bounded comparison only. Extra 3-qubit discrimination is treated as coverage/localization/tripartite companion structure, not final canon.",
        "summary": {
            "positive_pass": pos["passed"],
            "positive_fail": pos["failed"],
            "negative_pass": neg["passed"],
            "negative_fail": neg["failed"],
            "boundary_pass": bnd["passed"],
            "boundary_fail": bnd["failed"],
            "total_fail": total_fail,
            "all_pass": total_fail == 0,
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "bridge_2q_vs_3q_kernel_advantage_results.json")
    with open(out_path, "w") as handle:
        json.dump(results, handle, indent=2)

    print(f"Results written to {out_path}")
    print(json.dumps(results["summary"], indent=2))


if __name__ == "__main__":
    main()
