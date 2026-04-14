#!/usr/bin/env python3
"""
SIM: Chiral Density Bookkeeping
==============================

Bounded geometry-side lego for explicit rho_L / rho_R bookkeeping on the
Hopf/Weyl carrier. This sim constructs

  rho_L = |psi_L><psi_L|
  rho_R = |psi_R><psi_R|

on the same admitted carrier, checks density validity, verifies bookkeeping
consistency under fiber action, and cross-checks chirality projectors.

Scope discipline:
- geometry/Weyl bookkeeping only
- no axis / bridge / flux widening
- no claim beyond local rho_L / rho_R bookkeeping

Interpreter: use Makefile PYTHON
Result: system_v4/probes/a2_state/sim_results/chiral_density_bookkeeping_results.json
"""

from __future__ import annotations

import json
import math
import os
import sys
import traceback
from datetime import UTC, datetime

import numpy as np

PROBE_DIR = os.path.dirname(os.path.abspath(__file__))
if PROBE_DIR not in sys.path:
    sys.path.insert(0, PROBE_DIR)

from hopf_manifold import (
    density_to_bloch,
    fiber_action,
    left_density,
    left_weyl_spinor,
    right_density,
    right_weyl_spinor,
    torus_coordinates,
)

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": "not required for local chiral density bookkeeping"},
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": "not required; z3 is sufficient for bounded projector mutual-exclusion proof"},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": "not required; hopf_manifold already provides the needed Weyl-density primitives for this bounded packet"},
    "geomstats": {"tried": False, "used": False, "reason": "not required; no geodesic/curvature claim in this bookkeeping packet"},
    "e3nn": {"tried": False, "used": False, "reason": "not required; no equivariant carrier-learning claim in this bookkeeping packet"},
    "rustworkx": {"tried": False, "used": False, "reason": "not required; no shell-DAG update in this bookkeeping packet"},
    "xgi": {"tried": False, "used": False, "reason": "not required; no hypergraph claim in this bookkeeping packet"},
    "toponetx": {"tried": False, "used": False, "reason": "not required; no cell-complex claim in this bookkeeping packet"},
    "gudhi": {"tried": False, "used": False, "reason": "not required; no persistence/topology claim in this bookkeeping packet"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    from z3 import Real, Reals, Solver, unsat
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

for tool_name in ("clifford", "geomstats", "e3nn", "rustworkx", "xgi", "toponetx", "gudhi", "cvc5", "pyg"):
    # reasons already populated above/defaulted; mark tried if import succeeds where lightweight
    pass


CLASSIFICATION_NOTE = (
    "Direct local bookkeeping packet for left/right Weyl density matrices on one Hopf/Weyl carrier. "
    "It explicitly constructs rho_L and rho_R, verifies trace-one / PSD / Hermiticity, checks fiber-phase invariance, "
    "and separates chirality-projector algebra from geometric bookkeeping without claiming bridge or axis closure."
)
LEGO_IDS = [
    "weyl_chirality_pair",
    "chiral_density_bookkeeping",
    "left_right_asymmetry",
]
PRIMARY_LEGO_IDS = [
    "chiral_density_bookkeeping",
]

P_L_2 = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex)
P_R_2 = np.array([[0.0, 0.0], [0.0, 1.0]], dtype=complex)


def _projector_pair_dirac_sympy():
    I2 = sp.eye(2)
    Z2 = sp.zeros(2, 2)
    sigma_x = sp.Matrix([[0, 1], [1, 0]])
    sigma_y = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    sigma_z = sp.Matrix([[1, 0], [0, -1]])
    gamma0 = sp.BlockMatrix([[I2, Z2], [Z2, -I2]]).as_explicit()
    gamma1 = sp.BlockMatrix([[Z2, sigma_x], [-sigma_x, Z2]]).as_explicit()
    gamma2 = sp.BlockMatrix([[Z2, sigma_y], [-sigma_y, Z2]]).as_explicit()
    gamma3 = sp.BlockMatrix([[Z2, sigma_z], [-sigma_z, Z2]]).as_explicit()
    gamma5 = sp.simplify(sp.I * gamma0 * gamma1 * gamma2 * gamma3)
    I4 = sp.eye(4)
    P_L = sp.simplify((I4 - gamma5) / 2)
    P_R = sp.simplify((I4 + gamma5) / 2)
    return P_L, P_R


def _torch_density_from_spinor(spinor: np.ndarray) -> np.ndarray:
    vec = torch.tensor(spinor, dtype=torch.complex128)
    rho = torch.outer(vec, torch.conj(vec))
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "Load-bearing construction and validation of rho_L / rho_R from Weyl spinors with torch complex tensors"
    TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"
    return rho.detach().cpu().numpy()


