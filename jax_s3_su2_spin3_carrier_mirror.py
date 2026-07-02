#!/usr/bin/env python3
"""JAX finite S3/SU2/Spin3 carrier and frame-reduction mirror.

Julia references, read-only:
    system_v5/julia_carrier/layers/G_S3_spinor_carrier.jl
    system_v5/julia_carrier/layers/g_su2_spin3_double_cover.jl
    system_v5/julia_carrier/layers/G_SO3_frame_reduction.jl
    system_v5/julia_carrier/layers/pin3_spin3_chirality_clifford_object.jl

This is a diagnostic JAX audit lane. It does not run Julia, does not import
PyTorch, and does not promote G-structure selection or manifold admission.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jax
from jax import config

config.update("jax_enable_x64", True)

import jax.numpy as jnp


OUT = Path("jax_s3_su2_spin3_carrier_mirror_results.json")
I = 1j
ID2 = jnp.eye(2, dtype=jnp.complex128)
ID3 = jnp.eye(3, dtype=jnp.float64)
SX = jnp.asarray([[0, 1], [1, 0]], dtype=jnp.complex128)
SY = jnp.asarray([[0, -I], [I, 0]], dtype=jnp.complex128)
SZ = jnp.asarray([[1, 0], [0, -1]], dtype=jnp.complex128)
PAULI = jnp.stack([SX, SY, SZ])


def _f(x: Any) -> float:
    return float(jax.device_get(x))


def _b(x: Any) -> bool:
    return bool(jax.device_get(x))


def normalize(q: jax.Array) -> jax.Array:
    return q / jnp.linalg.norm(q, axis=-1, keepdims=True)


def qmul(a: jax.Array, b: jax.Array) -> jax.Array:
    a0, a1, a2, a3 = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    b0, b1, b2, b3 = b[..., 0], b[..., 1], b[..., 2], b[..., 3]
    return jnp.stack(
        [
            a0 * b0 - a1 * b1 - a2 * b2 - a3 * b3,
            a0 * b1 + a1 * b0 + a2 * b3 - a3 * b2,
            a0 * b2 - a1 * b3 + a2 * b0 + a3 * b1,
            a0 * b3 + a1 * b2 - a2 * b1 + a3 * b0,
        ],
        axis=-1,
    )


def qconj(q: jax.Array) -> jax.Array:
    return q * jnp.asarray([1.0, -1.0, -1.0, -1.0], dtype=jnp.float64)


def qrot(q: jax.Array) -> jax.Array:
    q = q / jnp.linalg.norm(q, axis=-1, keepdims=True)
    w, x, y, z = q[..., 0], q[..., 1], q[..., 2], q[..., 3]
    return jnp.stack(
        [
            jnp.stack([1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], axis=-1),
            jnp.stack([2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], axis=-1),
            jnp.stack([2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)], axis=-1),
        ],
        axis=-2,
    )


def su2_matrix(q: jax.Array) -> jax.Array:
    q = q / jnp.linalg.norm(q, axis=-1, keepdims=True)
    w, x, y, z = q[..., 0], q[..., 1], q[..., 2], q[..., 3]
    row0 = jnp.stack([w + I * z, x + I * y], axis=-1)
    row1 = jnp.stack([-x + I * y, w - I * z], axis=-1)
    return jnp.stack([row0, row1], axis=-2)


def su2_axis_angle(axis: jax.Array, theta: jax.Array) -> jax.Array:
    axis = axis / jnp.linalg.norm(axis)
    return jnp.cos(theta / 2.0) * ID2 - I * jnp.sin(theta / 2.0) * (
        axis[0] * SX + axis[1] * SY + axis[2] * SZ
    )


def so3_from_su2(U: jax.Array) -> jax.Array:
    cols = []
    Udag = U.conj().T
    for sj in PAULI:
        xp = U @ sj @ Udag
        cols.append(jnp.asarray([0.5 * jnp.trace(si @ xp).real for si in PAULI], dtype=jnp.float64))
    return jnp.stack(cols, axis=1)


def rodrigues(axis: jax.Array, theta: jax.Array) -> jax.Array:
    axis = axis / jnp.linalg.norm(axis)
    x, y, z = axis
    k = jnp.asarray([[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]], dtype=jnp.float64)
    return ID3 + jnp.sin(theta) * k + (1.0 - jnp.cos(theta)) * (k @ k)


def sample_quaternions(n: int = 1024) -> jax.Array:
    key = jax.random.PRNGKey(20260602)
    return normalize(jax.random.normal(key, (n, 4), dtype=jnp.float64))


def s3_su2_so3_checks() -> dict[str, Any]:
    q = sample_quaternions()
    p = jnp.roll(q, 17, axis=0)
    qp = jax.vmap(qmul)(q, p)
    qinv = qconj(q)
    ident = jax.vmap(qmul)(q, qinv)
    U = su2_matrix(q)
    R = qrot(q)
    norm_gap = jnp.max(jnp.abs(jnp.linalg.norm(q, axis=-1) - 1.0))
    closure_gap = jnp.max(jnp.abs(jnp.linalg.norm(qp, axis=-1) - 1.0))
    inverse_gap = jnp.max(jnp.linalg.norm(ident - jnp.asarray([1.0, 0.0, 0.0, 0.0]), axis=-1))
    unitary_gap = jnp.max(jnp.linalg.norm(jnp.swapaxes(U.conj(), -1, -2) @ U - ID2, axis=(-2, -1)))
    su2_det_gap = jnp.max(jnp.abs(jnp.linalg.det(U) - 1.0))
    orth_gap = jnp.max(jnp.linalg.norm(jnp.swapaxes(R, -1, -2) @ R - ID3, axis=(-2, -1)))
    so3_det_gap = jnp.max(jnp.abs(jnp.linalg.det(R) - 1.0))
    hom_gap = jnp.max(jnp.linalg.norm(qrot(qp) - (qrot(q) @ qrot(p)), axis=(-2, -1)))
    neg_cover_gap = jnp.max(jnp.linalg.norm(qrot(q) - qrot(-q), axis=(-2, -1)))
    q_neg_dist_min = jnp.min(jnp.linalg.norm(q - (-q), axis=-1))
    checks = {
        "s3_norm": _f(norm_gap) < 1.0e-12,
        "qmul_closure": _f(closure_gap) < 1.0e-12,
        "q_inverse": _f(inverse_gap) < 1.0e-12,
        "su2_unitary_det": _f(unitary_gap) < 1.0e-12 and _f(su2_det_gap) < 1.0e-12,
        "so3_orthogonal_det": _f(orth_gap) < 1.0e-12 and _f(so3_det_gap) < 1.0e-12,
        "spin3_to_so3_homomorphism": _f(hom_gap) < 1.0e-12,
        "q_negq_same_rotation_distinct_spinors": _f(neg_cover_gap) < 1.0e-12 and _f(q_neg_dist_min) > 1.0,
    }
    return {
        "pass": all(checks.values()),
        "checks": checks,
        "metrics": {
            "max_s3_norm_gap": _f(norm_gap),
            "max_qmul_closure_gap": _f(closure_gap),
            "max_inverse_gap": _f(inverse_gap),
            "max_su2_unitary_gap": _f(unitary_gap),
            "max_su2_det_gap": _f(su2_det_gap),
            "max_so3_orthogonality_gap": _f(orth_gap),
            "max_so3_det_gap": _f(so3_det_gap),
            "max_homomorphism_gap": _f(hom_gap),
            "max_q_negq_rotation_gap": _f(neg_cover_gap),
            "min_q_negq_distance": _f(q_neg_dist_min),
        },
    }


def axis_angle_checks() -> dict[str, Any]:
    axes = normalize(
        jnp.asarray(
            [
                [1.0, 2.0, -1.0],
                [-0.3, 0.7, 0.2],
                [0.4, -0.1, 0.9],
                [1.0, 0.0, 0.0],
            ],
            dtype=jnp.float64,
        )
    )
    angles = jnp.asarray([0.37, 1.1, 2.4, 2.0 * jnp.pi], dtype=jnp.float64)
    rows = []
    max_gap = 0.0
    for axis, theta in zip(jax.device_get(axes), jax.device_get(angles), strict=True):
        U = su2_axis_angle(jnp.asarray(axis), jnp.asarray(theta))
        gap = _f(jnp.linalg.norm(so3_from_su2(U) - rodrigues(jnp.asarray(axis), jnp.asarray(theta))))
        max_gap = max(max_gap, gap)
        rows.append({"theta": float(theta), "axis": [float(x) for x in axis], "rodrigues_gap": gap})
    u_2pi = su2_axis_angle(jnp.asarray([1.0, 0.0, 0.0]), 2.0 * jnp.pi)
    u_4pi = su2_axis_angle(jnp.asarray([1.0, 0.0, 0.0]), 4.0 * jnp.pi)
    checks = {
        "su2_adjoint_matches_rodrigues": max_gap < 1.0e-12,
        "two_pi_spinor_minus_identity": _f(jnp.linalg.norm(u_2pi + ID2)) < 1.0e-12,
        "four_pi_spinor_plus_identity": _f(jnp.linalg.norm(u_4pi - ID2)) < 1.0e-12,
        "two_pi_so3_identity": _f(jnp.linalg.norm(so3_from_su2(u_2pi) - ID3)) < 1.0e-12,
    }
    return {
        "pass": all(checks.values()),
        "checks": checks,
        "rows": rows,
        "metrics": {
            "max_rodrigues_gap": max_gap,
            "two_pi_spinor_plus_identity_gap": _f(jnp.linalg.norm(u_2pi + ID2)),
            "four_pi_spinor_identity_gap": _f(jnp.linalg.norm(u_4pi - ID2)),
        },
    }


def frame_reduction_checks() -> dict[str, Any]:
    q = sample_quaternions(256)
    p = jnp.roll(q, 11, axis=0)
    f1 = qrot(q)
    f2 = qrot(p)
    g = jnp.swapaxes(f1, -1, -2) @ f2
    recon_gap = jnp.max(jnp.linalg.norm(f1 @ g - f2, axis=(-2, -1)))
    det_gap = jnp.max(jnp.abs(jnp.linalg.det(g) - 1.0))
    reflection = jnp.diag(jnp.asarray([1.0, 1.0, -1.0], dtype=jnp.float64))
    reflected_g = jnp.swapaxes(f1, -1, -2) @ (f2 @ reflection)
    reflected_det = jnp.linalg.det(reflected_g)
    checks = {
        "oriented_frames_recovered_by_so3": _f(recon_gap) < 1.0e-12 and _f(det_gap) < 1.0e-12,
        "reflection_excluded_from_so3": _b(jnp.all(reflected_det < -0.999999)),
        "pin_reflection_would_flip_orientation": _b(jnp.all(jnp.abs(reflected_det + 1.0) < 1.0e-12)),
    }
    return {
        "pass": all(checks.values()),
        "checks": checks,
        "metrics": {
            "max_oriented_reconstruction_gap": _f(recon_gap),
            "max_recovered_so3_det_gap": _f(det_gap),
            "reflected_det_min": _f(jnp.min(reflected_det)),
            "reflected_det_max": _f(jnp.max(reflected_det)),
        },
    }


def chirality_reduction_checks() -> dict[str, Any]:
    h0 = 0.53 * SZ + 0.19 * SX
    psi_l = jnp.asarray([1.0 + 0.0j, 0.0 + 0.0j], dtype=jnp.complex128)
    psi_r = jnp.asarray([0.0 + 0.0j, 1.0 + 0.0j], dtype=jnp.complex128)
    e_l = jnp.real(jnp.vdot(psi_l, h0 @ psi_l))
    e_r = jnp.real(jnp.vdot(psi_r, (-h0) @ psi_r))
    parity = SX
    flipped = parity @ psi_l
    flip_overlap_r = jnp.abs(jnp.vdot(psi_r, flipped))
    wrong_same_sign_r = jnp.real(jnp.vdot(psi_r, h0 @ psi_r))
    checks = {
        "opposite_weyl_hamiltonian_signs": _f(e_l) > 0.5 and _f(e_r) > 0.5,
        "wrong_same_sign_control_differs": _f(wrong_same_sign_r) < -0.5,
        "pin_reflection_flips_sheet_basis": _f(flip_overlap_r) > 0.999999,
    }
    return {
        "pass": all(checks.values()),
        "checks": checks,
        "metrics": {
            "left_energy_H0": _f(e_l),
            "right_energy_minus_H0": _f(e_r),
            "right_energy_wrong_plus_H0": _f(wrong_same_sign_r),
            "parity_flip_overlap_with_R": _f(flip_overlap_r),
        },
    }


def main() -> int:
    carrier = s3_su2_so3_checks()
    axis_angle = axis_angle_checks()
    frame = frame_reduction_checks()
    chirality = chirality_reduction_checks()
    checks = {
        "s3_su2_so3_carrier": carrier["pass"],
        "axis_angle_double_cover": axis_angle["pass"],
        "so3_frame_reduction_pin_control": frame["pass"],
        "weyl_chirality_sign_control": chirality["pass"],
    }
    audit_pass = all(checks.values())
    receipt = {
        "sim_id": "jax_s3_su2_spin3_carrier_mirror",
        "name": "JAX S3/SU2/Spin3 carrier and frame-reduction mirror",
        "version": "1.0",
        "tier": "finite_carrier_gstructure_probe",
        "classification": "tool_lego_fit_probe",
        "sim_execution_kind": "nonclassical_diagnostic_jax_audit",
        "promotion_allowed": False,
        "promotion_status": "blocked_diagnostic_only",
        "claim_ceiling": "Dedicated finite JAX carrier/G-structure diagnostic only; not official G-structure selection or layer admission.",
        "ran_julia": False,
        "ran_pytorch": False,
        "root_constraints_in_force": {
            "F01": "finite quaternion/SU2/SO3 samples, finite frame pairs, finite Weyl spinor checks",
            "N01": "Spin/Pin orientation and chirality signs are order/sign sensitive controls",
        },
        "finite_map": "finite S3 unit quaternions -> SU2 matrices -> SO3 rotations/frame reductions and Weyl chirality signs",
        "domain": "finite S3 quaternion samples, axis-angle SU2 elements, oriented/reflected frame pairs, two Weyl sheet basis states",
        "codomain_or_output": "JSON receipt with carrier closure, double-cover, frame-reduction, Pin reflection, and chirality controls",
        "carrier_layer": "S3 as SU2/Spin3 carrier",
        "geometry_layer": "O3 -> SO3 -> Spin3/SU2 reduction with Pin reflection control",
        "carrier_realization": "jax arrays over finite quaternion, SU2, SO3, and C2 spinor objects",
        "spinor_state": "finite two-component Weyl sheet basis states with H_L=+H0, H_R=-H0 sign check",
        "quaternion_action": "Hamilton quaternion multiplication, q -> SU2, q -> SO3, q and -q double-cover invariant",
        "peps3d_embedding": "diagnostic finite carrier cell only; not admitted PEPS3D evidence",
        "dependency_receipts": [
            "system_v5/julia_carrier/layers/G_S3_spinor_carrier_results.json (read-only reference)",
            "system_v5/julia_carrier/layers/g_su2_spin3_double_cover_results.json (read-only reference)",
            "system_v5/julia_carrier/layers/G_SO3_frame_reduction_results.json (read-only reference)",
            "system_v5/julia_carrier/layers/pin3_spin3_chirality_clifford_object_results.json (read-only reference)",
        ],
        "blocked_consumers": ["official_g_structure_selection", "layer_stacking_readiness", "Axis0", "FEP", "flux", "Xi", "Phi0", "physics/gravity", "final_manifold_admission"],
        "tool_manifest": {"jax": "load-bearing finite carrier/group/action/chirality computation"},
        "tool_integration_depth": {"jax": "load_bearing"},
        "carrier": carrier,
        "axis_angle": axis_angle,
        "frame_reduction": frame,
        "chirality": chirality,
        "checks": checks,
        "AUDIT_PASS": audit_pass,
    }
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        "jax_s3_su2_spin3_carrier "
        f"carrier={carrier['pass']} axis={axis_angle['pass']} frame={frame['pass']} "
        f"chirality={chirality['pass']} AUDIT_PASS={audit_pass}"
    )
    return 0 if audit_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
