#!/usr/bin/env python3
"""Clifford rotor readout for a Hopf-style outer loop."""

from __future__ import annotations

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import json
import math
from pathlib import Path

import numpy as np
from receipt_boundary import apply_default_receipt_boundary


NAME = "clifford_hopf_outer_rotation_readout"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "builds Cl(3) blades, exponentiates a unit bivector rotor, and transports vector readouts by rotor sandwich",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "samples loop coordinates and compares coefficient arrays for readout metrics",
    },
}
TOOL_INTEGRATION_DEPTH = {"clifford": "load_bearing", "numpy": "supportive"}


try:
    from clifford import Cl
except Exception as exc:  # pragma: no cover - import failure is receipt data.
    Cl = None
    CLIFFORD_IMPORT_ERROR = repr(exc)
else:
    CLIFFORD_IMPORT_ERROR = None


def setup_cl3():
    if Cl is None:
        raise RuntimeError(f"clifford import failed: {CLIFFORD_IMPORT_ERROR}")
    layout, blades = Cl(3)
    return layout, blades, blades["e1"], blades["e2"], blades["e3"]


def rotor_exp(bivector, angle: float):
    return (-bivector * (angle / 2.0)).exp()


def vector_coeffs(vector, e1, e2, e3) -> np.ndarray:
    return np.array(
        [
            float((vector | e1).value[0]),
            float((vector | e2).value[0]),
            float((vector | e3).value[0]),
        ],
        dtype=float,
    )


def expected_bloch(theta: float, phi: float) -> np.ndarray:
    return np.array(
        [
            math.sin(theta) * math.cos(phi),
            math.sin(theta) * math.sin(phi),
            math.cos(theta),
        ],
        dtype=float,
    )


def path_metrics(points: list[np.ndarray]) -> dict[str, float | list[float]]:
    step_lengths = [
        float(np.linalg.norm(points[idx + 1] - points[idx]))
        for idx in range(len(points) - 1)
    ]
    displacements = [float(np.linalg.norm(point - points[0])) for point in points]
    return {
        "ambient_path_length": float(sum(step_lengths)),
        "max_displacement_from_start": float(max(displacements)),
        "start_point": [float(value) for value in points[0]],
        "end_point": [float(value) for value in points[-1]],
    }


def sample_outer_rotor_path(theta: float, samples: int) -> tuple[list[np.ndarray], float]:
    _, _, e1, e2, e3 = setup_cl3()
    bivector = e1 * e2
    base = math.sin(theta) * e1 + math.cos(theta) * e3
    max_error = 0.0
    points: list[np.ndarray] = []
    for phi in np.linspace(0.0, 2.0 * math.pi, samples):
        rotor = rotor_exp(bivector, float(phi))
        transported = rotor * base * (~rotor)
        got = vector_coeffs(transported, e1, e2, e3)
        expected = expected_bloch(theta, float(phi))
        max_error = max(max_error, float(np.linalg.norm(got - expected)))
        points.append(got)
    return points, max_error


def sample_inner_constant_path(theta: float, phi: float, samples: int) -> list[np.ndarray]:
    point = expected_bloch(theta, phi)
    return [point.copy() for _ in np.linspace(0.0, 2.0 * math.pi, samples)]


def candidate_survives(inner: dict[str, object], outer: dict[str, object], max_error: float) -> bool:
    return bool(
        max_error < 1e-9
        and inner["ambient_path_length"] < 1e-9
        and inner["max_displacement_from_start"] < 1e-9
        and outer["ambient_path_length"] > 5.0
        and outer["max_displacement_from_start"] > 1.0
    )


def run_positive() -> dict[str, object]:
    samples = 129
    theta = math.pi / 3.0
    inner_points = sample_inner_constant_path(theta=theta, phi=math.pi / 5.0, samples=samples)
    outer_points, max_error = sample_outer_rotor_path(theta=theta, samples=samples)
    inner = path_metrics(inner_points)
    outer = path_metrics(outer_points)
    return {
        "samples": samples,
        "theta": theta,
        "inner_loop": inner,
        "outer_loop": outer,
        "max_rotor_vs_expected_bloch_error": max_error,
        "survives_clifford_rotor_readout": candidate_survives(inner, outer, max_error),
    }


