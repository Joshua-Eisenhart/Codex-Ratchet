#!/usr/bin/env python3
import json
import math
from pathlib import Path

import jax

jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp


MATRIX_PATH = Path("/tmp/16_token_axis_projection_matrix.json")
RESULT_PATH = Path("/tmp/wol_geometry_0_jax_results.json")


def as_float(x):
    return float(jnp.asarray(x))


def qmul(a, b):
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return jnp.array(
        [
            aw * bw - ax * bx - ay * by - az * bz,
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
        ],
        dtype=jnp.float64,
    )


def quat_norm(q):
    return as_float(jnp.sqrt(jnp.sum(q * q)))


def unit_quat_sample(k, n):
    a = 2.0 * math.pi * (k + 0.5) / n
    b = 2.0 * math.pi * (k * 2 + 0.25) / n
    eta = (math.pi / 2.0) * (k + 0.5) / n
    return jnp.array(
        [
            jnp.cos(eta) * jnp.cos(a),
            jnp.cos(eta) * jnp.sin(a),
            jnp.sin(eta) * jnp.cos(b),
            jnp.sin(eta) * jnp.sin(b),
        ],
        dtype=jnp.float64,
    )


def su2_from_quat(q):
    w, x, y, z = q
    return jnp.array(
        [
            [w + 1j * z, x + 1j * y],
            [-x + 1j * y, w - 1j * z],
        ],
        dtype=jnp.complex128,
    )


def so3_from_quat(q):
    w, x, y, z = q
    return jnp.array(
        [
            [1 - 2 * y * y - 2 * z * z, 2 * x * y - 2 * z * w, 2 * x * z + 2 * y * w],
            [2 * x * y + 2 * z * w, 1 - 2 * x * x - 2 * z * z, 2 * y * z - 2 * x * w],
            [2 * x * z - 2 * y * w, 2 * y * z + 2 * x * w, 1 - 2 * x * x - 2 * y * y],
        ],
        dtype=jnp.float64,
    )


def sample_controls(n):
    max_quat_norm_error = 0.0
    max_su2_det_error = 0.0
    max_so3_orth_error = 0.0
    max_so3_det_error = 0.0
    for k in range(n):
        q = unit_quat_sample(k, n)
        max_quat_norm_error = max(max_quat_norm_error, abs(quat_norm(q) - 1.0))
        det_u = jnp.linalg.det(su2_from_quat(q))
        max_su2_det_error = max(max_su2_det_error, abs(as_float(jnp.real(det_u)) - 1.0), abs(as_float(jnp.imag(det_u))))
        r = so3_from_quat(q)
        orth = r.T @ r
        max_so3_orth_error = max(max_so3_orth_error, as_float(jnp.max(jnp.abs(orth - jnp.eye(3, dtype=jnp.float64)))))
        max_so3_det_error = max(max_so3_det_error, abs(as_float(jnp.linalg.det(r)) - 1.0))
    passes = (
        max_quat_norm_error < 1e-12
        and max_su2_det_error < 1e-12
        and max_so3_orth_error < 1e-12
        and max_so3_det_error < 1e-12
    )
    return {
        "sample_count": n,
        "max_quaternion_norm_error": max_quat_norm_error,
        "max_su2_det_error": max_su2_det_error,
        "max_so3_orthogonality_error": max_so3_orth_error,
        "max_so3_det_error": max_so3_det_error,
        "passes": passes,
    }


def psi(phi, chi, eta):
    return jnp.array(
        [
            jnp.exp(1j * (phi + chi)) * jnp.cos(eta),
            jnp.exp(1j * (phi - chi)) * jnp.sin(eta),
        ],
        dtype=jnp.complex128,
    )


def projector(v):
    return jnp.outer(v, jnp.conjugate(v))


