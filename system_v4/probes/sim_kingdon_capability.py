#!/usr/bin/env python3
"""
sim_kingdon_capability.py -- Tool-capability isolation sim for `kingdon`.

Bounded to the same Cl(3) fixture used by sim_torch_ga_capability.py:
blade metadata, e1/e2 anticommutation, rotor sandwiching, pseudoscalar sign,
and the shared multivector product fixture across float, torch, and sympy
coefficient backends.
"""

classification = "canonical"

import json
import math
import os
from importlib import metadata
from typing import Any

from receipt_boundary import apply_default_receipt_boundary

_NOT_USED_REASON = (
    "not used: this bounded kingdon capability receipt isolates Kingdon "
    "Algebra and MultiVector operations; other tool families require separate receipts."
)

TOOL_MANIFEST = {
    "kingdon": {
        "tried": False,
        "used": False,
        "reason": "under test: Algebra(3,0,0), MultiVector geometric products, reverse, and backend-flexible coefficients",
    },
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "supportive backend check for torch tensors and autograd through a kingdon product",
    },
    "sympy": {
        "tried": False,
        "used": False,
        "reason": "supportive backend check for symbolic coefficients through a kingdon product",
    },
    "torch_ga": {
        "tried": False,
        "used": False,
        "reason": "supportive comparison surface on the same Cl(3) fixture; not the package under test",
    },
    "clifford": {
        "tried": False,
        "used": False,
        "reason": "supportive comparison surface on the same Cl(3) fixture; not the package under test",
    },
    "pyg": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "z3": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "cvc5": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "xgi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "toponetx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "gudhi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
}

