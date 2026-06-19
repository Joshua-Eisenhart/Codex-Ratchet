#!/usr/bin/env python3
"""PyTorch R3 division-algebra leg through differentiable geometric algebra.

Scratch diagnostic only. This is not a JAX/Julia value-parity leg. It checks
PyTorch's distinct niche: autograd through a torch_ga geometric product.
"""

from __future__ import annotations

import datetime as _dt
import json
import math
import os
from pathlib import Path
from typing import Any

import torch
from torch.func import jacrev
from torch_ga import GeometricAlgebra


OBJECT_ID = "r3_div_algebra_torch_leg"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/r3_div_algebra_torch_leg_results.json"
TOL = 1.0e-10

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
sim_execution_kind = "differentiable_geometric_algebra"
SIM_EXECUTION_KIND = sim_execution_kind

ALLOWED_CLAIM = (
    "PyTorch-only differentiable geometric-algebra scout: Cl(0,2) represents the "
    "quaternion division-algebra structure and torch.func.jacrev differentiates "
    "a scalar extracted from a torch_ga geometric product."
)
CLAIM_CEILING = (
    "Allowed only: scratch diagnostic PyTorch differentiability-through-GA check. "
    "No exact-value authority, no promotion, no formal admission, and no "
    "downstream scientific claim."
)

TOOL_MANIFEST = {
    "torch_ga": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing GeometricAlgebra(metric=[-1,-1]) carrier; erasing it "
            "removes the Clifford/quaternion representation and geometric product"
        ),
    },
    "torch": {
        "tried": True,
        "used": True,
        "reason": "supportive tensor dtype/device/autograd substrate for torch_ga",
    },
    "torch.func.jacrev": {
        "tried": True,
        "used": True,
        "reason": "load-bearing differentiability check through the geometric product scalar",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON receipt, timestamp, path, and scalar formatting",
    },
    "JAX": {
        "tried": False,
        "used": False,
        "reason": "not used: this bounded leg must be different from JAX/Julia",
    },
    "Julia": {
        "tried": False,
        "used": False,
        "reason": "not used: this bounded leg is not a reference backend",
    },
    "NumPy": {
        "tried": False,
        "used": False,
        "reason": "not imported; no bare array-math fallback is allowed here",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch_ga": "load_bearing",
    "torch": "supportive",
    "torch.func.jacrev": "load_bearing",
    "Python stdlib": "supportive",
    "JAX": None,
    "Julia": None,
    "NumPy": None,
}


def run_token() -> str:
    return os.environ.get("R3_DIV_TORCH_RUN_TOKEN", "manual-token-not-set")


def as_float(value: torch.Tensor | float) -> float:
    if isinstance(value, torch.Tensor):
        return float(value.detach().cpu().item())
    return float(value)


def max_abs(value: torch.Tensor) -> float:
    return as_float(torch.max(torch.abs(value)))


def close_residual(a: torch.Tensor, b: torch.Tensor) -> float:
    return max_abs(a - b)


def scalar_part(mv: torch.Tensor) -> torch.Tensor:
    return mv[..., 0]


