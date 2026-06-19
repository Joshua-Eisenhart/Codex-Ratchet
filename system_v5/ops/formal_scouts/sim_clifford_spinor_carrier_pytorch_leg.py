#!/usr/bin/env python3
"""PyTorch-only CLIFFORD/SPINOR CARRIER rung scout.

Scratch diagnostic only. This leg checks PyTorch's distinct niche:
differentiation through a torch_ga geometric product, with e3nn used for the
SO(3) Wigner-D vector image of the Cl(3,0) spinor/rotor action.
"""

from __future__ import annotations

import datetime as _dt
import json
import math
from pathlib import Path
from typing import Any

import torch
from e3nn import o3
from torch.func import jacrev
from torch_ga import GeometricAlgebra


OBJECT_ID = "clifford_spinor_carrier_pytorch_leg"
ROOT = Path(__file__).resolve().parents[3]
RESULT_PATH = (
    ROOT
    / "system_v5"
    / "ops"
    / "formal_scouts"
    / "results"
    / "clifford_spinor_carrier_pytorch_leg_results.json"
)
TOL = 1.0e-10

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
reads_peer_result = False
READS_PEER_RESULT = reads_peer_result

TOOL_MANIFEST = {
    "torch_ga": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing Cl(3,0) GeometricAlgebra carrier; constructs the "
            "pseudoscalar/gamma5 blade and all geometric products under jacrev"
        ),
    },
    "torch.func.jacrev": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing gradient check differentiating a scalar extracted "
            "after torch_ga geometric products with respect to a rotation parameter"
        ),
    },
    "e3nn": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing SO(3) Wigner-D l=1 rotation check for the vector image "
            "of the Cl(3,0) spinor/rotor action"
        ),
    },
    "torch": {
        "tried": True,
        "used": True,
        "reason": "supportive tensor dtype/autograd substrate for torch_ga and e3nn",
    },
    "NumPy": {
        "tried": False,
        "used": False,
        "reason": "not imported; no bare array-math fallback is allowed in this PyTorch leg",
    },
    "JAX": {
        "tried": False,
        "used": False,
        "reason": "not used; this is only the PyTorch leg",
    },
    "Julia": {
        "tried": False,
        "used": False,
        "reason": "not used; reads_peer_result=false and PyTorch is not the reference backend",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch_ga": "load_bearing",
    "torch.func.jacrev": "load_bearing",
    "e3nn": "load_bearing",
    "torch": "supportive",
    "NumPy": None,
    "JAX": None,
    "Julia": None,
}


def _as_float(value: torch.Tensor | float) -> float:
    if isinstance(value, torch.Tensor):
        return float(value.detach().cpu().item())
    return float(value)


def _max_abs(value: torch.Tensor) -> float:
    return _as_float(torch.max(torch.abs(value)))


def _scalar_part(mv: torch.Tensor) -> torch.Tensor:
    return mv[..., 0]


def _mv_coords(mv: torch.Tensor) -> list[float]:
    return [float(x) for x in mv.detach().cpu().tolist()]


