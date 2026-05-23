#!/usr/bin/env python3
"""e3nn Hopf base-loop SO3 equivariance baseline."""

from __future__ import annotations

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import json
import math
from pathlib import Path

import torch
from e3nn import o3
from receipt_boundary import apply_default_receipt_boundary


NAME = "e3nn_hopf_base_loop_so3_equivariance"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "e3nn": {
        "tried": True,
        "used": True,
        "reason": "o3.spherical_harmonics, matrix_to_angles, and wigner_D check SO(3) equivariance of l=1 readouts on projected Hopf base-loop samples",
    },
    "torch": {
        "tried": True,
        "used": True,
        "reason": "tensor arithmetic for Hopf base-loop samples, rotations, and max-error readouts",
    },
}
TOOL_INTEGRATION_DEPTH = {"e3nn": "load_bearing", "torch": "supportive"}


def hopf_base_loop(theta: float, samples: int) -> torch.Tensor:
    points = []
    for phi in torch.linspace(0.0, 2.0 * math.pi, samples + 1, dtype=torch.float64)[:-1]:
        x = math.sin(theta) * torch.cos(phi)
        y = math.sin(theta) * torch.sin(phi)
        z = torch.tensor(math.cos(theta), dtype=torch.float64)
        points.append(torch.stack([x, y, z]))
    return torch.stack(points, dim=0)


def spherical_l1(points: torch.Tensor) -> torch.Tensor:
    return o3.spherical_harmonics(1, points, normalize=True, normalization="component")


def deterministic_rotation() -> torch.Tensor:
    alpha = torch.tensor(0.4, dtype=torch.float64)
    beta = torch.tensor(0.7, dtype=torch.float64)
    gamma = torch.tensor(-0.2, dtype=torch.float64)
    return o3.angles_to_matrix(alpha, beta, gamma)


def run_positive() -> dict[str, object]:
    points = hopf_base_loop(theta=math.pi / 3.0, samples=32)
    rotation = deterministic_rotation()
    rotated_points = points @ rotation.T
    alpha, beta, gamma = o3.matrix_to_angles(rotation)
    d_matrix = o3.wigner_D(1, alpha, beta, gamma)
    y_original = spherical_l1(points)
    y_rotated_direct = spherical_l1(rotated_points)
    y_rotated_from_irrep = y_original @ d_matrix.T
    max_equivariance_error = float(torch.max(torch.abs(y_rotated_direct - y_rotated_from_irrep)))
    return {
        "sample_count": int(points.shape[0]),
        "rotation_det": float(torch.linalg.det(rotation)),
        "max_equivariance_error": max_equivariance_error,
        "survives_l1_so3_equivariance": bool(
            abs(float(torch.linalg.det(rotation)) - 1.0) < 1e-10
            and max_equivariance_error < 1e-5
        ),
    }


def run_graveyards() -> dict[str, object]:
    points = hopf_base_loop(theta=math.pi / 3.0, samples=32)
    rotation = deterministic_rotation()
    rotated_points = points @ rotation.T
    alpha, beta, gamma = o3.matrix_to_angles(rotation)
    d_matrix = o3.wigner_D(1, alpha, beta, gamma)
    y_original = spherical_l1(points)
    y_rotated_direct = spherical_l1(rotated_points)
    wrong_identity_error = float(torch.max(torch.abs(y_rotated_direct - y_original)))
    wrong_transpose_error = float(torch.max(torch.abs(y_rotated_direct - y_original @ d_matrix)))
    pole_points = hopf_base_loop(theta=0.0, samples=32)
    pole_span = int(torch.linalg.matrix_rank(pole_points - pole_points.mean(dim=0, keepdim=True), tol=1e-10))
    no_rotation = torch.eye(3, dtype=torch.float64)
    no_rotation_angles = o3.matrix_to_angles(no_rotation)
    no_rotation_d = o3.wigner_D(1, *no_rotation_angles)
    no_rotation_error = float(torch.max(torch.abs(spherical_l1(points) - spherical_l1(points) @ no_rotation_d.T)))
    return {
        "ignoring_rotation_breaks_equivariance": {
            "max_error": wrong_identity_error,
            "passed": wrong_identity_error > 1e-3,
        },
        "wrong_irrep_side_breaks_equivariance": {
            "max_error": wrong_transpose_error,
            "passed": wrong_transpose_error > 1e-3,
        },
        "pole_base_loop_collapses_path_span": {
            "rank_after_centering": pole_span,
            "passed": pole_span == 0,
        },
        "identity_rotation_has_zero_equivariance_error": {
            "max_error": no_rotation_error,
            "passed": no_rotation_error < 1e-10,
        },
        "nonorthogonal_scaling_is_not_so3": {
            "scaled_det": float(torch.linalg.det(torch.diag(torch.tensor([2.0, 1.0, 1.0], dtype=torch.float64)))),
            "passed": abs(float(torch.linalg.det(torch.diag(torch.tensor([2.0, 1.0, 1.0], dtype=torch.float64)))) - 1.0)
            > 1e-6,
        },
    }