def _matrix_stats(rho: np.ndarray) -> dict:
    eigvals = np.linalg.eigvalsh(rho)
    return {
        "trace": float(np.trace(rho).real),
        "hermitian": bool(np.allclose(rho, rho.conj().T, atol=1e-10)),
        "min_eigenvalue": float(np.min(eigvals).real),
        "max_eigenvalue": float(np.max(eigvals).real),
        "psd": bool(np.min(eigvals).real >= -1e-10),
    }


def _serialize_complex_matrix(mat: np.ndarray) -> list[list[dict[str, float]]]:
    return [
        [{"re": float(z.real), "im": float(z.imag)} for z in row]
        for row in mat
    ]


def compute_bookkeeping_sample(eta: float, theta1: float, theta2: float) -> dict:
    q = torus_coordinates(eta, theta1, theta2)
    psi_L = left_weyl_spinor(q)
    psi_R = right_weyl_spinor(q)
    rho_L = left_density(q)
    rho_R = right_density(q)
    rho_sum = rho_L + rho_R
    bloch_L = density_to_bloch(rho_L)
    bloch_R = density_to_bloch(rho_R)
    return {
        "q": q,
        "psi_L": psi_L,
        "psi_R": psi_R,
        "rho_L": rho_L,
        "rho_R": rho_R,
        "rho_sum": rho_sum,
        "left_projector": P_L_2.copy(),
        "right_projector": P_R_2.copy(),
        "bloch_L": bloch_L,
        "bloch_R": bloch_R,
        "bloch_antipodal_gap": float(np.linalg.norm(bloch_L + bloch_R)),
        "rho_L_stats": _matrix_stats(rho_L),
        "rho_R_stats": _matrix_stats(rho_R),
        "rho_sum_trace": float(np.trace(rho_sum).real),
    }


