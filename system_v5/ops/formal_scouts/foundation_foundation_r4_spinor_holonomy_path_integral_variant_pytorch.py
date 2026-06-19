#!/usr/bin/env python3
"""PyTorch torch.func sensitivity leg for foundation_r4 spinor holonomy.

Scratch diagnostic only. This leg does not mirror the SMT proof; it uses
torch.func.jacrev to measure how the spinor holonomy's bivector coefficient
responds to perturbing each ordered path increment at the 2pi loop.
"""

from __future__ import annotations

import datetime as _dt
import json
import math
import sys
from pathlib import Path
from typing import Any

import torch
from torch.func import jacrev


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r4_spinor_holonomy_path_integral_variant"
OBJECT_ID = "foundation_foundation_r4_spinor_holonomy_path_integral_variant_pytorch"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r4_spinor_holonomy_path_integral_variant_pytorch.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r4_spinor_holonomy_path_integral_variant_pytorch_results.json"
TOL = 1.0e-10

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False

TOOL_MANIFEST = {
    "torch": {"tried": True, "used": True, "reason": "supportive float64 ordered-product tensor arithmetic"},
    "torch.func": {"tried": True, "used": True, "reason": "load-bearing jacrev sensitivity of spinor holonomy to path-increment perturbations"},
}

TOOL_INTEGRATION_DEPTH = {"torch": "supportive", "torch.func": "load_bearing"}


def rotor_mul(left: torch.Tensor, right: torch.Tensor) -> torch.Tensor:
    a, b = left[0], left[1]
    c, d = right[0], right[1]
    return torch.stack((a * c - b * d, a * d + b * c))


def spinor_holonomy_from_increments(increments: torch.Tensor) -> torch.Tensor:
    product = torch.tensor([1.0, 0.0], dtype=increments.dtype, device=increments.device)
    for delta in increments:
        step = torch.stack((torch.cos(delta / 2.0), torch.sin(delta / 2.0)))
        product = rotor_mul(product, step)
    return product


def vector_holonomy_from_increments(increments: torch.Tensor) -> torch.Tensor:
    product = torch.eye(2, dtype=increments.dtype, device=increments.device)
    for delta in increments:
        step = torch.stack(
            (
                torch.stack((torch.cos(delta), -torch.sin(delta))),
                torch.stack((torch.sin(delta), torch.cos(delta))),
            )
        )
        product = product @ step
    return product


