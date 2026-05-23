#!/usr/bin/env python3
"""e3nn SO(3) equivariance over Hopf/Weyl vertical-horizontal density readouts."""

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


NAME = "e3nn_hopf_weyl_vertical_horizontal_density_so3_equivariance"
RESULTS_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CLASSIFICATION = "classical_baseline"
TOOL_MANIFEST = {
    "e3nn": {
        "tried": True,
        "used": True,
        "reason": "o3.spherical_harmonics, matrix_to_angles, wigner_D, and angles_to_matrix check SO(3) equivariance of l=1 readouts on Hopf/Weyl vertical fiber and horizontal base-lift density paths",
    },
    "torch": {
        "tried": True,
        "used": True,
        "reason": "tensor arithmetic for sampled density readouts, rotations, rank controls, determinants, and max-error observables",
    },
}
TOOL_INTEGRATION_DEPTH = {"e3nn": "load_bearing", "torch": "supportive"}


def bloch_density_readout(theta: float, phi: torch.Tensor, sheet_orientation: int) -> torch.Tensor:
    signed_phi = float(sheet_orientation) * phi
    return torch.stack(
        [
            math.sin(theta) * torch.cos(signed_phi),
            math.sin(theta) * torch.sin(signed_phi),
            torch.full_like(phi, math.cos(theta)),
        ],
        dim=1,
    )


def vertical_fiber_density_path(theta: float, phi0: float, sheet_orientation: int, samples: int) -> torch.Tensor:
    phi = torch.full((samples,), phi0, dtype=torch.float64)
    return bloch_density_readout(theta, phi, sheet_orientation)


def horizontal_base_density_path(theta: float, phi0: float, sheet_orientation: int, samples: int) -> torch.Tensor:
    phi = torch.linspace(phi0, phi0 + 2.0 * math.pi, samples + 1, dtype=torch.float64)[:-1]
    return bloch_density_readout(theta, phi, sheet_orientation)


def spherical_l1(points: torch.Tensor) -> torch.Tensor:
    return o3.spherical_harmonics(1, points, normalize=True, normalization="component")


def deterministic_rotation() -> torch.Tensor:
    alpha = torch.tensor(0.37, dtype=torch.float64)
    beta = torch.tensor(0.61, dtype=torch.float64)
    gamma = torch.tensor(-0.29, dtype=torch.float64)
    return o3.angles_to_matrix(alpha, beta, gamma)


def centered_rank(points: torch.Tensor) -> int:
    centered = points - points.mean(dim=0, keepdim=True)
    return int(torch.linalg.matrix_rank(centered, tol=1e-10).item())


def max_pairwise_displacement(points: torch.Tensor) -> float:
    diffs = points[:, None, :] - points[None, :, :]
    return float(torch.linalg.norm(diffs, dim=2).max().item())


def equivariance_error(points: torch.Tensor, rotation: torch.Tensor) -> dict[str, float]:
    rotated_points = points @ rotation.T
    alpha, beta, gamma = o3.matrix_to_angles(rotation)
    d_matrix = o3.wigner_D(1, alpha, beta, gamma)
    y_original = spherical_l1(points)
    y_rotated_direct = spherical_l1(rotated_points)
    y_rotated_from_irrep = y_original @ d_matrix.T
    wrong_identity_error = float(torch.max(torch.abs(y_rotated_direct - y_original)).item())
    wrong_side_error = float(torch.max(torch.abs(y_rotated_direct - y_original @ d_matrix)).item())
    correct_error = float(torch.max(torch.abs(y_rotated_direct - y_rotated_from_irrep)).item())
    return {
        "correct_wigner_d_error": correct_error,
        "wrong_ignore_rotation_error": wrong_identity_error,
        "wrong_wigner_side_error": wrong_side_error,
    }


def run_positive() -> dict[str, object]:
    theta = math.pi / 3.0
    phi0 = math.pi / 5.0
    samples = 32
    rotation = deterministic_rotation()
    vertical = vertical_fiber_density_path(theta, phi0, 1, samples)
    horizontal = horizontal_base_density_path(theta, phi0, 1, samples)
    vertical_errors = equivariance_error(vertical, rotation)
    horizontal_errors = equivariance_error(horizontal, rotation)
    return {
        "theta": theta,
        "phi0": phi0,
        "samples": samples,
        "rotation_det": float(torch.linalg.det(rotation).item()),
        "vertical_fiber_density_readout": {
            "centered_rank": centered_rank(vertical),
            "max_pairwise_displacement": max_pairwise_displacement(vertical),
            "equivariance": vertical_errors,
        },
        "horizontal_base_density_readout": {
            "centered_rank": centered_rank(horizontal),
            "max_pairwise_displacement": max_pairwise_displacement(horizontal),
            "equivariance": horizontal_errors,
        },
        "density_so3_equivariance_pass": bool(
            abs(float(torch.linalg.det(rotation).item()) - 1.0) < 1e-10
            and vertical_errors["correct_wigner_d_error"] < 1e-5
            and horizontal_errors["correct_wigner_d_error"] < 1e-5
            and centered_rank(vertical) == 0
            and centered_rank(horizontal) == 2
            and max_pairwise_displacement(vertical) < 1e-10
            and max_pairwise_displacement(horizontal) > 1.0
        ),
    }


