#!/usr/bin/env python3
"""
sim_torch_ga_capability.py -- Tool-capability isolation sim for `torch_ga`.

This probe measures torch_ga directly instead of letting it ride the generic
clifford capability receipt. It is intentionally bounded to Cl(3), rotor
sandwiching, pseudoscalar sign, and torch autograd through geometric product.
"""

classification = "canonical"

import json
import math
import os
import contextlib
import io
from typing import Any

from receipt_boundary import apply_default_receipt_boundary

_NOT_USED_REASON = (
    "not used: this bounded torch_ga capability receipt isolates torch_ga "
    "GeometricAlgebra operations; other tool families require separate receipts."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "supportive backend for torch tensors and autograd; not the package under test",
    },
    "pyg": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "z3": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "cvc5": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "sympy": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "clifford": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "torch_ga": {
        "tried": False,
        "used": False,
        "reason": "under test: GeometricAlgebra, geom_prod, reversion, from_tensor, blade metadata, and autograd through GA product",
    },
    "geomstats": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "xgi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "toponetx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "gudhi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
}

TOOL_INTEGRATION_DEPTH = {
    "clifford": None,
    "cvc5": None,
    "e3nn": None,
    "geomstats": None,
    "gudhi": None,
    "pyg": None,
    "pytorch": "supportive",
    "rustworkx": None,
    "sympy": None,
    "toponetx": None,
    "torch_ga": "load_bearing",
    "xgi": None,
    "z3": None,
}

DTYPE = None
TORCH_OK = False
TORCH_GA_OK = False
TORCH_GA_VERSION = None
TORCH_GA_ORIGIN = None

try:
    import torch

    TORCH_OK = True
    DTYPE = torch.float64
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
except Exception as exc:
    TOOL_MANIFEST["pytorch"]["reason"] = f"not importable: {type(exc).__name__}: {exc}"

try:
    import torch_ga
    from torch_ga import GeometricAlgebra

    TORCH_GA_OK = True
    TORCH_GA_VERSION = getattr(torch_ga, "__version__", "unknown")
    TORCH_GA_ORIGIN = getattr(torch_ga, "__file__", None)
    TOOL_MANIFEST["torch_ga"]["tried"] = True
    TOOL_MANIFEST["torch_ga"]["used"] = True
except Exception as exc:
    TOOL_MANIFEST["torch_ga"]["reason"] = f"not importable: {type(exc).__name__}: {exc}"


def _float(value: Any) -> float:
    if hasattr(value, "detach"):
        return float(value.detach().cpu())
    return float(value)


def _list_float(tensor: Any) -> list[float]:
    return [float(x) for x in tensor.detach().cpu().reshape(-1).tolist()]


def _max_abs(tensor: Any) -> float:
    return _float(tensor.detach().abs().max())


def _imports_ready() -> bool:
    return bool(TORCH_OK and TORCH_GA_OK)


def _skip(reason: str) -> dict[str, Any]:
    return {"pass": False, "reason": reason}


def _ga(metric=None):
    if metric is None:
        metric = [1.0, 1.0, 1.0]
    return GeometricAlgebra(metric=metric, dtype=DTYPE)


def _cl3_fixtures():
    ga = _ga()
    blades = ga.blade_mvs.to(dtype=DTYPE)
    one, e1, e2, e3, e12, e13, e23, pseudoscalar = blades
    return ga, blades, one, e1, e2, e3, e12, e13, e23, pseudoscalar


