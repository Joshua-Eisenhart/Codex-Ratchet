#!/usr/bin/env python3
"""Finite Clifford/Hopf geometry closure candidate.

The parent Hopf/torus lego has geomstats-backed S3/S2/Hopf checks and the
operator/geometry matrix has Clifford-backed compatibility routing. This packet
asks one bounded closure question: can Clifford Cl(3) carry the Hopf S2 image
as a rotor-stable finite geometry witness while simple counterfeit projections
fail?

This is lego-stage evidence only. It does not admit QIT, GStack, axes, bridge,
or nonclassical claims.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

import geomstats.backend as gs
from clifford import Cl
from geomstats.geometry.hypersphere import Hypersphere

try:
    import sympy as sp
except Exception:  # pragma: no cover - optional support surface
    sp = None

from receipt_boundary import apply_default_receipt_boundary


SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
PARENT_RESULT_NAMES = [
    "foundation_hopf_torus_geomstats_clifford_results.json",
    "operator_geometry_compatibility_results.json",
]
OUT_PATH = RESULTS_DIR / "clifford_hopf_geometry_closure_results.json"
EPS = 1e-9

classification = "classical_baseline"
divergence_log = [
    "Finite Clifford/Hopf closure controls stay lego-stage only and explicitly block QIT, GStack, axis, bridge, and nonclassical promotion."
]

TOOL_MANIFEST = {
    "clifford": {"tried": True, "used": True, "reason": "load-bearing Cl(3) vector, bivector, and rotor checks"},
    "geomstats": {"tried": True, "used": True, "reason": "load-bearing S2 membership and geodesic distance cross-checks"},
    "numpy": {"tried": True, "used": True, "reason": "load-bearing finite spinor/Hopf sample grid and numeric controls"},
    "sympy": {"tried": sp is not None, "used": sp is not None, "reason": "supportive exact rotor identity check when available"},
    "pytorch": {"tried": False, "used": False, "reason": "not needed; no differentiable tensor check in this packet"},
    "pyg": {"tried": False, "used": False, "reason": "not needed; no message-passing graph"},
    "z3": {"tried": False, "used": False, "reason": "not needed; finite numeric/symbolic Clifford checks suffice"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "scipy": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
    "qutip": {"tried": False, "used": False, "reason": "not needed"},
    "qiskit": {"tried": False, "used": False, "reason": "not needed"},
}
TOOL_INTEGRATION_DEPTH = {
    "clifford": "load_bearing",
    "geomstats": "load_bearing",
    "numpy": "load_bearing",
    "sympy": "supportive" if sp is not None else None,
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "scipy": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
    "qutip": None,
    "qiskit": None,
}

LAYOUT, BLADES = Cl(3, 0)
E1, E2, E3 = BLADES["e1"], BLADES["e2"], BLADES["e3"]
E12 = E1 ^ E2
I3 = E1 * E2 * E3
S2 = Hypersphere(dim=2)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def parent_receipts() -> list[dict]:
    rows = []
    for name in PARENT_RESULT_NAMES:
        path = RESULTS_DIR / name
        payload = read_json(path) if path.exists() else {}
        rows.append(
            {
                "name": name,
                "path": str(path),
                "exists": path.exists(),
                "classification": payload.get("classification"),
                "all_pass": bool(payload.get("all_pass") or payload.get("summary", {}).get("all_pass")),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None,
            }
        )
    return rows


def normalized_spinor(eta: float, alpha: float, beta: float) -> np.ndarray:
    return np.array(
        [
            math.cos(eta) * np.exp(1j * alpha),
            math.sin(eta) * np.exp(1j * beta),
        ],
        dtype=np.complex128,
    )


def hopf_map(spinor: np.ndarray) -> np.ndarray:
    z1, z2 = spinor
    vec = np.array(
        [
            2.0 * np.real(z1 * np.conjugate(z2)),
            2.0 * np.imag(z1 * np.conjugate(z2)),
            np.abs(z1) ** 2 - np.abs(z2) ** 2,
        ],
        dtype=float,
    )
    return vec / np.linalg.norm(vec)


def cl_vector(vec: np.ndarray):
    return float(vec[0]) * E1 + float(vec[1]) * E2 + float(vec[2]) * E3


def mv_norm(mv) -> float:
    return float(np.sqrt(np.sum(np.asarray(mv.value, dtype=float) ** 2)))


def vector_components(mv) -> np.ndarray:
    return np.array([float(mv[E1]), float(mv[E2]), float(mv[E3])], dtype=float)


def rotor_z(delta: float):
    return math.cos(delta / 2.0) - math.sin(delta / 2.0) * E12


def rotate_z(vec: np.ndarray, delta: float) -> np.ndarray:
    rotor = rotor_z(delta)
    rotated = rotor * cl_vector(vec) * ~rotor
    return vector_components(rotated)


def cl_norm_squared(vec: np.ndarray) -> float:
    return float((cl_vector(vec) * cl_vector(vec))[()])


def bivector_area(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    biv = cl_vector(vec_a) ^ cl_vector(vec_b)
    return math.sqrt(max(float((biv * ~biv)[()]), 0.0))


def geodesic_distance(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    return float(S2.metric.dist(gs.array(vec_a), gs.array(vec_b)))


def sympy_rotor_identity() -> dict:
    if sp is None:
        return {"available": False, "pass": True}
    d, x, y = sp.symbols("d x y", real=True)
    x_rot = sp.cos(d) * x - sp.sin(d) * y
    y_rot = sp.sin(d) * x + sp.cos(d) * y
    norm_residual = sp.simplify((x_rot**2 + y_rot**2) - (x**2 + y**2))
    return {
        "available": True,
        "identity": "z-axis rotor preserves xy norm",
        "norm_residual": str(norm_residual),
        "pass": norm_residual == 0,
    }


def clifford_algebra_checks() -> dict:
    multivector = 1.0 + 2.0 * E1 - 0.5 * E2 + 0.25 * E3 + 1.7 * E12 - 0.8 * (E2 ^ E3) + 0.3 * I3
    grade_sum = multivector(0) + multivector(1) + multivector(2) + multivector(3)
    grade_residual = mv_norm(multivector - grade_sum)
    a = cl_vector(np.array([0.3, 0.5, 0.7]))
    b = cl_vector(np.array([-0.2, 0.4, 0.1]))
    c = cl_vector(np.array([0.6, -0.3, 0.2]))
    associativity_residual = mv_norm((a * b) * c - a * (b * c))
    rotor = rotor_z(math.pi / 3.0)
    unit_residual = mv_norm(rotor * ~rotor - 1.0)
    v = cl_vector(np.array([0.4, 0.2, 0.89]) / np.linalg.norm([0.4, 0.2, 0.89]))
    double_cover_residual = mv_norm(rotor * v * ~rotor - (-rotor) * v * ~(-rotor))
    full_turn = rotor_z(2.0 * math.pi)
    full_turn_action_residual = mv_norm(full_turn * v * ~full_turn - v)
    return {
        "grade_decomposition_residual": grade_residual,
        "geometric_product_associativity_residual": associativity_residual,
        "unit_rotor_residual": unit_residual,
        "spinor_double_cover_residual": double_cover_residual,
        "full_turn_rotor_scalar": float(full_turn[()]),
        "full_turn_action_residual": full_turn_action_residual,
        "pseudoscalar_square": float((I3 * I3)[()]),
        "pass": (
            grade_residual < 1e-12
            and associativity_residual < 1e-12
            and unit_residual < 1e-12
            and double_cover_residual < 1e-12
            and abs(float(full_turn[()]) + 1.0) < 1e-12
            and full_turn_action_residual < 1e-12
            and abs(float((I3 * I3)[()]) + 1.0) < 1e-12
        ),
    }


def main() -> int:
    parents = parent_receipts()
    samples = [
        (math.pi / 6.0, 0.10, 0.70, math.pi / 9.0),
        (math.pi / 4.0, 0.40, -0.20, math.pi / 7.0),
        (math.pi / 3.0, -0.30, 0.90, -math.pi / 8.0),
    ]
    rows = []
    for eta, alpha, beta, delta in samples:
        base = hopf_map(normalized_spinor(eta, alpha, beta))
        shifted = hopf_map(normalized_spinor(eta, alpha + delta, beta))
        rotated = rotate_z(base, delta)
        wrong_rotated = rotate_z(base, -delta)
        rows.append(
            {
                "eta": eta,
                "alpha": alpha,
                "beta": beta,
                "delta": delta,
                "base": base.tolist(),
                "shifted": shifted.tolist(),
                "clifford_rotated": rotated.tolist(),
                "wrong_sign_rotated": wrong_rotated.tolist(),
                "norm_squared": cl_norm_squared(base),
                "rotor_error": float(np.linalg.norm(rotated - shifted)),
                "wrong_rotor_error": float(np.linalg.norm(wrong_rotated - shifted)),
                "geomstats_distance_base_shifted": geodesic_distance(base, shifted),
                "bivector_area_base_shifted": bivector_area(base, shifted),
            }
        )

    phase_blind_a = normalized_spinor(math.pi / 4.0, 0.0, 0.0)
    phase_blind_b = normalized_spinor(math.pi / 4.0, math.pi / 3.0, 0.0)
    probability_projection_a = np.array([abs(phase_blind_a[0]) ** 2, abs(phase_blind_a[1]) ** 2])
    probability_projection_b = np.array([abs(phase_blind_b[0]) ** 2, abs(phase_blind_b[1]) ** 2])
    hopf_a = hopf_map(phase_blind_a)
    hopf_b = hopf_map(phase_blind_b)
    endpoint = hopf_map(normalized_spinor(1e-6, 0.0, math.pi / 3.0))
    endpoint_shifted = hopf_map(normalized_spinor(1e-6, math.pi / 2.0, math.pi / 3.0))
    nonunit = np.array([1.0, 1.0, 1.0])

    positive = {
        "parents_exist_and_pass": {
            "parents": parents,
            "pass": all(row["exists"] and row["all_pass"] for row in parents),
        },
        "native_clifford_algebra_checks": clifford_algebra_checks(),
        "clifford_vectors_preserve_hopf_unit_norm": {
            "norm_rows": [{"norm_squared": row["norm_squared"]} for row in rows],
            "pass": all(abs(row["norm_squared"] - 1.0) < 1e-9 for row in rows),
        },
        "clifford_z_rotor_matches_hopf_relative_phase_shift": {
            "rotor_errors": [row["rotor_error"] for row in rows],
            "pass": all(row["rotor_error"] < 1e-8 for row in rows),
        },
        "geomstats_and_clifford_detect_same_nontrivial_phase_motion": {
            "distance_area_rows": [
                {
                    "geomstats_distance": row["geomstats_distance_base_shifted"],
                    "bivector_area": row["bivector_area_base_shifted"],
                }
                for row in rows
            ],
            "pass": all(
                row["geomstats_distance_base_shifted"] > 0.05 and row["bivector_area_base_shifted"] > 0.05
                for row in rows
            ),
        },
        "sympy_supports_rotor_norm_identity": sympy_rotor_identity(),
    }
    negative = {
        "geometric_product_is_noncommutative_for_nonparallel_blades": {
            "commutator_norm": mv_norm(E1 * E2 - E2 * E1),
            "pass": mv_norm(E1 * E2 - E2 * E1) > 1e-9,
        },
        "grade1_blades_are_not_closed_under_product": {
            "grade1_norm_of_e1e2": mv_norm((E1 * E2)(1)),
            "grade2_norm_of_e1e2": mv_norm((E1 * E2)(2)),
            "pass": mv_norm((E1 * E2)(1)) < 1e-12 and mv_norm((E1 * E2)(2)) > 0.9,
        },
        "nonunit_rotor_counterfeit_fails_unitarity": {
            "candidate_scalar_norm": float(((1.0 + 2.0 * E12) * ~(1.0 + 2.0 * E12))[()]),
            "pass": abs(float(((1.0 + 2.0 * E12) * ~(1.0 + 2.0 * E12))[()]) - 1.0) > 0.1,
        },
        "phase_blind_probability_projection_fails_relative_phase": {
            "probability_projection_equal": bool(np.allclose(probability_projection_a, probability_projection_b, atol=1e-12)),
            "hopf_vector_distance": float(np.linalg.norm(hopf_a - hopf_b)),
            "pass": bool(np.allclose(probability_projection_a, probability_projection_b, atol=1e-12))
            and float(np.linalg.norm(hopf_a - hopf_b)) > 0.5,
        },
        "wrong_rotor_sign_fails_hopf_shift": {
            "wrong_rotor_errors": [row["wrong_rotor_error"] for row in rows],
            "pass": all(row["wrong_rotor_error"] > 0.2 for row in rows),
        },
        "nonunit_counterfeit_fails_unit_norm": {
            "nonunit_norm_squared": cl_norm_squared(nonunit),
            "pass": abs(cl_norm_squared(nonunit) - 1.0) > 1.0,
        },
    }
    boundary = {
        "finite_sample_only": {"sample_count": len(rows), "pass": len(rows) == 3},
        "degenerate_eta_limit_has_no_usable_phase_circle": {
            "endpoint_distance": float(np.linalg.norm(endpoint - endpoint_shifted)),
            "pass": float(np.linalg.norm(endpoint - endpoint_shifted)) < 1e-5,
        },
        "not_admission_or_promotion": {
            "classification": "classical_baseline",
            "promotion_allowed": False,
            "pass": True,
        },
        "no_qit_gstack_axis_bridge_or_nonclassical_promotion": {
            "claim_ceiling": "finite Clifford/Hopf geometry closure candidate only",
            "pass": True,
        },
    }

    all_pass = all(item["pass"] for group in (positive, negative, boundary) for item in group.values())
    result = {
        "name": "clifford_hopf_geometry_closure",
        "classification": "classical_baseline",
        "classification_note": "Finite Clifford/Hopf geometry closure candidate; lego-stage evidence only.",
        "generated_at": datetime.now(UTC).isoformat(),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "parents": parents,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "closure_candidate": all_pass,
            "promotion_allowed": False,
            "sample_count": len(rows),
            "max_rotor_error": max(row["rotor_error"] for row in rows),
            "min_geomstats_distance": min(row["geomstats_distance_base_shifted"] for row in rows),
            "scope_note": "Clifford rotor/Hopf geometry compatibility only; no stage promotion.",
        },
        "divergence_log": (
            "Clifford Cl(3) rotor action matches finite Hopf relative-phase motion while "
            "phase-blind, wrong-rotor, nonunit, and degenerate-limit controls fail."
        ),
        "all_pass": all_pass,
    }
    result = apply_default_receipt_boundary(
        result,
        source_name="sim_clifford_hopf_geometry_closure",
        target="Use as bounded Clifford/Hopf geometry closure-candidate evidence before broader assembly.",
    )
    result["promotion_condition"] = "Requires downstream assembly audit and explicit stage-gate admission."
    result["blocked_until"] = "Clifford/Hopf assembly audit and stage-gate admission"
    OUT_PATH.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Results written to {OUT_PATH}")
    print(f"ALL PASS: {all_pass}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
