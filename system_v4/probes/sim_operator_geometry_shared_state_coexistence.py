#!/usr/bin/env python3
"""Shared finite-state coexistence check for operator-geometry exclusions.

This packet tests whether the three named single-pair order exclusions can live
on one bounded finite Bloch-ball witness family, with controls that still kill
the expected commuting/degenerate cases.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from scipy.linalg import expm

from receipt_boundary import apply_default_receipt_boundary


classification = "supporting"

SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing finite shared-state witness checks"},
    "scipy": {"tried": True, "used": True, "reason": "load-bearing matrix exponentials for rotations"},
    "z3": {
        "tried": False,
        "used": False,
        "reason": "not used here; z3 structural fences live in the single-pair exclusion receipts",
    },
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "scipy": "load_bearing",
    "z3": None,
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


def valid_density(rho: np.ndarray) -> bool:
    eigvals = np.linalg.eigvalsh(rho)
    return bool(np.all(eigvals >= -1e-12) and abs(np.trace(rho) - 1.0) < 1e-12)


def ti_z_dephase(rho: np.ndarray, strength: float) -> np.ndarray:
    p0 = np.array([[1, 0], [0, 0]], dtype=complex)
    p1 = np.array([[0, 0], [0, 1]], dtype=complex)
    return (1 - strength) * rho + strength * (p0 @ rho @ p0 + p1 @ rho @ p1)


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


def gap_ti_fi(rho: np.ndarray, strength: float, theta: float) -> float:
    return rho_to_bloch(fi_x_rotate(ti_z_dephase(rho, strength), theta))[2] - rho_to_bloch(
        ti_z_dephase(fi_x_rotate(rho, theta), strength)
    )[2]


def gap_te_fe(rho: np.ndarray, strength: float, phi: float) -> float:
    return rho_to_bloch(fe_z_rotate(te_x_dephase(rho, strength), phi))[0] - rho_to_bloch(
        te_x_dephase(fe_z_rotate(rho, phi), strength)
    )[0]


def gap_fe_fi(rho: np.ndarray, phi: float, theta: float) -> float:
    return rho_to_bloch(fi_x_rotate(fe_z_rotate(rho, phi), theta))[2] - rho_to_bloch(
        fe_z_rotate(fi_x_rotate(rho, theta), phi)
    )[2]


def numeric_witness_family() -> list[dict]:
    strength = 0.5
    theta = np.pi / 3
    phi = np.pi / 5
    family = [
        {"name": "y_positive_a", "bloch": np.array([0.10, 0.35, 0.20])},
        {"name": "y_positive_b", "bloch": np.array([0.25, 0.30, 0.15])},
        {"name": "y_zero_a", "bloch": np.array([0.35, 0.00, 0.10])},
        {"name": "y_zero_b", "bloch": np.array([0.45, 0.00, -0.20])},
    ]
    rows = []
    for item in family:
        vec = item["bloch"]
        rho = bloch_to_rho(vec)
        row = {
            "name": item["name"],
            "bloch": vec.tolist(),
            "density_valid": valid_density(rho),
            "ti_fi_gap_z": gap_ti_fi(rho, strength, theta),
            "te_fe_gap_x": gap_te_fe(rho, strength, phi),
            "fe_fi_gap_z": gap_fe_fi(rho, phi, theta),
        }
        row["pass"] = bool(row["density_valid"] and (
            (abs(row["ti_fi_gap_z"]) > 1e-6 and abs(row["te_fe_gap_x"]) > 1e-6)
            or (abs(row["fe_fi_gap_z"]) > 1e-6 and abs(vec[1]) < 1e-12)
        ))
        rows.append(row)
    return rows


def numeric_commuting_controls() -> dict:
    strength = 0.5
    theta = np.pi / 3
    phi = np.pi / 5
    rho = bloch_to_rho(np.array([0.20, 0.30, 0.10]))
    ti_fe_z_gap = rho_to_bloch(fe_z_rotate(ti_z_dephase(rho, strength), phi))[2] - rho_to_bloch(
        ti_z_dephase(fe_z_rotate(rho, phi), strength)
    )[2]
    te_fi_x_gap = rho_to_bloch(fi_x_rotate(te_x_dephase(rho, strength), theta))[0] - rho_to_bloch(
        te_x_dephase(fi_x_rotate(rho, theta), strength)
    )[0]
    return {
        "ti_z_dephase_fe_z_rotate_z_invariant": {
            "gap": ti_fe_z_gap,
            "pass": bool(abs(ti_fe_z_gap) < 1e-12),
        },
        "te_x_dephase_fi_x_rotate_x_invariant": {
            "gap": te_fi_x_gap,
            "pass": bool(abs(te_fi_x_gap) < 1e-12),
        },
    }


def main() -> int:
    witnesses = numeric_witness_family()
    commuting_controls = numeric_commuting_controls()
    positive = {
        "shared_finite_family_has_expected_nonzero_gaps": {
            "witnesses": witnesses,
            "pass": all(row["pass"] for row in witnesses),
        },
        "y_positive_states_witness_all_three_order_gaps": {
            "states": [
                row["name"]
                for row in witnesses
                if abs(row["ti_fi_gap_z"]) > 1e-6
                and abs(row["te_fe_gap_x"]) > 1e-6
                and abs(row["fe_fi_gap_z"]) > 1e-6
            ],
            "pass": sum(
                1
                for row in witnesses
                if abs(row["ti_fi_gap_z"]) > 1e-6
                and abs(row["te_fe_gap_x"]) > 1e-6
                and abs(row["fe_fi_gap_z"]) > 1e-6
            )
            >= 2,
        },
    }
    negative = {
        "commuting_controls_block_false_positive": {
            "controls": commuting_controls,
            "pass": all(item["pass"] for item in commuting_controls.values()),
        },
        "all_witnesses_are_valid_density_states": {
            "pass": all(row["density_valid"] for row in witnesses),
        },
    }
    boundary = {
        "coexistence_is_finite_and_local": {
            "state_count": len(witnesses),
            "pass": len(witnesses) == 4,
        },
        "no_global_stack_claim": {
            "pass": True,
            "note": "This does not claim full operator-geometry closure, GStack, axis, or QIT admission.",
        },
    }
    all_pass = all(item["pass"] for group in (positive, negative, boundary) for item in group.values())
    results = {
        "name": "operator_geometry_shared_state_coexistence",
        "classification": "supporting",
        "classification_note": (
            "Fresh finite coexistence witness for three operator-order exclusions over one shared "
            "Bloch-ball state family. Queue evidence only, not admission."
        ),
        "generated_at": datetime.now(UTC).isoformat(),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "shared_state_count": len(witnesses),
            "coexistence_candidate": bool(all_pass),
            "promotion_allowed": False,
            "scope_note": "Finite shared-state coexistence candidate; broader closure still requires assembly/stage-gate review.",
        },
        "all_pass": all_pass,
        "divergence_log": (
            "This sim upgrades from reading prior receipts to a fresh shared finite witness family, "
            "but it remains local and supporting. It does not assemble all operator/geometry legos; "
            "z3 structural proof is intentionally left to the single-pair exclusion receipts."
        ),
    }
    results = apply_default_receipt_boundary(
        results,
        source_name="sim_operator_geometry_shared_state_coexistence",
        target="Use as local coexistence candidate before broader operator-geometry assembly.",
    )
    results["promotion_condition"] = (
        "Requires broader assembly across more operator/geometry legos and explicit stage-gate admission."
    )
    results["blocked_until"] = "broader operator-geometry assembly and stage-gate admission"

    out_path = RESULTS_DIR / "operator_geometry_shared_state_coexistence_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
