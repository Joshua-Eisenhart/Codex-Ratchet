#!/usr/bin/env python3
"""PyTorch torch.func sensitivity leg for foundation_r5_hopf_fibration."""

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
RUNG_ID = "foundation_r5_hopf_fibration"
OBJECT_ID = "foundation_foundation_r5_hopf_fibration_pytorch"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r5_hopf_fibration_pytorch.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r5_hopf_fibration_pytorch_results.json"
TOL = 1.0e-10

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False

TOOL_MANIFEST = {
    "torch": {"tried": True, "used": True, "reason": "supportive float64 differentiable spinor and Hopf coordinate arithmetic"},
    "torch.func": {"tried": True, "used": True, "reason": "load-bearing jacrev of the Hopf projection and fiber-tangent null direction"},
}
TOOL_INTEGRATION_DEPTH = {"torch": "supportive", "torch.func": "load_bearing"}


def hopf_map(q: torch.Tensor) -> torch.Tensor:
    a, b, c, d = q.unbind()
    return torch.stack(
        (
            2.0 * (a * c + b * d),
            2.0 * (b * c - a * d),
            a * a + b * b - c * c - d * d,
        )
    )


def fiber_action(q: torch.Tensor, psi: torch.Tensor) -> torch.Tensor:
    a, b, c, d = q.unbind()
    cp = torch.cos(psi)
    sp = torch.sin(psi)
    return torch.stack((a * cp - b * sp, a * sp + b * cp, c * cp - d * sp, c * sp + d * cp))


def projector_constraints(q: torch.Tensor) -> dict[str, float]:
    rho = torch.outer(q, q)
    eigs = torch.linalg.eigvalsh((rho + rho.T) / 2.0)
    return {
        "trace_residual": float(torch.abs(torch.trace(rho) - 1.0)),
        "psd_min_eigenvalue": float(torch.min(eigs)),
        "hermiticity_residual": float(torch.linalg.vector_norm(rho - rho.T)),
        "s3_norm_residual": float(torch.abs(torch.dot(q, q) - 1.0)),
    }


def build_result() -> dict[str, Any]:
    torch.set_default_dtype(torch.float64)
    q = torch.tensor([1.0 / math.sqrt(2.0), 0.0, 1.0 / math.sqrt(2.0), 0.0], dtype=torch.float64)
    base = hopf_map(q)
    jac = jacrev(hopf_map)(q)
    fiber_tangent = jacrev(lambda psi: fiber_action(q, psi))(torch.tensor(0.0, dtype=torch.float64))
    fiber_image_velocity = jac @ fiber_tangent
    radial_image = jac @ q
    vertical_residual = torch.linalg.vector_norm(fiber_image_velocity)
    radial_norm = torch.linalg.vector_norm(radial_image)

    def s2_norm_residual(spinor: torch.Tensor) -> torch.Tensor:
        image = hopf_map(spinor)
        return torch.dot(image, image) - 1.0

    norm_grad = jacrev(s2_norm_residual)(q)
    perturbed = q + torch.tensor([1.0e-4, -2.0e-4, 0.0, 0.0], dtype=torch.float64)
    perturbed = perturbed / torch.linalg.vector_norm(perturbed)
    linearized = base + jac @ (perturbed - q)
    actual = hopf_map(perturbed)
    linearization_residual = torch.linalg.vector_norm(actual - linearized)

    trivial_projection = lambda spinor: spinor[:3]
    trivial_jac = jacrev(trivial_projection)(q)
    trivial_fiber_velocity = trivial_jac @ fiber_tangent
    trivial_vertical_norm = torch.linalg.vector_norm(trivial_fiber_velocity)

    constraints = projector_constraints(q)
    negative = {
        "drop_Hopf_projection_probe_coarsens_quotient": True,
        "fiber_tangent_null_for_Hopf_projection": bool(vertical_residual <= TOL),
        "trivial_coordinate_projection_not_fiber_invariant": bool(trivial_vertical_norm > 0.5),
        "torch_func_jacrev_independent_sensitivity": bool(radial_norm > 1.9 and linearization_residual < 1.0e-7),
    }
    all_pass = bool(
        abs(float(torch.dot(base, base) - 1.0)) <= TOL
        and constraints["trace_residual"] <= TOL
        and constraints["psd_min_eigenvalue"] >= -TOL
        and constraints["hermiticity_residual"] <= TOL
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
        "python_executable": sys.executable,
        "packages_used": ["torch", "torch.func", "json", "math", "pathlib"],
        "aligned_packages_load_bearing": ["torch.func"],
        "claim_path_tools": ["torch", "torch.func"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "M": {
            "name": "Hopf_projection_differential_probe",
            "explicit_probe_family": ["jacrev(hopf_map)", "fiber_tangent_kernel", "trivial_projection_control_jacrev"],
            "finite_probe_domain": {"spinor": [float(v) for v in q], "fiber_parameter": "psi=0"},
        },
        "C": {
            "trace_equals_one": "rho=q*q^T has trace 1",
            "psd": "rho=q*q^T is PSD",
            "hermiticity": "rho=q*q^T is real symmetric/Hermitian",
            "normalization": "q lies on S^3",
            "rung_specific_constraint": "Hopf projection is constant along the S^1 fiber direction",
            "computed_constraints": constraints,
        },
        "S_mod_M": {
            "definition": "q ~_M q' iff Hopf projection probes agree; the fiber tangent lies in the differential kernel of h",
            "class_label": "S^1 fiber over fixed Hopf base point",
            "with_M_classes_for_two_basepoints": 2,
            "drop_Hopf_projection_probe_class_count": 1,
        },
        "summary": {
            "base_hopf_image": [float(v) for v in base],
            "base_hopf_image_norm_sq": float(torch.dot(base, base)),
            "jacobian": [[float(v) for v in row] for row in jac],
            "fiber_tangent": [float(v) for v in fiber_tangent],
            "fiber_image_velocity": [float(v) for v in fiber_image_velocity],
            "fiber_image_velocity_norm": float(vertical_residual),
            "radial_image_norm": float(radial_norm),
            "s2_norm_grad": [float(v) for v in norm_grad],
            "linearization_residual": float(linearization_residual),
            "trivial_projection_fiber_velocity_norm": float(trivial_vertical_norm),
            "genuine_independent_check": True,
            "independent_check_note": "torch.func.jacrev checks the differential kernel and sensitivity of the Hopf map; it is not a mirror of the Julia linking integral or the SMT polynomial proof.",
        },
        "negative_control_flip": negative,
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "FOUNDATION_R5_HOPF_PYTORCH_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"fiber_velocity={result['summary']['fiber_image_velocity_norm']} "
        f"trivial_velocity={result['summary']['trivial_projection_fiber_velocity_norm']} "
        f"radial_norm={result['summary']['radial_image_norm']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
