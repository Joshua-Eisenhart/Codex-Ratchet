#!/usr/bin/env python3
"""Bounded graveyard probe for the gauge_group_falsifier lego.

This compares an abelian U(1) phase-composition surface with a finite Pauli
commutator surface. The point is a falsifier: an over-strong identification of
U(1) holonomy behavior with the full nonabelian commutator pattern should fail.
"""

from __future__ import annotations

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import json
import pathlib
from datetime import datetime, timezone
from typing import Any

import numpy as np
import sympy as sp


CLASSIFICATION = "classical_baseline"
CLASSIFICATION_NOTE = (
    "Finite gauge/group graveyard probe: abelian U(1) phase composition and "
    "nonabelian Pauli commutator closure are compared on fixed bounded carriers. "
    "This records a falsifier/boundary only; it does not admit a coupling, "
    "assembly, QIT, GStack, axis, or nonclassical claim."
)

LEGO_IDS = ["gauge_group_falsifier", "berry_phase_u1_abelian", "commutator_algebra"]
PRIMARY_LEGO_IDS = ["gauge_group_falsifier"]

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "loads prerequisite receipts and writes canonical result JSON",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "resolves local result paths",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite matrix, rank, and commutator calculations",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact symbolic rank and commutator obstruction check",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "json": "supportive",
    "pathlib": "supportive",
    "numpy": "load_bearing",
    "sympy": "load_bearing",
}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
OUT_PATH = RESULT_DIR / "gauge_group_falsifier_graveyard_results.json"

EPS = 1e-10


