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

import json
import os
import time

import numpy as np

np.random.seed(42)
EPS = 1e-12

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "pure-math numpy baseline"},
    "pyg": {"tried": False, "used": False, "reason": "pure-math numpy baseline"},
    "z3": {"tried": False, "used": False, "reason": "not needed for this cut-kernel sweep"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed for this cut-kernel sweep"},
    "sympy": {"tried": False, "used": False, "reason": "not needed for this cut-kernel sweep"},
    "clifford": {"tried": False, "used": False, "reason": "not needed for this cut-kernel sweep"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed for this cut-kernel sweep"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed for this cut-kernel sweep"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed for this cut-kernel sweep"},
    "xgi": {"tried": False, "used": False, "reason": "not needed for this cut-kernel sweep"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed for this cut-kernel sweep"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed for this cut-kernel sweep"},
}


# =====================================================================
# HELPERS
# =====================================================================

def _hermitian(rho):
    return 0.5 * (rho + rho.conj().T)


def _ensure_density(rho):
    rho = _hermitian(rho)
    evals, evecs = np.linalg.eigh(rho)
    evals = np.maximum(evals, 0.0)
    rho = (evecs * evals) @ evecs.conj().T
    tr = np.real(np.trace(rho))
    if tr <= EPS:
        raise ValueError("trace too small")
    return rho / tr


def vn_entropy(rho):
    rho = _ensure_density(rho)
    evals = np.real(np.linalg.eigvalsh(rho))
    evals = evals[evals > EPS]
    if len(evals) == 0:
        return 0.0
    return float(-np.sum(evals * np.log2(evals)))


def partial_trace_A(rho_ab):
    return np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def partial_trace_B(rho_ab):
    return np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=1, axis2=3)


def purity(rho):
    rho = _ensure_density(rho)
    return float(np.real(np.trace(rho @ rho)))


def is_pure(rho, tol=1e-9):
    return abs(purity(rho) - 1.0) <= tol


def mutual_information(rho_ab):
    rho_ab = _ensure_density(rho_ab)
    return float(vn_entropy(partial_trace_A(rho_ab)) + vn_entropy(partial_trace_B(rho_ab)) - vn_entropy(rho_ab))


def conditional_entropy_a_given_b(rho_ab):
    rho_ab = _ensure_density(rho_ab)
    return float(vn_entropy(rho_ab) - vn_entropy(partial_trace_B(rho_ab)))


def coherent_information_a_to_b(rho_ab):
    return float(vn_entropy(partial_trace_B(rho_ab)) - vn_entropy(rho_ab))


def entanglement_entropy_if_pure(rho_ab):
    if not is_pure(rho_ab):
        return None
    return float(vn_entropy(partial_trace_A(rho_ab)))


def negativity(rho_ab):
    rho = _ensure_density(rho_ab)
    pt = rho.reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)
    evals = np.linalg.eigvalsh(_hermitian(pt))
    return float(max(0.0, (np.sum(np.abs(evals)) - 1.0) / 2.0))


def log_negativity(rho_ab):
    rho = _ensure_density(rho_ab)
    pt = rho.reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)
    evals = np.linalg.eigvalsh(_hermitian(pt))
    return float(np.log2(max(np.sum(np.abs(evals)), 1.0)))


def weighted_cut_functional(rho_ab):
    ee = entanglement_entropy_if_pure(rho_ab)
    ee_term = 0.0 if ee is None else ee
    mi = mutual_information(rho_ab)
    ic = coherent_information_a_to_b(rho_ab)
    neg = negativity(rho_ab)
    return float(0.35 * mi + 0.35 * max(0.0, ic) + 0.20 * neg + 0.10 * ee_term)


def fake_constant_kernel(_rho_ab):
    return 1.0


def fake_trace_kernel(rho_ab):
    return float(np.real(np.trace(_ensure_density(rho_ab))))


def cnot_gate():
    return np.array(
        [
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1],
            [0, 0, 1, 0],
        ],
        dtype=complex,
    )