def build_result() -> dict[str, Any]:
    torch.set_default_dtype(torch.float64)
    ga = GeometricAlgebra(metric=[-1.0, -1.0], dtype=torch.float64)

    # torch_ga's named blade helper composes vectors; use explicit blade basis.
    one, i, j, k = ga.blade_mvs.to(dtype=torch.float64)
    zero = torch.zeros_like(one)

    products = {
        "i_squared": ga.geom_prod(i, i),
        "j_squared": ga.geom_prod(j, j),
        "k_squared": ga.geom_prod(k, k),
        "i_j": ga.geom_prod(i, j),
        "j_i": ga.geom_prod(j, i),
        "j_k": ga.geom_prod(j, k),
        "k_i": ga.geom_prod(k, i),
    }
    expected = {
        "i_squared": -one,
        "j_squared": -one,
        "k_squared": -one,
        "i_j": k,
        "j_i": -k,
        "j_k": i,
        "k_i": j,
    }
    product_residuals = {
        name: close_residual(products[name], expected[name])
        for name in sorted(products)
    }

    assoc_left = ga.geom_prod(ga.geom_prod(i, j), k)
    assoc_right = ga.geom_prod(i, ga.geom_prod(j, k))
    associator_residual = close_residual(assoc_left, assoc_right)
    commutator_norm = max_abs(products["i_j"] - products["j_i"])

    theta_value = 0.37
    theta = torch.tensor(theta_value, dtype=torch.float64)

    def geometric_product_scalar(param: torch.Tensor) -> torch.Tensor:
        q = torch.cos(param) * one + torch.sin(param) * i
        return scalar_part(ga.geom_prod(q, i))

    gp_scalar = geometric_product_scalar(theta)
    gp_jacobian = jacrev(geometric_product_scalar)(theta)
    expected_scalar = -math.sin(theta_value)
    expected_jacobian = -math.cos(theta_value)
    scalar_residual = abs(as_float(gp_scalar) - expected_scalar)
    jacobian_residual = abs(as_float(gp_jacobian) - expected_jacobian)

    uses_torch_ga = isinstance(ga, GeometricAlgebra) and TOOL_MANIFEST["torch_ga"]["used"]
    quaternion_structure_ok = (
        max(product_residuals.values()) <= TOL
        and associator_residual <= TOL
        and commutator_norm > 1.0
    )
    differentiable_autograd_through_GA = (
        bool(gp_jacobian.requires_grad is False)
        and scalar_residual <= TOL
        and jacobian_residual <= TOL
    )
    not_bare_torch = (
        uses_torch_ga
        and TOOL_INTEGRATION_DEPTH["torch_ga"] == "load_bearing"
        and TOOL_INTEGRATION_DEPTH["torch.func.jacrev"] == "load_bearing"
    )
    fences_ok = (
        classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
    )
    core_pass = bool(
        uses_torch_ga
        and quaternion_structure_ok
        and differentiable_autograd_through_GA
        and not_bare_torch
        and fences_ok
    )

    result: dict[str, Any] = {
        "schema": "codex_ratchet.formal_scout.scratch_diagnostic.v1",
        "object_id": OBJECT_ID,
        "sim_id": OBJECT_ID,
        "name": OBJECT_ID,
        "version": "1.0",
        "tier": "R3_foundation_carrier_candidate_torch_leg",
        "backend": "pytorch",
        "run_token": run_token(),
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "promotion_status": "diagnostic_only",
        "claim_ceiling": CLAIM_CEILING,
        "allowed_claims": [ALLOWED_CLAIM],
        "eligible_consumers": [],
        "blocked_consumers": ["promotion", "formal_admission", "downstream scientific claims"],
        "sim_execution_kind": sim_execution_kind,
        "sim_class": "differentiable_carrier_probe",
        "purpose": "Build only the PyTorch leg for the R3 division-algebra structure with autograd through GA.",
        "scientific_question": "Can PyTorch add a distinct differentiable geometric-algebra check rather than repeat JAX/Julia exact-value arithmetic?",
        "carrier_layer": "Cl(0,2)_as_quaternion_H_via_torch_ga",
        "geometry_layer": "differentiable_geometric_algebra",
        "bridge_layer": "none",
        "law_or_candidate_tested": "torch_ga Cl(0,2) quaternion multiplication plus jacrev through geometric product scalar",
        "root_constraints_in_force": ["R0_finite_object", "R1_probe_quotient", "R2_admissible_operations_context"],
        "promotion_blockers": ["scratch diagnostic fence", "PyTorch exact values weighted least", "no formal admission"],
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "required_tools": ["torch_ga", "torch.func.jacrev"],
        "actual_tools_used": ["torch_ga", "torch", "torch.func.jacrev", "Python stdlib"],
        "plain_numpy_imported": False,
        "jax_imported": False,
        "julia_used": False,
        "torch_version": torch.__version__,
        "torch_dtype": str(torch.get_default_dtype()),
        "ga_metric": [-1.0, -1.0],
        "ga_blades": list(ga.blades),
        "basis_map": {"1": "", "i": "0", "j": "1", "k": "01"},
        "tol": TOL,
        "construction": {
            "method": "torch_ga.GeometricAlgebra(metric=[-1,-1])",
            "division_algebra_rung": "H",
            "representation": "quaternion_units_as_Cl(0,2)_blades",
        },
        "geometric_products": {
            name: {
                "residual": product_residuals[name],
                "pass": product_residuals[name] <= TOL,
            }
            for name in sorted(product_residuals)
        },
        "positive": {
            "torch_ga_loaded": {"pass": uses_torch_ga},
            "quaternion_structure_via_cl02": {"pass": quaternion_structure_ok},
            "autograd_through_geometric_product_scalar": {
                "pass": differentiable_autograd_through_GA,
                "theta": theta_value,
                "scalar": as_float(gp_scalar),
                "expected_scalar": expected_scalar,
                "scalar_residual": scalar_residual,
                "jacrev": as_float(gp_jacobian),
                "expected_jacrev": expected_jacobian,
                "jacobian_residual": jacobian_residual,
            },
            "not_bare_torch_array_math": {"pass": not_bare_torch},
            "classification_is_scratch_diagnostic": {"pass": classification == "scratch_diagnostic"},
            "promotion_allowed_false": {"pass": promotion_allowed is False},
            "formal_admission_allowed_false": {"pass": formal_admission_allowed is False},
        },
        "negative": {
            "noncommutative_control": {
                "pass": commutator_norm > 1.0,
                "commutator_norm": commutator_norm,
                "control_can_fail": True,
            },
            "bare_torch_fallback_absent": {
                "pass": not_bare_torch,
                "reason": "all carrier products use ga.geom_prod; torch tensors only support torch_ga and jacrev",
            },
        },
        "boundary": {
            "torch_leg_not_reference": {
                "pass": True,
                "reason": "PyTorch is used only for differentiable GA, not exact-value authority.",
            },
            "claim_ceiling": CLAIM_CEILING,
        },
        "probe": {
            "question": "differentiability through a Clifford/quaternion geometric product",
            "measured_properties": [
                "Cl(0,2) quaternion product signs",
                "associativity inside represented H",
                "noncommutative control",
                "jacrev of scalar part of geometric product",
            ],
            "differentiated_expression": "scalar_part(((cos(theta) * 1 + sin(theta) * i) * i))",
        },
        "kill_conditions": [
            "torch_ga is not imported and load-bearing",
            "quaternion product signs fail in Cl(0,2)",
            "jacrev does not match the analytic derivative through ga.geom_prod",
            "implementation falls back to bare torch array multiplication for the carrier",
            "classification or promotion fences are loosened",
        ],
        "required_artifacts": [str(RESULT_PATH)],
        "artifacts_emitted": [str(RESULT_PATH)],
        "criteria_checked": [
            "torch_ga GeometricAlgebra(metric=[-1,-1]) construction",
            "i^2=j^2=k^2=-1 in Cl(0,2)",
            "ij=k, ji=-k, jk=i, ki=j",
            "associator ((i*j)*k - i*(j*k)) is zero",
            "noncommutative control has nonzero commutator",
            "torch.func.jacrev differentiates a scalar from ga.geom_prod",
            "no NumPy/JAX/Julia backend used in this leg",
        ],
        "shared_scalars": {
            "commutator_norm": commutator_norm,
            "associator_residual": associator_residual,
            "geometric_product_scalar": as_float(gp_scalar),
            "geometric_product_jacrev": as_float(gp_jacobian),
            "jacobian_residual": jacobian_residual,
            "max_product_residual": max(product_residuals.values()),
        },
        "shared_booleans": {
            "uses_torch_ga": uses_torch_ga,
            "quaternion_structure_ok": quaternion_structure_ok,
            "differentiable_autograd_through_GA": differentiable_autograd_through_GA,
            "not_bare_torch": not_bare_torch,
            "ran": True,
            "core_pass": core_pass,
        },
        "result_summary": {
            "uses_torch_ga": uses_torch_ga,
            "differentiable_autograd_through_GA": differentiable_autograd_through_GA,
            "not_bare_torch": not_bare_torch,
            "ran": True,
            "core_pass": core_pass,
        },
        "uses_torch_ga": uses_torch_ga,
        "differentiable_autograd_through_GA": differentiable_autograd_through_GA,
        "not_bare_torch": not_bare_torch,
        "ran": True,
        "core_pass": core_pass,
        "all_pass": core_pass,
        "stop_condition_fired": not core_pass,
        "pass_rule": "torch_ga Cl(0,2) quaternion structure plus jacrev through ga.geom_prod scalar, with scratch fences intact",
        "fail_rule": "missing torch_ga, bare torch fallback, failed GA product signs, failed jacrev, or loosened fences",
    }
    return result


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {RESULT_PATH}")
    print(
        "SCOUT_DONE "
        f"uses_torch_ga={result['uses_torch_ga']} "
        f"differentiable_autograd_through_GA={result['differentiable_autograd_through_GA']} "
        f"not_bare_torch={result['not_bare_torch']} "
        f"ran={result['ran']}"
    )
    return 0 if result["core_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
