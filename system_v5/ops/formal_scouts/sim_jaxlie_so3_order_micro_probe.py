#!/usr/bin/env python3
"""JAXLie SO(3) finite order micro-probe.

This is a tool-stage/formal-scout receipt. It tests one JAX ecosystem surface:
``jaxlie.SO3.exp`` plus finite SO(3) composition. It does not run Julia, does
not import or run PyTorch, and cannot promote G-structure, flux, Axis0, or
manifold admission.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp
import jaxlie


RESULT = Path("system_v5/ops/formal_scouts/results/jaxlie_so3_order_micro_probe_results.json")
EPS = 1.0e-12

BLOCKED_CONSUMERS = [
    "full_layer_completion",
    "official_g_structure_selection",
    "layer_stacking",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "FEP",
    "physics_gravity",
    "final_manifold_admission",
]


def _jsonable(x: Any) -> Any:
    if hasattr(x, "item"):
        return x.item()
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    return x


def so3_from(v: jax.Array) -> jaxlie.SO3:
    return jaxlie.SO3.exp(jnp.asarray(v, dtype=jnp.float64))


def compose_matrix(a: jaxlie.SO3, b: jaxlie.SO3) -> jax.Array:
    return a.multiply(b).as_matrix()


def fro_gap(a: jax.Array, b: jax.Array) -> jax.Array:
    return jnp.linalg.norm(a - b)


def so3_health(m: jax.Array) -> dict[str, jax.Array]:
    eye = jnp.eye(3, dtype=jnp.float64)
    return {
        "det_gap": jnp.abs(jnp.linalg.det(m) - 1.0),
        "orthogonality_gap": jnp.max(jnp.abs(m.T @ m - eye)),
    }


def canonical_order_pair(a: jaxlie.SO3, b: jaxlie.SO3) -> tuple[jaxlie.SO3, jaxlie.SO3]:
    # Deliberately label-erases order by using a fixed canonical x-then-y pair.
    del a, b
    return so3_from(jnp.array([0.33, 0.0, 0.0])), so3_from(jnp.array([0.0, -0.27, 0.0]))


def main() -> int:
    RESULT.parent.mkdir(parents=True, exist_ok=True)

    rx = so3_from(jnp.array([0.33, 0.0, 0.0]))
    ry = so3_from(jnp.array([0.0, -0.27, 0.0]))
    rz = so3_from(jnp.array([0.0, 0.0, 0.19]))
    ident = jaxlie.SO3.identity()

    xy = compose_matrix(rx, ry)
    yx = compose_matrix(ry, rx)
    order_gap = fro_gap(xy, yx)

    id_gap = fro_gap(compose_matrix(rx, ident), compose_matrix(ident, rx))
    same_axis_a = so3_from(jnp.array([0.21, 0.0, 0.0]))
    same_axis_b = so3_from(jnp.array([-0.08, 0.0, 0.0]))
    same_axis_gap = fro_gap(compose_matrix(same_axis_a, same_axis_b), compose_matrix(same_axis_b, same_axis_a))

    ca, cb = canonical_order_pair(ry, rx)
    da, db = canonical_order_pair(rx, ry)
    order_erased_gap = fro_gap(compose_matrix(ca, cb), compose_matrix(da, db))

    zxy = compose_matrix(rz, so3_from(jnp.array([0.33, -0.27, 0.0])))
    health_xy = so3_health(xy)
    health_yx = so3_health(yx)
    health_zxy = so3_health(zxy)

    checks = {
        "jaxlie_so3_api_available": True,
        "different_axis_order_sensitive": order_gap > 1.0e-2,
        "identity_control_commutes": id_gap < 1.0e-12,
        "same_axis_control_commutes": same_axis_gap < 1.0e-12,
        "order_erased_control_zero": order_erased_gap < 1.0e-12,
        "xy_boundary_is_so3": health_xy["det_gap"] < 1.0e-12 and health_xy["orthogonality_gap"] < 1.0e-12,
        "yx_boundary_is_so3": health_yx["det_gap"] < 1.0e-12 and health_yx["orthogonality_gap"] < 1.0e-12,
        "third_rotation_boundary_is_so3": health_zxy["det_gap"] < 1.0e-12 and health_zxy["orthogonality_gap"] < 1.0e-12,
        "no_julia_execution": True,
        "no_pytorch_execution": True,
        "promotion_blocked": True,
    }
    audit_pass = all(bool(v) for v in checks.values())

    out = {
        "sim_id": "jaxlie_so3_order_micro_probe",
        "name": "JAXLie SO(3) finite order micro-probe",
        "version": "1.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "classification": "tool_lego_fit_probe",
        "sim_execution_kind": "diagnostic_jax_tool_probe",
        "AUDIT_PASS": audit_pass,
        "all_pass": audit_pass,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "purpose": "Exercise a single JAXLie SO(3) function surface on a finite noncommuting-order claim.",
        "scientific_question": "Can jaxlie.SO3.exp plus composition witness finite SO(3) order sensitivity with identity, same-axis, and order-erased negatives?",
        "root_constraints_in_force": {
            "F01": "finite set of SO(3) tangent vectors and composed rotations",
            "N01": "nonparallel SO(3) rotations are order-sensitive under composition",
        },
        "finite_map": "finite tangent vectors in R3 -> jaxlie.SO3.exp -> SO(3) products AB and BA -> Frobenius order gap",
        "domain": {
            "tool_surface": "jaxlie.SO3.exp, SO3.multiply, SO3.as_matrix",
            "finite_tangent_vectors": [[0.33, 0.0, 0.0], [0.0, -0.27, 0.0], [0.0, 0.0, 0.19]],
        },
        "codomain_or_output": "SO(3) matrices, determinant/orthogonality boundary checks, and order-gap controls",
        "carrier_layer": "SO(3) orientation-frame tool micro-surface",
        "geometry_layer": "finite orientation order sensitivity",
        "carrier_realization": "jaxlie.SO3 objects and JAX float64 matrices",
        "peps3d_embedding": "not_applicable: this is a tool-function micro-probe, not a PEPS3D carrier claim",
        "spinor_state": "not_applicable in this SO(3) tool probe",
        "quaternion_action": "implicit unit-quaternion SO(3) representation inside jaxlie, fenced as tool behavior only",
        "dependency_receipts": ["system_v5/ops/formal_scouts/results/jax_native_geometry_so3_orientation_frame_reduction_probe_results.json"],
        "allowed_claims": [
            "jaxlie.SO3.exp/composition is load-bearing for one finite order-sensitivity micro-claim",
            "identity, same-axis, and order-erased controls pass",
        ],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "eligible_consumers": ["bounded JAX tool coverage planning", "future SO(3) geometry scout design"],
        "promotion_blockers": [
            "tool micro-probe only",
            "no spinor/rho_AB carrier",
            "no PEPS3D cell embedding",
            "no G-structure selection packet",
        ],
        "required_tools": ["jaxlie", "jax", "python_stdlib"],
        "actual_tools_used": ["jaxlie", "jax", "python_stdlib"],
        "TOOL_MANIFEST": {
            "jaxlie": {
                "tried": True,
                "used": True,
                "role": "load_bearing",
                "reason": "jaxlie.SO3.exp and SO3.multiply produce the finite SO(3) order witness.",
            },
            "jax": {
                "tried": True,
                "used": True,
                "role": "load_bearing",
                "reason": "JAX x64 computes matrix gaps and SO(3) determinant/orthogonality checks.",
            },
            "python_stdlib": {
                "tried": True,
                "used": True,
                "role": "supportive",
                "reason": "JSON receipt writing only.",
            },
        },
        "TOOL_INTEGRATION_DEPTH": {"jaxlie": "load_bearing", "jax": "load_bearing", "python_stdlib": "supportive"},
        "tool_manifest": {
            "jaxlie": {
                "tried": True,
                "used": True,
                "role": "load_bearing",
                "reason": "jaxlie.SO3.exp and SO3.multiply produce the finite SO(3) order witness.",
            },
            "jax": {
                "tried": True,
                "used": True,
                "role": "load_bearing",
                "reason": "JAX x64 computes matrix gaps and SO(3) determinant/orthogonality checks.",
            },
            "python_stdlib": {
                "tried": True,
                "used": True,
                "role": "supportive",
                "reason": "JSON receipt writing only.",
            },
        },
        "tool_integration_depth": {"jaxlie": "load_bearing", "jax": "load_bearing", "python_stdlib": "supportive"},
        "checks": checks,
        "metrics": {
            "order_gap_xy_vs_yx": order_gap,
            "identity_gap": id_gap,
            "same_axis_gap": same_axis_gap,
            "order_erased_gap": order_erased_gap,
            "health_xy": health_xy,
            "health_yx": health_yx,
            "health_zxy": health_zxy,
        },
        "claim_boundary": "JAXLie tool-function receipt only; not G-structure selection, layer completion, stacking, flux, Axis0, FEP, physics, or final admission.",
    }
    RESULT.write_text(json.dumps(_jsonable(out), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "jaxlie_so3_order AUDIT_PASS={audit} order_gap={gap:.6f} "
        "same_axis={same:.3e} erased={erased:.3e}".format(
            audit=audit_pass,
            gap=float(order_gap),
            same=float(same_axis_gap),
            erased=float(order_erased_gap),
        )
    )
    return 0 if audit_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