def z_dephase(rho_ab, p=0.4, on="A"):
    z = np.array([[1, 0], [0, -1]], dtype=complex)
    op = np.kron(z, np.eye(2)) if on == "A" else np.kron(np.eye(2), z)
    return _ensure_density((1.0 - p) * rho_ab + p * (op @ rho_ab @ op.conj().T))


def werner_state(p):
    psi_minus = np.array([0.0, 1.0 / np.sqrt(2), -1.0 / np.sqrt(2), 0.0], dtype=complex)
    bell = np.outer(psi_minus, psi_minus.conj())
    return _ensure_density(p * bell + (1.0 - p) * np.eye(4, dtype=complex) / 4.0)


def product_state(name):
    if name == "00":
        psi = np.array([1.0, 0.0, 0.0, 0.0], dtype=complex)
    elif name == "+-":
        plus = np.array([1.0, 1.0], dtype=complex) / np.sqrt(2)
        minus = np.array([1.0, -1.0], dtype=complex) / np.sqrt(2)
        psi = np.kron(plus, minus)
    else:
        raise ValueError(name)
    return np.outer(psi, psi.conj())


def classical_correlated_state(p=0.7):
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


def bell_state(label="phi_plus"):
    if label == "phi_plus":
        psi = np.array([1.0, 0.0, 0.0, 1.0], dtype=complex) / np.sqrt(2)
    elif label == "phi_minus":
        psi = np.array([1.0, 0.0, 0.0, -1.0], dtype=complex) / np.sqrt(2)
    elif label == "psi_plus":
        psi = np.array([0.0, 1.0, 1.0, 0.0], dtype=complex) / np.sqrt(2)
    else:
        psi = np.array([0.0, 1.0, -1.0, 0.0], dtype=complex) / np.sqrt(2)
    return np.outer(psi, psi.conj())


def history_derived_states():
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


def kernel_row(label, cls, rho, family=None):
    rho_a = partial_trace_A(rho)
    rho_b = partial_trace_B(rho)
    row = {
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
    return row


def build_battery():
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


def score_discrimination(rows, kernel):
    classes = {}
    values = [r[kernel] for r in rows if r[kernel] is not None]
    for r in rows:
        if r[kernel] is not None:
            classes.setdefault(r["class"], []).append(r[kernel])
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


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
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
        [(r["label"], r["weighted_cut_functional"], r["negativity"], r["coherent_information_a_to_b"]) for r in werner_rows],
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
    boundary["pass"] = all(v["pass"] for v in boundary.values())

    positive["discrimination_scores"] = sweep
    positive["werner_ordering"] = werner_rows_sorted

    return positive, negative, boundary, exact_checks


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    t0 = time.time()
    positive, negative, boundary, exact_checks = run_positive_tests()

    all_tests = {}
    for section in (exact_checks, negative, boundary):
        if isinstance(section, dict):
            for name, test in section.items():
                if isinstance(test, dict) and "pass" in test:
                    all_tests[name] = bool(test["pass"])
                elif isinstance(test, bool):
                    all_tests[name] = bool(test)

    results = {
        "name": "axis0_cut_kernel_sweep",
        "schema": "axis0_cut_kernel_sweep/v1",
        "description": (
            "Pure-math sweep of bipartite cut kernels derived from rho_AB: "
            "mutual information, conditional entropy, coherent information, "
            "entanglement entropy where applicable, and a weighted cut functional."
        ),
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "canonical",
        "summary": {
            "total_tests": len(all_tests),
            "passed": sum(1 for ok in all_tests.values() if ok),
            "failed": sum(1 for ok in all_tests.values() if not ok),
            "all_pass": all(all_tests.values()) if all_tests else False,
            "elapsed_s": time.time() - t0,
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "axis0_cut_kernel_sweep_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"Results written to {out_path}")
    print(f"Tests: {results['summary']['passed']}/{results['summary']['total_tests']} passed")
    print("ALL PASS" if results["summary"]["all_pass"] else "FAILED")