TOOL_INTEGRATION_DEPTH = {
    "kingdon": "load_bearing",
    "pytorch": "supportive",
    "sympy": "supportive",
    "torch_ga": "supportive",
    "clifford": "supportive",
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

EPS = 1e-12
BASIS = ["e", "e1", "e2", "e3", "e12", "e13", "e23", "e123"]
PRODUCT_COEFFS = [0.3, -0.7, 1.1, 0.5, -0.2, 0.9, -1.3, 0.4]
PRODUCT_FIXED = [1.0, 0.2, -0.4, 0.7, -0.5, 0.6, 0.1, -0.8]
EXPECTED_PRODUCT = [-0.12, -0.76, -0.07, -0.26, -1.28, 0.86, 0.01, -0.86]
EXPECTED_SYMBOLIC_PRODUCT = {
    "e": "x0 + x1/5 - 2*x2/5 + 7*x3/10 + x4/2 - 3*x5/5 - x6/10 + 4*x7/5",
    "e1": "x0/5 + x1 + x2/2 - 3*x3/5 - 2*x4/5 + 7*x5/10 + 4*x6/5 - x7/10",
    "e2": "-2*x0/5 - x1/2 + x2 - x3/10 - x4/5 - 4*x5/5 + 7*x6/10 + 3*x7/5",
    "e3": "7*x0/10 + 3*x1/5 + x2/10 + x3 + 4*x4/5 - x5/5 + 2*x6/5 + x7/2",
    "e12": "-x0/2 - 2*x1/5 - x2/5 - 4*x3/5 + x4 - x5/10 + 3*x6/5 + 7*x7/10",
    "e13": "3*x0/5 + 7*x1/10 + 4*x2/5 - x3/5 + x4/10 + x5 + x6/2 + 2*x7/5",
    "e23": "x0/10 - 4*x1/5 + 7*x2/10 + 2*x3/5 - 3*x4/5 - x5/2 + x6 + x7/5",
    "e123": "-4*x0/5 + x1/10 - 3*x2/5 - x3/2 + 7*x4/10 + 2*x5/5 + x6/5 + x7",
}

KINGDON_OK = False
KINGDON_VERSION = None
KINGDON_ORIGIN = None
TORCH_OK = False
SYMPY_OK = False
TORCH_GA_OK = False
CLIFFORD_OK = False

try:
    import kingdon
    from kingdon import Algebra

    KINGDON_OK = True
    KINGDON_VERSION = getattr(kingdon, "__version__", None) or metadata.version("kingdon")
    KINGDON_ORIGIN = getattr(kingdon, "__file__", None)
    TOOL_MANIFEST["kingdon"]["tried"] = True
    TOOL_MANIFEST["kingdon"]["used"] = True
except Exception as exc:
    Algebra = None
    TOOL_MANIFEST["kingdon"]["reason"] = f"not importable: {type(exc).__name__}: {exc}"

try:
    import torch

    TORCH_OK = True
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
except Exception as exc:
    torch = None
    TOOL_MANIFEST["pytorch"]["reason"] = f"not importable: {type(exc).__name__}: {exc}"

try:
    import sympy as sp

    SYMPY_OK = True
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
except Exception as exc:
    sp = None
    TOOL_MANIFEST["sympy"]["reason"] = f"not importable: {type(exc).__name__}: {exc}"

try:
    import torch_ga
    from torch_ga import GeometricAlgebra

    TORCH_GA_OK = True
    TOOL_MANIFEST["torch_ga"]["tried"] = True
    TOOL_MANIFEST["torch_ga"]["used"] = True
except Exception as exc:
    torch_ga = None
    GeometricAlgebra = None
    TOOL_MANIFEST["torch_ga"]["reason"] = f"not importable: {type(exc).__name__}: {exc}"

try:
    from clifford import Cl

    CLIFFORD_OK = True
    TOOL_MANIFEST["clifford"]["tried"] = True
    TOOL_MANIFEST["clifford"]["used"] = True
except Exception as exc:
    Cl = None
    TOOL_MANIFEST["clifford"]["reason"] = f"not importable: {type(exc).__name__}: {exc}"


def _skip(reason: str) -> dict[str, Any]:
    return {"pass": False, "reason": reason}


def _float(value: Any) -> float:
    if TORCH_OK and hasattr(value, "detach"):
        return float(value.detach().cpu())
    return float(value)


def _allclose(a: list[float], b: list[float], tol: float = EPS) -> bool:
    return len(a) == len(b) and all(abs(float(x) - float(y)) <= tol for x, y in zip(a, b))


def _l2(values: list[Any]) -> float:
    return math.sqrt(sum(_float(v) ** 2 for v in values))


def _alg(p: int = 3, q: int = 0, r: int = 0):
    return Algebra(p, q, r)


def _mv(alg: Any, coeffs: list[Any]):
    return alg.multivector(dict(zip(BASIS, coeffs)))


def _coeffs(mv: Any) -> list[Any]:
    return [getattr(mv, blade, 0) for blade in BASIS]


def _float_coeffs(mv: Any) -> list[float]:
    return [_float(v) for v in _coeffs(mv)]


def _cl3_fixtures():
    alg = _alg()
    blades = alg.blades
    return (
        alg,
        blades["e"],
        blades["e1"],
        blades["e2"],
        blades["e3"],
        blades["e12"],
        blades["e13"],
        blades["e23"],
        blades["e123"],
    )


def run_positive_tests() -> dict[str, Any]:
    r: dict[str, Any] = {}
    if not KINGDON_OK:
        r["imports_available"] = _skip("kingdon not importable")
        return r

    alg, one, e1, e2, _e3, e12, _e13, _e23, pseudoscalar = _cl3_fixtures()

    r["cl3_basis_blade_count"] = {
        "pass": list(alg.basis) == BASIS and len(list(alg.blades)) == 8,
        "signature": list(alg.signature),
        "basis": list(alg.basis),
        "blade_count": len(list(alg.blades)),
    }

    e1e2 = e1 * e2
    e2e1 = e2 * e1
    anticommutator_norm = _l2(_coeffs(e1e2 + e2e1))
    commutator_norm = _l2(_coeffs(e1e2 - e2e1))
    r["e1_e2_anticommutation"] = {
        "pass": anticommutator_norm <= EPS and commutator_norm > 1.0,
        "e1e2_coefficients": _float_coeffs(e1e2),
        "e2e1_coefficients": _float_coeffs(e2e1),
        "anticommutator_norm": anticommutator_norm,
        "commutator_norm": commutator_norm,
    }

    phi = 0.73
    rotor = math.cos(0.5 * phi) * one - math.sin(0.5 * phi) * e12
    rotated = rotor * e1 * rotor.reverse()
    rotated_vector = _float_coeffs(rotated)[1:4]
    reference = [math.cos(phi), math.sin(phi), 0.0]
    rotor_residual = _l2([a - b for a, b in zip(rotated_vector, reference)])
    r["rotor_sandwich_matches_reference_rotation"] = {
        "pass": rotor_residual <= EPS,
        "angle_radians": phi,
        "rotated_vector_coefficients": rotated_vector,
        "reference_coefficients": reference,
        "residual_l2": rotor_residual,
    }

    pseudoscalar_square = pseudoscalar * pseudoscalar
    pseudoscalar_residual = _l2(_coeffs(pseudoscalar_square + one))
    r["pseudoscalar_square_minus_one"] = {
        "pass": pseudoscalar_residual <= EPS,
        "pseudoscalar_blade_name": "e123",
        "square_coefficients": _float_coeffs(pseudoscalar_square),
        "residual_vs_negative_scalar_one": pseudoscalar_residual,
    }

    float_product = _mv(alg, PRODUCT_COEFFS) * _mv(alg, PRODUCT_FIXED)
    float_values = _float_coeffs(float_product)
    r["float_coefficients_shared_product"] = {
        "pass": _allclose(float_values, EXPECTED_PRODUCT),
        "coefficients": float_values,
        "expected_coefficients": EXPECTED_PRODUCT,
        "max_abs_residual": max(abs(a - b) for a, b in zip(float_values, EXPECTED_PRODUCT)),
    }

    if TORCH_OK:
        coeffs = torch.tensor(PRODUCT_COEFFS, dtype=torch.float64, requires_grad=True)
        fixed = torch.tensor(PRODUCT_FIXED, dtype=torch.float64)
        torch_product = _mv(alg, list(coeffs)) * _mv(alg, list(fixed))
        torch_values_raw = _coeffs(torch_product)
        torch_values = [_float(v) for v in torch_values_raw]
        loss = sum(v * v for v in torch_values_raw)
        loss.backward()
        grad_norm = _float(torch.linalg.vector_norm(coeffs.grad))
        gradient_finite = bool(torch.isfinite(coeffs.grad).all().item())
        r["torch_coefficients_shared_product_and_autograd"] = {
            "pass": _allclose(torch_values, float_values) and gradient_finite and grad_norm > 1e-9,
            "coefficients": torch_values,
            "float_coefficients": float_values,
            "max_abs_residual_vs_float": max(abs(a - b) for a, b in zip(torch_values, float_values)),
            "loss": _float(loss),
            "gradient_norm": grad_norm,
            "gradient_finite": gradient_finite,
        }
    else:
        r["torch_coefficients_shared_product_and_autograd"] = _skip("torch not importable")

    if SYMPY_OK:
        symbols = sp.symbols("x0:8")
        fixed = [
            sp.Integer(1),
            sp.Rational(1, 5),
            -sp.Rational(2, 5),
            sp.Rational(7, 10),
            -sp.Rational(1, 2),
            sp.Rational(3, 5),
            sp.Rational(1, 10),
            -sp.Rational(4, 5),
        ]
        symbolic_product = _mv(alg, list(symbols)) * _mv(alg, fixed)
        symbolic_values = {blade: sp.simplify(value) for blade, value in zip(BASIS, _coeffs(symbolic_product))}
        expected = {blade: sp.sympify(expr) for blade, expr in EXPECTED_SYMBOLIC_PRODUCT.items()}
        symbolic_ok = all(sp.simplify(symbolic_values[blade] - expected[blade]) == 0 for blade in BASIS)
        r["sympy_symbolic_shared_product_closed_form"] = {
            "pass": symbolic_ok,
            "coefficients": {blade: str(symbolic_values[blade]) for blade in BASIS},
            "expected_coefficients": EXPECTED_SYMBOLIC_PRODUCT,
        }
    else:
        r["sympy_symbolic_shared_product_closed_form"] = _skip("sympy not importable")

    return r


def run_negative_tests() -> dict[str, Any]:
    r: dict[str, Any] = {}
    if not KINGDON_OK:
        r["imports_available"] = _skip("kingdon not importable")
        return r

    _alg3, one, e1, _e2, _e3, _e12, _e13, _e23, pseudoscalar = _cl3_fixtures()
    same_blade_gap = _l2(_coeffs((e1 * e1) - (e1 * e1)))
    r["same_blade_commuting_control_zero_gap"] = {
        "pass": same_blade_gap <= EPS,
        "gap_norm": same_blade_gap,
        "control": "identical same-blade product must not create a noncommutation gap",
    }

    wrong_alg = _alg(2, 1, 0)
    wrong_one = wrong_alg.blades["e"]
    wrong_pseudoscalar = wrong_alg.blades["e123"]
    wrong_square = wrong_pseudoscalar * wrong_pseudoscalar
    cl3_square = pseudoscalar * pseudoscalar
    wrong_residual_vs_cl3 = _l2([a - b for a, b in zip(_float_coeffs(wrong_square), _float_coeffs(cl3_square))])
    wrong_residual_vs_plus_one = _l2(_coeffs(wrong_square - wrong_one))
    r["wrong_signature_changes_pseudoscalar_square"] = {
        "pass": wrong_residual_vs_cl3 > 1.0 and wrong_residual_vs_plus_one <= EPS,
        "wrong_signature": list(wrong_alg.signature),
        "wrong_square_coefficients": _float_coeffs(wrong_square),
        "cl3_square_coefficients": _float_coeffs(cl3_square),
        "residual_vs_cl3_square": wrong_residual_vs_cl3,
        "residual_vs_positive_scalar_one": wrong_residual_vs_plus_one,
    }

    return r


def run_boundary_tests() -> dict[str, Any]:
    r: dict[str, Any] = {}
    if not KINGDON_OK:
        r["imports_available"] = _skip("kingdon not importable")
        return r

    alg, one, _e1, _e2, e3, _e12, _e13, _e23, pseudoscalar = _cl3_fixtures()

    scalar = alg.scalar([2.5])
    scalar_product = scalar * e3
    scalar_residual = _l2(_coeffs(scalar_product - 2.5 * e3))
    r["scalar_grade0_left_multiplies_vector"] = {
        "pass": scalar_residual <= EPS,
        "scalar_coefficients": _float_coeffs(scalar),
        "target_vector_blade": "e3",
        "residual_l2": scalar_residual,
    }

    pss_values = _float_coeffs(pseudoscalar)
    full_pseudoscalar_ok = pss_values == [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]
    r["full_pseudoscalar_boundary"] = {
        "pass": full_pseudoscalar_ok and pseudoscalar.keys() == (7,),
        "blade_name": "e123",
        "coefficients": pss_values,
        "keys": list(pseudoscalar.keys()),
        "basis": list(alg.basis),
    }

    unit_scalar = alg.scalar([1.0])
    r["scalar_identity_boundary"] = {
        "pass": _l2(_coeffs(unit_scalar * pseudoscalar - pseudoscalar)) <= EPS,
        "identity_times_pseudoscalar_coefficients": _float_coeffs(unit_scalar * pseudoscalar),
    }

    return r


def _torch_ga_shared_values() -> dict[str, Any]:
    if not (TORCH_OK and TORCH_GA_OK):
        return {"available": False, "reason": "torch or torch_ga not importable"}
    ga = GeometricAlgebra(metric=[1.0, 1.0, 1.0], dtype=torch.float64)
    coeffs = torch.tensor(PRODUCT_COEFFS, dtype=torch.float64)
    fixed = torch.tensor(PRODUCT_FIXED, dtype=torch.float64)
    product = ga.geom_prod(coeffs, fixed)
    phi = torch.tensor(0.73, dtype=torch.float64)
    blades = ga.blade_mvs.to(dtype=torch.float64)
    one, e1, _e2, _e3, e12 = blades[0], blades[1], blades[2], blades[3], blades[4]
    pseudoscalar = blades[-1]
    rotor = torch.cos(0.5 * phi) * one - torch.sin(0.5 * phi) * e12
    rotated = ga.geom_prod(ga.geom_prod(rotor, e1), ga.reversion(rotor))
    pseudoscalar_square = ga.geom_prod(pseudoscalar, pseudoscalar)
    return {
        "available": True,
        "version": getattr(torch_ga, "__version__", "unknown"),
        "product_coefficients": [float(x) for x in product.detach().cpu().reshape(-1).tolist()],
        "rotated_vector_coefficients": [float(x) for x in rotated[1:4].detach().cpu().reshape(-1).tolist()],
        "pseudoscalar_square_coefficients": [float(x) for x in pseudoscalar_square.detach().cpu().reshape(-1).tolist()],
    }


def _clifford_shared_values() -> dict[str, Any]:
    if not CLIFFORD_OK:
        return {"available": False, "reason": "clifford not importable"}
    _layout, blades = Cl(3)
    one = blades[""]
    e1 = blades["e1"]
    e12 = blades["e12"]
    pseudoscalar = blades["e123"]
    a = sum(c * blades[name.replace("e", "", 1) if name == "e" else name] for c, name in zip(PRODUCT_COEFFS, BASIS))
    b = sum(c * blades[name.replace("e", "", 1) if name == "e" else name] for c, name in zip(PRODUCT_FIXED, BASIS))
    product = a * b
    phi = 0.73
    rotor = math.cos(0.5 * phi) * one - math.sin(0.5 * phi) * e12
    rotated = rotor * e1 * ~rotor
    pseudoscalar_square = pseudoscalar * pseudoscalar
    basis_keys = [(), (1,), (2,), (3,), (1, 2), (1, 3), (2, 3), (1, 2, 3)]
    return {
        "available": True,
        "version": metadata.version("clifford"),
        "product_coefficients": [float(product[key]) for key in basis_keys],
        "rotated_vector_coefficients": [float(rotated[(1,)]), float(rotated[(2,)]), float(rotated[(3,)])],
        "pseudoscalar_square_coefficients": [float(pseudoscalar_square[key]) for key in basis_keys],
    }


def run_comparison_report(positive: dict[str, Any]) -> dict[str, Any]:
    kingdon_values = {
        "available": KINGDON_OK,
        "version": KINGDON_VERSION,
        "product_coefficients": positive.get("float_coefficients_shared_product", {}).get("coefficients"),
        "rotated_vector_coefficients": positive.get("rotor_sandwich_matches_reference_rotation", {}).get("rotated_vector_coefficients"),
        "pseudoscalar_square_coefficients": positive.get("pseudoscalar_square_minus_one", {}).get("square_coefficients"),
        "supports_float_coefficients": positive.get("float_coefficients_shared_product", {}).get("pass") is True,
        "supports_torch_autograd_coefficients": positive.get("torch_coefficients_shared_product_and_autograd", {}).get("pass") is True,
        "supports_sympy_symbolic_coefficients": positive.get("sympy_symbolic_shared_product_closed_form", {}).get("pass") is True,
    }
    torch_ga_values = _torch_ga_shared_values()
    clifford_values = _clifford_shared_values()

    product_agreement = {
        "kingdon_vs_torch_ga": bool(
            torch_ga_values.get("available")
            and _allclose(kingdon_values["product_coefficients"], torch_ga_values["product_coefficients"])
        ),
        "kingdon_vs_clifford": bool(
            clifford_values.get("available")
            and _allclose(kingdon_values["product_coefficients"], clifford_values["product_coefficients"])
        ),
    }
    rotor_agreement = {
        "kingdon_vs_torch_ga": bool(
            torch_ga_values.get("available")
            and _allclose(kingdon_values["rotated_vector_coefficients"], torch_ga_values["rotated_vector_coefficients"])
        ),
        "kingdon_vs_clifford": bool(
            clifford_values.get("available")
            and _allclose(kingdon_values["rotated_vector_coefficients"], clifford_values["rotated_vector_coefficients"])
        ),
    }
    pseudoscalar_agreement = {
        "kingdon_vs_torch_ga": bool(
            torch_ga_values.get("available")
            and _allclose(kingdon_values["pseudoscalar_square_coefficients"], torch_ga_values["pseudoscalar_square_coefficients"])
        ),
        "kingdon_vs_clifford": bool(
            clifford_values.get("available")
            and _allclose(kingdon_values["pseudoscalar_square_coefficients"], clifford_values["pseudoscalar_square_coefficients"])
        ),
    }

    replacement_ready = bool(
        all(product_agreement.values())
        and all(rotor_agreement.values())
        and all(pseudoscalar_agreement.values())
        and kingdon_values["supports_torch_autograd_coefficients"]
        and kingdon_values["supports_sympy_symbolic_coefficients"]
    )
    verdict = (
        "kingdon is the stronger replacement candidate for Cl(3) capability work: it matches torch_ga and clifford on the shared "
        "numeric fixture while using one MultiVector API for float, torch-autograd, and sympy-symbolic coefficients. Replacement "
        "should still stay capability-scoped until downstream torch_ga rows are rerun against kingdon."
        if replacement_ready
        else "kingdon is not replacement-ready on this receipt because at least one shared fixture or backend-flexibility check failed."
    )
    return {
        "shared_fixture": {
            "basis": BASIS,
            "product_coefficients_input": PRODUCT_COEFFS,
            "product_fixed_input": PRODUCT_FIXED,
            "rotor_angle_radians": 0.73,
            "signature": "Cl(3,0,0)",
        },
        "kingdon": kingdon_values,
        "torch_ga": torch_ga_values,
        "clifford": clifford_values,
        "agreement": {
            "product_coefficients": product_agreement,
            "rotor_rotation": rotor_agreement,
            "pseudoscalar_square": pseudoscalar_agreement,
        },
        "adequacy_verdict": {
            "api_quality": "good: direct Algebra and operator-overloaded MultiVector API; explicit basis-order extraction needed because internal keys are bitmask ordered",
            "backend_flexibility": "strong on this fixture: float scalars, torch tensors with finite nonzero autograd gradient, and sympy symbols all pass through the same product expression",
            "replacement_decision": verdict,
            "replacement_ready_for_capability_scoped_rows": replacement_ready,
        },
        "not_pass_fail": False,
    }


def _all_pass(section: dict[str, Any]) -> bool:
    return bool(section) and all(bool(v.get("pass", False)) for v in section.values())


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    comparison = run_comparison_report(pos)

    summary = {
        "positive_all_pass": _all_pass(pos),
        "negative_all_pass": _all_pass(neg),
        "boundary_all_pass": _all_pass(bnd),
        "comparison_all_pass": bool(
            comparison["adequacy_verdict"]["replacement_ready_for_capability_scoped_rows"]
        ),
        "importable": KINGDON_OK,
    }
    summary["all_pass"] = bool(
        summary["importable"]
        and summary["positive_all_pass"]
        and summary["negative_all_pass"]
        and summary["boundary_all_pass"]
        and summary["comparison_all_pass"]
    )

    results = {
        "name": "sim_kingdon_capability",
        "purpose": "Tool-capability isolation probe for kingdon Cl(3) operations and backend-flexible geometric products.",
        "classification": classification,
        "kingdon_version": KINGDON_VERSION,
        "kingdon_origin": KINGDON_ORIGIN,
        "kingdon_importable": KINGDON_OK,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "comparison": comparison,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
        "operation_sequence": [
            "install and import kingdon in the canonical Codex Ratchet Python env",
            "instantiate kingdon.Algebra(3,0,0) and check Cl(3) blade metadata",
            "measure e1/e2 anticommutation using kingdon MultiVector products",
            "rotate a basis vector by explicit rotor sandwich R*v*~R and compare against a trigonometric reference",
            "check Cl(3) pseudoscalar square equals -1",
            "run the shared multivector product with float coefficients",
            "run the same product with torch tensor coefficients and differentiate the product norm",
            "run the same product with sympy symbolic coefficients and compare the simplified closed form",
            "run negative controls for same-blade zero gap and wrong-signature pseudoscalar square",
            "run scalar and full-pseudoscalar boundary fixtures",
            "compare shared fixture values against torch_ga and clifford for replacement decisions",
        ],
        "carrier_topology": "finite Cl(3) kingdon Algebra fixtures only; no spinor geometry, bridge, axis, GStack, or nonclassical admission is claimed",
        "observable": {
            "blade_count": "len(Algebra(3,0,0).blades)",
            "anticommutation_gap": "norm((e1*e2) - (e2*e1)) and zero anticommutator residual",
            "rotor_residual": "L2 residual between R*v*~R vector coefficients and reference rotation",
            "pseudoscalar_square": "Cl(3) pseudoscalar product coefficients",
            "backend_flexibility": "same kingdon product expression over float, torch, and sympy coefficients",
            "autograd_gradient": "finite nonzero gradient of product norm with respect to torch multivector coefficients",
            "controls": "same-blade zero gap, wrong-signature pseudoscalar square, scalar grade-0, and full pseudoscalar boundaries",
        },
        "pass_fail_predicate": "kingdon must import; every positive, negative, boundary, and shared-fixture comparison check must pass. Adequacy feeds replacement decisions only within this capability scope.",
        "graveyards": [
            "kingdon as a mere import without direct Algebra/MultiVector witnesses",
            "same-blade product falsely reported as a noncommuting gap",
            "wrong metric silently producing the same pseudoscalar square as Cl(3,0)",
            "rotor sandwich accepted without comparison to a reference rotation",
            "backend-agnostic claim accepted without float/torch/sympy product parity",
            "torch backend accepted without finite nonzero autograd through a kingdon product",
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
        source_name="sim_kingdon_capability",
        target="Use as bounded kingdon capability evidence before kingdon load-bearing labels or torch_ga replacement decisions.",
    )

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "kingdon_capability_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"summary.all_pass = {summary['all_pass']}")
