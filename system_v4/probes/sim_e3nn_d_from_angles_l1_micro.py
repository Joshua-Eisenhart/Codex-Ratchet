#!/usr/bin/env python3
"""e3nn l=1 D_from_angles micro fit probe.

Tool-stage scope:
  - one tool: e3nn
  - one API surface: o3.Irrep("1o").D_from_angles
  - one tiny claim: the l=1 representation matrix from a pinned Euler-angle
    fixture admits the finite vector-feature carrier, excludes wrong feature
    orientation, and preserves identity/zero-batch boundary cases.

This is pre-lego tool-lego fit evidence only. It does not promote a lego,
coupling, bridge, axis, GStack, spherical-harmonic, or broad equivariance claim.
"""

from __future__ import annotations

import json
import os
from typing import Any

import torch
from e3nn import o3


classification = "tool_lego_fit_probe"
NAME = "sim_e3nn_d_from_angles_l1_micro"
PROBE_FAMILY = "e3nn_d_from_angles_l1_micro"
CONSTRAINT_SET = "finite_l1_vector_feature_fixed_euler_rotation_fixture"

DTYPE = torch.float64
TOLERANCE = 1e-10

_NOT_USED_REASON = (
    "not used: this micro probe isolates e3nn.o3.Irrep('1o').D_from_angles "
    "on one finite l=1 vector-feature fixture; proof, topology, graph, "
    "spherical-harmonic, tensor-product, coupling, bridge, axis, and "
    "promotion claims are out of scope."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "PyTorch is supportive: tensors carry the finite l=1 feature "
            "fixture and residual arithmetic while e3nn supplies the "
            "load-bearing representation matrix."
        ),
    },
    "pyg": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "z3": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "cvc5": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "sympy": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "clifford": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "e3nn": {
        "tried": True,
        "used": True,
        "reason": (
            "e3nn is load-bearing: o3.Irrep('1o').D_from_angles is the only "
            "API surface under test and decides the finite-carrier admission, "
            "exclusion, and boundary predicates."
        ),
    },
    "rustworkx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "xgi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "toponetx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "gudhi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
}