def main() -> int:
    positive = run_positive()
    graveyards = run_graveyards()
    all_pass = bool(
        positive["survives_l1_so3_equivariance"]
        and all(row["passed"] for row in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "claim_ceiling": (
            "e3nn l=1 spherical-harmonic SO(3) equivariance baseline on projected Hopf base-loop samples only; "
            "no physical distinguishability, QIT, GStack, axis, bridge, nonclassical, flux, Pauli shortcut, "
            "target-system, or full geometric-constraint-manifold admission"
        ),
        "next_lego_target": "hopf_base_loop_so3_readout_equivariance_baseline",
        "promotion_condition": (
            "May only support later carrier-geometry planning after independent Hopf/Weyl density and topology "
            "receipts reproduce compatible loop readouts with physical graveyards."
        ),
        "demotion_condition": (
            "Demote if l=1 spherical harmonics fail the SO(3) equivariance check, if wrong-action controls do not "
            "fail, or if pole/no-rotation/scaling controls do not classify correctly."
        ),
        "blocked_until": "blocked from target-system claims until fuller Hopf/Weyl carrier topology and physical-evolution fixtures exist",
        "out_of_scope": [
            "No full geometric-constraint-manifold implementation.",
            "No flux representation or Pauli shortcut.",
            "No Lindblad evolution, Hamiltonian dynamics, or target-system admission.",
            "No QIT, GStack, axis, bridge, or nonclassical admission.",
        ],
        "divergence_log": (
            "This baseline checks SO(3)-equivariance of a projected base-loop readout. It does not prove "
            "inner/outer loop independence or full Weyl-spinor carrier dynamics."
        ),
        "operation_sequence": [
            "sample a projected Hopf base latitude loop on S2",
            "compute e3nn l=1 spherical harmonics for the samples",
            "rotate the base-loop samples by a deterministic SO(3) matrix",
            "compare direct rotated spherical harmonics with Wigner-D-transformed original harmonics",
            "run ignored-rotation, wrong-side, pole-loop, identity-rotation, and non-SO3 scaling graveyards",
        ],
        "carrier_topology": "projected Hopf base-loop samples on S2 with SO(3) action on ambient coordinates",
        "observable": "l=1 spherical-harmonic equivariance error, rotation determinant, loop span, and wrong-action errors",
        "pass_fail_predicate": (
            "deterministic rotation has determinant one, l=1 readout equivariance error is below tolerance, "
            "wrong-action controls fail, and degenerate/identity/non-SO3 controls classify as expected"
        ),
        "graveyards": [
            "ignoring rotation breaks equivariance",
            "wrong irrep side breaks equivariance",
            "pole base loop collapses path span",
            "identity rotation has zero equivariance error",
            "nonorthogonal scaling is not SO3",
        ],
        "baselines": [
            "Geomstats Hopf inner-outer sphere-distance fixture",
            "SciPy Hopf horizontal-lift chi-shift fixture",
            "SymPy Hopf loop holonomy area-dependence fixture",
            "e3nn spherical harmonics equivariance micro fixture",
        ],
        "alternative_formulations": [
            "geomstats SO(3) distance/log/exp cross-check",
            "Clifford rotor action on projected base-loop vectors",
            "higher-l spherical harmonic equivariance fixture",
            "Weyl spinor density-object evolution under SU(2) lift",
        ],
        "exact_tool_function_needs": {
            "e3nn": ["o3.spherical_harmonics", "o3.matrix_to_angles", "o3.wigner_D", "o3.angles_to_matrix"],
            "torch": ["linspace", "stack", "linalg.det", "linalg.matrix_rank", "max", "abs"],
        },
        "lego_or_coupling_target": "hopf_base_loop_so3_readout_equivariance_baseline",
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