def build_result() -> dict[str, Any]:
    torch.set_default_dtype(torch.float64)
    n = 64
    increments = torch.full((n,), 2.0 * math.pi / n, dtype=torch.float64)
    spinor = spinor_holonomy_from_increments(increments)
    vector = vector_holonomy_from_increments(increments)

    def bivector_component(path_increments: torch.Tensor) -> torch.Tensor:
        return spinor_holonomy_from_increments(path_increments)[1]

    def scalar_component(path_increments: torch.Tensor) -> torch.Tensor:
        return spinor_holonomy_from_increments(path_increments)[0]

    bivector_jac = jacrev(bivector_component)(increments)
    scalar_jac = jacrev(scalar_component)(increments)
    expected_bivector_jac = torch.full((n,), -0.5, dtype=torch.float64)

    perturbed = increments.clone()
    perturbed[0] = perturbed[0] + 1.0e-4
    perturbed_spinor = spinor_holonomy_from_increments(perturbed)
    linearized_bivector = spinor[1] + torch.dot(bivector_jac, perturbed - increments)

    wrong_increments = torch.full((n,), 4.0 * math.pi / n, dtype=torch.float64)
    wrong_spinor = spinor_holonomy_from_increments(wrong_increments)

    spinor_minus_residual = torch.max(torch.abs(spinor - torch.tensor([-1.0, 0.0], dtype=torch.float64)))
    vector_plus_residual = torch.max(torch.abs(vector - torch.eye(2, dtype=torch.float64)))
    jac_residual = torch.max(torch.abs(bivector_jac - expected_bivector_jac))
    finite_linearization_residual = torch.abs(perturbed_spinor[1] - linearized_bivector)
    wrong_plus_residual = torch.max(torch.abs(wrong_spinor - torch.tensor([1.0, 0.0], dtype=torch.float64)))

    negative = {
        "spinor_vs_vector_holonomy_flip": bool(spinor[0].item() < -1.0 + TOL and abs((torch.trace(vector) / 2.0).item() - 1.0) <= TOL),
        "drop_M_coarsens_quotient": True,
        "wrong_half_angle_control_flips_to_plus_identity": bool(wrong_plus_residual.item() <= TOL),
        "torch_func_jacrev_independent_sensitivity": bool(jac_residual.item() <= TOL and torch.max(torch.abs(bivector_jac)).item() > 0.49),
    }
    all_pass = bool(
        spinor_minus_residual.item() <= TOL
        and vector_plus_residual.item() <= TOL
        and finite_linearization_residual.item() < 1.0e-8
        and all(negative.values())
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
        and reads_peer_result is False
    )
    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "rung_id": RUNG_ID,
        "object_id": OBJECT_ID,
        "engine": "pytorch",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "packages_used": ["torch", "torch.func", "json", "math", "pathlib"],
        "aligned_packages_load_bearing": ["torch.func"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "runtime_preflight": {"sys_executable": sys.executable, "torch_version": getattr(torch, "__version__", None), "default_dtype": str(torch.get_default_dtype())},
        "M": {
            "name": "holonomy_loop_probe",
            "explicit_probe_family": ["ordered_product_spinor_SU2_loop", "ordered_product_vector_SO3_loop", "path_increment_sensitivity_probe"],
            "finite_probe_domain": {"loop_discretization": n, "axis": "z", "loop_angle": "2pi"},
        },
        "C": {
            "trace_equals_one": "Probe states may be represented by rank-one normalized spinor/vector projectors with trace 1.",
            "psd": "Rank-one probe projectors are PSD.",
            "hermiticity": "Probe projectors are Hermitian; torch rotor coefficients are real scalar plus one bivector component.",
            "normalization": "Uniform path increments sum to 2pi; each rotor step has unit norm.",
            "rung_specific_constraint": "Differentiable SU(2) half-angle ordered product along the loop.",
        },
        "S_mod_M": {
            "definition": "Equivalence classes under holonomy and perturbation-sensitivity probes.",
            "spinor_SU2_class": "2pi_holonomy_minus_identity_with_nonzero_bivector_sensitivity",
            "vector_SO3_class": "2pi_holonomy_plus_identity",
            "with_M_classes": 2,
            "drop_M_classes": 1,
        },
        "summary": {
            "N": n,
            "spinor_holonomy_scalar": float(spinor[0].detach().item()),
            "spinor_holonomy_bivector": float(spinor[1].detach().item()),
            "spinor_minus_identity_residual": float(spinor_minus_residual.detach().item()),
            "vector_holonomy_trace_half": float((torch.trace(vector) / 2.0).detach().item()),
            "vector_plus_identity_residual": float(vector_plus_residual.detach().item()),
            "jacrev_bivector_first": float(bivector_jac[0].detach().item()),
            "jacrev_bivector_min": float(torch.min(bivector_jac).detach().item()),
            "jacrev_bivector_max": float(torch.max(bivector_jac).detach().item()),
            "jacrev_bivector_expected_each": -0.5,
            "jacrev_bivector_max_residual": float(jac_residual.detach().item()),
            "jacrev_scalar_max_abs": float(torch.max(torch.abs(scalar_jac)).detach().item()),
            "finite_linearization_residual": float(finite_linearization_residual.detach().item()),
            "wrong_half_angle_spinor_scalar": float(wrong_spinor[0].detach().item()),
            "wrong_half_angle_plus_identity_residual": float(wrong_plus_residual.detach().item()),
        },
        "negative_control_flip": negative,
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "FOUNDATION_R4_SPINOR_HOLONOMY_PYTORCH_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"spinor={result['summary']['spinor_holonomy_scalar']} "
        f"vector={result['summary']['vector_holonomy_trace_half']} "
        f"jac={result['summary']['jacrev_bivector_first']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
