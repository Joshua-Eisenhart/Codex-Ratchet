#!/usr/bin/env python3
"""Bounded e3nn Wigner-D tensor-product operator-family fit probe.

Tool-lego fit scope only:
  - one tool family: e3nn o3, with torch as its tensor backend;
  - one deterministic fixture: l=1 Wigner-D acting on two vector irreps;
  - one local claim: the e3nn Wigner-D / tensor-product API can express a
    tiny SO(3)-invariant scalar operator-family fixture and reject malformed
    inputs.

This receipt does not promote a lego, coupling, axis, bridge, GStack, QIT, or
nonclassical claim.
"""

from __future__ import annotations

import json
import math
import os
from typing import Any

from receipt_boundary import apply_default_receipt_boundary

classification = "tool_lego_fit_probe"
NAME = "e3nn_wigner_d_tensor_product_operator_family_fit_probe"
PROBE_FAMILY = "e3nn_wigner_d_tensor_product_operator_family_fit"
CONSTRAINT_SET = "tiny_l1_wigner_d_tensor_product_scalar_invariant_fixture"

CLAIM_CEILING = (
    "local tool-lego fit only: e3nn Wigner-D and tensor-product APIs fit a "
    "tiny deterministic SO(3) scalar-invariant operator-family fixture; "
    "promotion_allowed=false; no QIT, GStack, axis, bridge, nonclassical, "
    "or coupling claim"
)

_NOT_USED_REASON = (
    "not used: this receipt isolates one e3nn Wigner-D/tensor-product "
    "tool-lego fit fixture; other tool families require separate receipts."
)

TOOL_MANIFEST: dict[str, dict[str, Any]] = {
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "supportive tensor backend required by e3nn for deterministic fixture tensors",
    },
    "pyg": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "z3": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "cvc5": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "sympy": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "clifford": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "e3nn": {
        "tried": False,
        "used": False,
        "reason": (
            "load-bearing target: e3nn.o3.Irreps, o3.wigner_D, and "
            "o3.FullyConnectedTensorProduct decide the fit predicate"
        ),
    },
    "rustworkx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "xgi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "toponetx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "gudhi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
}

TOOL_INTEGRATION_DEPTH = {tool: None for tool in TOOL_MANIFEST}

TORCH_OK = False
E3NN_OK = False
TORCH_IMPORT_ERROR = None
E3NN_IMPORT_ERROR = None
E3NN_VERSION = None

try:
    import torch

    TORCH_OK = True
    TOOL_MANIFEST["pytorch"]["tried"] = True
except Exception as exc:  # pragma: no cover - environment receipt path
    torch = None  # type: ignore[assignment]
    TORCH_IMPORT_ERROR = f"{type(exc).__name__}: {exc}"
    TOOL_MANIFEST["pytorch"]["reason"] = f"blocked: torch import failed: {TORCH_IMPORT_ERROR}"

try:
    import e3nn
    from e3nn import o3

    E3NN_OK = True
    E3NN_VERSION = getattr(e3nn, "__version__", "unknown")
    TOOL_MANIFEST["e3nn"]["tried"] = True
except Exception as exc:  # pragma: no cover - environment receipt path
    o3 = None  # type: ignore[assignment]
    E3NN_IMPORT_ERROR = f"{type(exc).__name__}: {exc}"
    TOOL_MANIFEST["e3nn"]["reason"] = f"blocked: e3nn import failed: {E3NN_IMPORT_ERROR}"

if TORCH_OK:
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"
if E3NN_OK:
    TOOL_MANIFEST["e3nn"]["used"] = True
    TOOL_INTEGRATION_DEPTH["e3nn"] = "load_bearing"


