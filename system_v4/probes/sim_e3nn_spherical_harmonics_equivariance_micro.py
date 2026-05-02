#!/usr/bin/env python3
"""e3nn spherical harmonics equivariance micro probe.

Tool-stage scope:
  - one tool: e3nn
  - one API surface: o3.spherical_harmonics on tiny SO(3)/O(3) vector fixtures
  - one tiny claim: e3nn spherical harmonics transform according to the
    matching tiny irreps representation for bounded l=0, l=1, and l=2 cases.

This is pre-lego function evidence. It does not promote a lego, coupling,
learned GNN, e3nn convolution, bridge, axis, or operator-geometry claim.
"""

from __future__ import annotations

import json
import os
from typing import Any

import torch
from e3nn import o3


classification = "canonical"
NAME = "sim_e3nn_spherical_harmonics_equivariance_micro"
PROBE_FAMILY = "e3nn_spherical_harmonics_equivariance_micro"
CONSTRAINT_SET = "tiny_so3_o3_spherical_harmonics_vector_fixtures"

TOLERANCE = 1e-5
DTYPE = torch.float64

_NOT_USED_REASON = (
    "not used: this function micro isolates e3nn.o3.spherical_harmonics on "
    "tiny SO(3)/O(3) vector fixtures; proof, topology, GNN layers, "
    "convolution, lego promotion, bridge, axis, and operator-geometry claims "
    "are out of scope."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "PyTorch is supportive: tensors hold the tiny vector fixtures, "
            "orthogonal matrices, and numeric pass/fail comparisons."
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
            "e3nn is load-bearing: o3.spherical_harmonics computes the "
            "features under test and o3.Irreps.D_from_matrix supplies the "
            "matching SO(3)/O(3) representation for equivariance checks."
        ),
    },
    "rustworkx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "xgi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "toponetx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "gudhi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
}