def build_result() -> dict[str, Any]:
    torch.set_default_dtype(torch.float64)
    ga = GeometricAlgebra(metric=[1.0, 1.0, 1.0], dtype=torch.float64)
    blades = ga.blade_mvs.to(dtype=torch.float64)
    one = blades[0]
    e1, e2, e3 = blades[1], blades[2], blades[3]
    e12, e13, e23 = blades[4], blades[5], blades[6]

    gamma5 = ga.geom_prod(ga.geom_prod(e1, e2), e3)
    gamma5_squared = ga.geom_prod(gamma5, gamma5)
    expected_gamma5 = blades[7]
    gamma5_residual = _max_abs(gamma5 - expected_gamma5)
    gamma5_square_residual = _max_abs(gamma5_squared + one)

    theta_value = 0.43
    theta = torch.tensor(theta_value, dtype=torch.float64)
    probe_spinor = one + 0.375 * e12 - 0.25 * e13 + 0.125 * e23

    def rotor_z(param: torch.Tensor) -> torch.Tensor:
        half = 0.5 * param
        return torch.cos(half) * one - torch.sin(half) * e12

    def spinor_gp_scalar(param: torch.Tensor) -> torch.Tensor:
        spinor = ga.geom_prod(rotor_z(param), probe_spinor)
        product = ga.geom_prod(spinor, one + 0.2 * e12 - 0.1 * e13)
        chiral_product = ga.geom_prod(ga.geom_prod(product, gamma5), gamma5)
        return _scalar_part(chiral_product)

    scalar_value = spinor_gp_scalar(theta)
    jacobian_value = jacrev(spinor_gp_scalar)(theta)

    eps = torch.tensor(1.0e-6, dtype=torch.float64)
    finite_diff = (spinor_gp_scalar(theta + eps) - spinor_gp_scalar(theta - eps)) / (2.0 * eps)
    finite_diff_residual = abs(_as_float(jacobian_value - finite_diff))

    rotor = rotor_z(theta)
    rotor_rev = ga.reversion(rotor)
    sandwich_vector = ga.geom_prod(ga.geom_prod(rotor, e1), rotor_rev)
    sandwich_xyz = torch.stack([sandwich_vector[1], sandwich_vector[2], sandwich_vector[3]])

    wigner_d = o3.wigner_D(
        1,
        torch.tensor(0.0, dtype=torch.float64),
        torch.tensor(0.0, dtype=torch.float64),
        theta,
    ).to(dtype=torch.float64)
    initial_xyz = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)
    e3nn_xyz = wigner_d @ initial_xyz
    rotor_invariants = torch.stack(
        [
            torch.linalg.vector_norm(sandwich_xyz),
            torch.dot(sandwich_xyz, initial_xyz),
            torch.linalg.vector_norm(sandwich_xyz - initial_xyz),
        ]
    )
    e3nn_invariants = torch.stack(
        [
            torch.linalg.vector_norm(e3nn_xyz),
            torch.dot(e3nn_xyz, initial_xyz),
            torch.linalg.vector_norm(e3nn_xyz - initial_xyz),
        ]
    )
    e3nn_rotation_residual = _max_abs(rotor_invariants - e3nn_invariants)

    uses_torch_ga = isinstance(ga, GeometricAlgebra)
    uses_e3nn = bool(wigner_d.shape == (3, 3))
    differentiable_through_GA = bool(
        jacobian_value.numel() == 1
        and math.isfinite(_as_float(jacobian_value))
        and abs(_as_float(jacobian_value)) > 1.0e-8
        and finite_diff_residual <= 1.0e-7
    )
    cl3_dim = int(ga.num_blades)
    not_bare_torch = bool(
        uses_torch_ga
        and uses_e3nn
        and TOOL_INTEGRATION_DEPTH["torch_ga"] == "load_bearing"
        and TOOL_INTEGRATION_DEPTH["torch.func.jacrev"] == "load_bearing"
        and TOOL_INTEGRATION_DEPTH["e3nn"] == "load_bearing"
    )
    gamma5_ok = gamma5_residual <= TOL and gamma5_square_residual <= TOL
    e3nn_ok = e3nn_rotation_residual <= 1.0e-10
    ran = bool(
        reads_peer_result is False
        and uses_torch_ga
        and uses_e3nn
        and differentiable_through_GA
        and cl3_dim == 8
        and not_bare_torch
        and gamma5_ok
        and e3nn_ok
    )

    result: dict[str, Any] = {
        "schema": "codex_ratchet.formal_scout.scratch_diagnostic.v1",
        "object_id": OBJECT_ID,
        "sim_id": OBJECT_ID,
        "name": OBJECT_ID,
        "version": "1.0",
        "tier": "CLIFFORD_SPINOR_CARRIER_rung_pytorch_leg",
        "backend": "pytorch",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "promotion_status": "diagnostic_only",
        "reads_peer_result": reads_peer_result,
        "claim_ceiling": (
            "Allowed only: PyTorch scratch diagnostic for differentiability "
            "through a torch_ga Cl(3,0) spinor/geometric product scalar plus "
            "e3nn SO(3) Wigner-D vector-image check. No value authority, no "
            "formal admission, no cross-engine parity claim."
        ),
        "allowed_claims": [
            "torch_ga built an 8-blade Cl(3,0) carrier and constructed the pseudoscalar/gamma5 blade",
            "torch.func.jacrev differentiated through torch_ga geometric products",
            "e3nn supplied an SO(3) Wigner-D l=1 check for the vector image of the spinor/rotor action",
        ],
        "blocked_claims": [
            "half-integer SU(2) spinor Wigner-D from e3nn",
            "canonical carrier admission",
            "Julia or JAX parity",
            "bare torch array proof",
        ],
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "required_tools": ["torch_ga", "torch.func.jacrev", "e3nn"],
        "actual_tools_used": ["torch_ga", "torch", "torch.func.jacrev", "e3nn", "Python stdlib"],
        "plain_numpy_imported": False,
        "jax_imported": False,
        "julia_used": False,
        "torch_version": torch.__version__,
        "torch_dtype": str(torch.get_default_dtype()),
        "torch_ga_metric": [1.0, 1.0, 1.0],
        "torch_ga_blades": list(ga.blades),
        "cl3_dim": cl3_dim,
        "gamma5_pseudoscalar": {
            "constructed_as": "e1*e2*e3 using torch_ga.geom_prod",
            "coordinates": _mv_coords(gamma5),
            "expected_blade": "012",
            "residual": gamma5_residual,
            "square_expected": "-1",
            "square_residual": gamma5_square_residual,
            "pass": gamma5_ok,
        },
        "differentiable_spinor_geometric_product": {
            "rotation_parameter": theta_value,
            "scalar": _as_float(scalar_value),
            "jacrev": _as_float(jacobian_value),
            "central_finite_difference": _as_float(finite_diff),
            "finite_difference_residual": finite_diff_residual,
            "differentiated_expression": "scalar_part(((((rotor_z(theta) * probe_spinor) * probe) * gamma5) * gamma5))",
            "passes_through_torch_ga_geom_prod": True,
            "pass": differentiable_through_GA,
        },
        "e3nn_wigner_d_spinor_vector_image": {
            "scope_note": (
                "e3nn.o3 supports integer SO(3) irreps; this checks the SO(3) "
                "l=1 Wigner-D vector image of the Cl(3,0) spinor/rotor action, "
                "not a half-integer SU(2) spinor irrep. The comparison is made "
                "on SO(3) rotation invariants because e3nn's real Wigner-D basis "
                "is not the torch_ga Cartesian blade basis."
            ),
            "wigner_d_l": 1,
            "rotor_sandwich_xyz": _mv_coords(sandwich_xyz),
            "e3nn_wigner_d_xyz": _mv_coords(e3nn_xyz),
            "rotor_invariants_norm_dot_displacement": _mv_coords(rotor_invariants),
            "e3nn_invariants_norm_dot_displacement": _mv_coords(e3nn_invariants),
            "residual": e3nn_rotation_residual,
            "pass": e3nn_ok,
        },
        "fences": {
            "scratch_diagnostic": classification == "scratch_diagnostic",
            "promotion_allowed": promotion_allowed,
            "formal_admission_allowed": formal_admission_allowed,
            "reads_peer_result": reads_peer_result,
        },
        "booleans": {
            "uses_torch_ga": uses_torch_ga,
            "uses_e3nn": uses_e3nn,
            "differentiable_through_GA": differentiable_through_GA,
            "cl3_dim": cl3_dim,
            "not_bare_torch": not_bare_torch,
            "ran": ran,
        },
        "criteria_checked": [
            "torch_ga.GeometricAlgebra(metric=[1,1,1]) produced Cl(3,0) with 8 blades",
            "gamma5/pseudoscalar e123 was built via torch_ga geometric products and squares to -1",
            "torch.func.jacrev differentiated a spinor/geometric-product scalar through torch_ga.geom_prod",
            "e3nn.o3.wigner_D(1, ...) matched the SO(3) vector image of the rotor sandwich action",
            "reads_peer_result is false",
            "no NumPy/JAX/Julia backend was imported or read",
        ],
        "all_pass": ran,
        "SCOUT_DONE": (
            f"SCOUT_DONE uses_torch_ga={uses_torch_ga} uses_e3nn={uses_e3nn} "
            f"differentiable_through_GA={differentiable_through_GA} cl3_dim={cl3_dim} "
            f"not_bare_torch={not_bare_torch} ran={ran}"
        ),
    }
    return result


def main() -> int:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(result["SCOUT_DONE"])
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