def run_graveyards() -> dict[str, object]:
    samples = 129
    theta = math.pi / 3.0
    inner_points = sample_inner_constant_path(theta=theta, phi=math.pi / 5.0, samples=samples)
    outer_points, max_error = sample_outer_rotor_path(theta=theta, samples=samples)
    pole_outer_points, pole_error = sample_outer_rotor_path(theta=0.0, samples=samples)
    inner = path_metrics(inner_points)
    outer = path_metrics(outer_points)
    pole_outer = path_metrics(pole_outer_points)
    start_end_chord = float(np.linalg.norm(np.asarray(outer["end_point"]) - np.asarray(outer["start_point"])))

    _, _, e1, e2, e3 = setup_cl3()
    wrong_bivector = 2.0 * e1 * e2
    base = math.sin(theta) * e1 + math.cos(theta) * e3
    wrong_errors: list[float] = []
    for phi in np.linspace(0.0, 2.0 * math.pi, samples):
        rotor = rotor_exp(wrong_bivector, float(phi))
        got = vector_coeffs(rotor * base * (~rotor), e1, e2, e3)
        wrong_errors.append(float(np.linalg.norm(got - expected_bloch(theta, float(phi)))))

    return {
        "both_paths_inner_collapses_distinction": {
            "candidate_passed": candidate_survives(inner, inner, max_error),
            "expected": False,
            "passed": candidate_survives(inner, inner, max_error) is False,
        },
        "both_paths_outer_collapses_distinction": {
            "candidate_passed": candidate_survives(outer, outer, max_error),
            "expected": False,
            "passed": candidate_survives(outer, outer, max_error) is False,
        },
        "outer_loop_at_pole_degenerates": {
            "ambient_path_length": pole_outer["ambient_path_length"],
            "max_rotor_vs_expected_bloch_error": pole_error,
            "expected_collapse": True,
            "passed": bool(pole_outer["ambient_path_length"] < 1e-9 and pole_error < 1e-9),
        },
        "start_end_chord_hides_closed_outer_path": {
            "start_end_chord": start_end_chord,
            "outer_ambient_path_length": outer["ambient_path_length"],
            "passed": bool(start_end_chord < 1e-9 and outer["ambient_path_length"] > 5.0),
        },
        "non_unit_bivector_breaks_expected_rotation": {
            "max_error": float(max(wrong_errors)),
            "expected_break": True,
            "passed": bool(max(wrong_errors) > 1.0),
        },
    }


def blocked_result() -> dict[str, object]:
    return {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": False,
        "pass": False,
        "blocker": f"clifford import failed: {CLIFFORD_IMPORT_ERROR}",
        "tool_manifest": {
            "clifford": {
                "tried": True,
                "used": False,
                "reason": f"import failed: {CLIFFORD_IMPORT_ERROR}",
            },
            "numpy": TOOL_MANIFEST["numpy"],
        },
        "tool_integration_depth": {"clifford": None, "numpy": "supportive"},
        "claim_ceiling": "blocked classical baseline; no geometry, QIT, GStack, axis, bridge, nonclassical, or target-system claim",
        "out_of_scope": ["no target-system claim", "no admission or promotion"],
        "promotion_allowed": False,
    }