TOOL_INTEGRATION_DEPTH = {tool: None for tool in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"
TOOL_INTEGRATION_DEPTH["e3nn"] = "load_bearing"

IRREP = o3.Irrep("1o")


def _angles() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    return (
        torch.tensor(0.3, dtype=DTYPE),
        torch.tensor(0.4, dtype=DTYPE),
        torch.tensor(0.5, dtype=DTYPE),
    )


def _identity_angles() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    zero = torch.tensor(0.0, dtype=DTYPE)
    return zero, zero, zero


def _tiny_angles() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    tiny = torch.tensor(1e-12, dtype=DTYPE)
    return tiny, tiny, tiny


def _features() -> torch.Tensor:
    return torch.tensor(
        [
            [1.0, -2.0, 0.5],
            [0.25, 0.75, -1.5],
        ],
        dtype=DTYPE,
    )


def _d_from_angles(
    angles: tuple[torch.Tensor, torch.Tensor, torch.Tensor],
) -> torch.Tensor:
    return IRREP.D_from_angles(*angles).to(dtype=DTYPE)


def _orthogonality_residual(matrix: torch.Tensor) -> float:
    eye = torch.eye(matrix.shape[0], dtype=DTYPE)
    return float((matrix.T @ matrix - eye).abs().max())


def _norm_residual(before: torch.Tensor, after: torch.Tensor) -> float:
    before_norm = torch.linalg.norm(before, dim=-1)
    after_norm = torch.linalg.norm(after, dim=-1)
    return float((before_norm - after_norm).abs().max())


def _flatten_sections(*sections: dict[str, Any]) -> list[dict[str, Any]]:
    flat: list[dict[str, Any]] = []
    for section in sections:
        for value in section.values():
            if isinstance(value, dict) and "passed" in value:
                flat.append(value)
    return flat


def run_positive_tests() -> dict[str, Any]:
    d_matrix = _d_from_angles(_angles())
    features = _features()
    transformed = features @ d_matrix.T

    return {
        "l1_d_from_angles_admits_finite_vector_feature_carrier": {
            "passed": tuple(d_matrix.shape) == (3, 3)
            and tuple(transformed.shape) == tuple(features.shape),
            "api_surface": "e3nn.o3.Irrep('1o').D_from_angles",
            "carrier": "two finite l=1 vector-feature rows with width 3",
            "angles_radians": [float(value) for value in _angles()],
            "matrix_shape": list(d_matrix.shape),
            "input_shape": list(features.shape),
            "output_shape": list(transformed.shape),
        },
        "l1_d_from_angles_preserves_feature_norms_on_fixed_rotation": {
            "passed": _norm_residual(features, transformed) < TOLERANCE,
            "max_norm_residual": _norm_residual(features, transformed),
            "tolerance": TOLERANCE,
            "fixture": "right action by D_from_angles(alpha=0.3, beta=0.4, gamma=0.5).T",
        },
        "l1_d_from_angles_matrix_is_orthogonal": {
            "passed": _orthogonality_residual(d_matrix) < TOLERANCE,
            "max_orthogonality_residual": _orthogonality_residual(d_matrix),
            "tolerance": TOLERANCE,
        },
    }


def run_negative_tests() -> dict[str, Any]:
    d_matrix = _d_from_angles(_angles())
    features = _features()
    admitted = features @ d_matrix.T
    wrong_orientation = features @ d_matrix
    wrong_orientation_gap = float((admitted - wrong_orientation).abs().max())

    bad_width = torch.ones(1, 4, dtype=DTYPE)
    wrong_width_excluded = False
    wrong_width_error = None
    try:
        _ = bad_width @ d_matrix.T
    except Exception as exc:
        wrong_width_excluded = True
        wrong_width_error = f"{type(exc).__name__}: {exc}"

    malformed_angles_excluded = False
    malformed_angles_error = None
    try:
        _ = IRREP.D_from_angles(torch.zeros(2, dtype=DTYPE), *_angles()[1:])
    except Exception as exc:
        malformed_angles_excluded = True
        malformed_angles_error = f"{type(exc).__name__}: {exc}"

    return {
        "wrong_orientation_is_excluded_for_this_row_feature_fixture": {
            "passed": wrong_orientation_gap > 1e-3,
            "wrong_orientation_gap": wrong_orientation_gap,
            "exclusion_note": (
                "The row-feature fixture is admitted only for right action by "
                "D_from_angles(...).T, not the untransposed orientation."
            ),
        },
        "wrong_feature_width_is_excluded": {
            "passed": wrong_width_excluded,
            "bad_input_shape": list(bad_width.shape),
            "expected_width": 3,
            "error": wrong_width_error,
            "exclusion_note": "A width-4 feature row is inadmissible for an l=1 width-3 carrier.",
        },
        "malformed_angle_shape_is_excluded": {
            "passed": malformed_angles_excluded,
            "bad_alpha_shape": [2],
            "error": malformed_angles_error,
            "exclusion_note": "The fixed-rotation row must not silently admit vector-valued Euler scalars.",
        },
    }


def run_boundary_tests() -> dict[str, Any]:
    identity = _d_from_angles(_identity_angles())
    tiny = _d_from_angles(_tiny_angles())
    empty = torch.empty(0, IRREP.dim, dtype=DTYPE)
    empty_out = empty @ identity.T

    return {
        "identity_angles_admit_identity_boundary": {
            "passed": float((identity - torch.eye(3, dtype=DTYPE)).abs().max()) < TOLERANCE,
            "max_abs_identity_residual": float((identity - torch.eye(3, dtype=DTYPE)).abs().max()),
            "boundary_note": "Zero Euler angles sit on the identity boundary of this finite carrier.",
        },
        "tiny_angles_stay_near_identity_boundary": {
            "passed": float((tiny - torch.eye(3, dtype=DTYPE)).abs().max()) < 1e-10,
            "max_abs_tiny_angle_residual": float((tiny - torch.eye(3, dtype=DTYPE)).abs().max()),
            "angles_radians": [float(value) for value in _tiny_angles()],
            "boundary_note": "Near-zero Euler angles remain within the local tolerance boundary.",
        },
        "zero_batch_preserves_l1_width_boundary": {
            "passed": tuple(empty_out.shape) == (0, IRREP.dim),
            "input_shape": list(empty.shape),
            "output_shape": list(empty_out.shape),
            "expected_shape": [0, IRREP.dim],
            "boundary_note": "An empty finite batch preserves the l=1 feature width.",
        },
    }


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    flat_tests = _flatten_sections(positive, negative, boundary)
    all_pass = all(test.get("passed") for test in flat_tests)

    results = {
        "name": NAME,
        "probe_family": PROBE_FAMILY,
        "constraint_set": CONSTRAINT_SET,
        "classification": classification,
        "tool_function_scope": "tool_lego_fit_micro_only",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "surviving_alternatives": [
            "o3.spherical_harmonics, o3.wigner_D, and Irreps.D_from_matrix "
            "remain separate surfaces with separate receipts; this file only "
            "targets Irrep('1o').D_from_angles on a pinned l=1 fixture."
        ],
        "claim_ceiling": (
            "local tool-lego fit only: e3nn Irrep('1o').D_from_angles admits "
            "a tiny finite l=1 vector-feature fixed-rotation fixture; "
            "promotion_allowed=false; no QIT, GStack, axis, bridge, "
            "nonclassical, spherical-harmonic, or coupling claim"
        ),
        "summary": {
            "promotion_allowed": False,
            "claim": (
                "D_from_angles is tested only as a bounded l=1 representation "
                "matrix for a finite row-feature fixture."
            ),
            "passed": sum(1 for test in flat_tests if test.get("passed")),
            "total": len(flat_tests),
        },
        "carrier": "finite carrier: two l=1 vector-feature rows in R^3 plus one fixed Euler rotation triple",
        "one_variable": "only e3nn.o3.Irrep('1o').D_from_angles behavior is uncertain",
        "ledger_loopback": "tool-depth row: e3nn load-bearing shallow-tool checker threshold >=10 receipts",
        "next_lego_target": "bounded l=1 fixed-rotation representation-matrix fit fixture",
        "promotion_condition": (
            "requires a later admitted downstream row that names this exact "
            "tool-function receipt and passes runner/result/ledger reconciliation"
        ),
        "blocked_until": (
            "blocked from lego promotion, coupling, bridge, axis, GStack, "
            "nonclassical, and spherical-harmonic claims until separate "
            "downstream receipts and stage gates admit those consumers"
        ),
        "demotion_condition": (
            "Demote e3nn for this surface if D_from_angles is unavailable, "
            "does not return a 3x3 l=1 matrix, fails orthogonality or norm "
            "preservation on the pinned fixture, admits wrong feature width or "
            "malformed angle shape, or blurs the identity/zero-batch boundaries."
        ),
        "out_of_scope": [
            "no sim execution in authoring turn",
            "no result JSON authored by this packet",
            "no spherical_harmonics claim",
            "no wigner_D claim",
            "no D_from_matrix claim",
            "no tensor-product claim",
            "no tool-tool coupling",
            "no bridge claim",
            "no axis claim",
            "no GStack claim",
            "no nonclassical admission",
            "no scientific lego promotion",
        ],
        "criteria_checked": [
            "D_from_angles returns a 3x3 l=1 representation matrix",
            "fixed-rotation action preserves finite l=1 feature width",
            "fixed-rotation action preserves finite l=1 feature norms",
            "wrong row-feature orientation is excluded",
            "wrong feature width is excluded",
            "malformed angle shape is excluded",
            "identity, tiny-angle, and zero-batch boundaries are explicit",
        ],
        "all_pass": all_pass,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Summary: {results['summary']['passed']}/{results['summary']['total']} admitted checks")

    if not all_pass:
        raise SystemExit(1)