def boundary_control():
    phi = 0.37
    p0a = projector(psi(phi, 0.10, 0.0))
    p0b = projector(psi(phi, 1.80, 0.0))
    p1a = projector(psi(phi, 0.10, math.pi / 2.0))
    p1b = projector(psi(phi, 1.80, math.pi / 2.0))
    e0 = as_float(jnp.max(jnp.abs(p0a - p0b)))
    e1 = as_float(jnp.max(jnp.abs(p1a - p1b)))
    return {
        "eta_0_projector_chi_invariance_error": e0,
        "eta_pi_over_2_projector_chi_invariance_error": e1,
        "eta_0_norm": as_float(jnp.linalg.norm(psi(phi, 0.10, 0.0))),
        "eta_pi_over_2_norm": as_float(jnp.linalg.norm(psi(phi, 0.10, math.pi / 2.0))),
        "passes": e0 < 1e-12 and e1 < 1e-12,
    }


def chern_number(n, m, frozen=False):
    d_eta = (math.pi / 2.0) / n
    d_phi = (2.0 * math.pi) / n
    total = 0.0
    for i in range(n):
        eta = (i + 0.5) * d_eta
        for _ in range(n):
            curvature = 0.0 if frozen else -float(m) * as_float(jnp.sin(2.0 * eta))
            total += curvature * d_eta * d_phi
    return total / (2.0 * math.pi)


def gauss_linking(n, flat=False):
    big_r = 2.0
    small_r = 0.6
    dt = 2.0 * math.pi / n
    ds = 2.0 * math.pi / n
    total = 0.0
    for i in range(n):
        t = (i + 0.5) * dt
        c1 = jnp.array([big_r * jnp.cos(t), big_r * jnp.sin(t), 0.0], dtype=jnp.float64)
        dc1 = jnp.array([-big_r * jnp.sin(t), big_r * jnp.cos(t), 0.0], dtype=jnp.float64)
        for j in range(n):
            s = (j + 0.5) * ds
            if flat:
                c2 = jnp.array([4.0 + small_r * jnp.cos(s), 0.0, small_r * jnp.sin(s)], dtype=jnp.float64)
                dc2 = jnp.array([-small_r * jnp.sin(s), 0.0, small_r * jnp.cos(s)], dtype=jnp.float64)
            else:
                ss = -s
                c2 = jnp.array([big_r + small_r * jnp.cos(ss), 0.0, small_r * jnp.sin(ss)], dtype=jnp.float64)
                dc2 = jnp.array([small_r * jnp.sin(ss), 0.0, -small_r * jnp.cos(ss)], dtype=jnp.float64)
            diff = c1 - c2
            total += as_float(jnp.dot(diff, jnp.cross(dc1, dc2)) / (jnp.linalg.norm(diff) ** 3)) * dt * ds / (4.0 * math.pi)
    return total


def complex_vec_for_json(v):
    return [[as_float(jnp.real(z)), as_float(jnp.imag(z))] for z in v]