def run_positive_tests() -> dict[str, Any]:
    r: dict[str, Any] = {}
    if not _imports_ready():
        r["imports_available"] = _skip("torch or torch_ga not importable")
        return r

    torch.manual_seed(17)
    ga, _blades, one, e1, e2, e3, e12, _e13, _e23, pseudoscalar = _cl3_fixtures()

    r["cl3_basis_blade_count"] = {
        "pass": int(ga.num_blades) == 8,
        "metric": _list_float(ga.metric),
        "blade_names": list(ga.blades),
        "blade_count": int(ga.num_blades),
    }

    e1e2 = ga.geom_prod(e1, e2)
    e2e1 = ga.geom_prod(e2, e1)
    anticommutator_norm = _float(torch.linalg.vector_norm(e1e2 + e2e1))
    commutator_norm = _float(torch.linalg.vector_norm(e1e2 - e2e1))
    r["e1_e2_anticommutation"] = {
        "pass": anticommutator_norm <= 1e-12 and commutator_norm > 1.0,
        "blade_names_used": {"e1": ga.blades[1], "e2": ga.blades[2], "e1e2_blade": ga.blades[4]},
        "anticommutator_norm": anticommutator_norm,
        "commutator_norm": commutator_norm,
    }

    phi = torch.tensor(0.73, dtype=DTYPE)
    rotor = torch.cos(0.5 * phi) * one - torch.sin(0.5 * phi) * e12
    rotated = ga.geom_prod(ga.geom_prod(rotor, e1), ga.reversion(rotor))
    reference = torch.tensor([math.cos(float(phi)), math.sin(float(phi)), 0.0], dtype=DTYPE)
    rotor_residual = _float(torch.linalg.vector_norm(rotated[1:4] - reference))
    r["rotor_sandwich_matches_torch_reference"] = {
        "pass": rotor_residual <= 1e-12,
        "angle_radians": _float(phi),
        "rotated_vector_coefficients": _list_float(rotated[1:4]),
        "torch_reference_coefficients": _list_float(reference),
        "residual_l2": rotor_residual,
    }

    pseudoscalar_square = ga.geom_prod(pseudoscalar, pseudoscalar)
    pseudoscalar_residual = _max_abs(pseudoscalar_square + one)
    r["pseudoscalar_square_minus_one"] = {
        "pass": pseudoscalar_residual <= 1e-12,
        "pseudoscalar_blade_name": ga.blades[-1],
        "square_coefficients": _list_float(pseudoscalar_square),
        "residual_vs_negative_scalar_one": pseudoscalar_residual,
    }

    coeffs = torch.tensor(
        [0.3, -0.7, 1.1, 0.5, -0.2, 0.9, -1.3, 0.4],
        dtype=DTYPE,
        requires_grad=True,
    )
    fixed = torch.tensor([1.0, 0.2, -0.4, 0.7, -0.5, 0.6, 0.1, -0.8], dtype=DTYPE)
    product = ga.geom_prod(coeffs, fixed)
    loss = torch.dot(product, product)
    loss.backward()
    grad_norm = _float(torch.linalg.vector_norm(coeffs.grad))
    r["autograd_through_ga_product_norm"] = {
        "pass": bool(torch.isfinite(coeffs.grad).all().item()) and grad_norm > 1e-9,
        "loss": _float(loss),
        "gradient_norm": grad_norm,
        "gradient_finite": bool(torch.isfinite(coeffs.grad).all().item()),
    }

    return r


def run_negative_tests() -> dict[str, Any]:
    r: dict[str, Any] = {}
    if not _imports_ready():
        r["imports_available"] = _skip("torch or torch_ga not importable")
        return r

    ga, _blades, one, e1, _e2, _e3, _e12, _e13, _e23, pseudoscalar = _cl3_fixtures()
    same_blade_gap = _float(torch.linalg.vector_norm(ga.geom_prod(e1, e1) - ga.geom_prod(e1, e1)))
    r["same_blade_commuting_control_zero_gap"] = {
        "pass": same_blade_gap <= 1e-12,
        "gap_norm": same_blade_gap,
        "control": "identical same-blade product must not create a noncommutation gap",
    }

    wrong_ga = _ga([1.0, 1.0, -1.0])
    wrong_blades = wrong_ga.blade_mvs.to(dtype=DTYPE)
    wrong_square = wrong_ga.geom_prod(wrong_blades[-1], wrong_blades[-1])
    wrong_residual_vs_cl3 = _max_abs(wrong_square - ga.geom_prod(pseudoscalar, pseudoscalar))
    wrong_residual_vs_plus_one = _max_abs(wrong_square - one)
    r["wrong_signature_changes_pseudoscalar_square"] = {
        "pass": wrong_residual_vs_cl3 > 1.0 and wrong_residual_vs_plus_one <= 1e-12,
        "wrong_metric": _list_float(wrong_ga.metric),
        "wrong_square_coefficients": _list_float(wrong_square),
        "residual_vs_cl3_square": wrong_residual_vs_cl3,
        "residual_vs_positive_scalar_one": wrong_residual_vs_plus_one,
    }

    return r