def main() -> int:
    if Cl is None:
        results = apply_default_receipt_boundary(blocked_result(), source_name=f"sim_{NAME}")
        out_path = RESULTS_DIR / f"{NAME}_results.json"
        out_path.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
        print(f"Results written to {out_path}")
        print(f"PASS={results['pass']}  name={NAME}")
        return 1

    positive = run_positive()
    graveyards = run_graveyards()
    all_pass = bool(
        positive["survives_clifford_rotor_readout"]
        and all(row["passed"] for row in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "Clifford Cl(3) rotor readout baseline for a declared projected Hopf-style outer path only; no physical "
            "inner/outer loop independence, no full S3 bundle, no QIT, GStack, axis, bridge, nonclassical, "
            "target-system, or full geometric-constraint-manifold admission"
        ),
        "next_lego_target": "inner_outer_hopf_weyl_loop_geometry_fit",
        "promotion_condition": (
            "May only support later carrier-geometry planning after independent full-bundle and operator-evolution "
            "receipts reproduce compatible projected-path readouts with physical graveyards."
        ),
        "demotion_condition": (
            "Demote if Clifford rotor transport fails to match the projected Bloch latitude, if the inner readout "
            "moves, or if same-path/pole/start-end/non-unit-bivector graveyards do not collapse."
        ),
        "blocked_until": "blocked from target-system claims until fuller Hopf/Weyl carrier topology and physical-evolution fixtures exist",
        "out_of_scope": [
            "No full Hopf bundle implementation.",
            "No nested Hopf tori, geometric-constraint-manifold, or flux representation.",
            "No Lindblad evolution, Hamiltonian dynamics, or target-system admission.",
            "No QIT, GStack, axis, bridge, or nonclassical admission.",
        ],
        "divergence_log": (
            "This is a Clifford rotor baseline on projected S2/Bloch readouts. It does not simulate physical "
            "inner/outer loop independence, the full carrier bundle, nested tori, flux, or target geometric "
            "constraint manifold."
        ),
        "operation_sequence": [
            "build Cl(3) blades e1,e2,e3 and the unit bivector e1e2",
            "encode a nondegenerate projected Bloch point as sin(theta)e1 + cos(theta)e3",
            "sample an inner readout path as a constant vector",
            "sample an outer readout path by rotor sandwich exp(-e1e2 phi/2) v exp(e1e2 phi/2)",
            "compare transported coefficients to the declared latitude-circle readout",
            "run same-path, pole, start-end-chord, and non-unit-bivector graveyards",
        ],
        "carrier_topology": "projected S2/Bloch readout of Hopf-style inner constant path and outer base-angle path; no full S3 bundle object",
        "observable": "Clifford vector coefficients, ambient path length, displacement from start, and rotor-vs-latitude coefficient error",
        "pass_fail_predicate": (
            "inner readout path is stationary, outer rotor path has nonzero path length away from the pole, rotor "
            "coefficients match the declared latitude readout, and adjacent graveyards collapse"
        ),
        "graveyards": [
            "both paths forced to inner loop collapse distinction",
            "both paths forced to outer loop collapse distinction",
            "outer loop at pole degenerates",
            "start-end chord hides closed outer path",
            "non-unit bivector breaks expected projected rotation",
        ],
        "baselines": [
            "sampled NumPy Hopf path metric fixture",
            "symbolic SymPy Hopf density derivative fixture",
            "QuTiP/Qiskit/PyTorch density readout fixtures",
            "Geomstats projected S2 intrinsic-distance fixture",
        ],
        "alternative_formulations": [
            "full S3/S2 bundle fixture",
            "nested Hopf-torus carrier fixture",
            "operator-evolution manifold path fixture",
            "Clifford bundle connection transport fixture",
        ],
        "exact_tool_function_needs": {
            "clifford": ["Cl(3)", "MultiVector.exp", "rotor sandwich R*v*~R", "inner-product coefficient extraction"],
            "numpy": ["linspace", "array", "linalg.norm"],
        },
        "lego_or_coupling_target": "inner_outer_hopf_weyl_loop_geometry_fit",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyards_detail": graveyards,
        "promotion_allowed": False,
        "pass": all_pass,
    }
    results = apply_default_receipt_boundary(results, source_name=f"sim_{NAME}")
    out_path = RESULTS_DIR / f"{NAME}_results.json"
    out_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"PASS={results['pass']}  name={NAME}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