def run_graveyards() -> dict[str, object]:
    theta = math.pi / 3.0
    phi0 = math.pi / 5.0
    samples = 32
    rotation = deterministic_rotation()
    vertical = vertical_fiber_density_path(theta, phi0, 1, samples)
    horizontal = horizontal_base_density_path(theta, phi0, 1, samples)
    pole_horizontal = horizontal_base_density_path(0.0, phi0, 1, samples)
    reversed_horizontal = horizontal_base_density_path(theta, phi0, -1, samples)
    vertical_errors = equivariance_error(vertical, rotation)
    horizontal_errors = equivariance_error(horizontal, rotation)
    reversed_errors = equivariance_error(reversed_horizontal, rotation)
    identity = torch.eye(3, dtype=torch.float64)
    identity_horizontal_errors = equivariance_error(horizontal, identity)
    non_so3_scaling = torch.diag(torch.tensor([2.0, 1.0, 1.0], dtype=torch.float64))
    return {
        "vertical_fiber_density_readout_collapses": {
            "centered_rank": centered_rank(vertical),
            "max_pairwise_displacement": max_pairwise_displacement(vertical),
            "passed": centered_rank(vertical) == 0 and max_pairwise_displacement(vertical) < 1e-10,
        },
        "horizontal_base_density_readout_is_two_dimensional_loop": {
            "centered_rank": centered_rank(horizontal),
            "max_pairwise_displacement": max_pairwise_displacement(horizontal),
            "passed": centered_rank(horizontal) == 2 and max_pairwise_displacement(horizontal) > 1.0,
        },
        "ignoring_rotation_breaks_horizontal_equivariance": {
            "wrong_ignore_rotation_error": horizontal_errors["wrong_ignore_rotation_error"],
            "passed": horizontal_errors["wrong_ignore_rotation_error"] > 1e-3,
        },
        "wrong_wigner_side_breaks_horizontal_equivariance": {
            "wrong_wigner_side_error": horizontal_errors["wrong_wigner_side_error"],
            "passed": horizontal_errors["wrong_wigner_side_error"] > 1e-3,
        },
        "vertical_wrong_action_is_not_a_strong_graveyard": {
            "wrong_ignore_rotation_error": vertical_errors["wrong_ignore_rotation_error"],
            "passed": vertical_errors["wrong_ignore_rotation_error"] > 1e-3,
            "note": "A collapsed path can still move as a single vector under ambient SO(3); this control is not used as loop-independence evidence.",
        },
        "pole_horizontal_density_readout_collapses": {
            "centered_rank": centered_rank(pole_horizontal),
            "max_pairwise_displacement": max_pairwise_displacement(pole_horizontal),
            "passed": centered_rank(pole_horizontal) == 0 and max_pairwise_displacement(pole_horizontal) < 1e-10,
        },
        "sheet_reversal_preserves_horizontal_loop_rank_and_equivariance": {
            "positive_rank": centered_rank(horizontal),
            "reversed_rank": centered_rank(reversed_horizontal),
            "reversed_correct_wigner_d_error": reversed_errors["correct_wigner_d_error"],
            "passed": centered_rank(reversed_horizontal) == centered_rank(horizontal)
            and reversed_errors["correct_wigner_d_error"] < 1e-5,
        },
        "identity_rotation_has_zero_horizontal_equivariance_error": {
            "correct_wigner_d_error": identity_horizontal_errors["correct_wigner_d_error"],
            "passed": identity_horizontal_errors["correct_wigner_d_error"] < 1e-10,
        },
        "nonorthogonal_scaling_is_not_so3": {
            "scaled_det": float(torch.linalg.det(non_so3_scaling).item()),
            "orthogonality_error": float(torch.max(torch.abs(non_so3_scaling.T @ non_so3_scaling - torch.eye(3, dtype=torch.float64))).item()),
            "passed": abs(float(torch.linalg.det(non_so3_scaling).item()) - 1.0) > 1e-6,
        },
    }