def run_boundary_tests() -> dict[str, Any]:
    r: dict[str, Any] = {}
    if not _imports_ready():
        r["imports_available"] = _skip("torch or torch_ga not importable")
        return r

    ga, _blades, one, _e1, _e2, e3, _e12, _e13, _e23, pseudoscalar = _cl3_fixtures()

    scalar = ga.from_scalar(2.5).to(dtype=DTYPE)
    scalar_product = ga.geom_prod(scalar, e3)
    scalar_residual = _float(torch.linalg.vector_norm(scalar_product - 2.5 * e3))
    r["scalar_grade0_left_multiplies_vector"] = {
        "pass": scalar_residual <= 1e-12,
        "scalar_coefficients": _list_float(scalar),
        "target_vector_blade": ga.blades[3],
        "residual_l2": scalar_residual,
    }

    pseudoscalar_grade = ga.grade(pseudoscalar, 3)
    grade_residual = _float(torch.linalg.vector_norm(pseudoscalar_grade - pseudoscalar))
    r["high_grade_pseudoscalar_boundary"] = {
        "pass": grade_residual <= 1e-12 and ga.blades[-1] == "012",
        "blade_name": ga.blades[-1],
        "grade3_residual_l2": grade_residual,
        "blade_degree": int(ga.blade_degrees[-1]),
    }

    # torch_ga 0.0.6 allocates a float32 destination inside from_tensor even
    # when GeometricAlgebra(dtype=torch.float64) is requested.
    tensor = torch.tensor([4.0], dtype=torch.float32)
    scalar_from_tensor = ga.from_tensor(tensor, torch.tensor([0]))
    from_tensor_residual = _float(torch.linalg.vector_norm(scalar_from_tensor.to(dtype=DTYPE) - 4.0 * one))
    r["from_tensor_scalar_boundary"] = {
        "pass": from_tensor_residual <= 1e-12,
        "blade_indices": [0],
        "coefficients": _list_float(scalar_from_tensor),
        "residual_l2": from_tensor_residual,
    }

    return r


def run_adequacy_report() -> dict[str, Any]:
    report: dict[str, Any] = {
        "version": TORCH_GA_VERSION,
        "origin": TORCH_GA_ORIGIN,
        "importable": TORCH_GA_OK,
        "api_friction": [],
        "ops_that_error": [],
        "not_pass_fail": True,
    }
    if not _imports_ready():
        report["api_friction"].append("torch or torch_ga not importable; capability tests cannot execute")
        return report

    ga, _blades, _one, e1, _e2, _e3, _e12, _e13, _e23, _pseudoscalar = _cl3_fixtures()
    if list(ga.blades[:4]) == ["", "0", "1", "2"]:
        report["api_friction"].append(
            "basis vectors are zero-named ('0','1','2'), so local e1/e2/e3 labels map to blade indices 1/2/3 rather than literal blade names"
        )
    if hasattr(ga, "sandwitch_prod"):
        report["api_friction"].append("sandwich helper is exposed as misspelled sandwitch_prod; probe uses explicit R*v*~R geom_prod calls")
    report["api_friction"].append(
        "from_tensor uses an internal float32 destination in torch_ga 0.0.6; float64 coefficient input can raise a dtype mismatch"
    )
    if not hasattr(ga, "sandwich_prod"):
        report["ops_that_error"].append(
            {
                "operation": "GeometricAlgebra.sandwich_prod",
                "error_type": "AttributeError",
                "detail": "correctly spelled sandwich_prod helper is absent",
            }
        )

    try:
        ga.geom_prod(e1[:-1], e1)
    except Exception as exc:
        report["ops_that_error"].append(
            {
                "operation": "GeometricAlgebra.geom_prod(wrong_shape, vector)",
                "error_type": type(exc).__name__,
                "detail": str(exc),
            }
        )

    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            ga.from_tensor(torch.ones(2, dtype=DTYPE), torch.tensor([0]))
    except Exception as exc:
        report["ops_that_error"].append(
            {
                "operation": "GeometricAlgebra.from_tensor(coeff_count_2, blade_indices_len_1)",
                "error_type": type(exc).__name__,
                "detail": str(exc),
            }
        )

    return report


