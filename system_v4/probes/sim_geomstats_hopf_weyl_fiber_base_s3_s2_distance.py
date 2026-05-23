#!/usr/bin/env python3
"""Geomstats S3 carrier and S2 projection distances for Hopf/Weyl fiber-base loops."""

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
from geomstats.geometry.hypersphere import Hypersphere
from receipt_boundary import apply_default_receipt_boundary


NAME = "geomstats_hopf_weyl_fiber_base_s3_s2_distance"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": "computes intrinsic S3 carrier distances and S2 projection distances for declared Hopf/Weyl fiber-base loop samples",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "constructs sampled Hopf-coordinate carrier arrays and projection readouts",
    },
}
TOOL_INTEGRATION_DEPTH = {"geomstats": "load_bearing", "numpy": "supportive"}

S3 = Hypersphere(dim=3)
S2 = Hypersphere(dim=2)


def spinor_complex(theta: float, phi: float, chi: float, sheet_orientation: int) -> np.ndarray:
    if sheet_orientation not in (-1, 1):
        raise ValueError("sheet_orientation must be -1 or +1")
    signed_phi = float(sheet_orientation) * phi
    return np.asarray(
        [
            math.cos(theta / 2.0) * np.exp(0.5j * (chi + signed_phi)),
            math.sin(theta / 2.0) * np.exp(0.5j * (chi - signed_phi)),
        ],
        dtype=np.complex128,
    )


def spinor_s3(theta: float, phi: float, chi: float, sheet_orientation: int) -> np.ndarray:
    psi = spinor_complex(theta, phi, chi, sheet_orientation)
    point = np.asarray([psi[0].real, psi[0].imag, psi[1].real, psi[1].imag], dtype=float)
    norm = float(np.linalg.norm(point))
    if norm <= 0.0:
        raise ValueError("zero carrier point")
    return point / norm


def bloch_s2(theta: float, phi: float, sheet_orientation: int) -> np.ndarray:
    signed_phi = float(sheet_orientation) * phi
    return np.asarray(
        [
            math.sin(theta) * math.cos(signed_phi),
            math.sin(theta) * math.sin(signed_phi),
            math.cos(theta),
        ],
        dtype=float,
    )


def fiber_loop(theta: float, phi: float, sheet_orientation: int, samples: int) -> list[tuple[np.ndarray, np.ndarray]]:
    return [
        (spinor_s3(theta, phi, float(chi), sheet_orientation), bloch_s2(theta, phi, sheet_orientation))
        for chi in np.linspace(0.0, 2.0 * math.pi, samples)
    ]


def base_loop(theta: float, chi: float, sheet_orientation: int, samples: int) -> list[tuple[np.ndarray, np.ndarray]]:
    return [
        (spinor_s3(theta, float(phi), chi, sheet_orientation), bloch_s2(theta, float(phi), sheet_orientation))
        for phi in np.linspace(0.0, 2.0 * math.pi, samples)
    ]


def path_metrics(path: list[tuple[np.ndarray, np.ndarray]]) -> dict[str, object]:
    s3_points = [row[0] for row in path]
    s2_points = [row[1] for row in path]
    s3_steps = [float(S3.metric.dist(s3_points[idx], s3_points[idx + 1])) for idx in range(len(s3_points) - 1)]
    s2_steps = [float(S2.metric.dist(s2_points[idx], s2_points[idx + 1])) for idx in range(len(s2_points) - 1)]
    s3_displacements = [float(S3.metric.dist(s3_points[0], point)) for point in s3_points]
    s2_displacements = [float(S2.metric.dist(s2_points[0], point)) for point in s2_points]
    return {
        "s3_path_length": float(sum(s3_steps)),
        "s2_path_length": float(sum(s2_steps)),
        "s3_max_displacement": float(max(s3_displacements)),
        "s2_max_displacement": float(max(s2_displacements)),
        "s3_start_end_distance": float(S3.metric.dist(s3_points[0], s3_points[-1])),
        "s2_start_end_distance": float(S2.metric.dist(s2_points[0], s2_points[-1])),
        "s3_start": [float(value) for value in s3_points[0]],
        "s3_end": [float(value) for value in s3_points[-1]],
        "s2_start": [float(value) for value in s2_points[0]],
        "s2_end": [float(value) for value in s2_points[-1]],
    }