def main() -> int:
    positive = run_positive()
    graveyards = run_graveyards()
    all_pass = bool(
        positive["density_so3_equivariance_pass"]
        and all(row["passed"] for row in graveyards.values())
    )
    results = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "pass": all_pass,
        "claim_ceiling": (
            "e3nn l=1 spherical-harmonic SO(3) equivariance baseline for Bloch-density readouts from declared "
            "Hopf/Weyl vertical fiber and horizontal base-lift paths only; this checks ambient rotation consistency "
            "and density-loop collapse/rank controls, not physical loop independence in a full nested Hopf-torus "
            "geometric-constraint manifold; no flux representation, no QIT, no GStack, no axis, no bridge, "
            "no nonclassical admission, and no target-system admission"
        ),
        "next_lego_target": "hopf_weyl_carrier_loop_geometry_baseline",
        "promotion_condition": (
            "May only support later geometry planning after full carrier, connection, topology, solver, density-object, "
            "and physical operator-evolution receipts reproduce compatible vertical/horizontal separation with adjacent controls."
        ),
        "demotion_condition": (
            "Demote if e3nn l=1 SO(3) equivariance fails, if horizontal density readout does not remain a two-dimensional "
            "loop, if vertical or pole readouts do not collapse, or if this receipt is used as flux, axis, QIT, GStack, "
            "bridge, nonclassical, or target-system evidence."
        ),
        "blocked_until": "blocked from target-system claims until full carrier/topology and physical-evolution receipts exist",
        "out_of_scope": [
            "No full nested Hopf-torus manifold or geometric-constraint manifold.",
            "No flux representation or Pauli-boundary shortcut.",
            "No Lindblad, Hamiltonian, thermodynamic, information-cycle, or target-system mechanics.",
            "No proof of physical inner/outer loop independence.",
            "No QIT, GStack, axis, bridge, nonclassical, or target-system admission.",
        ],
        "divergence_log": (
            "This e3nn packet is an ambient SO(3)-equivariance formulation of projected density-readout geometry. "
            "It detects collapsed vertical-fiber density readouts and two-dimensional horizontal/base density loops, "
            "but does not distinguish connection sign or implement a full carrier manifold."
        ),
        "operation_sequence": [
            "sample declared Hopf/Weyl vertical fiber and horizontal base-lift paths",
            "project each sample family to three-coordinate Bloch-density readouts",
            "compute e3nn l=1 spherical harmonics for collapsed and loop readouts",
            "rotate readouts by a deterministic SO(3) matrix",
            "compare direct rotated harmonics with Wigner-D-transformed original harmonics",
            "run vertical-collapse, horizontal-loop, wrong-action, pole-collapse, sheet-reversal, identity, and non-SO3 graveyards",
        ],
        "carrier_topology": "declared two-component Hopf/Weyl carrier paths projected to Bloch-density readout vectors on S2",
        "observable": "e3nn l=1 spherical-harmonic equivariance errors, rotation determinant, centered-rank controls, and density-readout displacement",
        "pass_fail_predicate": (
            "vertical density readout collapses, horizontal density readout has centered rank two, correct Wigner-D SO(3) "
            "equivariance errors are below tolerance, wrong horizontal actions fail, and adjacent collapse/rank controls pass"
        ),
        "graveyards": [
            "vertical fiber density readout collapses",
            "horizontal base density readout is a two-dimensional loop",
            "ignoring rotation breaks horizontal equivariance",
            "wrong Wigner-D side breaks horizontal equivariance",
            "vertical wrong action is not a strong loop-independence graveyard",
            "pole horizontal density readout collapses",
            "sheet reversal preserves horizontal loop rank and equivariance",
            "identity rotation has zero horizontal equivariance error",
            "nonorthogonal scaling is not SO3",
        ],
        "baselines": [
            "e3nn Hopf base-loop SO3 equivariance baseline",
            "QuTiP/Qiskit Hopf/Weyl vertical-horizontal density transport baselines",
            "GUDHI/TopoNetX/rustworkx Hopf/Weyl vertical-horizontal density readout topology baselines",
            "SymPy/Geomstats/Clifford Hopf/Weyl vertical-horizontal metric baselines",
        ],
        "alternative_formulations": [
            "higher-l e3nn spherical harmonic readout equivariance",
            "Clifford rotor action on vertical/horizontal density vectors",
            "geomstats SO3 action distance cross-check",
            "physical Hamiltonian generator evolution over vertical and horizontal path families",
        ],
        "exact_tool_function_needs": {
            "e3nn": ["o3.spherical_harmonics", "o3.matrix_to_angles", "o3.wigner_D", "o3.angles_to_matrix"],
            "torch": ["linspace", "stack", "linalg.det", "linalg.matrix_rank", "linalg.norm", "max", "abs"],
        },
        "lego_or_coupling_target": "hopf_weyl_carrier_loop_geometry_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyards_detail": graveyards,
        "promotion_allowed": False,
    }
    results = apply_default_receipt_boundary(results, source_name=f"sim_{NAME}")
    out_path = RESULTS_DIR / f"{NAME}_results.json"
    out_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Results written to {out_path}")
    print(f"PASS={all_pass}  name={NAME}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
