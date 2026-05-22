#!/usr/bin/env python3
"""Single-pair operator/geometry exclusion for a named invariant.

Pair: z-dephasing Ti and x-rotation Fi.
Invariant: Bloch z-component after the two-step sequence.

The point is narrow: prove and witness that the order effect is structurally
nonzero on a bounded finite domain, while simple controls kill the effect.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from scipy.linalg import expm
from z3 import And, Not, Q, Real, Solver, unsat

from receipt_boundary import apply_default_receipt_boundary


classification = "supporting"

SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing numeric density-matrix witnesses"},
    "scipy": {"tried": True, "used": True, "reason": "load-bearing matrix exponential for x-rotation"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing UNSAT exclusion for zero z-invariant order gap"},
    "sympy": {"tried": False, "used": False, "reason": "not needed; z3 carries the proof fence"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed in first single-pair fence"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "scipy": "load_bearing",
    "z3": "load_bearing",
    "sympy": None,
    "cvc5": None,
}

sx = np.array([[0, 1], [1, 0]], dtype=complex)
sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
sz = np.array([[1, 0], [0, -1]], dtype=complex)
I2 = np.eye(2, dtype=complex)


def bloch_to_rho(r: np.ndarray) -> np.ndarray:
    return (I2 + r[0] * sx + r[1] * sy + r[2] * sz) / 2


def rho_to_bloch(rho: np.ndarray) -> np.ndarray:
    return np.array(
        [
            float(np.real(np.trace(rho @ sx))),
            float(np.real(np.trace(rho @ sy))),
            float(np.real(np.trace(rho @ sz))),
        ]
    )


def ti_z_dephase(rho: np.ndarray, strength: float) -> np.ndarray:
    p0 = np.array([[1, 0], [0, 0]], dtype=complex)
    p1 = np.array([[0, 0], [0, 1]], dtype=complex)
    return (1 - strength) * rho + strength * (p0 @ rho @ p0 + p1 @ rho @ p1)


def fi_x_rotate(rho: np.ndarray, theta: float) -> np.ndarray:
    unitary = expm(-1j * theta * sx / 2)
    return unitary @ rho @ unitary.conj().T


def z_after_ti_then_fi(rho: np.ndarray, strength: float, theta: float) -> float:
    return rho_to_bloch(fi_x_rotate(ti_z_dephase(rho, strength), theta))[2]


def z_after_fi_then_ti(rho: np.ndarray, strength: float, theta: float) -> float:
    return rho_to_bloch(ti_z_dephase(fi_x_rotate(rho, theta), strength))[2]


def z3_exclusion() -> dict:
    """Prove no zero gap on a finite rational subdomain.

    For Bloch y-component y, z-dephasing strength s, and sin(theta)=k:
    z(Ti->Fi) - z(Fi->Ti) = -s*k*y.

    On the bounded cell s in [1/4,3/4], k in [1/4,3/4], y in [1/4,3/4],
    the zero-gap equation is UNSAT.
    """
    s = Real("s")
    k = Real("k")
    y = Real("y")
    gap = -s * k * y
    solver = Solver()
    solver.add(
        And(
            s >= Q(1, 4),
            s <= Q(3, 4),
            k >= Q(1, 4),
            k <= Q(3, 4),
            y >= Q(1, 4),
            y <= Q(3, 4),
            gap == 0,
        )
    )
    return {
        "formula": "gap_z = -s * sin(theta) * y",
        "domain": "s,k,y in [1/4, 3/4]",
        "zero_gap_sat": str(solver.check()),
        "pass": solver.check() == unsat,
    }


def numeric_witnesses() -> list[dict]:
    strength = 0.5
    theta = np.pi / 3
    vectors = [
        np.array([0.10, 0.35, 0.20]),
        np.array([-0.20, 0.45, -0.10]),
        np.array([0.25, 0.30, 0.15]),
    ]
    out = []
    for vec in vectors:
        rho = bloch_to_rho(vec)
        z_tf = z_after_ti_then_fi(rho, strength, theta)
        z_ft = z_after_fi_then_ti(rho, strength, theta)
        predicted = -strength * np.sin(theta) * vec[1]
        out.append(
            {
                "bloch": vec.tolist(),
                "z_ti_then_fi": z_tf,
                "z_fi_then_ti": z_ft,
                "observed_gap": z_tf - z_ft,
                "predicted_gap": predicted,
                "pass": bool(abs((z_tf - z_ft) - predicted) < 1e-12 and abs(z_tf - z_ft) > 1e-6),
            }
        )
    return out


def controls() -> dict:
    rho = bloch_to_rho(np.array([0.1, 0.4, 0.2]))
    no_dephase_gap = z_after_ti_then_fi(rho, 0.0, np.pi / 3) - z_after_fi_then_ti(rho, 0.0, np.pi / 3)
    no_rotation_gap = z_after_ti_then_fi(rho, 0.5, 0.0) - z_after_fi_then_ti(rho, 0.5, 0.0)
    y_zero_rho = bloch_to_rho(np.array([0.1, 0.0, 0.2]))
    y_zero_gap = z_after_ti_then_fi(y_zero_rho, 0.5, np.pi / 3) - z_after_fi_then_ti(
        y_zero_rho, 0.5, np.pi / 3
    )
    return {
        "no_dephasing_control": {"gap": no_dephase_gap, "pass": abs(no_dephase_gap) < 1e-12},
        "no_rotation_control": {"gap": no_rotation_gap, "pass": abs(no_rotation_gap) < 1e-12},
        "y_zero_invariant_control": {"gap": y_zero_gap, "pass": abs(y_zero_gap) < 1e-12},
    }


def main() -> int:
    proof = z3_exclusion()
    witnesses = numeric_witnesses()
    control = controls()
    positive = {
        "z3_excludes_zero_gap_on_bounded_cell": proof,
        "three_numeric_witnesses_match_formula": {
            "witnesses": witnesses,
            "pass": all(item["pass"] for item in witnesses),
        },
    }
    negative = {
        "controls_kill_the_gap": {
            "controls": control,
            "pass": all(item["pass"] for item in control.values()),
        }
    }
    boundary = {
        "named_pair_and_invariant_only": {
            "pair": "Ti_z_dephase, Fi_x_rotate",
            "invariant": "Bloch z-component after sequence",
            "pass": True,
        },
        "no_admission_claim": {
            "pass": True,
            "note": "This is one structural exclusion receipt, not QIT/GStack/axis/nonclassical admission.",
        },
    }
    all_pass = all(item["pass"] for group in (positive, negative, boundary) for item in group.values())
    results = {
        "name": "operator_geometry_single_pair_exclusion",
        "classification": "supporting",
        "classification_note": (
            "Single-pair structural exclusion for operator-geometry order dependence. "
            "Closure-candidate evidence only; no promotion by itself."
        ),
        "generated_at": datetime.now(UTC).isoformat(),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "closure_candidate": bool(all_pass),
            "named_pair": "Ti_z_dephase vs Fi_x_rotate",
            "named_invariant": "Bloch z-component",
            "scope_note": "Finite single-pair exclusion plus controls; does not assemble a full geometry/operator stack.",
        },
        "all_pass": all_pass,
        "divergence_log": (
            "Unlike a broad compatibility matrix, this receipt targets one named noncommuting pair and one invariant. "
            "It still remains below full closure because it does not test coexistence across the larger lego set."
        ),
    }
    results = apply_default_receipt_boundary(
        results,
        source_name="sim_operator_geometry_single_pair_exclusion",
        target="Use as one closure-candidate operator-geometry exclusion before broader coexistence assembly.",
    )
    results["promotion_condition"] = (
        "Requires multiple independent single-pair exclusions plus coexistence/assembly receipts and stage-gate admission."
    )
    results["blocked_until"] = "additional independent exclusions and explicit coexistence-stage admission"

    out_path = RESULTS_DIR / "operator_geometry_single_pair_exclusion_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