def survives(fiber: dict[str, object], base: dict[str, object]) -> bool:
    return bool(
        fiber["s3_path_length"] > 2.9
        and fiber["s2_path_length"] < 1e-9
        and fiber["s2_max_displacement"] < 1e-9
        and base["s3_path_length"] > 2.9
        and base["s2_path_length"] > 5.0
        and base["s2_max_displacement"] > 1.0
        and fiber["s3_start_end_distance"] > 3.0
        and base["s3_start_end_distance"] > 3.0
        and fiber["s2_start_end_distance"] < 1e-9
        and base["s2_start_end_distance"] < 1e-9
    )


def run_positive() -> dict[str, object]:
    theta = math.pi / 3.0
    phi = math.pi / 5.0
    chi = math.pi / 7.0
    samples = 129
    fiber = path_metrics(fiber_loop(theta, phi, sheet_orientation=1, samples=samples))
    base = path_metrics(base_loop(theta, chi, sheet_orientation=1, samples=samples))
    reversed_base = path_metrics(base_loop(theta, chi, sheet_orientation=-1, samples=samples))
    return {
        "theta": theta,
        "phi": phi,
        "chi": chi,
        "samples": samples,
        "fiber_loop": fiber,
        "base_loop": base,
        "reversed_sheet_base_loop": reversed_base,
        "survives_geomstats_s3_s2_distance": survives(fiber, base),
    }


def run_graveyards() -> dict[str, object]:
    theta = math.pi / 3.0
    phi = math.pi / 5.0
    chi = math.pi / 7.0
    samples = 129
    fiber = path_metrics(fiber_loop(theta, phi, sheet_orientation=1, samples=samples))
    base = path_metrics(base_loop(theta, chi, sheet_orientation=1, samples=samples))
    pole_base = path_metrics(base_loop(0.0, chi, sheet_orientation=1, samples=samples))
    reversed_base = path_metrics(base_loop(theta, chi, sheet_orientation=-1, samples=samples))
    s2_only_fiber = {
        "s2_path_length": fiber["s2_path_length"],
        "s2_max_displacement": fiber["s2_max_displacement"],
    }
    return {
        "projection_to_s2_hides_fiber_carrier_motion": {
            "fiber_s3_path_length": fiber["s3_path_length"],
            "fiber_s2_path_length": fiber["s2_path_length"],
            "passed": bool(fiber["s3_path_length"] > 2.9 and fiber["s2_path_length"] < 1e-9),
        },
        "base_loop_at_pole_collapses_projection_motion": {
            "pole_base_s3_path_length": pole_base["s3_path_length"],
            "pole_base_s2_path_length": pole_base["s2_path_length"],
            "passed": bool(pole_base["s3_path_length"] > 2.9 and pole_base["s2_path_length"] < 1e-9),
        },
        "forcing_both_paths_to_fiber_collapses_candidate": {
            "candidate_passed": survives(fiber, fiber),
            "passed": survives(fiber, fiber) is False,
        },
        "forcing_both_paths_to_base_collapses_candidate": {
            "candidate_passed": survives(base, base),
            "passed": survives(base, base) is False,
        },
        "sheet_reversal_preserves_metric_lengths_but_reverses_sample_orientation": {
            "positive_base_s2_path_length": base["s2_path_length"],
            "negative_base_s2_path_length": reversed_base["s2_path_length"],
            "passed": bool(abs(base["s2_path_length"] - reversed_base["s2_path_length"]) < 1e-9),
        },
        "s2_only_readout_is_insufficient_for_fiber_path": {
            "s2_only_fiber": s2_only_fiber,
            "has_s3_carrier": False,
            "passed": bool(s2_only_fiber["s2_path_length"] < 1e-9),
        },
    }


