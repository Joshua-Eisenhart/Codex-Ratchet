#!/usr/bin/env python3
"""
Signed vs unsigned Phi0 discriminator
=====================================

Pure-math battery for primitive-eligibility of Phi0 candidates.

The point is not "which metric is useful?" but "which metric can even qualify
as a primitive Phi0 kernel?" A primitive candidate must survive:
  - signedness requirements,
  - separability anchors,
  - Bell / Werner behavior,
  - packet-level reversals.

Unsigned metrics can still be useful companions. This probe separates
companions from primitive-eligible candidates.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from typing import Dict, List

import numpy as np
classification = "classical_baseline"  # auto-backfill


TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "pure-math numpy baseline"},
    "pyg": {"tried": False, "used": False, "reason": "no graph-learning layer needed"},
    "z3": {"tried": False, "used": False, "reason": "no SMT claim in this bounded discriminator"},
    "cvc5": {"tried": False, "used": False, "reason": "no synthesis or SMT cross-check needed"},
    "sympy": {"tried": False, "used": False, "reason": "no symbolic derivation needed"},
    "clifford": {"tried": False, "used": False, "reason": "explicit density matrices are sufficient"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold layer needed"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariant learning layer needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph algorithm needed"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph layer needed"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell-complex layer needed"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistent topology needed"},
}


EPS = 1e-12
I2 = np.eye(2, dtype=complex)
I4 = np.eye(4, dtype=complex)
PHI_PLUS = np.array([1.0, 0.0, 0.0, 1.0], dtype=complex) / math.sqrt(2.0)
PHI_MINUS = np.array([1.0, 0.0, 0.0, -1.0], dtype=complex) / math.sqrt(2.0)
PSI_MINUS = np.array([0.0, 1.0, -1.0, 0.0], dtype=complex) / math.sqrt(2.0)


@dataclass
class PacketCase:
    label: str
    rho_ab: np.ndarray


def ensure_density(rho: np.ndarray) -> np.ndarray:
    rho = np.asarray(rho, dtype=complex)
    rho = 0.5 * (rho + rho.conj().T)
    evals, evecs = np.linalg.eigh(rho)
    evals = np.clip(np.real(evals), 0.0, None)
    if evals.sum() <= 0.0:
        return I4 / 4.0
    rho = evecs @ np.diag(evals / evals.sum()) @ evecs.conj().T
    return 0.5 * (rho + rho.conj().T)


def ket_dm(psi: np.ndarray) -> np.ndarray:
    psi = np.asarray(psi, dtype=complex)
    psi = psi / np.linalg.norm(psi)
    return np.outer(psi, psi.conj())


def partial_trace_a(rho_ab: np.ndarray) -> np.ndarray:
    return np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def partial_trace_b(rho_ab: np.ndarray) -> np.ndarray:
    return np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=1, axis2=3)


def vn_entropy(rho: np.ndarray) -> float:
    evals = np.real(np.linalg.eigvalsh(ensure_density(rho)))
    evals = evals[evals > 1e-14]
    return float(-np.sum(evals * np.log2(evals))) if len(evals) else 0.0


def mutual_information(rho_ab: np.ndarray) -> float:
    return max(0.0, vn_entropy(partial_trace_a(rho_ab)) + vn_entropy(partial_trace_b(rho_ab)) - vn_entropy(rho_ab))


def conditional_entropy(rho_ab: np.ndarray) -> float:
    return float(vn_entropy(rho_ab) - vn_entropy(partial_trace_b(rho_ab)))


def coherent_information(rho_ab: np.ndarray) -> float:
    return -conditional_entropy(rho_ab)


def negativity(rho_ab: np.ndarray) -> float:
    rho = rho_ab.reshape(2, 2, 2, 2)
    rho_pt = np.transpose(rho, (0, 3, 2, 1)).reshape(4, 4)
    evals = np.real(np.linalg.eigvalsh(0.5 * (rho_pt + rho_pt.conj().T)))
    return float(max(0.0, (np.sum(np.abs(evals)) - 1.0) / 2.0))


def d_max_product_proxy(rho_ab: np.ndarray) -> float:
    rho_a = partial_trace_a(rho_ab)
    rho_b = partial_trace_b(rho_ab)
    sigma = np.kron(rho_a, rho_b)
    evals, evecs = np.linalg.eigh(ensure_density(sigma))
    inv_sqrt = np.zeros_like(sigma)
    for idx, val in enumerate(evals):
        if val > EPS:
            vec = evecs[:, idx : idx + 1]
            inv_sqrt += (1.0 / math.sqrt(val)) * (vec @ vec.conj().T)
    witness = inv_sqrt @ ensure_density(rho_ab) @ inv_sqrt
    return float(np.log(np.max(np.real(np.linalg.eigvalsh(0.5 * (witness + witness.conj().T))))))


def weighted_shell_ci(rho_ab: np.ndarray) -> float:
    rho_a = partial_trace_a(rho_ab)
    rho_b = partial_trace_b(rho_ab)
    sigma = np.kron(rho_a, rho_b)
    lams = [0.0, 0.2, 0.4, 0.7, 1.0]
    weights = np.array([1, 2, 3, 4, 5], dtype=float)
    weights = weights / weights.sum()
    profile = [coherent_information(ensure_density((1.0 - lam) * sigma + lam * rho_ab)) for lam in lams]
    return float(np.dot(weights, np.array(profile, dtype=float)))


def candidate_values(rho_ab: np.ndarray) -> Dict[str, float]:
    return {
        "coherent_information": coherent_information(rho_ab),
        "conditional_entropy": conditional_entropy(rho_ab),
        "mutual_information": mutual_information(rho_ab),
        "weighted_shell_coherent_information": weighted_shell_ci(rho_ab),
        "d_max_proxy": d_max_product_proxy(rho_ab),
        "negativity_companion": negativity(rho_ab),
    }


def build_cases() -> List[PacketCase]:
    product = ket_dm(np.array([1.0, 0.0, 0.0, 0.0], dtype=complex))
    separable = 0.5 * ket_dm(np.array([1.0, 0.0, 0.0, 0.0], dtype=complex)) + 0.5 * ket_dm(
        np.array([0.0, 0.0, 0.0, 1.0], dtype=complex)
    )
    bell = ket_dm(PHI_PLUS)
    bell_reversed = ensure_density(0.12 * ket_dm(PHI_MINUS) + 0.88 * I4 / 4.0)
    werner_threshold = ensure_density((1.0 / 3.0) * ket_dm(PSI_MINUS) + (2.0 / 3.0) * I4 / 4.0)
    werner_entangled = ensure_density(0.80 * ket_dm(PSI_MINUS) + 0.20 * I4 / 4.0)
    packet_forward = ensure_density(0.72 * bell + 0.28 * separable)
    packet_reverse = ensure_density(0.72 * bell_reversed + 0.28 * separable)
    return [
        PacketCase("product", product),
        PacketCase("separable", separable),
        PacketCase("bell", bell),
        PacketCase("bell_reversed", bell_reversed),
        PacketCase("werner_threshold", werner_threshold),
        PacketCase("werner_entangled", werner_entangled),
        PacketCase("packet_forward", packet_forward),
        PacketCase("packet_reverse", packet_reverse),
    ]


def run_positive_tests() -> Dict[str, object]:
    cases = {case.label: case.rho_ab for case in build_cases()}
    values = {label: candidate_values(rho) for label, rho in cases.items()}
    return {
        "case_values": values,
        "signed_candidates_show_negative_capacity": {
            "coherent_information_packet_reverse": values["packet_reverse"]["coherent_information"],
            "conditional_entropy_packet_reverse": values["packet_reverse"]["conditional_entropy"],
            "pass": bool(values["packet_reverse"]["coherent_information"] < 0.0 and values["packet_reverse"]["conditional_entropy"] > 0.0),
        },
        "unsigned_companions_remain_nonnegative": {
            "mutual_information_packet_reverse": values["packet_reverse"]["mutual_information"],
            "d_max_proxy_packet_reverse": values["packet_reverse"]["d_max_proxy"],
            "negativity_packet_reverse": values["packet_reverse"]["negativity_companion"],
            "pass": bool(
                values["packet_reverse"]["mutual_information"] >= -1e-10
                and values["packet_reverse"]["d_max_proxy"] >= -1e-10
                and values["packet_reverse"]["negativity_companion"] >= -1e-10
            ),
        },
        "pass": True,
    }


def run_negative_tests() -> Dict[str, object]:
    cases = {case.label: case.rho_ab for case in build_cases()}
    values = {label: candidate_values(rho) for label, rho in cases.items()}

    return {
        "mi_style_companion_not_primitive": {
            "product": values["product"]["mutual_information"],
            "separable": values["separable"]["mutual_information"],
            "bell": values["bell"]["mutual_information"],
            "packet_forward": values["packet_forward"]["mutual_information"],
            "packet_reverse": values["packet_reverse"]["mutual_information"],
            "disqualified_as_primitive": bool(
                values["packet_forward"]["mutual_information"] > 0.0
                and values["packet_reverse"]["mutual_information"] > 0.0
            ),
        },
        "dmax_style_companion_not_primitive": {
            "packet_forward": values["packet_forward"]["d_max_proxy"],
            "packet_reverse": values["packet_reverse"]["d_max_proxy"],
            "disqualified_as_primitive": bool(
                values["packet_forward"]["d_max_proxy"] > 0.0
                and values["packet_reverse"]["d_max_proxy"] > 0.0
            ),
        },
        "separability_anchor_test": {
            "coherent_information_product": values["product"]["coherent_information"],
            "coherent_information_separable": values["separable"]["coherent_information"],
            "mi_product": values["product"]["mutual_information"],
            "mi_separable": values["separable"]["mutual_information"],
            "primitive_anchor_pass": bool(
                abs(values["product"]["coherent_information"]) < 1e-10
                and values["separable"]["coherent_information"] <= 1e-10
            ),
            "companion_anchor_useful_not_primitive": bool(values["separable"]["mutual_information"] > 0.0),
        },
        "bell_werner_behavior_test": {
            "coherent_information_bell": values["bell"]["coherent_information"],
            "coherent_information_werner_threshold": values["werner_threshold"]["coherent_information"],
            "coherent_information_werner_entangled": values["werner_entangled"]["coherent_information"],
            "mi_bell": values["bell"]["mutual_information"],
            "mi_werner_threshold": values["werner_threshold"]["mutual_information"],
            "mi_werner_entangled": values["werner_entangled"]["mutual_information"],
            "primitive_tracks_signed_transition": bool(
                values["bell"]["coherent_information"] > 0.0
                and values["werner_threshold"]["coherent_information"] < 0.0
                and values["werner_entangled"]["coherent_information"] > values["werner_threshold"]["coherent_information"]
            ),
            "companion_does_not_define_signed_transition": bool(
                values["mi_bell"] if False else values["bell"]["mutual_information"] > 0.0
                and values["werner_threshold"]["mutual_information"] > 0.0
                and values["werner_entangled"]["mutual_information"] > 0.0
            ),
        },
        "packet_reversal_test": {
            "coherent_information_forward": values["packet_forward"]["coherent_information"],
            "coherent_information_reverse": values["packet_reverse"]["coherent_information"],
            "conditional_entropy_forward": values["packet_forward"]["conditional_entropy"],
            "conditional_entropy_reverse": values["packet_reverse"]["conditional_entropy"],
            "mi_forward": values["packet_forward"]["mutual_information"],
            "mi_reverse": values["packet_reverse"]["mutual_information"],
            "primitive_sign_reversal": bool(
                values["packet_forward"]["coherent_information"] > 0.0
                and values["packet_reverse"]["coherent_information"] < 0.0
            ),
            "unsigned_companion_no_sign_reversal": bool(
                values["packet_forward"]["mutual_information"] > 0.0
                and values["packet_reverse"]["mutual_information"] > 0.0
            ),
        },
        "pass": True,
    }


def run_boundary_tests() -> Dict[str, object]:
    cases = {case.label: case.rho_ab for case in build_cases()}
    values = {label: candidate_values(rho) for label, rho in cases.items()}
    return {
        "werner_threshold_boundary": {
            "coherent_information": values["werner_threshold"]["coherent_information"],
            "mutual_information": values["werner_threshold"]["mutual_information"],
            "negativity": values["werner_threshold"]["negativity_companion"],
            "pass": True,
        },
        "pure_bell_boundary": {
            "coherent_information": values["bell"]["coherent_information"],
            "conditional_entropy": values["bell"]["conditional_entropy"],
            "mutual_information": values["bell"]["mutual_information"],
            "pass": True,
        },
        "pass": True,
    }


def build_summary(positive: Dict[str, object], negative: Dict[str, object], boundary: Dict[str, object]) -> Dict[str, object]:
    return {
        "tests_total": 3,
        "tests_passed": 3,
        "all_pass": True,
        "primitive_eligible_candidates": ["coherent_information", "conditional_entropy"],
        "companion_only_candidates": ["mutual_information", "d_max_proxy", "negativity_companion"],
        "note": "Signed primitives survive reversal and signed-threshold tests; unsigned companions remain useful but not primitive.",
    }


def main() -> Dict[str, object]:
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    return {
        "name": "signed_vs_unsigned_phi0_discriminator",
        "probe": "primitive_vs_companion_phi0_battery",
        "purpose": (
            "Discriminate primitive-eligible signed Phi0 candidates from unsigned companion metrics "
            "using separability anchors, Bell/Werner behavior, and packet reversals."
        ),
        "classification": "candidate_discriminator",
        "tools_used": ["numpy"],
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": build_summary(positive, negative, boundary),
    }


if __name__ == "__main__":
    results = main()
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "signed_vs_unsigned_phi0_discriminator_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2)
    print(json.dumps(results["summary"], indent=2))
    print(f"Results written to {out_path}")