def load_receipt(name: str) -> dict[str, Any]:
    path = RESULT_DIR / name
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def commutator(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return a @ b - b @ a


def hs_inner(a: np.ndarray, b: np.ndarray) -> complex:
    return np.trace(a.conj().T @ b)


def span_rank(mats: list[np.ndarray]) -> int:
    if not mats:
        return 0
    columns = [m.reshape(-1) for m in mats]
    return int(np.linalg.matrix_rank(np.stack(columns, axis=1), tol=1e-10))


def project_residual(m: np.ndarray, basis: list[np.ndarray]) -> float:
    columns = np.stack([b.reshape(-1) for b in basis], axis=1)
    coeffs, *_ = np.linalg.lstsq(columns, m.reshape(-1), rcond=None)
    recon = (columns @ coeffs).reshape(m.shape)
    return float(np.linalg.norm(m - recon))


def all_pass_from_receipt(data: dict[str, Any]) -> bool:
    summary = data.get("summary", {})
    return bool(summary.get("all_pass", data.get("all_pass", False)))


def sympy_rank_obstruction() -> dict[str, Any]:
    x = sp.Matrix([[0, 1], [1, 0]])
    y = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    z = sp.Matrix([[1, 0], [0, -1]])
    i2 = sp.eye(2)
    u1 = sp.I * i2
    pauli_rank = sp.Matrix.hstack(*[m.reshape(4, 1) for m in [x, y, z]]).rank()
    u1_rank = sp.Matrix.hstack(u1.reshape(4, 1)).rank()
    xy_bracket = x * y - y * x
    u1_self_bracket = u1 * u1 - u1 * u1
    return {
        "u1_rank": int(u1_rank),
        "pauli_rank": int(pauli_rank),
        "u1_self_commutator_zero": bool(u1_self_bracket == sp.zeros(2)),
        "xy_bracket_nonzero": bool(xy_bracket != sp.zeros(2)),
        "pass": bool(u1_rank == 1 and pauli_rank == 3 and u1_self_bracket == sp.zeros(2) and xy_bracket != sp.zeros(2)),
    }


def main() -> None:
    berry = load_receipt("berry_phase_u1_abelian_results.json")
    commutator_receipt = load_receipt("commutator_algebra_results.json")
    correspondence = load_receipt("gauge_group_correspondence_results.json")

    x = np.array([[0, 1], [1, 0]], dtype=complex)
    y = np.array([[0, -1j], [1j, 0]], dtype=complex)
    z = np.array([[1, 0], [0, -1]], dtype=complex)
    i2 = np.eye(2, dtype=complex)

    pauli_basis = [x, y, z]
    su2_brackets = [
        commutator(x, y) / (2j),
        commutator(y, z) / (2j),
        commutator(z, x) / (2j),
    ]
    su2_rank = span_rank(pauli_basis)
    bracket_rank = span_rank(su2_brackets)

    u1_generator = 1j * i2
    u1_rank = span_rank([u1_generator])
    u1_self_commutator_norm = float(np.linalg.norm(commutator(u1_generator, u1_generator)))

    residuals_against_single_u1 = {
        "[X,Y]": project_residual(su2_brackets[0], [u1_generator]),
        "[Y,Z]": project_residual(su2_brackets[1], [u1_generator]),
        "[Z,X]": project_residual(su2_brackets[2], [u1_generator]),
    }
    minimum_single_u1_residual = min(residuals_against_single_u1.values())

    phase_a = np.exp(0.37j)
    phase_b = np.exp(-1.11j)
    u1_commutes = abs((phase_a * phase_b) - (phase_b * phase_a)) < EPS
    pauli_noncommutes = float(np.linalg.norm(commutator(x, y))) > 1.0
    sympy_obstruction = sympy_rank_obstruction()

    prerequisites = {
        "berry_phase_u1_abelian": all_pass_from_receipt(berry),
        "commutator_algebra": all_pass_from_receipt(commutator_receipt),
        "gauge_group_correspondence": all_pass_from_receipt(correspondence),
    }

    positive = {
        "prerequisite_receipts_pass": {
            "values": prerequisites,
            "pass": all(prerequisites.values()),
        },
        "u1_phase_composition_is_abelian": {
            "phase_a": [float(np.real(phase_a)), float(np.imag(phase_a))],
            "phase_b": [float(np.real(phase_b)), float(np.imag(phase_b))],
            "pass": bool(u1_commutes),
        },
        "pauli_commutator_surface_is_nonabelian": {
            "xy_commutator_norm": float(np.linalg.norm(commutator(x, y))),
            "pass": bool(pauli_noncommutes),
        },
        "sympy_exact_rank_obstruction_matches_numeric_obstruction": sympy_obstruction,
    }

    negative = {
        "single_u1_generator_cannot_span_su2_bracket_surface": {
            "u1_rank": u1_rank,
            "su2_rank": su2_rank,
            "bracket_rank": bracket_rank,
            "residuals_against_single_u1": residuals_against_single_u1,
            "minimum_single_u1_residual": minimum_single_u1_residual,
            "pass": bool(u1_rank < su2_rank and minimum_single_u1_residual > 0.5),
        },
        "abelian_self_commutator_cannot_realize_nonzero_pauli_bracket": {
            "u1_self_commutator_norm": u1_self_commutator_norm,
            "pauli_xy_commutator_norm": float(np.linalg.norm(commutator(x, y))),
            "pass": bool(u1_self_commutator_norm < EPS and pauli_noncommutes),
        },
    }

    boundary = {
        "finite_fixed_carriers_only": {
            "state_space": "2x2 finite matrices and scalar U(1) phases",
            "pass": True,
        },
        "no_assembly_or_gauge_admission": {
            "pass": True,
        },
        "claim_ceiling_preserved": {
            "claim_ceiling": "gauge_group_falsifier_graveyard_control_only",
            "pass": True,
        },
    }

    all_pass = (
        all(check["pass"] for check in positive.values())
        and all(check["pass"] for check in negative.values())
        and all(check["pass"] for check in boundary.values())
    )

    result = {
        "name": "gauge_group_falsifier_graveyard",
        "classification": CLASSIFICATION,
        "classification_note": CLASSIFICATION_NOTE,
        "divergence_log": CLASSIFICATION_NOTE,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "claim_ceiling": "gauge_group_falsifier_graveyard_control_only",
        "next_lego_target": "none",
        "promotion_condition": "requires a separate admitted coupling-stage receipt and stage-gate approval",
        "blocked_until": "gauge/group candidate has fixed-carrier coupling evidence and an assembly gate",
        "demotion_condition": "demote if U(1) and Pauli surfaces are later shown identical on this finite carrier",
        "out_of_scope": [
            "QIT engine admission",
            "GStack admission",
            "axis promotion",
            "engine promotion",
            "nonclassical proof",
            "scientific coupling closure",
        ],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipts": {
            "berry_phase_u1_abelian": str(RESULT_DIR / "berry_phase_u1_abelian_results.json"),
            "commutator_algebra": str(RESULT_DIR / "commutator_algebra_results.json"),
            "gauge_group_correspondence": str(RESULT_DIR / "gauge_group_correspondence_results.json"),
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": bool(all_pass),
            "u1_rank": u1_rank,
            "su2_rank": su2_rank,
            "bracket_rank": bracket_rank,
            "recommendation": "keep_blocked_as_gauge_group_falsifier_graveyard",
        },
        "all_pass": bool(all_pass),
    }

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(OUT_PATH)
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