def main() -> int:
    positive = run_positive()
    graveyards = run_graveyards()
    all_pass = bool(
        positive["survives_geomstats_s3_s2_distance"]
        and all(row["passed"] for row in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "Geomstats S3-carrier and S2-projection distance baseline for declared Hopf/Weyl fiber-base loop samples only; "
            "this is local metric geometry, not full nested Hopf-torus dynamics; no physical fiber/base independence proof, "
            "no flux, no QIT, GStack, axis, bridge, nonclassical, target-system, or full geometric-constraint-manifold admission"
        ),
        "next_lego_target": "hopf_weyl_carrier_loop_geometry_baseline",
        "promotion_condition": (
            "May only support later carrier-geometry planning after symbolic, object-level, topology, and physical "
            "operator-evolution receipts reproduce compatible S3/S2 fiber-base behavior with adjacent controls."
        ),
        "demotion_condition": (
            "Demote if S2 projection does not hide fiber carrier motion, if base projection motion fails away from "
            "the pole, if pole projection does not collapse, or if same-path and S2-only graveyards do not fail."
        ),
        "blocked_until": "blocked from target-system claims until fuller carrier/topology and physical-evolution fixtures exist",
        "out_of_scope": [
            "No full nested Hopf-torus manifold or geometric-constraint manifold.",
            "No flux representation or Pauli-boundary shortcut.",
            "No Lindblad, Hamiltonian, thermodynamic, or information-cycle mechanics.",
            "No QIT, GStack, axis, bridge, nonclassical, or target-system admission.",
        ],
        "divergence_log": (
            "This uses Geomstats metric distances on S3 carrier samples and S2 projection samples. It improves over "
            "S2-only projection baselines by keeping carrier motion visible, but it is still a sampled local geometry baseline."
        ),
        "operation_sequence": [
            "construct complex two-component Hopf/Weyl carrier samples from theta, phi, and chi",
            "embed each carrier as a real point on S3",
            "project each carrier sample to an S2 Bloch readout",
            "sample a fiber loop by varying chi at fixed theta and phi",
            "sample a base loop by varying phi at fixed theta and chi",
            "compute Geomstats S3 and S2 intrinsic path lengths and endpoint distances",
            "run projection-hidden, pole-collapse, same-path, sheet-reversal, and S2-only graveyards",
        ],
        "carrier_topology": "sampled Hopf-coordinate two-component carrier embedded in S3 with projected S2 Bloch readout; no full nested-torus manifold",
        "observable": "Geomstats intrinsic S3 carrier path length, S2 projection path length, maximum displacement, and endpoint distance",
        "pass_fail_predicate": (
            "fiber loop has nonzero S3 carrier length but zero S2 projection length; base loop has nonzero S3 carrier "
            "length and nonzero S2 projection length away from the pole; pole and same-path controls collapse as predicted"
        ),
        "graveyards": [
            "projection to S2 hides fiber carrier motion",
            "base loop at pole collapses projection motion",
            "forcing both paths to fiber collapses candidate",
            "forcing both paths to base collapses candidate",
            "sheet reversal preserves metric lengths but reverses sample orientation",
            "S2-only readout is insufficient for fiber path",
        ],
        "baselines": [
            "Geomstats S2 projected Hopf loop distance baseline",
            "QuTiP/Qiskit/PyTorch Hopf/Weyl fiber-base carrier transport baselines",
            "SciPy Hopf horizontal-lift chi-shift baseline",
            "SymPy Hopf loop holonomy area-dependence baseline",
        ],
        "alternative_formulations": [
            "symbolic S3 and S2 path-length identities for the same coordinates",
            "QuTiP carrier-state distance with density projection controls",
            "triangulated S3-to-S2 bundle approximation with finite-cell incidence",
            "physical operator-evolution fixture over the same carrier samples",
        ],
        "exact_tool_function_needs": {
            "geomstats": ["Hypersphere(dim=3).metric.dist", "Hypersphere(dim=2).metric.dist"],
            "numpy": ["array", "exp", "linspace", "linalg.norm"],
        },
        "lego_or_coupling_target": "hopf_weyl_carrier_loop_geometry_baseline",
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