def _as_data(value: Any) -> Any:
    if TORCH_OK and isinstance(value, torch.Tensor):
        if value.ndim == 0:
            return float(value.detach().cpu().item())
        return value.detach().cpu().tolist()
    if isinstance(value, dict):
        return {str(k): _as_data(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_as_data(v) for v in value]
    return value


def _row_passes(row: dict[str, Any]) -> bool:
    if "passed" in row:
        return bool(row["passed"])
    return bool(row.get("pass"))


def _section_passes(section: dict[str, dict[str, Any]]) -> bool:
    return bool(section) and all(_row_passes(row) for row in section.values())


def _blocked_section() -> dict[str, dict[str, Any]]:
    return {
        "dependency_gate": {
            "passed": False,
            "status": "blocked",
            "torch_available": TORCH_OK,
            "e3nn_available": E3NN_OK,
            "torch_import_error": TORCH_IMPORT_ERROR,
            "e3nn_import_error": E3NN_IMPORT_ERROR,
            "blocked_reason": (
                "e3nn and torch are both required for this Wigner-D / "
                "tensor-product operator-family fit fixture"
            ),
        }
    }


def _fixture():
    vector_irreps = o3.Irreps("1x1o")
    scalar_irreps = o3.Irreps("1x0e")
    tensor_product = o3.FullyConnectedTensorProduct(
        vector_irreps,
        vector_irreps,
        scalar_irreps,
    )
    with torch.no_grad():
        for parameter in tensor_product.parameters():
            parameter.fill_(1.0)

    dtype = torch.float64
    alpha = torch.tensor(0.3, dtype=dtype)
    beta = torch.tensor(0.4, dtype=dtype)
    gamma = torch.tensor(0.5, dtype=dtype)
    D1 = o3.wigner_D(1, alpha, beta, gamma).to(dtype=dtype)
    x = torch.tensor([[0.25, -0.5, 1.0]], dtype=dtype)
    y = torch.tensor([[1.5, 0.75, -0.25]], dtype=dtype)
    return vector_irreps, scalar_irreps, tensor_product.to(dtype), D1, x, y


def run_positive_tests() -> dict[str, dict[str, Any]]:
    if not (TORCH_OK and E3NN_OK):
        return _blocked_section()

    vector_irreps, scalar_irreps, tensor_product, D1, x, y = _fixture()
    out = tensor_product(x, y)
    out_rotated = tensor_product(x @ D1.T, y @ D1.T)
    residual = float((out - out_rotated).detach().abs().max())
    orthogonality_residual = float((D1 @ D1.T - torch.eye(3, dtype=D1.dtype)).abs().max())

    return {
        "irreps_carrier_dimensions_match_fixture": {
            "passed": vector_irreps.dim == 3 and scalar_irreps.dim == 1,
            "vector_irreps": str(vector_irreps),
            "scalar_irreps": str(scalar_irreps),
            "observed_dims": {"vector": vector_irreps.dim, "scalar": scalar_irreps.dim},
            "expected_dims": {"vector": 3, "scalar": 1},
        },
        "wigner_d_l1_is_orthogonal_on_vector_carrier": {
            "passed": orthogonality_residual < 1e-10,
            "max_abs_residual": orthogonality_residual,
            "angles_radians": [0.3, 0.4, 0.5],
        },
        "tensor_product_scalar_is_invariant_under_wigner_d_action": {
            "passed": residual < 1e-10,
            "max_abs_residual": residual,
            "unrotated_scalar": _as_data(out),
            "rotated_scalar": _as_data(out_rotated),
            "fixture": "FullyConnectedTensorProduct(1x1o, 1x1o -> 1x0e)",
        },
    }


def run_negative_tests() -> dict[str, dict[str, Any]]:
    if not (TORCH_OK and E3NN_OK):
        return _blocked_section()

    _, _, tensor_product, _, x, y = _fixture()

    bad_width_rejected = False
    bad_width_error = None
    try:
        tensor_product(torch.zeros(1, 4, dtype=x.dtype), y)
    except Exception as exc:
        bad_width_rejected = True
        bad_width_error = f"{type(exc).__name__}: {exc}"

    stretch = torch.diag(torch.tensor([2.0, 1.0, 0.5], dtype=x.dtype))
    base = tensor_product(x, y)
    stretched = tensor_product(x @ stretch.T, y @ stretch.T)
    stretch_residual = float((base - stretched).detach().abs().max())

    malformed_irrep_rejected = False
    malformed_irrep_error = None
    try:
        o3.Irreps("not_an_irrep")
    except Exception as exc:
        malformed_irrep_rejected = True
        malformed_irrep_error = f"{type(exc).__name__}: {exc}"

    return {
        "malformed_irrep_string_is_rejected": {
            "passed": malformed_irrep_rejected,
            "error": malformed_irrep_error,
            "exclusion_note": "Irrep syntax must not silently accept malformed carrier declarations.",
        },
        "wrong_vector_width_is_rejected_by_tensor_product": {
            "passed": bad_width_rejected,
            "error": bad_width_error,
            "bad_input_shape": [1, 4],
            "expected_input_width": 3,
        },
        "non_orthogonal_stretch_is_not_admitted_as_rotation_invariant": {
            "passed": stretch_residual > 1e-3,
            "max_abs_residual": stretch_residual,
            "exclusion_note": (
                "The scalar fixture is admitted only for the Wigner-D rotation "
                "action, not for arbitrary non-orthogonal carrier transforms."
            ),
        },
    }


def run_boundary_tests() -> dict[str, dict[str, Any]]:
    if not (TORCH_OK and E3NN_OK):
        return _blocked_section()

    _, _, tensor_product, _, x, y = _fixture()

    identity_D = o3.wigner_D(
        1,
        torch.tensor(0.0, dtype=x.dtype),
        torch.tensor(0.0, dtype=x.dtype),
        torch.tensor(0.0, dtype=x.dtype),
    ).to(dtype=x.dtype)
    identity_residual = float(
        (tensor_product(x, y) - tensor_product(x @ identity_D.T, y @ identity_D.T))
        .detach()
        .abs()
        .max()
    )

    tiny = torch.tensor(1e-8, dtype=x.dtype)
    tiny_D = o3.wigner_D(1, tiny, tiny, tiny).to(dtype=x.dtype)
    tiny_residual = float(
        (tensor_product(x, y) - tensor_product(x @ tiny_D.T, y @ tiny_D.T))
        .detach()
        .abs()
        .max()
    )

    empty_x = torch.empty(0, 3, dtype=x.dtype)
    empty_y = torch.empty(0, 3, dtype=x.dtype)
    empty_out = tensor_product(empty_x, empty_y)

    return {
        "identity_wigner_d_is_exact_boundary_case": {
            "passed": identity_residual < 1e-12,
            "max_abs_residual": identity_residual,
        },
        "tiny_angle_wigner_d_stays_within_local_tolerance": {
            "passed": tiny_residual < 1e-10,
            "max_abs_residual": tiny_residual,
            "angle_radians": 1e-8,
        },
        "zero_batch_preserves_scalar_output_width": {
            "passed": tuple(empty_out.shape) == (0, 1),
            "output_shape": list(empty_out.shape),
            "expected_output_shape": [0, 1],
        },
    }


def build_result() -> dict[str, Any]:
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    summary = {
        "positive_all_pass": _section_passes(positive),
        "negative_all_pass": _section_passes(negative),
        "boundary_all_pass": _section_passes(boundary),
        "torch_available": TORCH_OK,
        "e3nn_available": E3NN_OK,
        "e3nn_version": E3NN_VERSION,
        "promotion_allowed": False,
    }
    summary["all_pass"] = bool(
        TORCH_OK
        and E3NN_OK
        and summary["positive_all_pass"]
        and summary["negative_all_pass"]
        and summary["boundary_all_pass"]
    )

    status = "passed" if summary["all_pass"] else "blocked"
    result = {
        "name": NAME,
        "probe_family": PROBE_FAMILY,
        "constraint_set": CONSTRAINT_SET,
        "classification": classification,
        "status": status,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "operation_sequence": [
            "construct o3.Irreps('1x1o') and o3.Irreps('1x0e')",
            "construct deterministic o3.wigner_D(l=1, alpha=0.3, beta=0.4, gamma=0.5)",
            "construct o3.FullyConnectedTensorProduct(1x1o, 1x1o -> 1x0e)",
            "evaluate scalar output before and after simultaneous Wigner-D action",
            "run malformed-irrep, wrong-width, non-orthogonal-stretch, identity, tiny-angle, and zero-batch controls",
        ],
        "carrier_topology": {
            "carrier": "two l=1 O(3) vector irreps mapped to one scalar irrep",
            "topology": "finite one-row tensor fixture; no graph, cell complex, manifold, bridge, or axis topology",
            "irreps": {"input_1": "1x1o", "input_2": "1x1o", "output": "1x0e"},
        },
        "observable": (
            "maximum absolute residual between scalar tensor-product output "
            "before and after simultaneous l=1 Wigner-D rotation"
        ),
        "pass_fail_predicate": (
            "pass iff imports are available, Wigner-D orthogonality residual < 1e-10, "
            "tensor-product scalar invariance residual < 1e-10, malformed carriers "
            "and wrong feature widths are rejected, non-orthogonal stretch is excluded, "
            "and boundary controls stay within tolerance"
        ),
        "graveyards": [
            "arbitrary non-orthogonal carrier transform as admitted SO(3) action",
            "malformed irrep declarations",
            "wrong feature-width tensors for declared vector irreps",
            "any promotion beyond local tool-lego fit",
        ],
        "baselines": {
            "identity_rotation": "zero residual boundary control",
            "tiny_angle_rotation": "near-identity Wigner-D tolerance control",
            "non_orthogonal_stretch": "negative control excluded from rotation-invariant family",
        },
        "alternative_formulations": [
            "Irreps.D_from_matrix on a named rotation matrix instead of o3.wigner_D angles",
            "o3.TensorProduct with explicit instructions instead of FullyConnectedTensorProduct",
            "l=2 tensor fixture after a separate micro receipt justifies the larger carrier",
        ],
        "exact_tool_function_needs": [
            "e3nn.o3.Irreps",
            "e3nn.o3.wigner_D",
            "e3nn.o3.FullyConnectedTensorProduct",
            "torch.Tensor arithmetic as e3nn backend only",
        ],
        "lego_coupling_target": (
            "bounded SO(3) scalar-invariant operator-family lego candidate; "
            "no coupling target admitted in this receipt"
        ),
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": False,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
        "surviving_alternatives": [
            "Other e3nn Wigner-D or tensor-product fixtures may remain admissible only as separate local receipts.",
            "This receipt does not decide any downstream lego, coupling, QIT, GStack, axis, or bridge surface.",
        ],
        "next_lego_target": "bounded SO(3) scalar-invariant operator-family lego fixture with this exact e3nn function receipt as local evidence",
        "promotion_condition": (
            "No promotion from this receipt. A later admitted lego row must name "
            "this exact receipt, declare the stage gate, and pass strict runner admission."
        ),
        "blocked_until": (
            "blocked from QIT, GStack, axis, bridge, nonclassical, or coupling claims "
            "until separate downstream receipts and stage-gate admission exist"
        ),
        "demotion_condition": (
            "Demote this fit if e3nn/torch imports fail, Wigner-D orthogonality breaks, "
            "tensor-product scalar invariance exceeds tolerance, malformed carriers or "
            "wrong-width tensors are accepted, or the non-orthogonal stretch control is admitted."
        ),
        "out_of_scope": [
            "no QIT claim",
            "no GStack claim",
            "no axis claim",
            "no bridge claim",
            "no nonclassical admission",
            "no tool-tool coupling claim",
            "no scientific lego promotion",
            "no proof of the whole e3nn library",
        ],
        "blocked_reason": None
        if summary["all_pass"]
        else "blocked because e3nn/torch imports or local fit predicates did not all pass",
    }
    return apply_default_receipt_boundary(
        result,
        source_name=NAME,
        target=result["next_lego_target"],
    )


if __name__ == "__main__":
    results = build_result()
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(_as_data(results), handle, indent=2, sort_keys=True)
    print(f"Results written to {out_path}")
    print(f"summary.all_pass = {results['summary']['all_pass']}")
    print(f"status = {results['status']}")