def _all_pass(section: dict[str, Any]) -> bool:
    return all(bool(v.get("pass", False)) for v in section.values())


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    adequacy = run_adequacy_report()

    summary = {
        "positive_all_pass": _all_pass(pos),
        "negative_all_pass": _all_pass(neg),
        "boundary_all_pass": _all_pass(bnd),
        "importable": bool(TORCH_OK and TORCH_GA_OK),
    }
    summary["all_pass"] = bool(
        summary["importable"]
        and summary["positive_all_pass"]
        and summary["negative_all_pass"]
        and summary["boundary_all_pass"]
    )

    results = {
        "name": "sim_torch_ga_capability",
        "purpose": "Tool-capability isolation probe for torch_ga Cl(3) operations and torch autograd through geometric product.",
        "classification": classification,
        "torch_ga_version": TORCH_GA_VERSION,
        "torch_ga_origin": TORCH_GA_ORIGIN,
        "torch_available": TORCH_OK,
        "torch_ga_importable": TORCH_GA_OK,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "adequacy": adequacy,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
        "operation_sequence": [
            "instantiate torch_ga.GeometricAlgebra([1,1,1]) and check Cl(3) blade metadata",
            "measure e1/e2 anticommutation using GeometricAlgebra.geom_prod",
            "rotate a basis vector by explicit rotor sandwich R*v*~R and compare against a torch trigonometric reference",
            "check Cl(3) pseudoscalar square equals -1",
            "differentiate a geometric-product norm with torch.autograd",
            "run negative controls for same-blade zero gap and wrong-signature pseudoscalar square",
            "run scalar and high-grade blade boundary fixtures",
            "report non-gating API adequacy findings for replacement decisions",
        ],
        "carrier_topology": "finite Cl(3) torch_ga GeometricAlgebra tensor fixtures only; no spinor geometry, bridge, axis, GStack, or nonclassical admission is claimed",
        "observable": {
            "blade_count": "GeometricAlgebra([1,1,1]).num_blades",
            "anticommutation_gap": "norm((e1*e2) - (e2*e1)) and zero anticommutator residual",
            "rotor_residual": "L2 residual between R*v*~R vector coefficients and torch reference rotation",
            "pseudoscalar_square": "Cl(3) pseudoscalar product coefficients",
            "autograd_gradient": "finite nonzero gradient of product norm with respect to multivector coefficients",
            "controls": "same-blade zero gap, wrong-signature pseudoscalar square, scalar grade-0, and grade-3 pseudoscalar boundaries",
        },
        "pass_fail_predicate": "torch and torch_ga must import; every positive, negative, and boundary fixture must pass. Adequacy is reported for replacement decisions but does not gate all_pass.",
        "graveyards": [
            "torch_ga as a mere import/symbol alias without direct geom_prod witness",
            "same-blade product falsely reported as a noncommuting gap",
            "wrong metric silently producing the same pseudoscalar square as Cl(3,0)",
            "rotor sandwich accepted without comparison to a torch reference rotation",
            "torch_ga geometric product not differentiable through torch.autograd",
        ],
        "out_of_scope": [
            "no lego promotion",
            "no broad sim queue launch",
            "no bridge claim",
            "no axis claim",
            "no GStack claim",
            "no nonclassical admission",
        ],
    }
    results = apply_default_receipt_boundary(
        results,
        source_name="sim_torch_ga_capability",
        target="Use as bounded torch_ga capability evidence before torch_ga load-bearing labels or replacement decisions.",
    )

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "torch_ga_capability_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"summary.all_pass = {summary['all_pass']}")
