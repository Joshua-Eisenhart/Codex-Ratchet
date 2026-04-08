#!/usr/bin/env python3
"""
PURE LEGO: Bridge-Built Cut Kernels on 3-Qubit States
=====================================================
Bounded pure-math extension of bridge-to-cut logic into a 3-qubit setting.

This sim builds simple 3-qubit states and compares cut kernels on:
  - 1|23 partitions
  - 2|1 partitions

Reported families:
  - mutual information
  - conditional entropy
  - coherent-information-like signed quantities
  - tripartite mutual information
  - cut negativities as multipartite companions

Claims are bounded:
  - this is a cut-kernel comparison only
  - no final doctrine or bridge canon is asserted
"""

import json
import os
from typing import Dict, List

import numpy as np

EPS = 1e-12

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "pure-math numpy baseline"},
    "pyg": {"tried": False, "used": False, "reason": "not needed for this bounded multipartite cut sim"},
    "z3": {"tried": False, "used": False, "reason": "not needed for this bounded multipartite cut sim"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed for this bounded multipartite cut sim"},
    "sympy": {"tried": False, "used": False, "reason": "not needed for this bounded multipartite cut sim"},
    "clifford": {"tried": False, "used": False, "reason": "not needed for this bounded multipartite cut sim"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed for this bounded multipartite cut sim"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed for this bounded multipartite cut sim"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed for this bounded multipartite cut sim"},
    "xgi": {"tried": False, "used": False, "reason": "not needed for this bounded multipartite cut sim"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed for this bounded multipartite cut sim"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed for this bounded multipartite cut sim"},
}


def normalize_rho(rho: np.ndarray) -> np.ndarray:
    rho = 0.5 * (rho + rho.conj().T)
    tr = np.trace(rho)
    if abs(tr) < EPS:
        raise ValueError("trace too small")
    return rho / tr


def rho_from_psi(psi: np.ndarray) -> np.ndarray:
    psi = np.asarray(psi, dtype=np.complex128).reshape(8, 1)
    return normalize_rho(psi @ psi.conj().T)


def basis(bits: str) -> np.ndarray:
    vec = np.zeros(8, dtype=np.complex128)
    vec[int(bits, 2)] = 1.0
    return vec


def reduced_density(rho: np.ndarray, keep: List[int]) -> np.ndarray:
    keep = list(keep)
    bra = ["a", "b", "c"]
    ket = ["d", "e", "f"]
    for idx in range(3):
        if idx not in keep:
            ket[idx] = bra[idx]
    subs_in = "".join(bra + ket)
    subs_out = "".join([bra[idx] for idx in keep] + [ket[idx] for idx in keep])
    red = np.einsum(f"{subs_in}->{subs_out}", rho.reshape(2, 2, 2, 2, 2, 2))
    dim = 2 ** len(keep)
    return normalize_rho(red.reshape(dim, dim))


def von_neumann_entropy(rho: np.ndarray) -> float:
    evals = np.linalg.eigvalsh(normalize_rho(rho)).real
    evals = np.clip(evals, 0.0, None)
    nz = evals[evals > EPS]
    if len(nz) == 0:
        return 0.0
    return float(-np.sum(nz * np.log2(nz)))


def mutual_information(rho: np.ndarray, keep_a: List[int], keep_b: List[int]) -> float:
    rho_a = reduced_density(rho, keep_a)
    rho_b = reduced_density(rho, keep_b)
    return float(von_neumann_entropy(rho_a) + von_neumann_entropy(rho_b) - von_neumann_entropy(rho))


def conditional_entropy(rho: np.ndarray, keep_a: List[int], keep_b: List[int]) -> float:
    del keep_a
    rho_b = reduced_density(rho, keep_b)
    return float(von_neumann_entropy(rho) - von_neumann_entropy(rho_b))


def coherent_information_like(rho: np.ndarray, keep_target: List[int]) -> float:
    rho_target = reduced_density(rho, keep_target)
    return float(von_neumann_entropy(rho_target) - von_neumann_entropy(rho))


def partial_transpose(rho: np.ndarray, subsystem: int) -> np.ndarray:
    tensor = rho.reshape(2, 2, 2, 2, 2, 2)
    if subsystem == 0:
        pt = tensor.transpose(3, 1, 2, 0, 4, 5)
    elif subsystem == 1:
        pt = tensor.transpose(0, 4, 2, 3, 1, 5)
    elif subsystem == 2:
        pt = tensor.transpose(0, 1, 5, 3, 4, 2)
    else:
        raise ValueError(subsystem)
    return normalize_rho(pt.reshape(8, 8))


def negativity_cut(rho: np.ndarray, subsystem: int) -> float:
    evals = np.linalg.eigvalsh(partial_transpose(rho, subsystem))
    return float(max(0.0, (np.sum(np.abs(evals)) - 1.0) / 2.0))


def tripartite_mutual_information(rho: np.ndarray) -> float:
    s_a = von_neumann_entropy(reduced_density(rho, [0]))
    s_b = von_neumann_entropy(reduced_density(rho, [1]))
    s_c = von_neumann_entropy(reduced_density(rho, [2]))
    s_ab = von_neumann_entropy(reduced_density(rho, [0, 1]))
    s_ac = von_neumann_entropy(reduced_density(rho, [0, 2]))
    s_bc = von_neumann_entropy(reduced_density(rho, [1, 2]))
    s_abc = von_neumann_entropy(rho)
    return float(s_a + s_b + s_c - s_ab - s_ac - s_bc + s_abc)


def ghz_state() -> np.ndarray:
    psi = (basis("000") + basis("111")) / np.sqrt(2.0)
    return rho_from_psi(psi)


def w_state() -> np.ndarray:
    psi = (basis("001") + basis("010") + basis("100")) / np.sqrt(3.0)
    return rho_from_psi(psi)


def product_state() -> np.ndarray:
    return rho_from_psi(basis("000"))


def bell_ab_tensor_zero() -> np.ndarray:
    psi = (basis("000") + basis("110")) / np.sqrt(2.0)
    return rho_from_psi(psi)


def bridge_mixture() -> np.ndarray:
    return normalize_rho(0.55 * ghz_state() + 0.45 * np.eye(8, dtype=np.complex128) / 8.0)


def classically_correlated_counterfeit() -> np.ndarray:
    diag = np.zeros((8, 8), dtype=np.complex128)
    diag[0, 0] = 0.5
    diag[3, 3] = 0.25
    diag[5, 5] = 0.25
    return normalize_rho(diag)


def local_proxy_counterfeit() -> np.ndarray:
    return normalize_rho(
        0.5 * np.kron(np.array([[1, 0], [0, 0]], dtype=np.complex128), np.eye(4, dtype=np.complex128) / 4.0)
        + 0.5 * np.kron(np.array([[0, 0], [0, 1]], dtype=np.complex128), np.eye(4, dtype=np.complex128) / 4.0)
    )


PARTITIONS = {
    "A|BC": {"a": [0], "b": [1, 2], "pt_sys": 0},
    "B|AC": {"a": [1], "b": [0, 2], "pt_sys": 1},
    "C|AB": {"a": [2], "b": [0, 1], "pt_sys": 2},
    "AB|C": {"a": [0, 1], "b": [2], "pt_sys": 2},
    "AC|B": {"a": [0, 2], "b": [1], "pt_sys": 1},
    "BC|A": {"a": [1, 2], "b": [0], "pt_sys": 0},
}


def kernel_report(rho: np.ndarray) -> Dict[str, dict]:
    report = {}
    for label, spec in PARTITIONS.items():
        report[label] = {
            "mutual_information": mutual_information(rho, spec["a"], spec["b"]),
            "conditional_entropy_a_given_b": conditional_entropy(rho, spec["a"], spec["b"]),
            "coherent_information_to_b": coherent_information_like(rho, spec["b"]),
            "negativity": negativity_cut(rho, spec["pt_sys"]),
        }
    report["tripartite_mutual_information"] = tripartite_mutual_information(rho)
    return report


def run_positive_tests() -> Dict[str, dict]:
    ghz = kernel_report(ghz_state())
    prod = kernel_report(product_state())
    bell0 = kernel_report(bell_ab_tensor_zero())
    bridge = kernel_report(bridge_mixture())

    return {
        "ghz_has_positive_signed_cut_signal_on_all_1v2_partitions": {
            "A|BC": ghz["A|BC"]["coherent_information_to_b"],
            "B|AC": ghz["B|AC"]["coherent_information_to_b"],
            "C|AB": ghz["C|AB"]["coherent_information_to_b"],
            "all_positive": all(ghz[key]["coherent_information_to_b"] > 0.99 for key in ["A|BC", "B|AC", "C|AB"]),
            "pass": all(ghz[key]["coherent_information_to_b"] > 0.99 for key in ["A|BC", "B|AC", "C|AB"]),
        },
        "product_state_kills_all_cut_kernels_except_trivial_zero": {
            "A|BC_mi": prod["A|BC"]["mutual_information"],
            "A|BC_ic": prod["A|BC"]["coherent_information_to_b"],
            "tripartite_mi": prod["tripartite_mutual_information"],
            "all_zero": abs(prod["A|BC"]["mutual_information"]) < 1e-12
                        and abs(prod["A|BC"]["coherent_information_to_b"]) < 1e-12
                        and abs(prod["tripartite_mutual_information"]) < 1e-12,
            "pass": abs(prod["A|BC"]["mutual_information"]) < 1e-12
                    and abs(prod["A|BC"]["coherent_information_to_b"]) < 1e-12
                    and abs(prod["tripartite_mutual_information"]) < 1e-12,
        },
        "bell_pair_tensor_product_is_asymmetric_across_partitions": {
            "AB|C_ic": bell0["AB|C"]["coherent_information_to_b"],
            "A|BC_ic": bell0["A|BC"]["coherent_information_to_b"],
            "C|AB_ic": bell0["C|AB"]["coherent_information_to_b"],
            "asymmetric": bell0["AB|C"]["mutual_information"] < 1e-12 and bell0["A|BC"]["mutual_information"] > 1.5 and bell0["C|AB"]["mutual_information"] < 1e-12,
            "pass": bell0["AB|C"]["mutual_information"] < 1e-12 and bell0["A|BC"]["mutual_information"] > 1.5 and bell0["C|AB"]["mutual_information"] < 1e-12,
        },
        "bridge_mixture_retains_signal_but_weaker_than_ghz": {
            "ghz_A|BC_ic": ghz["A|BC"]["coherent_information_to_b"],
            "bridge_A|BC_ic": bridge["A|BC"]["coherent_information_to_b"],
            "bridge_A|BC_mi": bridge["A|BC"]["mutual_information"],
            "bridge_A|BC_neg": bridge["A|BC"]["negativity"],
            "signal_present_but_weaker": (
                bridge["A|BC"]["mutual_information"] > 0.1
                and bridge["A|BC"]["negativity"] > 0.0
                and bridge["A|BC"]["negativity"] < ghz["A|BC"]["negativity"]
            ),
            "pass": (
                bridge["A|BC"]["mutual_information"] > 0.1
                and bridge["A|BC"]["negativity"] > 0.0
                and bridge["A|BC"]["negativity"] < ghz["A|BC"]["negativity"]
            ),
        },
        "multipartite_companion_negativity_tracks_nonproduct_cases": {
            "ghz_neg": ghz["A|BC"]["negativity"],
            "product_neg": prod["A|BC"]["negativity"],
            "bridge_neg": bridge["A|BC"]["negativity"],
            "ordered": ghz["A|BC"]["negativity"] > bridge["A|BC"]["negativity"] > prod["A|BC"]["negativity"],
            "pass": ghz["A|BC"]["negativity"] > bridge["A|BC"]["negativity"] > prod["A|BC"]["negativity"],
        },
    }


def run_negative_tests() -> Dict[str, dict]:
    classical = kernel_report(classically_correlated_counterfeit())
    proxy = kernel_report(local_proxy_counterfeit())
    wrep = kernel_report(w_state())
    bell0 = kernel_report(bell_ab_tensor_zero())

    return {
        "classically_correlated_counterfeit_has_mi_without_signed_cut_gain": {
            "A|BC_mi": classical["A|BC"]["mutual_information"],
            "A|BC_ic": classical["A|BC"]["coherent_information_to_b"],
            "mi_positive_ic_nonpositive": classical["A|BC"]["mutual_information"] > 0.1 and classical["A|BC"]["coherent_information_to_b"] <= 1e-12,
            "pass": classical["A|BC"]["mutual_information"] > 0.1 and classical["A|BC"]["coherent_information_to_b"] <= 1e-12,
        },
        "local_proxy_counterfeit_fails_to_generate_tripartite_signal": {
            "tripartite_mi": proxy["tripartite_mutual_information"],
            "A|BC_ic": proxy["A|BC"]["coherent_information_to_b"],
            "no_signed_gain": abs(proxy["tripartite_mutual_information"]) < 1e-12 and proxy["A|BC"]["coherent_information_to_b"] <= 1e-12,
            "pass": abs(proxy["tripartite_mutual_information"]) < 1e-12 and proxy["A|BC"]["coherent_information_to_b"] <= 1e-12,
        },
        "w_state_does_not_fake_ghz_symmetry_strength": {
            "w_A|BC_ic": wrep["A|BC"]["coherent_information_to_b"],
            "w_A|BC_neg": wrep["A|BC"]["negativity"],
            "weaker_than_ghz_like_unity": wrep["A|BC"]["coherent_information_to_b"] < 1.0 and wrep["A|BC"]["negativity"] < 0.5,
            "pass": wrep["A|BC"]["coherent_information_to_b"] < 1.0 and wrep["A|BC"]["negativity"] < 0.5,
        },
        "two_vs_one_partition_quantities_are_not_interchangeable_labels": {
            "A|BC_mi": bell0["A|BC"]["mutual_information"],
            "C|AB_mi": bell0["C|AB"]["mutual_information"],
            "A|BC_cond": bell0["A|BC"]["conditional_entropy_a_given_b"],
            "C|AB_cond": bell0["C|AB"]["conditional_entropy_a_given_b"],
            "conditional_differs_across_non_equivalent_cuts": abs(bell0["A|BC"]["conditional_entropy_a_given_b"] - bell0["C|AB"]["conditional_entropy_a_given_b"]) > 1e-6,
            "pass": abs(bell0["A|BC"]["conditional_entropy_a_given_b"] - bell0["C|AB"]["conditional_entropy_a_given_b"]) > 1e-6,
        },
    }


def run_boundary_tests() -> Dict[str, dict]:
    ghz = kernel_report(ghz_state())
    wrep = kernel_report(w_state())
    bridge = kernel_report(bridge_mixture())

    return {
        "pure_state_cut_identity_holds_for_ghz": {
            "A_entropy": von_neumann_entropy(reduced_density(ghz_state(), [0])),
            "A|BC_ic": ghz["A|BC"]["coherent_information_to_b"],
            "equal": abs(von_neumann_entropy(reduced_density(ghz_state(), [0])) - ghz["A|BC"]["coherent_information_to_b"]) < 1e-12,
            "pass": abs(von_neumann_entropy(reduced_density(ghz_state(), [0])) - ghz["A|BC"]["coherent_information_to_b"]) < 1e-12,
        },
        "pure_state_cut_identity_holds_for_w": {
            "A_entropy": von_neumann_entropy(reduced_density(w_state(), [0])),
            "A|BC_ic": wrep["A|BC"]["coherent_information_to_b"],
            "equal": abs(von_neumann_entropy(reduced_density(w_state(), [0])) - wrep["A|BC"]["coherent_information_to_b"]) < 1e-12,
            "pass": abs(von_neumann_entropy(reduced_density(w_state(), [0])) - wrep["A|BC"]["coherent_information_to_b"]) < 1e-12,
        },
        "mixed_bridge_breaks_pure_cut_identity_but_keeps_measure_defined": {
            "A_entropy": von_neumann_entropy(reduced_density(bridge_mixture(), [0])),
            "A|BC_ic": bridge["A|BC"]["coherent_information_to_b"],
            "different_but_defined": abs(von_neumann_entropy(reduced_density(bridge_mixture(), [0])) - bridge["A|BC"]["coherent_information_to_b"]) > 1e-4,
            "pass": abs(von_neumann_entropy(reduced_density(bridge_mixture(), [0])) - bridge["A|BC"]["coherent_information_to_b"]) > 1e-4,
        },
    }


def count_section(section: Dict[str, dict]) -> Dict[str, int]:
    total = sum(1 for v in section.values() if isinstance(v, dict) and "pass" in v)
    passed = sum(1 for v in section.values() if isinstance(v, dict) and v.get("pass") is True)
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
        "name": "PURE LEGO: Bridge-Built Cut Kernels on 3-Qubit States",
        "probe": "bridge_cut_kernels_3qubit",
        "purpose": "Extend cut-kernel comparisons from bipartite bridge-built states to bounded 3-qubit partitions",
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "classical_baseline",
        "caveat": "Bounded multipartite cut-kernel comparison only. No final bridge canon or preferred kernel is promoted here.",
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
    out_path = os.path.join(out_dir, "bridge_cut_kernels_3qubit_results.json")
    with open(out_path, "w") as handle:
        json.dump(results, handle, indent=2)

    print(f"Results written to {out_path}")
    print(json.dumps(results["summary"], indent=2))


if __name__ == "__main__":
    main()