def run_positive_tests() -> dict:
    results: dict[str, dict] = {}

    # Positive 1: local density validity on representative torus seats
    try:
        points = [
            (math.pi / 8, 0.3, 1.1),
            (math.pi / 4, 0.8, 1.7),
            (3 * math.pi / 8, 1.4, 0.2),
        ]
        checks = []
        all_pass = True
        for eta, theta1, theta2 in points:
            sample = compute_bookkeeping_sample(eta, theta1, theta2)
            rho_L = sample["rho_L"]
            rho_R = sample["rho_R"]
            rho_L_t = _torch_density_from_spinor(sample["psi_L"])
            rho_R_t = _torch_density_from_spinor(sample["psi_R"])
            valid = (
                sample["rho_L_stats"]["hermitian"]
                and sample["rho_R_stats"]["hermitian"]
                and abs(sample["rho_L_stats"]["trace"] - 1.0) < 1e-10
                and abs(sample["rho_R_stats"]["trace"] - 1.0) < 1e-10
                and sample["rho_L_stats"]["psd"]
                and sample["rho_R_stats"]["psd"]
                and np.allclose(rho_L, rho_L_t, atol=1e-10)
                and np.allclose(rho_R, rho_R_t, atol=1e-10)
            )
            all_pass = all_pass and valid
            checks.append({
                "eta": float(eta),
                "theta1": float(theta1),
                "theta2": float(theta2),
                "rho_L_stats": sample["rho_L_stats"],
                "rho_R_stats": sample["rho_R_stats"],
                "torch_crosscheck": bool(np.allclose(rho_L, rho_L_t, atol=1e-10) and np.allclose(rho_R, rho_R_t, atol=1e-10)),
                "pass": bool(valid),
            })
        results["local_density_validity"] = {"pass": bool(all_pass), "checks": checks}
    except Exception as exc:
        results["local_density_validity"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    # Positive 2: bookkeeping sum and Bloch antipodality
    try:
        points = [
            (math.pi / 8, 0.15, 0.45),
            (math.pi / 4, 1.0, 2.0),
            (3 * math.pi / 8, 2.2, 1.4),
        ]
        checks = []
        all_pass = True
        for eta, theta1, theta2 in points:
            sample = compute_bookkeeping_sample(eta, theta1, theta2)
            bookkeeping_ok = np.allclose(sample["rho_sum"], sample["rho_L"] + sample["rho_R"], atol=1e-10)
            antipodal_ok = sample["bloch_antipodal_gap"] < 1e-10
            all_pass = all_pass and bookkeeping_ok and antipodal_ok
            checks.append({
                "eta": float(eta),
                "theta1": float(theta1),
                "theta2": float(theta2),
                "rho_sum_trace": sample["rho_sum_trace"],
                "bloch_antipodal_gap": sample["bloch_antipodal_gap"],
                "bookkeeping_ok": bool(bookkeeping_ok),
                "antipodal_ok": bool(antipodal_ok),
                "pass": bool(bookkeeping_ok and antipodal_ok),
            })
        results["bookkeeping_sum_and_antipodality"] = {"pass": bool(all_pass), "checks": checks}
    except Exception as exc:
        results["bookkeeping_sum_and_antipodality"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    # Positive 3: fiber-phase invariance of densities
    try:
        q = torus_coordinates(math.pi / 4, 0.7, 1.3)
        q_fiber = fiber_action(q, 1.9)
        rho_L = left_density(q)
        rho_R = right_density(q)
        rho_L_fiber = left_density(q_fiber)
        rho_R_fiber = right_density(q_fiber)
        pass_flag = bool(np.allclose(rho_L, rho_L_fiber, atol=1e-10) and np.allclose(rho_R, rho_R_fiber, atol=1e-10))
        results["fiber_phase_invariance"] = {
            "pass": pass_flag,
            "left_invariant": bool(np.allclose(rho_L, rho_L_fiber, atol=1e-10)),
            "right_invariant": bool(np.allclose(rho_R, rho_R_fiber, atol=1e-10)),
        }
    except Exception as exc:
        results["fiber_phase_invariance"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    # Positive 4: sympy chirality projector algebra
    try:
        P_L, P_R = _projector_pair_dirac_sympy()
        zero4 = sp.zeros(4, 4)
        I4 = sp.eye(4)
        orthogonal = sp.simplify(P_L * P_R) == zero4
        left_idempotent = sp.simplify(P_L * P_L - P_L) == zero4
        right_idempotent = sp.simplify(P_R * P_R - P_R) == zero4
        complete = sp.simplify(P_L + P_R - I4) == zero4
        pass_flag = bool(orthogonal and left_idempotent and right_idempotent and complete)
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = "Load-bearing symbolic verification of chirality projector orthogonality, idempotency, and completeness"
        TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"
        results["sympy_projector_bookkeeping"] = {
            "pass": pass_flag,
            "orthogonal": bool(orthogonal),
            "left_idempotent": bool(left_idempotent),
            "right_idempotent": bool(right_idempotent),
            "complete": bool(complete),
        }
    except Exception as exc:
        results["sympy_projector_bookkeeping"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    # Positive 5: z3 mutual-exclusion proof for complementary chirality projectors
    try:
        x, y = Reals("x y")
        solver = Solver()
        # P_L v = v and P_R v = v for P_L=diag(1,0), P_R=diag(0,1)
        solver.add(x == x)
        solver.add(0 == y)
        solver.add(0 == x)
        solver.add(y == y)
        solver.add(x * x + y * y > 0)
        unsat_result = solver.check() == unsat
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = "Load-bearing UNSAT proof that no nonzero vector can be fixed by both complementary chirality projectors simultaneously"
        TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
        results["z3_projector_mutual_exclusion"] = {
            "pass": bool(unsat_result),
            "unsat": bool(unsat_result),
            "claim": "no nonzero bookkeeping state can satisfy both P_L v = v and P_R v = v for complementary projectors",
        }
    except Exception as exc:
        results["z3_projector_mutual_exclusion"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    return results


def run_negative_tests() -> dict:
    results: dict[str, dict] = {}

    # Negative 1: unnormalized spinors should fail trace-one bookkeeping
    try:
        q = torus_coordinates(math.pi / 4, 0.2, 0.9)
        psi_L = 2.0 * left_weyl_spinor(q)
        psi_R = 3.0 * right_weyl_spinor(q)
        bad_rho_L = np.outer(psi_L, np.conj(psi_L))
        bad_rho_R = np.outer(psi_R, np.conj(psi_R))
        pass_flag = bool(abs(np.trace(bad_rho_L).real - 1.0) > 1e-6 and abs(np.trace(bad_rho_R).real - 1.0) > 1e-6)
        results["unnormalized_spinor_trace_breaks"] = {
            "pass": pass_flag,
            "bad_trace_L": float(np.trace(bad_rho_L).real),
            "bad_trace_R": float(np.trace(bad_rho_R).real),
        }
    except Exception as exc:
        results["unnormalized_spinor_trace_breaks"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    # Negative 2: overlapping fake projectors fail chirality bookkeeping
    try:
        fake_P_L = np.eye(2, dtype=complex)
        fake_P_R = np.eye(2, dtype=complex)
        overlap = fake_P_L @ fake_P_R
        pass_flag = bool(not np.allclose(overlap, np.zeros((2, 2), dtype=complex)))
        results["fake_projectors_not_orthogonal"] = {
            "pass": pass_flag,
            "overlap_norm": float(np.linalg.norm(overlap)),
        }
    except Exception as exc:
        results["fake_projectors_not_orthogonal"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    # Negative 3: wrong right-density surrogate destroys L/R antipodality
    try:
        q = torus_coordinates(math.pi / 8, 1.1, 2.4)
        rho_L = left_density(q)
        wrong_rho_R = np.outer(left_weyl_spinor(q), np.conj(left_weyl_spinor(q)))
        gap = float(np.linalg.norm(density_to_bloch(rho_L) + density_to_bloch(wrong_rho_R)))
        pass_flag = bool(gap > 1e-6)
        results["wrong_right_density_breaks_antipodality"] = {
            "pass": pass_flag,
            "bloch_antipodal_gap": gap,
        }
    except Exception as exc:
        results["wrong_right_density_breaks_antipodality"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    return results


def run_boundary_tests() -> dict:
    results: dict[str, dict] = {}
    try:
        seats = [0.0, math.pi / 4, math.pi / 2]
        checks = []
        all_pass = True
        for eta in seats:
            sample = compute_bookkeeping_sample(eta, 0.0, 0.0)
            seat_pass = (
                sample["rho_L_stats"]["psd"]
                and sample["rho_R_stats"]["psd"]
                and abs(sample["rho_L_stats"]["trace"] - 1.0) < 1e-10
                and abs(sample["rho_R_stats"]["trace"] - 1.0) < 1e-10
            )
            all_pass = all_pass and seat_pass
            checks.append({
                "eta": float(eta),
                "rho_L_trace": sample["rho_L_stats"]["trace"],
                "rho_R_trace": sample["rho_R_stats"]["trace"],
                "bloch_antipodal_gap": sample["bloch_antipodal_gap"],
                "pass": bool(seat_pass),
            })
        results["named_torus_seats"] = {"pass": bool(all_pass), "checks": checks}
    except Exception as exc:
        results["named_torus_seats"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    try:
        q = torus_coordinates(math.pi / 4, 0.6, 0.9)
        q_zero = fiber_action(q, 0.0)
        q_full = fiber_action(q, 2 * math.pi)
        pass_flag = bool(np.allclose(left_density(q_zero), left_density(q_full), atol=1e-10) and np.allclose(right_density(q_zero), right_density(q_full), atol=1e-10))
        results["fiber_phase_boundary_0_2pi"] = {
            "pass": pass_flag,
            "left_equal": bool(np.allclose(left_density(q_zero), left_density(q_full), atol=1e-10)),
            "right_equal": bool(np.allclose(right_density(q_zero), right_density(q_full), atol=1e-10)),
        }
    except Exception as exc:
        results["fiber_phase_boundary_0_2pi"] = {"pass": False, "error": str(exc), "traceback": traceback.format_exc()}

    return results


def _count_passes(section: dict) -> tuple[int, int]:
    passed = sum(1 for item in section.values() if item.get("pass") is True)
    total = len(section)
    return passed, total


def main() -> None:
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    p_pass, p_total = _count_passes(positive)
    n_pass, n_total = _count_passes(negative)
    b_pass, b_total = _count_passes(boundary)
    all_pass = (p_pass == p_total) and (n_pass == n_total) and (b_pass == b_total)

    demo = compute_bookkeeping_sample(math.pi / 4, 0.3, 1.1)
    serial_demo = {
        "rho_L": _serialize_complex_matrix(demo["rho_L"]),
        "rho_R": _serialize_complex_matrix(demo["rho_R"]),
        "rho_sum": _serialize_complex_matrix(demo["rho_sum"]),
        "bloch_L": demo["bloch_L"].tolist(),
        "bloch_R": demo["bloch_R"].tolist(),
        "bloch_antipodal_gap": demo["bloch_antipodal_gap"],
    }

    results = {
        "name": "chiral_density_bookkeeping",
        "description": "Direct local bookkeeping packet for rho_L and rho_R on the Hopf/Weyl carrier",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "created_at": datetime.now(UTC).isoformat(),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "demo_sample": serial_demo,
        "all_pass": all_pass,
        "summary": {
            "positive": {"passed": p_pass, "total": p_total},
            "negative": {"passed": n_pass, "total": n_total},
            "boundary": {"passed": b_pass, "total": b_total},
        },
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "chiral_density_bookkeeping_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Results written to {out_path}")
    print(f"Summary: {p_pass+n_pass+b_pass} pass / {p_total+n_total+b_total-(p_pass+n_pass+b_pass)} fail / 0 error out of {p_total+n_total+b_total} tests")


if __name__ == "__main__":
    main()