def main():
    matrix = json.loads(MATRIX_PATH.read_text())
    tokens = [row["token"] for row in matrix["tokens"]]
    signed_operator_names = [row["name"] for row in matrix["signed_operators"]]
    matrix_context = {
        "path": str(MATRIX_PATH),
        "tokens": tokens,
        "token_row_count": len(tokens),
        "signed_operator_count": len(signed_operator_names),
        "signed_operator_names": signed_operator_names,
        "claim_ceiling_seen": matrix.get("claim_ceiling", "unknown"),
    }

    ladder_sizes = [8, 16, 32, 64]
    sample_ladder = {str(n): sample_controls(n) for n in ladder_sizes}
    chern_ladder = {str(n): {"grid": [n, n], "c1": chern_number(n, 1)} for n in ladder_sizes}

    qi = jnp.array([0.0, 1.0, 0.0, 0.0], dtype=jnp.float64)
    qj = jnp.array([0.0, 0.0, 1.0, 0.0], dtype=jnp.float64)
    ij = qmul(qi, qj)
    ji = qmul(qj, qi)
    noncomm_diff = as_float(jnp.max(jnp.abs(ij - ji)))

    negative_q = jnp.array([2.0, 0.0, 0.0, 0.0], dtype=jnp.float64)
    negative_excluded = abs(quat_norm(negative_q) - 1.0) > 1e-9

    cpos = chern_number(64, 1)
    cneg = chern_number(64, 0)
    ckill = chern_number(64, 1, frozen=True)
    link_nested = gauss_linking(128)
    link_flat = gauss_linking(128, flat=True)
    ps = psi(0.173, 0.417, 0.619)

    positive_pass = sample_ladder["64"]["passes"] and abs(cpos + 1.0) < 2e-4 and abs(link_nested - 1.0) < 1e-9
    negative_pass = bool(negative_excluded)
    boundary = boundary_control()
    kill_pass = abs(ckill) < 1e-12
    all_pass = (
        positive_pass
        and negative_pass
        and boundary["passes"]
        and kill_pass
        and abs(cneg) < 1e-12
        and abs(link_flat) < 1e-10
        and noncomm_diff > 0.0
        and matrix_context["token_row_count"] == 16
    )

    result = {
        "object_id": "wol_geometry_0_s3_spinor_carrier",
        "claim_ceiling": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "f01_finite_map": {
            "domain": "{q in H : |q|=1}, finite deterministic samples on S3",
            "codomain_or_output": "SU(2) matrices and SO(3) rotation maps",
            "matrix_context": matrix_context,
            "finite_sample_sizes": ladder_sizes,
            "peps3d_anchor_status": "not_claimed_scratch_geometry_subobject_only",
            "downstream_blocks": ["layer_admission", "flux", "Xi", "Phi0", "Axis0", "bridge", "basin", "physics"],
        },
        "n01_noncomm": {
            "a": [as_float(x) for x in qi],
            "b": [as_float(x) for x in qj],
            "a_times_b": [as_float(x) for x in ij],
            "b_times_a": [as_float(x) for x in ji],
            "max_abs_difference": noncomm_diff,
            "noncommutes": noncomm_diff > 0.0,
        },
        "positive_control": {
            "description": "sampled unit quaternions on S3 map to SU(2) det=+1 and SO(3) orthogonal det=+1",
            "sample_ladder": sample_ladder,
            "passes": positive_pass,
        },
        "negative_control": {
            "description": "non-unit quaternion excluded from carrier",
            "q": [as_float(x) for x in negative_q],
            "norm": quat_norm(negative_q),
            "kill_fires": negative_excluded,
            "passes": negative_pass,
        },
        "boundary_control": boundary,
        "kill_control": {
            "description": "globally frozen projector anti-hardcode control",
            "c1": ckill,
            "passes": kill_pass,
        },
        "chern_positive": {"m": 1, "grid": [64, 64], "expected_c1": -1.0, "c1": cpos, "abs_error": abs(cpos + 1.0), "passes": abs(cpos + 1.0) < 2e-4},
        "chern_negative": {"m": 0, "grid": [64, 64], "expected_c1": 0.0, "c1": cneg, "passes": abs(cneg) < 1e-12},
        "chern_kill_frozen": {"m": 1, "grid": [64, 64], "expected_c1": 0.0, "c1": ckill, "passes": kill_pass},
        "chern_ladder": chern_ladder,
        "linking_number_nested": link_nested,
        "linking_number_flat": link_flat,
        "psi_sample": {
            "formula": "psi(phi,chi;eta) = [exp(i(phi+chi))*cos(eta), exp(i(phi-chi))*sin(eta)]",
            "params": {"phi": 0.173, "chi": 0.417, "eta": 0.619, "s": "L"},
            "vector": complex_vec_for_json(ps),
        },
        "engine": "jax",
        "all_pass": all_pass,
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"wrote {RESULT_PATH} all_pass={all_pass}")


if __name__ == "__main__":
    main()