TOOL_INTEGRATION_DEPTH = {tool: None for tool in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["e3nn"] = "load_bearing"
TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"


def _fixtures() -> torch.Tensor:
    return torch.tensor(
        [
            [1.0, 2.0, 3.0],
            [-0.5, 1.5, 0.25],
            [0.0, -2.0, 1.0],
        ],
        dtype=DTYPE,
    )


def _rotation_z() -> torch.Tensor:
    angle = torch.tensor(0.7, dtype=DTYPE)
    return torch.tensor(
        [
            [torch.cos(angle), -torch.sin(angle), 0.0],
            [torch.sin(angle), torch.cos(angle), 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=DTYPE,
    )


def _reflection_x() -> torch.Tensor:
    return torch.diag(torch.tensor([-1.0, 1.0, 1.0], dtype=DTYPE))


def _inversion() -> torch.Tensor:
    return -torch.eye(3, dtype=DTYPE)


def _irrep_for_l(l_value: int) -> o3.Irreps:
    parity = "o" if l_value % 2 else "e"
    return o3.Irreps(f"1x{l_value}{parity}")


def _spherical_harmonics(l_value: int, vectors: torch.Tensor) -> torch.Tensor:
    return o3.spherical_harmonics(
        l_value,
        vectors,
        normalize=True,
        normalization="component",
    ).to(dtype=DTYPE)


def _transform_vectors(vectors: torch.Tensor, matrix: torch.Tensor) -> torch.Tensor:
    return vectors @ matrix.T


def _transform_features(features: torch.Tensor, l_value: int, matrix: torch.Tensor) -> torch.Tensor:
    representation = _irrep_for_l(l_value).D_from_matrix(matrix).to(dtype=DTYPE)
    return features @ representation.T


def _max_equivariance_error(l_value: int, matrix: torch.Tensor) -> float:
    vectors = _fixtures()
    base = _spherical_harmonics(l_value, vectors)
    transformed_direct = _spherical_harmonics(l_value, _transform_vectors(vectors, matrix))
    transformed_by_representation = _transform_features(base, l_value, matrix)
    return float((transformed_direct - transformed_by_representation).abs().max())


def _as_nested_list(tensor: torch.Tensor) -> list[list[float]]:
    return [[float(value) for value in row] for row in tensor.detach().cpu()]


def run_positive_tests() -> dict[str, Any]:
    rotation = _rotation_z()
    y1_error = _max_equivariance_error(1, rotation)
    y2_error = _max_equivariance_error(2, rotation)

    vectors = _fixtures()
    y0 = _spherical_harmonics(0, vectors)
    y1 = _spherical_harmonics(1, vectors)
    y2 = _spherical_harmonics(2, vectors)

    return {
        "l1_so3_rotation_equivariance": {
            "passed": y1_error < TOLERANCE,
            "max_equivariance_error": y1_error,
            "tolerance": TOLERANCE,
            "fixture": "Y_1(Rx) equals D^1(R) Y_1(x) on three tiny vectors",
            "e3nn_irrep": str(_irrep_for_l(1)),
        },
        "l2_so3_rotation_equivariance": {
            "passed": y2_error < TOLERANCE,
            "max_equivariance_error": y2_error,
            "tolerance": TOLERANCE,
            "fixture": "Y_2(Rx) equals D^2(R) Y_2(x) on three tiny vectors",
            "e3nn_irrep": str(_irrep_for_l(2)),
        },
        "declared_output_widths_match_degrees": {
            "passed": tuple(y0.shape) == (3, 1)
            and tuple(y1.shape) == (3, 3)
            and tuple(y2.shape) == (3, 5),
            "observed_shapes": {
                "l0": list(y0.shape),
                "l1": list(y1.shape),
                "l2": list(y2.shape),
            },
            "expected_shapes": {
                "l0": [3, 1],
                "l1": [3, 3],
                "l2": [3, 5],
            },
        },
    }


def run_negative_tests() -> dict[str, Any]:
    vectors = _fixtures()
    rotation = _rotation_z()
    y1 = _spherical_harmonics(1, vectors)
    y1_rotated_direct = _spherical_harmonics(1, _transform_vectors(vectors, rotation))
    y1_untransformed_error = float((y1_rotated_direct - y1).abs().max())

    wrong_l2_representation = _irrep_for_l(2).D_from_matrix(rotation).to(dtype=DTYPE)
    y2 = _spherical_harmonics(2, vectors)
    y2_rotated_direct = _spherical_harmonics(2, _transform_vectors(vectors, rotation))
    y2_wrong_path = y2 @ wrong_l2_representation
    y2_wrong_error = float((y2_rotated_direct - y2_wrong_path).abs().max())

    malformed_rejected = False
    error_type = None
    error_message = None
    try:
        _spherical_harmonics(1, torch.ones(2, 2, dtype=DTYPE))
    except Exception as exc:
        malformed_rejected = True
        error_type = type(exc).__name__
        error_message = str(exc)

    return {
        "untransformed_features_do_not_fake_rotation_equivariance": {
            "passed": y1_untransformed_error > 0.05,
            "untransformed_feature_error": y1_untransformed_error,
            "exclusion_note": (
                "The receipt must not pass by comparing rotated inputs to "
                "unchanged spherical harmonic features."
            ),
        },
        "wrong_representation_orientation_is_excluded": {
            "passed": y2_wrong_error > 0.05,
            "wrong_orientation_error": y2_wrong_error,
            "exclusion_note": (
                "For this row-vector fixture, the matching e3nn "
                "D_from_matrix action uses the transpose on the right."
            ),
        },
        "malformed_vector_width_is_rejected": {
            "passed": malformed_rejected,
            "expected": "spherical_harmonics input vectors require last dimension 3",
            "bad_input_shape": [2, 2],
            "error_type": error_type,
            "error_message": error_message,
        },
    }


def run_boundary_tests() -> dict[str, Any]:
    vectors = _fixtures()
    inversion = _inversion()
    reflection = _reflection_x()

    y0_reflection_error = _max_equivariance_error(0, reflection)
    y1_inversion_error = _max_equivariance_error(1, inversion)
    y2_inversion_error = _max_equivariance_error(2, inversion)

    empty = torch.empty(0, 3, dtype=DTYPE)
    empty_y1 = _spherical_harmonics(1, empty)

    y1 = _spherical_harmonics(1, vectors)
    y1_inverted_direct = _spherical_harmonics(1, _transform_vectors(vectors, inversion))

    return {
        "l0_o3_reflection_invariant_boundary": {
            "passed": y0_reflection_error < TOLERANCE,
            "max_equivariance_error": y0_reflection_error,
            "boundary_note": "Degree-0 spherical harmonics remain invariant under a tiny O(3) reflection.",
        },
        "l1_o3_inversion_odd_parity_boundary": {
            "passed": y1_inversion_error < TOLERANCE
            and torch.allclose(y1_inverted_direct, -y1, atol=TOLERANCE),
            "max_equivariance_error": y1_inversion_error,
            "sample_y1": _as_nested_list(y1[:1]),
            "sample_inverted_y1": _as_nested_list(y1_inverted_direct[:1]),
            "boundary_note": "Degree-1 harmonics have odd parity under inversion in this fixture.",
        },
        "l2_o3_inversion_even_parity_boundary": {
            "passed": y2_inversion_error < TOLERANCE,
            "max_equivariance_error": y2_inversion_error,
            "boundary_note": "Degree-2 harmonics have even parity under inversion in this fixture.",
        },
        "zero_batch_preserves_l1_width": {
            "passed": tuple(empty_y1.shape) == (0, 3),
            "observed_shape": list(empty_y1.shape),
            "expected_shape": [0, 3],
            "boundary_note": "An empty vector batch preserves the declared l=1 output width.",
        },
    }


def _flatten_sections(*sections: dict[str, Any]) -> list[dict[str, Any]]:
    flat = []
    for section in sections:
        for value in section.values():
            if isinstance(value, dict) and "passed" in value:
                flat.append(value)
    return flat


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
        "tool_function_scope": "tool_function_micro_only",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "surviving_alternatives": [
            "Other e3nn O(3) operations may remain useful; this micro receipt "
            "only covers o3.spherical_harmonics on tiny SO(3)/O(3) vector fixtures."
        ],
        "claim_ceiling": "tool_function_micro_only",
        "next_lego_target": (
            "minimal spherical-harmonics equivariance fixture before geometry "
            "or operator equivariance promotion"
        ),
        "promotion_condition": (
            "requires a later admitted downstream row that names this exact "
            "function receipt and passes strict runner admission; this MICRO "
            "row does not promote any lego"
        ),
        "blocked_until": (
            "blocked until a downstream queue row declares the exact geometry "
            "or operator target, parent receipt use, and active stage gate for promotion"
        ),
        "demotion_condition": (
            "Demote e3nn for this function surface if o3.spherical_harmonics "
            "returns incorrect l=0/l=1/l=2 widths, fails the tiny SO(3)/O(3) "
            "D_from_matrix equivariance checks, silently accepts malformed "
            "non-3D vector inputs, or lets wrong/untransformed representation "
            "paths pass."
        ),
        "out_of_scope": [
            "no learned GNN",
            "no e3nn convolution",
            "no operator-geometry promotion",
            "no lego promotion",
            "no tool-tool coupling",
            "no bridge claim",
            "no axis claim",
            "no broad equivariance proof",
            "no proof of the whole e3nn library",
        ],
        "criteria_checked": [
            "spherical_harmonics returns declared widths for l=0, l=1, and l=2",
            "l=1 harmonics satisfy tiny SO(3) rotation equivariance",
            "l=2 harmonics satisfy tiny SO(3) rotation equivariance",
            "l=0, l=1, and l=2 fixtures satisfy bounded O(3) reflection/inversion behavior",
            "wrong and untransformed comparison paths fail",
            "malformed vector width is rejected",
            "zero-batch l=1 boundary preserves output width",
        ],
        "summary": {
            "passed": sum(1 for test in flat_tests if test.get("passed")),
            "total": len(flat_tests),
        },
        "all_pass": all_pass,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Summary: {results['summary']['passed']}/{results['summary']['total']} passed")

    if not all_pass:
        raise SystemExit(1)
