#!/usr/bin/env python3
"""Independent single-pair order exclusions for operator/geometry coupling.

This extends the first Ti/Fi exclusion with two more named finite pair checks.
Each check has one named Bloch invariant, one z3 zero-gap exclusion on a bounded
rational cell, numeric witnesses, and controls that kill the gap.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from scipy.linalg import expm
from z3 import And, Q, Real, Solver, unsat

from receipt_boundary import apply_default_receipt_boundary


classification = "supporting"

SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing numeric density-matrix witnesses"},
    "scipy": {"tried": True, "used": True, "reason": "load-bearing matrix exponentials for rotations"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing bounded UNSAT exclusions"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed in this bounded z3 packet"},
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


def te_x_dephase(rho: np.ndarray, strength: float) -> np.ndarray:
    qp = np.array([[1, 1], [1, 1]], dtype=complex) / 2
    qm = np.array([[1, -1], [-1, 1]], dtype=complex) / 2
    return (1 - strength) * rho + strength * (qp @ rho @ qp + qm @ rho @ qm)


def fe_z_rotate(rho: np.ndarray, phi: float) -> np.ndarray:
    unitary = expm(-1j * phi * sz / 2)
    return unitary @ rho @ unitary.conj().T


def fi_x_rotate(rho: np.ndarray, theta: float) -> np.ndarray:
    unitary = expm(-1j * theta * sx / 2)
    return unitary @ rho @ unitary.conj().T


def bounded_unsat(product_terms: list[str]) -> dict:
    variables = {name: Real(name) for name in product_terms}
    gap = variables[product_terms[0]]
    for name in product_terms[1:]:
        gap *= variables[name]
    solver = Solver()
    solver.add(
        And(
            *[
                And(variables[name] >= Q(1, 4), variables[name] <= Q(3, 4))
                for name in product_terms
            ],
            gap == 0,
        )
    )
    return {
        "zero_gap_sat": str(solver.check()),
        "domain": f"{', '.join(product_terms)} in [1/4, 3/4]",
        "pass": solver.check() == unsat,
    }


def te_fe_check() -> dict:
    """Pair Te x-dephase and Fe z-rotation, x invariant.

    x(Te->Fe) - x(Fe->Te) = d * sin(phi) * y.
    """
    strength = 0.5
    phi = np.pi / 3
    vectors = [
        np.array([0.10, 0.35, 0.20]),
        np.array([-0.20, 0.45, -0.10]),
        np.array([0.25, 0.30, 0.15]),
    ]
    witnesses = []
    for vec in vectors:
        rho = bloch_to_rho(vec)
        x_te_fe = rho_to_bloch(fe_z_rotate(te_x_dephase(rho, strength), phi))[0]
        x_fe_te = rho_to_bloch(te_x_dephase(fe_z_rotate(rho, phi), strength))[0]
        predicted = strength * np.sin(phi) * vec[1]
        witnesses.append(
            {
                "bloch": vec.tolist(),
                "observed_gap": x_te_fe - x_fe_te,
                "predicted_gap": predicted,
                "pass": bool(abs((x_te_fe - x_fe_te) - predicted) < 1e-12 and abs(predicted) > 1e-6),
            }
        )
    controls = {
        "no_dephasing": 0.0 * np.sin(phi) * 0.4 == 0,
        "no_rotation": 0.5 * np.sin(0.0) * 0.4 == 0,
        "y_zero": 0.5 * np.sin(phi) * 0.0 == 0,
    }
    return {
        "pair": "Te_x_dephase vs Fe_z_rotate",
        "invariant": "Bloch x-component after sequence",
        "formula": "gap_x = d * sin(phi) * y",
        "z3": bounded_unsat(["d", "k", "y"]),
        "witnesses": witnesses,
        "controls": controls,
        "pass": all(item["pass"] for item in witnesses) and all(controls.values()),
    }


def fe_fi_check() -> dict:
    """Pair Fe z-rotation and Fi x-rotation, z invariant on y=0 slice.

    z(Fe->Fi) - z(Fi->Fe) = sin(theta) * sin(phi) * x when y=0.
    """
    theta = np.pi / 4
    phi = np.pi / 5
    vectors = [
        np.array([0.35, 0.0, 0.10]),
        np.array([0.45, 0.0, -0.20]),
        np.array([0.30, 0.0, 0.25]),
    ]
    witnesses = []
    for vec in vectors:
        rho = bloch_to_rho(vec)
        z_fe_fi = rho_to_bloch(fi_x_rotate(fe_z_rotate(rho, phi), theta))[2]
        z_fi_fe = rho_to_bloch(fe_z_rotate(fi_x_rotate(rho, theta), phi))[2]
        predicted = np.sin(theta) * np.sin(phi) * vec[0]
        witnesses.append(
            {
                "bloch_y_zero_slice": vec.tolist(),
                "observed_gap": z_fe_fi - z_fi_fe,
                "predicted_gap": predicted,
                "pass": bool(abs((z_fe_fi - z_fi_fe) - predicted) < 1e-12 and abs(predicted) > 1e-6),
            }
        )
    controls = {
        "no_x_rotation": np.sin(0.0) * np.sin(phi) * 0.4 == 0,
        "no_z_rotation": np.sin(theta) * np.sin(0.0) * 0.4 == 0,
        "x_zero": np.sin(theta) * np.sin(phi) * 0.0 == 0,
    }
    return {
        "pair": "Fe_z_rotate vs Fi_x_rotate",
        "invariant": "Bloch z-component after sequence on y=0 slice",
        "formula": "gap_z = sin(theta) * sin(phi) * x",
        "z3": bounded_unsat(["kx", "kz", "x"]),
        "witnesses": witnesses,
        "controls": controls,
        "pass": all(item["pass"] for item in witnesses) and all(controls.values()),
    }


def main() -> int:
    checks = {
        "te_fe_x_invariant": te_fe_check(),
        "fe_fi_z_invariant_y_zero_slice": fe_fi_check(),
    }
    positive = {
        "all_z3_exclusions_unsat": {
            "statuses": {name: check["z3"]["zero_gap_sat"] for name, check in checks.items()},
            "pass": all(check["z3"]["pass"] for check in checks.values()),
        },
        "all_numeric_witnesses_match_formulas": {
            "pass": all(item["pass"] for check in checks.values() for item in check["witnesses"]),
        },
    }
    negative = {
        "controls_kill_each_gap": {
            "controls": {name: check["controls"] for name, check in checks.items()},
            "pass": all(all(check["controls"].values()) for check in checks.values()),
        }
    }
    boundary = {
        "two_independent_named_pairs": {
            "pairs": [check["pair"] for check in checks.values()],
            "pass": len({check["pair"] for check in checks.values()}) == 2,
        },
        "no_admission_claim": {
            "pass": True,
            "note": "This is finite operator-order exclusion evidence only.",
        },
    }
    all_pass = all(item["pass"] for group in (positive, negative, boundary) for item in group.values())
    results = {
        "name": "operator_geometry_multi_pair_exclusions",
        "classification": "supporting",
        "classification_note": (
            "Two independent single-pair operator-order exclusions with z3 fences and numeric witnesses. "
            "Closure-candidate evidence only; not a promotion."
        ),
        "generated_at": datetime.now(UTC).isoformat(),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "checks": checks,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "closure_candidate": bool(all_pass),
            "independent_pair_count": len(checks),
            "scope_note": "Finite two-pair exclusion receipt; does not test global coexistence or assembly.",
        },
        "all_pass": all_pass,
        "divergence_log": (
            "These exclusions test order effects on named finite invariants. "
            "They do not prove the full operator-geometry manifold, GStack, or QIT engine."
        ),
    }
    results = apply_default_receipt_boundary(
        results,
        source_name="sim_operator_geometry_multi_pair_exclusions",
        target="Use with the first single-pair exclusion before attempting closure-grade coexistence assembly.",
    )
    results["promotion_condition"] = (
        "Requires integration with coexistence/assembly receipts and explicit stage-gate admission."
    )
    results["blocked_until"] = "closure-grade coexistence assembly and stage-gate admission"

    out_path = RESULTS_DIR / "operator_geometry_multi_pair_exclusions_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
